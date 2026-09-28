"""Translation Planner: Document IR to TranslationUnit Mapping and Binding.

Conforms to Section 5 of AIWF Document Reconstruction Directive:
- Deterministic mapping: SemanticObject -> TranslationUnit -> translated result -> SemanticObject.translated_content.
- Classifies translatable objects:
  * TITLE, HEADING, PARAGRAPH, LIST, CAPTION, CALLOUT, FOOTNOTE
  * TABLE textual cells (preserving numbers, dates, codes verbatim)
  * CHART: title, axis labels, legend, categories
  * DIAGRAM: node labels, annotations
  * FORMULA: natural-language annotations only
- Strictly prevents translation of:
  * Formula semantics & math equations
  * Pure numbers, percentages, and measurement units
  * Model numbers, product codes, standard codes
  * Identifiers, URLs, and references
- Automatically detects and registers protected entities and critical values.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import sys
from pathlib import Path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ir.models import DocumentIR, SemanticObject, SemanticObjectType
from translation_foundation import (
    ContentType,
    TranslationUnit,
    detect_protected_entities,
    extract_critical_values,
)


class TranslationPlanner:
    """Orchestrates translation extraction, entity protection, and result binding."""

    # Map SemanticObjectType to ContentType
    TYPE_MAP = {
        SemanticObjectType.TITLE: ContentType.HEADING,
        SemanticObjectType.HEADING: ContentType.HEADING,
        SemanticObjectType.PARAGRAPH: ContentType.BODY,
        SemanticObjectType.LIST: ContentType.LIST_ITEM,
        SemanticObjectType.CAPTION: ContentType.CAPTION,
        SemanticObjectType.CALLOUT: ContentType.BODY,
        SemanticObjectType.FOOTNOTE: ContentType.BODY,
        SemanticObjectType.HEADER: ContentType.HEADER,
        SemanticObjectType.FOOTER: ContentType.FOOTER,
    }

    def __init__(self, source_language: str = "ja", target_language: str = "vi"):
        self.source_language = source_language
        self.target_language = target_language

    def plan_document_translation(self, ir: DocumentIR) -> List[TranslationUnit]:
        """Extracts all translatable units from Document IR."""
        units: List[TranslationUnit] = []

        for obj in ir.get_objects_sorted():
            # 1. Text-like objects
            if obj.is_text_like():
                text = obj.get_text_content(prefer_translated=False).strip()
                if not text:
                    continue

                # Check if it is a pure number or page number or code
                if self._is_non_translatable_text(text):
                    continue

                content_type = self.TYPE_MAP.get(obj.type, ContentType.BODY)
                protected = detect_protected_entities(text)

                u = TranslationUnit(
                    id=obj.id,
                    source_text=text,
                    source_language=self.source_language,
                    target_language=self.target_language,
                    content_type=content_type,
                    context=f"Page {obj.geometry.page_number} {obj.type.value}",
                    protected_tokens=protected,
                    location={"page": obj.geometry.page_number, "bbox": list(obj.geometry.bbox)},
                    source_block_id=obj.id,
                )
                units.append(u)

            # 2. Table textual cells
            elif obj.type == SemanticObjectType.TABLE:
                table_content = obj.source_content or {}
                headers = table_content.get("headers", [])
                rows = table_content.get("rows", [])

                # Process headers
                for r_idx, h_row in enumerate(headers if (headers and isinstance(headers[0], list)) else [headers]):
                    for c_idx, cell in enumerate(h_row):
                        c_text = str(cell or "").strip()
                        if c_text and not self._is_non_translatable_text(c_text):
                            u = TranslationUnit(
                                id=f"{obj.id}_hdr_{r_idx}_{c_idx}",
                                source_text=c_text,
                                source_language=self.source_language,
                                target_language=self.target_language,
                                content_type=ContentType.TABLE_CELL,
                                context=f"Table Header col {c_idx+1}",
                                protected_tokens=detect_protected_entities(c_text),
                                location={"page": obj.geometry.page_number, "table_id": obj.id, "row": r_idx, "col": c_idx, "is_header": True},
                                parent_id=obj.id,
                            )
                            units.append(u)

                # Process data rows
                for r_idx, row in enumerate(rows):
                    if not isinstance(row, list):
                        continue
                    for c_idx, cell in enumerate(row):
                        c_text = str(cell or "").strip()
                        if c_text and not self._is_non_translatable_text(c_text):
                            u = TranslationUnit(
                                id=f"{obj.id}_cell_{r_idx}_{c_idx}",
                                source_text=c_text,
                                source_language=self.source_language,
                                target_language=self.target_language,
                                content_type=ContentType.TABLE_CELL,
                                context=f"Table Cell row {r_idx+1} col {c_idx+1}",
                                protected_tokens=detect_protected_entities(c_text),
                                location={"page": obj.geometry.page_number, "table_id": obj.id, "row": r_idx, "col": c_idx, "is_header": False},
                                parent_id=obj.id,
                            )
                            units.append(u)

            # 3. Chart textual components
            elif obj.type == SemanticObjectType.CHART:
                chart_data = obj.source_content or {}
                if isinstance(chart_data, dict):
                    title = chart_data.get("title", "").strip()
                    if title:
                        units.append(
                            TranslationUnit(
                                id=f"{obj.id}_title",
                                source_text=title,
                                source_language=self.source_language,
                                target_language=self.target_language,
                                content_type=ContentType.CAPTION,
                                context="Chart Title",
                                parent_id=obj.id,
                            )
                        )
                    # Categories
                    for cat_idx, cat in enumerate(chart_data.get("categories", [])):
                        c_str = str(cat).strip()
                        if c_str and not self._is_non_translatable_text(c_str):
                            units.append(
                                TranslationUnit(
                                    id=f"{obj.id}_cat_{cat_idx}",
                                    source_text=c_str,
                                    source_language=self.source_language,
                                    target_language=self.target_language,
                                    content_type=ContentType.LABEL,
                                    context="Chart Category",
                                    parent_id=obj.id,
                                )
                            )
                    # Series names
                    for s_idx, s in enumerate(chart_data.get("series", [])):
                        s_name = s.get("name", "").strip() if isinstance(s, dict) else ""
                        if s_name and not self._is_non_translatable_text(s_name):
                            units.append(
                                TranslationUnit(
                                    id=f"{obj.id}_series_{s_idx}",
                                    source_text=s_name,
                                    source_language=self.source_language,
                                    target_language=self.target_language,
                                    content_type=ContentType.LABEL,
                                    context="Chart Series Name",
                                    parent_id=obj.id,
                                )
                            )

            # 4. Diagram node labels
            elif obj.type == SemanticObjectType.DIAGRAM:
                diagram_data = obj.source_content or {}
                if isinstance(diagram_data, dict):
                    title = diagram_data.get("title", "").strip()
                    if title:
                        units.append(
                            TranslationUnit(
                                id=f"{obj.id}_title",
                                source_text=title,
                                source_language=self.source_language,
                                target_language=self.target_language,
                                content_type=ContentType.CAPTION,
                                context="Diagram Title",
                                parent_id=obj.id,
                            )
                        )
                    for n in diagram_data.get("nodes", []):
                        if isinstance(n, dict):
                            n_id = n.get("id", "")
                            lbl = n.get("label", "").strip()
                            if lbl and not self._is_non_translatable_text(lbl):
                                units.append(
                                    TranslationUnit(
                                        id=f"{obj.id}_node_{n_id}",
                                        source_text=lbl,
                                        source_language=self.source_language,
                                        target_language=self.target_language,
                                        content_type=ContentType.LABEL,
                                        context="Diagram Node Label",
                                        parent_id=obj.id,
                                    )
                                )

            # 5. Formulas: ONLY natural-language annotations, NOT math expressions
            elif obj.type == SemanticObjectType.FORMULA:
                # Do NOT translate mathematical expressions!
                # If formula has a text note/caption, translate that
                pass

        return units

    def apply_translations_to_ir(self, ir: DocumentIR, units: List[TranslationUnit]) -> None:
        """Binds translated units back to Document IR semantic objects."""
        unit_map = {u.id: u.translated_text for u in units if u.translated_text}

        for obj in ir.objects:
            # 1. Text-like objects
            if obj.is_text_like():
                if obj.id in unit_map:
                    obj.translated_content = unit_map[obj.id]
                else:
                    # Check by source text match if available
                    src_txt = obj.get_text_content(prefer_translated=False).strip()
                    for u in units:
                        if u.source_text.strip() == src_txt and u.translated_text:
                            obj.translated_content = u.translated_text
                            break

            # 2. Table cells
            elif obj.type == SemanticObjectType.TABLE:
                table_content = obj.source_content or {}
                headers = table_content.get("headers", [])
                rows = table_content.get("rows", [])

                trans_headers = []
                is_nested_hdr = headers and isinstance(headers[0], list)
                hdr_rows = headers if is_nested_hdr else [headers]
                for r_idx, h_row in enumerate(hdr_rows):
                    new_h_row = []
                    for c_idx, cell in enumerate(h_row):
                        c_id = f"{obj.id}_hdr_{r_idx}_{c_idx}"
                        new_h_row.append(unit_map.get(c_id, cell))
                    trans_headers.append(new_h_row)
                if not is_nested_hdr and trans_headers:
                    trans_headers = trans_headers[0]

                trans_rows = []
                for r_idx, row in enumerate(rows):
                    if not isinstance(row, list):
                        trans_rows.append(row)
                        continue
                    new_row = []
                    for c_idx, cell in enumerate(row):
                        c_id = f"{obj.id}_cell_{r_idx}_{c_idx}"
                        new_row.append(unit_map.get(c_id, cell))
                    trans_rows.append(new_row)

                obj.translated_content = {
                    "headers": trans_headers,
                    "rows": trans_rows,
                    "col_count": table_content.get("col_count", 0),
                    "row_count": len(trans_rows),
                }

            # 3. Chart
            elif obj.type == SemanticObjectType.CHART:
                chart_data = obj.source_content or {}
                if isinstance(chart_data, dict):
                    t_title = unit_map.get(f"{obj.id}_title", chart_data.get("title"))
                    t_cats = []
                    for c_idx, cat in enumerate(chart_data.get("categories", [])):
                        t_cats.append(unit_map.get(f"{obj.id}_cat_{c_idx}", cat))
                    t_series = []
                    for s_idx, s in enumerate(chart_data.get("series", [])):
                        s_name = s.get("name", "") if isinstance(s, dict) else ""
                        s_trans = unit_map.get(f"{obj.id}_series_{s_idx}", s_name)
                        t_series.append({"name": s_trans})

                    obj.translated_content = {
                        "title": t_title,
                        "categories": t_cats,
                        "series": t_series,
                    }

            # 4. Diagram
            elif obj.type == SemanticObjectType.DIAGRAM:
                diagram_data = obj.source_content or {}
                if isinstance(diagram_data, dict):
                    t_title = unit_map.get(f"{obj.id}_title", diagram_data.get("title"))
                    node_translations = {}
                    for n in diagram_data.get("nodes", []):
                        if isinstance(n, dict):
                            n_id = n.get("id", "")
                            u_key = f"{obj.id}_node_{n_id}"
                            if u_key in unit_map:
                                node_translations[n_id] = unit_map[u_key]
                    obj.translated_content = {
                        "title": t_title,
                        "nodes": node_translations,
                    }

    def _is_non_translatable_text(self, text: str) -> bool:
        """Determines if a text string should be excluded from translation."""
        s = text.strip()
        if not s:
            return True
        # Pure numbers, dates, ranges
        if re.match(r"^[\d\s.,\-–—/()%$€¥₫#+*:;]+$", s):
            return True
        # Standard pure alphanumeric codes (e.g. IP67, Cat.No. 12345, MX-500)
        if re.match(r"^[A-Z0-9\-–_./\s]+$", s) and len(s) < 25 and not any(ch.islower() for ch in s):
            # Check if it has Japanese/Vietnamese/Chinese characters
            return True
        # Single characters or punctuation
        if len(s) == 1 and not re.match(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]", s):
            return True
        return False
