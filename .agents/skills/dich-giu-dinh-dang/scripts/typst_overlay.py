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
# Edge-Safety Policy (QD-1 fix: prevent text clipping near page boundaries)
# ---------------------------------------------------------------------------
# Minimum distance from page edge before edge-safety activates
EDGE_SAFETY_THRESHOLD = 12.0  # pt
# Extra width added to text boxes near edges to prevent character clipping
EDGE_SAFETY_PADDING = 6.0  # pt
# Table cell internal padding (QD-2 fix: better alignment)
TABLE_CELL_PADDING_LEFT = 2.0  # pt
TABLE_CELL_PADDING_RIGHT = 2.0  # pt

# ---------------------------------------------------------------------------
# Multi-Tier Font Scaling Strategy (v4.0 Smart Reflow)
# ---------------------------------------------------------------------------

# Font tier classification constants (Content-Aware Roles)
TIER_TITLE = "title"
TIER_HEADING = "heading"
TIER_BODY = "body"
TIER_TABLE_HEADER = "table_header"
TIER_TABLE_CELL = "table_cell"
TIER_CAPTION = "caption"
TIER_DIAGRAM_LABEL = "diagram_label"
TIER_TIMELINE_LABEL = "timeline_label"
TIER_HEADER_FOOTER = "header_footer"
TIER_VERTICAL = "vertical"

# Per-tier font constraints (pt) with floor ratios
FONT_TIERS = {
    TIER_TITLE: {
        "min_size": 9.5,
        "max_scale": 1.0,
        "floor_ratio": 0.85,
        "min_leading": 0.25,
        "max_leading": 0.55,
    },
    TIER_HEADING: {
        "min_size": 8.5,
        "max_scale": 1.0,
        "floor_ratio": 0.80,
        "min_leading": 0.25,
        "max_leading": 0.55,
    },
    TIER_BODY: {
        "min_size": 7.5,
        "max_scale": 1.0,
        "floor_ratio": 0.75,
        "min_leading": 0.22,
        "max_leading": 0.50,
    },
    TIER_TABLE_HEADER: {
        "min_size": 6.5,
        "max_scale": 0.98,
        "floor_ratio": 0.70,
        "min_leading": 0.18,
        "max_leading": 0.45,
    },
    TIER_TABLE_CELL: {
        "min_size": 5.0,
        "max_scale": 0.95,
        "floor_ratio": 0.65,
        "min_leading": 0.18,
        "max_leading": 0.45,
    },
    TIER_CAPTION: {
        "min_size": 6.0,
        "max_scale": 0.95,
        "floor_ratio": 0.70,
        "min_leading": 0.20,
        "max_leading": 0.45,
    },
    TIER_TIMELINE_LABEL: {
        "min_size": 5.2,
        "max_scale": 0.90,
        "floor_ratio": 0.65,
        "min_leading": 0.15,
        "max_leading": 0.38,
    },
    TIER_DIAGRAM_LABEL: {
        "min_size": 5.0,
        "max_scale": 0.90,
        "floor_ratio": 0.65,
        "min_leading": 0.15,
        "max_leading": 0.40,
    },
    TIER_HEADER_FOOTER: {
        "min_size": 6.0,
        "max_scale": 0.95,
        "floor_ratio": 0.70,
        "min_leading": 0.20,
        "max_leading": 0.45,
    },
    TIER_VERTICAL: {
        "min_size": 4.5,
        "max_scale": 0.90,
        "floor_ratio": 0.60,
        "min_leading": 0.20,
        "max_leading": 0.45,
    },
}

_CAPTION_PREFIXES = (
    "hình ", "ảnh ", "sơ đồ ", "biểu đồ ", "bảng ", "fig. ", "figure ",
    "photo ", "table ", "図 ", "写真 ", "表 ", "chart ",
)


def _classify_block_tier(
    block: Dict[str, Any],
    page_width: float = 595.0,
    page_height: float = 842.0,
) -> str:
    """Classify a render block into a font tier based on its metadata and layout context."""
    if block.get("is_vertical"):
        return TIER_VERTICAL

    bbox = block.get("bbox", [0, 0, 100, 20])
    b_w = bbox[2] - bbox[0]
    b_h = bbox[3] - bbox[1]
    text = block.get("text", "").strip()
    text_lower = text.lower()
    weight = block.get("weight", "regular")
    font_size = block.get("font_size", 10.0)
    line_count = max(1, text.count("\n") + 1)
    is_bold = weight in ("bold", "700", "800", "900")

    # Header / Footer detection by position and line count
    if (bbox[1] < 45.0 or bbox[3] > page_height - 45.0) and line_count <= 2 and font_size <= 10.5:
        return TIER_HEADER_FOOTER

    # Caption detection
    if any(text_lower.startswith(p) for p in _CAPTION_PREFIXES) and len(text) < 180:
        return TIER_CAPTION

    # Timeline / Month label detection (dense timeline elements like JSTB p3)
    is_month_match = bool(re.search(r'^(?:tháng\s*\d{1,2}|\d{1,2}\s*月|q[1-4]|năm\s*\d{4}|year\s*\d{4})$', text_lower))
    if is_month_match or (b_w < 45.0 and re.search(r'(?:tháng\s*\d|\d\s*月|q[1-4])', text_lower)):
        return TIER_TIMELINE_LABEL

    # Title detection: prominent top header
    if font_size >= 13.5 or (font_size >= 11.5 and is_bold and bbox[1] < 120.0 and b_w > page_width * 0.4):
        return TIER_TITLE

    # Heading detection: prominent section headers, badges, bold titles
    is_large_font = font_size >= 10.8
    is_short = line_count <= 2 and len(text) < 120
    is_wide = b_w > page_width * 0.35
    is_section_header = (bbox[1] < 140.0 and abs((bbox[0] + bbox[2]) / 2.0 - page_width / 2.0) < 40.0 and line_count <= 2 and len(text) < 80)
    is_badge_header = (b_h < 26.0 and font_size >= 10.5 and is_short and not any(text_lower.startswith(p) for p in ("tháng", "quý", "năm", "http", "www")))

    if is_bold and is_short and (is_large_font or is_wide):
        return TIER_HEADING
    if is_large_font and is_short and b_h < 35.0:
        return TIER_HEADING
    if (is_section_header or is_badge_header) and font_size >= 10.0:
        return TIER_HEADING

    if block.get("is_in_diagram"):
        if b_w < 50.0 or b_h < 18.0:
            return TIER_TIMELINE_LABEL
        return TIER_DIAGRAM_LABEL

    if block.get("is_table_cell"):
        if is_bold or (b_h > 18.0 and font_size >= 10.0):
            return TIER_TABLE_HEADER
        return TIER_TABLE_CELL

    return TIER_BODY


