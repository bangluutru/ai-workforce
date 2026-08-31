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
    merged = []
    merged_count = 0
    for b_id, meta in sorted(manifest["batches"].items(), key=lambda x: x[1]["index"]):
        target_path = process_dir / meta["target_file"]
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as tf:
                batch_data = json.load(tf)
                merged.extend(batch_data)
                merged_count += 1

    if not merged:
        print(f"❌ No translated batches found. Nothing to merge.", file=sys.stderr)
        return

    merged_file = process_dir / "merged_ejv.json"
    with open(merged_file, "w", encoding="utf-8") as mf:
        json.dump(merged, mf, ensure_ascii=False, indent=2)
    print(f"✅ Merged {merged_count} batches → {merged_file} ({len(merged)} blocks)")

    # Locate script directory
    script_dir = Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build DOCX
    print(f"\n📄 Generating DOCX files...")
    for lang, lang_name in [("vn", "Tiếng Việt"), ("en", "English"), ("ja", "日本語")]:
        docx_path = output_dir / f"{file_stem}_{lang}.docx"
        # Try build_docx_v2.py first, fallback to build_docx.py
        docx_script = script_dir / "build_docx_v2.py"
        if not docx_script.exists():
            docx_script = script_dir / "build_docx.py"
        if docx_script.exists():
            ret = os.system(f'python3 "{docx_script}" --input "{merged_file}" --output "{docx_path}" --lang {lang}')
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

        # Single-language markdown
        for lang in ["vn", "en", "ja"]:
            md_path = output_dir / f"{file_stem}_{lang}.md"
            os.system(f'python3 "{md_script}" --input "{merged_file}" --output "{md_path}" --mode sequential --lang {lang}')

    # 3. Export PDF via Multi-Tier Conversion
    print(f"\n📑 Exporting PDF via Multi-Tier Conversion...")
    _export_pdf_multitier(output_dir, file_stem)

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
    parser.add_argument("--auto-export", action="store_true", default=False,
                        help="Automatically merge and export DOCX/PDF/MD after status check")
    parser.add_argument("--status-only", action="store_true", default=False,
                        help="Only print status, do not merge or export")
    args = parser.parse_args()

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
