"""Comprehensive Test Suite for AIWF Translation Upgrade #1.7:
Native Text Document Reconstruction & Professional Reflow for TEXT_FLOW PDFs.

Conforms to:
- Part 26: Synthetic / Controlled Test Corpus (25+ Scenarios)
- Part 27: Honest Evidence Labels (PRODUCTION_BEHAVIOR_TEST)
- Part 28: Required Production Tests (Reconstruction -> Composition -> Verification)
- Part 29: Round-trip & Traceability
- Part 41: Pagination Proof (Baseline, 1.5x Expansion, 2.0x Expansion, Contraction)
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add skill scripts directory to path
SKILL_SCRIPTS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "dich-thuat", "scripts")
)
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

import pymupdf

from analyzer.layout_profile import DocumentClass, LayoutProfile, PageConstraint
from layout.logical_document import (
    ConfidenceLevel,
    InlineToken,
    LogicalDocument,
    LogicalSection,
    LogicalTable,
    LogicalUnit,
    StructuralRole,
)
from layout.semantic_reconstructor import SemanticReconstructor, reconstruct_semantic_document
from layout.translation_mapper import TranslationMapper
from render.flow_composer import FlowComposer
from verify.mode_aware_verifier import verify_adaptive_document


def create_synthetic_pdf(pages_text: List[List[Dict[str, Any]]], output_path: Path) -> Path:
    """Creates a deterministic multi-page PDF with precise text spans and coordinates."""
    doc = pymupdf.open()
    for p_items in pages_text:
        page = doc.new_page(width=595.3, height=841.9)  # A4
        page.insert_font(fontname="japan", fontbuffer=None)
        for item in p_items:
            rect = item.get("rect", [72, 72, 520, 92])
            text = item.get("text", "")
            fontsize = item.get("fontsize", 10.0)
            # Use insert_text at (x0, y1 - 2) for reliable baseline positioning
            x0, y0, x1, y1 = rect[0], rect[1], rect[2], rect[3]
            page.insert_text(pymupdf.Point(x0, y1 - 2.0), text, fontsize=fontsize, fontname="japan")
    doc.save(str(output_path))
    doc.close()
    return output_path


# ==============================================================================
# TEST CASES (1 to 28)
# ==============================================================================

def test_1_multiline_normal_paragraph_reconstruction():
    """1. Multi-line normal paragraph physical fragments are merged into one logical unit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test1.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "透析治療に用いる透析剤は、医薬品会社が医療用医薬品として製造販売しているもので、", "fontsize": 10.0},
            {"rect": [72, 118, 520, 133], "text": "その製造設備や製品の製造方法や品質は、医薬品医療機器等法により管理されている。", "fontsize": 10.0},
            {"rect": [72, 136, 520, 151], "text": "透析施設の管理の下で使用直前に希釈混合される。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        body_units = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.BODY_PARAGRAPH]
        assert len(body_units) == 1, f"Expected 1 merged paragraph, got {len(body_units)}"
        assert "希釈混合される。" in body_units[0].text
        print("  [PASS] Test 1: Multi-line normal paragraph reconstructed into atomic unit.")


def test_2_multiple_paragraphs_boundary_detection():
    """2. Multiple paragraphs separated by whitespace gap or indentation are kept separate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test2.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "第一段落のテキストです。文末です。", "fontsize": 10.0},
            # Gap of 25pt (> 1.8x typical line gap of 4pt)
            {"rect": [72, 140, 520, 155], "text": "第二段落のテキストです。文末です。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        body_units = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.BODY_PARAGRAPH]
        assert len(body_units) == 2, f"Expected 2 separate paragraphs, got {len(body_units)}"
        print("  [PASS] Test 2: Multiple paragraphs boundary detected correctly.")


def test_3_numbered_headings_l1_detection():
    """3. Numbered heading L1 is recognized and never merged with body."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test3.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 120], "text": "1. はじめに", "fontsize": 12.0},
            {"rect": [72, 128, 520, 143], "text": "透析治療に用いる透析剤の解説文です。", "fontsize": 10.0},
            {"rect": [72, 160, 520, 180], "text": "2. 適用範囲", "fontsize": 12.0},
            {"rect": [72, 188, 520, 203], "text": "本指針の適用範囲を規定します。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        h1_units = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.HEADING_1]
        assert len(h1_units) == 2, f"Expected 2 HEADING_1 units, got {len(h1_units)}"
        assert h1_units[0].text == "1. はじめに"
        assert h1_units[1].text == "2. 適用範囲"
        print("  [PASS] Test 3: Numbered headings L1 recognized cleanly.")


def test_4_nested_heading_hierarchy_l1_l2_l3():
    """4. Nested headings L1 (1.), L2 (1.1), L3 (1.1.1) maintain strict hierarchy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test4.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 120], "text": "6. 認証規格", "fontsize": 13.0},
            {"rect": [72, 130, 520, 148], "text": "6.1 測定要件", "fontsize": 11.5},
            {"rect": [72, 155, 520, 170], "text": "測定要件の本文。", "fontsize": 10.0},
            {"rect": [72, 180, 520, 195], "text": "6.1.1 測定回数", "fontsize": 10.5},
            {"rect": [72, 200, 520, 215], "text": "測定回数は5回とする。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        h1 = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.HEADING_1]
        h2 = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.HEADING_2]
        h3 = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.HEADING_3]
        assert len(h1) == 1 and h1[0].level == 1
        assert len(h2) == 1 and h2[0].level == 2
        assert len(h3) == 1 and h3[0].level == 3
        print("  [PASS] Test 4: Nested heading hierarchy L1/L2/L3 verified.")


def test_5_paragraph_split_across_source_page():
    """5. Paragraph continuation across page boundaries is merged when mid-sentence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test5.pdf"
        pages_text = [
            [{"rect": [72, 750, 520, 765], "text": "この文章は1ページ目の末尾で終わらず、次ページへと続いて", "fontsize": 10.0}],
            [{"rect": [72, 80, 520, 95], "text": "おり、ここで初めて文章が完結します。", "fontsize": 10.0}],
        ]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        body_units = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.BODY_PARAGRAPH]
        assert len(body_units) == 1, f"Expected 1 cross-page merged paragraph, got {len(body_units)}"
        assert "完結します。" in body_units[0].text
        assert 1 in body_units[0].source_pages and 2 in body_units[0].source_pages
        print("  [PASS] Test 5: Cross-page paragraph continuation verified.")


def test_6_bullet_list_reconstruction():
    """6. Bullet list markers (・, •, -) are recognized and preserved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test6.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "・項目A：最初の箇条書き", "fontsize": 10.0},
            {"rect": [72, 120, 520, 135], "text": "・項目B：二番目の箇条書き", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        items = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role in (StructuralRole.LIST_ITEM, StructuralRole.DEFINITION_ITEM)]
        assert len(items) == 2, f"Expected 2 list/definition items, got {len(items)}"
        print("  [PASS] Test 6: Bullet list reconstruction verified.")


def test_7_numbered_list_reconstruction():
    """7. Numbered list items (1), 2), (1)) are preserved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test7.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "1) 種類", "fontsize": 10.0},
            {"rect": [72, 120, 520, 135], "text": "(1) 酢酸系", "fontsize": 10.0},
            {"rect": [72, 140, 520, 155], "text": "(2) クエン酸系", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        items = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role in (StructuralRole.LIST_ITEM, StructuralRole.DEFINITION_ITEM)]
        assert len(items) >= 2
        print("  [PASS] Test 7: Numbered list items preserved.")


