#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_audio.py — Bóc tách audio 16kHz mono PCM WAV và trích xuất metadata video.
Sử dụng FFmpeg & ffprobe (deterministic media tools).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys


def find_binary(name):
    p = shutil.which(name)
    if p:
        return p
    common_paths = [
        f"/opt/homebrew/opt/ffmpeg-full/bin/{name}",
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


def probe_video(video_path):
    ffprobe_bin = find_binary("ffprobe")
    if not ffprobe_bin:
        raise RuntimeError("Không tìm thấy công cụ 'ffprobe'. Vui lòng cài đặt FFmpeg (brew install ffmpeg).")

    cmd = [
        ffprobe_bin,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Lỗi khi đọc thông số video: {res.stderr.strip()}")

    data = json.loads(res.stdout)
    format_info = data.get("format", {})
    streams = data.get("streams", [])

    video_stream = None
    audio_stream = None
    for s in streams:
        if s.get("codec_type") == "video" and not video_stream:
            video_stream = s
        elif s.get("codec_type") == "audio" and not audio_stream:
            audio_stream = s

    duration = float(format_info.get("duration", 0.0))
    width = 1920
    height = 1080
    fps = 30.0
    video_codec = "unknown"
    audio_codec = "none"

    if video_stream:
        width = int(video_stream.get("width", 1920))
        height = int(video_stream.get("height", 1080))
        video_codec = video_stream.get("codec_name", "unknown")
        if duration == 0.0 and "duration" in video_stream:
            try:
                duration = float(video_stream["duration"])
            except ValueError:
                pass

        r_fps = video_stream.get("r_frame_rate", "30/1")
        if "/" in r_fps:
            num, den = r_fps.split("/", 1)
            try:
                den_f = float(den)
                if den_f > 0:
                    fps = round(float(num) / den_f, 2)
            except Exception:
                fps = 30.0
        else:
            try:
                fps = float(r_fps)
            except Exception:
                fps = 30.0

    if audio_stream:
        audio_codec = audio_stream.get("codec_name", "unknown")

    # Tính aspect ratio
    aspect_ratio = "16:9"
    if width > 0 and height > 0:
        gcd_val = _gcd(width, height)
        w_ratio = width // gcd_val
        h_ratio = height // gcd_val
        if (w_ratio, h_ratio) in [(16, 9), (9, 16), (4, 3), (1, 1), (21, 9)]:
            aspect_ratio = f"{w_ratio}:{h_ratio}"
        else:
            ratio_float = round(width / height, 2)
            if ratio_float == 1.78:
                aspect_ratio = "16:9"
            elif ratio_float == 0.56:
                aspect_ratio = "9:16"
            elif ratio_float == 1.0:
                aspect_ratio = "1:1"
            else:
                aspect_ratio = f"{width}:{height}"

    return {
        "source_path": os.path.abspath(video_path),
        "filename": os.path.basename(video_path),
        "duration": round(duration, 2),
        "width": width,
        "height": height,
        "fps": fps,
        "aspect_ratio": aspect_ratio,
        "video_codec": video_codec,
        "audio_codec": audio_codec,
    }


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def extract_audio(video_path, output_wav_path):
    ffmpeg_bin = find_binary("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("Không tìm thấy công cụ 'ffmpeg'. Vui lòng cài đặt FFmpeg (brew install ffmpeg).")

    os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_wav_path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Lỗi khi trích xuất âm thanh: {res.stderr.strip()}")
    return output_wav_path


def main():
    parser = argparse.ArgumentParser(description="Trích xuất audio WAV 16kHz và đọc thông số video.")
    parser.add_argument("--video", "-v", required=True, help="Đường dẫn file video đầu vào")
    parser.add_argument("--output-wav", "-o", required=True, help="Đường dẫn file audio .wav đầu ra")
    parser.add_argument("--meta-json", "-m", help="Đường dẫn file lưu metadata JSON (tùy chọn)")

    args = parser.parse_args()

    if not os.path.isfile(args.video):
        print(f"❌ File video không tồn tại: {args.video}", file=sys.stderr)
        return 1

    try:
        print(f"🔍 Đang phân tích thông số video: {args.video}")
        meta = probe_video(args.video)
        print(f"  Thời lượng: {meta['duration']}s | Kích thước: {meta['width']}x{meta['height']} ({meta['aspect_ratio']}) | FPS: {meta['fps']}")

        print(f"🎵 Đang trích xuất audio 16kHz mono WAV...")
        wav_path = extract_audio(args.video, args.output_wav)
        print(f"  ✅ Đã lưu audio: {wav_path}")

        if args.meta_json:
            os.makedirs(os.path.dirname(os.path.abspath(args.meta_json)), exist_ok=True)
            with open(args.meta_json, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            print(f"  ✅ Đã lưu metadata: {args.meta_json}")

        return 0
    except Exception as e:
        print(f"❌ Thất bại: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
