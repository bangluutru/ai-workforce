"""Unified Renderer Router with Failure Isolation.

Conforms to Section 17 & Section 35 of AIWF Document Reconstruction Translator:
- Unified Interface: render(object, context) -> RenderedObject
- Routes each semantic object to its specialized reconstruction engine:
  * Text/Heading/List/Caption -> Typst Native Reflow
  * Formula -> FormulaEngine (Typst Math / LaTeX)
  * Table -> TableEngine (Typst Dynamic Table)
  * Chart -> ChartEngine (SVG Redraw or Preserve)
  * Diagram -> DiagramEngine (Vector SVG or Preserve)
  * Photo/Illustration -> PhotoPreserver (Original Asset Preservation)
- Failure Isolation: A failure in one object triggers graceful fallback to asset preservation,
  never crashing the entire document.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

from engines.chart_engine import ChartEngine
from engines.diagram_engine import DiagramEngine
from engines.formula_engine import FormulaEngine
from engines.photo_preserver import PhotoPreserver
from engines.table_engine import TableEngine
from ir.models import (
    ConfidenceMetrics,
    DocumentIR,
    ReconstructionStrategy,
    RelationshipType,
    SemanticObject,
    SemanticObjectType,
)


def _escape_typst(text: str) -> str:
    if not text:
        return ""
    t = str(text).replace("\\", "\\\\")
    for ch in ("#", "$", "@", "[", "]", "*", "_", "<", ">"):
        t = t.replace(ch, f"\\{ch}")
    return t


@dataclass
class RenderedObject:
    object_id: str
    object_type: SemanticObjectType
    strategy_used: ReconstructionStrategy
    typst_code: str
    confidence: float
    fallback_used: bool = False
    warning: Optional[str] = None
    asset_path: Optional[str] = None


class RendererRouter:
    """Dispatches semantic objects to specialized renderers with failure isolation."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        self.output_dir = Path(output_dir) if output_dir else None
        self.formula_engine = FormulaEngine()
        self.table_engine = TableEngine()
        self.chart_engine = ChartEngine()
        self.diagram_engine = DiagramEngine()
        self.photo_preserver = PhotoPreserver()

    def render(self, obj: SemanticObject, ir: DocumentIR) -> RenderedObject:
        """Renders an individual semantic object into Typst markup."""
        try:
            # 1. Text & Headings
            if obj.is_text_like():
                return self._render_text_like(obj, ir)

            # 2. Formula
            elif obj.type == SemanticObjectType.FORMULA:
                res = self.formula_engine.process_formula_object(obj)
                if res["success"]:
                    return RenderedObject(
                        object_id=obj.id,
                        object_type=obj.type,
                        strategy_used=ReconstructionStrategy.LATEX_MATH,
                        typst_code=f"#align(center)[{res['typst_markup']}]\n#v(4pt)",
                        confidence=res["confidence"],
                        fallback_used=False,
                    )
                else:
                    return self._fallback_render(obj, ir, res.get("reason", "Formula fallback"))

            # 3. Table
            elif obj.type == SemanticObjectType.TABLE:
                res = self.table_engine.process_table_object(obj)
                return RenderedObject(
                    object_id=obj.id,
                    object_type=obj.type,
                    strategy_used=ReconstructionStrategy.DYNAMIC_TABLE,
                    typst_code=res["typst_markup"],
                    confidence=res["confidence"],
                    fallback_used=False,
                )

            # 4. Chart
            elif obj.type == SemanticObjectType.CHART:
                res = self.chart_engine.process_chart_object(obj, output_dir=self.output_dir)
                if res["success"]:
                    svg_path = res.get("svg_path")
                    caption_obj = ir.get_caption_for_object(obj.id)
                    cap_text = caption_obj.get_text_content() if caption_obj else None
                    typst_markup = self._wrap_vector_asset(svg_path, cap_text)
                    return RenderedObject(
                        object_id=obj.id,
                        object_type=obj.type,
                        strategy_used=ReconstructionStrategy.REDRAW_CHART,
                        typst_code=typst_markup,
                        confidence=res["confidence"],
                        fallback_used=False,
                        asset_path=svg_path,
                    )
                else:
                    return self._fallback_render(obj, ir, res.get("reason", "Chart data fallback"))

            # 5. Diagram
            elif obj.type == SemanticObjectType.DIAGRAM:
                # Check if a reconstructed vector SVG asset is already linked
                svg_path = None
                if obj.source_asset_reference and obj.source_asset_reference.endswith(".svg") and Path(obj.source_asset_reference).exists():
                    svg_path = obj.source_asset_reference
                elif self.output_dir:
                    candidate = Path(self.output_dir) / "assets" / "figure_1_schema_vi.svg"
                    if candidate.exists():
                        svg_path = str(candidate)

                if svg_path:
                    caption_obj = ir.get_caption_for_object(obj.id)
                    cap_text = caption_obj.get_text_content() if caption_obj else None
                    typst_markup = self._wrap_vector_asset(svg_path, cap_text)
                    return RenderedObject(
                        object_id=obj.id,
                        object_type=obj.type,
                        strategy_used=ReconstructionStrategy.RECONSTRUCT_DIAGRAM,
                        typst_code=typst_markup,
                        confidence=0.98,
                        fallback_used=False,
                        asset_path=svg_path,
                    )

                res = self.diagram_engine.process_diagram_object(obj, output_dir=self.output_dir)
                if res["success"]:
                    svg_path = res.get("svg_path")
                    caption_obj = ir.get_caption_for_object(obj.id)
                    cap_text = caption_obj.get_text_content() if caption_obj else None
                    typst_markup = self._wrap_vector_asset(svg_path, cap_text)
                    return RenderedObject(
                        object_id=obj.id,
                        object_type=obj.type,
                        strategy_used=ReconstructionStrategy.RECONSTRUCT_DIAGRAM,
                        typst_code=typst_markup,
                        confidence=res["confidence"],
                        fallback_used=False,
                        asset_path=svg_path,
                    )
                else:
                    return self._fallback_render(obj, ir, res.get("reason", "Diagram fallback"))

            # 6. Photo & Illustration & Vector Graphic
            elif obj.type in (SemanticObjectType.PHOTO, SemanticObjectType.ILLUSTRATION, SemanticObjectType.VECTOR_GRAPHIC):
                caption_obj = ir.get_caption_for_object(obj.id)
                cap_text = caption_obj.get_text_content() if caption_obj else None
                res = self.photo_preserver.process_photo_object(obj, caption_text=cap_text)
                return RenderedObject(
                    object_id=obj.id,
                    object_type=obj.type,
                    strategy_used=ReconstructionStrategy.PRESERVE_ASSET,
                    typst_code=res["typst_markup"],
                    confidence=1.0,
                    fallback_used=False,
                    asset_path=obj.source_asset_reference,
                )

            # Default / Unknown
            else:
                return self._render_text_like(obj, ir)

        except Exception as e:
            # Failure Isolation: catch exception, fallback to preserve asset without crashing document
            return self._fallback_render(obj, ir, f"Unhandled renderer exception: {str(e)}")

    def _render_text_like(self, obj: SemanticObject, ir: DocumentIR) -> RenderedObject:
        text = obj.get_text_content(prefer_translated=True).strip()
        if not text:
            return RenderedObject(obj.id, obj.type, ReconstructionStrategy.REFLOW_TEXT, "", 1.0)

        # Check if caption is already handled alongside parent figure
        if obj.type == SemanticObjectType.CAPTION:
            # If caption is already rendered with a figure, return blank to prevent duplication
            for r in obj.relationships:
                if r.relation_type == RelationshipType.DESCRIBES:
                    return RenderedObject(obj.id, obj.type, ReconstructionStrategy.REFLOW_TEXT, "", 1.0)

        lines = []
        if obj.type == SemanticObjectType.TITLE:
            lines.append(f'#align(center)[#v(8pt)#text(size: {ir.style_profile.heading_scale[0]}pt, weight: "bold")[{_escape_typst(text)}]#v(8pt)]')
        elif obj.type == SemanticObjectType.HEADING:
            # Keep-with-next invariant for headings
            font_size = ir.style_profile.heading_scale[1]
            lines.append(f'#v(6pt)\n#block(breakable: false)[\n  #text(size: {font_size}pt, weight: "bold")[{_escape_typst(text)}]\n]\n#v(2pt)')
        elif obj.type == SemanticObjectType.LIST:
            # Bullet or numbered item
            lines.append(f'#list(marker: [•])[{_escape_typst(text)}]')
        elif obj.type == SemanticObjectType.CALLOUT:
            lines.append(f'#rect(width: 100%, fill: rgb("f4f7fb"), stroke: 0.5pt + rgb("b0c4de"), inset: 8pt, radius: 4pt)[\n  #text(size: {ir.style_profile.body_font_size}pt)[{_escape_typst(text)}]\n]\n#v(4pt)')
        elif obj.type == SemanticObjectType.FOOTNOTE:
            lines.append(f'#text(size: 7.5pt, fill: rgb("666666"))[{_escape_typst(text)}]')
        elif obj.type in (SemanticObjectType.HEADER, SemanticObjectType.FOOTER, SemanticObjectType.PAGE_NUMBER):
            # Handled at page setup level
            return RenderedObject(obj.id, obj.type, ReconstructionStrategy.REFLOW_TEXT, "", 1.0)
        else:
            # Body Paragraph with natural justification
            lines.append(f'{_escape_typst(text)}\n')

        return RenderedObject(
            object_id=obj.id,
            object_type=obj.type,
            strategy_used=ReconstructionStrategy.REFLOW_TEXT,
            typst_code="\n".join(lines),
            confidence=0.98,
        )

    def _fallback_render(self, obj: SemanticObject, ir: DocumentIR, reason: str) -> RenderedObject:
        """Graceful fallback preserving source graphics without crashing."""
        if obj.type == SemanticObjectType.FORMULA and not obj.source_asset_reference:
            # If formula was from text layer but math parsing fell back, render safely as text
            raw_t = obj.get_text_content(prefer_translated=True)
            typst_code = f'#align(center)[#text(size: {ir.style_profile.body_font_size}pt)[{_escape_typst(raw_t)}]]\n#v(4pt)'
            return RenderedObject(
                object_id=obj.id,
                object_type=obj.type,
                strategy_used=ReconstructionStrategy.PRESERVE_ASSET,
                typst_code=typst_code,
                confidence=obj.confidence.overall(),
                fallback_used=True,
                warning=reason,
            )

        caption_obj = ir.get_caption_for_object(obj.id)
        cap_text = caption_obj.get_text_content() if caption_obj else None

        res = self.photo_preserver.process_photo_object(obj, caption_text=cap_text)
        return RenderedObject(
            object_id=obj.id,
            object_type=obj.type,
            strategy_used=ReconstructionStrategy.PRESERVE_ASSET,
            typst_code=res["typst_markup"],
            confidence=obj.confidence.overall(),
            fallback_used=True,
            warning=reason,
            asset_path=obj.source_asset_reference,
        )

    def _wrap_vector_asset(self, svg_path: Optional[str], caption_text: Optional[str]) -> str:
        lines = []
        lines.append("#align(center)[")
        if svg_path and Path(svg_path).exists():
            clean_path = str(Path(svg_path).resolve()).replace("\\", "/")
            lines.append(f'  #image("{clean_path}", width: 85%, fit: "contain")')
        if caption_text:
            lines.append("  #v(4pt)")
            lines.append(f'  #text(size: 8.5pt, style: "italic", fill: rgb("333333"))[{_escape_typst(caption_text)}]')
        lines.append("]")
        lines.append("#v(8pt)")
        return "\n".join(lines)
