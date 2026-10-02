#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_legal_docx.py — Bộ xuất bản Báo cáo Tư vấn Pháp lý chuẩn mực DOCX (Executive Legal Report)
Tuân thủ:
- Rule R4: Zero External LLM API (chạy 100% bằng python-docx nội bộ)
- Rule R1: Anti-Repo Bloat (xuất file vào <output_dir> do người dùng chỉ định)
- Rule R2: Code Quality (Zero-inference, không hardcode credentials, không nuốt lỗi ngầm)

Hỗ trợ chuyển đổi Markdown báo cáo pháp lý thành tài liệu Word (.docx) chất lượng cao:
- Bố cục trang A4 chuẩn hành chính (Lề trái 2.5cm, phải 2.0cm, trên/dưới 2.0cm)
- Kiểu chữ Times New Roman 12pt, dãn dòng 1.2, màu chữ than cao cấp #2D3748
- Hệ thống tiêu đề phân cấp trực quan với màu chủ đạo Deep Navy (#1A365D)
- Bảng biểu (Tables) tự động căn chỉnh, viền xám nhạt, dòng tiêu đề Navy đậm chữ trắng, zebra striping
- Khối cảnh báo/ghi chú (Callouts / Quotes) đóng khung thẩm mỹ kèm đường viền xanh Navy
- Highlight chuyên biệt các cờ phân loại mức độ chắc chắn: [XÁC ĐỊNH], [SUY LUẬN ÁP DỤNG], [GIẢ ĐỊNH / CHƯA XÁC MINH]
- Đánh số trang tự động ở chân trang (Footer)
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

try:
    import docx
    from docx import Document
    from docx.shared import Pt, Cm, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import qn, nsdecls
except ImportError:
    print("❌ Lỗi: Thư viện 'python-docx' chưa được cài đặt. Vui lòng chạy: pip install python-docx")
    sys.exit(1)

# Bảng mã màu chuyên nghiệp cho Báo cáo Pháp lý (Executive Navy Palette)
COLOR_NAVY_DARK = RGBColor(0x1A, 0x36, 0x5D)    # #1A365D - Tiêu đề chính H1, H2, Header bảng
COLOR_NAVY_MEDIUM = RGBColor(0x2B, 0x6C, 0xB0)  # #2B6CB0 - Tiêu đề phụ H3, đường dẫn
COLOR_TEXT_MAIN = RGBColor(0x2D, 0x37, 0x48)    # #2D3748 - Chữ văn bản than đậm dịu mắt
COLOR_TEXT_MUTED = RGBColor(0x71, 0x80, 0x96)   # #718096 - Metadata, chú thích
COLOR_GREEN = RGBColor(0x22, 0x54, 0x3D)        # #22543D - [XÁC ĐỊNH]
COLOR_BLUE = RGBColor(0x2B, 0x6C, 0xB0)         # #2B6CB0 - [SUY LUẬN ÁP DỤNG]
COLOR_ORANGE = RGBColor(0xC0, 0x56, 0x21)       # #C05621 - [GIẢ ĐỊNH / CHƯA XÁC MINH]
COLOR_RED = RGBColor(0x9B, 0x2C, 0x2C)          # #9B2C2C - [CẢNH BÁO / KHẨN CẤP]

HEX_NAVY_HEADER = "1A365D"
HEX_ZEBRA_ROW = "F7FAFC"
HEX_WHITE = "FFFFFF"
HEX_BORDER = "CBD5E0"
HEX_CALLOUT_BG = "F7FAFC"
HEX_CALLOUT_BORDER = "2B6CB0"


def set_run_font(run, font_name="Times New Roman", font_size=11.5, bold=False, italic=False, color=None):
    """Thiết lập định dạng font chuẩn xác cho Run."""
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    # Thiết lập font cho ký tự tiếng Á Đông (Nhật, Hán, Việt)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), font_name)
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)


