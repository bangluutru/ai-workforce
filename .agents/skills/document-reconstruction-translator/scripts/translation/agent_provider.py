"""Agent Translation Provider — Bridge between Pipeline and Antigravity IDE Agent Runtime.

Architecture:
  When the skill runs autonomously (SKILL.md → Agent orchestration), translation
  follows a 2-phase protocol:

  Phase 1 (Pipeline → Plan):
    pipeline writes `translation-plan.json` with all TranslationUnits.

  Phase 2 (Agent → Translate → File):
    The agent (the LLM integrated in Antigravity IDE) reads the plan,
    translates all text blocks leveraging its full linguistic capability,
    and writes results to `agent-translations.json` in the process directory.

  Phase 3 (Pipeline reads file → applies to IR):
    AgentTranslationProvider reads `agent-translations.json` and maps
    translations back to TranslationUnits.

This provider does NOT call any external REST API.
The agent IS the translation engine — it translates by reading and writing files.
For programmatic (non-agent) use cases, the IntegratedTranslationProvider remains
the fallback that uses terminology dictionaries and translation memory.

Usage (from SKILL.md autonomous execution):
  1. Agent runs pipeline Phase 1: creates translation-plan.json
  2. Agent reads translation-plan.json, translates all units, writes agent-translations.json
  3. Agent runs pipeline Phase 2 with AgentTranslationProvider(process_dir)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from translation_foundation import (
    ContentType,
    TermEntry,
    TranslationUnit,
    detect_protected_entities,
    extract_critical_values,
    verify_critical_values,
    verify_protected_entities,
)
from .provider import TranslationProvider, TranslationResult


class AgentTranslationProvider(TranslationProvider):
    """Translation provider that reads agent-produced translations from disk.

    The Antigravity IDE agent performs the actual translation as an LLM,
    writing results to a JSON file. This provider loads those results
    and maps them back to TranslationUnits with full integrity validation.

    File format for agent-translations.json:
    {
        "<unit_id>": "<translated_text>",
        ...
    }

    OR (extended format with metadata):
    {
        "<unit_id>": {
            "translated_text": "<text>",
            "confidence": 0.95,
            "notes": "..."
        },
        ...
    }
    """

    def __init__(
        self,
        process_dir: Path,
        translations_filename: str = "agent-translations.json",
        fallback_provider: Optional[TranslationProvider] = None,
    ):
        self.process_dir = Path(process_dir)
        self.translations_filename = translations_filename
        self.fallback_provider = fallback_provider
        self._agent_translations: Dict[str, str] = {}
        self._agent_metadata: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _load_translations(self) -> None:
        """Loads agent-produced translations from disk."""
        if self._loaded:
            return
        self._loaded = True

        translations_file = self.process_dir / self.translations_filename
        if not translations_file.exists():
            return

        try:
            raw = json.loads(translations_file.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return

            for key, value in raw.items():
                if isinstance(value, str):
                    self._agent_translations[key] = value
                elif isinstance(value, dict):
                    trans_text = value.get("translated_text", "")
                    if trans_text:
                        self._agent_translations[key] = str(trans_text)
                    self._agent_metadata[key] = value
        except (json.JSONDecodeError, UnicodeDecodeError):
            return

    def translate(
        self,
        units: List[TranslationUnit],
        context: str = "",
        glossary: Optional[List[TermEntry]] = None,
    ) -> TranslationResult:
        """Applies agent-produced translations to units, with integrity checks."""
        self._load_translations()

        if not self._agent_translations:
            # No agent translations available — delegate to fallback if present
            if self.fallback_provider:
                return self.fallback_provider.translate(units, context, glossary)
            return TranslationResult(
                units=units,
                success=False,
                provider_name="AgentTranslationProvider",
                total_units=len(units),
                translated_count=0,
                skipped_count=len(units),
                warnings=["No agent-translations.json found; no fallback provider set."],
            )

        translated_count = 0
        skipped_count = 0
        warnings: List[str] = []

        for unit in units:
            src = unit.source_text.strip()
            if not src:
                unit.translated_text = ""
                continue

            # Try unit ID match first
            agent_text = self._agent_translations.get(unit.id)

            # Try source_block_id match
            if agent_text is None and unit.source_block_id:
                agent_text = self._agent_translations.get(unit.source_block_id)

            # Try source text exact match
            if agent_text is None:
                agent_text = self._agent_translations.get(src)

            if agent_text is not None:
                # Integrity validation: ensure critical values are preserved
                src_vals = extract_critical_values(src)
                if src_vals:
                    val_result = verify_critical_values(src_vals, agent_text)
                    if not val_result["pass"]:
                        # Check for CORRUPTED or MISSING critical values
                        problems = [
                            d for d in val_result["details"]
                            if d["status"] in ("CORRUPTED", "MISSING")
                        ]
                        if problems:
                            reason = problems[0].get("reason", problems[0].get("status", "unknown"))
                            warnings.append(
                                f"Agent translation for {unit.id} has critical value issues: "
                                f"{reason} ({problems[0].get('value', '')}). Using original."
                            )
                            unit.translated_text = src
                            skipped_count += 1
                            continue

                # Integrity validation: ensure protected entities are preserved
                if unit.protected_tokens:
                    entity_violations = verify_protected_entities(src, agent_text, unit.protected_tokens)
                    if entity_violations:
                        warnings.append(
                            f"Agent translation for {unit.id} corrupted protected entities. "
                            f"Violations: {entity_violations[:2]}. Accepting with warning."
                        )

                unit.translated_text = agent_text
                translated_count += 1
            else:
                # Delegate to fallback provider for unmapped units
                if self.fallback_provider:
                    fallback_result = self.fallback_provider.translate(
                        [unit], context, glossary
                    )
                    if unit.translated_text and unit.translated_text != src:
                        translated_count += 1
                    else:
                        skipped_count += 1
                else:
                    unit.translated_text = src
                    skipped_count += 1
                    warnings.append(
                        f"No agent translation for unit: {unit.id} ({src[:30]}...)"
                    )

        return TranslationResult(
            units=units,
            success=True,
            provider_name="AgentTranslationProvider",
            total_units=len(units),
            translated_count=translated_count,
            skipped_count=skipped_count,
            warnings=warnings,
            metadata={
                "agent_translations_count": len(self._agent_translations),
                "used_fallback": self.fallback_provider is not None,
            },
        )

    @staticmethod
    def generate_translation_prompt(
        units: List[TranslationUnit],
        target_language: str = "vi",
        document_domain: str = "",
        glossary: Optional[List[TermEntry]] = None,
    ) -> str:
        """Generates a structured translation prompt for the agent to process.

        The agent reads this prompt, translates all units, and writes
        the result to agent-translations.json.

        Returns:
            A markdown-formatted prompt string that the agent can process.
        """
        lang_names = {"vi": "Tiếng Việt", "en": "English", "ja": "日本語"}
        target_name = lang_names.get(target_language, target_language)

        lines = [
            f"# Translation Task — {len(units)} units → {target_name}",
            "",
        ]

        if document_domain:
            lines.append(f"**Document Domain**: {document_domain}")
            lines.append("")

        if glossary:
            lines.append("## Terminology Glossary (MUST follow)")
            lines.append("| Source | Target |")
            lines.append("|--------|--------|")
            for term in glossary[:50]:
                lines.append(f"| {term.source} | {term.target} |")
            lines.append("")

        lines.append("## Rules")
        lines.append("1. Translate ALL source text to the target language.")
        lines.append("2. Preserve numbers, percentages, model codes, units of measurement EXACTLY.")
        lines.append("3. Use domain-appropriate terminology from the glossary above.")
        lines.append("4. Do NOT translate proper nouns (personal names, company names) — keep original.")
        lines.append("5. For table cells containing only numbers or codes, keep them unchanged.")
        lines.append("")
        lines.append("## Units to Translate")
        lines.append("For each unit, output ONLY the translated text.")
        lines.append("")

        for unit in units:
            src = unit.source_text.strip()
            if not src:
                continue
            protected_str = ""
            if unit.protected_tokens:
                protected_str = f" [KEEP: {', '.join(unit.protected_tokens[:5])}]"
            lines.append(f"### `{unit.id}` ({unit.content_type.value}){protected_str}")
            lines.append(f"```")
            lines.append(src)
            lines.append(f"```")
            lines.append("")

        lines.append("## Output Format")
        lines.append("Write your translations as a JSON object mapping unit IDs to translated text:")
        lines.append("```json")
        lines.append("{")
        sample_ids = [u.id for u in units[:3] if u.source_text.strip()]
        for sid in sample_ids:
            lines.append(f'  "{sid}": "<translated text here>",')
        lines.append("  ...")
        lines.append("}")
        lines.append("```")

        return "\n".join(lines)

    @staticmethod
    def save_plan_for_agent(
        units: List[TranslationUnit],
        process_dir: Path,
        target_language: str = "vi",
        document_domain: str = "",
        glossary: Optional[List[TermEntry]] = None,
    ) -> Path:
        """Saves the translation plan and prompt for the agent to pick up.

        Returns:
            Path to the generated agent-translation-prompt.md file.
        """
        proc = Path(process_dir)
        proc.mkdir(parents=True, exist_ok=True)

        # Save structured plan
        plan_data = []
        for u in units:
            plan_data.append({
                "id": u.id,
                "source_text": u.source_text,
                "content_type": u.content_type.value,
                "context": u.context,
                "protected_tokens": u.protected_tokens,
                "source_language": u.source_language,
                "target_language": u.target_language,
            })
        (proc / "translation-plan.json").write_text(
            json.dumps(plan_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Save human-readable prompt for the agent
        prompt = AgentTranslationProvider.generate_translation_prompt(
            units, target_language, document_domain, glossary
        )
        prompt_file = proc / "agent-translation-prompt.md"
        prompt_file.write_text(prompt, encoding="utf-8")

        return prompt_file
