#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dub_engine.py — Lõi âm thanh lồng tiếng chất lượng phòng thu (dùng bởi dubbing_pipeline và dub_workbench).

1. synthesize()  : VieNeu-TTS 48 kHz offline theo LÔ (nạp mô hình 1 lần) cho tiếng Việt; Kokoro/Edge-TTS
                   cho ngôn ngữ khác. Mỗi câu được Whisper NGHE LẠI (round-trip) và chấm lỗi ký tự (CER);
                   câu đọc sai/nuốt chữ được đọc lại tối đa `takes` lượt, giữ lượt tốt nhất.
2. plan_fit()    : khung thời gian của mỗi câu = tới lúc câu sau bắt đầu. CHỈ tăng tốc khi cần, không
                   bao giờ làm chậm (giọng kéo lê). Nhịp nền chung (median) để tốc độ đồng đều; trần 1.25×.
                   Câu vẫn tràn → cờ OVERFLOW: agent phải RÚT GỌN câu chữ (cách sửa đúng), không ép nhanh hơn.
3. render_fit()  : co giãn bằng rubberband (giữ formant, tự nhiên) nếu ffmpeg có, ngược lại atempo.
4. mix()         : giọng đặt đúng mốc; tiếng gốc hạ theo vùng có lời (fade 150/350 ms) — không bơm/giật;
                   chuẩn hoá độ lớn EBU R128 −16 LUFS, đỉnh −1.5 dBTP.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SR = 48000


