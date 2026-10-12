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
   - TESTED: Khai báo đã chạy kiểm thử kèm tham chiếu bằng chứng tồn tại trên đĩa (CLAIM; xác minh thực thi cần runner tin cậy).
   - OBSERVED: Đã trực tiếp quan sát kết quả (screenshot, DOM, console log) có bằng chứng.
   - SELF_REVIEWED: Đã tự rà soát bởi cùng model (kẹp trần <= 3.0/5, independent=False).
   - INDEPENDENTLY_REVIEWED: Được thẩm định bởi agent/công cụ độc lập có chứng thực thực thi tin cậy.
   - FAILED: Không đạt tiêu chuẩn nghiệm thu hoặc có lỗi.

2. BẢO TOÀN TÍNH TOÀN VẸN (INTEGRITY & FAIL-CLOSED):
   - Mọi artifact và file bằng chứng phải có mã băm SHA-256 xác thực.
   - Chống giả mạo thẩm định độc lập: Khai báo metadata (subagent_id, forked_subagent)
     KHÔNG ĐỒNG NGHĨA VỚI độc lập. Cần có trusted execution attestation.
   - Chống giả mạo phê duyệt con người: Không chấp nhận metadata caller tự khai báo
     (channel, auth_token, free-text approver) làm authenticated approval.
   - Khi thiếu nguồn xác thực tin cậy: Giữ phê duyệt ở mức APPROVAL_CLAIMED,
     Tier 3 release giữ trạng thái BLOCKED hoặc AWAITING_HUMAN_APPROVAL.
     "Fail closed, not fake secure."

CLI:
    python3 .agents/skills/_shared/governance/evidence_gate.py --validate <evidence_pack.json>
    python3 .agents/skills/_shared/governance/evidence_gate.py --summary <evidence_pack.json>
