#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ffmpeg_tools.py — Hạ tầng ffmpeg dùng chung cho phu-de, long-tieng, video-studio (Luật R7).

    ffmpeg_bin() / ffprobe_bin()   đường dẫn nhị phân (ưu tiên ffmpeg-full có libass + rubberband)
    has_filter(name)               ffmpeg có bộ lọc đó không (ass, rubberband, sidechaincompress…)
    decode(path, channels, sr)     file âm thanh bất kỳ → numpy float32
    encode(arr, path, channels, sr) numpy float32 → WAV PCM 16-bit
    duration(path)                 thời lượng (giây) qua ffprobe
    loudness(path)                 (integrated LUFS, true peak dBFS) theo EBU R128
    FONTS_DIR                      thư mục font dùng chung `_shared/fonts` (fontsdir cho libass)
"""
import json
import os
import re
import shutil
import subprocess

import numpy as np

SR = 48000
FONTS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts"))

_CANDIDATES = ["/opt/homebrew/opt/ffmpeg-full/bin/{}", "/opt/homebrew/bin/{}", "/usr/local/bin/{}"]
_FILTER_CACHE = {}


def _find(name):
    for tpl in _CANDIDATES:
        p = tpl.format(name)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return shutil.which(name) or name


def ffmpeg_bin():
    return _find("ffmpeg")


def ffprobe_bin():
    ff = ffmpeg_bin()
    sibling = os.path.join(os.path.dirname(ff), "ffprobe") if os.path.isabs(ff) else ""
    if sibling and os.path.isfile(sibling):
        return sibling
    return _find("ffprobe")


def has_filter(name):
    if name in _FILTER_CACHE:
        return _FILTER_CACHE[name]
    try:
        out = subprocess.run([ffmpeg_bin(), "-hide_banner", "-filters"], capture_output=True, text=True, timeout=15).stdout
    except (OSError, subprocess.SubprocessError) as e:
        print(f"⚠️ [ffmpeg] không liệt kê được bộ lọc ({e})")
        return False
    ok = re.search(rf"\s{re.escape(name)}\s", out) is not None
    _FILTER_CACHE[name] = ok
    return ok


def decode(path, channels=1, sr=SR):
    """File âm thanh bất kỳ (mp3/wav/ogg...) → float32 numpy @sr (shape [n] hoặc [n, channels])."""
    r = subprocess.run([ffmpeg_bin(), "-v", "error", "-i", path, "-f", "f32le", "-ac", str(channels), "-ar", str(sr), "-"],
                       capture_output=True, check=True)
    a = np.frombuffer(r.stdout, dtype=np.float32)
    return a.reshape(-1, channels) if channels > 1 else a


def encode(arr, path, channels=1, sr=SR):
    p = subprocess.run([ffmpeg_bin(), "-v", "error", "-y", "-f", "f32le", "-ac", str(channels), "-ar", str(sr), "-i", "-",
                        "-c:a", "pcm_s16le", path], input=np.ascontiguousarray(arr, dtype=np.float32).tobytes(), capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode()[-400:])


def duration(path):
    """Thời lượng file media (giây). Lỗi đọc → RuntimeError (không trả 0 im lặng)."""
    r = subprocess.run([ffprobe_bin(), "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"ffprobe lỗi với {path}: {r.stderr[-300:]}")
    return float(json.loads(r.stdout)["format"]["duration"])


def loudness(path):
    r = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return (float(i[-1]) if i else None, float(p[-1]) if p else None)


def escape_filter_path(p):
    """Thoát đường dẫn để nhúng vào chuỗi filtergraph (ass='...':fontsdir='...')."""
    return str(p).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
