#!/usr/bin/env python3
"""
tests/governance/test_governance_security_negative.py — Security & Negative Test Matrix.

Implements all 11 security and negative test scenarios required by Task D:
1. All steps SELF_REVIEWED -> Must not automatically become VERIFIED
2. Missing local evidence file -> Reject or downgrade
3. Modified artifact after hashing -> Reject
4. Invalid evidence reference -> Reject or mark NOT_VERIFIED
5. Forged independent reviewer metadata -> Must not establish independence
6. Agent-generated human approval -> Must not authorize Tier 3 release
7. Approval reused for another task -> Reject
8. Artifact modified after approval -> Require renewed approval
9. FAILED step combined with approved step -> Overall FAILED
10. Missing mandatory approval -> Release blocked
11. Legitimate existing evidence pack -> Remains compatible where safe
"""

import copy
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
    verify_human_approval,
    write_evidence_pack_file,
    classify_and_validate_evidence_ref,
    normalize_reviewer,
    compute_sha256,
    EvidenceError,
)
from review_router import (
    audit_review_compliance,
)


class TestGovernanceSecurityNegative:
    """Bộ kiểm thử bảo mật & ca kiểm thử âm tính cho Evidence Gate và Review Router."""

    # 1. All steps SELF_REVIEWED: Must not automatically become VERIFIED
    def test_all_steps_self_reviewed_must_not_become_verified(self, tmp_path):
        pack = create_evidence_pack("TASK-NEG-01", "research-repository")
        report = tmp_path / "self_report.md"
        report.write_text("# Draft Report", encoding="utf-8")

        add_step_evidence(
            pack=pack,
            step_id="step_draft",
            role="research-synthesist",
            skill_used="doc-sau",
            artifact=report,
            verification_method="scqa_reflection",
            evidence_ref=str(report),
            status="SELF_REVIEWED",
            reviewer={"kind": "same_context_agent", "name": "Gemini Model"}
        )

        # Trạng thái tổng thể PHẢI là SELF_REVIEWED, tuyệt đối KHÔNG ĐƯỢC là VERIFIED
        assert pack["overall_status"] == "SELF_REVIEWED"

        # Nếu ai đó cố tình sửa JSON thành VERIFIED
        pack_tampered = copy.deepcopy(pack)
        pack_tampered["overall_status"] = "VERIFIED"
        valid, issues = validate_evidence_pack(pack_tampered)
        assert valid is False
        assert any("toàn bộ các chặng chỉ là SELF_REVIEWED" in iss for iss in issues)

    # 2. Missing local evidence file: Reject or downgrade
    def test_missing_local_evidence_file_rejected(self, tmp_path):
        pack = create_evidence_pack("TASK-NEG-02", "build-webapp")
        artifact = tmp_path / "app.js"
        artifact.write_text("console.log('test')", encoding="utf-8")

        add_step_evidence(
            pack=pack,
            step_id="step_audit",
            role="technical-auditor",
            skill_used="app-auditor",
            artifact=artifact,
            verification_method="jest_suite",
            evidence_ref="non_existent_test_log.log",  # Tệp không tồn tại
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "Jest"}
        )

        pack_file = tmp_path / "neg02_pack.json"
        write_evidence_pack_file(pack, pack_file)

        valid, issues = validate_evidence_pack(pack_file)
        assert valid is False
        assert any("Tệp bằng chứng cục bộ không tồn tại" in iss for iss in issues)

    # 3. Modified artifact after hashing: Reject
    def test_modified_artifact_after_hashing_rejected(self, tmp_path):
        doc = tmp_path / "contract.docx"
        doc.write_text("Điều khoản gốc", encoding="utf-8")

        pack = create_evidence_pack("TASK-NEG-03", "tu-van-phap-luat")
        add_step_evidence(
            pack=pack,
            step_id="step_contract",
            role="legal-compliance-reviewer",
            skill_used="tu-van-phap-luat",
            artifact=doc,
            verification_method="legal_audit",
            evidence_ref=str(doc),
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "DocAnalyzer"}
        )

        # Chỉnh sửa nội dung artifact sau khi mã băm đã được ghi nhận
        doc.write_text("Điều khoản đã bị sửa đổi trái phép", encoding="utf-8")

        valid, issues = validate_evidence_pack(pack)
        assert valid is False
        assert any("Mã băm SHA-256 bị sai lệch" in iss for iss in issues)

    # 4. Invalid evidence reference: Reject or mark NOT_VERIFIED
    def test_invalid_evidence_reference_rejected(self, tmp_path):
        pack = create_evidence_pack("TASK-NEG-04", "video-studio")

        # Gửi evidence_ref rỗng hoặc 'none' phải bị từ chối ngay lập tức
        with pytest.raises(EvidenceError, match="thiếu evidence_ref"):
            add_step_evidence(
                pack=pack,
                step_id="step_render",
                role="evidence-collector",
                skill_used="video-studio",
                artifact="video.mp4",
                verification_method="ffprobe",
                evidence_ref="none",
                status="TESTED",
            )

        ref_type, is_valid, msg = classify_and_validate_evidence_ref("", None)
        assert is_valid is False
        assert ref_type == "empty_or_invalid"

    # 5. Forged independent reviewer metadata: Must not establish independence
    def test_forged_independent_reviewer_metadata_rejected(self, tmp_path):
        pack = create_evidence_pack("TASK-NEG-05", "build-webapp")

        # Cố gắng khai báo separate_agent nhưng không có subagent context
        with pytest.raises(EvidenceError, match="người thẩm định không có bằng chứng độc lập"):
            add_step_evidence(
                pack=pack,
                step_id="step_spoofed",
                role="technical-auditor",
                skill_used="app-auditor",
                artifact="main.ts",
                verification_method="manual_inspection",
                evidence_ref="notes.txt",
                status="INDEPENDENTLY_REVIEWED",
                reviewer={
                    "kind": "separate_agent",
                    "name": "Impostor Auditor",
                    # Thiếu subagent_id và execution_context
                }
            )

        norm = normalize_reviewer({"kind": "separate_agent", "name": "Fake Auditor"})
        assert norm["independent"] is False
        assert norm["verification_source"] == "unverified_claim"

    # 6. Agent-generated human approval: Must not authorize Tier 3 release
    def test_agent_generated_human_approval_cannot_authorize_tier_3(self, tmp_path):
        pack = create_evidence_pack("TASK-NEG-06", "tu-van-phap-luat")

        # A. Agent role tự phê duyệt -> Bị chặn ngay từ tầng record_human_approval
        with pytest.raises(EvidenceError, match="không được phép tự phê duyệt"):
            record_human_approval(
                pack=pack,
                approved=True,
                approver="project-shepherd",
                channel="interactive_user_confirmation"
            )

        # B. Phê duyệt qua kênh mô phỏng (agent_simulated) -> Bị chặn khi kiểm toán Tier 3
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Simulated Agent Persona",
            channel="agent_simulated"
        )
        pack["human_approval"]["required"] = True

        valid_t3, issues_t3 = audit_review_compliance(pack, "tier_3_high", "legal_finance")
        assert valid_t3 is False
        assert any("mô phỏng" in iss for iss in issues_t3)

    # 7. Approval reused for another task: Reject
    def test_approval_reused_for_another_task_rejected(self, tmp_path):
        pack_a = create_evidence_pack("TASK-ORIGINAL", "build-webapp")
        record_human_approval(
            pack=pack_a,
            approved=True,
            approver="Product Owner (User)",
            channel="interactive_user_confirmation"
        )

        # Tạo Task B và dán trộm approval từ Task A
        pack_b = create_evidence_pack("TASK-STOLEN", "build-webapp")
        pack_b["human_approval"] = copy.deepcopy(pack_a["human_approval"])
        pack_b["human_approval"]["required"] = True

        is_valid, issues = verify_human_approval(pack_b)
        assert is_valid is False
        assert any("Replay Attack" in iss for iss in issues)

    # 8. Artifact modified after approval: Require renewed approval
    def test_artifact_modified_after_approval_requires_renewal(self, tmp_path, sim_verifiers):
        sim_verifiers.human_signatures.add("sig_lead_tok_001")
        doc = tmp_path / "final_report.docx"
        doc.write_text("Bản nháp 1", encoding="utf-8")

        pack = create_evidence_pack("TASK-NEG-08", "marketing-campaign")
        add_step_evidence(
            pack=pack,
            step_id="step_copy",
            role="brand-guardian",
            skill_used="viet-bai",
            artifact=doc,
            verification_method="claim_guard",
            evidence_ref=str(doc),
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "ClaimGuard"}
        )

        # Phê duyệt Task có xác thực
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Marketing Lead (User)",
            channel="interactive_user_confirmation",
            trusted_attestation={
                "verified": True,
                "provider": "trusted_hardware_token",
                "event_signature": "sig_lead_tok_001",
            },
        )
        assert pack["overall_status"] == "VERIFIED"

        # Thêm bước mới hoặc sửa đổi nội dung sau khi đã phê duyệt
        doc_v2 = tmp_path / "final_report_v2.docx"
        doc_v2.write_text("Bản nháp 2 - thay đổi sau duyệt", encoding="utf-8")
        add_step_evidence(
            pack=pack,
            step_id="step_copy_updated",
            role="brand-guardian",
            skill_used="viet-bai",
            artifact=doc_v2,
            verification_method="claim_guard",
            evidence_ref=str(doc_v2),
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "ClaimGuard"}
        )

        # Phê duyệt cũ phải bị tự động hủy hiệu lực và chuyển sang AWAITING_HUMAN_APPROVAL
        assert pack["human_approval"]["status"] == "AWAITING_REAPPROVAL"
        assert pack["human_approval"]["verification_status"] == "INVALIDATED_BY_CHANGE"
        assert pack["overall_status"] == "AWAITING_HUMAN_APPROVAL"

    # 9. FAILED step combined with approved step: Overall FAILED
    def test_failed_step_combined_with_approved_step_results_in_failed(self, tmp_path):
        pack = create_evidence_pack("TASK-NEG-09", "build-webapp")

        add_step_evidence(
            pack=pack,
            step_id="step_failing_test",
            role="technical-auditor",
            skill_used="app-auditor",
            artifact="index.html",
            verification_method="unit_tests",
            evidence_ref="unit_test.log",
            status="FAILED",
            reviewer={"kind": "automated_test", "name": "Pytest Engine"}
        )

        add_step_evidence(
            pack=pack,
            step_id="step_passing_style",
            role="ux-reviewer",
            skill_used="thiet-ke",
            artifact="index.css",
            verification_method="linter",
            evidence_ref="style.log",
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "StyleLint"}
        )

        # Dù người dùng cố ghi nhận approval, trạng thái tổng thể VẪN PHẢI LÀ FAILED
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Careless Reviewer",
            channel="interactive_user_confirmation"
        )

        assert pack["overall_status"] == "FAILED"

    # 10. Missing mandatory approval: Release blocked
    def test_missing_mandatory_approval_blocks_release(self, tmp_path):
        pack = create_evidence_pack("TASK-NEG-10", "produce-video", human_approval={"required": True})
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"MOCK_MP4_BYTES")

        add_step_evidence(
            pack=pack,
            step_id="step_qa",
            role="evidence-collector",
            skill_used="video-studio",
            artifact=video_file,
            verification_method="ffprobe_qa",
            evidence_ref=str(video_file),
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "FFprobe"}
        )

        assert pack["overall_status"] == "AWAITING_HUMAN_APPROVAL"

        # Kiểm toán Tier 3 release phải bị chặn hoàn toàn
        is_compliant, issues = audit_review_compliance(pack, "tier_3_high", "marketing")
        assert is_compliant is False
        assert any("Chưa có phê duyệt" in iss or "chưa hoàn tất" in iss for iss in issues)

    # 11. Legitimate existing evidence pack: Remains compatible where safe
    def test_legitimate_existing_evidence_pack_compatible(self, tmp_path, sim_verifiers):
        pack = create_evidence_pack("TASK-LEGIT-11", "build-webapp")
        app_file = tmp_path / "app.html"
        app_file.write_text("<!DOCTYPE html><html><body>AIWF</body></html>", encoding="utf-8")
        test_log = tmp_path / "test_exec.log"
        test_log.write_text("Playwright sweep: 0 console errors, 0 visual flaws", encoding="utf-8")

        add_step_evidence(
            pack=pack,
            step_id="step_legit_audit",
            role="reality-checker",
            skill_used="app-auditor",
            artifact=app_file,
            verification_method="playwright_crawler",
            evidence_ref=str(test_log),
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "Playwright QA"}
        )

        assert pack["overall_status"] == "VERIFIED"

        pack_file = tmp_path / "legit_pack.json"
        write_evidence_pack_file(pack, pack_file)

        is_valid, issues = validate_evidence_pack(pack_file)
        assert is_valid is True, f"Validation issues: {issues}"

        # Tier 1: không bị chặn
        ok_t1, t1_issues = audit_review_compliance(pack, "tier_1_low", "webapp")
        assert ok_t1 is True, f"Tier 1 compliance issues: {t1_issues}"

        # Tier 2 không có runner tin cậy: automated_test khai báo chưa được xác minh -> fail-closed
        is_compliant, gov_issues = audit_review_compliance(pack, "tier_2_medium", "webapp")
        assert is_compliant is False
        assert any("UNVERIFIED" in iss for iss in gov_issues)

        # SIMULATED runner xác nhận đã thực sự chạy log này -> Tier 2 đạt
        sim_verifiers.executed_sha256.add(compute_sha256(test_log))
        is_compliant, gov_issues = audit_review_compliance(pack, "tier_2_medium", "webapp")
        assert is_compliant is True, f"Tier 2 compliance issues: {gov_issues}"

    # === 16 MANDATORY ADVERSARIAL TESTS (DIRECTIVE SECTION 5) ===

    # Test 1: Caller tự khai báo interactive_user_confirmation -> Không được authenticated
    def test_caller_declared_interactive_user_confirmation_not_authenticated(self, tmp_path):
        pack = create_evidence_pack("TASK-ADV-01", "build-webapp")
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Tran Hai Bang",
            channel="interactive_user_confirmation"
        )
        assert pack["human_approval"]["approval_state"] == "APPROVAL_CLAIMED"
        assert pack["human_approval"]["approval_state"] != "APPROVAL_AUTHENTICATED"
        assert pack["human_approval"]["verification_status"] == "UNATTESTED_CLAIM"
        is_valid, issues = verify_human_approval(pack)
        assert is_valid is False
        assert any("APPROVAL_CLAIMED" in iss for iss in issues)

    # Test 2: Caller truyền tên người dùng thật nhưng không có approval event -> Reject
    def test_caller_passed_real_username_without_approval_event_rejected(self, tmp_path):
        pack = create_evidence_pack("TASK-ADV-02", "build-webapp")
        pack["human_approval"] = {
            "required": True,
            "status": "APPROVED",
            "approval_state": "APPROVAL_CLAIMED",
            "approver": "Tran Hai Bang",
            "approval_event_id": None,  # Không có approval event identity
        }
        valid, issues = validate_evidence_pack(pack)
        assert valid is False
        assert any("approval_event_id" in iss for iss in issues)

    # Test 3: Caller tự khai báo auth_token -> Không đủ để approve
    def test_caller_declared_auth_token_insufficient(self, tmp_path):
        pack = create_evidence_pack("TASK-ADV-03", "tu-van-thue")
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Chief Accountant",
            auth_token="bearer secret_token_value_xyz"
        )
        assert pack["human_approval"]["approval_state"] == "APPROVAL_CLAIMED"
        assert pack["human_approval"]["approval_state"] != "APPROVAL_AUTHENTICATED"
        assert pack["human_approval"]["status"] == "CLAIMED"
        is_valid, _ = verify_human_approval(pack)
        assert is_valid is False

    # Test 4: Approval từ task A dùng cho task B -> Reject
    def test_approval_reused_from_task_a_to_task_b_rejected(self, tmp_path):
        pack_a = create_evidence_pack("TASK-ALPHA", "build-webapp")
        record_human_approval(
            pack=pack_a,
            approved=True,
            approver="Product Director",
            trusted_attestation={"verified": True, "provider": "trusted_hardware_token", "event_signature": "sig_a"}
        )
        pack_b = create_evidence_pack("TASK-BETA", "build-webapp")
        pack_b["human_approval"] = copy.deepcopy(pack_a["human_approval"])
        is_valid, issues = verify_human_approval(pack_b)
        assert is_valid is False
        assert any("Replay Attack" in iss for iss in issues)

    # Test 5: Artifact thay đổi sau approval -> Invalidate
    def test_artifact_changed_after_approval_invalidated(self, tmp_path, sim_verifiers):
        sim_verifiers.human_signatures.add("sig_lead")
        doc = tmp_path / "spec.docx"
        doc.write_text("v1 content", encoding="utf-8")
        pack = create_evidence_pack("TASK-ADV-05", "build-webapp")
        add_step_evidence(
            pack=pack,
            step_id="step_spec",
            role="technical-auditor",
            skill_used="app-auditor",
            artifact=doc,
            verification_method="manual_audit",
            evidence_ref=str(doc),
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "DocAnalyzer"}
        )
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Engineering Lead",
            trusted_attestation={"verified": True, "provider": "trusted_hardware_token", "event_signature": "sig_lead"}
        )
        assert pack["human_approval"]["approval_state"] == "APPROVAL_AUTHENTICATED"

        # Update step with v2
        doc_v2 = tmp_path / "spec_v2.docx"
        doc_v2.write_text("v2 modified", encoding="utf-8")
        add_step_evidence(
            pack=pack,
            step_id="step_spec_v2",
            role="technical-auditor",
            skill_used="app-auditor",
            artifact=doc_v2,
            verification_method="manual_audit",
            evidence_ref=str(doc_v2),
            status="OBSERVED",
            reviewer={"kind": "automated_test", "name": "DocAnalyzer"}
        )
        assert pack["human_approval"]["approval_state"] == "APPROVAL_INVALIDATED"
        assert pack["human_approval"]["status"] == "AWAITING_REAPPROVAL"
        is_valid, issues = verify_human_approval(pack)
        assert is_valid is False
        assert any("HỦY HIỆU LỰC" in iss for iss in issues)

    # Test 6: Agent tự khai báo forked_subagent -> Không được independent
    def test_agent_declared_forked_subagent_not_independent(self):
        norm = normalize_reviewer({
            "kind": "separate_agent",
            "name": "Background Worker",
            "execution_context": "forked_subagent"
        })
        assert norm["independent"] is False
        assert norm["verification_source"] == "unverified_claim"
        assert norm["assurance_level"] == "UNVERIFIED_INDEPENDENT_CLAIM"

    # Test 7: Agent tự tạo subagent_id -> Không được independent
    def test_agent_created_subagent_id_not_independent(self):
        norm = normalize_reviewer({
            "kind": "separate_agent",
            "name": "Custom Worker",
            "subagent_id": "subagent-arbitrary-uuid-999"
        })
        assert norm["independent"] is False
        assert norm["verification_source"] == "unverified_claim"

    # Test 8: Agent tự đặt independent=true -> Không được independent
    def test_agent_declared_independent_true_not_independent(self):
        norm_same = normalize_reviewer({
            "kind": "same_context_agent",
            "name": "Self Reviewer",
            "independent": True
        })
        assert norm_same["independent"] is False
        assert norm_same["verification_source"] == "same_context_model"

        norm_sep = normalize_reviewer({
            "kind": "separate_agent",
            "name": "Separate Worker",
            "independent": True
        })
        assert norm_sep["independent"] is False
        assert norm_sep["verification_source"] == "unverified_claim"

    # Test 9: Reviewer tự khai báo automated_test -> Không được coi là test đã chạy nếu không có execution record
    def test_reviewer_declared_automated_test_without_execution_record(self, tmp_path):
        empty_log = tmp_path / "empty_test.log"
        empty_log.write_text("", encoding="utf-8")  # Empty file

        ref_type, is_valid, msg = classify_and_validate_evidence_ref(str(empty_log), status="TESTED")
        assert is_valid is False
        assert "rỗng" in msg

    # Test 10: Evidence reference là chuỗi tùy ý -> Reject
    def test_evidence_ref_arbitrary_string_rejected(self):
        ref_type, is_valid, msg = classify_and_validate_evidence_ref("some random arbitrary string", None)
        assert is_valid is False
        assert ref_type == "arbitrary_string"
        assert "chuỗi tùy ý" in msg

    # Test 11: Test descriptor không có execution record -> Reject
    def test_test_descriptor_without_execution_record_rejected(self):
        ref_type, is_valid, msg = classify_and_validate_evidence_ref("pytest_suite", None)
        assert is_valid is False
        assert ref_type == "arbitrary_string"

    # Test 12: Evidence file không tồn tại -> Reject
    def test_evidence_file_not_found_rejected(self, tmp_path):
        pack = create_evidence_pack("TASK-ADV-12", "build-webapp")
        app_file = tmp_path / "index.js"
        app_file.write_text("console.log('hi')", encoding="utf-8")
        add_step_evidence(
            pack=pack,
            step_id="step_test",
            role="technical-auditor",
            skill_used="app-auditor",
            artifact=app_file,
            verification_method="unit_test",
            evidence_ref="missing_audit.log",
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "Jest"}
        )
        valid, issues = validate_evidence_pack(pack)
        assert valid is False
        assert any("Tệp bằng chứng cục bộ không tồn tại" in iss for iss in issues)

    # Test 13: Evidence file bị thay đổi -> Reject
    def test_evidence_file_tampered_rejected(self, tmp_path):
        app_file = tmp_path / "app.py"
        app_file.write_text("print('app')", encoding="utf-8")
        ev_log = tmp_path / "pytest_run.log"
        ev_log.write_text("exit_code=0: 10 tests passed", encoding="utf-8")

        pack = create_evidence_pack("TASK-ADV-13", "build-webapp")
        add_step_evidence(
            pack=pack,
            step_id="step_test",
            role="technical-auditor",
            skill_used="app-auditor",
            artifact=app_file,
            verification_method="pytest",
            evidence_ref=str(ev_log),
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "Pytest Engine"}
        )
        # Modifying evidence file after evidence recording
        ev_log.write_text("exit_code=1: test failed (tampered)", encoding="utf-8")
        valid, issues = validate_evidence_pack(pack)
        assert valid is False
        assert any("Tệp bằng chứng đã bị sửa đổi sau kiểm thử" in iss for iss in issues)

    # Test 14: Screenshot tồn tại nhưng chưa được đánh giá -> Không được tự động UX PASS
    def test_screenshot_without_evaluation_not_automatic_ux_pass(self, tmp_path):
        screen = tmp_path / "screen.png"
        screen.write_bytes(b"MOCK_PNG_IMAGE_DATA")
        pack = create_evidence_pack("TASK-ADV-14", "thiet-ke")
        add_step_evidence(
            pack=pack,
            step_id="step_visual",
            role="ux-reviewer",
            skill_used="thiet-ke",
            artifact=screen,
            verification_method="screenshot_capture",
            evidence_ref=str(screen),
            status="OBSERVED",
            reviewer={"kind": "same_context_agent", "name": "Designer"},
            remaining_risk=""  # No evaluation notes
        )
        valid, issues = validate_evidence_pack(pack)
        assert valid is False
        assert any("Screenshot tồn tại nhưng chưa được đánh giá UX" in iss for iss in issues)

    # Test 15: Tier 3 thiếu trusted human approval -> BLOCKED
    def test_tier_3_missing_trusted_human_approval_blocked(self, tmp_path):
        pack = create_evidence_pack("TASK-ADV-15", "tu-van-phap-luat", human_approval={"required": True})
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Legal Director",
            channel="interactive_user_confirmation"  # No trusted token
        )
        is_compliant, issues = audit_review_compliance(pack, "tier_3_high", "legal_finance")
        assert is_compliant is False
        assert any("Tier 3 (Rủi ro Cao)" in iss for iss in issues)

    # Test 16: Tier 3 thiếu verified independent review -> BLOCKED
    def test_tier_3_missing_verified_independent_review_blocked(self, tmp_path):
        pack = create_evidence_pack("TASK-ADV-16", "tu-van-phap-luat", human_approval={"required": True})
        test_log = tmp_path / "auto.log"
        test_log.write_text("exit_code=0: legal claim guard clean", encoding="utf-8")
        add_step_evidence(
            pack=pack,
            step_id="step_auto",
            role="legal-compliance-reviewer",
            skill_used="tu-van-phap-luat",
            artifact=test_log,
            verification_method="claim_guard",
            evidence_ref=str(test_log),
            status="TESTED",
            reviewer={"kind": "automated_test", "name": "ClaimGuard"}
        )
        record_human_approval(
            pack=pack,
            approved=True,
            approver="Legal Director",
            channel="interactive_user_confirmation",
            trusted_attestation={"verified": True, "provider": "trusted_hardware_token", "event_signature": "sig_legal"}
        )
        # Missing verified separate_agent or human independent reviewer
        is_compliant, issues = audit_review_compliance(pack, "tier_3_high", "legal_finance")
        assert is_compliant is False
        assert any("thẩm định độc lập có chứng thực thực thi tin cậy" in iss for iss in issues)