"""

from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

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

APPROVAL_STATES = {
    "APPROVAL_NOT_REQUESTED",
    "APPROVAL_REQUESTED",
    "APPROVAL_CLAIMED",
    "APPROVAL_AUTHENTICATED",
    "APPROVAL_REJECTED",
    "APPROVAL_INVALIDATED",
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

# ---------------------------------------------------------------------------
# TRUST BOUNDARY (fail-closed)
#
# Mọi dữ liệu do caller cung cấp (đối số hàm, JSON, Evidence Pack, metadata agent,
# trusted_attestation, verified=True, source=..., subagent_id, exit_code=...) đều là
# CLAIM, không phải bằng chứng. Chỉ một verifier nằm NGOÀI ranh giới dữ liệu (code
# đăng ký trong tiến trình, không thể nạp từ JSON) mới được xác lập "verified".
#
# HIỆN TẠI AIWF KHÔNG CÓ verifier tin cậy nào được cài đặt -> registry rỗng ->
# mọi xác minh độc lập / thực thi test / phê duyệt con người đều FAIL-CLOSED.
# Không tạo verifier giả. Test chỉ được cắm verifier mô phỏng qua monkeypatch.
# ---------------------------------------------------------------------------
VERIFIER_AUTOMATED_TEST = "automated_test"
VERIFIER_INDEPENDENT_REVIEW = "independent_review"
VERIFIER_HUMAN_APPROVAL = "human_approval"

UNVERIFIED_INDEPENDENT_CLAIM = "UNVERIFIED_INDEPENDENT_CLAIM"

_TRUSTED_VERIFIERS: Dict[str, Callable[[Dict[str, Any]], bool]] = {}


def _trusted_verify(kind: str, claim: Dict[str, Any]) -> bool:
    """Hỏi verifier tin cậy (nếu có). Không có / lỗi / trả khác `True` -> False."""
    fn = _TRUSTED_VERIFIERS.get(kind)
    if fn is None:
        return False
    try:
        return fn(copy.deepcopy(claim)) is True
    except Exception:
        return False


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
    (task_id, runbook, danh sách steps kèm artifact hashes và evidence hashes).
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
                "evidence_ref_sha256": s.get("evidence_ref_sha256"),
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
    status: str = "TESTED",
) -> Tuple[str, bool, Optional[str]]:
    """
    Phân loại và kiểm tra CẤU TRÚC của tham chiếu bằng chứng:
    Trả về (ref_type, is_valid, issue_message).
    `is_valid` chỉ nghĩa là tham chiếu TỒN TẠI và đúng cấu trúc; KHÔNG nghĩa là
    việc thực thi đã được xác minh (xem is_verified_automated_test).
    Các loại ref_type:
    - 'local_file': File trên đĩa (tồn tại; nội dung không được suy diễn PASS).
    - 'supporting_log': File log/json/txt/xml hỗ trợ (tồn tại, không rỗng khi TESTED).
    - 'screenshot': Ảnh chụp thực tế (tồn tại và kiểm tra hash).
    - 'external_url': URL ngoài (chỉ là reference, không phải bằng chứng đã xác minh).
    - 'arbitrary_string': Chuỗi tùy ý (kể cả 'exit_code=0') (BỊ TỪ CHỐI).
    """
    if not evidence_ref or not isinstance(evidence_ref, str):
        return "empty_or_invalid", False, "evidence_ref không được để trống."

    ref = evidence_ref.strip()
    if not ref or ref.lower() in ("none", "chưa kiểm tra", "không có", "null"):
        return "empty_or_invalid", False, f"evidence_ref '{ref}' không hợp lệ."

    if ref.startswith(("http://", "https://")):
        return "external_url", True, "URL ngoài: cú pháp hợp lệ nhưng chỉ là reference, chưa được kiểm chứng độc lập cục bộ."

    # Tách đường dẫn file nếu có cú pháp path:L1-L15 hoặc path#line
    file_part = ref.split(":")[0].split("#")[0].strip()
    clean_file_part = file_part.removeprefix("file://")
    p = Path(clean_file_part)

    has_file_ext = p.suffix.lower() in FILE_EXTENSIONS
    is_path_like = "/" in file_part or "\\" in file_part or ref.startswith("file://") or has_file_ext

    if is_path_like:
        direct_path = Path(clean_file_part)
        found_file: Optional[Path] = None
        if direct_path.is_file():
            found_file = direct_path
        elif base_dirs:
            for b in base_dirs:
                if b and (b / clean_file_part).is_file():
                    found_file = (b / clean_file_part).resolve()
                    break

        if not found_file:
            return "local_file", False, f"Tệp bằng chứng cục bộ không tồn tại: '{clean_file_part}'"

        # Phân loại cụ thể dựa trên loại file
        ext = found_file.suffix.lower()
        if ext in (".png", ".jpg", ".jpeg", ".webp"):
            return "screenshot", True, None
        if ext in (".log", ".txt", ".json", ".xml"):
            # Chỉ kiểm tra cấu trúc (không rỗng). TUYỆT ĐỐI không suy diễn PASS từ từ khóa nội dung.
            if status == "TESTED" and found_file.stat().st_size == 0:
                return "supporting_log", False, f"Tệp log '{found_file.name}' rỗng, không chứa kết quả thực thi kiểm thử."
            return "supporting_log", True, None

        return "local_file", True, None

    # Mọi chuỗi không phải tệp/URL (kể cả 'exit_code=0') -> BỊ TỪ CHỐI
    return "arbitrary_string", False, f"evidence_ref '{ref}' là chuỗi tùy ý, thiếu bản ghi thực thi kiểm thử có thể truy vết trên đĩa."


def normalize_reviewer(
    reviewer: Optional[Dict[str, Any]],
    verification_method: str = "",
    evidence_ref: str = "",
    trusted_attestation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Chuẩn hóa thông tin người thẩm định. CHỈ GHI NHẬN CLAIM, không bao giờ xác lập verified.

    `trusted_attestation` được giữ trong chữ ký để tương thích ngược nhưng BỊ BỎ QUA:
    dict do caller truyền vào (verified=True, source=..., subagent_id, execution_context,
    independent=True...) luôn là dữ liệu không tin cậy. Việc xác minh chỉ diễn ra tại thời điểm
    quyết định, qua verifier ngoài ranh giới dữ liệu (is_verified_* / verify_independent_review).
    """
    r = dict(reviewer or {"kind": "none", "name": "unknown"})
    kind = r.get("kind", "none")
    name = r.get("name", "unknown")
    if kind not in REVIEWER_KINDS:
        raise EvidenceError(f"reviewer.kind '{kind}' không hợp lệ (hỗ trợ: {list(REVIEWER_KINDS)}).")

    claimed_reviewer = {
        "kind": kind,
        "name": name,
        "declared_subagent_id": r.get("subagent_id"),
        "declared_execution_context": r.get("execution_context"),
    }

    verification_source = "unverified_claim"
    assurance_level = "LOW"

    if kind == "same_context_agent":
        verification_source = "same_context_model"
        assurance_level = "SELF_REVIEW"
        statement = "Thẩm định bởi cùng model và cùng ngữ cảnh hội thoại: KHÔNG PHẢI kiểm chứng độc lập."
    elif kind == "automated_test":
        assurance_level = "UNVERIFIED"
        statement = (
            f"Khai báo kiểm thử tự động ({verification_method or name}) được lưu để audit; "
            "chưa có bằng chứng thực thi được xác minh bởi runner tin cậy."
        )
    elif kind == "separate_agent":
        assurance_level = UNVERIFIED_INDEPENDENT_CLAIM
        statement = "Khai báo separate_agent chưa được verifier tin cậy xác minh (không được công nhận độc lập)."
    elif kind == "human":
        verification_source = "unattested_human_claim"
        assurance_level = "UNATTESTED_HUMAN_CLAIM"
        statement = f"Khai báo thẩm định con người chưa được verifier tin cậy xác minh ({name})."
    else:
        statement = "Không có thẩm định viên."

    r["kind"] = kind
    r["name"] = name
    r["claimed_reviewer"] = claimed_reviewer
    r["verified_reviewer"] = None
    r["verification_source"] = verification_source
    r["independent"] = False
    r["assurance_level"] = assurance_level
    r["independence_statement"] = statement
    return r


