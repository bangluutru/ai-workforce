"""Unified Document Reconstruction & Translation Pipeline Orchestrator.

Conforms to Sections 4, 34, 36, 46 of AIWF Document Reconstruction Translator:
- Ingests Native or Scanned PDF.
- Performs 3-Level Document Structure Analysis into Document IR.
- Extracts Style Profile and builds Relationship Graph.
- Maps translations with strict data preservation.
- Routes objects to specialized engines with failure isolation.
- Assembles and compiles publication-grade Typst document.
- Executes Multi-Dimensional Validation and Self-Repair Loop.
- Emits complete Review Artifacts without repository bloat.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure skill scripts directory is on sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Isolate package namespaces from old skill collisions
for _pkg in ("analyzer", "render", "layout", "verify", "ir", "validation", "engines"):
    if _pkg in sys.modules:
        _cur_mod = sys.modules[_pkg]
        if not hasattr(_cur_mod, "__file__") or str(SCRIPTS_DIR) not in getattr(_cur_mod, "__file__", ""):
            del sys.modules[_pkg]

import pymupdf

from analyzer.semantic_classifier import SemanticClassifier
from ir.models import DocumentIR, DocumentStyleProfile, ReconstructionStrategy, SemanticObjectType
from render.document_compositor import DocumentCompositor
from validation.data_validator import DataValidator
from validation.object_validators import ObjectSpecificValidator
from validation.self_repair_engine import SelfRepairEngine
from validation.semantic_validator import SemanticValidator
from validation.visual_validator import VisualValidator


class DocumentReconstructionPipeline:
    """End-to-End Orchestrator for Semantic Document Reconstruction with Translation."""

    def __init__(self, typst_bin: Optional[str] = None):
        self.classifier = SemanticClassifier()
        self.compositor = DocumentCompositor(typst_bin=typst_bin)
        self.repair_engine = SelfRepairEngine(max_attempts=3)

    def run(
        self,
        source_pdf: Union[str, Path],
        target_language: str = "vi",
        output_dir: Optional[Union[str, Path]] = None,
        process_dir: Optional[Union[str, Path]] = None,
        translation_map: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Runs the complete reconstruction pipeline."""
        src_path = Path(source_pdf).resolve()
        if not src_path.exists():
            raise FileNotFoundError(f"Source PDF not found: {source_pdf}")

        stem = src_path.stem
        default_out = Path.home() / "Downloads" / "AIWF_Output"
        out_dir = Path(output_dir) if output_dir else default_out
        out_dir.mkdir(parents=True, exist_ok=True)

        proc_dir = Path(process_dir) if process_dir else src_path.parent / "_process" / f"recon_{stem}"
        proc_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = proc_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        validation_dir = proc_dir / "validation"
        validation_dir.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------------------
        # 1. Structure Analysis & Document IR Ingest (Section 4 & 5)
        # ---------------------------------------------------------------------
        ir = self.classifier.analyze_document(
            pdf_path=src_path,
            target_language=target_language,
            extract_assets_dir=assets_dir,
        )

        # Save Initial IR and Style Profile
        ir.save_json(proc_dir / "document-ir.json")
        (proc_dir / "style-profile.json").write_text(
            json.dumps(ir.style_profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # ---------------------------------------------------------------------
        # 2. Apply Translation Layer (if provided)
        # ---------------------------------------------------------------------
        if translation_map:
            self._apply_translation_map(ir, translation_map)
            (proc_dir / "translation-map.json").write_text(
                json.dumps(translation_map, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        # ---------------------------------------------------------------------
        # 3. Composition, Compile, and Self-Repair Loop (Section 20 & 34)
        # ---------------------------------------------------------------------
        target_pdf_path = proc_dir / f"{stem}_reconstructed.pdf"

        def _compile_step(doc_ir: DocumentIR) -> Tuple[bool, str, Dict[str, Any]]:
            res = self.compositor.compose_and_compile(
                ir=doc_ir,
                output_pdf_path=target_pdf_path,
                process_dir=proc_dir,
            )
            return res["success"], res.get("output_pdf", ""), res

        # Execute Self-Repair Loop
        loop_result = self.repair_engine.run_repair_loop(
            ir=ir,
            render_compile_fn=_compile_step,
            process_dir=proc_dir,
        )

        final_compiled_pdf = Path(loop_result["final_pdf"]) if loop_result["final_pdf"] else None

        # ---------------------------------------------------------------------
        # 4. Final Multi-Dimensional Validation Audits & Artifact Export
        # ---------------------------------------------------------------------
        sem_report = self.repair_engine.semantic_validator.validate_document(ir)
        data_report = self.repair_engine.data_validator.validate_document(ir)
        obj_report = self.repair_engine.object_validator.validate_all_objects(ir)
        vis_report = (
            self.repair_engine.visual_validator.validate_pdf(final_compiled_pdf)
            if final_compiled_pdf and final_compiled_pdf.exists()
            else {"passed": False}
        )

        # Save Validation Reports
        (validation_dir / "semantic.json").write_text(
            json.dumps(sem_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (validation_dir / "data-integrity.json").write_text(
            json.dumps(data_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (validation_dir / "visual.json").write_text(
            json.dumps(vis_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (validation_dir / "object-fidelity.json").write_text(
            json.dumps(obj_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # ---------------------------------------------------------------------
        # 5. Delivery to User Output Directory
        # ---------------------------------------------------------------------
        final_delivery_path = out_dir / f"{stem}_translated_reconstructed.pdf"
        if final_compiled_pdf and final_compiled_pdf.exists():
            shutil.copy2(final_compiled_pdf, final_delivery_path)

        # Build Execution Report
        exec_report = {
            "document_id": ir.document_id,
            "source_pdf": str(src_path),
            "target_pdf": str(final_delivery_path) if final_delivery_path.exists() else "",
            "target_language": target_language,
            "total_objects": len(ir.objects),
            "total_pages_reconstructed": vis_report.get("total_pages", 0),
            "self_repair_attempts": loop_result["total_attempts"],
            "validation_results": {
                "semantic": sem_report["passed"],
                "data_integrity": data_report["passed"],
                "visual": vis_report.get("passed", False),
                "objects": obj_report["passed"],
            },
            "overall_status": "PASS" if loop_result["final_passed"] else "NEEDS_REVIEW",
        }

        (proc_dir / "execution-report.json").write_text(
            json.dumps(exec_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return {
            "success": loop_result["final_passed"],
            "final_pdf": str(final_delivery_path) if final_delivery_path.exists() else "",
            "process_dir": str(proc_dir),
            "execution_report": exec_report,
            "document_ir": ir.summary(),
        }

    def _apply_translation_map(self, ir: DocumentIR, t_map: Dict[str, Any]) -> None:
        """Applies external or model translations to the Document IR."""
        for obj in ir.objects:
            if obj.id in t_map:
                obj.translated_content = t_map[obj.id]
            elif obj.is_text_like():
                # If exact ID not in map, check by source text match
                src_txt = obj.get_text_content(prefer_translated=False).strip()
                if src_txt in t_map:
                    obj.translated_content = t_map[src_txt]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AIWF Semantic Document Reconstruction & Translation Pipeline")
    parser.add_argument("--source", required=True, help="Path to source PDF file")
    parser.add_argument("--target-lang", default="vi", help="Target language code (vi, en, ja)")
    parser.add_argument("--output-dir", default=None, help="Output directory for final delivery")
    parser.add_argument("--process-dir", default=None, help="Process directory for intermediate artifacts")
    parser.add_argument("--translation-map", default=None, help="Path to JSON file with translation mappings")
    args = parser.parse_args()

    t_map = None
    if args.translation_map and Path(args.translation_map).exists():
        t_map = json.loads(Path(args.translation_map).read_text(encoding="utf-8"))

    pipeline = DocumentReconstructionPipeline()
    res = pipeline.run(
        source_pdf=args.source,
        target_language=args.target_lang,
        output_dir=args.output_dir,
        process_dir=args.process_dir,
        translation_map=t_map,
    )
    print(json.dumps(res["execution_report"], ensure_ascii=False, indent=2))
    if not res["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
