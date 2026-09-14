"""Typst Overlay Engine for EJV Translate.

Provides 1:1 In-Place PDF Layout Preservation using Typst typesetting
and PyMuPDF clean vector redaction.

Key Innovations (adapted from RetainPDF):
1. Binary-search auto-font-scaling (`pdftr_fit_size`) ensuring translated text
   fits precisely inside original bounding boxes without overflowing or collision.
2. Full Vietnamese, Japanese, and English Unicode diacritic support via native macOS/Linux system fonts.
3. Clean background redaction preserving underlying graphics, photos, and table borders.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf


# ---------------------------------------------------------------------------
# Typst Helper Code & Templates
# ---------------------------------------------------------------------------

def _escape_typst_content(text: str) -> str:
    """Escape Typst syntax characters inside content blocks."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\\", "\\\\")
    replacements = [
        ("#", "\\#"),
        ("$", "\\$"),
        ("[", "\\["),
        ("]", "\\]"),
        ("<", "\\<"),
        (">", "\\>"),
        ("@", "\\@"),
        ("*", "\\*"),
        ("_", "\\_"),
        ("`", "\\`"),
    ]
    for char, escaped in replacements:
        text = text.replace(char, escaped)
    return text


def _build_typst_page_source(
    page_width_pt: float,
    page_height_pt: float,
    blocks: List[Dict[str, Any]],
    lang: str = "vi",
) -> str:
    """Generates complete Typst source for an overlay page."""
    font_families = [
        "Arial",
        "Helvetica Neue",
        "SF Pro Text",
        "Times New Roman",
        "PingFang SC",
        "Hiragino Sans",
    ]
    fonts_str = ", ".join(f'"{f}"' for f in font_families)

    lines = [
        "// Auto-generated Typst Overlay by EJV Translate",
        f"#set page(",
        f"  width: {page_width_pt:.2f}pt,",
        f"  height: {page_height_pt:.2f}pt,",
        f"  margin: (x: 0pt, y: 0pt),",
        f")",
        f'#set text(font: ({fonts_str}), lang: "{lang}")',
        "",
        "// --- Binary Search Font Auto-Fitting Helper Macro ---",
        "#let pdftr_fit_size(lo, hi, eps, fits) = {",
        "  if hi - lo <= eps { lo }",
        "  else {",
        "    let mid = lo + (hi - lo) / 2",
        "    if fits(mid) { pdftr_fit_size(mid, hi, eps, fits) }",
        "    else { pdftr_fit_size(lo, mid, eps, fits) }",
        "  }",
        "}",
        "#let pdftr_floor_size(a, b) = calc.max(a, b)",
        "",
        "#let pdftr_fit_text(",
        "  body,",
        "  max_size: 11pt,",
        "  min_size: 4.5pt,",
        "  max_leading: 0.55em,",
        "  min_leading: 0.20em,",
        "  fit_height: none,",
        '  weight: "regular",',
        '  style: "normal",',
        "  align_type: left,",
        "  fill_color: black,",
        "  eps: 0.08pt,",
        ") = {",
        "  layout(size => {",
        "    let allowed_h = if fit_height == none { size.height } else { calc.min(size.height, fit_height) }",
        "    let render_fn(text_size, leading) = block(width: size.width)[#{",
        "      set text(size: text_size, weight: weight, style: style, fill: fill_color)",
        "      set par(leading: leading, justify: false)",
        "      set align(align_type)",
        "      body",
        "    }]",
        "    let fits(text_size, leading) = measure(width: size.width, render_fn(text_size, leading)).height <= allowed_h",
        "",
        "    if fits(max_size, max_leading) {",
        "      render_fn(max_size, max_leading)",
        "    } else {",
        "      let chosen_size = pdftr_fit_size(min_size, max_size, eps, size_pt => fits(size_pt, min_leading))",
        "      let final_size = if fits(chosen_size, min_leading) {",
        "        chosen_size",
        "      } else {",
        "        let emerg = pdftr_floor_size(min_size * 0.80, 4.0pt)",
        "        if fits(emerg, min_leading * 0.80) { emerg } else { 4.0pt }",
        "      }",
        "      render_fn(final_size, min_leading)",
        "    }",
        "  })",
        "}",
        "",
        "// --- Content Overlay Blocks ---",
    ]

    for i, block in enumerate(blocks):
        bbox = block.get("bbox")
        if not bbox or len(bbox) < 4:
            continue

        x0, y0, x1, y1 = bbox
        width = max(6.0, x1 - x0)
        height = max(6.0, y1 - y0)

        raw_text = block.get("text", "").strip()
        if not raw_text:
            continue

        escaped_text = _escape_typst_content(raw_text)

        orig_font_size = block.get("font_size")
        if not orig_font_size:
            line_count = max(1, raw_text.count("\n") + 1)
            orig_font_size = max(7.0, (height / line_count) * 0.75)

        max_size = float(orig_font_size)
        min_size = max(4.0, min(7.5, max_size * 0.45))

        weight = "bold" if block.get("weight") in ("bold", "700", "800", "900") else "regular"
        style = "italic" if block.get("style") in ("italic", "oblique") else "normal"

        align_map = {"center": "center", "right": "right", "justify": "left", "left": "left"}
        align_type = align_map.get(str(block.get("align", "left")).lower(), "left")

        color_hex = str(block.get("color", "#000000")).strip()
        if not color_hex.startswith("#") or len(color_hex) not in (4, 7):
            color_hex = "#000000"

        lines.append(f"// Block {i}: [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}]")
        lines.append(f"#place(")
        lines.append(f"  top + left,")
        lines.append(f"  dx: {x0:.2f}pt,")
        lines.append(f"  dy: {y0:.2f}pt,")
        lines.append(f"  box(")
        lines.append(f"    width: {width:.2f}pt,")
        lines.append(f"    height: {height:.2f}pt,")
        lines.append(f"    clip: true,")
        lines.append(f"    pdftr_fit_text(")
        lines.append(f"      [{escaped_text}],")
        lines.append(f"      max_size: {max_size:.2f}pt,")
        lines.append(f"      min_size: {min_size:.2f}pt,")
        lines.append(f"      fit_height: {height:.2f}pt,")
        lines.append(f'      weight: "{weight}",')
        lines.append(f'      style: "{style}",')
        lines.append(f"      align_type: {align_type},")
        lines.append(f'      fill_color: rgb("{color_hex}"),')
        lines.append(f"    )")
        lines.append(f"  )")
        lines.append(f")")
        lines.append("")

    return "\n".join(lines)


