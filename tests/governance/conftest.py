#!/usr/bin/env python3
"""
tests/governance/conftest.py

SIMULATED trusted verifiers (TEST DOUBLES ONLY).

AIWF ships NO trusted verifier (trusted runner / subagent attestation / human approval authority).
Production behavior is therefore fail-closed. To exercise the *gate logic* that sits behind a real
verifier (invalidation after tampering, Tier 3 release path), tests may plug a simulated verifier
into the in-process registry via `sim_verifiers`.

A pass obtained through `sim_verifiers` proves ONLY that the gate honours a verifier's answer.
It does NOT prove that a real trusted verifier exists or works.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_DIR = REPO_ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

import evidence_gate  # noqa: E402


class SimulatedVerifiers:
    """Verifier ngoài ranh giới dữ liệu (mô phỏng): chỉ tin những gì chính nó đã 'chứng kiến'."""

    def __init__(self):
        self.human_signatures = set()   # event_signature do "authority" mô phỏng đã cấp
        self.executed_sha256 = set()    # sha256 của file log mà "runner" mô phỏng đã thực sự chạy
        self.spawned_reviewers = set()  # tên reviewer do "subagent runner" mô phỏng đã khởi chạy

    def _human(self, claim):
        return (claim.get("attestation") or {}).get("event_signature") in self.human_signatures

    def _auto(self, claim):
        return claim["step"].get("evidence_ref_sha256") in self.executed_sha256

    def _indep(self, claim):
        return claim["step"]["reviewer"].get("name") in self.spawned_reviewers


@pytest.fixture
def sim_verifiers(monkeypatch):
    sim = SimulatedVerifiers()
    monkeypatch.setitem(evidence_gate._TRUSTED_VERIFIERS, evidence_gate.VERIFIER_HUMAN_APPROVAL, sim._human)
    monkeypatch.setitem(evidence_gate._TRUSTED_VERIFIERS, evidence_gate.VERIFIER_AUTOMATED_TEST, sim._auto)
    monkeypatch.setitem(evidence_gate._TRUSTED_VERIFIERS, evidence_gate.VERIFIER_INDEPENDENT_REVIEW, sim._indep)
    return sim