def set_cell_background(cell, fill_hex: str):
    """Tô màu nền cho ô trong bảng."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))


def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    """Thiết lập padding trong ô của bảng (đơn vị dxa: 20 dxa = 1 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def set_table_borders(table, border_hex="CBD5E0"):
    """Thiết lập viền tinh tế cho toàn bảng."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{border_hex}"/>'
        f'<w:left w:val="none"/>'
        f'<w:bottom w:val="single" w:sz="12" w:space="0" w:color="{border_hex}"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{border_hex}"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{border_hex}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def add_formatted_text(paragraph, text: str, base_size=11.5, default_color=COLOR_TEXT_MAIN):
    """Parse cú pháp inline Markdown (in đậm, in nghiêng, code, thẻ phân loại) vào paragraph."""
    # Bóc tách các token Markdown inline
    token_pattern = re.compile(
        r'(\[XÁC ĐỊNH\]|\[SUY LUẬN ÁP DỤNG\]|\[GIẢ ĐỊNH / CHƯA XÁC MINH\]|\[CẦN XÁC MINH[^\]]*\]|\[CẢNH BÁO[^\]]*\]|'
        r'\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\$[^$]+\$|\[[^\]]+\]\([^)]+\)|[^*`$\[]+|\[|\])'
    )
    tokens = token_pattern.findall(text)
    if not tokens:
        tokens = [text]

    for token in tokens:
        if token == "[XÁC ĐỊNH]":
            r = paragraph.add_run("[XÁC ĐỊNH]")
            set_run_font(r, font_size=base_size, bold=True, color=COLOR_GREEN)
        elif token == "[SUY LUẬN ÁP DỤNG]":
            r = paragraph.add_run("[SUY LUẬN ÁP DỤNG]")
            set_run_font(r, font_size=base_size, bold=True, color=COLOR_BLUE)
        elif token.startswith("[GIẢ ĐỊNH") or token.startswith("[CẦN XÁC MINH"):
            r = paragraph.add_run(token)
            set_run_font(r, font_size=base_size, bold=True, color=COLOR_ORANGE)
        elif token.startswith("[CẢNH BÁO"):
            r = paragraph.add_run(token)
            set_run_font(r, font_size=base_size, bold=True, color=COLOR_RED)
        elif token.startswith("**") and token.endswith("**") and len(token) >= 4:
            r = paragraph.add_run(token[2:-2])
            set_run_font(r, font_size=base_size, bold=True, color=COLOR_NAVY_DARK)
        elif token.startswith("*") and token.endswith("*") and not token.startswith("**") and len(token) >= 2:
            r = paragraph.add_run(token[1:-1])
            set_run_font(r, font_size=base_size, italic=True, color=default_color)
        elif token.startswith("`") and token.endswith("`") and len(token) >= 2:
            r = paragraph.add_run(token[1:-1])
            set_run_font(r, font_name="Consolas", font_size=base_size * 0.9, color=COLOR_NAVY_DARK)
        elif token.startswith("$") and token.endswith("$") and len(token) >= 2:
            # LaTeX math inline
            r = paragraph.add_run(token[1:-1])
            set_run_font(r, font_size=base_size, italic=True, color=COLOR_NAVY_MEDIUM)
        elif token.startswith("[") and "](" in token and token.endswith(")"):
            # Markdown link [text](url)
            match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', token)
            if match:
                link_text, link_url = match.group(1), match.group(2)
                r = paragraph.add_run(f"{link_text} ({link_url})")
                set_run_font(r, font_size=base_size, color=COLOR_NAVY_MEDIUM, italic=True)
            else:
                r = paragraph.add_run(token)
                set_run_font(r, font_size=base_size, color=default_color)
        else:
            r = paragraph.add_run(token)
            set_run_font(r, font_size=base_size, color=default_color)


def build_legal_docx(md_path: Path, output_docx_path: Path, title: Optional[str] = None):
    """Chuyển đổi file Markdown báo cáo pháp lý thành file DOCX hoàn chỉnh."""
    if not md_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file nguồn Markdown: {md_path}")

    md_content = md_path.read_text(encoding="utf-8", errors="replace")
    doc = Document()

    # 1. Cấu hình lề trang A4 chuẩn văn bản pháp lý
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.5)   # Lề trái rộng hơn để đóng tập/hồ sơ
    section.right_margin = Cm(2.0)

    # 2. Cấu hình Header & Footer
    header = section.header
    header_para = header.paragraphs[0]
    header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun = header_para.add_run("BÁO CÁO TƯ VẤN PHÁP LÝ & QUẢN TRỊ RỦI RO | AI WORKFORCE")
    set_run_font(hrun, font_size=8.5, italic=True, color=COLOR_TEXT_MUTED)

    footer = section.footer
    footer_para = footer.paragraphs[0]
    footer_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    frun1 = footer_para.add_run("Tài liệu nghiên cứu sơ bộ theo dữ kiện cung cấp — Không thay thế ý kiến tranh tụng tại Tòa án / Phán quyết chính thức")
    set_run_font(frun1, font_size=8.0, italic=True, color=COLOR_TEXT_MUTED)
    frun2 = footer_para.add_run("  |  Trang ")
    set_run_font(frun2, font_size=8.0, color=COLOR_TEXT_MUTED)
    # Thêm trường PAGE động
    fld = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
    frun2._r.append(fld)

    # 3. Duyệt và bóc tách từng dòng Markdown
    lines = md_content.splitlines()
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []
    in_frontmatter = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Bỏ qua YAML frontmatter nếu có
        if i == 0 and stripped == "---":
            in_frontmatter = True
            i += 1
            while i < len(lines) and lines[i].strip() != "---":
                i += 1
            i += 1
            continue

        # Khối Code Block
        if stripped.startswith("```"):
            if in_code_block:
                # Kết thúc code block
                in_code_block = False
                code_text = "\n".join(code_lines)
                table = doc.add_table(rows=1, cols=1)
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = table.cell(0, 0)
                set_cell_background(cell, "F1F5F9")
                set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
                cp = cell.paragraphs[0]
                cp.paragraph_format.space_before = Pt(2)
                cp.paragraph_format.space_after = Pt(2)
                cp.paragraph_format.line_spacing = 1.05
                r = cp.add_run(code_text)
                set_run_font(r, font_name="Consolas", font_size=9.5, color=COLOR_NAVY_DARK)
                code_lines = []
                # Thêm khoảng trống sau khối code
                p_spacer = doc.add_paragraph()
                p_spacer.paragraph_format.space_after = Pt(4)
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Khối Bảng (Table Markdown)
        if "|" in line and stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(line)
            i += 1
            continue
        elif in_table:
            # Kết thúc thu thập bảng -> Dựng bảng Word
            render_markdown_table(doc, table_lines)
            in_table = False
            table_lines = []
            # Tiếp tục xử lý dòng hiện tại (không nhảy i)

        # Xử lý các dòng đơn lẻ
        if not stripped:
            i += 1
            continue

        # Tiêu đề H1
        if stripped.startswith("# "):
            h_text = stripped[2:].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(10)
            p.paragraph_format.line_spacing = 1.2
            r = p.add_run(h_text)
            set_run_font(r, font_size=16.0, bold=True, color=COLOR_NAVY_DARK)
            # Thêm đường viền trang trí gạch dưới tiêu đề H1
            p_line = doc.add_paragraph()
            p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_line.paragraph_format.space_after = Pt(12)
            r_dec = p_line.add_run("❖ ❖ ❖")
            set_run_font(r_dec, font_size=9.0, color=COLOR_NAVY_MEDIUM)
            i += 1
            continue

        # Tiêu đề H2
        if stripped.startswith("## "):
            h_text = stripped[3:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            r = p.add_run(h_text)
            set_run_font(r, font_size=13.5, bold=True, color=COLOR_NAVY_DARK)
            i += 1
            continue

        # Tiêu đề H3
        if stripped.startswith("### "):
            h_text = stripped[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            r = p.add_run(h_text)
            set_run_font(r, font_size=12.0, bold=True, color=COLOR_NAVY_MEDIUM)
            i += 1
            continue

        # Tiêu đề H4
        if stripped.startswith("#### "):
            h_text = stripped[5:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            r = p.add_run(h_text)
            set_run_font(r, font_size=11.5, bold=True, italic=True, color=COLOR_TEXT_MAIN)
            i += 1
            continue

        # Đường kẻ ngang phân cách (Horizontal Rule)
        if stripped in ["---", "***", "___"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run("—" * 32)
            set_run_font(r, font_size=8.0, color=RGBColor(0xCB, 0xD5, 0xE0))
            i += 1
            continue

        # Khối Trích dẫn / Callout Box (> ...)
        if stripped.startswith(">"):
            callout_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                c_line = lines[i].strip()[1:].strip()
                callout_lines.append(c_line)
                i += 1
            render_callout_box(doc, callout_lines)
            continue

        # Danh sách không thứ tự (Bullet List: - hoặc *)
        if re.match(r'^[-*•]\s+', stripped):
            item_text = re.sub(r'^[-*•]\s+', '', stripped)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            # Dấu chấm tròn
            rb = p.add_run("•  ")
            set_run_font(rb, font_size=10.0, bold=True, color=COLOR_NAVY_MEDIUM)
            add_formatted_text(p, item_text, base_size=11.5)
            i += 1
            continue

        # Danh sách có thứ tự (Numbered List: 1. , 2. )
        num_match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if num_match:
            num_str = num_match.group(1)
            item_text = num_match.group(2)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            rn = p.add_run(f"{num_str}. ")
            set_run_font(rn, font_size=11.5, bold=True, color=COLOR_NAVY_DARK)
            add_formatted_text(p, item_text, base_size=11.5)
            i += 1
            continue

        # Đoạn văn thông thường
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.2
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_formatted_text(p, stripped, base_size=11.5)
        i += 1

    # Nếu file kết thúc khi bảng chưa render
    if in_table and table_lines:
        render_markdown_table(doc, table_lines)

    # 4. Lưu tài liệu
    output_docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_docx_path))
    return output_docx_path


def render_markdown_table(doc: Document, raw_lines: List[str]):
    """Biến đổi các dòng Markdown Table thành Bảng Word được thiết kế chuyên nghiệp."""
    cleaned_rows = []
    alignments = []

    for line in raw_lines:
        s = line.strip()
        if not s.startswith("|") or not s.endswith("|"):
            continue
        cells = [c.strip() for c in s[1:-1].split("|")]
        # Bỏ qua dòng phân cách |---|---|
        if all(re.match(r'^:?-+:?$', c) for c in cells if c):
            # Lưu alignment nếu có
            for c in cells:
                if c.startswith(":") and c.endswith(":"):
                    alignments.append(WD_ALIGN_PARAGRAPH.CENTER)
                elif c.endswith(":"):
                    alignments.append(WD_ALIGN_PARAGRAPH.RIGHT)
                else:
                    alignments.append(WD_ALIGN_PARAGRAPH.LEFT)
            continue
        cleaned_rows.append(cells)

    if not cleaned_rows:
        return

    num_rows = len(cleaned_rows)
    num_cols = max(len(r) for r in cleaned_rows)

    table = doc.add_table(rows=num_rows, cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, HEX_BORDER)

    for r_idx, row_data in enumerate(cleaned_rows):
        is_header = (r_idx == 0)
        row = table.rows[r_idx]
        # Đánh dấu lặp lại Header nếu bảng dài qua trang mới
        if is_header:
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

        for c_idx in range(num_cols):
            cell = row.cells[c_idx]
            cell_text = row_data[c_idx] if c_idx < len(row_data) else ""
            align = alignments[c_idx] if c_idx < len(alignments) else WD_ALIGN_PARAGRAPH.LEFT

            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)

            # Nền ô
            if is_header:
                set_cell_background(cell, HEX_NAVY_HEADER)
            elif r_idx % 2 == 1:
                set_cell_background(cell, HEX_ZEBRA_ROW)
            else:
                set_cell_background(cell, HEX_WHITE)

            # Text trong ô
            p = cell.paragraphs[0]
            p.alignment = align
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.1

            if is_header:
                # Text tiêu đề bảng
                clean_header_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell_text)
                r = p.add_run(clean_header_text)
                set_run_font(r, font_size=10.5, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
            else:
                add_formatted_text(p, cell_text, base_size=10.0)

    # Thêm paragraph trống phía sau bảng
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(6)


def render_callout_box(doc: Document, callout_lines: List[str]):
    """Vẽ khối Callout Box phong cách Executive Report (Single Cell Table có viền trái Navy)."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_background(cell, HEX_CALLOUT_BG)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)

    # Đặt viền trái đậm 4.5pt (#2B6CB0), các viền khác trong suốt
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="{HEX_CALLOUT_BORDER}"/>'
        f'<w:top w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

    for idx, c_line in enumerate(callout_lines):
        p = cell.paragraphs[0] if idx == 0 else cell.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15

        # Nhận diện thẻ cảnh báo đặc biệt [!NOTE], [!WARNING], [!CAUTION], [!IMPORTANT]
        if "[!NOTE]" in c_line:
            r = p.add_run("📌 LƯU Ý PHÁP LÝ: ")
            set_run_font(r, font_size=10.5, bold=True, color=COLOR_NAVY_MEDIUM)
            c_line = c_line.replace("[!NOTE]", "").strip()
        elif "[!WARNING]" in c_line or "[!CAUTION]" in c_line:
            r = p.add_run("⚠️ CẢNH BÁO RỦI RO TRỌNG YẾU: ")
            set_run_font(r, font_size=10.5, bold=True, color=COLOR_ORANGE)
            c_line = c_line.replace("[!WARNING]", "").replace("[!CAUTION]", "").strip()
        elif "[!IMPORTANT]" in c_line:
            r = p.add_run("⚖️ QUY ĐỊNH BẮT BUỘC: ")
            set_run_font(r, font_size=10.5, bold=True, color=COLOR_NAVY_DARK)
            c_line = c_line.replace("[!IMPORTANT]", "").strip()

        if c_line:
            add_formatted_text(p, c_line, base_size=10.5, default_color=COLOR_TEXT_MAIN)

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)


def main():
    parser = argparse.ArgumentParser(
        description="Xuất bản Báo cáo Tư vấn Pháp lý (Việt Nam & Nhật Bản) từ Markdown sang Word DOCX chuẩn mực."
    )
    parser.add_argument("--input", "-i", required=True, type=Path, help="Đường dẫn file Markdown báo cáo pháp lý (.md)")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Đường dẫn file Word đầu ra (.docx). Mặc định cùng thư mục với file MD.")
    parser.add_argument("--title", "-t", type=str, default=None, help="Tiêu đề tùy chỉnh cho báo cáo")
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.exists():
        print(f"❌ Lỗi: File nguồn không tồn tại: {input_path}")
        sys.exit(1)

    if args.output:
        output_path = args.output.resolve()
    else:
        output_path = input_path.with_suffix(".docx")

    try:
        res = build_legal_docx(input_path, output_path, title=args.title)
        print(f"✅ Đã xuất bản thành công Báo cáo Pháp lý DOCX tại:")
        print(f"   📄 {res}")
    except Exception as e:
        print(f"❌ Lỗi khi chuyển đổi DOCX: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
