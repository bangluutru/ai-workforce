#!/usr/bin/env python3
"""Extract structured document blocks (headings, paragraphs, lists, tables, images) from any document.

Routing (by magic bytes, not extension):
- PDF  → native PyMuPDF extractor (y0 interleave, watermark filter, merge-aware tables). Preflight: password → exit 2;
         no text layer → exit 3 ("PDF scan → dùng boc-tach-pdf hoặc doc_ingest OCR"); pages whose PyMuPDF text has
         broken Vietnamese diacritics are re-extracted from scripts/doc_ingest.py (pdfplumber/pdftotext).
- DOCX → native python-docx in BODY ORDER (paragraphs, tables, content controls interleaved) + inline images.
         TCVN3/VNI legacy fonts → doc_ingest route (auto conversion).
- EPUB → native epub_parser (spine order, file/elem_index for epub_builder, tables kept); DRM → exit 2.
- MD   → native markdown parser (encoding-aware).
- Everything else (TXT/CSV with any encoding, XLSX/XLS/ODS, PPTX/PPT/ODP, DOC/ODT/RTF, HTML, images, unknown)
         → scripts/doc_ingest.py → source.md → blocks. Never read binary files as text.
Exit codes: 0 ok | 2 unreadable (password/DRM/encrypted/corrupt/empty) | 3 no text layer (scan) | 4 missing dependency.
Writes <output dir>/extraction_report.json (input, detected_format, route, warnings, scan/damaged pages).

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from doc_ingest_bridge import (EXIT_MISSING_DEP, EXIT_OK, EXIT_PARTIAL, EXIT_UNREADABLE,  # noqa: E402
                               explain, load_doc_ingest, md_blocks, pdf_preflight, run_ingest, sniff_kind,
                               strip_md_inline)

log = logging.getLogger(__name__)


def extract_from_markdown(md_path: Path) -> list[dict]:
    """Extract semantic blocks from a Markdown document."""
    try:
        text, _enc, _legacy = load_doc_ingest().decode_bytes(Path(md_path).read_bytes())
    except Exception:  # noqa: BLE001
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

        # Image line ![alt](src) → image block (src resolved against the .md folder)
        m_img = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)$", line)
        if m_img:
            src = m_img.group(2)
            if not re.match(r"^[a-z]+:", src) and not Path(src).is_absolute():
                src = str((Path(md_path).parent / src).resolve())
            blocks.append({"type": "image", "src": src, "alt": m_img.group(1)})
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


def _docx_table_block(headers: list, rows: list, merges=None) -> dict:
    if _is_meta_table(headers, rows):
        items = [{"label": r[0].strip(), "value": r[1].strip()} for r in rows
                 if len(r) >= 2 and (r[0].strip() or r[1].strip())]
        if items:
            return {"type": "meta_table", "items": items}
        return {}
    block = {"type": "table", "headers": headers, "rows": rows}
    if merges:
        block["merges"] = [{"row": m.row, "col": m.col, "rowspan": m.rowspan, "colspan": m.colspan, "value": m.value}
                           for m in merges]
    return block


def _docx_images(paragraph_el, part, media_dir: Path | None, counter: list) -> list[dict]:
    """Ảnh nội dòng trong một đoạn (a:blip r:embed, v:imagedata r:id) → khối image (lưu vào media_dir)."""
    if media_dir is None:
        return []
    from docx.oxml.ns import qn
    rids = [b.get(qn("r:embed")) for b in paragraph_el.iter(qn("a:blip"))]
    rids += [v.get(qn("r:id")) for v in paragraph_el.iter("{urn:schemas-microsoft-com:vml}imagedata")]
    out = []
    for rid in rids:
        if not rid or rid not in part.related_parts:
            continue
        img_part = part.related_parts[rid]
        ext = Path(str(getattr(img_part, "partname", "img.png"))).suffix.lower() or ".png"
        if ext in (".emf", ".wmf"):
            continue  # ảnh vector Windows: python-docx/Typst không hiển thị được
        counter[0] += 1
        media_dir.mkdir(parents=True, exist_ok=True)
        dest = media_dir / f"docx_image_{counter[0]:03d}{ext}"
        dest.write_bytes(img_part.blob)
        out.append({"type": "image", "src": str(dest.resolve()), "alt": ""})
    return out


def extract_from_docx(docx_path: Path, table_mode: str = "auto", media_dir: Path | None = None) -> list[dict]:
    """Extract semantic blocks from a Word DOCX document IN BODY ORDER.

    Paragraphs, tables (TableExtractor for precise merge detection from OOXML) and content controls (w:sdt)
    are interleaved exactly as in the document; inline images are saved to media_dir as image blocks.
    """
    from docx import Document
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph
    doc = Document(docx_path)
    blocks = []

    # Tables (top-level body tables, same order as doc.tables)
    extracted = None
    try:
        from table_extractor import TableExtractor
        extracted = TableExtractor(mode=table_mode).extract_tables_from_docx(docx_path)
    except ImportError:
        log.warning("table_extractor not available, falling back to basic DOCX table extraction")
    nonempty_idx = [i for i, t in enumerate(doc.tables) if len(t.rows) and len(t.columns)]
    table_by_el = {}
    for k, i in enumerate(nonempty_idx):
        tbl = doc.tables[i]
        if extracted is not None and k < len(extracted):
            et = extracted[k]
            table_by_el[id(tbl._tbl)] = _docx_table_block(et.headers, et.rows, et.merges)
        else:
            rows_data = [[cell.text.strip() for cell in row.cells] for row in tbl.rows]
            table_by_el[id(tbl._tbl)] = _docx_table_block(rows_data[0], rows_data[1:]) if rows_data else {}
    tbl_elems = {id(t._tbl): t._tbl for t in doc.tables}

    img_counter = [0]

    def para_block(p):
        text = p.text.strip()
        if not text:
            return None
        style_name = p.style.name.lower() if p.style is not None else ""
        if "heading 1" in style_name or style_name == "title":
            return {"type": "h1", "text": text}
        if "heading 2" in style_name:
            return {"type": "h2", "text": text}
        if "heading" in style_name:
            return {"type": "h3", "text": text}
        if "list" in style_name or "bullet" in style_name:
            return {"type": "ul", "items": [text]}
        if "quote" in style_name:
            return {"type": "blockquote", "text": text}
        return {"type": "p", "text": text}

    def walk(container_el):
        for child in container_el.iterchildren():
            tag = child.tag
            if tag == qn("w:p"):
                p = Paragraph(child, doc._body)
                b = para_block(p)
                if b:
                    blocks.append(b)
                blocks.extend(_docx_images(child, doc.part, media_dir, img_counter))
            elif tag == qn("w:tbl"):
                tb = table_by_el.get(id(child))
                if tb is None:  # bảng không nằm trong doc.tables (vd trong w:sdt) → trích cơ bản
                    from docx.table import Table
                    t = Table(child, doc._body)
                    rows_data = [[c.text.strip() for c in r.cells] for r in t.rows]
                    tb = _docx_table_block(rows_data[0], rows_data[1:]) if rows_data else {}
                if tb:
                    blocks.append(dict(tb))
                for p_el in child.iter(qn("w:p")):
                    blocks.extend(_docx_images(p_el, doc.part, media_dir, img_counter))
            elif tag == qn("w:sdt"):
                content = child.find(qn("w:sdtContent"))
                if content is not None:
                    walk(content)

    walk(doc.element.body)
    del tbl_elems  # giữ proxy lxml sống tới đây để id() của bảng ổn định trong lúc duyệt
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
                        "y1": t_rect.y1,
                        "x1": t_rect.x1,
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
                    "y1": t_rect.y1,
                    "x1": t_rect.x1,
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
                        "y1": b_rect.y1,
                        "x1": b_rect.x1,
                        "block": {"type": "ul", "items": items, "page": page_num}
                    })
                    continue
                elif any(re.match(r"^\d+[\.)\]]\s+", l) for l in lines):
                    items = [re.sub(r"^\d+[\.)\]]\s+", "", l) for l in lines]
                    page_items.append({
                        "y0": b_rect.y0,
                        "x0": b_rect.x0,
                        "y1": b_rect.y1,
                        "x1": b_rect.x1,
                        "block": {"type": "ol", "items": items, "page": page_num}
                    })
                    continue

            page_items.append({
                "y0": b_rect.y0,
                "x0": b_rect.x0,
                "y1": b_rect.y1,
                "x1": b_rect.x1,
                "block": {"type": b_type, "text": joined_text, "page": page_num}
            })

        # Sort all items on this page by natural column-aware reading position
        sorted_page_items = _sort_page_reading_order(page_items, page.rect.width)
        for item in sorted_page_items:
            blocks.append(item["block"])

    doc.close()

    # Cross-page table merging (DocStudio flushTable buffer pattern)
    blocks = _try_merge_cross_page_tables(blocks)

    return blocks


def _sort_page_reading_order(page_items: list[dict], page_width: float = 595.0) -> list[dict]:
    """Sorts page items into natural reading order, resolving multi-column layouts."""
    if len(page_items) <= 1:
        return page_items

    mid_x = page_width / 2.0
    col_tol = page_width * 0.08

    full_width, col1, col2 = [], [], []
    for it in page_items:
        x0, x1 = it.get("x0", 0.0), it.get("x1", it.get("x0", 0.0) + 100.0)
        w = x1 - x0
        if w > page_width * 0.58 or (x0 < mid_x - col_tol and x1 > mid_x + col_tol):
            full_width.append(it)
        elif x0 < mid_x and x1 <= mid_x + col_tol:
            col1.append(it)
        elif x0 >= mid_x - col_tol:
            col2.append(it)
        else:
            center = (x0 + x1) / 2.0
            (col1 if center < mid_x else col2).append(it)

    if len(col1) < 2 or len(col2) < 2:
        page_items.sort(key=lambda it: it.get("y0", 0.0))
        return page_items

    col1_y0 = min(it.get("y0", 9999.0) for it in col1)
    col2_y0 = min(it.get("y0", 9999.0) for it in col2)
    col_start = min(col1_y0, col2_y0) - 10.0

    col1_y1 = max(it.get("y1", 0.0) for it in col1)
    col2_y1 = max(it.get("y1", 0.0) for it in col2)
    col_end = max(col1_y1, col2_y1) + 10.0

    top = [it for it in full_width if it.get("y0", 0.0) <= col_start + 15.0]
    bottom = [it for it in full_width if it.get("y0", 0.0) >= col_end - 15.0]
    mid = [it for it in full_width if it not in top and it not in bottom]

    top.sort(key=lambda it: it.get("y0", 0.0))
    col1.sort(key=lambda it: it.get("y0", 0.0))
    col2.sort(key=lambda it: it.get("y0", 0.0))
    bottom.sort(key=lambda it: it.get("y0", 0.0))

    return top + col1 + mid + col2 + bottom


def extract_from_txt(txt_path: Path) -> list[dict]:
    """Plain text → one paragraph per non-empty line (encoding-aware: UTF-8/UTF-16/CP1258/TCVN3 via doc_ingest)."""
    try:
        text, _enc, _legacy = load_doc_ingest().decode_bytes(Path(txt_path).read_bytes())
    except Exception:  # noqa: BLE001
        text = Path(txt_path).read_text(encoding="utf-8", errors="ignore")
    return [{"type": "p", "text": ln.strip()} for ln in text.splitlines() if ln.strip()]


# ──────────────────────────────────────────────────────────────────────
# doc_ingest route (XLSX/PPTX/DOC/ODF/RTF/HTML/CSV/TXT/images/...)
# ──────────────────────────────────────────────────────────────────────

_XLSX_HEADER = re.compile(r"^[A-Z]{1,3}$")


def _clean_cell(c: str) -> str:
    return strip_md_inline(str(c)).replace("<br>", "\n").strip()


def _table_from_rows(rows: list[list[str]]) -> dict:
    rows = [[_clean_cell(c) for c in r] for r in rows]
    # Bảng XLSX của doc_ingest: hàng tiêu đề '# | A | B ...' + cột số hàng → bỏ, lấy hàng 1 làm tiêu đề
    if rows and rows[0] and rows[0][0] == "#" and all(_XLSX_HEADER.match(h or "") for h in rows[0][1:]):
        rows = [r[1:] for r in rows[1:]]
    if not rows:
        return {}
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    return {"type": "table", "headers": rows[0], "rows": rows[1:]}


def blocks_from_markdown_text(md: str, base_dir: Path, page: int | None = None) -> list[dict]:
    """source.md của doc_ingest → khối EJV (h1/h2/h3, p, ul, table, image). Bỏ bảng công thức XLSX
    (không dịch được) và bản nháp OCR (chưa kiểm chứng)."""
    out: list[dict] = []
    skip_formula_table = False
    cur_page = page
    for b in md_blocks(md):
        t = b["type"]
        if t == "page":
            cur_page = b["page"]
            continue
        if t == "ocr_notice":
            continue
        blk = None
        if t == "heading":
            text = strip_md_inline(b["text"])
            if text.startswith("Công thức — "):
                skip_formula_table = True
                continue
            blk = {"type": "h1" if b["level"] == 1 else "h2" if b["level"] == 2 else "h3", "text": text}
        elif t == "table":
            if skip_formula_table and b["rows"] and [c.strip() for c in b["rows"][0][:2]] == ["Ô", "Công thức"]:
                skip_formula_table = False
                continue
            blk = _table_from_rows(b["rows"])
        elif t == "paragraph":
            blk = {"type": "p", "text": strip_md_inline(b["text"])}
        elif t == "list_item":
            item = strip_md_inline(b["text"])
            if out and out[-1].get("type") == "ul" and out[-1].get("_md_list"):
                out[-1]["items"].append(item)
                continue
            blk = {"type": "ul", "items": [item], "_md_list": True}
        elif t == "image":
            src = b["src"]
            if not re.match(r"^[a-z]+:", src) and not Path(src).is_absolute():
                src = str((base_dir / src).resolve())
            blk = {"type": "image", "src": src, "alt": b.get("alt", "")}
        skip_formula_table = skip_formula_table and t == "heading"
        if blk:
            if cur_page is not None:
                blk["page"] = cur_page
            out.append(blk)
    for blk in out:
        blk.pop("_md_list", None)
    return out


def extract_via_doc_ingest(path: Path, work_dir: Path) -> tuple[list[dict], dict]:
    man = run_ingest(path, work_dir)
    if man.get("exit_code") not in (EXIT_OK, EXIT_PARTIAL):
        return [], man
    base = Path(man.get("out_dir") or work_dir)
    if man.get("detected_format") == "text":
        return [{"type": "p", "text": ln.strip()} for ln in man.get("source_md", "").splitlines() if ln.strip()], man
    return blocks_from_markdown_text(man.get("source_md", ""), base), man


def _page_sections(md: str) -> dict[int, str]:
    secs, cur, buf = {}, None, []
    for ln in md.split("\n"):
        m = re.match(r"^<!--\s*page\s+(\d+)\s*-->\s*$", ln.strip())
        if m:
            if cur is not None:
                secs[cur] = "\n".join(buf)
            cur, buf = int(m.group(1)), []
        else:
            buf.append(ln)
    if cur is not None:
        secs[cur] = "\n".join(buf)
    return secs


def _pdf_lines_to_paragraphs(md: str) -> str:
    """Chữ PDF theo dòng (pdfplumber/pdftotext) → đoạn: ngắt đoạn khi dòng trước kết thúc câu hoặc dòng sau bắt đầu
    bằng chữ HOA/số/gạch đầu dòng; dòng bảng '|' giữ nguyên."""
    out: list[str] = []
    prev = ""
    for ln in md.split("\n"):
        st = ln.strip()
        if not st or st.startswith(("|", "<!--", "![")):
            out.append(ln)
            prev = "" if not st else st
            continue
        if prev and not prev.startswith(("|", "<!--", "![")):
            if re.search(r"[.:;!?)\]”]$", prev) or re.match(r"^([A-ZÀ-Ỹ0-9]|[-•*+]\s)", st):
                out.append("")
        out.append(ln)
        prev = st
    return "\n".join(out)


def _replace_damaged_pdf_pages(blocks: list[dict], pdf: Path, pages: list[int], work_dir: Path) -> list[int]:
    """Trang có lớp chữ PyMuPDF vỡ dấu tiếng Việt → thay khối của trang đó bằng bản doc_ingest
    (đã chọn bộ trích ít vỡ dấu nhất: pdfplumber/pdftotext). Trả về danh sách trang đã thay."""
    man = run_ingest(pdf, work_dir, ocr=False)
    if man.get("exit_code") not in (EXIT_OK, EXIT_PARTIAL):
        return []
    secs = _page_sections(man.get("source_md", ""))
    base = Path(man.get("out_dir") or work_dir)
    replaced = []
    for pg in pages:
        if pg not in secs:
            continue
        new = [b for b in blocks_from_markdown_text(_pdf_lines_to_paragraphs(secs[pg]), base, page=pg)
               if b.get("type") != "image"]
        if not new:
            continue
        for b in new:  # cùng quy tắc tiêu đề như extract_from_pdf
            txt = b.get("text") or ""
            if b.get("type") == "p" and len(txt) < 120:
                if txt.isupper() or txt.startswith(("CHƯƠNG", "Chương", "PHỤ LỤC", "Phụ lục", "CHAPTER", "第", "CỘNG HÒA")):
                    b["type"] = "h1"
                elif txt.startswith(("Điều", "Article", "Mục", "Section", "Phần", "I.", "II.", "III.", "IV.")):
                    b["type"] = "h2"
        idx = [i for i, b in enumerate(blocks) if b.get("page") == pg]
        if not idx:
            continue
        blocks[idx[0]:idx[-1] + 1] = new
        replaced.append(pg)
    return replaced


def _legacy_encoding_in(blocks: list[dict], docx_path: Path) -> str | None:
    """TCVN3/VNI trong DOCX (font .VnTime/VNI-Times): python-docx trả về chữ sai dấu → cần doc_ingest chuyển mã."""
    import zipfile
    try:
        di = load_doc_ingest()
        with zipfile.ZipFile(docx_path) as z:
            hint = di._docx_font_hint(z)
        text = "\n".join(str(b.get("text") or " ".join(map(str, b.get("items") or []))) for b in blocks)
        return di.detect_legacy(text, hint=hint)
    except Exception:  # noqa: BLE001
        return None


def _translatable(b: dict) -> bool:
    if b.get("type") in ("hr", "image"):
        return False
    return bool(b.get("text") or b.get("items") or b.get("headers") or b.get("rows"))


def run_extraction(inp: Path, output: Path, table_mode: str = "auto") -> tuple[int, list[dict], dict]:
    """Định tuyến theo magic bytes → (exit_code, blocks, report)."""
    work = output.parent / "_ingest"
    media_dir = output.parent / "media"
    kind = sniff_kind(inp)
    ext = inp.suffix.lower()
    report = {"input": str(inp.resolve()) if inp.exists() else str(inp), "detected_format": kind, "route": None,
              "warnings": [], "scan_pages": [], "damaged_pages": [], "message": None}

    def fail(code: int, msg: str):
        report["message"] = msg
        return code, [], report

    if kind in ("missing", "dir"):
        return fail(EXIT_UNREADABLE, f"Không tìm thấy tệp đầu vào: {inp}")
    blocks: list[dict] = []
    if kind == "pdf":
        pf = pdf_preflight(inp, min_text_ratio=0.0)
        report["scan_pages"], report["pages"] = pf.get("scan_pages", []), pf.get("pages")
        if pf["code"] in (EXIT_UNREADABLE, EXIT_MISSING_DEP):
            return fail(pf["code"], pf["message"])
        if not pf.get("text_pages"):
            return fail(EXIT_PARTIAL, "PDF scan (không có lớp chữ) → dùng skill boc-tach-pdf (OCR → .md/.docx rồi dịch "
                                      "tệp đó) hoặc `.venv/bin/python scripts/doc_ingest.py <pdf> --out <dir>` (OCR nháp, "
                                      "phải đối chiếu ảnh ocr_pages/). Không có gì để dịch.")
        report["route"] = "native:pymupdf"
        blocks = extract_from_pdf(inp, table_mode=table_mode)
        damaged = [d["page"] for d in pf.get("damaged_pages", [])]
        if damaged:
            fixed = _replace_damaged_pdf_pages(blocks, inp, damaged, work)
            report["damaged_pages"] = damaged
            if fixed:
                report["route"] += "+doc_ingest(pages " + ",".join(map(str, fixed)) + ")"
                report["warnings"].append(f"⚠️ Trang {', '.join(map(str, fixed))}: lớp chữ PyMuPDF rơi dấu tiếng Việt → đã "
                                          "trích lại bằng doc_ingest (pdfplumber/pdftotext). Đối chiếu ảnh trang trước khi giao.")
            rest = [p for p in damaged if p not in fixed]
            if rest:
                report["warnings"].append(f"⚠️ DẤU TIẾNG VIỆT BỊ VỠ ở trang {', '.join(map(str, rest))} và không tự sửa được: "
                                          "đối chiếu ảnh trang, sửa câu nguồn trước khi dịch.")
        if pf.get("scan_pages"):
            report["warnings"].append(f"⚠️ Trang scan KHÔNG có lớp chữ, không được trích để dịch: "
                                      f"{', '.join(map(str, pf['scan_pages'][:40]))}. Báo người dùng; OCR các trang này "
                                      "bằng boc-tach-pdf nếu cần dịch.")
    elif kind == "docx":
        report["route"] = "native:python-docx(body-order)"
        blocks = extract_from_docx(inp, table_mode=table_mode, media_dir=media_dir)
        legacy = _legacy_encoding_in(blocks, inp)
        if legacy:
            report["warnings"].append(f"Văn bản dùng bảng mã cũ {legacy.upper()} → trích qua doc_ingest (tự chuyển mã).")
            kind = "docx-legacy"
    elif kind == "epub":
        try:
            from epub_parser import EpubDRMError, extract_from_epub
        except ImportError:
            from .epub_parser import EpubDRMError, extract_from_epub
        report["route"] = "native:epub_parser"
        try:
            blocks, toc_items, _ = extract_from_epub(inp)
        except EpubDRMError as e:
            return fail(EXIT_UNREADABLE, f"{e} Không dịch được bản có DRM; cần bản EPUB/PDF gốc mà người dùng có quyền sử dụng.")
        toc_path = output.parent / "toc_items.json"
        toc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(toc_path, "w", encoding="utf-8") as f_toc:
            json.dump(toc_items, f_toc, ensure_ascii=False, indent=2)
    elif kind == "markdown" or (kind == "text" and ext in (".md", ".markdown")):
        report["route"] = "native:markdown"
        blocks = extract_from_markdown(inp)

    if kind not in ("pdf", "docx", "epub", "markdown") and not (kind == "text" and ext in (".md", ".markdown")):
        blocks, man = extract_via_doc_ingest(inp, work)
        report["route"] = "doc_ingest:" + "+".join(man.get("converter_chain") or [str(man.get("detected_format"))])
        report["ingest_dir"] = man.get("out_dir")
        report["warnings"] += [w for w in man.get("warnings") or [] if w != man.get("message")]
        if man.get("exit_code") in (EXIT_UNREADABLE, EXIT_MISSING_DEP):
            return fail(man["exit_code"], explain(man, "ejv-translate"))
        if man.get("exit_code") == EXIT_PARTIAL:
            report["scan_pages"] = man.get("pages_needing_ocr") or []
            if not any(_translatable(b) for b in blocks):
                return fail(EXIT_PARTIAL, "Ảnh/trang scan không có lớp chữ → không có gì để dịch. Dùng skill boc-tach-pdf "
                                          f"(OCR) trước. {explain(man)}")
            report["warnings"].append("⚠️ " + explain(man))
    return EXIT_OK, blocks, report


def main():
    parser = argparse.ArgumentParser(description="Extract structured text blocks from document files.")
    parser.add_argument("--input", required=True, type=Path,
                        help="Input document (PDF, DOCX, EPUB, MD, TXT, XLSX/PPTX/DOC/ODT/RTF/HTML/CSV… via doc_ingest)")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON blocks file")
    parser.add_argument("--table-mode", default="auto", choices=["fast", "enhanced", "accurate", "auto"],
                        help="Table extraction mode: fast (PyMuPDF only), enhanced (img2table), "
                             "accurate (Docling), auto (hybrid, recommended)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    args.output.parent.mkdir(parents=True, exist_ok=True)
    code, blocks, report = run_extraction(args.input, args.output, table_mode=args.table_mode)

    # Clean up empty blocks (also accept meta_table which has 'items')
    valid_blocks = [b for b in blocks if b.get("type") in ("hr", "image") or b.get("text") or b.get("items")
                    or b.get("headers") or b.get("rows")]
    n_text = sum(1 for b in valid_blocks if _translatable(b))
    if code == EXIT_OK and n_text == 0:
        code = EXIT_UNREADABLE
        report["message"] = (f"Trích được 0 khối văn bản từ {args.input.name} (định dạng {report['detected_format']}). "
                             "Không có gì để dịch — hỏi người dùng tệp có nội dung/tệp gốc.")
    report.update(exit_code=code, blocks=len(valid_blocks), text_blocks=n_text,
                  images=sum(1 for b in valid_blocks if b.get("type") == "image"), output=str(args.output))
    with open(args.output.parent / "extraction_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    if code != EXIT_OK:
        if args.output.exists():
            args.output.unlink()  # không để lại extracted_blocks.json cũ gây hiểu nhầm
        print(f"❌ {report['message']}", file=sys.stderr)
        sys.exit(code)

    # Count tables with merges for reporting
    tables_with_merges = sum(1 for b in valid_blocks if b.get("type") == "table" and b.get("merges"))

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(valid_blocks, f, ensure_ascii=False, indent=2)

    mark = "⚠️" if report["warnings"] else "✅"
    print(f"{mark} Extracted {len(valid_blocks)} structured blocks ({n_text} text, route {report['route']}) to: {args.output}")
    if tables_with_merges:
        print(f"   📊 {tables_with_merges} table(s) with merged cells detected")
    if report["images"]:
        print(f"   🖼  {report['images']} image block(s) — copy them unchanged into translated batches")
    for w in report["warnings"]:
        print(f"   {w}")


if __name__ == "__main__":
    main()
