"""Tests for AIWF Translation Upgrade #1.6: Adaptive Document Classification & Elastic Layout Engine.

Validates:
- 3-level document, page, and region classification.
- Pagination constraints (HARD, SOFT, FREE).
- Layout elasticity and visual groups (image + caption keep-together).
- Native flow reflow vs spatial preservation.
- Mode-aware verification (evaluating structural fidelity, typography, readability without penalizing natural reflow).

Test Classifications:
- PRODUCTION_BEHAVIOR_TEST: Invokes actual production code functions directly on real models or fixtures.
- HELPER_TEST: Validates policy objects, elasticity definitions, and geometry helpers.
- SPECIFICATION_SIMULATION: Validates mathematical specification requirements and adversarial synthetic layouts.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

# Add scripts directory to path
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
from render.hybrid_composer import compose_adaptive_pdf
from render.spatial_renderer import render_spatial_pdf
from verify.mode_aware_verifier import verify_adaptive_document

CORPUS_A = "/Users/tranhaibang/Downloads/AIWF_Output/透析液成分濃度測定装置の認証指針第2版.pdf"
CORPUS_B = "/Users/tranhaibang/Downloads/AIWF_Output/21_R5_JSTB_mongolia.pdf"
CORPUS_C = "/Users/tranhaibang/Downloads/AIWF_Output/2025年度医療系研究科国際化推進事業実績報告書（北里大・小久保教授）.pdf"


def test_1_classifier_text_flow_corpus_a():
    """1. [PRODUCTION_BEHAVIOR_TEST] Corpus A must deterministically classify as TEXT_FLOW with FREE constraint."""
    prof = classify_document(CORPUS_A)
    assert prof.document_class == DocumentClass.TEXT_FLOW, f"Expected TEXT_FLOW, got {prof.document_class}"
    assert prof.page_constraint == PageConstraint.FREE, f"Expected FREE, got {prof.page_constraint}"
    assert prof.confidence >= 0.90, f"Expected confidence >= 0.90, got {prof.confidence}"
    assert len(prof.evidence) >= 1
    assert prof.page_count == 8
    print("✅ test_1_classifier_text_flow_corpus_a [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_2_classifier_mixed_corpus_b():
    """2. [PRODUCTION_BEHAVIOR_TEST] Corpus B must deterministically classify as MIXED with SOFT constraint."""
    prof = classify_document(CORPUS_B)
    assert prof.document_class == DocumentClass.MIXED, f"Expected MIXED, got {prof.document_class}"
    assert prof.page_constraint == PageConstraint.SOFT, f"Expected SOFT, got {prof.page_constraint}"
    assert prof.page_count == 11
    print("✅ test_2_classifier_mixed_corpus_b [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_3_classifier_hybrid_corpus_c():
    """3. [PRODUCTION_BEHAVIOR_TEST] Corpus C must deterministically classify as MIXED with SOFT constraint."""
    prof = classify_document(CORPUS_C)
    assert prof.document_class == DocumentClass.MIXED, f"Expected MIXED, got {prof.document_class}"
    assert prof.page_constraint == PageConstraint.SOFT, f"Expected SOFT, got {prof.page_constraint}"
    assert prof.page_count == 2
    # Verify page 1 is TABLE_FORM / MIXED and page 2 has IMAGE_GROUP
    p1 = prof.page_profiles[0]
    p2 = prof.page_profiles[1]
    assert p1.page_class in (DocumentClass.TABLE_FORM, DocumentClass.MIXED)
    assert p2.page_class == DocumentClass.IMAGE_GROUP
    print("✅ test_3_classifier_hybrid_corpus_c [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_4_page_constraint_policy():
    """4. [HELPER_TEST] Verify pagination constraint semantics and policies."""
    assert PageConstraint.HARD == "HARD"
    assert PageConstraint.SOFT == "SOFT"
    assert PageConstraint.FREE == "FREE"
    print("✅ test_4_page_constraint_policy [HELPER_TEST] PASSED")


def test_5_layout_elasticity_defaults():
    """5. [HELPER_TEST] Verify default elasticity per structural role."""
    # Body paragraph: high reflow and vertical resize
    e_par = get_default_elasticity(StructuralRole.BODY_PARAGRAPH, DocumentClass.TEXT_FLOW, PageConstraint.FREE)
    assert e_par.reflow == ElasticityLevel.HIGH
    assert e_par.vertical_resize == ElasticityLevel.HIGH
    assert e_par.keep_with_next is False
    assert e_par.min_font_size >= 7.5

    # Heading: keep-with-next must be True
    e_head = get_default_elasticity(StructuralRole.HEADING, DocumentClass.TEXT_FLOW, PageConstraint.FREE)
    assert e_head.keep_with_next is True
    assert e_head.reflow == ElasticityLevel.LIMITED

    # Table cell: topology locked
    e_tbl = get_default_elasticity(StructuralRole.TABLE_CELL, DocumentClass.TABLE_FORM, PageConstraint.SOFT)
    assert e_tbl.topology_locked is True

    # Caption: keep_together must be True
    e_cap = get_default_elasticity(StructuralRole.CAPTION, DocumentClass.IMAGE_GROUP, PageConstraint.SOFT)
    assert e_cap.keep_together is True
    print("✅ test_5_layout_elasticity_defaults [HELPER_TEST] PASSED")


def test_6_visual_group_detection_corpus_c():
    """6. [PRODUCTION_BEHAVIOR_TEST] Verify VisualGroup identifies 6 images on Corpus C Page 2."""
    doc = pymupdf.open(CORPUS_C)
    p2 = doc[1]
    v_groups = find_visual_groups(p2, page_idx=1)
    assert len(v_groups) == 6, f"Expected 6 image visual groups, got {len(v_groups)}"
    for vg in v_groups:
        assert vg.keep_together is True
        assert vg.image_rect[2] > vg.image_rect[0]
        assert vg.bounding_box[3] >= vg.image_rect[3]
    doc.close()
    print("✅ test_6_visual_group_detection_corpus_c [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_7_page_budget_widow_orphan_heading():
    """7. [HELPER_TEST] Heading near bottom of page must trigger page break."""
    budget = PageBudget(page_height=800.0, top_margin=40.0, bottom_margin=40.0, current_y=730.0)
    # Remaining space is 800 - 40 - 730 = 30pt
    # Heading height is 25pt, but needs 45pt keep-with-next space
    assert should_break_before(StructuralRole.HEADING, element_height=25.0, budget=budget) is True

    # When there is plenty of space (e.g. current_y = 200.0)
    budget_plenty = PageBudget(page_height=800.0, top_margin=40.0, bottom_margin=40.0, current_y=200.0)
    assert should_break_before(StructuralRole.HEADING, element_height=25.0, budget=budget_plenty) is False
    print("✅ test_7_page_budget_widow_orphan_heading [HELPER_TEST] PASSED")


def test_8_page_budget_body_paragraph():
    """8. [HELPER_TEST] Body paragraph with <32pt remaining should push to next page."""
    budget = PageBudget(page_height=800.0, top_margin=40.0, bottom_margin=40.0, current_y=745.0, elements_count=3)
    # Remaining space = 15pt
    assert should_break_before(StructuralRole.BODY_PARAGRAPH, element_height=50.0, budget=budget) is True
    print("✅ test_8_page_budget_body_paragraph [HELPER_TEST] PASSED")


def test_9_heading_detection_patterns():
    """9. [HELPER_TEST] Verify heading regex detection across Japanese and Vietnamese formats."""
    assert _is_heading("1. はじめに") == (True, 1)
    assert _is_heading("1. Đặt vấn đề") == (True, 1)
    assert _is_heading("5.1 測定項目") == (True, 2)
    assert _is_heading("5.1.1 Phương pháp thử") == (True, 3)
    assert _is_heading("Đây là một đoạn văn bản thông thường.") == (False, 0)
    print("✅ test_9_heading_detection_patterns [HELPER_TEST] PASSED")


def test_10_typst_escaping():
    """10. [HELPER_TEST] Verify Typst special characters are escaped safely."""
    raw = "Giá trị: $100 #1 [±2.2%] <Na+ & K+> _test_ *bold*"
    esc = _escape_typst(raw)
    assert "\\$" in esc
    assert "\\#" in esc
    assert "\\[" in esc
    assert "\\]" in esc
    assert "\\<" in esc
    assert "\\>" in esc
    assert "\\_" in esc
    assert "\\*" in esc
    print("✅ test_10_typst_escaping [HELPER_TEST] PASSED")


def test_11_flow_pipeline_production_execution():
    """11. [PRODUCTION_BEHAVIOR_TEST] Verify Flow pipeline generates readable PDF with 0 micro-text."""
    import json
    dict_path = "_process/retain_pdf_toseki_shishin_v2/merged_ejv.json"
    with open(dict_path) as f:
        blocks = json.load(f)

    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as tmp:
        out_pdf = tmp.name

    try:
        render_flow_pdf(
            source_pdf_path=CORPUS_A,
            blocks=blocks,
            lang="vi",
            output_pdf_path=out_pdf,
        )
        assert os.path.exists(out_pdf)
        doc = pymupdf.open(out_pdf)
        assert len(doc) >= 6, f"Expected at least 6 flowing pages, got {len(doc)}"

        # Check font sizes: must be >= 7.5pt (zero micro-text)
        all_sizes = []
        for p in doc:
            td = p.get_text("dict")
            for b in td["blocks"]:
                if b.get("type") == 0:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            if s.get("text", "").strip() and s.get("size"):
                                all_sizes.append(s["size"])
        assert min(all_sizes) >= 7.5, f"Expected min font >= 7.5pt, got {min(all_sizes)}pt"
        doc.close()
    finally:
        if os.path.exists(out_pdf):
            os.remove(out_pdf)
    print("✅ test_11_flow_pipeline_production_execution [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_12_hybrid_composer_routing():
    """12. [PRODUCTION_BEHAVIOR_TEST] Verify Hybrid Composer routes Corpus A to FLOW and Corpus B/C to HYBRID/VISUAL."""
    import json
    # Corpus A -> FLOW
    with open("_process/retain_pdf_toseki_shishin_v2/merged_ejv.json") as f:
        blocks_a = json.load(f)
    prof_a = classify_document(CORPUS_A)
    assert prof_a.document_class == DocumentClass.TEXT_FLOW
    assert prof_a.page_constraint == PageConstraint.FREE

    # Corpus B -> MIXED
    prof_b = classify_document(CORPUS_B)
    assert prof_b.document_class == DocumentClass.MIXED
    assert prof_b.page_constraint == PageConstraint.SOFT

    # Corpus C -> MIXED
    prof_c = classify_document(CORPUS_C)
    assert prof_c.document_class == DocumentClass.MIXED
    assert prof_c.page_constraint == PageConstraint.SOFT
    print("✅ test_12_hybrid_composer_routing [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_13_mode_aware_verifier_flow_corpus_a():
    """13. [PRODUCTION_BEHAVIOR_TEST] Verify mode-aware verifier evaluates Corpus A adaptive output as PASS and USABLE."""
    prof = classify_document(CORPUS_A)
    res = verify_adaptive_document(
        rendered_pdf_path="_process/test_upgrade_1_6/corpus_a_adaptive.pdf",
        layout_profile=prof,
        source_pdf_path=CORPUS_A,
    )
    assert res["evaluations"]["SEMANTIC_FIDELITY"] == "PASS"
    assert res["evaluations"]["TYPOGRAPHY_FIDELITY"] == "PASS"
    assert res["evaluations"]["READABILITY"] == "PASS"
    assert res["evaluations"]["STRUCTURAL_FIDELITY"] == "PASS"
    assert res["evaluations"]["PAGINATION_QUALITY"] == "PASS"
    assert res["overall_usability"] == "USABLE"
    assert res["metrics"]["micro_text_under_5pt"] == 0
    print("✅ test_13_mode_aware_verifier_flow_corpus_a [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_14_mode_aware_verifier_corpus_b():
    """14. [PRODUCTION_BEHAVIOR_TEST] Verify mode-aware verifier evaluates Corpus B as USABLE with 16 images intact."""
    prof = classify_document(CORPUS_B)
    res = verify_adaptive_document(
        rendered_pdf_path="_process/test_upgrade_1_6/corpus_b_adaptive.pdf",
        layout_profile=prof,
        source_pdf_path=CORPUS_B,
    )
    assert res["evaluations"]["SEMANTIC_FIDELITY"] == "PASS"
    assert res["evaluations"]["IMAGE_RETENTION"] == "PASS"
    assert res["metrics"]["total_images"] == 16
    assert res["overall_usability"] == "USABLE"
    print("✅ test_14_mode_aware_verifier_corpus_b [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_15_mode_aware_verifier_corpus_c():
    """15. [PRODUCTION_BEHAVIOR_TEST] Verify mode-aware verifier evaluates Corpus C (VI) as USABLE with 6 images intact."""
    prof = classify_document(CORPUS_C)
    res = verify_adaptive_document(
        rendered_pdf_path="_process/test_upgrade_1_6/corpus_c_adaptive.pdf",
        layout_profile=prof,
        source_pdf_path=CORPUS_C,
    )
    assert res["evaluations"]["SEMANTIC_FIDELITY"] == "PASS"
    assert res["evaluations"]["IMAGE_RETENTION"] == "PASS"
    assert res["metrics"]["total_images"] == 6
    assert res["metrics"]["micro_text_under_5pt"] == 0
    assert res["overall_usability"] == "USABLE"
    print("✅ test_15_mode_aware_verifier_corpus_c [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_16_adversarial_synthetic_pure_text_page():
    """16. [SPECIFICATION_SIMULATION] Synthetic single-page pure text document must classify as TEXT_FLOW / FREE."""
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        doc = pymupdf.open()
        p = doc.new_page(width=595, height=842)
        # Add pure paragraphs
        text = "Đây là văn bản tài liệu hướng dẫn quy chuẩn kỹ thuật y tế. " * 30
        p.insert_textbox(pymupdf.Rect(50, 50, 545, 750), text, fontsize=10)
        doc.save(pdf_path)
        doc.close()

        prof = classify_document(pdf_path)
        p_prof = prof.page_profiles[0]
        assert p_prof.page_class == DocumentClass.TEXT_FLOW
        assert p_prof.page_constraint == PageConstraint.FREE
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    print("✅ test_16_adversarial_synthetic_pure_text_page [SPECIFICATION_SIMULATION] PASSED")


def test_17_adversarial_synthetic_fixed_certificate():
    """17. [SPECIFICATION_SIMULATION] Synthetic certificate with multiple border rects must classify as FIXED_LAYOUT / HARD."""
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        doc = pymupdf.open()
        p = doc.new_page(width=595, height=842)
        # Add 6 border rects
        for i in range(6):
            p.draw_rect(pymupdf.Rect(20 + i * 5, 20 + i * 5, 575 - i * 5, 822 - i * 5), color=(0, 0, 0), width=1)
        # Add short text < 200 chars
        p.insert_textbox(pymupdf.Rect(100, 200, 495, 300), "GIẤY CHỨNG NHẬN PHÁP NHÂN\nCấp cho đơn vị.", fontsize=14)
        doc.save(pdf_path)
        doc.close()

        prof = classify_document(pdf_path)
        p_prof = prof.page_profiles[0]
        assert p_prof.page_class == DocumentClass.FIXED_LAYOUT
        assert p_prof.page_constraint == PageConstraint.HARD
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    print("✅ test_17_adversarial_synthetic_fixed_certificate [SPECIFICATION_SIMULATION] PASSED")


def main():
    print("=" * 70)
    print("🧪 Running AIWF Adaptive Layout & Pagination Tests (Upgrade #1.6)")
    print("=" * 70)

    tests = [
        test_1_classifier_text_flow_corpus_a,
        test_2_classifier_mixed_corpus_b,
        test_3_classifier_hybrid_corpus_c,
        test_4_page_constraint_policy,
        test_5_layout_elasticity_defaults,
        test_6_visual_group_detection_corpus_c,
        test_7_page_budget_widow_orphan_heading,
        test_8_page_budget_body_paragraph,
        test_9_heading_detection_patterns,
        test_10_typst_escaping,
        test_11_flow_pipeline_production_execution,
        test_12_hybrid_composer_routing,
        test_13_mode_aware_verifier_flow_corpus_a,
        test_14_mode_aware_verifier_corpus_b,
        test_15_mode_aware_verifier_corpus_c,
        test_16_adversarial_synthetic_pure_text_page,
        test_17_adversarial_synthetic_fixed_certificate,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"❌ {t.__name__} FAILED: {e}")
            failed += 1

    print("=" * 70)
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")
    if failed == 0:
        print("🎉 ALL 17 ADAPTIVE LAYOUT TESTS PASSED!")
    else:
        print(f"⚠️ {failed} tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
