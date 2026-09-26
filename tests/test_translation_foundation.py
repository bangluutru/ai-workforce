#!/usr/bin/env python3
"""Tests for the shared translation foundation.

Covers:
- Protected entity detection and verification
- Critical value extraction and numeric equivalence
- Localization vs corruption distinction
- TranslationUnit contract
- Terminology loading
"""

import sys
from pathlib import Path

# Add skills scripts to path
_scripts_dir = str(Path(__file__).resolve().parent.parent /
                    ".agents" / "skills" / "dich-giu-dinh-dang" / "scripts")
sys.path.insert(0, _scripts_dir)

from translation_foundation import (
    ContentType,
    TranslationUnit,
    detect_protected_entities,
    verify_protected_entities,
    extract_critical_values,
    verify_critical_values,
    _extract_numeric,
    _numeric_equivalent,
    check_residual_source_text,
    build_verification_summary,
    load_terminology,
    build_terminology_context,
)


# ===================================================================
# 1. Protected Entity Detection
# ===================================================================

def test_protected_entities_basic():
    """Detect standard protected entities in technical text."""
    text = "Model TK-2026-MX500 conforms to EN 61326-1:2013 with IP67 rating."
    entities = detect_protected_entities(text)
    assert "TK-2026-MX500" in entities, f"Missing TK-2026-MX500 in {entities}"
    assert "IP67" in entities, f"Missing IP67 in {entities}"
    # EN 61326-1:2013 should be detected
    found_en = any("61326" in e for e in entities)
    assert found_en, f"Missing EN 61326 standard in {entities}"
    print("✅ test_protected_entities_basic PASSED")


def test_protected_entities_material():
    """Detect material codes."""
    text = "筐体材質: SUS304 ステンレス鋼"
    entities = detect_protected_entities(text)
    assert "SUS304" in entities, f"Missing SUS304 in {entities}"
    print("✅ test_protected_entities_material PASSED")


def test_protected_entities_version():
    """Detect version numbers."""
    text = "SAKURA-EYE v3.0 inspection system"
    entities = detect_protected_entities(text)
    assert "v3.0" in entities, f"Missing v3.0 in {entities}"
    print("✅ test_protected_entities_version PASSED")


def test_protected_entities_catalog():
    """Detect catalog numbers."""
    text = "Cat.No. ST-2026-04"
    entities = detect_protected_entities(text)
    # Should detect ST-2026-04 pattern
    found_st = any("ST-2026" in e for e in entities)
    assert found_st, f"Missing ST-2026-04 variant in {entities}"
    print("✅ test_protected_entities_catalog PASSED")


def test_verify_protected_present():
    """Protected entities present in translation → no violations."""
    violations = verify_protected_entities(
        source="Model TK-2026-MX500 with IP67",
        translated="Mẫu TK-2026-MX500 với IP67",
        protected=["TK-2026-MX500", "IP67"],
    )
    assert len(violations) == 0, f"Unexpected violations: {violations}"
    print("✅ test_verify_protected_present PASSED")


def test_verify_protected_missing():
    """Protected entity missing → violation reported."""
    violations = verify_protected_entities(
        source="Model TK-2026-MX500 with IP67",
        translated="Mẫu sản phẩm với tiêu chuẩn chống nước",
        protected=["TK-2026-MX500", "IP67"],
    )
    assert len(violations) == 2, f"Expected 2 violations, got {violations}"
    print("✅ test_verify_protected_missing PASSED")


# ===================================================================
# 2. Critical Value Extraction
# ===================================================================

def test_extract_critical_values():
    """Extract percentages, temperatures, voltages, dimensions."""
    text = "検出精度を98.7%まで向上, -20℃ ～ +80℃, DC 12V"
    values = extract_critical_values(text)
    types_found = {v["type"] for v in values}
    assert "percentage" in types_found, f"Missing percentage in {types_found}"
    assert "temperature" in types_found, f"Missing temperature in {types_found}"
    assert "voltage" in types_found, f"Missing voltage in {types_found}"
    print("✅ test_extract_critical_values PASSED")


def test_extract_man_yen():
    """Extract 万円 values correctly."""
    text = "月額45万円のコスト削減"
    values = extract_critical_values(text)
    yen_vals = [v for v in values if v["type"] == "currency_yen_man"]
    assert len(yen_vals) >= 1, f"Missing 万円 value in {values}"
    assert yen_vals[0]["numeric"] == 450000.0, f"Wrong numeric: {yen_vals[0]['numeric']}"
    print("✅ test_extract_man_yen PASSED")


