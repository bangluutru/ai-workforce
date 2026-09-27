"""Deterministic Document, Page, and Region Classifier for Adaptive PDF Engine.

Part of AIWF Translation Upgrade #1.6:
- Three-level classification: Document Level, Page Level, Region Level.
- Layout taxonomy: TEXT_FLOW, TABLE_FORM, VISUAL_DIAGRAM, IMAGE_GROUP, FIXED_LAYOUT, MIXED.
- Pagination constraints: HARD, SOFT, FREE.
- Uses measurable geometric and content features without external LLM/vision API.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

from .layout_profile import (
    DocumentClass,
    LayoutProfile,
    PageConstraint,
    PageProfile,
    RegionProfile,
    StructuralRole,
)


def _compute_page_metrics(page: pymupdf.Page) -> Dict[str, Any]:
    """Extract measurable layout and content metrics from a PDF page."""
    page_rect = page.rect
    page_w = page_rect.width
    page_h = page_rect.height
    page_area = max(page_w * page_h, 1.0)

    # 1. Text blocks analysis
    text_blocks = page.get_text("blocks")
    valid_text_blocks = [b for b in text_blocks if b[4].strip() and b[6] == 0]
    total_blocks_count = len(valid_text_blocks)

    total_text_area = 0.0
    total_chars = 0
    paragraph_chars = 0
    block_sizes: List[float] = []
    font_sizes: List[float] = []
    y_coords: List[float] = []
    x_coords: List[float] = []

    # Detailed text extraction for spans/fonts
    text_page = page.get_text("dict")
    for b in text_page.get("blocks", []):
        if b.get("type") == 0:  # text
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    sz = span.get("size", 0.0)
                    if sz > 0:
                        font_sizes.append(sz)

    for b in valid_text_blocks:
        x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
        bw = max(x1 - x0, 0.0)
        bh = max(y1 - y0, 0.0)
        area = bw * bh
        total_text_area += area
        block_sizes.append(area)
        n_chars = len(text)
        total_chars += n_chars
        if n_chars >= 80 or (bw > page_w * 0.45 and bh > 25):
            paragraph_chars += n_chars
        x_coords.append(x0)
        y_coords.append(y0)

    text_area_ratio = min(total_text_area / page_area, 1.0)
    long_paragraph_ratio = (paragraph_chars / total_chars) if total_chars > 0 else 0.0
    median_block_size = sorted(block_sizes)[len(block_sizes) // 2] if block_sizes else 0.0

    # Font variance
    font_variance = 0.0
    if len(font_sizes) > 1:
        mean_font = sum(font_sizes) / len(font_sizes)
        font_variance = sum((f - mean_font) ** 2 for f in font_sizes) / len(font_sizes)

    # 2. Images analysis
    images = page.get_images()
    image_count = len(images)
    image_area = 0.0
    # Approximate image coverage
    for img in images:
        try:
            rects = page.get_image_rects(img[0])
            for r in rects:
                image_area += r.width * r.height
        except Exception:
            pass
    image_area_ratio = min(image_area / page_area, 1.0)

    # 3. Vector drawings analysis
    drawings = page.get_drawings()
    drawing_count = len(drawings)
    drawing_rect_count = sum(1 for d in drawings if d.get("type") in ("re", "rect") or "rect" in d)
    drawing_curve_count = sum(1 for d in drawings if d.get("type") in ("c", "curve"))
    drawing_line_count = sum(1 for d in drawings if d.get("type") in ("l", "line"))

    # 4. Tables analysis
    tables_found = []
    try:
        if hasattr(page, "find_tables"):
            tabs = page.find_tables()
            if tabs and hasattr(tabs, "tables"):
                tables_found = tabs.tables
    except Exception:
        tables_found = []
    table_count = len(tables_found)
    table_area = sum((t.bbox[2] - t.bbox[0]) * (t.bbox[3] - t.bbox[1]) for t in tables_found) if tables_found else 0.0
    table_area_ratio = min(table_area / page_area, 1.0)

    # 5. Margins calculation
    margins = {"top": 36.0, "bottom": 36.0, "left": 36.0, "right": 36.0}
    if valid_text_blocks:
        min_x = min(b[0] for b in valid_text_blocks)
        min_y = min(b[1] for b in valid_text_blocks)
        max_x = max(b[2] for b in valid_text_blocks)
        max_y = max(b[3] for b in valid_text_blocks)
        margins = {
            "top": round(max(min_y, 18.0), 1),
            "bottom": round(max(page_h - max_y, 18.0), 1),
            "left": round(max(min_x, 18.0), 1),
            "right": round(max(page_w - max_x, 18.0), 1),
        }

    return {
        "page_w": page_w,
        "page_h": page_h,
        "page_area": page_area,
        "text_blocks_count": total_blocks_count,
        "total_chars": total_chars,
        "text_area_ratio": round(text_area_ratio, 3),
        "long_paragraph_ratio": round(long_paragraph_ratio, 3),
        "median_block_size": round(median_block_size, 1),
        "font_variance": round(font_variance, 2),
        "image_count": image_count,
        "image_area_ratio": round(image_area_ratio, 3),
        "drawing_count": drawing_count,
        "drawing_rect_count": drawing_rect_count,
        "drawing_curve_count": drawing_curve_count,
        "drawing_line_count": drawing_line_count,
        "table_count": table_count,
        "table_area_ratio": round(table_area_ratio, 3),
        "margins": margins,
    }


def classify_page(page: pymupdf.Page, page_idx: int) -> PageProfile:
    """Classify a single PDF page into a PageProfile with evidence."""
    metrics = _compute_page_metrics(page)
    evidence: List[str] = []

    text_ratio = metrics["text_area_ratio"]
    par_ratio = metrics["long_paragraph_ratio"]
    draw_count = metrics["drawing_count"]
    img_count = metrics["image_count"]
    tab_count = metrics["table_count"]
    tab_ratio = metrics["table_area_ratio"]
    chars = metrics["total_chars"]

    # Decision tree based on measurable layout features
    page_class = DocumentClass.MIXED
    page_constraint = PageConstraint.SOFT
    confidence = 0.90

    # Case 1: Pure or dominant text flow
    if img_count == 0 and draw_count <= 25 and tab_ratio < 0.25 and (par_ratio >= 0.40 or chars > 700):
        page_class = DocumentClass.TEXT_FLOW
        page_constraint = PageConstraint.FREE
        evidence.append(f"High text content ({chars} chars, par_ratio={par_ratio:.2f})")
        evidence.append(f"Zero images, minimal drawings ({draw_count}), low table area ({tab_ratio:.2f})")
        confidence = 0.95

    # Case 2: Dominant Image Group (e.g. photo grid / gallery)
    elif img_count >= 3 and (metrics["image_area_ratio"] >= 0.25 or img_count >= 5):
        page_class = DocumentClass.IMAGE_GROUP
        page_constraint = PageConstraint.SOFT
        evidence.append(f"Dominant image layout ({img_count} images, image_area_ratio={metrics['image_area_ratio']:.2f})")
        confidence = 0.95

    # Case 3: Dominant Table or Form
    elif tab_count >= 1 and (tab_ratio >= 0.45 or (tab_count >= 2 and draw_count >= 40)):
        page_class = DocumentClass.TABLE_FORM
        page_constraint = PageConstraint.SOFT
        evidence.append(f"Dominant table structure ({tab_count} tables, table_area_ratio={tab_ratio:.2f}, drawings={draw_count})")
        confidence = 0.92

    # Case 4: Visual Diagram (many drawings, curves, connectors, low paragraph text)
    elif draw_count >= 35 and par_ratio < 0.25 and img_count < 3:
        page_class = DocumentClass.VISUAL_DIAGRAM
        page_constraint = PageConstraint.SOFT
        evidence.append(f"High vector drawing density ({draw_count} drawings, curves/lines) with low paragraph text")
        confidence = 0.90

    # Case 5: Certificate / Fixed Admin Card (single page or rigid border frames with tight fields)
    elif metrics["drawing_rect_count"] >= 4 and chars < 600 and img_count <= 1:
        page_class = DocumentClass.FIXED_LAYOUT
        page_constraint = PageConstraint.HARD
        evidence.append(f"Fixed border frame rects ({metrics['drawing_rect_count']}), low char count ({chars}), rigid certificate structure")
        confidence = 0.92

    # Case 6: Mixed
    else:
        page_class = DocumentClass.MIXED
        page_constraint = PageConstraint.SOFT
        evidence.append(f"Heterogeneous content: {chars} chars, {img_count} imgs, {draw_count} draws, {tab_count} tables")
        confidence = 0.88

    # Segment regions on this page
    regions = segment_page_regions(page, page_idx, page_class)

    return PageProfile(
        page_idx=page_idx,
        page_number=page_idx + 1,
        page_class=page_class,
        page_constraint=page_constraint,
        width=metrics["page_w"],
        height=metrics["page_h"],
        margins=metrics["margins"],
        regions=regions,
        confidence=confidence,
        evidence=evidence,
        metrics=metrics,
    )


def segment_page_regions(page: pymupdf.Page, page_idx: int, page_class: DocumentClass) -> List[RegionProfile]:
    """Segment page into structured regions with roles and layout classes."""
    regions: List[RegionProfile] = []
    page_w = page.rect.width
    page_h = page.rect.height

    # 1. Detect Tables as separate regions
    table_bboxes: List[Tuple[float, float, float, float]] = []
    try:
        if hasattr(page, "find_tables"):
            tabs = page.find_tables()
            if tabs and hasattr(tabs, "tables"):
                for idx, t in enumerate(tabs.tables):
                    tb = list(t.bbox)
                    table_bboxes.append(tuple(tb))
                    rows_cnt = getattr(t, "row_count", len(getattr(t, "rows", [])))
                    cols_cnt = getattr(t, "col_count", len(getattr(t, "columns", [])))
                    regions.append(RegionProfile(
                        region_id=f"p{page_idx}_tab{idx}",
                        region_class=DocumentClass.TABLE_FORM,
                        bbox=tb,
                        roles=[StructuralRole.TABLE_HEADER, StructuralRole.TABLE_CELL],
                        has_tables=True,
                        evidence=[f"Table detector found {rows_cnt} rows, {cols_cnt} cols"],
                    ))
    except Exception as e:
        pass

    # 2. Detect Images as VisualGroup regions (image + nearby caption)
    image_bboxes: List[Tuple[float, float, float, float]] = []
    try:
        for idx, img in enumerate(page.get_images()):
            rects = page.get_image_rects(img[0])
            for r_idx, r in enumerate(rects):
                ib = [r.x0, r.y0, r.x1, r.y1]
                image_bboxes.append(tuple(ib))
                regions.append(RegionProfile(
                    region_id=f"p{page_idx}_img{idx}_{r_idx}",
                    region_class=DocumentClass.IMAGE_GROUP,
                    bbox=ib,
                    roles=[StructuralRole.CAPTION],
                    has_images=True,
                    evidence=[f"Image {idx} rect [{r.x0:.1f}, {r.y0:.1f}, {r.x1:.1f}, {r.y1:.1f}]"],
                ))
    except Exception:
        pass

    # 3. Text blocks segmentation
    text_blocks = [b for b in page.get_text("blocks") if b[4].strip() and b[6] == 0]
    for idx, b in enumerate(text_blocks):
        bx0, by0, bx1, by1, text = b[0], b[1], b[2], b[3], b[4].strip()
        b_rect = pymupdf.Rect(bx0, by0, bx1, by1)

        # Check if inside already identified table or image
        inside_tab = any(b_rect.intersects(pymupdf.Rect(tb)) for tb in table_bboxes)
        if inside_tab:
            continue

        # Header detection (top 50pt)
        if by1 < 55.0 and len(text) < 100:
            regions.append(RegionProfile(
                region_id=f"p{page_idx}_hdr{idx}",
                region_class=DocumentClass.FIXED_LAYOUT,
                bbox=[bx0, by0, bx1, by1],
                roles=[StructuralRole.HEADER],
                blocks_count=1,
                evidence=["Top running header"],
            ))
            continue

        # Footer detection (bottom 50pt)
        if by0 > page_h - 55.0 and len(text) < 50:
            regions.append(RegionProfile(
                region_id=f"p{page_idx}_ftr{idx}",
                region_class=DocumentClass.FIXED_LAYOUT,
                bbox=[bx0, by0, bx1, by1],
                roles=[StructuralRole.FOOTER],
                blocks_count=1,
                evidence=["Bottom running footer/page number"],
            ))
            continue

        # Heading vs Paragraph
        role = StructuralRole.BODY_PARAGRAPH
        if (by1 - by0) < 30.0 and len(text) < 80:
            # Check for title/heading patterns
            if any(text.startswith(pfx) for pfx in ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.",
                                                    "第", "一、", "二、", "三、", "四、", "I.", "II.", "III.")):
                role = StructuralRole.HEADING
            elif idx == 0 and by0 < 150.0:
                role = StructuralRole.TITLE

        if page_class == DocumentClass.FIXED_LAYOUT:
            r_class = DocumentClass.FIXED_LAYOUT
        elif role in (StructuralRole.BODY_PARAGRAPH, StructuralRole.HEADING, StructuralRole.TITLE):
            r_class = DocumentClass.TEXT_FLOW
        else:
            r_class = DocumentClass.TEXT_FLOW if page_class in (DocumentClass.TEXT_FLOW, DocumentClass.MIXED) else page_class
        regions.append(RegionProfile(
            region_id=f"p{page_idx}_txt{idx}",
            region_class=r_class,
            bbox=[bx0, by0, bx1, by1],
            roles=[role],
            blocks_count=1,
            evidence=[f"Text block ({role.value}) with {len(text)} chars"],
        ))

    return regions


def classify_document(doc_path_or_fitz: str | Path | pymupdf.Document) -> LayoutProfile:
    """Perform comprehensive 3-level classification on an entire document."""
    if isinstance(doc_path_or_fitz, (str, Path)):
        doc = pymupdf.open(str(doc_path_or_fitz))
        should_close = True
    else:
        doc = doc_path_or_fitz
        should_close = False

    try:
        page_count = len(doc)
        page_profiles: List[PageProfile] = []
        evidence: List[str] = []
        ambiguous: List[str] = []

        total_text_flow_pages = 0
        total_image_pages = 0
        total_table_pages = 0
        total_diagram_pages = 0
        total_fixed_pages = 0
        total_mixed_pages = 0

        total_chars_all = 0
        total_images_all = 0
        total_drawings_all = 0

        for p_idx in range(page_count):
            p = doc[p_idx]
            prof = classify_page(p, p_idx)
            page_profiles.append(prof)

            # Aggregate stats
            p_class = prof.page_class
            if p_class == DocumentClass.TEXT_FLOW:
                total_text_flow_pages += 1
            elif p_class == DocumentClass.IMAGE_GROUP:
                total_image_pages += 1
            elif p_class == DocumentClass.TABLE_FORM:
                total_table_pages += 1
            elif p_class == DocumentClass.VISUAL_DIAGRAM:
                total_diagram_pages += 1
            elif p_class == DocumentClass.FIXED_LAYOUT:
                total_fixed_pages += 1
            else:
                total_mixed_pages += 1

            total_chars_all += prof.metrics.get("total_chars", 0)
            total_images_all += prof.metrics.get("image_count", 0)
            total_drawings_all += prof.metrics.get("drawing_count", 0)

        # Document-level aggregation logic
        flow_ratio = total_text_flow_pages / max(page_count, 1)

        # Primary Rule 1: High consistency text-heavy document (e.g. Guideline / Manual / Report)
        if flow_ratio >= 0.70 and total_images_all == 0:
            doc_class = DocumentClass.TEXT_FLOW
            page_constraint = PageConstraint.FREE
            evidence.append(f"Document dominated by text flow ({total_text_flow_pages}/{page_count} pages, {total_chars_all} chars)")
            evidence.append("Zero images across entire document; pagination constraint set to FREE for natural reflow")
            confidence = 0.96

        # Primary Rule 2: Single-page fixed certificate or card
        elif page_count == 1 and total_fixed_pages == 1:
            doc_class = DocumentClass.FIXED_LAYOUT
            page_constraint = PageConstraint.HARD
            evidence.append("Single page fixed administrative layout; constraint set to HARD")
            confidence = 0.90

        # Primary Rule 3: Uniform Visual diagram or image heavy document (>60% of pages)
        elif (total_image_pages + total_diagram_pages) / max(page_count, 1) >= 0.65:
            doc_class = DocumentClass.VISUAL_DIAGRAM if total_diagram_pages >= total_image_pages else DocumentClass.IMAGE_GROUP
            page_constraint = PageConstraint.SOFT
            evidence.append(f"Visual heavy document ({total_image_pages} img pages, {total_diagram_pages} diagram pages, {total_images_all} total imgs)")
            confidence = 0.92

        # Primary Rule 4: Mixed document with multiple modes (e.g. JSTB, Kitasato)
        else:
            doc_class = DocumentClass.MIXED
            page_constraint = PageConstraint.SOFT
            evidence.append(f"Mixed document across {page_count} pages ({total_text_flow_pages} flow, {total_image_pages} img, {total_table_pages} table, {total_diagram_pages} diagram, {total_mixed_pages} mixed)")
            evidence.append("Pagination constraint set to SOFT to preserve visual topology while allowing flow flexibility")
            confidence = 0.91

            if flow_ratio > 0.4:
                ambiguous.append("Contains substantial flowing text alongside visual/table elements; regional routing active")

        return LayoutProfile(
            document_class=doc_class,
            page_constraint=page_constraint,
            page_count=page_count,
            page_profiles=page_profiles,
            confidence=confidence,
            evidence=evidence,
            ambiguous_features=ambiguous,
        )

    finally:
        if should_close:
            doc.close()