# ------------------------------------------------------------------ binaries & helpers
def ffmpeg_bin():
    for p in ["/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return shutil.which("ffmpeg") or "ffmpeg"


def has_filter(name):
    try:
        out = subprocess.run([ffmpeg_bin(), "-hide_banner", "-filters"], capture_output=True, text=True, timeout=15).stdout
        return re.search(rf"\s{name}\s", out) is not None
    except Exception:
        return False


def decode(path, channels=1):
    """File âm thanh bất kỳ (mp3/wav/ogg...) → float32 numpy @48 kHz (shape [n] hoặc [n, 2])."""
    r = subprocess.run([ffmpeg_bin(), "-v", "error", "-i", path, "-f", "f32le", "-ac", str(channels), "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    a = np.frombuffer(r.stdout, dtype=np.float32)
    return a.reshape(-1, channels) if channels > 1 else a


def encode(arr, path, channels=1):
    p = subprocess.run([ffmpeg_bin(), "-v", "error", "-y", "-f", "f32le", "-ac", str(channels), "-ar", str(SR), "-i", "-",
                        "-c:a", "pcm_s16le", path], input=np.ascontiguousarray(arr, dtype=np.float32).tobytes(), capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode()[-400:])


def tts_python():
    """Python của venv có gói vieneu (.venv hoặc .venv-tts trong workspace)."""
    for cand in [os.path.join(WORKSPACE, ".venv", "bin", "python"), os.path.join(WORKSPACE, ".venv-tts", "bin", "python3"),
                 os.path.join(WORKSPACE, ".venv-tts", "bin", "python")]:
        if os.path.isfile(cand):
            if subprocess.run([cand, "-c", "import vieneu"], capture_output=True).returncode == 0:
                return cand
    return None


def is_edge_voice(v):
    return bool(v) and bool(re.match(r"^[a-z]{2}-[A-Z]{2}-\w+Neural$", v))


# ------------------------------------------------------------------ round-trip verification
_ASR = None


def _norm(t):
    t = unicodedata.normalize("NFC", t.lower())
    return re.sub(r"[\W\d_]+", "", t)          # chỉ so chữ: bỏ dấu câu, khoảng trắng, chữ số (TTS đọc số thành chữ)


def cer(ref, hyp):
    a, b = _norm(ref), _norm(hyp)
    if not a:
        return 0.0
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[-1] / len(a)


def hear(path, lang):
    global _ASR
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    if _ASR is None:
        _ASR = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = _ASR.transcribe(path, language=lang, vad_filter=False, beam_size=1, condition_on_previous_text=False)
    return " ".join(s.text.strip() for s in segs)


# ------------------------------------------------------------------ synthesis
def _vieneu_batch(items, voice, gender, work, log):
    py = tts_python()
    if not py:
        return None
    jf = os.path.join(work, f"tts_jobs_{os.getpid()}.json")
    json.dump({"voice": voice, "gender": gender, "items": items}, open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run([py, os.path.join(HERE, "tts_batch.py"), jf], capture_output=True, text=True)
    line = next((l for l in reversed(r.stdout.strip().splitlines()) if l.startswith("{")), None)
    if r.returncode or not line:
        log(f"   ⚠️ VieNeu lỗi: {(r.stderr or r.stdout)[-300:]}")
        return None
    return json.loads(line)


def _single(text, out, lang, gender, voice):
    sys.path.insert(0, HERE)
    from voice_synthesizer import synthesize_line
    res = synthesize_line(text, out, lang=lang, gender=gender, voice=voice)
    path = res.get("output_path") or out
    return path if res.get("success") and os.path.isfile(path) and os.path.getsize(path) > 0 else None


def synthesize(lines, lang, voice, gender, work, takes=3, verify=True, max_cer=0.08, log=print):
    """lines: [{"key", "text"}] → {key: {"path", "dur", "cer", "heard", "engine", "take"}}."""
    os.makedirs(work, exist_ok=True)
    use_vieneu = lang == "vi" and not is_edge_voice(voice) and tts_python() is not None
    temps = [0.65, 0.5, 0.8, 0.6]
    # cache theo (câu, giọng, ngôn ngữ): sửa 1 câu rồi render lại chỉ tổng hợp đúng câu đó
    import hashlib
    idx_file = os.path.join(work, "cache_index.json")
    cache = json.load(open(idx_file, encoding="utf-8")) if os.path.isfile(idx_file) else {}
    hkey = lambda ln: hashlib.sha1(f"{lang}|{voice}|{gender}|{ln['text']}".encode()).hexdigest()[:16]
    best, pending = {}, []
    for ln in lines:
        c = cache.get(hkey(ln))
        if c and os.path.isfile(c["path"]):
            best[ln["key"]] = dict(c)
        else:
            pending.append(ln)
    if len(pending) < len(lines):
        log(f"   ♻️  Dùng lại {len(lines) - len(pending)} câu đã tổng hợp (không đổi chữ)")
    used_voice = voice
    for t in range(max(1, takes)):
        if not pending:
            break
        outs = {ln["key"]: os.path.join(work, f"{hkey(ln)}_t{t}.wav") for ln in pending}
        got = {}
        if use_vieneu:
            r = _vieneu_batch([{"key": ln["key"], "text": ln["text"], "out": outs[ln["key"]], "temperature": temps[t % len(temps)]} for ln in pending],
                              voice, gender, work, log)
            if r:
                used_voice = r.get("voice") or voice
                got = {x["key"]: x["out"] for x in r["results"] if x.get("ok")}
            else:
                use_vieneu = False
        if not use_vieneu:
            for ln in pending:
                p = _single(ln["text"], outs[ln["key"]], lang, gender, voice)
                if p:
                    got[ln["key"]] = p
            if t > 0:                                   # engine tất định (edge/kokoro): đọc lại vô ích
                pass
        engine = f"VieNeu-TTS v3 Turbo ({used_voice})" if use_vieneu else "voice_synthesizer (Kokoro/Edge-TTS)"
        still = []
        for ln in pending:
            p = got.get(ln["key"])
            if not p:
                still.append(ln); continue
            dur = len(decode(p)) / SR
            heard = hear(p, lang) if verify else None
            c = cer(ln["text"], heard) if heard is not None else 0.0
            if dur < 0.15 or dur > max(3.0, len(ln["text"]) * 0.25):    # rỗng hoặc lặp vô tận
                c = max(c, 1.0)
            cur = best.get(ln["key"])
            if cur is None or c < cur["cer"]:
                best[ln["key"]] = {"path": p, "dur": round(dur, 3), "cer": round(c, 3), "heard": heard, "engine": engine, "take": t + 1}
            if c > max_cer:
                still.append(ln)
        log(f"   🎙  Lượt {t + 1}: {len(pending) - len(still)}/{len(pending)} câu đạt (CER ≤ {max_cer:.0%}) — {engine}")
        pending = still if use_vieneu else []
    for ln in lines:
        if ln["key"] in best:
            cache[hkey(ln)] = best[ln["key"]]
    json.dump(cache, open(idx_file, "w", encoding="utf-8"), ensure_ascii=False)
    return best, used_voice


# ------------------------------------------------------------------ fitting
def plan_fit(lines, video_dur, max_tempo=1.25, gap=0.12, base_cap=1.08, min_tempo=1.0):
    """lines (đã sort theo start): {"key","start","end","dur"} → thêm "slot","tempo","fit_dur","overflow"."""
    for i, ln in enumerate(lines):
        nxt = lines[i + 1]["start"] if i + 1 < len(lines) else video_dur
        ln["slot"] = round(max(0.3, nxt - ln["start"] - gap), 3)
        ln["need"] = ln["dur"] / ln["slot"]
    needs = sorted(ln["need"] for ln in lines) or [1.0]
    base = max(min_tempo, min(base_cap, max(1.0, needs[len(needs) // 2])))
    for ln in lines:
        ln["tempo"] = round(min(max_tempo, max(base, ln["need"])), 3)
        ln["fit_dur"] = round(ln["dur"] / ln["tempo"], 3)
        ln["overflow"] = round(max(0.0, ln["fit_dur"] - ln["slot"]), 3)
    return lines, base


def render_fit(src, dst, tempo):
    if abs(tempo - 1.0) < 0.01:
        filt = "anull"
    elif has_filter("rubberband"):
        filt = f"rubberband=tempo={tempo:.4f}:formant=preserved:pitchq=quality:transients=smooth"
    else:
        filt = f"atempo={tempo:.4f}"
    r = subprocess.run([ffmpeg_bin(), "-v", "error", "-y", "-i", src, "-af", filt, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", dst], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-300:])
    return dst


# ------------------------------------------------------------------ mix
def mix(original, placed, out_path, video_dur, bg_volume=1.0, duck_level=0.2, voice_volume=1.0, attack=0.15, release=0.35, lufs=-16.0):
    """placed: [(start_sec, wav_path)]. Trả về đường dẫn WAV stereo 48 kHz đã chuẩn hoá độ lớn."""
    n = int(round(video_dur * SR)) + SR // 2
    bg = np.zeros((n, 2), np.float32)
    if original and os.path.isfile(original):
        o = decode(original, 2)[:n]; bg[:len(o)] = o
    voice = np.zeros(n, np.float32)
    for start, p in placed:
        a = decode(p)
        rms = float(np.sqrt(np.mean(a ** 2))) if len(a) else 0.0
        if rms > 1e-4:
            a = a * (0.1 / rms)                     # mọi câu cùng độ lớn (~−20 dBFS RMS): không câu to câu nhỏ
        s = int(start * SR); e = min(n, s + len(a))
        if e > s:
            voice[s:e] += a[: e - s]
    # đường bao hạ tiếng gốc: tính theo vùng có giọng, mở rộng + dốc tuyến tính
    active = np.abs(voice) > 1e-4
    env = np.ones(n, np.float32)
    if active.any():
        win = max(1, int(0.05 * SR))
        act = np.convolve(active.astype(np.float32), np.ones(win, np.float32), "same") > 0
        idx = np.flatnonzero(np.diff(np.concatenate([[0], act.astype(np.int8), [0]])))
        for s, e in zip(idx[0::2], idx[1::2]):
            a0, a1 = max(0, s - int(attack * SR)), s
            r0, r1 = e, min(n, e + int(release * SR))
            env[a1:e] = np.minimum(env[a1:e], duck_level)
            if a1 > a0:
                env[a0:a1] = np.minimum(env[a0:a1], np.linspace(1, duck_level, a1 - a0, dtype=np.float32))
            if r1 > r0:
                env[r0:r1] = np.minimum(env[r0:r1], np.linspace(duck_level, 1, r1 - r0, dtype=np.float32))
    out = bg * (env * bg_volume)[:, None] + (voice * voice_volume)[:, None]
    out = out[: int(round(video_dur * SR))]
    tmp = out_path + ".pre.wav"
    encode(out, tmp, 2)
    r = subprocess.run([ffmpeg_bin(), "-v", "error", "-y", "-i", tmp, "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", out_path],
                       capture_output=True, text=True)
    if r.returncode:
        shutil.move(tmp, out_path)
    else:
        os.remove(tmp)
    return out_path


def loudness(path):
    r = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return (float(i[-1]) if i else None, float(p[-1]) if p else None)


# ------------------------------------------------------------------ one-call pipeline
def dub_audio(segments, video_dur, original_audio, work, lang="vi", voice=None, gender="female", bg_volume=1.0,
              duck_level=0.2, voice_volume=1.0, takes=3, verify=True, max_tempo=1.25, speed=1.0, log=print):
    """segments: [{"start","end","text"}] → (final_wav, report). Tất cả file tạm trong `work`."""
    os.makedirs(work, exist_ok=True)
    lines = [{"key": f"s{i:04d}", "start": float(s["start"]), "end": float(s["end"]), "text": s["text"].strip()}
             for i, s in enumerate(sorted(segments, key=lambda x: float(x["start"]))) if s.get("text", "").strip()]
    if not lines:
        raise RuntimeError("Không có câu thoại nào để lồng tiếng.")
    log(f"🗣  Tổng hợp {len(lines)} câu ({lang}, giọng {voice or gender})...")
    takes_res, used_voice = synthesize(lines, lang, voice, gender, os.path.join(work, "takes"), takes=takes, verify=verify, log=log)
    ok = [ln for ln in lines if ln["key"] in takes_res]
    for ln in ok:
        ln.update({k: takes_res[ln["key"]][k] for k in ("path", "dur", "cer", "heard", "take")})
    plan, base = plan_fit(ok, video_dur, max_tempo=max_tempo, min_tempo=max(1.0, float(speed or 1.0)))
    fit_dir = os.path.join(work, "fitted"); os.makedirs(fit_dir, exist_ok=True)
    placed = []
    for ln in plan:
        dst = os.path.join(fit_dir, f"{ln['key']}.wav")
        render_fit(ln["path"], dst, ln["tempo"])
        placed.append((ln["start"], dst))
    final = os.path.join(work, "final_mixed_audio.wav")
    mix(original_audio, placed, final, video_dur, bg_volume=bg_volume, duck_level=duck_level, voice_volume=voice_volume)
    i, peak = loudness(final)
    over = [ln for ln in plan if ln["overflow"] > 0.05]
    bad = [ln for ln in plan if ln.get("cer", 0) > 0.08]
    report = {"voice": used_voice, "engine": takes_res[ok[0]["key"]]["engine"] if ok else None, "lines": len(lines), "synthesized": len(ok),
              "base_tempo": base, "max_tempo": max((ln["tempo"] for ln in plan), default=1.0),
              "fast_lines": sum(1 for ln in plan if ln["tempo"] > 1.15), "overflow_lines": len(over), "mispronounced_lines": len(bad),
              "integrated_lufs": i, "true_peak_dbfs": peak,
              "items": [{k: ln.get(k) for k in ("key", "start", "end", "text", "dur", "slot", "tempo", "overflow", "cer", "heard", "take")} for ln in plan],
              "failed": [ln["text"] for ln in lines if ln["key"] not in takes_res]}
    json.dump(report, open(os.path.join(work, "dub_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    log(f"📊 Nhịp nền {base:.2f}× · tối đa {report['max_tempo']:.2f}× · {report['fast_lines']} câu > 1.15× · "
        f"{report['overflow_lines']} câu TRÀN khung · {report['mispronounced_lines']} câu đọc sai (CER>8%) · {i} LUFS")
    return final, report
