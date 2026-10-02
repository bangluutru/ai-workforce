#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transcribe_align.py — Nhận dạng giọng nói và trích xuất word-level timestamps.
Sử dụng faster-whisper (offline, hỗ trợ VAD và trích xuất thời gian từng từ).
"""

import argparse
import json
import os
import sys


def transcribe_audio(audio_path, model_size="large-v3-turbo", language=None, device="auto", compute_type="auto", glossary=None):
    """
    Nhận dạng audio và trích xuất word-level timestamps bằng faster-whisper.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("Chưa cài đặt 'faster-whisper'. Vui lòng chạy: pip install faster-whisper")

    # Tự động chọn device và compute_type tối ưu
    if device == "auto":
        # Trên Apple Silicon / CPU standard:
        device = "cpu"
        if compute_type == "auto":
            compute_type = "int8"
    elif compute_type == "auto":
        compute_type = "float16" if device == "cuda" else "int8"

    print(f"🤖 Đang nạp mô hình Whisper ({model_size}) trên thiết bị: {device} ({compute_type})...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type, cpu_threads=max(4, (os.cpu_count() or 8) - 2))

    print(f"🎙️ Đang nhận dạng giọng nói & trích xuất word-level timestamps...")
    segments_gen, info = model.transcribe(
        audio_path,
        language=language,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400),
        word_timestamps=True,
        beam_size=5,
        # Không mồi bằng câu trước: tránh vòng lặp lặp-lại-câu (hallucination) trên video dài
        condition_on_previous_text=False,
        # Glossary: tên riêng / thuật ngữ / cách viết đúng ("eTax Mobile, định danh, 定款") — giảm mạnh lỗi thuật ngữ
        initial_prompt=glossary or None,
        hotwords=glossary or None,
    )

    detected_lang = info.language
    lang_prob = round(info.language_probability, 2)
    print(f"  Ngôn ngữ phát hiện: {detected_lang} (độ tin cậy: {lang_prob * 100}%)")

    raw_segments = []
    total_words = 0

    for idx, seg in enumerate(segments_gen):
        words_list = []
        if hasattr(seg, "words") and seg.words:
            for w in seg.words:
                words_list.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 2),
                    "end": round(w.end, 2),
                    "probability": round(getattr(w, "probability", 1.0), 3),
                })
                total_words += 1

        raw_segments.append({
            "id": idx,
            "seek": getattr(seg, "seek", 0),
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
            "words": words_list,
            "avg_logprob": round(getattr(seg, "avg_logprob", 0.0), 3),
        })

    print(f"  ✅ Đã nhận dạng xong: {len(raw_segments)} phân đoạn, {total_words} từ.")

    return {
        "audio_path": os.path.abspath(audio_path),
        "detected_language": detected_lang,
        "language_probability": lang_prob,
        "model": model_size,
        "glossary": glossary or "",
        "segments": raw_segments,
    }


def main():
    parser = argparse.ArgumentParser(description="Chạy Whisper STT và trích xuất word-level timestamps.")
    parser.add_argument("--audio", "-a", required=True, help="Đường dẫn file audio .wav")
    parser.add_argument("--output", "-o", required=True, help="Đường dẫn file raw_transcript.json đầu ra")
    parser.add_argument("--model", "-m", default="large-v3-turbo",
                        help="large-v3-turbo (mặc định: chính xác, ~0.5× thời gian thực trên Apple Silicon) | large-v3 (chậm hơn ~3×) | small/base (CHỈ để thử nhanh: sai nhiều với tiếng Việt/Nhật)")
    parser.add_argument("--glossary", "-g", default=None,
                        help="Tên riêng, thuật ngữ, cách viết đúng, cách nhau dấu phẩy. Ví dụ: \"eTax Mobile, định danh điện tử, giảm trừ gia cảnh\"")
    parser.add_argument("--language", "-l", default=None, help="Mã ngôn ngữ (vi, en, ja...) hoặc để trống để tự phát hiện")
    parser.add_argument("--device", "-d", default="auto", help="Thiết bị tính toán (auto, cpu, cuda)")

    args = parser.parse_args()

    if not os.path.isfile(args.audio):
        print(f"❌ File audio không tồn tại: {args.audio}", file=sys.stderr)
        return 1

    try:
        data = transcribe_audio(
            args.audio,
            model_size=args.model,
            language=args.language,
            device=args.device,
            glossary=args.glossary,
        )

        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 Đã lưu kết quả raw transcript vào: {args.output}")
        return 0
    except Exception as e:
        print(f"❌ Lỗi khi nhận dạng: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
