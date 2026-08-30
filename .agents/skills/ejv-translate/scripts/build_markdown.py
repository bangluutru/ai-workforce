#!/usr/bin/env python3
"""Build parallel and sequential Markdown documents from EJV Trilingual JSON data.

Supports standard document blocks and legal/administrative hierarchy:
h1, h2, h3, chapter, article, clause, point, p, ul, ol, table, meta_table, blockquote, hr.
"""

import argparse
import json
import sys
from pathlib import Path


def clean_cell(text: str) -> str:
    """Clean string for markdown table cell."""
    if text is None:
        return ""
    t = str(text).replace("\n", "<br/>").replace("|", "\\|").strip()
    return t


def build_markdown(blocks: list, output_path: Path, mode: str = "parallel"):
    lines = []
    lines.append("# BẢN DỊCH ĐỐI CHIẾU ĐA NGÔN NGỮ (EJV Trilingual Document)\n")

    if mode == "parallel":
        lines.append("| Tiếng Việt (VN) | English (EN) | 日本語 (JA) |")
        lines.append("| :--- | :--- | :--- |")

        for block in blocks:
            b_type = block.get("type", "p")
            vn = block.get("vn", "")
            en = block.get("en", "")
            ja = block.get("ja", "")

            if b_type == "h1":
                lines.append(f"| **# {clean_cell(vn)}** | **# {clean_cell(en)}** | **# {clean_cell(ja)}** |")

            elif b_type == "h2":
                lines.append(f"| **## {clean_cell(vn)}** | **## {clean_cell(en)}** | **## {clean_cell(ja)}** |")

            elif b_type == "h3":
                lines.append(f"| **### {clean_cell(vn)}** | **### {clean_cell(en)}** | **### {clean_cell(ja)}** |")

            elif b_type == "chapter":
                lines.append(f"| **### {clean_cell(vn)}** | **### {clean_cell(en)}** | **### {clean_cell(ja)}** |")

            elif b_type == "article":
                lines.append(f"| **#### {clean_cell(vn)}** | **#### {clean_cell(en)}** | **#### {clean_cell(ja)}** |")

            elif b_type in {"clause", "point", "p"}:
                c_vn = clean_cell(vn)
                c_en = clean_cell(en)
                c_ja = clean_cell(ja)
                if b_type == "clause":
                    lines.append(f"| {c_vn} | {c_en} | {c_ja} |")
                elif b_type == "point":
                    lines.append(f"| &nbsp;&nbsp;{c_vn} | &nbsp;&nbsp;{c_en} | &nbsp;&nbsp;{c_ja} |")
                else:
                    lines.append(f"| {c_vn} | {c_en} | {c_ja} |")

            elif b_type in {"ul", "ol"}:
                vn_items = "<br/>".join([f"• {clean_cell(x)}" for x in vn]) if isinstance(vn, list) else clean_cell(vn)
                en_items = "<br/>".join([f"• {clean_cell(x)}" for x in en]) if isinstance(en, list) else clean_cell(en)
                ja_items = "<br/>".join([f"• {clean_cell(x)}" for x in ja]) if isinstance(ja, list) else clean_cell(ja)
                lines.append(f"| {vn_items} | {en_items} | {ja_items} |")

            elif b_type == "table":
                headers_dict = block.get("headers", {})
                rows_dict = block.get("rows", {})
                h_vn = headers_dict.get("vn", []) if isinstance(headers_dict, dict) else (headers_dict or [])
                h_en = headers_dict.get("en", []) if isinstance(headers_dict, dict) else (headers_dict or [])
                h_ja = headers_dict.get("ja", []) if isinstance(headers_dict, dict) else (headers_dict or [])

                r_vn = rows_dict.get("vn", []) if isinstance(rows_dict, dict) else (rows_dict or [])
                r_en = rows_dict.get("en", []) if isinstance(rows_dict, dict) else (rows_dict or [])
                r_ja = rows_dict.get("ja", []) if isinstance(rows_dict, dict) else (rows_dict or [])

                tbl_vn_lines = ["**[BẢNG TIẾNG VIỆT]**"]
                if h_vn:
                    tbl_vn_lines.append(" | ".join([clean_cell(h) for h in h_vn]))
                for r in r_vn:
                    tbl_vn_lines.append(" | ".join([clean_cell(c) for c in r]))
                
                tbl_en_lines = ["**[ENGLISH TABLE]**"]
                if h_en:
                    tbl_en_lines.append(" | ".join([clean_cell(h) for h in h_en]))
                for r in r_en:
                    tbl_en_lines.append(" | ".join([clean_cell(c) for c in r]))

                tbl_ja_lines = ["**[日本語 表]**"]
                if h_ja:
                    tbl_ja_lines.append(" | ".join([clean_cell(h) for h in h_ja]))
                for r in r_ja:
                    tbl_ja_lines.append(" | ".join([clean_cell(c) for c in r]))

                cell_vn = "<br/>".join(tbl_vn_lines)
                cell_en = "<br/>".join(tbl_en_lines)
                cell_ja = "<br/>".join(tbl_ja_lines)
                lines.append(f"| {cell_vn} | {cell_en} | {cell_ja} |")

            elif b_type == "meta_table":
                items = block.get("items", [])
                m_vn, m_en, m_ja = [], [], []
                for it in items:
                    lbl = it.get("label", {})
                    val = it.get("value", {})
                    if isinstance(lbl, dict):
                        m_vn.append(f"**{clean_cell(lbl.get('vn', ''))}:** {clean_cell(val.get('vn', '')) if isinstance(val, dict) else clean_cell(val)}")
                        m_en.append(f"**{clean_cell(lbl.get('en', ''))}:** {clean_cell(val.get('en', '')) if isinstance(val, dict) else clean_cell(val)}")
                        m_ja.append(f"**{clean_cell(lbl.get('ja', ''))}:** {clean_cell(val.get('ja', '')) if isinstance(val, dict) else clean_cell(val)}")
                    else:
                        m_vn.append(f"**{clean_cell(lbl)}:** {clean_cell(val)}")
                        m_en.append(f"**{clean_cell(lbl)}:** {clean_cell(val)}")
                        m_ja.append(f"**{clean_cell(lbl)}:** {clean_cell(val)}")

                lines.append(f"| {'<br/>'.join(m_vn)} | {'<br/>'.join(m_en)} | {'<br/>'.join(m_ja)} |")

            elif b_type == "blockquote":
                lines.append(f"| *💡 {clean_cell(vn)}* | *💡 {clean_cell(en)}* | *💡 {clean_cell(ja)}* |")

            elif b_type == "hr":
                lines.append("| --- | --- | --- |")

    else:
        # Sequential mode: by language
        for lang_code, lang_name in [("vn", "🇻🇳 TIẾNG VIỆT"), ("en", "🇬🇧 ENGLISH"), ("ja", "🇯🇵 日本語")]:
            lines.append(f"\n---\n## {lang_name}\n")
            for block in blocks:
                b_type = block.get("type", "p")
                val = block.get(lang_code, "")
                if b_type == "h1":
                    lines.append(f"# {val}\n")
                elif b_type == "h2":
                    lines.append(f"## {val}\n")
                elif b_type == "h3":
                    lines.append(f"### {val}\n")
                elif b_type == "chapter":
                    lines.append(f"\n### {val}\n")
                elif b_type == "article":
                    lines.append(f"\n#### {val}\n")
                elif b_type == "clause":
                    lines.append(f"{val}\n")
                elif b_type == "point":
                    lines.append(f"  {val}\n")
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
                elif b_type == "table":
                    headers_dict = block.get("headers", {})
                    rows_dict = block.get("rows", {})
                    headers = headers_dict.get(lang_code, []) if isinstance(headers_dict, dict) else (headers_dict or [])
                    rows = rows_dict.get(lang_code, []) if isinstance(rows_dict, dict) else (rows_dict or [])
                    if headers:
                        lines.append("| " + " | ".join(clean_cell(h) for h in headers) + " |")
                        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                    for row in rows:
                        lines.append("| " + " | ".join(clean_cell(c) for c in row) + " |")
                    lines.append("")
                elif b_type == "meta_table":
                    items = block.get("items", [])
                    for it in items:
                        lbl = it.get("label", {})
                        val_item = it.get("value", {})
                        lbl_str = lbl.get(lang_code, "") if isinstance(lbl, dict) else str(lbl)
                        val_str = val_item.get(lang_code, "") if isinstance(val_item, dict) else str(val_item)
                        lines.append(f"- **{lbl_str}**: {val_str}")
                    lines.append("")

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
