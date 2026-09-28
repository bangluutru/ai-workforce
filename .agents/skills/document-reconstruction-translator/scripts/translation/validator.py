"""Pre-Reconstruction Translation Integrity Validator.

Conforms to Section 7 of AIWF Document Reconstruction Directive:
- Audits translated units before reconstruction begins:
  * Missing translations
  * Empty translations
  * Protected entity corruption (model numbers, codes, URLs, ratings)
  * Numeric corruption (percentages, temperatures, voltages, currencies)
  * Unit corruption (e.g., V -> W, kg -> g)
  * Identifier corruption
  * Suspicious untranslated residual (CJK characters left in target text)
  * Duplicated translation
- Never lets reconstruction conceal translation failure.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

import sys
from pathlib import Path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ir.models import DocumentIR, SemanticObject
from translation_foundation import (
    TranslationUnit,
    check_residual_source_text,
    detect_protected_entities,
    extract_critical_values,
    verify_critical_values,
    verify_protected_entities,
)


class TranslationValidator:
    """Validates translated units and document IR for semantic and data fidelity."""

    def validate_translations(
        self,
        units: List[TranslationUnit],
        ir: DocumentIR,
    ) -> Dict[str, Any]:
        """Runs complete pre-reconstruction validation on all translated units."""
        missing: List[Dict[str, Any]] = []
        empty: List[Dict[str, Any]] = []
        entity_violations: List[Dict[str, Any]] = []
        numeric_violations: List[Dict[str, Any]] = []
        unit_violations: List[Dict[str, Any]] = []
        residual_violations: List[Dict[str, Any]] = []
        duplicates: List[Dict[str, Any]] = []

        seen_translations: Dict[str, List[str]] = {}

        for u in units:
            src = u.source_text.strip()
            trans = u.translated_text.strip()

            # 1. Missing or Empty Check
            if not u.translated_text:
                missing.append({"id": u.id, "source": src[:50]})
                continue
            if not trans:
                empty.append({"id": u.id, "source": src[:50]})
                continue

            # 2. Protected Entities Preservation
            if u.protected_tokens:
                violations = verify_protected_entities(src, trans, u.protected_tokens)
                if violations:
                    entity_violations.append({
                        "id": u.id,
                        "violations": violations,
                    })

            # 3. Numeric & Critical Values Integrity
            src_vals = extract_critical_values(src)
            if src_vals:
                num_res = verify_critical_values(src_vals, trans)
                if not num_res["pass"]:
                    for d in num_res["details"]:
                        if d["status"] == "CORRUPTED":
                            if "unit_mismatch" in d.get("reason", ""):
                                unit_violations.append({"id": u.id, "detail": d})
                            else:
                                numeric_violations.append({"id": u.id, "detail": d})
                        elif d["status"] == "MISSING":
                            numeric_violations.append({"id": u.id, "detail": d})

            # 4. Residual Source Text (e.g. leftover CJK in ja -> vi translation)
            if u.source_language in ("ja", "zh"):
                res_check = check_residual_source_text(trans, u.source_language, u.protected_tokens)
                if res_check["missed_count"] > 0:
                    residual_violations.append({
                        "id": u.id,
                        "missed_count": res_check["missed_count"],
                        "segments": res_check["segments"],
                    })

            # 5. Duplicated Translation detection (accidental copy-paste)
            if len(trans) > 30:
                if trans not in seen_translations:
                    seen_translations[trans] = []
                seen_translations[trans].append(u.id)

        for trans_text, ids in seen_translations.items():
            if len(ids) > 1:
                # Check if sources were actually different
                sources = {u.source_text for u in units if u.id in ids}
                if len(sources) > 1:
                    duplicates.append({
                        "translated_text": trans_text[:60] + "...",
                        "unit_ids": ids,
                        "distinct_sources": len(sources),
                    })

        total = len(units)
        is_passed = (
            len(missing) == 0
            and len(empty) == 0
            and len(entity_violations) == 0
            and len(numeric_violations) == 0
            and len(unit_violations) == 0
            and len(residual_violations) == 0
        )

        return {
            "total_units": total,
            "passed": is_passed,
            "metrics": {
                "missing_count": len(missing),
                "empty_count": len(empty),
                "entity_violations_count": len(entity_violations),
                "numeric_violations_count": len(numeric_violations),
                "unit_violations_count": len(unit_violations),
                "residual_violations_count": len(residual_violations),
                "duplicates_count": len(duplicates),
            },
            "details": {
                "missing": missing,
                "empty": empty,
                "entity_violations": entity_violations,
                "numeric_violations": numeric_violations,
                "unit_violations": unit_violations,
                "residual_violations": residual_violations,
                "duplicates": duplicates,
            },
        }