def _resolve_local_path(ref: str, base_dirs: List[Path]) -> Optional[Path]:
    clean = ref.split(":")[0].split("#")[0].strip().removeprefix("file://")
    if not clean:
        return None
    p = Path(clean)
    if p.is_file():
        return p
    if not p.is_absolute():
        for b in base_dirs:
            if b and (b / clean).is_file():
                return b / clean
    return None


def _step_base_dirs(step: Dict[str, Any], base_dirs: Optional[List[Path]] = None) -> List[Path]:
    dirs = [Path(b) for b in (base_dirs or [])]
    art = step.get("artifact")
    if art and Path(str(art)).is_file():
        dirs.append(Path(str(art)).parent)
    dirs.append(Path.cwd())
    return dirs


def hash_integrity_issues(
    step: Dict[str, Any],
    step_id: str,
    base_dirs: List[Path],
) -> List[str]:
    """Phát hiện artifact / file bằng chứng đã bị sửa đổi so với mã băm SHA-256 đã ghi."""
    issues: List[str] = []
    art = step.get("artifact")
    if art:
        art_p = Path(str(art))
        if not art_p.is_absolute():
            art_p = _resolve_local_path(str(art), base_dirs) or art_p
        if art_p.is_file():
            recorded = step.get("artifact_sha256")
            current = compute_sha256(art_p)
            if recorded and recorded != current:
                issues.append(
                    f"{step_id}: Mã băm SHA-256 bị sai lệch (file bị sửa sau kiểm định). "
                    f"Gốc: {recorded[:12]}... Hiện tại: {current[:12]}..."
                )
    ev_ref = step.get("evidence_ref")
    recorded_ev = step.get("evidence_ref_sha256")
    if recorded_ev and isinstance(ev_ref, str):
        ev_p = _resolve_local_path(ev_ref, base_dirs)
        if ev_p and ev_p.is_file():
            cur_ev = compute_sha256(ev_p)
            if cur_ev != recorded_ev:
                issues.append(
                    f"{step_id}: Tệp bằng chứng đã bị sửa đổi sau kiểm thử (evidence hash mismatch). "
                    f"Gốc: {recorded_ev[:12]}... Hiện tại: {cur_ev[:12]}..."
                )
    return issues


