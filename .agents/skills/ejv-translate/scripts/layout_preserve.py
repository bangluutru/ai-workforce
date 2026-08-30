#!/usr/bin/env python3
"""Layout-preserving document translation for EJV Translate.

Clone the original source file (DOCX or PDF) and replace text in-place with
translated content, preserving all formatting, fonts, margins, page breaks,
table borders, images, and layout structure.

This is "Track 1" of EJV output — complementing the standard DOCX/Markdown
export with format-faithful copies in each target language.

Usage:
    python layout_preserve.py \\
        --source "original.docx" \\
        --blocks "merged_ejv.json" \\
        --lang en \\
        --output "original_en.docx"

Supports:
    - DOCX → DOCX (python-docx clone-replace)
    - PDF → PDF (PyMuPDF redact + insert)
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Text normalisation helpers
# ---------------------------------------------------------------------------

_WHITESPACE = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """Collapse whitespace and strip for fuzzy matching."""
    return _WHITESPACE.sub(" ", text).strip()


def _similarity(a: str, b: str) -> float:
    """Simple token-overlap ratio for paragraph matching."""
    if not a or not b:
        return 0.0
    a_norm = _normalise(a).lower()
    b_norm = _normalise(b).lower()
    if a_norm == b_norm:
        return 1.0
    tokens_a = set(a_norm.split())
    tokens_b = set(b_norm.split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    return len(intersection) / max(len(tokens_a), len(tokens_b))


# ---------------------------------------------------------------------------
# EJV JSON block helpers
# ---------------------------------------------------------------------------

def _get_block_text(block: dict, lang: str) -> str:
    """Extract text for a given language from an EJV block."""
    val = block.get(lang)
    if val is None:
        return ""
    if isinstance(val, list):
        return "\n".join(str(item) for item in val)
    return str(val)


def _get_block_source_text(block: dict) -> str:
    """Get the source (vn) text from a block — the original content."""
    return _get_block_text(block, "vn")


def _get_table_cells_flat(block: dict, lang: str) -> list[str]:
    """Flatten table headers + rows for a given language."""
    cells = []
    headers_raw = block.get("headers", {})
    rows_raw = block.get("rows", {})

    if isinstance(headers_raw, dict):
        headers = headers_raw.get(lang, headers_raw.get("vn", []))
    elif isinstance(headers_raw, list):
        headers = headers_raw
    else:
        headers = []

    if isinstance(rows_raw, dict):
        rows = rows_raw.get(lang, rows_raw.get("vn", []))
    elif isinstance(rows_raw, list):
        rows = rows_raw
    else:
        rows = []

    cells.extend(str(h) for h in headers)
    for row in rows:
        if isinstance(row, list):
            cells.extend(str(c) for c in row)
        else:
            cells.append(str(row))
    return cells


# ---------------------------------------------------------------------------
# Build translation mapping from EJV JSON blocks
# ---------------------------------------------------------------------------

_ALL_LANGS = ("vn", "en", "ja")


def _build_text_mapping(blocks: list[dict], lang: str) -> dict[str, str]:
    """Build a mapping from source text → translated text.

    Keys are normalised text in ALL available languages (vn, en, ja) so that
    matching works regardless of the source document's language. Values are
    the target language text.

    For example, if the source DOCX is in Japanese and we want EN output:
    - ja_text → en_text (matches against the Japanese text in the file)
    - vn_text → en_text (fallback if extract matched Vietnamese)
    """
    mapping: dict[str, str] = {}
    for block in blocks:
        btype = block.get("type", "")
        dst = _get_block_text(block, lang)
        if not dst:
            continue

        # Add mapping from every available language as key → target as value
        for src_lang in _ALL_LANGS:
            if src_lang == lang:
                continue  # Don't map target to itself
            src = _get_block_text(block, src_lang)
            if src:
                mapping[_normalise(src)] = dst

        # Also add individual list items
        if btype in ("ul", "ol"):
            for src_lang in _ALL_LANGS:
                if src_lang == lang:
                    continue
                src_items = block.get(src_lang, [])
                dst_items = block.get(lang, [])
                if isinstance(src_items, list) and isinstance(dst_items, list):
                    for si, di in zip(src_items, dst_items):
                        si_str = str(si).strip()
                        di_str = str(di).strip()
                        if si_str and di_str:
                            mapping[_normalise(si_str)] = di_str

    return mapping


def _build_table_cell_mapping(blocks: list[dict], lang: str) -> dict[str, str]:
    """Build cell-level mapping for tables from EJV blocks.

    Like _build_text_mapping, tries all languages as keys for source matching.
    """
    mapping: dict[str, str] = {}
    for block in blocks:
        if block.get("type") not in ("table", "meta_table"):
            continue
        if block.get("type") == "meta_table":
            items = block.get("items", [])
            for item in items:
                for key in ("label", "value"):
                    raw = item.get(key, {})
                    if isinstance(raw, dict):
                        dst = str(raw.get(lang, "")).strip()
                        if not dst:
                            continue
                        # Add mapping from all other languages
                        for src_lang in _ALL_LANGS:
                            if src_lang == lang:
                                continue
                            src = str(raw.get(src_lang, "")).strip()
                            if src and src != dst:
                                mapping[_normalise(src)] = dst
                    else:
                        pass  # Literal string — same across languages
        else:
            # Standard table: map cells from all source languages
            dst_cells = _get_table_cells_flat(block, lang)
            for src_lang in _ALL_LANGS:
                if src_lang == lang:
                    continue
                src_cells = _get_table_cells_flat(block, src_lang)
                for sc, dc in zip(src_cells, dst_cells):
                    sc_str = sc.strip()
                    dc_str = dc.strip()
                    if sc_str and dc_str and sc_str != dc_str:
                        mapping[_normalise(sc_str)] = dc_str
    return mapping


def _find_translation(text: str, mapping: dict[str, str], threshold: float = 0.70) -> Optional[str]:
    """Find the best translation for a piece of text using fuzzy matching."""
    norm = _normalise(text)
    if not norm:
        return None

    # Exact match first
    if norm in mapping:
        return mapping[norm]

    # Try case-insensitive exact
    norm_lower = norm.lower()
    for key, val in mapping.items():
        if key.lower() == norm_lower:
            return val

    # Fuzzy match
    best_score = 0.0
    best_val = None
    for key, val in mapping.items():
        score = _similarity(norm, key)
        if score > best_score:
            best_score = score
            best_val = val

    if best_score >= threshold and best_val is not None:
        return best_val
    return None


# =========================================================================
# DOCX Clone-Replace Engine
# =========================================================================

def _replace_paragraph_text(paragraph, new_text: str) -> None:
    """Replace paragraph text while preserving the first run's formatting.

    Strategy: keep the first run with its formatting and set its text to the
    full new content, then remove all subsequent runs. This preserves font,
    size, bold, italic, color, and other character-level formatting from the
    original first run.
    """
    if not paragraph.runs:
        # No runs — create one
        paragraph.add_run(new_text)
        return

    # Preserve first run's formatting, set new text
    first_run = paragraph.runs[0]
    first_run.text = new_text

    # Remove subsequent runs
    for run in paragraph.runs[1:]:
        run._element.getparent().remove(run._element)


def _replace_cell_text(cell, new_text: str) -> None:
    """Replace cell text while preserving formatting."""
    if cell.paragraphs:
        _replace_paragraph_text(cell.paragraphs[0], new_text)
        # Remove extra paragraphs
        for p in cell.paragraphs[1:]:
            p._element.getparent().remove(p._element)


def preserve_docx(
    source_path: Path,
    blocks: list[dict],
    lang: str,
    output_path: Path,
) -> Path:
    """Clone a DOCX file and replace text in-place with translated content.

    Preserves: styles, fonts, margins, page breaks, headers/footers, images,
    shapes, table borders, cell shading, merged cells.

    Args:
        source_path: Path to original DOCX file
        blocks: EJV JSON blocks with translations
        lang: Target language code ('en' or 'ja')
        output_path: Where to save the translated copy

    Returns:
        Path to the generated file
    """
    from docx import Document

    # Build translation mappings
    text_map = _build_text_mapping(blocks, lang)
    cell_map = _build_table_cell_mapping(blocks, lang)
    all_map = {**text_map, **cell_map}

    # Open original document (clone it by loading)
    doc = Document(str(source_path))

    replaced = 0
    skipped = 0

    # Replace paragraphs
    for paragraph in doc.paragraphs:
        original = paragraph.text.strip()
        if not original:
            continue
        translation = _find_translation(original, all_map)
        if translation:
            _replace_paragraph_text(paragraph, translation)
            replaced += 1
        else:
            skipped += 1

    # Replace table cells
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                original = cell.text.strip()
                if not original:
                    continue
                translation = _find_translation(original, all_map)
                if translation:
                    _replace_cell_text(cell, translation)
                    replaced += 1

    # Replace header/footer text
    for section in doc.sections:
        for header_footer in [section.header, section.footer]:
            if header_footer and header_footer.is_linked_to_previous is False:
                for paragraph in header_footer.paragraphs:
                    original = paragraph.text.strip()
                    if not original:
                        continue
                    translation = _find_translation(original, all_map)
                    if translation:
                        _replace_paragraph_text(paragraph, translation)
                        replaced += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    print(f"✅ Layout-preserved DOCX ({lang.upper()}): {output_path}")
    print(f"   Replaced: {replaced} blocks | Kept original: {skipped} blocks")
    return output_path


# =========================================================================
# PDF Clone-Replace Engine
# =========================================================================

def _select_font(lang: str) -> str:
    """Select a system font that supports the target language."""
    import os

    if lang in ("ja",):
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "C:\\Windows\\Fonts\\msgothic.ttc",
            "C:\\Windows\\Fonts\\YuGothM.ttc",
        ]
    elif lang in ("zh", "zh-cn", "zh-tw", "ko"):
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "C:\\Windows\\Fonts\\simsun.ttc",
        ]
    else:
        # Latin-script languages (en, etc.)
        candidates = [
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\times.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            return path

    # Fallback: let PyMuPDF use built-in Helvetica
    return ""


def preserve_pdf(
    source_path: Path,
    blocks: list[dict],
    lang: str,
    output_path: Path,
) -> Path:
    """Clone a PDF file and replace text in-place with translated content.

    Uses PyMuPDF's redaction API: for each text block, redact the original
    text (whitening the area) and insert the translated text at the same
    position with matching font size.

    Preserves: layout, images, borders, fills, page structure.

    Args:
        source_path: Path to original PDF file
        blocks: EJV JSON blocks with translations
        lang: Target language code ('en' or 'ja')
        output_path: Where to save the translated copy

    Returns:
        Path to the generated file
    """
    import pymupdf

    # Build translation mappings
    text_map = _build_text_mapping(blocks, lang)
    cell_map = _build_table_cell_mapping(blocks, lang)
    all_map = {**text_map, **cell_map}

    doc = pymupdf.open(str(source_path))
    font_path = _select_font(lang)

    replaced = 0
    skipped = 0

    for page in doc:
        # Get text blocks with bounding boxes: (x0, y0, x1, y1, text, block_no, block_type)
        text_blocks = page.get_text("blocks")
        text_blocks.sort(key=lambda b: (b[1], b[0]))

        redactions = []  # Collect (rect, translated_text, fontsize) tuples

        for block in text_blocks:
            if block[6] != 0:  # Image block
                continue
            original_text = block[4].strip()
            if not original_text:
                continue

            # Clean newlines for matching
            match_text = " ".join(original_text.split())
            translation = _find_translation(match_text, all_map)

            if translation:
                rect = pymupdf.Rect(block[0], block[1], block[2], block[3])
                # Estimate font size from block height and line count
                lines = original_text.count("\n") + 1
                block_height = rect.height
                fontsize = max(6.0, min(block_height / lines * 0.75, 14.0))
                redactions.append((rect, translation, fontsize))
                replaced += 1
            else:
                skipped += 1

        # Apply redactions: first add all, then apply at once
        for rect, translated_text, fontsize in redactions:
            # Add redaction annotation (marks the area to be cleared)
            page.add_redact_annot(
                rect,
                text="",  # Clear text in the annot itself
                fill=(1, 1, 1),  # White fill
            )

        # Apply all redactions at once (whiten the areas)
        if redactions:
            page.apply_redactions()

            # Now insert translated text at each position
            for rect, translated_text, fontsize in redactions:
                # Shrink rect slightly to avoid bleeding into borders
                inner_rect = pymupdf.Rect(
                    rect.x0 + 1, rect.y0 + 1,
                    rect.x1 - 1, rect.y1 - 1,
                )

                # Try to fit text, reduce font size if necessary
                attempts = 0
                current_size = fontsize
                while attempts < 5:
                    rc = page.insert_textbox(
                        inner_rect,
                        translated_text,
                        fontsize=current_size,
                        fontname="custom" if font_path else "helv",
                        fontfile=font_path if font_path else None,
                        align=pymupdf.TEXT_ALIGN_LEFT,
                    )
                    if rc >= 0:  # Text fits
                        break
                    current_size *= 0.85  # Reduce by 15%
                    attempts += 1

                if rc < 0:
                    # Still doesn't fit — use smallest size
                    page.insert_textbox(
                        inner_rect,
                        translated_text,
                        fontsize=max(5.0, current_size),
                        fontname="custom" if font_path else "helv",
                        fontfile=font_path if font_path else None,
                        align=pymupdf.TEXT_ALIGN_LEFT,
                    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path), garbage=4, deflate=True)
    doc.close()
    print(f"✅ Layout-preserved PDF ({lang.upper()}): {output_path}")
    print(f"   Replaced: {replaced} blocks | Kept original: {skipped} blocks")
    return output_path


# =========================================================================
# CLI
# =========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate layout-preserved translations from EJV JSON blocks."
    )
    parser.add_argument(
        "--source", required=True, type=Path,
        help="Original source file (PDF or DOCX)"
    )
    parser.add_argument(
        "--blocks", required=True, type=Path,
        help="EJV JSON file containing translated blocks (merged_ejv.json)"
    )
    parser.add_argument(
        "--lang", required=True, choices=["vn", "en", "ja"],
        help="Target language to export"
    )
    parser.add_argument(
        "--output", required=True, type=Path,
        help="Output file path (same format as source)"
    )
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"Error: Source file not found: {args.source}", file=sys.stderr)
        return 1
    if not args.blocks.is_file():
        print(f"Error: Blocks file not found: {args.blocks}", file=sys.stderr)
        return 1

    with open(args.blocks, "r", encoding="utf-8") as f:
        blocks = json.load(f)

    ext = args.source.suffix.lower()
    if ext == ".docx":
        preserve_docx(args.source, blocks, args.lang, args.output)
    elif ext == ".pdf":
        preserve_pdf(args.source, blocks, args.lang, args.output)
    else:
        print(f"Error: Unsupported format '{ext}'. Use .docx or .pdf", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
