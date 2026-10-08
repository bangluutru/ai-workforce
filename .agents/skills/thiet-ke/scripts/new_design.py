#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
new_design.py - Khởi tạo thư mục thiết kế in ấn từ template chuẩn (đã có bleed, nếp gấp, font tiếng Việt).

  python3 .agents/skills/thiet-ke/scripts/new_design.py --template trifold --out _process/thiet_ke_<du_an>/

Tạo: <out>/design.html (bản sao template), <out>/fonts/ (font OFL + fonts.css), <out>/images/, <out>/facts.md
"""

import argparse
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SHARED_FONTS = SKILL_DIR.parent / "_shared" / "fonts"   # kho font dùng chung (Luật R7)
PRINT_FONTS = ("BeVietnamPro-*.ttf", "Spectral-*.ttf", "OFL-*.txt", "fonts.css")   # chỉ bộ font in ấn, không chép font Nhật/phụ đề
TEMPLATES = {
    "trifold": ("leaflet_trifold_a4.html", "Tờ gấp 3 A4 (297x210, panel 97/100/100mm)"),
    "bifold": ("leaflet_bifold_a4.html", "Tờ gấp đôi A4 -> A5"),
    "poster_a3": ("poster_a3.html", "Poster A3 dọc 297x420"),
    "slides_16x9": ("slides_16x9.html", "Slide 16:9 (không bleed)"),
}

FACTS_TEMPLATE = """# Bảng dữ kiện ấn phẩm (nguồn sự thật duy nhất)

Chỉ điền thông tin NGƯỜI DÙNG cung cấp. Mục nào chưa có -> để nguyên `[CẦN XÁC MINH: ...]` và
giữ nguyên chuỗi đó trên ấn phẩm. TUYỆT ĐỐI KHÔNG tự bịa tên, địa chỉ, số điện thoại, giá,
giấy phép, số liệu, chứng nhận, đánh giá khách hàng.

| Trường | Giá trị | Nguồn (tin nhắn / file của người dùng) |
|---|---|---|
| Tên thương hiệu | [CẦN XÁC MINH: tên] | |
| Địa chỉ | [CẦN XÁC MINH: địa chỉ] | |
| Điện thoại | [CẦN XÁC MINH: điện thoại] | |
| Giờ mở cửa | [CẦN XÁC MINH: giờ] | |
| Bảng giá / sản phẩm | [CẦN XÁC MINH: bảng giá] | |
| Khổ in / số lượng / giấy | [CẦN XÁC MINH: quy cách nhà in] | |
"""


def main():
    ap = argparse.ArgumentParser(description="Khởi tạo thiết kế in ấn từ template chuẩn thiet-ke")
    ap.add_argument("--template", "-t", required=True, choices=sorted(TEMPLATES), help="Loại ấn phẩm")
    ap.add_argument("--out", "-o", required=True, help="Thư mục làm việc (<process_dir>)")
    ap.add_argument("--force", action="store_true", help="Ghi đè design.html nếu đã tồn tại")
    args = ap.parse_args()

    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    tpl_name, desc = TEMPLATES[args.template]
    dst = out / "design.html"
    if dst.exists() and not args.force:
        print(f"❌ {dst} đã tồn tại (dùng --force để ghi đè).", file=sys.stderr)
        sys.exit(1)
    shutil.copy(SKILL_DIR / "templates" / tpl_name, dst)
    fonts_dst = out / "fonts"
    if fonts_dst.exists():
        shutil.rmtree(fonts_dst)
    fonts_dst.mkdir()
    for pattern in PRINT_FONTS:
        for f in sorted(SHARED_FONTS.glob(pattern)):
            shutil.copy(f, fonts_dst / f.name)
    (out / "images").mkdir(exist_ok=True)
    css_dst = out / "css"
    css_dst.mkdir(exist_ok=True)
    shared_dtp_css = SKILL_DIR.parent / "_shared" / "html" / "dtp_layout.css"
    if shared_dtp_css.exists():
        shutil.copy(shared_dtp_css, css_dst / "dtp_layout.css")
    facts = out / "facts.md"
    if not facts.exists():
        facts.write_text(FACTS_TEMPLATE, encoding="utf-8")

    print(f"✅ Đã khởi tạo {desc}")
    print(f"   HTML thiết kế : {dst}")
    print(f"   Font OFL      : {fonts_dst} (Be Vietnam Pro, Spectral)")
    print(f"   CSS DTP       : {css_dst / 'dtp_layout.css'} (Baseline Grid, Micro-typography)")
    print(f"   Ảnh           : {out / 'images'} (ảnh cần >= 300ppi ở kích thước đặt)")
    print(f"   Dữ kiện       : {facts}")
    print("   Tiếp theo: điền facts.md -> sửa design.html (chỉ vùng THIẾT KẾ) -> export_print_pdf.py -> preflight.py -> XEM ảnh PNG")


if __name__ == "__main__":
    main()
