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

# ---------------------------------------------------------------------------
# Multi-Tier Font Scaling Strategy (v3.0)
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
        if not colors:
            return (1.0, 1.0, 1.0)
        from collections import Counter
        most_common = Counter(colors).most_common(1)[0][0]
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
    """Generates complete Typst source for an overlay page.

    v3.0: Multi-Tier Font Scaling — each block receives per-tier
    min/max constraints based on its classification (HEADING, BODY,
    TABLE_CELL, DIAGRAM_LABEL, VERTICAL). BODY blocks share a
    unified floor size for visual consistency.
    """
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
        "// Auto-generated Typst Overlay by EJV Translate (v3.0 Multi-Tier)",
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
        "    let fits(text_size, leading) = {",
        "      let h_ok = measure(width: size.width, render_fn(text_size, leading)).height <= allowed_h",
        "      let w_ok = if not is_multiline { measure(text(size: text_size)[#body]).width <= (size.width + 0.5pt) } else { true }",
        "      h_ok and w_ok",
        "    }",
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

        # --- v3.0: Multi-Tier Font Constraints ---
        tier = block.get("block_tier", TIER_BODY)
        tier_cfg = FONT_TIERS.get(tier, FONT_TIERS[TIER_BODY])

        max_size = float(orig_font_size) * tier_cfg["max_scale"]
        tier_min = tier_cfg["min_size"]

        # For BODY blocks, use the page-level unified floor
        if tier == TIER_BODY:
            min_size = max(tier_min, body_floor)
        elif tier == TIER_HEADING:
            # Headings: floor at 70% of original, never below tier min
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

        if block.get("is_vertical"):
            # v2.1: Vertical text now uses pdftr_fit_text for auto-scaling
            vert_max = min(max_size, 9.0)
            vert_min = max(4.0, vert_max * 0.4)
            lines.append(f"// Vertical Block {i} [tier={tier}]: [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}]")
            lines.append(f"#place(")
            lines.append(f"  top + left,")
            lines.append(f"  dx: {x0:.2f}pt,")
            lines.append(f"  dy: {y0:.2f}pt,")
            lines.append(f"  box(")
            lines.append(f"    width: {width:.2f}pt,")
            lines.append(f"    height: {height:.2f}pt,")
            lines.append(f"    clip: true,")
            lines.append(f"    align(center + horizon)[")
            lines.append(f"      #rotate(-90deg, reflow: false)[")
            lines.append(f"        #box(width: {height:.2f}pt, height: {width:.2f}pt,[")
            lines.append(f"          #pdftr_fit_text(")
            lines.append(f"            [{escaped_text}],")
            lines.append(f"            max_size: {vert_max:.2f}pt,")
            lines.append(f"            min_size: {vert_min:.2f}pt,")
            lines.append(f"            fit_height: {width:.2f}pt,")
            lines.append(f"            is_multiline: false,")
            lines.append(f'            weight: "{weight}",')
            lines.append(f'            style: "{style}",')
            lines.append(f"            align_type: center,")
            lines.append(f'            fill_color: rgb("{color_hex}"),')
            lines.append(f"          )")
            lines.append(f"        ])")
            lines.append(f"      ]")
            lines.append(f"    ]")
            lines.append(f"  )")
            lines.append(f")")
            lines.append("")
            continue

        lines.append(f"// Block {i} [tier={tier}]: [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}]")
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
        is_multi_str = "true" if ("\n" in raw_text or len(block.get("lines", [])) > 1) else "false"
        lines.append(f"      is_multiline: {is_multi_str},")
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
# Diagram Region Detection (v2.1)
# ---------------------------------------------------------------------------

def _detect_diagram_regions(
    page: pymupdf.Page,
    text_blocks: list[dict],
) -> list[dict]:
    """Detect diagram regions by finding vector rectangles that contain text blocks.
    
    Returns the text_blocks list with an added 'container_rect' field for blocks
    that are inside a diagram/flowchart container.
    """
    try:
        drawings = page.get_drawings()
    except Exception:
        return text_blocks

    # Collect all rectangular regions from vector drawings
    containers: list[pymupdf.Rect] = []
    for d in drawings:
        rect = d.get("rect")
        if not rect:
            continue
        r = pymupdf.Rect(rect)
        # Only consider node-sized rectangles (flowchart nodes, not entire tables or page frames)
        if 30 < r.width < 220 and 15 < r.height < 140:
            stroke = d.get("color")
            fill = d.get("fill")
            w = d.get("width", 0)
            if (stroke and w > 0) or fill:
                containers.append(r)

    if not containers:
        return text_blocks

    # For each text block, find its container
    for b in text_blocks:
        bx = b.get("bbox")
        if not bx or len(bx) < 4:
            continue
        block_rect = pymupdf.Rect(bx)

        # Find smallest enclosing container
        best = None
        best_area = float("inf")
        for c in containers:
            if c.contains(block_rect):
                area = c.width * c.height
                if area < best_area:
                    best_area = area
                    best = c

        if best is not None:
            b["container_rect"] = [best.x0, best.y0, best.x1, best.y1]
            b["is_in_diagram"] = True

    return text_blocks


