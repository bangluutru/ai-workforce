#!/usr/bin/env python3
"""Extract structured document blocks (headings, paragraphs, lists, tables) from PDF, DOCX, MD, or TXT."""

import argparse
import json
import re
import sys
from pathlib import Path


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
        if re.match(r"^\d+[\.\)]\s+", line):
            ol_items = []
            while i < total and re.match(r"^\d+[\.\)]\s+", lines[i].strip()):
                clean_item = re.sub(r"^\d+[\.\)]\s+", "", lines[i].strip())
                ol_items.append(clean_item)
                i += 1
            blocks.append({"type": "ol", "items": ol_items})
            continue

        # Normal Paragraph
        p_lines = [line]
        i += 1
        while i < total:
            next_l = lines[i].strip()
            if not next_l or next_l.startswith("#") or next_l.startswith("|") or next_l.startswith(">") or next_l in {"---", "***", "___"} or re.match(r"^[\-\*\•\□\☐\☑\d+[\.\)]]\s+", next_l) or next_l.startswith("<!--"):
                break
            p_lines.append(next_l)
            i += 1
        
        full_p = " ".join(p_lines)
        if full_p:
            blocks.append({"type": "p", "text": full_p})

    return blocks


def extract_from_docx(docx_path: Path) -> list[dict]:
    """Extract semantic blocks from a Word DOCX document."""
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

    for table in doc.tables:
        rows_data = []
        for row in table.rows:
            row_vals = [cell.text.strip() for cell in row.cells]
            rows_data.append(row_vals)
        if rows_data:
            blocks.append({"type": "table", "headers": rows_data[0], "rows": rows_data[1:]})

    return blocks


def extract_from_pdf(pdf_path: Path) -> list[dict]:
    """Extract semantic blocks from a PDF document using PyMuPDF."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    blocks = []

    for page_idx, page in enumerate(doc):
        # Try extracting tables first
        try:
            tabs = page.find_tables()
            tab_rects = [t.bbox for t in tabs]
        except Exception:
            tabs = []
            tab_rects = []

        # Get text blocks
        page_blocks = page.get_text("blocks")
        # sort by vertical position (y0), then horizontal (x0)
        page_blocks.sort(key=lambda b: (b[1], b[0]))

        for b in page_blocks:
            # b = (x0, y0, x1, y1, text, block_no, block_type)
            if b[6] != 0:  # image block
                continue
            text = b[4].strip()
            if not text:
                continue

            # Check if this text block falls inside any table
            is_in_table = False
            for t_box in tab_rects:
                if (b[0] >= t_box[0] - 2 and b[1] >= t_box[1] - 2 and
                    b[2] <= t_box[2] + 2 and b[3] <= t_box[3] + 2):
                    is_in_table = True
                    break
            if is_in_table:
                continue

            # Detect block type
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            joined_text = " ".join(lines)

            if len(lines) == 1 and len(joined_text) < 100:
                if joined_text.isupper() or joined_text.startswith(("CHƯƠNG", "Chương", "PHỤ LỤC", "Phụ lục", "CHAPTER", "第")):
                    blocks.append({"type": "h1", "text": joined_text, "page": page_idx + 1})
                    continue
                elif joined_text.startswith(("Điều", "Article", "Mục", "Section", "第")):
                    blocks.append({"type": "h2", "text": joined_text, "page": page_idx + 1})
                    continue

            # List detection
            if any(re.match(r"^[\-\*\•\□\☐\☑\d+[\.\)]]\s+", l) for l in lines):
                items = [re.sub(r"^[\-\*\•\□\☐\☑\d+[\.\)]]\s+", "", l) for l in lines]
                blocks.append({"type": "ul", "items": items, "page": page_idx + 1})
            else:
                blocks.append({"type": "p", "text": joined_text, "page": page_idx + 1})

        # Append tables for this page
        for t in tabs:
            extracted_tab = t.extract()
            if extracted_tab and len(extracted_tab) > 0:
                headers = [str(c or '').strip() for c in extracted_tab[0]]
                rows = [[str(c or '').strip() for c in row] for row in extracted_tab[1:]]
                blocks.append({
                    "type": "table",
                    "headers": headers,
                    "rows": rows,
                    "page": page_idx + 1
                })

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
    args = parser.parse_args()

    ext = args.input.suffix.lower()
    if ext == ".md":
        blocks = extract_from_markdown(args.input)
    elif ext == ".pdf":
        blocks = extract_from_pdf(args.input)
    elif ext == ".docx":
        blocks = extract_from_docx(args.input)
    else:
        blocks = extract_from_txt(args.input)

    # Clean up empty blocks
    valid_blocks = [b for b in blocks if b.get("type") == "hr" or b.get("text") or b.get("items") or b.get("headers") or b.get("rows")]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(valid_blocks, f, ensure_ascii=False, indent=2)

    print(f"✅ Extracted {len(valid_blocks)} structured blocks to: {args.output}")


if __name__ == "__main__":
    main()
