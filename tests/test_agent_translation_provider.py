"""Tests for AgentTranslationProvider — the bridge between pipeline and agent runtime."""

import json
import pytest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "dich-thuat"
SCRIPTS_DIR = str(SKILL_DIR / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from translation.agent_provider import AgentTranslationProvider
from translation.provider import IntegratedTranslationProvider, TranslationResult
from translation_foundation import ContentType, TranslationUnit


@pytest.fixture
def tmp_process_dir(tmp_path):
    """Creates a temporary process directory with agent-translations.json."""
    proc = tmp_path / "process"
    proc.mkdir()
    return proc


def _make_unit(uid: str, source: str, src_lang: str = "ja", tgt_lang: str = "vi") -> TranslationUnit:
    return TranslationUnit(
        id=uid,
        source_text=source,
        source_language=src_lang,
        target_language=tgt_lang,
        content_type=ContentType.BODY,
    )


class TestAgentTranslationProvider:

    def test_loads_simple_string_format(self, tmp_process_dir):
        """Agent writes simple {id: text} format."""
        translations = {
            "unit_1": "Xin chào",
            "unit_2": "Thế giới",
        }
        (tmp_process_dir / "agent-translations.json").write_text(
            json.dumps(translations, ensure_ascii=False), encoding="utf-8"
        )

        provider = AgentTranslationProvider(process_dir=tmp_process_dir)
        units = [
            _make_unit("unit_1", "こんにちは"),
            _make_unit("unit_2", "世界"),
        ]

        result = provider.translate(units)
        assert result.success
        assert result.translated_count == 2
        assert result.skipped_count == 0
        assert units[0].translated_text == "Xin chào"
        assert units[1].translated_text == "Thế giới"
        assert result.provider_name == "AgentTranslationProvider"

    def test_loads_extended_format_with_metadata(self, tmp_process_dir):
        """Agent writes extended {id: {translated_text, confidence}} format."""
        translations = {
            "unit_1": {
                "translated_text": "Phó Giáo sư",
                "confidence": 0.95,
                "notes": "Academic title"
            },
        }
        (tmp_process_dir / "agent-translations.json").write_text(
            json.dumps(translations, ensure_ascii=False), encoding="utf-8"
        )

        provider = AgentTranslationProvider(process_dir=tmp_process_dir)
        units = [_make_unit("unit_1", "准教授")]

        result = provider.translate(units)
        assert result.success
        assert result.translated_count == 1
        assert units[0].translated_text == "Phó Giáo sư"

    def test_falls_back_when_no_file(self, tmp_process_dir):
        """When no agent-translations.json exists, delegates to fallback."""
        fallback = IntegratedTranslationProvider()
        provider = AgentTranslationProvider(
            process_dir=tmp_process_dir,
            fallback_provider=fallback,
        )
        units = [_make_unit("unit_1", "12345")]  # Pure number, should be kept by fallback

        result = provider.translate(units)
        assert result.success
        assert result.provider_name == "IntegratedTranslationProvider"

    def test_fails_gracefully_when_no_file_and_no_fallback(self, tmp_process_dir):
        """When no file and no fallback, returns failure result."""
        provider = AgentTranslationProvider(process_dir=tmp_process_dir)
        units = [_make_unit("unit_1", "テスト")]

        result = provider.translate(units)
        assert not result.success
        assert result.skipped_count == 1

    def test_unmapped_units_use_fallback(self, tmp_process_dir):
        """Units not in agent-translations.json delegate to fallback provider."""
        translations = {"unit_1": "Kết quả"}
        (tmp_process_dir / "agent-translations.json").write_text(
            json.dumps(translations, ensure_ascii=False), encoding="utf-8"
        )

        fallback = IntegratedTranslationProvider()
        provider = AgentTranslationProvider(
            process_dir=tmp_process_dir,
            fallback_provider=fallback,
        )

        units = [
            _make_unit("unit_1", "結果"),
            _make_unit("unit_2", "42.5%"),  # Pure number, fallback handles
        ]

        result = provider.translate(units)
        assert result.success
        assert units[0].translated_text == "Kết quả"
        # unit_2 should be preserved by fallback since it's purely numeric
        assert "42.5%" in units[1].translated_text

    def test_integrity_rejects_corrupted_numbers(self, tmp_process_dir):
        """Agent translation that corrupts/drops critical numeric values is rejected."""
        translations = {
            "unit_1": "Tỷ lệ là 99%",  # Source says 85%, agent changed to 99%
        }
        (tmp_process_dir / "agent-translations.json").write_text(
            json.dumps(translations, ensure_ascii=False), encoding="utf-8"
        )

        provider = AgentTranslationProvider(process_dir=tmp_process_dir)
        units = [_make_unit("unit_1", "割合は85%です")]

        result = provider.translate(units)
        # Should have a warning about corrupted/missing value
        assert len(result.warnings) > 0
        assert "critical" in result.warnings[0].lower() or "corrupted" in result.warnings[0].lower()

    def test_source_text_key_match(self, tmp_process_dir):
        """Agent can write translations keyed by source text instead of unit ID."""
        translations = {
            "准教授": "Phó Giáo sư",
        }
        (tmp_process_dir / "agent-translations.json").write_text(
            json.dumps(translations, ensure_ascii=False), encoding="utf-8"
        )

        provider = AgentTranslationProvider(process_dir=tmp_process_dir)
        units = [_make_unit("p1_cell_0_2", "准教授")]

        result = provider.translate(units)
        assert result.success
        assert units[0].translated_text == "Phó Giáo sư"

    def test_generate_translation_prompt(self):
        """Smoke test for prompt generation."""
        units = [
            _make_unit("u1", "透析治療"),
            _make_unit("u2", "共同研究"),
        ]
        prompt = AgentTranslationProvider.generate_translation_prompt(
            units, target_language="vi", document_domain="Medical Research"
        )

        assert "Translation Task" in prompt
        assert "Medical Research" in prompt
        assert "透析治療" in prompt
        assert "共同研究" in prompt
        assert "agent-translations" not in prompt  # Prompt shouldn't reference itself

    def test_save_plan_for_agent(self, tmp_process_dir):
        """Plan saving creates both structured plan and human-readable prompt."""
        units = [_make_unit("u1", "テスト文章")]
        prompt_path = AgentTranslationProvider.save_plan_for_agent(
            units, process_dir=tmp_process_dir, target_language="vi"
        )

        assert prompt_path.exists()
        assert (tmp_process_dir / "translation-plan.json").exists()

        plan = json.loads((tmp_process_dir / "translation-plan.json").read_text())
        assert len(plan) == 1
        assert plan[0]["id"] == "u1"
        assert plan[0]["source_text"] == "テスト文章"

    def test_empty_source_text_units_skipped(self, tmp_process_dir):
        """Units with empty source text are skipped gracefully."""
        translations = {"unit_1": "Something"}
        (tmp_process_dir / "agent-translations.json").write_text(
            json.dumps(translations, ensure_ascii=False), encoding="utf-8"
        )

        provider = AgentTranslationProvider(process_dir=tmp_process_dir)
        units = [
            _make_unit("unit_1", "テスト"),
            _make_unit("unit_2", ""),
            _make_unit("unit_3", "  "),
        ]

        result = provider.translate(units)
        assert result.translated_count == 1  # Only unit_1
