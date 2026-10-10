#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Creative Shared Engines (Luật R7).
Module trung tâm cung cấp các hợp đồng dữ liệu, thẩm định storyboard, quản lý thương hiệu,
chuyển động tất định, điều phối timeline, bộ kết xuất Render Adapters và 10 Motion Presets.
"""

from .storyboard_schema import (
    ASPECT_RATIOS,
    SCENE_TYPES,
    COMPOSITION_LAYOUTS,
    TRANSITION_TYPES,
    MOTION_INTENSITIES,
    EASING_FUNCTIONS,
    STORYBOARD_SCHEMA_V2,
)
from .storyboard_validator import (
    validate_storyboard,
    calculate_storyboard_durations,
    StoryboardValidationError,
)
from .brand_profile import (
    BUILTIN_BRAND_PROFILES,
    load_brand_profile,
    validate_brand_profile,
    get_safe_area_box,
)
from .legacy_adapter import (
    is_legacy_script,
    convert_legacy_script_to_storyboard,
    estimate_scene_duration,
)
from .motion_director import (
    evaluate_easing,
    calculate_easing,
    get_intensity_params,
    deterministic_hash,
    deterministic_float,
    deterministic_choice,
    MotionState,
    interpolate_motion,
    plan_element_motion,
)
from .timeline_planner import (
    TimelineEvent,
    validate_timeline_events,
    plan_scene_timeline,
    snap_to_nearest_beat,
    TimelineValidationError,
)
from .renderers.base import (
    BaseRenderAdapter,
    RenderJob,
    RenderResult,
)
from .renderers.hyperframes_adapter import (
    HyperFramesAdapter,
    find_hyperframes_binary,
)
from .renderers.canvas_adapter import (
    Canvas2DAdapter,
)
from .render_router import (
    RenderRouter,
    render_scene,
)
from .presets.registry import (
    PRESET_REGISTRY,
    get_preset_metadata,
    list_presets,
    render_preset_html,
)

from .qa.report_builder import (
    QAReport,
    run_visual_qa,
)
from .qa.technical_validator import (
    validate_video_technical,
    TechnicalValidationResult,
)
from .qa.visual_inspector import (
    inspect_visual_frames,
    VisualInspectionResult,
)
from .qa.frame_sampler import (
    SampledFrame,
    sample_video_frames,
)
from .qa.contact_sheet import (
    generate_contact_sheet,
)
from .storyboard_renderer import (
    StoryboardRenderer,
    render_storyboard,
    StoryboardRenderResult,
)

__all__ = [
    "ASPECT_RATIOS",
    "SCENE_TYPES",
    "COMPOSITION_LAYOUTS",
    "TRANSITION_TYPES",
    "MOTION_INTENSITIES",
    "EASING_FUNCTIONS",
    "STORYBOARD_SCHEMA_V2",
    "validate_storyboard",
    "calculate_storyboard_durations",
    "StoryboardValidationError",
    "BUILTIN_BRAND_PROFILES",
    "load_brand_profile",
    "validate_brand_profile",
    "get_safe_area_box",
    "is_legacy_script",
    "convert_legacy_script_to_storyboard",
    "estimate_scene_duration",
    "evaluate_easing",
    "calculate_easing",
    "get_intensity_params",
    "deterministic_hash",
    "deterministic_float",
    "deterministic_choice",
    "MotionState",
    "interpolate_motion",
    "plan_element_motion",
    "TimelineEvent",
    "validate_timeline_events",
    "plan_scene_timeline",
    "snap_to_nearest_beat",
    "TimelineValidationError",
    "BaseRenderAdapter",
    "RenderJob",
    "RenderResult",
    "HyperFramesAdapter",
    "find_hyperframes_binary",
    "Canvas2DAdapter",
    "RenderRouter",
    "render_scene",
    "PRESET_REGISTRY",
    "get_preset_metadata",
    "list_presets",
    "render_preset_html",
    "QAReport",
    "run_visual_qa",
    "validate_video_technical",
    "TechnicalValidationResult",
    "inspect_visual_frames",
    "VisualInspectionResult",
    "SampledFrame",
    "sample_video_frames",
    "generate_contact_sheet",
    "StoryboardRenderer",
    "render_storyboard",
    "StoryboardRenderResult",
]
