#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storyboard_schema.py — Hợp đồng đặc tả Storyboard v2.0 cho AIWF Creative Studio.
Định nghĩa JSON Schema v2.0 và các hằng số tiêu chuẩn phân cảnh (Luật R7).
"""

from typing import Dict, Any, Tuple

# Bảng kích thước chuẩn theo tỷ lệ khung hình
ASPECT_RATIOS: Dict[str, Tuple[int, int]] = {
    "1:1": (1080, 1080),    # Square (Instagram, Facebook, LinkedIn post)
    "16:9": (1920, 1080),  # Landscape Full HD (YouTube, TV, Web)
    "9:16": (1080, 1920),  # Portrait Full HD (TikTok, Reels, Shorts)
    "4:5": (1080, 1350),   # Portrait Feed (Instagram Feed)
}

# Các loại phân cảnh được hỗ trợ
SCENE_TYPES = [
    "motion_graphics",   # Đồ họa chuyển động (typography, chart, cards, kinetic)
    "stock_media",       # Video cảnh quay thực tế (Pexels, Pixabay, local)
    "photo_kenburns",    # Ảnh tĩnh có chuyển động lia máy/zoom Ken Burns
    "hand_drawn"         # Hoạt hình vẽ tay Canvas 2D
]

# Các kiểu bố cục (Composition Layouts)
COMPOSITION_LAYOUTS = [
    "centered",
    "split_left",
    "split_right",
    "top_bottom",
    "grid",
    "card_stack"
]

# Các hiệu ứng chuyển cảnh (Transitions)
TRANSITION_TYPES = [
    "none",
    "fade",
    "slide_left",
    "slide_right",
    "zoom",
    "wipe"
]

# Các mức cường độ chuyển động
MOTION_INTENSITIES = [
    "subtle",
    "moderate",
    "energetic"
]

# Các hàm nội suy chuyển động (Easing)
EASING_FUNCTIONS = [
    "linear",
    "ease-in",
    "ease-out",
    "ease-in-out",
    "spring",
    "cubic-bezier"
]

# JSON Schema v2.0 đầy đủ
STORYBOARD_SCHEMA_V2: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AIWFCreativeStoryboardV2",
    "type": "object",
    "required": [
        "schema_version",
        "project_id",
        "fps",
        "resolution",
        "scenes"
    ],
    "properties": {
        "schema_version": {
            "type": "string",
            "enum": ["2.0"]
        },
        "project_id": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]+$"
        },
        "title": {
            "type": "string",
            "default": "Untitled Project"
        },
        "purpose": {
            "type": "string",
            "default": "general"
        },
        "language": {
            "type": "string",
            "enum": ["vi", "en", "ja"],
            "default": "vi"
        },
        "fps": {
            "type": "integer",
            "enum": [24, 30, 60]
        },
        "resolution": {
            "type": "object",
            "required": ["width", "height"],
            "properties": {
                "width": {
                    "type": "integer",
                    "minimum": 360,
                    "maximum": 3840
                },
                "height": {
                    "type": "integer",
                    "minimum": 360,
                    "maximum": 3840
                }
            }
        },
        "aspect_ratio": {
            "type": "string",
            "enum": list(ASPECT_RATIOS.keys())
        },
        "target_duration_seconds": {
            "type": "number",
            "minimum": 1.0,
            "maximum": 600.0
        },
        "brand_profile": {
            "type": "string",
            "default": "default"
        },
        "scenes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "id",
                    "type",
                    "duration_seconds",
                    "visual_goal"
                ],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^[a-zA-Z0-9_-]+$"
                    },
                    "type": {
                        "type": "string",
                        "enum": SCENE_TYPES
                    },
                    "duration_seconds": {
                        "type": "number",
                        "minimum": 0.5,
                        "maximum": 120.0
                    },
                    "narration": {
                        "type": "string",
                        "default": ""
                    },
                    "visual_goal": {
                        "type": "string"
                    },
                    "composition": {
                        "type": "object",
                        "properties": {
                            "layout": {
                                "type": "string",
                                "enum": COMPOSITION_LAYOUTS
                            },
                            "primary_subject": {
                                "type": "string"
                            },
                            "background_type": {
                                "type": "string",
                                "enum": ["solid", "gradient", "pattern", "video", "image"]
                            },
                            "background_value": {
                                "type": "string"
                            }
                        }
                    },
                    "motion": {
                        "type": "object",
                        "properties": {
                            "preset": {
                                "type": "string"
                            },
                            "intensity": {
                                "type": "string",
                                "enum": MOTION_INTENSITIES
                            },
                            "easing": {
                                "type": "string",
                                "enum": EASING_FUNCTIONS
                            }
                        }
                    },
                    "transition": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": TRANSITION_TYPES
                            },
                            "duration_seconds": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 5.0
                            }
                        }
                    },
                    "assets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "path"],
                            "properties": {
                                "id": { "type": "string" },
                                "type": {
                                    "type": "string",
                                    "enum": ["image", "video", "audio", "font", "vector"]
                                },
                                "path": { "type": "string" },
                                "alt": { "type": "string" }
                            }
                        }
                    }
                }
            }
        }
    }
}
