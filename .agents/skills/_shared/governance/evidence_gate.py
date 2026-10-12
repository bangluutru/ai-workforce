#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evidence_gate.py — AIWF Shared Governance Evidence Gate Engine (Luật R7).

Cung cấp hợp đồng bằng chứng thống nhất (Standardized Evidence Contract),
ngăn chặn tuyên bố hoàn thành khống (False Done / Zero Unverified Claims Ban - Rule R3 §9),
và phân định rạch ròi giữa các mức độ kiểm chứng.

Nguyên tắc cốt lõi:
1. 7 TRẠNG THÁI BẰNG CHỨNG CHUẨN:
   - NOT_VERIFIED: Mặc định khi chưa có kiểm chứng.
   - IMPLEMENTED: File/mã nguồn đã viết nhưng chưa chạy test.
   - TESTED: Đã chạy lệnh kiểm thử tự động với exit code xác định.
   - OBSERVED: Đã trực tiếp quan sát kết quả (screenshot, DOM, console log).
   - SELF_REVIEWED: Đã tự rà soát bởi cùng model (kẹp trần <= 3.0/5, independent=False).
   - INDEPENDENTLY_REVIEWED: Được thẩm định bởi agent hoặc công cụ kiểm toán độc lập.
   - FAILED: Không đạt tiêu chuẩn nghiệm thu hoặc có lỗi.

2. BẢO TOÀN TÍNH TOÀN VẸN (INTEGRITY):
   - Mọi artifact bàn giao phải có mã băm SHA-256 xác thực.
   - Technical FAIL chặn đứng hoàn toàn việc phê duyệt tổng thể.
   - Agent KHÔNG THỂ tự thăng hạng NOT_VERIFIED thành VERIFIED.

CLI:
    python3 .agents/skills/_shared/governance/evidence_gate.py --validate <evidence_pack.json>
    python3 .agents/skills/_shared/governance/evidence_gate.py --summary <evidence_pack.json>
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VALID_STATUSES = {
    "NOT_VERIFIED",
    "IMPLEMENTED",
    "TESTED",
    "OBSERVED",
    "SELF_REVIEWED",
    "INDEPENDENTLY_REVIEWED",
    "FAILED",
}

REVIEWER_KINDS = {
    "human": True,                 # Con người thẩm định trực tiếp
    "separate_agent": True,        # Agent/subagent chạy trong ngữ cảnh riêng
    "automated_test": True,        # Bộ test tự động (pytest, playwright, script)
    "same_context_agent": False,   # Cùng model + cùng context: KHÔNG ĐỘC LẬP
    "none": False,
}

SAME_CONTEXT_MAX_SCORE = 3.0


class EvidenceError(ValueError):
    """Lỗi dữ liệu bằng chứng không hợp lệ."""


def compute_sha256(file_path: str | Path) -> str:
    """Tính toán mã băm SHA-256 của một file trên đĩa."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Tệp không tồn tại để tính sha256: {p}")
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def normalize_reviewer(reviewer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Chuẩn hóa thông tin người thẩm định."""
    r = dict(reviewer or {"kind": "none", "name": "unknown"})
    kind = r.get("kind", "none")
    if kind not in REVIEWER_KINDS:
        raise EvidenceError(f"reviewer.kind '{kind}' không hợp lệ (hỗ trợ: {list(REVIEWER_KINDS)}).")
    
    r["kind"] = kind
    r["independent"] = REVIEWER_KINDS[kind]
    if kind == "same_context_agent":
        r["independence_statement"] = (
            "Thẩm định bởi cùng model và cùng ngữ cảnh hội thoại: KHÔNG PHẢI kiểm chứng độc lập."
        )
    return r


