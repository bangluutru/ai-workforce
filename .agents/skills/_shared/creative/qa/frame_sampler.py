#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Smart Frame Sampler (Luật R7).
Trích xuất các khung hình chính (Keyframes) và các điểm lấy mẫu đồng đều từ video
thông qua FFmpeg, tối ưu bộ nhớ và phục vụ kiểm định thị giác.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image

_CURRENT_DIR = Path(__file__).resolve().parent
_SHARED_DIR = _CURRENT_DIR.parents[1]


def _get_ffmpeg_tools():
    try:
        from ffmpeg_tools import duration, ffmpeg_bin, ffprobe_bin
        return ffmpeg_bin, ffprobe_bin, duration
    except ImportError:
        import sys
        media_path = str(_SHARED_DIR / "media")
        if media_path not in sys.path:
            sys.path.insert(0, media_path)
        from ffmpeg_tools import duration, ffmpeg_bin, ffprobe_bin
        return ffmpeg_bin, ffprobe_bin, duration


@dataclass
class SampledFrame:
    """Đại diện cho một khung hình được trích xuất để kiểm định thị giác."""
    index: int
    timestamp: float
    width: int
    height: int
    rgb_array: np.ndarray  # Shape: (height, width, 3), dtype: uint8
    image_path: Optional[str] = None

    @property
    def luminance_mean(self) -> float:
        """Độ sáng trung bình (0.0 = đen hoàn toàn, 1.0 = trắng hoàn toàn)."""
        r = self.rgb_array[:, :, 0].astype(np.float32)
        g = self.rgb_array[:, :, 1].astype(np.float32)
        b = self.rgb_array[:, :, 2].astype(np.float32)
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        return float(np.mean(lum))


def extract_frame_at(
    video_path: str,
    timestamp: float,
    target_width: int = 480,
    save_path: Optional[str] = None,
) -> SampledFrame:
    """
    Trích xuất một khung hình tại thời điểm timestamp xác định.
    """
    ffmpeg_bin, _, _ = _get_ffmpeg_tools()
    ff = ffmpeg_bin()

    # Lấy kích thước gốc hoặc scale theo target_width giữ tỷ lệ
    cmd = [
        ff,
        "-ss",
        f"{timestamp:.3f}",
        "-i",
        video_path,
        "-vframes",
        "1",
        "-vf",
        f"scale={target_width}:-2",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "-",
    ]

    proc = subprocess.run(cmd, capture_output=True, check=True)
    import io
    img = Image.open(io.BytesIO(proc.stdout)).convert("RGB")
    arr = np.array(img, dtype=np.uint8)

    h, w, _ = arr.shape
    if save_path:
        img.save(save_path, "JPEG", quality=90)

    return SampledFrame(
        index=0,
        timestamp=round(timestamp, 3),
        width=w,
        height=h,
        rgb_array=arr,
        image_path=save_path,
    )


def sample_video_frames(
    video_path: str,
    count: int = 12,
    timestamps: Optional[List[float]] = None,
    target_width: int = 480,
    save_dir: Optional[str] = None,
) -> List[SampledFrame]:
    """
    Lấy mẫu danh sách khung hình từ video phục vụ QA 2.0.
    
    Args:
        video_path: Đường dẫn video MP4/MOV/WebM
        count: Số lượng khung hình lấy mẫu đồng đều (nếu không truyền timestamps)
        timestamps: Danh sách mốc thời gian cụ thể cần chụp
        target_width: Chiều rộng scale ảnh mẫu (mặc định 480px)
        save_dir: Thư mục lưu ảnh snapshot (tùy chọn)
        
    Returns:
        List[SampledFrame]: Danh sách các khung hình đã nạp vào bộ nhớ.
    """
    _, _, duration_func = _get_ffmpeg_tools()
    total_dur = duration_func(video_path)

    if timestamps:
        ts_list = [min(max(0.0, t), total_dur) for t in sorted(timestamps)]
    else:
        # Lấy mẫu phân bố đều, tránh viền 0s tuyệt đối để có frame hình ảnh thực tế
        count = max(3, count)
        if total_dur <= 1.0:
            ts_list = [k * total_dur / (count - 1) for k in range(count)]
        else:
            step = (total_dur - 0.2) / (count - 1)
            ts_list = [0.1 + k * step for k in range(count)]

    if save_dir:
        Path(save_dir).mkdir(parents=True, exist_ok=True)

    frames: List[SampledFrame] = []
    for idx, ts in enumerate(ts_list):
        img_out = os.path.join(save_dir, f"frame_{idx:03d}_{ts:.2f}s.jpg") if save_dir else None
        try:
            sf = extract_frame_at(video_path, ts, target_width=target_width, save_path=img_out)
            sf.index = idx
            frames.append(sf)
        except Exception:
            # Nếu ffmpeg không trích xuất được ở mốc cụ thể, fallback mốc trước đó
            continue

    return frames
