#!/usr/bin/env python3
"""
tests/governance/test_quality_governance.py — Test suite for Quality Governance & Review Router.

Verifies:
1. Risk tier determination logic across blast radius and domain sensitivity.
2. Required reviewer routing rules per risk tier and domain.
3. Compliance audit of evidence packs against risk tier requirements.
4. Rejection of unapproved Tier 3 packs or packs with missing automated tests in Tier 2/3.
5. CLI execution of review_router.py.
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_DIR = REPO_ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

from review_router import (
    determine_risk_tier,
    get_required_reviewers,
    audit_review_compliance,
    GovernanceError,
)
from evidence_gate import (
    create_evidence_pack,
    add_step_evidence,
    record_human_approval,
)


class TestQualityGovernance:
    def test_determine_risk_tier(self):
        # Tier 1: Small non-critical task
        assert determine_risk_tier("doc_fix", blast_radius=1) == "tier_1_low"

        # Tier 2: Feature or media task
        assert determine_risk_tier("feature", blast_radius=3) == "tier_2_medium"
        assert determine_risk_tier("video_production", blast_radius=2) == "tier_2_medium"

        # Tier 3: Critical domain or high blast radius
        assert determine_risk_tier("tax_update", is_financial_or_legal=True) == "tier_3_high"
        assert determine_risk_tier("cleanup", is_destructive=True) == "tier_3_high"
        assert determine_risk_tier("deploy", is_production_publish=True) == "tier_3_high"
        assert determine_risk_tier("refactor", blast_radius=15) == "tier_3_high"

    def test_get_required_reviewers(self):
        t1 = get_required_reviewers("tier_1_low", "code")
        assert t1["requires_cross_review"] is False
        assert t1["requires_human_gate"] is False

        t2 = get_required_reviewers("tier_2_medium", "webapp")
        assert t2["requires_cross_review"] is True
        assert t2["requires_human_gate"] is False
        assert "ux-reviewer" in t2["suggested_roles"]

        t3 = get_required_reviewers("tier_3_high", "marketing")
        assert t3["requires_cross_review"] is True
        assert t3["requires_human_gate"] is True
        assert "legal-compliance-reviewer" in t3["suggested_roles"]

    def test_audit_tier_compliance(self):
        # Pack with automated test only
        pack = create_evidence_pack("TASK-T2-TEST", "build-webapp")
        add_step_evidence(
            pack=pack,
            step_id="step_test",
            role="evidence-collector",
            skill_used="app-auditor",
            artifact="index.html",
            verification_method="pytest_suite",
            evidence_ref="test_run.log",
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "Pytest Engine"}
        )

        # Tier 1 should pass
        valid_t1, issues_t1 = audit_review_compliance(pack, "tier_1_low")
        assert valid_t1 is True

        # Tier 2 should pass because it has automated_test
        valid_t2, issues_t2 = audit_review_compliance(pack, "tier_2_medium")
        assert valid_t2 is True

        # Tier 3 should FAIL because human_approval is required and pending
        valid_t3, issues_t3 = audit_review_compliance(pack, "tier_3_high")
        assert valid_t3 is False
        assert any("Tier 3 (Rủi ro Cao)" in iss for iss in issues_t3)

        # Now add independent reviewer and approve for Tier 3
        add_step_evidence(
            pack=pack,
            step_id="step_sec_review",
            role="technical-auditor",
            skill_used="app-auditor",
            artifact="audit_report.md",
            verification_method="code_inspection",
            evidence_ref="sec_audit.log",
            status="INDEPENDENTLY_REVIEWED",
            reviewer={"kind": "separate_agent", "name": "Security Subagent"}
        )
        pack["human_approval"]["required"] = True
        record_human_approval(pack, approved=True, approver="Security Chief", notes="Approved")
        valid_t3_approved, issues_t3_approved = audit_review_compliance(pack, "tier_3_high")
        assert valid_t3_approved is True

    def test_cli_execution(self, tmp_path):
        pack = create_evidence_pack("TASK-CLI-GOV", "marketing-campaign")
        add_step_evidence(
            pack=pack,
            step_id="step_claim",
            role="legal-compliance-reviewer",
            skill_used="viet-bai",
            artifact="post.md",
            verification_method="claim_guard",
            evidence_ref="report.json",
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "ClaimGuard"}
        )
        pack_file = tmp_path / "gov_pack.json"
        pack_file.write_text(json.dumps(pack), encoding="utf-8")

        cmd = [
            sys.executable,
            str(SHARED_DIR / "governance" / "review_router.py"),
            "--check-pack",
            str(pack_file),
            "--tier",
            "tier_2_medium",
            "--domain",
            "marketing",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0
        assert "Evidence Pack đạt chuẩn quản trị chất lượng" in res.stdout