def create_evidence_pack(
    task_id: str,
    runbook: str,
    steps: Optional[List[Dict[str, Any]]] = None,
    human_approval: Optional[Dict[str, Any]] = None,
    out_dir: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Khởi tạo một Evidence Pack có cấu trúc."""
    if not task_id or not isinstance(task_id, str):
        raise EvidenceError("task_id bắt buộc phải là chuỗi không rỗng.")
    if not runbook or not isinstance(runbook, str):
        raise EvidenceError("runbook bắt buộc phải là chuỗi không rỗng.")

    pack = {
        "$schema_version": "1.0",
        "task_id": task_id.strip(),
        "runbook": runbook.strip(),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "overall_status": "NOT_VERIFIED",
        "steps": [],
        "human_approval": {
            "required": False,
            "status": "PENDING",
            "approver": None,
            "timestamp": None,
            "notes": None,
        },
    }

    if human_approval:
        pack["human_approval"].update(human_approval)

    if steps:
        for s in steps:
            add_step_evidence(
                pack=pack,
                step_id=s["step_id"],
                role=s["role"],
                skill_used=s["skill_used"],
                artifact=s["artifact"],
                verification_method=s["verification_method"],
                evidence_ref=s["evidence_ref"],
                status=s["status"],
                reviewer=s.get("reviewer"),
                remaining_risk=s.get("remaining_risk", ""),
            )

    return pack


def add_step_evidence(
    pack: Dict[str, Any],
    step_id: str,
    role: str,
    skill_used: str,
    artifact: str | Path,
    verification_method: str,
    evidence_ref: str,
    status: str,
    reviewer: Optional[Dict[str, Any]] = None,
    remaining_risk: str = "",
) -> Dict[str, Any]:
    """Thêm một bước thẩm định vào Evidence Pack."""
    if status not in VALID_STATUSES:
        raise EvidenceError(f"Trạng thái '{status}' không hợp lệ (hỗ trợ: {list(VALID_STATUSES)}).")

    art_str = str(artifact)
    art_sha256 = None
    if Path(art_str).is_file():
        art_sha256 = compute_sha256(art_str)

    norm_rev = normalize_reviewer(reviewer)

    # Kiểm tra tính trung thực của tuyên bố
    if status in ("TESTED", "OBSERVED", "INDEPENDENTLY_REVIEWED"):
        if not verification_method or verification_method.strip() in ("", "none", "chưa kiểm tra"):
            raise EvidenceError(f"Bước '{step_id}' tuyên bố trạng thái '{status}' nhưng thiếu verification_method.")
        if not evidence_ref or evidence_ref.strip() in ("", "none", "không có"):
            raise EvidenceError(f"Bước '{step_id}' tuyên bố trạng thái '{status}' nhưng thiếu evidence_ref.")

    step_data = {
        "step_id": step_id,
        "role": role,
        "skill_used": skill_used,
        "artifact": art_str,
        "artifact_sha256": art_sha256,
        "verification_method": verification_method,
        "evidence_ref": evidence_ref,
        "status": status,
        "reviewer": norm_rev,
        "remaining_risk": remaining_risk or "Chưa ghi nhận rủi ro tồn đọng",
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    # Cập nhật hoặc thay thế bước đã tồn tại cùng step_id
    existing_idx = next((i for i, s in enumerate(pack["steps"]) if s["step_id"] == step_id), -1)
    if existing_idx >= 0:
        pack["steps"][existing_idx] = step_data
    else:
        pack["steps"].append(step_data)

    # Tái tính toán overall_status
    recompute_overall_status(pack)
    return step_data


def recompute_overall_status(pack: Dict[str, Any]) -> str:
    """Tái tính toán trạng thái tổng thể dựa trên từng bước và phê duyệt con người."""
    steps = pack.get("steps", [])
    if not steps:
        pack["overall_status"] = "NOT_VERIFIED"
        return "NOT_VERIFIED"

    # Nếu có bất kỳ bước nào FAILED -> BLOCKED_BY_FAIL
    if any(s.get("status") == "FAILED" for s in steps):
        pack["overall_status"] = "FAILED"
        return "FAILED"

    # Nếu có bước NOT_VERIFIED hoặc IMPLEMENTED -> NEEDS_WORK
    if any(s.get("status") in ("NOT_VERIFIED", "IMPLEMENTED") for s in steps):
        pack["overall_status"] = "NEEDS_WORK"
        return "NEEDS_WORK"

    # Nếu yêu cầu phê duyệt con người mà chưa duyệt
    human = pack.get("human_approval", {})
    if human.get("required") and human.get("status") != "APPROVED":
        pack["overall_status"] = "AWAITING_HUMAN_APPROVAL"
        return "AWAITING_HUMAN_APPROVAL"

    # Tất cả các bước đều đã TESTED, OBSERVED, hoặc REVIEWED
    pack["overall_status"] = "VERIFIED"
    return "VERIFIED"


def record_human_approval(
    pack: Dict[str, Any],
    approved: bool,
    approver: str,
    notes: str = "",
) -> Dict[str, Any]:
    """Ghi nhận quyết định phê duyệt chính thức từ người dùng."""
    if not approver or not isinstance(approver, str):
        raise EvidenceError("approver bắt buộc phải là chuỗi định danh người dùng.")

    pack["human_approval"]["status"] = "APPROVED" if approved else "REJECTED"
    pack["human_approval"]["approver"] = approver.strip()
    pack["human_approval"]["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pack["human_approval"]["notes"] = notes.strip()

    recompute_overall_status(pack)
    return pack["human_approval"]


def validate_evidence_pack(pack_or_path: Dict[str, Any] | str | Path) -> Tuple[bool, List[str]]:
    """
    Thẩm định toàn diện tính hợp lệ của Evidence Pack.
    Trả về: (is_valid, issues_list).
    """
    issues = []
    if isinstance(pack_or_path, (str, Path)):
        p = Path(pack_or_path)
        if not p.is_file():
            return False, [f"Tệp không tồn tại: {p}"]
        try:
            with open(p, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except Exception as e:
            return False, [f"Lỗi đọc JSON: {e}"]
    else:
        pack = pack_or_path

    if not isinstance(pack, dict):
        return False, ["Evidence pack phải là dictionary"]

    # Kiểm tra các trường cấp 1
    for req in ("task_id", "runbook", "overall_status", "steps"):
        if req not in pack:
            issues.append(f"Thiếu trường bắt buộc '{req}'")

    steps = pack.get("steps", [])
    if not isinstance(steps, list):
        issues.append("Trường 'steps' phải là một mảng")
    else:
        for idx, s in enumerate(steps):
            step_id = s.get("step_id", f"step_{idx}")
            status = s.get("status")
            if status not in VALID_STATUSES:
                issues.append(f"{step_id}: Trạng thái '{status}' không hợp lệ.")

            # Kiểm tra mã băm nếu file tồn tại
            art = s.get("artifact")
            if art and Path(art).is_file():
                current_hash = compute_sha256(art)
                recorded_hash = s.get("artifact_sha256")
                if recorded_hash and recorded_hash != current_hash:
                    issues.append(
                        f"{step_id}: Mã băm SHA-256 bị sai lệch (file bị sửa sau kiểm định). "
                        f"Gốc: {recorded_hash[:12]}... Hiện tại: {current_hash[:12]}..."
                    )

            # Kiểm tra reviewer
            rev = s.get("reviewer", {})
            if rev.get("kind") == "same_context_agent" and rev.get("independent") is True:
                issues.append(f"{step_id}: same_context_agent KHÔNG ĐƯỢC tuyên bố independent=True.")

    # Kiểm tra mâu thuẫn giữa overall_status và các bước
    overall = pack.get("overall_status")
    if overall == "VERIFIED":
        if any(s.get("status") in ("FAILED", "NOT_VERIFIED", "IMPLEMENTED") for s in steps):
            issues.append("overall_status là VERIFIED nhưng vẫn tồn tại bước FAILED hoặc NOT_VERIFIED.")
        human = pack.get("human_approval", {})
        if human.get("required") and human.get("status") != "APPROVED":
            issues.append("overall_status là VERIFIED nhưng human_approval chưa APPROVED.")

    return len(issues) == 0, issues


def render_evidence_summary_md(pack: Dict[str, Any]) -> str:
    """Kết xuất bản tóm tắt hồ sơ bằng chứng sang Markdown."""
    lines = [
        f"# 📋 HỒ SƠ BẰNG CHỨNG (EVIDENCE PACK): {pack.get('task_id', 'UNKNOWN')}",
        f"- **Runbook:** `{pack.get('runbook', 'N/A')}`",
        f"- **Thời gian khởi tạo:** `{pack.get('created_at', 'N/A')}`",
        f"- **Trạng thái tổng thể:** **`{pack.get('overall_status', 'UNKNOWN')}`**",
        "",
        "## Danh Sách Các Chặng Thẩm Định (Verification Steps)",
        "| Chặng (Step) | Vai Trò (Role) | Kỹ Năng (Skill) | Trạng Thái | Phương Pháp Thẩm Định | Bằng Chứng (Ref) |",
        "|---|---|---|:---:|---|---|",
    ]

    for s in pack.get("steps", []):
        st = s.get("status", "NOT_VERIFIED")
        icon = "✅" if st in ("TESTED", "OBSERVED", "INDEPENDENTLY_REVIEWED") else ("❌" if st == "FAILED" else "⏳")
        lines.append(
            f"| `{s.get('step_id')}` | `{s.get('role')}` | `{s.get('skill_used')}` | "
            f"{icon} **{st}** | {s.get('verification_method')} | `{s.get('evidence_ref')}` |"
        )

    lines.append("")
    human = pack.get("human_approval", {})
    lines.append("## Phê Duyệt Con Người (Human Acceptance Gate)")
    lines.append(f"- **Yêu cầu phê duyệt:** `{'Có' if human.get('required') else 'Không'}`")
    lines.append(f"- **Trạng thái:** **`{human.get('status', 'PENDING')}`**")
    if human.get("approver"):
        lines.append(f"- **Người phê duyệt:** `{human.get('approver')}` lúc `{human.get('timestamp')}`")
    if human.get("notes"):
        lines.append(f"- **Ghi chú:** {human.get('notes')}")

    return "\n".join(lines)


def write_evidence_pack_file(pack: Dict[str, Any], out_path: str | Path) -> Path:
    """Lưu Evidence Pack ra file JSON trên đĩa."""
    p = Path(out_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False, indent=2)
    return p


def main():
    parser = argparse.ArgumentParser(description="AIWF Evidence Gate Engine CLI")
    parser.add_argument("--validate", help="Đường dẫn file evidence_pack.json cần thẩm định")
    parser.add_argument("--summary", help="In bản tóm tắt markdown của evidence pack")
    args = parser.parse_args()

    if args.validate:
        valid, issues = validate_evidence_pack(args.validate)
        if valid:
            print(f"✅ Evidence Pack hợp lệ 100%: {args.validate}")
            sys.exit(0)
        else:
            print(f"❌ Phát hiện {len(issues)} lỗi vi phạm trong Evidence Pack:")
            for iss in issues:
                print(f"  - {iss}")
            sys.exit(1)

    if args.summary:
        with open(args.summary, "r", encoding="utf-8") as f:
            pack = json.load(f)
        print(render_evidence_summary_md(pack))
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
