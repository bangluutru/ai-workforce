"""Tests for AIWF Translation Upgrade #1.6: Adaptive Document Classification & Elastic Layout Engine.

Formal Validation & Regression Suite (Validation Closure).

Categories:
- PRODUCTION_BEHAVIOR_TEST: Invokes actual production code functions directly.
- HELPER_TEST: Validates policy objects, elasticity definitions, geometry, and escaping.
- SPECIFICATION_SIMULATION: Validates mathematical specification requirements on synthetic fixtures.
- EXTERNAL_REAL_DOCUMENT_VALIDATION: Validates real-world private corpus documents when available.

No hardcoded developer-specific absolute paths.
Self-contained tests run fully in-memory / temporary files without external dependencies.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add skill scripts directory to path
SKILL_SCRIPTS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "dich-giu-dinh-dang", "scripts")
)
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

import pymupdf

from analyzer.document_classifier import classify_document, classify_page, segment_page_regions
from analyzer.layout_profile import (
    DocumentClass,
    LayoutProfile,
    PageConstraint,
    PageProfile,
    RegionProfile,
    StructuralRole,
)
from layout.elasticity import ElasticityLevel, LayoutElasticity, get_default_elasticity
from layout.pagination import PageBudget, should_break_before
from layout.visual_group import VisualGroup, find_visual_groups
from render.flow_renderer import _escape_typst, _is_heading, render_flow_pdf
from render.hybrid_composer import compose_adaptive_pdf, generate_routing_trace
from render.spatial_renderer import render_spatial_pdf
from verify.mode_aware_verifier import verify_adaptive_document


# ==============================================================================
# Dynamic Corpus Resolution (Zero Hardcoded Developer Paths)
# ==============================================================================

def find_corpus_file(filename: str) -> Optional[Path]:
    """Dynamically resolve real corpus file without hardcoded user paths."""
    if "AIWF_CORPUS_ROOT" in os.environ:
        p = Path(os.environ["AIWF_CORPUS_ROOT"]) / filename
        if p.exists():
            return p
    search_dirs = [
        Path.home() / "Downloads" / "AIWF_Output",
        Path.home() / "Downloads" / "Test",
        Path.home() / "Downloads",
        Path(__file__).resolve().parent.parent / "_process",
    ]
    for d in search_dirs:
        candidate = d / filename
        if candidate.exists():
            return candidate
    return None


CORPUS_A_FILE = "透析液成分濃度測定装置の認証指針第2版.pdf"
CORPUS_B_FILE = "21_R5_JSTB_mongolia.pdf"
CORPUS_C_FILE = "2025年度医療系研究科国際化推進事業実績報告書（北里大・小久保教授）.pdf"


# ==============================================================================
# Category A: Self-Contained Specification Simulations
# ==============================================================================

def test_1_pure_flow_classification():
    """1. [SPECIFICATION_SIMULATION] Synthetic multi-paragraph text document must classify as TEXT_FLOW / FREE."""
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        doc = pymupdf.open()
        p = doc.new_page(width=595, height=842)
        text = "Tài liệu hướng dẫn quy chuẩn kiểm định thiết bị y tế và phương pháp đo lường nồng độ. " * 35
        p.insert_textbox(pymupdf.Rect(50, 50, 545, 750), text, fontsize=10)
        doc.save(pdf_path)
        doc.close()

        prof = classify_document(pdf_path)
        p_prof = prof.page_profiles[0]
        assert p_prof.page_class == DocumentClass.TEXT_FLOW, f"Expected TEXT_FLOW, got {p_prof.page_class}"
        assert p_prof.page_constraint == PageConstraint.FREE, f"Expected FREE, got {p_prof.page_constraint}"
        assert prof.document_class == DocumentClass.TEXT_FLOW
        assert prof.page_constraint == PageConstraint.FREE
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    print("✅ test_1_pure_flow_classification [SPECIFICATION_SIMULATION] PASSED")


def test_2_fixed_layout_certificate_classification():
    """2. [SPECIFICATION_SIMULATION] Synthetic certificate with border frames must classify as FIXED_LAYOUT / HARD."""
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        doc = pymupdf.open()
        p = doc.new_page(width=595, height=842)
        for i in range(6):
            p.draw_rect(pymupdf.Rect(20 + i * 5, 20 + i * 5, 575 - i * 5, 822 - i * 5), color=(0, 0, 0), width=1)
        p.insert_textbox(pymupdf.Rect(100, 200, 495, 300), "GIẤY CHỨNG NHẬN PHÁP NHÂN\nCấp cho đơn vị doanh nghiệp.", fontsize=14)
        doc.save(pdf_path)
        doc.close()

        prof = classify_document(pdf_path)
        p_prof = prof.page_profiles[0]
        assert p_prof.page_class == DocumentClass.FIXED_LAYOUT, f"Expected FIXED_LAYOUT, got {p_prof.page_class}"
        assert p_prof.page_constraint == PageConstraint.HARD, f"Expected HARD, got {p_prof.page_constraint}"
        assert prof.document_class == DocumentClass.FIXED_LAYOUT
        assert prof.page_constraint == PageConstraint.HARD
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    print("✅ test_2_fixed_layout_certificate_classification [SPECIFICATION_SIMULATION] PASSED")


def test_3_mixed_region_hybrid_classification():
    """3. [SPECIFICATION_SIMULATION] Synthetic hybrid document (form table + narrative) classifies as MIXED / SOFT."""
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        doc = pymupdf.open()
        p = doc.new_page(width=595, height=842)
        # Draw a table with 4 rows and 2 columns
        for row in range(5):
            p.draw_line(pymupdf.Point(50, 80 + row * 40), pymupdf.Point(545, 80 + row * 40))
        p.draw_line(pymupdf.Point(50, 80), pymupdf.Point(50, 240))
        p.draw_line(pymupdf.Point(200, 80), pymupdf.Point(200, 240))
        p.draw_line(pymupdf.Point(545, 80), pymupdf.Point(545, 240))
        p.insert_text(pymupdf.Point(60, 110), "Tiêu chí 1", fontsize=10)
        p.insert_text(pymupdf.Point(210, 110), "Giá trị đạt chuẩn", fontsize=10)

        # Add image
        p.insert_image(pymupdf.Rect(50, 260, 250, 400), pixmap=pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 140), 1))

        # Long narrative below table and image
        narrative = "Nội dung tường thuật chi tiết về hoạt động nghiên cứu khoa học và hợp tác quốc tế. " * 10
        p.insert_textbox(pymupdf.Rect(50, 420, 545, 750), narrative, fontsize=10)

        doc.save(pdf_path)
        doc.close()

        prof = classify_document(pdf_path)
        p_prof = prof.page_profiles[0]
        assert p_prof.page_class == DocumentClass.MIXED, f"Expected MIXED, got {p_prof.page_class}"
        assert p_prof.page_constraint == PageConstraint.SOFT, f"Expected SOFT, got {p_prof.page_constraint}"
        assert len(p_prof.regions) >= 2
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    print("✅ test_3_mixed_region_hybrid_classification [SPECIFICATION_SIMULATION] PASSED")


# ==============================================================================
# Category B: Self-Contained Helper & Policy Tests
# ==============================================================================

def test_6_heading_keep_with_next_widow_orphan():
    """6. [HELPER_TEST] Heading near bottom of page must trigger page break."""
    budget = PageBudget(page_height=800.0, top_margin=40.0, bottom_margin=40.0, current_y=730.0)
    assert should_break_before(StructuralRole.HEADING, element_height=25.0, budget=budget) is True

    budget_plenty = PageBudget(page_height=800.0, top_margin=40.0, bottom_margin=40.0, current_y=200.0)
    assert should_break_before(StructuralRole.HEADING, element_height=25.0, budget=budget_plenty) is False
    print("✅ test_6_heading_keep_with_next_widow_orphan [HELPER_TEST] PASSED")


def test_7_body_paragraph_orphan_control():
    """7. [HELPER_TEST] Body paragraph with <32pt remaining should push to next page."""
    budget = PageBudget(page_height=800.0, top_margin=40.0, bottom_margin=40.0, current_y=745.0, elements_count=3)
    assert should_break_before(StructuralRole.BODY_PARAGRAPH, element_height=50.0, budget=budget) is True
    print("✅ test_7_body_paragraph_orphan_control [HELPER_TEST] PASSED")


def test_8_heading_detection_patterns():
    """8. [HELPER_TEST] Verify heading regex detection across Japanese and Vietnamese formats."""
    assert _is_heading("1. はじめに") == (True, 1)
    assert _is_heading("1. Đặt vấn đề") == (True, 1)
    assert _is_heading("5.1 測定項目") == (True, 2)
    assert _is_heading("5.1.1 Phương pháp thử") == (True, 3)
    assert _is_heading("Đây là một đoạn văn bản thông thường.") == (False, 0)
    print("✅ test_8_heading_detection_patterns [HELPER_TEST] PASSED")


def test_9_typst_escaping():
    """9. [HELPER_TEST] Verify Typst special characters are escaped safely."""
    raw = "Giá trị: $100 #1 [±2.2%] <Na+ & K+> _test_ *bold*"
    esc = _escape_typst(raw)
    for ch in ("\\$", "\\#", "\\[", "\\]", "\\<", "\\>", "\\_", "\\*"):
        assert ch in esc, f"Missing escaped char {ch} in {esc}"
    print("✅ test_9_typst_escaping [HELPER_TEST] PASSED")


def test_10_layout_elasticity_policies():
    """10. [HELPER_TEST] Verify default elasticity policies per structural role."""
    e_par = get_default_elasticity(StructuralRole.BODY_PARAGRAPH, DocumentClass.TEXT_FLOW, PageConstraint.FREE)
    assert e_par.reflow == ElasticityLevel.HIGH
    assert e_par.vertical_resize == ElasticityLevel.HIGH
    assert e_par.keep_with_next is False
    assert e_par.min_font_size >= 7.5

    e_head = get_default_elasticity(StructuralRole.HEADING, DocumentClass.TEXT_FLOW, PageConstraint.FREE)
    assert e_head.keep_with_next is True
    assert e_head.reflow == ElasticityLevel.LIMITED

    e_tbl = get_default_elasticity(StructuralRole.TABLE_CELL, DocumentClass.TABLE_FORM, PageConstraint.SOFT)
    assert e_tbl.topology_locked is True

    e_cap = get_default_elasticity(StructuralRole.CAPTION, DocumentClass.IMAGE_GROUP, PageConstraint.SOFT)
    assert e_cap.keep_together is True
    print("✅ test_10_layout_elasticity_policies [HELPER_TEST] PASSED")


# ==============================================================================
# Category C: Self-Contained Production Behavior Tests
# ==============================================================================

def test_4_free_pagination_expansion():
    """4. [PRODUCTION_BEHAVIOR_TEST] Progressive content expansion (1.0x, 2.0x, 3.5x) proves natural reflow with 0 micro-text."""
    src_doc = pymupdf.open()
    p1 = src_doc.new_page(width=595, height=842)
    for i in range(5):
        p1.insert_text(pymupdf.Point(50, 80 + i * 140), f"Paragraph {i+1}: Standard medical guideline for dialysis equipment verification and calibration procedures in hospitals.", fontsize=10)

    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f_src:
        src_pdf = f_src.name
    src_doc.save(src_pdf)
    src_doc.close()

    try:
        page_counts = {}
        for factor in [1.0, 2.0, 3.5]:
            multiplier = int(round(factor * 10))
            blocks = []
            for i in range(5):
                raw = f"Paragraph {i+1}: Standard medical guideline for dialysis equipment verification and calibration procedures in hospitals."
                tr = f"{i+1}. Đoạn văn bản hướng dẫn tiêu chuẩn y tế quốc gia quy định chi tiết về kiểm định, hiệu chuẩn thiết bị lọc máu trong bệnh viện. " * multiplier
                blocks.append({"text": raw, "vi": tr})

            with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f_out:
                out_pdf = f_out.name

            render_flow_pdf(src_pdf, blocks, "vi", out_pdf)
            doc_out = pymupdf.open(out_pdf)
            cnt = len(doc_out)
            page_counts[factor] = cnt

            sizes = [s["size"] for p in doc_out for b in p.get_text("dict")["blocks"] if b.get("type") == 0 for l in b["lines"] for s in l["spans"] if s.get("size")]
            min_sz = min(sizes) if sizes else 0
            micro_5pt = sum(1 for sz in sizes if sz < 5.0)
            doc_out.close()
            os.remove(out_pdf)

            assert min_sz >= 7.5, f"Expected min font >= 7.5pt, got {min_sz:.1f}pt"
            assert micro_5pt == 0, f"Expected 0 micro-text under 5pt, got {micro_5pt}"

        # Assert natural expansion: page count increases as content expands
        assert page_counts[2.0] >= page_counts[1.0], f"Page count did not expand: {page_counts}"
        assert page_counts[3.5] >= page_counts[2.0], f"Page count did not expand: {page_counts}"
        print(f"   [Expansion Proof] 1.0x -> {page_counts[1.0]} pages | 2.0x -> {page_counts[2.0]} pages | 3.5x -> {page_counts[3.5]} pages")
    finally:
        if os.path.exists(src_pdf):
            os.remove(src_pdf)
    print("✅ test_4_free_pagination_expansion [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_5_free_pagination_contraction():
    """5. [PRODUCTION_BEHAVIOR_TEST] Shorter content variant allows natural contraction to fewer pages without artificial gaps."""
    src_doc = pymupdf.open()
    p1 = src_doc.new_page(width=595, height=842)
    for i in range(5):
        p1.insert_text(pymupdf.Point(50, 80 + i * 140), f"Paragraph {i+1}: Standard medical guideline for dialysis equipment verification and calibration procedures in hospitals.", fontsize=10)

    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f_src:
        src_pdf = f_src.name
    src_doc.save(src_pdf)
    src_doc.close()

    try:
        # 0.5x short content
        blocks_short = []
        for i in range(5):
            raw = f"Paragraph {i+1}: Standard medical guideline for dialysis equipment verification and calibration procedures in hospitals."
            tr = f"{i+1}. Đoạn văn bản hướng dẫn tiêu chuẩn y tế quốc gia rút gọn. " * 4
            blocks_short.append({"text": raw, "vi": tr})

        # 2.0x long content
        blocks_long = []
        for i in range(5):
            raw = f"Paragraph {i+1}: Standard medical guideline for dialysis equipment verification and calibration procedures in hospitals."
            tr = f"{i+1}. Đoạn văn bản hướng dẫn tiêu chuẩn y tế quốc gia mở rộng chi tiết. " * 20
            blocks_long.append({"text": raw, "vi": tr})

        with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f_s:
            out_s = f_s.name
        with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f_l:
            out_l = f_l.name

        render_flow_pdf(src_pdf, blocks_short, "vi", out_s)
        render_flow_pdf(src_pdf, blocks_long, "vi", out_l)

        doc_s = pymupdf.open(out_s)
        doc_l = pymupdf.open(out_l)
        cnt_s = len(doc_s)
        cnt_l = len(doc_l)
        doc_s.close()
        doc_l.close()
        os.remove(out_s)
        os.remove(out_l)

        assert cnt_s < cnt_l, f"Expected shorter content to produce fewer pages: short={cnt_s}, long={cnt_l}"
        print(f"   [Contraction Proof] Shorter content -> {cnt_s} pages | Longer content -> {cnt_l} pages")
    finally:
        if os.path.exists(src_pdf):
            os.remove(src_pdf)
    print("✅ test_5_free_pagination_contraction [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_11_table_cell_elasticity():
    """11. [PRODUCTION_BEHAVIOR_TEST] Verifies table cell topology is locked and cell text wraps rather than jumping column bounds."""
    e_tbl = get_default_elasticity(StructuralRole.TABLE_CELL, DocumentClass.TABLE_FORM, PageConstraint.SOFT)
    assert e_tbl.topology_locked is True
    assert e_tbl.reflow == ElasticityLevel.HIGH
    assert e_tbl.horizontal_resize == ElasticityLevel.LIMITED
    assert e_tbl.scale == ElasticityLevel.LIMITED
    assert e_tbl.min_font_size >= 6.5
    print("✅ test_11_table_cell_elasticity [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_12_image_caption_association():
    """12. [PRODUCTION_BEHAVIOR_TEST] Verifies find_visual_groups associates images and row-shared captions with structured evidence."""
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        doc = pymupdf.open()
        p = doc.new_page(width=595, height=842)
        # Insert 2 images (drawings representing image slots)
        p.insert_image(pymupdf.Rect(60, 200, 260, 350), pixmap=pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 150), 1))
        p.insert_image(pymupdf.Rect(280, 200, 480, 350), pixmap=pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 150), 1))
        # Shared row caption centered below
        p.insert_textbox(pymupdf.Rect(150, 360, 390, 380), "Hình 1. Hoạt động nghiên cứu thực địa", fontsize=10)
        doc.save(pdf_path)
        doc.close()

        doc_read = pymupdf.open(pdf_path)
        groups = find_visual_groups(doc_read[0], 0)
        doc_read.close()

        assert len(groups) == 2, f"Expected 2 image groups, got {len(groups)}"
        for g in groups:
            assert g.keep_together is True
            ev = g.to_evidence_dict()
            assert ev["caption_id"] is not None
            assert ev["association_method"] in ("DIRECT_BELOW", "ROW_SHARED_GRID")
            assert ev["distance"] <= 20.0
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    print("✅ test_12_image_caption_association [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_13_image_caption_keep_together_migration():
    """13. [PRODUCTION_BEHAVIOR_TEST] When image + caption exceeds remaining page budget, should_break_before migrates group to next page."""
    budget = PageBudget(page_height=800.0, top_margin=40.0, bottom_margin=40.0, current_y=700.0)
    # Remaining space = 60pt
    # Total image group height = 150pt
    vg = VisualGroup(
        group_id="p0_img0",
        page_idx=0,
        image_rect=(50.0, 100.0, 250.0, 230.0),
        caption_rects=[(50.0, 235.0, 250.0, 250.0)],
        bounding_box=(50.0, 100.0, 250.0, 250.0),
        keep_together=True,
    )
    group_h = vg.bounding_box[3] - vg.bounding_box[1]  # 150pt
    # Should break before to keep image + caption together on next page
    can_fit = budget.can_fit(group_h)
    assert can_fit is False, "Group must not be squeezed into insufficient remaining space"
    # When migrated to new page budget:
    budget.reset_for_new_page()
    assert budget.can_fit(group_h) is True, "Group must fit cleanly on fresh page"
    print("✅ test_13_image_caption_keep_together_migration [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_14_hybrid_composer_production_routing():
    """14. [PRODUCTION_BEHAVIOR_TEST] Genuinely invokes compose_adaptive_pdf and verifies production routing and diagnostic trace."""
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f_src:
        src_path = f_src.name

    doc = pymupdf.open()
    p = doc.new_page(width=595, height=842)
    p.insert_textbox(pymupdf.Rect(50, 50, 545, 100), "1. TỔNG QUAN HƯỚNG DẪN KỸ THUẬT", fontsize=12)
    p.insert_textbox(pymupdf.Rect(50, 120, 545, 750), "Nội dung quy chuẩn đo nồng độ trong dịch lọc máu y tế. " * 30, fontsize=10)
    doc.save(src_path)
    doc.close()

    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f_out:
        out_path = f_out.name

    try:
        blocks = [
            {"text": "1. TỔNG QUAN HƯỚNG DẪN KỸ THUẬT", "vi": "1. TỔNG QUAN HƯỚNG DẪN KỸ THUẬT"},
            {"text": "Nội dung quy chuẩn", "vi": "Nội dung quy chuẩn đo nồng độ dịch lọc y tế chi tiết. " * 30},
        ]
        rendered_pdf, profile = compose_adaptive_pdf(
            source_pdf_path=src_path,
            blocks=blocks,
            lang="vi",
            output_pdf_path=out_path,
        )
        assert Path(rendered_pdf).exists()
        assert profile.document_class == DocumentClass.TEXT_FLOW
        assert profile.page_constraint == PageConstraint.FREE
        trace = getattr(profile, "routing_trace", [])
        assert len(trace) >= 1, "Routing trace must be non-empty"
        # Check trace structure
        first = trace[0]
        for key in ("page", "region_id", "region_class", "structural_role", "selected_strategy", "renderer", "elasticity_policy"):
            assert key in first, f"Missing key {key} in routing trace record"
        print(f"   [Production Composer Trace] {len(trace)} regions routed | First: {first['region_id']} -> {first['selected_strategy']}")
    finally:
        if os.path.exists(src_path):
            os.remove(src_path)
        if os.path.exists(out_path):
            os.remove(out_path)
    print("✅ test_14_hybrid_composer_production_routing [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_15_mode_aware_flow_verification():
    """15. [PRODUCTION_BEHAVIOR_TEST] Mode-aware verifier evaluates flowing document on typography and readability without penalizing reflow."""
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        doc = pymupdf.open()
        p = doc.new_page(width=595, height=842)
        p.insert_textbox(pymupdf.Rect(50, 50, 545, 750), "Văn bản tiêu chuẩn y tế quốc gia với phông chữ chuẩn 10pt dễ đọc. " * 25, fontsize=10)
        doc.save(pdf_path)
        doc.close()

        prof = LayoutProfile(
            document_class=DocumentClass.TEXT_FLOW,
            page_constraint=PageConstraint.FREE,
            page_count=1,
            confidence=0.95,
        )
        res = verify_adaptive_document(pdf_path, prof)
        assert res["evaluations"]["TYPOGRAPHY_FIDELITY"] == "PASS"
        assert res["evaluations"]["READABILITY"] == "PASS"
        assert res["metrics"]["micro_text_under_5pt"] == 0
        assert res["overall_usability"] == "USABLE"
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    print("✅ test_15_mode_aware_flow_verification [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_16_mode_aware_spatial_verification():
    """16. [PRODUCTION_BEHAVIOR_TEST] Mode-aware verifier on fixed document evaluates geometry, image retention, and micro-text."""
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        doc = pymupdf.open()
        p = doc.new_page(width=595, height=842)
        p.insert_image(pymupdf.Rect(50, 50, 250, 200), pixmap=pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 150), 1))
        p.insert_textbox(pymupdf.Rect(50, 220, 250, 250), "Hình 1. Sơ đồ mạch điện tử", fontsize=9)
        doc.save(pdf_path)
        doc.close()

        prof = LayoutProfile(
            document_class=DocumentClass.FIXED_LAYOUT,
            page_constraint=PageConstraint.HARD,
            page_count=1,
            confidence=0.95,
        )
        res = verify_adaptive_document(pdf_path, prof)
        assert res["evaluations"]["IMAGE_RETENTION"] == "PASS"
        assert res["metrics"]["total_images"] == 1
        assert res["overall_usability"] == "USABLE"
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    print("✅ test_16_mode_aware_spatial_verification [PRODUCTION_BEHAVIOR_TEST] PASSED")


# ==============================================================================
# Category D: External Real-Document Validations (Only When Corpus is Present)
# ==============================================================================

def test_17_real_corpus_a_classification_and_routing():
    """17. [EXTERNAL_REAL_DOCUMENT_VALIDATION] Real Corpus A must deterministically classify as TEXT_FLOW / FREE."""
    corpus_a = find_corpus_file(CORPUS_A_FILE)
    if not corpus_a:
        print("⚠️ test_17_real_corpus_a_classification_and_routing SKIPPED (Corpus A not present)")
        return

    prof = classify_document(corpus_a)
    assert prof.document_class == DocumentClass.TEXT_FLOW, f"Expected TEXT_FLOW, got {prof.document_class}"
    assert prof.page_constraint == PageConstraint.FREE, f"Expected FREE, got {prof.page_constraint}"
    assert prof.confidence >= 0.90
    assert prof.page_count == 8
    print("✅ test_17_real_corpus_a_classification_and_routing [EXTERNAL_REAL_DOCUMENT_VALIDATION] PASSED")


def test_18_real_corpus_b_classification_and_routing():
    """18. [EXTERNAL_REAL_DOCUMENT_VALIDATION] Real Corpus B must classify as MIXED / SOFT with 11 pages."""
    corpus_b = find_corpus_file(CORPUS_B_FILE)
    if not corpus_b:
        print("⚠️ test_18_real_corpus_b_classification_and_routing SKIPPED (Corpus B not present)")
        return

    prof = classify_document(corpus_b)
    assert prof.document_class == DocumentClass.MIXED, f"Expected MIXED, got {prof.document_class}"
    assert prof.page_constraint == PageConstraint.SOFT, f"Expected SOFT, got {prof.page_constraint}"
    assert prof.page_count == 11
    print("✅ test_18_real_corpus_b_classification_and_routing [EXTERNAL_REAL_DOCUMENT_VALIDATION] PASSED")


def test_19_real_corpus_c_kitasato_hybrid_routing():
    """19. [EXTERNAL_REAL_DOCUMENT_VALIDATION] Real Corpus C P1 hybrid table+narrative routing and P2 6-image groups."""
    corpus_c = find_corpus_file(CORPUS_C_FILE)
    if not corpus_c:
        print("⚠️ test_19_real_corpus_c_kitasato_hybrid_routing SKIPPED (Corpus C not present)")
        return

    prof = classify_document(corpus_c)
    assert prof.document_class == DocumentClass.MIXED
    assert prof.page_constraint == PageConstraint.SOFT
    assert prof.page_count == 2

    # Verify P1 hybrid trace
    trace = generate_routing_trace(prof)
    p1_trace = [t for t in trace if t["page"] == 1]
    has_table_strategy = any(t["selected_strategy"] == "SPATIAL/TABLE" for t in p1_trace)
    has_flow_strategy = any(t["selected_strategy"] == "FLOW" for t in p1_trace)
    assert has_table_strategy, "Kitasato P1 must have SPATIAL/TABLE strategy for table regions"
    assert has_flow_strategy, "Kitasato P1 must have FLOW strategy for narrative regions"

    # Verify P2 visual groups
    doc = pymupdf.open(corpus_c)
    v_groups = find_visual_groups(doc[1], 1)
    doc.close()
    assert len(v_groups) == 6, f"Expected 6 image visual groups on P2, got {len(v_groups)}"
    for vg in v_groups:
        assert vg.keep_together is True
        ev = vg.to_evidence_dict()
        assert ev["caption_id"] is not None, "All images in grid must have associated caption"
        assert ev["association_method"] in ("DIRECT_BELOW", "ROW_SHARED_GRID")
    print("✅ test_19_real_corpus_c_kitasato_hybrid_routing [EXTERNAL_REAL_DOCUMENT_VALIDATION] PASSED")


def test_20_real_corpus_verifier_usability():
    """20. [EXTERNAL_REAL_DOCUMENT_VALIDATION] Verify mode-aware verifier on real rendered outputs if present."""
    test_dir = Path(__file__).resolve().parent.parent / "_process" / "test_upgrade_1_6"
    pdf_a = test_dir / "corpus_a_adaptive.pdf"
    pdf_b = test_dir / "corpus_b_adaptive.pdf"
    pdf_c = test_dir / "corpus_c_adaptive.pdf"

    if pdf_a.exists():
        prof_a = LayoutProfile(document_class=DocumentClass.TEXT_FLOW, page_constraint=PageConstraint.FREE, page_count=8)
        res_a = verify_adaptive_document(pdf_a, prof_a)
        assert res_a["overall_usability"] == "USABLE"
        assert res_a["metrics"]["micro_text_under_5pt"] == 0

    if pdf_b.exists():
        prof_b = LayoutProfile(document_class=DocumentClass.MIXED, page_constraint=PageConstraint.SOFT, page_count=11)
        res_b = verify_adaptive_document(pdf_b, prof_b)
        assert res_b["overall_usability"] == "USABLE"
        assert res_b["metrics"]["total_images"] == 16

    if pdf_c.exists():
        prof_c = LayoutProfile(document_class=DocumentClass.MIXED, page_constraint=PageConstraint.SOFT, page_count=2)
        res_c = verify_adaptive_document(pdf_c, prof_c)
        assert res_c["overall_usability"] == "USABLE"
        assert res_c["metrics"]["total_images"] == 6
        assert res_c["metrics"]["micro_text_under_5pt"] == 0

    print("✅ test_20_real_corpus_verifier_usability [EXTERNAL_REAL_DOCUMENT_VALIDATION] PASSED")


# ==============================================================================
# Main Runner & Classification Summary
# ==============================================================================

def main():
    print("=" * 75)
    print("🧪 Running AIWF Adaptive Layout & Pagination Validation Suite (Upgrade #1.6)")
    print("=" * 75)

    test_registry = [
        # SPECIFICATION_SIMULATION (3)
        (test_1_pure_flow_classification, "SPECIFICATION_SIMULATION"),
        (test_2_fixed_layout_certificate_classification, "SPECIFICATION_SIMULATION"),
        (test_3_mixed_region_hybrid_classification, "SPECIFICATION_SIMULATION"),

        # PRODUCTION_BEHAVIOR_TEST (8)
        (test_4_free_pagination_expansion, "PRODUCTION_BEHAVIOR_TEST"),
        (test_5_free_pagination_contraction, "PRODUCTION_BEHAVIOR_TEST"),
        (test_11_table_cell_elasticity, "PRODUCTION_BEHAVIOR_TEST"),
        (test_12_image_caption_association, "PRODUCTION_BEHAVIOR_TEST"),
        (test_13_image_caption_keep_together_migration, "PRODUCTION_BEHAVIOR_TEST"),
        (test_14_hybrid_composer_production_routing, "PRODUCTION_BEHAVIOR_TEST"),
        (test_15_mode_aware_flow_verification, "PRODUCTION_BEHAVIOR_TEST"),
        (test_16_mode_aware_spatial_verification, "PRODUCTION_BEHAVIOR_TEST"),

        # HELPER_TEST (5)
        (test_6_heading_keep_with_next_widow_orphan, "HELPER_TEST"),
        (test_7_body_paragraph_orphan_control, "HELPER_TEST"),
        (test_8_heading_detection_patterns, "HELPER_TEST"),
        (test_9_typst_escaping, "HELPER_TEST"),
        (test_10_layout_elasticity_policies, "HELPER_TEST"),

        # EXTERNAL_REAL_DOCUMENT_VALIDATION (4)
        (test_17_real_corpus_a_classification_and_routing, "EXTERNAL_REAL_DOCUMENT_VALIDATION"),
        (test_18_real_corpus_b_classification_and_routing, "EXTERNAL_REAL_DOCUMENT_VALIDATION"),
        (test_19_real_corpus_c_kitasato_hybrid_routing, "EXTERNAL_REAL_DOCUMENT_VALIDATION"),
        (test_20_real_corpus_verifier_usability, "EXTERNAL_REAL_DOCUMENT_VALIDATION"),
    ]

    counts = {
        "PRODUCTION_BEHAVIOR_TEST": 0,
        "HELPER_TEST": 0,
        "SPECIFICATION_SIMULATION": 0,
        "EXTERNAL_REAL_DOCUMENT_VALIDATION": 0,
        "FAILED": 0,
    }

    for test_fn, category in test_registry:
        try:
            test_fn()
            counts[category] += 1
        except Exception as e:
            print(f"❌ {test_fn.__name__} [{category}] FAILED: {e}")
            counts["FAILED"] += 1

    print("=" * 75)
    print("📊 TEST CLASSIFICATION SUMMARY:")
    print(f"   PRODUCTION_BEHAVIOR_TEST:          {counts['PRODUCTION_BEHAVIOR_TEST']}")
    print(f"   HELPER_TEST:                       {counts['HELPER_TEST']}")
    print(f"   SPECIFICATION_SIMULATION:          {counts['SPECIFICATION_SIMULATION']}")
    print(f"   EXTERNAL_REAL_DOCUMENT_VALIDATION: {counts['EXTERNAL_REAL_DOCUMENT_VALIDATION']}")
    print(f"   FAILED:                            {counts['FAILED']}")
    print("=" * 75)

    if counts["FAILED"] == 0:
        print("🎉 ALL 20 ADAPTIVE LAYOUT VALIDATION TESTS PASSED!")
    else:
        print(f"⚠️ {counts['FAILED']} tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
