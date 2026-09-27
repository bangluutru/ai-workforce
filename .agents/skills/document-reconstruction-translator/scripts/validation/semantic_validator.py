"""Semantic Validation Engine.

Conforms to Section 27 of AIWF Document Reconstruction Translator:
- Full Accounting: Every semantic object in Source IR must be accounted for in Target IR.
- Zero Omission: Verifies that translatable content has been fully translated.
- Duplication Guard: Detects accidental repetitions or phantom elements.
- Placeholder Ban: Catches dot placeholders (.), empty stubs, or TODOs.
- Zero Residual Source Text: Scans for untranslated source scripts (CJK / foreign residual).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ir.models import DocumentIR, SemanticObject, SemanticObjectType


class SemanticValidator:
    """Verifies that all source content and structure are faithfully preserved in target."""

    CJK_REGEX = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]{2,}")

    def validate_document(self, ir: DocumentIR) -> Dict[str, Any]:
        violations: List[Dict[str, Any]] = []
        translated_texts = []

        total_translatable = 0
        translated_count = 0

        for obj in ir.objects:
            if obj.is_text_like():
                total_translatable += 1
                src = obj.get_text_content(prefer_translated=False).strip()
                tgt = obj.get_text_content(prefer_translated=True).strip()

                # 1. Check for missing / omitted translations
                if not tgt:
                    violations.append({
                        "object_id": obj.id,
                        "type": "OMITTED_CONTENT",
                        "description": f"Object {obj.id} has empty translated content",
                        "severity": "CRITICAL",
                    })
                    continue

                translated_count += 1

                # 2. Check for Placeholder Ban (.)
                if tgt in (".", "-", "--", "...", "N/A", "TODO"):
                    violations.append({
                        "object_id": obj.id,
                        "type": "PLACEHOLDER_DETECTED",
                        "description": f"Object {obj.id} contains forbidden placeholder: '{tgt}'",
                        "severity": "CRITICAL",
                    })

                # 3. Check for Untranslated CJK Residuals (if translating from JA/ZH to VI/EN)
                if ir.target_language in ("vi", "en"):
                    residuals = self.CJK_REGEX.findall(tgt)
                    if residuals:
                        violations.append({
                            "object_id": obj.id,
                            "type": "SOURCE_SCRIPT_RESIDUAL",
                            "description": f"Untranslated CJK characters found: {residuals}",
                            "severity": "CRITICAL",
                        })

                # 4. Check for Duplicate Content
                if len(tgt) > 40:
                    if tgt in translated_texts:
                        violations.append({
                            "object_id": obj.id,
                            "type": "DUPLICATE_CONTENT",
                            "description": f"Duplicate paragraph content detected in {obj.id}",
                            "severity": "MEDIUM",
                        })
                    else:
                        translated_texts.append(tgt)

        # 5. Check Table and Visual Accounting
        visual_objects = ir.get_objects_by_type(SemanticObjectType.TABLE) + \
                         ir.get_objects_by_type(SemanticObjectType.PHOTO) + \
                         ir.get_objects_by_type(SemanticObjectType.CHART) + \
                         ir.get_objects_by_type(SemanticObjectType.DIAGRAM)

        for vis in visual_objects:
            if not vis.reconstruction_strategy:
                violations.append({
                    "object_id": vis.id,
                    "type": "UNASSIGNED_RECONSTRUCTION_STRATEGY",
                    "description": f"Visual object {vis.id} has no reconstruction strategy",
                    "severity": "HIGH",
                })

        passed = len([v for v in violations if v["severity"] == "CRITICAL"]) == 0

        return {
            "passed": passed,
            "total_objects": len(ir.objects),
            "translatable_objects": total_translatable,
            "translated_objects": translated_count,
            "coverage_rate": round(translated_count / max(1, total_translatable), 3),
            "violations_count": len(violations),
            "violations": violations,
        }
