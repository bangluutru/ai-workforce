#!/usr/bin/env python3
"""Autonomous Batch Translation Pipeline — Merge & Export Engine.

Orchestrates the full EJV Translate post-extraction pipeline:
  1. Scans manifest.json to identify pending (untranslated) batches
  2. Prints pending batch info for the Antigravity Agent to translate
  3. Merges all completed batches into merged_ejv.json
  4. Exports publication-grade DOCX, PDF, and Markdown documents

IMPORTANT — ZERO EXTERNAL API PRINCIPLE:
  This script does NOT call any external AI API (Gemini, OpenAI, etc.).
  All translation is performed by the Antigravity Agent (built-in LLM).
  This script only handles file I/O, merging, validation, and export.

Usage:
    # Check status & merge/export completed batches:
    python auto_translate.py \\
        --process-dir "/path/to/process_dir" \\
        --output-dir "/Users/user/Downloads" \\
        --file-stem "document_name" \\
        --auto-export

    # Just check status (no export):
    python auto_translate.py \\
        --process-dir "/path/to/process_dir" \\
        --status-only
"""

import argparse
import json
import os
import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Status & Pending Batch Reporter
# ─────────────────────────────────────────────────────────────────────────────

def report_status(process_dir: Path) -> dict:
    """Read manifest.json and report batch translation status.
    
    Returns dict with keys: total, completed, pending, pending_batches.
    """
    manifest_file = process_dir / "manifest.json"
    if not manifest_file.exists():
        print(f"❌ Error: manifest.json not found in {process_dir}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    batches = manifest.get("batches", {})
    total = len(batches)

    completed = []
    pending = []
    for b_id, meta in sorted(batches.items(), key=lambda x: x[1]["index"]):
        target_path = process_dir / meta["target_file"]
        if target_path.exists():
            completed.append((b_id, meta))
        else:
            pending.append((b_id, meta))

    print(f"\n{'='*60}")
    print(f"📊 EJV TRANSLATE — BATCH STATUS REPORT")
    print(f"📂 Process Directory: {process_dir}")
    print(f"{'='*60}")
    print(f"✅ Completed: {len(completed)}/{total}")
    print(f"⏳ Pending:   {len(pending)}/{total}")

    if pending:
        print(f"\n📋 Pending batches (need Agent translation):")
        for b_id, meta in pending:
            source_path = process_dir / meta["source_file"]
            print(f"   - {b_id}: {meta['source_file']} → {meta['target_file']} ({meta.get('block_count', '?')} blocks)")
    else:
        print(f"\n🎉 All batches translated! Ready for merge & export.")

    return {
        "total": total,
        "completed": len(completed),
        "pending": len(pending),
        "pending_batches": pending,
        "manifest": manifest,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Merge & Export Engine
# ─────────────────────────────────────────────────────────────────────────────

def merge_and_export(process_dir: Path, output_dir: Path, file_stem: str, status: dict):
    """Merge all translated batches and export DOCX/PDF/MD documents."""
    manifest = status["manifest"]

    if status["pending"] > 0:
        print(f"\n⚠️ Warning: {status['pending']} batch(es) still pending translation.")
        print(f"   Merging only completed batches. Run again after Agent finishes translating.")

    # Merge all available translated batches
    print(f"\n📦 Merging translated batches...")
    script_dir = Path(__file__).resolve().parent
    merge_script = script_dir / "merge_batches.py"
    merged_file = process_dir / "merged_ejv.json"
    ret = os.system(f'python3 "{merge_script}" --process-dir "{process_dir}" --output "{merged_file}"')
    if ret != 0:
        print(f"❌ Error during merge_batches", file=sys.stderr)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    _rep = process_dir / "extraction_report.json"
    if _rep.exists():
        try:
            _w = json.loads(_rep.read_text(encoding="utf-8")).get("warnings") or []
        except (ValueError, OSError):
            _w = []
        for w in _w:
            print(f"   ⚠️ [trích xuất] {w}")

    # 0b. CỔNG CHẶN: chỉ xuất ngôn ngữ được yêu cầu, và chỉ khi translation_qa.py không còn lỗi chặn.
    #     (Trước đây xuất cả 3 ngôn ngữ kể cả batch chưa dịch → "_ja.docx" chứa 99% tiếng Việt.)
    langs = [l for l in (os.environ.get("EJV_LANGS") or "vn,en,ja").split(",") if l]
    if status["pending"] > 0 and not os.environ.get("EJV_ALLOW_PARTIAL"):
        print(f"❌ Còn {status['pending']} batch chưa dịch — KHÔNG xuất file. Dịch xong rồi chạy lại.", file=sys.stderr)
        sys.exit(2)
    qa_json = process_dir / "translation_qa.json"
    ret = os.system(f'python3 "{script_dir / "translation_qa.py"}" --input "{merged_file}" --langs {",".join(langs)} --json "{qa_json}"')
    if ret != 0 and not os.environ.get("EJV_ALLOW_PARTIAL"):
        print(f"❌ translation_qa.py còn lỗi chặn (xem {qa_json}) — KHÔNG xuất file. Dịch lại các khối bị báo rồi chạy lại.", file=sys.stderr)
        sys.exit(2)

    # 0. Build EPUB if source document is an EPUB
    epub_script = script_dir / "epub_builder.py"
    toc_trans = process_dir / "toc_translations.json"
    source_file_str = manifest.get("source_file", "")
    source_epub = None
    # extract_text.py ghi extraction_report.json: tệp gốc + định dạng nhận theo magic bytes (không đoán theo đuôi)
    report_file = process_dir / "extraction_report.json"
    if not report_file.exists() and source_file_str:
        report_file = Path(source_file_str).parent / "extraction_report.json"
    extraction = {}
    if report_file.exists():
        try:
            extraction = json.loads(report_file.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            extraction = {}
    if extraction.get("detected_format") == "epub" and Path(extraction.get("input", "")).is_file():
        source_epub = Path(extraction["input"])
    elif extraction:
        source_epub = None  # nguồn không phải EPUB: không dựng EPUB
    elif source_file_str.endswith(".epub") and Path(source_file_str).exists():
        source_epub = Path(source_file_str)
    elif (process_dir / "toc_items.json").exists():
        # Look for epub in parent or metadata
        epub_candidates = list(Path(source_file_str).parent.glob("*.epub")) if source_file_str else []
        if epub_candidates:
            source_epub = epub_candidates[0]

    if source_epub and epub_script.exists():
        print(f"\n📚 Reconstructing Layout-Preserved EPUB...")
        epub_out = output_dir / f"{file_stem}_vi.epub"
        toc_opt = f'--toc "{toc_trans}"' if toc_trans.exists() else ""
        cmd = f'python3 "{epub_script}" --source "{source_epub}" --blocks "{merged_file}" --output "{epub_out}" --lang {langs[0]} {toc_opt}'
        ret = os.system(cmd)
        if ret == 0:
            print(f"   ✅ EPUB Reconstructed (100% layout preserved): {epub_out.name}")
        else:
            print(f"   ⚠️ EPUB reconstruction returned error code {ret}")

    # 1. Build DOCX
    print(f"\n📄 Generating DOCX files...")
    for lang, lang_name in [(l, n) for l, n in [("vn", "Tiếng Việt"), ("en", "English"), ("ja", "日本語")] if l in langs]:
        docx_path = output_dir / f"{file_stem}_{lang}.docx"
        # build_docx.py chung cho mọi tài liệu (build_docx_v2 cũ chèn cứng tiêu đề "Dự thảo Nghị định mỹ phẩm" → đã bỏ)
        docx_script = script_dir / "build_docx.py"
        style = "administrative" if lang == "vn" else "standard"
        if docx_script.exists():
            ret = os.system(f'python3 "{docx_script}" --input "{merged_file}" --output "{docx_path}" --lang {lang} --style {style}')
            if ret == 0:
                print(f"   ✅ {lang_name}: {docx_path.name}")
            else:
                print(f"   ⚠️ {lang_name}: DOCX generation returned error code {ret}")
        else:
            print(f"   ⚠️ No DOCX builder script found at {script_dir}")

    # 2. Build Markdown
    print(f"\n📝 Generating Markdown documents...")
    md_script = script_dir / "build_markdown.py"
    if md_script.exists():
        for mode, suffix in [("parallel", "tam_ngu_parallel"), ("sequential", "tam_ngu_sequential")]:
            md_path = output_dir / f"{file_stem}_{suffix}.md"
            os.system(f'python3 "{md_script}" --input "{merged_file}" --output "{md_path}" --mode {mode}')
            print(f"   ✅ {suffix}: {md_path.name}")

        # Dual-mode markdown (parallel & sequential) generated above

    # 3. Export PDF via Multi-Tier Conversion
    print(f"\n📑 Exporting PDF via Multi-Tier Conversion...")
    _export_pdf_multitier(output_dir, file_stem)

    # 4. Build Responsive HTML (Dual-View: Desktop Side-by-Side & Mobile Tabbed)
    print(f"\n🌐 Generating Standalone Responsive HTML...")
    html_script = script_dir / "build_html.py"
    if html_script.exists():
        html_path = output_dir / f"{file_stem}_tam_ngu.html"
        ret = os.system(f'python3 "{html_script}" --input "{merged_file}" --out "{html_path}" --type parallel --title "{file_stem} — Bản Dịch Tam Ngữ"')
        if ret == 0:
            print(f"   ✅ Responsive HTML: {html_path.name}")
        else:
            print(f"   ⚠️ HTML export returned code {ret}")

    print(f"\n{'='*60}")
    print(f"🎉 ALL EXPORTS COMPLETED → {output_dir}")
    print(f"{'='*60}\n")


def _export_pdf_multitier(output_dir: Path, file_stem: str):
    """Multi-Tier DOCX→PDF conversion (LibreOffice > docx2pdf > DOCX delivery)."""
    docx_files = [output_dir / f"{file_stem}_{lang}.docx" for lang in ["vi", "en", "ja"]]
    # Also check 'vn' suffix variant
    for i, f in enumerate(docx_files):
        if not f.exists():
            alt = output_dir / f"{file_stem}_vn.docx" if "vi" in f.name else f
            if alt.exists():
                docx_files[i] = alt

    existing_docx = [f for f in docx_files if f.exists()]
    if not existing_docx:
        print(f"   ⚠️ No DOCX files found to convert to PDF.")
        return

    # Tier 1: LibreOffice headless
    libreoffice_paths = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
        "/usr/bin/soffice",                                       # Linux
        "/usr/bin/libreoffice",                                   # Linux alt
    ]
    lo_bin = None
    for p in libreoffice_paths:
        if os.path.exists(p):
            lo_bin = p
            break

    if lo_bin:
        files_str = " ".join(f'"{f}"' for f in existing_docx)
        cmd = f'"{lo_bin}" --headless "-env:UserInstallation=file:///tmp/libreoffice_ejv_auto" --convert-to pdf --outdir "{output_dir}" {files_str}'
        ret = os.system(cmd)
        if ret == 0:
            print(f"   ✅ PDF exported via LibreOffice (Tier 1)")
            return
        print(f"   ⚠️ LibreOffice returned error code {ret}, trying Tier 2...")

    # Tier 2: docx2pdf (requires MS Word)
    try:
        import docx2pdf
        for f in existing_docx:
            pdf_path = f.with_suffix(".pdf")
            docx2pdf.convert(str(f), str(pdf_path))
        print(f"   ✅ PDF exported via docx2pdf (Tier 2)")
        return
    except (ImportError, Exception):
        pass

    # Tier 3: Pure DOCX delivery
    print(f"   ℹ️ No PDF converter available (Tier 3: DOCX delivery).")
    print(f"   📌 Mở file .docx trong Word/Google Docs và chọn File → Save as PDF")


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EJV Translate — Autonomous Merge & Export Engine (Zero External API)",
        epilog="All translation is done by the Antigravity Agent. This script only handles I/O."
    )
    parser.add_argument("--process-dir", required=True, type=Path,
                        help="Working directory containing batches and manifest.json")
    parser.add_argument("--output-dir", default=None, type=Path,
                        help="Target export folder (default: ~/Downloads)")
    parser.add_argument("--file-stem", default="document", type=str,
                        help="Base name for exported documents")
    parser.add_argument("--langs", default="vn,en,ja", help="Ngôn ngữ ĐÍCH cần xuất, ví dụ vn hoặc vn,ja (chỉ xuất các ngôn ngữ này)")
    parser.add_argument("--allow-partial", action="store_true", help="Cho phép xuất khi còn batch/lỗi (KHÔNG dùng cho bàn giao)")
    parser.add_argument("--auto-export", action="store_true", default=False,
                        help="Automatically merge and export DOCX/PDF/MD after status check")
    parser.add_argument("--status-only", action="store_true", default=False,
                        help="Only print status, do not merge or export")
    args = parser.parse_args()
    os.environ["EJV_LANGS"] = args.langs
    if args.allow_partial:
        os.environ["EJV_ALLOW_PARTIAL"] = "1"

    if args.output_dir is None:
        args.output_dir = Path.home() / "Downloads"

    status = report_status(args.process_dir)

    if args.status_only:
        return

    if args.auto_export or status["pending"] == 0:
        merge_and_export(
            process_dir=args.process_dir,
            output_dir=args.output_dir,
            file_stem=args.file_stem,
            status=status,
        )
    else:
        print(f"\nℹ️ Use --auto-export to merge and export even with pending batches.")
        print(f"ℹ️ Or let the Antigravity Agent translate remaining batches first.")


if __name__ == "__main__":
    main()