def _compute_body_floor_size(
    render_blocks: List[Dict[str, Any]],
) -> float:
    """Compute a unified minimum font size for BODY blocks on a page."""
    body_sizes = [
        b.get("font_size", 10.0)
        for b in render_blocks
        if b.get("block_tier") == TIER_BODY
    ]
    if not body_sizes:
        return 7.5

    body_sizes.sort()
    median = body_sizes[len(body_sizes) // 2]
    return max(7.5, median * 0.75)


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


def _protect_inline_groups(text: str) -> str:
    """Protects short semantic groups (month+number, number+unit, currency) from awkward line breaks."""
    if not text:
        return ""
    # Month + number: e.g. "Tháng 5" -> "Tháng~5"
    text = re.sub(r'\b(Tháng|tháng|Quý|quý)\s+(\d{1,2})\b', r'\1~\2', text)
    # Number + unit: e.g. "5 người" -> "5~người", "7 ngày" -> "7~ngày", "3 năm" -> "3~năm"
    text = re.sub(r'(\d+)\s+(năm|tháng|ngày|tuần|người|cơ sở|bệnh viện|học viên|chuyên gia|đối tượng|ca|bệnh nhân|lần|USD|JPY|V|A|%)\b', r'\1~\2', text)
    # Formatted currency: e.g. "5.700 USD" -> "5.700~USD", "450.000 JPY" -> "450.000~JPY"
    text = re.sub(r'(\d{1,3}(?:\.\d{3})+)\s+(USD|JPY|đồng|yên|VNĐ)\b', r'\1~\2', text)
    return text


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
    text = _protect_inline_groups(text)
    text = text.replace("\n", " \\ ")
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
    if height >= orig_font_size * 1.20 and len(raw_text) > 15:
        return True
    if height >= 16.0 and len(raw_text) > 20:
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
        "    let fits(text_size, leading, allow_wrap: false) = {",
        "      let m = measure(width: size.width, render_fn(text_size, leading))",
        "      let height_ok = if (not is_multiline) and (not allow_wrap) {",
        "        m.height <= (text_size * 1.40 + 1.0pt) and m.height <= (allowed_h + 1.0pt)",
        "      } else {",
        "        m.height <= (allowed_h + 1.0pt)",
        "      }",
        "      let width_ok = if (not is_multiline) and (not allow_wrap) {",
        "        measure(block[#set text(size: text_size, weight: weight, style: style); #body]).width <= (size.width + 0.2pt)",
        "      } else { true }",
        "      height_ok and width_ok",
        "    }",
        "",
        "    if fits(max_size, max_leading) {",
        "      render_fn(max_size, max_leading)",
        "    } else {",
        "      let chosen_size = pdftr_fit_size(min_size, max_size, eps, size_pt => fits(size_pt, min_leading))",
        "      if fits(chosen_size, min_leading) {",
        "        render_fn(chosen_size, min_leading)",
        "      } else if (not is_multiline) and allowed_h >= 13.5pt {",
        "        let wrap_size = pdftr_fit_size(calc.max(min_size, 5.0pt), max_size, eps, size_pt => fits(size_pt, min_leading, allow_wrap: true))",
        "        if fits(wrap_size, min_leading, allow_wrap: true) {",
        "          render_fn(wrap_size, min_leading)",
        "        } else {",
        "          let wrap_emerg = pdftr_fit_size(4.2pt, max_size, eps, size_pt => fits(size_pt, min_leading * 0.70, allow_wrap: true))",
        "          if fits(wrap_emerg, min_leading * 0.70, allow_wrap: true) {",
        "            render_fn(wrap_emerg, min_leading * 0.70)",
        "          } else {",
        "            let emerg = pdftr_fit_size(3.8pt, min_size, eps, size_pt => fits(size_pt, min_leading * 0.70))",
        "            let final_size = if fits(emerg, min_leading * 0.70) { emerg } else { 4.0pt }",
        "            render_fn(final_size, min_leading * 0.70)",
        "          }",
        "        }",
        "      } else {",
        "        let emerg = pdftr_fit_size(3.8pt, min_size, eps, size_pt => fits(size_pt, min_leading * 0.70))",
        "        let final_size = if fits(emerg, min_leading * 0.70) { emerg } else { 4.0pt }",
        "        render_fn(final_size, min_leading * 0.70)",
        "      }",
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

            # --- Edge-Safety Policy (QD-1 fix) ---
            # For blocks near page edges, extend the Typst box slightly
            # to prevent the last character from being clipped.
            # This does NOT move the block visually — it only gives
            # the Typst text-fitting algorithm more room.
            is_near_right = (page_width_pt - x1) < EDGE_SAFETY_THRESHOLD
            is_near_left = x0 < EDGE_SAFETY_THRESHOLD
            is_near_bottom = (page_height_pt - y1) < EDGE_SAFETY_THRESHOLD

            effective_x0 = x0
            effective_x1 = x1
            effective_y1 = y1

            if is_near_right:
                effective_x1 = min(page_width_pt - 4.0, x1 + EDGE_SAFETY_PADDING)
            if is_near_left:
                effective_x0 = max(4.0, x0 - EDGE_SAFETY_PADDING)
            if is_near_bottom:
                effective_y1 = min(page_height_pt - 4.0, y1 + 3.0)

            # --- Table Cell Padding (QD-2 fix) ---
            is_table = block.get("is_table_cell", False)
            if is_table:
                effective_x0 = effective_x0 + TABLE_CELL_PADDING_LEFT
                effective_x1 = max(effective_x0 + 6.0, effective_x1 - TABLE_CELL_PADDING_RIGHT)

            width = max(6.0, effective_x1 - effective_x0)
            height = max(6.0, effective_y1 - y0)

            raw_text = block.get("text", "").strip()
            if not raw_text:
                continue

            # --- Module H: Newline-Aware Rendering ---
            # Preserve \n in translated text as Typst line breaks
            if "\n" in raw_text:
                parts = raw_text.split("\n")
                escaped_parts = [_escape_typst_content(p.strip()) for p in parts if p.strip()]
                escaped_text = (" " + "\\\\" + " ").join(escaped_parts)  # Typst line break syntax
            else:
                escaped_text = _escape_typst_content(raw_text)

            orig_font_size = block.get("font_size")
            if not orig_font_size:
                line_count = max(1, raw_text.count("\n") + 1)
                orig_font_size = max(7.0, (height / line_count) * 0.75)

            # --- Multi-Tier Font Constraints (Content-Aware Adaptation) ---
            tier = block.get("block_tier", TIER_BODY)
            tier_cfg = FONT_TIERS.get(tier, FONT_TIERS[TIER_BODY])

            max_size = float(orig_font_size) * tier_cfg["max_scale"]
            tier_min = tier_cfg["min_size"]
            floor_from_ratio = float(orig_font_size) * tier_cfg.get("floor_ratio", 0.70)

            if tier == TIER_BODY:
                min_size = max(tier_min, min(body_floor, floor_from_ratio))
            elif tier in (TIER_TITLE, TIER_HEADING):
                min_size = max(tier_min, floor_from_ratio)
            elif tier in (TIER_TIMELINE_LABEL, TIER_TABLE_CELL, TIER_TABLE_HEADER, TIER_DIAGRAM_LABEL):
                min_size = tier_min
            else:
                min_size = max(tier_min, floor_from_ratio)
            min_size = min(min_size, max_size)

            min_leading_em = f"{tier_cfg['min_leading']:.2f}em"
            max_leading_em = f"{tier_cfg['max_leading']:.2f}em"

            weight = "bold" if block.get("weight") in ("bold", "700", "800", "900") else "regular"
            style = "italic" if block.get("style") in ("italic", "oblique") else "normal"

            align_map = {"center": "center", "right": "right", "justify": "left", "left": "left"}
            align_type = align_map.get(str(block.get("align", "left")).lower(), "left")

            color_hex = str(block.get("color", "#000000")).strip()
            if not color_hex.startswith("#") or len(color_hex) not in (4, 7):
                color_hex = "#000000"

            if tier == TIER_TIMELINE_LABEL and len(raw_text) < 20:
                is_multi = False
            else:
                is_multi = _is_multiline_block(block, raw_text, height, float(orig_font_size))
            is_multi_str = "true" if is_multi else "false"

            if block.get("is_vertical"):
                vert_max = min(max_size, 9.0)
                vert_min = max(4.0, vert_max * 0.4)
                clean_vert_text = escaped_text.replace(" \\\\ ", " ")
                if "(" in clean_vert_text and not clean_vert_text.startswith("("):
                    p_before, p_after = clean_vert_text.split("(", 1)
                    clean_vert_text = p_before.strip() + " \\\\ (" + p_after.strip()
                vert_box_h = max(height, 16.0)
                lines.append(f"// Vertical {prefix} {i} [tier={tier}]: [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}]")
                lines.append(f"#place(top + left, dx: {x0:.2f}pt, dy: {y0:.2f}pt, box(width: {width:.2f}pt, height: {height:.2f}pt, clip: true, align(center + horizon)[#rotate(-90deg, reflow: false)[#box(width: {height:.2f}pt, height: {vert_box_h:.2f}pt, [#pdftr_fit_text([{clean_vert_text}], max_size: {vert_max:.2f}pt, min_size: {vert_min:.2f}pt, fit_height: {vert_box_h:.2f}pt, is_multiline: false, weight: \"{weight}\", style: \"{style}\", align_type: center, fill_color: rgb(\"{color_hex}\"))])]]))")
                lines.append("")
                continue

            lines.append(f"// {prefix} {i} [tier={tier}]: [{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}]")
            lines.append(f"#place(")
            lines.append(f"  top + left,")
            lines.append(f"  dx: {effective_x0:.2f}pt,")
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
            found_src = False
            for lang_code in ("ja", "en", "vi"):
                if lang_code == target_lang_canonical:
                    continue
                src = _get_field(block, lang_code)
                if src and isinstance(src, str):
                    _add_pair(src, target)
                    found_src = True

            # Fallback: use combined_text as source (standard AIWF extraction key)
            if not found_src:
                ct = block.get("combined_text")
                if ct and isinstance(ct, str):
                    _add_pair(ct, target)

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
    threshold: float = 0.60,
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

    # Substring match on compact representation (strictly scoped for OCR fragmented lines)
    if len(comp) >= 6:
        for k_comp, target in compact_map.items():
            if len(k_comp) >= 6:
                if comp in k_comp or k_comp in comp:
                    ratio = min(len(comp), len(k_comp)) / max(len(comp), len(k_comp))
                    # Upgrade #1.5: Require high ratio (>= 0.85) to prevent a partial sentence
                    # from incorrectly receiving an entire multi-sentence paragraph translation
                    if ratio >= 0.85:
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
    min_gap: float = 0.5,
) -> bool:
    """Check if a candidate bounding box overlaps with any existing rendered block."""
    cr = pymupdf.Rect(candidate_bbox)
    for eb in existing_bboxes:
        er = pymupdf.Rect(eb)
        if cr.intersects(pymupdf.Rect(er.x0 - min_gap, er.y0 - min_gap, er.x1 + min_gap, er.y1 + min_gap)):
            ix0 = max(cr.x0, er.x0)
            iy0 = max(cr.y0, er.y0)
            ix1 = min(cr.x1, er.x1)
            iy1 = min(cr.y1, er.y1)
            if ix1 > ix0 + 0.3 and iy1 > iy0 + 0.3:
                return True
    return False


