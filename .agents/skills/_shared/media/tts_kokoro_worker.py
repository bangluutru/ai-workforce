#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_kokoro_worker.py — Tổng hợp NHIỀU câu bằng Kokoro ONNX v1.0 trong MỘT tiến trình (offline).

Chạy bằng Python của venv có `kokoro-onnx` (thường .venv-tts); được gọi bởi tts.py:
    <venv>/bin/python tts_kokoro_worker.py jobs.json
jobs.json = {"voice": "af_heart", "lang": "en-us"|"en-gb"|"ja", "speed": 1.0, "model": "...onnx", "voices": "...bin",
             "items": [{"key": "...", "text": "...", "out": "/abs.wav"}]}
In ra JSON: {"voice": "...", "results": [{"key", "out", "dur", "ok", "error"}]}
Tiếng Nhật: chữ Hán/Kana → phoneme bằng misaki[ja] (espeak-ng đọc sai chữ Hán), rồi create(..., is_phonemes=True).
"""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        jobs = json.load(f)
    import soundfile as sf
    from kokoro_onnx import Kokoro

    kokoro = Kokoro(jobs["model"], jobs["voices"])
    voice, lang, speed = jobs["voice"], jobs.get("lang", "en-us"), float(jobs.get("speed", 1.0))
    g2p = None
    g2p_error = None
    if lang == "ja":
        try:
            from misaki import ja
            g2p = ja.JAG2P()
        except ImportError as e:
            g2p_error = f"Thiếu G2P tiếng Nhật misaki[ja] ({e}). Chạy: bash scripts/auto-setup.sh"
    out = {"voice": voice, "results": []}
    for it in jobs["items"]:
        try:
            if lang == "ja":
                if g2p is None:
                    raise RuntimeError(g2p_error)
                ph = g2p(it["text"])
                ph = ph[0] if isinstance(ph, tuple) else ph
                samples, sr = kokoro.create(ph, voice=voice, speed=speed, lang="ja", is_phonemes=True)
            else:
                samples, sr = kokoro.create(it["text"], voice=voice, speed=speed, lang=lang)
            os.makedirs(os.path.dirname(os.path.abspath(it["out"])), exist_ok=True)
            sf.write(it["out"], samples, sr)
            out["results"].append({"key": it["key"], "out": it["out"], "dur": round(len(samples) / sr, 3), "ok": True})
        except Exception as e:                          # một câu lỗi không làm hỏng cả lô; lỗi được trả về cho caller
            out["results"].append({"key": it["key"], "out": it["out"], "ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}"})
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
