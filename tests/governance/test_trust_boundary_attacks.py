#!/usr/bin/env python3
"""
tests/governance/test_trust_boundary_attacks.py — Adversarial trust-boundary regression suite.

Principle under test: caller-controlled data must never be treated as trusted evidence.

Every attack drives the real governance functions (add_step_evidence, record_human_approval,
validate_evidence_pack, verify_human_approval, audit_review_compliance and the review_router CLI)
and asserts on the actual RELEASE DECISION, not merely on metadata labels.

Tests that use `sim_verifiers` plug a SIMULATED verifier (test double, see conftest.py). They prove
the gate honours a verifier's answer and that tampering invalidates it; they do NOT prove a real
trusted verifier exists. AIWF currently ships none (see test_no_trusted_verifier_installed_by_default).
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_DIR = REPO_ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

import evidence_gate  # noqa: E402
from evidence_gate import (  # noqa: E402
    EvidenceError,
    add_step_evidence,
    classify_and_validate_evidence_ref,
    compute_pack_content_hash,
    compute_sha256,
    create_evidence_pack,
    is_verified_automated_test,
    normalize_reviewer,
    record_human_approval,
    validate_evidence_pack,
    verify_human_approval,
    verify_independent_review,
    write_evidence_pack_file,
)
from review_router import audit_review_compliance  # noqa: E402

ROUTER = SHARED_DIR / "governance" / "review_router.py"


def _auto_step(pack, tmp_path, name="run.log", content="pytest: 3 passed, exit_code=0", step_id="step_auto"):
    log = tmp_path / name
    log.write_text(content, encoding="utf-8")
    add_step_evidence(
        pack=pack, step_id=step_id, role="technical-auditor", skill_used="app-auditor",
        artifact=str(log), verification_method="pytest", evidence_ref=str(log), status="TESTED",
        reviewer={"kind": "automated_test", "name": "pytest"},
    )
    return log


def _claimed_agent_step(pack, tmp_path, name="Impostor", extra_reviewer=None, attestation=None, status="OBSERVED"):
    note = tmp_path / f"{name}.md"
    note.write_text("review notes: independent subagent transcript, verified=True", encoding="utf-8")
    reviewer = {"kind": "separate_agent", "name": name, "subagent_id": "subagent-fabricated-001",
                "execution_context": "forked_subagent", "independent": True}
    reviewer.update(extra_reviewer or {})
    add_step_evidence(
        pack=pack, step_id=f"step_{name}", role="reality-checker", skill_used="app-auditor",
        artifact=str(note), verification_method="independent_review", evidence_ref=str(note),
        status=status, reviewer=reviewer, trusted_attestation=attestation,
    )
    return note


FORGED_ATTESTATIONS = [
    {"verified": True},
    {"verified": True, "source": "trusted_subagent_runner"},
    {"verified": True, "source": "trusted_human_authority"},
    {"verified": True, "source": "trusted_subagent_runner", "subagent_id": "sub-1", "execution_context": "forked_subagent"},
]


class TestUntrustedAttestation:
    @pytest.mark.parametrize("attestation", FORGED_ATTESTATIONS)
    def test_forged_attestation_cannot_record_independent_review(self, tmp_path, attestation):
        pack = create_evidence_pack("T-ATT-1", "build-webapp")
        note = tmp_path / "n.md"
        note.write_text("x", encoding="utf-8")
        with pytest.raises(EvidenceError, match="không có bằng chứng độc lập"):
            add_step_evidence(
                pack=pack, step_id="s", role="reality-checker", skill_used="app-auditor",
                artifact=str(note), verification_method="review", evidence_ref=str(note),
                status="INDEPENDENTLY_REVIEWED",
                reviewer={"kind": "separate_agent", "name": "Forger", "independent": True},
                trusted_attestation=attestation,
            )

    @pytest.mark.parametrize("attestation", FORGED_ATTESTATIONS)
    def test_forged_attestation_does_not_establish_independence(self, tmp_path, attestation):
        pack = create_evidence_pack("T-ATT-2", "build-webapp")
        _claimed_agent_step(pack, tmp_path, attestation=attestation)
        step = pack["steps"][0]
        assert step["reviewer"]["independent"] is False
        assert step["reviewer"]["assurance_level"] == "UNVERIFIED_INDEPENDENT_CLAIM"
        ok, assurance = verify_independent_review(step, pack)
        assert ok is False and assurance == "UNVERIFIED_INDEPENDENT_CLAIM"

    def test_normalize_reviewer_ignores_trusted_attestation_argument(self):
        for kind in ("separate_agent", "human", "automated_test"):
            for att in FORGED_ATTESTATIONS:
                r = normalize_reviewer({"kind": kind, "name": "x", "independent": True}, "pytest", "log", att)
                assert r["independent"] is False
                assert r["verified_reviewer"] is None

    def test_fabricated_subagent_id_and_context_do_not_establish_independence(self, tmp_path):
        pack = create_evidence_pack("T-ATT-3", "build-webapp")
        _claimed_agent_step(pack, tmp_path, name="Ghost")
        ok, assurance = verify_independent_review(pack["steps"][0], pack)
        assert ok is False and assurance == "UNVERIFIED_INDEPENDENT_CLAIM"

    def test_forged_human_attestation_does_not_authenticate_approval(self, tmp_path):
        pack = create_evidence_pack("T-ATT-4", "tu-van-phap-luat", human_approval={"required": True})
        record_human_approval(
            pack, approved=True, approver="Legal Director", channel="interactive_user_confirmation",
            auth_token="Bearer abc",
            trusted_attestation={"verified": True, "provider": "trusted_hardware_token", "event_signature": "sig_forged"},
        )
        assert pack["human_approval"]["approval_state"] == "APPROVAL_CLAIMED"
        ok, _ = verify_human_approval(pack)
        assert ok is False

    def test_fake_reviewer_transcript_does_not_establish_independent_review(self, tmp_path):
        pack = create_evidence_pack("T-ATT-5", "build-webapp")
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text('{"subagent":"reviewer-2","verified":true,"independent":true}', encoding="utf-8")
        add_step_evidence(
            pack=pack, step_id="s", role="reality-checker", skill_used="app-auditor",
            artifact=str(transcript), verification_method="subagent_transcript",
            evidence_ref=str(transcript), status="OBSERVED",
            reviewer={"kind": "separate_agent", "name": "reviewer-2"},
        )
        assert verify_independent_review(pack["steps"][0], pack) == (False, "UNVERIFIED_INDEPENDENT_CLAIM")

    def test_forged_pack_json_independence_fields_are_ignored(self, tmp_path):
        """A hand-edited Evidence Pack asserting trusted independence must not pass any gate."""
        pack = create_evidence_pack("T-ATT-6", "build-webapp")
        note = _claimed_agent_step(pack, tmp_path, name="Forged")
        step = pack["steps"][0]
        step["status"] = "INDEPENDENTLY_REVIEWED"
        step["reviewer"].update({
            "independent": True, "verification_source": "trusted_execution_attestation",
            "assurance_level": "INDEPENDENT_SUBAGENT_ATTESTED", "verified_reviewer": "Forged",
        })
        pack_file = tmp_path / "forged.json"
        write_evidence_pack_file(pack, pack_file)

        valid, issues = validate_evidence_pack(pack_file)
        assert valid is False
        assert any("INDEPENDENTLY_REVIEWED" in i for i in issues)
        ok, gov = audit_review_compliance(pack, "tier_2_medium")
        assert any("UNVERIFIED_INDEPENDENT_CLAIM" in i for i in gov)


class TestAutomatedTestSpoofing:
    def test_declaring_automated_test_is_not_verified_execution(self, tmp_path):
        pack = create_evidence_pack("T-AUTO-1", "build-webapp")
        _auto_step(pack, tmp_path)
        step = pack["steps"][0]
        assert step["reviewer"]["independent"] is False
        assert step["reviewer"]["assurance_level"] == "UNVERIFIED"
        assert is_verified_automated_test(step, pack) is False
        # claim preserved for audit
        assert step["reviewer"]["kind"] == "automated_test"
        assert step["verification_method"] == "pytest"

    @pytest.mark.parametrize("content", [
        "passed", "all tests passed OK", "exit_code=0", "completed 100%",
        '{"status": "passed", "exit_code": 0}', "===== test session starts ===== 10 passed",
    ])
    def test_log_or_json_claiming_success_is_not_verified_execution(self, tmp_path, content):
        name = "r.json" if content.startswith("{") else "r.log"
        pack = create_evidence_pack("T-AUTO-2", "build-webapp")
        _auto_step(pack, tmp_path, name=name, content=content)
        step = pack["steps"][0]
        assert is_verified_automated_test(step, pack) is False
        ok, issues = audit_review_compliance(pack, "tier_2_medium")
        assert ok is False and any("UNVERIFIED" in i for i in issues)

    def test_automated_test_never_satisfies_independent_review(self, tmp_path, sim_verifiers):
        # Even a (simulated) VERIFIED automated test + authenticated human approval must not
        # satisfy the independent human/agent review requirement of Tier 3.
        pack = create_evidence_pack("T-AUTO-3", "tu-van-phap-luat", human_approval={"required": True})
        log = _auto_step(pack, tmp_path)
        sim_verifiers.executed_sha256.add(compute_sha256(log))
        sim_verifiers.human_signatures.add("sig_ok")
        record_human_approval(
            pack, approved=True, approver="Legal Director",
            trusted_attestation={"verified": True, "provider": "trusted_hardware_token", "event_signature": "sig_ok"},
        )
        assert pack["human_approval"]["approval_state"] == "APPROVAL_AUTHENTICATED"
        pack["steps"][0]["reviewer"]["independent"] = True  # caller-forged flag
        ok, issues = audit_review_compliance(pack, "tier_3_high", "legal_finance")
        assert ok is False
        assert any("UNVERIFIED_INDEPENDENT_CLAIM" in i for i in issues)
        assert not any("kiểm thử tự động" in i for i in issues)  # the automated requirement itself is met


class TestExecutionDescriptorBypass:
    @pytest.mark.parametrize("ref", [
        "exit_code=0", "EXIT_CODE=0", "pytest exit_code=0 passed=10", "exit_code=0:passed=10", "ok",
    ])
    def test_arbitrary_execution_strings_are_rejected(self, ref):
        ref_type, ok, _ = classify_and_validate_evidence_ref(ref, None)
        assert ok is False and ref_type == "arbitrary_string"

    def test_descriptor_cannot_back_a_validated_pack(self, tmp_path):
        pack = create_evidence_pack("T-DESC-1", "build-webapp")
        add_step_evidence(
            pack=pack, step_id="s", role="technical-auditor", skill_used="app-auditor",
            artifact="x.py", verification_method="pytest", evidence_ref="exit_code=0", status="TESTED",
            reviewer={"kind": "automated_test", "name": "pytest"},
        )
        valid, issues = validate_evidence_pack(pack)
        assert valid is False and any("chuỗi tùy ý" in i for i in issues)
        ok, gov = audit_review_compliance(pack, "tier_2_medium")
        assert ok is False

    def test_local_log_is_supporting_evidence_only(self, tmp_path):
        log = tmp_path / "a.log"
        log.write_text("passed", encoding="utf-8")
        ref_type, ok, _ = classify_and_validate_evidence_ref(str(log), None)
        assert ok is True  # exists + structurally valid (kept as supporting evidence)
        assert ref_type == "supporting_log"  # but never an 'automated_test_record'

    def test_external_url_is_reference_only(self, tmp_path):
        pack = create_evidence_pack("T-DESC-2", "build-webapp")
        add_step_evidence(
            pack=pack, step_id="s", role="technical-auditor", skill_used="app-auditor",
            artifact="x.py", verification_method="ci", evidence_ref="https://ci.example.com/run/1",
            status="TESTED", reviewer={"kind": "automated_test", "name": "ci"},
        )
        assert is_verified_automated_test(pack["steps"][0], pack) is False
        ok, _ = audit_review_compliance(pack, "tier_2_medium")
        assert ok is False

    def test_evidence_modified_after_recording_invalidates_evidence_and_verification(self, tmp_path, sim_verifiers):
        pack = create_evidence_pack("T-DESC-3", "build-webapp")
        log = _auto_step(pack, tmp_path)
        sim_verifiers.executed_sha256.add(compute_sha256(log))
        step = pack["steps"][0]
        assert is_verified_automated_test(step, pack) is True          # simulated verifier path
        assert audit_review_compliance(pack, "tier_2_medium")[0] is True

        log.write_text("exit_code=0 (edited after the fact)", encoding="utf-8")

        valid, issues = validate_evidence_pack(pack)
        assert valid is False and any("evidence hash mismatch" in i for i in issues)
        assert is_verified_automated_test(step, pack) is False         # verification claim invalidated
        ok, gov = audit_review_compliance(pack, "tier_2_medium")
        assert ok is False and any("evidence hash mismatch" in i for i in gov)
        # integrity violations are reported at every tier
        assert audit_review_compliance(pack, "tier_1_low")[0] is False

    def test_evidence_deleted_after_recording_invalidates_verification(self, tmp_path, sim_verifiers):
        pack = create_evidence_pack("T-DESC-4", "build-webapp")
        log = _auto_step(pack, tmp_path)
        sim_verifiers.executed_sha256.add(compute_sha256(log))
        step = pack["steps"][0]
        assert is_verified_automated_test(step, pack) is True
        log.unlink()
        assert is_verified_automated_test(step, pack) is False
        assert audit_review_compliance(pack, "tier_2_medium")[0] is False

    def test_missing_recorded_hash_cannot_be_verified(self, tmp_path, sim_verifiers):
        pack = create_evidence_pack("T-DESC-5", "build-webapp")
        log = _auto_step(pack, tmp_path)
        sim_verifiers.executed_sha256.add(compute_sha256(log))
        step = copy.deepcopy(pack["steps"][0])
        step["evidence_ref_sha256"] = None  # hand-edited pack dropping the integrity anchor
        assert is_verified_automated_test(step, pack) is False


class TestTier3FailClosed:
    def _tier3_pack(self, tmp_path):
        pack = create_evidence_pack("T-T3-1", "tu-van-phap-luat", human_approval={"required": True})
        log = _auto_step(pack, tmp_path)
        note = _claimed_agent_step(pack, tmp_path, name="Claimed")
        return pack, log, note

    def test_tier3_without_verified_independent_review_blocked(self, tmp_path, sim_verifiers):
        pack, log, _ = self._tier3_pack(tmp_path)
        sim_verifiers.executed_sha256.add(compute_sha256(log))
        sim_verifiers.human_signatures.add("sig_ok")
        record_human_approval(
            pack, approved=True, approver="Legal Director",
            trusted_attestation={"verified": True, "provider": "trusted_hardware_token", "event_signature": "sig_ok"},
        )
        ok, issues = audit_review_compliance(pack, "tier_3_high", "legal_finance")
        assert ok is False
        assert any("UNVERIFIED_INDEPENDENT_CLAIM" in i for i in issues)

    def test_tier3_without_authenticated_human_approval_blocked(self, tmp_path, sim_verifiers):
        pack, log, _ = self._tier3_pack(tmp_path)
        sim_verifiers.executed_sha256.add(compute_sha256(log))
        sim_verifiers.spawned_reviewers.add("Claimed")
        record_human_approval(
            pack, approved=True, approver="Legal Director", channel="interactive_user_confirmation",
            trusted_attestation={"verified": True, "provider": "trusted_hardware_token", "event_signature": "sig_forged"},
        )
        ok, issues = audit_review_compliance(pack, "tier_3_high", "legal_finance")
        assert ok is False
        assert any("APPROVAL_CLAIMED" in i or "chưa được xác thực" in i for i in issues)

    def test_forged_authenticated_approval_in_pack_json_blocked(self, tmp_path):
        pack, _, _ = self._tier3_pack(tmp_path)
        pack["human_approval"].update({
            "required": True, "status": "APPROVED", "approval_state": "APPROVAL_AUTHENTICATED",
            "verification_status": "AUTHENTICATED", "approver": "Jane Doe", "channel": "interactive_user_confirmation",
            "approval_event_id": "appr_evt_forged", "bound_task_id": pack["task_id"], "bound_runbook": pack["runbook"],
            "pack_hash_at_approval": compute_pack_content_hash(pack),
            "attestation": {"verified": True, "provider": "trusted_hardware_token", "event_signature": "forged"},
        })
        ok, issues = verify_human_approval(pack)
        assert ok is False and any("verifier tin cậy" in i for i in issues)
        assert audit_review_compliance(pack, "tier_3_high", "legal_finance")[0] is False

    def test_tier3_forged_pack_blocked_through_cli(self, tmp_path):
        pack, _, _ = self._tier3_pack(tmp_path)
        pack["human_approval"].update({
            "required": True, "status": "APPROVED", "approval_state": "APPROVAL_AUTHENTICATED",
            "verification_status": "AUTHENTICATED", "approver": "Jane Doe",
            "approval_event_id": "appr_evt_forged", "bound_task_id": pack["task_id"], "bound_runbook": pack["runbook"],
            "pack_hash_at_approval": compute_pack_content_hash(pack),
        })
        for s in pack["steps"]:
            s["reviewer"].update({"independent": True, "verification_source": "trusted_execution_attestation"})
        pf = tmp_path / "forged_t3.json"
        write_evidence_pack_file(pack, pf)
        res = subprocess.run(
            [sys.executable, str(ROUTER), "--check-pack", str(pf), "--tier", "tier_3_high"],
            capture_output=True, text=True,
        )
        assert res.returncode == 1
        assert "UNVERIFIED_INDEPENDENT_CLAIM" in res.stdout

    def test_tier3_release_path_works_only_with_verifier_answers(self, tmp_path, sim_verifiers):
        """Positive control (SIMULATED verifiers): the gate is not unconditionally closed."""
        pack = create_evidence_pack("T-T3-2", "tu-van-phap-luat", human_approval={"required": True})
        log = _auto_step(pack, tmp_path)
        sim_verifiers.executed_sha256.add(compute_sha256(log))
        sim_verifiers.spawned_reviewers.add("Real Subagent")
        sim_verifiers.human_signatures.add("sig_real")
        note = tmp_path / "r.md"
        note.write_text("review", encoding="utf-8")
        add_step_evidence(
            pack, "step_ir", "reality-checker", "app-auditor", str(note), "independent_review",
            str(note), "INDEPENDENTLY_REVIEWED", {"kind": "separate_agent", "name": "Real Subagent"},
        )
        record_human_approval(
            pack, approved=True, approver="Legal Director",
            trusted_attestation={"verified": True, "provider": "trusted_hardware_token", "event_signature": "sig_real"},
        )
        ok, issues = audit_review_compliance(pack, "tier_3_high", "legal_finance")
        assert ok is True, issues


class TestNoOverBlocking:
    def test_tier1_ordinary_workflow_not_blocked(self, tmp_path):
        pack = create_evidence_pack("T-T1-1", "build-webapp")
        log = _auto_step(pack, tmp_path)
        note = tmp_path / "self.md"
        note.write_text("self review", encoding="utf-8")
        add_step_evidence(
            pack, "step_self", "reality-checker", "doc-sau", str(note), "reflection", str(note),
            "SELF_REVIEWED", {"kind": "same_context_agent", "name": "model"},
        )
        ok, issues = audit_review_compliance(pack, "tier_1_low", "code")
        assert ok is True, issues
        valid, vissues = validate_evidence_pack(pack)
        assert valid is True, vissues
        assert pack["overall_status"] == "VERIFIED"

    def test_tier1_cli_ordinary_workflow_exit_0(self, tmp_path):
        pack = create_evidence_pack("T-T1-2", "build-webapp")
        _auto_step(pack, tmp_path)
        pf = tmp_path / "p.json"
        write_evidence_pack_file(pack, pf)
        res = subprocess.run(
            [sys.executable, str(ROUTER), "--check-pack", str(pf), "--tier", "tier_1_low"],
            capture_output=True, text=True,
        )
        assert res.returncode == 0


class TestVerifierBoundary:
    def test_no_trusted_verifier_installed_by_default(self):
        """OBSERVED limitation: AIWF ships no trusted verifier; all verification is fail-closed."""
        assert evidence_gate._TRUSTED_VERIFIERS == {}

    def test_verifier_must_return_exactly_true(self, monkeypatch):
        for bad in ("yes", 1, {"verified": True}, None, [True]):
            monkeypatch.setitem(evidence_gate._TRUSTED_VERIFIERS, "automated_test", lambda c, b=bad: b)
            assert evidence_gate._trusted_verify("automated_test", {}) is False

    def test_verifier_exception_is_fail_closed(self, monkeypatch):
        def boom(_):
            raise RuntimeError("verifier down")
        monkeypatch.setitem(evidence_gate._TRUSTED_VERIFIERS, "independent_review", boom)
        assert evidence_gate._trusted_verify("independent_review", {}) is False

    def test_verifier_cannot_mutate_the_pack_it_inspects(self, tmp_path, monkeypatch):
        pack = create_evidence_pack("T-VB-1", "build-webapp")
        _auto_step(pack, tmp_path)
        snapshot = copy.deepcopy(pack["steps"][0])

        def mutator(claim):
            claim["step"]["reviewer"]["independent"] = True
            return True
        monkeypatch.setitem(evidence_gate._TRUSTED_VERIFIERS, "automated_test", mutator)
        is_verified_automated_test(pack["steps"][0], pack)
        assert pack["steps"][0] == snapshot
