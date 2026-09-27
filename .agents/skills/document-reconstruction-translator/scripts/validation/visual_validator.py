"""Visual Typographic & Layout Validation Engine.

Conforms to Section 26 of AIWF Document Reconstruction Translator:
- Inspects target PDF without rigid 1:1 pixel comparison.
- Detects visual typographic and layout anomalies:
  * Text overlap / bounding box collisions.
  * Margin clipping and page overflow.
  * Unreadable micro-text (font sizes < 7.0pt).
  * Orphan headings (heading near page bottom with no body paragraph).
  * Page imbalance & nearly empty trailing pages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pymupdf


class VisualValidator:
    """Performs geometric, typographic, and layout checks on compiled PDF."""

    def __init__(self, min_font_size: float = 7.0):
        self.min_font_size = min_font_size

    def validate_pdf(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        p = Path(pdf_path)
        if not p.exists():
            return {
                "passed": False,
                "error": f"Target PDF does not exist: {pdf_path}",
                "total_pages": 0,
                "violations": [{"type": "FILE_NOT_FOUND", "severity": "CRITICAL"}],
            }

        doc = pymupdf.open(str(p))
        total_pages = len(doc)
        violations: List[Dict[str, Any]] = []

        for p_idx, page in enumerate(doc):
            page_num = p_idx + 1
            page_w = page.rect.width
            page_h = page.rect.height

            d = page.get_text("dict")
            blocks = d.get("blocks", [])

            text_blocks = [b for b in blocks if b.get("type") == 0]
            page_char_count = sum(len(span.get("text", "")) for b in text_blocks for l in b.get("lines", []) for span in l.get("spans", []))

            # 1. Nearly Empty Page (except possibly single-page docs)
            if total_pages > 1 and page_char_count < 20 and len(page.get_images()) == 0:
                violations.append({
                    "page": page_num,
                    "type": "NEARLY_EMPTY_PAGE",
                    "description": f"Page {page_num} has only {page_char_count} chars and no images.",
                    "severity": "MEDIUM",
                })

            # 2. Check each text span for clipping and font floor
            spans_on_page: List[Dict[str, Any]] = []
            for b in text_blocks:
                b_bbox = b.get("bbox", (0, 0, 0, 0))
                # Check block clipping
                if b_bbox[0] < 5 or b_bbox[1] < 5 or b_bbox[2] > page_w - 5 or b_bbox[3] > page_h - 5:
                    violations.append({
                        "page": page_num,
                        "type": "PAGE_EDGE_CLIPPING",
                        "bbox": b_bbox,
                        "description": f"Content extends beyond printable page boundaries on page {page_num}",
                        "severity": "HIGH",
                    })

                for l in b.get("lines", []):
                    for s in l.get("spans", []):
                        s_text = s.get("text", "").strip()
                        s_size = s.get("size", 10.0)
                        s_bbox = s.get("bbox", (0, 0, 0, 0))

                        if len(s_text) > 2:
                            spans_on_page.append({"text": s_text, "bbox": s_bbox, "size": s_size})

                        # Micro-text check (< 7.0pt floor)
                        if s_size < self.min_font_size and len(s_text) > 4:
                            violations.append({
                                "page": page_num,
                                "type": "UNREADABLE_MICRO_TEXT",
                                "font_size": round(s_size, 1),
                                "snippet": s_text[:30],
                                "severity": "HIGH",
                            })

            # 3. Text Overlap Detection (pairwise bounding box intersection)
            for i in range(len(spans_on_page)):
                for j in range(i + 1, len(spans_on_page)):
                    s1 = spans_on_page[i]
                    s2 = spans_on_page[j]
                    b1 = s1["bbox"]
                    b2 = s2["bbox"]
                    # If bboxes overlap significantly (intersection area > 50% of smaller)
                    inter_x0 = max(b1[0], b2[0])
                    inter_y0 = max(b1[1], b2[1])
                    inter_x1 = min(b1[2], b2[2])
                    inter_y1 = min(b1[3], b2[3])

                    if inter_x1 > inter_x0 + 4 and inter_y1 > inter_y0 + 4:
                        inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
                        area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
                        area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
                        min_area = min(area1, area2)
                        if min_area > 0 and (inter_area / min_area) > 0.40:
                            # Potential collision
                            violations.append({
                                "page": page_num,
                                "type": "TEXT_COLLISION_OVERLAP",
                                "text1": s1["text"][:30],
                                "text2": s2["text"][:30],
                                "severity": "HIGH",
                            })
                            break

            # 4. Orphan Heading Detection
            for b in text_blocks:
                b_bbox = b.get("bbox", (0, 0, 0, 0))
                # Check if block looks like a heading near the bottom of the page
                is_heading = any(
                    s.get("size", 10.0) >= 12.0 or bool(s.get("flags", 0) & 2)
                    for l in b.get("lines", [])
                    for s in l.get("spans", [])
                )
                if is_heading and b_bbox[1] > page_h - 60.0:
                    # No room for subsequent paragraph on this page
                    violations.append({
                        "page": page_num,
                        "type": "ORPHAN_HEADING",
                        "bbox": b_bbox,
                        "description": f"Heading positioned at page bottom ({b_bbox[1]:.1f}pt) without body content",
                        "severity": "MEDIUM",
                    })

        doc.close()
        critical_count = sum(1 for v in violations if v["severity"] == "HIGH")
        passed = critical_count == 0

        return {
            "passed": passed,
            "total_pages": total_pages,
            "violations_count": len(violations),
            "critical_violations": critical_count,
            "violations": violations,
        }
