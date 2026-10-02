#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
office_utils.py - Tìm LibreOffice (soffice) trên macOS/Windows/Linux, recalc file xlsx, render PDF/PNG.
Dùng bởi verify_report.py và export_slides_deck.py. Không gọi dịch vụ ngoài.
"""

import glob
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_CANDIDATES = [
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    os.path.expanduser("~/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    "/usr/bin/soffice", "/usr/bin/libreoffice", "/usr/local/bin/soffice",
    "/opt/homebrew/bin/soffice", "/snap/bin/libreoffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def find_soffice():
    """Trả về đường dẫn soffice hoặc None. Thứ tự: $SOFFICE -> PATH -> vị trí cài đặt chuẩn."""
    env = os.environ.get("SOFFICE")
    if env and Path(env).exists():
        return env
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    for c in _CANDIDATES:
        if Path(c).exists():
            return c
    for c in glob.glob("/opt/libreoffice*/program/soffice"):
        return c
    return None


def require_soffice():
    p = find_soffice()
    if not p:
        raise RuntimeError(
            "Không tìm thấy LibreOffice (soffice). Cài đặt: macOS `brew install --cask libreoffice`, "
            "Ubuntu `sudo apt install libreoffice`, Windows tải tại libreoffice.org; "
            "hoặc đặt biến môi trường SOFFICE=<đường dẫn soffice>.")
    return p


def convert(src, fmt, outdir):
    """soffice --headless --convert-to <fmt>. Trả về đường dẫn file kết quả."""
    soffice = require_soffice()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    # Profile riêng để không đụng phiên LibreOffice đang mở của người dùng
    profile = Path(tempfile.mkdtemp(prefix="lo_profile_"))
    cmd = [soffice, f"-env:UserInstallation=file://{profile.as_posix()}", "--headless",
           "--convert-to", fmt, "--outdir", str(outdir), str(src)]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    out = outdir / (Path(src).stem + "." + fmt.split(":")[0])
    shutil.rmtree(profile, ignore_errors=True)
    if not out.exists():
        raise RuntimeError(f"LibreOffice không tạo được {out.name}: {res.stderr.strip() or res.stdout.strip()}")
    return out


def recalc_xlsx(path):
    """Mở bằng LibreOffice và lưu lại để mọi công thức có giá trị (cached values). Trả về file tạm."""
    tmp = Path(tempfile.mkdtemp(prefix="recalc_"))
    return convert(path, "xlsx", tmp)


def render_png(src, outdir, dpi=80):
    """Render file Office -> PDF -> PNG từng trang. Trả về danh sách PNG.
    Mỗi file render vào thư mục con riêng <tên>_<đuôi>/ để xlsx và pptx cùng tên không ghi đè nhau."""
    outdir = Path(outdir) / f"{Path(src).stem}_{Path(src).suffix.lstrip('.')}"
    pdf = convert(src, "pdf", outdir)
    stem = outdir / Path(src).stem
    pngs = []
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(stem)], check=True)
        pngs = sorted(outdir.glob(Path(src).stem + "-*.png"))
    else:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise RuntimeError("Cần pdftoppm (poppler) hoặc PyMuPDF để render PNG.")
        doc = fitz.open(str(pdf))
        for i, page in enumerate(doc, 1):
            p = outdir / f"{Path(src).stem}-{i}.png"
            page.get_pixmap(dpi=dpi).save(str(p))
            pngs.append(p)
    return pdf, pngs
