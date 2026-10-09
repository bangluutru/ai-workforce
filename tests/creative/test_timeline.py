"""
Unit tests for AIWF Creative Studio 2.0 — Motion Director & Timeline Planner.
Tests:
- Easing functions and boundary conditions
- Deterministic pseudo-random generation
- Motion interpolation and state keyframing
- Timeline event validation and collision detection
- Beat snapping algorithm
- Scene timeline planning across audio alignment modes
"""
import pytest
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SHARED = ROOT / ".agents" / "skills" / "_shared"
import sys
sys.path.insert(0, str(SHARED))
import bootstrap  # noqa: F401,E402

from creative.motion_director import (
    calculate_easing,
    deterministic_hash,
    deterministic_float,
    interpolate_motion,
    plan_element_motion,
    MotionState,
    INTENSITY_PROFILES
)
from creative.timeline_planner import (
    TimelineEvent,
    validate_timeline_events,
    snap_to_nearest_beat,
    plan_scene_timeline
)


class TestEasingFunctions:
    """Kiểm tra các hàm làm mượt (easing functions) và giá trị biên."""

    def test_linear_boundaries(self):
        assert calculate_easing("linear", 0.0) == pytest.approx(0.0)
        assert calculate_easing("linear", 0.5) == pytest.approx(0.5)
        assert calculate_easing("linear", 1.0) == pytest.approx(1.0)

    def test_ease_in_boundaries(self):
        assert calculate_easing("ease-in", 0.0) == pytest.approx(0.0)
        assert calculate_easing("ease-in", 1.0) == pytest.approx(1.0)
        # ease-in starts slower: f(0.5) < 0.5
        assert calculate_easing("ease-in", 0.5) < 0.5

    def test_ease_out_boundaries(self):
        assert calculate_easing("ease-out", 0.0) == pytest.approx(0.0)
        assert calculate_easing("ease-out", 1.0) == pytest.approx(1.0)
        # ease-out starts faster: f(0.5) > 0.5
        assert calculate_easing("ease-out", 0.5) > 0.5

    def test_spring_easing(self):
        assert calculate_easing("spring", 0.0) == pytest.approx(0.0)
        assert calculate_easing("spring", 1.0) == pytest.approx(1.0)

    def test_clamping(self):
        assert calculate_easing("linear", -0.5) == pytest.approx(0.0)
        assert calculate_easing("linear", 1.5) == pytest.approx(1.0)
        assert calculate_easing("ease-in", -1.0) == pytest.approx(0.0)
        assert calculate_easing("ease-in", 2.0) == pytest.approx(1.0)

    def test_unknown_easing_fallback(self):
        # Fallback to linear
        assert calculate_easing("non_existent_curve", 0.4) == pytest.approx(0.4)


class TestDeterminism:
    """Kiểm tra tính tái tạo 100% (deterministic) của animation seeds."""

    def test_deterministic_hash_consistency(self):
        h1 = deterministic_hash("scene_1", "text_title", "seed_42")
        h2 = deterministic_hash("scene_1", "text_title", "seed_42")
        assert h1 == h2

    def test_deterministic_float_range(self):
        for i in range(100):
            val = deterministic_float(f"seed_{i}", min_val=-15.0, max_val=15.0)
            assert -15.0 <= val <= 15.0

    def test_deterministic_variation_across_seeds(self):
        val1 = deterministic_float("seed_alpha", 0.0, 100.0)
        val2 = deterministic_float("seed_beta", 0.0, 100.0)
        assert val1 != val2


class TestMotionPlanning:
    """Kiểm tra lập kế hoạch chuyển động cho phần tử visual."""

    def test_plan_element_motion_structure(self):
        plan = plan_element_motion(
            element_id="badge_logo",
            motion_type="bounce",
            duration=3.0,
            intensity="moderate",
            seed="test_run_1"
        )
        assert plan["element_id"] == "badge_logo"
        assert plan["duration"] == 3.0
        assert len(plan["keyframes"]) >= 3
        # First keyframe should be at 0.0, last keyframe at 1.0 progress
        assert plan["keyframes"][0]["progress"] == 0.0
        assert plan["keyframes"][-1]["progress"] == 1.0

    def test_plan_reproducibility(self):
        plan_a = plan_element_motion("card", "slide_up", 2.0, "subtle", seed="reproduce_42")
        plan_b = plan_element_motion("card", "slide_up", 2.0, "subtle", seed="reproduce_42")
        assert plan_a == plan_b

    def test_interpolate_motion(self):
        state_start = MotionState(x=0.0, y=0.0, scale_x=0.0, scale_y=0.0, opacity=0.0)
        state_end = MotionState(x=100.0, y=200.0, scale_x=1.0, scale_y=1.0, opacity=1.0)
        
        mid = interpolate_motion(state_start, state_end, 0.5, easing="linear")
        assert mid.x == pytest.approx(50.0)
        assert mid.y == pytest.approx(100.0)
        assert mid.opacity == pytest.approx(0.5)


