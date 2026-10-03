"""Layout Profile and Classification Taxonomy for Adaptive PDF Engine.

Part of AIWF Translation Upgrade #1.6:
- 3-level classification: Document Level, Page Level, Region Level.
- Layout taxonomy: TEXT_FLOW, TABLE_FORM, VISUAL_DIAGRAM, IMAGE_GROUP, FIXED_LAYOUT, MIXED.
- Pagination constraints: HARD, SOFT, FREE.
- Structural roles: TITLE, HEADING, BODY_PARAGRAPH, LIST_ITEM, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class DocumentClass(str, Enum):
    """Layout classification taxonomy (Part A, Section 5)."""
    TEXT_FLOW = "TEXT_FLOW"              # Manual, guideline, contract, report, regulation
    TABLE_FORM = "TABLE_FORM"            # Forms, ledgers, grid-based tables
    VISUAL_DIAGRAM = "VISUAL_DIAGRAM"    # Diagrams, schemas, timelines, flowcharts
    IMAGE_GROUP = "IMAGE_GROUP"          # Photo grids, figure + caption + notes
    FIXED_LAYOUT = "FIXED_LAYOUT"        # Certificates, posters, fixed administrative cards
    MIXED = "MIXED"                      # Heterogeneous regions requiring segmentation


class PageConstraint(str, Enum):
    """Pagination constraint policy (Part C, Section 15)."""
    HARD = "HARD"  # Intrinsic geometry (certificates, posters, brochures). Restricts repagination.
    SOFT = "SOFT"  # Original pagination desirable, but readability has higher priority.
    FREE = "FREE"  # Natural flowing document (guidelines, manuals, reports). Unrestricted pagination.


class StructuralRole(str, Enum):
    """Structural role of a block or element (Part D, Section 22)."""
    TITLE = "TITLE"
    HEADING = "HEADING"
    BODY_PARAGRAPH = "BODY_PARAGRAPH"
    LIST_ITEM = "LIST_ITEM"
    TABLE_HEADER = "TABLE_HEADER"
    TABLE_CELL = "TABLE_CELL"
    CAPTION = "CAPTION"
    DIAGRAM_LABEL = "DIAGRAM_LABEL"
    TIMELINE_LABEL = "TIMELINE_LABEL"
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    FORM_LABEL = "FORM_LABEL"
    FORM_VALUE = "FORM_VALUE"
    OTHER = "OTHER"


@dataclass
class RegionProfile:
    """Classification profile of a specific spatial region on a page."""
    region_id: str
    region_class: DocumentClass
    bbox: List[float]  # [x0, y0, x1, y1]
    roles: List[StructuralRole] = field(default_factory=list)
    blocks_count: int = 0
    has_images: bool = False
    has_tables: bool = False
    has_drawings: bool = False
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["region_class"] = self.region_class.value
        d["roles"] = [r.value for r in self.roles]
        return d


@dataclass
class PageProfile:
    """Classification profile of a single PDF page."""
    page_idx: int  # 0-indexed
    page_number: int  # 1-indexed
    page_class: DocumentClass
    page_constraint: PageConstraint
    width: float
    height: float
    margins: Dict[str, float] = field(default_factory=dict)
    regions: List[RegionProfile] = field(default_factory=list)
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["page_class"] = self.page_class.value
        d["page_constraint"] = self.page_constraint.value
        d["regions"] = [r.to_dict() for r in self.regions]
        return d


@dataclass
class LayoutProfile:
    """Comprehensive layout profile for an entire document."""
    document_class: DocumentClass
    page_constraint: PageConstraint
    page_count: int
    page_profiles: List[PageProfile] = field(default_factory=list)
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)
    ambiguous_features: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_class": self.document_class.value,
            "page_constraint": self.page_constraint.value,
            "page_count": self.page_count,
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "ambiguous_features": self.ambiguous_features,
            "page_profiles": [p.to_dict() for p in self.page_profiles],
        }
