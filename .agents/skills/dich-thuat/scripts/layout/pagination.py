"""Pagination and Page Budget Management for Adaptive PDF Engine.

Part of AIWF Translation Upgrade #1.6 (Part C, Sections 15-19 & Part F, Sections 28-30):
- Implements HARD, SOFT, and FREE pagination constraint policies.
- Widow and orphan control:
  - Never allow a heading alone at the bottom of a page (keep-with-next).
  - Never separate a caption from its associated figure.
  - Prevent single-line paragraph fragments at page breaks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from analyzer.layout_profile import PageConstraint, StructuralRole
except ImportError:
    from ..analyzer.layout_profile import PageConstraint, StructuralRole


@dataclass
class PageBudget:
    """Tracks vertical space budget on a page."""
    page_height: float
    top_margin: float = 36.0
    bottom_margin: float = 36.0
    current_y: float = 36.0
    constraint: PageConstraint = PageConstraint.FREE
    elements_count: int = 0

    @property
    def usable_height(self) -> float:
        return max(self.page_height - self.top_margin - self.bottom_margin, 0.0)

    @property
    def remaining_space(self) -> float:
        return max(self.page_height - self.bottom_margin - self.current_y, 0.0)

    def can_fit(self, height: float, keep_with_next_height: float = 0.0) -> bool:
        total_needed = height + keep_with_next_height
        if self.constraint == PageConstraint.HARD:
            # Under HARD constraint, stretch up to 105% of usable space before breaking
            return (self.current_y + total_needed) <= (self.page_height - self.bottom_margin * 0.5)
        return total_needed <= self.remaining_space

    def consume(self, height: float):
        self.current_y += height
        self.elements_count += 1

    def reset_for_new_page(self):
        self.current_y = self.top_margin
        self.elements_count = 0


def should_break_before(
    role: StructuralRole,
    element_height: float,
    budget: PageBudget,
    is_last_on_page: bool = False,
) -> bool:
    """Determine if a page break should be inserted before an element to avoid orphans."""
    # Under FREE or SOFT constraint, headings must never be near the bottom
    if role in (StructuralRole.HEADING, StructuralRole.TITLE):
        # Need space for heading plus at least 2 lines of subsequent body text (~40pt)
        if not budget.can_fit(element_height, keep_with_next_height=45.0):
            return True

    # Image groups / Figures should not be squeezed into tiny remaining space
    if role == StructuralRole.CAPTION:
        # Caption must stay with image
        return False

    # Normal body paragraph: if remaining space is less than 30pt (less than 2 lines), push to next page
    if role == StructuralRole.BODY_PARAGRAPH:
        if budget.remaining_space < 32.0 and budget.elements_count > 0:
            return True

    return not budget.can_fit(element_height)
