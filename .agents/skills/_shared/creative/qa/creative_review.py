#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
creative_review.py — Creative Scorecard (Creative Studio 2.1, Phase 4). Bổ sung bên cạnh Visual QA 2.0, KHÔNG thay thế.

Hai lớp tách bạch:
  * Technical QA (tự động, đã có: run_visual_qa)  -> PASS / WARN / FAIL.
  * Creative QA (đánh giá chủ quan theo rubric nội bộ, KHÔNG phải chuẩn ngành) -> module này.

Nguyên tắc cứng (theo Master Directive mục 7):
  1. Không bao giờ tự cho điểm. Tiêu chí không có người/agent đánh giá phù hợp = "NOT REVIEWED".
  2. Mỗi điểm bắt buộc có `evidence` (cái đã quan sát) và `basis` (đã xem gì: stills / video / audio).
  3. Reviewer cùng model + cùng ngữ cảnh KHÔNG được tuyên bố độc lập; điểm tối đa bị kẹp ở 3/5.
  4. Technical FAIL không bị scorecard che giấu: trạng thái BLOCKED_BY_TECHNICAL_FAIL, không có tổng điểm.
  5. Tổng /100 chỉ có khi 100% tiêu chí đã được đánh giá; còn lại chỉ báo điểm trên phần đã đánh giá + độ phủ.
  6. Tín hiệu đo tự động (auto_signals) là bằng chứng tham khảo, KHÔNG quy đổi thành điểm.

API:
    build_review(technical_report, scores, reviewer, issues, auto_signals, limitations, pass_number) -> dict
    extract_signals(technical_report, audio_report=None) -> dict
    render_markdown(review) -> str
    write_evidence_pack(out_dir, video_path, review, qa_dir=None, renderer_meta=None, audio_report=None) -> dict
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

NOT_REVIEWED = "NOT REVIEWED"

CRITERIA = [
    ("visual_hierarchy", "Visual hierarchy", 20),
    ("motion_quality", "Motion quality", 20),
    ("brand_consistency", "Brand consistency", 15),
    ("typography_readability", "Typography & readability", 15),
    ("storytelling_pacing", "Storytelling & pacing", 15),
    ("audio_visual_sync", "Audio-visual synchronization", 15),
]
CRITERIA_IDS = [c[0] for c in CRITERIA]
WEIGHTS = {c[0]: c[2] for c in CRITERIA}
assert sum(WEIGHTS.values()) == 100

# Loại reviewer -> có được coi là độc lập hay không
REVIEWER_KINDS = {
    "human": True,                 # người xem video thật
    "separate_agent": True,        # reviewer/agent riêng, ngữ cảnh riêng do môi trường cung cấp
    "same_context_agent": False,   # cùng model + cùng ngữ cảnh: pass tách biệt nhưng KHÔNG độc lập
    "none": False,
}
BASES = ("stills", "video", "audio", "video+audio", "metadata")
SAME_CONTEXT_MAX_SCORE = 3.0
SEVERITIES = ("low", "medium", "high")


class ReviewError(ValueError):
    """Dữ liệu review không hợp lệ (vd điểm không kèm bằng chứng)."""


def _repo_root() -> Optional[Path]:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists():
            return parent
    return None


