#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_storyboard.py — Bộ kiểm thử hợp đồng Storyboard v2.0, Brand Motion Profile và Legacy Adapter (Phase 1).
"""

import copy
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SHARED = ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED))
import bootstrap  # noqa: F401,E402

from creative.storyboard_schema import (
    ASPECT_RATIOS,
    SCENE_TYPES,
    STORYBOARD_SCHEMA_V2,
)
from creative.storyboard_validator import (
    validate_storyboard,
    calculate_storyboard_durations,
    StoryboardValidationError,
)
from creative.brand_profile import (
    BUILTIN_BRAND_PROFILES,
    load_brand_profile,
    validate_brand_profile,
    get_safe_area_box,
)
from creative.legacy_adapter import (
    is_legacy_script,
    convert_legacy_script_to_storyboard,
    estimate_scene_duration,
)


@pytest.fixture
def sample_valid_storyboard():
    return {
        "schema_version": "2.0",
        "project_id": "chotto_intro_001",
        "title": "Giới thiệu ChottoDay Newsroom",
        "language": "vi",
        "fps": 30,
        "aspect_ratio": "1:1",
        "resolution": {
            "width": 1080,
            "height": 1080
        },
        "target_duration_seconds": 12.0,
        "brand_profile": "chottoday",
        "scenes": [
            {
                "id": "scene-001",
                "type": "motion_graphics",
                "duration_seconds": 4.0,
                "narration": "Chào mừng bạn đến với chuyên trang tin tức ChottoDay.",
                "visual_goal": "Tiêu đề xuất hiện kinetic typography phong cách năng động.",
                "composition": {
                    "layout": "centered",
                    "primary_subject": "title",
                    "background_type": "gradient"
                },
                "motion": {
                    "preset": "kinetic_title",
                    "intensity": "moderate",
                    "easing": "ease-out"
                },
                "transition": {
                    "type": "fade",
                    "duration_seconds": 0.5
                }
            },
            {
                "id": "scene-002",
                "type": "motion_graphics",
                "duration_seconds": 5.0,
                "narration": "Cập nhật chính sách mới nhất từ cơ quan chính phủ Nhật Bản.",
                "visual_goal": "Hiển thị 3 thẻ tính năng thông tin chính sách nổi bật.",
                "composition": {
                    "layout": "card_stack",
                    "primary_subject": "cards"
                },
                "motion": {
                    "preset": "feature_card",
                    "intensity": "moderate",
                    "easing": "ease-out"
                },
                "transition": {
                    "type": "slide_left",
                    "duration_seconds": 0.4
                }
            },
            {
                "id": "scene-003",
                "type": "motion_graphics",
                "duration_seconds": 3.0,
                "narration": "Theo dõi ngay hôm nay tại chottoday.com.",
                "visual_goal": "Kêu gọi hành động và hiển thị logo ChottoDay.",
                "composition": {
                    "layout": "centered",
                    "primary_subject": "cta"
                },
                "motion": {
                    "preset": "cta_reveal",
                    "intensity": "energetic",
                    "easing": "spring"
                },
                "transition": {
                    "type": "none",
                    "duration_seconds": 0.0
                }
            }
        ]
    }


# ============================================================
# 1. Tests Thẩm định Storyboard Schema v2.0
# ============================================================

def test_valid_storyboard_passes(sample_valid_storyboard):
    is_valid, errors = validate_storyboard(sample_valid_storyboard)
    assert is_valid is True, f"Báo lỗi không mong muốn: {errors}"
    assert len(errors) == 0


def test_invalid_schema_version(sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["schema_version"] = "1.0"
    is_valid, errors = validate_storyboard(sb)
    assert is_valid is False
    assert any("schema_version" in e for e in errors)


def test_invalid_project_id(sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["project_id"] = "invalid id with spaces & symbols!"
    is_valid, errors = validate_storyboard(sb)
    assert is_valid is False
    assert any("project_id" in e for e in errors)


def test_invalid_fps(sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["fps"] = 25  # Chỉ hỗ trợ 24, 30, 60
    is_valid, errors = validate_storyboard(sb)
    assert is_valid is False
    assert any("fps" in e for e in errors)


def test_invalid_resolution_out_of_bounds(sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["resolution"]["width"] = 100  # < 360
    is_valid, errors = validate_storyboard(sb)
    assert is_valid is False
    assert any("resolution.width" in e for e in errors)


def test_invalid_aspect_ratio(sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["aspect_ratio"] = "21:9"  # Không nằm trong danh mục hỗ trợ
    is_valid, errors = validate_storyboard(sb)
    assert is_valid is False
    assert any("aspect_ratio" in e for e in errors)


def test_resolution_mismatch_aspect_ratio(sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["aspect_ratio"] = "16:9"  # nhưng resolution là 1080x1080
    is_valid, errors = validate_storyboard(sb)
    assert is_valid is False
    assert any("không khớp với aspect_ratio" in e for e in errors)


def test_duplicate_scene_ids(sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["scenes"][1]["id"] = "scene-001"  # Trùng lặp với scene 0
    is_valid, errors = validate_storyboard(sb)
    assert is_valid is False
    assert any("Trùng lặp scene id" in e for e in errors)


def test_negative_or_too_short_scene_duration(sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["scenes"][0]["duration_seconds"] = 0.2  # < 0.5s
    is_valid, errors = validate_storyboard(sb)
    assert is_valid is False
    assert any("duration_seconds phải là số >= 0.5" in e for e in errors)


def test_transition_duration_exceeds_scene(sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["scenes"][0]["duration_seconds"] = 2.0
    sb["scenes"][0]["transition"]["duration_seconds"] = 2.5  # Lớn hơn thời lượng cảnh!
    is_valid, errors = validate_storyboard(sb)
    assert is_valid is False
    assert any("Thời lượng chuyển cảnh" in e for e in errors)


def test_missing_assets_detection(tmp_path, sample_valid_storyboard):
    sb = copy.deepcopy(sample_valid_storyboard)
    non_existent = tmp_path / "missing_logo.png"
    sb["scenes"][0]["assets"] = [
        {"id": "logo", "type": "image", "path": str(non_existent)}
    ]
    # Khi check_asset_paths=False: vẫn hợp lệ về cú pháp
    is_valid, _ = validate_storyboard(sb, check_asset_paths=False)
    assert is_valid is True

    # Khi check_asset_paths=True: bắt buộc phải có file thật
    is_valid_checked, errors = validate_storyboard(sb, check_asset_paths=True)
    assert is_valid_checked is False
    assert any("Không tìm thấy file" in e for e in errors)

    # Khi tạo file thật: đạt chuẩn
    non_existent.write_text("fake image content")
    is_valid_after_create, errors_after = validate_storyboard(sb, check_asset_paths=True)
    assert is_valid_after_create is True


# ============================================================
# 2. Tests Phân Định Thời Lượng (Duration Calculations)
# ============================================================

def test_calculate_storyboard_durations(sample_valid_storyboard):
    dur_info = calculate_storyboard_durations(sample_valid_storyboard)
    assert dur_info["target_duration_seconds"] == 12.0
    assert dur_info["planned_duration_seconds"] == 12.0  # 4.0 + 5.0 + 3.0
    assert dur_info["scene_count"] == 3
    assert dur_info["duration_difference"] == 0.0

    # Khi các cảnh có tổng thời lượng khác target
    sb = copy.deepcopy(sample_valid_storyboard)
    sb["target_duration_seconds"] = 15.0
    dur_info2 = calculate_storyboard_durations(sb)
    assert dur_info2["target_duration_seconds"] == 15.0
    assert dur_info2["planned_duration_seconds"] == 12.0
    assert dur_info2["duration_difference"] == -3.0


# ============================================================
# 3. Tests Brand Motion Profile
# ============================================================

def test_builtin_brand_profiles():
    for brand_key in ["default", "chottoday", "balancera"]:
        prof = load_brand_profile(brand_key)
        assert prof["brand_id"] == brand_key
        is_valid, errors = validate_brand_profile(prof)
        assert is_valid is True, f"Brand {brand_key} lỗi: {errors}"


def test_brand_profile_fallback_unknown():
    prof = load_brand_profile("brand_chua_ton_tai")
    assert prof["is_provisional"] is True
    assert prof["brand_id"] == "brand_chua_ton_tai"
    assert "colors" in prof
    assert prof["colors"]["primary"] == BUILTIN_BRAND_PROFILES["default"]["colors"]["primary"]


def test_brand_safe_area_box():
    prof = load_brand_profile("default")  # 8% ngang, 8% dọc
    box = get_safe_area_box(1080, 1080, prof)
    # 8% của 1080 là 86.4 -> round 86
    assert box["margin_x"] == 86
    assert box["margin_y"] == 86
    assert box["width"] == 1080 - (2 * 86)
    assert box["height"] == 1080 - (2 * 86)


# ============================================================
# 4. Tests Tương Thích Ngược (Legacy Script Adapter)
# ============================================================

def test_legacy_script_detection():
    v1_script = {
        "title_top": "Tiêu đề video",
        "mood": "traditional",
        "scenes": [
            {"id": "s01", "vi": "Câu dẫn tiếng Việt", "keywords": ["japan", "tokyo"]}
        ]
    }
    assert is_legacy_script(v1_script) is True

    raw_list = [
        {"id": "s01", "narration": "Lời dẫn"}
    ]
    assert is_legacy_script(raw_list) is True

    v2_storyboard = {
        "schema_version": "2.0",
        "project_id": "p01",
        "scenes": []
    }
    assert is_legacy_script(v2_storyboard) is False


def test_legacy_script_conversion_produces_valid_v2():
    legacy_script = {
        "title_top": "Chính Sách Visa Mới Tại Nhật Bản",
        "mood": "traditional",
        "scenes": [
            {
                "id": "s01",
                "vi": "Chính phủ Nhật Bản vừa công bố chính sách mới về visa kỹ năng đặc định.",
                "keywords": ["japan visa government", "tokyo immigration"]
            },
            {
                "id": "s02",
                "vi": "Người lao động có thêm nhiều quyền lợi và cơ hội bảo lãnh gia đình.",
                "keywords": ["happy family tokyo", "worker japan"]
            },
            {
                "id": "s03",
                "vi": "Hãy chuẩn bị hồ sơ đầy đủ để đón đầu cơ hội việc làm hấp dẫn.",
                "keywords": ["business contract document"]
            }
        ]
    }

    # Chuyển đổi sang Storyboard v2.0
    v2_result = convert_legacy_script_to_storyboard(
        legacy_script,
        aspect_ratio="9:16",
        project_id="migrated_visa_news",
        language="vi"
    )

    # 1. Kiểm tra cấu trúc v2
    assert v2_result["schema_version"] == "2.0"
    assert v2_result["project_id"] == "migrated_visa_news"
    assert v2_result["aspect_ratio"] == "9:16"
    assert v2_result["resolution"]["width"] == 1080
    assert v2_result["resolution"]["height"] == 1920
    assert len(v2_result["scenes"]) == 3
    assert v2_result["scenes"][0]["type"] == "stock_media"

    # 2. Thẩm định qua validator chính thức: PHẢI ĐẠT 100%
    is_valid, errors = validate_storyboard(v2_result)
    assert is_valid is True, f"Bản chuyển đổi không vượt qua validator v2: {errors}"
    assert len(errors) == 0


def test_estimate_scene_duration():
    # Câu ngắn
    short_dur = estimate_scene_duration("Chào mừng bạn.", default_dur=4.0)
    assert short_dur >= 4.0

    # Câu dài (28 từ -> 28 / 2.8 = 10s)
    long_text = " ".join(["từ"] * 28)
    long_dur = estimate_scene_duration(long_text, default_dur=4.0)
    assert abs(long_dur - 10.0) < 0.5
