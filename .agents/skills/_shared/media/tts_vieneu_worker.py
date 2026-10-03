#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_vieneu_worker.py — Tổng hợp NHIỀU câu bằng VieNeu-TTS v3 Turbo (48 kHz, offline) trong MỘT tiến trình.

Chạy bằng Python của venv có gói `vieneu` (.venv hoặc .venv-tts), được gọi bởi tts.py:
    <venv>/bin/python tts_vieneu_worker.py jobs.json
jobs.json = {"voice": "Thùy Dung", "gender": "female", "ref_audio": null | "/mau.wav",
             "items": [{"key": "...", "text": "...", "out": "/abs.wav", "temperature": 0.65}]}
In ra JSON: {"voice": "<giọng thực dùng>", "results": [{"key", "out", "dur", "ok", "error"}]}
Nạp mô hình một lần (~7 s) thay vì mỗi câu một lần. `ref_audio` → nhân bản giọng từ file mẫu.
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
    from vieneu import Vieneu
    tts = Vieneu()
    sr = getattr(tts, "sample_rate", 48000)
    ref = jobs.get("ref_audio")
    voice = jobs.get("voice")
    resolved = None
    if not ref:
        if voice:
            try:
                resolved = tts.resolve_voice_name(voice)
            except Exception as e:                      # kiểu lỗi của resolve_voice_name không được tài liệu hoá → ghi log, không nuốt
                print(f"⚠️ Giọng '{voice}' không có trong VieNeu ({e}) → dùng giọng mặc định theo giới tính", file=sys.stderr)
        if not resolved:                                    # giọng không tồn tại → giọng mặc định theo giới tính
            presets = getattr(tts, "_preset_voices", {})   # {tên: {"gender", "region", ...}} theo thứ tự đề cử
            want = jobs.get("gender", "female")
            resolved = next((n for n, v in presets.items() if isinstance(v, dict) and v.get("gender") == want), None)
    out = {"voice": resolved if not ref else f"clone:{os.path.basename(ref)}", "results": []}
    for it in jobs["items"]:
        try:
            temp = float(it.get("temperature", 0.65))
            w = tts.infer(it["text"], ref_audio=ref, temperature=temp) if ref else tts.infer(it["text"], voice=resolved, temperature=temp)
            os.makedirs(os.path.dirname(os.path.abspath(it["out"])), exist_ok=True)
            sf.write(it["out"], w, sr)
            out["results"].append({"key": it["key"], "out": it["out"], "dur": round(len(w) / sr, 3), "ok": True})
        except Exception as e:                          # một câu lỗi không làm hỏng cả lô; lỗi được trả về cho caller
            out["results"].append({"key": it["key"], "out": it["out"], "ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}"})
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
