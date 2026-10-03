"""Structure test for the merged `dich-thuat` skill (R7 consolidation).

`dich-giu-dinh-dang` (preserve) and `document-reconstruction-translator` (reconstruct)
were merged into `.agents/skills/dich-thuat`. Generic PDF tools (asset extraction,
retention / coordinate / layout-parity verifiers) live once in `.agents/skills/_shared/pdf`.

Verifies:
- dich-thuat exists with both rendering modes (preserve + reconstruct)
- shared PDF tools exist in _shared/pdf and are NOT duplicated inside skills
- the reconstruct modules import and render Typst markup
- old skill directories are gone
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
SKILL_DIR = SKILLS_DIR / "dich-thuat"
SHARED_PDF_DIR = SKILLS_DIR / "_shared" / "pdf"

SHARED_PDF_TOOLS = [
    "pdf_asset_extractor.py",
    "verify_retention.py",
    "verify_layout_parity.py",
    "verify_coordinates.py",
]

SKILL_SCRIPTS = [
    "typst_overlay.py",
    "verify_layout_quality.py",
    "translation_foundation.py",
    "analyzer/document_classifier.py",
    "analyzer/layout_profile.py",
    "layout/logical_document.py",
    "layout/semantic_reconstructor.py",
    "layout/translation_mapper.py",
    "pipeline/document_pipeline.py",
    "render/flow_composer.py",
    "render/flow_renderer.py",
    "render/hybrid_composer.py",
    "verify/mode_aware_verifier.py",
]


def test_1_merged_structure():
    """dich-thuat holds the rendering engine; _shared/pdf holds generic tools."""
    assert SKILL_DIR.exists(), "dich-thuat skill directory missing"
    skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "name: dich-thuat" in skill_md
    assert "Dịch Thuật" in skill_md

    for script in SKILL_SCRIPTS:
        assert (SKILL_DIR / "scripts" / script).exists(), f"dich-thuat/scripts/{script} missing"

    for tool in SHARED_PDF_TOOLS:
        assert (SHARED_PDF_DIR / tool).exists(), f"_shared/pdf/{tool} missing"
        dups = [p for p in SKILLS_DIR.glob(f"*/scripts/**/{tool}") if "_shared" not in p.parts]
        assert not dups, f"{tool} duplicated outside _shared (R7): {dups}"


def test_2_reconstruct_modules_import_and_render():
    """Reconstruct-mode modules import from dich-thuat/scripts and compose Typst."""
    scripts_dir = str(SKILL_DIR / "scripts")
    orig_path = list(sys.path)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from layout.logical_document import LogicalDocument, LogicalSection, LogicalUnit, StructuralRole
        from render.flow_composer import FlowComposer

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

        d_dict = doc.to_dict()
        assert len(d_dict["units"]) == 2
        assert d_dict["counts_by_role"]["HEADING_1"] == 1
        assert d_dict["counts_by_role"]["BODY_PARAGRAPH"] == 1

        markup = FlowComposer(log_doc=doc).compose_typst()
        assert "Đây là đoạn văn thử nghiệm." in markup
        assert "#set text(" in markup
        assert 'lang: "vi"' in markup
    finally:
        sys.path = orig_path


def test_3_old_skills_removed():
    """Merged skills must not linger (single owner per capability)."""
    assert not (SKILLS_DIR / "dich-giu-dinh-dang").exists()
    assert not (SKILLS_DIR / "document-reconstruction-translator").exists()


if __name__ == "__main__":
    test_1_merged_structure()
    test_2_reconstruct_modules_import_and_render()
    test_3_old_skills_removed()
    print("ALL dich-thuat STRUCTURE TESTS PASSED")
