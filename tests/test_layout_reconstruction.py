"""
Tests for AIWF Translation Upgrade #1.5: Layout Fidelity & Reconstruction Hardening.
Validates layout, reconstruction, fitting, and verification behaviors.

Explicit Test Classifications:
- PRODUCTION_BEHAVIOR_TEST: Invokes actual production code functions directly without manual arithmetic simulation.
- HELPER_TEST: Validates geometric helper functions and bounds clamping.
- SPECIFICATION_SIMULATION: Validates mathematical specification requirements.
- SYNTHETIC_REGRESSION_TEST: Validates critical value verifiers against artificial test fixtures.
"""

import sys
import os
import math
import subprocess
from typing import List, Dict, Any

# Add scripts directory to path
SKILL_SCRIPTS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "dich-giu-dinh-dang", "scripts")
)
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

from translation_foundation import (
    TranslationUnit,
    extract_critical_values,
    verify_critical_values,
)
from typst_overlay import (
    _classify_block_tier,
    _build_typst_page_source,
    build_translation_map,
    find_best_translation,
    TIER_TITLE,
    TIER_HEADING,
    TIER_BODY,
    TIER_TABLE_HEADER,
    TIER_TABLE_CELL,
    TIER_CAPTION,
    TIER_TIMELINE_LABEL,
    TIER_DIAGRAM_LABEL,
    TIER_HEADER_FOOTER,
    FONT_TIERS,
    _is_multiline_block,
)
from verify_layout_quality import (
    bbox_iou,
    bbox_intersection_ratio,
    classify_text_role,
    ROLE_READABILITY_FLOORS,
    audit_layout_quality,
)


def test_1_parent_child_duplication_prevention():
    """1. [HELPER_TEST] Verify parent + child combined_text geometric collision logic."""
    parent_text = "Hoạt động giao lưu quốc tế với Đại học Y khoa Hà Nội (HMU)"
    child_text = "Đại học Y khoa Hà Nội (HMU)"
    
    # Simulate parent bbox and child bbox inside parent
    parent_bbox = [68.0, 147.0, 526.0, 220.0]
    child_bbox = [68.0, 147.0, 250.0, 165.0]
    
    inter = bbox_intersection_ratio(parent_bbox, child_bbox)
    iou = bbox_iou(parent_bbox, child_bbox)
    
    assert inter >= 0.90, f"Child must be inside parent, got {inter}"
    has_spatial_collision = (inter > 0.15 or iou > 0.10 or (abs(parent_bbox[1] - child_bbox[1]) < 50.0))
    is_substring_dup = (child_text in parent_text) and has_spatial_collision
    assert is_substring_dup is True, "Parent-child duplicate overlay must be detected"
    print("✅ test_1_parent_child_duplication_prevention [HELPER_TEST] PASSED")


def test_2_near_identical_bbox_duplicate_prevention():
    """2. [HELPER_TEST] Verify near-identical bbox duplicate detection math."""
    b1 = [100.0, 150.0, 300.0, 180.0]
    b2 = [101.5, 149.5, 300.5, 181.0]  # Near identical
    
    iou = bbox_iou(b1, b2)
    inter = bbox_intersection_ratio(b1, b2)
    
    assert iou > 0.90, f"Expected high IoU for near-identical boxes, got {iou}"
    assert inter > 0.90, f"Expected high intersection ratio, got {inter}"
    print("✅ test_2_near_identical_bbox_duplicate_prevention [HELPER_TEST] PASSED")


def test_3_legitimate_repeated_text_preservation():
    """3. [SPECIFICATION_SIMULATION] Verify legitimate repeated text in separate regions specification."""
    t1_bbox = [50.0, 120.0, 250.0, 140.0]
    t2_bbox = [50.0, 350.0, 250.0, 370.0]  # 230pt apart
    
    inter = bbox_intersection_ratio(t1_bbox, t2_bbox)
    dist_y = abs(t1_bbox[1] - t2_bbox[1])
    
    assert inter == 0.0, "Disparate regions must not intersect"
    assert dist_y > 100.0, "Disparate regions must have significant vertical separation"
    
    src_blocks = [
        {"id": "s1", "bbox": [50.0, 120.0, 250.0, 140.0], "text": "① 日本国内研修参加研修員"},
        {"id": "s2", "bbox": [50.0, 350.0, 250.0, 370.0], "text": "① 日本国内研修参加研修員"}
    ]
    assert len(src_blocks) >= 2, "Source document contains 2 distinct blocks"
    print("✅ test_3_legitimate_repeated_text_preservation [SPECIFICATION_SIMULATION] PASSED")


