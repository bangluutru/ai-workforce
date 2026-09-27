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
    _extract_vi_multiplier_values,
    _parse_vi_number,
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
    assert _extract_numeric("3億円") == 300000000.0
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
    """P1: 1,200万円 → 12 triệu yên MUST PASS (numeric equivalence: 12,000,000 = 12,000,000)."""
    source_vals = extract_critical_values("1,200万円")
    assert len(source_vals) >= 1, f"Source extraction failed: {source_vals}"
    assert source_vals[0]["numeric"] == 12000000.0, f"Source numeric wrong: {source_vals[0]}"
    result = verify_critical_values(source_vals, "12 triệu yên tổng chi phí")
    assert result["pass"] is True, f"P1 FAILED: 1,200万円 → 12 triệu yên should PASS. Got: {result}"
    print("✅ test_verify_large_man_yen (P1) PASSED")


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
# 4b. V2 Multiplier-Aware Positive/Negative Tests
# ===================================================================

def test_vi_multiplier_extraction():
    """Vietnamese multiplier words are correctly parsed."""
    vals = _extract_vi_multiplier_values("12 triệu yên")
    assert 12000000.0 in vals, f"Expected 12M in {vals}"
    vals2 = _extract_vi_multiplier_values("450 nghìn đồng")
    assert 450000.0 in vals2, f"Expected 450K in {vals2}"
    vals3 = _extract_vi_multiplier_values("3,5 tỷ đồng")
    assert 3500000000.0 in vals3, f"Expected 3.5B in {vals3}"
    vals4 = _extract_vi_multiplier_values("1,2 triệu yên")
    assert 1200000.0 in vals4, f"Expected 1.2M in {vals4}"
    print("✅ test_vi_multiplier_extraction PASSED")


def test_vi_number_parsing():
    """Vietnamese number formatting edge cases."""
    assert _parse_vi_number("1,2") == 1.2
    assert _parse_vi_number("98,7") == 98.7
    assert _parse_vi_number("450.000") == 450000.0
    assert _parse_vi_number("1.200") == 1200.0
    assert _parse_vi_number("12") == 12.0
    assert _parse_vi_number("1,200") == 1200.0
    print("✅ test_vi_number_parsing PASSED")


def test_oku_extraction():
    """Japanese 億 (×100M) extraction."""
    assert _extract_numeric("3億円") == 300000000.0
    vals = extract_critical_values("3億円")
    oku_vals = [v for v in vals if v["type"] == "currency_yen_oku"]
    assert len(oku_vals) >= 1, f"Missing 億円 in {vals}"
    print("✅ test_oku_extraction PASSED")


def test_P1_large_man_yen_trieu():
    """P1: 1,200万円 → 12 triệu yên = PASS (12,000,000 = 12,000,000)."""
    src = extract_critical_values("1,200万円")
    result = verify_critical_values(src, "12 triệu yên")
    assert result["pass"] is True, f"P1 FAILED: {result}"
    print("✅ test_P1 PASSED")


def test_P2_man_yen_vn_thousands():
    """P2: 45万円 → 450.000 yên = PASS."""
    src = extract_critical_values("45万円")
    result = verify_critical_values(src, "450.000 yên")
    assert result["pass"] is True, f"P2 FAILED: {result}"
    print("✅ test_P2 PASSED")


def test_P3_percentage_comma():
    """P3: 98.7% → 98,7% = PASS."""
    src = extract_critical_values("98.7%")
    result = verify_critical_values(src, "98,7%")
    assert result["pass"] is True, f"P3 FAILED: {result}"
    print("✅ test_P3 PASSED")


def test_P4_voltage_space():
    """P4: 24V → 24 V = PASS."""
    src = extract_critical_values("24V")
    result = verify_critical_values(src, "24 V")
    assert result["pass"] is True, f"P4 FAILED: {result}"
    print("✅ test_P4 PASSED")