def _compute_safe_expansion_budget(
    bx: List[float],
    raw_blocks: List[Dict[str, Any]],
    current_b: Dict[str, Any],
    page_width: float,
    page_height: float,
    align_type: str = "left",
    container_rect: Optional[List[float]] = None,
    is_vertical: bool = False,
    page_mode: str = "TEXT_ONLY",
    existing_rendered_bboxes: Optional[List[List[float]]] = None,
) -> Tuple[float, float, float, float]:
    """Computes safe, collision-free expanded bounding box without cascading displacement."""
    x0, y0, x1, y1 = bx[0], max(4.0, bx[1]), bx[2], max(bx[1] + 6.0, bx[3])
    w = max(4.0, x1 - x0)
    h = max(4.0, y1 - y0)

    if is_vertical:
        return x0, y0, x1, y1

    tier = current_b.get("block_tier", TIER_BODY)
    text = current_b.get("text", "")

    # Set page margin boundaries (protect edge safety)
    min_x = 8.0
    max_x = page_width - 16.0
    min_y = 4.0
    max_y = page_height - 6.0

    # If inside container, check if it's a tight heading badge vs a real layout container
    is_badge = False
    if container_rect:
        c_x0, c_y0, c_x1, c_y1 = container_rect
        c_w = c_x1 - c_x0
        c_h = c_y1 - c_y0
        if c_h < 30.0 and c_w < 180.0 and tier in (TIER_HEADING, TIER_TITLE):
            is_badge = True
            min_x = max(min_x, c_x0 + 2.0)
            min_y = max(min_y, c_y0 + 2.0)
        elif c_w > page_width * 0.70 and c_h > page_height * 0.40:
            # Full-page / multi-column background container
            min_x = max(min_x, c_x0 + 4.0)
            max_x = min(max_x, c_x1 - 4.0)
            min_y = max(min_y, c_y0 + 3.0)
            max_y = min(max_y, c_y1 - 3.0)
        else:
            min_x = max(min_x, c_x0 + 4.0)
            max_x = min(max_x, c_x1 - 4.0)
            min_y = max(min_y, c_y0 + 3.0)
            max_y = min(max_y, c_y1 - 3.0)

    left_limit = min_x
    right_limit = max_x

    # Scan all blocks on page for horizontal neighbors in the same vertical slice
    for ob in raw_blocks:
        if ob is current_b:
            continue
        obx = ob.get("bbox", [0, 0, 0, 0])
        if max(y0, obx[1]) < min(y1, obx[3]) - 0.5:
            if obx[2] <= x0 + 1.0:
                left_limit = max(left_limit, obx[2] + 4.0)
            if obx[0] >= x1 - 1.0:
                right_limit = min(right_limit, obx[0] - 4.0)

    # Two-column / timeline boundary check: only constrain timeline or diagram labels in column 1
    if tier in (TIER_TIMELINE_LABEL, TIER_DIAGRAM_LABEL) and x1 <= 165.0 and right_limit > 165.0:
        right_limit = min(right_limit, 165.0)

    new_x0 = x0
    new_y0 = y0
    new_x1 = x1
    new_y1 = y1

    if container_rect and not is_badge:
        siblings_in_container = [
            ob for ob in raw_blocks
            if ob is not current_b and ob.get("container_rect") == container_rect
        ]
        if not siblings_in_container:
            new_x0 = left_limit
            new_x1 = right_limit
        else:
            if align_type == "right":
                new_x0 = max(left_limit, x0 - 80.0)
                new_x1 = min(right_limit, x1 + 10.0)
            elif align_type == "center":
                mid = (x0 + x1) / 2.0
                span = min(mid - left_limit, right_limit - mid, 100.0)
                new_x0 = max(left_limit, mid - span)
                new_x1 = min(right_limit, mid + span)
            else:
                new_x0 = max(left_limit, x0 - 4.0)
                new_x1 = min(right_limit, x1 + 120.0)
    else:
        if align_type == "right":
            max_left = 180.0 if tier in (TIER_HEADING, TIER_TITLE, TIER_BODY) else 80.0
            new_x0 = max(left_limit, x0 - max_left)
            new_x1 = min(right_limit, x1 + 8.0)
        elif align_type == "center":
            max_span = 140.0 if tier in (TIER_HEADING, TIER_TITLE) else 70.0
            mid = (x0 + x1) / 2.0
            span = min(mid - left_limit, right_limit - mid, max_span)
            new_x0 = max(left_limit, mid - span)
            new_x1 = min(right_limit, mid + span)
        else:
            if tier == TIER_TABLE_CELL or current_b.get("is_table_cell"):
                max_right = min(25.0, max(0.0, (right_limit - x1) * 0.6))
            else:
                max_right = 320.0 if tier in (TIER_HEADING, TIER_TITLE, TIER_BODY) else 120.0
            new_x0 = max(left_limit, x0 - 2.0)
            new_x1 = min(right_limit, x1 + max_right)

    # Scan bottom limit against ALL raw blocks that intersect [new_x0, new_x1]
    bottom_limit = max_y
    for ob in raw_blocks:
        if ob is current_b:
            continue
        obx = ob.get("bbox", [0, 0, 0, 0])
        if max(new_x0, obx[0]) < min(new_x1, obx[2]) - 1.0:
            if obx[1] >= y1 - 0.5:
                bottom_limit = min(bottom_limit, obx[1] - 2.0)

    if bottom_limit > y1 + 3.0:
        if h < 14.0 and len(text) > 12:
            new_y1 = min(bottom_limit, y1 + 12.0)
        elif tier == TIER_BODY:
            new_y1 = min(bottom_limit, y1 + 20.0)
        elif tier in (TIER_TABLE_CELL, TIER_DIAGRAM_LABEL):
            new_y1 = min(bottom_limit, y1 + 8.0)

    if existing_rendered_bboxes:
        cand = pymupdf.Rect(new_x0, new_y0, new_x1, new_y1)
        for eb in existing_rendered_bboxes:
            er = pymupdf.Rect(eb)
            ix0 = max(cand.x0, er.x0)
            iy0 = max(cand.y0, er.y0)
            ix1 = min(cand.x1, er.x1)
            iy1 = min(cand.y1, er.y1)
            if ix1 > ix0 + 0.3 and iy1 > iy0 + 0.3:
                # Collision detected with an earlier rendered block: rollback horizontal
                new_x0, new_x1 = x0, x1
                cand_y = pymupdf.Rect(x0, new_y0, x1, new_y1)
                if cand_y.intersects(pymupdf.Rect(er.x0 + 0.2, er.y0 + 0.2, er.x1 - 0.2, er.y1 - 0.2)):
                    new_y1 = y1
                break

    return new_x0, new_y0, new_x1, new_y1


