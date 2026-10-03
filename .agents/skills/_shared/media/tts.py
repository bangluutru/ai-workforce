#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts.py — Engine giọng đọc OFFLINE dùng chung (Luật R7) cho long-tieng, video-studio, phu-de.

  • Tiếng Việt  : VieNeu-TTS v3 Turbo 48 kHz (venv có gói `vieneu`), hỗ trợ nhân bản giọng từ file mẫu.
  • Tiếng Anh   : Kokoro ONNX v1.0 (Apache-2.0), giọng af_* / am_* (Mỹ), bf_* / bm_* (Anh).
  • Tiếng Nhật  : Kokoro ONNX v1.0 + G2P misaki[ja] (pyopenjtalk) → phoneme, giọng jf_* / jm_*.

KHÔNG dùng dịch vụ giọng đọc trực tuyến (vd Microsoft Edge Read Aloud) (rủi ro bản quyền — Luật R7 §4). Không API key.
Engine thiếu → báo lỗi rõ ràng kèm lệnh cài, KHÔNG lặng lẽ đổi sang engine khác.

API:
    get_voice_catalog() / get_sample_text(voice_id) / default_voice(lang, gender)
    engine_for(lang, voice)                        → "vieneu" | "kokoro"
    synthesize_batch(items, lang, voice, gender, work, speed, ref_audio, log)
        items = [{"key", "text", "out" (.wav), "temperature"?}] → {"engine", "voice", "results": [{key,out,dur,ok,error}]}
    synthesize_line(text, output_path, lang, gender, voice, speed, ref_audio) → {"success", "engine", "voice", "output_path"|"error"}
CLI:
    python3 tts.py --text "..." --output out.wav [--lang vi|en|ja] [--gender female|male] [--voice ID] [--speed 1.0] [--ref-audio f.wav]
    python3 tts.py --list-voices
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
VIENEU_WORKER = os.path.join(HERE, "tts_vieneu_worker.py")
KOKORO_WORKER = os.path.join(HERE, "tts_kokoro_worker.py")

# Model Kokoro tải bởi scripts/auto-setup.sh vào thư mục gitignored (không commit model vào repo).
KOKORO_DIR = os.environ.get("AIWF_KOKORO_DIR") or os.path.abspath(os.path.join(HERE, "..", "models", "kokoro"))
KOKORO_MODELS = ["kokoro-v1.0.onnx", "kokoro-v1.0.fp16.onnx", "kokoro-v1.0.int8.onnx"]   # ưu tiên bản đầy đủ nếu có
KOKORO_VOICES_FILE = "voices-v1.0.bin"

INSTALL_HINT = "bash scripts/auto-setup.sh (cài vieneu, kokoro-onnx, misaki[ja] vào .venv-tts và tải model Kokoro)"

# id giọng Kokoro → mã ngôn ngữ phonemizer
KOKORO_VOICES = {
    "af_heart": "en-us", "af_bella": "en-us", "af_nova": "en-us", "af_sarah": "en-us",
    "am_adam": "en-us", "am_michael": "en-us", "am_eric": "en-us",
    "bf_emma": "en-gb", "bf_isabella": "en-gb", "bm_george": "en-gb",
    "jf_alpha": "ja", "jf_gongitsune": "ja", "jf_nezumi": "ja", "jf_tebukuro": "ja", "jm_kumo": "ja",
}

DEFAULT_VOICES = {
    "vi": {"female": "Thùy Dung", "male": "Thái Sơn"},
    "en": {"female": "af_heart", "male": "am_adam"},
    "ja": {"female": "jf_alpha", "male": "jm_kumo"},
}


def _v(vid, name, lang, gender, engine, desc, region=None):
    d = {"id": vid, "name": name, "lang": lang, "gender": gender, "engine": engine, "description": desc}
    if region:
        d["region"] = region
    return d


