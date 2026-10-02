#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
semantic_segmenter.py — Phân đoạn phụ đề theo câu, chuẩn broadcast (Netflix-like).

Thuật toán (thay cho cách "đầy 42 ký tự thì cắt" cũ):
  1. Gom từ thành CÂU (dấu kết câu hoặc khoảng lặng dài).
  2. Câu vừa một phụ đề (≤ max_lines × CPL ký tự, ≤ max_duration) → giữ nguyên.
     Câu dài → chia đệ quy tại điểm ngắt ngữ pháp rẻ nhất (linebreak.break_cost):
     sau dấu câu, trước liên từ, tại khoảng lặng; không treo từ chức năng; cân bằng hai nửa.
  3. Gộp mảnh mồ côi (< min_duration hoặc quá ngắn) vào phụ đề kề bên nếu còn vừa.
  4. Thời gian đọc: kéo dài end để đạt min_duration / CPS mục tiêu, thêm "linger" sau lời nói,
     khép khoảng hở < 0.5 s còn 2 frame (chống chớp), không bao giờ chồng lấn phụ đề sau.
Tham số mặc định: Latin 42 CPL × 2 dòng, CJK 16 × 2, 1.0–6.0 s, ≤ 17 CPS (vi/en), ≤ 7 CPS (ja).
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from linebreak import MAJOR_PUNCT, best_wrap, break_cost, is_cjk, join_tokens, lang_of  # noqa: E402

FRAME_GAP = 0.083        # 2 frame @ 24 fps: khoảng nghỉ tối thiểu giữa hai phụ đề liền nhau
LINGER = 0.5             # giữ phụ đề thêm sau khi người nói dứt câu (nếu còn chỗ)
CLOSE_GAP = 0.5          # khoảng hở nhỏ hơn mức này bị khép lại (tránh chớp tắt)


def flatten_words(raw_segments):
    words = []
    for s in raw_segments:
        ws = [w for w in s.get("words", []) if str(w.get("word", "")).strip()]
        if ws:
            words.extend({**w, "word": str(w["word"]).strip()} for w in ws)
            continue
        text = s.get("text", "").strip()                    # không có word timestamps: chia đều
        toks = list(text) if is_cjk(text) else text.split()
        if toks:
            dur = max(0.2, s.get("end", 0) - s.get("start", 0)); step = dur / len(toks)
            for i, t in enumerate(toks):
                words.append({"word": t, "start": round(s["start"] + i * step, 3), "end": round(s["start"] + (i + 1) * step, 3), "probability": 1.0})
    return words


def sentences_of(words, long_pause=1.2):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt is None or MAJOR_PUNCT.search(w["word"]) or nxt["start"] - w["end"] >= long_pause:
            out.append(cur); cur = []
    return out


def split_sentence(ws, cfg):
    cjk = cfg["cjk"]; text = join_tokens([w["word"] for w in ws], cjk)
    dur = ws[-1]["end"] - ws[0]["start"]
    fits = len(text) <= cfg["max_chars"] and dur <= cfg["max_duration"]
    if fits and len(text) > cfg["cpl"]:
        fits = best_wrap(text, cfg["cpl"])[1] < 5.5        # chỉ "vừa" nếu ngắt được 2 dòng tại ranh giới thật
    if fits or len(ws) < 2:
        return [ws]
    best, best_i = None, 1
    for i in range(1, len(ws)):
        a, b = join_tokens([w["word"] for w in ws[:i]], cjk), join_tokens([w["word"] for w in ws[i:]], cjk)
        gap = ws[i]["start"] - ws[i - 1]["end"]
        left, right = (a[-8:], b[:8]) if cjk else (ws[i - 1]["word"], ws[i]["word"])
        cost = break_cost(left, right, gap, cfg["lang"])
        cost += abs(len(a) - len(b)) / max(1, len(text)) * 5                 # cân bằng
        short = cfg["max_chars"] * 0.22                                       # mảnh quá ngắn = mồ côi
        cost += 6 if len(a) < short else 0
        cost += 6 if len(b) < short else 0
        if best is None or cost < best:
            best, best_i = cost, i
    return split_sentence(ws[:best_i], cfg) + split_sentence(ws[best_i:], cfg)


def merge_orphans(chunks, cfg):
    def size(c):
        return len(join_tokens([w["word"] for w in c], cfg["cjk"]))
    changed = True
    while changed:
        changed = False
        for i, c in enumerate(chunks):
            d = c[-1]["end"] - c[0]["start"]
            if d >= cfg["min_duration"] and size(c) >= cfg["max_chars"] * 0.18:
                continue
            options = []
            for j in (i - 1, i + 1):
                if 0 <= j < len(chunks):
                    m = chunks[min(i, j)] + chunks[max(i, j)]
                    gap = chunks[max(i, j)][0]["start"] - chunks[min(i, j)][-1]["end"]
                    if size(m) <= cfg["max_chars"] * 1.15 and m[-1]["end"] - m[0]["start"] <= cfg["max_duration"] + 1.0 and gap < 1.0:
                        options.append((gap, j, m))
            if options:
                _, j, m = min(options, key=lambda o: o[0])
                lo = min(i, j); chunks[lo:lo + 2] = [m]; changed = True
                break
    return chunks


