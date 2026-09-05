#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_video.py — Render video hardsub MP4 bằng FFmpeg + libass.
Chuyển đổi project.json -> ASS tạm thời -> FFmpeg filter 'ass' -> final MP4.
Lưu file vào <output_dir> (mặc định ~/Downloads/).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

# Import local ass_generator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ass_generator import generate_ass


def find_binary(name):
    # Ưu tiên ffmpeg-full (có libass) nếu có trên hệ thống
    full_path = f"/opt/homebrew/opt/ffmpeg-full/bin/{name}"
    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
        return full_path

    p = shutil.which(name)
    if p:
        return p
    common_paths = [
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
        f"/usr/bin/{name}",
        f"/bin/{name}",
        f"C:\\ffmpeg\\bin\\{name}.exe",
        f"C:\\Program Files\\ffmpeg\\bin\\{name}.exe",
    ]
    for cp in common_paths:
        if os.path.isfile(cp) and os.access(cp, os.X_OK):
            return cp
    return None


def escape_ffmpeg_filter_path(path):
    """
    Escape đường dẫn file để dùng an toàn trong FFmpeg filtergraph:
    Dấu hai chấm ':' và dấu gạch chéo ngược '\' phải được escape.
    """
    normalized = path.replace("\\", "/")
    # Trong FFmpeg filter, dấu ':' là separator nên phải escape
    escaped = normalized.replace(":", "\\:")
    return escaped


def parse_time_str(time_str):
    """Chuyển đổi chuỗi thời gian HH:MM:SS.xx thành số giây."""
    parts = time_str.split(":")
    if len(parts) == 3:
        h = float(parts[0])
        m = float(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s
    return 0.0


def render_hardsub(project_path, output_video_path=None, output_dir=None, progress_callback=None):
    """
    Render video hardsub bằng FFmpeg + libass.
    """
    ffmpeg_bin = find_binary("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("Không tìm thấy 'ffmpeg'. Vui lòng cài đặt FFmpeg (brew install ffmpeg).")

    with open(project_path, "r", encoding="utf-8") as f:
        project = json.load(f)

    video_info = project.get("video", {})
    source_video = video_info.get("source_path")
    if not source_video or not os.path.isfile(source_video):
        raise FileNotFoundError(f"File video gốc không tồn tại: {source_video}")

    duration = float(video_info.get("duration", 0.0))
    proj_dir = os.path.dirname(os.path.abspath(project_path))

    # Đảm bảo reload ass_generator để luôn nhận logic style mới nhất
    import importlib
    import ass_generator
    importlib.reload(ass_generator)
    from ass_generator import generate_ass

    # Sinh file ASS tạm
    temp_ass = os.path.join(proj_dir, "temp_render.ass")
    generate_ass(project, temp_ass)

    # Xác định đường dẫn output
    if not output_video_path:
        base_name = os.path.splitext(video_info.get("filename", "video.mp4"))[0]
        out_dir = output_dir or os.path.expanduser("~/Downloads")
        os.makedirs(out_dir, exist_ok=True)
        output_video_path = os.path.join(out_dir, f"{base_name}_subtitled.mp4")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)

    escaped_ass = escape_ffmpeg_filter_path(temp_ass)
    fonts_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "fonts"))
    if os.path.isdir(fonts_dir):
        escaped_fonts = escape_ffmpeg_filter_path(fonts_dir)
        filter_arg = f"ass=filename='{escaped_ass}':fontsdir='{escaped_fonts}'"
    else:
        filter_arg = f"ass=filename='{escaped_ass}'"

    render_settings = project.get("render_settings", {})
    crf = str(render_settings.get("crf", 20))
    preset = render_settings.get("preset", "fast")

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", source_video,
        "-vf", filter_arg,
        "-c:v", "libx264",
        "-crf", crf,
        "-preset", preset,
        "-c:a", "copy",
        output_video_path,
    ]

    print(f"🎬 Bắt đầu render video với FFmpeg libass...")
    print(f"  Nguồn : {source_video}")
    print(f"  Phụ đề: {temp_ass}")
    print(f"  Đích  : {output_video_path}")

    # Chạy FFmpeg và bắt tiến độ
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    time_regex = re.compile(r"time=(\d+:\d+:\d+\.\d+)")
    last_reported_pct = -1

    for line in proc.stderr:
        match = time_regex.search(line)
        if match and duration > 0:
            cur_sec = parse_time_str(match.group(1))
            pct = min(99, int((cur_sec / duration) * 100))
            if pct > last_reported_pct:
                last_reported_pct = pct
                if progress_callback:
                    progress_callback(pct)
                else:
                    sys.stdout.write(f"\r  [Tiến độ: {pct}%] ({round(cur_sec, 1)}s / {duration}s)")
                    sys.stdout.flush()

    proc.wait()
    if proc.returncode != 0:
        # Nếu audio copy lỗi do container, thử encode lại aac
        print("\n⚠️ Thử lại với audio encoder aac...")
        cmd_fallback = [
            ffmpeg_bin,
            "-y",
            "-i", source_video,
            "-vf", filter_arg,
            "-c:v", "libx264",
            "-crf", crf,
            "-preset", preset,
            "-c:a", "aac",
            "-b:a", "192k",
            output_video_path,
        ]
        res = subprocess.run(cmd_fallback, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg render thất bại: {res.stderr[-500:]}")

    if progress_callback:
        progress_callback(100)
    print(f"\n🎉 RENDER THÀNH CÔNG 100%! File đã sẵn sàng tại:")
    print(f"👉 {output_video_path}")

    return output_video_path


def main():
    parser = argparse.ArgumentParser(description="Render video hardsub MP4 bằng FFmpeg + libass.")
    parser.add_argument("--project", "-p", required=True, help="Đường dẫn file project.json")
    parser.add_argument("--output", "-o", help="Đường dẫn file MP4 xuất ra (tùy chọn)")
    parser.add_argument("--output-dir", help="Thư mục xuất file (mặc định ~/Downloads/)")

    args = parser.parse_args()

    if not os.path.isfile(args.project):
        print(f"❌ Không tìm thấy file project: {args.project}", file=sys.stderr)
        return 1

    try:
        render_hardsub(
            args.project,
            output_video_path=args.output,
            output_dir=args.output_dir,
        )
        return 0
    except Exception as e:
        print(f"\n❌ Lỗi khi render video: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