class TestTimelineValidation:
    """Kiểm tra xác thực sự kiện dòng thời gian."""

    def test_valid_timeline_events(self):
        events = [
            TimelineEvent("e1", "title", 0.0, 1.0),
            TimelineEvent("e2", "body", 1.0, 3.0),
            TimelineEvent("e3", "cta", 3.0, 4.0),
        ]
        valid, errors = validate_timeline_events(events, total_duration=5.0)
        assert valid is True
        assert len(errors) == 0

    def test_event_out_of_bounds(self):
        events = [
            TimelineEvent("e1", "title", 0.0, 6.0),
        ]
        valid, errors = validate_timeline_events(events, total_duration=5.0)
        assert valid is False
        assert any("vượt quá thời lượng scene" in e for e in errors)

    def test_event_negative_start(self):
        events = [
            TimelineEvent("e1", "title", -0.5, 2.0),
        ]
        valid, errors = validate_timeline_events(events, total_duration=5.0)
        assert valid is False
        assert any("thời gian bắt đầu âm" in e for e in errors)

    def test_event_duration_invalid(self):
        events = [
            TimelineEvent("e1", "title", 2.0, 1.5),
        ]
        valid, errors = validate_timeline_events(events, total_duration=5.0)
        assert valid is False
        assert any("lớn hơn thời gian kết thúc" in e for e in errors)


class TestBeatSnapping:
    """Kiểm tra thuật toán bắt nhịp âm nhạc."""

    def test_snap_within_threshold(self):
        beats = [0.5, 1.0, 1.5, 2.0, 2.5]
        # 1.08s is within 0.15s of 1.0s -> snaps to 1.0
        snapped = snap_to_nearest_beat(1.08, beats, max_shift=0.15)
        assert snapped == 1.0

    def test_snap_exceeding_threshold_preserved(self):
        beats = [0.5, 1.0, 1.5, 2.0]
        # 1.25s is 0.25s away from 1.0 and 1.5 -> exceeds max_shift 0.10, remains 1.25
        snapped = snap_to_nearest_beat(1.25, beats, max_shift=0.10)
        assert snapped == 1.25

    def test_snap_empty_beats(self):
        assert snap_to_nearest_beat(2.34, []) == 2.34


class TestSceneTimelinePlanning:
    """Kiểm tra lập kế hoạch toàn cảnh scene timeline."""

    def test_sequential_planning(self):
        scene = {
            "id": "scene_01",
            "type": "content",
            "elements": [
                {"id": "heading", "type": "text"},
                {"id": "chart", "type": "graphic"},
                {"id": "summary", "type": "text"}
            ]
        }
        res = plan_scene_timeline(scene, scene_duration=6.0, alignment_mode="sequential")
        assert res["valid"] is True
        assert len(res["events"]) == 3
        # Verify events do not overlap
        events = res["events"]
        assert events[0].start_time == 0.0
        assert events[1].start_time >= events[0].end_time
        assert events[2].start_time >= events[1].end_time
        assert events[2].end_time <= 6.0

    def test_beat_synced_planning(self):
        scene = {
            "id": "scene_beat",
            "type": "content",
            "elements": [
                {"id": "beat_1", "type": "graphic"},
                {"id": "beat_2", "type": "graphic"}
            ]
        }
        beats = [0.0, 1.2, 2.4, 3.6, 4.8]
        res = plan_scene_timeline(
            scene,
            scene_duration=5.0,
            alignment_mode="beat_synced",
            beat_timestamps=beats
        )
        assert res["valid"] is True
        assert len(res["events"]) == 2
