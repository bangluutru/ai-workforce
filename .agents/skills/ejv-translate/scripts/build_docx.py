#!/usr/bin/env python3
"""Build formatted DOCX documents from EJV Trilingual JSON data."""

import argparse
import json
import sys
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

FORMAT_STYLES = {
    "standard": {
        "font_name": "Calibri",
        "font_size": 11,
        "line_spacing": 1.15,
        "align": WD_ALIGN_PARAGRAPH.LEFT,
        "indent_first": 0,
        "h1_size": 18,
        "h2_size": 14,
        "h3_size": 12,
    },
    "administrative": {
        "font_name": "Times New Roman",
        "font_size": 13,
        "line_spacing": 1.3,
        "align": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "indent_first": 0.4,  # inches (~1cm)
        "h1_size": 16,
        "h2_size": 14,
        "h3_size": 13,
    },
    "academic": {
        "font_name": "Arial",
        "font_size": 10.5,
        "line_spacing": 1.0,
        "align": WD_ALIGN_PARAGRAPH.LEFT,
        "indent_first": 0,
        "h1_size": 14,
        "h2_size": 12,
        "h3_size": 11,
    },
}


def set_cell_border(cell, **kwargs):
    """Set cell border in docx table."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key, val in edge_data.items():
                element.set(qn('w:{}'.format(key)), str(val))


def build_docx(blocks: list, output_path: Path, lang: str = "vn", style_name: str = "administrative"):
    doc = Document()
    style = FORMAT_STYLES.get(style_name, FORMAT_STYLES["administrative"])

    # Page setup: Standard A4 margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(0.8)

    for block in blocks:
        b_type = block.get("type")
        val = block.get(lang) or block.get("vn") or block.get("en") or block.get("ja") or ""

        if b_type == "h1":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(8)
            run = p.add_run(str(val).upper())
            run.bold = True
            run.font.name = style["font_name"]
            run.font.size = Pt(style["h1_size"])

        elif b_type == "h2":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(str(val))
            run.bold = True
            run.font.name = style["font_name"]
            run.font.size = Pt(style["h2_size"])

        elif b_type == "h3":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(str(val))
            run.bold = True
            run.font.name = style["font_name"]
            run.font.size = Pt(style["h3_size"])

        elif b_type == "p":
            p = doc.add_paragraph()
            p.alignment = style["align"]
            p.paragraph_format.space_after = Pt(4)
            if style["indent_first"] > 0:
                p.paragraph_format.first_line_indent = Inches(style["indent_first"])
            run = p.add_run(str(val))
            run.font.name = style["font_name"]
            run.font.size = Pt(style["font_size"])

        elif b_type in {"ul", "ol"}:
            items = val if isinstance(val, list) else [val]
            for item in items:
                p = doc.add_paragraph(style='List Bullet' if b_type == 'ul' else 'List Number')
                p.paragraph_format.space_after = Pt(2)
                run = p.add_run(str(item))
                run.font.name = style["font_name"]
                run.font.size = Pt(style["font_size"])

        elif b_type == "blockquote":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(str(val))
            run.italic = True
            run.font.name = style["font_name"]
            run.font.size = Pt(style["font_size"])
            run.font.color.rgb = RGBColor(80, 80, 80)

        elif b_type == "table":
            headers = block.get("headers", {}).get(lang) or block.get("headers", {}).get("vn") or []
            rows = block.get("rows", {}).get(lang) or block.get("rows", {}).get("vn") or []
            if headers or rows:
                cols_count = len(headers) if headers else (len(rows[0]) if rows else 0)
                if cols_count > 0:
                    tbl = doc.add_table(rows=0, cols=cols_count)
                    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

                    if headers:
                        h_row = tbl.add_row()
                        for c_idx, h_text in enumerate(headers):
                            cell = h_row.cells[c_idx]
                            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                            run = cell.paragraphs[0].add_run(str(h_text))
                            run.bold = True
                            run.font.name = style["font_name"]
                            run.font.size = Pt(style["font_size"] - 1)
                            set_cell_border(cell, top={"val": "single", "sz": "4", "color": "888888"},
                                            bottom={"val": "single", "sz": "4", "color": "888888"},
                                            left={"val": "single", "sz": "4", "color": "888888"},
                                            right={"val": "single", "sz": "4", "color": "888888"})

                    for r in rows:
                        cells = r if isinstance(r, list) else [r]
                        row = tbl.add_row()
                        for c_idx, c_val in enumerate(cells[:cols_count]):
                            cell = row.cells[c_idx]
                            run = cell.paragraphs[0].add_run(str(c_val))
                            run.font.name = style["font_name"]
                            run.font.size = Pt(style["font_size"] - 1)
                            set_cell_border(cell, top={"val": "single", "sz": "4", "color": "CCCCCC"},
                                            bottom={"val": "single", "sz": "4", "color": "CCCCCC"},
                                            left={"val": "single", "sz": "4", "color": "CCCCCC"},
                                            right={"val": "single", "sz": "4", "color": "CCCCCC"})
                    doc.add_paragraph()  # spacing

        elif b_type == "caption":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(str(val))
            run.italic = True
            run.font.name = style["font_name"]
            run.font.size = Pt(style["font_size"] - 2)

    doc.save(str(output_path))
    print(f"✅ Generated DOCX ({lang.upper()}): {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Export EJV JSON to formatted DOCX document.")
    parser.add_argument("--input", required=True, type=Path, help="Input EJV JSON file")
    parser.add_argument("--output", required=True, type=Path, help="Output DOCX file path")
    parser.add_argument("--lang", default="vn", choices=["vn", "en", "ja"], help="Language to export (vn, en, ja)")
    parser.add_argument("--style", default="administrative", choices=["standard", "administrative", "academic"], help="Layout format style")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        blocks = json.load(f)

    build_docx(blocks, args.output, lang=args.lang, style_name=args.style)


if __name__ == "__main__":
    main()