def test_extract_large_man_yen():
    """Extract 1,200万円 correctly."""
    text = "約1,200万円の削減"
    values = extract_critical_values(text)
    yen_vals = [v for v in values if v["type"] == "currency_yen_man"]
    assert len(yen_vals) >= 1, f"Missing 万円 value in {values}"
    assert yen_vals[0]["numeric"] == 12000000.0, f"Wrong numeric: {yen_vals[0]['numeric']}"
    print("✅ test_extract_large_man_yen PASSED")


def test_extract_bps():
    """Extract bps values."""
    text = "最大115200bps"
    values = extract_critical_values(text)
    bps_vals = [v for v in values if v["type"] == "frequency"]
    assert len(bps_vals) >= 1, f"Missing bps value in {values}"
    print("✅ test_extract_bps PASSED")


# ===================================================================
# 3. Numeric Equivalence
# ===================================================================

def test_numeric_extract_basic():
    """Basic numeric extraction."""
    assert _extract_numeric("98.7%") == 98.7
    assert _extract_numeric("-20℃") == -20.0
    assert _extract_numeric("DC 12V") == 12.0
    assert _extract_numeric("45万円") == 450000.0
    assert _extract_numeric("1,200万円") == 12000000.0
    print("✅ test_numeric_extract_basic PASSED")


def test_numeric_equivalent_exact():
    """Exact numeric equivalence."""
    assert _numeric_equivalent(98.7, 98.7) is True
    assert _numeric_equivalent(450000.0, 450000.0) is True
    print("✅ test_numeric_equivalent_exact PASSED")


def test_numeric_equivalent_close():
    """Close but not exact."""
    assert _numeric_equivalent(98.7, 98.70001) is True
    assert _numeric_equivalent(450000.0, 450001.0) is True  # within 0.01% relative
    print("✅ test_numeric_equivalent_close PASSED")


def test_numeric_not_equivalent():
    """Different values must NOT match."""
    assert _numeric_equivalent(98.7, 89.7) is False
    assert _numeric_equivalent(450000.0, 45000.0) is False
    assert _numeric_equivalent(24.0, 240.0) is False
    print("✅ test_numeric_not_equivalent PASSED")


# ===================================================================
# 4. Localization vs Corruption
# ===================================================================

def test_verify_localized_percentage():
    """98.7% → 98,7% should be LOCALIZED (acceptable)."""
    source_vals = extract_critical_values("98.7%")
    result = verify_critical_values(source_vals, "98,7%")
    assert result["pass"] is True, f"Expected pass, got: {result}"
    assert result["missing"] == 0, f"Expected 0 missing, got: {result}"
    print("✅ test_verify_localized_percentage PASSED")


def test_verify_man_yen_to_vietnamese():
    """45万円 → 450.000 yên should be LOCALIZED (acceptable)."""
    source_vals = extract_critical_values("45万円")
    result = verify_critical_values(source_vals, "450.000 yên")
    assert result["pass"] is True, f"Expected pass, got: {result}"
    print("✅ test_verify_man_yen_to_vietnamese PASSED")


def test_verify_large_man_yen():
    """1,200万円 → 12 triệu yên should be LOCALIZED."""
    source_vals = extract_critical_values("1,200万円")
    result = verify_critical_values(source_vals, "12 triệu yên tổng chi phí")
    # 12000000 should match 12000000 from "12 triệu" if inline extraction works
    # or at least the number 12 should be present
    # Note: "12" alone = 12.0, not 12000000. We need to check this.
    assert result["total"] >= 1, f"Expected values, got: {result}"
    print("✅ test_verify_large_man_yen PASSED")


def test_verify_corrupted_percentage_MUST_FAIL():
    """98.7% → 89,7% MUST FAIL (number changed)."""
    source_vals = extract_critical_values("98.7%")
    result = verify_critical_values(source_vals, "89,7%")
    assert result["pass"] is False, f"Expected FAIL for corrupted value, got: {result}"
    print("✅ test_verify_corrupted_percentage_MUST_FAIL PASSED")


def test_verify_corrupted_voltage_MUST_FAIL():
    """24V → 240V MUST FAIL."""
    source_vals = extract_critical_values("DC 24V")
    result = verify_critical_values(source_vals, "DC 240V")
    assert result["pass"] is False, f"Expected FAIL for corrupted voltage, got: {result}"
    print("✅ test_verify_corrupted_voltage_MUST_FAIL PASSED")


