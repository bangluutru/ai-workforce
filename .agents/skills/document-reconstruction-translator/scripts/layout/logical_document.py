"""Logical Document Model for AIWF Translation Upgrade #1.7.

Represents the semantic structure of a document (sections, headings, paragraphs,
lists, tables, formula blocks, inline scientific notation, headers, footers)
between physical PDF extraction and translation/flow composition.

Conforms to AIWF Translation Upgrade #1.7 (Sections 6, 21, 29, 30, 31).
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class StructuralRole(str, Enum):
    """Semantic structural roles for document elements."""
    TITLE = "TITLE"
    SUBTITLE = "SUBTITLE"
    AUTHOR = "AUTHOR"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    BODY_PARAGRAPH = "BODY_PARAGRAPH"
    LIST_ITEM = "LIST_ITEM"
    DEFINITION_ITEM = "DEFINITION_ITEM"
    TABLE_HEADER = "TABLE_HEADER"
    TABLE_CELL = "TABLE_CELL"
    TABLE_BLOCK = "TABLE_BLOCK"
    CAPTION = "CAPTION"
    FORM_LABEL = "FORM_LABEL"
    FORM_VALUE = "FORM_VALUE"
    FORMULA_BLOCK = "FORMULA_BLOCK"
    FOOTNOTE = "FOOTNOTE"
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    PAGE_NUMBER = "PAGE_NUMBER"
    OTHER = "OTHER"


class ConfidenceLevel(str, Enum):
    """Confidence level of semantic reconstruction."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class InlineToken:
    """Represents an atomic inline fragment, preserving scientific notation.
    
    Prevents superscript, subscript, signs, and units from fragmenting into
    separate semantic paragraphs.
    """
    def __init__(
        self,
        base_text: str,
        superscript: str = "",
        subscript: str = "",
        symbol: str = "",
        is_bold: bool = False,
        is_italic: bool = False,
    ):
        self.base_text = base_text
        self.superscript = superscript
        self.subscript = subscript
        self.symbol = symbol
        self.is_bold = is_bold
        self.is_italic = is_italic

    def to_text(self) -> str:
        """Returns normalized string representation."""
        t = self.base_text
        if self.subscript:
            t += self.subscript
        if self.superscript:
            t += self.superscript
        if self.symbol:
            t += self.symbol
        return t

    def to_typst(self) -> str:
        """Emits Typst-safe inline string with sub/superscript formatting."""
        from render.flow_renderer import _escape_typst
        res = _escape_typst(self.base_text)
        if self.subscript:
            res += f"#sub[{_escape_typst(self.subscript)}]"
        if self.superscript:
            res += f"#super[{_escape_typst(self.superscript)}]"
        if self.symbol:
            res += _escape_typst(self.symbol)
        if self.is_bold:
            res = f"#text(weight: \"bold\")[{res}]"
        if self.is_italic:
            res = f"#text(style: \"italic\")[{res}]"
        return res

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_text": self.base_text,
            "superscript": self.superscript,
            "subscript": self.subscript,
            "symbol": self.symbol,
            "is_bold": self.is_bold,
            "is_italic": self.is_italic,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> InlineToken:
        return cls(
            base_text=d.get("base_text", ""),
            superscript=d.get("superscript", ""),
            subscript=d.get("subscript", ""),
            symbol=d.get("symbol", ""),
            is_bold=d.get("is_bold", False),
            is_italic=d.get("is_italic", False),
        )


