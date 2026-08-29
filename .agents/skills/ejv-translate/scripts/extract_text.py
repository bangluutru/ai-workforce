#!/usr/bin/env python3
"""Extract structured text segments from PDF, DOCX, or TXT documents."""

import argparse
import json
import sys
from pathlib import Path


def extract_from_pdf(pdf_path: Path) -> list[dict]:
    import pymupdf
    doc = pymupdf.open(pdf_path)
    segments = []

    for page_idx, page in enumerate(doc):
        text = page.get_text("text").strip()
        if not text:
            continue
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines:
            # Simple heuristic for headings
            if len(line) < 60 and (line.isupper() or line.startswith(("1.", "2.", "3.", "I.", "II.", "Điều"))):
                segments.append({"type": "h2", "text": line, "page": page_idx + 1})
            else:
                segments.append({"type": "p", "text": line, "page": page_idx + 1})

    return segments


def extract_from_docx(docx_path: Path) -> list[dict]:
    from docx import Document
    doc = Document(docx_path)
    segments = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        style_name = p.style.name.lower() if p.style else ""
        if "heading 1" in style_name:
            segments.append({"type": "h1", "text": text})
        elif "heading 2" in style_name:
            segments.append({"type": "h2", "text": text})
        elif "heading 3" in style_name:
            segments.append({"type": "h3", "text": text})
        elif "list" in style_name:
            segments.append({"type": "ul", "text": text})
        else:
            segments.append({"type": "p", "text": text})

    for table in doc.tables:
        rows_data = []
        for row in table.rows:
            row_vals = [cell.text.strip() for cell in row.cells]
            rows_data.append(row_vals)
        if rows_data:
            segments.append({"type": "table", "headers": rows_data[0], "rows": rows_data[1:]})

    return segments


def extract_from_txt(txt_path: Path) -> list[dict]:
    segments = []
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                segments.append({"type": "p", "text": line_str})
    return segments


def main():
    parser = argparse.ArgumentParser(description="Extract structured text segments from document files.")
    parser.add_argument("--input", required=True, type=Path, help="Input document (PDF, DOCX, TXT)")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON segments file")
    args = parser.parse_args()

    ext = args.input.suffix.lower()
    if ext == ".pdf":
        segments = extract_from_pdf(args.input)
    elif ext == ".docx":
        segments = extract_from_docx(args.input)
    else:
        segments = extract_from_txt(args.input)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    print(f"✅ Extracted {len(segments)} segments to: {args.output}")


if __name__ == "__main__":
    main()
