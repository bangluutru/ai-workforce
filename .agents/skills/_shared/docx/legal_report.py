#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
legal_report.py — Engine dùng chung (Luật R7, id: docx.legal_report): xuất Báo cáo Tư vấn Pháp lý
(Markdown → DOCX) cho tu-van-phap-luat và tu-van-phap-luat-nhat-ban. Chỉ tồn tại MỘT bản tại đây.

Tuân thủ: Zero External LLM API (python-docx), Anti-Repo Bloat (ghi vào <output_dir>).

Định dạng hỗ trợ:
- Tiêu đề #..###### (cấp ≥4 dùng chung kiểu H4), đoạn văn, danh sách (lồng theo thụt lề), bảng Markdown
  (độ rộng cột theo nội dung: cột trích dẫn dài được rộng hơn), khối trích dẫn/callout ([!NOTE] [!WARNING]
  [!CAUTION] [!IMPORTANT]), code block, đường kẻ ngang (viền, không dùng ký tự gạch dài).
- Inline: **đậm**, *nghiêng* (chỉ khi dấu * sát chữ: "2 * 3" giữ nguyên), `code`, [link](url).
- Ký hiệu tiền "$50.000" giữ nguyên. Chỉ $...$ có lệnh LaTeX (\\text, \\times, _ , ^) mới được đổi sang chữ
  thường; dòng $$...$$ thành công thức chữ thường căn giữa. Không bao giờ in "\\text{...}" ra file.
- Cờ độ tin cậy được tô màu: [XÁC ĐỊNH], [SUY LUẬN ÁP DỤNG], [GIẢ ĐỊNH ...], [Giả định ...],
  [CẦN XÁC MINH ...], [CHƯA XÁC MINH ...], [CẢNH BÁO ...], [Web].
- Font: Times New Roman cho chữ Latinh/tiếng Việt; ô eastAsia dùng font Nhật (--cjk-font, mặc định
  "Yu Mincho"; Word tự thay bằng font Nhật có sẵn nếu máy thiếu, nhờ lang eastAsia=ja-JP).
- Số trang: trường PAGE / NUMPAGES đặt đúng cấp đoạn văn ở chân trang.

Cách dùng (từ thư mục workspace AIWF):
  python3 .agents/skills/_shared/docx/legal_report.py --input report.md [--output report.docx]
         [--title "Tiêu đề"] [--cjk-font "Yu Mincho"]
