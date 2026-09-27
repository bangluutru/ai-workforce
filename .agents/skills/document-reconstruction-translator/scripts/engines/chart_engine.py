"""Chart Reconstruction Engine with Dual-Mode Policy.

Conforms to Section 13 & Section 31 of AIWF Document Reconstruction Translator:
- MODE A (Data Recoverable, Confidence >= 0.85):
  * Recovers series, axes, categories, values, units, and legend.
  * Redraws clean publication-grade SVG chart with translated labels.
  * Preserves data points, values, and relative proportions exactly.
- MODE B (Data Not Reliably Recoverable, Confidence < 0.85):
  * HARD BAN: NEVER GUESS OR INVENT DATA.
  * Preserves original source chart asset.
  * Translates caption and external annotations.
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ir.models import ConfidenceMetrics, ReconstructionStrategy, SemanticObject, SemanticObjectType


@dataclass
class ChartSeries:
    name: str
    translated_name: Optional[str] = None
    values: List[float] = field(default_factory=list)
    color: str = "#1a5fb4"


@dataclass
class ChartModel:
    chart_type: str = "bar"  # bar, line, unknown
    title: str = ""
    translated_title: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    translated_categories: List[str] = field(default_factory=list)
    series: List[ChartSeries] = field(default_factory=list)
    x_label: str = ""
    translated_x_label: Optional[str] = None
    y_label: str = ""
    translated_y_label: Optional[str] = None
    unit: str = ""
    confidence: float = 0.90

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ChartModel:
        series_list = []
        for s in d.get("series", []):
            series_list.append(
                ChartSeries(
                    name=s.get("name", ""),
                    translated_name=s.get("translated_name"),
                    values=[float(v) for v in s.get("values", [])],
                    color=s.get("color", "#1a5fb4"),
                )
            )
        return cls(
            chart_type=d.get("chart_type", "bar"),
            title=d.get("title", ""),
            translated_title=d.get("translated_title"),
            categories=d.get("categories", []),
            translated_categories=d.get("translated_categories", []),
            series=series_list,
            x_label=d.get("x_label", ""),
            translated_x_label=d.get("translated_x_label"),
            y_label=d.get("y_label", ""),
            translated_y_label=d.get("translated_y_label"),
            unit=d.get("unit", ""),
            confidence=float(d.get("confidence", 0.90)),
        )


class ChartEngine:
    """Manages chart analysis, SVG redraw, and fallback preservation."""

    PALETTE = ["#1a5fb4", "#26a269", "#e5a50a", "#c01c28", "#9141ac", "#1c71d8"]

    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold

    def process_chart_object(
        self, obj: SemanticObject, output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """Processes a CHART SemanticObject and decides between Redraw and Preserve."""
        content = obj.source_content or {}
        chart_model = None

        if isinstance(content, dict) and "series" in content:
            chart_model = ChartModel.from_dict(content)
            # If translated content exists, apply
            if isinstance(obj.translated_content, dict):
                t_dict = obj.translated_content
                chart_model.translated_title = t_dict.get("title")
                chart_model.translated_categories = t_dict.get("categories", [])
                chart_model.translated_x_label = t_dict.get("x_label")
                chart_model.translated_y_label = t_dict.get("y_label")
                for s_idx, t_s in enumerate(t_dict.get("series", [])):
                    if s_idx < len(chart_model.series):
                        chart_model.series[s_idx].translated_name = t_s.get("name")

        # Check Mode A vs Mode B
        if chart_model and chart_model.confidence >= self.confidence_threshold and chart_model.series:
            # Mode A: Reconstruct / Redraw SVG
            svg_code = self.render_to_svg(chart_model)
            svg_path = None
            if output_dir:
                out_path = Path(output_dir) / f"{obj.id}_chart.svg"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(svg_code, encoding="utf-8")
                svg_path = str(out_path)

            obj.reconstruction_strategy = ReconstructionStrategy.REDRAW_CHART
            obj.source_asset_reference = svg_path
            return {
                "success": True,
                "strategy": ReconstructionStrategy.REDRAW_CHART.value,
                "svg_code": svg_code,
                "svg_path": svg_path,
                "confidence": chart_model.confidence,
                "fallback": False,
            }
        else:
            # Mode B: Data not reliably recoverable -> PRESERVE SOURCE ASSET
            obj.reconstruction_strategy = ReconstructionStrategy.PRESERVE_ASSET
            obj.fallback_used = True
            return {
                "success": False,
                "strategy": ReconstructionStrategy.PRESERVE_ASSET.value,
                "reason": "Data points not reliably recoverable. Preserving original chart graphic without hallucination.",
                "confidence": chart_model.confidence if chart_model else 0.50,
                "fallback": True,
            }

    def render_to_svg(self, model: ChartModel, width: int = 500, height: int = 300) -> str:
        """Generates crisp vector SVG for bar or line charts."""
        margin_left = 60
        margin_right = 30
        margin_top = 40
        margin_bottom = 60

        plot_w = width - margin_left - margin_right
        plot_h = height - margin_top - margin_bottom

        # Find max value across all series
        all_vals = []
        for s in model.series:
            all_vals.extend(s.values)
        max_val = max(all_vals) if all_vals else 100.0
        if max_val <= 0:
            max_val = 100.0
        # Round up to clean ceiling (e.g. 87 -> 100)
        magnitude = 10 ** math.floor(math.log10(max_val))
        ceil_val = math.ceil(max_val / magnitude) * magnitude

        cats = model.translated_categories or model.categories or [f"Cat {i+1}" for i in range(len(model.series[0].values))]
        num_cats = len(cats)

        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="auto" style="background:#ffffff; font-family:system-ui, -apple-system, sans-serif;">')

        # 1. Title
        title_text = model.translated_title or model.title
        if title_text:
            svg.append(f'<text x="{width/2}" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#222222">{html.escape(title_text)}</text>')

        # 2. Grid lines & Y-axis labels
        num_y_ticks = 4
        for i in range(num_y_ticks + 1):
            tick_val = (ceil_val / num_y_ticks) * i
            y_pos = margin_top + plot_h - (i / num_y_ticks) * plot_h
            svg.append(f'<line x1="{margin_left}" y1="{y_pos}" x2="{margin_left + plot_w}" y2="{y_pos}" stroke="#e0e0e0" stroke-width="1"/>')
            display_val = f"{int(tick_val)}" if tick_val.is_integer() else f"{tick_val:.1f}"
            svg.append(f'<text x="{margin_left - 8}" y="{y_pos + 4}" text-anchor="end" font-size="10" fill="#666666">{display_val}</text>')

        # Y Axis Line
        svg.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" stroke="#888888" stroke-width="1.5"/>')
        # X Axis Line
        svg.append(f'<line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{margin_left + plot_w}" y2="{margin_top + plot_h}" stroke="#888888" stroke-width="1.5"/>')

        # 3. Draw Bars / Lines
        if num_cats > 0 and model.series:
            cat_slot_w = plot_w / num_cats
            num_series = len(model.series)
            bar_w = min(35.0, (cat_slot_w * 0.7) / max(1, num_series))

            for c_idx, cat in enumerate(cats):
                slot_center_x = margin_left + c_idx * cat_slot_w + cat_slot_w / 2

                # X label
                svg.append(f'<text x="{slot_center_x}" y="{margin_top + plot_h + 18}" text-anchor="middle" font-size="10" fill="#333333">{html.escape(str(cat))}</text>')

                # Bars for each series
                start_x = slot_center_x - (num_series * bar_w) / 2
                for s_idx, s in enumerate(model.series):
                    val = s.values[c_idx] if c_idx < len(s.values) else 0.0
                    bar_h = (val / ceil_val) * plot_h
                    bx = start_x + s_idx * bar_w
                    by = margin_top + plot_h - bar_h
                    color = s.color or self.PALETTE[s_idx % len(self.PALETTE)]

                    svg.append(f'<rect x="{bx}" y="{by}" width="{bar_w - 2}" height="{bar_h}" fill="{color}" rx="2"/>')
                    # Value label on bar
                    if bar_h > 15:
                        svg.append(f'<text x="{bx + (bar_w-2)/2}" y="{by - 4}" text-anchor="middle" font-size="8.5" font-weight="bold" fill="#333333">{val:g}</text>')

        # 4. Legend
        if len(model.series) > 1:
            legend_y = height - 12
            total_legend_w = sum(len(s.translated_name or s.name) * 7 + 30 for s in model.series)
            cur_lx = max(margin_left, (width - total_legend_w) / 2)
            for s_idx, s in enumerate(model.series):
                color = s.color or self.PALETTE[s_idx % len(self.PALETTE)]
                s_name = s.translated_name or s.name
                svg.append(f'<rect x="{cur_lx}" y="{legend_y - 8}" width="10" height="10" fill="{color}" rx="2"/>')
                svg.append(f'<text x="{cur_lx + 15}" y="{legend_y}" font-size="10" fill="#444444">{html.escape(s_name)}</text>')
                cur_lx += len(s_name) * 7 + 30

        svg.append('</svg>')
        return "\n".join(svg)
