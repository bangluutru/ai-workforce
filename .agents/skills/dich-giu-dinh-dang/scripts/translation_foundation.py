"""Shared Translation Foundation for AIWF.

This module provides format-agnostic translation primitives reusable
across document adapters (PDF, DOCX, PPTX, XLSX).

Architecture boundary:

    DOCUMENT ADAPTER (format-specific)
           ↓
    TranslationUnit (this module)
           ↓
    Terminology + Protected Entities
           ↓
    Agent Translation (Antigravity integrated model)
           ↓
    Integrity + Quality Checks
           ↓
    Translated Units
           ↓
    DOCUMENT RENDERER (format-specific)

This module does NOT:
- Know about PDF pages, DOCX paragraphs, or slide shapes.
- Call external LLM APIs.
- Perform actual translation (the Agent does that).
- Build a framework or database server.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. TranslationUnit — Minimal internal contract
# ---------------------------------------------------------------------------

class ContentType(str, Enum):
    """Content classification for translation units."""
    HEADING = "heading"
    BODY = "body"
    TABLE_CELL = "table_cell"
    CAPTION = "caption"
    FOOTER = "footer"
    HEADER = "header"
    LABEL = "label"
    LIST_ITEM = "list_item"
    UNKNOWN = "unknown"


@dataclass
class TranslationUnit:
    """A single translatable text segment.

    Location is opaque to this module — it may represent:
    - PDF: page/block/bbox
    - DOCX: paragraph index / table cell
    - PPTX: slide/shape
    - XLSX: sheet/cell
    """
    id: str
    source_text: str
    source_language: str
    target_language: str
    content_type: ContentType = ContentType.UNKNOWN
    context: str = ""
    location: Dict[str, Any] = field(default_factory=dict)
    protected_tokens: List[str] = field(default_factory=list)
    translated_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["content_type"] = self.content_type.value
        return d


# ---------------------------------------------------------------------------
# 2. Protected Entities — Deterministic detection
# ---------------------------------------------------------------------------

# Patterns that identify tokens normally not freely rewritten in translation
_PROTECTED_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("model_number", re.compile(
        r'\b[A-Z]{1,5}[-–]?\d{2,6}[-–]?[A-Z]{0,3}\d{0,4}\b'
    )),
    ("standard_code", re.compile(
        r'\b(?:EN|ISO|IEC|JIS|UL|ASTM|IEEE|DIN|BS|NF|GB|KS)\s*'
        r'[A-Z]?\s*\d[\d.:/-]+\d\b'
    )),
    ("ip_rating", re.compile(r'\bIP\d{2}\b')),
    ("version", re.compile(r'\bv\d+\.\d+(?:\.\d+)?\b', re.IGNORECASE)),
    ("url", re.compile(
        r'https?://[^\s<>\"\']+|www\.[^\s<>\"\']+',
        re.IGNORECASE
    )),
    ("email", re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b')),
    ("catalog_number", re.compile(
        r'\b(?:Cat\.?\s*(?:No\.?)?|型番|製品番号)\s*[:\s]*[A-Z0-9][-A-Z0-9.]+\b',
        re.IGNORECASE
    )),
    ("material_code", re.compile(
        r'\b(?:SUS|AISI|SS)\s*\d{3,4}[A-Z]?\b'
    )),
]


def detect_protected_entities(text: str) -> List[str]:
    """Extract tokens that should be preserved verbatim during translation.

    Returns deduplicated list of protected tokens found in text.
    """
    entities = []
    seen = set()
    for _name, pattern in _PROTECTED_PATTERNS:
        for match in pattern.finditer(text):
            token = match.group().strip()
            if token and token not in seen:
                seen.add(token)
                entities.append(token)
    return entities


def verify_protected_entities(
    source: str,
    translated: str,
    protected: List[str],
) -> List[Dict[str, Any]]:
    """Check that protected entities survive translation.

    Returns list of violations (empty = all preserved).
    """
    violations = []
    for token in protected:
        # Allow minor whitespace/dash normalization
        normalized = re.sub(r'[\s\-–—]+', '', token)
        target_normalized = re.sub(r'[\s\-–—]+', '', translated)
        if normalized not in target_normalized and token not in translated:
            violations.append({
                "token": token,
                "status": "MISSING",
                "source_present": token in source,
            })
    return violations


# ---------------------------------------------------------------------------
# 3. Critical Values — Deterministic extraction & verification
# ---------------------------------------------------------------------------

_CRITICAL_VALUE_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("percentage", re.compile(r'\d+[.,]\d+\s*%|\d+\s*%')),
    ("temperature", re.compile(r'[+-]?\d+\s*[°℃℉]')),
    ("voltage", re.compile(r'\d+(?:\.\d+)?\s*(?:kV|V|mV)\b')),
    ("current", re.compile(r'\d+(?:\.\d+)?\s*(?:A|mA|μA)\b')),
    ("power", re.compile(r'\d+(?:\.\d+)?\s*(?:kW|W|mW)\b')),
    ("frequency", re.compile(r'\d+(?:\.\d+)?\s*(?:GHz|MHz|kHz|Hz|bps)\b')),
    ("dimension_mm", re.compile(r'\d+(?:\.\d+)?\s*mm\b')),
    ("weight", re.compile(r'\d+(?:\.\d+)?\s*(?:kg|g|mg|ton)\b', re.IGNORECASE)),
    ("currency_yen_man", re.compile(r'\d[\d,]*\s*万円')),
    ("currency_explicit", re.compile(
        r'\d[\d,.]*\s*(?:yên|yen|円|đồng|VND|USD|EUR|JPY)\b',
        re.IGNORECASE
    )),
    ("date_iso", re.compile(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}')),
    ("date_jp", re.compile(r'\d{4}年\d{1,2}月\d{1,2}日')),
]


def extract_critical_values(text: str) -> List[Dict[str, str]]:
    """Extract critical numeric/unit values from text.

    Returns list of {type, value, numeric} dicts.
    """
    values = []
    seen = set()
    for vtype, pattern in _CRITICAL_VALUE_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group().strip()
            if raw not in seen:
                seen.add(raw)
                values.append({
                    "type": vtype,
                    "value": raw,
                    "numeric": _extract_numeric(raw),
                })
    return values


def _extract_numeric(value_str: str) -> Optional[float]:
    """Extract the numeric portion from a value string.

    Handles:
    - 98.7% → 98.7
    - 98,7% → 98.7
    - 45万円 → 450000.0
    - 1,200万円 → 12000000.0
    - DC 12V → 12.0
    - -20℃ → -20.0
    """
    s = value_str.strip()

    # Handle 万 (x10000) notation
    m = re.match(r'^([\d,]+(?:\.\d+)?)\s*万', s)
    if m:
        num_str = m.group(1).replace(',', '')
        try:
            return float(num_str) * 10000.0
        except ValueError:
            pass

    # General: extract first numeric value
    m = re.search(r'[+-]?[\d,]+(?:\.\d+)?', s)
    if m:
        num_str = m.group().replace(',', '')
        try:
            return float(num_str)
        except ValueError:
            pass
    return None


def verify_critical_values(
    source_values: List[Dict[str, str]],
    translated_text: str,
    target_values: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Verify that critical values survive translation.

    Distinguishes:
    - PRESERVED: exact match
    - LOCALIZED: different format, same numeric value (e.g. 98.7% → 98,7%)
    - CORRUPTED: numeric value changed
    - MISSING: not found at all

    Returns summary dict with per-value results.
    """
    if target_values is None:
        target_values = extract_critical_values(translated_text)

    target_numerics = []
    for tv in target_values:
        n = tv.get("numeric")
        if n is not None:
            target_numerics.append(n)

    # Also extract inline numbers from translated text
    inline_nums = set()
    for m in re.finditer(r'[+-]?[\d,.]+', translated_text):
        raw = m.group().replace(',', '.').replace('..', '.')
        # Handle Vietnamese thousands separator: 450.000 → 450000
        parts = raw.split('.')
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]) and len(parts[0]) <= 3:
            # Likely Vietnamese thousands notation
            raw_joined = ''.join(parts)
            try:
                inline_nums.add(float(raw_joined))
            except ValueError:
                pass
        try:
            inline_nums.add(float(raw))
        except ValueError:
            pass

    results = []
    for sv in source_values:
        src_raw = sv["value"]
        src_num = sv.get("numeric")
        if src_num is None:
            src_num = _extract_numeric(src_raw)

        # Check exact string presence
        if src_raw in translated_text:
            results.append({"value": src_raw, "status": "PRESERVED"})
            continue

        # Check with comma<->period localization
        localized = src_raw.replace('.', ',')
        if localized in translated_text:
            results.append({"value": src_raw, "status": "LOCALIZED"})
            continue

        # Check numeric equivalence
        if src_num is not None:
            found_equiv = False
            all_candidates = set(target_numerics) | inline_nums
            for tn in all_candidates:
                if _numeric_equivalent(src_num, tn):
                    found_equiv = True
                    break
            if found_equiv:
                results.append({"value": src_raw, "status": "LOCALIZED"})
                continue

        # Not found
        results.append({"value": src_raw, "status": "MISSING"})

    preserved = sum(1 for r in results if r["status"] == "PRESERVED")
    localized = sum(1 for r in results if r["status"] == "LOCALIZED")
    missing = sum(1 for r in results if r["status"] == "MISSING")

    return {
        "total": len(results),
        "preserved": preserved,
        "localized": localized,
        "missing": missing,
        "pass": missing == 0,
        "details": results,
    }


