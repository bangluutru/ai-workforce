#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brand_profile.py — Quản lý hồ sơ chuyển động & nhận diện thương hiệu (Brand Motion Profile).
Hỗ trợ bảng màu, font chữ, easing, cường độ chuyển động và vùng an toàn (Safe Area) (Luật R7).
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Danh mục Brand Profiles tích hợp chuẩn mực
BUILTIN_BRAND_PROFILES: Dict[str, Dict[str, Any]] = {
    "default": {
        "brand_id": "default",
        "version": 1,
        "name": "AIWF Standard Motion",
        "colors": {
            "primary": "#14213D",
            "secondary": "#2EC4B6",
            "accent": "#FCA311",
            "background": "#FFFFFF",
            "surface": "#F8F9FA",
            "text": "#1A1A1A"
        },
        "typography": {
            "title_font": "Be Vietnam Pro",
            "body_font": "Be Vietnam Pro",
            "mono_font": "Roboto"
        },
        "motion": {
            "intensity": "moderate",
            "default_easing": "ease-out",
            "transition_style": "smooth",
            "stagger_delay_seconds": 0.08
        },
        "safe_area": {
            "horizontal_percent": 8,
            "vertical_percent": 8
        }
    },
    "chottoday": {
        "brand_id": "chottoday",
        "version": 1,
        "name": "ChottoDay Newsroom Brand",
        "colors": {
            "primary": "#0A2540",
            "secondary": "#FF6B35",
            "accent": "#00A896",
            "background": "#FAFAFA",
            "surface": "#FFFFFF",
            "text": "#1E293B"
        },
        "typography": {
            "title_font": "Be Vietnam Pro",
            "body_font": "Be Vietnam Pro",
            "cjk_font": "Noto Sans JP",
            "mono_font": "Roboto"
        },
        "motion": {
            "intensity": "moderate",
            "default_easing": "ease-out",
            "transition_style": "smooth",
            "stagger_delay_seconds": 0.06
        },
        "safe_area": {
            "horizontal_percent": 10,
            "vertical_percent": 12
        }
    },
    "balancera": {
        "brand_id": "balancera",
        "version": 1,
        "name": "Balancera Japan Wellness Brand",
        "colors": {
            "primary": "#006964",
            "secondary": "#51BF9D",
            "accent": "#D4AF37",
            "background": "#FDFBF7",
            "surface": "#FFFFFF",
            "text": "#2C3E50"
        },
        "typography": {
            "title_font": "Be Vietnam Pro",
            "body_font": "Spectral",
            "cjk_font": "Noto Sans JP",
            "mono_font": "Roboto"
        },
        "motion": {
            "intensity": "subtle",
            "default_easing": "ease-in-out",
            "transition_style": "smooth",
            "stagger_delay_seconds": 0.10
        },
        "safe_area": {
            "horizontal_percent": 8,
            "vertical_percent": 8
        }
    }
}


def validate_brand_profile(profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Kiểm tra tính hợp lệ của Brand Motion Profile."""
    errors: List[str] = []

    if not isinstance(profile, dict):
        return False, ["Hồ sơ thương hiệu phải là dict."]

    if not profile.get("brand_id"):
        errors.append("brand_id là bắt buộc.")

    colors = profile.get("colors")
    if not isinstance(colors, dict):
        errors.append("Mục 'colors' là bắt buộc.")
    else:
        hex_pattern = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
        for col_key, col_val in colors.items():
            if not isinstance(col_val, str) or not hex_pattern.match(col_val):
                errors.append(f"Màu colors.{col_key} ('{col_val}') không phải là mã hex hợp lệ (#RRGGBB hoặc #RGB).")

    typo = profile.get("typography")
    if not isinstance(typo, dict):
        errors.append("Mục 'typography' là bắt buộc.")
    else:
        if not typo.get("title_font"):
            errors.append("typography.title_font là bắt buộc.")

    safe_area = profile.get("safe_area")
    if isinstance(safe_area, dict):
        hp = safe_area.get("horizontal_percent", 0)
        vp = safe_area.get("vertical_percent", 0)
        if not isinstance(hp, (int, float)) or hp < 0 or hp > 25:
            errors.append(f"safe_area.horizontal_percent phải nằm trong khoảng 0-25%, nhận được: {hp}.")
        if not isinstance(vp, (int, float)) or vp < 0 or vp > 25:
            errors.append(f"safe_area.vertical_percent phải nằm trong khoảng 0-25%, nhận được: {vp}.")

    return (len(errors) == 0, errors)


def load_brand_profile(
    profile_name_or_dict: str | Dict[str, Any],
    custom_dir: Optional[Path | str] = None
) -> Dict[str, Any]:
    """
    Nạp hồ sơ thương hiệu từ tên cấu hình có sẵn hoặc file tùy biến.
    Nếu không tìm thấy, tự động fallback an toàn về 'default' (Neutral Provisional).
    """
    if isinstance(profile_name_or_dict, dict):
        is_valid, errors = validate_brand_profile(profile_name_or_dict)
        if is_valid:
            return profile_name_or_dict
        # Merge với default nếu thiếu trường
        merged = dict(BUILTIN_BRAND_PROFILES["default"])
        merged.update(profile_name_or_dict)
        return merged

    name = str(profile_name_or_dict).strip().lower()

    # 1. Tra trong cấu hình built-in
    if name in BUILTIN_BRAND_PROFILES:
        return BUILTIN_BRAND_PROFILES[name]

    # 2. Tra trong custom directory nếu có
    if custom_dir:
        c_path = Path(custom_dir) / f"{name}.json"
        if c_path.exists():
            try:
                data = json.loads(c_path.read_text(encoding="utf-8"))
                is_valid, errors = validate_brand_profile(data)
                if is_valid:
                    return data
            except Exception:
                pass

    # 3. Fallback an toàn về default và gắn cờ provisional
    fallback = dict(BUILTIN_BRAND_PROFILES["default"])
    fallback["brand_id"] = name
    fallback["is_provisional"] = True
    return fallback


def get_safe_area_box(width: int, height: int, profile: Dict[str, Any]) -> Dict[str, int]:
    """
    Tính toán toạ độ hộp vùng an toàn (Safe Area Bounding Box) cho render và QA.
    Trả về: {"x": int, "y": int, "width": int, "height": int, "margin_x": int, "margin_y": int}
    """
    safe = profile.get("safe_area", {})
    hp = safe.get("horizontal_percent", 8)
    vp = safe.get("vertical_percent", 8)

    margin_x = int(round(width * (hp / 100.0)))
    margin_y = int(round(height * (vp / 100.0)))

    safe_w = width - (2 * margin_x)
    safe_h = height - (2 * margin_y)

    return {
        "x": margin_x,
        "y": margin_y,
        "width": max(1, safe_w),
        "height": max(1, safe_h),
        "margin_x": margin_x,
        "margin_y": margin_y
    }
