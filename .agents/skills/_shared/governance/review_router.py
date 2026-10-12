#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_router.py — AIWF Cross-Review & Quality Governance Engine (Luật R7).

Cung cấp cơ chế định tuyến phản biện chéo phân tầng theo rủi ro (Risk-Tiered Quality Governance),
đảm bảo:
1. Không lãng phí token/thời gian đưa các tác vụ nhỏ qua toàn bộ hội đồng chuyên gia.
2. Các tác vụ có rủi ro cao (pháp lý, tài chính, kiến trúc, xuất bản) bắt buộc phải qua
   kiểm định chéo đa vai trò và chốt phê duyệt của con người (Gate 3).
3. Minh bạch tuyệt đối về bản chất người thẩm định:
   - human: Con người thực tế.
   - separate_agent: Subagent/agent phiên riêng biệt.
   - automated_test: Bộ công cụ kiểm thử tự động (exit code, Playwright, claim_guard).
   - same_context_agent: Cùng model trong cùng phiên (KHÔNG ĐỘC LẬP, kẹp trần <= 3.0/5).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from evidence_gate import (
        verify_human_approval,
        is_verified_automated_test,
        verify_independent_review,
        hash_integrity_issues,
        _step_base_dirs,
    )
except ImportError:
    from .evidence_gate import (
        verify_human_approval,
        is_verified_automated_test,
        verify_independent_review,
        hash_integrity_issues,
        _step_base_dirs,
    )

RISK_TIERS = {
    "tier_1_low": {
        "label": "Rủi ro Thấp",
        "description": "Sửa chính tả, cập nhật doc, thay đổi vi mô < 10 dòng không ảnh hưởng logic",
        "requires_cross_review": False,
        "requires_human_gate": False,
        "allowed_evaluators": ["automated_test", "same_context_agent"],
    },
    "tier_2_medium": {
        "label": "Rủi ro Trung bình",
        "description": "Thêm tính năng mới, viết bài tiếp thị, dựng video, sửa đổi logic cục bộ",
        "requires_cross_review": True,
        "requires_human_gate": False,
        "allowed_evaluators": ["automated_test", "same_context_agent", "separate_agent"],
    },
    "tier_3_high": {
        "label": "Rủi ro Cao",
        "description": "Kiến trúc hệ thống, pháp lý, thuế/tài chính, phát hành production, thao tác ghi đè lớn",
        "requires_cross_review": True,
        "requires_human_gate": True,
        "allowed_evaluators": ["automated_test", "same_context_agent", "separate_agent", "human"],
    },
}

DOMAIN_REVIEW_MAPPING = {
    "code": ["technical-auditor", "reality-checker"],
    "webapp": ["ux-reviewer", "reality-checker"],
    "marketing": ["brand-guardian", "legal-compliance-reviewer"],
    "legal_finance": ["legal-compliance-reviewer", "reality-checker"],
    "research": ["research-synthesist", "reality-checker"],
    "general": ["reality-checker"],
}


class GovernanceError(ValueError):
    """Lỗi quản trị chất lượng không hợp lệ."""


def determine_risk_tier(
    task_type: str = "general",
    blast_radius: int = 1,
    is_financial_or_legal: bool = False,
    is_destructive: bool = False,
    is_production_publish: bool = False,
) -> str:
    """
    Xác định cấp độ rủi ro khách quan của tác vụ.
    """
    if is_financial_or_legal or is_destructive or is_production_publish or blast_radius >= 10:
        return "tier_3_high"
    if blast_radius >= 3 or task_type in ("feature", "video_production", "marketing_campaign", "deep_research"):
        return "tier_2_medium"
    return "tier_1_low"


def get_required_reviewers(risk_tier: str, domain: str = "general") -> Dict[str, Any]:
    """
    Tra cứu yêu cầu phản biện chéo tương ứng với cấp rủi ro và lĩnh vực.
    """
    if risk_tier not in RISK_TIERS:
        raise GovernanceError(f"Cấp rủi ro '{risk_tier}' không hợp lệ (hỗ trợ: {list(RISK_TIERS)}).")

    tier_info = RISK_TIERS[risk_tier]
    target_domain = domain if domain in DOMAIN_REVIEW_MAPPING else "general"
    suggested_roles = DOMAIN_REVIEW_MAPPING[target_domain]

    return {
        "risk_tier": risk_tier,
        "label": tier_info["label"],
        "requires_cross_review": tier_info["requires_cross_review"],
        "requires_human_gate": tier_info["requires_human_gate"],
        "suggested_roles": suggested_roles if tier_info["requires_cross_review"] else [],
        "allowed_evaluators": tier_info["allowed_evaluators"],
    }


