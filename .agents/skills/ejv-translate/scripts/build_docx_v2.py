#!/usr/bin/env python3
"""Build publication-grade DOCX documents from EJV Trilingual JSON.

Compliant with Vietnamese Administrative Document Standards (Decree 30/2020/NĐ-CP):
- Page Setup: A4, Margins: Top 20mm, Bottom 20mm, Left 30mm, Right 15mm.
- Typography: Times New Roman (VN/EN 13-14pt), MS Mincho/Yu Mincho (JA 12-13pt).
- Page Numbering: Centered Arabic numerals in footer, skipping Page 1 (Decree 30 standard).
- Administrative Header: 2-column borderless table with national motto underline.
- Legal Hierarchy: Chapter (Center Bold), Article (Indent Bold), Clause (Indent Regular), Point (Hanging Indent).
- Sign-off: 2-column borderless table for Recipients (Left) and Signatory / Prime Minister (Right).
- Annexes: Explicit Page Breaks before each Annex, centered bold headers.
- Tables: 100% width, 0.5pt clean borders, shaded headers (#F2F2F2), repeat header across pages (tblHeader), cantSplit.
"""

import argparse
import json
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
from lxml import etree


# ──────────────────────────────────────────────────────────────────────
# XML Helpers
# ──────────────────────────────────────────────────────────────────────

