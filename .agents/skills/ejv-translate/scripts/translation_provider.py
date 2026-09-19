#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translation Provider Abstraction for AI Workforce (AIWF).

Provides a decoupled interface for translation engines:
1. AgentBatchProvider (Default):
   - 100% Zero External API.
   - Outputs batch_XXX_source.json with formula placeholders (<formula_N>).
   - Antigravity IDE Agent translates batches and saves batch_XXX_translated.json.
   - Merger combines them into standardized merged_ejv.json.
2. OllamaProvider (Local Model):
   - Connects to local Ollama server at http://localhost:11434/v1.
   - Zero commercial API key. Runs fully offline on user's hardware.
3. CachedProvider:
   - Replays from precomputed translation files (merged_ejv.json) for instant testing.
"""

from __future__ import annotations

import abc
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# Formula and technical token preservation regex
FORMULA_PATTERNS = [
    re.compile(r"\b(?:Na|K|Cl|Ca|Mg|HCO3|CH3COO|H2CO3|CO2|H2O|NH4|Fe|Zn)(?:\d*[+-]|\^\d*[+-])?\b"),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:mmol/L|mg/dL|mL/min|mmHg|mEq/L|L/min|g/dL|μmol/L|mol/L|kPa|%|ppm)\b", re.IGNORECASE),
    re.compile(r"\b(?:JCCRM\s*\d+|DIA\d+-\d+-\d+|EX-[A-Z0-9]+|J\d{5}|JAN\s*\d{13}|\d{13})\b"),
    re.compile(r"(?:[±×÷≤≥≈~]\s*\d+(?:\.\d+)?)"),
]


def protect_formulas(text: str) -> Tuple[str, Dict[str, str]]:
    """Replaces technical formulas and standards with placeholdered tokens (<formula_N>)."""
    if not text:
        return text, {}

    placeholders: Dict[str, str] = {}
    counter = 0

    def _repl(match: re.Match) -> str:
        nonlocal counter
        matched_str = match.group(0)
        # Avoid placeholdering simple single digits
        if matched_str.strip().isdigit() and len(matched_str.strip()) <= 2:
            return matched_str
        token = f"<formula_{counter}>"
        counter += 1
        placeholders[token] = matched_str
        return token

    protected_text = text
    for pat in FORMULA_PATTERNS:
        protected_text = pat.sub(_repl, protected_text)

    return protected_text, placeholders


def restore_formulas(text: str, placeholders: Dict[str, str]) -> str:
    """Restores placeholdered formula tokens back to their original values."""
    if not text or not placeholders:
        return text
    restored = text
    for token, original in placeholders.items():
        restored = restored.replace(token, original)
    return restored


class BaseTranslationProvider(abc.ABC):
    """Abstract interface for AIWF translation providers."""

    @abc.abstractmethod
    def translate_blocks(
        self,
        blocks: List[Dict[str, Any]],
        source_lang: str,
        target_lang: str,
    ) -> List[Dict[str, Any]]:
        """Translates a list of document blocks from source_lang to target_lang."""
        pass


class CachedProvider(BaseTranslationProvider):
    """Loads translations from an existing merged_ejv.json or precomputed cache."""

    def __init__(self, cache_file: Path | str):
        self.cache_file = Path(cache_file)
        self.cache_blocks: List[Dict[str, Any]] = []
        if self.cache_file.is_file():
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self.cache_blocks = json.load(f)

    def translate_blocks(
        self,
        blocks: List[Dict[str, Any]],
        source_lang: str,
        target_lang: str,
    ) -> List[Dict[str, Any]]:
        tgt_key = "vn" if target_lang in ("vi", "vn") else target_lang.lower()
        src_key = "ja" if source_lang in ("ja", "jp") else source_lang.lower()

        # Build lookup map from cache
        lookup: Dict[str, str] = {}
        for b in self.cache_blocks:
            src = b.get(src_key) or b.get("text")
            tgt = b.get(tgt_key) or b.get("vn") or b.get("vi") or b.get("text_vn")
            if src and tgt and isinstance(src, str) and isinstance(tgt, str):
                lookup[src.strip().lower()] = tgt

        results = []
        for b in blocks:
            b_copy = dict(b)
            src_text = b.get("text") or b.get(src_key) or ""
            if src_text and isinstance(src_text, str):
                norm = src_text.strip().lower()
                if norm in lookup:
                    b_copy[tgt_key] = lookup[norm]
            results.append(b_copy)
        return results


class OllamaProvider(BaseTranslationProvider):
    """Translates blocks using a local Ollama model instance (e.g. qwen2.5, llama3.2)."""

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: str = "http://localhost:11434/v1",
        timeout: float = 60.0,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Sends a single prompt to local Ollama API."""
        import urllib.request
        import json

        lang_names = {
            "ja": "Japanese",
            "en": "English",
            "vi": "Vietnamese",
            "vn": "Vietnamese",
        }
        s_name = lang_names.get(source_lang.lower(), source_lang)
        t_name = lang_names.get(target_lang.lower(), target_lang)

        prompt = (
            f"You are a professional document translator. Translate the following {s_name} text into {t_name}.\n"
            f"Rules:\n"
            f"1. Preserve exact meaning, numbers, and technical terms.\n"
            f"2. Keep any placeholders like <formula_0>, <formula_1> unchanged.\n"
            f"3. Return ONLY the translated text without explanations or quotation marks.\n\n"
            f"Text to translate:\n{text}"
        )

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()

    def translate_blocks(
        self,
        blocks: List[Dict[str, Any]],
        source_lang: str,
        target_lang: str,
    ) -> List[Dict[str, Any]]:
        tgt_key = "vn" if target_lang in ("vi", "vn") else target_lang.lower()
        src_key = "ja" if source_lang in ("ja", "jp") else source_lang.lower()

        results = []
        for i, b in enumerate(blocks):
            b_copy = dict(b)
            if b.get("type") in ("h1", "h2", "h3", "p", "blockquote"):
                raw_text = b.get("text") or b.get(src_key) or ""
                if raw_text:
                    protected, tokens = protect_formulas(raw_text)
                    translated = self.translate_text(protected, source_lang, target_lang)
                    restored = restore_formulas(translated, tokens)
                    b_copy[tgt_key] = restored
            elif b.get("type") == "ul" and isinstance(b.get("items"), list):
                translated_items = []
                for it in b["items"]:
                    p_it, tokens = protect_formulas(str(it))
                    t_it = self.translate_text(p_it, source_lang, target_lang)
                    translated_items.append(restore_formulas(t_it, tokens))
                b_copy[tgt_key] = translated_items
            elif b.get("type") == "table":
                headers = b.get("headers", [])
                rows = b.get("rows", [])
                t_headers = [self.translate_text(str(h), source_lang, target_lang) if str(h).strip() else "" for h in headers]
                t_rows = []
                for row in rows:
                    t_row = [self.translate_text(str(c), source_lang, target_lang) if str(c).strip() else "" for c in row]
                    t_rows.append(t_row)
                if not isinstance(b_copy.get("headers"), dict):
                    b_copy["headers"] = {src_key: headers, tgt_key: t_headers}
                else:
                    b_copy["headers"][tgt_key] = t_headers
                if not isinstance(b_copy.get("rows"), dict):
                    b_copy["rows"] = {src_key: rows, tgt_key: t_rows}
                else:
                    b_copy["rows"][tgt_key] = t_rows
            results.append(b_copy)
        return results


def get_provider(
    provider_name: str = "agent",
    cache_path: Optional[Path | str] = None,
    ollama_model: str = "qwen2.5:7b",
) -> BaseTranslationProvider:
    """Factory function to resolve translation provider."""
    name = provider_name.lower().strip()
    if name == "cached" and cache_path:
        return CachedProvider(cache_path)
    elif name == "ollama":
        return OllamaProvider(model=ollama_model)
    elif name in ("agent", "ide"):
        # Agent batch workflow uses file-based checkpoints
        if cache_path and Path(cache_path).is_file():
            return CachedProvider(cache_path)
        raise NotImplementedError(
            "AgentBatchProvider operates via batch_XXX_source.json files. "
            "Use chunk_manager.py and auto_translate.py for the IDE Agent workflow."
        )
    else:
        raise ValueError(f"Unknown translation provider '{provider_name}'. Choose 'agent', 'ollama', or 'cached'.")
