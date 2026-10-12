#!/usr/bin/env python3
"""
tests/governance/test_runbook_e2e_pilot.py — End-to-end pilot integration test.

Simulates a full runbook execution lifecycle (research-repository):
Phase 1 (Scoping) -> Gate 1 (Approval) -> Phase 2 (Ingestion) -> Phase 3 (Deep Reading)
-> Phase 4 (Reality Check) -> Gate 2 (Report Acceptance) -> Phase 5 (Publishing)
-> Gate 3 (Final Signoff) -> Evidence Pack verification & Compliance Audit.
"""

import json
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
)
from review_router import (
    determine_risk_tier,
    audit_review_compliance,
)


class TestRunbookE2EPilot:
    def test_full_research_runbook_lifecycle(self, tmp_path):
        out_dir = tmp_path / "AIWF_Output" / "research_pilot"
        out_dir.mkdir(parents=True)

        # 0. Initialize Evidence Pack for research-repository runbook
        task_id = "TASK-PILOT-RR-01"
        pack = create_evidence_pack(
            task_id=task_id,
            runbook="research-repository",
            human_approval={"required": True}
        )
        assert pack["overall_status"] == "NOT_VERIFIED"

        # Phase 1: Research Scoping -> verified
        scoping_doc = out_dir / "search_strategy.md"
        scoping_doc.write_text("# Search Strategy\n- Query: AI Workforce\n- Sources: SSOT", encoding="utf-8")
        add_step_evidence(
            pack=pack,
            step_id="phase_1_scoping",
            role="research-synthesist",
            skill_used="doc-sau",
            artifact=scoping_doc,
            verification_method="scope_definition",
            evidence_ref=str(scoping_doc),
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "ScopeValidator"}
        )

        # Phase 2: Ingestion & Extraction
        source_doc = out_dir / "source.md"
        source_doc.write_text("# Ingested Source\nRaw extracted data blocks.", encoding="utf-8")
        add_step_evidence(
            pack=pack,
            step_id="phase_2_ingest",
            role="research-synthesist",
            skill_used="doc-sau",
            artifact=source_doc,
            verification_method="doc_ingest_bridge",
            evidence_ref="manifest.json",
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "doc_ingest_bridge"}
        )

        # Phase 3: Multi-Model Deep Reading -> audited in phase 4
        report_doc = out_dir / "draft_deep_reading.md"
        report_doc.write_text("# Deep Reading Analysis\n- SCQA: Situation, Complication, Question, Answer.", encoding="utf-8")
        add_step_evidence(
            pack=pack,
            step_id="phase_3_analysis",
            role="research-synthesist",
            skill_used="doc-sau",
            artifact=report_doc,
            verification_method="mental_models_scqa",
            evidence_ref=str(report_doc),
            status="SELF_REVIEWED",
            reviewer={"kind": "same_context_agent", "name": "DocSau Assistant"}
        )

        # Phase 4: Evidence Audit & Reality Check
        audit_notes = out_dir / "audit_notes.md"
        audit_notes.write_text("# Reality Check Audit\n- 0 hallucinations found. Citations verified against source.md.", encoding="utf-8")
        add_step_evidence(
            pack=pack,
            step_id="phase_4_reality_check",
            role="reality-checker",
            skill_used="doc-sau",
            artifact=audit_notes,
            verification_method="zero_hallucination_cross_check",
            evidence_ref="source.md:L1-L15",
            status="OBSERVED",
            reviewer={"kind": "separate_agent", "name": "Reality Checker Subagent"}
        )

        # Phase 5: Publishing
        final_docx = out_dir / "bao_cao_nghien_cuu.docx"
        final_docx.write_text("Binary DOCX content placeholder for mock output", encoding="utf-8")
        add_step_evidence(
            pack=pack,
            step_id="phase_5_publishing",
            role="project-shepherd",
            skill_used="doc-sau",
            artifact=final_docx,
            verification_method="legal_report_generator",
            evidence_ref=str(final_docx),
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "Docx Inspect Engine"}
        )

        # Before Gate 3, status is awaiting approval
        assert pack["overall_status"] == "AWAITING_HUMAN_APPROVAL"

        # Gate 3: Final Acceptance Gate (User signoff)
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Research Director (User)",
            notes="Nghiệm thu đạt chuẩn 100%, đầy đủ trích dẫn."
        )

        # Now overall_status must be VERIFIED!
        assert pack["overall_status"] == "VERIFIED"

        # Write out evidence pack
        pack_file = out_dir / "evidence_pack.json"
        write_evidence_pack_file(pack, pack_file)

        # Verify pack integrity
        is_valid, issues = validate_evidence_pack(pack_file)
        assert is_valid is True, f"Evidence pack issues: {issues}"

        # Verify quality governance compliance for Tier 3
        tier = determine_risk_tier("deep_research", blast_radius=1, is_financial_or_legal=True)
        assert tier == "tier_3_high"

        gov_valid, gov_issues = audit_review_compliance(pack, tier, "research")
        assert gov_valid is True, f"Governance compliance issues: {gov_issues}"

        # Verify markdown summary output
        summary_md = render_evidence_summary_md(pack)
        assert "TASK-PILOT-RR-01" in summary_md
        assert "research-repository" in summary_md
        assert "Research Director (User)" in summary_md
        assert "APPROVED" in summary_md
