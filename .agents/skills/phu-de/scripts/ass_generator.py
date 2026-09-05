#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ass_generator.py — Biên dịch project.json thành định dạng phụ đề ASS và SRT.
Chuyển đổi các thuộc tính màu sắc, font chữ, viền, hộp nền và canh lề sang ASS Styles.
"""

import argparse
import json
import math
import os
import sys


def hex_to_ass_color(hex_str, opacity=1.0):
    """
    Chuyển mã màu Hex (#RRGGBB) sang định dạng màu ASS: &HAABBGGRR&.
    Lưu ý: ASS dùng thứ tự BGR và Alpha đảo ngược (00 = đậm đặc, FF = trong suốt).
    """
    if not hex_str:
        hex_str = "#FFFFFF"
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join([c * 2 for c in hex_str])

    if len(hex_str) >= 6:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
    else:
        r, g, b = 255, 255, 255

    # Tính Alpha: opacity 1.0 -> 0x00; opacity 0.0 -> 0xFF
    opacity = max(0.0, min(1.0, float(opacity)))
    alpha = int((1.0 - opacity) * 255)

    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}&"


def format_ass_time(seconds):
    """Chuyển số giây sang định dạng thời gian ASS: H:MM:SS.cc (centiseconds)."""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def format_srt_time(seconds):
    """Chuyển số giây sang định dạng thời gian SRT: HH:MM:SS,mmm (milliseconds)."""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def make_rounded_rect_path(w, h, r):
    """
    Sinh đường vẽ vector ASS (m/l/b) cho hình chữ nhật bo góc.
    Sử dụng 4 đoạn thẳng và 4 cung Bezier bậc 3 (constant k = 0.5522847 * r).
    """
    r = max(0.0, min(float(r), w / 2.0, h / 2.0))
    if r <= 0:
        return f"m 0 0 l {w:.1f} 0 l {w:.1f} {h:.1f} l 0 {h:.1f} l 0 0"

    k = 0.5522847 * r
    return (
        f"m {r:.1f} 0 "
        f"l {w - r:.1f} 0 "
        f"b {w - r + k:.1f} 0 {w:.1f} {r - k:.1f} {w:.1f} {r:.1f} "
        f"l {w:.1f} {h - r:.1f} "
        f"b {w:.1f} {h - r + k:.1f} {w - r + k:.1f} {h:.1f} {w - r:.1f} {h:.1f} "
        f"l {r:.1f} {h:.1f} "
        f"b {r - k:.1f} {h:.1f} 0 {h - r + k:.1f} 0 {h - r:.1f} "
        f"l 0 {r:.1f} "
        f"b 0 {r - k:.1f} {r - k:.1f} 0 {r:.1f} 0"
    )


def resolve_font_file(font_family):
    """Tìm đường dẫn file font TTF/OTF để PIL đo kích thước chữ chính xác."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(base_dir, "templates", "fonts")
    clean_name = font_family.replace(" ", "").lower()

    # Bảng tra cứu nhanh: font_family → file name (ưu tiên Bold cho phụ đề)
    font_map = {
        "montserrat": "Montserrat-Bold.ttf",
        "bevietnam": "BeVietnamPro-Bold.ttf",
        "bevietpro": "BeVietnamPro-Bold.ttf",
        "roboto": "Roboto-Bold.ttf",
        "notoserif": "NotoSerif-Bold.ttf",
        "notosansjp": "NotoSansJP-Bold.otf",
        "notosans": "NotoSansJP-Bold.otf",
    }

    for key, filename in font_map.items():
        if key in clean_name:
            p = os.path.join(fonts_dir, filename)
            if os.path.isfile(p):
                return p

    # Tìm fuzzy trong thư mục fonts
    if os.path.isdir(fonts_dir):
        for fname in os.listdir(fonts_dir):
            if fname.lower().endswith((".ttf", ".otf")) and clean_name in fname.replace("-", "").replace("_", "").lower():
                return os.path.join(fonts_dir, fname)

    # Fallback: Montserrat Bold hoặc Be Vietnam Pro Bold
    for fallback_name in ["Montserrat-Bold.ttf", "BeVietnamPro-Bold.ttf"]:
        fallback = os.path.join(fonts_dir, fallback_name)
        if os.path.isfile(fallback):
            return fallback
    return None


def is_cjk(text):
    """Kiểm tra xem văn bản có chứa ký tự CJK (Nhật, Trung, Hàn) không."""
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff' or '\u3040' <= ch <= '\u30ff':
            return True
    return False


def smart_wrap_text(text, max_chars=30):
    """
    Phân tách dòng phụ đề thông minh cân bằng (balanced auto-wrap):
    - Tôn trọng dấu xuống dòng thủ công (\\n).
    - Tự động tính số dòng mục tiêu và chia đều số lượng từ giữa các dòng.
    - Không ngắt lưng chừng 1 từ đơn độc ở dòng cuối (chống orphan words).
    - Với CJK: ngắt theo độ dài ký tự cân xứng.
    """
    text = text.strip()
    if not text:
        return []

    # Tôn trọng dấu xuống dòng thủ công
    if "\n" in text:
        result = []
        for line in text.split("\n"):
            result.extend(smart_wrap_text(line, max_chars))
        return result

    if len(text) <= max_chars:
        return [text]

    if is_cjk(text):
        max_cjk = max(12, int(round(max_chars * 0.52)))
        num_cjk_lines = max(2, math.ceil(len(text) / max_cjk))
        target_cjk_len = len(text) / num_cjk_lines
        lines = []
        cur = ""
        for ch in text:
            cur += ch
            if len(cur) >= int(round(target_cjk_len)) and len(lines) < num_cjk_lines - 1:
                lines.append(cur)
                cur = ""
        if cur:
            lines.append(cur)
        return lines

    words = text.split(" ")
    if len(words) <= 1:
        return [text]

    num_lines = max(2, math.ceil(len(text) / max_chars))
    target_len = len(text) / num_lines

    best_split = 1
    best_score = float("inf")

    for i in range(1, len(words)):
        p1 = " ".join(words[:i])
        p2 = " ".join(words[i:])

        # Phạt nặng nếu dòng 1 vượt quá max_chars
        penalty = 0
        if len(p1) > max_chars:
            penalty += (len(p1) - max_chars) * 100

        # Phạt nếu dòng cuối chỉ có 1 từ ngắn (orphan word)
        if i == len(words) - 1 and len(words[-1]) <= 4:
            penalty += 50

        diff_from_target = abs(len(p1) - target_len)
        score = diff_from_target + penalty

        if score < best_score:
            best_score = score
            best_split = i

    p1 = " ".join(words[:best_split])
    p2 = " ".join(words[best_split:])
    res = [p1]
    if len(p2) > max_chars:
        res.extend(smart_wrap_text(p2, max_chars))
    else:
        res.append(p2)
    return res


def measure_text_lines(lines_info, font_path, fonts_dir=None, outline_width=0.0):
    """
    lines_info: list of tuples (text, font_size)
    Đo đạc chính xác chiều rộng tối đa và tổng chiều cao dựa trên FreeType metrics (ascent + descent).
    Tự động chuyển sang NotoSansJP cho các dòng CJK để tránh lỗi zero-height glyph.
    """
    cjk_font_path = os.path.join(fonts_dir, "NotoSansJP-Bold.otf") if fonts_dir else None
    try:
        from PIL import ImageFont
        loaded_fonts = {}
        max_w = 0
        total_h = 0
        for text, fsize in lines_info:
            use_cjk = is_cjk(text) and cjk_font_path and os.path.isfile(cjk_font_path)
            fkey = (fsize, "cjk" if use_cjk else "main")
            if fkey not in loaded_fonts:
                p = cjk_font_path if use_cjk else font_path
                if p and os.path.isfile(p):
                    loaded_fonts[fkey] = ImageFont.truetype(p, fsize)
                else:
                    loaded_fonts[fkey] = ImageFont.load_default()
            font = loaded_fonts[fkey]

            if hasattr(font, "getlength"):
                lw = int(round(font.getlength(text))) + int(round(outline_width * 2))
            else:
                bbox = font.getbbox(text)
                lw = (bbox[2] - bbox[0]) + int(round(outline_width * 2))

            # Bắt buộc line-height trong ASS phải 100% khớp với line-height: 1.35 của Web CSS
            lh = int(round(fsize * 1.35))

            max_w = max(max_w, lw)
            total_h += lh
        return max_w, total_h
    except Exception:
        max_w = 0
        total_h = 0
        for text, fsize in lines_info:
            lw = int(len(text) * fsize * 0.55) + int(round(outline_width * 2))
            lh = int(fsize * 1.35)
            max_w = max(max_w, lw)
            total_h += lh
        return max_w, total_h


def generate_ass(project, output_ass_path):
    """
    Sinh file ASS hoàn chỉnh từ project dict.
    Đồng bộ tỷ lệ font chữ, màu sắc, viền chữ, ngắt dòng thông minh và hộp nền bo góc 1:1 với Web Preview.
    """
    video_meta = project.get("video", {})
    play_res_x = video_meta.get("width", 1280)
    play_res_y = video_meta.get("height", 720)

    style = project.get("style", {})
    font_name = style.get("font_family", "Be Vietnam Pro")
    font_size = int(style.get("font_size", 24))

    # Tỷ lệ co giãn theo độ phân giải gốc chuẩn 720p
    base_h = 720.0
    scale_factor = (play_res_y / base_h) if play_res_y > 0 else 1.0
    ass_font_size = max(14, int(round(font_size * scale_factor)))

    primary_col = hex_to_ass_color(style.get("primary_color", "#FFFFFF"), opacity=1.0)
    secondary_col = hex_to_ass_color(style.get("secondary_color", "#FFD700"), opacity=1.0)
    outline_col = hex_to_ass_color(style.get("outline_color", "#000000"), opacity=1.0)

    # Chuẩn hóa background_opacity (UI gửi 0 - 100)
    raw_bg_opacity = float(style.get("background_opacity", 35))
    bg_opacity = (raw_bg_opacity / 100.0) if raw_bg_opacity > 1.0 else raw_bg_opacity
    bg_col = hex_to_ass_color(style.get("background_color", "#000000"), opacity=bg_opacity)

    outline_w = float(style.get("outline_width", 2.2))
    shadow_w = float(style.get("shadow_width", 1.0))
    border_radius = float(style.get("border_radius", 8.0))
    alignment = int(style.get("alignment", 2))
    margin_l = int(style.get("margin_l", 40))
    margin_r = int(style.get("margin_r", 40))
    margin_v = int(style.get("margin_v", 45))
    line_spacing = int(round(float(style.get("line_spacing", 6)) * scale_factor))

    # Co giãn theo độ phân giải
    ass_margin_v = int(round(margin_v * scale_factor))
    ass_margin_l = int(round(margin_l * (play_res_x / 1280.0))) if play_res_x > 0 else margin_l
    ass_margin_r = int(round(margin_r * (play_res_x / 1280.0))) if play_res_x > 0 else margin_r
    ass_outline_w = max(0.5, round(outline_w * scale_factor, 1))
    ass_shadow_w = max(0.0, round(shadow_w * scale_factor, 1))
    ass_border_radius = max(0.0, round(border_radius * scale_factor, 1))

    # Khoảng đệm hộp (Padding): Không hardcode tỷ lệ, dùng giá trị pixel người dùng đặt (hoặc default)
    custom_pad = style.get("box_padding")
    if custom_pad is not None:
        pad_x = int(round(float(custom_pad) * scale_factor))
        pad_y = int(round(float(custom_pad) * 0.6 * scale_factor)) # Y thường nhỏ hơn X
    else:
        pad_x = int(round(ass_font_size * 0.5 * scale_factor))
        pad_y = int(round(ass_font_size * 0.3 * scale_factor))

    # Giới hạn số ký tự trên 1 dòng để tự động xuống hàng cân đối
    # Nâng tỷ lệ chiếm ngang của chữ lên 85% video để tránh chữ rớt thành 2 hàng trên Web
    # nhưng bị 1 hàng trên Video do chênh lệch khung hiển thị.
    target_text_width = (play_res_x - ass_margin_l - ass_margin_r) * 0.85
    avg_char_w = ass_font_size * 0.58
    max_chars = max(24, min(42, int(round(target_text_width / avg_char_w))))
    max_cjk_chars = max(12, min(24, int(round(max_chars * 0.52))))

    has_box = bg_opacity > 0.05
    mode = style.get("mode", "bilingual")
    bilingual_order = style.get("bilingual_order", "target_top")
    sub_font_size = max(12, int(round(ass_font_size * 0.8)))

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(base_dir, "templates", "fonts")
    font_path = resolve_font_file(font_name)

    lines = []
    lines.append("[Script Info]")
    lines.append("Title: AI Workforce Generated Subtitles")
    lines.append("ScriptType: v4.00+")
    lines.append("WrapStyle: 0")
    lines.append("ScaledBorderAndShadow: yes")
    lines.append(f"PlayResX: {play_res_x}")
    lines.append(f"PlayResY: {play_res_y}")
    lines.append("")

    lines.append("[V4+ Styles]")
    lines.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding")

    if has_box:
        # Layer 0: BgBox vẽ vector hình chữ nhật bo góc với fill bg_col (Alignment 7 Top-Left)
        # Layer 1: TextStyle vẽ text sắc nét với căn giữa tuyệt đối Alignment 5 (Middle-Center)
        lines.append(f"Style: BgBox,Arial,10,{bg_col},{bg_col},&HFF000000&,&HFF000000&,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1")
        lines.append(f"Style: TextStyle,{font_name},{ass_font_size},{primary_col},{secondary_col},{outline_col},&HFF000000&,1,0,0,0,100,100,0,0,1,{ass_outline_w},{ass_shadow_w},5,0,0,0,1")
    else:
        lines.append(f"Style: Default,{font_name},{ass_font_size},{primary_col},{secondary_col},{outline_col},&H80000000&,1,0,0,0,100,100,0,0,1,{ass_outline_w},{ass_shadow_w},{alignment},{ass_margin_l},{ass_margin_r},{ass_margin_v},1")

    lines.append("")
    lines.append("[Events]")
    lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")

    segments = project.get("segments", [])
    for seg in segments:
        start_time = format_ass_time(seg["start"])
        end_time = format_ass_time(seg["end"])

        src_text = seg.get("source_text", "").strip()
        trans_text = seg.get("translated_text", "").strip()

        lines_info = []
        if mode == "bilingual" and src_text and trans_text and src_text != trans_text:
            first_raw = trans_text if bilingual_order == "target_top" else src_text
            second_raw = src_text if bilingual_order == "target_top" else trans_text
            first_is_cjk = is_cjk(first_raw)
            second_is_cjk = is_cjk(second_raw)

            first_lines = smart_wrap_text(first_raw, max_cjk_chars if first_is_cjk else max_chars)
            second_lines = smart_wrap_text(second_raw, max_cjk_chars if second_is_cjk else max_chars)

            for subline in first_lines:
                lines_info.append((subline.strip(), ass_font_size))
            for subline in second_lines:
                lines_info.append((subline.strip(), sub_font_size))

            first_formatted = r"\N".join(first_lines)
            if first_is_cjk:
                first_formatted = f"{{\\fnNoto Sans JP}}{first_formatted}"

            second_formatted = r"\N".join(second_lines)
            if second_is_cjk:
                second_tag = f"{{\\fs{sub_font_size}\\fnNoto Sans JP\\c{secondary_col}}}"
            else:
                second_tag = f"{{\\fs{sub_font_size}\\c{secondary_col}}}"

            formatted_text = f"{first_formatted}\\N{second_tag}{second_formatted}"

        elif mode == "source_only":
            raw_text = src_text
            text_is_cjk = is_cjk(raw_text)
            text_lines = smart_wrap_text(raw_text, max_cjk_chars if text_is_cjk else max_chars)
            for subline in text_lines:
                lines_info.append((subline.strip(), ass_font_size))
            formatted_text = r"\N".join(text_lines)
            if text_is_cjk:
                formatted_text = f"{{\\fnNoto Sans JP}}{formatted_text}"
        else:
            # Monolingual: Target (câu dịch)
            raw_text = trans_text if trans_text else src_text
            text_is_cjk = is_cjk(raw_text)
            text_lines = smart_wrap_text(raw_text, max_cjk_chars if text_is_cjk else max_chars)
            for subline in text_lines:
                lines_info.append((subline.strip(), ass_font_size))
            formatted_text = r"\N".join(text_lines)
            if text_is_cjk:
                formatted_text = f"{{\\fnNoto Sans JP}}{formatted_text}"

        if not lines_info:
            continue

        if has_box:
            max_w, total_h = measure_text_lines(lines_info, font_path, fonts_dir, ass_outline_w)
            if len(lines_info) > 1:
                total_h += line_spacing * (len(lines_info) - 1)

            box_w = max_w + pad_x * 2
            box_h = total_h + pad_y * 2

            # Tính toạ độ box theo alignment
            if alignment in (1, 4, 7):
                box_x = ass_margin_l
            elif alignment in (3, 6, 9):
                box_x = play_res_x - ass_margin_r - box_w
            else:
                box_x = int(round((play_res_x - box_w) / 2.0))

            if alignment in (7, 8, 9):
                box_y = ass_margin_v
            elif alignment in (4, 5, 6):
                box_y = int(round((play_res_y - box_h) / 2.0))
            else:
                # Bottom alignment (1, 2, 3)
                box_y = int(round(play_res_y - ass_margin_v - box_h))

            # Tâm của hộp và chữ: căn giữa tuyệt đối theo 2 trục
            center_x = box_x + int(round(box_w / 2.0))
            center_y = box_y + int(round(box_h / 2.0))

            box_path = make_rounded_rect_path(box_w, box_h, ass_border_radius)
            lines.append(f"Dialogue: 0,{start_time},{end_time},BgBox,,0,0,0,,{{\\pos({box_x},{box_y})\\p1}}{box_path}{{\\p0}}")
            lines.append(f"Dialogue: 1,{start_time},{end_time},TextStyle,,0,0,0,,{{\\an5\\pos({center_x},{center_y})}}{formatted_text}")
        else:
            lines.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{formatted_text}")

    os.makedirs(os.path.dirname(os.path.abspath(output_ass_path)), exist_ok=True)
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return output_ass_path


def generate_srt(project, output_srt_path):
    """
    Sinh file SRT chuẩn SubRip từ project dict kèm ngắt dòng thông minh cân xứng.
    """
    video_meta = project.get("video", {})
    play_res_x = video_meta.get("width", 1280)
    style = project.get("style", {})
    font_size = int(style.get("font_size", 24))
    margin_l = int(style.get("margin_l", 40))
    margin_r = int(style.get("margin_r", 40))

    target_text_width = (play_res_x - margin_l - margin_r) * 0.85
    avg_char_w = font_size * 0.58
    max_chars = max(24, min(42, int(round(target_text_width / avg_char_w))))
    max_cjk_chars = max(12, min(24, int(round(max_chars * 0.52))))

    mode = style.get("mode", "bilingual")
    bilingual_order = style.get("bilingual_order", "target_top")

    segments = project.get("segments", [])
    lines = []

    for idx, seg in enumerate(segments, 1):
        start_time = format_srt_time(seg["start"])
        end_time = format_srt_time(seg["end"])

        src_text = seg.get("source_text", "").strip()
        trans_text = seg.get("translated_text", "").strip()

        if mode == "bilingual" and src_text and trans_text and src_text != trans_text:
            first_raw = trans_text if bilingual_order == "target_top" else src_text
            second_raw = src_text if bilingual_order == "target_top" else trans_text

            first_lines = smart_wrap_text(first_raw, max_cjk_chars if is_cjk(first_raw) else max_chars)
            second_lines = smart_wrap_text(second_raw, max_cjk_chars if is_cjk(second_raw) else max_chars)

            first_block = "\n".join(first_lines)
            second_block = "\n".join(second_lines)
            text_block = f"{first_block}\n{second_block}"
        elif mode == "source_only":
            lines_wrap = smart_wrap_text(src_text, max_cjk_chars if is_cjk(src_text) else max_chars)
            text_block = "\n".join(lines_wrap)
        else:
            final_raw = trans_text if trans_text else src_text
            lines_wrap = smart_wrap_text(final_raw, max_cjk_chars if is_cjk(final_raw) else max_chars)
            text_block = "\n".join(lines_wrap)

        lines.append(str(idx))
        lines.append(f"{start_time} --> {end_time}")
        lines.append(text_block)
        lines.append("")

    os.makedirs(os.path.dirname(os.path.abspath(output_srt_path)), exist_ok=True)
    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_srt_path


def main():
    parser = argparse.ArgumentParser(description="Sinh file phụ đề ASS và SRT từ project.json.")
    parser.add_argument("--project", "-p", required=True, help="Đường dẫn file project.json")
    parser.add_argument("--output-ass", help="Đường dẫn file .ass xuất ra")
    parser.add_argument("--output-srt", help="Đường dẫn file .srt xuất ra")

    args = parser.parse_args()

    if not os.path.isfile(args.project):
        print(f"❌ File không tồn tại: {args.project}", file=sys.stderr)
        return 1

    try:
        with open(args.project, "r", encoding="utf-8") as f:
            proj = json.load(f)

        if args.output_ass:
            generate_ass(proj, args.output_ass)
            print(f"✅ Đã sinh file ASS: {args.output_ass}")

        if args.output_srt:
            generate_srt(proj, args.output_srt)
            print(f"✅ Đã sinh file SRT: {args.output_srt}")

        return 0
    except Exception as e:
        print(f"❌ Lỗi khi sinh phụ đề: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
