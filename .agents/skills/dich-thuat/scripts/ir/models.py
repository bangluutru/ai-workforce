"""Document Intermediate Representation (Document IR) & Relationship Graph Model.

Conforms to AIWF Document Reconstruction Translator Architecture:
- Section 5: Document IR - Content separated from presentation
- Section 6: Relationship Graph - Semantic preservation over coordinate preservation
- Section 18: Style Profile Extraction & Representation
- Section 25: Confidence-Aware Processing & Strategy Routing
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class SemanticObjectType(str, Enum):
    """16+ Semantic Object Types recognized in Document IR."""
    TITLE = "TITLE"
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    LIST = "LIST"
    TABLE = "TABLE"
    FORMULA = "FORMULA"
    CHART = "CHART"
    DIAGRAM = "DIAGRAM"
    PHOTO = "PHOTO"
    ILLUSTRATION = "ILLUSTRATION"
    VECTOR_GRAPHIC = "VECTOR_GRAPHIC"
    CAPTION = "CAPTION"
    CALLOUT = "CALLOUT"
    FOOTNOTE = "FOOTNOTE"
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    PAGE_NUMBER = "PAGE_NUMBER"
    UNKNOWN = "UNKNOWN"
    MIXED_FIGURE = "MIXED_FIGURE"


class RelationshipType(str, Enum):
    """Semantic Relationship Types between objects."""
    DESCRIBES = "DESCRIBES"            # e.g., CAPTION -> describes -> PHOTO / CHART / TABLE
    REFERENCES = "REFERENCES"          # e.g., PARAGRAPH -> references -> TABLE / FIGURE
    BELONGS_TO = "BELONGS_TO"          # e.g., TABLE_NOTE -> belongs_to -> TABLE, LEGEND -> CHART
    CONNECTS = "CONNECTS"              # e.g., DIAGRAM_EDGE -> connects -> NODE_A, NODE_B
    ANNOTATES = "ANNOTATES"            # e.g., CALLOUT / LABEL -> annotates -> OBJECT
    CONTINUES = "CONTINUES"            # e.g., PARAGRAPH (page 2) -> continues -> PARAGRAPH (page 1)


class ReconstructionStrategy(str, Enum):
    """Strategy used for rendering / reconstructing a semantic object."""
    REFLOW_TEXT = "REFLOW_TEXT"
    LATEX_MATH = "LATEX_MATH"
    DYNAMIC_TABLE = "DYNAMIC_TABLE"
    REDRAW_CHART = "REDRAW_CHART"
    RECONSTRUCT_DIAGRAM = "RECONSTRUCT_DIAGRAM"
    PRESERVE_ASSET = "PRESERVE_ASSET"
    HYBRID_OVERLAY = "HYBRID_OVERLAY"


@dataclass
class ConfidenceMetrics:
    """Multi-tiered confidence scores (0.0 to 1.0)."""
    recognition: float = 1.0
    semantic: float = 1.0
    reconstruction: float = 1.0
    data: float = 1.0

    def overall(self) -> float:
        return min(self.recognition, self.semantic, self.reconstruction, self.data)

    def to_dict(self) -> Dict[str, float]:
        return {
            "recognition": round(self.recognition, 3),
            "semantic": round(self.semantic, 3),
            "reconstruction": round(self.reconstruction, 3),
            "data": round(self.data, 3),
            "overall": round(self.overall(), 3),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ConfidenceMetrics:
        return cls(
            recognition=float(d.get("recognition", 1.0)),
            semantic=float(d.get("semantic", 1.0)),
            reconstruction=float(d.get("reconstruction", 1.0)),
            data=float(d.get("data", 1.0)),
        )


@dataclass
class SemanticRelationship:
    """A directed edge in the document relationship graph."""
    source_id: str
    target_id: str
    relation_type: RelationshipType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value if isinstance(self.relation_type, RelationshipType) else str(self.relation_type),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SemanticRelationship:
        rel = d.get("relation_type", "DESCRIBES")
        try:
            rel_type = RelationshipType(rel)
        except ValueError:
            rel_type = RelationshipType.DESCRIBES
        return cls(
            source_id=d["source_id"],
            target_id=d["target_id"],
            relation_type=rel_type,
            metadata=d.get("metadata", {}),
        )


@dataclass
class ObjectGeometry:
    """Reference geometry from the source PDF (evidence, not constraint)."""
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x0, y0, x1, y1
    page_number: int = 1
    page_width: float = 595.3
    page_height: float = 841.9
    rotation: float = 0.0

    @property
    def width(self) -> float:
        return max(0.0, self.bbox[2] - self.bbox[0])

    @property
    def height(self) -> float:
        return max(0.0, self.bbox[3] - self.bbox[1])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bbox": [round(c, 2) for c in self.bbox],
            "page_number": self.page_number,
            "page_width": round(self.page_width, 2),
            "page_height": round(self.page_height, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
            "rotation": self.rotation,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ObjectGeometry:
        bbox_list = d.get("bbox", [0.0, 0.0, 0.0, 0.0])
        bbox = (float(bbox_list[0]), float(bbox_list[1]), float(bbox_list[2]), float(bbox_list[3]))
        return cls(
            bbox=bbox,
            page_number=int(d.get("page_number", 1)),
            page_width=float(d.get("page_width", 595.3)),
            page_height=float(d.get("page_height", 841.9)),
            rotation=float(d.get("rotation", 0.0)),
        )


@dataclass
class SemanticObject:
    """Atomic semantic entity inside the Document IR."""
    id: str
    type: SemanticObjectType
    source_content: Any  # text, table dict, formula string, chart data dict, etc.
    translated_content: Optional[Any] = None
    reading_order: int = 0
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    relationships: List[SemanticRelationship] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=dict)
    geometry: ObjectGeometry = field(default_factory=ObjectGeometry)
    confidence: ConfidenceMetrics = field(default_factory=ConfidenceMetrics)
    reconstruction_strategy: ReconstructionStrategy = ReconstructionStrategy.REFLOW_TEXT
    source_asset_reference: Optional[str] = None  # path to extracted PNG/SVG/PDF asset
    fallback_used: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_text_like(self) -> bool:
        return self.type in (
            SemanticObjectType.TITLE,
            SemanticObjectType.HEADING,
            SemanticObjectType.PARAGRAPH,
            SemanticObjectType.LIST,
            SemanticObjectType.CAPTION,
            SemanticObjectType.CALLOUT,
            SemanticObjectType.FOOTNOTE,
            SemanticObjectType.HEADER,
            SemanticObjectType.FOOTER,
        )

    def get_text_content(self, prefer_translated: bool = True) -> str:
        """Returns string representation of content."""
        if prefer_translated and self.translated_content:
            if isinstance(self.translated_content, str):
                return self.translated_content
            if isinstance(self.translated_content, dict) and "text" in self.translated_content:
                return str(self.translated_content["text"])
        if isinstance(self.source_content, str):
            return self.source_content
        if isinstance(self.source_content, dict) and "text" in self.source_content:
            return str(self.source_content["text"])
        return ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, SemanticObjectType) else str(self.type),
            "source_content": self.source_content,
            "translated_content": self.translated_content,
            "reading_order": self.reading_order,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "relationships": [r.to_dict() for r in self.relationships],
            "style": self.style,
            "geometry": self.geometry.to_dict(),
            "confidence": self.confidence.to_dict(),
            "reconstruction_strategy": (
                self.reconstruction_strategy.value
                if isinstance(self.reconstruction_strategy, ReconstructionStrategy)
                else str(self.reconstruction_strategy)
            ),
            "source_asset_reference": self.source_asset_reference,
            "fallback_used": self.fallback_used,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> SemanticObject:
        t_str = d.get("type", "PARAGRAPH")
        try:
            o_type = SemanticObjectType(t_str)
        except ValueError:
            o_type = SemanticObjectType.PARAGRAPH

        strat_str = d.get("reconstruction_strategy", "REFLOW_TEXT")
        try:
            strat = ReconstructionStrategy(strat_str)
        except ValueError:
            strat = ReconstructionStrategy.REFLOW_TEXT

        geom = ObjectGeometry.from_dict(d.get("geometry", {})) if "geometry" in d else ObjectGeometry()
        conf = ConfidenceMetrics.from_dict(d.get("confidence", {})) if "confidence" in d else ConfidenceMetrics()
        rels = [SemanticRelationship.from_dict(r) for r in d.get("relationships", [])]

        return cls(
            id=d["id"],
            type=o_type,
            source_content=d.get("source_content"),
            translated_content=d.get("translated_content"),
            reading_order=d.get("reading_order", 0),
            parent_id=d.get("parent_id"),
            children_ids=d.get("children_ids", []),
            relationships=rels,
            style=d.get("style", {}),
            geometry=geom,
            confidence=conf,
            reconstruction_strategy=strat,
            source_asset_reference=d.get("source_asset_reference"),
            fallback_used=d.get("fallback_used", False),
            metadata=d.get("metadata", {}),
        )


@dataclass
class DocumentStyleProfile:
    """Captures the visual identity of the source document."""
    page_size: str = "a4"  # a4, letter, custom
    orientation: str = "portrait"
    page_width_pt: float = 595.3
    page_height_pt: float = 841.9
    margin_top_pt: float = 56.7  # ~20mm
    margin_bottom_pt: float = 56.7
    margin_left_pt: float = 56.7
    margin_right_pt: float = 56.7
    column_count: int = 1
    column_gap_pt: float = 14.2  # ~5mm
    dominant_body_font: str = "Times New Roman"
    dominant_heading_font: str = "Arial"
    body_font_size: float = 10.0
    heading_scale: List[float] = field(default_factory=lambda: [18.0, 14.0, 12.0])
    line_height_em: float = 0.65
    paragraph_spacing_em: float = 0.70
    primary_color_hex: str = "#000000"
    accent_color_hex: str = "#1a5fb4"
    table_border_width_pt: float = 0.5
    table_cell_padding_pt: float = 4.0
    caption_font_size: float = 8.5
    caption_alignment: str = "center"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> DocumentStyleProfile:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class DocumentIR:
    """Document Intermediate Representation (Root Container).
    
    Ties together metadata, style profile, semantic objects, relationship graph,
    and asset registry.
    """
    document_id: str
    source_pdf: str
    title: str = ""
    target_language: str = "vi"
    source_language: str = "auto"
    style_profile: DocumentStyleProfile = field(default_factory=DocumentStyleProfile)
    objects: List[SemanticObject] = field(default_factory=list)
    relationships: List[SemanticRelationship] = field(default_factory=list)
    asset_registry: Dict[str, str] = field(default_factory=dict)  # asset_id -> local file path
    metadata: Dict[str, Any] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Object Management & Indexing
    # -------------------------------------------------------------------------

    def add_object(self, obj: SemanticObject) -> None:
        """Adds an object and ensures proper reading order indexing."""
        if not obj.reading_order:
            obj.reading_order = len(self.objects) + 1
        self.objects.append(obj)

    def get_object(self, object_id: str) -> Optional[SemanticObject]:
        for o in self.objects:
            if o.id == object_id:
                return o
        return None

    def get_objects_by_type(self, obj_type: SemanticObjectType) -> List[SemanticObject]:
        return [o for o in self.objects if o.type == obj_type]

    def get_objects_sorted(self) -> List[SemanticObject]:
        """Returns all objects sorted by reading order."""
        return sorted(self.objects, key=lambda o: (o.geometry.page_number, o.reading_order))

    # -------------------------------------------------------------------------
    # Relationship Graph Management
    # -------------------------------------------------------------------------

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationshipType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SemanticRelationship:
        rel = SemanticRelationship(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            metadata=metadata or {},
        )
        self.relationships.append(rel)
        # Also mirror on source object
        src_obj = self.get_object(source_id)
        if src_obj:
            src_obj.relationships.append(rel)
        return rel

    def get_relationships_for_object(self, object_id: str) -> List[SemanticRelationship]:
        return [r for r in self.relationships if r.source_id == object_id or r.target_id == object_id]

    def get_caption_for_object(self, object_id: str) -> Optional[SemanticObject]:
        """Finds any CAPTION that describes this object."""
        for r in self.relationships:
            if r.target_id == object_id and r.relation_type == RelationshipType.DESCRIBES:
                caption_obj = self.get_object(r.source_id)
                if caption_obj and caption_obj.type == SemanticObjectType.CAPTION:
                    return caption_obj
        return None

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "source_pdf": self.source_pdf,
            "title": self.title,
            "target_language": self.target_language,
            "source_language": self.source_language,
            "style_profile": self.style_profile.to_dict(),
            "total_objects": len(self.objects),
            "total_relationships": len(self.relationships),
            "objects": [o.to_dict() for o in self.objects],
            "relationships": [r.to_dict() for r in self.relationships],
            "asset_registry": self.asset_registry,
            "metadata": self.metadata,
        }

    def save_json(self, output_path: Union[str, Path]) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> DocumentIR:
        ir = cls(
            document_id=d["document_id"],
            source_pdf=d.get("source_pdf", ""),
            title=d.get("title", ""),
            target_language=d.get("target_language", "vi"),
            source_language=d.get("source_language", "auto"),
            style_profile=DocumentStyleProfile.from_dict(d.get("style_profile", {})),
            asset_registry=d.get("asset_registry", {}),
            metadata=d.get("metadata", {}),
        )
        for obj_data in d.get("objects", []):
            ir.add_object(SemanticObject.from_dict(obj_data))
        for rel_data in d.get("relationships", []):
            ir.relationships.append(SemanticRelationship.from_dict(rel_data))
        return ir

    @classmethod
    def load_json(cls, input_path: Union[str, Path]) -> DocumentIR:
        with open(input_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return cls.from_dict(d)

    def summary(self) -> Dict[str, Any]:
        type_counts: Dict[str, int] = {}
        for o in self.objects:
            t = o.type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "document_id": self.document_id,
            "total_objects": len(self.objects),
            "type_counts": type_counts,
            "relationships_count": len(self.relationships),
            "assets_count": len(self.asset_registry),
        }
