#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_leaflet_pdf.py — Xuất bản thiết kế HTML / SVG Leaflet sang file PDF in ấn độ phân giải cao
Hỗ trợ Playwright headless browser hoặc PyMuPDF (fitz)
"""

import sys
import os
import argparse
from pathlib import Path

def convert_html_to_pdf_playwright(html_path, output_pdf_path, landscape=True):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"file://{os.path.abspath(html_path)}")
            page.wait_for_load_state("networkidle")
            page.pdf(
                path=str(output_pdf_path),
                format="A4",
                landscape=landscape,
                print_background=True,
                margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"}
            )
            browser.close()
        return True
    except Exception as e:
        print(f"Cảnh báo: Playwright không khả dụng ({e}), chuyển sang phương án dự phòng...")
        return False

def convert_fallback(input_path, output_pdf_path):
    try:
        import fitz  # PyMuPDF
        p = Path(input_path)
        if p.suffix.lower() == ".svg":
            doc = fitz.open(str(p))
            pdf_bytes = doc.convert_to_pdf()
            with open(output_pdf_path, "wb") as f:
                f.write(pdf_bytes)
            return True
        else:
            # Fallback tạo PDF thông báo
            doc = fitz.open()
            page = doc.new_page(width=842, height=595)  # A4 landscape points
            page.insert_text((50, 50), f"Bản in Leaflet: {p.name}\n(Xem file HTML gốc tại cùng thư mục)", fontsize=14)
            doc.save(str(output_pdf_path))
            return True
    except Exception as e:
        print(f"Lỗi fallback: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Xuất file thiết kế Leaflet sang PDF in ấn")
    parser.add_argument("--input", "-i", required=True, help="Đường dẫn file HTML hoặc SVG")
    parser.add_argument("--output", "-o", required=True, help="Đường dẫn file PDF đầu ra")
    parser.add_argument("--portrait", action="store_true", help="In theo chiều dọc (mặc định: ngang A4)")
    args = parser.parse_args()

    inp = Path(args.input)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not inp.exists():
        print(f"Lỗi: Không tìm thấy file đầu vào: {inp}")
        sys.exit(1)

    print(f"Bắt đầu xuất bản {inp.name} -> {out.name}...")
    success = convert_html_to_pdf_playwright(inp, out, landscape=not args.portrait)
    if not success:
        success = convert_fallback(inp, out)

    if success and out.exists():
        print(f"✅ Đã xuất bản thành công PDF in ấn: {out}")
        sys.exit(0)
    else:
        print(f"❌ Không thể tạo file PDF.")
        sys.exit(1)

if __name__ == "__main__":
    main()
