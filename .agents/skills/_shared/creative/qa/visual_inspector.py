#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Visual Inspector (Luật R7).
Phân tích thị giác khách quan trên các khung hình video đã lấy mẫu:
phát hiện khung hình đen/cháy sáng, đứng hình (dead shot), cảnh trống và vi phạm vùng an toàn.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import numpy as np

from .frame_sampler import SampledFrame


@dataclass
class VisualFinding:
    level: str  # "FAIL", "WARN", "INFO"
    code: str
    message: str
    frame_index: Optional[int] = None
    timestamp: Optional[float] = None


@dataclass
class VisualInspectionResult:
    success: bool
    verdict: str  # "PASS", "WARN", "FAIL"
    score: int  # 0 -> 100
    findings: List[VisualFinding] = field(default_factory=list)
    frame_metrics: List[Dict[str, Any]] = field(default_factory=list)


def calculate_frame_difference(arr1: np.ndarray, arr2: np.ndarray) -> float:
    """Tính toán sai số chuyển động trung bình chuẩn hóa giữa 2 khung hình (0.0 đến 1.0)."""
    if arr1.shape != arr2.shape:
        return 1.0
    diff = np.abs(arr1.astype(np.float32) - arr2.astype(np.float32))
    return float(np.mean(diff) / 255.0)


def calculate_flat_color_ratio(arr: np.ndarray, threshold_distance: float = 25.0) -> float:
    """
    Tính toán tỷ lệ điểm ảnh thuộc về màu nền chiếm ưu thế nhất (đo độ phẳng/trống của khung hình).
    """
    # Downsample nhẹ để tăng tốc độ phân tích histogram
    small = arr[::4, ::4, :]
    h, w, c = small.shape
    total_pixels = h * w
    if total_pixels == 0:
        return 1.0

    # Lượng tử hóa 16 mức mỗi kênh màu để tìm màu chủ đạo
    quantized = (small >> 4).astype(np.int32)
    keys = (quantized[:, :, 0] << 8) | (quantized[:, :, 1] << 4) | quantized[:, :, 2]
    unique, counts = np.unique(keys, return_counts=True)
    if len(counts) == 0:
        return 1.0

    dominant_key = unique[np.argmax(counts)]
    dom_r = ((dominant_key >> 8) & 0xF) * 16 + 8
    dom_g = ((dominant_key >> 4) & 0xF) * 16 + 8
    dom_b = (dominant_key & 0xF) * 16 + 8
    dom_color = np.array([dom_r, dom_g, dom_b], dtype=np.float32)

    # Đếm số pixel nằm trong bán kính khoảng cách Euclidean
    diffs = np.linalg.norm(small.astype(np.float32) - dom_color, axis=2)
    matching_pixels = np.sum(diffs < threshold_distance)

    return float(matching_pixels / total_pixels)


def check_safe_area_activity(arr: np.ndarray, safe_margin_ratio: float = 0.05) -> float:
    """
    Đo lường mức độ tương phản hoặc chi tiết đồ họa sát mép khung hình (ngoài vùng an toàn).
    """
    h, w, _ = arr.shape
    my = max(2, int(h * safe_margin_ratio))
    mx = max(2, int(w * safe_margin_ratio))

    # Cắt 4 dải biên ngoài cùng
    top_band = arr[:my, :, :]
    bottom_band = arr[-my:, :, :]
    left_band = arr[:, :mx, :]
    right_band = arr[:, -mx:, :]

    # Tính độ lệch chuẩn màu sắc ở các dải biên ngoài
    stds = [np.std(top_band), np.std(bottom_band), np.std(left_band), np.std(right_band)]
    return float(np.mean(stds))


