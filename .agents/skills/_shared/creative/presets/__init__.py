#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Motion Presets Module (Luật R7).
"""

from .registry import (
    PRESET_REGISTRY,
    get_preset_metadata,
    list_presets,
    render_preset_html,
)

__all__ = [
    "PRESET_REGISTRY",
    "get_preset_metadata",
    "list_presets",
    "render_preset_html",
]
