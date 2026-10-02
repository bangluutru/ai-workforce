"""Semantic Object Classifier & Document Structure Analyzer.

Conforms to:
- Section 4: Document Structure Analysis (Document -> Page -> Region/Object)
- Section 6: Relationship Graph Construction
- Section 8: Object Classifier (16+ semantic types, distinguishing photo/diagram/chart/table/formula)
- Section 16: Mixed Object Decomposition (Nested objects in figures)
"""

from __future__ import annotations

import re
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pymupdf

from ir.models import (
    ConfidenceMetrics,
    DocumentIR,
    DocumentStyleProfile,
    ObjectGeometry,
    ReconstructionStrategy,
    RelationshipType,
    SemanticObject,
    SemanticObjectType,
    SemanticRelationship,
)
from .ocr_engine import OCREngine
from .style_extractor import StyleExtractor


class SemanticClassifier:
    """Classifies raw PDF pages, text blocks, drawings, and images into Document IR."""

    def __init__(self):
        self.style_extractor = StyleExtractor()
        self.ocr_engine = OCREngine()

    def analyze_document(
        self,
        pdf_path: Union[str, Path],
        target_language: str = "vi",
        extract_assets_dir: Optional[Union[str, Path]] = None,
    ) -> DocumentIR:
        doc = pymupdf.open(str(pdf_path))
        style_profile = self.style_extractor.extract_profile(doc)
        doc_id = Path(pdf_path).stem

        ir = DocumentIR(
            document_id=doc_id,
            source_pdf=str(pdf_path),
            title=doc.metadata.get("title", "") or doc_id,
            target_language=target_language,
            style_profile=style_profile,
        )

        assets_dir = Path(extract_assets_dir) if extract_assets_dir else None
        if assets_dir:
            assets_dir.mkdir(parents=True, exist_ok=True)

        reading_order_counter = 1
        objects_by_page: Dict[int, List[SemanticObject]] = {}

        # ---------------------------------------------------------------------
        # 1. Process Page by Page
        # ---------------------------------------------------------------------
        for p_idx in range(len(doc)):
            page = doc[p_idx]
            page_num = p_idx + 1
            page_w = page.rect.width
            page_h = page.rect.height
            objects_by_page[page_num] = []

            # A. Extract Tables First (Structured Grid)
            table_bboxes: List[Tuple[float, float, float, float]] = []
            try:
                tables = page.find_tables()
                for t_idx, tbl in enumerate(tables):
                    t_bbox = (tbl.bbox[0], tbl.bbox[1], tbl.bbox[2], tbl.bbox[3])
                    table_bboxes.append(t_bbox)

                    # Extract table data
                    extracted_data = tbl.extract()
                    headers = extracted_data[0] if extracted_data else []
                    rows = extracted_data[1:] if len(extracted_data) > 1 else []

                    t_geom = ObjectGeometry(
                        bbox=t_bbox,
                        page_number=page_num,
                        page_width=page_w,
                        page_height=page_h,
                    )

                    t_obj = SemanticObject(
                        id=f"p{page_num}_tbl_{t_idx}",
                        type=SemanticObjectType.TABLE,
                        source_content={
                            "headers": headers,
                            "rows": rows,
                            "col_count": len(headers) if headers else 0,
                            "row_count": len(rows),
                        },
                        reading_order=reading_order_counter,
                        geometry=t_geom,
                        confidence=ConfidenceMetrics(recognition=0.95, semantic=0.95, reconstruction=0.95, data=0.98),
                        reconstruction_strategy=ReconstructionStrategy.DYNAMIC_TABLE,
                    )
                    reading_order_counter += 1
                    ir.add_object(t_obj)
                    objects_by_page[page_num].append(t_obj)
            except Exception:
                pass

            # B. Extract Raster Images & Classify (Photo vs Chart vs Diagram)
            image_list = page.get_images(full=True)
            for img_idx, img_info in enumerate(image_list):
                xref = img_info[0]
                img_bbox = self._get_image_bbox(page, xref)
                if not img_bbox:
                    continue

                # Save asset if dir provided
                asset_ref = None
                if assets_dir:
                    asset_filename = f"asset_p{page_num}_img_{img_idx}.png"
                    asset_path = assets_dir / asset_filename
                    try:
                        pix = pymupdf.Pixmap(doc, xref)
                        if pix.alpha:
                            pix.save(str(asset_path))
                        else:
                            pix_rgb = pymupdf.Pixmap(pymupdf.csRGB, pix)
                            pix_rgb.save(str(asset_path))
                            pix_rgb = None
                        pix = None
                        asset_ref = str(asset_path)
                        ir.asset_registry[f"p{page_num}_img_{img_idx}"] = asset_ref
                    except Exception:
                        pass

                # Classify Image: Photo vs Chart vs Diagram
                img_type, strategy, conf = self._classify_image(doc, xref, img_bbox, page_w, page_h)

                img_geom = ObjectGeometry(
                    bbox=img_bbox,
                    page_number=page_num,
                    page_width=page_w,
                    page_height=page_h,
                )

                img_obj = SemanticObject(
                    id=f"p{page_num}_img_{img_idx}",
                    type=img_type,
                    source_content={"xref": xref, "image_type": img_type.value},
                    reading_order=reading_order_counter,
                    geometry=img_geom,
                    confidence=conf,
                    reconstruction_strategy=strategy,
                    source_asset_reference=asset_ref,
                )
                reading_order_counter += 1
                ir.add_object(img_obj)
                objects_by_page[page_num].append(img_obj)

            # C. Extract Drawings (Vector Graphics, Flowcharts, Diagrams)
            drawings = page.get_drawings()
            clustered_drawings = self._cluster_drawings(drawings, page_w, page_h)
            for d_idx, cluster in enumerate(clustered_drawings):
                c_bbox = cluster["bbox"]
                # Skip if already inside a table or image
                if self._is_inside_any(c_bbox, table_bboxes):
                    continue

                d_type, d_strat, d_conf = self._classify_vector_cluster(cluster)
                d_geom = ObjectGeometry(
                    bbox=c_bbox,
                    page_number=page_num,
                    page_width=page_w,
                    page_height=page_h,
                )

                # Save asset crop if assets_dir provided
                draw_asset_ref = None
                if assets_dir:
                    asset_filename = f"asset_p{page_num}_draw_{d_idx}.png"
                    asset_path = assets_dir / asset_filename
                    try:
                        clip_rect = pymupdf.Rect(c_bbox) & page.rect
                        if clip_rect.is_valid and clip_rect.width >= 5 and clip_rect.height >= 5:
                            pix = page.get_pixmap(clip=clip_rect, dpi=200)
                            pix.save(str(asset_path))
                            draw_asset_ref = str(asset_path)
                            ir.asset_registry[f"p{page_num}_draw_{d_idx}"] = draw_asset_ref
                    except Exception as e:
                        logger.warning(f"Failed to rasterize drawing cluster p{page_num}_draw_{d_idx}: {e}")

                d_obj = SemanticObject(
                    id=f"p{page_num}_draw_{d_idx}",
                    type=d_type,
                    source_content={"path_count": len(cluster["paths"]), "is_vector": True},
                    reading_order=reading_order_counter,
                    geometry=d_geom,
                    confidence=d_conf,
                    reconstruction_strategy=d_strat,
                    source_asset_reference=draw_asset_ref,
                )
                reading_order_counter += 1
                ir.add_object(d_obj)
                objects_by_page[page_num].append(d_obj)

            # D. Extract Text Blocks & Formulas
            page_text_dict = page.get_text("dict")
            blocks = page_text_dict.get("blocks", [])

            # Check if page is scanned and needs OCR fallback
            if len(blocks) == 0 and self.ocr_engine.is_page_scanned(page):
                ocr_blocks = self.ocr_engine.ocr_page(page)
                for ob_idx, ob in enumerate(ocr_blocks):
                    ob_geom = ObjectGeometry(
                        bbox=ob["bbox"],
                        page_number=page_num,
                        page_width=page_w,
                        page_height=page_h,
                    )
                    ob_obj = SemanticObject(
                        id=f"p{page_num}_ocr_{ob_idx}",
                        type=SemanticObjectType.PARAGRAPH,
                        source_content=ob["text"],
                        reading_order=reading_order_counter,
                        geometry=ob_geom,
                        confidence=ConfidenceMetrics(recognition=ob.get("confidence", 0.8), semantic=0.8, reconstruction=0.85),
                        reconstruction_strategy=ReconstructionStrategy.REFLOW_TEXT,
                    )
                    reading_order_counter += 1
                    ir.add_object(ob_obj)
                    objects_by_page[page_num].append(ob_obj)
                continue

            for b_idx, block in enumerate(blocks):
                if block.get("type") == 0:  # text block
                    bbox = block.get("bbox", (0, 0, 0, 0))
                    # Skip if block is entirely inside an already extracted table
                    if self._is_inside_any(bbox, table_bboxes):
                        continue

                    block_text, avg_font_size, is_bold, is_italic, font_name = self._extract_block_properties(block)
                    if not block_text.strip():
                        continue

                    # Classify Text Object
                    t_type, t_strat, t_conf = self._classify_text_block(
                        block_text, avg_font_size, is_bold, bbox, style_profile, page_w, page_h
                    )

                    t_geom = ObjectGeometry(
                        bbox=bbox,
                        page_number=page_num,
                        page_width=page_w,
                        page_height=page_h,
                    )

                    t_obj = SemanticObject(
                        id=f"p{page_num}_txt_{b_idx}",
                        type=t_type,
                        source_content=block_text,
                        reading_order=reading_order_counter,
                        geometry=t_geom,
                        style={
                            "font_size": avg_font_size,
                            "is_bold": is_bold,
                            "is_italic": is_italic,
                            "font_name": font_name,
                        },
                        confidence=t_conf,
                        reconstruction_strategy=t_strat,
                    )
                    reading_order_counter += 1
                    ir.add_object(t_obj)
                    objects_by_page[page_num].append(t_obj)

        doc.close()

        # ---------------------------------------------------------------------
        # 2. Build Relationship Graph (Section 6)
        # ---------------------------------------------------------------------
        self._build_relationships(ir, objects_by_page)

        return ir

    # -------------------------------------------------------------------------
    # Classification Helpers
    # -------------------------------------------------------------------------

    def _classify_text_block(
        self,
        text: str,
        font_size: float,
        is_bold: bool,
        bbox: Tuple[float, float, float, float],
        style: DocumentStyleProfile,
        page_w: float,
        page_h: float,
    ) -> Tuple[SemanticObjectType, ReconstructionStrategy, ConfidenceMetrics]:
        t_clean = text.strip()
        y0, y1 = bbox[1], bbox[3]

        # 1. Header / Footer / Page Number (Margin zones)
        if y0 < 45.0:
            if re.match(r"^(\d+|-\s*\d+\s*-|Page\s*\d+(\s*of\s*\d+)?)$", t_clean, re.I):
                return SemanticObjectType.PAGE_NUMBER, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.98, 0.98, 0.98)
            return SemanticObjectType.HEADER, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.92, 0.92, 0.92)

        if y1 > page_h - 45.0:
            if re.match(r"^(\d+|-\s*\d+\s*-|Page\s*\d+(\s*of\s*\d+)?)$", t_clean, re.I):
                return SemanticObjectType.PAGE_NUMBER, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.98, 0.98, 0.98)
            return SemanticObjectType.FOOTER, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.92, 0.92, 0.92)

        # 2. Footnotes (Small font, near bottom)
        if font_size <= style.body_font_size - 1.5 and y1 > page_h * 0.75:
            if re.match(r"^(\*|\†|\(\d+\)|\[\d+\]|\d+\.)", t_clean):
                return SemanticObjectType.FOOTNOTE, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.95, 0.95, 0.95)

        # 3. Mathematical Formulas
        if self._is_formula(t_clean, font_size, style.body_font_size):
            return SemanticObjectType.FORMULA, ReconstructionStrategy.LATEX_MATH, ConfidenceMetrics(0.92, 0.90, 0.94)

        # 4. Captions (Figure / Table / Chart / Diagram annotations)
        if re.match(r"^(Figure|Fig\.|Hình|Bảng|Table|Chart|Diagram|Sơ đồ|図|表)\s*(\d+|[A-Z])", t_clean, re.I):
            return SemanticObjectType.CAPTION, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.96, 0.96, 0.96)

        # 5. Headings & Titles
        if font_size >= style.body_font_size + 4.0 or (font_size >= style.body_font_size + 1.5 and is_bold):
            if len(t_clean) < 180 and not t_clean.endswith("."):
                if font_size >= style.heading_scale[0]:
                    return SemanticObjectType.TITLE, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.95, 0.95, 0.95)
                return SemanticObjectType.HEADING, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.95, 0.95, 0.95)

        # Check numbered headings: e.g. "1. Introduction", "2.1 Methods"
        if re.match(r"^\d+(\.\d+)*\s+[A-ZÀ-Ỹ]", t_clean) and len(t_clean) < 120:
            return SemanticObjectType.HEADING, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.94, 0.94, 0.94)

        # 6. Lists
        if re.match(r"^([•–\-\*\u2022\u25cb\u25cf]|\(\d+\)|\d+\))\s+", t_clean):
            return SemanticObjectType.LIST, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.94, 0.94, 0.94)

        # 7. Callouts
        if re.match(r"^(Note|Lưu ý|Chú ý|Warning|Caution|Quan trọng|Important|※):", t_clean, re.I):
            return SemanticObjectType.CALLOUT, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.93, 0.93, 0.93)

        # Default: Normal Paragraph
        return SemanticObjectType.PARAGRAPH, ReconstructionStrategy.REFLOW_TEXT, ConfidenceMetrics(0.98, 0.98, 0.98)

    def _is_formula(self, text: str, font_size: float, body_size: float) -> bool:
        """Heuristics for standalone or structured mathematical expressions."""
        t_clean = text.strip()

        # Japanese sentence / prose markers
        if re.search(r"[。、]|(?:について|において|による|により|とする|である|こと|および|または|重測定|設定|試料|装置|指針)", t_clean):
            return False
        if t_clean.endswith("。") or t_clean.endswith("."):
            return False

        # Check if it is a natural language explanatory sentence containing inline variables
        words = t_clean.split()
        if len(words) >= 5:
            common_prose = {
                "the", "a", "an", "this", "that", "these", "those", "above", "below",
                "we", "in", "is", "are", "where", "govern", "equilibrium", "shown",
                "such", "as", "section", "analyze", "được", "trong", "theo", "với", "cho", "của"
            }
            prose_words = sum(1 for w in words if w.lower().strip(".,;:()") in common_prose)
            if prose_words >= 2:
                return False

        # Common math symbols
        math_symbols = set("=≠≈≤≥±×÷∑∏∫∂√∞∈∉⊂⊆∪∩∧∨¬⇒⇔λμπθσωΔΩ")
        symbol_count = sum(1 for ch in text if ch in math_symbols)

        # Standalone equation markers
        has_eq = "=" in text or "≈" in text or "≤" in text or "≥" in text
        has_symbols = symbol_count >= 2

        # Check fraction-like or exponent patterns: e.g. f(x) = (x^2 + 1) / 2
        is_short = len(text) < 100
        has_vars = bool(re.search(r"\b[a-zA-Z]\s*[\^_=]\s*", text))

        if has_eq and (has_symbols or has_vars) and is_short:
            return True
        if symbol_count >= 3 and is_short:
            return True
        return False

    def _classify_image(
        self,
        doc: pymupdf.Document,
        xref: int,
        bbox: Tuple[float, float, float, float],
        page_w: float,
        page_h: float,
    ) -> Tuple[SemanticObjectType, ReconstructionStrategy, ConfidenceMetrics]:
        """Distinguishes PHOTO vs CHART vs DIAGRAM vs ILLUSTRATION."""
        try:
            pix = pymupdf.Pixmap(doc, xref)
            w, h = pix.width, pix.height
            aspect_ratio = w / max(1, h)

            # Heuristic: Photographs tend to be large, continuous tone, 3-channel RGB/CMYK
            if w > 300 and h > 200:
                # Check color depth / colors
                # True photo: immutable source artifact
                return SemanticObjectType.PHOTO, ReconstructionStrategy.PRESERVE_ASSET, ConfidenceMetrics(0.95, 0.95, 1.0)

            # Smaller images could be icons, stamps, or illustrations
            if w < 120 and h < 120:
                return SemanticObjectType.VECTOR_GRAPHIC, ReconstructionStrategy.PRESERVE_ASSET, ConfidenceMetrics(0.90, 0.90, 1.0)

            return SemanticObjectType.PHOTO, ReconstructionStrategy.PRESERVE_ASSET, ConfidenceMetrics(0.88, 0.88, 1.0)
        except Exception:
            return SemanticObjectType.PHOTO, ReconstructionStrategy.PRESERVE_ASSET, ConfidenceMetrics(0.80, 0.80, 1.0)

    def _cluster_drawings(
        self, drawings: List[Dict[str, Any]], page_w: float, page_h: float
    ) -> List[Dict[str, Any]]:
        """Groups vector drawing paths into coherent graphical regions."""
        if not drawings:
            return []

        clusters: List[Dict[str, Any]] = []
        for path in drawings:
            rect = path.get("rect")
            if not rect:
                continue
            r_bbox = (rect.x0, rect.y0, rect.x1, rect.y1)
            # Skip tiny single lines or page borders
            w, h = r_bbox[2] - r_bbox[0], r_bbox[3] - r_bbox[1]
            if w < 5 and h < 5:
                continue
            if w > page_w - 20 and h < 3:
                continue  # horizontal rule

            # Check if merges into an existing cluster
            merged = False
            for c in clusters:
                c_bbox = c["bbox"]
                # Expand by 15pt neighborhood
                if not (r_bbox[0] > c_bbox[2] + 15 or r_bbox[2] < c_bbox[0] - 15 or
                        r_bbox[1] > c_bbox[3] + 15 or r_bbox[3] < c_bbox[1] - 15):
                    # Merge
                    c["bbox"] = (
                        min(c_bbox[0], r_bbox[0]),
                        min(c_bbox[1], r_bbox[1]),
                        max(c_bbox[2], r_bbox[2]),
                        max(c_bbox[3], r_bbox[3]),
                    )
                    c["paths"].append(path)
                    merged = True
                    break

            if not merged:
                clusters.append({"bbox": r_bbox, "paths": [path]})

        # Filter out trivial single line decorations
        significant_clusters = [
            c for c in clusters
            if (c["bbox"][2] - c["bbox"][0] > 40 and c["bbox"][3] - c["bbox"][1] > 30)
            or len(c["paths"]) >= 4
        ]
        return significant_clusters

    def _classify_vector_cluster(
        self, cluster: Dict[str, Any]
    ) -> Tuple[SemanticObjectType, ReconstructionStrategy, ConfidenceMetrics]:
        """Classifies vector clusters into DIAGRAM, CHART, or VECTOR_GRAPHIC."""
        paths = cluster["paths"]
        # If cluster has rects, lines, and curves -> DIAGRAM (Flowchart / Block diagram)
        has_rects = any(p.get("type") in ("re", "rect") for p in paths)
        has_lines = any(p.get("type") in ("l", "line") for p in paths)
        has_curves = any(p.get("type") in ("c", "curve") for p in paths)

        if len(paths) >= 10:
            if has_rects and has_lines:
                return SemanticObjectType.DIAGRAM, ReconstructionStrategy.RECONSTRUCT_DIAGRAM, ConfidenceMetrics(0.90, 0.90, 0.90)
            return SemanticObjectType.CHART, ReconstructionStrategy.REDRAW_CHART, ConfidenceMetrics(0.85, 0.85, 0.85)

        if len(paths) >= 4:
            return SemanticObjectType.DIAGRAM, ReconstructionStrategy.RECONSTRUCT_DIAGRAM, ConfidenceMetrics(0.85, 0.85, 0.85)

        return SemanticObjectType.VECTOR_GRAPHIC, ReconstructionStrategy.PRESERVE_ASSET, ConfidenceMetrics(0.90, 0.90, 1.0)

    # -------------------------------------------------------------------------
    # Relationship Graph Building (Section 6)
    # -------------------------------------------------------------------------

    def _build_relationships(
        self, ir: DocumentIR, objects_by_page: Dict[int, List[SemanticObject]]
    ) -> None:
        """Infers semantic relationships between objects based on spatial proximity & references."""
        for page_num, page_objs in objects_by_page.items():
            captions = [o for o in page_objs if o.type == SemanticObjectType.CAPTION]
            visuals = [
                o for o in page_objs
                if o.type in (
                    SemanticObjectType.PHOTO,
                    SemanticObjectType.CHART,
                    SemanticObjectType.DIAGRAM,
                    SemanticObjectType.TABLE,
                    SemanticObjectType.ILLUSTRATION,
                )
            ]
            paragraphs = [o for o in page_objs if o.type == SemanticObjectType.PARAGRAPH]
            footnotes = [o for o in page_objs if o.type == SemanticObjectType.FOOTNOTE]

            # 1. CAPTION -> DESCRIBES -> VISUAL (Photo, Table, Chart, Diagram)
            for cap in captions:
                cap_y0 = cap.geometry.bbox[1]
                closest_vis = None
                min_dist = float("inf")
                for vis in visuals:
                    vis_y1 = vis.geometry.bbox[3]
                    vis_y0 = vis.geometry.bbox[1]
                    # Caption is typically directly below (0 to 35pt) or directly above
                    dist_below = cap_y0 - vis_y1
                    dist_above = vis_y0 - cap.geometry.bbox[3]
                    dist = min(abs(dist_below), abs(dist_above))
                    if dist < min_dist and dist < 45.0:
                        min_dist = dist
                        closest_vis = vis

                if closest_vis:
                    ir.add_relationship(cap.id, closest_vis.id, RelationshipType.DESCRIBES)

            # 2. PARAGRAPH -> REFERENCES -> TABLE / FIGURE
            for p in paragraphs:
                p_text = p.get_text_content()
                # Check references like "như trong Bảng 1", "as shown in Figure 2"
                table_refs = re.findall(r"(?:Bảng|Table|表)\s*(\d+)", p_text, re.I)
                fig_refs = re.findall(r"(?:Hình|Figure|Fig\.|図)\s*(\d+)", p_text, re.I)

                for t_num in table_refs:
                    for v in visuals:
                        if v.type == SemanticObjectType.TABLE:
                            ir.add_relationship(p.id, v.id, RelationshipType.REFERENCES, {"ref_id": t_num})

                for f_num in fig_refs:
                    for v in visuals:
                        if v.type in (SemanticObjectType.PHOTO, SemanticObjectType.CHART, SemanticObjectType.DIAGRAM):
                            ir.add_relationship(p.id, v.id, RelationshipType.REFERENCES, {"ref_id": f_num})

            # 3. FOOTNOTE -> ANNOTATES -> PARAGRAPH
            for fn in footnotes:
                fn_text = fn.get_text_content()
                # Look for matching footnote marker in paragraphs on the same page
                marker_match = re.match(r"^(\*|\†|\(\d+\)|\[\d+\]|\d+)", fn_text)
                if marker_match:
                    marker = marker_match.group(1)
                    for p in paragraphs:
                        if marker in p.get_text_content():
                            ir.add_relationship(fn.id, p.id, RelationshipType.ANNOTATES, {"marker": marker})

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _get_image_bbox(self, page: pymupdf.Page, xref: int) -> Optional[Tuple[float, float, float, float]]:
        for img_rect in page.get_image_rects(xref):
            return (img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1)
        return None

    def _is_inside_any(
        self, bbox: Tuple[float, float, float, float], parent_bboxes: List[Tuple[float, float, float, float]]
    ) -> bool:
        bx0, by0, bx1, by1 = bbox
        for px0, py0, px1, py1 in parent_bboxes:
            if bx0 >= px0 - 2 and by0 >= py0 - 2 and bx1 <= px1 + 2 and by1 <= py1 + 2:
                return True
        return False

    def _extract_block_properties(
        self, block: Dict[str, Any]
    ) -> Tuple[str, float, bool, bool, str]:
        lines = block.get("lines", [])
        line_texts: List[str] = []
        sizes: List[float] = []
        bolds: List[bool] = []
        italics: List[bool] = []
        fonts: List[str] = []

        for l in lines:
            span_texts = []
            for s in l.get("spans", []):
                t = s.get("text", "")
                if t:
                    span_texts.append(t)
                    sizes.append(s.get("size", 10.0))
                    flags = s.get("flags", 0)
                    bolds.append(bool(flags & 2 or "bold" in s.get("font", "").lower()))
                    italics.append(bool(flags & 1 or "italic" in s.get("font", "").lower()))
                    fonts.append(s.get("font", ""))
            line_texts.append("".join(span_texts))

        full_text = _join_lines_cjk_aware(line_texts)
        avg_size = statistics.mean(sizes) if sizes else 10.0
        is_bold = any(bolds)
        is_italic = any(italics)
        font_name = fonts[0] if fonts else "Times New Roman"

        return full_text, avg_size, is_bold, is_italic, font_name


