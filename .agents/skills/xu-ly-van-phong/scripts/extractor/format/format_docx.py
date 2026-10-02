#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
format_docx.py - Hậu xử lý file DOCX do Pandoc sinh ra theo KHUNG MẶC ĐỊNH CHUNG (SKILL.md quy tắc 9).

Hai chế độ màu (bắt buộc chọn rõ):
  --mono               Đen trắng tuyệt đối (mặc định). Dùng cho Track 1 và tài liệu không có brand.
  --brand-kit <json>   Đắp lớp màu từ brand_kit.json (schema trong resources/extractor_docs.md).
                       Brand kit CHỈ đổi màu heading, nền header bảng, zebra, callout, code;
                       không đổi khung (lề, indent, spacing).

Khung (theo standards/dynamic_structure/docx-page-setup.md):
  - A4, lề trên/dưới 2 cm, trái 3 cm, phải 2 cm; header 0,8 cm, footer 1,3 cm.
  - Body: căn đều, lùi đầu dòng 1,25 cm, spacing 3pt/3pt, line at-least 1,3 x cỡ chữ.
  - Heading cấp cao nhất (H2 khi H1 là tiêu đề) lùi 1,0 cm; các cấp dưới lùi 1,25 cm; left indent 0.
  - Bullet ký tự '-' cấp 1, '+' cấp 2, khối thẳng (left 0, first-line 1,25 cm).
  - Bảng full khổ, chữ nhỏ hơn body 2pt.

  python3 format_docx.py input.docx [output.docx] [--mono | --brand-kit path/brand_kit.json] [--size 13]
