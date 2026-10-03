"""Deterministic Semantic Reconstructor for TEXT_FLOW and Hybrid PDF Documents.

Extracts physical PDF spans, lines, and geometries, and reconstructs the logical
document structure (LogicalDocument) prior to translation and flow composition.

Conforms to AIWF Translation Upgrade #1.7:
- Part 7: Semantic Reconstruction
- Part 8: Paragraph Reconstruction & Boundary Detection
- Part 9: Cross-Page Paragraph Continuation
- Part 10: Heading Hierarchy & Invariant Protection
- Part 11: Lists and Definition Lists
- Part 12: Inline Scientific Grouping (Na+, K+, Cl-, HCO3-, units)
- Part 13: Formula Blocks
- Part 14: Tables inside TEXT_FLOW
- Part 15: Header / Footer / Page Number Isolation
- Part 31: Confidence & Ambiguity Handling
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pymupdf

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    from layout.logical_document import (
        ConfidenceLevel,
        InlineToken,
        LogicalDocument,
        LogicalSection,
        LogicalTable,
        LogicalUnit,
        StructuralRole,
    )
except ImportError:
    from logical_document import (
        ConfidenceLevel,
        InlineToken,
        LogicalDocument,
        LogicalSection,
        LogicalTable,
        LogicalUnit,
        StructuralRole,
    )


# Inline scientific patterns that must not be fragmented
SCIENTIFIC_ION_PATTERN = re.compile(
    r"\b(Na|K|Cl|Ca|Mg|HCO3|CO3|SO4|PO4|NH4|H|OH)[\+\-－\d\±\^]*\b|"
    r"(mmol/L|mg/dL|mL/min|mmHg|mEq/L|μmol/L|mol/L|g/dL|μg/mL|CFU/mL|pg/mL|%|pH|°C)\b"
)

# Heading patterns
HEADING_L1_REGEX = re.compile(
    r"^(\d+\.\s+[^\d\.]|^第\s*\d+\s*[章条節]|^序文$|^参考文献$|^付則$|^目次$|^はじめに$|^総論$|^各論$)"
)
HEADING_L2_REGEX = re.compile(r"^\d+\.\d+\s+[^\d\.]")
HEADING_L3_REGEX = re.compile(r"^\d+\.\d+\.\d+\s+")

# Definition list / Abbreviation / Key-Value pattern: e.g. "HD: 血液透析", "JCCRM: ...", "【対象者】...", "測定試料："
DEFINITION_REGEX = re.compile(
    r"^([A-Z0-9\-\/]{2,10}\s*[:：]|【[^】]+】|注[:：]?|\d+\)\s+|\(\d+\)\s+|[^\n:：]{2,25}：|[^\n:：]{2,25}:(?:\s+|$))\s*(.*)"
)

# Bullet markers
BULLET_REGEX = re.compile(r"^([・•\-\*○■◆▶])\s*(.*)")

# Formula patterns (strict standalone equations, never prose)
FORMULA_REGEX = re.compile(
    r"^(Cm\s*=|B\s*=|M\s*-|偏り\s*（B）|ts/√n\s*=|=[（\(]B|[A-Za-z]\s*=\s*[\d\.\+\-\{\(]|.*（Cm）\s*=|^\s*=\s*（B\s*の符号）)"
)
PROSE_INDICATORS = re.compile(r"(の平均値と|を設定する|とする|は、|について|である|による|において|を行う)")


class SemanticReconstructor:
    """Reconstructs logical document model from physical PDF pages."""

    def __init__(self, source_pdf: str | Path):
        self.source_pdf = Path(source_pdf)
        self.doc = pymupdf.open(str(self.source_pdf))
        self.page_count = len(self.doc)

    def reconstruct(self) -> LogicalDocument:
        """Executes full semantic reconstruction pipeline across all pages."""
        raw_pages_data = []

        # 1. Page-level extraction of raw lines and tables
        for p_idx in range(self.page_count):
            p_data = self._extract_page_primitives(p_idx)
            raw_pages_data.append(p_data)

        # 2. Global running header & footer detection
        headers, footers, page_numbers = self._detect_recurring_headers_footers(raw_pages_data)

        # 3. Document Title / Subtitle / Author extraction (Page 1)
        title, subtitle, authors = self._detect_title_metadata(raw_pages_data[0] if raw_pages_data else None)

        # 4. Process body content per page with span fusing & inline scientific grouping
        all_units: List[Union[LogicalUnit, LogicalTable]] = []
        unit_counter = 0

        for p_idx, p_data in enumerate(raw_pages_data):
            # Tables on this page
            for tbl in p_data["tables"]:
                all_units.append(tbl)

            # Process prose lines on this page
            page_units = self._reconstruct_page_units(
                p_data=p_data,
                p_idx=p_idx,
                excluded_line_ids=headers | footers | page_numbers | (title["ids"] if title else set()),
                unit_counter_start=unit_counter,
            )
            unit_counter += len(page_units)
            all_units.extend(page_units)

        # 5. Cross-page paragraph continuation (Section 9)
        all_units = self._merge_cross_page_paragraphs(all_units)

        # 6. Build sections from heading hierarchy (Section 10)
        sections = self._build_sections(all_units)

        # 7. Construct final LogicalDocument
        log_doc = LogicalDocument(
            document_id=f"doc_{self.source_pdf.stem}",
            source_pdf=str(self.source_pdf),
            title=title["unit"] if title else None,
            subtitle=subtitle["unit"] if subtitle else None,
            authors=[a["unit"] for a in authors],
            running_headers=[h["unit"] for h in raw_pages_data[0].get("running_headers", [])],
            running_footers=[f["unit"] for f in raw_pages_data[0].get("running_footers", [])],
            sections=sections,
            units=all_units,
            metadata={
                "source_page_count": self.page_count,
                "reconstruction_strategy": "NATIVE_SEMANTIC_REFLOW_1_7",
            },
        )

        return log_doc

    def _extract_page_primitives(self, page_idx: int) -> Dict[str, Any]:
        """Extracts structured lines, spans, and tables from a single page."""
        page = self.doc[page_idx]
        page_w = page.rect.width
        page_h = page.rect.height

        # A. Detect Tables via find_tables()
        tables: List[LogicalTable] = []
        table_bboxes: List[Tuple[float, float, float, float]] = []

        try:
            if hasattr(page, "find_tables"):
                found_tables = page.find_tables()
                if found_tables and hasattr(found_tables, "tables"):
                    for t_idx, t in enumerate(found_tables.tables):
                        tb = tuple(t.bbox)
                        t_w = tb[2] - tb[0]
                        rows_data = t.extract()
                        if not rows_data or len(rows_data) < 2 or t_w < 120.0:
                            continue
                        # Filter out sparse diagram grids (density check)
                        total_cells = len(rows_data) * len(rows_data[0])
                        filled_cells = sum(1 for r in rows_data for c in r if c and str(c).strip())
                        if (filled_cells / total_cells) < 0.35:
                            continue

                        table_bboxes.append(tb)
                        hdr = [str(c or "").strip() for c in rows_data[0]]
                        body_rows = [[str(c or "").strip() for c in r] for r in rows_data[1:]]
                        tables.append(LogicalTable(
                            table_id=f"p{page_idx}_tbl{t_idx}",
                            source_page=page_idx + 1,
                            bbox=tb,
                            headers=[hdr],
                            rows=body_rows,
                            confidence=ConfidenceLevel.HIGH,
                        ))
        except Exception:
            pass

        # B. Extract Dict Spans
        d = page.get_text("dict")
        raw_lines = []
        line_id_counter = 0

        for b in d.get("blocks", []):
            if "lines" not in b or b.get("type", 0) != 0:
                continue

            for l in b.get("lines", []):
                l_bbox = tuple(l["bbox"])
                # Exclude lines entirely inside detected tables
                if any(self._is_inside_bbox(l_bbox, tb) for tb in table_bboxes):
                    continue

                spans = l.get("spans", [])
                if not spans:
                    continue

                line_text = "".join(s.get("text", "") for s in spans).strip()
                if not line_text:
                    continue

                # Median font size and style flags
                sizes = [s.get("size", 10.0) for s in spans]
                avg_size = sum(sizes) / len(sizes) if sizes else 10.0
                is_bold = any((s.get("flags", 0) & (1 << 4) != 0) or "bold" in s.get("font", "").lower() for s in spans)
                is_italic = any((s.get("flags", 0) & (1 << 1) != 0) or "italic" in s.get("font", "").lower() for s in spans)
                font_name = spans[0].get("font", "Arial") if spans else "Arial"

                raw_lines.append({
                    "line_id": f"p{page_idx}_l{line_id_counter}",
                    "bbox": l_bbox,
                    "text": line_text,
                    "spans": spans,
                    "font_size": avg_size,
                    "font_family": font_name,
                    "is_bold": is_bold,
                    "is_italic": is_italic,
                    "page_idx": page_idx,
                })
                line_id_counter += 1

        # C. Fuse horizontal adjacent fragments on the same baseline (Section 12)
        fused_lines = self._fuse_horizontal_fragments(raw_lines)

        # Estimate typical body font size & line gap
        body_sizes = [l["font_size"] for l in fused_lines if 8.0 <= l["font_size"] <= 12.0]
        typical_size = sorted(body_sizes)[len(body_sizes) // 2] if body_sizes else 10.0

        line_gaps = []
        for i in range(len(fused_lines) - 1):
            gap = fused_lines[i + 1]["bbox"][1] - fused_lines[i]["bbox"][3]
            if 0 < gap < 20:
                line_gaps.append(gap)
        typical_gap = sorted(line_gaps)[len(line_gaps) // 2] if line_gaps else 4.0

        return {
            "page_idx": page_idx,
            "page_w": page_w,
            "page_h": page_h,
            "lines": fused_lines,
            "tables": tables,
            "typical_font_size": typical_size,
            "typical_line_gap": typical_gap,
        }

    def _fuse_horizontal_fragments(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fuses same-row fragments that PyMuPDF split across blocks.
        
        Uses vertical center clustering and horizontal sorting to robustly
        reconnect split superscripts/subscripts (e.g. Na+, HCO3-, Cl-).
        """
        if not lines:
            return []

        # Sort lines by vertical center first
        def line_center_y(l):
            return (l["bbox"][1] + l["bbox"][3]) / 2.0

        sorted_lines = sorted(lines, key=line_center_y)

        # Cluster into rows where vertical center difference < 3.5pt
        rows: List[List[Dict[str, Any]]] = []
        curr_row: List[Dict[str, Any]] = []
        curr_row_center = 0.0

        for l in sorted_lines:
            c_y = line_center_y(l)
            if not curr_row:
                curr_row = [l]
                curr_row_center = c_y
            elif abs(c_y - curr_row_center) <= 3.8:
                curr_row.append(l)
                # Update running average center
                curr_row_center = sum(line_center_y(x) for x in curr_row) / len(curr_row)
            else:
                rows.append(curr_row)
                curr_row = [l]
                curr_row_center = c_y

        if curr_row:
            rows.append(curr_row)

        fused: List[Dict[str, Any]] = []

        # Process each row: sort elements left-to-right (by x0)
        for row in rows:
            row.sort(key=lambda l: l["bbox"][0])
            i = 0
            while i < len(row):
                curr = dict(row[i])
                curr_spans = list(curr["spans"])

                j = i + 1
                while j < len(row):
                    nxt = row[j]
                    # Check horizontal adjacency: gap < 15pt and not overlapping backwards
                    horiz_gap = nxt["bbox"][0] - curr["bbox"][2]
                    if -2.0 <= horiz_gap <= 14.0:
                        nxt_text = nxt["text"].strip()
                        # Seamlessly attach if punctuation, sign, or subscript
                        if (
                            nxt_text.startswith(("-", "－", "+", "±", ")", "）", "、", "。", ":", "：", "]", "】"))
                            or curr["text"].endswith(("-", "－", "+", "±", "(", "（", "[", "【", "・", "•"))
                            or horiz_gap <= 1.5
                        ):
                            curr["text"] = curr["text"] + nxt["text"]
                        else:
                            curr["text"] = curr["text"] + " " + nxt["text"]

                        curr["bbox"] = (
                            min(curr["bbox"][0], nxt["bbox"][0]),
                            min(curr["bbox"][1], nxt["bbox"][1]),
                            max(curr["bbox"][2], nxt["bbox"][2]),
                            max(curr["bbox"][3], nxt["bbox"][3]),
                        )
                        curr_spans.extend(nxt["spans"])
                        j += 1
                    else:
                        break

                curr["spans"] = curr_spans
                fused.append(curr)
                i = j

        # Final sort in reading order (top-to-bottom, then left-to-right)
        fused.sort(key=lambda l: (round(l["bbox"][1], 1), round(l["bbox"][0], 1)))
        return fused

    def _detect_recurring_headers_footers(self, pages_data: List[Dict[str, Any]]) -> Tuple[set, set, set]:
        """Detects recurring running headers, footers, and page numbers."""
        headers = set()
        footers = set()
        page_numbers = set()

        for p_data in pages_data:
            page_h = p_data["page_h"]
            for l in p_data["lines"]:
                lid = l["line_id"]
                txt = l["text"].strip()
                y0, y1 = l["bbox"][1], l["bbox"][3]

                # Standalone page number at bottom or top
                if txt.isdigit() and len(txt) <= 3:
                    if y1 > page_h - 85 or y0 < 75:
                        page_numbers.add(lid)
                        continue
                if re.match(r"^[-－\s]*\d+[-－\s]*$", txt) and len(txt) <= 6:
                    if y1 > page_h - 85 or y0 < 75:
                        page_numbers.add(lid)
                        continue

                # Running header: near top margin (< 65pt)
                if y0 < 65 and len(txt) < 80:
                    headers.add(lid)
                    continue

                # Running footer: near bottom margin (> page_h - 60pt)
                if y1 > page_h - 60 and len(txt) < 80:
                    footers.add(lid)
                    continue

        return headers, footers, page_numbers

    def _detect_title_metadata(self, p1_data: Optional[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extracts title, subtitle, author from Page 1 (bounded to top header zone)."""
        if not p1_data:
            return None, None, []

        title_info = None
        subtitle_info = None
        authors_info = []

        # Bound strictly to the title header region (y < 185)
        top_lines = [l for l in p1_data["lines"] if l["bbox"][1] < 185]
        top_lines.sort(key=lambda l: l["bbox"][1])

        title_ids = set()

        for l in top_lines:
            txt = l["text"].strip()
            sz = l["font_size"]

            # Stop if hitting section headers or narrative
            if "序文" in txt or re.match(r"^\d+\.", txt) or len(txt) > 50 or "は、" in txt:
                break

            # Title is typically largest font at top
            if sz >= 13.0 and not title_info:
                title_info = {
                    "ids": {l["line_id"]},
                    "unit": LogicalUnit(
                        unit_id="doc_title",
                        role=StructuralRole.TITLE,
                        text=txt,
                        source_pages=[1],
                        source_bboxes=[l["bbox"]],
                        font_size=sz,
                        font_weight="bold",
                        alignment="center",
                    )
                }
                title_ids.add(l["line_id"])
            elif (sz >= 11.0 or "第" in txt or "版" in txt) and not subtitle_info and title_info:
                subtitle_info = {
                    "ids": {l["line_id"]},
                    "unit": LogicalUnit(
                        unit_id="doc_subtitle",
                        role=StructuralRole.SUBTITLE,
                        text=txt,
                        source_pages=[1],
                        source_bboxes=[l["bbox"]],
                        font_size=sz,
                        font_weight="bold",
                        alignment="center",
                    )
                }
                title_ids.add(l["line_id"])
            elif ("学会" in txt or "一般社団法人" in txt or "協会" in txt or "著者" in txt) and not "は、" in txt and len(txt) < 40 and title_info:
                authors_info.append({
                    "ids": {l["line_id"]},
                    "unit": LogicalUnit(
                        unit_id=f"doc_author_{len(authors_info)}",
                        role=StructuralRole.AUTHOR,
                        text=txt,
                        source_pages=[1],
                        source_bboxes=[l["bbox"]],
                        font_size=sz,
                        font_weight="regular",
                        alignment="center",
                    )
                })
                title_ids.add(l["line_id"])

        if title_info:
            title_info["ids"] = title_ids

        return title_info, subtitle_info, authors_info

    def _reconstruct_page_units(
        self,
        p_data: Dict[str, Any],
        p_idx: int,
        excluded_line_ids: set,
        unit_counter_start: int,
    ) -> List[LogicalUnit]:
        """Reconstructs logical units (Headings, Paragraphs, Lists) on a page."""
        lines = [l for l in p_data["lines"] if l["line_id"] not in excluded_line_ids]
        if not lines:
            return []

        # Sort lines strictly in reading order
        lines.sort(key=lambda l: (round(l["bbox"][1], 1), round(l["bbox"][0], 1)))

        typical_size = p_data["typical_font_size"]
        typical_gap = p_data["typical_line_gap"]

        units: List[LogicalUnit] = []
        u_idx = unit_counter_start

        # State machine for grouping consecutive lines into paragraphs/lists
        curr_role: Optional[StructuralRole] = None
        curr_lines: List[Dict[str, Any]] = []
        curr_marker: Optional[str] = None
        curr_level: int = 0

        def flush_current():
            nonlocal curr_role, curr_lines, curr_marker, curr_level, u_idx
            if not curr_lines or not curr_role:
                curr_lines = []
                curr_role = None
                curr_marker = None
                return

            # Smart join for lines (handles CJK, signs, and punctuation without artificial spaces)
            if not curr_lines:
                full_text = ""
            else:
                full_text = curr_lines[0]["text"].strip()
                for l_item in curr_lines[1:]:
                    t_item = l_item["text"].strip()
                    if not t_item:
                        continue
                    prev_is_cjk = bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]$", full_text))
                    curr_is_cjk = bool(re.search(r"^[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", t_item))
                    is_punct = (t_item[0] in ("-", "－", "+", "±", "、", "。", ")", "）", "]", "】", ":", "：")) or (full_text[-1] in ("(", "（", "[", "【"))
                    if (prev_is_cjk and curr_is_cjk) or is_punct:
                        full_text += t_item
                    else:
                        full_text += " " + t_item
            full_text = re.sub(r"\s+", " ", full_text).strip()

            # Preserve chemical tokens
            tokens = self._extract_inline_tokens(full_text)

            bboxes = [l["bbox"] for l in curr_lines]
            avg_sz = sum(l["font_size"] for l in curr_lines) / len(curr_lines)
            is_bold = any(l["is_bold"] for l in curr_lines)

            # Assign confidence
            conf = ConfidenceLevel.HIGH
            if len(curr_lines) == 1 and curr_role == StructuralRole.BODY_PARAGRAPH and len(full_text) < 30:
                conf = ConfidenceLevel.MEDIUM

            unit = LogicalUnit(
                unit_id=f"u_{u_idx}",
                role=curr_role,
                text=full_text,
                tokens=tokens,
                source_pages=[p_idx + 1],
                source_bboxes=bboxes,
                font_size=round(avg_sz, 1),
                font_weight="bold" if is_bold else "regular",
                list_marker=curr_marker,
                level=curr_level,
                confidence=conf,
                merge_reasons=[f"merged_{len(curr_lines)}_lines"],
                source_fragments=curr_lines,
            )
            units.append(unit)
            u_idx += 1

            curr_lines = []
            curr_role = None
            curr_marker = None
            curr_level = 0

        for idx, line in enumerate(lines):
            txt = line["text"].strip()
            sz = line["font_size"]
            is_bold = line["is_bold"]

            # 1. Heading check (Invariant: never merge with body)
            is_h1 = bool(HEADING_L1_REGEX.match(txt))
            is_h2 = bool(HEADING_L2_REGEX.match(txt))
            is_h3 = bool(HEADING_L3_REGEX.match(txt))

            if is_h1 or (sz >= typical_size * 1.20 and len(txt) < 50):
                flush_current()
                curr_role = StructuralRole.HEADING_1
                curr_level = 1
                curr_lines.append(line)
                flush_current()
                continue
            elif is_h2 or (is_bold and sz >= typical_size * 1.08 and len(txt) < 60 and not DEFINITION_REGEX.match(txt)):
                flush_current()
                curr_role = StructuralRole.HEADING_2
                curr_level = 2
                curr_lines.append(line)
                flush_current()
                continue
            elif is_h3:
                flush_current()
                curr_role = StructuralRole.HEADING_3
                curr_level = 3
                curr_lines.append(line)
                flush_current()
                continue

            # 2. Line continuation for open punctuation (brackets, comma, etc.)
            if curr_lines:
                prev_txt = curr_lines[-1]["text"].strip()
                if prev_txt.endswith((",", "，", "(", "（", "{", "｛", "[", "【")) and len(txt) < 40 and not is_h1 and not is_h2:
                    curr_lines.append(line)
                    continue

            # 3. Formula block check
            if FORMULA_REGEX.search(txt) and ("=" in txt or "Cm" in txt or "√" in txt) and len(txt) < 80 and not PROSE_INDICATORS.search(txt):
                if curr_role == StructuralRole.FORMULA_BLOCK:
                    curr_lines.append(line)
                    continue
                else:
                    flush_current()
                    curr_role = StructuralRole.FORMULA_BLOCK
                    curr_lines.append(line)
                    continue

            # 4. Definition item / List item check
            def_match = DEFINITION_REGEX.match(txt)
            bullet_match = BULLET_REGEX.match(txt)

            if def_match and not (curr_role == StructuralRole.FORMULA_BLOCK and "=" in txt):
                flush_current()
                curr_role = StructuralRole.DEFINITION_ITEM
                curr_marker = def_match.group(1).split(":")[0].strip() if ":" in def_match.group(1) else def_match.group(1).strip()
                curr_lines.append(line)
                continue
            elif bullet_match:
                flush_current()
                curr_role = StructuralRole.LIST_ITEM
                curr_marker = bullet_match.group(1)
                curr_lines.append(line)
                continue

            # 5. Body paragraph continuation vs boundary
            if curr_role in (StructuralRole.LIST_ITEM, StructuralRole.DEFINITION_ITEM):
                # Check if continuation of the list item
                gap = line["bbox"][1] - curr_lines[-1]["bbox"][3]
                if gap <= typical_gap * 1.8 and abs(sz - curr_lines[-1]["font_size"]) < 1.0:
                    curr_lines.append(line)
                    continue
                else:
                    flush_current()

            if curr_role == StructuralRole.BODY_PARAGRAPH:
                gap = line["bbox"][1] - curr_lines[-1]["bbox"][3]
                prev_text = curr_lines[-1]["text"].strip()
                is_prev_full_stop = prev_text.endswith("。") or prev_text.endswith(".")
                is_indent = line["bbox"][0] > curr_lines[0]["bbox"][0] + typical_size * 0.7

                # Boundary condition: larger vertical gap or explicit indentation
                if gap > typical_gap * 1.8 or (is_prev_full_stop and is_indent):
                    flush_current()
                    curr_role = StructuralRole.BODY_PARAGRAPH
                    curr_lines.append(line)
                else:
                    curr_lines.append(line)
            else:
                flush_current()
                curr_role = StructuralRole.BODY_PARAGRAPH
                curr_lines.append(line)

        flush_current()
        return units

    def _merge_cross_page_paragraphs(self, units: List[Union[LogicalUnit, LogicalTable]]) -> List[Union[LogicalUnit, LogicalTable]]:
        """Merges body paragraphs that naturally continue across source page boundaries (Section 9)."""
        merged: List[Union[LogicalUnit, LogicalTable]] = []
        i = 0

        while i < len(units):
            curr = units[i]
            if not isinstance(curr, LogicalUnit) or curr.role != StructuralRole.BODY_PARAGRAPH:
                merged.append(curr)
                i += 1
                continue

            # Look ahead to see if the next unit is on the very next page and is a continuation
            if i + 1 < len(units):
                nxt = units[i + 1]
                if isinstance(nxt, LogicalUnit) and nxt.role == StructuralRole.BODY_PARAGRAPH:
                    curr_last_p = curr.source_pages[-1] if curr.source_pages else 0
                    nxt_first_p = nxt.source_pages[0] if nxt.source_pages else 0

                    if nxt_first_p == curr_last_p + 1:
                        # Check sentence continuation: curr text does NOT end with paragraph terminator
                        ends_mid_sentence = not (curr.text.endswith("。") or curr.text.endswith(".") or curr.text.endswith("：") or curr.text.endswith(":"))
                        same_size = abs(curr.font_size - nxt.font_size) < 1.0

                        if ends_mid_sentence and same_size:
                            # Merge nxt into curr
                            curr.text = (curr.text + " " + nxt.text).strip()
                            curr.tokens.extend(nxt.tokens)
                            curr.source_pages.extend(nxt.source_pages)
                            curr.source_bboxes.extend(nxt.source_bboxes)
                            curr.merge_reasons.append(f"cross_page_continuation_p{curr_last_p}_p{nxt_first_p}")
                            curr.source_fragments.extend(nxt.source_fragments)
                            i += 2
                            merged.append(curr)
                            continue

            merged.append(curr)
            i += 1

        return merged

    def _build_sections(self, units: List[Union[LogicalUnit, LogicalTable]]) -> List[LogicalSection]:
        """Groups units into logical document sections based on headings."""
        sections: List[LogicalSection] = []
        curr_sec: Optional[LogicalSection] = None
        sec_idx = 0

        for u in units:
            if isinstance(u, LogicalUnit) and u.role in (StructuralRole.HEADING_1, StructuralRole.HEADING_2):
                if curr_sec:
                    sections.append(curr_sec)
                curr_sec = LogicalSection(
                    section_id=f"sec_{sec_idx}",
                    heading=u,
                    units=[],
                )
                sec_idx += 1
            else:
                if not curr_sec:
                    curr_sec = LogicalSection(
                        section_id=f"sec_preamble",
                        heading=None,
                        units=[],
                    )
                curr_sec.units.append(u)

        if curr_sec:
            sections.append(curr_sec)

        return sections

    def _extract_inline_tokens(self, text: str) -> List[InlineToken]:
        """Extracts scientific tokens preserving subscripts, superscripts, and units."""
        tokens = []
        # Find scientific patterns
        matches = list(SCIENTIFIC_ION_PATTERN.finditer(text))
        if not matches:
            return [InlineToken(base_text=text)]

        last_pos = 0
        for m in matches:
            start, end = m.span()
            if start > last_pos:
                tokens.append(InlineToken(base_text=text[last_pos:start]))

            match_text = m.group(0)
            # Parse sub / super: e.g. Na+ -> base Na, super +
            if "+" in match_text or "-" in match_text or "－" in match_text:
                parts = re.split(r"([\+\-－\d\±]+)", match_text)
                base = parts[0]
                sign = "".join(parts[1:])
                tokens.append(InlineToken(base_text=base, superscript=sign))
            elif match_text.startswith("HCO3"):
                tokens.append(InlineToken(base_text="HCO", subscript="3", superscript=match_text[4:]))
            else:
                tokens.append(InlineToken(base_text=match_text))

            last_pos = end

        if last_pos < len(text):
            tokens.append(InlineToken(base_text=text[last_pos:]))

        return tokens

    def _is_inside_bbox(self, inner: Tuple[float, float, float, float], outer: Tuple[float, float, float, float]) -> bool:
        """Tests if inner bbox is substantially contained inside outer bbox."""
        ix0, iy0, ix1, iy1 = inner
        ox0, oy0, ox1, oy1 = outer
        return (ix0 >= ox0 - 2.0) and (iy0 >= oy0 - 2.0) and (ix1 <= ox1 + 2.0) and (iy1 <= oy1 + 2.0)


def reconstruct_semantic_document(source_pdf_path: str | Path) -> LogicalDocument:
    """Convenience entry point for semantic document reconstruction."""
    reconstructor = SemanticReconstructor(source_pdf_path)
    return reconstructor.reconstruct()