def is_typst_available() -> bool:
    """Checks if Typst binary is available on system PATH or standard locations."""
    if shutil.which("typst"):
        return True
    for p in ["/opt/homebrew/bin/typst", "/usr/local/bin/typst"]:
        if Path(p).is_file():
            return True
    return False


def get_typst_bin() -> str:
    """Resolves path to typst binary."""
    bin_path = shutil.which("typst")
    if bin_path:
        return bin_path
    for p in ["/opt/homebrew/bin/typst", "/usr/local/bin/typst"]:
        if Path(p).is_file():
            return p
    raise FileNotFoundError("Typst executable not found. Install with: brew install typst")


# ---------------------------------------------------------------------------
# Text Matching & Extraction
# ---------------------------------------------------------------------------

_WHITESPACE = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """Collapses whitespace and lowercases string."""
    return _WHITESPACE.sub(" ", text).strip().lower()


def _similarity(a: str, b: str) -> float:
    """Token-overlap ratio for fuzzy matching."""
    if not a or not b:
        return 0.0
    na, nb = _normalise(a), _normalise(b)
    if na == nb:
        return 1.0
    ta, tb = set(na.split()), set(nb.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _compact(text: str) -> str:
    """Removes all whitespace and lowercases for CJK and dense text matching."""
    return re.sub(r"\s+", "", text).strip().lower()


def build_translation_map(blocks: list[dict], target_lang: str) -> tuple[dict[str, str], dict[str, str]]:
    """Builds normal and compact mappings from source text (ja, en, vn) to target translation."""
    norm_map: dict[str, str] = {}
    compact_map: dict[str, str] = {}

    def _add_pair(src_text: str, tgt_text: str):
        if not src_text or not tgt_text or not isinstance(src_text, str) or not isinstance(tgt_text, str):
            return
        s_norm = _normalise(src_text)
        s_comp = _compact(src_text)
        if s_norm:
            norm_map[s_norm] = tgt_text
        if s_comp:
            compact_map[s_comp] = tgt_text

    for block in blocks:
        # 1. Standard string fields
        target = block.get(target_lang)
        if target and isinstance(target, str):
            for lang_code in ("ja", "en", "vn"):
                if lang_code == target_lang:
                    continue
                src = block.get(lang_code)
                if src and isinstance(src, str):
                    _add_pair(src, target)

        # 2. Lists (items or list field)
        items_tgt = block.get(target_lang) if isinstance(block.get(target_lang), list) else block.get("items")
        for lang_code in ("ja", "en", "vn"):
            if lang_code == target_lang:
                continue
            items_src = block.get(lang_code) if isinstance(block.get(lang_code), list) else []
            if items_src and items_tgt and len(items_src) == len(items_tgt):
                for s, t in zip(items_src, items_tgt):
                    _add_pair(str(s), str(t))

        # 3. Tables (headers and rows)
        if block.get("type") == "table":
            headers_d = block.get("headers", {})
            rows_d = block.get("rows", {})
            if isinstance(headers_d, dict):
                h_tgt = headers_d.get(target_lang, [])
                for lang_code in ("ja", "en", "vn"):
                    if lang_code == target_lang:
                        continue
                    h_src = headers_d.get(lang_code, [])
                    if len(h_src) == len(h_tgt):
                        for s, t in zip(h_src, h_tgt):
                            _add_pair(str(s), str(t))
            if isinstance(rows_d, dict):
                r_tgt = rows_d.get(target_lang, [])
                for lang_code in ("ja", "en", "vn"):
                    if lang_code == target_lang:
                        continue
                    r_src = rows_d.get(lang_code, [])
                    if len(r_src) == len(r_tgt):
                        for row_s, row_t in zip(r_src, r_tgt):
                            if len(row_s) == len(row_t):
                                for s, t in zip(row_s, row_t):
                                    _add_pair(str(s), str(t))

        # 4. Meta tables
        if block.get("type") == "meta_table":
            for it in block.get("items", []):
                lbl = it.get("label", {})
                val = it.get("value", {})
                if isinstance(lbl, dict):
                    t_lbl = lbl.get(target_lang)
                    for lang_code in ("ja", "en", "vn"):
                        if lang_code != target_lang and lbl.get(lang_code) and t_lbl:
                            _add_pair(lbl.get(lang_code), t_lbl)
                if isinstance(val, dict):
                    t_val = val.get(target_lang)
                    for lang_code in ("ja", "en", "vn"):
                        if lang_code != target_lang and val.get(lang_code) and t_val:
                            _add_pair(val.get(lang_code), t_val)

    return norm_map, compact_map



def find_best_translation(
    raw_text: str,
    norm_map: dict[str, str],
    compact_map: dict[str, str],
    threshold: float = 0.50,
) -> Optional[str]:
    """Looks up translation via normalized exact, compact CJK, or token fuzzy match."""
    clean = raw_text.strip()
    if not clean:
        return None

    norm = _normalise(clean)
    if norm in norm_map:
        return norm_map[norm]

    comp = _compact(clean)
    if comp in compact_map:
        return compact_map[comp]

    # Substring match on compact representation (common for OCR fragmented lines)
    if len(comp) >= 4:
        for k_comp, target in compact_map.items():
            if len(k_comp) >= 4:
                if comp in k_comp or k_comp in comp:
                    ratio = min(len(comp), len(k_comp)) / max(len(comp), len(k_comp))
                    if ratio >= 0.50:
                        return target

    # Token overlap fuzzy match for Latin/spaced text
    best_score = 0.0
    best_target = None
    for src_norm, target in norm_map.items():
        score = _similarity(norm, src_norm)
        if score > best_score:
            best_score = score
            best_target = target

    if best_score >= threshold:
        return best_target

    return None


# ---------------------------------------------------------------------------
# Main Overlay Pipeline
# ---------------------------------------------------------------------------

def preserve_pdf_typst(
    source_pdf_path: Path,
    blocks: list[dict],
    lang: str,
    output_pdf_path: Path,
) -> Path:
    """Translates PDF in-place preserving 1:1 layout via Typst & PyMuPDF.
    
    Args:
        source_pdf_path: Original input PDF.
        blocks: EJV JSON blocks with translations.
        lang: Target language code ('vi', 'en', 'ja').
        output_pdf_path: Destination output path.
        
    Returns:
        Path to generated output PDF.
    """
    typst_bin = get_typst_bin()
    norm_map, compact_map = build_translation_map(blocks, target_lang=lang)

    doc_src = pymupdf.open(source_pdf_path)
    temp_dir = Path(tempfile.mkdtemp(prefix="ejv_typst_"))

    try:
        overlay_doc = pymupdf.open()
        pages_bboxes: dict[int, list[list[float]]] = {}

        for page_idx in range(len(doc_src)):
            page = doc_src[page_idx]
            w = page.rect.width
            h = page.rect.height

            # Extract blocks from page via get_text("dict")
            text_dict = page.get_text("dict")
            render_blocks = []
            page_bboxes = []

            for b in text_dict.get("blocks", []):
                if b.get("type") != 0 or "lines" not in b:
                    continue

                bx = b.get("bbox")
                if not bx or len(bx) < 4:
                    continue

                # Combine lines into full block text
                block_text = " ".join(
                    "".join(s.get("text", "") for s in l.get("spans", []))
                    for l in b.get("lines", [])
                ).strip()

                if not block_text:
                    continue

                # Find translation
                translated = find_best_translation(block_text, norm_map, compact_map)
                if not translated:
                    # If block-level did not match, try line-level matching for tables and multi-part blocks
                    if len(b.get("lines", [])) > 1:
                        for l in b.get("lines", []):
                            line_text = "".join(s.get("text", "") for s in l.get("spans", [])).strip()
                            if not line_text:
                                continue
                            line_trans = find_best_translation(line_text, norm_map, compact_map)
                            if line_trans:
                                lbx = l.get("bbox")
                                if not lbx or len(lbx) < 4:
                                    continue
                                sp = l["spans"][0]
                                fs = sp.get("size", 10.0)
                                fl = sp.get("flags", 0)
                                is_b = bool(fl & 16) or ("bold" in sp.get("font", "").lower())
                                is_it = bool(fl & 2) or ("italic" in sp.get("font", "").lower())
                                c_int = sp.get("color", 0)
                                c_hex = f"#{c_int:06x}" if c_int else "#000000"
                                pad_box = [lbx[0], lbx[1], lbx[2], min(h, lbx[3] + 1.5)]
                                render_blocks.append({
                                    "bbox": pad_box,
                                    "text": line_trans,
                                    "font_size": fs,
                                    "weight": "bold" if is_b else "regular",
                                    "style": "italic" if is_it else "normal",
                                    "align": "left",
                                    "color": c_hex,
                                })
                                page_bboxes.append(pad_box)
                    continue

                # Detect font attributes from first span
                first_span = b["lines"][0]["spans"][0]
                font_size = first_span.get("size", 10.0)
                flags = first_span.get("flags", 0)
                is_bold = bool(flags & 16) or ("bold" in first_span.get("font", "").lower())
                is_italic = bool(flags & 2) or ("italic" in first_span.get("font", "").lower())

                # Color
                color_int = first_span.get("color", 0)
                color_hex = f"#{color_int:06x}" if color_int else "#000000"

                # Check alignment based on position
                align = "left"
                mid_x = (bx[0] + bx[2]) / 2
                if abs(mid_x - (w / 2)) < 30 and (bx[2] - bx[0]) < (w * 0.8):
                    align = "center"
                elif bx[0] > (w * 0.65):
                    align = "right"

                # Padding
                padded_bbox = [bx[0], bx[1], bx[2], min(h, bx[3] + 1.5)]

                render_blocks.append({
                    "bbox": padded_bbox,
                    "text": translated,
                    "font_size": font_size,
                    "weight": "bold" if is_bold else "regular",
                    "style": "italic" if is_italic else "normal",
                    "align": align,
                    "color": color_hex,
                })
                page_bboxes.append(padded_bbox)

            pages_bboxes[page_idx] = page_bboxes

            # Build and compile Typst overlay for this page
            typ_code = _build_typst_page_source(w, h, render_blocks, lang=lang)
            typ_file = temp_dir / f"page_{page_idx}.typ"
            pdf_page_overlay = temp_dir / f"page_{page_idx}.pdf"

            typ_file.write_text(typ_code, encoding="utf-8")

            # Compile
            cmd = [typst_bin, "compile", str(typ_file), str(pdf_page_overlay)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"Typst compilation failed for page {page_idx}:\n{res.stderr}")

            single_page_doc = pymupdf.open(pdf_page_overlay)
            overlay_doc.insert_pdf(single_page_doc)
            single_page_doc.close()

        # Synthesis onto doc_src
        for page_idx in range(len(doc_src)):
            page_src = doc_src[page_idx]
            bboxes = pages_bboxes.get(page_idx, [])
            if not bboxes or page_idx >= len(overlay_doc):
                continue

            # 1. Clean links
            for link in page_src.get_links():
                l_rect = link.get("from")
                if l_rect:
                    for b in bboxes:
                        if l_rect.intersects(pymupdf.Rect(b)):
                            page_src.delete_link(link)
                            break

            # 2. Add redactions & cover background pixels
            for b in bboxes:
                rect = pymupdf.Rect(b)
                page_src.add_redact_annot(rect, fill=(1.0, 1.0, 1.0))
                page_src.draw_rect(rect, color=None, fill=(1.0, 1.0, 1.0), overlay=True)

            try:
                page_src.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
            except Exception:
                page_src.apply_redactions()

            # 3. Apply Typst overlay on top
            page_src.show_pdf_page(page_src.rect, overlay_doc, page_idx, overlay=True)

        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        doc_src.save(str(output_pdf_path), garbage=4, deflate=True)

    finally:
        doc_src.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"✅ Typst 1:1 Layout-preserved PDF ({lang.upper()}): {output_pdf_path}")
    return output_pdf_path