def build_segments(chunks, cfg):
    segs = []
    for ws in chunks:
        text = join_tokens([w["word"] for w in ws], cfg["cjk"])
        low = [w["word"] for w in ws if w.get("probability", 1.0) < 0.6]
        segs.append({"start": ws[0]["start"], "end": ws[-1]["end"], "speech_end": ws[-1]["end"], "source_text": text,
                     "translated_text": text, "words": ws,
                     "confidence": round(sum(w.get("probability", 1.0) for w in ws) / len(ws), 2), "low_confidence_words": low})
    return retime(segs, cfg)


def make_cfg(lang, max_cpl=42, max_lines=2, max_duration=6.0, min_duration=1.0, max_cps=None, sample=""):
    cjk = lang in ("ja", "zh", "ko") or is_cjk(sample)
    cpl = min(max_cpl, 16) if cjk else max_cpl
    return {"lang": "ja" if cjk else (lang or lang_of(sample)), "cjk": cjk, "cpl": cpl, "max_chars": cpl * max_lines,
            "max_duration": max_duration, "min_duration": min_duration, "max_cps": max_cps or (7.0 if cjk else 17.0)}


def retime(segs, cfg):
    """Đặt start/end theo word timestamps + thời gian đọc. Gọi lại sau mọi thao tác đổi ranh giới."""
    for s in segs:
        if s.get("words"):
            s["start"] = s["words"][0]["start"]; s["speech_end"] = s["words"][-1]["end"]
        s.setdefault("speech_end", s["end"]); s["end"] = s["speech_end"]
    for i, s in enumerate(segs):
        nxt = segs[i + 1]["start"] if i + 1 < len(segs) else s["end"] + 10
        limit = nxt - FRAME_GAP
        shown = max(len(s.get("source_text", "")), len(s.get("translated_text", "")))   # phụ đề dịch thường dài hơn
        need = max(cfg["min_duration"], shown / cfg["max_cps"])
        end = max(s["end"], s["start"] + need, s["end"] + LINGER)
        if 0 < nxt - end < CLOSE_GAP:
            end = limit
        s["end"] = round(max(s["speech_end"], min(end, limit)), 3)
        s["start"] = round(s["start"], 3)
    for idx, s in enumerate(segs, 1):
        dur = max(0.01, s["end"] - s["start"])
        s.update({"id": f"seg_{idx:03d}", "duration": round(dur, 2), "cps": round(len(s["source_text"]) / dur, 1), "cpl": len(s["source_text"])})
    return segs


def semantic_chunk_words(raw_segments, max_cpl=42, max_duration=6.0, min_duration=1.0, max_cps=None, max_lines=2, lang=None, **_):
    words = flatten_words(raw_segments)
    if not words:
        return []
    sample = join_tokens([w["word"] for w in words[:200]])
    cfg = make_cfg(lang or lang_of(sample), max_cpl, max_lines, max_duration, min_duration, max_cps, sample)
    chunks = []
    for sent in sentences_of(words):
        chunks.extend(split_sentence(sent, cfg))
    return build_segments(merge_orphans(chunks, cfg), cfg)


def main():
    p = argparse.ArgumentParser(description="Phân đoạn phụ đề theo câu từ raw_transcript.json (word timestamps).")
    p.add_argument("--input", "-i", required=True, help="raw_transcript.json")
    p.add_argument("--output", "-o", required=True, help="segmented_subtitles.json")
    p.add_argument("--max-cpl", type=int, default=42, help="Ký tự tối đa mỗi dòng (Latin, mặc định 42; CJK tự dùng 16)")
    p.add_argument("--max-lines", type=int, default=2, help="Số dòng tối đa mỗi phụ đề (2 cho đơn ngữ, 1 cho song ngữ)")
    p.add_argument("--max-duration", type=float, default=6.0)
    p.add_argument("--min-duration", type=float, default=1.0)
    p.add_argument("--max-cps", type=float, default=None, help="Tốc độ đọc mục tiêu (mặc định 17 Latin / 7 CJK)")
    p.add_argument("--language", default=None, help="vi | en | ja ... (mặc định: lấy từ transcript)")
    a = p.parse_args()
    if not os.path.isfile(a.input):
        print(f"❌ File không tồn tại: {a.input}", file=sys.stderr); return 1
    data = json.load(open(a.input, encoding="utf-8"))
    lang = a.language or data.get("detected_language")
    segs = semantic_chunk_words(data.get("segments", []), max_cpl=a.max_cpl, max_duration=a.max_duration, min_duration=a.min_duration,
                                max_cps=a.max_cps, max_lines=a.max_lines, lang=lang)
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    json.dump({"source_language": lang or "auto", "total_segments": len(segs), "segments": segs}, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ {len(segs)} phụ đề (≤ {a.max_lines} dòng): {a.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
