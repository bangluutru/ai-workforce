"""Unified Document Reconstruction & Translation Pipeline Orchestrator.

Conforms to Sections 3, 4, 5, 6, 7, 20, 21 of AIWF Document Reconstruction Directive:
- Unified End-to-End Pipeline:
  PDF -> Analyze -> Document IR -> Translation Planning -> Translation ->
  Translation Validation -> Reconstruction -> Multi-Dimensional Validation ->
  Self-Repair Loop -> Final PDF Delivery.
- Zero paid API dependency: fully autonomous local translation provider.
- Full support for translation_map as an override / deterministic regression interface.
- Object Reconstruction Metrics reporting for TEXT, TABLE, FORMULA, CHART, DIAGRAM, PHOTO, ILLUSTRATION.
- Confidence distribution reporting: HIGH, MEDIUM, LOW.
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
for _pkg in ("analyzer", "render", "layout", "verify", "ir", "validation", "engines", "translation"):
    if _pkg in sys.modules:
        _cur_mod = sys.modules[_pkg]
        if not hasattr(_cur_mod, "__file__") or str(SCRIPTS_DIR) not in getattr(_cur_mod, "__file__", ""):
            del sys.modules[_pkg]

import pymupdf

from analyzer.semantic_classifier import SemanticClassifier
from ir.models import DocumentIR, DocumentStyleProfile, ReconstructionStrategy, SemanticObject, SemanticObjectType
from render.document_compositor import DocumentCompositor
from translation.planner import TranslationPlanner
from translation.agent_provider import AgentTranslationProvider
from translation.provider import (
    IntegratedTranslationProvider,
    TranslationMapProvider,
    TranslationProvider,
    TranslationResult,
)
from translation.validator import TranslationValidator
from validation.data_validator import DataValidator
from validation.object_validators import ObjectSpecificValidator
from validation.self_repair_engine import SelfRepairEngine
from validation.semantic_validator import SemanticValidator
from validation.visual_validator import VisualValidator


class DocumentReconstructionPipeline:
    """End-to-End Orchestrator for Semantic Document Reconstruction with Autonomous Translation."""

    def __init__(self, typst_bin: Optional[str] = None):
        self.classifier = SemanticClassifier()
        self.compositor = DocumentCompositor(typst_bin=typst_bin)
        self.repair_engine = SelfRepairEngine(max_attempts=3)
        self.translation_validator = TranslationValidator()

    def run(
        self,
        source_pdf: Union[str, Path],
        target_language: str = "vi",
        source_language: str = "ja",
        output_dir: Optional[Union[str, Path]] = None,
        process_dir: Optional[Union[str, Path]] = None,
        translation_map: Optional[Dict[str, Any]] = None,
        translation_provider: Optional[TranslationProvider] = None,
        allow_draft: bool = False,
        preflight: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Runs the complete reconstruction pipeline autonomously.

        `preflight`: kết quả pdf_preflight() do CLI chạy trước (main). Cảnh báo của nó (trang scan, dấu tiếng Việt
        vỡ) được ghi vào preflight.json, execution-report.json và agent-translation-prompt.md. Gọi kiểu thư viện
        (test) không cần truyền — run() không tự chặn tệp."""
        src_path = Path(source_pdf).resolve()
        if not src_path.exists():
            raise FileNotFoundError(f"Source PDF not found: {source_pdf}")

        stem = src_path.stem
        default_out = Path.home() / "Downloads" / "AIWF_Output"
        out_dir = Path(output_dir).resolve() if output_dir else default_out.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        proc_dir = Path(process_dir).resolve() if process_dir else (src_path.parent / "_process" / f"recon_{stem}").resolve()
        proc_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = proc_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        validation_dir = proc_dir / "validation"
        validation_dir.mkdir(parents=True, exist_ok=True)

        pf_extra: Dict[str, Any] = {}
        if preflight is not None:
            (proc_dir / "preflight.json").write_text(json.dumps(preflight, ensure_ascii=False, indent=2), encoding="utf-8")
            pf_extra = {"preflight_warnings": preflight.get("warnings", []),
                        "diacritic_damaged_pages": preflight.get("damaged_pages", [])}

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
        # 2. Translation Planning (Closure #1, Section 3, 4, 5)
        # ---------------------------------------------------------------------
        planner = TranslationPlanner(source_language=source_language, target_language=target_language)
        units = planner.plan_document_translation(ir)

        (proc_dir / "translation-plan.json").write_text(
            json.dumps([u.to_dict() for u in units], ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # ---------------------------------------------------------------------
        # 3. Autonomous Translation Execution (Closure #1, Section 6)
        # ---------------------------------------------------------------------
        if translation_provider:
            provider = translation_provider
        elif translation_map:
            provider = TranslationMapProvider(translation_map)
        elif (proc_dir / "agent-translations.json").exists():
            # Pha 3: agent (LLM trong IDE) đã dịch → dùng bản dịch của agent, bộ nhớ dịch chỉ để lấp chỗ trống
            provider = AgentTranslationProvider(process_dir=proc_dir, fallback_provider=IntegratedTranslationProvider())
        elif not units:
            # 0 đơn vị dịch → không có gì để dịch; tuyệt đối không bảo agent "dịch 0 đơn vị" rồi dựng PDF nguyên gốc.
            msg = ("NO_TRANSLATABLE_TEXT: không trích được đoạn chữ nào từ PDF nguồn (scan/ảnh hoặc lớp chữ rỗng). "
                   "Dùng skill boc-tach-pdf để OCR/bóc tách trước; không giao PDF.")
            print(msg, file=sys.stderr)
            report = {"overall_status": "NO_TRANSLATABLE_TEXT", "units": 0, "message": msg, **pf_extra}
            (proc_dir / "execution-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"success": False, "final_pdf": "", "process_dir": str(proc_dir), "execution_report": report,
                    "object_reconstruction_metrics": {}, "confidence_distribution": {}, "document_ir": ir.summary()}
        else:
            # Pha 1: CHƯA có bản dịch. Trước đây pipeline dùng bộ nhớ dịch/từ điển rồi vẫn xuất
            # "<tên>_translated_reconstructed.pdf" còn nguyên tiếng nguồn. Giờ: ghi plan + prompt cho agent và DỪNG.
            prompt = AgentTranslationProvider.save_plan_for_agent(units, proc_dir, target_language)
            if pf_extra.get("preflight_warnings"):
                with open(prompt, "a", encoding="utf-8") as fh:
                    fh.write("\n\n## ⚠️ CẢNH BÁO TỪ BƯỚC KIỂM TRA TRƯỚC (đọc trước khi dịch)\n"
                             + "".join(f"- {w}\n" for w in pf_extra["preflight_warnings"])
                             + ("- Trang có dấu tiếng Việt vỡ: source_text các unit ở trang đó có thể thiếu/sai dấu — "
                                "đối chiếu ảnh trang hoặc chữ pdfplumber để hiểu đúng nghĩa trước khi dịch.\n"
                                if pf_extra.get("diacritic_damaged_pages") else ""))
            msg = (f"AWAITING_AGENT_TRANSLATION: đọc {prompt}, dịch TOÀN BỘ {len(units)} đơn vị trong "
                   f"{proc_dir / 'translation-plan.json'}, ghi {proc_dir / 'agent-translations.json'} dạng {{\"<id>\": \"<bản dịch>\"}}, rồi chạy lại đúng lệnh này.")
            print(msg)
            report = {"overall_status": "AWAITING_AGENT_TRANSLATION", "units": len(units), "prompt": str(prompt), "message": msg,
                      **pf_extra}
            (proc_dir / "execution-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"success": False, "final_pdf": "", "process_dir": str(proc_dir), "execution_report": report,
                    "object_reconstruction_metrics": {}, "confidence_distribution": {}, "document_ir": ir.summary()}

        translation_result = provider.translate(units)
        planner.apply_translations_to_ir(ir, translation_result.units)

        # If a legacy translation_map was passed, apply direct overrides as well
        if translation_map:
            self._apply_translation_map(ir, translation_map)
            (proc_dir / "translation-map.json").write_text(
                json.dumps(translation_map, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        # ---------------------------------------------------------------------
        # 4. Pre-Reconstruction Translation Validation (Section 7)
        # ---------------------------------------------------------------------
        trans_report = self.translation_validator.validate_translations(translation_result.units, ir)
        (validation_dir / "translation.json").write_text(
            json.dumps(trans_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # ---------------------------------------------------------------------
        # 5. Composition, Compile, and Self-Repair Loop (Section 20 & 34)
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
        # 6. Final Multi-Dimensional Validation Audits & Artifact Export
        # ---------------------------------------------------------------------
        sem_report = self.repair_engine.semantic_validator.validate_document(ir)
        data_report = self.repair_engine.data_validator.validate_document(ir)
        obj_report = self.repair_engine.object_validator.validate_all_objects(ir)
        vis_report = (
            self.repair_engine.visual_validator.validate_pdf(final_compiled_pdf)
            if final_compiled_pdf and final_compiled_pdf.exists()
            else {"passed": False}
        )

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
        # 7. Object Reconstruction Metrics & Confidence Distribution (Section 20, 21)
        # ---------------------------------------------------------------------
        obj_metrics = self._calculate_object_metrics(ir)
        conf_distribution = self._calculate_confidence_distribution(ir)

        # ---------------------------------------------------------------------
        # 8. Delivery to User Output Directory
        # ---------------------------------------------------------------------
        final_delivery_path = out_dir / f"{stem}_translated_reconstructed.pdf"
        if final_delivery_path.exists() and not trans_report["passed"]:
            final_delivery_path.unlink()                     # không để bản cũ đánh lừa
        if final_compiled_pdf and final_compiled_pdf.exists():
            if trans_report["passed"] or allow_draft:
                shutil.copy2(final_compiled_pdf, final_delivery_path)
            else:
                # Còn câu chưa dịch/sai số liệu → KHÔNG giao vào output_dir; bản nháp ở lại process_dir để agent xem
                print(f"⛔ Kiểm định dịch chưa đạt (validation/translation.json) — không giao PDF. Bản nháp: {final_compiled_pdf}")

        exec_report = {
            "document_id": ir.document_id,
            "source_pdf": str(src_path),
            "target_pdf": str(final_delivery_path) if final_delivery_path.exists() else "",
            "target_language": target_language,
            "total_objects": len(ir.objects),
            "total_pages_reconstructed": vis_report.get("total_pages", 0),
            "self_repair_attempts": loop_result["total_attempts"],
            "object_reconstruction_metrics": obj_metrics,
            "confidence_distribution": conf_distribution,
            "validation_results": {
                "translation": trans_report["passed"],
                "semantic": sem_report["passed"],
                "data_integrity": data_report["passed"],
                "visual": vis_report.get("passed", False),
                "objects": obj_report["passed"],
            },
            "overall_status": "PASS" if loop_result["final_passed"] else "NEEDS_REVIEW",
            **pf_extra,
        }

        (proc_dir / "execution-report.json").write_text(
            json.dumps(exec_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Copy required delivery artifacts to output_dir
        if out_dir and final_compiled_pdf and final_compiled_pdf.exists() and (trans_report["passed"] or allow_draft):
            for art_src, art_dst in [
                (proc_dir / "reconstruction-report.json", out_dir / "reconstruction-report.json"),
                (proc_dir / "execution-report.json", out_dir / "validation-report.json"),
                (proc_dir / "source-map.json", out_dir / "source-map.json"),
            ]:
                if art_src.exists():
                    shutil.copy2(art_src, art_dst)

        return {
            "success": loop_result["final_passed"],
            "final_pdf": str(final_delivery_path) if final_delivery_path.exists() else "",
            "process_dir": str(proc_dir),
            "execution_report": exec_report,
            "object_reconstruction_metrics": obj_metrics,
            "confidence_distribution": conf_distribution,
            "document_ir": ir.summary(),
        }

    def _apply_translation_map(self, ir: DocumentIR, t_map: Dict[str, Any]) -> None:
        """Applies external or override translations to the Document IR."""
        for obj in ir.objects:
            if obj.id in t_map:
                obj.translated_content = t_map[obj.id]
            elif obj.is_text_like():
                src_txt = obj.get_text_content(prefer_translated=False).strip()
                if src_txt in t_map:
                    obj.translated_content = t_map[src_txt]

    def _calculate_object_metrics(self, ir: DocumentIR) -> Dict[str, Dict[str, int]]:
        """Calculates reconstruction metrics per object type conforming to Section 20."""
        type_categories = {
            "TEXT": (
                SemanticObjectType.TITLE,
                SemanticObjectType.HEADING,
                SemanticObjectType.PARAGRAPH,
                SemanticObjectType.LIST,
                SemanticObjectType.CAPTION,
                SemanticObjectType.CALLOUT,
                SemanticObjectType.FOOTNOTE,
            ),
            "TABLE": (SemanticObjectType.TABLE,),
            "FORMULA": (SemanticObjectType.FORMULA,),
            "CHART": (SemanticObjectType.CHART,),
            "DIAGRAM": (SemanticObjectType.DIAGRAM,),
            "PHOTO": (SemanticObjectType.PHOTO,),
            "ILLUSTRATION": (SemanticObjectType.ILLUSTRATION, SemanticObjectType.VECTOR_GRAPHIC),
        }

        metrics: Dict[str, Dict[str, int]] = {}
        for cat_name, types in type_categories.items():
            objs = [o for o in ir.objects if o.type in types]
            detected = len(objs)
            translated = 0
            reconstructed = 0
            preserved = 0
            fallback = 0
            failed = 0

            for o in objs:
                # Check translated
                if o.translated_content is not None:
                    translated += 1

                # Check reconstruction / preservation strategy
                if o.fallback_used:
                    fallback += 1
                elif o.reconstruction_strategy in (
                    ReconstructionStrategy.REFLOW_TEXT,
                    ReconstructionStrategy.LATEX_MATH,
                    ReconstructionStrategy.DYNAMIC_TABLE,
                    ReconstructionStrategy.REDRAW_CHART,
                    ReconstructionStrategy.RECONSTRUCT_DIAGRAM,
                ):
                    reconstructed += 1
                elif o.reconstruction_strategy == ReconstructionStrategy.PRESERVE_ASSET:
                    preserved += 1
                else:
                    failed += 1

            metrics[cat_name.lower()] = {
                "detected": detected,
                "translated": translated,
                "reconstructed": reconstructed,
                "preserved": preserved,
                "fallback": fallback,
                "failed": failed,
            }

        return metrics

    def _calculate_confidence_distribution(self, ir: DocumentIR) -> Dict[str, int]:
        """Calculates confidence distribution (HIGH, MEDIUM, LOW) conforming to Section 21."""
        high = 0
        med = 0
        low = 0
        for o in ir.objects:
            score = o.confidence.overall()
            if score >= 0.85:
                high += 1
            elif score >= 0.70:
                med += 1
            else:
                low += 1
        return {"HIGH": high, "MEDIUM": med, "LOW": low}


def _cli_preflight(source: str) -> Optional[Dict[str, Any]]:
    """Kiểm tra trước ở tầng CLI (run() không tự chặn để test/thư viện dùng PDF tổng hợp vẫn chạy).

    Từ chối (thoát 2; thiếu thư viện thoát 4): không phải PDF thật (DOCX/PPTX/ảnh đổi đuôi), PDF có mật khẩu,
    PDF chủ yếu là scan. Cảnh báo dấu tiếng Việt vỡ (PyMuPDF so với pdfplumber/pdftotext) ra stderr."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_shared"))
    try:
        from doc_ingest_bridge import pdf_preflight
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Không nạp được .agents/skills/_shared/doc_ingest_bridge.py ({e}) — bỏ qua kiểm tra trước.", file=sys.stderr)
        return None
    pf = pdf_preflight(source)
    if not pf["ok"]:
        msg = pf["message"]
        if pf.get("kind") in ("docx", "pptx", "xlsx", "doc", "ppt", "odt", "odp", "rtf") and Path(source).suffix.lower() == ".pdf":
            msg += (f" Lưu ý: tệp mang đuôi .pdf nhưng thực chất là {pf['kind']} — đổi lại đuôi .{pf['kind']} trước khi "
                    "chuyển bằng soffice (tránh ghi đè lên chính tệp nguồn).")
        print(f"⛔ KIỂM TRA TRƯỚC THẤT BẠI — không tái dựng được tệp {source}:\n   {msg}", file=sys.stderr)
        print(json.dumps({"overall_status": "PREFLIGHT_REFUSED", "kind": pf.get("kind"), "pages": pf.get("pages"),
                          "scan_pages": pf.get("scan_pages", [])[:50], "message": msg}, ensure_ascii=False, indent=2))
        sys.exit(4 if pf["code"] == 4 else 2)
    for w in pf["warnings"]:
        print(w if w.startswith("⚠️") else f"⚠️ {w}", file=sys.stderr)
    return pf


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AIWF Semantic Document Reconstruction & Translation Pipeline")
    parser.add_argument("--source", required=True, help="Path to source PDF file")
    parser.add_argument("--target-lang", default="vi", help="Target language code (vi, en, ja)")
    parser.add_argument("--source-lang", default="ja", help="Source language code (ja, en, vi)")
    parser.add_argument("--output-dir", default=None, help="Output directory for final delivery")
    parser.add_argument("--process-dir", default=None, help="Process directory for intermediate artifacts")
    parser.add_argument("--translation-map", default=None, help="Path to JSON file with translation mappings")
    parser.add_argument("--allow-draft", action="store_true", help="Vẫn giao PDF khi kiểm định dịch chưa đạt (chỉ để xem nháp)")
    parser.add_argument("--skip-preflight", action="store_true", help="Bỏ kiểm tra trước (PDF thật/mật khẩu/lớp chữ/dấu tiếng Việt)")
    args = parser.parse_args()

    preflight = None if args.skip_preflight else _cli_preflight(args.source)

    t_map = None
    if args.translation_map and Path(args.translation_map).exists():
        t_map = json.loads(Path(args.translation_map).read_text(encoding="utf-8"))

    pipeline = DocumentReconstructionPipeline()
    res = pipeline.run(
        source_pdf=args.source,
        target_language=args.target_lang,
        source_language=args.source_lang,
        output_dir=args.output_dir,
        process_dir=args.process_dir,
        translation_map=t_map,
        allow_draft=args.allow_draft,
        preflight=preflight,
    )
    rep = res["execution_report"]
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    if rep.get("diacritic_damaged_pages"):
        print("⚠️ NHẮC LẠI: " + rep["preflight_warnings"][-1].removeprefix("⚠️").strip(), file=sys.stderr)
    if rep.get("overall_status") == "NO_TRANSLATABLE_TEXT":
        sys.exit(2)
    if rep.get("overall_status") == "AWAITING_AGENT_TRANSLATION":
        sys.exit(3)
    n_translated = sum(m.get("translated", 0) for m in res.get("object_reconstruction_metrics", {}).values())
    if n_translated == 0:
        print("⛔ 0 đối tượng được dịch — PDF tái dựng vẫn là chữ gốc, KHÔNG coi là hoàn tất.", file=sys.stderr)
        sys.exit(1)
    if not res["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