"""

import argparse
import math
import re
import sys
import unicodedata
from pathlib import Path
from typing import List, Optional

try:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn
    from docx.shared import Cm, Pt, RGBColor
except ImportError:
    print("❌ Lỗi: thiếu thư viện 'python-docx'. Chạy: pip3 install python-docx")
    sys.exit(1)

COLOR_NAVY_DARK = RGBColor(0x1A, 0x36, 0x5D)
COLOR_NAVY_MEDIUM = RGBColor(0x2B, 0x6C, 0xB0)
COLOR_TEXT_MAIN = RGBColor(0x2D, 0x37, 0x48)
COLOR_TEXT_MUTED = RGBColor(0x71, 0x80, 0x96)
COLOR_GREEN = RGBColor(0x22, 0x54, 0x3D)
COLOR_BLUE = RGBColor(0x2B, 0x6C, 0xB0)
COLOR_ORANGE = RGBColor(0xC0, 0x56, 0x21)
COLOR_RED = RGBColor(0x9B, 0x2C, 0x2C)
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)

HEX_NAVY_HEADER = "1A365D"
HEX_ZEBRA_ROW = "F7FAFC"
HEX_WHITE = "FFFFFF"
HEX_BORDER = "CBD5E0"
HEX_CALLOUT_BG = "F7FAFC"
HEX_CALLOUT_BORDER = "2B6CB0"

LATIN_FONT = "Times New Roman"
CJK_FONT = "Yu Mincho"
CONTENT_WIDTH_CM = 21.0 - 2.5 - 2.0

# ---------------------------------------------------------------------------
# Font & run helpers
# ---------------------------------------------------------------------------


def set_run_font(run, font_name=None, font_size=11.5, bold=False, italic=False, color=None):
    font_name = font_name or LATIN_FONT
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)
    rFonts.set(qn("w:cs"), font_name)
    rFonts.set(qn("w:eastAsia"), CJK_FONT)


def configure_document_defaults(doc):
    """Font mặc định của tài liệu: Latinh = Times New Roman, eastAsia = font Nhật, lang eastAsia = ja-JP."""
    styles = doc.styles.element
    rpr_default = styles.find(qn("w:docDefaults"))
    if rpr_default is None:
        return
    rPrDefault = rpr_default.find(qn("w:rPrDefault"))
    if rPrDefault is None:
        return
    rPr = rPrDefault.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        rPrDefault.append(rPr)
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in list(rFonts.attrib):
        if "Theme" in attr:
            del rFonts.attrib[attr]
    rFonts.set(qn("w:ascii"), LATIN_FONT)
    rFonts.set(qn("w:hAnsi"), LATIN_FONT)
    rFonts.set(qn("w:cs"), LATIN_FONT)
    rFonts.set(qn("w:eastAsia"), CJK_FONT)
    lang = rPr.find(qn("w:lang"))
    if lang is None:
        lang = OxmlElement("w:lang")
        rPr.append(lang)
    lang.set(qn("w:val"), "vi-VN")
    lang.set(qn("w:eastAsia"), "ja-JP")


def set_cell_background(cell, fill_hex: str):
    cell._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{fill_hex}"/>'))


def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    cell._tc.get_or_add_tcPr().append(parse_xml(
        f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>'))


def set_table_borders(table, border_hex=HEX_BORDER):
    table._tbl.tblPr.append(parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{border_hex}"/>'
        f'<w:left w:val="nil"/>'
        f'<w:bottom w:val="single" w:sz="12" w:space="0" w:color="{border_hex}"/>'
        f'<w:right w:val="nil"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{border_hex}"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{border_hex}"/>'
        f'</w:tblBorders>'))


def set_table_fixed_layout(table, widths_cm: List[float]):
    tblPr = table._tbl.tblPr
    tblPr.append(parse_xml(f'<w:tblLayout {nsdecls("w")} w:type="fixed"/>'))
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:w"), str(int(sum(widths_cm) * 567)))
    tblW.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths_cm):
        gc.set(qn("w:w"), str(int(w * 567)))
    for row in table.rows:
        for cell, w in zip(row.cells, widths_cm):
            cell.width = Cm(w)


def add_page_field(paragraph, instr: str, size=8.0):
    """Trường Word (PAGE/NUMPAGES) dạng fldChar, đặt trong các run của đoạn văn (hợp lệ schema)."""
    def run_with(child_xml):
        r = paragraph.add_run()
        set_run_font(r, font_size=size, color=COLOR_TEXT_MUTED)
        r._r.append(parse_xml(child_xml))
        return r
    run_with(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    run_with(f'<w:instrText {nsdecls("w")} xml:space="preserve"> {instr} </w:instrText>')
    run_with(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>')
    r = paragraph.add_run("1")
    set_run_font(r, font_size=size, color=COLOR_TEXT_MUTED)
    run_with(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')


def add_bottom_border(paragraph, color=HEX_BORDER, size=6):
    pPr = paragraph._p.get_or_add_pPr()
    pPr.append(parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="{size}" w:space="1" w:color="{color}"/></w:pBdr>'))


# ---------------------------------------------------------------------------
# Inline Markdown
# ---------------------------------------------------------------------------

_LATEX_SYMBOLS = {
    r"\times": "×", r"\cdot": "·", r"\rightarrow": "→", r"\to": "→", r"\Rightarrow": "⇒", r"\leftarrow": "←",
    r"\le": "≤", r"\leq": "≤", r"\ge": "≥", r"\geq": "≥", r"\neq": "≠", r"\approx": "≈", r"\pm": "±",
    r"\%": "%", r"\$": "$", r"\,": " ", r"\;": " ", r"\quad": " ", r"\sum": "Σ", r"\div": "÷",
}


def latex_to_text(s: str) -> str:
    s = s.strip().strip("$").strip()
    for _ in range(3):
        s = re.sub(r"\\(?:text|mathrm|mathbf|textbf|operatorname|mbox)\{([^{}]*)\}", r"\1", s)
        s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1) / (\2)", s)
    for k in sorted(_LATEX_SYMBOLS, key=len, reverse=True):
        s = s.replace(k, _LATEX_SYMBOLS[k])
    s = re.sub(r"\\left|\\right", "", s)
    s = re.sub(r"\\[A-Za-z]+", "", s)
    s = re.sub(r"[_^]\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"[_^](\w)", r"\1", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


FLAG_STYLES = [
    (re.compile(r"^\[XÁC ĐỊNH\]$"), COLOR_GREEN),
    (re.compile(r"^\[SUY LUẬN(?: ÁP DỤNG)?[^\]]*\]$", re.I), COLOR_BLUE),
    (re.compile(r"^\[(?:GIẢ ĐỊNH|Giả định|giả định|CẦN XÁC MINH|Cần xác minh|CHƯA XÁC MINH)[^\]]*\]$"), COLOR_ORANGE),
    (re.compile(r"^\[(?:CẢNH BÁO|Cảnh báo)[^\]]*\]$"), COLOR_RED),
    (re.compile(r"^\[Web\]$", re.I), COLOR_NAVY_MEDIUM),
]

INLINE_RE = re.compile(
    r"(?P<br>\s*<[bB][rR]\s*/?>\s*)"
    r"|(?P<flag>\[(?:XÁC ĐỊNH|SUY LUẬN[^\]]*|GIẢ ĐỊNH[^\]]*|Giả định[^\]]*|giả định[^\]]*|CẦN XÁC MINH[^\]]*|"
    r"Cần xác minh[^\]]*|CHƯA XÁC MINH[^\]]*|CẢNH BÁO[^\]]*|Cảnh báo[^\]]*|Web)\])"
    r"|(?P<link>\[(?P<ltext>[^\]]+)\]\((?P<lurl>[^()\s]+(?:\([^()\s]*\)[^()\s]*)*)\))"
    r"|(?P<code>`[^`\n]+`)"
    r"|(?P<bold>\*\*(?P<btext>.+?)\*\*|__(?P<btext2>.+?)__)"
    r"|(?P<ital>(?<![\w*\\])\*(?=[^\s*])(?P<itext>[^*\n]*?[^\s*\\])\*(?![\w*]))"
    r"|(?P<math>\$(?=\S)(?P<mtext>[^$\n]*?(?:\\[A-Za-z]+|[_^]\{?)[^$\n]*?)(?<=\S)\$)"
)


def add_formatted_text(paragraph, text: str, base_size=11.5, default_color=COLOR_TEXT_MAIN,
                       bold=False, italic=False, bold_color=COLOR_NAVY_DARK):
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            r = paragraph.add_run(text[pos:m.start()])
            set_run_font(r, font_size=base_size, bold=bold, italic=italic,
                         color=bold_color if bold else default_color)
        if m.group("br"):
            r = paragraph.add_run()
            r.add_break()
        elif m.group("flag"):
            tok = m.group("flag")
            color = next((c for rx, c in FLAG_STYLES if rx.match(tok)), COLOR_ORANGE)
            r = paragraph.add_run(tok)
            set_run_font(r, font_size=base_size, bold=True, italic=italic, color=color)
        elif m.group("link"):
            r = paragraph.add_run(f"{m.group('ltext')} ({m.group('lurl')})")
            set_run_font(r, font_size=base_size, italic=True, bold=bold, color=COLOR_NAVY_MEDIUM)
        elif m.group("code"):
            r = paragraph.add_run(m.group("code")[1:-1])
            set_run_font(r, font_name="Consolas", font_size=base_size * 0.9, bold=bold, color=COLOR_NAVY_DARK)
        elif m.group("bold"):
            inner = m.group("btext") if m.group("btext") is not None else m.group("btext2")
            add_formatted_text(paragraph, inner, base_size, default_color, bold=True, italic=italic,
                               bold_color=bold_color)
        elif m.group("ital"):
            add_formatted_text(paragraph, m.group("itext"), base_size, default_color, bold=bold, italic=True,
                               bold_color=bold_color)
        elif m.group("math"):
            r = paragraph.add_run(latex_to_text(m.group("mtext")))
            set_run_font(r, font_size=base_size, bold=bold, italic=True, color=COLOR_NAVY_MEDIUM)
        pos = m.end()
    if pos < len(text):
        r = paragraph.add_run(text[pos:])
        set_run_font(r, font_size=base_size, bold=bold, italic=italic,
                     color=bold_color if bold else default_color)


def strip_markdown(text: str) -> str:
    text = re.sub(r"\s*<[bB][rR]\s*/?>\s*", " ", text)
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2), text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    return text


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------


def split_table_row(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells = re.split(r"(?<!\\)\|", s)
    return [c.strip().replace("\\|", "|") for c in cells]


def display_len(text: str) -> int:
    """Độ rộng hiển thị: chữ Nhật/Hán (East Asian Wide/Fullwidth) chiếm 2 ô."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def column_widths(rows: List[List[str]], num_cols: int) -> List[float]:
    """Độ rộng cột theo nội dung: cột chữ dài (trích dẫn) rộng hơn; mọi cột đủ chỗ cho từ dài nhất."""
    weights, min_cm = [], []
    for c in range(num_cols):
        cells = [strip_markdown(r[c]) if c < len(r) else "" for r in rows]
        lengths = [display_len(t) for t in cells]
        longest = max(lengths) if lengths else 0
        avg = sum(lengths) / max(len(lengths), 1)
        words = [display_len(w) for t in cells for w in t.split()]
        longest_word = max(words) if words else 1
        weights.append(max(3.0, min(longest, 160) ** 0.7 + min(avg, 120) ** 0.7))
        min_cm.append(min(4.0, 0.19 * longest_word + 0.45))
    total = sum(weights)
    widths = [CONTENT_WIDTH_CM * w / total for w in weights]
    for _ in range(3):  # nâng cột hẹp lên mức tối thiểu, lấy bớt từ cột rộng
        short = [i for i, w in enumerate(widths) if w < min_cm[i]]
        if not short:
            break
        need = sum(min_cm[i] - widths[i] for i in short)
        for i in short:
            widths[i] = min_cm[i]
        donors = [i for i in range(num_cols) if i not in short and widths[i] > min_cm[i]]
        spare = sum(widths[i] - min_cm[i] for i in donors)
        if spare <= 0:
            break
        for i in donors:
            widths[i] -= need * (widths[i] - min_cm[i]) / spare
    scale = CONTENT_WIDTH_CM / sum(widths)
    return [round(w * scale, 2) for w in widths]