"""

import argparse
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

BODY_INDENT = Cm(1.25)
TOP_HEADING_INDENT = Cm(1.0)
REQUIRED_COLORS = ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2")
PBDR_SUCCESSORS = ('w:shd', 'w:tabs', 'w:suppressAutoHyphens', 'w:kinsoku', 'w:wordWrap', 'w:overflowPunct', 'w:topLinePunct', 'w:autoSpaceDE', 'w:autoSpaceDN', 'w:bidi', 'w:adjustRightInd', 'w:snapToGrid', 'w:spacing', 'w:ind', 'w:contextualSpacing', 'w:mirrorIndents', 'w:suppressOverlap', 'w:jc', 'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap', 'w:outlineLvl', 'w:divId', 'w:cnfStyle', 'w:rPr', 'w:sectPr', 'w:pPrChange')
SHD_SUCCESSORS = PBDR_SUCCESSORS[1:]
TBL_ORDER = ("w:tblStyle", "w:tblpPr", "w:tblOverlap", "w:bidiVisual", "w:tblStyleRowBandSize",
             "w:tblStyleColBandSize", "w:tblW", "w:jc", "w:tblCellSpacing", "w:tblInd", "w:tblBorders", "w:shd",
             "w:tblLayout", "w:tblCellMar", "w:tblLook", "w:tblCaption", "w:tblDescription")


def palette_mono():
    return {
        "font_body": "Times New Roman", "font_heading": "Times New Roman",
        "text": "000000", "h1": "000000", "h2": "000000", "h3": "000000", "h4": "000000",
        "tbl_head_bg": None, "tbl_head_text": "000000", "tbl_zebra": None, "tbl_border": "000000",
        "quote_bar": "000000", "quote_bg": None, "quote_text": "000000",
        "code_bg": None, "code_border": "000000", "code_text": "000000", "inline_code": "000000",
    }


def palette_brand(path):
    p = Path(path).expanduser()
    if not p.is_file():
        raise SystemExit(f"❌ Không tìm thấy brand kit: {p}")
    kit = json.loads(p.read_text(encoding="utf-8"))
    colors = kit.get("colors") or {}
    missing = [k for k in REQUIRED_COLORS if not colors.get(k)]
    if missing:
        raise SystemExit(f"❌ brand_kit.json thiếu màu {missing}. Chạy lại extract_brand.py hoặc chọn preset; "
                         "không dùng màu mặc định ngầm.")
    fonts = kit.get("fonts") or {}
    c = colors
    return {
        "font_body": fonts.get("body") or "Times New Roman",
        "font_heading": fonts.get("heading") or fonts.get("body") or "Times New Roman",
        "text": c["dk1"], "h1": c["accent1"], "h2": c["accent1"], "h3": c["dk2"], "h4": c["dk2"],
        "tbl_head_bg": c["accent1"], "tbl_head_text": c["lt1"], "tbl_zebra": c["lt2"], "tbl_border": c["dk2"],
        "quote_bar": c["accent1"], "quote_bg": c["lt2"], "quote_text": c["dk1"],
        "code_bg": c["lt2"], "code_border": c["dk2"], "code_text": c["dk1"], "inline_code": c["accent2"],
    }


def insert_before(parent, child, *successors):
    """Chèn child trước phần tử đầu tiên thuộc successors (giữ đúng thứ tự schema OOXML)."""
    for tag in successors:
        found = parent.find(qn(tag))
        if found is not None:
            found.addprevious(child)
            return child
    parent.append(child)
    return child


def rgb(hexstr):
    return RGBColor.from_string(hexstr.upper())


def set_style_font(style, font_name):
    style.font.name = font_name
    rpr = style.element.find(qn("w:rPr"))
    if rpr is None:
        rpr = parse_xml(f'<w:rPr {nsdecls("w")}/>')
        style.element.append(rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), font_name)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(a)) is not None:
            del rfonts.attrib[qn(a)]


def set_run_font(run, font_name):
    run.font.name = font_name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
        rpr.insert(0, rf)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(attr), font_name)


def _ppr(el):
    ppr = el.find(qn("w:pPr"))
    if ppr is None:
        ppr = parse_xml(f'<w:pPr {nsdecls("w")}/>')
        el.insert(0, ppr)
    return ppr


def shade(el, color):
    ppr = _ppr(el)
    for old in ppr.findall(qn("w:shd")):
        ppr.remove(old)
    if color:
        ppr.insert_element_before(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}" w:val="clear"/>'),
                                  *SHD_SUCCESSORS)


def border(el, sides, color, size=4, space=4):
    ppr = _ppr(el)
    for old in ppr.findall(qn("w:pBdr")):
        ppr.remove(old)
    inner = "".join(f'<w:{s} w:val="single" w:sz="{size}" w:space="{space}" w:color="{color}"/>' for s in sides)
    ppr.insert_element_before(parse_xml(f'<w:pBdr {nsdecls("w")}>{inner}</w:pBdr>'), *PBDR_SUCCESSORS)


def body_format(pf, size, indent=BODY_INDENT, before=3, after=3):
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = indent
    pf.left_indent = Cm(0)
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
    pf.line_spacing = Pt(round(size * 1.3))


def fix_bullets(doc, font):
    """Bullet Pandoc -> '-' cấp 1, '+' cấp 2, khối thẳng left 0, first-line 1,25 cm."""
    for rel in doc.part.rels.values():
        if "numbering" not in rel.reltype:
            continue
        for absn in rel.target_part.element.findall(qn("w:abstractNum")):
            for lvl in absn.findall(qn("w:lvl")):
                fmt = lvl.find(qn("w:numFmt"))
                ilvl = int(lvl.get(qn("w:ilvl"), "0"))
                if fmt is not None and fmt.get(qn("w:val")) == "bullet":
                    txt = lvl.find(qn("w:lvlText"))
                    if txt is not None:
                        txt.set(qn("w:val"), "-" if ilvl % 2 == 0 else "+")
                    rpr = lvl.find(qn("w:rPr"))
                    if rpr is None:
                        rpr = parse_xml(f'<w:rPr {nsdecls("w")}/>')
                        lvl.append(rpr)  # rPr là phần tử cuối của w:lvl
                    for old in rpr.findall(qn("w:rFonts")):
                        rpr.remove(old)
                    rpr.append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>'))
                ppr = lvl.find(qn("w:pPr"))
                if ppr is None:
                    ppr = parse_xml(f'<w:pPr {nsdecls("w")}/>')
                    insert_before(lvl, ppr, "w:rPr")
                for old in ppr.findall(qn("w:ind")):
                    ppr.remove(old)
                ppr.insert_element_before(parse_xml(f'<w:ind {nsdecls("w")} w:left="0" w:firstLine="709"/>'),
                                          *PBDR_SUCCESSORS[PBDR_SUCCESSORS.index("w:contextualSpacing"):])
                suff = lvl.find(qn("w:suff"))
                if suff is None:
                    suff = parse_xml(f'<w:suff {nsdecls("w")} w:val="space"/>')
                    insert_before(lvl, suff, "w:lvlText", "w:lvlPicBulletId", "w:legacy", "w:lvlJc",
                                              "w:pPr", "w:rPr")
                else:
                    suff.set(qn("w:val"), "space")


def format_docx(input_path, output_path, pal, size=13):
    doc = Document(input_path)
    for s in doc.sections:
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.top_margin, s.bottom_margin = Cm(2.0), Cm(2.0)
        s.left_margin, s.right_margin = Cm(3.0), Cm(2.0)
        s.header_distance, s.footer_distance = Cm(0.8), Cm(1.3)
        s.gutter = Cm(0)

    fix_bullets(doc, pal["font_body"])
    styles = doc.styles
    normal = styles["Normal"]
    set_style_font(normal, pal["font_body"])
    normal.font.size = Pt(size)
    normal.font.color.rgb = rgb(pal["text"])
    body_format(normal.paragraph_format, size)

    has_chapters = any(p.text.strip().startswith("CHƯƠNG") for p in doc.paragraphs)
    h1_is_title = not has_chapters
    heading_spec = {  # size, color, before, after, indent
        "Heading 1": (size + 3, pal["h1"], 18, 8),
        "Heading 2": (size + 1, pal["h2"], 18 if h1_is_title else 12, 8 if h1_is_title else 6),
        "Heading 3": (size, pal["h3"], 12, 6),
        "Heading 4": (size, pal["h4"], 12, 6),
    }
    for name, (sz, col, before, after) in heading_spec.items():
        st = styles[name] if name in [x.name for x in styles] else styles.add_style(name, 1)
        set_style_font(st, pal["font_heading"])
        st.font.size, st.font.bold, st.font.italic = Pt(sz), True, False
        st.font.color.rgb = rgb(col)
        pf = st.paragraph_format
        pf.space_before, pf.space_after = Pt(before), Pt(after)
        pf.keep_with_next = True
        pf.left_indent = Cm(0)
        pf.line_spacing = 1.15

    top_heading = "Heading 2" if h1_is_title else "Heading 1"
    seen_h1 = False
    for idx, para in enumerate(doc.paragraphs):
        sname = para.style.name if para.style else ""
        text = para.text.strip()
        for run in para.runs:
            set_run_font(run, pal["font_body"] if not sname.startswith("Heading") else pal["font_heading"])

        if sname.startswith("Source") or "code" in sname.lower():
            pf = para.paragraph_format
            pf.alignment, pf.first_line_indent = WD_ALIGN_PARAGRAPH.LEFT, Cm(0)
            pf.space_before, pf.space_after, pf.line_spacing = Pt(2), Pt(2), 1.0
            shade(para._element, pal["code_bg"])
            border(para._element, ("top", "left", "bottom", "right"), pal["code_border"], 4, 4)
            for run in para.runs:
                set_run_font(run, "Consolas")
                run.font.size = Pt(size - 3)
                run.font.color.rgb = rgb(pal["code_text"])
            continue

        if sname.startswith("Heading"):
            pf = para.paragraph_format
            if sname == "Heading 1" and h1_is_title and not seen_h1:
                pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
                pf.first_line_indent = Cm(0)
                pf.space_before, pf.space_after = Pt(0), Pt(6)
                seen_h1 = True
            elif sname == "Heading 1" and has_chapters:
                pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
                pf.first_line_indent = TOP_HEADING_INDENT
                pf.page_break_before = idx > 0
            else:
                pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
                pf.first_line_indent = TOP_HEADING_INDENT if sname == top_heading else BODY_INDENT
            continue

        if sname in ("Block Text", "Quote", "Intense Quote") or sname.startswith("Block"):
            body_format(para.paragraph_format, size, indent=Cm(0), before=6, after=6)
            para.paragraph_format.left_indent = Cm(0.4)
            shade(para._element, pal["quote_bg"])
            border(para._element, ("left",), pal["quote_bar"], 18, 8)
            for run in para.runs:
                run.font.color.rgb = rgb(pal["quote_text"])
                run.font.italic = True
            continue

        for run in para.runs:
            rs = run.style.name if run.style else ""
            if rs in ("Verbatim Char", "Source Code Char") or "code" in rs.lower():
                set_run_font(run, "Consolas")
                run.font.size = Pt(size - 2)
                run.font.color.rgb = rgb(pal["inline_code"])

        has_drawing = bool(para._element.findall(".//" + qn("w:drawing")))
        pf = para.paragraph_format
        if has_drawing:
            pf.alignment, pf.first_line_indent = WD_ALIGN_PARAGRAPH.CENTER, Cm(0)
            pf.space_before, pf.space_after = Pt(6), Pt(3)
        elif not text:
            pf.first_line_indent = Cm(0)
            pf.space_before = pf.space_after = Pt(0)
        elif sname.startswith("List") or sname in ("Compact", "List Paragraph"):
            body_format(pf, size, before=2, after=3)
            ppr = para._element.find(qn("w:pPr"))
            if ppr is not None:
                for old in ppr.findall(qn("w:ind")):
                    ppr.remove(old)
                ppr.insert_element_before(parse_xml(f'<w:ind {nsdecls("w")} w:left="0" w:firstLine="709"/>'),
                                          *PBDR_SUCCESSORS[PBDR_SUCCESSORS.index("w:contextualSpacing"):])
        else:
            body_format(pf, size)
        for run in para.runs:
            if run.font.color is None or run.font.color.type is None:
                run.font.color.rgb = rgb(pal["text"])

    for table in doc.tables:
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = table._tbl.find(qn("w:tblPr"))
        for tag in ("w:tblW", "w:tblLayout", "w:tblBorders", "w:tblCellMar"):
            for old in tblPr.findall(qn(tag)):
                tblPr.remove(old)
        bc = pal["tbl_border"]
        def put(el):
            tag = el.tag.split("}")[1]
            after = TBL_ORDER[TBL_ORDER.index("w:" + tag) + 1:]
            tblPr.insert_element_before(el, *after)
        put(parse_xml(f'<w:tblW {nsdecls("w")} w:w="5000" w:type="pct"/>'))
        put(parse_xml(f'<w:tblBorders {nsdecls("w")}>' + "".join(
            f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="{bc}"/>'
            for e in ("top", "left", "bottom", "right", "insideH", "insideV")) + "</w:tblBorders>"))
        put(parse_xml(f'<w:tblLayout {nsdecls("w")} w:type="autofit"/>'))
        put(parse_xml(f'<w:tblCellMar {nsdecls("w")}><w:top w:w="40" w:type="dxa"/>'
                      f'<w:left w:w="100" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/>'
                      f'<w:right w:w="100" w:type="dxa"/></w:tblCellMar>'))
        for i, row in enumerate(table.rows):
            for cell in row.cells:
                tcPr = cell._tc.get_or_add_tcPr()
                for old in tcPr.findall(qn("w:shd")):
                    tcPr.remove(old)
                fill = pal["tbl_head_bg"] if i == 0 else (pal["tbl_zebra"] if i % 2 == 0 else None)
                if fill:
                    tcPr.insert_element_before(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill}" w:val="clear"/>'),
                                               "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText",
                                               "w:vAlign", "w:hideMark", "w:headers", "w:cellIns", "w:cellDel",
                                               "w:cellMerge", "w:tcPrChange")
                for para in cell.paragraphs:
                    pf = para.paragraph_format
                    pf.first_line_indent = Cm(0)
                    pf.space_before = pf.space_after = Pt(2)
                    pf.line_spacing = 1.0
                    txt = para.text.strip().replace(".", "").replace(",", "").replace("%", "")
                    if i == 0:
                        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    elif txt.lstrip("-").isdigit():
                        pf.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    else:
                        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for run in para.runs:
                        set_run_font(run, pal["font_body"])
                        run.font.size = Pt(size - 2)
                        if i == 0:
                            run.font.bold = True
                            run.font.color.rgb = rgb(pal["tbl_head_text"])
                        else:
                            run.font.color.rgb = rgb(pal["text"])

    doc.save(output_path)
    print(f"OK - {output_path}")
    print(f"   chế độ màu: {'đen trắng (--mono)' if pal['h1'] == '000000' and not pal['tbl_head_bg'] else 'brand kit'} | "
          f"{len(doc.paragraphs)} đoạn | {len(doc.tables)} bảng")


def main():
    ap = argparse.ArgumentParser(description="Định dạng DOCX (Pandoc) theo khung mặc định chung")
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--mono", action="store_true", help="Đen trắng tuyệt đối (mặc định)")
    g.add_argument("--brand-kit", help="Đường dẫn brand_kit.json để đắp lớp màu")
    ap.add_argument("--size", type=int, default=13, help="Cỡ chữ body (mặc định 13)")
    a = ap.parse_args()
    pal = palette_brand(a.brand_kit) if a.brand_kit else palette_mono()
    format_docx(a.input, a.output or a.input, pal, a.size)


if __name__ == "__main__":
    main()
