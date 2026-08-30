#!/usr/bin/env python3
"""Extract structured document blocks (headings, paragraphs, lists, tables) from PDF, DOCX, MD, or TXT.

Enhanced with:
- DocStudio-inspired table handling (meta table detection, cross-page merging)
- Hybrid table extraction: PyMuPDF (fast) + Docling TableFormer (accurate fallback)
- Empty cell normalization (None → "")
- Ordered list detection
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def extract_from_markdown(md_path: Path) -> list[dict]:
    """Extract semantic blocks from a Markdown document."""
    with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    blocks = []
    lines = text.split("\n")
    i = 0
    total = len(lines)

    while i < total:
        line = lines[i].strip()

        # Skip empty lines, page markers, and HTML font comments
        if not line or line.startswith("<!--") or line.startswith("<div") or line.startswith("</div>") or line.startswith("<center>") or line.startswith("</center>"):
            i += 1
            continue

        # Horizontal rule
        if line in {"---", "***", "___"}:
            blocks.append({"type": "hr"})
            i += 1
            continue

        # Headings
        if line.startswith("# "):
            blocks.append({"type": "h1", "text": line[2:].strip()})
            i += 1
            continue
        elif line.startswith("## "):
            blocks.append({"type": "h2", "text": line[3:].strip()})
            i += 1
            continue
        elif line.startswith("### "):
            blocks.append({"type": "h3", "text": line[4:].strip()})
            i += 1
            continue

        # Blockquote
        if line.startswith(">"):
            quote_lines = [line[1:].strip()]
            i += 1
            while i < total and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append({"type": "blockquote", "text": "\n".join(quote_lines)})
            continue

        # Table
        if line.startswith("|") and "|" in line[1:]:
            table_lines = []
            while i < total and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            
            # Parse markdown table
            headers = []
            rows = []
            for t_idx, t_line in enumerate(table_lines):
                cells = [c.strip() for c in t_line.split("|")[1:-1]]
                if t_idx == 0:
                    headers = cells
                elif t_idx == 1 and all(set(c).issubset({"-", ":", " "}) for c in cells):
                    # Separator line
                    continue
                else:
                    rows.append(cells)
            
            if headers or rows:
                blocks.append({
                    "type": "table",
                    "headers": headers,
                    "rows": rows
                })
            continue

        # Unordered list (bullet points)
        if re.match(r"^[\-\*\•\□\☐\☑]\s+", line):
            ul_items = []
            while i < total and re.match(r"^[\-\*\•\□\☐\☑]\s+", lines[i].strip()):
                clean_item = re.sub(r"^[\-\*\•\□\☐\☑]\s+", "", lines[i].strip())
                ul_items.append(clean_item)
                i += 1
            blocks.append({"type": "ul", "items": ul_items})
            continue

        # Ordered list
        if re.match(r"^\d+[\.)\]]\s+", line):
            ol_items = []
            while i < total and re.match(r"^\d+[\.)\]]\s+", lines[i].strip()):
                clean_item = re.sub(r"^\d+[\.)\]]\s+", "", lines[i].strip())
                ol_items.append(clean_item)
                i += 1
            blocks.append({"type": "ol", "items": ol_items})
            continue

        # Normal Paragraph
        p_lines = [line]
        i += 1
        while i < total:
            next_l = lines[i].strip()
            if not next_l or next_l.startswith("#") or next_l.startswith("|") or next_l.startswith(">") or next_l in {"---", "***", "___"} or re.match(r"^[\-\*\•\□\☐\☑]\s+", next_l) or re.match(r"^\d+[\.)\]]\s+", next_l) or next_l.startswith("<!--"):
                break
            p_lines.append(next_l)
            i += 1
        
        full_p = " ".join(p_lines)
        if full_p:
            blocks.append({"type": "p", "text": full_p})

    return blocks


def extract_from_docx(docx_path: Path, table_mode: str = "auto") -> list[dict]:
    """Extract semantic blocks from a Word DOCX document.
    
    Uses TableExtractor for precise merge detection from OOXML structure.
    """
    from docx import Document
    doc = Document(docx_path)
    blocks = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        style_name = p.style.name.lower() if p.style else ""
        if "heading 1" in style_name:
            blocks.append({"type": "h1", "text": text})
        elif "heading 2" in style_name:
            blocks.append({"type": "h2", "text": text})
        elif "heading 3" in style_name:
            blocks.append({"type": "h3", "text": text})
        elif "list" in style_name or "bullet" in style_name:
            blocks.append({"type": "ul", "items": [text]})
        elif p.style and "quote" in p.style.name.lower():
            blocks.append({"type": "blockquote", "text": text})
        else:
            blocks.append({"type": "p", "text": text})

    # Use TableExtractor for precise merge detection
    try:
        from table_extractor import TableExtractor
        extractor = TableExtractor(mode=table_mode)
        extracted_tables = extractor.extract_tables_from_docx(docx_path)
        
        for et in extracted_tables:
            if _is_meta_table(et.headers, et.rows):
                meta_items = []
                for row in et.rows:
                    if len(row) >= 2 and (row[0].strip() or row[1].strip()):
                        meta_items.append({"label": row[0].strip(), "value": row[1].strip()})
                if meta_items:
                    blocks.append({"type": "meta_table", "items": meta_items})
            else:
                table_block = {
                    "type": "table",
                    "headers": et.headers,
                    "rows": et.rows
                }
                if et.merges:
                    table_block["merges"] = [
                        {"row": m.row, "col": m.col,
                         "rowspan": m.rowspan, "colspan": m.colspan,
                         "value": m.value}
                        for m in et.merges
                    ]
                blocks.append(table_block)
    except ImportError:
        log.warning("table_extractor not available, falling back to basic DOCX table extraction")
        for table in doc.tables:
            rows_data = []
            for row in table.rows:
                row_vals = [cell.text.strip() for cell in row.cells]
                rows_data.append(row_vals)
            if rows_data:
                headers = rows_data[0]
                rows = rows_data[1:]
                if _is_meta_table(headers, rows):
                    meta_items = []
                    for row in rows:
                        if len(row) >= 2 and (row[0].strip() or row[1].strip()):
                            meta_items.append({"label": row[0].strip(), "value": row[1].strip()})
                    if meta_items:
                        blocks.append({"type": "meta_table", "items": meta_items})
                else:
                    blocks.append({"type": "table", "headers": headers, "rows": rows})

    return blocks


# ──────────────────────────────────────────────────────────────────────
# DocStudio-inspired Table Helpers
# ──────────────────────────────────────────────────────────────────────

def _is_meta_table(headers: list[str], rows: list[list[str]]) -> bool:
    """Detect if a table is a meta/key-value table (2 columns: label | value).
    
    Inspired by DocStudio CertificatePage meta[] pattern — tables where
    the first column contains short labels and the second contains values.
    """
    if len(headers) != 2:
        return False
    # Meta tables are typically < 15 rows
    if len(rows) > 15:
        return False
    # Check if first column cells are short (labels)
    short_labels = 0
    for row in rows:
        if len(row) >= 2 and len(str(row[0]).strip()) < 50:
            short_labels += 1
    return short_labels >= len(rows) * 0.7


def _normalize_table_cells(extracted_tab: list[list]) -> list[list[str]]:
    """Normalize table cells: None → '', strip whitespace, join multi-line cells."""
    result = []
    for row in extracted_tab:
        normalized_row = []
        for cell in row:
            if cell is None:
                normalized_row.append("")
            else:
                cell_str = str(cell).strip()
                # Collapse internal newlines to space for cleaner output
                cell_str = re.sub(r'\n+', ' ', cell_str)
                normalized_row.append(cell_str)
        result.append(normalized_row)
    return result


def _detect_merged_cells(normalized: list[list[str]]) -> list[dict]:
    """Detect merged cells (colspan/rowspan) from normalized table data.
    
    PyMuPDF's table.extract() duplicates content for merged cells.
    This function detects adjacent cells with identical content to infer merges.
    
    Returns a list of merge descriptors:
    [{"row": r, "col": c, "rowspan": rs, "colspan": cs}, ...]
    
    Also marks cells that are "consumed" by a merge (should be skipped in rendering).
    """
    if not normalized or len(normalized) < 1:
        return []
    
    num_rows = len(normalized)
    num_cols = max(len(row) for row in normalized) if normalized else 0
    if num_cols == 0:
        return []
    
    # Pad rows to same length
    for row in normalized:
        while len(row) < num_cols:
            row.append("")
    
    # Track which cells are "consumed" by a merge
    consumed = [[False] * num_cols for _ in range(num_rows)]
    merges = []
    
    for r in range(num_rows):
        for c in range(num_cols):
            if consumed[r][c]:
                continue
            
            cell_val = normalized[r][c]
            
            # Detect colspan: count identical consecutive cells to the right
            colspan = 1
            while c + colspan < num_cols and normalized[r][c + colspan] == cell_val and cell_val != "":
                colspan += 1
            
            # Detect rowspan: count identical cells below (with same colspan width)
            rowspan = 1
            if cell_val != "":
                while r + rowspan < num_rows:
                    # Check if all cells in the span below match
                    match = True
                    for dc in range(colspan):
                        if c + dc >= num_cols or normalized[r + rowspan][c + dc] != cell_val:
                            match = False
                            break
                    if match:
                        rowspan += 1
                    else:
                        break
            
            # Only record if there's an actual merge
            if colspan > 1 or rowspan > 1:
                merges.append({
                    "row": r,
                    "col": c,
                    "rowspan": rowspan,
                    "colspan": colspan,
                    "value": cell_val
                })
                # Mark consumed cells
                for dr in range(rowspan):
                    for dc in range(colspan):
                        if dr == 0 and dc == 0:
                            continue  # Keep the anchor cell
                        consumed[r + dr][c + dc] = True
    
    return merges


def _try_merge_cross_page_tables(blocks: list[dict]) -> list[dict]:
    """Merge tables that span across pages if they have the same column count.
    
    If a table is followed by another table with matching headers,
    merge rows into the first table.
    Inspired by DocStudio's flushTable() buffer pattern.
    """
    if len(blocks) < 2:
        return blocks

    merged = []
    i = 0
    while i < len(blocks):
        block = blocks[i]
        if block.get("type") == "table" and i + 1 < len(blocks):
            next_block = blocks[i + 1]
            if next_block.get("type") == "table":
                curr_cols = len(block.get("headers", []))
                next_cols = len(next_block.get("headers", []))
                if curr_cols == next_cols and curr_cols > 0:
                    curr_headers = block.get("headers", [])
                    next_headers = next_block.get("headers", [])
                    headers_similar = all(
                        h1.strip().lower() == h2.strip().lower()
                        for h1, h2 in zip(curr_headers, next_headers)
                    )
                    if headers_similar:
                        merged_block = {**block}
                        merged_block["rows"] = block.get("rows", []) + next_block.get("rows", [])
                        merged_block["_merged_pages"] = True
                        merged.append(merged_block)
                        i += 2
                        continue
        merged.append(block)
        i += 1
    return merged


# ──────────────────────────────────────────────────────────────────────
# PDF Extraction
# ──────────────────────────────────────────────────────────────────────

WATERMARK_PATTERNS = [
    r"anhnn\.qld",
    r"Nguyen Ngoc Anh",
    r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}"
]


def is_watermark_text(text: str) -> bool:
    """Detect if a text segment is a tracking/timestamp watermark."""
    for pat in WATERMARK_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def clean_cell_text(text: str) -> str:
    """Clean watermark artifacts and excess whitespace from table cells."""
    if not text:
        return ""
    for pat in WATERMARK_PATTERNS:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    cleaned_lines = []
    for l in lines:
        # filter out isolated watermark fragments (single punctuation / symbols)
        if re.fullmatch(r"[_.:]{1,2}", l):
            continue
        cleaned_lines.append(l)
    res = " ".join(cleaned_lines)
    # clean extra internal whitespace
    res = re.sub(r"\s+", " ", res).strip()
    return res


def extract_from_pdf(pdf_path: Path, table_mode: str = "auto") -> list[dict]:
    """Extract semantic blocks from a PDF document in correct reading order.
    
    Features:
    - Filters background watermarks and diagonal text.
    - Page-by-page interleaved extraction: preserves exact vertical top-to-bottom reading sequence.
    - Table detection with cell cleaning and merge awareness.
    - Meta table detection (2-col key-value forms).
    - Cross-page table merging.
    """
    import pymupdf
    doc = pymupdf.open(pdf_path)
    blocks = []

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        page_items = []

        # 1. Extract tables on this page
        tabs = page.find_tables()
        tab_rects = []

        for t in tabs.tables:
            t_rect = pymupdf.Rect(t.bbox)
            tab_rects.append(t_rect)
            raw_tab = t.extract()
            if not raw_tab:
                continue

            cleaned_grid = []
            for row in raw_tab:
                cleaned_row = [clean_cell_text(c if c is not None else "") for c in row]
                cleaned_grid.append(cleaned_row)

            if not cleaned_grid:
                continue

            headers = cleaned_grid[0]
            rows = cleaned_grid[1:]

            if _is_meta_table(headers, rows):
                meta_items = []
                for row in cleaned_grid:
                    if len(row) >= 2 and (row[0].strip() or row[1].strip()):
                        meta_items.append({
                            "label": row[0].strip(),
                            "value": row[1].strip()
                        })
                if meta_items:
                    page_items.append({
                        "y0": t_rect.y0,
                        "x0": t_rect.x0,
                        "block": {
                            "type": "meta_table",
                            "items": meta_items,
                            "page": page_num
                        }
                    })
            else:
                # Detect merges
                merges = _detect_merged_cells(cleaned_grid)
                table_block = {
                    "type": "table",
                    "headers": headers,
                    "rows": rows,
                    "page": page_num
                }
                if merges:
                    table_block["merges"] = merges
                page_items.append({
                    "y0": t_rect.y0,
                    "x0": t_rect.x0,
                    "block": table_block
                })

        # 2. Extract text blocks on this page (excluding tables and watermarks)
        raw_blocks = page.get_text("blocks")
        for b in raw_blocks:
            if b[6] != 0:  # image block
                continue
            text = b[4].strip()
            if not text or is_watermark_text(text):
                continue

            b_rect = pymupdf.Rect(b[:4])

            # Check if this text block falls inside or significantly overlaps any table
            inside_table = False
            for t_rect in tab_rects:
                intersect = b_rect & t_rect
                if intersect.get_area() > 0.3 * b_rect.get_area():
                    inside_table = True
                    break
            if inside_table:
                continue

            lines = [l.strip() for l in text.split("\n") if l.strip()]
            joined_text = " ".join(lines)

            # Detect block type
            b_type = "p"
            if len(lines) == 1 and len(joined_text) < 120:
                if joined_text.isupper() or joined_text.startswith(("CHƯƠNG", "Chương", "PHỤ LỤC", "Phụ lục", "CHAPTER", "第", "CỘNG HÒA", "TÊN CƠ SỞ", "ỦY BAN")):
                    b_type = "h1"
                elif joined_text.startswith(("Điều", "Article", "Mục", "Section", "Phần", "I.", "II.", "III.", "IV.")):
                    b_type = "h2"

            if b_type == "p":
                if any(re.match(r"^[\-\*\•\□\☐\☑]\s+", l) for l in lines):
                    items = [re.sub(r"^[\-\*\•\□\☐\☑]\s+", "", l) for l in lines]
                    page_items.append({
                        "y0": b_rect.y0,
                        "x0": b_rect.x0,
                        "block": {"type": "ul", "items": items, "page": page_num}
                    })
                    continue
                elif any(re.match(r"^\d+[\.)\]]\s+", l) for l in lines):
                    items = [re.sub(r"^\d+[\.)\]]\s+", "", l) for l in lines]
                    page_items.append({
                        "y0": b_rect.y0,
                        "x0": b_rect.x0,
                        "block": {"type": "ol", "items": items, "page": page_num}
                    })
                    continue

            page_items.append({
                "y0": b_rect.y0,
                "x0": b_rect.x0,
                "block": {"type": b_type, "text": joined_text, "page": page_num}
            })

        # Sort all items on this page by vertical reading position (y0)
        page_items.sort(key=lambda x: x["y0"])
        for item in page_items:
            blocks.append(item["block"])

    doc.close()

    # Cross-page table merging (DocStudio flushTable buffer pattern)
    blocks = _try_merge_cross_page_tables(blocks)

    return blocks


def extract_from_txt(txt_path: Path) -> list[dict]:
    blocks = []
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                blocks.append({"type": "p", "text": line_str})
    return blocks


def main():
    parser = argparse.ArgumentParser(description="Extract structured text blocks from document files.")
    parser.add_argument("--input", required=True, type=Path, help="Input document (PDF, DOCX, MD, TXT)")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON blocks file")
    parser.add_argument("--table-mode", default="auto", choices=["fast", "enhanced", "accurate", "auto"],
                        help="Table extraction mode: fast (PyMuPDF only), enhanced (img2table), "
                             "accurate (Docling), auto (hybrid, recommended)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    ext = args.input.suffix.lower()
    if ext == ".md":
        blocks = extract_from_markdown(args.input)
    elif ext == ".pdf":
        blocks = extract_from_pdf(args.input, table_mode=args.table_mode)
    elif ext == ".docx":
        blocks = extract_from_docx(args.input, table_mode=args.table_mode)
    else:
        blocks = extract_from_txt(args.input)

    # Clean up empty blocks (also accept meta_table which has 'items')
    valid_blocks = [b for b in blocks if b.get("type") == "hr" or b.get("text") or b.get("items") or b.get("headers") or b.get("rows")]

    # Count tables with merges for reporting
    tables_with_merges = sum(1 for b in valid_blocks if b.get("type") == "table" and b.get("merges"))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(valid_blocks, f, ensure_ascii=False, indent=2)

    print(f"✅ Extracted {len(valid_blocks)} structured blocks to: {args.output}")
    if tables_with_merges:
        print(f"   📊 {tables_with_merges} table(s) with merged cells detected")


if __name__ == "__main__":
    main()
