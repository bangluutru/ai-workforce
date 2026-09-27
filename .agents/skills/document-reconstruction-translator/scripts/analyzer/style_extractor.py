"""Document Style Profile Extractor.

Conforms to Section 18 of AIWF Document Reconstruction Translator:
- Analyzes page geometry, margins, column structure, font hierarchies, line spacing,
  and color palette.
- Produces a DocumentStyleProfile for high-fidelity typographic reconstruction.
"""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

from ir.models import DocumentStyleProfile


class StyleExtractor:
    """Analyzes a PDF document to extract its characteristic style profile."""

    def extract_profile(self, doc: pymupdf.Document) -> DocumentStyleProfile:
        if len(doc) == 0:
            return DocumentStyleProfile()

        # 1. Page Geometry & Orientation
        first_page = doc[0]
        w, h = first_page.rect.width, first_page.rect.height
        orientation = "portrait" if h >= w else "landscape"

        # Match known paper sizes (within 5pt tolerance)
        page_size = "a4"
        if abs(w - 595.3) < 10 and abs(h - 841.9) < 10:
            page_size = "a4"
        elif abs(w - 612.0) < 10 and abs(h - 792.0) < 10:
            page_size = "letter"
        elif orientation == "landscape" and abs(w - 841.9) < 10 and abs(h - 595.3) < 10:
            page_size = "a4"

        # 2. Margins (analyze text bounding boxes across pages)
        min_x_list: List[float] = []
        min_y_list: List[float] = []
        max_x_list: List[float] = []
        max_y_list: List[float] = []

        font_sizes: List[float] = []
        font_names: List[str] = []
        font_colors: List[str] = []

        for p_idx in range(min(5, len(doc))):
            page = doc[p_idx]
            page_w, page_h = page.rect.width, page.rect.height
            d = page.get_text("dict")
            for b in d.get("blocks", []):
                if b.get("type") == 0:  # text
                    bbox = b.get("bbox", (0, 0, 0, 0))
                    # Avoid extreme headers/footers when calculating general margins
                    if 30 < bbox[1] < page_h - 30:
                        min_x_list.append(bbox[0])
                        max_x_list.append(page_w - bbox[2])
                    if bbox[1] > 20:
                        min_y_list.append(bbox[1])
                    if bbox[3] < page_h - 20:
                        max_y_list.append(page_h - bbox[3])

                    for l in b.get("lines", []):
                        for s in l.get("spans", []):
                            text = s.get("text", "").strip()
                            if len(text) > 1:
                                font_sizes.append(round(s.get("size", 10.0), 1))
                                f_name = s.get("font", "Times New Roman")
                                # Clean font name prefixes (e.g. ABCDEF+Arial -> Arial)
                                if "+" in f_name:
                                    f_name = f_name.split("+")[-1]
                                font_names.append(f_name)

                                color_int = s.get("color", 0)
                                if color_int != 0:
                                    # Convert int to hex
                                    r = (color_int >> 16) & 0xFF
                                    g = (color_int >> 8) & 0xFF
                                    b_val = color_int & 0xFF
                                    font_colors.append(f"#{r:02x}{g:02x}{b_val:02x}")

        margin_left = statistics.median(min_x_list) if min_x_list else 56.7
        margin_right = statistics.median(max_x_list) if max_x_list else 56.7
        margin_top = statistics.median(min_y_list) if min_y_list else 56.7
        margin_bottom = statistics.median(max_y_list) if max_y_list else 56.7

        # Clamp margins to safe typographic bounds
        margin_left = max(28.3, min(margin_left, 85.0))
        margin_right = max(28.3, min(margin_right, 85.0))
        margin_top = max(28.3, min(margin_top, 85.0))
        margin_bottom = max(28.3, min(margin_bottom, 85.0))

        # 3. Typography & Hierarchy
        body_font_size = 10.0
        heading_scale = [18.0, 14.0, 12.0]
        dominant_font = "Times New Roman"

        if font_sizes:
            # Body font size is typically the most frequent font size (mode)
            size_counts = Counter(font_sizes)
            body_font_size = size_counts.most_common(1)[0][0]
            # Ensure reasonable floor
            if body_font_size < 8.0:
                body_font_size = 10.0

            larger_sizes = sorted([s for s in size_counts.keys() if s > body_font_size + 1.0], reverse=True)
            if len(larger_sizes) >= 3:
                heading_scale = larger_sizes[:3]
            elif len(larger_sizes) == 2:
                heading_scale = [larger_sizes[0], larger_sizes[1], body_font_size + 2.0]
            elif len(larger_sizes) == 1:
                heading_scale = [larger_sizes[0] + 2.0, larger_sizes[0], body_font_size + 2.0]
            else:
                heading_scale = [body_font_size + 6.0, body_font_size + 4.0, body_font_size + 2.0]

        if font_names:
            font_counts = Counter(font_names)
            dominant_font = font_counts.most_common(1)[0][0]

        # 4. Accent Colors
        accent_color = "#1a5fb4"
        if font_colors:
            color_counts = Counter(font_colors)
            for c, _ in color_counts.most_common():
                if c.lower() not in ("#000000", "#ffffff", "#111111", "#222222", "#333333"):
                    accent_color = c
                    break

        # 5. Detect Multi-column
        # If text blocks cluster around 2 distinct X centers
        col_count = 1
        x_centers = []
        for p_idx in range(min(3, len(doc))):
            d = doc[p_idx].get_text("dict")
            for b in d.get("blocks", []):
                if b.get("type") == 0:
                    bbox = b.get("bbox", (0, 0, 0, 0))
                    width = bbox[2] - bbox[0]
                    # If width is less than half the printable area, likely multi-column
                    if width < (w - margin_left - margin_right) * 0.55 and width > 100:
                        x_centers.append(bbox[0])

        if len(x_centers) >= 6:
            # Check if there are two distinct clusters (e.g. left col vs right col)
            left_col = [x for x in x_centers if x < w * 0.45]
            right_col = [x for x in x_centers if x > w * 0.45]
            if len(left_col) >= 3 and len(right_col) >= 3:
                col_count = 2

        return DocumentStyleProfile(
            page_size=page_size,
            orientation=orientation,
            page_width_pt=round(w, 2),
            page_height_pt=round(h, 2),
            margin_top_pt=round(margin_top, 2),
            margin_bottom_pt=round(margin_bottom, 2),
            margin_left_pt=round(margin_left, 2),
            margin_right_pt=round(margin_right, 2),
            column_count=col_count,
            column_gap_pt=14.2 if col_count > 1 else 0.0,
            dominant_body_font=dominant_font,
            dominant_heading_font="Arial" if "Arial" in dominant_font or "Sans" in dominant_font else dominant_font,
            body_font_size=round(body_font_size, 1),
            heading_scale=[round(s, 1) for s in heading_scale],
            line_height_em=0.65,
            paragraph_spacing_em=0.70,
            primary_color_hex="#000000",
            accent_color_hex=accent_color,
            table_border_width_pt=0.5,
            table_cell_padding_pt=4.0,
            caption_font_size=round(max(7.5, body_font_size - 1.5), 1),
            caption_alignment="center",
        )
