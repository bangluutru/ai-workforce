#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_brand.py - Bóc Brand Kit (màu + font + ảnh) từ file Office mẫu (.docx/.pptx/.xlsx).

Nguồn dữ liệu (theo thứ tự ưu tiên):
  1. Màu THỰC SỰ ĐƯỢC DÙNG trong nội dung: a:srgbClr (slide, shape, chart), w:color / w:shd (Word),
     <color rgb>/<fgColor rgb> (Excel styles.xml). Đếm tần suất, tách màu nhấn (bão hòa) và màu trung tính.
  2. theme1.xml (clrScheme / fontScheme): chỉ dùng để lấp chỗ trống. Theme mặc định của Office
     (xanh 4472C4, 4F81BD, 156082...) KHÔNG được coi là màu thương hiệu.
  3. Font: font thực dùng (styles.xml Word, a:latin trong slide, font Excel) rồi mới đến fontScheme.

Kết quả: <out>/brand_kit.json theo schema trong resources/extractor_docs.md, có thêm "_sources" ghi
nguồn từng màu để Agent kiểm tra.

Mã thoát: 0 = có màu thương hiệu thật; 3 = chỉ có theme mặc định Office / không đủ màu riêng
(file vẫn được ghi để xem, nhưng KHÔNG dùng làm brand: hỏi người dùng hoặc chọn preset); 2 = lỗi file.
"""

import argparse
import colorsys
import json
import os
import re
import shutil
import sys
import zipfile
from collections import Counter

DEFAULT_OFFICE_ACCENTS = {
    "4472C4", "ED7D31", "A5A5A5", "FFC000", "5B9BD5", "70AD47",   # Office 2013-2022
    "4F81BD", "C0504D", "9BBB59", "8064A2", "4BACC6", "F79646",   # Office 2007-2010
    "156082", "E97132", "196B24", "0F9ED5", "A02B93", "4EA72E",   # Office 2023+
}
KEYS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6"]


def hsv(hexstr):
    r, g, b = (int(hexstr[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)


def is_accent(c):
    h, s, v = hsv(c)
    return s >= 0.25 and v >= 0.2


def is_dark_neutral(c):
    h, s, v = hsv(c)
    return v <= 0.45 and s < 0.25


def is_light_neutral(c):
    h, s, v = hsv(c)
    return v >= 0.88 and s < 0.12 and c != "FFFFFF"


def theme_colors(xml):
    out = {}
    m = re.search(r"<a:clrScheme.*?</a:clrScheme>", xml, re.S)
    if not m:
        return out
    block = m.group(0)
    for k in KEYS:
        mm = re.search(rf"<a:{k}>(.*?)</a:{k}>", block, re.S)
        if mm:
            v = re.search(r'srgbClr val="([0-9A-Fa-f]{6})"', mm.group(1)) or \
                re.search(r'lastClr="([0-9A-Fa-f]{6})"', mm.group(1))
            if v:
                out[k] = v.group(1).upper()
    return out


def theme_fonts(xml):
    maj = re.search(r"<a:majorFont>\s*<a:latin typeface=\"([^\"]*)\"", xml)
    mnr = re.search(r"<a:minorFont>\s*<a:latin typeface=\"([^\"]*)\"", xml)
    return (maj.group(1) if maj else None), (mnr.group(1) if mnr else None)


def _count(xml, used, fonts, weight=1):
    for v in re.findall(r'<a:srgbClr val="([0-9A-Fa-f]{6})"', xml):
        used[v.upper()] += weight
    for v in re.findall(r'<w:color w:val="([0-9A-Fa-f]{6})"', xml):
        used[v.upper()] += weight
    for v in re.findall(r'<w:shd [^>]*w:fill="([0-9A-Fa-f]{6})"', xml):
        used[v.upper()] += 2 * weight
    for v in re.findall(r'<(?:color|fgColor|bgColor) rgb="(?:FF)?([0-9A-Fa-f]{6})"', xml):
        used[v.upper()] += weight
    for f in re.findall(r'<a:latin typeface="([^"+][^"]*)"', xml):
        fonts[f] += weight
    for f in re.findall(r'<w:rFonts [^>]*w:ascii="([^"]+)"', xml):
        fonts[f] += weight


def scan(archive):
    """Đếm màu/font THỰC SỰ dùng. Với Word, styles.xml chỉ tính các style được tham chiếu trong nội dung
    (template mặc định chứa hàng chục style màu Office không dùng tới)."""
    used, fonts = Counter(), Counter()
    heading_font = None
    names = archive.namelist()
    content_xml = ""
    for name in names:
        if not name.endswith(".xml") or "/theme/" in name or name.endswith("word/styles.xml"):
            continue
        if name.startswith("word/") and not re.search(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$", name):
            continue
        xml = archive.read(name).decode("utf8", "ignore")
        if name.startswith("word/"):
            content_xml += xml
        _count(xml, used, fonts)
    if "word/styles.xml" in names:
        styles = archive.read("word/styles.xml").decode("utf8", "ignore")
        ids = set(re.findall(r'<w:(?:pStyle|rStyle|tblStyle) w:val="([^"]+)"', content_xml)) | {"Normal"}
        blocks = {m.group(1): m.group(0) for m in re.finditer(
            r'<w:style [^>]*w:styleId="([^"]+)".*?</w:style>', styles, re.S)}
        frontier = list(ids)
        while frontier:  # thêm style gốc (basedOn) của style được dùng
            b = blocks.get(frontier.pop())
            if b:
                m = re.search(r'<w:basedOn w:val="([^"]+)"', b)
                if m and m.group(1) not in ids:
                    ids.add(m.group(1))
                    frontier.append(m.group(1))
        for sid in ids:
            if sid in blocks:
                _count(blocks[sid], used, fonts, weight=3)
        defaults = re.search(r"<w:docDefaults>.*?</w:docDefaults>", styles, re.S)
        if defaults:
            _count(defaults.group(0), Counter(), fonts)
        if "Heading1" in ids and "Heading1" in blocks:
            m = re.search(r'w:ascii="([^"]+)"', blocks["Heading1"])
            heading_font = m.group(1) if m else None
    return used, fonts, heading_font


def build_kit(path):
    kit = {"company_name": os.path.splitext(os.path.basename(path))[0], "colors": {}, "fonts": {},
           "assets": {}, "_sources": {}}
    with zipfile.ZipFile(path) as z:
        theme_xml = next((z.read(n).decode("utf8", "ignore") for n in z.namelist()
                          if re.search(r"(word|ppt|xl)/theme/theme1\.xml$", n)), "")
        used, fonts, heading_font = scan(z)
        media = [n for n in z.namelist() if re.match(r"(word|ppt|xl)/media/", n) and not n.endswith("/")]
    th = theme_colors(theme_xml) if theme_xml else {}
    th_major, th_minor = theme_fonts(theme_xml) if theme_xml else (None, None)
    theme_is_default = bool(th) and {th.get(f"accent{i}") for i in range(1, 7)} <= DEFAULT_OFFICE_ACCENTS

    accents = [c for c, _ in used.most_common() if is_accent(c)]
    darks = [c for c, _ in used.most_common() if is_dark_neutral(c)]
    lights = [c for c, _ in used.most_common() if is_light_neutral(c)]
    colors, src = {}, {}

    def put(k, v, s):
        if v and k not in colors:
            colors[k] = v
            src[k] = s

    for i, c in enumerate(accents[:6], 1):
        put(f"accent{i}", c, f"màu dùng thực tế (xếp hạng {i})")
    put("dk1", darks[0] if darks else None, "màu chữ tối dùng nhiều nhất")
    put("dk2", darks[1] if len(darks) > 1 else None, "màu tối thứ hai")
    put("lt2", lights[0] if lights else None, "màu nền sáng dùng nhiều nhất")
    for k in KEYS:
        if k not in colors and k in th and not (theme_is_default and k.startswith("accent")):
            put(k, th[k], "theme1.xml" + (" (theme mặc định Office)" if theme_is_default else ""))
    put("lt1", "FFFFFF", "mặc định nền trắng")
    put("dk1", "000000", "mặc định chữ đen")

    body_font = next((f for f, _ in fonts.most_common() if not f.startswith("+")), None) or th_minor
    head_font = heading_font or th_major or body_font
    if body_font:
        kit["fonts"]["body"] = body_font
        kit["_sources"]["font.body"] = "font dùng nhiều nhất" if fonts else "theme1.xml"
    if head_font:
        kit["fonts"]["heading"] = head_font
    kit["colors"] = {k: colors[k] for k in KEYS if k in colors}
    kit["_sources"].update(src)
    return kit, media, len(accents), theme_is_default


def main():
    ap = argparse.ArgumentParser(description="Bóc Brand Kit từ file Office (màu dùng thực tế + theme + font + ảnh)")
    ap.add_argument("file", help=".docx, .pptx hoặc .xlsx")
    ap.add_argument("--out", required=True, help="Thư mục brand kit, vd standards/brand_kits/<ten_doanh_nghiep>")
    a = ap.parse_args()
    if not os.path.isfile(a.file):
        print(f"❌ File không tồn tại: {a.file}", file=sys.stderr)
        sys.exit(2)
    try:
        kit, media, n_accents, theme_default = build_kit(a.file)
    except zipfile.BadZipFile:
        print("❌ Không phải file OOXML hợp lệ (.docx/.pptx/.xlsx)", file=sys.stderr)
        sys.exit(2)

    os.makedirs(os.path.join(a.out, "assets"), exist_ok=True)
    with zipfile.ZipFile(a.file) as z:
        for i, item in enumerate(media):
            target = os.path.join(a.out, "assets", os.path.basename(item))
            with z.open(item) as s, open(target, "wb") as t:
                shutil.copyfileobj(s, t)
            if i == 0:
                kit["assets"]["logo"] = f"assets/{os.path.basename(item)}"
                kit["_sources"]["logo"] = "ảnh đầu tiên trong media/ - PHẢI mở ảnh xác nhận đúng là logo"
    path = os.path.join(a.out, "brand_kit.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(kit, f, indent=2, ensure_ascii=False)

    print(f"Đã ghi {path}")
    for k, v in kit["colors"].items():
        print(f"  {k:8} {v}  <- {kit['_sources'].get(k, '')}")
    print(f"  font    heading={kit['fonts'].get('heading')} body={kit['fonts'].get('body')}")
    if n_accents == 0:
        why = "chỉ có theme mặc định của Office" if theme_default else "không tìm thấy màu nhấn nào"
        print(f"⚠️  KHÔNG CÓ MÀU THƯƠNG HIỆU: file {why}. Không dùng kit này; hỏi người dùng mã màu/logo "
              "hoặc đề xuất preset trong standards/brand_kits/README.md.")
        sys.exit(3)
    if n_accents < 2:
        print("⚠️  Chỉ bóc được 1 màu nhấn; các màu còn lại lấy từ theme. Xác nhận với người dùng trước khi dùng.")
    print("✅ Brand kit có màu dùng thực tế. Mở file mẫu và so màu bằng mắt trước khi generate.")


if __name__ == "__main__":
    main()
