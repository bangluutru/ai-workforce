#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm thử hệ thống Visual QA 2.0 (Frame Sampler, Technical Validator, Visual Inspector, Contact Sheet, Report Builder).
"""

import json
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import pytest

SHARED_DIR = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

from creative.qa.frame_sampler import SampledFrame, sample_video_frames, extract_frame_at
from creative.qa.technical_validator import validate_video_technical, inspect_media_streams
from creative.qa.visual_inspector import (
    inspect_visual_frames,
    calculate_frame_difference,
    calculate_flat_color_ratio,
)
from creative.qa.contact_sheet import generate_contact_sheet
from creative.qa.report_builder import run_visual_qa, QAReport

SAMPLE_VIDEO = Path(__file__).resolve().parents[2] / "_process" / "hyperframes_sandbox" / "preset_samples" / "preset_01_sample.mp4"


def test_technical_validator_good_video():
    """Kiểm tra video mẫu đạt chuẩn kỹ thuật."""
    if not SAMPLE_VIDEO.is_file():
        pytest.skip("Chưa có file preset_01_sample.mp4 để kiểm tra thực tế")

    res = validate_video_technical(str(SAMPLE_VIDEO), expected_spec={
        "duration": 3.0,
        "width": 1080,
        "height": 1080,
        "fps": 30,
        "aspect_ratio": "1:1",
    })
    assert res.success is True
    assert res.verdict == "PASS"
    assert res.score >= 90
    assert res.metrics["width"] == 1080
    assert res.metrics["height"] == 1080
    assert res.metrics["duration"] == pytest.approx(3.0, abs=0.1)


def test_technical_validator_nonexistent_file():
    """Kiểm tra báo lỗi khi file video không tồn tại."""
    res = validate_video_technical("/nonexistent/video.mp4")
    assert res.success is False
    assert res.verdict == "FAIL"
    assert res.score == 0
    assert any(f.code == "file_not_found" for f in res.findings)


def test_technical_validator_mismatches():
    """Kiểm tra bắt đúng các lỗi sai lệch kịch bản (resolution, duration, fps)."""
    if not SAMPLE_VIDEO.is_file():
        pytest.skip("Chưa có file preset_01_sample.mp4")

    res = validate_video_technical(str(SAMPLE_VIDEO), expected_spec={
        "duration": 10.0,      # Lệch 7s
        "width": 1920,         # Lệch width
        "height": 1080,
        "fps": 60,             # Lệch fps
        "aspect_ratio": "16:9", # Lệch aspect
        "require_audio": True,  # Thiếu audio
    })
    assert res.success is False
    assert res.verdict == "FAIL"
    codes = [f.code for f in res.findings]
    assert "duration_mismatch" in codes
    assert "resolution_mismatch" in codes
    assert "fps_mismatch" in codes
    assert "aspect_mismatch" in codes
    assert "missing_required_audio" in codes


def test_frame_sampler_extraction():
    """Kiểm tra trích xuất khung hình từ video qua FFmpeg."""
    if not SAMPLE_VIDEO.is_file():
        pytest.skip("Chưa có file preset_01_sample.mp4")

    frames = sample_video_frames(str(SAMPLE_VIDEO), count=4, target_width=360)
    assert len(frames) == 4
    for f in frames:
        assert isinstance(f, SampledFrame)
        assert f.width == 360
        assert f.height == 360  # 1:1 ratio
        assert f.rgb_array.shape == (360, 360, 3)
        assert f.luminance_mean > 0.0


def test_visual_inspector_detects_black_frames():
    """Kiểm thử thuật toán phát hiện màn hình đen (black frames)."""
    black_arr = np.zeros((120, 120, 3), dtype=np.uint8)
    frames = [
        SampledFrame(index=i, timestamp=float(i), width=120, height=120, rgb_array=black_arr)
        for i in range(5)
    ]
    res = inspect_visual_frames(frames)
    assert res.success is False
    assert res.verdict == "FAIL"
    assert any(f.code == "excessive_black_frames" for f in res.findings)


def test_visual_inspector_detects_frozen_video():
    """Kiểm thử thuật toán phát hiện video bị đứng hình hoàn toàn."""
    # Tạo hình ảnh tĩnh có chi tiết (không đen)
    static_arr = np.zeros((120, 120, 3), dtype=np.uint8)
    static_arr[30:90, 30:90, :] = 200  # Khối vuông sáng

    frames = [
        SampledFrame(index=i, timestamp=float(i) * 1.0, width=120, height=120, rgb_array=static_arr.copy())
        for i in range(5)
    ]
    res = inspect_visual_frames(frames)
    assert res.success is False
    assert res.verdict == "FAIL"
    assert any(f.code == "completely_frozen_video" for f in res.findings)


def test_visual_inspector_passes_dynamic_motion():
    """Kiểm thử video có chuyển động động học đạt chuẩn PASS."""
    frames = []
    for i in range(5):
        arr = np.zeros((120, 120, 3), dtype=np.uint8)
        # Khối di chuyển theo từng frame
        start_x = i * 20
        arr[30:70, start_x:start_x + 30, 0] = 220
        arr[30:70, start_x:start_x + 30, 1] = 120
        frames.append(SampledFrame(index=i, timestamp=float(i) * 0.5, width=120, height=120, rgb_array=arr))

    res = inspect_visual_frames(frames)
    assert res.success is True
    assert res.verdict == "PASS"
    assert res.score >= 90


def test_contact_sheet_generation(tmp_path):
    """Kiểm tra xuất bản ảnh Contact Sheet dạng lưới."""
    frames = []
    for i in range(6):
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[:, :, i % 3] = (i + 1) * 35
        frames.append(SampledFrame(index=i, timestamp=i * 0.5, width=100, height=100, rgb_array=arr))

    out_sheet = str(tmp_path / "contact_sheet.jpg")
    res_path = generate_contact_sheet(frames, out_sheet, columns=3, cell_width=150)

    assert Path(res_path).is_file()
    assert Path(res_path).stat().st_size > 1000

    img = Image.open(res_path)
    assert img.format == "JPEG"
    assert img.width > 400
    assert img.height > 200


def test_report_builder_full_pipeline(tmp_path):
    """Kiểm tra chạy toàn diện pipeline run_visual_qa và xuất báo cáo JSON/Markdown."""
    if not SAMPLE_VIDEO.is_file():
        pytest.skip("Chưa có file preset_01_sample.mp4")

    qa_out_dir = str(tmp_path / "qa_report_out")
    report = run_visual_qa(
        video_path=str(SAMPLE_VIDEO),
        expected_spec={"duration": 3.0, "width": 1080, "height": 1080, "aspect_ratio": "1:1"},
        generate_sheet=True,
        sample_count=6,
        output_dir=qa_out_dir,
    )

    assert isinstance(report, QAReport)
    assert report.overall_verdict in ("PASS", "WARN")
    assert report.overall_score >= 85
    assert report.contact_sheet_path is not None
    assert Path(report.contact_sheet_path).is_file()

    # Kiểm tra JSON report
    json_path = tmp_path / "qa_report_out" / "preset_01_sample_technical_report.json"
    assert json_path.is_file()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["overall_verdict"] == report.overall_verdict

    # Kiểm tra Markdown report
    md = report.to_markdown()
    assert "# " in md
    assert "VISUAL QA 2.0" in md
    assert "Độ phân giải" in md
