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
   - INDEPENDENTLY_REVIEWED: Được thẩm định bởi agent hoặc công cụ kiểm toán độc lập có bằng chứng.
   - FAILED: Không đạt tiêu chuẩn nghiệm thu hoặc có lỗi.

2. BẢO TOÀN TÍNH TOÀN VẸN (INTEGRITY):
   - Mọi artifact bàn giao phải có mã băm SHA-256 xác thực.
   - Technical FAIL chặn đứng hoàn toàn việc phê duyệt tổng thể.
   - Ngăn chặn mạo danh thẩm định độc lập: chỉ công nhận independent khi có bằng chứng thực thi.
   - Phê duyệt con người (Human Acceptance): Khóa băm snapshot, chống replay, tự hủy hiệu lực khi nội dung thay đổi.

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

KNOWN_AGENT_ROLES = {
    "systems-architect",
    "reality-checker",
    "evidence-collector",
    "minimal-change-engineer",
    "project-shepherd",
    "ux-reviewer",
    "brand-guardian",
    "research-synthesist",
    "legal-compliance-reviewer",
    "technical-auditor",
}

FILE_EXTENSIONS = {
    ".log", ".txt", ".json", ".png", ".jpg", ".jpeg", ".pdf",
    ".docx", ".xlsx", ".pptx", ".xml", ".html", ".py", ".md",
    ".csv", ".webp", ".mp4", ".mp3", ".m4b", ".sh",
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


def compute_pack_content_hash(pack: Dict[str, Any]) -> str:
    """
    Tính mã băm SHA-256 đại diện cho toàn bộ nội dung công việc của Evidence Pack
    (task_id, runbook, danh sách steps kèm artifact hashes).
    Không bao gồm trường human_approval để tránh vòng lặp tự tham chiếu.
    """
    canonical_data = {
        "task_id": pack.get("task_id", ""),
        "runbook": pack.get("runbook", ""),
        "steps": [
            {
                "step_id": s.get("step_id"),
                "role": s.get("role"),
                "skill_used": s.get("skill_used"),
                "artifact": str(s.get("artifact", "")),
                "artifact_sha256": s.get("artifact_sha256"),
                "verification_method": s.get("verification_method"),
                "evidence_ref": s.get("evidence_ref"),
                "status": s.get("status"),
                "reviewer": s.get("reviewer"),
            }
            for s in pack.get("steps", [])
        ],
    }
    canonical_json = json.dumps(canonical_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def classify_and_validate_evidence_ref(
    evidence_ref: str,
    base_dirs: Optional[List[Path]] = None,
) -> Tuple[str, bool, Optional[str]]:
    """
    Phân loại và kiểm tra tính hợp lệ của tham chiếu bằng chứng:
    Trả về (ref_type, is_valid, issue_message).
    Các loại ref_type:
    - 'local_file': File trên đĩa (phải kiểm tra sự tồn tại).
    - 'external_url': URL ngoài (ghi nhận nhưng không công nhận là đã kiểm chứng độc lập nếu thiếu bản chụp).
    - 'execution_descriptor': Tên bộ test/lệnh (pytest, exit code).
    - 'empty_or_invalid': Thiếu hoặc không hợp lệ.
    """
    if not evidence_ref or not isinstance(evidence_ref, str):
        return "empty_or_invalid", False, "evidence_ref không được để trống."

    ref = evidence_ref.strip()
    if not ref or ref.lower() in ("none", "chưa kiểm tra", "không có", "null"):
        return "empty_or_invalid", False, f"evidence_ref '{ref}' không hợp lệ."

    if ref.startswith(("http://", "https://")):
        return "external_url", True, "URL ngoài: cú pháp hợp lệ nhưng chưa được xác thực độc lập trên đĩa."

    # Tách đường dẫn file nếu có cú pháp path:L1-L15 hoặc path#line
    file_part = ref.split(":")[0].split("#")[0].strip()
    clean_file_part = file_part.removeprefix("file://")
    p = Path(clean_file_part)

    # Nhận diện nếu là file: có đuôi mở rộng hoặc có dấu / hoặc \ hoặc file://
    has_file_ext = p.suffix.lower() in FILE_EXTENSIONS
    is_path_like = "/" in file_part or "\\" in file_part or ref.startswith("file://") or has_file_ext

    if is_path_like:
        # 1. Kiểm tra trực tiếp đường dẫn
        direct_path = Path(clean_file_part)
        if direct_path.is_file():
            return "local_file", True, None

        # 2. Kiểm tra tương đối so với base_dirs
        if base_dirs:
            for b in base_dirs:
                if b and (b / clean_file_part).is_file():
                    return "local_file", True, None

        # Nếu là path-like nhưng không tìm thấy file -> Báo lỗi thiếu file
        return "local_file", False, f"Tệp bằng chứng cục bộ không tồn tại: '{clean_file_part}'"

    # Trường hợp không phải path-like -> coi là execution_descriptor (vd: pytest_suite, claim_guard_cli)
    return "execution_descriptor", True, None


def normalize_reviewer(
    reviewer: Optional[Dict[str, Any]],
    verification_method: str = "",
    evidence_ref: str = "",
) -> Dict[str, Any]:
    """Chuẩn hóa thông tin người thẩm định và ngăn chặn mạo danh kiểm chứng độc lập."""
    r = dict(reviewer or {"kind": "none", "name": "unknown"})
    kind = r.get("kind", "none")
    name = r.get("name", "unknown")
    if kind not in REVIEWER_KINDS:
        raise EvidenceError(f"reviewer.kind '{kind}' không hợp lệ (hỗ trợ: {list(REVIEWER_KINDS)}).")

    claimed_reviewer = {
        "kind": kind,
        "name": name,
    }

    verified_reviewer = None
    verification_source = "unverified_claim"
    independent = False
    assurance_level = "LOW"

    if kind == "same_context_agent":
        verification_source = "same_context_model"
        independent = False
        assurance_level = "SELF_REVIEW"
        statement = "Thẩm định bởi cùng model và cùng ngữ cảnh hội thoại: KHÔNG PHẢI kiểm chứng độc lập."

    elif kind == "automated_test":
        verification_source = "automated_test_engine"
        verified_reviewer = name
        independent = True
        assurance_level = "AUTOMATED_VERIFIED"
        statement = f"Kiểm thử tự động thực thi qua {verification_method or name}."

    elif kind == "separate_agent":
        # Yêu cầu bằng chứng thực thi độc lập (subagent_id, execution_context='forked_subagent', hoặc log transcript)
        has_subagent_proof = (
            r.get("subagent_id") is not None
            or r.get("execution_context") == "forked_subagent"
            or (evidence_ref and any(k in evidence_ref.lower() for k in ("subagent", "task-", "transcript")))
        )
        if has_subagent_proof:
            verification_source = "subagent_execution_context"
            verified_reviewer = name
            independent = True
            assurance_level = "INDEPENDENT_SUBAGENT_VERIFIED"
            statement = f"Thẩm định độc lập bởi subagent phiên riêng biệt ({name})."
        else:
            verification_source = "unverified_claim"
            verified_reviewer = None
            independent = False
            assurance_level = "UNVERIFIED_INDEPENDENT_CLAIM"
            statement = "Khai báo separate_agent nhưng thiếu bằng chứng thực thi độc lập (hạ cấp độ tin cậy)."

    elif kind == "human":
        channel = r.get("channel", "interactive_user_confirmation")
        if channel in ("agent_simulated", "mock") or r.get("is_simulated"):
            verification_source = "simulated_human"
            verified_reviewer = None
            independent = False
            assurance_level = "SIMULATED_NOT_AUTHENTICATED"
            statement = "Phê duyệt mô phỏng bởi script/agent: KHÔNG PHẢI con người thực tế."
        else:
            verification_source = "human_session"
            verified_reviewer = name
            independent = True
            assurance_level = "HUMAN_VERIFIED"
            statement = f"Thẩm định trực tiếp bởi con người ({name})."

    else:
        statement = "Không có thẩm định viên."

    r["kind"] = kind
    r["name"] = name
    r["claimed_reviewer"] = claimed_reviewer
    r["verified_reviewer"] = verified_reviewer
    r["verification_source"] = verification_source
    r["independent"] = independent
    r["assurance_level"] = assurance_level
    r["independence_statement"] = statement
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
            "scope": "final_release",
            "approver": None,
            "channel": None,
            "verification_status": "PENDING",
            "timestamp": None,
            "bound_task_id": None,
            "pack_hash_at_approval": None,
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
    art_path = Path(art_str)
    if art_path.is_file():
        art_sha256 = compute_sha256(art_str)

    norm_rev = normalize_reviewer(reviewer, verification_method, evidence_ref)

    # Kiểm tra tính trung thực của tuyên bố
    if status in ("TESTED", "OBSERVED", "INDEPENDENTLY_REVIEWED"):
        if not verification_method or verification_method.strip() in ("", "none", "chưa kiểm tra"):
            raise EvidenceError(f"Bước '{step_id}' tuyên bố trạng thái '{status}' nhưng thiếu verification_method.")
        if not evidence_ref or evidence_ref.strip() in ("", "none", "không có"):
            raise EvidenceError(f"Bước '{step_id}' tuyên bố trạng thái '{status}' nhưng thiếu evidence_ref.")

    # A3: Cấm phong danh INDEPENDENTLY_REVIEWED khi reviewer không độc lập
    if status == "INDEPENDENTLY_REVIEWED":
        if not norm_rev.get("independent"):
            raise EvidenceError(
                f"Bước '{step_id}' tuyên bố INDEPENDENTLY_REVIEWED nhưng người thẩm định không có bằng chứng độc lập "
                f"(verification_source: {norm_rev.get('verification_source')})."
            )

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

    # Invalidate prior human approval if content changed after approval was granted
    human = pack.get("human_approval", {})
    if human.get("status") == "APPROVED":
        hash_at_appr = human.get("pack_hash_at_approval")
        current_hash = compute_pack_content_hash(pack)
        if hash_at_appr and hash_at_appr != current_hash:
            human["status"] = "AWAITING_REAPPROVAL"
            human["verification_status"] = "INVALIDATED_BY_CHANGE"
            human["invalidation_reason"] = f"Bước '{step_id}' được thêm/sửa đổi sau khi phê duyệt. Cần phê duyệt lại."

    # Tái tính toán overall_status
    recompute_overall_status(pack)
    return step_data


def recompute_overall_status(pack: Dict[str, Any]) -> str:
    """Tái tính toán trạng thái tổng thể dựa trên từng bước và phê duyệt con người."""
    steps = pack.get("steps", [])
    if not steps:
        pack["overall_status"] = "NOT_VERIFIED"
        return "NOT_VERIFIED"

    # 1. Nếu có bất kỳ bước nào FAILED -> FAILED
    if any(s.get("status") == "FAILED" for s in steps):
        pack["overall_status"] = "FAILED"
        return "FAILED"

    # 2. Nếu có bước NOT_VERIFIED hoặc IMPLEMENTED -> NEEDS_WORK
    if any(s.get("status") in ("NOT_VERIFIED", "IMPLEMENTED") for s in steps):
        pack["overall_status"] = "NEEDS_WORK"
        return "NEEDS_WORK"

    # 3. A1: Cấm tự thăng hạng VERIFIED nếu toàn bộ các bước chỉ là SELF_REVIEWED
    if all(s.get("status") == "SELF_REVIEWED" for s in steps):
        pack["overall_status"] = "SELF_REVIEWED"
        return "SELF_REVIEWED"

    # 4. Phải có ít nhất 1 bước có bằng chứng kiểm chứng thực tế (TESTED, OBSERVED, hoặc INDEPENDENTLY_REVIEWED)
    has_verifiable = any(s.get("status") in ("TESTED", "OBSERVED", "INDEPENDENTLY_REVIEWED") for s in steps)
    if not has_verifiable:
        pack["overall_status"] = "NEEDS_WORK"
        return "NEEDS_WORK"

    # 5. Nếu yêu cầu phê duyệt con người mà chưa duyệt hoặc phê duyệt không hợp lệ
    human = pack.get("human_approval", {})
    if human.get("required") or human.get("status") in ("AWAITING_REAPPROVAL", "REJECTED"):
        is_appr_valid, _ = verify_human_approval(pack)
        if not is_appr_valid or human.get("status") != "APPROVED":
            pack["overall_status"] = "AWAITING_HUMAN_APPROVAL"
            return "AWAITING_HUMAN_APPROVAL"

    # 6. Đạt chuẩn xác thực
    pack["overall_status"] = "VERIFIED"
    return "VERIFIED"


def request_human_approval(
    pack: Dict[str, Any],
    scope: str = "final_release",
    details: str = "",
) -> Dict[str, Any]:
    """Tạo yêu cầu phê duyệt gửi tới con người, khóa snapshot mã băm hiện tại."""
    pack_hash = compute_pack_content_hash(pack)
    pack["human_approval"] = {
        "required": True,
        "status": "PENDING",
        "scope": scope,
        "details": details,
        "requested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "bound_task_id": pack.get("task_id"),
        "pack_hash_at_approval": None,
        "approver": None,
        "channel": None,
        "timestamp": None,
        "notes": None,
        "verification_status": "PENDING",
    }
    recompute_overall_status(pack)
    return pack["human_approval"]


def record_human_approval(
    pack: Dict[str, Any],
    approved: bool,
    approver: str,
    notes: str = "",
    channel: str = "interactive_user_confirmation",
    auth_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Ghi nhận quyết định phê duyệt chính thức từ người dùng."""
    if not approver or not isinstance(approver, str) or not approver.strip():
        raise EvidenceError("approver bắt buộc phải là chuỗi định danh người dùng không rỗng.")

    approver_clean = approver.strip()
    if approver_clean.lower() in KNOWN_AGENT_ROLES:
        raise EvidenceError(f"Agent role '{approver_clean}' không được phép tự phê duyệt phê chuẩn của con người.")

    current_hash = compute_pack_content_hash(pack)
    task_id = pack.get("task_id", "")

    if channel in ("agent_simulated", "mock", "programmatic_test"):
        ver_status = "SIMULATED_NOT_AUTHENTICATED"
    elif channel in ("interactive_user_confirmation", "cli_prompt", "web_confirmation"):
        ver_status = "USER_CONFIRMED"
    else:
        ver_status = "UNVERIFIED_CHANNEL"

    pack["human_approval"]["required"] = True
    pack["human_approval"]["status"] = "APPROVED" if approved else "REJECTED"
    pack["human_approval"]["approver"] = approver_clean
    pack["human_approval"]["channel"] = channel
    pack["human_approval"]["verification_status"] = ver_status
    pack["human_approval"]["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    pack["human_approval"]["notes"] = notes.strip()
    pack["human_approval"]["bound_task_id"] = task_id
    pack["human_approval"]["pack_hash_at_approval"] = current_hash

    recompute_overall_status(pack)
    return pack["human_approval"]


def verify_human_approval(pack: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Thẩm định tính hợp lệ, tính toàn vẹn và chống giả mạo của phê duyệt con người.
    """
    human = pack.get("human_approval", {})
    if not human.get("required"):
        return True, []

    status = human.get("status")
    if status != "APPROVED":
        return False, [f"Phê duyệt con người chưa hoàn tất (hiện tại: {status})."]

    approver = human.get("approver")
    if not approver or not str(approver).strip():
        return False, ["Thiếu định danh người phê duyệt (approver)."]

    if str(approver).strip().lower() in KNOWN_AGENT_ROLES:
        return False, [f"Vi phạm nghiêm trọng: Agent role '{approver}' không thể tự phê duyệt phê chuẩn con người."]

    bound_task = human.get("bound_task_id")
    current_task = pack.get("task_id")
    if bound_task and bound_task != current_task:
        return False, [
            f"Phát hiện Replay Attack: Phê duyệt được cấp cho task '{bound_task}', không khớp với task hiện tại '{current_task}'."
        ]

    hash_at_approval = human.get("pack_hash_at_approval")
    current_hash = compute_pack_content_hash(pack)
    if hash_at_approval and hash_at_approval != current_hash:
        return False, [
            "Nội dung task hoặc artifact đã bị thay đổi sau khi được phê duyệt. Yêu cầu tái phê duyệt (renewed approval required)."
        ]

    return True, []


def validate_evidence_pack(
    pack_or_path: Dict[str, Any] | str | Path,
    base_dir: Optional[str | Path] = None,
) -> Tuple[bool, List[str]]:
    """
    Thẩm định toàn diện tính hợp lệ của Evidence Pack.
    Trả về: (is_valid, issues_list).
    """
    issues = []
    resolved_base_dirs: List[Path] = []

    if isinstance(pack_or_path, (str, Path)):
        p = Path(pack_or_path)
        if not p.is_file():
            return False, [f"Tệp không tồn tại: {p}"]
        resolved_base_dirs.append(p.parent)
        try:
            with open(p, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except Exception as e:
            return False, [f"Lỗi đọc JSON: {e}"]
    else:
        pack = pack_or_path

    if base_dir:
        resolved_base_dirs.append(Path(base_dir))

    if not isinstance(pack, dict):
        return False, ["Evidence pack phải là dictionary"]

    # Thêm thư mục chứa artifact nếu có
    for s in pack.get("steps", []):
        art_path = s.get("artifact")
        if art_path and Path(art_path).is_file():
            resolved_base_dirs.append(Path(art_path).parent)

    resolved_base_dirs.append(Path.cwd())

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

            # Kiểm tra mã băm artifact nếu file tồn tại
            art = s.get("artifact")
            if art:
                art_p = Path(art)
                if not art_p.is_absolute():
                    for b in resolved_base_dirs:
                        if (b / art).is_file():
                            art_p = b / art
                            break
                if art_p.is_file():
                    current_hash = compute_sha256(art_p)
                    recorded_hash = s.get("artifact_sha256")
                    if recorded_hash and recorded_hash != current_hash:
                        issues.append(
                            f"{step_id}: Mã băm SHA-256 bị sai lệch (file bị sửa sau kiểm định). "
                            f"Gốc: {recorded_hash[:12]}... Hiện tại: {current_hash[:12]}..."
                        )

            # A2: Kiểm tra evidence_ref
            ev_ref = s.get("evidence_ref")
            ref_type, ref_valid, ref_msg = classify_and_validate_evidence_ref(ev_ref, resolved_base_dirs)
            if not ref_valid:
                issues.append(f"{step_id}: {ref_msg}")

            # A3: Kiểm tra reviewer
            rev = s.get("reviewer", {})
            if rev.get("kind") == "same_context_agent" and rev.get("independent") is True:
                issues.append(f"{step_id}: same_context_agent KHÔNG ĐƯỢC tuyên bố independent=True.")

            if status == "INDEPENDENTLY_REVIEWED":
                if not rev.get("independent") or rev.get("verification_source") == "unverified_claim":
                    issues.append(
                        f"{step_id}: Trạng thái là INDEPENDENTLY_REVIEWED nhưng reviewer không chứng minh được tính độc lập "
                        f"(verification_source: {rev.get('verification_source')})."
                    )

    # Thẩm định human approval
    human = pack.get("human_approval", {})
    if human.get("required"):
        is_appr_ok, appr_issues = verify_human_approval(pack)
        if not is_appr_ok and human.get("status") == "APPROVED":
            issues.extend(appr_issues)

    # Kiểm tra mâu thuẫn giữa overall_status và các bước
    overall = pack.get("overall_status")
    if overall == "VERIFIED":
        if any(s.get("status") in ("FAILED", "NOT_VERIFIED", "IMPLEMENTED") for s in steps):
            issues.append("overall_status là VERIFIED nhưng vẫn tồn tại bước FAILED hoặc NOT_VERIFIED.")
        if all(s.get("status") == "SELF_REVIEWED" for s in steps):
            issues.append("overall_status là VERIFIED nhưng toàn bộ các chặng chỉ là SELF_REVIEWED.")
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
        "| Chặng (Step) | Vai Trò (Role) | Kỹ Năng (Skill) | Trạng Thái | Phương Pháp | Bằng Chứng (Ref) | Reviewer (Source) |",
        "|---|---|---|:---:|---|---|---|",
    ]

    for s in pack.get("steps", []):
        st = s.get("status", "NOT_VERIFIED")
        icon = "✅" if st in ("TESTED", "OBSERVED", "INDEPENDENTLY_REVIEWED") else ("❌" if st == "FAILED" else "⏳")
        rev = s.get("reviewer", {})
        rev_desc = f"{rev.get('name', 'N/A')} ({rev.get('verification_source', 'unknown')})"
        lines.append(
            f"| `{s.get('step_id')}` | `{s.get('role')}` | `{s.get('skill_used')}` | "
            f"{icon} **{st}** | {s.get('verification_method')} | `{s.get('evidence_ref')}` | {rev_desc} |"
        )

    lines.append("")
    human = pack.get("human_approval", {})
    lines.append("## Phê Duyệt Con Người (Human Acceptance Gate)")
    lines.append(f"- **Yêu cầu phê duyệt:** `{'Có' if human.get('required') else 'Không'}`")
    lines.append(f"- **Trạng thái:** **`{human.get('status', 'PENDING')}`**")
    if human.get("approver"):
        lines.append(
            f"- **Người phê duyệt:** `{human.get('approver')}` (Kênh: `{human.get('channel')}`, Xác thực: `{human.get('verification_status')}`) lúc `{human.get('timestamp')}`"
        )
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