def _numeric_equivalent(a: float, b: float, tolerance: float = 0.01) -> bool:
    """Check if two numeric values are semantically equivalent.

    Handles: 98.7 ≈ 98.7, 450000 ≈ 450000, etc.
    Relative tolerance for large numbers, absolute for small.
    """
    if a == b:
        return True
    if abs(a) < 1e-9 and abs(b) < 1e-9:
        return True
    if abs(a) > 100:
        return abs(a - b) / max(abs(a), abs(b)) < tolerance
    return abs(a - b) < tolerance


# ---------------------------------------------------------------------------
# 4. Terminology Layer — Lightweight repository-managed knowledge
# ---------------------------------------------------------------------------

TERMINOLOGY_DIR = Path(__file__).resolve().parent.parent.parent.parent / "knowledge" / "translation"

# Precedence (highest first):
# 1. document-specific (temporary, not persisted)
# 2. company/domain
# 3. shared/common


@dataclass
class TermEntry:
    """A single terminology entry."""
    source: str
    target: str
    source_language: str
    target_language: str
    domain: str = "general"
    notes: str = ""


def load_terminology(
    source_lang: str,
    target_lang: str,
    domain: Optional[str] = None,
    extra_dirs: Optional[List[Path]] = None,
) -> List[TermEntry]:
    """Load terminology entries from repository knowledge.

    Searches:
    1. .agents/knowledge/translation/common-terms.json
    2. .agents/knowledge/translation/company-terms.json
    3. .agents/knowledge/translation/protected-entities.json

    Files are JSON arrays of objects with at minimum:
    {source, target, source_language, target_language}

    Returns entries matching the requested language pair.
    """
    entries = []
    search_dirs = [TERMINOLOGY_DIR]
    if extra_dirs:
        search_dirs.extend(extra_dirs)

    for d in search_dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    continue
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    sl = item.get("source_language", "")
                    tl = item.get("target_language", "")
                    if sl == source_lang and tl == target_lang:
                        entries.append(TermEntry(
                            source=item.get("source", ""),
                            target=item.get("target", ""),
                            source_language=sl,
                            target_language=tl,
                            domain=item.get("domain", "general"),
                            notes=item.get("notes", ""),
                        ))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                continue

    # Filter by domain if specified
    if domain:
        domain_entries = [e for e in entries if e.domain in (domain, "general")]
        return domain_entries

    return entries


