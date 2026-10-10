"""Tests chuyển cảnh Creative Studio 2.1 (Phase 3)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parent.parent.parent / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED))
import bootstrap  # noqa: F401,E402
from creative.storyboard_renderer import StoryboardRenderer  # noqa: E402
from creative.storyboard_validator import validate_storyboard  # noqa: E402
from creative.transitions import build_concat_filter, plan_transitions, validate_transitions  # noqa: E402
from ffmpeg_tools import ffprobe_bin  # noqa: E402


def _sb(n=3, dur=3.0, **extra):
    sb = {"schema_version": "2.0", "project_id": "tr", "fps": 30, "resolution": {"width": 480, "height": 480},
          "scenes": [{"id": f"s{i + 1}", "type": "motion_graphics", "duration_seconds": dur,
                      "visual_goal": f"c{i + 1}", "motion": {"preset": "01_fade_in"}} for i in range(n)]}
    sb.update(extra)
    return sb


def test_no_declaration_means_hard_cut():
    sb = _sb()
    assert plan_transitions(sb, [3, 3, 3]) == [("none", 0.0), ("none", 0.0)]


def test_default_and_scene_override_and_clamp():
    sb = _sb(transitions={"default": "fade", "duration": 0.5})
    sb["scenes"][1]["transition"] = {"type": "wipe", "duration_seconds": 0.4}
    assert plan_transitions(sb, [3, 3, 3]) == [("fade", 0.5), ("wipe", 0.4)]
    # cảnh ngắn: kẹp ≤ 45% cảnh ngắn hơn
    assert plan_transitions(_sb(transitions={"default": "fade", "duration": 1.5}), [1.0, 1.0, 1.0])[0] == ("fade", 0.45)
    # quá ngắn -> hạ về cắt thẳng
    assert plan_transitions(_sb(transitions={"default": "fade"}), [0.3, 0.3, 0.3])[0] == ("none", 0.0)


def test_scene_level_zero_or_loose_duration_is_tolerated():
    sb = _sb(dur=30.0)
    sb["scenes"][0]["transition"] = {"type": "fade", "duration_seconds": 0.0}     # hợp lệ theo schema v2.0 cũ
    sb["scenes"][1]["transition"] = {"type": "fade", "duration_seconds": 9.0}
    ok, errs = validate_storyboard(sb)
    assert ok, errs
    assert plan_transitions(sb, [30, 30, 30]) == [("none", 0.0), ("fade", 1.5)]


def test_kill_switch_and_validation():
    assert plan_transitions(_sb(transitions={"default": "fade", "enabled": False}), [3, 3, 3]) == [("none", 0.0)] * 2
    assert not validate_transitions(_sb(transitions={"default": "zoom", "duration": 0.6}))
    for bad in ({"default": "spin"}, {"duration": 9}, {"enabled": "yes"}, []):
        ok, errs = validate_storyboard(_sb(transitions=bad))
        assert not ok and errs, bad
    ok, _ = validate_storyboard(_sb())          # storyboard v2.0 cũ vẫn hợp lệ
    assert ok


def test_filter_graph_offsets_preserve_nominal_starts():
    # cảnh 3.0s + đuôi 0.5; cảnh 3.0s + đuôi 0.4; cảnh cuối 3.0s  -> tổng danh nghĩa 9.0s
    plan = [("fade", 0.5), ("wipe", 0.4)]
    fc, last = build_concat_filter([3.5, 3.4, 3.0], plan, 30)
    assert "xfade=transition=fade:duration=0.500:offset=3.000" in fc
    assert "xfade=transition=wipeleft:duration=0.400:offset=6.000" in fc and last == "m2"


def test_real_render_total_duration_unchanged(tmp_path):
    sb = _sb(n=3, dur=2.0, transitions={"default": "fade", "duration": 0.4})
    sb["scenes"][1]["transition"] = {"type": "slide_left", "duration_seconds": 0.4}
    r = StoryboardRenderer().render_storyboard(sb, output_path=tmp_path / "o.mp4", work_dir=tmp_path / "w", run_qa=False)
    if not r.success and "hyperframes" in (r.error_message or "").lower():
        pytest.skip(f"Renderer không khả dụng: {r.error_message}")
    assert r.success, r.error_message
    d = json.loads(subprocess.run([ffprobe_bin(), "-v", "error", "-show_entries", "format=duration", "-of", "json",
                                   str(tmp_path / "o.mp4")], capture_output=True, text=True).stdout)
    assert abs(float(d["format"]["duration"]) - 6.0) < 0.15, d      # = tổng thời lượng cảnh, không co lại
    assert abs(r.total_duration - 6.0) < 1e-6


def test_real_render_without_transitions_unchanged_path(tmp_path):
    r = StoryboardRenderer().render_storyboard(_sb(n=2, dur=2.0), output_path=tmp_path / "o.mp4",
                                               work_dir=tmp_path / "w", run_qa=False)
    assert r.success, r.error_message
    assert (tmp_path / "w" / "concat_list.txt").exists()            # đường cắt thẳng cũ (concat demuxer)