def set_cell_border(cell, **kwargs):
    """Set cell borders with specific thickness and color."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key, val in edge_data.items():
                element.set(qn(f'w:{key}'), str(val))


def clear_cell_borders(cell):
    """Clear all borders for a cell (borderless table)."""
    none_border = {'val': 'none', 'sz': '0', 'space': '0', 'color': 'auto'}
    set_cell_border(cell, top=none_border, bottom=none_border, left=none_border, right=none_border)


def set_table_borders(table, color="B0B0B0", sz="4"):
    """Set clean subtle border for standard tables."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideV w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def set_cell_shading(cell, hex_color: str):
    """Set background fill for cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}" w:val="clear"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set internal cell margins (padding) in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="{top}" w:type="dxa"/>\n'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'  <w:left w:w="{left}" w:type="dxa"/>\n'
        f'  <w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_page_number_to_footer(section, font_name: str = "Times New Roman", font_size: float = 13.0):
    """Add dynamic centered page numbering to footer, skipping page 1 (Decree 30 standard)."""
    section.different_first_page_header_footer = True
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.text = ""
    run = p.add_run()
    run.font.name = font_name
    run.font.size = Pt(font_size)
    fld = parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr="PAGE"/>')
    p._p.append(fld)


# ──────────────────────────────────────────────────────────────────────
# Text Styling Helper
# ──────────────────────────────────────────────────────────────────────

def clean_inline_artifacts(text: str) -> str:
    """Clean inline artifacts like '| DRAFT', leaked page numbers inside sentences."""
    if not text:
        return ""
    t = str(text).strip()
    t = re.sub(r"^\|\s*", "", t)
    # Clean leaked page numbers at beginning of sentences: e.g. '37 Government...' -> 'Government...'
    t = re.sub(r"^(\d{1,3})\s+([A-ZÀ-Ỹa-zà-ỹ])", r"\2", t)
    return t


def add_runs(paragraph, text: str, font_name: str, font_size: float,
             bold: bool = False, italic: bool = False, color: RGBColor = None):
    """Parse inline Markdown and add formatted runs."""
    if not text:
        return

    text = clean_inline_artifacts(text)
    pattern = r'(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*)'
    parts = re.split(pattern, str(text))

    for part in parts:
        if not part:
            continue
        is_b = bold
        is_i = italic
        run_text = part

        if part.startswith('***') and part.endswith('***'):
            run_text = part[3:-3]
            is_b = True
            is_i = True
        elif part.startswith('**') and part.endswith('**'):
            run_text = part[2:-2]
            is_b = True
        elif part.startswith('*') and part.endswith('*'):
            run_text = part[1:-1]
            is_i = True

        run = paragraph.add_run(run_text)
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.bold = is_b
        run.italic = is_i
        if color:
            run.font.color.rgb = color


# ──────────────────────────────────────────────────────────────────────
# Administrative Sign-off Table Builder
# ──────────────────────────────────────────────────────────────────────

def add_signoff_table(doc, recipients_list: list[str], signatory_title: str,
                      authority_title: str, font_name: str, body_size: float, lang: str):
    """Render 2-column borderless Sign-off Table (Nơi nhận & Thủ tướng ký)."""
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Mm(75)
    tbl.columns[1].width = Mm(85)

    cell_left = tbl.cell(0, 0)
    cell_right = tbl.cell(0, 1)
    clear_cell_borders(cell_left)
    clear_cell_borders(cell_right)
    set_cell_margins(cell_left, top=80, bottom=80, left=0, right=80)
    set_cell_margins(cell_right, top=80, bottom=80, left=80, right=0)

    # Left cell: Recipients (Nơi nhận)
    p_rec_hdr = cell_left.paragraphs[0]
    p_rec_hdr.paragraph_format.space_before = Pt(3)
    p_rec_hdr.paragraph_format.space_after = Pt(2)
    
    if lang == "vn":
        rec_title = "Nơi nhận:"
    elif lang == "en":
        rec_title = "Recipients:"
    else:
        rec_title = "送付先："

    add_runs(p_rec_hdr, rec_title, font_name, body_size - 2, bold=True, italic=True)

    for item in recipients_list:
        it_str = str(item).strip()
        if not it_str or it_str.startswith(("Nơi nhận", "Recipients", "送付先")):
            continue
        p_item = cell_left.add_paragraph()
        p_item.paragraph_format.left_indent = Mm(4)
        p_item.paragraph_format.space_after = Pt(1)
        p_item.paragraph_format.line_spacing = 1.0
        bullet = "- " if not it_str.startswith(("-", "•")) else ""
        add_runs(p_item, bullet + it_str.lstrip("• "), font_name, body_size - 2.5)

    # Right cell: Signatory (TM. CHÍNH PHỦ / THỦ TƯỚNG)
    p_auth = cell_right.paragraphs[0]
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_before = Pt(3)
    p_auth.paragraph_format.space_after = Pt(2)
    add_runs(p_auth, authority_title, font_name, body_size, bold=True)

    p_sig = cell_right.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sig.paragraph_format.space_after = Pt(40)  # Blank space for signature & seal
    add_runs(p_sig, signatory_title, font_name, body_size, bold=True)

    p_name = cell_right.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_name.paragraph_format.space_after = Pt(0)
    # Placeholder for signer's full name
    name_str = "(Ký tên, đóng dấu)" if lang == "vn" else ("(Signature and seal)" if lang == "en" else "（署名及び押印）")
    add_runs(p_name, name_str, font_name, body_size - 1, italic=True)

    # Space after signoff table
    p_end = doc.add_paragraph()
    p_end.paragraph_format.space_after = Pt(12)


# ──────────────────────────────────────────────────────────────────────
# Main Administrative Document Builder
# ──────────────────────────────────────────────────────────────────────

def create_admin_docx(blocks: list[dict], output_path: Path, lang: str = "vn"):
    doc = Document()
    
    # Page setup according to Decree 30/2020/NĐ-CP (A4)
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(20)
    section.bottom_margin = Mm(20)
    section.left_margin = Mm(30)
    section.right_margin = Mm(20)

    # Font selection
    if lang == "ja":
        font_name = "MS Mincho"
        body_size = 12.0
    else:
        font_name = "Times New Roman"
        body_size = 13.0

    # Add dynamic centered page numbering to footer
    add_page_number_to_footer(section, font_name=font_name, font_size=body_size)

    # Render National Administrative Header on First Page (6.0cm and 10.0cm split)
    header_tbl = doc.add_table(rows=1, cols=2)
    header_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_tbl.autofit = False
    header_tbl.columns[0].width = Mm(60)
    header_tbl.columns[1].width = Mm(100)

    cell_left = header_tbl.cell(0, 0)
    cell_right = header_tbl.cell(0, 1)
    clear_cell_borders(cell_left)
    clear_cell_borders(cell_right)

    # Left cell: Agency + Reference No.
    p_org = cell_left.paragraphs[0]
    p_org.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_org.paragraph_format.space_after = Pt(2)
    
    if lang == "vn":
        org_title = "CHÍNH PHỦ"
        ref_no = "Số:       /2026/NĐ-CP"
    elif lang == "en":
        org_title = "THE GOVERNMENT"
        ref_no = "No.:       /2026/ND-CP"
    else:
        org_title = "ベトナム社会主義共和国政府"
        ref_no = "第       /2026/ND-CP号"

    add_runs(p_org, org_title, font_name, body_size - 1, bold=True)
    
    # Separator rule under org
    p_org_rule = cell_left.add_paragraph()
    p_org_rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_org_rule.paragraph_format.space_after = Pt(4)
    run_rule = p_org_rule.add_run("———————")
    run_rule.font.name = font_name
    run_rule.font.size = Pt(body_size - 4)

    p_ref = cell_left.add_paragraph()
    p_ref.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ref.paragraph_format.space_after = Pt(0)
    add_runs(p_ref, ref_no, font_name, body_size - 1, bold=False)

    # Right cell: Country + Motto + Date
    p_country = cell_right.paragraphs[0]
    p_country.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_country.paragraph_format.space_after = Pt(2)
    
    if lang == "vn":
        country_name = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"
        motto = "Độc lập - Tự do - Hạnh phúc"
        date_str = "Hà Nội, ngày      tháng      năm 2026"
    elif lang == "en":
        country_name = "SOCIALIST REPUBLIC OF VIETNAM"
        motto = "Independence - Freedom - Happiness"
        date_str = "Hanoi, [Day] [Month] 2026"
    else:
        country_name = "ベトナム社会主義共和国"
        motto = "独立・自由・幸福"
        date_str = "ハノイ、2026年  月  日"

    add_runs(p_country, country_name, font_name, body_size - 1, bold=True)

    p_motto = cell_right.add_paragraph()
    p_motto.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_motto.paragraph_format.space_after = Pt(2)
    add_runs(p_motto, motto, font_name, body_size, bold=True)

    # Motto underline
    p_motto_rule = cell_right.add_paragraph()
    p_motto_rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_motto_rule.paragraph_format.space_after = Pt(4)
    run_mrule = p_motto_rule.add_run("—————————————")
    run_mrule.font.name = font_name
    run_mrule.font.size = Pt(body_size - 4)

    p_date = cell_right.add_paragraph()
    p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_date.paragraph_format.space_after = Pt(0)
    add_runs(p_date, date_str, font_name, body_size, italic=True)

    # Space after header table
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(8)
    p_space.paragraph_format.space_after = Pt(0)

    # Title: DỰ THẢO
    p_draft = doc.add_paragraph()
    p_draft.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_draft.paragraph_format.space_before = Pt(6)
    p_draft.paragraph_format.space_after = Pt(4)
    
    if lang == "vn":
        draft_text = "DỰ THẢO"
        decree_name = "NGHỊ ĐỊNH"
        decree_desc = "Quy định về quản lý mỹ phẩm"
    elif lang == "en":
        draft_text = "DRAFT"
        decree_name = "DECREE"
        decree_desc = "Providing Regulations on the Management of Cosmetics"
    else:
        draft_text = "草案"
        decree_name = "政令"
        decree_desc = "化粧品管理に関する政令"

    add_runs(p_draft, draft_text, font_name, body_size + 2, bold=True)

    # Title: NGHỊ ĐỊNH
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(2)
    add_runs(p_title, decree_name, font_name, body_size + 2, bold=True)

    # Subtitle: Quy định về...
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(2)
    p_sub.paragraph_format.space_after = Pt(12)
    add_runs(p_sub, decree_desc, font_name, body_size + 1, bold=True)

    # Skip first header blocks if already represented by administrative header
    start_idx = 0
    while start_idx < len(blocks) and start_idx < 10:
        v_check = str(blocks[start_idx].get("vn", "")).strip()
        if (v_check.startswith(("CHÍNH PHỦ", "Độc lập", "Hà Nội", "DỰ THẢO", "NGHỊ ĐỊNH Quy định", "13/05/2026")) or
            "anhnn.qld" in v_check):
            start_idx += 1
        else:
            break

    # Main Rendering Loop
    i = start_idx
    total_blocks = len(blocks)

    while i < total_blocks:
        block = blocks[i]
        b_type = block.get("type", "p")
        raw_val = block.get(lang) or block.get("vn") or block.get("en") or block.get("ja") or ""

        # Check for Decree Sign-off block (Recipients list followed by TM. CHÍNH PHỦ)
        if b_type in {"ul", "ol"} and isinstance(raw_val, list) and len(raw_val) > 0:
            first_it = str(raw_val[0]).strip()
            if first_it.startswith(("Nơi nhận:", "Recipients:", "送付先：")):
                # Lookahead to see if next block is Signatory
                auth_title = "TM. CHÍNH PHỦ" if lang == "vn" else ("ON BEHALF OF THE GOVERNMENT" if lang == "en" else "ベトナム社会主義共和国政府")
                sig_title = "THỦ TƯỚNG" if lang == "vn" else ("PRIME MINISTER" if lang == "en" else "首相")
                
                # Check next 1-2 blocks for signatory
                j = i + 1
                while j < min(i + 3, total_blocks):
                    n_val = str(blocks[j].get(lang) or blocks[j].get("vn") or "").strip()
                    if "CHÍNH PHỦ" in n_val or "GOVERNMENT" in n_val:
                        auth_title = n_val
                    if "THỦ TƯỚNG" in n_val or "PRIME MINISTER" in n_val or "首相" in n_val:
                        sig_title = n_val
                    j += 1

                add_signoff_table(doc, raw_val, sig_title, auth_title, font_name, body_size, lang)
                i = j  # Skip consumed blocks
                continue

        # Check for Annex Heading -> Insert Page Break
        val_str = str(raw_val).strip() if isinstance(raw_val, str) else ""
        if val_str.startswith(("Phụ lục I", "Phụ lục II", "Phụ lục III", "Phụ lục IV", "Phụ lục V",
                               "Annex I", "Annex II", "Annex III", "Annex IV", "Annex V",
                               "附録I", "附録II", "附録III", "附録IV", "附録V", "附属書")):
            doc.add_page_break()
            p_annex = doc.add_paragraph()
            p_annex.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_annex.paragraph_format.space_before = Pt(14)
            p_annex.paragraph_format.space_after = Pt(8)
            add_runs(p_annex, val_str, font_name, body_size + 1, bold=True)
            i += 1
            continue

        # Chapter
        if b_type == "chapter" or (isinstance(raw_val, str) and (val_str.startswith(("Chương ", "Chapter ")) or (val_str.startswith("第") and "章" in val_str))):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(8)
            add_runs(p, val_str, font_name, body_size + 1, bold=True)

        # Article (Điều)
        elif b_type == "article" or (isinstance(raw_val, str) and (val_str.startswith(("Điều ", "Article ")) or (val_str.startswith("第") and "条" in val_str))):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Mm(12.5)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.3
            add_runs(p, val_str, font_name, body_size, bold=True)

        # Clause (Khoản)
        elif b_type == "clause":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Mm(12.5)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.3
            add_runs(p, val_str, font_name, body_size, bold=False)

        # Point (Điểm)
        elif b_type == "point":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Mm(12.5)
            p.paragraph_format.left_indent = Mm(0)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.3
            add_runs(p, val_str, font_name, body_size, bold=False)

        # Headings
        elif b_type == "h1":
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(8)
            add_runs(p, val_str.upper(), font_name, body_size + 1, bold=True)

        elif b_type in {"h2", "h3"}:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.first_line_indent = Mm(12.5)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            add_runs(p, val_str, font_name, body_size, bold=True)

        # Normal Paragraph / Preamble
        elif b_type == "p":
            if not val_str:
                i += 1
                continue

            # Check if this is Form Representative Signature line
            if "REPRESENTATIVE OF THE AGENCY" in val_str or "ĐẠI DIỆN ĐƠN VỊ" in val_str or "機関代表者" in val_str or "ĐẠI DIỆN CƠ SỞ" in val_str:
                p_rep = doc.add_paragraph()
                p_rep.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                p_rep.paragraph_format.space_before = Pt(12)
                p_rep.paragraph_format.space_after = Pt(2)
                add_runs(p_rep, val_str, font_name, body_size, bold=True)
                i += 1
                continue

            if "(Signature, full name, and seal)" in val_str or "(Ký tên, ghi rõ họ tên và đóng dấu)" in val_str or "（署名、氏名明記及び押印）" in val_str:
                p_sig = doc.add_paragraph()
                p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                p_sig.paragraph_format.space_after = Pt(30)
                add_runs(p_sig, val_str, font_name, body_size - 1, italic=True)
                i += 1
                continue

            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Mm(12.5)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.3
            
            # Preamble italic style if starts with Căn cứ / Pursuant to
            is_preamble = val_str.startswith(("Căn cứ ", "Pursuant to ", "Theo đề nghị", "At the proposal", "に基づき"))
            add_runs(p, val_str, font_name, body_size, italic=is_preamble)

        # Unordered or Ordered list
        elif b_type in {"ul", "ol"}:
            items = raw_val if isinstance(raw_val, list) else [raw_val]
            for item in items:
                it_str = str(item).strip()
                if not it_str:
                    continue
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.first_line_indent = Mm(12.5)
                p.paragraph_format.left_indent = Mm(0)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.3
                if b_type == "ul":
                    clean_item = it_str.lstrip("• ")
                    add_runs(p, "- " + clean_item, font_name, body_size)
                else:
                    add_runs(p, it_str, font_name, body_size)

        # Table rendering (with merge cell support)
        elif b_type == "table":
            headers_dict = block.get("headers", {})
            rows_dict = block.get("rows", {})
            merges_data = block.get("merges", [])

            if isinstance(headers_dict, dict):
                headers = headers_dict.get(lang) or headers_dict.get("vn") or []
            else:
                headers = headers_dict or []

            if isinstance(rows_dict, dict):
                rows = rows_dict.get(lang) or rows_dict.get("vn") or []
            else:
                rows = rows_dict or []

            num_cols = len(headers) if headers else (max(len(r) for r in rows) if rows else 0)
            if num_cols == 0:
                i += 1
                continue

            # Determine if we have merge metadata
            has_merges = bool(merges_data) and any(
                m.get("rowspan", 1) > 1 or m.get("colspan", 1) > 1
                for m in merges_data
            )

            if has_merges:
                # ── Merge-aware rendering ──
                # Pre-allocate full grid (header + data rows)
                total_rows = 1 + len(rows) if headers else len(rows)
                tbl = doc.add_table(rows=total_rows, cols=num_cols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl, color="B0B0B0", sz="4")

                # Track which cells are consumed by merges
                consumed = [[False] * num_cols for _ in range(total_rows)]

                # Apply merges BEFORE filling content
                for merge in merges_data:
                    m_row = merge.get("row", 0)
                    m_col = merge.get("col", 0)
                    m_rs = merge.get("rowspan", 1)
                    m_cs = merge.get("colspan", 1)

                    if m_row >= total_rows or m_col >= num_cols:
                        continue  # Skip out-of-bounds merges

                    end_row = min(m_row + m_rs - 1, total_rows - 1)
                    end_col = min(m_col + m_cs - 1, num_cols - 1)

                    if m_rs > 1 or m_cs > 1:
                        try:
                            start_cell = tbl.cell(m_row, m_col)
                            end_cell = tbl.cell(end_row, end_col)
                            start_cell.merge(end_cell)
                        except Exception:
                            pass  # Graceful: skip invalid merges

                        # Mark consumed cells (excluding anchor)
                        for dr in range(m_rs):
                            for dc in range(m_cs):
                                if dr == 0 and dc == 0:
                                    continue
                                r_idx = m_row + dr
                                c_idx = m_col + dc
                                if r_idx < total_rows and c_idx < num_cols:
                                    consumed[r_idx][c_idx] = True

                # Fill header row
                header_offset = 0
                if headers:
                    header_offset = 1
                    hdr_row = tbl.rows[0]
                    trPr = hdr_row._tr.get_or_add_trPr()
                    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
                    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

                    for c_idx, h_text in enumerate(headers):
                        if consumed[0][c_idx]:
                            continue
                        cell = tbl.cell(0, c_idx)
                        set_cell_shading(cell, "EAEAEA")
                        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
                        p_cell = cell.paragraphs[0]
                        p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_cell.paragraph_format.space_after = Pt(0)
                        add_runs(p_cell, str(h_text), font_name, body_size - 1, bold=True)

                # Fill data rows
                for r_idx, r_data in enumerate(rows):
                    grid_row = r_idx + header_offset
                    if grid_row >= total_rows:
                        break
                    row_obj = tbl.rows[grid_row]
                    trPr = row_obj._tr.get_or_add_trPr()
                    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

                    for c_idx in range(num_cols):
                        if consumed[grid_row][c_idx]:
                            continue
                        cell = tbl.cell(grid_row, c_idx)
                        cell_val = str(r_data[c_idx]) if c_idx < len(r_data) else ""
                        set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                        p_cell = cell.paragraphs[0]
                        p_cell.paragraph_format.space_after = Pt(0)
                        if cell_val.isdigit() or cell_val in {"-", "..."}:
                            p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        else:
                            p_cell.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        add_runs(p_cell, cell_val, font_name, body_size - 1)

            else:
                # ── Simple table rendering (no merges, original logic) ──
                tbl = doc.add_table(rows=0, cols=num_cols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl, color="B0B0B0", sz="4")

                # Header row
                if headers:
                    hdr_row = tbl.add_row()
                    trPr = hdr_row._tr.get_or_add_trPr()
                    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
                    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

                    for c_idx, h_text in enumerate(headers):
                        cell = hdr_row.cells[c_idx]
                        set_cell_shading(cell, "EAEAEA")
                        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
                        p_cell = cell.paragraphs[0]
                        p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_cell.paragraph_format.space_after = Pt(0)
                        add_runs(p_cell, str(h_text), font_name, body_size - 1, bold=True)

                # Data rows
                for r_data in rows:
                    row = tbl.add_row()
                    trPr = row._tr.get_or_add_trPr()
                    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

                    for c_idx in range(num_cols):
                        cell = row.cells[c_idx]
                        cell_val = str(r_data[c_idx]) if c_idx < len(r_data) else ""
                        set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                        p_cell = cell.paragraphs[0]
                        p_cell.paragraph_format.space_after = Pt(0)
                        if cell_val.isdigit() or cell_val in {"-", "..."}:
                            p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        else:
                            p_cell.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        add_runs(p_cell, cell_val, font_name, body_size - 1)

            p_post = doc.add_paragraph()
            p_post.paragraph_format.space_before = Pt(4)
            p_post.paragraph_format.space_after = Pt(4)

        # Meta Table rendering
        elif b_type == "meta_table":
            items = block.get("items", [])
            if items:
                tbl = doc.add_table(rows=0, cols=2)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(tbl, color="B0B0B0", sz="4")
                tbl.columns[0].width = Mm(55)
                tbl.columns[1].width = Mm(105)

                for item in items:
                    lbl = item.get("label", {})
                    val = item.get("value", {})
                    lbl_text = lbl.get(lang) or lbl.get("vn") if isinstance(lbl, dict) else str(lbl)
                    val_text = val.get(lang) or val.get("vn") if isinstance(val, dict) else str(val)

                    row = tbl.add_row()
                    trPr = row._tr.get_or_add_trPr()
                    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

                    cell_0 = row.cells[0]
                    set_cell_shading(cell_0, "F4F4F4")
                    set_cell_margins(cell_0, top=80, bottom=80, left=120, right=120)
                    p0 = cell_0.paragraphs[0]
                    p0.paragraph_format.space_after = Pt(0)
                    add_runs(p0, str(lbl_text), font_name, body_size - 1, bold=True)

                    cell_1 = row.cells[1]
                    set_cell_margins(cell_1, top=80, bottom=80, left=120, right=120)
                    p1 = cell_1.paragraphs[0]
                    p1.paragraph_format.space_after = Pt(0)
                    add_runs(p1, str(val_text), font_name, body_size - 1)

                p_post = doc.add_paragraph()
                p_post.paragraph_format.space_before = Pt(4)
                p_post.paragraph_format.space_after = Pt(4)

        i += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"✅ Created Publication-grade Administrative DOCX ({lang.upper()}): {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Build publication-grade DOCX documents.")
    parser.add_argument("--input", required=True, type=Path, help="Input clean_structured_ejv.json")
    parser.add_argument("--output", required=True, type=Path, help="Output DOCX file")
    parser.add_argument("--lang", choices=["vn", "en", "ja", "zh", "cn"], default="en", help="Target language")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        blocks = json.load(f)

    create_admin_docx(blocks, args.output, lang=args.lang)


if __name__ == "__main__":
    main()
