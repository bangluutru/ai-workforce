#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_audiobook_engines.py — Kiểm thử tự động cho spoken_normalizer và audiobook_packager (Luật R7).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Thiết lập đường dẫn import _shared
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
SHARED_DIR = REPO_ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

from audiobook_packager import check_ffmpeg_installed, create_silence_wav, package_m4b_audiobook
from ffmpeg_tools import ffmpeg_bin, ffprobe_bin
from spoken_normalizer import (
    load_user_dictionary,
    normalize_spoken_vietnamese,
)


def test_spoken_normalizer_core_rules():
    # 1. Số La Mã trong tiêu đề
    text_roman = "Chương IV. Khởi đầu mới\nBài viết này không đổi\nPhần II: Kết nối"
    res_roman = normalize_spoken_vietnamese(text_roman)
    assert "Chương bốn" in res_roman
    assert "Phần hai" in res_roman
    assert "Bài viết này không đổi" in res_roman

    # 2. Khử dấu ngoặc kép (tránh đọc chữ 'dấu ngoặc kép')
    text_quote = 'Ông nói: “Phải hành động ngay” và "Không chần chừ".'
    res_quote = normalize_spoken_vietnamese(text_quote)
    assert "“" not in res_quote
    assert "”" not in res_quote
    assert '"' not in res_quote
    assert "Phải hành động ngay" in res_quote

    # 3. Từ viết tắt hành chính & thuật ngữ
    text_abbr = "Làm việc tại TP.HCM và báo cáo UBND. Áp dụng KPI, OKR và công nghệ AI."
    res_abbr = normalize_spoken_vietnamese(text_abbr)
    assert "Thành phố Hồ Chí Minh" in res_abbr
    assert "Ủy ban nhân dân" in res_abbr
    assert "ca pê i" in res_abbr
    assert "ô ca rờ" in res_abbr
    assert "a i" in res_abbr

    # 4. Ký hiệu số học, phần trăm, phân số
    text_nums = "Tăng trưởng 50%, đạt 1/3 chỉ tiêu trong khoảng 2-3 tháng."
    res_nums = normalize_spoken_vietnamese(text_nums)
    assert "50 phần trăm" in res_nums
    assert "một phần ba" in res_nums
    assert "2 đến 3" in res_nums

    # 5. Danh sách số thứ tự
    text_list = "1. Ý thứ nhất\n2. Ý thứ hai\n3. Ý thứ ba"
    res_list = normalize_spoken_vietnamese(text_list)
    assert "Thứ nhất, Ý thứ nhất" in res_list
    assert "Thứ hai, Ý thứ hai" in res_list
    assert "Thứ ba, Ý thứ ba" in res_list


def test_spoken_normalizer_custom_dict():
    sample_dict = {"Antigravity": "An ti gờ ra vi ti", "Sano": "Xa nô"}
    text = "Sử dụng Antigravity và phần mềm Sano để làm sách."
    res = normalize_spoken_vietnamese(text, user_dict=sample_dict)
    assert "An ti gờ ra vi ti" in res
    assert "Xa nô" in res


def test_audiobook_packager_m4b_and_mp3(tmp_path):
    if not check_ffmpeg_installed():
        pytest.skip("FFmpeg chưa được cài đặt trên máy này (bỏ qua render M4B)")

    # 1. Tạo 2 file WAV giả lập (mỗi file 1.5 giây)
    wav1 = tmp_path / "chap1.wav"
    wav2 = tmp_path / "chap2.wav"
    create_silence_wav(wav1, 1.5, sample_rate=44100)
    create_silence_wav(wav2, 2.0, sample_rate=44100)

    # 2. Tạo một ảnh bìa giả lập (JPEG 200x200)
    cover = tmp_path / "cover.jpg"
    cmd_cover = [
        ffmpeg_bin(), "-y", "-v", "error",
        "-f", "lavfi", "-i", "color=c=navy:s=200x200:d=1",
        "-frames:v", "1",
        str(cover)
    ]
    subprocess.run(cmd_cover, check=True)

    chapters = [
        {"title": "Chương 1: Khởi đầu", "audio_path": str(wav1)},
        {"title": "Chương 2: Tăng tốc", "audio_path": str(wav2)},
    ]

    out_m4b = tmp_path / "TestBook.m4b"
    mp3_dir = tmp_path / "mp3s"

    report = package_m4b_audiobook(
        chapters=chapters,
        output_m4b=out_m4b,
        book_title="Cuốn Sách Thử Nghiệm",
        author="Tác Giả AIWF",
        cover_path=cover,
        bitrate="64k",
        chapter_gap_sec=1.0,
        narrator="Thái Sơn",
        mp3_dir=mp3_dir
    )

    # 3. Kiểm chứng kết quả đầu ra
    assert out_m4b.exists()
    assert out_m4b.stat().st_size > 1000
    assert report["chapter_count"] == 2
    # Tổng thời lượng = 1.5 + 1.0 (gap) + 2.0 = 4.5s
    assert abs(report["total_duration_sec"] - 4.5) < 0.2

    # Kiểm tra MP3
    assert mp3_dir.exists()
    mp3_files = list(mp3_dir.glob("*.mp3"))
    assert len(mp3_files) == 2

    # Kiểm tra ffprobe đọc metadata chapters từ M4B
    probe_cmd = [
        ffprobe_bin(), "-v", "error",
        "-show_chapters",
        "-of", "json",
        str(out_m4b)
    ]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    probe_data = json.loads(probe_res.stdout)
    assert len(probe_data.get("chapters", [])) == 2
    assert probe_data["chapters"][0]["tags"]["title"] == "Chương 1: Khởi đầu"
    assert probe_data["chapters"][1]["tags"]["title"] == "Chương 2: Tăng tốc"

