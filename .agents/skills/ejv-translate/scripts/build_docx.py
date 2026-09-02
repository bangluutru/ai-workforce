#!/usr/bin/env python3
"""Build formatted DOCX documents from EJV Trilingual JSON data.

Enhanced with DocStudio-inspired rendering:
- Markdown inline styling → native Word TextRuns (bold, italic, bold+italic)
- Meta table rendering (2-col key-value with shaded header)
- Table column auto-width
- Cell border styling helpers
"""

import argparse
import json
import re
import sys
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsdecls
from lxml import etree


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


# ──────────────────────────────────────────────────────────────────────
# Cell & Table Helpers (DocStudio export.js pattern)
# ──────────────────────────────────────────────────────────────────────

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


def set_cell_shading(cell, hex_color: str):
    """Set cell background shading color (DocStudio CertificatePage meta pattern).
    
    Args:
        cell: python-docx table cell
        hex_color: Hex color string without '#' (e.g., 'F5F5F5')
    """
    shading_elm = etree.SubElement(
        cell._tc.get_or_add_tcPr(),
        qn('w:shd')
    )
    shading_elm.set(qn('w:fill'), hex_color)
    shading_elm.set(qn('w:val'), 'clear')
    shading_elm.set(qn('w:color'), 'auto')


def set_table_full_width(table):
    """Set table to use 100% page width (DocStudio export pattern)."""
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')
    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:type'), 'pct')
    tblW.set(qn('w:w'), '5000')  # 5000 = 100% in pct units
    # Remove old tblW if exists
    old_w = tblPr.find(qn('w:tblW'))
    if old_w is not None:
        tblPr.remove(old_w)
    tblPr.append(tblW)


# ──────────────────────────────────────────────────────────────────────
# Markdown → Native Word TextRuns
# (DocStudio LegalDocumentView.jsx L250-268 pattern ported to Python)
# ──────────────────────────────────────────────────────────────────────

def add_styled_text(paragraph, text: str, font_name: str = "Times New Roman",
                    font_size: float = 13, force_bold: bool = False,
                    force_italic: bool = False, color: RGBColor = None):
    """Parse Markdown inline formatting and add native Word runs.
    
    Supports: ***bold+italic***, **bold**, *italic*, and plain text.
    Inspired by DocStudio LegalDocumentView.jsx inline styling logic.
    """
    if not text:
        return

    # Regex to split on Markdown formatting markers
    # Order matters: ***bold+italic*** first, then **bold**, then *italic*
    pattern = r'(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*)'
    parts = re.split(pattern, text)

    for part in parts:
        if not part:
            continue

        is_bold = force_bold
        is_italic = force_italic

        if part.startswith('***') and part.endswith('***'):
            part = part[3:-3]
            is_bold = True
            is_italic = True
        elif part.startswith('**') and part.endswith('**'):
            part = part[2:-2]
            is_bold = True
        elif part.startswith('*') and part.endswith('*'):
            part = part[1:-1]
            is_italic = True

        run = paragraph.add_run(part)
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.bold = is_bold
        run.italic = is_italic
        if color:
            run.font.color.rgb = color


