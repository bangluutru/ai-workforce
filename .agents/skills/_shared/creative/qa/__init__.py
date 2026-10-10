#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Visual QA 2.0 Package (Luật R7).
"""

from .frame_sampler import SampledFrame, extract_frame_at, sample_video_frames
from .technical_validator import (
    TechnicalFinding,
    TechnicalValidationResult,
    inspect_media_streams,
    validate_video_technical,
)
from .visual_inspector import (
    VisualFinding,
    VisualInspectionResult,
    calculate_flat_color_ratio,
    calculate_frame_difference,
    inspect_visual_frames,
)
from .contact_sheet import generate_contact_sheet
from .report_builder import QAReport, run_visual_qa
from .dom_validator import DOMValidationIssue, DOMValidationResult, validate_dom_layout

__all__ = [
    "SampledFrame",
    "extract_frame_at",
    "sample_video_frames",
    "TechnicalFinding",
    "TechnicalValidationResult",
    "inspect_media_streams",
    "validate_video_technical",
    "VisualFinding",
    "VisualInspectionResult",
    "calculate_flat_color_ratio",
    "calculate_frame_difference",
    "inspect_visual_frames",
    "generate_contact_sheet",
    "QAReport",
    "run_visual_qa",
    "DOMValidationIssue",
    "DOMValidationResult",
    "validate_dom_layout",
]