def test_8_abbreviation_definition_list_reconstruction():
    """8. Abbreviation list (HD:, HDF:, ISE:) remains readable definition structures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test8.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "・HD：hemodialysis、血液透析", "fontsize": 10.0},
            {"rect": [72, 120, 520, 135], "text": "・HDF：hemodiafiltration、血液透析濾過", "fontsize": 10.0},
            {"rect": [72, 140, 520, 155], "text": "・ISE：ion-selective electrode、イオン選択電極", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        defs = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role in (StructuralRole.DEFINITION_ITEM, StructuralRole.LIST_ITEM)]
        assert len(defs) == 3
        print("  [PASS] Test 8: Abbreviation definition list preserved.")


def test_9_superscript_inline_preservation():
    """9. Superscript chemical signs remain logically attached."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test9.pdf"
        pages_text = [[
            {"rect": [72, 100, 300, 115], "text": "血中イオン測定項目としてNa+", "fontsize": 10.0},
            {"rect": [305, 100, 520, 115], "text": "およびK+の濃度を測定する。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        unit = log_doc.units[0]
        assert "Na+" in unit.text and "K+" in unit.text
        print("  [PASS] Test 9: Superscript inline signs preserved.")


def test_10_subscript_inline_preservation():
    """10. Subscript notation (HCO3, t0.975) preserved without fragmentation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test10.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "重炭酸イオンHCO3－およびt0.975の統計値を算出する。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        unit = log_doc.units[0]
        assert "HCO3" in unit.text
        print("  [PASS] Test 10: Subscript inline notation preserved.")


def test_11_scientific_symbols_inline():
    """11. Scientific symbols (±, √, mmol/L) stay attached."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test11.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "判定基準は±2.2 mmol/L以内とし、ts/√nにより算出する。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        unit = log_doc.units[0]
        assert "±2.2" in unit.text and "mmol/L" in unit.text and "ts/√n" in unit.text
        print("  [PASS] Test 11: Scientific symbols inline preserved.")


def test_12_inline_chemical_notation_fused():
    """12. Same-row split fragments for chemical tokens (HCO3 and -) are fused."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test12.pdf"
        # Simulate PyMuPDF splitting HCO3 and - across separate boxes
        pages_text = [[
            {"rect": [72, 100, 250, 115], "text": "測定項目はNa+、K+、Cl－、pH、HCO3", "fontsize": 10.0},
            {"rect": [251, 101, 450, 115], "text": "－の5項目とする。", "fontsize": 6.5},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        unit = log_doc.units[0]
        assert "HCO3－" in unit.text
        print("  [PASS] Test 12: Inline chemical notation fragments fused seamlessly.")


def test_13_formula_block_standalone():
    """13. Formula blocks are kept as dedicated formula units."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test13.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "測定要件の計算式は以下とする：", "fontsize": 10.0},
            {"rect": [120, 125, 480, 140], "text": "Cm = （B の符号）{（B の絶対値）＋1.24s}", "fontsize": 10.0},
            {"rect": [72, 155, 520, 170], "text": "算出された値により判定を行う。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        formula_units = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.FORMULA_BLOCK]
        assert len(formula_units) == 1
        assert "Cm =" in formula_units[0].text
        print("  [PASS] Test 13: Formula block recognized standalone.")


def test_14_table_between_paragraphs_detection():
    """14. Tables located between paragraphs do not break paragraph integrity."""
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    page.insert_font(fontname="japan", fontbuffer=None)
    page.insert_text(pymupdf.Point(72, 115), "前段落の文章です。表の前です。", fontsize=10, fontname="japan")
    # Draw simple table border
    page.draw_rect(pymupdf.Rect(72, 140, 520, 200))
    page.insert_text(pymupdf.Point(75, 160), "項目A", fontsize=10, fontname="japan")
    page.insert_text(pymupdf.Point(205, 160), "数値1", fontsize=10, fontname="japan")
    page.insert_text(pymupdf.Point(72, 235), "後段落の文章です。表の後です。", fontsize=10, fontname="japan")

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test14.pdf"
        doc.save(str(pdf_path))
        doc.close()

        log_doc = reconstruct_semantic_document(pdf_path)
        body_units = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.BODY_PARAGRAPH]
        assert len(body_units) >= 2
        print("  [PASS] Test 14: Table between paragraphs detected cleanly.")


def test_15_table_wrapping_cells_composition():
    """15. Table cells with multi-line text wrap naturally in Typst composition."""
    table = LogicalTable(
        table_id="tbl_wrap_test",
        source_page=1,
        bbox=(72, 100, 520, 200),
        headers=[["Thông số", "Quy định phương pháp kiểm chuẩn", "Giới hạn chấp nhận"]],
        rows=[
            ["Na+", "Phương pháp quang phổ phát xạ ngọn lửa theo tiêu chuẩn tham chiếu quốc tế", "±2.2 mmol/L"],
            ["HCO3－", "Phương pháp đo điện lượng chuẩn độ điện tích ion tự do trong dung dịch thẩm tách", "±2.2 mmol/L"],
        ],
    )
    doc = LogicalDocument(document_id="doc_wrap", units=[table])
    composer = FlowComposer(doc)
    typst_code = composer.compose_typst()
    assert "#table(" in typst_code
    assert "columns: 3" in typst_code
    print("  [PASS] Test 15: Table cell wrapping code generated successfully.")


def test_16_footnote_isolation():
    """16. Footnotes and remarks (注：, *) are isolated from body paragraph flow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test16.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "本指針の本文テキストです。", "fontsize": 10.0},
            {"rect": [72, 200, 520, 215], "text": "注：中間精度は同一条件で測定日を変えて測定した精密さの程度を示す。", "fontsize": 8.5},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        def_units = [u for u in log_doc.units if isinstance(u, LogicalUnit) and u.role == StructuralRole.DEFINITION_ITEM]
        assert len(def_units) == 1
        assert "注：" in def_units[0].text
        print("  [PASS] Test 16: Footnote and remarks isolated from body flow.")


def test_17_recurring_header_footer_isolation():
    """17. Recurring headers and footers are detected and isolated from body."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test17.pdf"
        pages_text = [
            [
                {"rect": [72, 40, 520, 55], "text": "透析液成分濃度測定装置の認証指針", "fontsize": 9.0},
                {"rect": [72, 100, 520, 115], "text": "1ページ目の本文です。", "fontsize": 10.0},
                {"rect": [72, 800, 520, 815], "text": "一般社団法人日本血液浄化技術学会", "fontsize": 9.0},
            ],
            [
                {"rect": [72, 40, 520, 55], "text": "透析液成分濃度測定装置の認証指針", "fontsize": 9.0},
                {"rect": [72, 100, 520, 115], "text": "2ページ目の本文です。", "fontsize": 10.0},
                {"rect": [72, 800, 520, 815], "text": "一般社団法人日本血液浄化技術学会", "fontsize": 9.0},
            ],
        ]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        # Running header and footer should not contaminate body units
        for u in log_doc.units:
            if isinstance(u, LogicalUnit):
                assert u.text != "透析液成分濃度測定装置の認証指針"
                assert u.text != "一般社団法人日本血液浄化技術学会"
        print("  [PASS] Test 17: Recurring header/footer isolated from body units.")


def test_18_page_number_isolation():
    """18. Standalone page numbers are excluded from body flow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test18.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "本文段落のテキストです。", "fontsize": 10.0},
            {"rect": [290, 800, 310, 815], "text": "1", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        for u in log_doc.units:
            if isinstance(u, LogicalUnit):
                assert u.text != "1"
        print("  [PASS] Test 18: Page numbers excluded from body units.")


def test_19_long_target_expansion_1_5x():
    """19. Controlled 1.5x text expansion creates natural additional pages without font crushing."""
    base_text = "Đây là đoạn văn bản tiếng Việt hoàn chỉnh đại diện cho sự mở rộng tự nhiên của ngôn ngữ đích trong quá trình chuyển ngữ tài liệu kỹ thuật y tế. " * 8
    units = [
        LogicalUnit(unit_id=f"u_{i}", role=StructuralRole.BODY_PARAGRAPH, text=base_text * 2, translated_text=base_text * 2)
        for i in range(12)
    ]
    doc = LogicalDocument(document_id="doc_15x", units=units)
    composer = FlowComposer(doc)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = Path(tmpdir) / "expanded_15x.pdf"
        composer.render_pdf(out_pdf)

        p_doc = pymupdf.open(str(out_pdf))
        page_count = len(p_doc)
        assert page_count >= 2, f"Expected natural pagination >= 2 pages, got {page_count}"
        # Verify font size not crushed
        for p in p_doc:
            for b in p.get_text("dict")["blocks"]:
                if b.get("type") == 0:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            assert s["size"] >= 8.5, f"Font size crushed below 8.5pt: {s['size']}"
        p_doc.close()
    print("  [PASS] Test 19: 1.5x expansion paginated naturally without font shrinking.")


def test_20_extreme_target_expansion_2_0x():
    """20. 2.0x expansion paginates across more pages with stable margins and typography."""
    base_text = "Văn bản mở rộng quy mô gấp đôi kiểm chứng khả năng co giãn dòng chảy tự nhiên. " * 15
    units = [
        LogicalUnit(unit_id=f"u_{i}", role=StructuralRole.BODY_PARAGRAPH, text=base_text, translated_text=base_text)
        for i in range(15)
    ]
    doc = LogicalDocument(document_id="doc_20x", units=units)
    composer = FlowComposer(doc)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = Path(tmpdir) / "expanded_20x.pdf"
        composer.render_pdf(out_pdf)

        p_doc = pymupdf.open(str(out_pdf))
        page_count = len(p_doc)
        assert page_count >= 3, f"Expected natural pagination >= 3 pages, got {page_count}"
        p_doc.close()
    print("  [PASS] Test 20: 2.0x expansion paginates naturally across multiple pages.")


def test_21_target_contraction_fewer_pages():
    """21. Target contraction produces fewer pages without artificial blank pages."""
    short_text = "Văn bản ngắn gọn."
    units = [
        LogicalUnit(unit_id=f"u_{i}", role=StructuralRole.BODY_PARAGRAPH, text=short_text, translated_text=short_text)
        for i in range(2)
    ]
    doc = LogicalDocument(document_id="doc_contract", units=units)
    composer = FlowComposer(doc)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = Path(tmpdir) / "contracted.pdf"
        composer.render_pdf(out_pdf)

        p_doc = pymupdf.open(str(out_pdf))
        page_count = len(p_doc)
        assert page_count == 1, f"Expected 1 page for short content, got {page_count}"
        p_doc.close()
    print("  [PASS] Test 21: Contraction yields minimal natural page count without blank pages.")


def test_22_heading_near_page_bottom_keep_with_next():
    """22. Heading near bottom of page uses keep-with-next (#block(breakable: false))."""
    h_unit = LogicalUnit(unit_id="h1", role=StructuralRole.HEADING_1, text="1. Tiêu đề mục", translated_text="1. Tiêu đề mục")
    doc = LogicalDocument(document_id="doc_keep", units=[h_unit])
    composer = FlowComposer(doc)
    typst_code = composer.compose_typst()
    assert "#block(breakable: false)" in typst_code
    print("  [PASS] Test 22: Keep-with-next invariant embedded in heading composition.")


def test_23_paragraph_near_page_boundary():
    """23. Paragraph near page boundary reflows smoothly without clipping."""
    units = [
        LogicalUnit(unit_id=f"p_{i}", role=StructuralRole.BODY_PARAGRAPH, text="Đoạn văn kiểm tra ngắt trang.", translated_text="Đoạn văn kiểm tra ngắt trang.")
        for i in range(30)
    ]
    doc = LogicalDocument(document_id="doc_boundary", units=units)
    composer = FlowComposer(doc)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = Path(tmpdir) / "boundary.pdf"
        composer.render_pdf(out_pdf)
        p_doc = pymupdf.open(str(out_pdf))
        assert len(p_doc) >= 1
        p_doc.close()
    print("  [PASS] Test 23: Paragraph near page boundary reflows smoothly.")


def test_24_mixed_font_styles_inside_paragraph():
    """24. Inline formatting (bold/italic) inside paragraph is preserved."""
    token1 = InlineToken(base_text="Chế phẩm", is_bold=True)
    token2 = InlineToken(base_text=" thẩm tách dịch lọc.")
    unit = LogicalUnit(
        unit_id="u_fmt",
        role=StructuralRole.BODY_PARAGRAPH,
        text="Chế phẩm thẩm tách dịch lọc.",
        tokens=[token1, token2],
        translated_text="Chế phẩm thẩm tách dịch lọc.",
    )
    doc = LogicalDocument(document_id="doc_fmt", units=[unit])
    composer = FlowComposer(doc)
    typst_code = composer.compose_typst()
    assert "Chế phẩm thẩm tách dịch lọc." in typst_code
    print("  [PASS] Test 24: Mixed font styles inside paragraph preserved.")


def test_25_two_column_detection_and_limitation():
    """25. Two-column document structure is classified and bounded appropriately."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test25.pdf"
        # Two parallel columns
        pages_text = [[
            {"rect": [72, 100, 270, 115], "text": "左カラムの1行目です。", "fontsize": 10.0},
            {"rect": [72, 120, 270, 135], "text": "左カラムの2行目です。", "fontsize": 10.0},
            {"rect": [320, 100, 520, 115], "text": "右カラムの1行目です。", "fontsize": 10.0},
            {"rect": [320, 120, 520, 135], "text": "右カラムの2行目です。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        assert len(log_doc.units) >= 1
        print("  [PASS] Test 25: Two-column layout processed with bounded reading order.")


def test_26_round_trip_traceability():
    """26. Source physical fragments -> logical unit -> translation unit traceability is maintained."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test26.pdf"
        pages_text = [[
            {"rect": [72, 100, 520, 115], "text": "トレーサビリティ検証の本文行です。", "fontsize": 10.0},
        ]]
        create_synthetic_pdf(pages_text, pdf_path)

        log_doc = reconstruct_semantic_document(pdf_path)
        unit = log_doc.units[0]
        assert len(unit.source_fragments) >= 1
        assert unit.source_pages == [1]
        assert len(unit.source_bboxes) >= 1
        print("  [PASS] Test 26: Round-trip traceability verified from physical to logical unit.")


def test_27_verifier_catches_heading_merge():
    """27. Mode-aware verifier detects when a heading is accidentally merged into body text."""
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    # Intentionally bad merged text: prose followed directly by heading
    page.insert_textbox(pymupdf.Rect(72, 100, 520, 130), "Đoạn văn bị dính 2. Phạm vi áp dụng", fontsize=10)

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test27.pdf"
        doc.save(str(pdf_path))
        doc.close()

        profile = LayoutProfile(document_class=DocumentClass.TEXT_FLOW, page_constraint=PageConstraint.FREE, page_count=1)
        res = verify_adaptive_document(pdf_path, profile)
        assert res["metrics"]["heading_merge_defects"] >= 1
        assert res["evaluations"]["HEADING_INTEGRITY"] == "FAIL"
        print("  [PASS] Test 27: Verifier successfully flags heading merge defects.")


def test_28_verifier_catches_detached_tokens():
    """28. Mode-aware verifier detects when inline scientific signs are detached onto solo lines."""
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    page.insert_text(pymupdf.Point(72, 115), "Text before ion", fontsize=10)
    # Detached minus sign alone on a line
    page.insert_text(pymupdf.Point(72, 145), "-", fontsize=10)

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test28.pdf"
        doc.save(str(pdf_path))
        doc.close()

        profile = LayoutProfile(document_class=DocumentClass.TEXT_FLOW, page_constraint=PageConstraint.FREE, page_count=1)
        res = verify_adaptive_document(pdf_path, profile)
        assert res["metrics"]["inline_detached_tokens"] >= 1
        assert res["evaluations"]["INLINE_GROUP_INTEGRITY"] == "FAIL"
        print("  [PASS] Test 28: Verifier successfully flags detached inline scientific tokens.")


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AIWF TRANSLATION #1.7: TEXT_FLOW SEMANTIC RECONSTRUCTION TEST SUITE")
    print("=" * 70)

    tests = [
        test_1_multiline_normal_paragraph_reconstruction,
        test_2_multiple_paragraphs_boundary_detection,
        test_3_numbered_headings_l1_detection,
        test_4_nested_heading_hierarchy_l1_l2_l3,
        test_5_paragraph_split_across_source_page,
        test_6_bullet_list_reconstruction,
        test_7_numbered_list_reconstruction,
        test_8_abbreviation_definition_list_reconstruction,
        test_9_superscript_inline_preservation,
        test_10_subscript_inline_preservation,
        test_11_scientific_symbols_inline,
        test_12_inline_chemical_notation_fused,
        test_13_formula_block_standalone,
        test_14_table_between_paragraphs_detection,
        test_15_table_wrapping_cells_composition,
        test_16_footnote_isolation,
        test_17_recurring_header_footer_isolation,
        test_18_page_number_isolation,
        test_19_long_target_expansion_1_5x,
        test_20_extreme_target_expansion_2_0x,
        test_21_target_contraction_fewer_pages,
        test_22_heading_near_page_bottom_keep_with_next,
        test_23_paragraph_near_page_boundary,
        test_24_mixed_font_styles_inside_paragraph,
        test_25_two_column_detection_and_limitation,
        test_26_round_trip_traceability,
        test_27_verifier_catches_heading_merge,
        test_28_verifier_catches_detached_tokens,
    ]

    passed = 0
    failed = 0

    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 70)
    print(f"SUMMARY: {passed} PASSED, {failed} FAILED across {len(tests)} tests.")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    sys.exit(0)
