#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voice_synthesizer.py — Bộ tổng hợp giọng nói cho kỹ năng Lồng Tiếng (long-tieng).
Tích hợp trực tiếp với VoiceStudio (localhost:3900) hoặc Edge-TTS Neural cục bộ.
Tuyệt đối KHÔNG gọi API ngoài trả phí. Không yêu cầu API key.
"""

import sys
import os
import json
import argparse
import subprocess
import urllib.request
import urllib.error
import shutil

GLOBAL_CLIENT = os.path.expanduser("~/.gemini/config/skills/voice-studio/scripts/voice_client.py")

DEFAULT_VOICES = {
    "vi": {
        "female": "vi-VN-HoaiMyNeural",
        "male": "vi-VN-NamMinhNeural",
        "default": "vi-VN-HoaiMyNeural"
    },
    "ja": {
        "female": "ja-JP-NanamiNeural",
        "male": "ja-JP-KeitaNeural",
        "default": "ja-JP-NanamiNeural"
    },
    "en": {
        "female": "en-US-JennyNeural",
        "male": "en-US-GuyNeural",
        "default": "en-US-JennyNeural"
    }
}

def synthesize_line(text, output_path, lang="vi", gender="female", voice=None, speed=1.0):
    """
    Tổng hợp một dòng lời thoại thành file âm thanh.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    selected_voice = voice or DEFAULT_VOICES.get(lang, {}).get(gender, DEFAULT_VOICES.get(lang, {}).get("default", "vi-VN-HoaiMyNeural"))

    # Ưu tiên sử dụng global voice_client nếu có
    if os.path.exists(GLOBAL_CLIENT):
        cmd = [
            sys.executable, GLOBAL_CLIENT,
            "--text", text,
            "--lang", lang,
            "--voice", selected_voice,
            "--gender", gender,
            "--speed", str(speed),
            "--output", output_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                return json.loads(res.stdout)
            except Exception:
                return {"success": True, "output_path": output_path}

    # Fallback trực tiếp bằng edge-tts
    rate_str = f"+{int((speed - 1.0) * 100)}%" if speed >= 1.0 else f"{int((speed - 1.0) * 100)}%"
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", selected_voice,
        "--text", text,
        "--write-media", output_path,
        "--rate", rate_str
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {
            "success": True,
            "engine": "edge-tts direct",
            "voice": selected_voice,
            "output_path": os.path.abspath(output_path)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Bộ tổng hợp âm thanh lồng tiếng")
    parser.add_argument("--text", "-t", required=True, help="Nội dung lời thoại")
    parser.add_argument("--output", "-o", required=True, help="Đường dẫn file âm thanh đầu ra")
    parser.add_argument("--lang", "-l", default="vi", choices=["vi", "ja", "en"], help="Ngôn ngữ")
    parser.add_argument("--gender", "-g", default="female", choices=["female", "male"], help="Giới tính giọng")
    parser.add_argument("--voice", "-v", default=None, help="Mã giọng cụ thể")
    parser.add_argument("--speed", "-s", type=float, default=1.0, help="Tốc độ nói")
    args = parser.parse_args()

    result = synthesize_line(
        text=args.text,
        output_path=args.output,
        lang=args.lang,
        gender=args.gender,
        voice=args.voice,
        speed=args.speed
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