# ──────────────────────────────────────────────────────────────────────
# Main DOCX Builder
# ──────────────────────────────────────────────────────────────────────

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
            add_styled_text(p, str(val).upper(), font_name=style["font_name"],
                           font_size=style["h1_size"], force_bold=True)

        elif b_type == "h2":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            add_styled_text(p, str(val), font_name=style["font_name"],
                           font_size=style["h2_size"], force_bold=True)

        elif b_type == "h3":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            add_styled_text(p, str(val), font_name=style["font_name"],
                           font_size=style["h3_size"], force_bold=True)

        elif b_type == "p":
            p = doc.add_paragraph()
            p.alignment = style["align"]
            p.paragraph_format.space_after = Pt(4)
            if style["indent_first"] > 0:
                p.paragraph_format.first_line_indent = Inches(style["indent_first"])
            add_styled_text(p, str(val), font_name=style["font_name"],
                           font_size=style["font_size"])

        elif b_type in {"ul", "ol"}:
            items = val if isinstance(val, list) else [val]
            for item in items:
                p = doc.add_paragraph(style='List Bullet' if b_type == 'ul' else 'List Number')
                p.paragraph_format.space_after = Pt(2)
                add_styled_text(p, str(item), font_name=style["font_name"],
                               font_size=style["font_size"])

        elif b_type == "blockquote":
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.4)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            add_styled_text(p, str(val), font_name=style["font_name"],
                           font_size=style["font_size"], force_italic=True,
                           color=RGBColor(80, 80, 80))

        elif b_type == "meta_table":
            # ── DocStudio CertificatePage meta[] pattern ──
            # 2-column key-value table with shaded label column
            items = block.get("items", [])
            if items:
                tbl = doc.add_table(rows=0, cols=2)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_full_width(tbl)

                for item in items:
                    # Get label and value, respecting language
                    label = item.get("label", {})
                    value = item.get("value", {})
                    if isinstance(label, dict):
                        label_text = label.get(lang) or label.get("vn") or label.get("en") or label.get("ja") or ""
                    else:
                        label_text = str(label)
                    if isinstance(value, dict):
                        value_text = value.get(lang) or value.get("vn") or value.get("en") or value.get("ja") or ""
                    else:
                        value_text = str(value)

                    row = tbl.add_row()

                    # Label cell — bold, gray background (DocStudio shaded pattern)
                    label_cell = row.cells[0]
                    label_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                    add_styled_text(label_cell.paragraphs[0], label_text,
                                   font_name=style["font_name"],
                                   font_size=style["font_size"] - 1,
                                   force_bold=True)
                    set_cell_shading(label_cell, "F0F0F0")
                    border_style = {"val": "single", "sz": "4", "color": "AAAAAA"}
                    set_cell_border(label_cell, top=border_style, bottom=border_style,
                                   left=border_style, right=border_style)

                    # Value cell
                    value_cell = row.cells[1]
                    add_styled_text(value_cell.paragraphs[0], value_text,
                                   font_name=style["font_name"],
                                   font_size=style["font_size"] - 1)
                    set_cell_border(value_cell, top=border_style, bottom=border_style,
                                   left=border_style, right=border_style)

                doc.add_paragraph()  # spacing after table

        elif b_type == "table":
            # ── Standard Data Table ──
            raw_headers = block.get("headers", [])
            raw_rows = block.get("rows", [])
            
            # Support both dict format {lang: [...]} and flat list format [...]
            if isinstance(raw_headers, dict):
                headers = raw_headers.get(lang) or raw_headers.get("vn") or []
            elif isinstance(raw_headers, list):
                headers = raw_headers
            else:
                headers = []
            
            if isinstance(raw_rows, dict):
                rows = raw_rows.get(lang) or raw_rows.get("vn") or []
            elif isinstance(raw_rows, list) and raw_rows:
                if isinstance(raw_rows[0], list):
                    rows = raw_rows
                else:
                    rows = []
            else:
                rows = []

            if headers or rows:
                cols_count = len(headers) if headers else (len(rows[0]) if rows else 0)
                if cols_count > 0:
                    # Build full table grid first (headers + all rows)
                    all_rows_data = []
                    if headers:
                        all_rows_data.append(headers)
                    all_rows_data.extend(rows)

                    total_rows = len(all_rows_data)
                    tbl = doc.add_table(rows=total_rows, cols=cols_count)
                    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                    set_table_full_width(tbl)

                    header_border = {"val": "single", "sz": "6", "color": "555555"}
                    data_border = {"val": "single", "sz": "4", "color": "CCCCCC"}

                    # Apply merges if present (colspan/rowspan)
                    merges = block.get("merges", [])
                    merged_cells = set()  # Track (row, col) that are consumed by merge
                    for merge_info in merges:
                        m_row = merge_info.get("row", 0)
                        m_col = merge_info.get("col", 0)
                        m_rowspan = merge_info.get("rowspan", 1)
                        m_colspan = merge_info.get("colspan", 1)
                        # Validate bounds
                        if (m_row + m_rowspan <= total_rows and
                            m_col + m_colspan <= cols_count):
                            try:
                                anchor = tbl.cell(m_row, m_col)
                                target = tbl.cell(m_row + m_rowspan - 1, m_col + m_colspan - 1)
                                anchor.merge(target)
                            except Exception:
                                pass  # Skip invalid merges gracefully
                            # Mark consumed cells
                            for dr in range(m_rowspan):
                                for dc in range(m_colspan):
                                    if dr == 0 and dc == 0:
                                        continue
                                    merged_cells.add((m_row + dr, m_col + dc))

                    # Fill cell content
                    for r_idx, row_data in enumerate(all_rows_data):
                        is_header = (r_idx == 0 and headers)
                        cells_data = row_data if isinstance(row_data, list) else [row_data]
                        for c_idx in range(min(len(cells_data), cols_count)):
                            if (r_idx, c_idx) in merged_cells:
                                continue  # Skip consumed cells

                            cell = tbl.cell(r_idx, c_idx)
                            cell_text = str(cells_data[c_idx])

                            # Clear default empty paragraph if needed
                            if cell.paragraphs and not cell.paragraphs[0].text:
                                p = cell.paragraphs[0]
                            else:
                                p = cell.paragraphs[0]

                            if is_header:
                                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                                add_styled_text(p, cell_text,
                                              font_name=style["font_name"],
                                              font_size=style["font_size"] - 1,
                                              force_bold=True)
                                set_cell_shading(cell, "E8E8E8")
                                set_cell_border(cell, top=header_border, bottom=header_border,
                                              left=header_border, right=header_border)
                            else:
                                add_styled_text(p, cell_text,
                                              font_name=style["font_name"],
                                              font_size=style["font_size"] - 1)
                                set_cell_border(cell, top=data_border, bottom=data_border,
                                              left=data_border, right=data_border)
                    doc.add_paragraph()  # spacing

        elif b_type == "caption":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_styled_text(p, str(val), font_name=style["font_name"],
                           font_size=style["font_size"] - 2, force_italic=True)

        elif b_type == "hr":
            # Horizontal rule — add a thin paragraph border
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(8)
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '6')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), 'CCCCCC')
            pBdr.append(bottom)
            pPr.append(pBdr)

    doc.save(str(output_path))
    print(f"✅ Generated DOCX ({lang.upper()}): {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Export EJV JSON to formatted DOCX document.")
    parser.add_argument("--input", required=True, type=Path, help="Input EJV JSON file")
    parser.add_argument("--output", required=True, type=Path, help="Output DOCX file path")
    parser.add_argument("--lang", default="vn", choices=["vn", "en", "ja", "zh", "cn"], help="Language to export (vn, en, ja, zh, cn)")
    parser.add_argument("--style", default="administrative", choices=["standard", "administrative", "academic"], help="Layout format style")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        blocks = json.load(f)

    build_docx(blocks, args.output, lang=args.lang, style_name=args.style)


if __name__ == "__main__":
    main()
