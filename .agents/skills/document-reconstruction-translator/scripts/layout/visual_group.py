"""Visual Grouping and Atomic Keep-Together Logic.

Part of AIWF Translation Upgrade #1.6 (Part H, Sections 34-36 & Part G, Sections 23-26):
- Treats related image + caption + note as VisualGroup.
- Prevents image on page N and caption on page N+1.
- Maintains ordering, grouping, and relative hierarchy for image grids.
- Emits structured VisualGroup evidence (image_id, image_bbox, caption_id, caption_bbox,
  association_method, distance, reading_order, keep_together, final_page).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pymupdf


@dataclass
class VisualGroup:
    """An atomic grouping of visual content (e.g. image + caption) that must stay together."""
    group_id: str
    page_idx: int
    image_rect: Tuple[float, float, float, float]
    caption_rects: List[Tuple[float, float, float, float]] = field(default_factory=list)
    caption_texts: List[str] = field(default_factory=list)
    bounding_box: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    keep_together: bool = True
    image_id: str = ""
    image_bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    caption_id: Optional[str] = None
    caption_bbox: Optional[Tuple[float, float, float, float]] = None
    association_method: str = "DIRECT_BELOW"
    distance: float = 0.0
    reading_order: int = 0
    final_page: int = 1

    def __post_init__(self):
        if not self.image_bbox or self.image_bbox == (0.0, 0.0, 0.0, 0.0):
            self.image_bbox = self.image_rect
        if not self.image_id:
            self.image_id = self.group_id
        if self.caption_rects and not self.caption_bbox:
            self.caption_bbox = self.caption_rects[0]
        if not self.final_page:
            self.final_page = self.page_idx + 1

        if not self.bounding_box or self.bounding_box == (0.0, 0.0, 0.0, 0.0):
            all_rects = [self.image_rect] + self.caption_rects
            x0 = min(r[0] for r in all_rects)
            y0 = min(r[1] for r in all_rects)
            x1 = max(r[2] for r in all_rects)
            y1 = max(r[3] for r in all_rects)
            self.bounding_box = (x0, y0, x1, y1)

    def to_evidence_dict(self) -> Dict[str, Any]:
        """Emit structured diagnostic record conforming to Part G Section 24."""
        return {
            "image_id": self.image_id,
            "image_bbox": [round(x, 1) for x in self.image_bbox],
            "caption_id": self.caption_id,
            "caption_bbox": [round(x, 1) for x in self.caption_bbox] if self.caption_bbox else None,
            "association_method": self.association_method,
            "distance": round(self.distance, 1),
            "reading_order": self.reading_order,
            "keep_together": self.keep_together,
            "final_page": self.final_page,
        }


def find_visual_groups(page: pymupdf.Page, page_idx: int) -> List[VisualGroup]:
    """Identify images and their associated captions on a page with row-shared grid support."""
    groups: List[VisualGroup] = []
    images = page.get_images()
    if not images:
        return groups

    text_blocks = [b for b in page.get_text("blocks") if b[4].strip() and b[6] == 0]

    # Collect all image bounding boxes on page
    raw_images: List[Dict[str, Any]] = []
    seen_rects = set()
    for img_idx, img in enumerate(images):
        try:
            rects = page.get_image_rects(img[0])
            for r_idx, r in enumerate(rects):
                rect_key = (round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1))
                if rect_key in seen_rects:
                    continue
                seen_rects.add(rect_key)
                raw_images.append({
                    "raw_idx": img_idx,
                    "sub_idx": r_idx,
                    "rect": (r.x0, r.y0, r.x1, r.y1),
                })
        except Exception:
            continue

    if not raw_images:
        return groups

    # Sort images by reading order: y0 (banded by 40pt) then x0
    raw_images.sort(key=lambda item: (round(item["rect"][1] / 40.0), item["rect"][0]))

    # Group into image rows (images within ±20pt vertical alignment)
    rows: List[List[Dict[str, Any]]] = []
    for item in raw_images:
        placed = False
        for row in rows:
            ref_y0 = row[0]["rect"][1]
            if abs(item["rect"][1] - ref_y0) <= 25.0:
                row.append(item)
                placed = True
                break
        if not placed:
            rows.append([item])

    global_order = 1
    for row in rows:
        row.sort(key=lambda item: item["rect"][0])
        row_min_x = min(item["rect"][0] for item in row)
        row_max_x = max(item["rect"][2] for item in row)
        row_bottom = max(item["rect"][3] for item in row)

        # Find row-level captions (text block within 40pt below the row)
        row_caption_block = None
        row_caption_id = None
        for b_idx, b in enumerate(text_blocks):
            bx0, by0, bx1, by1, btext = b[0], b[1], b[2], b[3], b[4].strip()
            is_below_row = 0.0 <= (by0 - row_bottom) <= 45.0
            within_h_span = (bx0 >= row_min_x - 30.0 and bx1 <= row_max_x + 30.0)
            if is_below_row and within_h_span:
                row_caption_block = (bx0, by0, bx1, by1, btext)
                row_caption_id = f"p{page_idx}_cap_b{b_idx}"
                break

        for item in row:
            r = item["rect"]
            img_id = f"p{page_idx}_img_{item['raw_idx']}_{item['sub_idx']}"
            cap_rects: List[Tuple[float, float, float, float]] = []
            cap_texts: List[str] = []
            cap_id = None
            cap_bbox = None
            assoc_method = "STANDALONE_IMAGE"
            dist = 0.0

            if row_caption_block:
                cbx0, cby0, cbx1, cby1, cbtext = row_caption_block
                cap_rects.append((cbx0, cby0, cbx1, cby1))
                cap_texts.append(cbtext)
                cap_bbox = (cbx0, cby0, cbx1, cby1)
                cap_id = row_caption_id
                dist = max(0.0, cby0 - r[3])

                # Determine association method
                # Direct below if horizontal overlap > 10pt with this image
                h_overlap = max(0.0, min(r[2], cbx1) - max(r[0], cbx0))
                if h_overlap > 10.0:
                    assoc_method = "DIRECT_BELOW"
                else:
                    assoc_method = "ROW_SHARED_GRID"
            else:
                # Check for individual image caption
                for b_idx, b in enumerate(text_blocks):
                    bx0, by0, bx1, by1, btext = b[0], b[1], b[2], b[3], b[4].strip()
                    is_below = 0.0 <= (by0 - r[3]) <= 35.0
                    h_overlap = max(0.0, min(r[2], bx1) - max(r[0], bx0))
                    is_cap = any(btext.lower().startswith(p) for p in ("fig", "figure", "hình", "ảnh", "図", "写真", "photo"))
                    if is_below and (h_overlap > 10.0 or is_cap):
                        cap_rects.append((bx0, by0, bx1, by1))
                        cap_texts.append(btext)
                        cap_bbox = (bx0, by0, bx1, by1)
                        cap_id = f"p{page_idx}_cap_b{b_idx}"
                        assoc_method = "DIRECT_BELOW"
                        dist = max(0.0, by0 - r[3])
                        break

            vg = VisualGroup(
                group_id=img_id,
                page_idx=page_idx,
                image_rect=r,
                caption_rects=cap_rects,
                caption_texts=cap_texts,
                keep_together=True,
                image_id=img_id,
                image_bbox=r,
                caption_id=cap_id,
                caption_bbox=cap_bbox,
                association_method=assoc_method,
                distance=dist,
                reading_order=global_order,
                final_page=page_idx + 1,
            )
            groups.append(vg)
            global_order += 1

    return groups
