#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for StoryboardRenderer (Phase 6).
Kiểm thử bộ điều phối kết xuất đa cảnh StoryboardRenderer.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SHARED = ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED))
import bootstrap  # noqa: F401,E402

from creative.storyboard_renderer import StoryboardRenderer, render_storyboard


def test_infer_preset_for_scene():
    renderer = StoryboardRenderer()
    assert renderer._infer_preset_for_scene({"type": "title_card"}) == "04_kinetic_title"
    assert renderer._infer_preset_for_scene({"type": "infographic"}) == "09_bar_chart"
    assert renderer._infer_preset_for_scene({"type": "product_highlight"}) == "07_product_spotlight"
    assert renderer._infer_preset_for_scene({"type": "ui_showcase"}) == "08_feature_card"
    assert renderer._infer_preset_for_scene({"type": "outro"}) == "10_cta_reveal"
    assert renderer._infer_preset_for_scene({"type": "motion_graphic"}) == "01_fade_in"


def test_invalid_storyboard_fails_gracefully():
    renderer = StoryboardRenderer()
    # Missing required fields
    res = renderer.render_storyboard({"invalid": True})
    assert res.success is False
    assert "Storyboard không hợp lệ" in res.error_message


def test_nonexistent_file_fails():
    res = render_storyboard("/path/that/does/not/exist/storyboard.json")
    assert res.success is False
    assert "không tồn tại" in res.error_message


def test_render_multi_scene_storyboard_mock():
    """Kiểm thử render một storyboard 2 cảnh qua Canvas fallback."""
    test_sb = {
        "schema_version": "2.0",
        "project_id": "test_pilot",
        "fps": 30,
        "resolution": {"width": 720, "height": 720},
        "brand_profile": "default",
        "scenes": [
            {
                "id": "s01",
                "type": "motion_graphics",
                "duration_seconds": 1.0,
                "visual_goal": "Tiêu đề mở đầu",
                "motion": {
                    "preset": "04_kinetic_title"
                },
                "props": {
                    "title": "Scene 1",
                    "subtitle": "Subtitle 1"
                }
            },
            {
                "id": "s02",
                "type": "motion_graphics",
                "duration_seconds": 1.0,
                "visual_goal": "Kêu gọi hành động",
                "motion": {
                    "preset": "10_cta_reveal"
                },
                "props": {
                    "title": "Call To Action",
                    "cta_button": "Click Here"
                }
            }
        ]
    }

    temp_dir = Path(tempfile.mkdtemp(prefix="test_sb_render_"))
    try:
        out_mp4 = temp_dir / "output.mp4"
        renderer = StoryboardRenderer()
        result = renderer.render_storyboard(
            storyboard=test_sb,
            output_path=str(out_mp4),
            work_dir=str(temp_dir / "work"),
            run_qa=True,
            force_adapter="canvas",
        )

        assert result.success is True
        assert Path(result.output_mp4).exists()
        assert Path(result.output_mp4).stat().st_size > 0
        assert len(result.scene_clips) == 2
        assert result.total_duration >= 1.9
        assert result.qa_report is not None
        assert result.qa_report.overall_score > 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
