#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
semantic_segmenter.py — Phân đoạn phụ đề ngữ nghĩa thông minh.
Kế thừa logic phân đoạn tự nhiên từ VideoLingo & Anchor Sub Sync:
Tuân thủ chuẩn CPL (Characters Per Line), CPS (Characters Per Second),
khoảng lặng giọng nói (speech pauses) và ranh giới cú pháp/dấu câu.
"""

import argparse
import json
import os
import re
import sys


def is_cjk(text):
    """Kiểm tra xem văn bản có phải ngôn ngữ CJK (Trung, Nhật, Hàn) không."""
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff' or '\u3040' <= ch <= '\u30ff':
            return True
    return False


def semantic_chunk_words(raw_segments, max_cpl=42, max_duration=5.0, min_duration=0.8, max_cps=21.0, pause_threshold=0.45):
    """
    Nhóm danh sách từ word-level thành các phân đoạn phụ đề tự nhiên, dễ đọc.
    """
    # 1. Thu thập toàn bộ danh sách từ phẳng kèm thời gian
    flat_words = []
    for s in raw_segments:
        words = s.get("words", [])
        if words:
            flat_words.extend(words)
        else:
            # Nếu phân đoạn không có word-level timestamps (fallback)
            text = s.get("text", "").strip()
            if text:
                w_tokens = text.split()
                if w_tokens:
                    dur = max(0.2, s.get("end", 0) - s.get("start", 0))
                    step = dur / len(w_tokens)
                    for i, tok in enumerate(w_tokens):
                        w_start = s.get("start", 0) + i * step
                        w_end = w_start + step
                        flat_words.append({
                            "word": tok,
                            "start": round(w_start, 2),
                            "end": round(w_end, 2),
                            "probability": 1.0,
                        })

    if not flat_words:
        return []

    # 2. Thuật toán gom cụm phụ đề
    chunks = []
    current_words = []

    def flush_chunk():
        nonlocal current_words
        if not current_words:
            return
        
        # Ghép chữ: CJK không chèn dấu cách, Latin chèn dấu cách
        sample_text = "".join(w["word"] for w in current_words)
        if is_cjk(sample_text):
            clean_text = sample_text.strip()
        else:
            raw_text = " ".join(w["word"] for w in current_words).strip()
            clean_text = re.sub(r'\s+([,.:;?!])', r'\1', raw_text)
        
        c_start = current_words[0]["start"]
        c_end = current_words[-1]["end"]
        dur = max(0.1, c_end - c_start)
        cps = round(len(clean_text) / dur, 1)

        chunks.append({
            "start": round(c_start, 2),
            "end": round(c_end, 2),
            "source_text": clean_text,
            "translated_text": clean_text,
            "words": list(current_words),
            "duration": round(dur, 2),
            "cps": cps,
            "cpl": len(clean_text),
            "confidence": round(sum(w.get("probability", 1.0) for w in current_words) / len(current_words), 2),
        })
        current_words = []

    for i, w in enumerate(flat_words):
        current_words.append(w)
        sample_cat = "".join(item["word"] for item in current_words)
        is_cur_cjk = is_cjk(sample_cat)
        cur_text = sample_cat if is_cur_cjk else " ".join(item["word"] for item in current_words)
        cur_dur = w["end"] - current_words[0]["start"]

        has_next = i + 1 < len(flat_words)
        next_w = flat_words[i + 1] if has_next else None

        # Ràng buộc CPL theo ngôn ngữ (CJK ~ 22 ký tự, Latin ~ 42 ký tự)
        effective_max_cpl = 22 if is_cur_cjk else max_cpl

        # Kiểm tra điều kiện cắt phân đoạn:
        should_split = False

        if not has_next:
            should_split = True
        else:
            gap = next_w["start"] - w["end"]
            ends_with_major_punct = bool(re.search(r'[.!?。！？]$', w["word"].strip()))
            ends_with_minor_punct = bool(re.search(r'[,:;、，]$', w["word"].strip()))

            # Điều kiện 1: Dấu câu kết thúc câu lớn (. ! ? 。 ！) và độ dài tối thiểu
            if ends_with_major_punct and cur_dur >= min_duration:
                should_split = True
            # Điều kiện 2: Khoảng lặng đáng kể trong giọng nói (speech pause)
            elif gap >= pause_threshold and cur_dur >= min_duration:
                should_split = True
            # Điều kiện 3: Vượt quá thời lượng tối đa cho 1 phụ đề
            elif cur_dur >= max_duration:
                should_split = True
            # Điều kiện 4: Dấu phẩy kèm độ dài đã đạt ngưỡng thoải mái
            elif ends_with_minor_punct and (len(cur_text) >= effective_max_cpl * 0.7 or cur_dur >= 2.5):
                should_split = True
            # Điều kiện 5: Độ dài ký tự vượt quá CPL và từ kế tiếp sẽ làm tràn dòng
            elif len(cur_text) + len(next_w["word"]) > effective_max_cpl and cur_dur >= min_duration:
                should_split = True

        if should_split:
            flush_chunk()

    # Post-processing: Gán ID ổn định (seg_001, seg_002, ...)
    final_segments = []
    for idx, c in enumerate(chunks, 1):
        seg_id = f"seg_{idx:03d}"
        c["id"] = seg_id
        final_segments.append(c)

    return final_segments


def main():
    parser = argparse.ArgumentParser(description="Phân đoạn phụ đề ngữ nghĩa từ raw transcript.")
    parser.add_argument("--input", "-i", required=True, help="Đường dẫn file raw_transcript.json")
    parser.add_argument("--output", "-o", required=True, help="Đường dẫn file segmented_subtitles.json")
    parser.add_argument("--max-cpl", type=int, default=42, help="Ký tự tối đa một dòng (mặc định 42)")
    parser.add_argument("--max-duration", type=float, default=5.0, help="Thời lượng tối đa một phân đoạn (giây)")
    parser.add_argument("--min-duration", type=float, default=0.8, help="Thời lượng tối thiểu một phân đoạn (giây)")

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"❌ File không tồn tại: {args.input}", file=sys.stderr)
        return 1

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_segs = data.get("segments", [])
        print(f"✂️  Đang phân đoạn {len(raw_segs)} raw segments theo ngữ nghĩa CPL={args.max_cpl}...")

        segmented = semantic_chunk_words(
            raw_segs,
            max_cpl=args.max_cpl,
            max_duration=args.max_duration,
            min_duration=args.min_duration,
        )

        output_data = {
            "source_language": data.get("detected_language", "vi"),
            "total_segments": len(segmented),
            "segments": segmented,
        }

        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Đã tạo thành công {len(segmented)} phân đoạn phụ đề chuẩn ngữ nghĩa: {args.output}")
        return 0
    except Exception as e:
        print(f"❌ Lỗi khi phân đoạn: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