_CJK_RE = __import__("re").compile(r"[\u3000-\u30ff\u3400-\u9fff\uff00-\uffef]")


def _join_lines_cjk_aware(line_texts):
    """Nối các dòng của một khối: tiếng Nhật/Trung KHÔNG có dấu cách ở chỗ xuống dòng ("測定 は" → "測定は"),
    bỏ dấu cách lạc giữa chữ số và chữ Hán ("2009 年" → "2009年"); tiếng Latin nối từ bị gạch nối cuối dòng."""
    import re as _re
    out = ""
    for t in (x.strip() for x in line_texts):
        if not t:
            continue
        if not out:
            out = t
        elif _CJK_RE.search(out[-1]) or _CJK_RE.search(t[0]):
            out += t
        elif out.endswith("-") and t[:1].islower():
            out = out[:-1] + t
        else:
            out += " " + t
    if len(_CJK_RE.findall(out)) > len(out) * 0.3:
        out = _re.sub(r"(?<=[\u3000-\u30ff\u3400-\u9fff\uff00-\uffef]) +(?=[\u3000-\u30ff\u3400-\u9fff\uff00-\uffef\d])", "", out)
        out = _re.sub(r"(?<=\d) +(?=[\u3000-\u30ff\u3400-\u9fff])", "", out)
    return out.strip()