# ---------------------------------------------------------------------------
# Main Overlay Pipeline (Smart Reflow v4.0)
# ---------------------------------------------------------------------------

def preserve_pdf_typst(
    source_pdf_path: Path,
    blocks: list[dict],
    lang: str,
    output_pdf_path: Path,
    strict_parity: bool = True,
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

            # Decompose blocks with horizontally disjoint lines & clean empty lines
            split_raw_blocks = []
            for b in raw_blocks:
                lines = [
                    l for l in b.get("lines", [])
                    if "".join(s.get("text", "") for s in l.get("spans", [])).strip()
                ]
                if not lines:
                    continue
                if len(lines) <= 1:
                    new_b = dict(b)
                    new_b["lines"] = lines
                    new_b["bbox"] = [
                        min(l["bbox"][0] for l in lines),
                        min(l["bbox"][1] for l in lines),
                        max(l["bbox"][2] for l in lines),
                        max(l["bbox"][3] for l in lines),
                    ]
                    split_raw_blocks.append(new_b)
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
                    new_b = dict(b)
                    new_b["lines"] = lines
                    new_b["bbox"] = [
                        min(l["bbox"][0] for l in lines),
                        min(l["bbox"][1] for l in lines),
                        max(l["bbox"][2] for l in lines),
                        max(l["bbox"][3] for l in lines),
                    ]
                    split_raw_blocks.append(new_b)
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

            # --- Module F: Line-Level Sub-Block Splitting ---
            # Split mega-blocks (>12 lines) into sub-blocks at numbered items and headings
            _SPLIT_RE = re.compile(
                r'^\s*(?:'
                r'\d{1,2}\)\s|'           # "1) " "10) "
                r'\d{1,2}）\s*|'          # "1）" fullwidth
                r'\d{1,2}\.\s+(?!\d)|'   # "1. " but not "1.2"
                r'\d{1,2}\.\d{1,2}\s|'   # "9.4 "
                r'第\s*\d|'               # "第1"
                r'[①-⑩]\s*|'             # circled numbers
                r'Section\s|Article\s|Chapter\s'
                r')'
            )
            expanded_blocks = []
            for b in raw_blocks:
                b_lines = b.get("lines", [])
                if len(b_lines) < 12:
                    expanded_blocks.append(b)
                    continue
                # Scan for split points
                split_idxs = [0]
                for li, line in enumerate(b_lines):
                    if li == 0:
                        continue
                    lt = "".join(s.get("text", "") for s in line.get("spans", [])).strip()
                    spans = line.get("spans", [])
                    is_line_bold = any(
                        (s.get("flags", 0) & 16) or "bold" in s.get("font", "").lower()
                        for s in spans
                    ) if spans else False
                    is_short = len(lt) < 60
                    # Split at numbered items
                    if _SPLIT_RE.match(lt):
                        split_idxs.append(li)
                    # Split at bold heading transitions
                    elif is_line_bold and is_short and li > 0:
                        prev_spans = b_lines[li - 1].get("spans", [])
                        prev_bold = any(
                            (s.get("flags", 0) & 16) or "bold" in s.get("font", "").lower()
                            for s in prev_spans
                        ) if prev_spans else False
                        if not prev_bold:
                            split_idxs.append(li)
                if len(split_idxs) <= 1:
                    expanded_blocks.append(b)
                    continue
                # Create sub-blocks
                for si, start_li in enumerate(split_idxs):
                    end_li = split_idxs[si + 1] if si + 1 < len(split_idxs) else len(b_lines)
                    sub_lines = b_lines[start_li:end_li]
                    if not sub_lines:
                        continue
                    sub_y0 = min(l["bbox"][1] for l in sub_lines)
                    sub_y1 = max(l["bbox"][3] for l in sub_lines)
                    sub_x0 = min(l["bbox"][0] for l in sub_lines)
                    sub_x1 = max(l["bbox"][2] for l in sub_lines)
                    sub_b = dict(b)
                    sub_b["lines"] = sub_lines
                    sub_b["bbox"] = [sub_x0, sub_y0, sub_x1, sub_y1]
                    expanded_blocks.append(sub_b)
            raw_blocks = expanded_blocks

            # Detect all vector containers (including callout boxes and diagram nodes)
            raw_blocks = _detect_all_containers(page, raw_blocks)

            # Geometric reading-order sort: snap top to 8pt line grid, then x
            raw_blocks.sort(key=lambda b: (round(b["bbox"][1] / 8.0) * 8.0, b["bbox"][0]))
            for idx, b in enumerate(raw_blocks):
                b["source_block_id"] = f"p{page_idx}_b{idx}"

            # Classify page mode FIRST (needed for adaptive table cell detection)
            page_mode = _classify_page_mode(page, raw_blocks)

            # Detect table cells (Page-Mode Adaptive threshold)
            for b in raw_blocks:
                bx = b["bbox"]
                b_area = (bx[2] - bx[0]) * (bx[3] - bx[1])
                same_band = [
                    ob for ob in raw_blocks
                    if ob is not b
                    and abs(ob["bbox"][1] - bx[1]) < 5.0
                    and abs(ob["bbox"][3] - bx[3]) < 5.0
                ]
                # Page-Mode Adaptive: MIXED/CONSTRAINED need >=2 neighbors (strict)
                # TEXT_ONLY can use >=1 (relaxed) since no images to confuse
                min_neighbors = 1 if page_mode == PAGE_MODE_TEXT_ONLY else 2
                b["is_table_cell"] = (len(same_band) >= min_neighbors and b_area < 8000)

            # --- Module D: Expanded list markers (EN + JP) ---
            LIST_MARKERS = (
                "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩",
                "・", "●", "■", "◆", "▶", "▪",
                "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.",
                "1)", "2)", "3)", "4)", "5)", "6)", "7)", "8)", "9)",
                "(1)", "(2)", "(3)", "(4)", "(5)",
                "[1]", "[2]", "[3]", "[4]", "[5]",
                "a)", "b)", "c)", "d)", "e)",
                "•", "–", "—",
            )
            LABEL_MARKERS = (
                "期 間：", "期間：", "場 所：", "場所：", "参加者：", "日 時：", "日時：",
                "活動①", "活動②", "活動③", "活動④", "活動⑤",
            )
            # Section heading patterns (JP + EN)
            _HEADING_RE = re.compile(
                r'^\s*(?:'
                r'\d{1,2}\.\s|'          # "1. " "10. "
                r'\d{1,2}\.\d{1,2}\s|'   # "9.4 " "10.1 "
                r'\d{1,2}\.\d\.\d\s|'    # "8.1.2 "
                r'第\s*\d|'               # "第1" "第 2"
                r'[IVXLCDM]+\.\s|'       # Roman numerals
                r'（[0-9一二三四五六七八九十]+）|'
                r'Section\s|Article\s|Chapter\s'
                r')'
            )

            def _get_block_font_info(b):
                """Extract dominant font size, weight, flags from a raw block."""
                sizes, bolds = [], 0
                for l in b.get("lines", []):
                    for s in l.get("spans", []):
                        sz = s.get("size", 10.0)
                        sizes.append(sz)
                        fl = s.get("flags", 0)
                        if (fl & 16) or "bold" in s.get("font", "").lower():
                            bolds += 1
                avg_size = sum(sizes) / len(sizes) if sizes else 10.0
                is_bold = bolds > len(sizes) * 0.5
                return avg_size, is_bold

            # --- Module A: Smart paragraph break detection ---
            # page_mode captured from enclosing scope for adaptive thresholds
            def can_merge(b1, b2, current_group_size=0):
                # A4: Max group size limit — allow long narrative paragraphs (up to 18 lines)
                if current_group_size >= 18:
                    return False

                if b1.get("is_table_cell") or b2.get("is_table_cell"):
                    return False
                bx1, bx2 = b1["bbox"], b2["bbox"]
                step_y = bx2[1] - bx1[1]

                fs1, bold1 = _get_block_font_info(b1)
                line_fs = fs1 if fs1 > 0 else 10.0
                # Adaptive step_y: accounts for line font size and leading
                max_step = max(24.0, line_fs * 2.3) if page_mode == PAGE_MODE_TEXT_ONLY else max(22.0, line_fs * 2.1)
                if not (3.0 <= step_y <= max_step):
                    return False

                # A1: Heading detection breaker
                t2_str = "".join(s.get("text", "") for l in b2.get("lines", []) for s in l.get("spans", [])).strip()
                t1_str = "".join(s.get("text", "") for l in b1.get("lines", []) for s in l.get("spans", [])).strip()

                # Break if b2 starts with a section heading pattern
                if _HEADING_RE.match(t2_str):
                    fs2, bold2 = _get_block_font_info(b2)
                    # If heading-like: bold or larger font → do NOT merge
                    if bold2 or fs2 >= fs1 * 1.05:
                        return False
                    # Even if same size/weight, numbered headings at start of line = new section
                    if len(t2_str) < 80:
                        return False

                # A3: Font style change breaker
                fs2, bold2 = _get_block_font_info(b2)
                # Bold ↔ regular transition = new paragraph
                if bold1 != bold2:
                    return False
                # Font size change > 1.5pt = different section
                if abs(fs1 - fs2) > 1.5:
                    return False

                # W4: Centered heading guard — only for MIXED/CONSTRAINED pages
                if page_mode != PAGE_MODE_TEXT_ONLY:
                    page_center = w / 2.0
                    b2_center = (bx2[0] + bx2[2]) / 2.0
                    b2_width = bx2[2] - bx2[0]
                    if abs(b2_center - page_center) < 40.0 and b2_width < w * 0.6 and len(t2_str) < 60:
                        return False

                diff_x = abs(bx1[0] - bx2[0])
                max_indent = max(20.0, line_fs * 2.0) if page_mode == PAGE_MODE_TEXT_ONLY else max(16.0, line_fs * 1.6)
                is_first_line_indent = (bx1[0] >= bx2[0] - 2.0 and diff_x <= max_indent)
                is_hanging_indent = (bx2[0] >= bx1[0] - 2.0 and diff_x <= 18.0)
                is_aligned = (diff_x <= 8.0)
                if not (is_aligned or is_first_line_indent or is_hanging_indent):
                    return False

                # Module D3: Indent-based sub-item detection
                # If b2 is indented > 18pt deeper than b1, it's a sub-item → don't merge
                if bx2[0] > bx1[0] + 18.0 and diff_x > 18.0:
                    return False

                w1, w2 = bx1[2] - bx1[0], bx2[2] - bx2[0]
                if w2 > w1 * 1.8 and w1 < 160.0:
                    return False
                t1_len = sum(len(s.get("text", "")) for l in b1.get("lines", []) for s in l.get("spans", []))
                if t1_len <= 12 and (bx2[3] - bx2[1]) > (bx1[3] - bx1[1]) * 1.5:
                    return False

                # A2: Paragraph end detection — short last line = paragraph break
                # Only apply if b1 already has multiple lines
                if len(b1.get("lines", [])) >= 2:
                    last_line = b1.get("lines", [])[-1]
                    ll_bbox = last_line.get("bbox", [0, 0, 0, 0])
                    ll_width = ll_bbox[2] - ll_bbox[0]
                    page_content_w = w
                    margin_adjusted = page_content_w - 108.0
                    if margin_adjusted > 100 and ll_width < margin_adjusted * 0.65:
                        return False

                # List marker check (expanded Module D)
                if t2_str.startswith(LIST_MARKERS) or t2_str.startswith(LABEL_MARKERS):
                    return False
                if t1_str.startswith(("活動①", "活動②", "活動③", "活動④", "活動⑤")):
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
                while i + 1 < len(raw_blocks) and can_merge(grp[-1], raw_blocks[i + 1], current_group_size=len(grp)):
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
                        # --- Module B: Majority style calculation ---
                        # Collect font info from ALL spans in the group (not just first_span)
                        all_sizes, bold_count, italic_count, total_spans = [], 0, 0, 0
                        color_counts: Dict[int, int] = {}
                        for b in group:
                            for l in b.get("lines", []):
                                for s in l.get("spans", []):
                                    total_spans += 1
                                    all_sizes.append(s.get("size", 10.0))
                                    fl = s.get("flags", 0)
                                    if (fl & 16) or "bold" in s.get("font", "").lower():
                                        bold_count += 1
                                    if (fl & 2) or "italic" in s.get("font", "").lower():
                                        italic_count += 1
                                    c_int = s.get("color", 0)
                                    color_counts[c_int] = color_counts.get(c_int, 0) + 1

                        # Use median font size and majority weight/style
                        all_sizes.sort()
                        fs = all_sizes[len(all_sizes) // 2] if all_sizes else 10.0
                        is_b = bold_count > total_spans * 0.5  # majority bold
                        is_it = italic_count > total_spans * 0.5  # majority italic
                        dominant_color = max(color_counts, key=color_counts.get) if color_counts else 0
                        c_hex = f"#{dominant_color:06x}" if dominant_color else "#000000"

                        is_cont = any(b.get("is_in_container") for b in group)
                        container = next((b.get("container_rect") for b in group if b.get("container_rect")), None)

                        # For blocks in container, use container bounds with clean inner margins
                        if is_cont and container:
                            # Check if other blocks exist to the right inside the container
                            right_lim = container[2] - 5.0
                            for other_b in raw_blocks:
                                if any(other_b is gb for gb in group):
                                    continue
                                obx = other_b["bbox"]
                                if max(pad_box[1], obx[1]) < min(pad_box[3], obx[3]) + 2.0:
                                    if obx[0] >= pad_box[2] - 4.0:
                                        right_lim = min(right_lim, obx[0] - 8.0)
                            render_right = min(pad_box[2], right_lim) if right_lim < container[2] - 5.0 else min(pad_box[2], container[2] - 5.0)
                            r_bbox = [
                                max(pad_box[0], container[0] + 5.0),
                                max(pad_box[1], container[1] + 3.0),
                                render_right,
                                min(h, container[3] - 5.0),
                            ]
                        else:
                            r_bbox = pad_box

                        # --- Module C+G: Adaptive height expansion with cascade fallback ---
                        if not is_cont:
                            # Estimate if translated text will need more vertical space
                            char_count = len(trans)
                            box_w = r_bbox[2] - r_bbox[0]
                            box_h = r_bbox[3] - r_bbox[1]
                            est_chars_per_line = max(1, (box_w / (fs * 0.50)) * 0.85)
                            est_lines = max(1, math.ceil(char_count / est_chars_per_line))
                            needed_h = est_lines * fs * 1.35 + 4.0
                            if needed_h > box_h:
                                # Module G: Try progressive expansion ratios (50% → 10%)
                                expanded = False
                                for ratio in [1.50, 1.40, 1.30, 1.20, 1.10]:
                                    candidate_h = min(needed_h, box_h * ratio)
                                    candidate_bbox = [r_bbox[0], r_bbox[1], r_bbox[2], r_bbox[1] + candidate_h]
                                    if not _check_2d_overlap(candidate_bbox, page_bboxes):
                                        r_bbox = candidate_bbox
                                        expanded = True
                                        break
                                # If still couldn't expand, try reducing font as last resort
                                if not expanded and fs > 7.5:
                                    reduced_fs = max(7.0, fs - 1.0)
                                    re_cpl = max(1, (box_w / (reduced_fs * 0.50)) * 0.85)
                                    re_lines = max(1, math.ceil(char_count / re_cpl))
                                    re_needed = re_lines * reduced_fs * 1.35 + 4.0
                                    if re_needed <= box_h * 1.30:
                                        candidate_bbox = [r_bbox[0], r_bbox[1], r_bbox[2], r_bbox[1] + min(re_needed, box_h * 1.30)]
                                        if not _check_2d_overlap(candidate_bbox, page_bboxes):
                                            r_bbox = candidate_bbox
                                            fs = reduced_fs

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

                        # --- Module E: Quality gate warning ---
                        if len(trans) > 500:
                            _clip_warnings.append({
                                "page": page_idx,
                                "type": "oversized_merged_block",
                                "char_count": len(trans),
                                "bbox": r_bbox,
                            })

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

                    # Special header handling
                    is_header_title = (bx[1] < 55.0 and bx[0] > 80.0 and b_w > 180.0)
                    is_society_header = (bx[1] < 85.0 and bx[0] > 350.0 and b_w > 100.0)

                    align = "left"
                    if is_society_header:
                        align = "right"
                    else:
                        mid_x = (bx[0] + bx[2]) / 2.0
                        is_bullet = any(translated.strip().startswith(p) for p in ("•", "-", "●", "①", "②", "③", "1.", "2.", "3.", "*"))
                        is_multi_line = len(b.get("lines", [])) > 1 or "\n" in translated or (b_h >= font_size * 1.20 and len(translated) > 20)

                        # Check for timeline month headers (e.g. "Tháng 5", "5月")
                        is_month_header = bool(re.search(r'^(?:tháng\s*\d{1,2}|\d{1,2}\s*月)$', translated.strip().lower()))
                        if is_month_header:
                            is_multi_line = False
                            align = "center"
                        elif not is_vert and not is_bullet and not is_multi_line:
                            if abs(mid_x - (w / 2.0)) < 35.0 and (bx[2] - bx[0]) < 220.0:
                                align = "center"
                            elif bx[0] > (w * 0.65) and (bx[2] - bx[0]) < 200.0:
                                align = "right"
                            elif is_container and container:
                                align = "center"

                    temp_block = {
                        "bbox": bx,
                        "text": translated,
                        "font_size": font_size,
                        "weight": "bold" if is_bold else "regular",
                        "align": align,
                        "is_vertical": is_vert,
                        "is_in_container": is_container,
                        "is_in_diagram": is_diagram,
                        "is_table_cell": b.get("is_table_cell", False),
                    }
                    tier = _classify_block_tier(temp_block, w, h)
                    temp_block["block_tier"] = tier

                    render_x0, render_y0, render_x1, render_y1 = _compute_safe_expansion_budget(
                        bx=bx,
                        raw_blocks=raw_blocks,
                        current_b=temp_block,
                        page_width=w,
                        page_height=h,
                        align_type=align,
                        container_rect=container if is_container else None,
                        is_vertical=is_vert,
                        page_mode=page_mode,
                        existing_rendered_bboxes=page_bboxes,
                    )

                    if is_header_title:
                        render_x1 = min(w - 54.0, max(render_x1, bx[0] + 440.0))
                    elif is_society_header:
                        render_x0 = max(180.0, min(render_x0, bx[0] - 200.0))
                    elif is_month_header and (render_x1 - render_x0) < 36.0:
                        cx = (bx[0] + bx[2]) / 2.0
                        render_x0 = max(2.0, cx - 18.0)
                        render_x1 = min(w - 2.0, cx + 18.0)

                    if is_vert:
                        render_x1 = bx[0] + max(b_w, 14.0)
                        render_y1 = bx[3]

                    render_bbox = [render_x0, render_y0, render_x1, min(h, render_y1)]
                    padded_bbox = [render_x0, render_y0, render_x1, min(h, render_y1)]

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
                        "block_tier": tier,
                    }
                    render_blocks.append(single_block_data)
                    page_bboxes.append(padded_bbox)

            # --- Module J: Deterministic Deduplication Pass ---
            # Suppress duplicate overlays where the same content or a parent/child
            # representation was already placed with high spatial overlap.
            if len(render_blocks) > 1:
                deduped = []
                for b in render_blocks:
                    b_bbox = b["bbox"]
                    b_area = max(1.0, (b_bbox[2] - b_bbox[0]) * (b_bbox[3] - b_bbox[1]))
                    b_text = b["text"].strip()
                    is_dup = False
                    for kept in deduped:
                        k_bbox = kept["bbox"]
                        k_area = max(1.0, (k_bbox[2] - k_bbox[0]) * (k_bbox[3] - k_bbox[1]))
                        k_text = kept["text"].strip()

                        # Check bounding box intersection
                        ix0 = max(b_bbox[0], k_bbox[0])
                        iy0 = max(b_bbox[1], k_bbox[1])
                        ix1 = min(b_bbox[2], k_bbox[2])
                        iy1 = min(b_bbox[3], k_bbox[3])
                        if ix1 > ix0 and iy1 > iy0:
                            inter_area = (ix1 - ix0) * (iy1 - iy0)
                            iou = inter_area / (b_area + k_area - inter_area)
                            b_cov = inter_area / b_area
                            k_cov = inter_area / k_area

                            # 1. Identical/near-identical text with significant spatial overlap
                            if (b_text == k_text or _similarity(_normalise(b_text), _normalise(k_text)) > 0.85) and (iou > 0.35 or b_cov > 0.50 or k_cov > 0.50):
                                if len(b_text) > len(k_text) or b_area > k_area:
                                    kept.update(b)
                                is_dup = True
                                break

                            # 2. Parent-child text containment with strong area overlap
                            if b_cov > 0.60 or k_cov > 0.60:
                                norm_b = _normalise(b_text)
                                norm_k = _normalise(k_text)
                                if norm_b in norm_k or norm_k in norm_b:
                                    if len(b_text) > len(k_text):
                                        kept.update(b)
                                    is_dup = True
                                    break
                    if not is_dup:
                        deduped.append(b)
                render_blocks = deduped

            # --- Module I: Post-Placement Overlap Resolution ---
            # Scan all rendered blocks for vertical overlaps and resolve them safely
            if len(render_blocks) > 1:
                # Sort by y0 for sequential overlap detection
                render_blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
                for ri in range(len(render_blocks)):
                    rb = render_blocks[ri]
                    rb_bbox = rb["bbox"]
                    rb_y1 = rb_bbox[3]
                    # Skip non-text blocks (containers, diagrams stay fixed)
                    if rb.get("is_in_container") or rb.get("is_in_diagram"):
                        continue
                    for rj in range(ri + 1, len(render_blocks)):
                        rb2 = render_blocks[rj]
                        rb2_bbox = rb2["bbox"]
                        if rb2.get("is_in_container") or rb2.get("is_in_diagram"):
                            continue
                        # Check if rb overlaps rb2 vertically
                        overlap_y = rb_y1 - rb2_bbox[1]
                        if overlap_y <= 2.0:
                            break  # No more overlaps (sorted by y0)
                        # Check horizontal overlap too
                        x_overlap = min(rb_bbox[2], rb2_bbox[2]) - max(rb_bbox[0], rb2_bbox[0])
                        if x_overlap <= 5.0:
                            continue  # No horizontal overlap
                        # Resolve: truncate bottom of upper block safely (protect readability floor)
                        orig_h = rb_bbox[3] - rb_bbox[1]
                        new_y1 = rb2_bbox[1] - 1.5
                        if new_y1 >= rb_bbox[1] + max(8.0, orig_h * 0.80):
                            rb["bbox"] = [rb_bbox[0], rb_bbox[1], rb_bbox[2], new_y1]
                            rb_y1 = new_y1  # Update for subsequent checks
                # Also update page_bboxes to match resolved render_blocks
                page_bboxes = [b["bbox"] for b in render_blocks]

            # Apply Smart Reflow Y-Shift (or strict 1:1 parity)
            if strict_parity:
                current_blocks, overflow_blocks = render_blocks, []
            else:
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
