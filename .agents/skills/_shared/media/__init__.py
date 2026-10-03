"""AIWF shared media engines (Luật R7).

Import từ script trong skill:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared" / "media"))
    import dub_engine                      # tổng hợp + nghe lại + co giãn + trộn ducking
    from tts import synthesize_line        # TTS offline: VieNeu (vi), Kokoro (en/ja)
    from ass_generator import generate_ass # phụ đề ASS/SRT

Các module trong thư mục này import lẫn nhau theo tên phẳng (`from linebreak import ...`), nên khi
được nạp dạng gói (`from media import x`) thư mục này cũng được thêm vào sys.path.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
