"""Tests Creative Scorecard (Phase 4): không tự cho điểm, ràng buộc bằng chứng/độc lập, không che Technical FAIL."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SHARED = ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED))
import bootstrap  # noqa: F401,E402
from creative.qa import creative_review as cr  # noqa: E402

PASS_TECH = {"overall_verdict": "PASS"}
FAIL_TECH = {"overall_verdict": "FAIL"}


def _s(score, basis="video", ev="đã xem"):
    return {"score": score, "basis": basis, "evidence": ev}


def test_default_is_all_not_reviewed():
    r = cr.build_review(PASS_TECH)
    assert r["status"] == "NOT_REVIEWED" and r["coverage_percent"] == 0 and r["total_score_100"] is None
    assert all(c["status"] == cr.NOT_REVIEWED for c in r["criteria"].values())
    assert sum(c["weight"] for c in r["criteria"].values()) == 100


def test_score_requires_evidence_basis_and_reviewer():
    human = {"kind": "human"}
    for bad in ({"score": 4}, {"score": 4, "evidence": " ", "basis": "video"}, {"score": 4, "evidence": "x"},
                {"score": 9, "evidence": "x", "basis": "video"}):
        with pytest.raises(cr.ReviewError):
            cr.build_review(PASS_TECH, {"visual_hierarchy": bad}, human)
    with pytest.raises(cr.ReviewError):                      # không có reviewer thì không được chấm
        cr.build_review(PASS_TECH, {"visual_hierarchy": _s(4)}, None)
    with pytest.raises(cr.ReviewError):                      # tiêu chí lạ
        cr.build_review(PASS_TECH, {"foo": _s(3)}, human)


def test_same_context_reviewer_is_not_independent_and_capped():
    r = cr.build_review(PASS_TECH, {"visual_hierarchy": _s(5)}, {"kind": "same_context_agent"})
    assert r["reviewer"]["independent"] is False and "KHÔNG phải đánh giá độc lập" in r["reviewer"]["independence_statement"]
    c = r["criteria"]["visual_hierarchy"]
    assert c["score"] == 3.0 and "kẹp" in c["capped_reason"]
    h = cr.build_review(PASS_TECH, {"visual_hierarchy": _s(5)}, {"kind": "human"})
    assert h["reviewer"]["independent"] is True and h["criteria"]["visual_hierarchy"]["score"] == 5.0


def test_partial_has_no_total_and_complete_has_total():
    r = cr.build_review(PASS_TECH, {"visual_hierarchy": _s(4), "motion_quality": _s(5)}, {"kind": "human"})
    assert r["status"] == "PARTIAL" and r["coverage_percent"] == 40 and r["total_score_100"] is None
    assert r["score_of_reviewed_percent"] == 90.0          # (20*4/5 + 20*5/5)/40
    full = {k: _s(5) for k in cr.CRITERIA_IDS}
    c = cr.build_review(PASS_TECH, full, {"kind": "human"})
    assert c["status"] == "COMPLETE" and c["total_score_100"] == 100.0


def test_technical_fail_is_never_hidden():
    full = {k: _s(5) for k in cr.CRITERIA_IDS}
    r = cr.build_review(FAIL_TECH, full, {"kind": "human"})
    assert r["status"] == "BLOCKED_BY_TECHNICAL_FAIL" and r["total_score_100"] is None
    assert r["technical_qa"]["verdict"] == "FAIL"
    assert "BLOCKED_BY_TECHNICAL_FAIL" in cr.render_markdown(r)


def test_issue_validation_and_markdown_labels_not_reviewed():
    with pytest.raises(cr.ReviewError):
        cr.build_review(PASS_TECH, issues=[{"title": "x", "severity": "catastrophic"}])
    r = cr.build_review(PASS_TECH, issues=[{"id": "C1", "title": "lỗi", "severity": "high"}], limitations=["chưa nghe audio"])
    md = cr.render_markdown(r)
    assert "NOT REVIEWED" in md and "chưa nghe audio" in md and "không có" in md


def test_extract_signals_flags_blank_first_frame():
    tr = {"technical": {"metrics": {"width": 1280, "height": 720, "has_audio": True}, "findings": []},
          "visual": {"frame_metrics": [{"is_white": True, "flat_ratio": 1.0, "is_flat": True, "motion_to_next": 0.05},
                                       {"is_white": False, "flat_ratio": 0.5, "is_flat": False, "motion_to_next": 0.2}],
                     "findings": []}}
    s = cr.extract_signals(tr)
    assert s["first_frame_blank"] is True and s["flat_frames"] == 1 and s["has_audio"] is True


def test_evidence_pack_outside_repo_only(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    review = cr.build_review(PASS_TECH)
    m = cr.write_evidence_pack(tmp_path / "pack", video, review, renderer_meta={"actual": ["hyperframes"]}, audio_report={"mode": "narration"})
    assert m["video"]["sha256"] and (tmp_path / "pack" / "creative_review.md").exists()
    assert (tmp_path / "pack" / "renderer_meta.json").exists() and (tmp_path / "pack" / "audio_qa.json").exists()
    assert not (tmp_path / "pack" / "v.mp4").exists()        # không sao chép media lớn
    with pytest.raises(cr.ReviewError):
        cr.write_evidence_pack(ROOT / "docs" / "_should_not_exist", video, review)
    assert not (ROOT / "docs" / "_should_not_exist").exists()


def test_cli_roundtrip(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"fake")
    out = subprocess.run([sys.executable, str(SHARED / "creative" / "qa" / "creative_review.py"), "--video", str(video),
                          "--out", str(tmp_path / "o")], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout)["status"] == "NOT_REVIEWED"
