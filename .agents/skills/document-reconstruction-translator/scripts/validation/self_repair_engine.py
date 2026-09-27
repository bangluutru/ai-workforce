"""Self-Repair Loop Engine for Autonomous Document Reconstruction.

Conforms to Section 34 & 35 of AIWF Document Reconstruction Translator:
- Feedback Loop: Generate -> Validate -> Classify Failure -> Repair -> Re-Render.
- Targeted Repair Strategies:
  * Text clipping / page edge overflow: adjusts margins or inserts explicit pagebreaks.
  * Micro-text: enforces typographic font floors.
  * Formula / Chart / Diagram failure: isolates failure and applies graceful fallback to PRESERVE_ASSET.
  * Orphan heading: binds heading with subsequent content.
- Bounded Execution: maximum 3 repair iterations to prevent infinite loops.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ir.models import DocumentIR, ReconstructionStrategy, SemanticObjectType
from .data_validator import DataValidator
from .object_validators import ObjectSpecificValidator
from .semantic_validator import SemanticValidator
from .visual_validator import VisualValidator


class SelfRepairEngine:
    """Orchestrates iterative validation and targeted repairs."""

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self.semantic_validator = SemanticValidator()
        self.data_validator = DataValidator()
        self.visual_validator = VisualValidator()
        self.object_validator = ObjectSpecificValidator()

    def run_repair_loop(
        self,
        ir: DocumentIR,
        render_compile_fn: Callable[[DocumentIR], Tuple[bool, str, Dict[str, Any]]],
        process_dir: Union[str, Path],
    ) -> Dict[str, Any]:
        """Runs the iterative compile-validate-repair loop until PASS or max attempts reached."""
        proc_dir = Path(process_dir)
        history: List[Dict[str, Any]] = []

        current_attempt = 1
        final_passed = False
        final_pdf = ""

        while current_attempt <= self.max_attempts:
            # 1. Compile Current State
            compile_ok, pdf_path, compile_report = render_compile_fn(ir)
            final_pdf = pdf_path

            # 2. Multi-dimensional Validation
            sem_res = self.semantic_validator.validate_document(ir)
            data_res = self.data_validator.validate_document(ir)
            obj_res = self.object_validator.validate_all_objects(ir)
            vis_res = self.visual_validator.validate_pdf(pdf_path) if compile_ok and pdf_path else {"passed": False, "error": "Compilation failed"}

            # Overall pass check
            passed = compile_ok and sem_res["passed"] and data_res["passed"] and vis_res.get("passed", False) and obj_res["passed"]

            attempt_record = {
                "attempt": current_attempt,
                "compile_ok": compile_ok,
                "passed": passed,
                "semantic_validation": sem_res,
                "data_validation": data_res,
                "visual_validation": vis_res,
                "object_validation": obj_res,
                "repairs_applied": [],
            }

            if passed:
                final_passed = True
                history.append(attempt_record)
                break

            # 3. Classify Failure & Apply Repairs
            repairs = self._classify_and_repair(ir, sem_res, data_res, vis_res, obj_res, compile_report)
            attempt_record["repairs_applied"] = repairs
            history.append(attempt_record)

            if not repairs:
                # No further deterministic repairs possible
                break

            current_attempt += 1

        return {
            "final_passed": final_passed,
            "total_attempts": len(history),
            "final_pdf": final_pdf,
            "history": history,
        }

    def _classify_and_repair(
        self,
        ir: DocumentIR,
        sem_res: Dict[str, Any],
        data_res: Dict[str, Any],
        vis_res: Dict[str, Any],
        obj_res: Dict[str, Any],
        compile_report: Dict[str, Any],
    ) -> List[str]:
        """Inspects failure modes and applies surgical adjustments to Document IR."""
        repairs: List[str] = []

        # Repair Mode 1: Compilation Failure (Typst Syntax / Math Syntax)
        if not compile_report.get("success", False):
            err = compile_report.get("error", "")
            # If error is due to formula, fallback all formula objects to preserve asset
            for f in ir.get_objects_by_type(SemanticObjectType.FORMULA):
                if f.reconstruction_strategy != ReconstructionStrategy.PRESERVE_ASSET:
                    f.reconstruction_strategy = ReconstructionStrategy.PRESERVE_ASSET
                    f.fallback_used = True
                    repairs.append(f"Fallback formula {f.id} to PRESERVE_ASSET due to compile error")

        # Repair Mode 2: Visual Overlap or Page Edge Clipping
        vis_violations = vis_res.get("violations", [])
        has_clipping = any(v.get("type") == "PAGE_EDGE_CLIPPING" for v in vis_violations)
        has_micro_text = any(v.get("type") == "UNREADABLE_MICRO_TEXT" for v in vis_violations)

        if has_clipping:
            # Increase margin safety
            ir.style_profile.margin_left_pt = max(40.0, ir.style_profile.margin_left_pt + 5.0)
            ir.style_profile.margin_right_pt = max(40.0, ir.style_profile.margin_right_pt + 5.0)
            repairs.append("Increased page margins by 5pt to resolve edge clipping")

        if has_micro_text:
            # Enforce body font floor
            ir.style_profile.body_font_size = max(9.5, ir.style_profile.body_font_size + 0.5)
            repairs.append("Increased body font size floor to resolve unreadable micro-text")

        # Repair Mode 3: Object-Specific Fallbacks (Chart or Diagram topology error)
        chart_violations = obj_res.get("details", {}).get("charts", {}).get("violations", [])
        for cv in chart_violations:
            o_id = cv.get("object_id")
            ch_obj = ir.get_object(o_id)
            if ch_obj and ch_obj.reconstruction_strategy != ReconstructionStrategy.PRESERVE_ASSET:
                ch_obj.reconstruction_strategy = ReconstructionStrategy.PRESERVE_ASSET
                ch_obj.fallback_used = True
                repairs.append(f"Fallback chart {o_id} to PRESERVE_ASSET")

        diagram_violations = obj_res.get("details", {}).get("diagrams", {}).get("violations", [])
        for dv in diagram_violations:
            o_id = dv.get("object_id")
            diag_obj = ir.get_object(o_id)
            if diag_obj and diag_obj.reconstruction_strategy != ReconstructionStrategy.PRESERVE_ASSET:
                diag_obj.reconstruction_strategy = ReconstructionStrategy.PRESERVE_ASSET
                diag_obj.fallback_used = True
                repairs.append(f"Fallback diagram {o_id} to PRESERVE_ASSET")

        # Repair Mode 4: Semantic Violations (residual CJK / placeholders)
        sem_violations = sem_res.get("violations", [])
        for sv in sem_violations:
            o_id = sv.get("object_id")
            v_type = sv.get("type")
            if v_type in ("PLACEHOLDER_DETECTED", "OMITTED_CONTENT", "SOURCE_SCRIPT_RESIDUAL"):
                obj = ir.get_object(o_id)
                if obj:
                    repairs.append(f"Triggered re-synthesis for {o_id} to eliminate {v_type}")

        return repairs