def render_markdown_table(doc, raw_lines: List[str]):
    rows, aligns = [], []
    for line in raw_lines:
        cells = split_table_row(line)
        if cells and all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            aligns = [WD_ALIGN_PARAGRAPH.CENTER if c.startswith(":") and c.endswith(":")
                      else WD_ALIGN_PARAGRAPH.RIGHT if c.endswith(":") else WD_ALIGN_PARAGRAPH.LEFT for c in cells]
            continue
        rows.append(cells)
    if not rows:
        return
    num_cols = max(len(r) for r in rows)
    widths = column_widths(rows, num_cols)
    table = doc.add_table(rows=len(rows), cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    set_table_fixed_layout(table, widths)
    small = num_cols >= 5
    for r_idx, data in enumerate(rows):
        row = table.rows[r_idx]
        if r_idx == 0:
            row._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
        for c_idx in range(num_cols):
            cell = row.cells[c_idx]
            text = data[c_idx] if c_idx < len(data) else ""
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=80, bottom=80, left=110, right=110)
            set_cell_background(cell, HEX_NAVY_HEADER if r_idx == 0 else (HEX_ZEBRA_ROW if r_idx % 2 else HEX_WHITE))
            p = cell.paragraphs[0]
            p.alignment = aligns[c_idx] if c_idx < len(aligns) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.1
            size = 9.0 if small else 10.0
            if r_idx == 0:
                add_formatted_text(p, text, base_size=size + 0.5, default_color=COLOR_WHITE,
                                   bold=True, bold_color=COLOR_WHITE)
            else:
                add_formatted_text(p, text, base_size=size)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


