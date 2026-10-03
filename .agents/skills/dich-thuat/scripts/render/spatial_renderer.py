"""Spatial In-Place Renderer for Fixed and Visual PDF Layouts.

Part of AIWF Translation Upgrade #1.6:
- Provides 1:1 In-Place spatial reconstruction with redaction and vector preservation.
- Used for FIXED_LAYOUT (certificates, posters) and visual/mixed pages with locked geometry.
- Wraps the tested Smart Reflow v4.0 engine.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path to import typst_overlay
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from typst_overlay import (
    preserve_pdf_typst,
    build_translation_map,
    find_best_translation,
    _classify_block_tier,
    _build_typst_page_source,
    _compute_safe_expansion_budget,
    TIER_TITLE,
    TIER_HEADING,
    TIER_BODY,
    TIER_TABLE_HEADER,
    TIER_TABLE_CELL,
    TIER_CAPTION,
    TIER_DIAGRAM_LABEL,
    TIER_TIMELINE_LABEL,
    TIER_HEADER_FOOTER,
    FONT_TIERS,
)


def render_spatial_pdf(
    source_pdf_path: str | Path,
    blocks: List[Dict[str, Any]],
    lang: str = "vi",
    output_pdf_path: str | Path = "output.pdf",
) -> Path:
    """Renders a PDF using spatial in-place redaction and vector overlay."""
    return preserve_pdf_typst(
        source_pdf_path=Path(source_pdf_path),
        blocks=blocks,
        lang=lang,
        output_pdf_path=Path(output_pdf_path),
    )
