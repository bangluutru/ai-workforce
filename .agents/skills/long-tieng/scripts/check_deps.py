#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_deps.py — Kiểm tra môi trường cho kỹ năng Lồng Tiếng (long-tieng).
Zero External API: ffmpeg + engine giọng đọc OFFLINE dùng chung (_shared/media/tts.py — Luật R7):
VieNeu-TTS (tiếng Việt), Kokoro ONNX + misaki[ja] (tiếng Anh/Nhật). Không dùng dịch vụ giọng đọc trực tuyến (Luật R7).
"""
import os
import subprocess
import sys

SHARED_MEDIA = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_shared", "media"))
sys.path.insert(0, SHARED_MEDIA)

import tts  # noqa: E402
from ffmpeg_tools import ffmpeg_bin, has_filter  # noqa: E402


def main():
    print("🔍 Kiểm tra phụ thuộc cho kỹ năng Lồng Tiếng (long-tieng)...")
    ff = ffmpeg_bin()
    ff_ok = os.path.isabs(ff) and os.path.isfile(ff)
    print(f" • FFmpeg: {'✅ ' + ff if ff_ok else '❌ thiếu ffmpeg (brew install ffmpeg-full)'}")

    vn = tts.vieneu_python()
    print(f" • VieNeu-TTS 48 kHz (tiếng Việt): {'✅ ' + vn if vn else '❌ chưa cài gói vieneu → ' + tts.INSTALL_HINT}")

    ko = tts.kokoro_python()
    model, _ = tts.kokoro_model_paths()
    print(f" • Kokoro ONNX (tiếng Anh/Nhật): {'✅ ' + ko if ko else '❌ chưa cài kokoro-onnx → ' + tts.INSTALL_HINT}")
    print(f" • Model Kokoro: {'✅ ' + model if model else '❌ chưa tải vào ' + tts.KOKORO_DIR + ' → ' + tts.INSTALL_HINT}")
    if ko:
        ja = subprocess.run([ko, "-c", "from misaki import ja"], capture_output=True).returncode == 0
        print(f" • G2P tiếng Nhật misaki[ja]: {'✅' if ja else '⚠️ chưa cài → tiếng Nhật không tổng hợp được (' + tts.INSTALL_HINT + ')'}")

    print(f" • rubberband (co giãn tự nhiên): {'✅' if has_filter('rubberband') else '⚠️ không có → dùng atempo (brew install ffmpeg-full)'}")
    print(f" • libass (khắc phụ đề): {'✅' if has_filter('ass') else '⚠️ không có → phụ đề mềm (brew install ffmpeg-full)'}")
    try:
        import faster_whisper  # noqa: F401
        print(" • faster-whisper (kiểm tra phát âm): ✅")
    except ImportError:
        print(" • faster-whisper (kiểm tra phát âm): ⚠️ chưa cài → bỏ qua kiểm tra phát âm (pip3 install faster-whisper)")

    if not ff_ok:
        print("\n❌ Cần FFmpeg để ghép nối âm thanh và render video lồng tiếng.")
        return 1
    if not vn and not (ko and model):
        print("\n❌ Chưa có engine giọng đọc offline nào. Chạy: " + tts.INSTALL_HINT)
        return 1
    print("\n✅ Môi trường sẵn sàng phục vụ tác vụ lồng tiếng video!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