CALLOUT_LABELS = {
    "[!NOTE]": ("LƯU Ý PHÁP LÝ: ", COLOR_NAVY_MEDIUM),
    "[!TIP]": ("GỢI Ý: ", COLOR_NAVY_MEDIUM),
    "[!WARNING]": ("CẢNH BÁO RỦI RO TRỌNG YẾU: ", COLOR_ORANGE),
    "[!CAUTION]": ("CẢNH BÁO RỦI RO TRỌNG YẾU: ", COLOR_ORANGE),
    "[!IMPORTANT]": ("QUY ĐỊNH BẮT BUỘC: ", COLOR_NAVY_DARK),
}


def render_callout_box(doc, lines: List[str]):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_fixed_layout(table, [CONTENT_WIDTH_CM])
    cell = table.cell(0, 0)
    set_cell_background(cell, HEX_CALLOUT_BG)
    set_cell_margins(cell, top=120, bottom=120, left=200, right=200)
    cell._tc.get_or_add_tcPr().append(parse_xml(
        f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="36" w:space="0" w:color="{HEX_CALLOUT_BORDER}"/>'
        f'<w:top w:val="nil"/><w:right w:val="nil"/><w:bottom w:val="nil"/></w:tcBorders>'))
    first = True
    for line in lines:
        p = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        for tag, (label, color) in CALLOUT_LABELS.items():
            if tag in line:
                r = p.add_run(label)
                set_run_font(r, font_size=10.5, bold=True, color=color)
                line = line.replace(tag, "").strip()
        bullet = re.match(r"^[-*•]\s+(.*)$", line)
        if bullet:
            r = p.add_run("•  ")
            set_run_font(r, font_size=10.0, bold=True, color=COLOR_NAVY_MEDIUM)
            line = bullet.group(1)
        if line:
            add_formatted_text(p, line, base_size=10.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_heading(doc, level: int, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(4)
        add_formatted_text(p, text, base_size=16.0, bold=True)
        deco = doc.add_paragraph()
        deco.alignment = WD_ALIGN_PARAGRAPH.CENTER
        deco.paragraph_format.space_after = Pt(12)
        add_bottom_border(deco, color=HEX_CALLOUT_BORDER, size=8)
        return
    sizes = {2: (13.5, COLOR_NAVY_DARK, False), 3: (12.0, COLOR_NAVY_MEDIUM, False)}
    size, color, ital = sizes.get(level, (11.5, COLOR_TEXT_MAIN, True))
    p.paragraph_format.space_before = Pt(14 if level == 2 else 10 if level == 3 else 8)
    p.paragraph_format.space_after = Pt(6 if level == 2 else 4)
    p.paragraph_format.line_spacing = 1.15
    add_formatted_text(p, text, base_size=size, bold=True, italic=ital, bold_color=color)


def build_legal_docx(md_path: Path, output_docx_path: Path, title: Optional[str] = None):
    if not md_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file nguồn Markdown: {md_path}")
    lines = md_path.read_text(encoding="utf-8", errors="replace").splitlines()
    doc = Document()
    configure_document_defaults(doc)

    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21.0), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2.0)
    section.left_margin, section.right_margin = Cm(2.5), Cm(2.0)

    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = hp.add_run("BÁO CÁO TƯ VẤN PHÁP LÝ & QUẢN TRỊ RỦI RO | AI WORKFORCE")
    set_run_font(r, font_size=8.5, italic=True, color=COLOR_TEXT_MUTED)

    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("Tài liệu nghiên cứu sơ bộ theo dữ kiện cung cấp, không thay thế ý kiến pháp lý chính thức  |  Trang ")
    set_run_font(r, font_size=8.0, italic=True, color=COLOR_TEXT_MUTED)
    add_page_field(fp, "PAGE")
    r = fp.add_run(" / ")
    set_run_font(r, font_size=8.0, color=COLOR_TEXT_MUTED)
    add_page_field(fp, "NUMPAGES")

    first_h1 = None
    if title:
        add_heading(doc, 1, title)
        first_h1 = title

    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        i += 1

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            t = doc.add_table(rows=1, cols=1)
            t.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_table_fixed_layout(t, [CONTENT_WIDTH_CM])
            cell = t.cell(0, 0)
            set_cell_background(cell, "F1F5F9")
            set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
            cp = cell.paragraphs[0]
            cp.paragraph_format.line_spacing = 1.05
            rr = cp.add_run("\n".join(code))
            set_run_font(rr, font_name="Consolas", font_size=9.0, color=COLOR_NAVY_DARK)
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
            continue

        if stripped.startswith("$$"):
            buf = [stripped]
            if not (len(stripped) > 4 and stripped.endswith("$$")):
                i += 1
                while i < len(lines) and "$$" not in lines[i]:
                    buf.append(lines[i].strip())
                    i += 1
                if i < len(lines):
                    buf.append(lines[i].strip())
            i += 1
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(6)
            rr = p.add_run(latex_to_text(" ".join(buf).replace("$$", "")))
            set_run_font(rr, font_size=11.0, italic=True, color=COLOR_NAVY_MEDIUM)
            continue

        if stripped.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            render_markdown_table(doc, block)
            continue

        if not stripped:
            i += 1
            continue

        if stripped.startswith("<!--"):  # chú thích HTML (VD mốc TARIFF_LOOKUP) không in ra
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue

        hm = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", stripped)
        if hm:
            text = hm.group(2)
            level = len(hm.group(1))
            if level == 1 and first_h1 is None:
                first_h1 = strip_markdown(text)
            add_heading(doc, min(level, 4), text)
            i += 1
            continue

        if re.fullmatch(r"(-\s*){3,}|(\*\s*){3,}|(_\s*){3,}", stripped):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(8)
            add_bottom_border(p)
            i += 1
            continue

        if stripped.startswith(">"):
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(lines[i].strip()[1:].strip())
                i += 1
            render_callout_box(doc, [b for b in block if b])
            continue

        indent = len(line) - len(line.lstrip(" "))
        level = min(indent // 2, 4)
        bm = re.match(r"^[-*+•]\s+(.*)$", stripped)
        nm = re.match(r"^(\d+)[\.\)]\s+(.*)$", stripped)
        if bm or nm:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6 + 0.6 * level)
            p.paragraph_format.first_line_indent = Cm(-0.45)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            if bm:
                rr = p.add_run("•  " if level == 0 else "–  ")
                set_run_font(rr, font_size=10.0, bold=True, color=COLOR_NAVY_MEDIUM)
                add_formatted_text(p, bm.group(1))
            else:
                rr = p.add_run(f"{nm.group(1)}. ")
                set_run_font(rr, font_size=11.5, bold=True, color=COLOR_NAVY_DARK)
                add_formatted_text(p, nm.group(2))
            i += 1
            continue

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.2
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_formatted_text(p, stripped)
        i += 1

    if first_h1:
        doc.core_properties.title = first_h1[:250]
    output_docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_docx_path))
    return output_docx_path


