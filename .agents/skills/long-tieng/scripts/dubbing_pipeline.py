#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dubbing_pipeline.py — Quy trình lồng tiếng video tự động chuẩn Antigravity (long-tieng).
Tích hợp:
1. Đọc kịch bản / phụ đề từ file JSON (phu-de project.json hoặc dubbing_project.json hoặc SRT).
2. Tổng hợp giọng nói từng phân đoạn (Zero-API / VoiceStudio / Edge-TTS).
3. Tự động co giãn thời gian (Time-Stretching qua FFmpeg atempo) để khớp mốc khẩu hình/thời lượng.
4. Tự động cân bằng âm lượng giọng gốc và giọng lồng tiếng (Smart Audio Ducking & Volume Balancing).
5. Khắc phụ đề ASS thẩm mỹ cao 1:1 theo style cấu hình và đóng gói video MP4 (-c:v copy hoặc hardsub).
"""

import sys
import os
import json
import argparse
import subprocess
import shutil
import re
import math

def get_ffmpeg_bin():
    """Xác định đường dẫn nhị phân FFmpeg tối ưu."""
    for p in ["/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return shutil.which("ffmpeg") or "ffmpeg"

def get_ffprobe_bin():
    """Xác định đường dẫn nhị phân FFprobe."""
    for p in ["/opt/homebrew/opt/ffmpeg-full/bin/ffprobe", "/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe"]:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return shutil.which("ffprobe") or "ffprobe"

def get_media_info(video_path):
    """Trích xuất thông số video bằng ffprobe."""
    ffprobe_bin = get_ffprobe_bin()
    cmd = [
        ffprobe_bin, "-v", "quiet", "-print_format", "json",
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
    Định dạng chuẩn: list các dict: {"id": int, "start": float, "end": float, "text": str, "source_text": str, "target_text": str}
    """
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
                        "start": start_sec,
                        "end": end_sec,
                        "source_text": text,
                        "target_text": text,
                        "text": text
                    })
        return segments

    raise ValueError(f"Định dạng phụ đề không hỗ trợ: {ext}")