def test_N1_wrong_magnitude_trieu():
    """N1: 1,200万円 → 1,2 triệu yên = FAIL (12,000,000 ≠ 1,200,000)."""
    src = extract_critical_values("1,200万円")
    result = verify_critical_values(src, "1,2 triệu yên")
    assert result["pass"] is False, f"N1 FAILED: should reject 1,2 triệu for 1200万. Got: {result}"
    print("✅ test_N1 PASSED")


def test_N2_wrong_magnitude_120_trieu():
    """N2: 1,200万円 → 120 triệu yên = FAIL (12,000,000 ≠ 120,000,000)."""
    src = extract_critical_values("1,200万円")
    result = verify_critical_values(src, "120 triệu yên")
    assert result["pass"] is False, f"N2 FAILED: should reject 120 triệu for 1200万. Got: {result}"
    print("✅ test_N2 PASSED")


def test_N3_wrong_man_yen_conversion():
    """N3: 45万円 → 45.000 yên = FAIL (450,000 ≠ 45,000)."""
    src = extract_critical_values("45万円")
    result = verify_critical_values(src, "45.000 yên")
    assert result["pass"] is False, f"N3 FAILED: {result}"
    print("✅ test_N3 PASSED")


def test_N4_corrupted_percentage():
    """N4: 98.7% → 89,7% = FAIL (different number)."""
    src = extract_critical_values("98.7%")
    result = verify_critical_values(src, "89,7%")
    assert result["pass"] is False, f"N4 FAILED: {result}"
    print("✅ test_N4 PASSED")


def test_N5_corrupted_voltage():
    """N5: 24V → 240V = FAIL (different magnitude)."""
    src = extract_critical_values("24V")
    result = verify_critical_values(src, "240V")
    assert result["pass"] is False, f"N5 FAILED: {result}"
    print("✅ test_N5 PASSED")


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


def test_unit_mismatch_voltage_to_current_MUST_FAIL():
    """Verify that 24V translated to 24A fails verification."""
    source = "定格電圧はDC 24Vです。"
    translated = "Điện áp định mức là DC 24A."
    sv = extract_critical_values(source)
    res = verify_critical_values(sv, translated)
    assert not res["pass"], f"Expected 24V -> 24A to FAIL, got {res}"
    assert res["corrupted"] >= 1, f"Expected corrupted status, got {res}"
    print("✅ test_unit_mismatch_voltage_to_current_MUST_FAIL PASSED")


def test_currency_mismatch_jpy_to_usd_MUST_FAIL():
    """Verify that 450,000 JPY translated to 450,000 USD fails verification."""
    source = "費用は450,000 JPYです。"
    translated = "Chi phí là 450,000 USD."
    sv = extract_critical_values(source)
    res = verify_critical_values(sv, translated)
    assert not res["pass"], f"Expected 450,000 JPY -> 450,000 USD to FAIL, got {res}"
    assert res["corrupted"] >= 1, f"Expected corrupted status, got {res}"
    print("✅ test_currency_mismatch_jpy_to_usd_MUST_FAIL PASSED")


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
        # V2: Multiplier-aware tests
        test_vi_multiplier_extraction,
        test_vi_number_parsing,
        test_oku_extraction,
        test_P1_large_man_yen_trieu,
        test_P2_man_yen_vn_thousands,
        test_P3_percentage_comma,
        test_P4_voltage_space,
        test_N1_wrong_magnitude_trieu,
        test_N2_wrong_magnitude_120_trieu,
        test_N3_wrong_man_yen_conversion,
        test_N4_corrupted_percentage,
        test_N5_corrupted_voltage,
        # TranslationUnit
        test_translation_unit_basic,
        test_residual_clean,
        test_residual_with_protected,
        test_residual_missed,
        test_load_terminology,
        test_build_terminology_context,
        test_unit_mismatch_voltage_to_current_MUST_FAIL,
        test_currency_mismatch_jpy_to_usd_MUST_FAIL,
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