def inspect_visual_frames(
    frames: List[SampledFrame],
    safe_margin_ratio: float = 0.05,
    max_flat_ratio_threshold: float = 0.95,
) -> VisualInspectionResult:
    """
    Kiểm toán thị giác trên danh sách các khung hình đã trích xuất.
    
    Args:
        frames: Danh sách SampledFrame
        safe_margin_ratio: Tỷ lệ viền an toàn (mặc định 5%)
        max_flat_ratio_threshold: Ngưỡng cảnh báo frame quá trống (mặc định 95%)
    """
    if not frames:
        return VisualInspectionResult(
            success=False,
            verdict="FAIL",
            score=0,
            findings=[VisualFinding("FAIL", "no_frames_provided", "Không có khung hình nào được cung cấp để kiểm định.")],
        )

    findings: List[VisualFinding] = []
    frame_metrics: List[Dict[str, Any]] = []
    score = 100

    black_frame_count = 0
    white_frame_count = 0
    flat_frame_count = 0

    # 1. Kiểm tra từng khung hình đơn lẻ
    for f in frames:
        lum = f.luminance_mean
        flat_ratio = calculate_flat_color_ratio(f.rgb_array)
        safe_activity = check_safe_area_activity(f.rgb_array, safe_margin_ratio)

        is_black = lum < 0.015
        is_white = lum > 0.985
        is_flat = flat_ratio > max_flat_ratio_threshold

        if is_black:
            black_frame_count += 1
        if is_white:
            white_frame_count += 1
        if is_flat and not is_black:
            flat_frame_count += 1

        frame_metrics.append({
            "index": f.index,
            "timestamp": f.timestamp,
            "luminance": round(lum, 3),
            "flat_ratio": round(flat_ratio, 3),
            "safe_activity": round(safe_activity, 2),
            "is_black": is_black,
            "is_white": is_white,
            "is_flat": is_flat,
        })

    total_frames = len(frames)

    # Đánh giá tỷ lệ khung hình đen
    black_ratio = black_frame_count / total_frames
    if black_ratio > 0.5:
        findings.append(VisualFinding("FAIL", "excessive_black_frames", f"Hơn 50% khung hình bị đen hoàn toàn ({black_frame_count}/{total_frames} frames)."))
        score -= 50
    elif black_ratio > 0.2:
        findings.append(VisualFinding("WARN", "noticeable_black_frames", f"Có {black_frame_count}/{total_frames} khung hình bị tối hoàn toàn."))
        score -= 20

    # Đánh giá tỷ lệ khung hình phẳng / trống
    flat_ratio_total = flat_frame_count / total_frames
    if flat_ratio_total > 0.6:
        findings.append(VisualFinding("WARN", "mostly_empty_composition", f"Đa số khung hình ({flat_frame_count}/{total_frames}) có màu nền đơn điệu, thiếu chi tiết đồ họa."))
        score -= 15

    # 2. Kiểm tra chuyển động giữa các khung hình liên tiếp (Motion Delta / Frozen Detection)
    motion_deltas: List[float] = []
    frozen_segments = 0
    for i in range(len(frames) - 1):
        delta = calculate_frame_difference(frames[i].rgb_array, frames[i + 1].rgb_array)
        motion_deltas.append(delta)
        frame_metrics[i]["motion_to_next"] = round(delta, 4)

        # Nếu độ lệch gần như bằng 0 (< 0.002) mà thời gian cách nhau > 0.5s -> đứng hình
        time_gap = frames[i + 1].timestamp - frames[i].timestamp
        if delta < 0.002 and time_gap >= 0.5:
            frozen_segments += 1

    if motion_deltas:
        avg_motion = float(np.mean(motion_deltas))
        max_motion = float(np.max(motion_deltas))

        # Nếu tất cả các khung hình đều đứng yên (delta = 0 trên toàn bộ video)
        if max_motion < 0.001 and total_frames > 2:
            findings.append(VisualFinding("FAIL", "completely_frozen_video", "Video hoàn toàn đứng hình, không có bất kỳ chuyển động đồ họa nào."))
            score -= 60
        elif frozen_segments >= total_frames // 2:
            findings.append(VisualFinding("WARN", "prolonged_frozen_shots", f"Phát hiện {frozen_segments} đoạn chuyển cảnh bị đứng hình kéo dài."))
            score -= 20

    # Kết luận verdict
    has_fail = any(f.level == "FAIL" for f in findings)
    has_warn = any(f.level == "WARN" for f in findings)
    final_score = max(0, score)

    if has_fail or final_score < 70:
        verdict = "FAIL"
    elif has_warn or final_score < 90:
        verdict = "WARN"
    else:
        verdict = "PASS"

    return VisualInspectionResult(
        success=not has_fail,
        verdict=verdict,
        score=final_score,
        findings=findings,
        frame_metrics=frame_metrics,
    )
