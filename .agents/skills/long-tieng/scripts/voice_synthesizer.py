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

# Kokoro ONNX model paths (Tier 1 for EN — offline, Apache 2.0)
KOKORO_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "kokoro")
KOKORO_MODEL_PATH = os.path.join(KOKORO_MODEL_DIR, "kokoro-v1.0.onnx")
KOKORO_VOICES_PATH = os.path.join(KOKORO_MODEL_DIR, "voices-v1.0.bin")
# Kokoro venv path for isolated dependencies
KOKORO_VENV_PYTHON = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), ".venv-tts", "bin", "python3")

# Mapping Kokoro voice IDs to their lang codes
KOKORO_VOICES = {
    "af_heart": "en-us", "af_bella": "en-us", "af_nova": "en-us", "af_sarah": "en-us",
    "am_adam": "en-us", "am_michael": "en-us", "am_eric": "en-us",
    "bf_emma": "en-gb", "bf_isabella": "en-gb", "bm_george": "en-gb",
}

DEFAULT_VOICES = {
    "vi": {
        "female": "Thùy Dung",
        "male": "Thái Sơn",
        "default": "Thùy Dung"
    },
    "ja": {
        "female": "ja-JP-NanamiNeural",
        "male": "ja-JP-KeitaNeural",
        "default": "ja-JP-NanamiNeural"
    },
    "en": {
        "female": "af_heart",
        "male": "am_adam",
        "default": "af_heart"
    }
}

