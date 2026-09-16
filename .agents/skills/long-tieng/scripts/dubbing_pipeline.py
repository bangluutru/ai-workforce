#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dubbing_pipeline.py — Quy trình lồng tiếng video tự động chuẩn Antigravity (long-tieng).
Tích hợp:
1. Đọc kịch bản / phụ đề từ file JSON (phu-de project.json hoặc SRT).
2. Tổng hợp giọng nói từng phân đoạn (Zero-API / VoiceStudio / Edge-TTS).
3. Tự động co giãn thời gian (Time-Stretching qua FFmpeg atempo) để khớp mốc khẩu hình/thời lượng.
4. Tự động giảm âm nền (Smart Audio Ducking) khi có giọng nói mới lồng vào.
5. Ghép nối video (-c:v copy) bảo toàn chất lượng hình ảnh gốc 100%.
"""

import sys
import os
import json
import argparse
import subprocess
import shutil
import re
import math

def get_media_info(video_path):
    """Trích xuất thông số video bằng ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", video_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    meta = json.loads(res.stdout)
    
    duration = float(meta.get("format", {}).get("duration", 0))
    has_audio = any(s.get("codec_type") == "audio" for s in meta.get("streams", []))
    
    return {
        "duration": duration,
        "has_audio": has_audio,
        "format": meta.get("format", {})
    }

def parse_subtitles(subtitle_path):
    """
    Nạp danh sách phân đoạn phụ đề từ file JSON hoặc SRT.
    Định dạng chuẩn: list các dict: {"id": int, "start": float, "end": float, "text": str}
    """
    if not os.path.isfile(subtitle_path):
        raise FileNotFoundError(f"Không tìm thấy file phụ đề: {subtitle_path}")

    ext = os.path.splitext(subtitle_path)[1].lower()
    if ext == ".json":
        with open(subtitle_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Format phu-de project.json
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
                        "start": start_sec,
                        "end": end_sec,
                        "text": text
                    })
        return segments

    raise ValueError(f"Định dạng phụ đề không hỗ trợ: {ext}")

