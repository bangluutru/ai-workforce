#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_deps.py — Kiểm tra toàn bộ dependencies cho kỹ năng phu-de (AIWF).
Kiểm tra FFmpeg, ffprobe và các package Python (faster-whisper, pysubs2).
"""

import importlib
import os
import shutil
import subprocess
import sys


def find_binary(name):
    """Tìm đường dẫn binary trong PATH và các thư mục phổ biến trên macOS/Linux/Windows."""
    p = shutil.which(name)
    if p:
        return p
    common_paths = [
        f"/opt/homebrew/opt/ffmpeg-full/bin/{name}",
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
        f"/usr/bin/{name}",
        f"/bin/{name}",
        f"C:\\ffmpeg\\bin\\{name}.exe",
        f"C:\\Program Files\\ffmpeg\\bin\\{name}.exe",
    ]
    for cp in common_paths:
        if os.path.isfile(cp) and os.access(cp, os.X_OK):
            return cp
    return None


def get_binary_version(binary_path):
    try:
        res = subprocess.run([binary_path, "-version"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            first_line = res.stdout.strip().split("\n")[0]
            return first_line
    except Exception:
        pass
    return "Đã tìm thấy"


def check_python_package(import_name, pip_name, description):
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, "__version__", getattr(mod, "version", "unknown"))
        return True, str(version), description
    except ImportError:
        return False, None, description


def main():
    print("=" * 64)
    print("  KỸ NĂNG PHỤ ĐỀ (phu-de) — KIỂM TRA MÔI TRƯỜNG HỆ THỐNG")
    print("=" * 64)

    all_ok = True
    missing_bins = []
    missing_pips = []

    # 1. Kiểm tra System Binaries (FFmpeg & ffprobe)
    print("\n[1. Media Engine Binaries]")
    for b in ["ffmpeg", "ffprobe"]:
        b_path = find_binary(b)
        if b_path:
            v_info = get_binary_version(b_path)
            print(f"  ✅ {b:<10} : {b_path} ({v_info})")
        else:
            print(f"  ❌ {b:<10} : CHƯA CÓ TRONG HỆ THỐNG")
            missing_bins.append(b)
            all_ok = False

    # 2. Kiểm tra Python Libraries
    py_deps = [
        ("pysubs2", "pysubs2", "Biên dịch và đọc xuất định dạng ASS, SRT, VTT"),
        ("faster_whisper", "faster-whisper", "Nhận dạng giọng nói và trích xuất word-level timestamps"),
    ]

    print("\n[2. Python Dependencies]")
    for imp_name, pip_name, desc in py_deps:
        ok, ver, d = check_python_package(imp_name, pip_name, desc)
        if ok:
            print(f"  ✅ {pip_name:<16} (v{ver}) — {d}")
        else:
            print(f"  ⚠️  {pip_name:<16} — CHƯA CÀI — {d}")
            missing_pips.append(pip_name)
            all_ok = False

    # 3. Hướng dẫn khắc phục nếu thiếu
    print("\n" + "-" * 64)
    if all_ok:
        print("🎉 MÔI TRƯỜNG SẴN SÀNG 100% CHO KỸ NĂNG PHỤ ĐỀ (phu-de)")
        print("-" * 64)
        return 0

    print("⚠️  MỘT SỐ PHỤ THUỘC CẦN ĐƯỢC BỔ SUNG:")
    if missing_bins:
        print("\n* Cài đặt FFmpeg & ffprobe:")
        if sys.platform == "darwin":
            print("    brew install ffmpeg")
        elif sys.platform.startswith("linux"):
            print("    sudo apt update && sudo apt install -y ffmpeg")
        else:
            print("    winget install Gyan.FFmpeg hoặc tải từ https://ffmpeg.org")

    if missing_pips:
        print("\n* Cài đặt thư viện Python:")
        print(f"    pip install {' '.join(missing_pips)}")

    print("-" * 64)
    return 1


if __name__ == "__main__":
    sys.exit(main())
