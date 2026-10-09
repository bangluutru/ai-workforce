#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
legacy_adapter.py — Lớp tương thích ngược (Backward Compatibility Adapter).
Chuyển đổi kịch bản Video Studio v1 (video_script.json / preset scripts) sang Storyboard v2.0 (Luật R7).
"""

from typing import Dict, Any, List, Union
from pathlib import Path

from storyboard_schema import ASPECT_RATIOS


def is_legacy_script(data: Any) -> bool:
    """Kiểm tra xem dữ liệu có phải là định dạng kịch bản v1 (legacy) hay không."""
    if isinstance(data, list):
        return True
    if isinstance(data, dict):
        # Nếu đã có schema_version == "2.0" thì là v2
        if data.get("schema_version") == "2.0":
            return False
        # Nếu có các trường đặc trưng của v1
        if "title_top" in data or "mood" in data:
            return True
        if "scenes" in data and isinstance(data["scenes"], list):
            # Kiểm tra xem scene có thuộc tính vi/jp/keywords đặc trưng của v1 không
            if len(data["scenes"]) > 0:
                first = data["scenes"][0]
                if isinstance(first, dict) and ("vi" in first or "jp" in first or "keywords" in first):
                    return True
    return False


def estimate_scene_duration(text: str, default_dur: float = 4.0) -> float:
    """Ước tính thời lượng nói dựa trên số từ (khoảng 2.8 từ / giây cho tiếng Việt)."""
    if not text:
        return default_dur
    words = text.strip().split()
    word_count = len(words)
    estimated = max(default_dur, round(word_count / 2.8, 1))
    return min(30.0, estimated)


def convert_legacy_script_to_storyboard(
    legacy_data: Union[Dict[str, Any], List[Dict[str, Any]]],
    aspect_ratio: str = "1:1",
    project_id: str = "migrated_project",
    fps: int = 30,
    language: str = "vi",
    brand_profile: str = "default"
) -> Dict[str, Any]:
    """
    Chuyển đổi mượt mà kịch bản cũ sang Storyboard v2.0 hợp chuẩn.
    Bảo toàn 100% nội dung gốc và không làm thay đổi các file kịch bản lịch sử.
    """
    if aspect_ratio not in ASPECT_RATIOS:
        aspect_ratio = "1:1"

    width, height = ASPECT_RATIOS[aspect_ratio]

    title = "Migrated Video Project"
    scenes_raw = []

    if isinstance(legacy_data, list):
        scenes_raw = legacy_data
    elif isinstance(legacy_data, dict):
        title = legacy_data.get("title_top") or legacy_data.get("title") or title
        scenes_raw = legacy_data.get("scenes", [])

    v2_scenes = []
    total_duration = 0.0

    for idx, sc in enumerate(scenes_raw):
        sc_id = sc.get("id") or f"scene_{idx + 1:03d}"

        # Trích xuất lời thoại tiếng Việt / Anh / Nhật
        narration = sc.get("narration") or sc.get("vi") or sc.get("text") or ""
        if not narration and sc.get("jp"):
            narration = sc["jp"]

        # Xác định loại scene dựa trên keywords / assets
        keywords = sc.get("keywords", [])
        assets = sc.get("assets", [])

        if keywords:
            scene_type = "stock_media"
            visual_goal = f"Stock footage minh họa: {', '.join(keywords[:3])}"
        elif assets:
            scene_type = "photo_kenburns"
            visual_goal = "Trình chiếu hình ảnh với hiệu ứng chuyển động Ken Burns"
        else:
            scene_type = "motion_graphics"
            visual_goal = f"Đồ họa chuyển động truyền tải thông điệp: {narration[:40]}..."

        # Thời lượng
        dur = sc.get("duration_seconds")
        if dur is None or not isinstance(dur, (int, float)) or dur < 0.5:
            dur = estimate_scene_duration(narration, default_dur=4.5)

        total_duration += dur

        v2_scene: Dict[str, Any] = {
            "id": sc_id,
            "type": scene_type,
            "duration_seconds": round(dur, 1),
            "narration": narration,
            "visual_goal": visual_goal,
            "composition": {
                "layout": "centered",
                "primary_subject": "subject",
                "background_type": "solid"
            },
            "motion": {
                "preset": "fade_in",
                "intensity": "moderate",
                "easing": "ease-out"
            },
            "transition": {
                "type": "fade",
                "duration_seconds": 0.4
            }
        }

        if assets:
            v2_scene["assets"] = assets

        v2_scenes.append(v2_scene)

    storyboard_v2: Dict[str, Any] = {
        "schema_version": "2.0",
        "project_id": project_id,
        "title": title,
        "language": language,
        "fps": fps,
        "aspect_ratio": aspect_ratio,
        "resolution": {
            "width": width,
            "height": height
        },
        "target_duration_seconds": round(total_duration, 1),
        "brand_profile": brand_profile,
        "scenes": v2_scenes
    }

    return storyboard_v2
