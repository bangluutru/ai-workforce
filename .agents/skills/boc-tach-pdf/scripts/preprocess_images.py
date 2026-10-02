#!/usr/bin/env python3
"""
preprocess_images.py — Tiền xử lý ảnh scan để Agent đọc dễ hơn.

NGUYÊN TẮC: KHÔNG BAO GIỜ GHI ĐÈ ẢNH GỐC trong 01.input/ (ảnh gốc dùng cho đối chiếu OCR, crop hình minh họa,
và để làm lại). Ảnh đã xử lý ghi vào 02.process/preprocessed/page_NNN.png. Chạy lại nhiều lần không cộng dồn.

Tầng 1 (mặc định, Pillow): lọc trung vị 3x3 (xóa hạt nhiễu) + autocontrast nhẹ. Không làm nét (làm nét khuếch đại nhiễu).
Tầng 2 (--enhance): + khử nghiêng bằng projection profile (ổn định với nhiễu hạt) + khử nhiễu
                    (OpenCV fastNlMeansDenoising nếu có, nếu không dùng lọc trung vị).

Usage:
    python3 preprocess_images.py <thư_mục_processing>
    python3 preprocess_images.py <thư_mục_processing> --enhance
    python3 preprocess_images.py <thư_mục_processing> --enhance --pages 3,7
Output: 02.process/preprocessed/page_NNN.png + 02.process/preprocess_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps


def tier1(img: Image.Image) -> Image.Image:
    g = img.convert("L")
    g = g.filter(ImageFilter.MedianFilter(3))
    return ImageOps.autocontrast(g, cutoff=0.5)


def estimate_skew(gray: Image.Image, max_angle: float = 5.0) -> float:
    """Góc nghiêng (độ) bằng projection profile: góc làm các dòng chữ 'thẳng hàng' nhất
    (phương sai tổng hàng ngang lớn nhất). Ổn định với nhiễu hạt vì nhiễu phân bố đều."""
    import numpy as np

    small = gray.copy()
    scale = 1200 / max(small.size)
    if scale < 1:
        small = small.resize((int(small.width * scale), int(small.height * scale)))
    small = small.filter(ImageFilter.MedianFilter(3))
    arr = np.asarray(small, dtype=np.float32)
    thr = arr.mean() - 1.0 * arr.std()          # chỉ lấy nét chữ đậm, bỏ nền và hạt nhiễu nhạt
    ink = Image.fromarray(((arr < thr) * 255).astype("uint8"))

    def score(angle: float) -> float:
        rot = np.asarray(ink.rotate(angle, resample=Image.BILINEAR, fillcolor=0), dtype=np.float32)
        prof = rot.sum(axis=1)
        return float(np.var(prof))

    best = max((a / 2 for a in range(int(-max_angle * 2), int(max_angle * 2) + 1)), key=score)
    fine = max((best + d / 20 for d in range(-10, 11)), key=score)
    return round(fine, 2)


def denoise(gray: Image.Image) -> Image.Image:
    try:
        import cv2
        import numpy as np
        arr = np.asarray(gray)
        out = cv2.fastNlMeansDenoising(arr, None, 10, 7, 21)  # đối số vị trí: tương thích OpenCV 4 và 5
        return Image.fromarray(out)
    except Exception as e:  # noqa: BLE001  (thiếu cv2 hoặc lỗi API -> dùng lọc trung vị, BÁO RÕ)
        print(f"    [WARN] OpenCV denoise không dùng được ({type(e).__name__}); dùng MedianFilter(3).")
        return gray.filter(ImageFilter.MedianFilter(3))


def main() -> int:
    ap = argparse.ArgumentParser(description="Tiền xử lý ảnh scan (không ghi đè ảnh gốc)")
    ap.add_argument("processing_dir")
    ap.add_argument("--enhance", action="store_true", help="Tầng 2: khử nghiêng + khử nhiễu")
    ap.add_argument("--pages", default=None, help="VD: 1,3,5 (mặc định: tất cả)")
    a = ap.parse_args()

    root = Path(a.processing_dir)
    input_dir = root / "01.input"
    out_dir = root / "02.process" / "preprocessed"
    out_dir.mkdir(parents=True, exist_ok=True)
    images = sorted(input_dir.glob("page_*.png"))
    if a.pages:
        want = {int(x) for x in a.pages.split(",") if x.strip()}
        images = [p for p in images if int(p.stem.split("_")[1]) in want]
    if not images:
        print(f"[FAIL] Không tìm thấy ảnh page_*.png trong {input_dir}")
        return 2

    report_path = root / "02.process" / "preprocess_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    failed = 0
    print(f"[INFO] {len(images)} ảnh. Tầng 1{' + Tầng 2' if a.enhance else ''}. Ảnh gốc giữ nguyên.")
    for p in images:
        try:
            img = Image.open(p)
            g = tier1(img)
            entry = {"tier": 2 if a.enhance else 1}
            if a.enhance:
                angle = estimate_skew(g)
                entry["skew_deg"] = angle
                if abs(angle) >= 0.2:
                    g = g.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=255)
                g = denoise(g)
                print(f"  {p.name}: khử nghiêng {angle:+.2f}°")
            g.save(out_dir / p.name)
            report[p.name] = entry
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  [FAIL] {p.name}: {e}")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'OK' if not failed else 'FAIL'}] {len(images) - failed}/{len(images)} ảnh -> {out_dir}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