def _norm_reviewer(reviewer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    r = dict(reviewer or {"kind": "none"})
    kind = r.get("kind", "none")
    if kind not in REVIEWER_KINDS:
        raise ReviewError(f"reviewer.kind '{kind}' không hợp lệ (hỗ trợ: {list(REVIEWER_KINDS)}).")
    r["kind"] = kind
    r["independent"] = REVIEWER_KINDS[kind]
    if kind == "same_context_agent":
        r["independence_statement"] = (
            "Review pass tách biệt nhưng cùng model và cùng ngữ cảnh với bên tạo ra video: KHÔNG phải đánh giá độc lập."
        )
    return r


def _norm_scores(scores: Optional[Dict[str, Any]], reviewer: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    scores = scores or {}
    unknown = [k for k in scores if k not in WEIGHTS]
    if unknown:
        raise ReviewError(f"Tiêu chí không tồn tại: {unknown} (hợp lệ: {CRITERIA_IDS}).")
    for cid, label, weight in CRITERIA:
        raw = scores.get(cid)
        if raw is None or raw == NOT_REVIEWED or (isinstance(raw, dict) and raw.get("score") in (None, NOT_REVIEWED)):
            reason = raw.get("reason") if isinstance(raw, dict) else None
            out[cid] = {"label": label, "weight": weight, "status": NOT_REVIEWED, "score": None,
                        "reason": reason or "Chưa có reviewer/bằng chứng phù hợp để đánh giá tiêu chí này."}
            continue
        if not isinstance(raw, dict):
            raise ReviewError(f"{cid}: điểm phải là object {{score, evidence, basis}} hoặc 'NOT REVIEWED'.")
        sc = raw.get("score")
        if isinstance(sc, bool) or not isinstance(sc, (int, float)) or not (0 <= sc <= 5):
            raise ReviewError(f"{cid}: score phải là số trong [0, 5], nhận được {sc!r}.")
        ev = (raw.get("evidence") or "").strip()
        if not ev:
            raise ReviewError(f"{cid}: không được cho điểm khi thiếu `evidence` (đã quan sát gì).")
        basis = raw.get("basis")
        if basis not in BASES:
            raise ReviewError(f"{cid}: basis phải thuộc {list(BASES)}, nhận được {basis!r}.")
        if reviewer["kind"] == "none":
            raise ReviewError(f"{cid}: không có reviewer thì không được cho điểm (dùng NOT REVIEWED).")
        capped = None
        final = float(sc)
        if not reviewer["independent"] and final > SAME_CONTEXT_MAX_SCORE:
            final, capped = SAME_CONTEXT_MAX_SCORE, f"kẹp từ {sc} xuống {SAME_CONTEXT_MAX_SCORE}: reviewer không độc lập"
        entry = {"label": label, "weight": weight, "status": "REVIEWED", "score": final, "basis": basis, "evidence": ev}
        if capped:
            entry["capped_reason"] = capped
        out[cid] = entry
    return out


def build_review(
    technical_report: Optional[Dict[str, Any]] = None,
    scores: Optional[Dict[str, Any]] = None,
    reviewer: Optional[Dict[str, Any]] = None,
    issues: Optional[List[Dict[str, Any]]] = None,
    auto_signals: Optional[Dict[str, Any]] = None,
    limitations: Optional[List[str]] = None,
    pass_number: int = 1,
) -> Dict[str, Any]:
    rv = _norm_reviewer(reviewer)
    crit = _norm_scores(scores, rv)

    tech_verdict = (technical_report or {}).get("overall_verdict") or (technical_report or {}).get("verdict") or "UNKNOWN"
    reviewed = {k: v for k, v in crit.items() if v["status"] == "REVIEWED"}
    coverage = sum(v["weight"] for v in reviewed.values())
    pct_of_reviewed = None
    if coverage:
        pct_of_reviewed = round(sum(v["weight"] * v["score"] / 5.0 for v in reviewed.values()) / coverage * 100, 1)

    if tech_verdict == "FAIL":
        status, total = "BLOCKED_BY_TECHNICAL_FAIL", None
    elif coverage == 0:
        status, total = "NOT_REVIEWED", None
    elif coverage < 100:
        status, total = "PARTIAL", None
    else:
        status, total = "COMPLETE", pct_of_reviewed

    norm_issues = []
    for i in issues or []:
        sev = i.get("severity", "medium")
        if sev not in SEVERITIES:
            raise ReviewError(f"issue.severity phải thuộc {list(SEVERITIES)}, nhận được {sev!r}.")
        if not i.get("title"):
            raise ReviewError("issue thiếu `title`.")
        norm_issues.append({"id": i.get("id"), "severity": sev, "title": i["title"], "criterion": i.get("criterion"),
                            "evidence": i.get("evidence"), "status": i.get("status", "open"), "found_in_pass": i.get("found_in_pass", pass_number)})

    return {
        "rubric": "AIWF Creative Scorecard (rubric nội bộ, không phải tiêu chuẩn ngành được chứng nhận)",
        "pass_number": pass_number,
        "reviewer": rv,
        "technical_qa": {"verdict": tech_verdict, "note": "Kết quả tự động; scorecard không thay thế và không che giấu kết quả này."},
        "status": status,
        "criteria": crit,
        "coverage_percent": coverage,
        "score_of_reviewed_percent": pct_of_reviewed,
        "total_score_100": total,
        "issues": norm_issues,
        "auto_signals": {"note": "Tín hiệu đo tự động, KHÔNG quy đổi thành điểm.", **(auto_signals or {})},
        "limitations": list(limitations or []),
    }


def extract_signals(technical_report: Optional[Dict[str, Any]], audio_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Rút tín hiệu khách quan từ báo cáo Visual QA (không chấm điểm)."""
    sig: Dict[str, Any] = {}
    tr = technical_report or {}
    m = (tr.get("technical") or {}).get("metrics") or {}
    if m:
        sig["resolution"] = f"{m.get('width')}x{m.get('height')}"
        sig["duration_s"] = m.get("duration")
        sig["has_audio"] = m.get("has_audio")
        sig["audio_lufs"] = m.get("audio_lufs")
        sig["audio_peak_dbfs"] = m.get("audio_peak_dbfs")
    frames = (tr.get("visual") or {}).get("frame_metrics") or []
    if frames:
        sig["frames_sampled"] = len(frames)
        sig["first_frame_blank"] = bool(frames[0].get("is_white") or frames[0].get("is_black") or (frames[0].get("flat_ratio", 0) >= 0.98))
        sig["flat_frames"] = sum(1 for f in frames if f.get("is_flat"))
        sig["min_motion_to_next"] = round(min(f.get("motion_to_next", 0) for f in frames), 4)
    sig["technical_findings"] = [f.get("code") for f in ((tr.get("technical") or {}).get("findings") or [])] + \
                                [f.get("code") for f in ((tr.get("visual") or {}).get("findings") or [])]
    if audio_report:
        sig["audio_mode"] = audio_report.get("mode")
    return sig


def render_markdown(review: Dict[str, Any]) -> str:
    rv = review["reviewer"]
    lines = [
        "# Creative Review",
        "",
        f"- Rubric: {review['rubric']}",
        f"- Review pass: **{review['pass_number']}** · Reviewer: `{rv['kind']}` · Độc lập: **{'có' if rv['independent'] else 'KHÔNG'}**",
    ]
    if rv.get("independence_statement"):
        lines.append(f"- {rv['independence_statement']}")
    lines += [
        f"- Technical QA (tự động): **{review['technical_qa']['verdict']}**",
        f"- Trạng thái Creative QA: **{review['status']}** · Độ phủ đánh giá: **{review['coverage_percent']}%**",
    ]
    if review["total_score_100"] is not None:
        lines.append(f"- Tổng điểm: **{review['total_score_100']}/100**")
    else:
        lines.append("- Tổng điểm /100: **không có** (chưa đánh giá đủ 100% tiêu chí hoặc bị chặn bởi Technical FAIL)")
        if review["score_of_reviewed_percent"] is not None:
            lines.append(f"- Điểm trên phần đã đánh giá: {review['score_of_reviewed_percent']}% (KHÔNG phải tổng điểm)")
    lines += ["", "| Tiêu chí | Trọng số | Kết quả | Cơ sở | Bằng chứng |", "|:---|:---:|:---:|:---|:---|"]
    for c in review["criteria"].values():
        if c["status"] == NOT_REVIEWED:
            lines.append(f"| {c['label']} | {c['weight']} | **{NOT_REVIEWED}** | - | {c['reason']} |")
        else:
            cap = f" ({c['capped_reason']})" if c.get("capped_reason") else ""
            lines.append(f"| {c['label']} | {c['weight']} | {c['score']}/5{cap} | {c['basis']} | {c['evidence']} |")
    if review["issues"]:
        lines += ["", "## Vấn đề ghi nhận", "", "| ID | Mức | Tiêu chí | Vấn đề | Trạng thái | Phát hiện ở pass |", "|:---|:---:|:---|:---|:---:|:---:|"]
        for i in review["issues"]:
            lines.append(f"| {i['id'] or '-'} | {i['severity']} | {i['criterion'] or '-'} | {i['title']} | {i['status']} | {i['found_in_pass']} |")
    sig = {k: v for k, v in review["auto_signals"].items() if k != "note"}
    if sig:
        lines += ["", "## Tín hiệu đo tự động (không quy đổi thành điểm)", "", "```json", json.dumps(sig, ensure_ascii=False, indent=2), "```"]
    if review["limitations"]:
        lines += ["", "## Giới hạn còn tồn tại", ""] + [f"- {x}" for x in review["limitations"]]
    return "\n".join(lines) + "\n"


def _sha256(path: Path, limit: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(limit)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def write_evidence_pack(
    out_dir: Any,
    video_path: Any,
    review: Dict[str, Any],
    qa_dir: Any = None,
    renderer_meta: Optional[Dict[str, Any]] = None,
    audio_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Gói bằng chứng: creative_review.json/.md, bản sao contact sheet + technical report (nhỏ),
    renderer_meta.json, audio_qa.json và manifest (đường dẫn + sha256 của MP4, MP4 không bị sao chép).
    Từ chối ghi vào bên trong Git repository (R1: không xả media/báo cáo vào repo).
    """
    out = Path(out_dir).expanduser().resolve()
    root = _repo_root()
    if root is not None and (out == root or root in out.parents):
        raise ReviewError(f"Từ chối ghi evidence pack vào trong repository ({root}). Dùng ~/Downloads/AIWF_Output/.")
    out.mkdir(parents=True, exist_ok=True)
    video = Path(video_path).expanduser().resolve()
    files: Dict[str, Any] = {}

    (out / "creative_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "creative_review.md").write_text(render_markdown(review), encoding="utf-8")
    files["creative_review"] = ["creative_review.json", "creative_review.md"]

    if qa_dir:
        qd = Path(qa_dir)
        for pat in ("*contact_sheet*", "*technical_report*"):
            for f in qd.glob(pat):
                shutil.copy2(f, out / f.name)
                files.setdefault("visual_qa", []).append(f.name)
    if renderer_meta is not None:
        (out / "renderer_meta.json").write_text(json.dumps(renderer_meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        files["renderer_meta"] = "renderer_meta.json"
    if audio_report is not None:
        (out / "audio_qa.json").write_text(json.dumps(audio_report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        files["audio_qa"] = "audio_qa.json"

    manifest = {
        "video": {"path": str(video), "exists": video.exists(),
                  "size_bytes": video.stat().st_size if video.exists() else None,
                  "sha256": _sha256(video) if video.exists() else None},
        "files": files,
        "creative_status": review["status"],
        "limitations": review["limitations"],
    }
    (out / "evidence_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Tạo Creative Review + evidence pack từ video đã render và kết quả Visual QA.")
    ap.add_argument("--video", required=True)
    ap.add_argument("--qa-report", help="technical_report.json của Visual QA (mặc định tìm cạnh video)")
    ap.add_argument("--review-input", help="JSON {reviewer, scores, issues, limitations, pass_number}; bỏ trống = tất cả NOT REVIEWED")
    ap.add_argument("--out", help="Thư mục xuất (mặc định <video>_review)")
    a = ap.parse_args(argv)

    video = Path(a.video).expanduser().resolve()
    qa_dir = video.parent / f"{video.stem}_qa"
    qa_path = Path(a.qa_report) if a.qa_report else next(iter(qa_dir.glob("*technical_report.json")), None)
    tech = json.loads(qa_path.read_text(encoding="utf-8")) if qa_path and Path(qa_path).exists() else None
    inp = json.loads(Path(a.review_input).read_text(encoding="utf-8")) if a.review_input else {}
    try:
        review = build_review(
            technical_report=tech, scores=inp.get("scores"), reviewer=inp.get("reviewer"), issues=inp.get("issues"),
            auto_signals=extract_signals(tech), limitations=inp.get("limitations"), pass_number=inp.get("pass_number", 1))
        out = Path(a.out) if a.out else video.parent / f"{video.stem}_review"
        manifest = write_evidence_pack(out, video, review, qa_dir=qa_dir if qa_dir.exists() else None)
    except ReviewError as e:
        print(f"LỖI REVIEW: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"status": review["status"], "coverage_percent": review["coverage_percent"],
                      "total_score_100": review["total_score_100"], "evidence": str(out), "manifest": manifest["files"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
