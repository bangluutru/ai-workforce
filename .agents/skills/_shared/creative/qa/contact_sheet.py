#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Visual Contact Sheet Generator (Luật R7).
Ghép các khung hình mẫu thành bức ảnh tiếp xúc tổng quan (Contact Sheet Grid),
gắn nhãn thời gian và cờ cảnh báo thị giác cho con người thẩm định nhanh.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .frame_sampler import SampledFrame


def generate_contact_sheet(
    frames: List[SampledFrame],
    output_path: str,
    columns: int = 4,
    cell_width: int = 360,
    title: str = "CREATIVE STUDIO 2.0 — VISUAL CONTACT SHEET",
) -> str:
    """
    Tạo ảnh Contact Sheet dạng lưới từ danh sách các khung hình đã lấy mẫu.
    
    Args:
        frames: Danh sách SampledFrame
        output_path: Đường dẫn lưu ảnh contact_sheet.jpg
        columns: Số cột trong lưới (mặc định 4)
        cell_width: Chiều rộng mỗi ô hình (mặc định 360px)
        title: Tiêu đề banner ở đỉnh ảnh
        
    Returns:
        str: Đường dẫn file ảnh đã lưu.
    """
    if not frames:
        raise ValueError("Danh sách frames rỗng, không thể tạo contact sheet.")

    n = len(frames)
    cols = max(1, min(columns, n))
    rows = math.ceil(n / cols)

    # Tính toán kích thước ô dựa trên tỷ lệ khung hình đầu tiên
    first = frames[0]
    aspect = first.width / first.height if first.height > 0 else 1.0
    cell_h = int(cell_width / aspect)

    header_height = 60
    padding = 12
    footer_cell_label = 24

    total_w = cols * cell_width + (cols + 1) * padding
    total_h = header_height + rows * (cell_h + footer_cell_label) + (rows + 1) * padding

    # Tạo canvas nền tối hiện đại
    sheet = Image.new("RGB", (total_w, total_h), color=(15, 17, 26))
    draw = ImageDraw.Draw(sheet)

    # Vẽ tiêu đề Header
    draw.rectangle([(0, 0), (total_w, header_height)], fill=(24, 27, 40))
    draw.text((padding + 8, 18), title, fill=(240, 240, 250))

    # Ghép từng khung hình vào lưới
    for idx, f in enumerate(frames):
        r = idx // cols
        c = idx % cols

        x0 = padding + c * (cell_width + padding)
        y0 = header_height + padding + r * (cell_h + footer_cell_label + padding)

        # Chuyển đổi rgb_array sang PIL Image và resize
        pil_frame = Image.fromarray(f.rgb_array).resize((cell_width, cell_h), Image.Resampling.LANCZOS)
        sheet.paste(pil_frame, (x0, y0))

        # Viền nhẹ quanh khung hình
        draw.rectangle([(x0, y0), (x0 + cell_width, y0 + cell_h)], outline=(60, 65, 85), width=1)

        # Nhãn thời gian và chỉ số ở đáy khung hình
        label_y = y0 + cell_h + 4
        lbl_text = f"#{f.index + 1:02d} · t={f.timestamp:.2f}s · lum={f.luminance_mean:.2f}"
        draw.text((x0 + 4, label_y), lbl_text, fill=(180, 185, 205))

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(str(out_file.resolve()), "JPEG", quality=90)

    return str(out_file.resolve())