VOICE_CATALOG = [
    # Tiếng Việt 48 kHz Studio HD (VieNeu-TTS v3 Turbo)
    {
        "id": "Thùy Dung",
        "name": "Thùy Dung (Nữ · Nam 48kHz ⭐⭐⭐⭐⭐)",
        "lang": "vi",
        "gender": "female",
        "region": "Nam",
        "engine": "VieNeu 48kHz",
        "description": "Nữ miền Nam, phong cách tin tức, truyền cảm chuẩn studio HD"
    },
    {
        "id": "Thái Sơn",
        "name": "Thái Sơn (Nam · Nam 48kHz ⭐⭐⭐⭐⭐)",
        "lang": "vi",
        "gender": "male",
        "region": "Nam",
        "engine": "VieNeu 48kHz",
        "description": "Nam miền Nam, kể chuyện, phóng sự, trầm ấm đĩnh đạc"
    },
    {
        "id": "Trúc Ly",
        "name": "Trúc Ly (Nữ · Bắc 48kHz ⭐⭐⭐⭐⭐)",
        "lang": "vi",
        "gender": "female",
        "region": "Bắc",
        "engine": "VieNeu 48kHz",
        "description": "Nữ miền Bắc, giọng đọc tự nhiên, dịu dàng, nhã nhặn"
    },
    {
        "id": "Mai Anh",
        "name": "Mai Anh (Nữ · Bắc 48kHz ⭐⭐⭐⭐⭐)",
        "lang": "vi",
        "gender": "female",
        "region": "Bắc",
        "engine": "VieNeu 48kHz",
        "description": "Nữ miền Bắc, phát thanh viên thời sự, rõ ràng chuyên nghiệp"
    },
    {
        "id": "Minh Quân Pro",
        "name": "Minh Quân Pro (Nam · Bắc 48kHz ⭐⭐⭐⭐⭐)",
        "lang": "vi",
        "gender": "male",
        "region": "Bắc",
        "engine": "VieNeu 48kHz",
        "description": "Nam miền Bắc, phong thái đĩnh đạc, tự nhiên chuẩn studio"
    },
    {
        "id": "Anh Khôi",
        "name": "Anh Khôi (Nam · Bắc 48kHz ⭐⭐⭐⭐⭐)",
        "lang": "vi",
        "gender": "male",
        "region": "Bắc",
        "engine": "VieNeu 48kHz",
        "description": "Nam miền Bắc, phong cách kể chuyện ấm áp, truyền cảm hứng"
    },
    {
        "id": "Quang Sơn",
        "name": "Quang Sơn (Nam · Trung 48kHz ⭐⭐⭐⭐⭐)",
        "lang": "vi",
        "gender": "male",
        "region": "Trung",
        "engine": "VieNeu 48kHz",
        "description": "Nam miền Trung (xứ Huế/Đà Nẵng), chân chất, tự nhiên mộc mạc"
    },
    {
        "id": "Ngọc Trân",
        "name": "Ngọc Trân (Nữ · Trung 48kHz ⭐⭐⭐⭐⭐)",
        "lang": "vi",
        "gender": "female",
        "region": "Trung",
        "engine": "VieNeu 48kHz",
        "description": "Nữ miền Trung (xứ Huế), ngọt ngào, duyên dáng và sâu lắng"
    },
    {
        "id": "Adam bựa",
        "name": "Adam bựa (Nam · Bắc 48kHz ⭐⭐⭐⭐⭐)",
        "lang": "vi",
        "gender": "male",
        "region": "Bắc",
        "engine": "VieNeu 48kHz",
        "description": "Nam miền Bắc, phong cách hài hước, dí dỏm, khẩu ngữ đời thường"
    },
    # Tiếng Việt Fast Preview (Edge-TTS 24 kHz)
    {
        "id": "vi-VN-HoaiMyNeural",
        "name": "Hoài My (Nữ · Bắc Preview ⚡)",
        "lang": "vi",
        "gender": "female",
        "region": "Bắc",
        "engine": "Edge-TTS",
        "description": "Nữ miền Bắc, truyền cảm, tốc độ preview siêu tốc < 1s"
    },
    {
        "id": "vi-VN-NamMinhNeural",
        "name": "Nam Minh (Nam · Bắc Preview ⚡)",
        "lang": "vi",
        "gender": "male",
        "region": "Bắc",
        "engine": "Edge-TTS",
        "description": "Nam thời sự truyền hình, tốc độ preview siêu tốc < 1s"
    },
    # Tiếng Nhật
    {
        "id": "ja-JP-NanamiNeural",
        "name": "Nanami (Nữ ⭐⭐⭐⭐⭐)",
        "lang": "ja",
        "gender": "female",
        "description": "Nữ chuẩn Tokyo, trong trẻo, tự nhiên, nhã nhặn"
    },
    {
        "id": "ja-JP-KeitaNeural",
        "name": "Keita (Nam ⭐⭐⭐⭐⭐)",
        "lang": "ja",
        "gender": "male",
        "description": "Nam trẻ trung, năng động, chuẩn phát thanh NHK"
    },
    # Tiếng Anh — Kokoro ONNX 5★ (Tier 1: Offline, CPU, Apache 2.0)
    {
        "id": "af_heart",
        "name": "Heart (Nữ · Kokoro Offline ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "female",
        "engine": "Kokoro ONNX",
        "description": "Nữ Mỹ biểu cảm, ấm áp, tự nhiên nhất — chạy 100% offline CPU"
    },
    {
        "id": "af_bella",
        "name": "Bella (Nữ · Kokoro Offline ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "female",
        "engine": "Kokoro ONNX",
        "description": "Nữ Mỹ dịu dàng, truyền cảm — chạy 100% offline CPU"
    },
    {
        "id": "am_adam",
        "name": "Adam (Nam · Kokoro Offline ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "male",
        "engine": "Kokoro ONNX",
        "description": "Nam Mỹ trầm ấm, chuyên nghiệp — chạy 100% offline CPU"
    },
    {
        "id": "am_michael",
        "name": "Michael (Nam · Kokoro Offline ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "male",
        "engine": "Kokoro ONNX",
        "description": "Nam Mỹ tự nhiên, phong cách kể chuyện — chạy 100% offline CPU"
    },
    # Tiếng Anh — Edge-TTS Fallback (Tier 2: Online)
    {
        "id": "en-US-AvaNeural",
        "name": "Ava (Nữ Studio HD ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "female",
        "description": "Nữ Mỹ tự nhiên, biểu cảm sống động, AI Neural thế hệ mới"
    },
    {
        "id": "en-US-EmmaNeural",
        "name": "Emma (Nữ Thuyết Minh ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "female",
        "description": "Nữ Mỹ dịu dàng, trong trẻo, phong cách tài liệu cao cấp"
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (Nữ Podcast ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "female",
        "description": "Nữ Mỹ tươi sáng, rõ ràng, nhịp điệu nhanh podcast"
    },
    {
        "id": "en-US-AndrewNeural",
        "name": "Andrew (Nam Studio HD ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "male",
        "description": "Nam Mỹ ấm áp, phong cách hội thoại, tự nhiên xuất sắc"
    },
    {
        "id": "en-US-BrianNeural",
        "name": "Brian (Nam Kể Chuyện ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "male",
        "description": "Nam Mỹ trầm ấm, truyền cảm, cuốn hút phong cách kể chuyện"
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (Nam Thời Sự ⭐⭐⭐⭐⭐)",
        "lang": "en",
        "gender": "male",
        "description": "Nam Mỹ tin cậy, đĩnh đạc, chuẩn phát thanh viên"
    }
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
    "vi-VN-HoaiMyNeural": "Xin chào, đây là giọng đọc Hoài My truyền cảm của AI Workforce.",
    "vi-VN-NamMinhNeural": "Xin chào quý vị, đây là giọng đọc Nam Minh, phong cách thời sự truyền hình.",
    "ja-JP-NanamiNeural": "こんにちは、こちらはナナミの音声プレビューです。",
    "ja-JP-KeitaNeural": "こんにちは、ケイタの音声です。どうぞよろしくお願いします。",
    "en-US-AvaNeural": "Hello there! This is Ava, an expressive and natural neural studio voice.",
    "en-US-EmmaNeural": "Hello, this is Emma, a gentle and professional narration voice.",
    "en-US-JennyNeural": "Hello! This is Jenny, welcome to AI Workforce Video Studio.",
    "en-US-AndrewNeural": "Hello, this is Andrew, a warm and conversational voice for your video.",
    "en-US-BrianNeural": "Hello, this is Brian, an engaging storytelling voice for rich narratives.",
    "en-US-GuyNeural": "Hello, this is Guy, a trustworthy news anchor voice."
}

def get_voice_catalog():
    """Trả về danh mục giọng đọc có sẵn."""
    return VOICE_CATALOG

def get_sample_text(voice_id):
    """Lấy câu thoại mẫu cho từng giọng đọc."""
    return VOICE_SAMPLES.get(voice_id, "Xin chào, đây là âm thanh nghe thử giọng đọc AI.")

def synthesize_line(text, output_path, lang="vi", gender="female", voice=None, speed=1.0, ref_audio=None):
    """
    Tổng hợp một dòng lời thoại thành file âm thanh.
    Ưu tiên VieNeu-TTS v3 Turbo 48 kHz qua global voice_client.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    selected_voice = voice or DEFAULT_VOICES.get(lang, {}).get(gender, DEFAULT_VOICES.get(lang, {}).get("default", "Thùy Dung"))

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
        if ref_audio:
            cmd.extend(["--ref-audio", ref_audio])
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                return json.loads(res.stdout)
            except Exception:
                return {"success": True, "output_path": output_path}

    # =========================================================
    # Tier 1 (EN only): Kokoro ONNX — offline, CPU, Apache 2.0
    # Chất lượng 5★, không cần internet, không cần GPU
    # =========================================================
    if selected_voice in KOKORO_VOICES and os.path.exists(KOKORO_MODEL_PATH) and os.path.exists(KOKORO_VENV_PYTHON):
        kokoro_lang = KOKORO_VOICES[selected_voice]
        kokoro_script = f"""
import sys
sys.path.insert(0, '{os.path.dirname(os.path.abspath(__file__))}')
from kokoro_onnx import Kokoro
import soundfile as sf
kokoro = Kokoro('{KOKORO_MODEL_PATH}', '{KOKORO_VOICES_PATH}')
samples, sr = kokoro.create('''{text.replace("'", "\\'")}''', voice='{selected_voice}', speed={speed}, lang='{kokoro_lang}')
sf.write('{os.path.abspath(output_path)}', samples, sr)
print('OK')
"""
        try:
            res = subprocess.run(
                [KOKORO_VENV_PYTHON, "-c", kokoro_script],
                capture_output=True, text=True, timeout=120
            )
            if res.returncode == 0 and os.path.exists(output_path):
                return {
                    "success": True,
                    "engine": "Kokoro ONNX v1.0 (offline)",
                    "voice": selected_voice,
                    "output_path": os.path.abspath(output_path)
                }
        except Exception:
            pass  # Fall through to Edge-TTS

    # Fallback: Edge-TTS (online, vi/ja/en)
    edge_voice = selected_voice
    if selected_voice in KOKORO_VOICES:
        # Kokoro failed — map to Edge-TTS equivalent
        edge_voice = "en-US-AvaNeural" if gender == "female" else "en-US-AndrewNeural"
    elif not selected_voice.startswith(("vi-VN-", "ja-JP-", "en-US-", "en-GB-")):
        if lang == "ja":
            edge_voice = "ja-JP-NanamiNeural" if gender == "female" else "ja-JP-KeitaNeural"
        elif lang == "en":
            edge_voice = "en-US-AvaNeural" if gender == "female" else "en-US-AndrewNeural"
        else:
            edge_voice = "vi-VN-HoaiMyNeural" if gender == "female" else "vi-VN-NamMinhNeural"
    rate_str = f"+{int((speed - 1.0) * 100)}%" if speed >= 1.0 else f"{int((speed - 1.0) * 100)}%"
    for py_bin in ["/usr/bin/python3", sys.executable]:
        cmd = [
            py_bin, "-m", "edge_tts",
            "--voice", edge_voice,
            "--text", text,
            "--write-media", output_path,
            f"--rate={rate_str}"
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return {
                "success": True,
                "engine": f"edge-tts ({py_bin})",
                "voice": edge_voice,
                "output_path": os.path.abspath(output_path)
            }
        except Exception:
            continue

    return {"success": False, "error": "Không thể tổng hợp giọng đọc qua các engine cục bộ"}

def main():
    parser = argparse.ArgumentParser(description="Bộ tổng hợp âm thanh lồng tiếng")
    parser.add_argument("--text", "-t", required=True, help="Nội dung lời thoại")
    parser.add_argument("--output", "-o", required=True, help="Đường dẫn file âm thanh đầu ra")
    parser.add_argument("--lang", "-l", default="vi", choices=["vi", "ja", "en"], help="Ngôn ngữ")
    parser.add_argument("--gender", "-g", default="female", choices=["female", "male"], help="Giới tính giọng")
    parser.add_argument("--voice", "-v", default=None, help="Mã giọng cụ thể")
    parser.add_argument("--speed", "-s", type=float, default=1.0, help="Tốc độ nói")
    parser.add_argument("--ref-audio", "-r", default=None, help="File âm thanh mẫu để clone giọng")
    args = parser.parse_args()

    result = synthesize_line(
        text=args.text,
        output_path=args.output,
        lang=args.lang,
        gender=args.gender,
        voice=args.voice,
        speed=args.speed,
        ref_audio=args.ref_audio
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
