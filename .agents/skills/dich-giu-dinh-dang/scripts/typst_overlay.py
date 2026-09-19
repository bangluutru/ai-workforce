"""Typst Overlay Engine for EJV Translate.

Provides 1:1 In-Place PDF Layout Preservation using Typst typesetting
and PyMuPDF clean vector redaction.

Key Innovations (adapted from RetainPDF):
1. Binary-search auto-font-scaling (`pdftr_fit_size`) ensuring translated text
   fits precisely inside original bounding boxes without overflowing or collision.
2. Full Vietnamese, Japanese, and English Unicode diacritic support via native macOS/Linux system fonts.
3. Clean background redaction preserving underlying graphics, photos, and table borders.
4. Diagram-Aware region detection via vector analysis (v2.1).
5. 2D overlap prevention and border-safe redaction margins (v2.1).
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

# Module-level log for smart clip warnings
_clip_warnings: list[dict] = []

# Page Mode Classification constants (Smart Reflow v4.0)
PAGE_MODE_TEXT_ONLY = "TEXT_ONLY"
PAGE_MODE_MIXED = "MIXED"
PAGE_MODE_CONSTRAINED = "CONSTRAINED"

# ---------------------------------------------------------------------------
# Multi-Tier Font Scaling Strategy (v4.0 Smart Reflow)
# ---------------------------------------------------------------------------

# Font tier classification constants
TIER_HEADING = "heading"
TIER_BODY = "body"
TIER_TABLE_CELL = "table_cell"
TIER_DIAGRAM_LABEL = "diagram_label"
TIER_VERTICAL = "vertical"

# Per-tier font constraints (pt)
FONT_TIERS = {
    TIER_HEADING: {
        "min_size": 8.0,    # Headings should stay readable
        "max_scale": 1.0,   # Use original font size as max
        "min_leading": 0.25,
        "max_leading": 0.55,
    },
    TIER_BODY: {
        "min_size": 7.0,    # Body text: readable floor
        "max_scale": 1.0,
        "min_leading": 0.25,
        "max_leading": 0.55,
    },
    TIER_TABLE_CELL: {
        "min_size": 4.5,    # Table cells can shrink more
        "max_scale": 0.95,  # Slight reduction from original
        "min_leading": 0.18,
        "max_leading": 0.45,
    },
    TIER_DIAGRAM_LABEL: {
        "min_size": 4.0,    # Diagram labels: tightest fit allowed
        "max_scale": 0.85,
        "min_leading": 0.15,
        "max_leading": 0.40,
    },
    TIER_VERTICAL: {
        "min_size": 4.0,
        "max_scale": 0.90,
        "min_leading": 0.20,
        "max_leading": 0.45,
    },
}


def _classify_block_tier(
    block: Dict[str, Any],
    page_width: float = 595.0,
) -> str:
    """Classify a render block into a font tier based on its metadata.

    Classification rules (priority order):
    1. Explicit is_vertical → VERTICAL
    2. Explicit is_in_diagram → DIAGRAM_LABEL
    3. is_table_cell flag → TABLE_CELL
    4. Heuristic: bold + short text + wide bbox → HEADING
    5. Default → BODY
    """
    if block.get("is_vertical"):
        return TIER_VERTICAL
    if block.get("is_in_diagram"):
        return TIER_DIAGRAM_LABEL
    if block.get("is_table_cell"):
        return TIER_TABLE_CELL

    # Heuristic heading detection
    bbox = block.get("bbox", [0, 0, 100, 20])
    b_w = bbox[2] - bbox[0]
    b_h = bbox[3] - bbox[1]
    text = block.get("text", "")
    weight = block.get("weight", "regular")
    font_size = block.get("font_size", 10.0)
    line_count = max(1, text.count("\n") + 1)

    # Heading indicators: bold, large font, short text, spanning width
    is_bold = weight in ("bold", "700", "800", "900")
    is_large_font = font_size >= 11.0
    is_short = line_count <= 2 and len(text) < 120
    is_wide = b_w > page_width * 0.35

    if is_bold and is_short and (is_large_font or is_wide):
        return TIER_HEADING
    if is_large_font and is_short and b_h < 30.0:
        return TIER_HEADING

    return TIER_BODY


def _compute_body_floor_size(
    render_blocks: List[Dict[str, Any]],
) -> float:
    """Compute a unified minimum font size for BODY blocks on a page.

    Strategy: collect all BODY blocks' original font sizes, then set the
    floor to 75% of the median — ensuring visual consistency while still
    allowing some shrinkage for tight fits.
    """
    body_sizes = [
        b.get("font_size", 10.0)
        for b in render_blocks
        if b.get("block_tier") == TIER_BODY
    ]
    if not body_sizes:
        return 7.0

    body_sizes.sort()
    median = body_sizes[len(body_sizes) // 2]
    # Floor = 75% of median, but never below 6.5pt for readability
    return max(6.5, median * 0.75)


# ---------------------------------------------------------------------------
# Typst Helper Code & Templates
# ---------------------------------------------------------------------------

def _sample_bg_color(page: pymupdf.Page, rect: pymupdf.Rect) -> tuple[float, float, float]:
    """Sample background color around bounding box edges to match cell background."""
    try:
        pix = page.get_pixmap(clip=rect, dpi=72)
        if pix.width < 1 or pix.height < 1:
            return (1.0, 1.0, 1.0)
        colors = []
        w, h = pix.width, pix.height
        for x in range(w):
            colors.append(pix.pixel(x, 0)[:3])
            colors.append(pix.pixel(x, h - 1)[:3])
        for y in range(h):
            colors.append(pix.pixel(0, y)[:3])
            colors.append(pix.pixel(w - 1, y)[:3])
        # Filter out accidental MuPDF unapplied redact annotation red border (e.g. #fd0f10)
        filtered_colors = [c for c in colors if not (c[0] > 230 and c[1] < 40 and c[2] < 40)]
        if not filtered_colors:
            filtered_colors = colors
        from collections import Counter
        most_common = Counter(filtered_colors).most_common(1)[0][0]
        return tuple(c / 255.0 for c in most_common)
    except Exception:
        return (1.0, 1.0, 1.0)


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
        ("~", "\\~"),
    ]
    for char, escaped in replacements:
        text = text.replace(char, escaped)
    return text


def _is_multiline_block(
    block: Dict[str, Any],
    raw_text: str = "",
    height: float = 0.0,
    orig_font_size: float = 10.0,
) -> bool:
    """Robust multiline detection for paragraph text."""
    if block.get("is_vertical"):
        return False
    if block.get("is_multiline") is not None:
        return bool(block["is_multiline"])
    if "\n" in raw_text:
        return True
    if len(block.get("lines", [])) > 1:
        return True
    if height >= orig_font_size * 1.35 and len(raw_text) > 15:
        return True
    return False


def _build_typst_page_source(
    page_width_pt: float,
    page_height_pt: float,
    blocks: List[Dict[str, Any]],
    continuation_blocks: Optional[List[Dict[str, Any]]] = None,
    lang: str = "vi",
) -> str:
    """Generates complete Typst source for an overlay page with Smart Reflow v4.0."""
    font_families = [
        "Arial",
        "Helvetica Neue",
        "SF Pro Text",
        "Times New Roman",
        "PingFang SC",
        "Hiragino Sans",
    ]
    fonts_str = ", ".join(f'"{f}"' for f in font_families)

    # Compute unified body floor for this page
    body_floor = _compute_body_floor_size(blocks)

    lines = [
        "// Auto-generated Typst Overlay by EJV Translate (v4.0 Smart Reflow)",
        f"#set page(",
        f"  width: {page_width_pt:.2f}pt,",
        f"  height: {page_height_pt:.2f}pt,",
        f"  margin: (x: 0pt, y: 0pt),",
        f"  fill: none,",
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
        "  is_multiline: false,",
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
        "    let fits(text_size, leading) = (",
        "      measure(width: size.width, render_fn(text_size, leading)).height <= (allowed_h + 1.0pt) and",
        "      (if not is_multiline { measure(text(size: text_size)[#body]).width <= (size.width + 0.5pt) } else { true })",
        "    )",
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

    def _render_block_list(blk_list: List[Dict[str, Any]], prefix: str = "Block"):
        for i, block in enumerate(blk_list):
            bbox = block.get("bbox")
            if not bbox or len(bbox) < 4:
                continue

            x0, y0, x1, y1 = bbox
            y0 = max(2.0, y0)  # Safe top boundary clamp
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

            # --- Multi-Tier Font Constraints ---
            tier = block.get("block_tier", TIER_BODY)
            tier_cfg = FONT_TIERS.get(tier, FONT_TIERS[TIER_BODY])

            max_size = float(orig_font_size) * tier_cfg["max_scale"]
            tier_min = tier_cfg["min_size"]

            if tier == TIER_BODY:
                min_size = max(tier_min, body_floor)
            elif tier == TIER_HEADING:
                min_size = max(tier_min, float(orig_font_size) * 0.70)
            else:
                min_size = tier_min

            min_leading_em = f"{tier_cfg['min_leading']:.2f}em"
            max_leading_em = f"{tier_cfg['max_leading']:.2f}em"

            weight = "bold" if block.get("weight") in ("bold", "700", "800", "900") else "regular"
            style = "italic" if block.get("style") in ("italic", "oblique") else "normal"

            align_map = {"center": "center", "right": "right", "justify": "left", "left": "left"}
            align_type = align_map.get(str(block.get("align", "left")).lower(), "left")

            color_hex = str(block.get("color", "#000000")).strip()
            if not color_hex.startswith("#") or len(color_hex) not in (4, 7):
                color_hex = "#000000"

            is_multi = _is_multiline_block(block, raw_text, height, float(orig_font_size))
            is_multi_str = "true" if is_multi else "false"

            if block.get("is_vertical"):
                vert_max = min(max_size, 9.0)
                vert_min = max(4.0, vert_max * 0.4)
                lines.append(f"// Vertical {prefix} {i} [tier={tier}]: [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}]")
                lines.append(f"#place(top + left, dx: {x0:.2f}pt, dy: {y0:.2f}pt, box(width: {width:.2f}pt, height: {height:.2f}pt, clip: true, align(center + horizon)[#rotate(-90deg, reflow: false)[#box(width: {height:.2f}pt, height: {width:.2f}pt, [#pdftr_fit_text([{escaped_text}], max_size: {vert_max:.2f}pt, min_size: {vert_min:.2f}pt, fit_height: {width:.2f}pt, is_multiline: false, weight: \"{weight}\", style: \"{style}\", align_type: center, fill_color: rgb(\"{color_hex}\"))])]]))")
                lines.append("")
                continue

            lines.append(f"// {prefix} {i} [tier={tier}]: [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}]")
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
            lines.append(f"      max_leading: {max_leading_em},")
            lines.append(f"      min_leading: {min_leading_em},")
            lines.append(f"      fit_height: {height:.2f}pt,")
            lines.append(f"      is_multiline: {is_multi_str},")
            lines.append(f'      weight: "{weight}",')
            lines.append(f'      style: "{style}",')
            lines.append(f"      align_type: {align_type},")
            lines.append(f'      fill_color: rgb("{color_hex}"),')
            lines.append(f"    )")
            lines.append(f"  )")
            lines.append(f")")
            lines.append("")

    _render_block_list(blocks, prefix="Block")

    if continuation_blocks:
        lines.append("#pagebreak()")
        lines.append("// --- Continuation Page (Adaptive Reflow) ---")
        h_block = next((b for b in blocks if b.get("bbox", [0, 0, 0, 0])[1] < 20.0), None)
        if h_block:
            h_esc = _escape_typst_content(h_block.get("text", "") + " (Continued)")
            lines.append(f"#place(top + left, dx: 12.34pt, dy: 10.00pt, text(size: 7.0pt, fill: rgb(\"#666666\"))[{h_esc}])")
        _render_block_list(continuation_blocks, prefix="ContBlock")

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
    """Removes all whitespace and formatting artifacts ($#|_) for robust CJK matching."""
    # In Japanese PDF vertical text fonts, the particle 'の' is often encoded as '$'
    text = text.replace("$", "の")
    return re.sub(r"[\s#\|_]+", "", text).strip().lower()


def build_translation_map(blocks: list[dict], target_lang: str) -> tuple[dict[str, str], dict[str, str]]:
    """Builds normal and compact mappings from source text (ja, en, vn) to target translation."""
    norm_map: dict[str, str] = {}
    compact_map: dict[str, str] = {}

    target_lang_canonical = "vi" if target_lang in ("vi", "vn") else target_lang.lower()

    def _get_field(b: dict, lang_code: str) -> Any:
        if lang_code in ("vi", "vn"):
            return b.get("vn") or b.get("vi") or b.get("text_vn") or b.get("text_vi")
        elif lang_code == "en":
            return b.get("en") or b.get("text_en")
        elif lang_code in ("ja", "jp"):
            return b.get("ja") or b.get("jp") or b.get("text_ja") or b.get("text")
        return b.get(lang_code)

    def _add_pair(src_text: str, tgt_text: str):
        if not src_text or not tgt_text or not isinstance(src_text, str) or not isinstance(tgt_text, str):
            return
        s_norm = _normalise(src_text)
        s_comp = _compact(src_text)
        if s_norm:
            norm_map[s_norm] = tgt_text
        if s_comp:
            compact_map[s_comp] = tgt_text

        # Also add line-by-line pairs if multiline
        if "\n" in src_text and "\n" in tgt_text:
            s_lines = [l.strip() for l in src_text.split("\n") if l.strip()]
            t_lines = [l.strip() for l in tgt_text.split("\n") if l.strip()]
            if len(s_lines) == len(t_lines):
                for sl, tl in zip(s_lines, t_lines):
                    sl_norm = _normalise(sl)
                    sl_comp = _compact(sl)
                    if sl_norm:
                        norm_map[sl_norm] = tl
                    if sl_comp:
                        compact_map[sl_comp] = tl

    for block in blocks:
        # 1. Standard string fields
        target = _get_field(block, target_lang_canonical)
        if target and isinstance(target, str):
            for lang_code in ("ja", "en", "vi"):
                if lang_code == target_lang_canonical:
                    continue
                src = _get_field(block, lang_code)
                if src and isinstance(src, str):
                    _add_pair(src, target)

        # 2. Lists (items or list field)
        items_tgt = target if isinstance(target, list) else block.get("items")
        for lang_code in ("ja", "en", "vi"):
            if lang_code == target_lang_canonical:
                continue
            items_src = _get_field(block, lang_code) if isinstance(_get_field(block, lang_code), list) else []
            if items_src and items_tgt and len(items_src) == len(items_tgt):
                for s, t in zip(items_src, items_tgt):
                    _add_pair(str(s), str(t))

        # 3. Tables (headers and rows)
        if block.get("type") == "table":
            headers_d = block.get("headers", {})
            rows_d = block.get("rows", {})
            if isinstance(headers_d, dict):
                h_tgt = headers_d.get(target_lang, headers_d.get("vn" if target_lang_canonical == "vi" else target_lang_canonical, []))
                for lang_code in ("ja", "en", "vi", "vn"):
                    if lang_code in (target_lang, target_lang_canonical):
                        continue
                    h_src = headers_d.get(lang_code, [])
                    if len(h_src) == len(h_tgt):
                        for s, t in zip(h_src, h_tgt):
                            _add_pair(str(s), str(t))
                        _add_pair(" ".join(str(s) for s in h_src), " ".join(str(t) for t in h_tgt))
            elif isinstance(headers_d, list) and isinstance(target, list):
                if len(headers_d) == len(target):
                    for s, t in zip(headers_d, target):
                        _add_pair(str(s), str(t))

            if isinstance(rows_d, dict):
                r_tgt = rows_d.get(target_lang, rows_d.get("vn" if target_lang_canonical == "vi" else target_lang_canonical, []))
                for lang_code in ("ja", "en", "vi", "vn"):
                    if lang_code in (target_lang, target_lang_canonical):
                        continue
                    r_src = rows_d.get(lang_code, [])
                    if len(r_src) == len(r_tgt):
                        for row_s, row_t in zip(r_src, r_tgt):
                            if len(row_s) == len(row_t):
                                for s, t in zip(row_s, row_t):
                                    _add_pair(str(s), str(t))
                                _add_pair(" ".join(str(s) for s in row_s), " ".join(str(t) for t in row_t))

        # 4. Meta tables
        if block.get("type") == "meta_table":
            for it in block.get("items", []):
                lbl = it.get("label", {})
                val = it.get("value", {})
                if isinstance(lbl, dict):
                    t_lbl = lbl.get(target_lang) or lbl.get("vn" if target_lang_canonical == "vi" else target_lang_canonical)
                    for lang_code in ("ja", "en", "vi", "vn"):
                        s_lbl = lbl.get(lang_code)
                        if s_lbl and t_lbl and s_lbl != t_lbl:
                            _add_pair(s_lbl, t_lbl)
                if isinstance(val, dict):
                    t_val = val.get(target_lang) or val.get("vn" if target_lang_canonical == "vi" else target_lang_canonical)
                    for lang_code in ("ja", "en", "vi", "vn"):
                        s_val = val.get(lang_code)
                        if s_val and t_val and s_val != t_val:
                            _add_pair(s_val, t_val)

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
# Container & Diagram Region Detection (Smart Reflow v4.0)
# ---------------------------------------------------------------------------

def _detect_all_containers(
    page: pymupdf.Page,
    raw_blocks: list[dict],
) -> list[dict]:
    """Detect all vector containers (flowchart boxes, bordered callouts, table cells)."""
    try:
        drawings = page.get_drawings()
    except Exception:
        return raw_blocks

    containers: list[pymupdf.Rect] = []
    for d in drawings:
        rect = d.get("rect")
        if not rect:
            continue
        r = pymupdf.Rect(rect)
        # Bounded boxes (from flowchart nodes to large callout boxes)
        if 25 < r.width < 550 and 12 < r.height < 350:
            stroke = d.get("color")
            fill = d.get("fill")
            w = d.get("width", 0)
            if (stroke and w is not None and w > 0) or fill:
                containers.append(r)

    if not containers:
        return raw_blocks

    for b in raw_blocks:
        bx = b.get("bbox")
        if not bx or len(bx) < 4:
            continue
        block_rect = pymupdf.Rect(bx)

        best = None
        best_area = float("inf")
        for c in containers:
            # c contains block_rect with small margin
            if c.x0 <= block_rect.x0 + 3.0 and c.y0 <= block_rect.y0 + 3.0 and \
               c.x1 >= block_rect.x1 - 3.0 and c.y1 >= block_rect.y1 - 3.0:
                area = c.width * c.height
                if area < best_area:
                    best_area = area
                    best = c

        if best is not None:
            b["container_rect"] = [best.x0, best.y0, best.x1, best.y1]
            b["is_in_container"] = True
            if best.width < 240 and best.height < 140:
                b["is_in_diagram"] = True

    return raw_blocks

# Backward compatibility alias
_detect_diagram_regions = _detect_all_containers


def _classify_page_mode(
    page: pymupdf.Page,
    raw_blocks: List[Dict[str, Any]],
) -> str:
    """Classifies page layout into TEXT_ONLY, MIXED, or CONSTRAINED."""
    images = page.get_images()
    drawings = page.get_drawings()
    diagram_blocks = [b for b in raw_blocks if b.get("is_in_diagram")]
    table_cell_blocks = [b for b in raw_blocks if b.get("is_table_cell")]
    total = len(raw_blocks)
    if total == 0:
        return PAGE_MODE_TEXT_ONLY
    constrained_ratio = (len(diagram_blocks) + len(table_cell_blocks)) / total
    if constrained_ratio > 0.60:
        return PAGE_MODE_CONSTRAINED
    if len(images) > 0 or len(diagram_blocks) > 0 or len(table_cell_blocks) > 0 or len(drawings) > 30:
        return PAGE_MODE_MIXED
    return PAGE_MODE_TEXT_ONLY


def _compute_reflow_font(
    block: Dict[str, Any],
    page_mode: str,
) -> Tuple[float, float]:
    """Calculates ideal font size and required height for free body paragraphs."""
    bbox = block.get("bbox", [0, 0, 100, 20])
    bw = max(6.0, bbox[2] - bbox[0])
    bh = max(6.0, bbox[3] - bbox[1])
    orig_fs = float(block.get("font_size", 10.0))
    tier = block.get("block_tier", TIER_BODY)
    text = block.get("text", "")
    
    # Blocks inside containers (diagrams, tables, bordered boxes) do NOT reflow vertically
    if tier != TIER_BODY or block.get("is_in_container") or block.get("is_table_cell") or block.get("is_vertical"):
        return orig_fs, bh
        
    if page_mode == PAGE_MODE_CONSTRAINED:
        return orig_fs, bh
        
    target_fs = max(8.0, orig_fs * 0.95)
    char_width = 0.50 * target_fs
    cpl = max(1.0, (bw / char_width) * 0.90)
    lines_est = max(1, math.ceil(len(text) / cpl))
    line_h = target_fs * 1.35
    needed_h = lines_est * line_h + 4.0
    new_h = max(bh, needed_h)
    return target_fs, new_h


def _apply_y_shift(
    render_blocks: List[Dict[str, Any]],
    page_mode: str,
    max_page_y: float = 780.0,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Applies vertical shift to subsequent content blocks when text expands."""
    if not render_blocks:
        return [], []
    if page_mode in (PAGE_MODE_CONSTRAINED, PAGE_MODE_MIXED):
        return render_blocks, []
        
    footer_blocks = [b for b in render_blocks if b.get("bbox", [0, 0, 0, 0])[1] > max_page_y]
    content_blocks = [b for b in render_blocks if b.get("bbox", [0, 0, 0, 0])[1] <= max_page_y]
    content_blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
    
    delta_y = 0.0
    current_page: List[Dict[str, Any]] = []
    overflow: List[Dict[str, Any]] = []
    
    for b in content_blocks:
        x0, y0, x1, y1 = b["bbox"]
        bw = x1 - x0
        bh = y1 - y0
        tier = b.get("block_tier", TIER_BODY)
        is_container = b.get("is_in_container", False)
        is_table = b.get("is_table_cell", False)
        
        # If block is inside a fixed container, it stays at its container Y
        if is_container:
            current_page.append(b)
            continue
            
        shifted_y0 = y0 + delta_y
        
        if tier == TIER_BODY and not is_table and b.get("is_multiline", False):
            target_fs, new_h = _compute_reflow_font(b, page_mode)
            b_shifted = dict(b)
            b_shifted["font_size"] = target_fs
            b_shifted["bbox"] = [x0, shifted_y0, x1, shifted_y0 + new_h]
            if new_h > bh:
                delta_y += (new_h - bh)
        else:
            b_shifted = dict(b)
            b_shifted["bbox"] = [x0, shifted_y0, x1, shifted_y0 + bh]
            
        if b_shifted["bbox"][3] > max_page_y and b_shifted["bbox"][1] >= 660.0:
            overflow.append(b_shifted)
        else:
            current_page.append(b_shifted)
            
    current_page.extend(footer_blocks)
    
    if overflow:
        min_ov_y = min(b["bbox"][1] for b in overflow)
        top_margin = 60.0
        norm_overflow = []
        for b in overflow:
            x0, y0, x1, y1 = b["bbox"]
            rel_y = y0 - min_ov_y
            bh = y1 - y0
            b_norm = dict(b)
            b_norm["bbox"] = [x0, top_margin + rel_y, x1, top_margin + rel_y + bh]
            norm_overflow.append(b_norm)
        overflow = norm_overflow
        
    return current_page, overflow


def _check_2d_overlap(
    candidate_bbox: list[float],
    existing_bboxes: list[list[float]],
    min_gap: float = 3.0,
) -> bool:
    """Check if a candidate bounding box overlaps with any existing rendered block."""
    cr = pymupdf.Rect(candidate_bbox)
    for eb in existing_bboxes:
        er = pymupdf.Rect(eb)
        # Expand existing rect by min_gap for safety margin
        er_padded = pymupdf.Rect(
            er.x0 - min_gap, er.y0 - min_gap,
            er.x1 + min_gap, er.y1 + min_gap,
        )
        if cr.intersects(er_padded):
            return True
    return False


# ---------------------------------------------------------------------------
# Main Overlay Pipeline (Smart Reflow v4.0)
# ---------------------------------------------------------------------------

def preserve_pdf_typst(
    source_pdf_path: Path,
    blocks: list[dict],
    lang: str,
    output_pdf_path: Path,
) -> Path:
    """Translates PDF with Adaptive Height Smart Reflow via Typst & PyMuPDF.
    
    Preserves vector containers, headers, tables, diagrams, and allows natural
    paragraph expansion with continuation pages when required for readability.
    """
    typst_bin = get_typst_bin()
    norm_map, compact_map = build_translation_map(blocks, target_lang=lang)

    doc_src = pymupdf.open(source_pdf_path)
    output_doc = pymupdf.open()
    temp_dir = Path(tempfile.mkdtemp(prefix="ejv_v4_"))

    try:
        for page_idx in range(len(doc_src)):
            page = doc_src[page_idx]
            w = page.rect.width
            h = page.rect.height

            # Extract blocks from page via get_text("dict")
            text_dict = page.get_text("dict")
            raw_blocks = [
                b for b in text_dict.get("blocks", [])
                if b.get("type") == 0 and "lines" in b and b.get("bbox") and len(b["bbox"]) >= 4
            ]

            # Decompose blocks with horizontally disjoint lines
            split_raw_blocks = []
            for b in raw_blocks:
                lines = b.get("lines", [])
                if len(lines) <= 1:
                    split_raw_blocks.append(b)
                    continue
                clusters = [[lines[0]]]
                for l in lines[1:]:
                    lb = l.get("bbox", [0, 0, 0, 0])
                    matched_cluster = None
                    for cl in clusters:
                        cl_x0 = min(item["bbox"][0] for item in cl)
                        cl_x1 = max(item["bbox"][2] for item in cl)
                        if not (lb[0] > cl_x1 + 12.0 or lb[2] < cl_x0 - 12.0):
                            matched_cluster = cl
                            break
                    if matched_cluster:
                        matched_cluster.append(l)
                    else:
                        clusters.append([l])
                if len(clusters) == 1:
                    split_raw_blocks.append(b)
                else:
                    for cl in clusters:
                        new_b = dict(b)
                        new_b["lines"] = cl
                        new_b["bbox"] = [
                            min(l["bbox"][0] for l in cl),
                            min(l["bbox"][1] for l in cl),
                            max(l["bbox"][2] for l in cl),
                            max(l["bbox"][3] for l in cl),
                        ]
                        split_raw_blocks.append(new_b)
            raw_blocks = split_raw_blocks

            # Detect all vector containers (including callout boxes and diagram nodes)
            raw_blocks = _detect_all_containers(page, raw_blocks)

            # Detect table cells
            for b in raw_blocks:
                bx = b["bbox"]
                b_area = (bx[2] - bx[0]) * (bx[3] - bx[1])
                same_band = [
                    ob for ob in raw_blocks
                    if ob is not b
                    and abs(ob["bbox"][1] - bx[1]) < 5.0
                    and abs(ob["bbox"][3] - bx[3]) < 5.0
                ]
                b["is_table_cell"] = (len(same_band) >= 1 and b_area < 8000)

            page_mode = _classify_page_mode(page, raw_blocks)

            LIST_MARKERS = (
                "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
                "・", "●", "■", "◆", "1.", "2.", "3.", "4.", "5.",
                "(1)", "(2)", "(3)", "[1]", "[2]", "[3]",
            )

            # Paragraph merging with strict line spacing
            def can_merge(b1, b2):
                if b1.get("is_table_cell") or b2.get("is_table_cell"):
                    return False
                bx1, bx2 = b1["bbox"], b2["bbox"]
                step_y = bx2[1] - bx1[1]
                # Distance between lines of same paragraph: 3 to 20pt (allows standard 1.5x / 18pt leading)
                if not (3.0 <= step_y <= 20.0):
                    return False
                # Allow first line indent: either lines align (<= 8pt) or b1 is indented (b1.x0 > b2.x0 by up to 16pt)
                diff_x = abs(bx1[0] - bx2[0])
                is_indent = (bx1[0] >= bx2[0] - 2.0 and diff_x <= 16.0)
                is_aligned = (diff_x <= 8.0)
                if not (is_aligned or is_indent):
                    return False
                w1, w2 = bx1[2] - bx1[0], bx2[2] - bx2[0]
                if w2 > w1 * 1.8 and w1 < 160.0:
                    return False
                t1_len = sum(len(s.get("text", "")) for l in b1.get("lines", []) for s in l.get("spans", []))
                if t1_len <= 12 and (bx2[3] - bx2[1]) > (bx1[3] - bx1[1]) * 1.5:
                    return False
                t2_str = "".join(s.get("text", "") for l in b2.get("lines", []) for s in l.get("spans", [])).strip()
                if t2_str.startswith(LIST_MARKERS):
                    return False
                if w1 < 55.0:
                    return False
                # Do not merge across container boundary
                if b1.get("container_rect") != b2.get("container_rect"):
                    return False
                return True

            merged_groups = []
            i = 0
            while i < len(raw_blocks):
                grp = [raw_blocks[i]]
                while i + 1 < len(raw_blocks) and can_merge(grp[-1], raw_blocks[i + 1]):
                    grp.append(raw_blocks[i + 1])
                    i += 1
                merged_groups.append(grp)
                i += 1

            render_blocks = []
            page_bboxes = []

            for group in merged_groups:
                if len(group) > 1:
                    pad_box = [
                        min(b["bbox"][0] for b in group),
                        min(b["bbox"][1] for b in group),
                        max(b["bbox"][2] for b in group),
                        min(h, max(b["bbox"][3] for b in group) + 1.5),
                    ]
                    combined_text = " ".join(
                        "".join(s.get("text", "") for s in l.get("spans", []))
                        for b in group for l in b["lines"]
                    ).strip()
                    trans = find_best_translation(combined_text, norm_map, compact_map)
                    if not trans:
                        sub_trans = []
                        for b in group:
                            bt = " ".join("".join(s.get("text", "") for s in l.get("spans", [])) for l in b["lines"]).strip()
                            t_sub = find_best_translation(bt, norm_map, compact_map)
                            if t_sub:
                                sub_trans.append(t_sub)
                        if len(sub_trans) == len(group):
                            trans = " ".join(sub_trans)

                    if trans:
                        first_span = group[0]["lines"][0]["spans"][0]
                        fs = first_span.get("size", 10.0)
                        fl = first_span.get("flags", 0)
                        is_b = bool(fl & 16) or ("bold" in first_span.get("font", "").lower())
                        is_it = bool(fl & 2) or ("italic" in first_span.get("font", "").lower())
                        c_int = first_span.get("color", 0)
                        c_hex = f"#{c_int:06x}" if c_int else "#000000"

                        is_cont = any(b.get("is_in_container") for b in group)
                        container = next((b.get("container_rect") for b in group if b.get("container_rect")), None)

                        # For blocks in container, use container bounds with clean inner margins
                        if is_cont and container:
                            r_bbox = [
                                max(pad_box[0], container[0] + 5.0),
                                max(pad_box[1], container[1] + 3.0),
                                min(pad_box[2], container[2] - 5.0),
                                min(h, container[3] - 5.0),
                            ]
                        else:
                            r_bbox = pad_box

                        merged_block_data = {
                            "bbox": r_bbox,
                            "text": trans,
                            "font_size": fs,
                            "weight": "bold" if is_b else "regular",
                            "style": "italic" if is_it else "normal",
                            "align": "left",
                            "color": c_hex,
                            "is_multiline": True,
                            "is_in_container": is_cont,
                            "is_in_diagram": any(b.get("is_in_diagram") for b in group),
                            "is_table_cell": any(b.get("is_table_cell") for b in group),
                        }
                        merged_block_data["block_tier"] = _classify_block_tier(merged_block_data, w)
                        render_blocks.append(merged_block_data)
                        page_bboxes.append(pad_box)
                        continue

                # Single block processing
                for b in group:
                    bx = b["bbox"]
                    block_text = " ".join(
                        "".join(s.get("text", "") for s in l.get("spans", []))
                        for l in b.get("lines", [])
                    ).strip()
                    if not block_text:
                        continue
                    translated = find_best_translation(block_text, norm_map, compact_map)
                    if not translated:
                        # Line level fallback
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
                                    pad_box = [lbx[0], lbx[1], lbx[2], min(h, lbx[3] + 1.5)]
                                    line_block_data = {
                                        "bbox": pad_box,
                                        "text": line_trans,
                                        "font_size": sp.get("size", 10.0),
                                        "weight": "bold" if (sp.get("flags", 0) & 16) else "regular",
                                        "style": "normal",
                                        "align": "left",
                                        "color": "#000000",
                                        "is_multiline": False,
                                        "is_table_cell": b.get("is_table_cell", False),
                                        "is_in_diagram": b.get("is_in_diagram", False),
                                        "is_in_container": b.get("is_in_container", False),
                                    }
                                    line_block_data["block_tier"] = _classify_block_tier(line_block_data, w)
                                    render_blocks.append(line_block_data)
                                    page_bboxes.append(pad_box)
                        continue

                    first_span = b["lines"][0]["spans"][0]
                    font_size = first_span.get("size", 10.0)
                    flags = first_span.get("flags", 0)
                    is_bold = bool(flags & 16) or ("bold" in first_span.get("font", "").lower())
                    is_italic = bool(flags & 2) or ("italic" in first_span.get("font", "").lower())
                    color_int = first_span.get("color", 0)
                    color_hex = f"#{color_int:06x}" if color_int else "#000000"

                    b_w = bx[2] - bx[0]
                    b_h = bx[3] - bx[1]
                    is_vert = (b_h > b_w * 2.2 and b_w < 25.0)
                    is_container = b.get("is_in_container", False)
                    is_diagram = b.get("is_in_diagram", False)
                    container = b.get("container_rect")

                    render_x0 = bx[0]
                    render_x1 = bx[2]

                    # Special header handling
                    is_header_title = (bx[1] < 55.0 and bx[0] > 80.0 and b_w > 180.0)
                    is_society_header = (bx[1] < 85.0 and bx[0] > 350.0 and b_w > 100.0)

                    if is_header_title:
                        # Title expands to the right (up to 440pt width)
                        render_x1 = min(w - 54.0, max(bx[2], bx[0] + 440.0))
                    elif is_society_header:
                        # Society header expands to the left (right-aligned)
                        render_x0 = max(180.0, bx[0] - 200.0)
                        render_x1 = bx[2]
                    elif not is_vert and not is_container and b_w < 220.0:
                        right_limit = w - 54.0
                        for other_b in raw_blocks:
                            if other_b is b:
                                continue
                            obx = other_b["bbox"]
                            if max(bx[1], obx[1]) < min(bx[3], obx[3]) + 2.0:
                                if obx[0] >= bx[2] - 4.0:
                                    right_limit = min(right_limit, obx[0] - 4.0)
                        if right_limit > bx[2] + 20.0:
                            candidate_x1 = min(right_limit, max(bx[2], bx[0] + 280.0))
                            candidate_bbox = [bx[0], bx[1], candidate_x1, bx[3] + 1.5]
                            if not _check_2d_overlap(candidate_bbox, page_bboxes):
                                render_x1 = candidate_x1
                    elif is_container and container and not is_vert:
                        container_left = container[0] + 5.0
                        container_right = container[2] - 5.0
                        render_x0 = max(bx[0], container_left)
                        render_x1 = min(max(bx[2], container_right), container_right)

                    if is_vert:
                        render_x1 = bx[0] + max(b_w, 14.0)

                    align = "left"
                    if is_society_header:
                        align = "right"
                    else:
                        mid_x = (bx[0] + bx[2]) / 2
                        is_bullet = any(translated.strip().startswith(p) for p in ("•", "-", "●", "①", "②", "③", "1.", "2.", "3.", "*"))
                        is_multi_line = len(b.get("lines", [])) > 1 or "\n" in translated or (b_h >= font_size * 1.35 and len(translated) > 20)

                        if not is_vert and not is_bullet and not is_multi_line:
                            if abs(mid_x - (w / 2)) < 25 and (bx[2] - bx[0]) < 220.0:
                                align = "center"
                            elif bx[0] > (w * 0.65) and (bx[2] - bx[0]) < 200.0:
                                align = "right"
                            elif is_container and container:
                                align = "center"

                    render_y0 = bx[1]
                    render_y1 = bx[3] + 1.5
                    if is_container and container:
                        render_x0 = max(render_x0, container[0] + 5.0)
                        render_x1 = min(render_x1, container[2] - 5.0)
                        render_y0 = max(render_y0, container[1] + 3.0)
                        render_y1 = min(bx[3], container[3] - 5.0)

                    render_bbox = [render_x0, render_y0, render_x1, min(h, render_y1)]
                    padded_bbox = [bx[0], bx[1], bx[2], min(h, bx[3] + 1.5)]

                    single_block_data = {
                        "bbox": render_bbox,
                        "text": translated,
                        "font_size": font_size,
                        "weight": "bold" if is_bold else "regular",
                        "style": "italic" if is_italic else "normal",
                        "align": align,
                        "color": color_hex,
                        "is_vertical": is_vert,
                        "is_in_container": is_container,
                        "is_in_diagram": is_diagram,
                        "is_table_cell": b.get("is_table_cell", False),
                        "is_multiline": is_multi_line,
                    }
                    single_block_data["block_tier"] = _classify_block_tier(single_block_data, w)
                    render_blocks.append(single_block_data)
                    page_bboxes.append(padded_bbox)

            # Apply Smart Reflow Y-Shift
            current_blocks, overflow_blocks = _apply_y_shift(render_blocks, page_mode)

            # Build and compile Typst overlay
            typ_code = _build_typst_page_source(w, h, current_blocks, continuation_blocks=overflow_blocks, lang=lang)
            typ_file = temp_dir / f"page_{page_idx}.typ"
            pdf_page_overlay = temp_dir / f"page_{page_idx}.pdf"
            typ_file.write_text(typ_code, encoding="utf-8")

            cmd = [typst_bin, "compile", str(typ_file), str(pdf_page_overlay)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"Typst compilation failed on page {page_idx}:\n{res.stderr}")

            # PyMuPDF Redaction on original page
            for link in page.get_links():
                l_rect = link.get("from")
                if l_rect:
                    for b in page_bboxes:
                        if l_rect.intersects(pymupdf.Rect(b)):
                            page.delete_link(link)
                            break

            # Pre-sample all background colors before adding any redaction annotations
            # (Prevents subsequent samples from capturing unapplied redaction border artifacts)
            bg_colors = [_sample_bg_color(page, pymupdf.Rect(b)) for b in page_bboxes]

            for b, bg_col in zip(page_bboxes, bg_colors):
                rect = pymupdf.Rect(b)
                safe_rect = pymupdf.Rect(rect.x0 + 0.8, rect.y0 + 0.5, rect.x1 - 0.8, rect.y1 - 0.5)
                if safe_rect.width > 2 and safe_rect.height > 1:
                    page.add_redact_annot(safe_rect, fill=bg_col)
                else:
                    page.add_redact_annot(rect, fill=bg_col)

            try:
                page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
            except Exception:
                page.apply_redactions()

            # Stamp overlay page 0 on original page
            single_page_doc = pymupdf.open(pdf_page_overlay)
            page.show_pdf_page(page.rect, single_page_doc, 0, overlay=True)

            # Transfer original page to output_doc
            output_doc.insert_pdf(doc_src, from_page=page_idx, to_page=page_idx)

            # If Typst generated continuation pages (len > 1), insert them into output_doc
            if len(single_page_doc) > 1:
                for extra_idx in range(1, len(single_page_doc)):
                    extra_page = output_doc.new_page(width=w, height=h)
                    extra_page.show_pdf_page(extra_page.rect, single_page_doc, extra_idx, overlay=True)

            single_page_doc.close()

        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        output_doc.save(str(output_pdf_path), garbage=4, deflate=True)
        output_doc.close()

    finally:
        doc_src.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"✅ Typst Smart Reflow v4.0 PDF successfully generated: {output_pdf_path}")
    return output_pdf_path


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Typst Smart Reflow Overlay for PDF")
    parser.add_argument("--pdf", required=True, type=Path, help="Source PDF file")
    parser.add_argument("--blocks", required=True, type=Path, help="Merged JSON blocks file")
    parser.add_argument("--lang", default="vi", help="Target language code (vi/en/ja)")
    parser.add_argument("--output", required=True, type=Path, help="Output PDF file")
    args = parser.parse_args()

    with open(args.blocks, "r", encoding="utf-8") as f:
        loaded_blocks = json.load(f)

    preserve_pdf_typst(
        source_pdf_path=args.pdf,
        blocks=loaded_blocks,
        lang=args.lang,
        output_pdf_path=args.output,
    )