def _evidence_intact(step: Dict[str, Any], base_dirs: Optional[List[Path]] = None) -> bool:
    """Evidence tồn tại, đúng cấu trúc, còn nguyên vẹn so với hash đã ghi (local file bắt buộc có hash)."""
    dirs = _step_base_dirs(step, base_dirs)
    ref_type, ok, _ = classify_and_validate_evidence_ref(step.get("evidence_ref"), dirs, step.get("status", "TESTED"))
    if not ok:
        return False
    if ref_type != "external_url" and not step.get("evidence_ref_sha256"):
        return False
    return not hash_integrity_issues(step, str(step.get("step_id", "?")), dirs)


def _verification_claim(step: Dict[str, Any], pack: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    pack = pack or {}
    return {"task_id": pack.get("task_id"), "runbook": pack.get("runbook"), "step": step}


def is_verified_automated_test(
    step: Dict[str, Any],
    pack: Optional[Dict[str, Any]] = None,
    base_dirs: Optional[List[Path]] = None,
) -> bool:
    """
    True CHỈ KHI: reviewer khai báo automated_test, evidence còn nguyên vẹn, VÀ runner tin cậy
    xác nhận thực thi. reviewer.kind / verification_method / exit_code / nội dung log KHÔNG đủ.
    Hiện chưa có runner tin cậy -> luôn False (fail-closed).
    """
    if (step.get("reviewer") or {}).get("kind") != "automated_test":
        return False
    if not _evidence_intact(step, base_dirs):
        return False
    return _trusted_verify(VERIFIER_AUTOMATED_TEST, _verification_claim(step, pack))


def verify_independent_review(
    step: Dict[str, Any],
    pack: Optional[Dict[str, Any]] = None,
    base_dirs: Optional[List[Path]] = None,
) -> Tuple[bool, str]:
    """
    Trả (verified, assurance). Không dựa trên bất kỳ trường nào trong step/reviewer do caller
    cung cấp (independent, verification_source, subagent_id, execution_context, transcript...).
    Không có verifier tin cậy -> (False, 'UNVERIFIED_INDEPENDENT_CLAIM').
    """
    kind = (step.get("reviewer") or {}).get("kind")
    if kind in ("separate_agent", "human") and _evidence_intact(step, base_dirs):
        if _trusted_verify(VERIFIER_INDEPENDENT_REVIEW, _verification_claim(step, pack)):
            return True, "INDEPENDENT_VERIFIED"
    return False, UNVERIFIED_INDEPENDENT_CLAIM


def is_verified_independent_review(
    step: Dict[str, Any],
    pack: Optional[Dict[str, Any]] = None,
    base_dirs: Optional[List[Path]] = None,
) -> bool:
    return verify_independent_review(step, pack, base_dirs)[0]


def create_evidence_pack(
    task_id: str,
    runbook: str,
    steps: Optional[List[Dict[str, Any]]] = None,
    human_approval: Optional[Dict[str, Any]] = None,
    out_dir: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Khởi tạo một Evidence Pack có cấu trúc."""
    if not task_id or not isinstance(task_id, str) or not task_id.strip():
        raise EvidenceError("task_id bắt buộc phải là chuỗi không rỗng.")
    if not runbook or not isinstance(runbook, str) or not runbook.strip():
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
            "status": "NOT_REQUESTED",
            "approval_state": "APPROVAL_NOT_REQUESTED",
            "scope": "final_release",
            "approver": None,
            "channel": None,
            "verification_status": "NOT_REQUESTED",
            "timestamp": None,
            "bound_task_id": None,
            "bound_runbook": None,
            "pack_hash_at_approval": None,
            "approval_event_id": None,
            "notes": None,
            "attestation": None,
        },
    }

    if human_approval:
        if human_approval.get("required"):
            pack["human_approval"]["required"] = True
            pack["human_approval"]["status"] = "PENDING"
            pack["human_approval"]["approval_state"] = "APPROVAL_REQUESTED"
            pack["human_approval"]["verification_status"] = "PENDING"
            pack["human_approval"]["bound_task_id"] = task_id.strip()
            pack["human_approval"]["bound_runbook"] = runbook.strip()
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
    trusted_attestation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Thêm một bước thẩm định vào Evidence Pack."""
    if status not in VALID_STATUSES:
        raise EvidenceError(f"Trạng thái '{status}' không hợp lệ (hỗ trợ: {list(VALID_STATUSES)}).")

    art_str = str(artifact)
    art_sha256 = None
    art_path = Path(art_str)
    if art_path.is_file():
        art_sha256 = compute_sha256(art_str)

    norm_rev = normalize_reviewer(reviewer, verification_method, evidence_ref, trusted_attestation)

    # Kiểm tra tính trung thực của tuyên bố
    if status in ("TESTED", "OBSERVED", "INDEPENDENTLY_REVIEWED"):
        if not verification_method or verification_method.strip() in ("", "none", "chưa kiểm tra"):
            raise EvidenceError(f"Bước '{step_id}' tuyên bố trạng thái '{status}' nhưng thiếu verification_method.")
        if not evidence_ref or evidence_ref.strip().lower() in ("", "none", "không có", "null"):
            raise EvidenceError(f"Bước '{step_id}' tuyên bố trạng thái '{status}' nhưng thiếu evidence_ref.")

    # Tính mã băm file bằng chứng nếu là local file tồn tại trên đĩa
    ev_sha256 = None
    ev_clean = evidence_ref.split(":")[0].split("#")[0].strip().removeprefix("file://")
    ev_path = Path(ev_clean)
    if ev_path.is_file():
        ev_sha256 = compute_sha256(ev_path)
    elif art_path.is_file() and (art_path.parent / ev_clean).is_file():
        ev_sha256 = compute_sha256(art_path.parent / ev_clean)

    step_data = {
        "step_id": step_id,
        "role": role,
        "skill_used": skill_used,
        "artifact": art_str,
        "artifact_sha256": art_sha256,
        "verification_method": verification_method,
        "evidence_ref": evidence_ref,
        "evidence_ref_sha256": ev_sha256,
        "status": status,
        "reviewer": norm_rev,
        "remaining_risk": remaining_risk or "Chưa ghi nhận rủi ro tồn đọng",
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    # Cấm phong danh INDEPENDENTLY_REVIEWED khi verifier tin cậy không xác nhận (fail-closed).
    # Mọi trường do caller cung cấp (trusted_attestation, subagent_id...) đều bị bỏ qua.
    if status == "INDEPENDENTLY_REVIEWED":
        verified, assurance = verify_independent_review(step_data, pack)
        if not verified:
            raise EvidenceError(
                f"Bước '{step_id}' tuyên bố INDEPENDENTLY_REVIEWED nhưng người thẩm định không có bằng chứng độc lập "
                f"được verifier tin cậy xác minh ({assurance})."
            )
        norm_rev.update({
            "independent": True,
            "verified_reviewer": norm_rev.get("name"),
            "verification_source": "trusted_verifier",
            "assurance_level": assurance,
        })

    existing_idx = next((i for i, s in enumerate(pack["steps"]) if s["step_id"] == step_id), -1)
    if existing_idx >= 0:
        pack["steps"][existing_idx] = step_data
    else:
        pack["steps"].append(step_data)

    # Fix 1: Invalidate prior human approval if content changed after approval was recorded
    human = pack.get("human_approval", {})
    if human.get("approval_state") in ("APPROVAL_CLAIMED", "APPROVAL_AUTHENTICATED") or human.get("status") in ("APPROVED", "CLAIMED"):
        hash_at_appr = human.get("pack_hash_at_approval")
        current_hash = compute_pack_content_hash(pack)
        if hash_at_appr and hash_at_appr != current_hash:
            human["status"] = "AWAITING_REAPPROVAL"
            human["approval_state"] = "APPROVAL_INVALIDATED"
            human["verification_status"] = "INVALIDATED_BY_CHANGE"
            human["invalidation_reason"] = f"Nội dung task hoặc bước '{step_id}' đã bị sửa đổi sau phê duyệt."

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

    # 4. Phải có ít nhất 1 bước có bằng chứng kiểm chứng thực tế
    has_verifiable = any(s.get("status") in ("TESTED", "OBSERVED", "INDEPENDENTLY_REVIEWED") for s in steps)
    if not has_verifiable:
        pack["overall_status"] = "NEEDS_WORK"
        return "NEEDS_WORK"

    # 5. Fix 1: Nếu yêu cầu phê duyệt con người, chỉ công nhận VERIFIED khi APPROVAL_AUTHENTICATED
    human = pack.get("human_approval", {})
    if human.get("required"):
        is_appr_valid, _ = verify_human_approval(pack)
        if not is_appr_valid or human.get("approval_state") != "APPROVAL_AUTHENTICATED":
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
        "approval_state": "APPROVAL_REQUESTED",
        "scope": scope,
        "details": details,
        "requested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "bound_task_id": pack.get("task_id"),
        "bound_runbook": pack.get("runbook"),
        "pack_hash_at_approval": None,
        "approver": None,
        "channel": None,
        "timestamp": None,
        "notes": None,
        "verification_status": "PENDING",
        "approval_event_id": None,
        "attestation": None,
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
    trusted_attestation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Ghi nhận quyết định phê duyệt con người (Fix 1).
    NGUYÊN TẮC P0: Không được tự tạo trạng thái xác thực (AUTHENTICATED) chỉ dựa trên
    tham số channel, approver hoặc auth_token tự khai báo.
    Nếu thiếu trusted attestation provider, trạng thái dừng ở APPROVAL_CLAIMED (Fail-closed).
    """
    if not approver or not isinstance(approver, str) or not approver.strip():
        raise EvidenceError("approver bắt buộc phải là chuỗi định danh người dùng không rỗng.")

    approver_clean = approver.strip()
    if approver_clean.lower() in KNOWN_AGENT_ROLES:
        raise EvidenceError(f"Agent role '{approver_clean}' không được phép tự phê duyệt phê chuẩn của con người.")

    current_hash = compute_pack_content_hash(pack)
    task_id = pack.get("task_id", "")
    runbook = pack.get("runbook", "")
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Ràng buộc chặt chẽ Approval Event Identity
    event_payload = f"{task_id}:{runbook}:{approver_clean}:{current_hash}:{now_iso}"
    approval_event_id = "appr_evt_" + hashlib.sha256(event_payload.encode("utf-8")).hexdigest()[:16]

    pack["human_approval"]["required"] = True
    pack["human_approval"]["approver"] = approver_clean
    pack["human_approval"]["channel"] = channel
    pack["human_approval"]["timestamp"] = now_iso
    pack["human_approval"]["notes"] = notes.strip()
    pack["human_approval"]["bound_task_id"] = task_id
    pack["human_approval"]["bound_runbook"] = runbook
    pack["human_approval"]["pack_hash_at_approval"] = current_hash
    pack["human_approval"]["approval_event_id"] = approval_event_id

    if not approved:
        pack["human_approval"]["status"] = "REJECTED"
        pack["human_approval"]["approval_state"] = "APPROVAL_REJECTED"
        pack["human_approval"]["verification_status"] = "REJECTED"
    else:
        if channel in ("agent_simulated", "mock"):
            pack["human_approval"]["status"] = "CLAIMED"
            pack["human_approval"]["approval_state"] = "APPROVAL_CLAIMED"
            pack["human_approval"]["verification_status"] = "SIMULATED_NOT_AUTHENTICATED"
            pack["human_approval"]["attestation_note"] = "Phê duyệt mô phỏng bởi agent/mock: không có giá trị xác thực con người."
        else:
            # Channel, approver, auth_token, trusted_attestation do caller truyền đều là CLAIM.
            # Chỉ verifier ngoài ranh giới dữ liệu mới được xác lập AUTHENTICATED (hiện chưa có -> fail-closed).
            is_attested = (
                isinstance(trusted_attestation, dict)
                and trusted_attestation.get("verified") is True
                and trusted_attestation.get("provider") in ("trusted_hardware_token", "aiwf_attestation_authority")
                and bool(trusted_attestation.get("event_signature"))
                and _trusted_verify(VERIFIER_HUMAN_APPROVAL, {
                    "task_id": task_id,
                    "runbook": runbook,
                    "approver": approver_clean,
                    "pack_hash": current_hash,
                    "approval_event_id": approval_event_id,
                    "attestation": trusted_attestation,
                })
            )
            if is_attested:
                pack["human_approval"]["status"] = "APPROVED"
                pack["human_approval"]["approval_state"] = "APPROVAL_AUTHENTICATED"
                pack["human_approval"]["verification_status"] = "AUTHENTICATED"
                pack["human_approval"]["attestation"] = trusted_attestation
            else:
                # Fallback an toàn (Fail closed): Ghi nhận dưới dạng CLAIM để audit trail
                pack["human_approval"]["status"] = "CLAIMED"
                pack["human_approval"]["approval_state"] = "APPROVAL_CLAIMED"
                pack["human_approval"]["verification_status"] = "UNATTESTED_CLAIM"
                pack["human_approval"]["attestation_note"] = (
                    "Phê duyệt được ghi nhận ở mức APPROVAL_CLAIMED để phục vụ audit. "
                    "Chưa có trusted approval provider để chuyển thành APPROVAL_AUTHENTICATED (Fail closed, not fake secure)."
                )

    recompute_overall_status(pack)
    return pack["human_approval"]


def verify_human_approval(pack: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Thẩm định tính hợp lệ, tính toàn vẹn và chống giả mạo của phê duyệt con người.
    """
    human = pack.get("human_approval", {})
    if not human.get("required"):
        return True, []

    state = human.get("approval_state")
    if state == "APPROVAL_NOT_REQUESTED" or not state:
        return False, ["Phê duyệt con người chưa hoàn tất (chưa được kích hoạt)."]

    if state == "APPROVAL_REQUESTED":
        return False, ["Phê duyệt con người chưa hoàn tất (đang ở trạng thái chờ APPROVAL_REQUESTED)."]

    if state == "APPROVAL_REJECTED":
        return False, ["Phê duyệt con người đã bị TỪ CHỐI (APPROVAL_REJECTED)."]

    if state == "APPROVAL_INVALIDATED" or human.get("status") == "AWAITING_REAPPROVAL":
        return False, [f"Phê duyệt con người đã bị HỦY HIỆU LỰC: {human.get('invalidation_reason', 'nội dung thay đổi')}."]

    approver = human.get("approver")
    if not approver or not str(approver).strip():
        return False, ["Thiếu định danh người phê duyệt (approver)."]

    if str(approver).strip().lower() in KNOWN_AGENT_ROLES:
        return False, [f"Vi phạm nghiêm trọng: Agent role '{approver}' không thể tự phê duyệt phê chuẩn con người."]

    if not human.get("approval_event_id"):
        return False, ["Thiếu approval_event_id: Phê duyệt không có sự kiện xác thực."]

    bound_task = human.get("bound_task_id")
    current_task = pack.get("task_id")
    if bound_task and bound_task != current_task:
        return False, [
            f"Phát hiện Replay Attack: Phê duyệt được cấp cho task '{bound_task}', không khớp với task hiện tại '{current_task}'."
        ]

    bound_runbook = human.get("bound_runbook")
    current_runbook = pack.get("runbook")
    if bound_runbook and bound_runbook != current_runbook:
        return False, [
            f"Phát hiện Cross-Runbook Attack: Phê duyệt được cấp cho runbook '{bound_runbook}', không khớp với '{current_runbook}'."
        ]

    hash_at_approval = human.get("pack_hash_at_approval")
    current_hash = compute_pack_content_hash(pack)
    if hash_at_approval and hash_at_approval != current_hash:
        return False, [
            "Nội dung task hoặc artifact đã bị thay đổi sau khi được phê duyệt. Yêu cầu tái phê duyệt (renewed approval required)."
        ]

    if state == "APPROVAL_CLAIMED":
        return False, [
            "Phê duyệt mới dừng ở mức APPROVAL_CLAIMED (chưa có trusted attestation provider)."
        ]

    if state != "APPROVAL_AUTHENTICATED":
        return False, [
            f"Phê duyệt con người chưa được xác thực (trạng thái: {state})."
        ]

    # Trạng thái AUTHENTICATED lưu trong pack/JSON là dữ liệu không tin cậy: luôn xác minh lại.
    if not _trusted_verify(VERIFIER_HUMAN_APPROVAL, {
        "task_id": current_task,
        "runbook": current_runbook,
        "approver": str(approver).strip(),
        "pack_hash": current_hash,
        "approval_event_id": human.get("approval_event_id"),
        "attestation": human.get("attestation"),
    }):
        return False, [
            "Phê duyệt con người khai báo APPROVAL_AUTHENTICATED nhưng không được verifier tin cậy xác minh (fail-closed)."
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

            # Kiểm tra mã băm artifact + file bằng chứng (nếu file tồn tại)
            issues.extend(hash_integrity_issues(s, step_id, resolved_base_dirs))

            # Fix 3: Kiểm tra evidence_ref và evidence_ref_sha256
            ev_ref = s.get("evidence_ref")
            ref_type, ref_valid, ref_msg = classify_and_validate_evidence_ref(ev_ref, resolved_base_dirs, status)
            if not ref_valid:
                issues.append(f"{step_id}: {ref_msg}")
            else:
                # Test 14: Screenshot tồn tại nhưng chưa được đánh giá UX
                if ref_type == "screenshot":
                    has_ux_eval = any(
                        kw in (s.get("verification_method", "") + " " + s.get("remaining_risk", "")).lower()
                        for kw in ("crawler", "playwright", "audit", "sweep", "biên bản đánh giá ux", "ux_assessment", "ux_reviewed")
                    )
                    if not has_ux_eval:
                        issues.append(
                            f"{step_id}: Screenshot tồn tại nhưng chưa được đánh giá UX (thiếu biên bản thẩm định UX)."
                        )

            # Fix 2: Kiểm tra reviewer
            rev = s.get("reviewer", {})
            if rev.get("kind") == "same_context_agent" and rev.get("independent") is True:
                issues.append(f"{step_id}: same_context_agent KHÔNG ĐƯỢC tuyên bố independent=True.")

            if status == "INDEPENDENTLY_REVIEWED":
                verified, assurance = verify_independent_review(s, pack, resolved_base_dirs)
                if not verified:
                    issues.append(
                        f"{step_id}: Trạng thái là INDEPENDENTLY_REVIEWED nhưng reviewer thiếu trusted execution attestation "
                        f"được verifier tin cậy xác minh ({assurance})."
                    )

    # Fix 1: Thẩm định human approval
    human = pack.get("human_approval", {})
    if human.get("approver") and not human.get("approval_event_id"):
        issues.append("human_approval: Khai báo người phê duyệt nhưng không có approval_event_id hợp lệ (Reject).")

    if human.get("required"):
        is_appr_ok, appr_issues = verify_human_approval(pack)
        if not is_appr_ok and human.get("status") in ("APPROVED", "CLAIMED"):
            issues.extend(appr_issues)

    # Kiểm tra mâu thuẫn giữa overall_status và các bước
    overall = pack.get("overall_status")
    if overall == "VERIFIED":
        if any(s.get("status") in ("FAILED", "NOT_VERIFIED", "IMPLEMENTED") for s in steps):
            issues.append("overall_status là VERIFIED nhưng vẫn tồn tại bước FAILED hoặc NOT_VERIFIED.")
        if all(s.get("status") == "SELF_REVIEWED" for s in steps):
            issues.append("overall_status là VERIFIED nhưng toàn bộ các chặng chỉ là SELF_REVIEWED.")
        if human.get("required") and human.get("approval_state") != "APPROVAL_AUTHENTICATED":
            issues.append("overall_status là VERIFIED nhưng human_approval chưa APPROVAL_AUTHENTICATED.")

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
    lines.append(f"- **Trạng thái:** **`{human.get('status', 'PENDING')}`** (`{human.get('approval_state', 'APPROVAL_NOT_REQUESTED')}`)")
    if human.get("approver"):
        lines.append(
            f"- **Người phê duyệt:** `{human.get('approver')}` (Kênh: `{human.get('channel')}`, Xác thực: `{human.get('verification_status')}`) lúc `{human.get('timestamp')}`"
        )
    if human.get("approval_event_id"):
        lines.append(f"- **Event ID:** `{human.get('approval_event_id')}`")
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
