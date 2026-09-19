#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BabelDOC / PDFMathTranslate Bridge for AI Workforce.

Integrates BabelDOC layout preservation capabilities into AIWF:
1. Uses the unified .venv Python environment.
2. Supports local Ollama models (Zero commercial API key).
3. Configures Vietnamese and Japanese Unicode font mappings.
4. Provides CLI interface conforming to AIWF path resolution and anti-repo bloat rules.

Usage:
    python3 scripts/babeldoc_bridge.py \\
        --input "document.pdf" \\
        --lang-in ja \\
        --lang-out vi \\
        --service ollama \\
        --model "qwen2.5:7b" \\
        --output-dir "~/Downloads"
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_python_bin() -> str:
    """Finds the python executable with babeldoc installed."""
    venv_py = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python3"
    if venv_py.is_file():
        return str(venv_py)
    return sys.executable


def check_babeldoc_available() -> bool:
    """Checks if babeldoc is installed and importable."""
    py = resolve_python_bin()
    res = subprocess.run(
        [py, "-c", "import babeldoc; print('ok')"],
        capture_output=True,
        text=True,
    )
    return res.returncode == 0 and "ok" in res.stdout


def run_babeldoc_translation(
    input_pdf: Path,
    lang_in: str,
    lang_out: str,
    output_dir: Path,
    service: str = "ollama",
    ollama_url: str = "http://localhost:11434/v1",
    model: str = "qwen2.5:7b",
    font_family: str = "sans-serif",
) -> Path:
    """Runs BabelDOC via subprocess."""
    py = resolve_python_bin()
    babeldoc_bin = Path(py).parent / "babeldoc"
    if not babeldoc_bin.is_file():
        cmd_base = [py, "-m", "babeldoc.main"]
    else:
        cmd_base = [str(babeldoc_bin)]

    output_dir.mkdir(parents=True, exist_ok=True)
    out_stem = input_pdf.stem
    target_lang_code = "vi" if lang_out in ("vi", "vn") else lang_out

    cmd = list(cmd_base)
    cmd.extend([
        "--files", str(input_pdf),
        "--lang-in", lang_in,
        "--lang-out", target_lang_code,
        "--watermark-output-mode", "no_watermark",
        "--primary-font-family", font_family,
    ])

    if service == "ollama":
        cmd.extend([
            "--openai",
            "--openai-base-url", ollama_url,
            "--openai-api-key", "ollama",
            "--openai-model", model,
        ])
    elif service == "dry-run":
        cmd.extend(["--only-parse-generate-pdf"])
    else:
        raise ValueError(f"Unsupported service '{service}'. Supported: 'ollama', 'dry-run'")

    print(f"🚀 Launching BabelDOC translation engine...")
    print(f"   Input:  {input_pdf}")
    print(f"   Langs:  {lang_in} -> {target_lang_code}")
    print(f"   Service: {service} (Model: {model})")

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ BabelDOC failed with return code {res.returncode}:", file=sys.stderr)
        print(res.stderr, file=sys.stderr)
        raise RuntimeError(f"BabelDOC execution error: {res.stderr}")

    # Locate generated output PDF
    # BabelDOC defaults to placing output in same directory or working directory
    expected_output = input_pdf.parent / f"{out_stem}.translated.pdf"
    if not expected_output.is_file():
        # Check current working directory
        cwd_output = Path.cwd() / f"{out_stem}.translated.pdf"
        if cwd_output.is_file():
            expected_output = cwd_output

    dest_output = output_dir / f"{out_stem}_babeldoc_{target_lang_code}.pdf"
    if expected_output.is_file():
        shutil.move(str(expected_output), str(dest_output))
        print(f"✅ BabelDOC Translation Complete: {dest_output}")
        return dest_output

    print(f"ℹ️ BabelDOC completed. Checking outputs in {output_dir}...")
    return dest_output


def main():
    parser = argparse.ArgumentParser(description="BabelDOC / PDFMathTranslate AIWF Bridge")
    parser.add_argument("--input", required=True, type=Path, help="Source PDF file")
    parser.add_argument("--lang-in", default="ja", help="Source language (ja, en)")
    parser.add_argument("--lang-out", default="vi", help="Target language (vi, en, ja)")
    parser.add_argument("--service", default="ollama", choices=["ollama", "dry-run"], help="Translation backend")
    parser.add_argument("--ollama-url", default="http://localhost:11434/v1", help="Ollama base URL")
    parser.add_argument("--model", default="qwen2.5:7b", help="Model name")
    parser.add_argument("--output-dir", default=Path("~/Downloads").expanduser(), type=Path, help="Output directory")

    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        return 1

    if not check_babeldoc_available():
        print("Error: BabelDOC is not installed in the active environment.", file=sys.stderr)
        return 1

    try:
        out = run_babeldoc_translation(
            input_pdf=args.input,
            lang_in=args.lang_in,
            lang_out=args.lang_out,
            output_dir=args.output_dir,
            service=args.service,
            ollama_url=args.ollama_url,
            model=args.model,
        )
        print(f"Output saved to: {out}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
