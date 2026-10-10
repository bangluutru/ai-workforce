#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storyboard_validator.py — Bộ kiểm định tính toàn vẹn của Storyboard v2.0 (Luật R7).
Kiểm tra cấu trúc schema, tính độc nhất của scene ID, tỷ lệ khung hình, thời lượng và đường dẫn asset.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from storyboard_schema import (
    ASPECT_RATIOS,
    SCENE_TYPES,
    COMPOSITION_LAYOUTS,
    TRANSITION_TYPES,
    MOTION_INTENSITIES,
    EASING_FUNCTIONS,
)


class StoryboardValidationError(ValueError):
    """Lỗi khi cấu trúc storyboard không hợp lệ."""
    pass


def calculate_storyboard_durations(storyboard: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phân định rạch ròi giữa các loại thời lượng:
    - target_duration_seconds: Thời lượng mục tiêu do người dùng chỉ định.
    - planned_duration_seconds: Tổng thời lượng dự kiến từ các phân cảnh.
    - scene_durations: Danh sách thời lượng chi tiết từng cảnh.
    """
    scenes = storyboard.get("scenes", [])
    scene_durations = []
    total_planned = 0.0

    for idx, sc in enumerate(scenes):
        dur = float(sc.get("duration_seconds", 0.0))
        scene_durations.append({
            "scene_index": idx,
            "scene_id": sc.get("id", f"scene_{idx}"),
            "duration_seconds": dur
        })
        total_planned += dur

    target = storyboard.get("target_duration_seconds")
    target_val = float(target) if target is not None else None

    return {
        "target_duration_seconds": target_val,
        "planned_duration_seconds": round(total_planned, 3),
        "scene_count": len(scenes),
        "scene_durations": scene_durations,
        "duration_difference": round(total_planned - target_val, 3) if target_val is not None else None
    }


def validate_storyboard(
    storyboard: Dict[str, Any],
    check_asset_paths: bool = False,
    base_dir: Optional[Path | str] = None
) -> Tuple[bool, List[str]]:
    """
    Thẩm định nghiêm ngặt toàn diện Storyboard v2.0:
    Trắc nghiệm đầy đủ các điều kiện:
    1. Schema version bắt buộc là "2.0".
    2. project_id hợp lệ (chuỗi chữ số không dấu và gạch dưới/nối).
    3. fps thuộc danh mục hỗ trợ [24, 30, 60].
    4. resolution: width và height phải là số nguyên dương hợp lệ.
    5. aspect_ratio: nếu có thì phải nằm trong danh mục hỗ trợ và khớp tỷ lệ.
    6. Danh sách scenes: tối thiểu 1 cảnh.
    7. Scene ID: duy nhất, không được trùng lặp.
    8. Scene duration: phải là số thực > 0 (tối thiểu 0.5s).
    9. Transition: thời lượng chuyển cảnh không được vượt quá thời lượng của cảnh.
    10. Assets: nếu check_asset_paths=True, kiểm tra sự tồn tại của file asset cục bộ.

    Trả về: (is_valid: bool, errors: List[str])
    """
    errors: List[str] = []

    if not isinstance(storyboard, dict):
        return False, ["Storyboard phải là một JSON object (dict)."]

    # 1. Schema version
    version = storyboard.get("schema_version")
    if version != "2.0":
        errors.append(f"schema_version bắt buộc là '2.0', nhận được: '{version}'.")

    # 2. Project ID
    project_id = storyboard.get("project_id")
    if not project_id or not isinstance(project_id, str):
        errors.append("project_id là bắt buộc và phải là chuỗi không rỗng.")
    elif not re.match(r"^[a-zA-Z0-9_-]+$", project_id):
        errors.append(f"project_id chứa ký tự không hợp lệ: '{project_id}' (chỉ cho phép a-z, A-Z, 0-9, _, -).")

    # 3. FPS
    fps = storyboard.get("fps")
    if fps not in [24, 30, 60]:
        errors.append(f"fps phải thuộc [24, 30, 60], nhận được: {fps}.")

    # 4. Resolution
    res = storyboard.get("resolution")
    if not isinstance(res, dict):
        errors.append("resolution là bắt buộc và phải là đối tượng {'width': int, 'height': int}.")
    else:
        w = res.get("width")
        h = res.get("height")
        if not isinstance(w, int) or w < 360 or w > 3840:
            errors.append(f"resolution.width phải là số nguyên từ 360 đến 3840, nhận được: {w}.")
        if not isinstance(h, int) or h < 360 or h > 3840:
            errors.append(f"resolution.height phải là số nguyên từ 360 đến 3840, nhận được: {h}.")

    # 5. Aspect Ratio
    aspect = storyboard.get("aspect_ratio")
    if aspect is not None:
        if aspect not in ASPECT_RATIOS:
            errors.append(f"aspect_ratio '{aspect}' không được hỗ trợ (chỉ chấp nhận: {list(ASPECT_RATIOS.keys())}).")
        elif isinstance(res, dict) and isinstance(res.get("width"), int) and isinstance(res.get("height"), int):
            expected_w, expected_h = ASPECT_RATIOS[aspect]
            # Kiểm tra tỷ lệ có xấp xỉ tỷ lệ mong đợi không
            actual_ratio = res["width"] / res["height"]
            expected_ratio = expected_w / expected_h
            if abs(actual_ratio - expected_ratio) > 0.05:
                errors.append(
                    f"Kích thước resolution ({res['width']}x{res['height']}) không khớp với aspect_ratio '{aspect}' "
                    f"(tỷ lệ thực tế: {actual_ratio:.3f} vs mong đợi: {expected_ratio:.3f})."
                )

    # 6. Target duration (nếu có)
    target_dur = storyboard.get("target_duration_seconds")
    if target_dur is not None:
        if not isinstance(target_dur, (int, float)) or target_dur <= 0:
            errors.append(f"target_duration_seconds phải là số dương, nhận được: {target_dur}.")

    # 7. Scenes
    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list) or len(scenes) == 0:
        errors.append("storyboard bắt buộc phải có ít nhất 1 phân cảnh trong mảng 'scenes'.")
        return False, errors

    seen_scene_ids = set()
    total_planned = 0.0

    for idx, sc in enumerate(scenes):
        sc_prefix = f"Scene #{idx + 1}"
        if not isinstance(sc, dict):
            errors.append(f"{sc_prefix}: Phân cảnh phải là một đối tượng dict.")
            continue

        # ID
        sc_id = sc.get("id")
        if not sc_id or not isinstance(sc_id, str):
            errors.append(f"{sc_prefix}: Thiếu thuộc tính 'id' hoặc không phải chuỗi.")
        else:
            if sc_id in seen_scene_ids:
                errors.append(f"{sc_prefix}: Trùng lặp scene id '{sc_id}'. Mọi scene ID phải là duy nhất.")
            seen_scene_ids.add(sc_id)

        # Type
        sc_type = sc.get("type")
        if sc_type not in SCENE_TYPES:
            errors.append(f"{sc_prefix} ('{sc_id}'): Loại scene '{sc_type}' không hợp lệ (hỗ trợ: {SCENE_TYPES}).")

        # Duration
        dur = sc.get("duration_seconds")
        if not isinstance(dur, (int, float)) or dur < 0.5:
            errors.append(f"{sc_prefix} ('{sc_id}'): duration_seconds phải là số >= 0.5 giây, nhận được: {dur}.")
        else:
            total_planned += dur

        # Visual goal
        vg = sc.get("visual_goal")
        if not vg or not isinstance(vg, str):
            errors.append(f"{sc_prefix} ('{sc_id}'): 'visual_goal' là bắt buộc để định hướng hình ảnh.")

        # Composition (nếu có)
        comp = sc.get("composition")
        if comp is not None and isinstance(comp, dict):
            layout = comp.get("layout")
            if layout is not None and layout not in COMPOSITION_LAYOUTS:
                errors.append(f"{sc_prefix} ('{sc_id}'): layout '{layout}' không hợp lệ (hỗ trợ: {COMPOSITION_LAYOUTS}).")

        # Motion (nếu có)
        motion = sc.get("motion")
        if motion is not None and isinstance(motion, dict):
            intensity = motion.get("intensity")
            if intensity is not None and intensity not in MOTION_INTENSITIES:
                errors.append(f"{sc_prefix} ('{sc_id}'): intensity '{intensity}' không hợp lệ (hỗ trợ: {MOTION_INTENSITIES}).")
            easing = motion.get("easing")
            if easing is not None and easing not in EASING_FUNCTIONS:
                errors.append(f"{sc_prefix} ('{sc_id}'): easing '{easing}' không hợp lệ (hỗ trợ: {EASING_FUNCTIONS}).")

        # Transition (nếu có)
        trans = sc.get("transition")
        if trans is not None and isinstance(trans, dict):
            t_type = trans.get("type")
            if t_type is not None and t_type not in TRANSITION_TYPES:
                errors.append(f"{sc_prefix} ('{sc_id}'): transition type '{t_type}' không hợp lệ (hỗ trợ: {TRANSITION_TYPES}).")
            t_dur = trans.get("duration_seconds", 0.0)
            if not isinstance(t_dur, (int, float)) or t_dur < 0:
                errors.append(f"{sc_prefix} ('{sc_id}'): transition duration_seconds phải >= 0.")
            elif isinstance(dur, (int, float)) and t_dur > dur:
                errors.append(
                    f"{sc_prefix} ('{sc_id}'): Thời lượng chuyển cảnh ({t_dur}s) vượt quá thời lượng của phân cảnh ({dur}s)."
                )

        # Assets
        assets = sc.get("assets")
        if assets is not None and isinstance(assets, list):
            for a_idx, asset in enumerate(assets):
                if not isinstance(asset, dict):
                    errors.append(f"{sc_prefix} Asset #{a_idx}: Phải là một object.")
                    continue
                a_path = asset.get("path")
                if not a_path:
                    errors.append(f"{sc_prefix} Asset #{a_idx}: Thiếu thuộc tính 'path'.")
                elif check_asset_paths:
                    # Kiểm tra tồn tại file nếu là file cục bộ (không phải URL http/https)
                    if not a_path.startswith(("http://", "https://")):
                        resolved_path = Path(a_path)
                        if not resolved_path.is_absolute() and base_dir:
                            resolved_path = Path(base_dir) / resolved_path
                        if not resolved_path.exists():
                            errors.append(f"{sc_prefix} Asset '{asset.get('id', a_idx)}': Không tìm thấy file tại '{resolved_path}'.")

    return (len(errors) == 0, errors)
