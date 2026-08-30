#!/usr/bin/env python3
"""Autonomous Batch Translator & End-to-End Pipeline for EJV Translate.

Translates all chunked batches sequentially and autonomously without requiring
manual turn-by-turn prompts, then automatically validates, merges, and exports
publication-grade DOCX, PDF, and parallel Markdown documents.

Usage:
    python auto_translate.py \\
        --process-dir "/path/to/process_dir" \\
        --output-dir "/Users/tranhaibang/Downloads" \\
        --file-stem "du-thao-nd-quan-ly-my-pham" \\
        --auto-export
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Prompt Template for EJV Trilingual Translation
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are EJV Trilingual Document Translator — an expert legal and technical translator specializing in Vietnamese, English, and Japanese.
Translate the input JSON array of document blocks into high-accuracy Vietnamese (vn), English (en), and Japanese (ja).

CRITICAL REQUIREMENTS:
1. Maintain exact 1-to-1 block correspondence and block 'type'.
2. Symmetrical structure: For 'ul' or 'ol', each item in 'vn' must have exact matching items in 'en' and 'ja'.
3. For 'table', provide 'headers' (dict of vn, en, ja arrays) and 'rows' (dict of vn, en, ja 2D arrays).
4. For 'meta_table', provide 'items' with 'label' (dict of vn, en, ja) and 'value' (dict of vn, en, ja).
5. Clean watermarks and OCR artifacts (e.g., '0 /2 5', 'n A c o g N').
6. Ensure professional legal terminology:
   - VN: "công bố mỹ phẩm", "Số quản lý", "Hồ sơ thông tin sản phẩm (PIF)", "Biến cố bất lợi nghiêm trọng (Cosmetovigilance)"
   - EN: "Cosmetic Product Notification", "Management Number", "Product Information File (PIF)", "Serious Adverse Event"
   - JA: "化粧品製品届出", "管理番号", "製品情報ファイル（PIF）", "重大有害事象（コスメトビジランス）"
7. Output ONLY valid JSON array with no extra markdown or explanations.
"""


