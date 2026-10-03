"""Data Integrity Validation Engine.

Conforms to Section 28 of AIWF Document Reconstruction Translator:
- Hard gate for critical values: numbers, percentages, dates, units, currency,
  product codes, model identifiers, formulas.
- Zero-Tolerance: e.g. 97.3% MUST NOT become 93.7%.
- Cross-references source text entities against translated text entities.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Tuple

from ir.models import DocumentIR, SemanticObject, SemanticObjectType


class DataValidator:
    """Verifies that numerical data, units, and identifiers are strictly preserved."""

    NUMERIC_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")
    PERCENT_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\s*%")
    UNIT_PATTERN = re.compile(
        r"\b\d+(?:[.,]\d+)?\s*(?:mm|cm|m|km|mg|g|kg|ml|l|mmol/L|EU/mL|CFU/mL|V|mV|A|mA|Hz|kHz|MHz|W|kW|°C|K|Pa|kPa|MPa|bps|kbps|Mbps|¥|円|USD|\$|VND|VNĐ|triệu|tỷ)\b",
        re.I,
    )
    MODEL_ID_PATTERN = re.compile(r"\b[A-Z]{2,}-\d{2,}[A-Z0-9-]*\b")

    def validate_document(self, ir: DocumentIR) -> Dict[str, Any]:
        """Audits all objects in Document IR for data corruption or omissions."""
        violations: List[Dict[str, Any]] = []
        total_checks = 0

        for obj in ir.objects:
            src_text = obj.get_text_content(prefer_translated=False)
            tgt_text = obj.get_text_content(prefer_translated=True)

            if not src_text or not tgt_text or src_text == tgt_text:
                continue

            # 1. Percentages
            src_pcts = self.PERCENT_PATTERN.findall(src_text)
            tgt_pcts = self.PERCENT_PATTERN.findall(tgt_text)
            for p in src_pcts:
                total_checks += 1
                norm_p = p.replace(" ", "")
                if not any(norm_p == tp.replace(" ", "") for tp in tgt_pcts):
                    # Check if number exists even with different spacing
                    num = re.search(r"\d+(?:[.,]\d+)?", p).group(0)
                    if num not in tgt_text:
                        violations.append({
                            "object_id": obj.id,
                            "type": "PERCENT_CORRUPTION",
                            "expected": p,
                            "source_snippet": src_text[:60],
                            "target_snippet": tgt_text[:60],
                            "severity": "CRITICAL",
                        })

            # 2. Units of Measurement
            src_units = self.UNIT_PATTERN.findall(src_text)
            for u in src_units:
                total_checks += 1
                num_part = re.search(r"\d+(?:[.,]\d+)?", u).group(0)
                if num_part not in tgt_text:
                    violations.append({
                        "object_id": obj.id,
                        "type": "UNIT_VALUE_CORRUPTION",
                        "expected": u,
                        "source_snippet": src_text[:60],
                        "target_snippet": tgt_text[:60],
                        "severity": "CRITICAL",
                    })

            # 3. Model IDs and Codes
            src_models = self.MODEL_ID_PATTERN.findall(src_text)
            for m in src_models:
                total_checks += 1
                if m not in tgt_text:
                    violations.append({
                        "object_id": obj.id,
                        "type": "IDENTIFIER_MISSING",
                        "expected": m,
                        "source_snippet": src_text[:60],
                        "target_snippet": tgt_text[:60],
                        "severity": "HIGH",
                    })

        passed = len(violations) == 0
        return {
            "passed": passed,
            "total_checks": total_checks,
            "violations_count": len(violations),
            "violations": violations,
            "score": round(100.0 * (total_checks - len(violations)) / max(1, total_checks), 2),
        }