_VN = "VieNeu 48kHz"
_KO = "Kokoro ONNX"
VOICE_CATALOG = [
    # Tiếng Việt — VieNeu-TTS v3 Turbo 48 kHz (offline)
    _v("Thùy Dung", "Thùy Dung (Nữ · Nam 48kHz)", "vi", "female", _VN, "Nữ miền Nam, phong cách tin tức, truyền cảm chuẩn studio HD", "Nam"),
    _v("Thái Sơn", "Thái Sơn (Nam · Nam 48kHz)", "vi", "male", _VN, "Nam miền Nam, kể chuyện, phóng sự, trầm ấm đĩnh đạc", "Nam"),
    _v("Trúc Ly", "Trúc Ly (Nữ · Bắc 48kHz)", "vi", "female", _VN, "Nữ miền Bắc, giọng đọc tự nhiên, dịu dàng, nhã nhặn", "Bắc"),
    _v("Mai Anh", "Mai Anh (Nữ · Bắc 48kHz)", "vi", "female", _VN, "Nữ miền Bắc, phát thanh viên thời sự, rõ ràng chuyên nghiệp", "Bắc"),
    _v("Minh Quân Pro", "Minh Quân Pro (Nam · Bắc 48kHz)", "vi", "male", _VN, "Nam miền Bắc, phong thái đĩnh đạc, tự nhiên chuẩn studio", "Bắc"),
    _v("Anh Khôi", "Anh Khôi (Nam · Bắc 48kHz)", "vi", "male", _VN, "Nam miền Bắc, phong cách kể chuyện ấm áp, truyền cảm hứng", "Bắc"),
    _v("Quang Sơn", "Quang Sơn (Nam · Trung 48kHz)", "vi", "male", _VN, "Nam miền Trung (xứ Huế/Đà Nẵng), chân chất, tự nhiên mộc mạc", "Trung"),
    _v("Ngọc Trân", "Ngọc Trân (Nữ · Trung 48kHz)", "vi", "female", _VN, "Nữ miền Trung (xứ Huế), ngọt ngào, duyên dáng và sâu lắng", "Trung"),
    _v("Adam bựa", "Adam bựa (Nam · Bắc 48kHz)", "vi", "male", _VN, "Nam miền Bắc, phong cách hài hước, dí dỏm, khẩu ngữ đời thường", "Bắc"),
    # Tiếng Anh — Kokoro ONNX (offline, Apache-2.0)
    _v("af_heart", "Heart (Nữ Mỹ · Kokoro)", "en", "female", _KO, "Nữ Mỹ biểu cảm, ấm áp, tự nhiên"),
    _v("af_bella", "Bella (Nữ Mỹ · Kokoro)", "en", "female", _KO, "Nữ Mỹ dịu dàng, truyền cảm"),
    _v("am_adam", "Adam (Nam Mỹ · Kokoro)", "en", "male", _KO, "Nam Mỹ trầm ấm, chuyên nghiệp"),
    _v("am_michael", "Michael (Nam Mỹ · Kokoro)", "en", "male", _KO, "Nam Mỹ tự nhiên, phong cách kể chuyện"),
    _v("bf_emma", "Emma (Nữ Anh · Kokoro)", "en", "female", _KO, "Nữ giọng Anh (British), thanh lịch"),
    _v("bm_george", "George (Nam Anh · Kokoro)", "en", "male", _KO, "Nam giọng Anh (British), đĩnh đạc"),
    # Tiếng Nhật — Kokoro ONNX + misaki[ja] (offline)
    _v("jf_alpha", "Alpha (Nữ · Kokoro JA)", "ja", "female", _KO, "Nữ tiếng Nhật chuẩn, rõ ràng"),
    _v("jf_gongitsune", "Gongitsune (Nữ · Kokoro JA)", "ja", "female", _KO, "Nữ tiếng Nhật, phong cách kể chuyện"),
    _v("jf_nezumi", "Nezumi (Nữ · Kokoro JA)", "ja", "female", _KO, "Nữ tiếng Nhật, trẻ trung"),
    _v("jf_tebukuro", "Tebukuro (Nữ · Kokoro JA)", "ja", "female", _KO, "Nữ tiếng Nhật, nhẹ nhàng"),
    _v("jm_kumo", "Kumo (Nam · Kokoro JA)", "ja", "male", _KO, "Nam tiếng Nhật, trầm ổn"),
]