def _check_2d_overlap(
    candidate_bbox: list[float],
    existing_bboxes: list[list[float]],
    min_gap: float = 3.0,
) -> bool:
    """Check if a candidate bounding box overlaps with any existing rendered block.
    
    Returns True if overlap detected.
    """
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

            # Extract valid text blocks
            raw_blocks = [
                b for b in text_dict.get("blocks", [])
                if b.get("type") == 0 and "lines" in b and b.get("bbox") and len(b["bbox"]) >= 4
            ]

            # Decompose blocks with horizontally disjoint lines (e.g. table columns, diagram labels)
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

            # v2.1: Detect diagram regions via vector analysis
            raw_blocks = _detect_diagram_regions(page, raw_blocks)

            LIST_MARKERS = (
                "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
                "・", "●", "■", "◆", "1.", "2.", "3.", "4.", "5.",
                "(1)", "(2)", "(3)", "[1]", "[2]", "[3]",
            )

            # Group adjacent single-line blocks that form continuous paragraphs
            # v2.4: Protected headings, list markers, and stricter paragraph grouping
            def can_merge(b1, b2):
                bx1 = b1["bbox"]
                bx2 = b2["bbox"]
                step_y = bx2[1] - bx1[1]
                # Distance between lines of same paragraph: 3 to 24pt
                if not (3.0 <= step_y <= 24.0):
                    return False
                # Similar left margin (within 8pt)
                if abs(bx1[0] - bx2[0]) > 8.0:
                    return False
                w1 = bx1[2] - bx1[0]
                w2 = bx2[2] - bx2[0]
                # Disallow merging if b1 is a short heading followed by a much wider block
                if w2 > w1 * 1.8 and w1 < 160.0:
                    return False
                # Disallow merging if b1 has few characters (heading/label tab)
                t1_len = sum(len(s.get("text", "")) for l in b1.get("lines", []) for s in l.get("spans", []))
                if t1_len <= 12 and (bx2[3] - bx2[1]) > (bx1[3] - bx1[1]) * 1.5:
                    return False
                # Disallow merging if b2 starts with a list marker (never merge bullet items together)
                t2_str = "".join(s.get("text", "") for l in b2.get("lines", []) for s in l.get("spans", [])).strip()
                if t2_str.startswith(LIST_MARKERS):
                    return False
                # First line should be a substantial line (> 55pt for multi-column)
                if w1 < 55.0:
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

            for group in merged_groups:
                if len(group) > 1:
                    # Multi-line paragraph: Merge into one unified bounding box
                    pad_box = [
                        min(b["bbox"][0] for b in group),
                        min(b["bbox"][1] for b in group),
                        max(b["bbox"][2] for b in group),
                        min(h, max(b["bbox"][3] for b in group) + 1.5)
                    ]
                    # Check combined translation
                    combined_text = "".join(
                        " ".join("".join(s.get("text", "") for s in l.get("spans", [])) for l in b["lines"])
                        for b in group
                    ).strip()
                    trans = find_best_translation(combined_text, norm_map, compact_map)
                    if not trans:
                        # Try joining individual translations of sub-blocks
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

                        merged_block_data = {
                            "bbox": pad_box,
                            "text": trans,
                            "font_size": fs,
                            "weight": "bold" if is_b else "regular",
                            "style": "italic" if is_it else "normal",
                            "align": "left",
                            "color": c_hex,
                        }
                        merged_block_data["block_tier"] = _classify_block_tier(merged_block_data, w)
                        render_blocks.append(merged_block_data)
                        page_bboxes.append(pad_box)
                        continue

                # Single block processing (or fallback for unmerged groups)
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
                                    fs = sp.get("size", 10.0)
                                    fl = sp.get("flags", 0)
                                    is_b = bool(fl & 16) or ("bold" in sp.get("font", "").lower())
                                    is_it = bool(fl & 2) or ("italic" in sp.get("font", "").lower())
                                    c_int = sp.get("color", 0)
                                    c_hex = f"#{c_int:06x}" if c_int else "#000000"
                                    pad_box = [lbx[0], lbx[1], lbx[2], min(h, lbx[3] + 1.5)]
                                    line_block_data = {
                                        "bbox": pad_box,
                                        "text": line_trans,
                                        "font_size": fs,
                                        "weight": "bold" if is_b else "regular",
                                        "style": "italic" if is_it else "normal",
                                        "align": "left",
                                        "color": c_hex,
                                    }
                                    line_block_data["block_tier"] = _classify_block_tier(line_block_data, w)
                                    render_blocks.append(line_block_data)
                                    page_bboxes.append(pad_box)
                        continue

                    # Found single block translation
                    first_span = b["lines"][0]["spans"][0]
                    font_size = first_span.get("size", 10.0)
                    flags = first_span.get("flags", 0)
                    is_bold = bool(flags & 16) or ("bold" in first_span.get("font", "").lower())
                    is_italic = bool(flags & 2) or ("italic" in first_span.get("font", "").lower())
                    color_int = first_span.get("color", 0)
                    color_hex = f"#{color_int:06x}" if color_int else "#000000"

                    # Vertical column banner detection
                    b_w = bx[2] - bx[0]
                    b_h = bx[3] - bx[1]
                    is_vert = (b_h > b_w * 2.2 and b_w < 25.0)

                    # v2.1: Check if block is inside a diagram container
                    is_diagram = b.get("is_in_diagram", False)
                    container = b.get("container_rect")

                    # Heading clearance calculation with 2D overlap prevention
                    render_x1 = bx[2]
                    if not is_vert and not is_diagram and b_w < 220.0:
                        # Only expand for non-diagram blocks
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
                            # v2.1: 2D overlap check against already-rendered blocks
                            candidate_bbox = [bx[0], bx[1], candidate_x1, bx[3] + 1.5]
                            if not _check_2d_overlap(candidate_bbox, page_bboxes):
                                render_x1 = candidate_x1
                    elif is_diagram and container and not is_vert:
                        # v2.2: Diagram blocks — use container bounds for width,
                        # but constrain to avoid overlapping container border
                        container_left = container[0] + 2.0
                        container_right = container[2] - 2.0
                        # Expand render width to fill container if text would overflow
                        render_x1 = min(max(bx[2], container_right), container_right)
                        # v3.0: Diagram font capping is now handled by FONT_TIERS
                        # (no more aggressive uniform shrink here)

                    if is_vert:
                        render_x1 = bx[0] + max(b_w, 14.0)

                    align = "left"
                    mid_x = (bx[0] + bx[2]) / 2
                    is_bullet = any(translated.strip().startswith(p) for p in ("•", "-", "●", "①", "②", "③", "1.", "2.", "3.", "*"))
                    is_multi_line = len(b.get("lines", [])) > 1 or "\n" in translated
                    if not is_vert and not is_bullet and not is_multi_line:
                        if abs(mid_x - (w / 2)) < 25 and (bx[2] - bx[0]) < 220.0:
                            align = "center"
                        elif bx[0] > (w * 0.65) and (bx[2] - bx[0]) < 200.0:
                            align = "right"
                        elif is_diagram and container:
                            # v2.2: Center diagram labels within their container
                            container_mid = (container[0] + container[2]) / 2
                            if abs(mid_x - container_mid) < (b_w * 0.6):
                                align = "center"

                    # v2.2: For diagram blocks, use container-aware bbox
                    if is_diagram and container and not is_vert:
                        padded_bbox = [
                            max(bx[0], container[0] + 1.0),
                            bx[1],
                            min(render_x1, container[2] - 1.0),
                            min(h, bx[3] + 1.5),
                        ]
                    else:
                        padded_bbox = [bx[0], bx[1], bx[2], min(h, bx[3] + 1.5)]
                    render_bbox = [bx[0], bx[1], render_x1, min(h, bx[3] + 1.5)]
                    single_block_data = {
                        "bbox": render_bbox,
                        "text": translated,
                        "font_size": font_size,
                        "weight": "bold" if is_bold else "regular",
                        "style": "italic" if is_italic else "normal",
                        "align": align,
                        "color": color_hex,
                        "is_vertical": is_vert,
                        "is_in_diagram": is_diagram,
                        "is_table_cell": False,  # will be set by heuristic below
                    }
                    # v3.0: Classify block tier
                    # Heuristic: detect table cells by checking if block is small and
                    # surrounded by grid-like neighbours on the same Y band
                    if not is_vert and not is_diagram:
                        b_area = (bx[2] - bx[0]) * (bx[3] - bx[1])
                        same_band = [
                            ob for ob in raw_blocks
                            if ob is not b
                            and abs(ob["bbox"][1] - bx[1]) < 5.0
                            and abs(ob["bbox"][3] - bx[3]) < 5.0
                        ]
                        # If 2+ blocks share the same Y-band → table-like row
                        if len(same_band) >= 2 and b_area < 8000:
                            single_block_data["is_table_cell"] = True

                    single_block_data["block_tier"] = _classify_block_tier(single_block_data, w)
                    render_blocks.append(single_block_data)
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

            # 2. Add redactions matching background color
            # v2.1: Border-safe redaction — shrink rect by 0.8pt to avoid covering border vectors
            for b in bboxes:
                rect = pymupdf.Rect(b)
                safe_rect = pymupdf.Rect(
                    rect.x0 + 0.8, rect.y0 + 0.5,
                    rect.x1 - 0.8, rect.y1 - 0.5,
                )
                # Ensure safe_rect is still valid
                if safe_rect.width > 2 and safe_rect.height > 1:
                    bg_col = _sample_bg_color(page_src, rect)
                    page_src.add_redact_annot(safe_rect, fill=bg_col)
                else:
                    bg_col = _sample_bg_color(page_src, rect)
                    page_src.add_redact_annot(rect, fill=bg_col)

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