def get_audio_duration(audio_path):
    """Đo thời lượng file audio chính xác bằng ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip() or 0)

def adjust_audio_speed(input_audio, output_audio, speed_factor):
    """
    Co giãn thời lượng âm thanh bằng bộ lọc atempo của FFmpeg (giữ nguyên cao độ).
    speed_factor = duration_gốc / duration_mục_tiêu
    """
    # atempo chỉ nhận dải 0.5 đến 2.0. Giới hạn dải an toàn 0.75 - 1.35
    safe_speed = max(0.75, min(1.35, speed_factor))
    cmd = [
        "ffmpeg", "-y", "-i", input_audio,
        "-filter:a", f"atempo={safe_speed:.4f}",
        output_audio
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def run_dubbing(video_path, subtitles_path, output_path, lang="vi", gender="female", voice=None, ducking=0.20, process_dir=None):
    """
    Thực thi toàn bộ quy trình lồng tiếng.
    """
    project_id = os.path.splitext(os.path.basename(video_path))[0]
    if not process_dir:
        process_dir = os.path.abspath(f"_process/dubbing_{project_id}")
    os.makedirs(process_dir, exist_ok=True)
    seg_dir = os.path.join(process_dir, "segments")
    os.makedirs(seg_dir, exist_ok=True)

    print(f"🎬 Khởi động quy trình lồng tiếng cho: {os.path.basename(video_path)}")
    print(f"📁 Thư mục tạm xử lý: {process_dir}")

    # Bước 1: Kiểm tra video & trích xuất audio nền
    meta = get_media_info(video_path)
    orig_audio = os.path.join(process_dir, "original_audio.wav")
    if meta["has_audio"]:
        print("🔊 Đang trích xuất audio gốc từ video...")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            orig_audio
        ], capture_output=True, check=True)
    else:
        # Tạo silent audio track theo độ dài video
        print("🔇 Video không có tiếng, tạo audio nền tĩnh...")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(meta["duration"]), orig_audio
        ], capture_output=True, check=True)

    # Bước 2: Nạp phân đoạn lời thoại
    segments = parse_subtitles(subtitles_path)
    print(f"📝 Đã nạp {len(segments)} phân đoạn lời thoại cần lồng tiếng (Ngôn ngữ: {lang.upper()})")

    # Import synthesizer
    from voice_synthesizer import synthesize_line

    timed_segments = []
    for idx, seg in enumerate(segments):
        text = seg.get("target_text") or seg.get("text") or ""
        text = text.strip()
        if not text:
            continue

        start = float(seg["start"])
        end = float(seg["end"])
        target_dur = max(0.5, end - start)

        raw_seg_path = os.path.join(seg_dir, f"raw_seg_{idx:04d}.mp3")
        fitted_seg_path = os.path.join(seg_dir, f"fitted_seg_{idx:04d}.wav")

        print(f" 🎙️ [{idx+1}/{len(segments)}] [{start:.2f}s -> {end:.2f}s]: \"{text[:40]}...\"")
        synth_res = synthesize_line(text, raw_seg_path, lang=lang, gender=gender, voice=voice)
        if not synth_res.get("success", False):
            print(f"   ⚠️ Lỗi tạo tiếng cho đoạn {idx+1}: {synth_res.get('error')}")
            continue

        actual_dur = get_audio_duration(raw_seg_path)
        speed_factor = actual_dur / target_dur

        # Nếu độ dài âm thanh thực tế chênh lệch quá 10%, co giãn tự động
        if abs(speed_factor - 1.0) > 0.08:
            adjust_audio_speed(raw_seg_path, fitted_seg_path, speed_factor)
        else:
            subprocess.run(["ffmpeg", "-y", "-i", raw_seg_path, fitted_seg_path], capture_output=True, check=True)

        timed_segments.append({
            "path": fitted_seg_path,
            "start": start,
            "duration": get_audio_duration(fitted_seg_path)
        })

    if not timed_segments:
        raise RuntimeError("Không có đoạn âm thanh nào được tổng hợp thành công.")

    # Bước 3: Ghép tất cả các đoạn lồng tiếng vào một track hoàn chỉnh theo mốc thời gian
    print("🎛️ Đang định vị mốc thời gian và hòa âm track lồng tiếng (Master Speech Track)...")
    filter_complex_parts = []
    inputs = []
    for i, seg in enumerate(timed_segments):
        inputs.extend(["-i", seg["path"]])
        delay_ms = int(seg["start"] * 1000)
        filter_complex_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}];")

    mix_inputs = "".join(f"[a{i}]" for i in range(len(timed_segments)))
    filter_complex_str = "".join(filter_complex_parts) + f"{mix_inputs}amix=inputs={len(timed_segments)}:dropout_transition=0:normalize=0[speech_out]"

    master_speech_path = os.path.join(process_dir, "master_speech.wav")
    mix_cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_complex_str, "-map", "[speech_out]", master_speech_path]
    subprocess.run(mix_cmd, capture_output=True, check=True)

    # Bước 4: Smart Audio Ducking & Final Audio Mix
    # Giảm âm lượng nhạc nền (ducking) khi có lời thoại đè lên
    print(f"📉 Đang áp dụng hiệu ứng Audio Ducking (mức nền {int(ducking*100)}%)...")
    final_audio_path = os.path.join(process_dir, "final_mixed_audio.wav")

    # Sử dụng sidechain compress hoặc volume ducking
    # Cách đáng tin cậy: sidechaincompress giảm volume input 0 (orig_audio) khi input 1 (speech) phát âm thanh
    ducking_filter = (
        f"[0:a]volume=1.0[bg];"
        f"[1:a]volume=1.2[voice];"
        f"[bg][voice]sidechaincompress=threshold=0.08:ratio=6:attack=100:release=400[ducked_bg];"
        f"[ducked_bg][voice]amix=inputs=2:duration=first:dropout_transition=2[a_final]"
    )
    subprocess.run([
        "ffmpeg", "-y",
        "-i", orig_audio,
        "-i", master_speech_path,
        "-filter_complex", ducking_filter,
        "-map", "[a_final]",
        final_audio_path
    ], capture_output=True, check=True)

    # Bước 5: Đóng gói video thành phẩm
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    print(f"🎥 Đang đóng gói video thành phẩm (-c:v copy) vào: {output_path}")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", final_audio_path,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ], capture_output=True, check=True)

    print(f"🎉 Lồng tiếng video thành công! File xuất bản: {output_path}")
    return {
        "success": True,
        "video_path": video_path,
        "output_path": os.path.abspath(output_path),
        "segments_dubbed": len(timed_segments),
        "total_duration": meta["duration"]
    }

def main():
    parser = argparse.ArgumentParser(description="Quy trình Lồng Tiếng Video Tự Động (AIWF long-tieng)")
    parser.add_argument("--video", "-v", required=True, help="Đường dẫn file video gốc")
    parser.add_argument("--subtitles", "-s", required=True, help="Đường dẫn file phụ đề (project.json hoặc SRT)")
    parser.add_argument("--output", "-o", default=None, help="Đường dẫn xuất video lồng tiếng (mặc định ~/Downloads/)")
    parser.add_argument("--lang", "-l", default="vi", choices=["vi", "ja", "en"], help="Ngôn ngữ lồng tiếng")
    parser.add_argument("--gender", "-g", default="female", choices=["female", "male"], help="Giới tính giọng")
    parser.add_argument("--voice", default=None, help="Mã giọng cụ thể")
    parser.add_argument("--ducking", "-d", type=float, default=0.20, help="Mức âm lượng nền khi ducking (0.10 đến 0.35)")
    parser.add_argument("--process-dir", default=None, help="Thư mục tạm xử lý")
    args = parser.parse_args()

    output_path = args.output
    if not output_path:
        base_name = os.path.splitext(os.path.basename(args.video))[0]
        output_path = os.path.expanduser(f"~/Downloads/{base_name}_dubbed.mp4")

    res = run_dubbing(
        video_path=args.video,
        subtitles_path=args.subtitles,
        output_path=output_path,
        lang=args.lang,
        gender=args.gender,
        voice=args.voice,
        ducking=args.ducking,
        process_dir=args.process_dir
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