VOICE_SAMPLES = {
    "Thùy Dung": "Xin chào quý vị, đây là Thùy Dung với giọng đọc miền Nam truyền cảm bốn mươi tám kilo héc.",
    "Thái Sơn": "Kính chào quý vị, đây là giọng đọc Thái Sơn phong cách kể chuyện và phóng sự đĩnh đạc.",
    "Trúc Ly": "Xin chào các bạn, đây là Trúc Ly với giọng nói miền Bắc tự nhiên, nhẹ nhàng.",
    "Mai Anh": "Bản tin thời sự hôm nay, tôi là Mai Anh, phát thanh viên AI Workforce.",
    "Minh Quân Pro": "Xin chào mọi người, đây là Minh Quân Pro, giọng đọc chuyên nghiệp chuẩn studio.",
    "Anh Khôi": "Chào bạn, mình là Anh Khôi, giọng kể chuyện ấm áp và truyền cảm hứng.",
    "Quang Sơn": "Dạ xin chào mọi người, tui là Quang Sơn, mang giọng đọc miền Trung mộc mạc.",
    "Ngọc Trân": "Dạ em là Ngọc Trân, gửi lời chào từ xứ Huế thân thương đến quý thính giả.",
    "Adam bựa": "Alo alo, một hai ba bốn, Adam bựa xin chào toàn thể anh em nhá!",
}
_LANG_SAMPLE = {
    "en": "Hello, this is an offline voice preview from AI Workforce.",
    "ja": "こんにちは、AIワークフォースのオフライン音声プレビューです。",
    "vi": "Xin chào, đây là âm thanh nghe thử giọng đọc AI.",
}
_PY_CACHE = {}


def get_voice_catalog():
    return VOICE_CATALOG


def get_sample_text(voice_id):
    if voice_id in VOICE_SAMPLES:
        return VOICE_SAMPLES[voice_id]
    lang = KOKORO_VOICES.get(voice_id, "vi")[:2]
    return _LANG_SAMPLE.get(lang, _LANG_SAMPLE["vi"])


def default_voice(lang, gender="female"):
    d = DEFAULT_VOICES.get(lang) or DEFAULT_VOICES["vi"]
    return d.get(gender) or d["female"]


def engine_for(lang, voice=None):
    if voice in KOKORO_VOICES:
        return "kokoro"
    return "vieneu" if lang == "vi" else "kokoro"


def find_python(module):
    """Python của venv trong workspace có `module` (.venv, .venv-tts). None nếu không có."""
    if module in _PY_CACHE:
        return _PY_CACHE[module]
    found = None
    for cand in [os.path.join(WORKSPACE, ".venv-tts", "bin", "python3"), os.path.join(WORKSPACE, ".venv-tts", "bin", "python"),
                 os.path.join(WORKSPACE, ".venv", "bin", "python"), sys.executable]:
        if cand and os.path.isfile(cand) and subprocess.run([cand, "-c", f"import {module}"], capture_output=True).returncode == 0:
            found = cand
            break
    _PY_CACHE[module] = found
    return found


def vieneu_python():
    return find_python("vieneu")


def kokoro_python():
    return find_python("kokoro_onnx")


def kokoro_model_paths():
    """(model, voices) nếu đã tải, ngược lại (None, None)."""
    voices = os.path.join(KOKORO_DIR, KOKORO_VOICES_FILE)
    for m in KOKORO_MODELS:
        p = os.path.join(KOKORO_DIR, m)
        if os.path.isfile(p) and os.path.isfile(voices):
            return p, voices
    return None, None


def _resolve_kokoro_voice(lang, voice, gender):
    if voice in KOKORO_VOICES and KOKORO_VOICES[voice][:2] == lang:
        return voice
    return default_voice(lang, gender)


def _run_worker(py, worker, jobs, work, tag, log):
    os.makedirs(work, exist_ok=True)
    jf = os.path.join(work, f"tts_{tag}_jobs_{os.getpid()}.json")
    with open(jf, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False)
    r = subprocess.run([py, worker, jf], capture_output=True, text=True)
    line = next((ln for ln in reversed(r.stdout.strip().splitlines()) if ln.startswith("{")), None)
    if r.returncode or not line:
        raise RuntimeError(f"{tag} worker lỗi (mã {r.returncode}): {(r.stderr or r.stdout)[-400:]}")
    return json.loads(line)


