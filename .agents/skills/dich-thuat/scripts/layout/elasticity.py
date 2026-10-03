"""Layout Elasticity Policy for Adaptive PDF Engine.

Part of AIWF Translation Upgrade #1.6 (Part E, Sections 23-25):
- Explicit policy describing what each region/object may change.
- Simple, deterministic policy object without a heavyweight constraint solver.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    from analyzer.layout_profile import DocumentClass, PageConstraint, StructuralRole
except ImportError:
    from ..analyzer.layout_profile import DocumentClass, PageConstraint, StructuralRole


class ElasticityLevel(str, Enum):
    LOCKED = "LOCKED"
    LIMITED = "LIMITED"
    HIGH = "HIGH"


@dataclass
class LayoutElasticity:
    """Policy defining allowable geometric and typographic adaptations for an element."""
    horizontal_resize: ElasticityLevel = ElasticityLevel.LIMITED
    vertical_resize: ElasticityLevel = ElasticityLevel.HIGH
    reposition: ElasticityLevel = ElasticityLevel.LIMITED
    reflow: ElasticityLevel = ElasticityLevel.HIGH
    page_break: ElasticityLevel = ElasticityLevel.HIGH
    scale: ElasticityLevel = ElasticityLevel.LIMITED
    keep_together: bool = False
    keep_with_next: bool = False
    topology_locked: bool = False
    aspect_ratio_locked: bool = False
    min_font_size: float = 7.5
    allow_micro_text: bool = False

    def to_dict(self):
        return {
            "horizontal_resize": self.horizontal_resize.value,
            "vertical_resize": self.vertical_resize.value,
            "reposition": self.reposition.value,
            "reflow": self.reflow.value,
            "page_break": self.page_break.value,
            "scale": self.scale.value,
            "keep_together": self.keep_together,
            "keep_with_next": self.keep_with_next,
            "topology_locked": self.topology_locked,
            "aspect_ratio_locked": self.aspect_ratio_locked,
            "min_font_size": self.min_font_size,
        }


def get_default_elasticity(
    role: StructuralRole,
    doc_class: DocumentClass = DocumentClass.TEXT_FLOW,
    page_constraint: PageConstraint = PageConstraint.FREE,
) -> LayoutElasticity:
    """Retrieve standard elasticity policy for a structural role under a page constraint."""
    # Hard constraints lock geometry more tightly
    is_hard = page_constraint == PageConstraint.HARD

    if role == StructuralRole.BODY_PARAGRAPH:
        return LayoutElasticity(
            horizontal_resize=ElasticityLevel.LIMITED if is_hard else ElasticityLevel.HIGH,
            vertical_resize=ElasticityLevel.LIMITED if is_hard else ElasticityLevel.HIGH,
            reposition=ElasticityLevel.LIMITED if is_hard else ElasticityLevel.HIGH,
            reflow=ElasticityLevel.HIGH,
            page_break=ElasticityLevel.LOCKED if is_hard else ElasticityLevel.HIGH,
            scale=ElasticityLevel.LIMITED,
            keep_together=False,
            min_font_size=5.0 if is_hard else 8.0,
            allow_micro_text=is_hard,
        )

    if role in (StructuralRole.TITLE, StructuralRole.HEADING):
        return LayoutElasticity(
            horizontal_resize=ElasticityLevel.LIMITED,
            vertical_resize=ElasticityLevel.HIGH,
            reposition=ElasticityLevel.LIMITED,
            reflow=ElasticityLevel.LIMITED,
            page_break=ElasticityLevel.LOCKED,
            keep_with_next=True,
            min_font_size=8.5,
        )

    if role in (StructuralRole.TABLE_HEADER, StructuralRole.TABLE_CELL):
        return LayoutElasticity(
            horizontal_resize=ElasticityLevel.LIMITED,
            vertical_resize=ElasticityLevel.HIGH,
            reposition=ElasticityLevel.LOCKED,
            reflow=ElasticityLevel.HIGH,
            page_break=ElasticityLevel.LIMITED,
            topology_locked=True,
            min_font_size=5.5 if is_hard else 6.5,
            allow_micro_text=is_hard,
        )

    if role == StructuralRole.CAPTION:
        return LayoutElasticity(
            horizontal_resize=ElasticityLevel.LIMITED,
            vertical_resize=ElasticityLevel.HIGH,
            reposition=ElasticityLevel.HIGH,
            reflow=ElasticityLevel.HIGH,
            page_break=ElasticityLevel.LOCKED,
            keep_together=True,
            min_font_size=6.0,
        )

    if role in (StructuralRole.DIAGRAM_LABEL, StructuralRole.TIMELINE_LABEL):
        return LayoutElasticity(
            horizontal_resize=ElasticityLevel.LIMITED,
            vertical_resize=ElasticityLevel.LIMITED,
            reposition=ElasticityLevel.LIMITED,
            reflow=ElasticityLevel.LIMITED,
            page_break=ElasticityLevel.LOCKED,
            topology_locked=True,
            min_font_size=4.5 if is_hard else 5.5,
            allow_micro_text=is_hard,
        )

    if role in (StructuralRole.HEADER, StructuralRole.FOOTER):
        return LayoutElasticity(
            horizontal_resize=ElasticityLevel.LOCKED,
            vertical_resize=ElasticityLevel.LOCKED,
            reposition=ElasticityLevel.LOCKED,
            reflow=ElasticityLevel.LOCKED,
            page_break=ElasticityLevel.LOCKED,
            topology_locked=True,
            min_font_size=6.0,
        )

    # Default generic
    return LayoutElasticity(
        horizontal_resize=ElasticityLevel.LIMITED,
        vertical_resize=ElasticityLevel.HIGH,
        reposition=ElasticityLevel.LIMITED,
        reflow=ElasticityLevel.HIGH,
        page_break=ElasticityLevel.LOCKED if is_hard else ElasticityLevel.HIGH,
        min_font_size=7.0,
    )
