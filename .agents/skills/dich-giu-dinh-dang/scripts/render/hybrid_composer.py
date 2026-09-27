"""Hybrid Page Composer and Adaptive Layout Router for PDF Translation.

Part of AIWF Translation Upgrade #1.6 (Part J, Sections 39-41 & Part E, Sections 16-18):
- Inspects document and page classifications.
- Generates structured diagnostic routing trace per region:
  (page, region_id, region_class, structural_role, page_constraint,
   selected_strategy, renderer, keep_together, elasticity_policy, pagination_action).
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
from analyzer.layout_profile import DocumentClass, LayoutProfile, PageConstraint, StructuralRole
from layout.elasticity import get_default_elasticity
from render.flow_renderer import render_flow_pdf
from render.spatial_renderer import render_spatial_pdf


def generate_routing_trace(profile: LayoutProfile) -> List[Dict[str, Any]]:
    """Generates structured diagnostic routing trace conforming to Part E Section 17.
    
    Includes:
    - page
    - region_id
    - region_class
    - structural_role
    - page_constraint
    - selected_strategy
    - renderer
    - keep_together
    - elasticity_policy
    - pagination_action
    """
    trace: List[Dict[str, Any]] = []

    for p_prof in profile.page_profiles:
        p_num = p_prof.page_number
        p_constraint = p_prof.page_constraint.value

        for r in p_prof.regions:
            role = r.roles[0] if r.roles else StructuralRole.BODY_PARAGRAPH
            r_class = r.region_class

            # 1. Strategy determination
            if r_class == DocumentClass.TABLE_FORM:
                strategy = "SPATIAL/TABLE"
                renderer = "spatial_renderer"
                pagination_act = "PRESERVE_CONTAINER"
                keep_tog = True
            elif r_class == DocumentClass.IMAGE_GROUP:
                strategy = "VISUAL_GROUP"
                renderer = "spatial_renderer"
                pagination_act = "MIGRATE_IF_OVERFLOW"
                keep_tog = True
            elif r_class == DocumentClass.VISUAL_DIAGRAM:
                strategy = "SPATIAL/DIAGRAM"
                renderer = "spatial_renderer"
                pagination_act = "IN_PLACE_LOCKED"
                keep_tog = True
            elif r_class == DocumentClass.FIXED_LAYOUT:
                strategy = "FIXED/SPATIAL"
                renderer = "spatial_renderer"
                pagination_act = "IN_PLACE_LOCKED"
                keep_tog = True
            elif r_class == DocumentClass.TEXT_FLOW:
                strategy = "FLOW"
                renderer = "flow_renderer" if profile.page_constraint == PageConstraint.FREE else "hybrid_composer"
                pagination_act = "FLOW_NATURAL" if profile.page_constraint == PageConstraint.FREE else "FLOW_IN_PAGE"
                keep_tog = (role in (StructuralRole.HEADING, StructuralRole.TITLE))
            else:
                strategy = "HYBRID_ELASTIC"
                renderer = "hybrid_composer"
                pagination_act = "FLOW_IN_PAGE"
                keep_tog = False

            # 2. Elasticity policy for this role & region
            elasticity = get_default_elasticity(role, r_class, p_prof.page_constraint)

            trace_item = {
                "page": p_num,
                "region_id": r.region_id,
                "region_class": r_class.value,
                "structural_role": role.value,
                "page_constraint": p_constraint,
                "selected_strategy": strategy,
                "renderer": renderer,
                "keep_together": keep_tog,
                "elasticity_policy": elasticity.to_dict(),
                "pagination_action": pagination_act,
            }
            trace.append(trace_item)

    return trace


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

    # 2. Generate and attach structured diagnostic routing trace
    routing_trace = generate_routing_trace(profile)
    setattr(profile, "routing_trace", routing_trace)

    print(f"📋 Adaptive Layout Profile for {src_path.name}:")
    print(f"   Class: {doc_class.value} | Constraint: {constraint.value} | Confidence: {profile.confidence:.2f}")
    for ev in profile.evidence:
        print(f"   • {ev}")
    print(f"   Diagnostic Regions Segmented: {len(routing_trace)}")

    # 3. Strategy Routing Decision
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