def call_gemini_api(blocks: list, api_key: str, model: str = "gemini-2.5-flash") -> list:
    """Call Gemini API via REST to translate a batch of blocks."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt_content = f"Translate the following blocks into trilingual EJV JSON format (vn, en, ja):\n\n{json.dumps(blocks, ensure_ascii=False, indent=2)}"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt_content}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                translated_blocks = json.loads(raw_text)
                if isinstance(translated_blocks, list) and len(translated_blocks) == len(blocks):
                    return translated_blocks
                elif isinstance(translated_blocks, list):
                    print(f"⚠️ Warning: Received {len(translated_blocks)} blocks, expected {len(blocks)}", file=sys.stderr)
                    return translated_blocks
                else:
                    raise ValueError("API response is not a JSON list")
        except Exception as e:
            print(f"⚠️ API attempt {attempt+1}/{max_retries} failed: {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt * 3)
            else:
                raise e


# ─────────────────────────────────────────────────────────────────────────────
# Execution Engine
# ─────────────────────────────────────────────────────────────────────────────

def run_auto_translation(process_dir: Path, output_dir: Path, file_stem: str, api_key: str = None, model: str = "gemini-2.5-flash", auto_export: bool = True):
    manifest_file = process_dir / "manifest.json"
    if not manifest_file.exists():
        print(f"❌ Error: manifest.json not found in {process_dir}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    batches = manifest.get("batches", {})
    total_batches = len(batches)
    print(f"\n=======================================================")
    print(f"🚀 EJV TRANSLATE AUTONOMOUS ENGINE")
    print(f"📂 Process Directory: {process_dir}")
    print(f"📦 Total Batches: {total_batches}")
    print(f"=======================================================\n")

    # If API key is not passed, check environment
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    pending_batches = [
        (b_id, meta) for b_id, meta in sorted(batches.items(), key=lambda x: x[1]["index"])
        if not (process_dir / meta["target_file"]).exists() or meta.get("status") != "completed"
    ]

    print(f"📊 Status: {total_batches - len(pending_batches)}/{total_batches} batches already completed.")
    if pending_batches:
        print(f"⏳ Remaining to translate: {len(pending_batches)} batch(es).")
        if api_key:
            print(f"🔑 Gemini API Key detected. Commencing autonomous translation loop...")
            for idx, (b_id, meta) in enumerate(pending_batches, 1):
                source_path = process_dir / meta["source_file"]
                target_path = process_dir / meta["target_file"]
                print(f"[{idx}/{len(pending_batches)}] Translating {b_id} ({meta['block_count']} blocks)...", end="", flush=True)
                
                with open(source_path, "r", encoding="utf-8") as sf:
                    source_blocks = json.load(sf)
                
                t0 = time.time()
                translated = call_gemini_api(source_blocks, api_key=api_key, model=model)
                elapsed = time.time() - t0
                
                with open(target_path, "w", encoding="utf-8") as tf:
                    json.dump(translated, tf, ensure_ascii=False, indent=2)
                
                meta["status"] = "completed"
                meta["block_count"] = len(translated)
                print(f" Done ({elapsed:.1f}s) ✅")
                
                # Save progress in manifest after each batch
                with open(manifest_file, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, ensure_ascii=False, indent=2)
        else:
            print(f"ℹ️ Note: No API key passed. Manifest reflects current file states.")

    # Check overall completion
    completed_count = sum(1 for m in manifest["batches"].values() if (process_dir / m["target_file"]).exists())
    print(f"\n=======================================================")
    print(f"📈 Total Translated Batches: {completed_count}/{total_batches} ({completed_count/total_batches*100:.1f}%)")
    print(f"=======================================================\n")

    if auto_export:
        print("📦 Merging all translated batches...")
        merged = []
        for b_id, meta in sorted(manifest["batches"].items(), key=lambda x: x[1]["index"]):
            target_path = process_dir / meta["target_file"]
            if target_path.exists():
                with open(target_path, "r", encoding="utf-8") as tf:
                    merged.extend(json.load(tf))

        merged_file = process_dir / "merged_ejv.json"
        with open(merged_file, "w", encoding="utf-8") as mf:
            json.dump(merged, mf, ensure_ascii=False, indent=2)
        print(f"✅ Created merged dataset: {merged_file} ({len(merged)} blocks)")

        # Export outputs
        script_dir = Path(__file__).resolve().parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Build DOCX
        print("\n📄 Generating Publication-grade Administrative DOCX files...")
        os.system(f'python3 "{script_dir}/build_docx_v2.py" --input "{merged_file}" --output "{output_dir}/{file_stem}_vi.docx" --lang vn')
        os.system(f'python3 "{script_dir}/build_docx_v2.py" --input "{merged_file}" --output "{output_dir}/{file_stem}_en.docx" --lang en')
        os.system(f'python3 "{script_dir}/build_docx_v2.py" --input "{merged_file}" --output "{output_dir}/{file_stem}_ja.docx" --lang ja')

        # 2. Build Markdown
        print("\n📝 Generating Parallel Markdown document...")
        os.system(f'python3 "{script_dir}/build_markdown.py" --input "{merged_file}" --output "{output_dir}/{file_stem}_tam_ngu_parallel.md" --mode parallel')

        # 3. Export PDF via LibreOffice / docx2pdf
        print("\n📑 Exporting high-fidelity PDF documents...")
        libreoffice_bin = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        if os.path.exists(libreoffice_bin):
            cmd = f'"{libreoffice_bin}" --headless "-env:UserInstallation=file:///tmp/libreoffice_ejv_auto" --convert-to pdf --outdir "{output_dir}" "{output_dir}/{file_stem}_vi.docx" "{output_dir}/{file_stem}_en.docx" "{output_dir}/{file_stem}_ja.docx"'
            os.system(cmd)
        else:
            print("⚠️ LibreOffice not found at standard path, attempting system soffice...")
            os.system(f'soffice --headless --convert-to pdf --outdir "{output_dir}" "{output_dir}/{file_stem}_en.docx" "{output_dir}/{file_stem}_ja.docx"')

        print(f"\n🎉 ALL EXPORTS COMPLETED IN: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Batch Translation & Export Engine.")
    parser.add_argument("--process-dir", required=True, type=Path, help="Working directory containing batches and manifest.json")
    parser.add_argument("--output-dir", default=Path("/Users/tranhaibang/Downloads"), type=Path, help="Target export folder")
    parser.add_argument("--file-stem", default="document", type=str, help="Base name for exported documents")
    parser.add_argument("--api-key", default=None, type=str, help="Gemini API Key (optional, defaults to env var)")
    parser.add_argument("--model", default="gemini-2.5-flash", type=str, help="Gemini model name")
    parser.add_argument("--auto-export", action="store_true", default=True, help="Automatically merge and export DOCX/PDF/MD")
    args = parser.parse_args()

    run_auto_translation(
        process_dir=args.process_dir,
        output_dir=args.output_dir,
        file_stem=args.file_stem,
        api_key=args.api_key,
        model=args.model,
        auto_export=args.auto_export
    )


if __name__ == "__main__":
    main()