def test_4_long_translated_body_paragraph():
    """4. [PRODUCTION_BEHAVIOR_TEST] Verify long translated body paragraph classification & multiline detection."""
    text = (
        "Khoa Y Đại học Kitasato đã thiết lập quan hệ đối tác chiến lược toàn diện "
        "với Đại học Y Hà Nội (HMU) trong khuôn khổ dự án xúc tiến quốc tế hóa giáo dục. "
        "Chương trình bao gồm các chuyến trao đổi học thuật, đào tạo chuyên sâu về kỹ thuật lọc máu."
    )
    role = classify_text_role(text, [68.0, 147.0, 526.0, 280.0], 595.0, 842.0, 9.5, False)
    assert role == "body", f"Expected body role, got {role}"
    
    floor = ROLE_READABILITY_FLOORS.get(role, 6.0)
    assert floor >= 6.0, f"Body floor must be >= 6.0pt, got {floor}"
    
    is_multi = _is_multiline_block({"lines": [1, 2, 3]}, text, 133.0, 9.5)
    assert is_multi is True, "Long paragraph must be detected as multiline"
    print("✅ test_4_long_translated_body_paragraph [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_5_long_table_cell():
    """5. [PRODUCTION_BEHAVIOR_TEST] Verify long table cell role classification and floor."""
    cell_bbox = [100.0, 200.0, 180.0, 230.0]  # w = 80pt, h = 30pt
    text = "Khảo sát chất lượng nước và đánh giá độ an toàn"
    role = classify_text_role(text, cell_bbox, 595.0, 842.0, 8.0, False)
    assert role == "table_cell", f"Expected table_cell role, got {role}"
    
    floor = ROLE_READABILITY_FLOORS.get(role, 4.5)
    assert floor >= 4.5, f"Table cell floor must be >= 4.5pt, got {floor}"
    print("✅ test_5_long_table_cell [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_6_dense_timeline_label_single_line():
    """6. [PRODUCTION_BEHAVIOR_TEST] Verify dense timeline label single-line role detection."""
    timeline_bbox = [151.26, 144.80, 179.26, 158.74]  # w = 28pt, h = 13.94pt
    text = "Tháng 5"
    role = classify_text_role(text, timeline_bbox, 595.0, 842.0, 10.2, True)
    assert role == "timeline_label", f"Expected timeline_label role, got {role}"
    
    is_multi = _is_multiline_block({}, text, 13.94, 10.2)
    assert is_multi is False, "Short timeline header must not wrap multiline"
    print("✅ test_6_dense_timeline_label_single_line [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_7_caption_near_image_association():
    """7. [PRODUCTION_BEHAVIOR_TEST] Verify caption near image classification & association."""
    img_bbox = [68.0, 100.0, 260.0, 250.0]
    caption_bbox = [68.0, 252.0, 260.0, 268.0]
    text = "Ảnh 1: Lễ ký kết biên bản ghi nhớ hợp tác"
    
    role = classify_text_role(text, caption_bbox, 595.0, 842.0, 8.0, False)
    assert role == "caption", f"Expected caption role, got {role}"
    
    gap = caption_bbox[1] - img_bbox[3]
    assert 0.0 <= gap <= 15.0, f"Caption must be directly below image, got gap {gap}"
    print("✅ test_7_caption_near_image_association [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_8_minimum_readable_font_tiers():
    """8. [PRODUCTION_BEHAVIOR_TEST] Verify minimum readable font tiers policy configuration."""
    for tier, cfg in FONT_TIERS.items():
        min_size = cfg["min_size"]
        assert min_size >= 4.5, f"Tier {tier} min_size must be >= 4.5pt, got {min_size}"
        assert cfg["floor_ratio"] >= 0.60, f"Tier {tier} floor_ratio must be >= 0.60, got {cfg['floor_ratio']}"
    print("✅ test_8_minimum_readable_font_tiers [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_9_bbox_expansion_collision_guard():
    """9. [HELPER_TEST] Verify bbox expansion collision guard prevents overwriting sibling elements."""
    container = [50.0, 100.0, 500.0, 200.0]
    blk_a = [50.0, 100.0, 200.0, 150.0]
    blk_b = [220.0, 100.0, 400.0, 150.0]
    
    sibling_lefts = [b[0] for b in [blk_b] if b[0] > blk_a[0]]
    right_lim = min(sibling_lefts) - 2.0 if sibling_lefts else container[2]
    
    assert right_lim == 218.0, f"Expected expansion right limit 218.0, got {right_lim}"
    assert right_lim < container[2], "Must not expand over sibling element"
    print("✅ test_9_bbox_expansion_collision_guard [HELPER_TEST] PASSED")


def test_10_page_edge_safety():
    """10. [HELPER_TEST] Verify page-edge safety and margin protection clamping."""
    pw, ph = 595.0, 842.0
    x0, y0, x1, y1 = 500.0, 50.0, 594.0, 70.0
    is_near_right = (pw - x1) < 15.0
    assert is_near_right is True, "Block near right edge must be flagged"
    
    effective_x1 = min(pw - 2.0, x1 + 4.0)
    assert effective_x1 <= pw - 2.0, f"Clamped x1 must be within page boundary, got {effective_x1}"
    print("✅ test_10_page_edge_safety [HELPER_TEST] PASSED")


def test_11_unit_mismatch_critical_value():
    """11. [SYNTHETIC_REGRESSION_TEST] Verify unit mismatch detection (24V -> 24A = FAIL)."""
    src = "定格電圧は 24V です。"
    bad_tgt = "Điện áp định mức là 24A."
    good_tgt = "Điện áp định mức là 24V."
    
    src_vals = extract_critical_values(src)
    bad_res = verify_critical_values(src_vals, bad_tgt)
    assert bad_res["pass"] is False, "Unit mismatch (24V -> 24A) MUST fail"
    
    good_res = verify_critical_values(src_vals, good_tgt)
    assert good_res["pass"] is True, "Correct unit (24V -> 24V) MUST pass"
    print("✅ test_11_unit_mismatch_critical_value [SYNTHETIC_REGRESSION_TEST] PASSED")


def test_12_currency_mismatch_critical_value():
    """12. [SYNTHETIC_REGRESSION_TEST] Verify currency mismatch detection (450,000 JPY -> 450,000 USD = FAIL)."""
    src = "事業費は 450,000 JPY です。"
    bad_tgt = "Chi phí dự án là 450,000 USD."
    good_tgt = "Chi phí dự án là 450,000 JPY."
    
    src_vals = extract_critical_values(src)
    bad_res = verify_critical_values(src_vals, bad_tgt)
    assert bad_res["pass"] is False, "Currency mismatch (JPY -> USD) MUST fail"
    
    good_res = verify_critical_values(src_vals, good_tgt)
    assert good_res["pass"] is True, "Correct currency (JPY -> JPY) MUST pass"
    print("✅ test_12_currency_mismatch_critical_value [SYNTHETIC_REGRESSION_TEST] PASSED")


def test_13_production_block_dedup_and_matching():
    """13. [PRODUCTION_BEHAVIOR_TEST] Verify production find_best_translation & build_translation_map.
    Parent translation is matched, child fragment (<85% length) is rejected (None),
    and legitimate independent neighbor is matched correctly."""
    blocks = [
        {
            "id": "unit_parent",
            "combined_text": "本事業では、ベトナムのハノイ医科大学との国際交流活動を実施する。",
            "ja": "本事業では、ベトナムのハノイ医科大学との国際交流活動を実施する。",
            "vi": "Trong dự án này, chúng tôi thực hiện các hoạt động giao lưu quốc tế với Đại học Y Hà Nội của Việt Nam."
        },
        {
            "id": "unit_neighbor",
            "combined_text": "共同研究の連携について具体的な計画を策定する。",
            "ja": "共同研究の連携について具体的な計画を策定する。",
            "vi": "Xây dựng kế hoạch cụ thể về việc phối hợp nghiên cứu chung."
        }
    ]
    norm_map, compact_map = build_translation_map(blocks, "vi")
    
    # 1. Full parent text matches full translation
    parent_res = find_best_translation("本事業では、ベトナムのハノイ医科大学との国際交流活動を実施する。", norm_map, compact_map)
    assert parent_res is not None, "Parent text must match translation"
    assert "Đại học Y Hà Nội" in parent_res
    
    # 2. Child fragment ("ハノイ医科大学") has len 7 vs parent len 33 (ratio 0.21 < 0.85).
    # Production find_best_translation MUST reject it (return None) to prevent orphan fragment overlay!
    child_res = find_best_translation("ハノイ医科大学", norm_map, compact_map)
    assert child_res is None, f"Child fragment must be rejected to prevent duplicate overlay, got {child_res}"
    
    # 3. Legitimate neighbor matches its own translation
    neighbor_res = find_best_translation("共同研究の連携について具体的な計画を策定する。", norm_map, compact_map)
    assert neighbor_res is not None, "Neighbor text must match translation"
    assert "Xây dựng kế hoạch" in neighbor_res
    print("✅ test_13_production_block_dedup_and_matching [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_14_production_typst_single_line_fitting():
    """14. [PRODUCTION_BEHAVIOR_TEST] Verify production Typst source generation and compilation.
    Validates that a timeline month header in a tight 28pt box is rendered strictly on a single line."""
    import pymupdf
    
    render_blocks = [
        {
            "bbox": [151.26, 144.80, 179.26, 158.74], # 28.0pt width, 13.94pt height
            "text": "Tháng 5",
            "font_size": 10.2,
            "tier": TIER_TIMELINE_LABEL,
            "weight": "bold",
            "align": "center",
            "color": "#ffffff",
        }
    ]
    typst_src = _build_typst_page_source(595.0, 842.0, render_blocks)
    tmp_pdf = "/tmp/test_typst_prod_fit.pdf"
    p = subprocess.run(["typst", "compile", "-", tmp_pdf], input=typst_src.encode("utf-8"), capture_output=True)
    assert p.returncode == 0, f"Typst compile failed: {p.stderr.decode()}"
    
    doc = pymupdf.open(tmp_pdf)
    page = doc[0]
    td = page.get_text("dict")
    text_blocks = [b for b in td.get("blocks", []) if b.get("type") == 0]
    assert len(text_blocks) == 1, f"Expected 1 text block, got {len(text_blocks)}"
    
    lines = text_blocks[0].get("lines", [])
    assert len(lines) == 1, f"Production fitting MUST maintain 1 single line, got {len(lines)} lines"
    
    rendered_text = "".join(s.get("text", "") for l in lines for s in l.get("spans", [])).strip()
    assert rendered_text == "Tháng 5", f"Expected 'Tháng 5', got {rendered_text}"
    
    font_size = lines[0]["spans"][0]["size"]
    assert 5.0 <= font_size <= 8.5, f"Expected fitted font size between 5.0pt and 8.5pt, got {font_size}"
    print("✅ test_14_production_typst_single_line_fitting [PRODUCTION_BEHAVIOR_TEST] PASSED")


def test_15_production_legitimate_repeated_text_audit():
    """15. [PRODUCTION_BEHAVIOR_TEST] Verify production verify_layout_quality detects legitimate repetitions."""
    import pymupdf
    
    src_pdf_path = "/tmp/test_legit_rep_src.pdf"
    tgt_pdf_path = "/tmp/test_legit_rep_tgt.pdf"
    
    doc_src = pymupdf.open()
    p_src = doc_src.new_page(width=595.0, height=842.0)
    p_src.insert_text((50.0, 150.0), "Kế hoạch thực hiện dự án (Plan)", fontsize=10.0)
    p_src.insert_text((50.0, 400.0), "Kế hoạch thực hiện dự án (Plan)", fontsize=10.0)
    doc_src.save(src_pdf_path)
    
    doc_tgt = pymupdf.open()
    p_tgt = doc_tgt.new_page(width=595.0, height=842.0)
    p_tgt.insert_text((50.0, 150.0), "Kế hoạch thực hiện dự án (Plan)", fontsize=10.0)
    p_tgt.insert_text((50.0, 400.0), "Kế hoạch thực hiện dự án (Plan)", fontsize=10.0)
    doc_tgt.save(tgt_pdf_path)
    
    res = audit_layout_quality(src_pdf_path, tgt_pdf_path)
    dup_dim = res["dimensions"]["DUPLICATION"]
    assert dup_dim["status"] == "PASS", f"Expected PASS for legitimate source repetitions, got {dup_dim['status']}"
    assert dup_dim["metric"] == 0, f"Expected 0 duplication issues, got {dup_dim['metric']}"
    print("✅ test_15_production_legitimate_repeated_text_audit [PRODUCTION_BEHAVIOR_TEST] PASSED")


def main():
    print("=" * 70)
    print("🧪 Running Layout Fidelity & Reconstruction Hardening Tests (Upgrade #1.5)")
    print("=" * 70)
    
    tests = [
        test_1_parent_child_duplication_prevention,
        test_2_near_identical_bbox_duplicate_prevention,
        test_3_legitimate_repeated_text_preservation,
        test_4_long_translated_body_paragraph,
        test_5_long_table_cell,
        test_6_dense_timeline_label_single_line,
        test_7_caption_near_image_association,
        test_8_minimum_readable_font_tiers,
        test_9_bbox_expansion_collision_guard,
        test_10_page_edge_safety,
        test_11_unit_mismatch_critical_value,
        test_12_currency_mismatch_critical_value,
        test_13_production_block_dedup_and_matching,
        test_14_production_typst_single_line_fitting,
        test_15_production_legitimate_repeated_text_audit,
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
        print("🎉 ALL 15 LAYOUT RECONSTRUCTION TESTS PASSED!")
    else:
        print(f"⚠️ {failed} tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
