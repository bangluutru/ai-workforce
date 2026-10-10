#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transitions.py — Áp dụng chuyển cảnh cho Storyboard v2.0 (Creative Studio 2.1, Phase 3).

Dùng lại trường ĐÃ CÓ của schema v2.0: scene["transition"] = {"type": ..., "duration_seconds": ...}
(loại hợp lệ theo storyboard_schema.TRANSITION_TYPES: none, fade, slide_left, slide_right, zoom, wipe).
Trước 2.1, renderer bỏ qua trường này (cắt thẳng). Từ 2.1 renderer áp dụng, NHƯNG chỉ khi storyboard khai báo
rõ ràng; không khai báo = cắt thẳng như cũ (tương thích ngược).

Tiện ích: khối `transitions` ở cấp storyboard làm mặc định cho mọi ranh giới:
    "transitions": {"default": "fade", "duration": 0.5}
Trường scene["transition"] (chuyển cảnh ở CUỐI cảnh đó, sang cảnh kế tiếp) ghi đè mặc định. Cảnh cuối bỏ qua.

Giữ nguyên mốc thời gian âm thanh: mỗi cảnh có chuyển cảnh phía sau được dựng DÀI THÊM đúng bằng thời lượng
chuyển cảnh (đuôi chồng lấn), nên cảnh kế tiếp vẫn BẮT ĐẦU đúng mốc danh nghĩa và tổng thời lượng video
= tổng thời lượng cảnh (không co lại như xfade thông thường). Lời đọc/BGM không bị lệch.

API:
    validate_transitions(storyboard) -> [lỗi]
    plan_transitions(storyboard, durations) -> [(loại, giây)]   # n-1 ranh giới; 'none' => giây = 0
    build_concat_filter(clip_lengths, plan, fps) -> (filter_complex, nhãn_cuối)
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple, Union

from .storyboard_schema import TRANSITION_TYPES  # nguồn duy nhất của danh sách loại hợp lệ

_XFADE = {"fade": "fade", "slide_left": "slideleft", "slide_right": "slideright", "zoom": "zoomin", "wipe": "wipeleft"}
MIN_DURATION, MAX_DURATION = 0.15, 1.5
DEFAULT_DURATION = 0.5


def _norm_item(item: Any) -> Tuple[str, Union[float, None], List[str]]:
    """Trả (loại, giây|None, lỗi)."""
    errs: List[str] = []
    if isinstance(item, str):
        t, d = item, None
    elif isinstance(item, dict):
        t, d = item.get("type"), item.get("duration_seconds", item.get("duration"))
    else:
        return "none", None, [f"chuyển cảnh phải là chuỗi hoặc object, nhận được {item!r}"]
    if t not in TRANSITION_TYPES:
        errs.append(f"loại chuyển cảnh '{t}' không hợp lệ (hỗ trợ: {list(TRANSITION_TYPES)})")
        t = "none"
    if d is not None and (isinstance(d, bool) or not isinstance(d, (int, float)) or not (MIN_DURATION <= d <= MAX_DURATION)):
        errs.append(f"thời lượng chuyển cảnh phải trong [{MIN_DURATION}, {MAX_DURATION}] giây, nhận được {d!r}")
        d = None
    return t, (float(d) if d is not None else None), errs


def validate_transitions(storyboard: Dict[str, Any]) -> List[str]:
    block = storyboard.get("transitions")
    errors: List[str] = []
    if block is not None:
        if not isinstance(block, dict):
            errors.append("transitions phải là một object.")
        else:
            if "default" in block:
                _, _, e = _norm_item(block["default"])
                errors += [f"transitions.default: {x}" for x in e]
            if "enabled" in block and not isinstance(block["enabled"], bool):
                errors.append("transitions.enabled phải là true/false.")
            d = block.get("duration")
            if d is not None and (isinstance(d, bool) or not isinstance(d, (int, float)) or not (MIN_DURATION <= d <= MAX_DURATION)):
                errors.append(f"transitions.duration phải trong [{MIN_DURATION}, {MAX_DURATION}] giây, nhận được {d!r}")
    # scene["transition"] đã được storyboard_validator kiểm tra theo schema v2.0 (không kiểm lại để không siết chặt hơn v2.0)
    return errors


def plan_transitions(storyboard: Dict[str, Any], durations: List[float]) -> List[Tuple[str, float]]:
    """Kế hoạch cho n-1 ranh giới. Thời lượng bị kẹp ≤ 45% cảnh ngắn hơn ở hai bên để cảnh luôn có thời gian đọc."""
    scenes = storyboard.get("scenes") or []
    block = storyboard.get("transitions") if isinstance(storyboard.get("transitions"), dict) else {}
    default_t, default_d, _ = _norm_item(block.get("default", "none")) if block else ("none", None, [])
    base_d = block.get("duration", DEFAULT_DURATION) if block else DEFAULT_DURATION
    plan: List[Tuple[str, float]] = []
    if block and block.get("enabled") is False:      # công tắc tắt toàn bộ chuyển cảnh
        return [("none", 0.0)] * max(0, len(scenes) - 1)
    for i in range(max(0, len(scenes) - 1)):
        t, d = default_t, (default_d if default_d is not None else float(base_d))
        if "transition" in scenes[i]:
            t2, d2, _ = _norm_item(scenes[i]["transition"])
            t, d = t2, (d2 if d2 is not None else float(base_d))
            raw = scenes[i]["transition"]
            raw_d = raw.get("duration_seconds") if isinstance(raw, dict) else None
            if isinstance(raw_d, (int, float)) and not isinstance(raw_d, bool):
                if raw_d <= 0:
                    t = "none"                       # v2.0 cho phép duration 0 = không chuyển
                else:
                    d = min(float(raw_d), MAX_DURATION)
        if t == "none":
            plan.append(("none", 0.0))
            continue
        cap = 0.45 * min(durations[i], durations[i + 1])
        plan.append((t, round(max(0.0, min(d, cap)), 3)))
        if plan[-1][1] < MIN_DURATION:
            plan[-1] = ("none", 0.0)
    return plan


def build_concat_filter(clip_lengths: List[float], plan: List[Tuple[str, float]], fps: int) -> Tuple[str, str]:
    """
    clip_lengths[i] = độ dài file clip i (đã gồm đuôi chồng lấn nếu có chuyển cảnh phía sau).
    Trả (filter_complex, nhãn video cuối). Cut dùng concat, còn lại dùng xfade.
    """
    n = len(clip_lengths)
    parts = [f"[{i}:v]fps={fps},format=yuv420p,setsar=1,settb=AVTB,setpts=PTS-STARTPTS[c{i}]" for i in range(n)]
    cur, length = "c0", clip_lengths[0]
    for i in range(1, n):
        kind, t = plan[i - 1]
        out = f"m{i}"
        if kind == "none" or t <= 0:
            parts.append(f"[{cur}][c{i}]concat=n=2:v=1:a=0[{out}]")
            length += clip_lengths[i]
        else:
            off = max(0.0, length - t)
            parts.append(f"[{cur}][c{i}]xfade=transition={_XFADE[kind]}:duration={t:.3f}:offset={off:.3f}[{out}]")
            length += clip_lengths[i] - t
        cur = out
    return ";".join(parts), cur
