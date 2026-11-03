#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creative Studio 2.2: kiểm thử nối Motion Director vào 10 preset (window.AIWF_MOTION),
tương thích ngược khi không có kế hoạch chuyển động, và easing chỉ ghi đè khi khai báo.
"""
import re
import sys
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED))
import bootstrap  # noqa: F401,E402

from creative.motion_director import perceptual_scale, interpolate_clamped, plan_element_motion  # noqa: E402
from creative.presets.registry import (  # noqa: E402
    EASING_TO_GSAP,
    PRESET_REGISTRY,
    build_motion_runtime_js,
    render_preset_html,
)

PRESETS_DIR = SHARED / "creative" / "presets"


def _k(js: str) -> dict:
    m = re.search(r"var K = \{ travel: ([\d.]+), scale: ([\d.]+), stagger: ([\d.]+), rot: ([\d.]+), dur: ([\d.]+) \}", js)
    assert m, js
    return dict(zip(("travel", "scale", "stagger", "rot", "dur"), map(float, m.groups())))


def test_default_runtime_is_identity():
    """Không có kế hoạch (hoặc moderate) -> mọi hệ số = 1, preset giữ nguyên số gốc."""
    assert _k(build_motion_runtime_js()) == {"travel": 1.0, "scale": 1.0, "stagger": 1.0, "rot": 1.0, "dur": 1.0}
    plan = plan_element_motion(element_id="x", motion_type="fade_in", intensity="moderate")
    k = _k(build_motion_runtime_js(plan["travel_distance_px"], plan["scale_delta"], plan["stagger_delay_sec"],
                                   plan["duration_factor"], plan["rotation_max_deg"]))
    assert k == {"travel": 1.0, "scale": 1.0, "stagger": 1.0, "rot": 1.0, "dur": 1.0}


def test_intensity_scales_factors_monotonically():
    ks = {}
    for inten in ("subtle", "moderate", "energetic"):
        p = plan_element_motion(element_id="x", motion_type="fade_in", intensity=inten)
        ks[inten] = _k(build_motion_runtime_js(p["travel_distance_px"], p["scale_delta"], p["stagger_delay_sec"],
                                               p["duration_factor"], p["rotation_max_deg"]))
    assert ks["subtle"]["travel"] < ks["moderate"]["travel"] < ks["energetic"]["travel"]
    assert ks["subtle"]["scale"] < ks["moderate"]["scale"] < ks["energetic"]["scale"]
    assert ks["subtle"]["dur"] > ks["moderate"]["dur"] > ks["energetic"]["dur"]


def test_runtime_clamps_garbage_input():
    k = _k(build_motion_runtime_js(travel_px="abc", scale_delta=float("nan"), stagger_sec=-5, duration_factor=99))
    assert k["travel"] == 1.0 and k["scale"] == 1.0 and k["stagger"] == 0.0 and k["dur"] == 4.0


@pytest.mark.parametrize("preset", list(PRESET_REGISTRY.keys()))
def test_every_template_reads_motion_runtime(preset):
    """Cả 10 template phải đọc window.AIWF_MOTION và có fallback khi mở độc lập."""
    src = (PRESETS_DIR / PRESET_REGISTRY[preset]["template_file"]).read_text(encoding="utf-8")
    assert "window.AIWF_MOTION ||" in src
    assert re.search(r"M\.(d|s|r)\(", src), "template chưa bọc quãng/độ phóng/góc qua Motion Director"
    assert "M.t(" in src and "M.at(" in src


def test_render_injects_runtime_before_template_script():
    html = render_preset_html("01_fade_in", props={"title": "T"}, duration=5.0)
    assert html.index("window.AIWF_MOTION = {") < html.index("const M = window.AIWF_MOTION")


def test_easing_override_only_when_declared():
    plan = plan_element_motion(element_id="x", motion_type="fade_in", intensity="moderate")
    html_default = render_preset_html("01_fade_in", props={"title": "T", "_motion_plan": dict(plan)})
    assert 'EASE = ""' in html_default
    plan["easing_override"] = "linear"
    html_linear = render_preset_html("01_fade_in", props={"title": "T", "_motion_plan": plan})
    assert f'EASE = "{EASING_TO_GSAP["linear"]}"' in html_linear


def test_perceptual_scale_and_clamped_interpolation():
    assert perceptual_scale(1.0, 9.0, 0.5, easing_name="linear") == pytest.approx(3.0)
    assert interpolate_clamped(-10, [0, 10], [50, 100]) == 50
    assert interpolate_clamped(20, [0, 10], [50, 100]) == 100
    assert interpolate_clamped(5, [0, 10], [1, 9], perceptual=True) == pytest.approx(3.0)
    with pytest.raises(ValueError):
        interpolate_clamped(1, [0], [1])
