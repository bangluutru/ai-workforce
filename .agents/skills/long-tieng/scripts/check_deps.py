#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_deps.py — Kiểm tra môi trường phụ thuộc cho Kỹ năng Lồng Tiếng (long-tieng v1.0).
Zero External API: Kiểm tra ffmpeg và engine giọng nói cục bộ (VoiceStudio / edge-tts).
"""

import sys
import os
import shutil
import subprocess
import urllib.request

def check_ffmpeg():
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        # Check standard macOS paths
        for p in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/Applications/VoiceStudio.app/Contents/MacOS/ffmpeg"]:
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return True, p
        return False, "Thiếu ffmpeg. Cần cài đặt qua Homebrew: brew install ffmpeg"
    return True, ffmpeg_path

def check_voicestudio():
    # Check app installation
    app_exists = os.path.isdir("/Applications/VoiceStudio.app")
    # Check active port
    port_active = False
    for port in [3900, 3902]:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/")
            with urllib.request.urlopen(req, timeout=1) as resp:
                port_active = True
                break
        except Exception:
            pass
    return app_exists, port_active

def check_vieneu():
    for py in [sys.executable, os.path.expanduser("~/.gemini/antigravity-ide/scratch/ai-workforce/.venv/bin/python")]:
        if os.path.isfile(py):
            try:
                res = subprocess.run([py, "-c", "import vieneu"], capture_output=True)
                if res.returncode == 0:
                    return True, f"VieNeu-TTS v3 Turbo 48 kHz sẵn sàng ({py})"
            except Exception:
                pass
    return False, "Chưa cài vieneu. Chạy: bash ~/.gemini/config/skills/voice-studio/scripts/setup_vieneu.sh"

def check_edge_tts():
    for py in [sys.executable, os.path.expanduser("~/.gemini/antigravity-ide/scratch/ai-workforce/.venv/bin/python")]:
        if os.path.isfile(py):
            try:
                res = subprocess.run([py, "-c", "import edge_tts"], capture_output=True)
                if res.returncode == 0:
                    return True, f"Thư viện edge_tts sẵn sàng ({py})"
            except Exception:
                pass
    which_tts = shutil.which("edge-tts")
    if which_tts:
        return True, which_tts
    return False, "Chưa cài edge-tts. Chạy: uv pip install edge-tts"

def main():
    print("🔍 Kiểm tra phụ thuộc cho kỹ năng Lồng Tiếng (long-tieng v2.2)...")
    ff_ok, ff_msg = check_ffmpeg()
    print(f" • FFmpeg: {'✅ ' + ff_msg if ff_ok else '❌ ' + ff_msg}")

    vn_ok, vn_msg = check_vieneu()
    print(f" • VieNeu-TTS (48 kHz Studio HD): {'✅ ' + vn_msg if vn_ok else '⚠️ ' + vn_msg}")

    vs_installed, vs_running = check_voicestudio()
    if vs_installed:
        status_str = "Đang chạy" if vs_running else "Đã cài đặt (sẵn sàng khởi chạy)"
        print(f" • VoiceStudio: ✅ /Applications/VoiceStudio.app [{status_str}]")
    else:
        print(" • VoiceStudio: ℹ️ Không bắt buộc khi đã có VieNeu-TTS 48 kHz & Edge-TTS")

    tts_ok, tts_msg = check_edge_tts()
    print(f" • Edge-TTS (Dự phòng siêu tốc): {'✅ ' + tts_msg if tts_ok else '⚠️ ' + tts_msg}")

    if not ff_ok:
        print("\n❌ Cần FFmpeg để ghép nối âm thanh và render video lồng tiếng.")
        sys.exit(1)
    
    print("\n✅ Môi trường sẵn sàng phục vụ tác vụ lồng tiếng video!")

if __name__ == "__main__":
    main()