def synthesize_batch(items, lang="vi", voice=None, gender="female", work=None, speed=1.0, ref_audio=None, log=print):
    """Tổng hợp nhiều câu trong MỘT tiến trình (nạp model một lần).

    Trả về {"engine", "voice", "results": [{"key","out","dur","ok","error"}]}.
    Engine không sẵn sàng → RuntimeError có hướng dẫn cài (không đổi engine ngầm).
    """
    work = work or os.path.dirname(os.path.abspath(items[0]["out"])) if items else (work or ".")
    engine = engine_for(lang, voice)
    if engine == "vieneu":
        py = vieneu_python()
        if not py:
            raise RuntimeError(f"Chưa có VieNeu-TTS (gói `vieneu`) trong .venv/.venv-tts. Chạy: {INSTALL_HINT}")
        jobs = {"voice": voice or default_voice("vi", gender), "gender": gender, "ref_audio": ref_audio, "items": items}
        out = _run_worker(py, VIENEU_WORKER, jobs, work, "vieneu", log)
        out["engine"] = "VieNeu-TTS v3 Turbo 48kHz (offline)" + (" · clone" if ref_audio else "")
        return out
    if ref_audio:
        log("   ⚠️ Nhân bản giọng (ref_audio) chỉ hỗ trợ tiếng Việt (VieNeu); Kokoro dùng giọng có sẵn.")
    py = kokoro_python()
    model, voices = kokoro_model_paths()
    if not py:
        raise RuntimeError(f"Chưa có Kokoro (gói `kokoro-onnx`) trong .venv-tts. Chạy: {INSTALL_HINT}")
    if not model:
        raise RuntimeError(f"Chưa tải model Kokoro vào {KOKORO_DIR}. Chạy: {INSTALL_HINT}")
    kv = _resolve_kokoro_voice(lang, voice, gender)
    jobs = {"voice": kv, "lang": KOKORO_VOICES[kv], "speed": float(speed or 1.0), "model": model, "voices": voices, "items": items}
    out = _run_worker(py, KOKORO_WORKER, jobs, work, "kokoro", log)
    out["engine"] = f"Kokoro ONNX v1.0 ({os.path.basename(model)}, offline)"
    return out


def synthesize_line(text, output_path, lang="vi", gender="female", voice=None, speed=1.0, ref_audio=None):
    """Tổng hợp một câu → WAV. Luôn trả dict (không ném lỗi) để dùng trong server/UI."""
    wav_out = os.path.splitext(os.path.abspath(output_path))[0] + ".wav"
    try:
        r = synthesize_batch([{"key": "one", "text": text, "out": wav_out, "temperature": 0.6}], lang=lang, voice=voice,
                             gender=gender, work=os.path.dirname(wav_out), speed=speed, ref_audio=ref_audio, log=lambda m: None)
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    res = (r.get("results") or [{}])[0]
    if res.get("ok") and os.path.isfile(wav_out) and os.path.getsize(wav_out) > 0:
        return {"success": True, "engine": r.get("engine"), "voice": r.get("voice"), "output_path": wav_out, "duration": res.get("dur")}
    return {"success": False, "engine": r.get("engine"), "error": res.get("error") or "Engine không sinh được âm thanh"}


def main():
    ap = argparse.ArgumentParser(description="TTS offline dùng chung AIWF: VieNeu (vi) · Kokoro (en/ja)")
    ap.add_argument("--text", "-t", help="Nội dung lời thoại")
    ap.add_argument("--output", "-o", help="File WAV đầu ra")
    ap.add_argument("--lang", "-l", default="vi", choices=["vi", "ja", "en"])
    ap.add_argument("--gender", "-g", default="female", choices=["female", "male"])
    ap.add_argument("--voice", "-v", default=None, help="Mã giọng (xem --list-voices)")
    ap.add_argument("--speed", "-s", type=float, default=1.0, help="Tốc độ (chỉ Kokoro)")
    ap.add_argument("--ref-audio", "-r", default=None, help="File mẫu để nhân bản giọng (chỉ tiếng Việt / VieNeu)")
    ap.add_argument("--list-voices", action="store_true", help="In danh mục giọng dạng JSON")
    a = ap.parse_args()
    if a.list_voices:
        print(json.dumps(VOICE_CATALOG, ensure_ascii=False, indent=2))
        return 0
    if not a.text or not a.output:
        ap.error("cần --text và --output (hoặc --list-voices)")
    res = synthesize_line(a.text, a.output, lang=a.lang, gender=a.gender, voice=a.voice, speed=a.speed, ref_audio=a.ref_audio)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