class LogicalUnit:
    """Represents a coherent logical unit of text (e.g. Paragraph, Heading, ListItem)."""
    def __init__(
        self,
        unit_id: str,
        role: StructuralRole,
        text: str,
        tokens: Optional[List[InlineToken]] = None,
        source_pages: Optional[List[int]] = None,
        source_bboxes: Optional[List[Tuple[float, float, float, float]]] = None,
        font_family: str = "Arial",
        font_size: float = 10.0,
        font_weight: str = "regular",
        is_italic: bool = False,
        alignment: str = "left",
        indentation: float = 0.0,
        line_spacing: float = 0.65,
        paragraph_spacing: float = 0.5,
        list_marker: Optional[str] = None,
        numbering: Optional[str] = None,
        level: int = 0,
        confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
        merge_reasons: Optional[List[str]] = None,
        source_fragments: Optional[List[Dict[str, Any]]] = None,
        parent_section_id: Optional[str] = None,
        translation_unit_id: Optional[str] = None,
        translated_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.unit_id = unit_id
        self.role = role
        self.text = text
        self.tokens = tokens or []
        self.source_pages = source_pages or []
        self.source_bboxes = source_bboxes or []
        self.font_family = font_family
        self.font_size = font_size
        self.font_weight = font_weight
        self.is_italic = is_italic
        self.alignment = alignment
        self.indentation = indentation
        self.line_spacing = line_spacing
        self.paragraph_spacing = paragraph_spacing
        self.list_marker = list_marker
        self.numbering = numbering
        self.level = level
        self.confidence = confidence
        self.merge_reasons = merge_reasons or []
        self.source_fragments = source_fragments or []
        self.parent_section_id = parent_section_id
        self.translation_unit_id = translation_unit_id
        self.translated_text = translated_text
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "role": self.role.value if isinstance(self.role, StructuralRole) else str(self.role),
            "text": self.text,
            "tokens": [t.to_dict() for t in self.tokens],
            "source_pages": self.source_pages,
            "source_bboxes": self.source_bboxes,
            "font_family": self.font_family,
            "font_size": round(self.font_size, 2),
            "font_weight": self.font_weight,
            "is_italic": self.is_italic,
            "alignment": self.alignment,
            "indentation": round(self.indentation, 2),
            "line_spacing": round(self.line_spacing, 2),
            "paragraph_spacing": round(self.paragraph_spacing, 2),
            "list_marker": self.list_marker,
            "numbering": self.numbering,
            "level": self.level,
            "confidence": self.confidence.value if isinstance(self.confidence, ConfidenceLevel) else str(self.confidence),
            "merge_reasons": self.merge_reasons,
            "source_fragments_count": len(self.source_fragments),
            "parent_section_id": self.parent_section_id,
            "translation_unit_id": self.translation_unit_id,
            "translated_text": self.translated_text,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> LogicalUnit:
        role_str = d.get("role", StructuralRole.BODY_PARAGRAPH.value)
        try:
            role = StructuralRole(role_str)
        except ValueError:
            role = StructuralRole.BODY_PARAGRAPH

        conf_str = d.get("confidence", ConfidenceLevel.HIGH.value)
        try:
            conf = ConfidenceLevel(conf_str)
        except ValueError:
            conf = ConfidenceLevel.HIGH

        tokens = [InlineToken.from_dict(t) for t in d.get("tokens", [])]

        return cls(
            unit_id=d["unit_id"],
            role=role,
            text=d.get("text", ""),
            tokens=tokens,
            source_pages=d.get("source_pages", []),
            source_bboxes=d.get("source_bboxes", []),
            font_family=d.get("font_family", "Arial"),
            font_size=d.get("font_size", 10.0),
            font_weight=d.get("font_weight", "regular"),
            is_italic=d.get("is_italic", False),
            alignment=d.get("alignment", "left"),
            indentation=d.get("indentation", 0.0),
            line_spacing=d.get("line_spacing", 0.65),
            paragraph_spacing=d.get("paragraph_spacing", 0.5),
            list_marker=d.get("list_marker"),
            numbering=d.get("numbering"),
            level=d.get("level", 0),
            confidence=conf,
            merge_reasons=d.get("merge_reasons", []),
            source_fragments=d.get("source_fragments", []),
            parent_section_id=d.get("parent_section_id"),
            translation_unit_id=d.get("translation_unit_id"),
            translated_text=d.get("translated_text"),
            metadata=d.get("metadata", {}),
        )


class LogicalTable:
    """Represents a structured table in the logical document."""
    def __init__(
        self,
        table_id: str,
        source_page: int,
        bbox: Tuple[float, float, float, float],
        headers: List[List[str]],
        rows: List[List[str]],
        translated_headers: Optional[List[List[str]]] = None,
        translated_rows: Optional[List[List[str]]] = None,
        col_widths: Optional[List[float]] = None,
        caption: Optional[str] = None,
        translated_caption: Optional[str] = None,
        footnote: Optional[str] = None,
        translated_footnote: Optional[str] = None,
        confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.table_id = table_id
        self.source_page = source_page
        self.bbox = bbox
        self.headers = headers
        self.rows = rows
        self.translated_headers = translated_headers or []
        self.translated_rows = translated_rows or []
        self.col_widths = col_widths or []
        self.caption = caption
        self.translated_caption = translated_caption
        self.footnote = footnote
        self.translated_footnote = translated_footnote
        self.confidence = confidence
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_id": self.table_id,
            "source_page": self.source_page,
            "bbox": self.bbox,
            "headers": self.headers,
            "rows": self.rows,
            "translated_headers": self.translated_headers,
            "translated_rows": self.translated_rows,
            "col_widths": self.col_widths,
            "caption": self.caption,
            "translated_caption": self.translated_caption,
            "footnote": self.footnote,
            "translated_footnote": self.translated_footnote,
            "confidence": self.confidence.value if isinstance(self.confidence, ConfidenceLevel) else str(self.confidence),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> LogicalTable:
        conf_str = d.get("confidence", ConfidenceLevel.HIGH.value)
        try:
            conf = ConfidenceLevel(conf_str)
        except ValueError:
            conf = ConfidenceLevel.HIGH

        return cls(
            table_id=d["table_id"],
            source_page=d.get("source_page", 1),
            bbox=tuple(d.get("bbox", (0.0, 0.0, 0.0, 0.0))),
            headers=d.get("headers", []),
            rows=d.get("rows", []),
            translated_headers=d.get("translated_headers", []),
            translated_rows=d.get("translated_rows", []),
            col_widths=d.get("col_widths", []),
            caption=d.get("caption"),
            translated_caption=d.get("translated_caption"),
            footnote=d.get("footnote"),
            translated_footnote=d.get("translated_footnote"),
            confidence=conf,
            metadata=d.get("metadata", {}),
        )


class LogicalSection:
    """Represents a hierarchical document section."""
    def __init__(
        self,
        section_id: str,
        heading: Optional[LogicalUnit] = None,
        units: Optional[List[Union[LogicalUnit, LogicalTable]]] = None,
        subsections: Optional[List[LogicalSection]] = None,
    ):
        self.section_id = section_id
        self.heading = heading
        self.units = units or []
        self.subsections = subsections or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "heading": self.heading.to_dict() if self.heading else None,
            "units_count": len(self.units),
            "subsections": [s.to_dict() for s in self.subsections],
        }


class LogicalDocument:
    """Complete semantic representation of a document for native flow reconstruction."""
    def __init__(
        self,
        document_id: str,
        source_pdf: str = "",
        title: Optional[LogicalUnit] = None,
        subtitle: Optional[LogicalUnit] = None,
        authors: Optional[List[LogicalUnit]] = None,
        running_headers: Optional[List[LogicalUnit]] = None,
        running_footers: Optional[List[LogicalUnit]] = None,
        page_numbers: Optional[List[LogicalUnit]] = None,
        sections: Optional[List[LogicalSection]] = None,
        units: Optional[List[Union[LogicalUnit, LogicalTable]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.document_id = document_id
        self.source_pdf = source_pdf
        self.title = title
        self.subtitle = subtitle
        self.authors = authors or []
        self.running_headers = running_headers or []
        self.running_footers = running_footers or []
        self.page_numbers = page_numbers or []
        self.sections = sections or []
        self.units = units or []
        self.metadata = metadata or {}

    def get_units_by_role(self, role: StructuralRole) -> List[LogicalUnit]:
        """Returns all logical units matching a given role."""
        return [u for u in self.units if isinstance(u, LogicalUnit) and u.role == role]

    def count_by_role(self) -> Dict[str, int]:
        """Returns a breakdown of unit counts by structural role."""
        counts: Dict[str, int] = {}
        for u in self.units:
            if isinstance(u, LogicalUnit):
                r = u.role.value if isinstance(u.role, StructuralRole) else str(u.role)
                counts[r] = counts.get(r, 0) + 1
            elif isinstance(u, LogicalTable):
                counts["TABLE_BLOCK"] = counts.get("TABLE_BLOCK", 0) + 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        """Converts entire LogicalDocument to JSON-serializable dictionary."""
        return {
            "document_id": self.document_id,
            "source_pdf": self.source_pdf,
            "title": self.title.to_dict() if self.title else None,
            "subtitle": self.subtitle.to_dict() if self.subtitle else None,
            "authors": [a.to_dict() for a in self.authors],
            "running_headers": [h.to_dict() for h in self.running_headers],
            "running_footers": [f.to_dict() for f in self.running_footers],
            "page_numbers": [p.to_dict() for p in self.page_numbers],
            "units": [u.to_dict() for u in self.units],
            "counts_by_role": self.count_by_role(),
            "metadata": self.metadata,
        }

    def generate_reconstruction_report(self) -> Dict[str, Any]:
        """Generates structured diagnostic reconstruction report (Section 30)."""
        low_conf_units = []
        for u in self.units:
            if isinstance(u, LogicalUnit) and u.confidence == ConfidenceLevel.LOW:
                low_conf_units.append({
                    "unit_id": u.unit_id,
                    "role": u.role.value,
                    "text_preview": u.text[:60] + "..." if len(u.text) > 60 else u.text,
                    "source_pages": u.source_pages,
                    "reasons": u.merge_reasons,
                })

        return {
            "document_id": self.document_id,
            "source_pdf": self.source_pdf,
            "total_logical_units": len(self.units),
            "counts_by_role": self.count_by_role(),
            "low_confidence_units_count": len(low_conf_units),
            "low_confidence_units": low_conf_units,
            "cross_page_continuations": sum(
                1 for u in self.units if isinstance(u, LogicalUnit) and len(u.source_pages) > 1
            ),
            "tables_count": sum(1 for u in self.units if isinstance(u, LogicalTable)),
        }
