#!/usr/bin/env python3
"""
tile_page.py — Cắt trang scan thành các mảnh (tile) có chồng lấn để Agent đọc ở độ phân giải đầy đủ.

Khi nào dùng (BẮT BUỘC theo SKILL.md Bước 2.1):
  - Trang dày chữ (> ~35 dòng), bảng nhiều cột/nhiều số, chữ nhỏ (chú thích, footnote), dấu tiếng Việt khó nhìn;
  - Ảnh trang lớn (> 2500 px chiều dài): IDE sẽ thu nhỏ ảnh khi view_file, làm mất dấu và số.
  - Hoặc cắt một vùng cụ thể (bảng, con dấu, chữ ký) bằng --box theo tỉ lệ 0-1.

Usage:
  python3 tile_page.py <processing_dir> --page 3                     # tự chọn lưới theo kích thước ảnh
  python3 tile_page.py <processing_dir> --page 3 --rows 3 --cols 1   # 3 dải ngang
  python3 tile_page.py <processing_dir> --page 3 --box 0.05,0.40,0.95,0.75   # chỉ vùng bảng
Output: 02.process/tiles/page_NNN_rRcC.png (hoặc page_NNN_box_*.png)
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from PIL import Image

MAX_TILE_SIDE = 1800  # px: giữ dưới ngưỡng IDE thu nhỏ ảnh


def main() -> int:
    ap = argparse.ArgumentParser(description="Cắt trang scan thành tile có chồng lấn")
    ap.add_argument("processing_dir")
    ap.add_argument("--page", type=int, required=True)
    ap.add_argument("--rows", type=int, default=0)
    ap.add_argument("--cols", type=int, default=0)
    ap.add_argument("--overlap", type=float, default=0.06, help="tỉ lệ chồng lấn giữa các tile (mặc định 6%%)")
    ap.add_argument("--box", type=str, default=None, help="x0,y0,x1,y1 theo tỉ lệ 0-1 của trang")
    ap.add_argument("--source", choices=["original", "preprocessed"], default="original")
    a = ap.parse_args()

    root = Path(a.processing_dir)
    name = f"page_{a.page:03d}.png"
    src = root / "01.input" / name
    if a.source == "preprocessed" and (root / "02.process" / "preprocessed" / name).exists():
        src = root / "02.process" / "preprocessed" / name
    if not src.exists():
        print(f"[FAIL] Không thấy {src}")
        return 2
    im = Image.open(src)
    W, H = im.size
    out_dir = root / "02.process" / "tiles"
    out_dir.mkdir(parents=True, exist_ok=True)

    if a.box:
        x0, y0, x1, y1 = [float(v) for v in a.box.split(",")]
        crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        if max(crop.size) < 900:  # phóng to vùng nhỏ cho dễ đọc
            k = 900 / max(crop.size)
            crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
        out = out_dir / f"page_{a.page:03d}_box_{int(x0*100)}_{int(y0*100)}_{int(x1*100)}_{int(y1*100)}.png"
        crop.save(out)
        print(out)
        return 0

    rows = a.rows or max(1, math.ceil(H / MAX_TILE_SIDE))
    cols = a.cols or max(1, math.ceil(W / MAX_TILE_SIDE))
    th, tw = H / rows, W / cols
    oy, ox = int(th * a.overlap), int(tw * a.overlap)
    for r in range(rows):
        for c in range(cols):
            box = (max(0, int(c * tw) - ox), max(0, int(r * th) - oy),
                   min(W, int((c + 1) * tw) + ox), min(H, int((r + 1) * th) + oy))
            out = out_dir / f"page_{a.page:03d}_r{r + 1}c{c + 1}.png"
            im.crop(box).save(out)
            print(out)
    print(f"[OK] {rows}x{cols} tile (chồng lấn {a.overlap:.0%}). Đọc theo thứ tự r1c1, r1c2, ... ; "
          f"dòng nằm ở vùng chồng lấn chỉ ghi MỘT lần.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
