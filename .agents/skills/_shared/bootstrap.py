#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bootstrap.py — Điểm vào chuẩn để script trong skill dùng engine chung `_shared/` (Luật R7).

Cách dùng (trong .agents/skills/<skill>/scripts/<file>.py):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
    import bootstrap  # noqa: F401,E402  — thêm _shared, _shared/media, _shared/pdf, _shared/docx vào sys.path

    from tts import synthesize_line            # _shared/media/tts.py
    from dub_engine import dub_audio           # _shared/media/dub_engine.py
    from ass_generator import generate_ass     # _shared/media/ass_generator.py
    from doc_ingest_bridge import run_ingest   # _shared/doc_ingest_bridge.py
    from legal_report import build_legal_docx  # _shared/docx/legal_report.py
    from verify_retention import LayoutRetentionAuditor   # _shared/pdf/verify_retention.py

Lưu ý: thư mục `_shared/docx/` KHÔNG phải gói Python (trùng tên thư viện python-docx) — import thẳng tên module.

Danh mục engine: .agents/skills/_shared/ENGINES.md (người đọc) · engines.json (máy đọc).
"""
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parent
SKILLS = SHARED.parent
WORKSPACE = SKILLS.parent.parent
MEDIA = SHARED / "media"
PDF = SHARED / "pdf"
DOCX = SHARED / "docx"
HTML = SHARED / "html"
OFFICE = SHARED / "office"
LAYOUT = SHARED / "layout"
FONTS = SHARED / "fonts"
MODELS = SHARED / "models"          # gitignored — tải bởi scripts/auto-setup.sh
REGISTRY = SHARED / "engines.json"

for _p in (DOCX, PDF, MEDIA, HTML, OFFICE, LAYOUT, SHARED):   # SHARED đứng đầu sys.path sau vòng lặp
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def engine(engine_id: str) -> dict:
    """Tra một engine trong engines.json theo id (vd 'media.tts'); KeyError nếu chưa đăng ký."""
    import json
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for e in data.get("engines", []):
        if e["id"] == engine_id:
            return e
    raise KeyError(f"Engine '{engine_id}' chưa đăng ký trong {REGISTRY}")
