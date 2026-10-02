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
    vs = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), {})

    return {
        "duration": duration,
        "has_audio": has_audio,
        "width": int(vs.get("width", 1920) or 1920),
        "height": int(vs.get("height", 1080) or 1080),
        "format": meta.get("format", {})
    }

def normalize_segment(s):
    """Thống nhất trường văn bản giữa phu-de (translated_text), long-tieng (target_text) và SRT (text).
    Câu để ĐỌC = bản dịch nếu có, rồi target_text, rồi text, cuối cùng mới tới câu gốc."""
    s = dict(s)
    tgt = s.get("dub_text") or s.get("translated_text") or s.get("target_text") or s.get("text") or s.get("source_text") or ""
    s["target_text"] = tgt.replace("\n", " ").strip()
    s.setdefault("source_text", s.get("text") or tgt)
    s["text"] = s["target_text"]
    return s


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
        segs = data.get("segments") or data.get("subtitles") if isinstance(data, dict) else data
        if isinstance(segs, list):
            return [normalize_segment(s) for s in segs]
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

PHUDE_SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "phu-de", "scripts"))
PHUDE_FONTS = os.path.abspath(os.path.join(PHUDE_SCRIPTS, "..", "templates", "fonts"))


def generate_subtitles(segments, process_dir, output_dir=None, base_name="subtitles", style=None, video_meta=None):
    """Sinh SRT + ASS. Ưu tiên bộ sinh của phu-de (cùng preset, font Be Vietnam Pro, ngắt dòng theo ngữ pháp,
    hộp nền bo góc) để phụ đề video lồng tiếng đẹp như video phụ đề; lỗi thì dùng bộ sinh cũ bên dưới."""
    try:
        sys.path.insert(0, PHUDE_SCRIPTS)
        from ass_generator import generate_ass as _gen_ass, generate_srt as _gen_srt
        presets = json.load(open(os.path.join(PHUDE_SCRIPTS, "..", "templates", "default_styles.json"), encoding="utf-8"))["presets"]
        st = dict(presets.get((style or {}).get("preset", "modern_bottom"), presets["modern_bottom"]))
        st.update({k: v for k, v in (style or {}).items() if v is not None})
        st.setdefault("mode", "monolingual")
        proj = {"video": video_meta or {"width": 1920, "height": 1080}, "style": st,
                "segments": [{"start": float(x["start"]), "end": float(x["end"]),
                              "source_text": (x.get("source_text") or "").strip(),
                              "translated_text": (x.get("translated_text") or x.get("target_text") or x.get("text") or "").strip()} for x in segments]}
        out_dir = output_dir or process_dir
        ass_path = os.path.join(process_dir, f"{base_name}.ass"); srt_path = os.path.join(out_dir, f"{base_name}.srt")
        _gen_ass(proj, ass_path); _gen_srt(proj, srt_path)
        return ass_path, srt_path
    except Exception as e:
        print(f"   ⚠️ Không dùng được bộ sinh phụ đề phu-de ({e}); dùng bộ sinh cơ bản.")
    return _generate_subtitles_basic(segments, process_dir, output_dir, base_name, style)


def _generate_subtitles_basic(segments, process_dir, output_dir=None, base_name="subtitles", style=None):
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

    # Bước 3–4: Tổng hợp (VieNeu offline, đọc lại câu sai), khớp khung từng câu (chỉ tăng tốc, trần 1.25×),
    # hạ tiếng gốc theo vùng có lời + chuẩn hoá −16 LUFS. Chi tiết: dub_engine.py
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dub_engine
    report_progress(20, "Tổng hợp giọng đọc + kiểm tra phát âm bằng Whisper...")
    final_audio_path, dub_report = dub_engine.dub_audio(
        [{"start": s["start"], "end": s["end"], "text": s.get("target_text") or s.get("text") or ""} for s in segments],
        meta["duration"], orig_audio, process_dir, lang=lang, voice=voice, gender=gender,
        bg_volume=bg_volume, duck_level=max(0.0, min(1.0, ducking_ratio)), voice_volume=voice_volume,
        speed=speed, log=lambda m: report_progress(60, m))
    timed_segments = dub_report["items"]

    # Bước 5: Đóng gói video thành phẩm
    report_progress(85, "Đóng gói video xuất bản...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    out_dir = os.path.dirname(os.path.abspath(output_path))
    out_base = os.path.splitext(os.path.basename(output_path))[0]
    ass_file, srt_file = generate_subtitles(segments, process_dir, out_dir, out_base, style=style, video_meta={"width": meta.get("width", 1920), "height": meta.get("height", 1080)})

    filters_out = subprocess.run([ffmpeg_bin, "-filters"], capture_output=True, text=True).stdout
    has_ass = any(line.strip().startswith(".. ass") or line.strip().startswith("TS ass") for line in filters_out.splitlines())
    has_subtitles = any(line.strip().startswith(".. subtitles") or line.strip().startswith("TS subtitles") for line in filters_out.splitlines())

    render_success = False
    if include_subtitles and (has_ass or has_subtitles):
        esc = lambda p: p.replace("\\", "/").replace(":", "\\:")
        filter_str = (f"ass='{esc(ass_file)}':fontsdir='{esc(PHUDE_FONTS)}'" if os.path.isdir(PHUDE_FONTS) else f"ass='{esc(ass_file)}'") if has_ass else f"subtitles='{esc(srt_file)}'"
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
        "dub_report": {k: v for k, v in dub_report.items() if k != "items"},
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
    parser.add_argument("--output", "-o", default=None, help="Đường dẫn xuất video lồng tiếng (mặc định ~/Downloads/AIWF_Output/)")
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
        output_path = os.path.expanduser(f"~/Downloads/AIWF_Output/long-tieng/{base_name}_dubbed.mp4")

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
