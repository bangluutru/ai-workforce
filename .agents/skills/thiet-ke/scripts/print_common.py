#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""print_common.py - Hàm dùng chung cho export_print_pdf.py / preflight.py / new_design.py (thiet-ke)."""

import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = SKILL_DIR.parent.parent.parent
FONTS_DIR = SKILL_DIR.parent / "_shared" / "fonts"   # kho font dùng chung (Luật R7)
VENV_PY = WORKSPACE / ".venv" / "bin" / "python"

PT_PER_MM = 72.0 / 25.4


def mm2pt(v: float) -> float:
    return v * PT_PER_MM


def pt2mm(v: float) -> float:
    return v / PT_PER_MM


def require_playwright():
    """Import Playwright hoặc thoát với hướng dẫn rõ ràng (KHÔNG fallback âm thầm)."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return sync_playwright
    except ImportError:
        print("❌ LỖI: Python hiện tại không có Playwright -> KHÔNG thể xuất PDF in ấn.", file=sys.stderr)
        print(f"   Python đang dùng: {sys.executable}", file=sys.stderr)
        print(f"   Hãy chạy bằng Python của repo: {VENV_PY} <script> ...", file=sys.stderr)
        print("   Nếu .venv chưa có: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt "
              "&& .venv/bin/python -m playwright install chromium", file=sys.stderr)
        sys.exit(2)


def require_fitz():
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24
    except ImportError:
        try:
            import fitz  # type: ignore
        except ImportError:
            print(f"❌ LỖI: thiếu PyMuPDF. Chạy bằng {VENV_PY} hoặc pip install pymupdf.", file=sys.stderr)
            sys.exit(2)
    return fitz


def parse_size(text: str):
    """'297x210' -> (297.0, 210.0) mm."""
    m = re.match(r"^\s*([\d.]+)\s*[xX×*]\s*([\d.]+)\s*$", str(text))
    if not m:
        raise ValueError(f"Kích thước không hợp lệ: {text!r} (định dạng đúng: 297x210)")
    return float(m.group(1)), float(m.group(2))


def read_print_meta(html_path: Path) -> dict:
    """Đọc <meta name="print:trim"> và <meta name="print:bleed"> trong file HTML."""
    meta = {}
    try:
        text = Path(html_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return meta
    for key in ("trim", "bleed"):
        m = re.search(r'<meta\s+name=["\']print:%s["\']\s+content=["\']([^"\']+)["\']' % key, text, re.I)
        if m:
            meta[key] = m.group(1).strip()
    return meta


def bundled_fontface_css() -> str:
    """CSS @font-face trỏ tuyệt đối tới font đóng gói (dùng làm lưới an toàn khi export)."""
    css_path = FONTS_DIR / "fonts.css"
    css = css_path.read_text(encoding="utf-8")
    base = FONTS_DIR.as_uri() + "/"
    return re.sub(r'url\("([^"/]+\.ttf)"\)', lambda m: f'url("{base}{m.group(1)}")', css)
