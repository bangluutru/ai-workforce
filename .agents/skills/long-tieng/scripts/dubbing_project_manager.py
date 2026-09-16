#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dubbing_project_manager.py — Quản lý trạng thái và cấu hình dự án Lồng Tiếng (long-tieng).
Lưu trữ thông tin video, các phân đoạn câu thoại, cấu hình âm thanh và kiểu dáng phụ đề (style).
Hoàn toàn độc lập, không phụ thuộc API ngoài.
"""

import os
import sys
import json
import re
import subprocess
import shutil

DEFAULT_AUDIO_SETTINGS = {
    "lang": "vi",
    "gender": "female",
    "voice": "vi-VN-HoaiMyNeural",
    "speed": 1.0,
    "bg_volume": 1.0,
    "voice_volume": 1.4,
    "ducking_ratio": 0.20,
    "include_subtitles": True
}

DEFAULT_STYLE = {
    "preset": "modern_bottom",
    "mode": "monolingual",  # monolingual | bilingual | source_only
    "bilingual_order": "target_top",
    "font_family": "Be Vietnam Pro",
    "font_size": 24,
    "primary_color": "#ffffff",
    "secondary_color": "#ffd700",
    "outline_color": "#000000",
    "outline_width": 2.2,
    "background_color": "#000000",
    "background_opacity": 35,
    "alignment": 2,
    "margin_v": 45,
    "margin_l": 40,
    "margin_r": 40,
    "line_spacing": 6,
    "border_radius": 8
}

def get_video_metadata(video_path):
    """Trích xuất siêu dữ liệu video bằng ffprobe."""
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", video_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    meta = json.loads(res.stdout)

    fmt = meta.get("format", {})
    duration = float(fmt.get("duration", 0))

    video_stream = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), {})
    width = int(video_stream.get("width", 1920))
    height = int(video_stream.get("height", 1080))
    has_audio = any(s.get("codec_type") == "audio" for s in meta.get("streams", []))

    # Tính FPS
    fps = 30.0
    r_fps = video_stream.get("r_frame_rate", "30/1")
    if "/" in r_fps:
        num, den = r_fps.split("/")
        fps = round(float(num) / float(den), 2) if float(den) > 0 else 30.0

    return {
        "source_path": os.path.abspath(video_path),
        "filename": os.path.basename(video_path),
        "duration": round(duration, 3),
        "width": width,
        "height": height,
        "fps": fps,
        "has_audio": has_audio
    }

def parse_subtitles(subtitle_path):
    """Nạp danh sách phân đoạn câu thoại từ file JSON hoặc file SRT."""
    if not os.path.isfile(subtitle_path):
        raise FileNotFoundError(f"Không tìm thấy file phụ đề: {subtitle_path}")

    ext = os.path.splitext(subtitle_path)[1].lower()
    if ext == ".json":
        with open(subtitle_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "segments" in data:
                return data["segments"]
            elif "subtitles" in data:
                return data["subtitles"]
        elif isinstance(data, list):
            return data
    elif ext in [".srt", ".vtt"]:
        segments = []
        with open(subtitle_path, "r", encoding="utf-8") as f:
            content = f.read()
        blocks = re.split(r"\n\s*\n", content.strip())
        for block in blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            if len(lines) >= 2:
                time_line = lines[1] if lines[0].isdigit() else lines[0]
                text_lines = lines[2:] if lines[0].isdigit() else lines[1:]
                time_match = re.search(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", time_line)
                if time_match:
                    h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, time_match.groups())
                    start_sec = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
                    end_sec = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
                    text = " ".join(text_lines)
                    segments.append({
                        "id": len(segments) + 1,
                        "start": round(start_sec, 3),
                        "end": round(end_sec, 3),
                        "source_text": text,
                        "target_text": text,
                        "text": text
                    })
        return segments

    raise ValueError(f"Định dạng phụ đề không hỗ trợ: {ext}")

def create_dubbing_project(video_path, subtitles_path, process_dir=None, audio_settings=None, style=None):
    """Khởi tạo file dubbing_project.json đầy đủ."""
    v_meta = get_video_metadata(video_path)
    segments = parse_subtitles(subtitles_path)

    # Chuẩn hóa các segment
    normalized_segments = []
    for idx, s in enumerate(segments, 1):
        target_text = s.get("target_text") or s.get("text") or s.get("source_text") or ""
        source_text = s.get("source_text") or s.get("text") or target_text
        normalized_segments.append({
            "id": idx,
            "start": round(float(s.get("start", 0)), 3),
            "end": round(float(s.get("end", 0)), 3),
            "source_text": source_text.strip(),
            "target_text": target_text.strip(),
            "text": target_text.strip()
        })

    settings = dict(DEFAULT_AUDIO_SETTINGS)
    if audio_settings and isinstance(audio_settings, dict):
        settings.update(audio_settings)

    style_cfg = dict(DEFAULT_STYLE)
    if style and isinstance(style, dict):
        style_cfg.update(style)

    project_id = os.path.splitext(os.path.basename(video_path))[0]
    if not process_dir:
        process_dir = os.path.abspath(f"_process/dubbing_{project_id}")
    os.makedirs(process_dir, exist_ok=True)

    project_data = {
        "version": "1.0",
        "project_type": "long-tieng",
        "video": v_meta,
        "audio_settings": settings,
        "style": style_cfg,
        "segments": normalized_segments,
        "process_dir": os.path.abspath(process_dir)
    }

    project_file = os.path.join(process_dir, "dubbing_project.json")
    save_dubbing_project(project_data, project_file)
    return project_file, project_data

def load_dubbing_project(project_path):
    """Nạp project từ file JSON."""
    if not os.path.isfile(project_path):
        raise FileNotFoundError(f"Project file not found: {project_path}")
    with open(project_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "style" not in data:
        data["style"] = dict(DEFAULT_STYLE)
    return data

def save_dubbing_project(project_data, project_path):
    """Lưu project ra file JSON."""
    os.makedirs(os.path.dirname(os.path.abspath(project_path)), exist_ok=True)
    with open(project_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2, ensure_ascii=False)
    return True

def split_segment(project_data, segment_id, split_time):
    """Chia một câu thành 2 câu tại mốc split_time."""
    segments = project_data.get("segments", [])
    new_segments = []
    found = False

    for s in segments:
        if s["id"] == segment_id and s["start"] < split_time < s["end"]:
            found = True
            seg1 = dict(s)
            seg1["end"] = round(split_time, 2)

            seg2 = dict(s)
            seg2["id"] = s["id"] + 1
            seg2["start"] = round(split_time, 2)
            seg2["source_text"] = "..."
            seg2["target_text"] = "..."
            seg2["text"] = "..."

            new_segments.append(seg1)
            new_segments.append(seg2)
        else:
            new_segments.append(dict(s))

    if found:
        # Đánh lại số ID
        for idx, s in enumerate(new_segments, 1):
            s["id"] = idx
        project_data["segments"] = new_segments

    return project_data
