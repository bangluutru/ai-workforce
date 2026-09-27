"""Visual Grouping and Atomic Keep-Together Logic.

Part of AIWF Translation Upgrade #1.6 (Part H, Sections 34-36):
- Treats related image + caption + note as VisualGroup.
- Prevents image on page N and caption on page N+1.
- Maintains ordering, grouping, and relative hierarchy for image grids.
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

    def __post_init__(self):
        if not self.bounding_box or self.bounding_box == (0.0, 0.0, 0.0, 0.0):
            all_rects = [self.image_rect] + self.caption_rects
            x0 = min(r[0] for r in all_rects)
            y0 = min(r[1] for r in all_rects)
            x1 = max(r[2] for r in all_rects)
            y1 = max(r[3] for r in all_rects)
            self.bounding_box = (x0, y0, x1, y1)


def find_visual_groups(page: pymupdf.Page, page_idx: int) -> List[VisualGroup]:
    """Identify images and their associated captions on a page."""
    groups: List[VisualGroup] = []
    images = page.get_images()
    if not images:
        return groups

    text_blocks = [b for b in page.get_text("blocks") if b[4].strip() and b[6] == 0]

    for img_idx, img in enumerate(images):
        try:
            rects = page.get_image_rects(img[0])
            for r_idx, r in enumerate(rects):
                img_rect = (r.x0, r.y0, r.x1, r.y1)
                caption_rects: List[Tuple[float, float, float, float]] = []
                caption_texts: List[str] = []

                # Find text immediately below the image (within 35pt vertical distance)
                # or with horizontal overlap
                for b in text_blocks:
                    bx0, by0, bx1, by1, btext = b[0], b[1], b[2], b[3], b[4].strip()
                    # Check vertical proximity below image
                    is_below = 0.0 <= (by0 - r.y1) <= 35.0
                    # Horizontal overlap
                    h_overlap = max(0.0, min(r.x1, bx1) - max(r.x0, bx0))
                    # Or caption prefixes
                    is_caption_text = any(btext.lower().startswith(p) for p in (
                        "fig", "figure", "hình", "ảnh", "図", "写真", "photo"
                    ))

                    if (is_below and h_overlap > 10.0) or (is_below and is_caption_text):
                        caption_rects.append((bx0, by0, bx1, by1))
                        caption_texts.append(btext)

                vg = VisualGroup(
                    group_id=f"p{page_idx}_img_{img_idx}_{r_idx}",
                    page_idx=page_idx,
                    image_rect=img_rect,
                    caption_rects=caption_rects,
                    caption_texts=caption_texts,
                )
                groups.append(vg)
        except Exception:
            continue

    return groups