def main():
    global CJK_FONT
    ap = argparse.ArgumentParser(description="Xuất Báo cáo Tư vấn Pháp lý (VN & JP) từ Markdown sang DOCX.")
    ap.add_argument("--input", "-i", required=True, type=Path, help="File Markdown báo cáo (.md)")
    ap.add_argument("--output", "-o", type=Path, default=None, help="File .docx đầu ra (mặc định cạnh file .md)")
    ap.add_argument("--title", "-t", type=str, default=None, help="Tiêu đề chèn đầu tài liệu (và metadata)")
    ap.add_argument("--cjk-font", type=str, default=CJK_FONT,
                    help="Font cho chữ Nhật/Hán (mặc định 'Yu Mincho'; có thể dùng 'MS Mincho', 'Hiragino Mincho ProN')")
    args = ap.parse_args()
    CJK_FONT = args.cjk_font

    src = args.input.expanduser().resolve()
    if not src.exists():
        print(f"❌ Lỗi: File nguồn không tồn tại: {src}")
        sys.exit(1)
    out = args.output.expanduser().resolve() if args.output else src.with_suffix(".docx")
    try:
        res = build_legal_docx(src, out, title=args.title)
    except Exception as e:  # noqa: BLE001
        print(f"❌ Lỗi khi chuyển đổi DOCX: {e}")
        sys.exit(1)
    print("✅ Đã xuất bản Báo cáo Pháp lý DOCX tại:")
    print(f"   {res}")


if __name__ == "__main__":
    main()