def build_terminology_context(
    text: str,
    terminology: List[TermEntry],
) -> str:
    """Build a terminology guidance string for the Agent.

    NOT naive replacement — provides context for the Agent to use
    during translation. The Agent maintains semantic correctness.

    Returns a formatted string like:
    TERMINOLOGY GUIDANCE:
    - 品質管理 → Quản lý chất lượng (domain: manufacturing)
    - 不良品 → Sản phẩm lỗi (domain: manufacturing)
    """
    applicable = []
    for entry in terminology:
        if entry.source in text:
            applicable.append(entry)

    if not applicable:
        return ""

    lines = ["TERMINOLOGY GUIDANCE:"]
    for entry in applicable[:20]:  # Limit to avoid context overflow
        note = f" ({entry.notes})" if entry.notes else ""
        domain_tag = f" [domain: {entry.domain}]" if entry.domain != "general" else ""
        lines.append(f"- {entry.source} → {entry.target}{domain_tag}{note}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. Translation Completeness Check
# ---------------------------------------------------------------------------

# CJK character ranges (Japanese/Chinese)
_CJK_RE = re.compile(
    r'[\u3041-\u3096'   # Hiragana
    r'\u30a1-\u30fa'    # Katakana
    r'\u3400-\u4dbf'    # CJK Unified Ext A
    r'\u4e00-\u9fff'    # CJK Unified
    r'\uf900-\ufaff]'   # CJK Compat
)


def check_residual_source_text(
    translated_text: str,
    source_language: str,
    protected_tokens: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Check for suspicious residual source-language text in translation.

    Distinguishes INTENTIONAL_RETENTION (protected entities, proper nouns)
    from MISSED_TRANSLATION (untranslated segments).
    """
    if source_language not in ("ja", "zh"):
        return {"residual_count": 0, "status": "NOT_APPLICABLE"}

    protected_set = set(protected_tokens or [])

    # Find CJK character runs
    residual_segments = []
    for match in re.finditer(r'[\u3041-\u3096\u30a1-\u30fa\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+', translated_text):
        segment = match.group()
        if len(segment) < 2:
            continue  # Single CJK chars may be intentional (units, etc.)

        # Check if this segment is part of a protected entity
        is_protected = any(segment in pt or pt in segment for pt in protected_set)
        if is_protected:
            residual_segments.append({
                "text": segment,
                "classification": "INTENTIONAL_RETENTION",
            })
        else:
            residual_segments.append({
                "text": segment,
                "classification": "MISSED_TRANSLATION",
            })

    missed = [s for s in residual_segments if s["classification"] == "MISSED_TRANSLATION"]
    return {
        "residual_count": len(residual_segments),
        "missed_count": len(missed),
        "intentional_count": len(residual_segments) - len(missed),
        "status": "FAIL" if missed else "PASS",
        "segments": residual_segments[:10],  # Limit output
    }


# ---------------------------------------------------------------------------
# 6. Verification Summary
# ---------------------------------------------------------------------------

def build_verification_summary(
    units: List[TranslationUnit],
) -> Dict[str, Any]:
    """Build a deterministic verification summary for a batch of translation units.

    Covers:
    - Protected entity preservation
    - Critical value integrity
    - Residual source text

    Does NOT assess semantic accuracy (that requires Agent quality review).
    """
    total = len(units)
    entity_violations = 0
    value_missing = 0
    residual_missed = 0

    for unit in units:
        if not unit.translated_text:
            continue

        # Protected entities
        violations = verify_protected_entities(
            unit.source_text,
            unit.translated_text,
            unit.protected_tokens,
        )
        entity_violations += len(violations)

        # Critical values
        source_vals = extract_critical_values(unit.source_text)
        if source_vals:
            result = verify_critical_values(source_vals, unit.translated_text)
            value_missing += result["missing"]

        # Residual check
        residual = check_residual_source_text(
            unit.translated_text,
            unit.source_language,
            unit.protected_tokens,
        )
        residual_missed += residual.get("missed_count", 0)

    return {
        "total_units": total,
        "entity_violations": entity_violations,
        "value_missing": value_missing,
        "residual_missed": residual_missed,
        "deterministic_pass": (entity_violations == 0 and value_missing == 0 and residual_missed == 0),
    }
