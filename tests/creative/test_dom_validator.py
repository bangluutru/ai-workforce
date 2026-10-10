#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for DOM & Layout Visual QA Validator (Fix 3).
Kiểm tra phát hiện chính xác các class lỗi bố cục:
- TEXT_OVERFLOW
- ELEMENT_OUT_OF_BOUNDS
- SAFE_AREA_VIOLATION
- TEXT_COLLISION
- LOGO_OUT_OF_BOUNDS
"""

import pytest
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

from creative.qa.dom_validator import (
    CHECKED_ERROR_CLASSES,
    DOMValidationIssue,
    DOMValidationResult,
    validate_dom_layout,
)


def test_checked_error_classes_list():
    """Kiểm tra danh mục các class lỗi được định nghĩa rõ ràng."""
    assert "TEXT_OVERFLOW" in CHECKED_ERROR_CLASSES
    assert "ELEMENT_OUT_OF_BOUNDS" in CHECKED_ERROR_CLASSES
    assert "SAFE_AREA_VIOLATION" in CHECKED_ERROR_CLASSES
    assert "TEXT_COLLISION" in CHECKED_ERROR_CLASSES
    assert "LOGO_OUT_OF_BOUNDS" in CHECKED_ERROR_CLASSES
    assert len(CHECKED_ERROR_CLASSES) == 5


def test_dom_validation_clean_layout():
    """Kiểm tra bố cục hợp lệ không phát sinh lỗi nào."""
    mock_clean = [
        {
            "tag": "h1",
            "name": "h1.title",
            "is_text": True,
            "is_content": True,
            "scroll_width": 400,
            "client_width": 400,
            "scroll_height": 60,
            "client_height": 60,
            "bounds": {"left": 200, "top": 200, "right": 600, "bottom": 260, "width": 400, "height": 60},
        },
        {
            "tag": "p",
            "name": "p.subtitle",
            "is_text": True,
            "is_content": True,
            "scroll_width": 500,
            "client_width": 500,
            "scroll_height": 40,
            "client_height": 40,
            "bounds": {"left": 200, "top": 300, "right": 700, "bottom": 340, "width": 500, "height": 40},
        },
    ]

    res = validate_dom_layout("", width=1920, height=1080, mock_elements=mock_clean, scene_id="scene_01")
    assert res.valid is True
    assert len(res.issues) == 0
    d = res.to_dict()
    assert d["valid"] is True
    assert d["scene_id"] == "scene_01"


def test_text_overflow_detection():
    """Kiểm tra phát hiện lỗi văn bản tràn khung scrollWidth > clientWidth."""
    mock_overflow = [
        {
            "tag": "h1",
            "name": "h1.title",
            "is_text": True,
            "scroll_width": 650,  # Bị tràn
            "client_width": 400,
            "scroll_height": 50,
            "client_height": 50,
            "bounds": {"left": 200, "top": 200, "right": 600, "bottom": 250, "width": 400, "height": 50},
        }
    ]

    res = validate_dom_layout("", width=1920, height=1080, mock_elements=mock_overflow, scene_id="overflow_scene")
    assert res.valid is False
    codes = [i.code for i in res.issues]
    assert "TEXT_OVERFLOW" in codes
    overflow_issue = next(i for i in res.issues if i.code == "TEXT_OVERFLOW")
    assert overflow_issue.severity == "FAIL"
    assert "Văn bản bị tràn khung chứa" in overflow_issue.message


def test_element_out_of_bounds_detection():
    """Kiểm tra phát hiện phần tử vượt quá biên giới viewport (W x H)."""
    mock_oob = [
        {
            "tag": "div",
            "name": "div.banner",
            "is_content": True,
            "bounds": {"left": 1800, "top": 200, "right": 2100, "bottom": 300, "width": 300, "height": 100},
        }
    ]

    res = validate_dom_layout("", width=1920, height=1080, mock_elements=mock_oob, scene_id="oob_scene")
    assert res.valid is False
    codes = [i.code for i in res.issues]
    assert "ELEMENT_OUT_OF_BOUNDS" in codes
    oob_issue = next(i for i in res.issues if i.code == "ELEMENT_OUT_OF_BOUNDS")
    assert oob_issue.severity == "FAIL"
    assert oob_issue.bounds["right"] == 2100


def test_safe_area_violation_detection():
    """Kiểm tra phát hiện vi phạm vùng an toàn 8% (cảnh báo WARN)."""
    # Viewport 1000x1000, 8% safe area = [80, 80] đến [920, 920]
    mock_unsafe = [
        {
            "tag": "h2",
            "name": "h2.heading",
            "is_text": True,
            "is_content": True,
            "bounds": {"left": 40, "top": 100, "right": 400, "bottom": 150, "width": 360, "height": 50},
        }
    ]

    res = validate_dom_layout("", width=1000, height=1000, safe_margin_ratio=0.08, mock_elements=mock_unsafe, scene_id="safe_scene")
    # SAFE_AREA_VIOLATION có mức độ WARN, nên valid vẫn là True (không phải lỗi chết người)
    assert res.valid is True
    codes = [i.code for i in res.issues]
    assert "SAFE_AREA_VIOLATION" in codes
    safe_issue = next(i for i in res.issues if i.code == "SAFE_AREA_VIOLATION")
    assert safe_issue.severity == "WARN"


def test_text_collision_detection():
    """Kiểm tra phát hiện 2 khối văn bản đè lấn tọa độ lên nhau."""
    mock_collision = [
        {
            "tag": "h1",
            "name": "h1.title",
            "is_text": True,
            "bounds": {"left": 200, "top": 200, "right": 500, "bottom": 300, "width": 300, "height": 100},
        },
        {
            "tag": "p",
            "name": "p.desc",
            "is_text": True,
            "bounds": {"left": 250, "top": 240, "right": 550, "bottom": 340, "width": 300, "height": 100},
        },
    ]

    res = validate_dom_layout("", width=1920, height=1080, mock_elements=mock_collision, scene_id="collision_scene")
    assert res.valid is False
    codes = [i.code for i in res.issues]
    assert "TEXT_COLLISION" in codes
    col_issue = next(i for i in res.issues if i.code == "TEXT_COLLISION")
    assert col_issue.severity == "FAIL"
    assert "đè lấn tọa độ" in col_issue.message


def test_logo_out_of_bounds_detection():
    """Kiểm tra phát hiện logo thương hiệu vượt khỏi khung nhìn."""
    mock_logo = [
        {
            "tag": "img",
            "name": "img.logo",
            "is_logo": True,
            "bounds": {"left": -30, "top": 50, "right": 120, "bottom": 100, "width": 150, "height": 50},
        }
    ]

    res = validate_dom_layout("", width=1920, height=1080, mock_elements=mock_logo, scene_id="logo_scene")
    assert res.valid is False
    codes = [i.code for i in res.issues]
    assert "LOGO_OUT_OF_BOUNDS" in codes
    logo_issue = next(i for i in res.issues if i.code == "LOGO_OUT_OF_BOUNDS")
    assert logo_issue.severity == "FAIL"


def test_machine_readable_output_structure():
    """Kiểm tra cấu trúc đầu ra máy đọc được đúng đặc tả Fix 3."""
    mock = [
        {
            "tag": "h1",
            "name": "h1.header",
            "is_text": True,
            "scroll_width": 800,
            "client_width": 500,
            "bounds": {"left": 200, "top": 200, "right": 700, "bottom": 260, "width": 500, "height": 60},
        }
    ]
    res = validate_dom_layout("", width=1920, height=1080, mock_elements=mock, scene_id="test_scene")
    d = res.to_dict()
    assert "valid" in d
    assert "scene_id" in d
    assert "checked_classes" in d
    assert "issues" in d
    assert "execution_time_ms" in d
    assert len(d["issues"]) == 1
    issue_dict = d["issues"][0]
    assert issue_dict["code"] == "TEXT_OVERFLOW"
    assert issue_dict["severity"] == "FAIL"
    assert issue_dict["element"] == "h1.header"
    assert issue_dict["scene"] == "test_scene"
    assert "bounds" in issue_dict
    assert "message" in issue_dict
