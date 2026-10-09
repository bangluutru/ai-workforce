#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm thử kho 10 Motion Presets chuẩn mực và trình biên dịch HTML/GSAP.
"""

import json
import sys
from pathlib import Path
import pytest

SHARED_DIR = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

from creative.presets.registry import (
    PRESET_REGISTRY,
    get_preset_metadata,
    list_presets,
    render_preset_html,
)

PRESETS_DIR = SHARED_DIR / "creative" / "presets"


def test_preset_registry_count():
    """Kiểm tra kho phải có đầy đủ 10 presets chuẩn mực theo đặc tả kỹ thuật."""
    assert len(PRESET_REGISTRY) == 10
    expected_presets = [
        "01_fade_in",
        "02_slide_reveal",
        "03_scale_pop",
        "04_kinetic_title",
        "05_number_counter",
        "06_logo_reveal",
        "07_product_spotlight",
        "08_feature_card",
        "09_bar_chart",
        "10_cta_reveal",
    ]
    for p in expected_presets:
        assert p in PRESET_REGISTRY


def test_preset_template_files_exist():
    """Kiểm tra 100% file HTML template vật lý tồn tại và có dung lượng hợp lệ."""
    for key, meta in PRESET_REGISTRY.items():
        tpl_path = PRESETS_DIR / meta["template_file"]
        assert tpl_path.is_file(), f"File template {tpl_path} không tồn tại"
        assert tpl_path.stat().st_size > 200, f"File template {tpl_path} quá ngắn hoặc rỗng"


def test_get_preset_metadata():
    """Kiểm tra lấy metadata và xử lý lỗi khi sai tên."""
    meta = get_preset_metadata("01_fade_in")
    assert meta["name"] == "01_fade_in"
    assert meta["category"] == "typography"
    assert "16:9" in meta["supported_aspects"]

    # Có đuôi .html vẫn nhận dạng tốt
    meta_html = get_preset_metadata("01_fade_in.html")
    assert meta_html["name"] == "01_fade_in"

    with pytest.raises(KeyError, match="không tồn tại"):
        get_preset_metadata("unknown_preset")


def test_list_presets():
    """Kiểm tra hàm liệt kê toàn bộ presets."""
    items = list_presets()
    assert len(items) == 10
    names = [item["name"] for item in items]
    assert "05_number_counter" in names
    assert "10_cta_reveal" in names


@pytest.mark.parametrize("preset_key", list(PRESET_REGISTRY.keys()))
@pytest.mark.parametrize("aspect,width,height", [
    ("1:1", 1080, 1080),
    ("16:9", 1920, 1080),
    ("9:16", 1080, 1920),
])
def test_render_all_presets_across_all_aspect_ratios(preset_key, aspect, width, height):
    """
    Kiểm tra 10 presets kết xuất thành công HTML hợp lệ trên cả 3 tỷ lệ khung hình:
    1:1 (Square), 16:9 (Landscape), 9:16 (Portrait).
    """
    html = render_preset_html(
        preset_name=preset_key,
        props={"title": f"Test {preset_key} - {aspect}"},
        width=width,
        height=height,
        duration=4.5,
    )
    assert "<!DOCTYPE html>" in html
    assert "<script" in html
    assert "gsap" in html.lower()
    assert f"{width}/{height}" in html or f"{width}" in html
    assert "4.5" in html
    assert f"Test {preset_key} - {aspect}" in html


def test_brand_profile_color_injection():
    """Kiểm tra tích hợp Brand Motion Profile tự động ghi đè bảng màu vào preset."""
    brand = {
        "brand_id": "test_corp",
        "colors": {
            "primary": "#FF0077",
            "background": "#000000",
            "text": "#E2E8F0",
        }
    }
    html = render_preset_html(
        preset_name="01_fade_in",
        props={"title": "Brand Test"},
        brand_profile=brand,
    )
    assert "#FF0077" in html
    assert "#000000" in html
