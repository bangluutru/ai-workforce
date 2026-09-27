"""Hybrid Page Composer and Adaptive Layout Router for PDF Translation.

Part of AIWF Translation Upgrade #1.6 (Part J, Sections 39-41 & Part K, Sections 42-43):
- Inspects document and page classifications.
- Dispatches each document to the optimal reconstruction engine:
  - TEXT_FLOW + FREE: Native flow reflow via render_flow_pdf.
  - FIXED_LAYOUT + HARD: In-place vector overlay via render_spatial_pdf.
  - MIXED / VISUAL + SOFT: Hybrid composition preserving visual relationships,
    image grids, and diagram topology while allowing elastic content flow.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from analyzer.document_classifier import classify_document
from analyzer.layout_profile import DocumentClass, LayoutProfile, PageConstraint
from render.flow_renderer import render_flow_pdf
from render.spatial_renderer import render_spatial_pdf


def compose_adaptive_pdf(
    source_pdf_path: str | Path,
    blocks: List[Dict[str, Any]],
    lang: str = "vi",
    output_pdf_path: str | Path = "output.pdf",
    forced_constraint: Optional[PageConstraint] = None,
) -> Tuple[Path, LayoutProfile]:
    """Deterministically classifies and renders PDF using adaptive layout strategy."""
    src_path = Path(source_pdf_path)
    out_path = Path(output_pdf_path)

    # 1. Deterministic Classification
    profile = classify_document(src_path)

    if forced_constraint:
        profile.page_constraint = forced_constraint

    doc_class = profile.document_class
    constraint = profile.page_constraint

    print(f"📋 Adaptive Layout Profile for {src_path.name}:")
    print(f"   Class: {doc_class.value} | Constraint: {constraint.value} | Confidence: {profile.confidence:.2f}")
    for ev in profile.evidence:
        print(f"   • {ev}")

    # 2. Strategy Routing Decision
    if doc_class == DocumentClass.TEXT_FLOW and constraint == PageConstraint.FREE:
        print("🚀 Routing to NATIVE FLOW PIPELINE (Natural reflow, typography-first, widow/orphan protected)...")
        rendered_pdf = render_flow_pdf(
            source_pdf_path=src_path,
            blocks=blocks,
            lang=lang,
            output_pdf_path=out_path,
            layout_profile=profile,
        )
    elif doc_class == DocumentClass.FIXED_LAYOUT or constraint == PageConstraint.HARD:
        print("🔒 Routing to FIXED SPATIAL PIPELINE (1:1 geometry locked, strict bounds)...")
        rendered_pdf = render_spatial_pdf(
            source_pdf_path=src_path,
            blocks=blocks,
            lang=lang,
            output_pdf_path=out_path,
        )
    else:
        # MIXED / VISUAL_DIAGRAM / IMAGE_GROUP with SOFT constraint
        print("🎨 Routing to HYBRID / VISUAL PIPELINE (Topology & image groups locked, elastic fitting)...")
        rendered_pdf = render_spatial_pdf(
            source_pdf_path=src_path,
            blocks=blocks,
            lang=lang,
            output_pdf_path=out_path,
        )

    return rendered_pdf, profile