def audit_review_compliance(
    pack: Dict[str, Any],
    risk_tier: str,
    domain: str = "general",
    base_dir: Optional[Path] = None,
) -> Tuple[bool, List[str]]:
    """
    Kiểm toán tính hợp chuẩn quản trị của Evidence Pack đối với cấp rủi ro tương ứng.

    TRUST BOUNDARY: các trường reviewer.independent / verification_source / assurance_level
    / approval_state lưu trong pack là CLAIM do caller cung cấp và bị bỏ qua. Tier 2/3 chỉ được
    tính automated test / thẩm định độc lập khi verifier tin cậy (ngoài ranh giới dữ liệu)
    xác nhận tại thời điểm này. Hiện chưa có verifier -> Tier 2/3 fail-closed; Tier 1 không đổi.
    """
    issues = []
    if risk_tier not in RISK_TIERS:
        return False, [f"Cấp rủi ro '{risk_tier}' không hợp lệ."]

    tier_info = RISK_TIERS[risk_tier]
    steps = pack.get("steps", [])
    extra_dirs = [Path(base_dir)] if base_dir else []

    # Mọi tier: bằng chứng/artifact bị sửa sau khi ghi nhận -> vô hiệu
    for s in steps:
        issues.extend(hash_integrity_issues(s, s.get("step_id", "unknown"), _step_base_dirs(s, extra_dirs)))

    # Tier 2 & Tier 3: Bắt buộc có kiểm thử tự động ĐÃ ĐƯỢC XÁC MINH thực thi (khai báo kind=automated_test không đủ)
    if tier_info["requires_cross_review"]:
        has_auto = any(is_verified_automated_test(s, pack, extra_dirs) for s in steps)
        if not has_auto:
            issues.append(
                f"{tier_info['label']}: Bắt buộc phải có ít nhất 1 bước kiểm thử tự động có bằng chứng thực thi được "
                "runner tin cậy xác minh (automated_test khai báo chưa được xác minh: UNVERIFIED)."
            )

    # Tier 3: Bắt buộc phải có phê duyệt của con người và ít nhất 1 thẩm định độc lập
    if tier_info["requires_human_gate"]:
        human = pack.get("human_approval", {})
        if not human.get("required"):
            issues.append("Tier 3 (Rủi ro Cao): Bắt buộc phải khai báo human_approval.required = True.")

        is_appr_valid, appr_issues = verify_human_approval(pack)
        if not is_appr_valid:
            issues.extend([f"Tier 3 (Rủi ro Cao): {iss}" for iss in appr_issues])

        # Kiểm tra tính xác thực của danh tính người dùng (Fail-closed cho Tier 3)
        ver_status = human.get("verification_status")
        channel = human.get("channel")
        state = human.get("approval_state")
        if ver_status == "SIMULATED_NOT_AUTHENTICATED" or channel in ("agent_simulated", "mock"):
            issues.append(
                "Tier 3 (Rủi ro Cao): Phê duyệt con người đang ở trạng thái mô phỏng (agent_simulated / unauthenticated). "
                "Không thể cấp phép phát hành Tier 3 mà không có xác thực người dùng thật (Fail-closed)."
            )
        elif is_appr_valid and (state != "APPROVAL_AUTHENTICATED" or ver_status != "AUTHENTICATED"):
            issues.append(
                f"Tier 3 (Rủi ro Cao): Phê duyệt con người chưa được xác thực (approval_state: {state}). "
                "Không thể cấp phép phát hành Tier 3 mà không có xác thực người dùng thật (Fail-closed)."
            )

        has_independent_reviewer = any(
            verify_independent_review(s, pack, extra_dirs)[0] for s in steps
        )
        if not has_independent_reviewer:
            issues.append(
                "Tier 3 (Rủi ro Cao): Bắt buộc phải có ít nhất 1 bước thẩm định độc lập có chứng thực thực thi tin cậy "
                "(separate_agent hoặc human) được verifier tin cậy xác minh [UNVERIFIED_INDEPENDENT_CLAIM]."
            )

    # Kiểm tra tính trung thực của reviewer
    for s in steps:
        step_id = s.get("step_id", "unknown")
        rev = s.get("reviewer", {})
        kind = rev.get("kind")

        if kind not in tier_info["allowed_evaluators"]:
            issues.append(f"Bước '{step_id}': reviewer.kind '{kind}' không được phép cho {tier_info['label']}.")

        if kind == "same_context_agent" and rev.get("independent") is True:
            issues.append(f"Bước '{step_id}': same_context_agent vi phạm nghiêm trọng khi tự xưng là độc lập.")

        if s.get("status") == "INDEPENDENTLY_REVIEWED" and not verify_independent_review(s, pack, extra_dirs)[0]:
            issues.append(
                f"Bước '{step_id}': Tuyên bố INDEPENDENTLY_REVIEWED nhưng reviewer '{rev.get('name')}' "
                f"không được verifier tin cậy xác minh (UNVERIFIED_INDEPENDENT_CLAIM)."
            )

    return len(issues) == 0, issues


def main():
    parser = argparse.ArgumentParser(description="AIWF Quality Governance & Review Router CLI")
    parser.add_argument("--check-pack", help="Đường dẫn file evidence_pack.json")
    parser.add_argument(
        "--verify-by-execution", action="store_true",
        help="Opt-in: bật verifier chạy lệnh cục bộ (trusted_runner) - CHỈ xác minh automated_test, "
             "không xác minh human/independent review.",
    )
    parser.add_argument("--tier", choices=list(RISK_TIERS.keys()), default="tier_2_medium", help="Cấp rủi ro")
    parser.add_argument("--domain", choices=list(DOMAIN_REVIEW_MAPPING.keys()), default="general", help="Lĩnh vực")
    args = parser.parse_args()

    if args.check_pack:
        if args.verify_by_execution:
            try:
                import trusted_runner
            except ImportError:
                from . import trusted_runner  # type: ignore
            trusted_runner.install_local_runner_verifier()
        p = Path(args.check_pack)
        if not p.is_file():
            print(f"❌ File không tồn tại: {p}", file=sys.stderr)
            sys.exit(1)
        with open(p, "r", encoding="utf-8") as f:
            pack = json.load(f)

        valid, issues = audit_review_compliance(pack, args.tier, args.domain, base_dir=p.parent)
        if valid:
            print(f"✅ Evidence Pack đạt chuẩn quản trị chất lượng cho cấp {args.tier} ({args.domain}).")
            sys.exit(0)
        else:
            print(f"❌ Phát hiện {len(issues)} vi phạm quản trị chất lượng:")
            for iss in issues:
                print(f"  - {iss}")
            sys.exit(1)

    parser.print_help()


if __name__ == "__main__":
    main()
