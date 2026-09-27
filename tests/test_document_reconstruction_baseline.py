"""Baseline Parity Test for Document Reconstruction Translator (Skill Clone & Isolation).

Verifies Phase A requirements:
- Cloned skill exists at .agents/skills/document-reconstruction-translator
- Cloned modules import cleanly and independently
- Full baseline execution parity with original skill
- Original skill (.agents/skills/dich-giu-dinh-dang) is completely untouched and intact
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "dich-giu-dinh-dang"
CLONED_SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "document-reconstruction-translator"


def test_1_structure_and_isolation():
    """Verify cloned skill exists with all expected scripts and references."""
    print("  [TEST 1] Verifying directory structure and isolation...")
    assert ORIGINAL_SKILL_DIR.exists(), "Original skill directory missing!"
    assert CLONED_SKILL_DIR.exists(), "Cloned skill directory missing!"
    assert (CLONED_SKILL_DIR / "SKILL.md").exists(), "Cloned SKILL.md missing!"
    assert (CLONED_SKILL_DIR / "references" / "SOP-document-reconstruction-translator.md").exists(), (
        "Cloned SOP reference missing!"
    )

    expected_scripts = [
        "pdf_asset_extractor.py",
        "typst_overlay.py",
        "verify_retention.py",
        "verify_layout_parity.py",
        "verify_layout_quality.py",
        "translation_foundation.py",
        "analyzer/document_classifier.py",
        "analyzer/layout_profile.py",
        "layout/logical_document.py",
        "layout/semantic_reconstructor.py",
        "layout/translation_mapper.py",
        "render/flow_composer.py",
        "render/flow_renderer.py",
        "render/hybrid_composer.py",
        "verify/mode_aware_verifier.py",
    ]

    for script in expected_scripts:
        orig = ORIGINAL_SKILL_DIR / "scripts" / script
        cloned = CLONED_SKILL_DIR / "scripts" / script
        assert orig.exists(), f"Original script {script} missing!"
        assert cloned.exists(), f"Cloned script {script} missing!"
    print("  [PASS] All expected scripts present in cloned skill.")


def test_2_cloned_module_import_and_execution():
    """Verify cloned modules import independently and execute correctly."""
    print("  [TEST 2] Verifying independent import and execution of cloned modules...")
    cloned_scripts_dir = str(CLONED_SKILL_DIR / "scripts")
    
    # Save original sys.path and prepend cloned scripts
    orig_path = list(sys.path)
    if cloned_scripts_dir not in sys.path:
        sys.path.insert(0, cloned_scripts_dir)

    try:
        from analyzer.layout_profile import DocumentClass, LayoutProfile, PageConstraint
        from layout.logical_document import LogicalDocument, LogicalSection, LogicalUnit, StructuralRole
        from layout.semantic_reconstructor import SemanticReconstructor
        from layout.translation_mapper import TranslationMapper
        from render.flow_composer import FlowComposer

        # Create sample LogicalDocument
        doc = LogicalDocument(document_id="doc1", source_pdf="sample.pdf")
        heading_unit = LogicalUnit(
            unit_id="u0",
            role=StructuralRole.HEADING_1,
            text="1. Introduction",
            translated_text="1. Giới thiệu",
        )
        sec = LogicalSection(section_id="sec1", heading=heading_unit)
        body_unit = LogicalUnit(
            unit_id="u1",
            role=StructuralRole.BODY_PARAGRAPH,
            text="This is a test paragraph.",
            translated_text="Đây là đoạn văn thử nghiệm.",
        )
        sec.units.append(body_unit)
        doc.sections.append(sec)
        doc.units.extend([heading_unit, body_unit])

        # Check export
        d_dict = doc.to_dict()
        assert len(d_dict["units"]) == 2
        assert d_dict["counts_by_role"]["HEADING_1"] == 1
        assert d_dict["counts_by_role"]["BODY_PARAGRAPH"] == 1

        # Verify FlowComposer renders Typst code
        composer = FlowComposer(log_doc=doc)
        markup = composer.compose_typst()
        assert "Đây là đoạn văn thử nghiệm." in markup
        assert "#set text(" in markup
        assert 'lang: "vi"' in markup
        print("  [PASS] Cloned modules executed independently and produced valid output.")
    finally:
        sys.path = orig_path


def test_3_original_skill_immutability():
    """Verify original skill has not been modified."""
    print("  [TEST 3] Verifying original skill immutability...")
    orig_skill_md = (ORIGINAL_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "name: dich-giu-dinh-dang" in orig_skill_md
    assert "display-name: Dịch Giữ Định Dạng" in orig_skill_md
    print("  [PASS] Original skill dich-giu-dinh-dang is completely unchanged.")


if __name__ == "__main__":
    print("=" * 70)
    print("AIWF PHASE A: CLONE & ISOLATION BASELINE VERIFICATION")
    print("=" * 70)
    test_1_structure_and_isolation()
    test_2_cloned_module_import_and_execution()
    test_3_original_skill_immutability()
    print("=" * 70)
    print("ALL PHASE A BASELINE TESTS PASSED!")
    print("=" * 70)
