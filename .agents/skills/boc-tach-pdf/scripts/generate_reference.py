"""
generate_reference.py — Tạo reference.docx cho Pandoc từ format_spec.json.

v4: Khởi tạo từ reference.docx MẶC ĐỊNH CỦA PANDOC (`pandoc --print-default-data-file reference.docx`)
rồi chỉnh style. Lý do: template trống của python-docx THIẾU các style Pandoc dùng (Table, Compact,
First Paragraph, Body Text...) khiến LibreOffice/WPS dàn trang hỏng (bảng rỗng, chữ bị ép vào ô).

Phân nhánh: NĐ 30 (đen trắng, chuẩn hành chính) vs VB dài (tùy biến theo spec).

Usage:
    python3 generate_reference.py <thư_mục_processing>
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Mm, Pt, RGBColor

def default_east_asia_font():
    """Font cho chữ Nhật/Hán (chữ Việt/Latin vẫn dùng body_font). macOS: Hiragino Mincho ProN (có sẵn);
    Windows/Office: MS Mincho. Word tự thay thế font Đông Á khi máy mở không có font này.
    Ghi đè bằng "east_asia_font" trong format_spec.json."""
    import platform
    return "Hiragino Mincho ProN" if platform.system() == "Darwin" else "MS Mincho"


EAST_ASIA_FONT_DEFAULT = default_east_asia_font()


def pt_to_mm(pt_val):
    return pt_val * 25.4 / 72


def pandoc_binary():
    try:
        import pypandoc
        p = pypandoc.get_pandoc_path()
        if p:
            return p
    except Exception:  # noqa: BLE001
        pass
    return shutil.which("pandoc")


def base_document(ref_path):
    """reference.docx mặc định của Pandoc; nếu không có Pandoc -> template python-docx (CẢNH BÁO)."""
    exe = pandoc_binary()
    if exe:
        try:
            subprocess.run([exe, "-o", str(ref_path), "--print-default-data-file", "reference.docx"],
                           check=True, capture_output=True)
            return Document(str(ref_path)), "pandoc_default"
        except Exception as e:  # noqa: BLE001
            print(f"[WARN] Không tạo được reference mặc định của Pandoc: {e}")
    print("[WARN] Dùng template python-docx (thiếu style Pandoc: bảng/đoạn có thể hiển thị sai trên LibreOffice/WPS).")
    return Document(), "python_docx_blank"


def set_font_all(style, font_name, east_asia):
    style.font.name = font_name
    rpr = style.element.find(qn("w:rPr"))
    if rpr is None:
        rpr = parse_xml(f'<w:rPr {nsdecls("w")}/>')
        style.element.append(rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
        rpr.insert(0, rfonts)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(attr)) is not None:
            del rfonts.attrib[qn(attr)]
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), font_name)
    rfonts.set(qn("w:eastAsia"), east_asia)


def get_or_add(doc, name, base="Body Text"):
    try:
        return doc.styles[name]
    except KeyError:
        st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = doc.styles[base]
        return st


def style_table_grid(doc):
    """Style 'Table' của Pandoc: thêm viền lưới đơn (bảng trong tài liệu scan hầu hết là bảng kẻ ô)."""
    try:
        st = doc.styles["Table"]
    except KeyError:
        return
    tblPr = st.element.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = parse_xml(f'<w:tblPr {nsdecls("w")}/>')
        st.element.append(tblPr)
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    borders = parse_xml(f'''<w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>
        <w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>
        <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
        <w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>
        <w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>
    </w:tblBorders>''')
    # thứ tự schema: tblStyle.. tblW, jc, tblCellSpacing, tblInd, tblBorders, shd, tblLayout, tblCellMar, tblLook
    anchor = None
    for tag in ("w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook"):
        anchor = tblPr.find(qn(tag))
        if anchor is not None:
            break
    if anchor is not None:
        anchor.addprevious(borders)
    else:
        tblPr.append(borders)


def common_styles(doc, spec, body_font, east_asia, body_size, line_spacing, indent_pt, heading_sizes, black):
    by_name = {s.name: s for s in doc.styles}
    for name in ("Normal", "Body Text", "First Paragraph", "Compact", "Block Text", "Title", "Subtitle",
                 "Table Caption", "Image Caption", "Caption", "Footnote Text", "Figure", "Captioned Figure"):
        st = by_name.get(name)
        if st is None:
            continue
        set_font_all(st, body_font, east_asia)
        st.font.size = Pt(body_size)
        if black:
            st.font.color.rgb = RGBColor(0, 0, 0)
    for name in ("Body Text", "First Paragraph"):
        st = get_or_add(doc, name)
        pf = st.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.line_spacing = line_spacing
        pf.space_before = Pt(0)
        pf.space_after = Pt(6)
        pf.first_line_indent = Pt(indent_pt) if indent_pt > 5 else Pt(0)
    compact = get_or_add(doc, "Compact")
    compact.paragraph_format.first_line_indent = Pt(0)
    compact.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT  # ô bảng/list: không giãn đều
    compact.paragraph_format.line_spacing = 1.0
    compact.paragraph_format.space_after = Pt(2)
    for name, align in (("Center", WD_ALIGN_PARAGRAPH.CENTER), ("Right", WD_ALIGN_PARAGRAPH.RIGHT)):
        st = get_or_add(doc, name)
        st.paragraph_format.alignment = align
        st.paragraph_format.first_line_indent = Pt(0)
    for level, size in heading_sizes.items():
        try:
            st = doc.styles[f"Heading {level}"]
        except KeyError:
            continue
        set_font_all(st, body_font, east_asia)
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.italic = False
        if black:
            st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.first_line_indent = Pt(0)
        st.paragraph_format.space_before = Pt(12 if level == 1 else 6)
        st.paragraph_format.space_after = Pt(6)
    for name in ("Title",):
        try:
            st = doc.styles[name]
            st.font.size = Pt(max(heading_sizes.values()) + 1)
            st.font.bold = True
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        except KeyError:
            pass
    style_table_grid(doc)


def generate_reference(processing_dir):
    processing_dir = Path(processing_dir)
    process_dir = processing_dir / "02.process"
    spec_path = process_dir / "format_spec.json"
    if not spec_path.exists():
        print(f"[FAIL] Không tìm thấy format_spec.json tại {process_dir}. Chạy analyze_format.py trước.")
        return None
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    doc_type = spec.get("doc_type", "van_ban_dai")
    ref_path = process_dir / "reference.docx"
    doc, origin = base_document(ref_path)
    print(f"[INFO] Loại văn bản: {doc_type} | template gốc: {origin}")

    body_font = spec.get("body_font", "Times New Roman")
    if "+" in body_font:  # font subset trong PDF (ABCDEF+Arial)
        body_font = body_font.split("+", 1)[1] or "Times New Roman"
    east_asia = spec.get("east_asia_font", EAST_ASIA_FONT_DEFAULT)
    body_size = float(spec.get("body_font_size", 13.0))
    line_spacing = float(spec.get("line_spacing", 1.5))
    indent_pt = float(spec.get("first_line_indent_pt", 28))

    if doc_type == "hanh_chinh_nd30":
        for section in doc.sections:
            section.top_margin, section.bottom_margin = Mm(20), Mm(20)
            section.left_margin, section.right_margin = Mm(30), Mm(20)
            section.page_width, section.page_height = Mm(210), Mm(297)
        # NĐ 30: heading cùng cỡ chữ thân bài, phân cấp bằng đậm/IN HOA, màu đen
        common_styles(doc, spec, body_font, east_asia, body_size, line_spacing, indent_pt,
                      {1: body_size, 2: body_size, 3: body_size, 4: body_size}, black=True)
    else:
        margins = spec.get("margins_pt", {})
        for section in doc.sections:
            section.top_margin = Mm(pt_to_mm(margins.get("top", 57)))
            section.bottom_margin = Mm(pt_to_mm(margins.get("bottom", 57)))
            section.left_margin = Mm(pt_to_mm(margins.get("left", 85)))
            section.right_margin = Mm(pt_to_mm(margins.get("right", 57)))
            section.page_width = Mm(pt_to_mm(spec.get("page_width_pt", 595)))
            section.page_height = Mm(pt_to_mm(spec.get("page_height_pt", 842)))
        hs = float(spec.get("heading_font_size", body_size + 2))
        common_styles(doc, spec, body_font, east_asia, body_size, line_spacing, indent_pt,
                      {1: hs + 2, 2: hs + 1, 3: hs, 4: body_size}, black=True)

    doc.save(str(ref_path))
    print(f"[OK] Đã tạo reference.docx ({doc_type}): {body_font} {body_size}pt (Đông Á: {east_asia}), "
          f"giãn dòng {line_spacing}, thụt {indent_pt}pt")
    print(f"[OK] Lưu tại: {ref_path}")
    return str(ref_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Sử dụng: python3 generate_reference.py <thư_mục_processing>")
        sys.exit(1)
    if generate_reference(sys.argv[1]) is None:
        sys.exit(1)