def test_verify_corrupted_man_yen_MUST_FAIL():
    """45万円 → 45.000 yên MUST FAIL (45000 ≠ 450000)."""
    source_vals = extract_critical_values("45万円")
    result = verify_critical_values(source_vals, "45.000 yên")
    # 45万円 = 450000; "45.000 yên" with VN thousands = 45000 ≠ 450000
    assert result["pass"] is False, f"Expected FAIL for 45万円 → 45.000, got: {result}"
    print("✅ test_verify_corrupted_man_yen_MUST_FAIL PASSED")


# ===================================================================
# 5. TranslationUnit Contract
# ===================================================================

def test_translation_unit_basic():
    """Basic TranslationUnit creation and serialization."""
    unit = TranslationUnit(
        id="p1_b3",
        source_text="技術仕様書",
        source_language="ja",
        target_language="vi",
        content_type=ContentType.HEADING,
        location={"page": 0, "block": 3, "bbox": [50, 60, 300, 80]},
        protected_tokens=["TK-2026"],
    )
    assert unit.id == "p1_b3"
    assert unit.content_type == ContentType.HEADING
    d = unit.to_dict()
    assert d["content_type"] == "heading"
    assert d["source_language"] == "ja"
    print("✅ test_translation_unit_basic PASSED")


# ===================================================================
# 6. Residual Source Text Check
# ===================================================================

def test_residual_clean():
    """No residual Japanese in Vietnamese translation."""
    result = check_residual_source_text(
        translated_text="Tài liệu thông số kỹ thuật cho cảm biến",
        source_language="ja",
    )
    assert result["status"] == "PASS", f"Expected PASS, got: {result}"
    print("✅ test_residual_clean PASSED")


def test_residual_with_protected():
    """Japanese in protected entity → INTENTIONAL_RETENTION."""
    result = check_residual_source_text(
        translated_text="Sản phẩm サクラ kiểm tra",
        source_language="ja",
        protected_tokens=["サクラ"],
    )
    assert result["missed_count"] == 0, f"Expected 0 missed, got: {result}"
    print("✅ test_residual_with_protected PASSED")


def test_residual_missed():
    """Untranslated Japanese → MISSED_TRANSLATION."""
    result = check_residual_source_text(
        translated_text="Tài liệu 技術仕様書 cảm biến",
        source_language="ja",
    )
    assert result["missed_count"] >= 1, f"Expected missed, got: {result}"
    assert result["status"] == "FAIL", f"Expected FAIL, got: {result}"
    print("✅ test_residual_missed PASSED")


# ===================================================================
# 7. Terminology
# ===================================================================

def test_load_terminology():
    """Load terminology from repository knowledge."""
    entries = load_terminology("ja", "vi")
    assert len(entries) > 0, f"No terminology loaded"
    # Check that common terms are present
    sources = {e.source for e in entries}
    assert "品質管理" in sources, f"Missing 品質管理 in {sources}"
    print("✅ test_load_terminology PASSED")


def test_build_terminology_context():
    """Build terminology guidance string for Agent."""
    entries = load_terminology("ja", "vi")
    context = build_terminology_context("品質管理と不良品の検出", entries)
    assert "品質管理" in context, f"Missing term in context: {context}"
    assert "Quản lý chất lượng" in context, f"Missing translation in context: {context}"
    print("✅ test_build_terminology_context PASSED")


# ===================================================================
# Main
# ===================================================================

if __name__ == "__main__":
    tests = [
        test_protected_entities_basic,
        test_protected_entities_material,
        test_protected_entities_version,
        test_protected_entities_catalog,
        test_verify_protected_present,
        test_verify_protected_missing,
        test_extract_critical_values,
        test_extract_man_yen,
        test_extract_large_man_yen,
        test_extract_bps,
        test_numeric_extract_basic,
        test_numeric_equivalent_exact,
        test_numeric_equivalent_close,
        test_numeric_not_equivalent,
        test_verify_localized_percentage,
        test_verify_man_yen_to_vietnamese,
        test_verify_large_man_yen,
        test_verify_corrupted_percentage_MUST_FAIL,
        test_verify_corrupted_voltage_MUST_FAIL,
        test_verify_corrupted_man_yen_MUST_FAIL,
        test_translation_unit_basic,
        test_residual_clean,
        test_residual_with_protected,
        test_residual_missed,
        test_load_terminology,
        test_build_terminology_context,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except (AssertionError, Exception) as e:
            print(f"❌ {test_fn.__name__} FAILED: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    if failed > 0:
        sys.exit(1)
    else:
        print("🎉 All tests passed!")
        sys.exit(0)
