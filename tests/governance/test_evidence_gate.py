#!/usr/bin/env python3
"""
tests/governance/test_evidence_gate.py — Test suite for AIWF Evidence Gate Engine.

Verifies:
1. Creation, schema validation, and serialization of evidence_pack.json.
2. 7 standard evidence statuses (NOT_VERIFIED to INDEPENDENTLY_REVIEWED, FAILED).
3. SHA-256 calculation and tampering detection on physical artifacts.
4. Enforcement that same_context_agent cannot claim independence.
5. Overall status transitions (NOT_VERIFIED, NEEDS_WORK, AWAITING_HUMAN_APPROVAL, VERIFIED, FAILED).
6. Human approval gate workflow.
7. CLI interface (--validate, --summary).
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

from evidence_gate import (
    create_evidence_pack,
    add_step_evidence,
    validate_evidence_pack,
    record_human_approval,
    render_evidence_summary_md,
    write_evidence_pack_file,
    compute_sha256,
    EvidenceError,
)


class TestEvidenceGateEngine:
    def test_create_and_validate_basic_pack(self, tmp_path):
        # Create a dummy artifact file
        artifact = tmp_path / "result.txt"
        artifact.write_text("Sample output text", encoding="utf-8")

        pack = create_evidence_pack(
            task_id="TASK-T01-TEST",
            runbook="build-webapp",
            human_approval={"required": False}
        )
        assert pack["task_id"] == "TASK-T01-TEST"
        assert pack["overall_status"] == "NOT_VERIFIED"

        # Add an observed step
        add_step_evidence(
            pack=pack,
            step_id="step_1_audit",
            role="reality-checker",
            skill_used="app-auditor",
            artifact=artifact,
            verification_method="playwright_crawler",
            evidence_ref="screenshots/desktop.png",
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "Playwright Engine"}
        )

        assert pack["overall_status"] == "VERIFIED"
        pack_file = tmp_path / "evidence_pack.json"
        write_evidence_pack_file(pack, pack_file)

        valid, issues = validate_evidence_pack(pack_file)
        assert valid is True
        assert len(issues) == 0

    def test_tampering_detection(self, tmp_path):
        artifact = tmp_path / "secure_doc.docx"
        artifact.write_text("Original content", encoding="utf-8")

        pack = create_evidence_pack(task_id="TASK-TAMPER", runbook="produce-video")
        add_step_evidence(
            pack=pack,
            step_id="phase_render",
            role="evidence-collector",
            skill_used="video-studio",
            artifact=artifact,
            verification_method="ffprobe_audit",
            evidence_ref="video_log.txt",
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "FFprobe"}
        )

        # Modify artifact content after evidence was recorded
        artifact.write_text("Tampered content", encoding="utf-8")

        valid, issues = validate_evidence_pack(pack)
        assert valid is False
        assert any("Mã băm SHA-256 bị sai lệch" in iss for iss in issues)

    def test_same_context_agent_cannot_claim_independent(self, tmp_path):
        pack = create_evidence_pack(task_id="TASK-SAME-CTX", runbook="marketing-campaign")
        
        # Invalidate directly in dict to test validator catch
        pack["steps"].append({
            "step_id": "step_review",
            "role": "brand-guardian",
            "skill_used": "viet-bai",
            "artifact": "none",
            "artifact_sha256": None,
            "verification_method": "llm_self_review",
            "evidence_ref": "review.md",
            "status": "SELF_REVIEWED",
            "reviewer": {
                "kind": "same_context_agent",
                "name": "Gemini Assistant",
                "independent": True  # Illegal!
            }
        })

        valid, issues = validate_evidence_pack(pack)
        assert valid is False
        assert any("same_context_agent KHÔNG ĐƯỢC tuyên bố independent=True" in iss for iss in issues)

    def test_failed_step_blocks_overall_status(self, tmp_path):
        pack = create_evidence_pack(task_id="TASK-FAIL-BLOCK", runbook="build-webapp")
        
        add_step_evidence(
            pack=pack,
            step_id="step_syntax",
            role="technical-auditor",
            skill_used="app-auditor",
            artifact="main.js",
            verification_method="syntax_linter",
            evidence_ref="lint.log",
            status="FAILED",
            reviewer={"kind": "automated_test", "name": "ESLint"}
        )

        assert pack["overall_status"] == "FAILED"

    def test_human_approval_workflow(self, tmp_path):
        pack = create_evidence_pack(
            task_id="TASK-HITL",
            runbook="marketing-campaign",
            human_approval={"required": True}
        )

        add_step_evidence(
            pack=pack,
            step_id="step_claim_guard",
            role="legal-compliance-reviewer",
            skill_used="viet-bai",
            artifact="post.md",
            verification_method="claim_guard_cli",
            evidence_ref="claim_report.json",
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "ClaimGuard"}
        )

        # Before human approval, status should be AWAITING_HUMAN_APPROVAL
        assert pack["overall_status"] == "AWAITING_HUMAN_APPROVAL"

        # Record human approval
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Product Director",
            notes="Phê duyệt phát hành đa kênh"
        )

        assert pack["overall_status"] == "VERIFIED"
        assert pack["human_approval"]["status"] == "APPROVED"
        assert pack["human_approval"]["approver"] == "Product Director"

    def test_cli_execution(self, tmp_path):
        artifact = tmp_path / "cli_test.txt"
        artifact.write_text("CLI test artifact", encoding="utf-8")

        pack = create_evidence_pack(task_id="TASK-CLI", runbook="research-repository")
        add_step_evidence(
            pack=pack,
            step_id="step_cli",
            role="research-synthesist",
            skill_used="doc-sau",
            artifact=artifact,
            verification_method="doc_ingest_check",
            evidence_ref="manifest.json",
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "DocIngest"}
        )
        pack_file = tmp_path / "cli_pack.json"
        write_evidence_pack_file(pack, pack_file)

        # Test CLI --validate
        cmd_validate = [
            sys.executable,
            str(SHARED_DIR / "governance" / "evidence_gate.py"),
            "--validate",
            str(pack_file),
        ]
        res = subprocess.run(cmd_validate, capture_output=True, text=True)
        assert res.returncode == 0
        assert "Evidence Pack hợp lệ 100%" in res.stdout

        # Test CLI --summary
        cmd_summary = [
            sys.executable,
            str(SHARED_DIR / "governance" / "evidence_gate.py"),
            "--summary",
            str(pack_file),
        ]
        res_summary = subprocess.run(cmd_summary, capture_output=True, text=True)
        assert res_summary.returncode == 0
        assert "HỒ SƠ BẰNG CHỨNG (EVIDENCE PACK): TASK-CLI" in res_summary.stdout