def get_audio_duration(audio_path):
    """Đo thời lượng file audio chính xác bằng ffprobe."""
    ffprobe_bin = get_ffprobe_bin()
    cmd = [
        ffprobe_bin, "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip() or 0)

def adjust_audio_speed(input_audio, output_audio, speed_factor):
    """
    Co giãn thời lượng âm thanh bằng bộ lọc atempo của FFmpeg (giữ nguyên cao độ).
    FFmpeg atempo chỉ hỗ trợ 0.5-2.0 mỗi lần, dùng chain nếu cần.
    Hỗ trợ input bất kỳ format (mp3, wav, ogg...).
    """
    ffmpeg_bin = get_ffmpeg_bin()
    safe_speed = max(0.50, min(2.0, speed_factor))
    
    # FFmpeg atempo filter hỗ trợ range [0.5, 100.0] nhưng chất lượng tốt nhất ở [0.5, 2.0]
    # Nếu cần ngoài range, chain nhiều atempo filter
    if safe_speed >= 0.5 and safe_speed <= 2.0:
        filter_str = f"atempo={safe_speed:.4f}"
    elif safe_speed < 0.5:
        # Chain: atempo=0.5 * atempo=(safe_speed/0.5)
        filter_str = f"atempo=0.5,atempo={safe_speed/0.5:.4f}"
    else:
        filter_str = f"atempo=2.0,atempo={safe_speed/2.0:.4f}"
    
    cmd = [
        ffmpeg_bin, "-y", "-i", input_audio,
        "-filter:a", filter_str,
        "-acodec", "pcm_s16le",
        output_audio
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def hex_to_ass_color(hex_color, alpha_pct=0):
    """Chuyển đổi màu HEX (#RRGGBB) sang định dạng màu ASS &HAABBGGRR."""
    clean = hex_color.replace("#", "").strip() if hex_color else "FFFFFF"
    if len(clean) == 6:
        r, g, b = clean[0:2], clean[2:4], clean[4:6]
    elif len(clean) == 3:
        r, g, b = clean[0]*2, clean[1]*2, clean[2]*2
    else:
        r, g, b = "FF", "FF", "FF"
    # alpha trong ASS: 0 = đặc, 255 = trong suốt hoàn toàn
    alpha_val = max(0, min(255, int(alpha_pct * 2.55)))
    alpha_hex = f"{alpha_val:02X}"
    return f"&H{alpha_hex}{b.upper()}{g.upper()}{r.upper()}"

def generate_subtitles(segments, process_dir, output_dir=None, base_name="subtitles", style=None):
    """Sinh file phụ đề SRT và ASS chuẩn thẩm mỹ studio theo style tùy chỉnh."""
    def fmt_srt(sec):
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int(round((sec - int(sec)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def fmt_ass(sec):
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        cs = int(round((sec - int(sec)) * 100))
        return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"

    s = style or {}
    font_name = s.get("font_family", "Be Vietnam Pro")
    font_size = int(s.get("font_size", 24))
    primary_color = hex_to_ass_color(s.get("primary_color", "#FFFFFF"), 0)
    secondary_color = hex_to_ass_color(s.get("secondary_color", "#FFD700"), 0)
    outline_color = hex_to_ass_color(s.get("outline_color", "#000000"), 0)
    outline_width = float(s.get("outline_width", 2.0))
    bg_color = hex_to_ass_color(s.get("background_color", "#000000"), 100 - int(s.get("background_opacity", 35)))
    align = int(s.get("alignment", 2))
    margin_v = int(s.get("margin_v", 45))
    margin_l = int(s.get("margin_l", 40))
    margin_r = int(s.get("margin_r", 40))
    border_style = 3 if int(s.get("background_opacity", 35)) > 10 else 1
    mode = s.get("mode", "monolingual")
    bilingual_order = s.get("bilingual_order", "target_top")

    srt_lines = []
    ass_events = []

    for idx, seg in enumerate(segments, 1):
        start = float(seg["start"])
        end = float(seg["end"])
        trans_text = (seg.get("target_text") or seg.get("text") or "").strip()
        src_text = (seg.get("source_text") or "").strip()

        # SRT output
        if mode == "bilingual" and src_text and trans_text and src_text != trans_text:
            srt_content = f"{trans_text}\n{src_text}" if bilingual_order == "target_top" else f"{src_text}\n{trans_text}"
        elif mode == "source_only" and src_text:
            srt_content = src_text
        else:
            srt_content = trans_text or src_text

        srt_lines.extend([str(idx), f"{fmt_srt(start)} --> {fmt_srt(end)}", srt_content, ""])

        # ASS output
        if mode == "bilingual" and src_text and trans_text and src_text != trans_text:
            sub_font_size = int(font_size * 0.78)
            sec_col_ass = secondary_color.replace("&H00", "&H")
            if bilingual_order == "target_top":
                ass_line = f"{trans_text}\\N{{\\fs{sub_font_size}\\c{sec_col_ass}}}{src_text}"
            else:
                ass_line = f"{src_text}\\N{{\\fs{sub_font_size}\\c{sec_col_ass}}}{trans_text}"
        elif mode == "source_only" and src_text:
            ass_line = src_text
        else:
            ass_line = trans_text or src_text

        ass_events.append(f"Dialogue: 0,{fmt_ass(start)},{fmt_ass(end)},Default,,0,0,0,,{ass_line}")

    # Ghi SRT
    proc_srt = os.path.join(process_dir, "subtitles.srt")
    with open(proc_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines) + "\n")
    if output_dir:
        out_srt = os.path.join(output_dir, f"{base_name}.srt")
        with open(out_srt, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines) + "\n")

    # Ghi ASS
    ass_header = f"""[Script Info]
Title: Video Dubbing Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},{secondary_color},{outline_color},{bg_color},-1,0,0,0,100,100,0,0,{border_style},{outline_width:.1f},1.0,{align},{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass_path = os.path.join(process_dir, "subtitles.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(ass_events) + "\n")

    return ass_path, proc_srt

def run_dubbing(
    video_path,
    subtitles_path,
    output_path,
    lang="vi",
    gender="female",
    voice=None,
    speed=1.0,
    bg_volume=1.0,
    voice_volume=1.4,
    ducking_ratio=0.20,
    include_subtitles=True,
    style=None,
    process_dir=None,
    progress_callback=None
):
    """
    Thực thi toàn bộ quy trình lồng tiếng video khép kín:
    - Bóc tách audio gốc
    - Đọc style cấu hình và các câu thoại mới nhất
    - Tổng hợp giọng nói neural theo từng câu
    - Co giãn nhịp điệu atempo
    - Hòa âm mốc thời gian master speech
    - Cân bằng âm lượng gốc và âm lượng lồng tiếng với smart audio ducking
    - Xuất video thành phẩm ra output_path
    """
    def report_progress(pct, msg):
        if progress_callback:
            try:
                progress_callback(pct, msg)
            except Exception:
                pass
        print(f"[{pct:3d}%] {msg}")

    ffmpeg_bin = get_ffmpeg_bin()
    project_id = os.path.splitext(os.path.basename(video_path))[0]
    if not process_dir:
        process_dir = os.path.abspath(f"_process/dubbing_{project_id}")
    os.makedirs(process_dir, exist_ok=True)
    seg_dir = os.path.join(process_dir, "segments")
    os.makedirs(seg_dir, exist_ok=True)

    report_progress(5, f"Khởi động quy trình lồng tiếng cho {os.path.basename(video_path)}")

    # Nạp style từ file JSON nếu có
    if style is None and subtitles_path.endswith(".json") and os.path.isfile(subtitles_path):
        try:
            with open(subtitles_path, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict) and "style" in d:
                    style = d["style"]
        except Exception:
            pass

    # Bước 1: Kiểm tra video & trích xuất audio nền (Chuẩn 48 kHz)
    meta = get_media_info(video_path)
    orig_audio = os.path.join(process_dir, "original_audio.wav")
    if meta["has_audio"]:
        report_progress(10, "Trích xuất audio gốc từ video (48 kHz)...")
        subprocess.run([
            ffmpeg_bin, "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "48000", "-ac", "2",
            orig_audio
        ], capture_output=True, check=True)
    else:
        report_progress(10, "Video không có tiếng, tạo audio nền tĩnh (48 kHz)...")
        subprocess.run([
            ffmpeg_bin, "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
            "-t", str(meta["duration"]), orig_audio
        ], capture_output=True, check=True)

    # Bước 2: Nạp phân đoạn lời thoại
    segments = parse_subtitles(subtitles_path)
    total_segments = len(segments)
    report_progress(15, f"Đã nạp {total_segments} phân đoạn lời thoại cần lồng tiếng")

    # Import synthesizer
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from voice_synthesizer import synthesize_line

    # =====================================================================
    # PASS 1: Tổng hợp giọng nói tất cả phân đoạn, đo thời lượng thô
    # Auto-detect file format thực tế (.mp3 vs .wav) từ voice engine
    # =====================================================================
    raw_data = []  # list of {idx, start, end, target_dur, raw_path, actual_dur}
    for idx, seg in enumerate(segments):
        text = seg.get("target_text") or seg.get("text") or ""
        text = text.strip()
        if not text:
            continue

        start = float(seg["start"])
        end = float(seg["end"])
        target_dur = max(0.5, end - start)

        raw_seg_path = os.path.join(seg_dir, f"raw_seg_{idx:04d}.wav")

        pct_seg = 15 + int((idx / max(1, total_segments)) * 35)
        report_progress(pct_seg, f"[Pass 1] Tổng hợp giọng câu {idx+1}/{total_segments}: \"{text[:30]}...\"")

        ref_audio_seg = seg.get("ref_audio")
        synth_res = synthesize_line(text, raw_seg_path, lang=lang, gender=gender, voice=voice, speed=speed, ref_audio=ref_audio_seg)
        if not synth_res.get("success", False):
            print(f"   ⚠️ Lỗi tạo tiếng cho câu {idx+1}: {synth_res.get('error')}")
            continue

        # Auto-detect: voice engine có thể lưu .mp3 thay vì .wav
        actual_raw_path = raw_seg_path
        if not os.path.isfile(actual_raw_path) or os.path.getsize(actual_raw_path) == 0:
            # Tìm file thực tế với các extension phổ biến
            base_no_ext = os.path.splitext(raw_seg_path)[0]
            for alt_ext in [".mp3", ".ogg", ".m4a", ".wav"]:
                candidate = base_no_ext + alt_ext
                if os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
                    actual_raw_path = candidate
                    break
        # Nếu synth_res trả về output_path khác, ưu tiên dùng nó
        synth_output = synth_res.get("output_path", "")
        if synth_output and os.path.isfile(synth_output) and os.path.getsize(synth_output) > 0:
            actual_raw_path = synth_output

        if not os.path.isfile(actual_raw_path) or os.path.getsize(actual_raw_path) == 0:
            print(f"   ⚠️ Không tìm thấy file âm thanh thô cho câu {idx+1}")
            continue

        actual_dur = get_audio_duration(actual_raw_path)
        if actual_dur <= 0.01:
            print(f"   ⚠️ File âm thanh câu {idx+1} có thời lượng quá ngắn ({actual_dur:.3f}s), bỏ qua.")
            continue

        raw_data.append({
            "idx": idx,
            "start": start,
            "end": end,
            "target_dur": target_dur,
            "raw_path": actual_raw_path,
            "actual_dur": actual_dur
        })
        print(f"      ↳ Câu {idx+1}: AI thô = {actual_dur:.2f}s | Gốc = {target_dur:.2f}s | File: {os.path.basename(actual_raw_path)}")

    if not raw_data:
        raise RuntimeError("Không có đoạn âm thanh nào được tổng hợp thành công.")

    # =====================================================================
    # PASS 2: Tính atempo ĐỒNG NHẤT toàn cục, áp dụng cùng tốc độ cho mọi câu
    # Thuật toán: Tính tổng thời lượng AI thô vs tổng thời lượng mục tiêu (88% gốc)
    # => ra 1 hệ số atempo duy nhất giữ nhịp đọc BẰNG NHAU xuyên suốt video
    # =====================================================================
    report_progress(52, "Phân tích nhịp đọc toàn cục để tính tốc độ đồng nhất...")

    total_raw_dur = sum(d["actual_dur"] for d in raw_data)
    total_target_cover = sum(d["target_dur"] * 0.88 for d in raw_data)  # 88% cho khoảng thở tự nhiên

    global_atempo = total_raw_dur / total_target_cover if total_target_cover > 0.1 else 1.0
    # Giới hạn dải an toàn: 0.70 (chậm vừa phải) → 1.15 (nhanh nhẹ) để tránh méo tiếng
    global_atempo = max(0.70, min(1.15, global_atempo))

    print(f"\n   📊 PHÂN TÍCH NHỊP ĐỌC TOÀN CỤC:")
    print(f"      Tổng thời lượng AI thô:  {total_raw_dur:.2f}s")
    print(f"      Tổng mục tiêu (88%):     {total_target_cover:.2f}s")
    print(f"      ➤ atempo ĐỒNG NHẤT:      {global_atempo:.4f}")
    print(f"      (Áp dụng cùng tốc độ cho tất cả {len(raw_data)} câu)\n")

    timed_segments = []
    for entry in raw_data:
        idx = entry["idx"]
        fitted_seg_path = os.path.join(seg_dir, f"fitted_seg_{idx:04d}.wav")

        pct_seg = 55 + int((len(timed_segments) / max(1, len(raw_data))) * 10)
        report_progress(pct_seg, f"[Pass 2] Căn nhịp đồng nhất câu {len(timed_segments)+1}/{len(raw_data)} (atempo={global_atempo:.3f})...")

        if abs(global_atempo - 1.0) >= 0.02:
            adjust_audio_speed(entry["raw_path"], fitted_seg_path, global_atempo)
        else:
            # Chuyển đổi sang WAV chuẩn nếu không cần co giãn
            subprocess.run([
                ffmpeg_bin, "-y", "-i", entry["raw_path"],
                "-acodec", "pcm_s16le", fitted_seg_path
            ], capture_output=True, check=True)

        fitted_dur = get_audio_duration(fitted_seg_path)
        coverage_pct = (fitted_dur / entry["target_dur"]) * 100 if entry["target_dur"] > 0 else 100
        print(f"      ↳ Gốc: {entry['target_dur']:4.2f}s | AI thô: {entry['actual_dur']:4.2f}s | atempo={global_atempo:.3f} -> Khớp: {fitted_dur:4.2f}s ({coverage_pct:.1f}%)")

        timed_segments.append({
            "path": fitted_seg_path,
            "start": entry["start"],
            "duration": fitted_dur
        })

    if not timed_segments:
        raise RuntimeError("Không có đoạn âm thanh nào được tổng hợp thành công.")

    # Bước 3: Hòa âm Master Speech Track
    report_progress(65, "Định vị mốc thời gian và hòa âm Master Speech Track (48 kHz)...")
    filter_complex_parts = []
    inputs = []
    for i, seg in enumerate(timed_segments):
        inputs.extend(["-i", seg["path"]])
        delay_ms = int(seg["start"] * 1000)
        filter_complex_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}];")

    mix_inputs = "".join(f"[a{i}]" for i in range(len(timed_segments)))
    filter_complex_str = "".join(filter_complex_parts) + f"{mix_inputs}amix=inputs={len(timed_segments)}:dropout_transition=0:normalize=0,apad=whole_dur={meta['duration']}[speech_out]"

    master_speech_path = os.path.join(process_dir, "master_speech.wav")
    mix_cmd = [ffmpeg_bin, "-y"] + inputs + ["-filter_complex", filter_complex_str, "-map", "[speech_out]", master_speech_path]
    subprocess.run(mix_cmd, capture_output=True, check=True)

    # Bước 4: Smart Audio Ducking & Volume Balancing
    report_progress(75, "Cân bằng âm lượng và hòa âm Smart Audio Ducking...")
    final_audio_path = os.path.join(process_dir, "final_mixed_audio.wav")
    master_48k = os.path.join(process_dir, "master_speech_48k.wav")
    master_44k = os.path.join(process_dir, "master_speech_44k.wav")

    subprocess.run([
        ffmpeg_bin, "-y", "-i", master_speech_path,
        "-ar", "48000", "-ac", "2", master_48k
    ], capture_output=True, check=True)
    subprocess.run([
        ffmpeg_bin, "-y", "-i", master_speech_path,
        "-ar", "44100", "-ac", "2", master_44k
    ], capture_output=True, check=True)

    if bg_volume <= 0.01:
        subprocess.run([
            ffmpeg_bin, "-y", "-i", master_48k,
            "-filter:a", f"volume={voice_volume:.2f}",
            final_audio_path
        ], capture_output=True, check=True)
    else:
        duck_ratio_val = max(4.0, min(30.0, 1.0 / max(0.03, ducking_ratio)))
        ducking_filter = (
            f"[0:a][1:a]sidechaincompress=threshold=0.01:ratio={duck_ratio_val:.1f}:attack=40:release=350[ducked_bg];"
            f"[ducked_bg]volume={bg_volume:.2f}[bg];"
            f"[1:a]volume={voice_volume:.2f}[voice];"
            f"[bg][voice]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a_final]"
        )
        subprocess.run([
            ffmpeg_bin, "-y",
            "-i", orig_audio,
            "-i", master_48k,
            "-filter_complex", ducking_filter,
            "-map", "[a_final]",
            final_audio_path
        ], capture_output=True, check=True)

    # Bước 5: Đóng gói video thành phẩm
    report_progress(85, "Đóng gói video xuất bản...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    out_dir = os.path.dirname(os.path.abspath(output_path))
    out_base = os.path.splitext(os.path.basename(output_path))[0]
    ass_file, srt_file = generate_subtitles(segments, process_dir, out_dir, out_base, style=style)

    filters_out = subprocess.run([ffmpeg_bin, "-filters"], capture_output=True, text=True).stdout
    has_ass = any(line.strip().startswith(".. ass") or line.strip().startswith("TS ass") for line in filters_out.splitlines())
    has_subtitles = any(line.strip().startswith(".. subtitles") or line.strip().startswith("TS subtitles") for line in filters_out.splitlines())

    render_success = False
    if include_subtitles and (has_ass or has_subtitles):
        filter_str = f"ass='{ass_file}'" if has_ass else f"subtitles='{srt_file}'"
        report_progress(90, f"Đang khắc phụ đề ({filter_str}) và lồng tiếng vào video: {output_path}")
        render_cmd = [
            ffmpeg_bin, "-y",
            "-i", video_path,
            "-i", final_audio_path,
            "-vf", filter_str,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "h264_videotoolbox",
            "-b:v", "2800k",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
        try:
            subprocess.run(render_cmd, capture_output=True, check=True)
            render_success = True
        except subprocess.CalledProcessError:
            try:
                # Fallback libx264
                render_cmd[render_cmd.index("h264_videotoolbox")] = "libx264"
                render_cmd.insert(render_cmd.index("2800k") + 1, "-preset")
                render_cmd.insert(render_cmd.index("-preset") + 1, "fast")
                subprocess.run(render_cmd, capture_output=True, check=True)
                render_success = True
            except Exception:
                render_success = False

    if not render_success:
        report_progress(90, f"Đóng gói video siêu tốc (-c:v copy) kèm âm thanh lồng tiếng vào: {output_path}")
        copy_cmd = [
            ffmpeg_bin, "-y",
            "-i", video_path,
            "-i", final_audio_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k"
        ]
        if os.path.isfile(srt_file):
            copy_cmd.extend([
                "-i", srt_file,
                "-map", "2:s",
                "-c:s", "mov_text",
                "-metadata:s:s:0", f"language={lang}"
            ])
        copy_cmd.append(output_path)
        subprocess.run(copy_cmd, capture_output=True, check=True)

    report_progress(100, f"Lồng tiếng video thành công! File xuất bản: {output_path}")
    return {
        "success": True,
        "video_path": video_path,
        "output_path": os.path.abspath(output_path),
        "segments_dubbed": len(timed_segments),
        "total_duration": meta["duration"],
        "audio_settings": {
            "lang": lang,
            "gender": gender,
            "voice": voice,
            "speed": speed,
            "bg_volume": bg_volume,
            "voice_volume": voice_volume,
            "ducking_ratio": ducking_ratio,
            "include_subtitles": include_subtitles
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Quy trình Lồng Tiếng Video Tự Động (AIWF long-tieng)")
    parser.add_argument("--video", "-v", required=True, help="Đường dẫn file video gốc")
    parser.add_argument("--subtitles", "-s", required=True, help="Đường dẫn file phụ đề (project.json hoặc SRT)")
    parser.add_argument("--output", "-o", default=None, help="Đường dẫn xuất video lồng tiếng (mặc định ~/Downloads/)")
    parser.add_argument("--lang", "-l", default="vi", choices=["vi", "ja", "en"], help="Ngôn ngữ lồng tiếng")
    parser.add_argument("--gender", "-g", default="female", choices=["female", "male"], help="Giới tính giọng")
    parser.add_argument("--voice", default=None, help="Mã giọng cụ thể")
    parser.add_argument("--speed", type=float, default=1.0, help="Tốc độ đọc cơ sở (0.8 đến 1.25)")
    parser.add_argument("--bg-volume", type=float, default=1.0, help="Hệ số âm lượng nền (0.0 đến 1.5)")
    parser.add_argument("--voice-volume", type=float, default=1.4, help="Hệ số âm lượng giọng lồng tiếng (0.5 đến 2.0)")
    parser.add_argument("--ducking", "-d", type=float, default=0.20, help="Mức âm lượng nền khi ducking (0.05 đến 0.40)")
    parser.add_argument("--no-subtitles", action="store_true", help="Không khắc phụ đề lên video (chỉ lồng tiếng)")
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
        speed=args.speed,
        bg_volume=args.bg_volume,
        voice_volume=args.voice_volume,
        ducking_ratio=args.ducking,
        include_subtitles=not args.no_subtitles,
        process_dir=args.process_dir
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
