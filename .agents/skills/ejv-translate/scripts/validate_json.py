#!/usr/bin/env python3
"""Validate EJV Translator JSON schema and verify 3-language completeness."""

import argparse
import json
import sys
from pathlib import Path

VALID_TYPES = {"h1", "h2", "h3", "p", "ul", "ol", "table", "blockquote", "hr", "caption"}
LANGUAGES = ["vn", "en", "ja"]


def validate_ejv_json(data: list) -> list[str]:
    errors = []
    if not isinstance(data, list):
        return ["Root JSON element must be an Array/List of block objects."]

    if len(data) == 0:
        return ["JSON array is empty."]

    for i, block in enumerate(data):
        if not isinstance(block, dict):
            errors.append(f"Block #{i+1} is not a valid JSON object.")
            continue

        b_type = block.get("type")
        if not b_type or b_type not in VALID_TYPES:
            errors.append(f"Block #{i+1}: Invalid or missing 'type': '{b_type}'. Expected one of {sorted(VALID_TYPES)}.")
            continue

        if b_type == "hr":
            continue

        if b_type in {"ul", "ol"}:
            for lang in LANGUAGES:
                val = block.get(lang)
                if val is not None and not isinstance(val, list):
                    errors.append(f"Block #{i+1} ({b_type}): '{lang}' must be a list of strings.")

        elif b_type == "table":
            headers = block.get("headers", {})
            rows = block.get("rows", {})
            for lang in LANGUAGES:
                h_lang = headers.get(lang, []) if isinstance(headers, dict) else []
                r_lang = rows.get(lang, []) if isinstance(rows, dict) else []
                if not isinstance(h_lang, list) or not isinstance(r_lang, list):
                    errors.append(f"Block #{i+1} (table): '{lang}' headers/rows must be lists.")

        else:
            # Check presence of text
            present_langs = [lang for lang in LANGUAGES if block.get(lang)]
            if not present_langs:
                errors.append(f"Block #{i+1} ({b_type}): At least one language (vn, en, ja) must be populated.")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate EJV JSON format.")
    parser.add_argument("--input", required=True, type=Path, help="Path to JSON file")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Error: File does not exist: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON Syntax Error: {e}", file=sys.stderr)
        sys.exit(1)

    errors = validate_ejv_json(data)
    if errors:
        print(f"❌ Validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"✅ EJV JSON validation passed! Total blocks: {len(data)}")


if __name__ == "__main__":
    main()
