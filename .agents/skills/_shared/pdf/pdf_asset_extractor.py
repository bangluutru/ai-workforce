#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_asset_extractor.py - High-Fidelity Asset Extractor & Frame Preprocessor
AI Workforce - RetainPDF Layout Preservation Engine (Rule R6 Compliant)

Features:
1. Automatic Soft Mask (SMask) Alpha Decoding:
   - Pairs RGB Image XObjects with their /SMask transparency masks.
   - Performs alpha compositing over white or exports 4-channel RGBA PNGs.
   - Triệt tiêu hoàn toàn lỗi con dấu/chữ ký bị bôi đen nền.
2. High-Resolution Multi-Panel Subplot Bounding:
   - Crops composite scientific figures at 300 DPI including all subplots,
     axes, and statistical control limits without truncating lower charts.
3. Ornate Certificate Frame & Seal Isolation:
   - Whitewashes inner content area while preserving decorative gold borders.
   - Isolates standalone square seals and header logos.
"""

import os
import sys
import argparse
from pathlib import Path
import pymupdf
import cv2
import numpy as np
from PIL import Image


def extract_images_with_smask(doc: pymupdf.Document, page_num: int, output_dir: Path) -> list:
    """Extracts all embedded images on a given page, resolving soft masks if present."""
    output_dir.mkdir(parents=True, exist_ok=True)
    page = doc[page_num - 1]
    saved_files = []

    for img_idx, img_info in enumerate(page.get_images()):
        xref = img_info[0]
        smask_xref = img_info[1]
        width, height = img_info[2], img_info[3]

        pix = pymupdf.Pixmap(doc, xref)
        out_filename = f"p{page_num:02d}_img{img_idx}_{xref}.png"
        out_path = output_dir / out_filename

        if smask_xref > 0:
            # Decode soft mask and composite
            mask = pymupdf.Pixmap(doc, smask_xref)
            pix_bytes = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
            mask_bytes = np.frombuffer(mask.samples, dtype=np.uint8).reshape((mask.height, mask.width, mask.n))

            rgb = pix_bytes[:, :, :3].astype(np.float32)
            alpha = (mask_bytes[:, :, 0:1].astype(np.float32)) / 255.0

            # Composite over white
            white_bg = np.ones_like(rgb) * 255.0
            composited_white = (rgb * alpha + white_bg * (1.0 - alpha)).astype(np.uint8)

            # Export RGBA
            rgba = np.zeros((pix.height, pix.width, 4), dtype=np.uint8)
            rgba[:, :, :3] = composited_white
            rgba[:, :, 3] = mask_bytes[:, :, 0]

            pil_img = Image.fromarray(rgba, 'RGBA')
            pil_img.save(str(out_path))
            print(f"  ✅ Extracted masked image: {out_filename} ({width}x{height}) [SMask applied]")
        else:
            if pix.n >= 5:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            pix.save(str(out_path))
            print(f"  ✅ Extracted standard image: {out_filename} ({width}x{height})")

        saved_files.append(str(out_path))

    return saved_files


def crop_high_res_figure(doc: pymupdf.Document, page_num: int, bbox_300dpi: tuple, output_path: Path, dpi: int = 300) -> str:
    """Renders page at high DPI and crops bounding box [ymin:ymax, xmin:xmax] in pixels."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page = doc[page_num - 1]
    pix = page.get_pixmap(dpi=dpi)
    img = cv2.imdecode(np.frombuffer(pix.tobytes(), np.uint8), cv2.IMREAD_COLOR)

    ymin, ymax, xmin, xmax = bbox_300dpi
    cropped = img[ymin:ymax, xmin:xmax]
    cv2.imwrite(str(output_path), cropped)
    print(f"  ✅ Cropped figure: {output_path.name} ({cropped.shape[1]}x{cropped.shape[0]}px at {dpi} DPI)")
    return str(output_path)


def create_frame_template(doc: pymupdf.Document, page_num: int, clear_rect_300dpi: tuple, output_path: Path, dpi: int = 300) -> str:
    """Whitewashes inner text canvas of a page to produce a clean background frame."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page = doc[page_num - 1]
    pix = page.get_pixmap(dpi=dpi)
    img = cv2.imdecode(np.frombuffer(pix.tobytes(), np.uint8), cv2.IMREAD_COLOR)

    xmin, ymin, xmax, ymax = clear_rect_300dpi
    clean_frame = img.copy()
    cv2.rectangle(clean_frame, (xmin, ymin), (xmax, ymax), (255, 255, 255), -1)
    cv2.imwrite(str(output_path), clean_frame)
    print(f"  ✅ Created clean frame template: {output_path.name} ({clean_frame.shape[1]}x{clean_frame.shape[0]}px)")
    return str(output_path)


def isolate_seal_stamp(doc: pymupdf.Document, page_num: int, seal_bbox_300dpi: tuple, output_path: Path, dpi: int = 300) -> str:
    """Extracts a square seal stamp with clean borders at high resolution."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page = doc[page_num - 1]
    pix = page.get_pixmap(dpi=dpi)
    img = cv2.imdecode(np.frombuffer(pix.tobytes(), np.uint8), cv2.IMREAD_COLOR)

    ymin, ymax, xmin, xmax = seal_bbox_300dpi
    seal = img[ymin:ymax, xmin:xmax]
    cv2.imwrite(str(output_path), seal)
    print(f"  ✅ Isolated seal stamp: {output_path.name} ({seal.shape[1]}x{seal.shape[0]}px)")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="RetainPDF Asset & Figure Extractor (Rule R6 Compliant)")
    parser.add_argument("--pdf", required=True, help="Path to input PDF document")
    parser.add_argument("--output-dir", default="_process/extracted_assets", help="Directory to save extracted assets")
    parser.add_argument("--page", type=int, default=1, help="Page number (1-indexed)")
    parser.add_argument("--extract-all", action="store_true", help="Extract all embedded images across all pages with smask resolution")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"❌ Error: File not found: {pdf_path}")
        sys.exit(1)

    doc = pymupdf.open(str(pdf_path))
    out_dir = Path(args.output_dir)

    print("=" * 75)
    print("🔬 RETAIN-PDF ASSET EXTRACTOR (RULE R6)")
    print(f"📄 Document: {pdf_path.name} ({len(doc)} pages)")
    print(f"📁 Output Directory: {out_dir}")
    print("=" * 75)

    if args.extract_all:
        total = 0
        for p in range(1, len(doc) + 1):
            imgs = extract_images_with_smask(doc, p, out_dir)
            total += len(imgs)
        print(f"🎉 Successfully processed all {len(doc)} pages. Total embedded images extracted: {total}")
    else:
        extract_images_with_smask(doc, args.page, out_dir)


if __name__ == "__main__":
    main()
