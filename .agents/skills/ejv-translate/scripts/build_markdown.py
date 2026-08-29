#!/usr/bin/env python3
"""Build parallel Markdown document from EJV Trilingual JSON data."""

import argparse
import json
import sys
from pathlib import Path


def build_markdown(blocks: list, output_path: Path, mode: str = "parallel"):
    lines = []
    lines.append("# BẢN DỊCH ĐỐI CHIẾU ĐA NGÔN NGỮ (EJV Trilingual Document)\n")

    if mode == "parallel":
        lines.append("| Tiếng Việt (VN) | English (EN) | 日本語 (JA) |")
        lines.append("| :--- | :--- | :--- |")

        for block in blocks:
            b_type = block.get("type")
            vn = block.get("vn", "")
            en = block.get("en", "")
            ja = block.get("ja", "")

            if b_type in {"h1", "h2", "h3"}:
                prefix = "#" * (1 if b_type == "h1" else (2 if b_type == "h2" else 3))
                lines.append(f"| **{prefix} {vn}** | **{prefix} {en}** | **{prefix} {ja}** |")

            elif b_type == "p":
                vn_clean = str(vn).replace("\n", "<br/>").replace("|", "\\|")
                en_clean = str(en).replace("\n", "<br/>").replace("|", "\\|")
                ja_clean = str(ja).replace("\n", "<br/>").replace("|", "\\|")
                lines.append(f"| {vn_clean} | {en_clean} | {ja_clean} |")

            elif b_type in {"ul", "ol"}:
                vn_items = "<br/>".join([f"• {x}" for x in vn]) if isinstance(vn, list) else str(vn)
                en_items = "<br/>".join([f"• {x}" for x in en]) if isinstance(en, list) else str(en)
                ja_items = "<br/>".join([f"• {x}" for x in ja]) if isinstance(ja, list) else str(ja)
                lines.append(f"| {vn_items} | {en_items} | {ja_items} |")

            elif b_type == "blockquote":
                lines.append(f"| *💡 {vn}* | *💡 {en}* | *💡 {ja}* |")

            elif b_type == "hr":
                lines.append("| --- | --- | --- |")

    else:
        # Sequential mode: by language
        for lang_code, lang_name in [("vn", "🇻🇳 TIẾNG VIỆT"), ("en", "🇬🇧 ENGLISH"), ("ja", "🇯🇵 日本語")]:
            lines.append(f"\n---\n## {lang_name}\n")
            for block in blocks:
                b_type = block.get("type")
                val = block.get(lang_code, "")
                if b_type == "h1":
                    lines.append(f"# {val}\n")
                elif b_type == "h2":
                    lines.append(f"## {val}\n")
                elif b_type == "h3":
                    lines.append(f"### {val}\n")
                elif b_type == "p":
                    lines.append(f"{val}\n")
                elif b_type in {"ul", "ol"}:
                    items = val if isinstance(val, list) else [val]
                    for item in items:
                        prefix = "1." if b_type == "ol" else "-"
                        lines.append(f"{prefix} {item}")
                    lines.append("")
                elif b_type == "blockquote":
                    lines.append(f"> {val}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ Generated Markdown: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Export EJV JSON to Markdown format.")
    parser.add_argument("--input", required=True, type=Path, help="Input EJV JSON file")
    parser.add_argument("--output", required=True, type=Path, help="Output Markdown file path")
    parser.add_argument("--mode", default="parallel", choices=["parallel", "sequential"], help="Display mode")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        blocks = json.load(f)

    build_markdown(blocks, args.output, mode=args.mode)


if __name__ == "__main__":
    main()
