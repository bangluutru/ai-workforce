#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_batch.py — Tổng hợp NHIỀU câu bằng VieNeu-TTS v3 Turbo (48 kHz, offline) trong MỘT tiến trình.

Chạy bằng Python của venv có gói `vieneu` (.venv hoặc .venv-tts), KHÔNG phải python hệ thống:
    <venv>/bin/python tts_batch.py jobs.json
jobs.json = {"voice": "Thùy Dung", "items": [{"key": "...", "text": "...", "out": "/abs.wav", "temperature": 0.65}]}
In ra JSON: {"voice": "<giọng thực dùng>", "results": [{"key", "out", "dur", "ok", "error"}]}
Nạp mô hình một lần (~7 s) thay vì mỗi câu một lần.
"""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")


def main():
    jobs = json.load(open(sys.argv[1], encoding="utf-8"))
    import soundfile as sf
    from vieneu import Vieneu
    tts = Vieneu()
    voice = jobs.get("voice")
    try:
        resolved = tts.resolve_voice_name(voice) if voice else None
    except Exception:
        resolved = None
    if not resolved:                                    # giọng không tồn tại → giọng mặc định theo giới tính
        presets = getattr(tts, "_preset_voices", {})   # {tên: {"gender", "region", ...}} theo thứ tự đề cử
        want = jobs.get("gender", "female")
        resolved = next((n for n, v in presets.items() if isinstance(v, dict) and v.get("gender") == want), None)
    out = {"voice": resolved, "results": []}
    for it in jobs["items"]:
        try:
            w = tts.infer(it["text"], voice=resolved, temperature=float(it.get("temperature", 0.65)))
            os.makedirs(os.path.dirname(it["out"]), exist_ok=True)
            sf.write(it["out"], w, getattr(tts, "sample_rate", 48000))
            out["results"].append({"key": it["key"], "out": it["out"], "dur": round(len(w) / getattr(tts, "sample_rate", 48000), 3), "ok": True})
        except Exception as e:                          # một câu lỗi không làm hỏng cả lô
            out["results"].append({"key": it["key"], "out": it["out"], "ok": False, "error": str(e)[:300]})
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
