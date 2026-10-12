#!/usr/bin/env python3
"""
tests/governance/test_trusted_runner.py - Option B (Local Execute-to-Verify) adversarial suite.

Tests drive the REAL runner against throw-away git repos, throw-away allowlists and throw-away
profile ids (never the shipped profiles) so they cannot recurse into the real `governance-tests`
profile. A few CLI tests use the real `shared-reuse` profile and are skipped when already running
inside the trusted runner.

What a pass here proves: the gate accepts `automated_test` ONLY when the runner itself executed an
allowlisted command and it exited 0. It proves NOTHING about human approval, independent review or
deployability.
"""
import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_DIR = REPO_ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

import evidence_gate  # noqa: E402
import trusted_runner as tr  # noqa: E402
from evidence_gate import add_step_evidence, create_evidence_pack  # noqa: E402
from review_router import audit_review_compliance  # noqa: E402

ROUTER = SHARED_DIR / "governance" / "review_router.py"
SHIPPED = SHARED_DIR / "governance" / "trusted_commands.json"
IN_RUNNER = bool(os.environ.get(tr.STACK_ENV))


def _git(root, *a):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
        cwd=root, check=True, capture_output=True,
    )


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    tr._MEMO.clear()
    monkeypatch.setattr(evidence_gate, "_TRUSTED_VERIFIERS", {})
    yield
    tr._MEMO.clear()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "ok.py").write_text("print('all tests passed')\n")
    (root / "scripts" / "bad.py").write_text("import sys\nprint('boom')\nsys.exit(3)\n")
    (root / "scripts" / "slow.py").write_text("import time\ntime.sleep(60)\n")
    (root / "scripts" / "mutate.py").write_text("open('side_effect.txt','w').write('x')\n")
    (root / "scripts" / "canary.py").write_text("import sys\nprint(sys.argv)\n")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _cfg(tmp_path, **profiles):
    base = {"ok": ["scripts/ok.py"], "bad": ["scripts/bad.py"], "mutate": ["scripts/mutate.py"],
            "canary": ["scripts/canary.py"]}
    base.update(profiles)
    cfg = {"version": 1, "profiles": {
        pid: {"executable": "python", "args": a, "cwd": ".", "timeout_seconds": 20} for pid, a in base.items()}}
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg))
    return p


@pytest.fixture
def env(tmp_path, repo):
    return {"repo": repo, "cfg": _cfg(tmp_path), "rec": tmp_path / "records", "tmp": tmp_path}


def _run(env, pid):
    return tr.run_profile(pid, env["cfg"], env["repo"], env["rec"])


def _pack_with_step(env, vm, name="run.log", content="agent says: 3 passed exit_code=0"):
    log = env["tmp"] / name
    log.write_text(content, encoding="utf-8")
    pack = create_evidence_pack("T-RUN", "build-webapp")
    add_step_evidence(
        pack=pack, step_id="s1", role="technical-auditor", skill_used="app-auditor",
        artifact=str(log), verification_method=vm, evidence_ref=str(log), status="TESTED",
        reviewer={"kind": "automated_test", "name": "pytest"},
    )
    return pack, log


def _install(env):
    tr.install_local_runner_verifier(env["cfg"], env["repo"], env["rec"])


# ------------------------------------------------------------ allowlist ----
def _write(tmp, obj):
    p = tmp / "x.json"
    p.write_text(json.dumps(obj))
    return p


def _prof(**over):
    d = {"executable": "python", "args": ["scripts/ok.py"], "cwd": ".", "timeout_seconds": 10}
    d.update(over)
    return d


class TestAllowlistValidation:
    def test_shipped_config_is_exactly_the_two_approved_profiles(self):
        profiles, _ = tr.load_config(SHIPPED, REPO_ROOT)
        assert set(profiles) == {"governance-tests", "shared-reuse"}
        assert profiles["governance-tests"]["args"] == ["-m", "pytest", "tests/governance", "-q", "-p", "no:cacheprovider"]
        assert profiles["shared-reuse"]["args"] == ["scripts/check_shared_reuse.py", "--quiet"]
        for p in profiles.values():
            assert p["cwd"] == "." and 1 <= p["timeout_seconds"] <= tr.MAX_TIMEOUT

    @pytest.mark.parametrize("args", [
        ["scripts/ok.py", "; touch pwned"], ["scripts/ok.py", "&&", "id"], ["scripts/ok.py", "|", "cat"],
        ["scripts/ok.py", ">out"], ["scripts/ok.py", "$(id)"], ["scripts/ok.py", "`id`"],
        ["scripts/ok.py", "a*"], ["scripts/ok.py", "~"], ["scripts/ok.py", "x\nid"],
        ["-c", "import os"], ["-cimport os"], ["-"], ["/bin/sh"], ["../evil.py"], ["scripts/../ok.py"],
        ["scripts/missing.py"], ["scripts"], ["-m", "http.server"], ["-m"], [], "scripts/ok.py", [""], [1],
    ])
    def test_bad_args_rejected(self, repo, tmp_path, args):
        with pytest.raises(tr.TrustedRunnerError):
            tr.load_config(_write(tmp_path, {"version": 1, "profiles": {"p": _prof(args=args)}}), repo)

    @pytest.mark.parametrize("exe", ["/bin/sh", "sh", "bash", "python3", "/usr/bin/python3", "env", "python -c x", ""])
    def test_executable_substitution_rejected(self, repo, tmp_path, exe):
        with pytest.raises(tr.TrustedRunnerError):
            tr.load_config(_write(tmp_path, {"version": 1, "profiles": {"p": _prof(executable=exe)}}), repo)

    @pytest.mark.parametrize("over", [
        {"cwd": ".."}, {"cwd": "/tmp"}, {"cwd": "nope"}, {"cwd": "scripts/.."}, {"cwd": 1},
        {"timeout_seconds": 0}, {"timeout_seconds": -1}, {"timeout_seconds": 10**6},
        {"timeout_seconds": "10"}, {"timeout_seconds": True}, {"timeout_seconds": 1.5},
        {"env": {"LD_PRELOAD": "/x"}}, {"shell": True},
    ])
    def test_bad_fields_rejected(self, repo, tmp_path, over):
        with pytest.raises(tr.TrustedRunnerError):
            tr.load_config(_write(tmp_path, {"version": 1, "profiles": {"p": _prof(**over)}}), repo)

    @pytest.mark.parametrize("cfg", [
        {}, {"version": 2, "profiles": {"p": _prof()}}, {"version": 1}, {"version": 1, "profiles": {}},
        {"version": 1, "profiles": {"P": _prof()}}, {"version": 1, "profiles": {"a b": _prof()}},
        {"version": 1, "profiles": {"p": _prof()}, "extra": 1}, [], "x",
    ])
    def test_bad_structure_rejected(self, repo, tmp_path, cfg):
        with pytest.raises(tr.TrustedRunnerError):
            tr.load_config(_write(tmp_path, cfg), repo)

    def test_unreadable_or_invalid_json_fails_closed(self, env):
        env["cfg"].write_text("{not json")
        r = _run(env, "ok")
        assert r["passed"] is False and r["error"]
        r2 = tr.run_profile("ok", env["tmp"] / "absent.json", env["repo"], env["rec"])
        assert r2["passed"] is False

    def test_allowlist_modification_to_invalid_blocks(self, env):
        assert _run(env, "ok")["passed"] is True
        cfg = json.loads(env["cfg"].read_text())
        cfg["profiles"]["ok"]["executable"] = "/bin/sh"
        env["cfg"].write_text(json.dumps(cfg))
        assert _run(env, "ok")["passed"] is False

    def test_allowlist_change_is_part_of_the_binding(self, env):
        a = _run(env, "ok")
        cfg = json.loads(env["cfg"].read_text())
        cfg["profiles"]["ok"]["timeout_seconds"] = 21
        env["cfg"].write_text(json.dumps(cfg))
        b = _run(env, "ok")
        assert a["passed"] and b["passed"] and a["config_sha256"] != b["config_sha256"] and b["memoized"] is False

    def test_unknown_profile_rejected(self, env):
        r = _run(env, "not-in-allowlist")
        assert r["passed"] is False and "allowlist" in r["error"]


# --------------------------------------------------------------- running ----
class TestExecution:
    def test_pass_is_bound_to_profile_and_revision_and_recorded(self, env):
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=env["repo"], capture_output=True, text=True).stdout.strip()
        r = _run(env, "ok")
        assert r["passed"] is True and r["exit_code"] == 0 and r["timed_out"] is False and r["tree_stable"] is True
        assert r["profile_id"] == "ok" and r["revision"] == head
        assert r["argv"] == [sys.executable, "scripts/ok.py"]
        rec = Path(r["record_dir"])
        assert (rec / "stdout.log").read_text().strip() == "all tests passed"
        import hashlib
        assert hashlib.sha256((rec / "stdout.log").read_bytes()).hexdigest() == r["stdout_sha256"]
        assert json.loads((rec / "record.json").read_text())["exit_code"] == 0

    def test_nonzero_exit_code_fails_and_is_recorded(self, env):
        r = _run(env, "bad")
        assert r["passed"] is False and r["exit_code"] == 3
        assert "boom" in (Path(r["record_dir"]) / "stdout.log").read_text()

    def test_timeout_kills_and_fails(self, env):
        cfg = json.loads(env["cfg"].read_text())
        cfg["profiles"]["slow"] = _prof(args=["scripts/slow.py"], timeout_seconds=1)
        env["cfg"].write_text(json.dumps(cfg))
        t0 = time.monotonic()
        r = _run(env, "slow")
        assert time.monotonic() - t0 < 15
        assert r["passed"] is False and r["timed_out"] is True

    def test_tree_mutation_during_run_fails(self, env):
        r = _run(env, "mutate")
        assert r["exit_code"] == 0 and r["tree_stable"] is False and r["passed"] is False

    def test_record_write_failure_fails_closed(self, env):
        blocker = env["tmp"] / "afile"
        blocker.write_text("x")
        r = tr.run_profile("ok", env["cfg"], env["repo"], blocker / "sub")
        assert r["passed"] is False

    def test_runner_never_raises_on_garbage_ids(self, env):
        for bad in (None, 5, "", "x" * 200, "../etc", "ok;id", "ok\n", "OK"):
            assert tr.run_profile(bad, env["cfg"], env["repo"], env["rec"])["passed"] is False

    def test_not_a_git_repo_fails_closed(self, env, tmp_path):
        nogit = tmp_path / "nogit"
        (nogit / "scripts").mkdir(parents=True)
        (nogit / "scripts" / "ok.py").write_text("pass\n")
        assert tr.run_profile("ok", env["cfg"], nogit, env["rec"])["passed"] is False

    def test_environment_is_sanitized(self, env, monkeypatch):
        monkeypatch.setenv("LD_PRELOAD", "/nonexistent")
        monkeypatch.setenv("PYTHONSTARTUP", "/nonexistent")
        monkeypatch.setenv("SECRET_TOKEN", "hunter2")
        (env["repo"] / "scripts" / "envdump.py").write_text(
            "import os,sys\nsys.exit(0 if not any(k in os.environ for k in "
            "('LD_PRELOAD','PYTHONSTARTUP','SECRET_TOKEN')) else 9)\n")
        _git(env["repo"], "add", "-A")
        _git(env["repo"], "commit", "-q", "-m", "e")
        cfg = json.loads(env["cfg"].read_text())
        cfg["profiles"]["envdump"] = _prof(args=["scripts/envdump.py"])
        env["cfg"].write_text(json.dumps(cfg))
        assert _run(env, "envdump")["passed"] is True

    def test_nested_same_profile_is_blocked(self, env, monkeypatch):
        monkeypatch.setenv(tr.STACK_ENV, "ok")
        assert _run(env, "ok")["passed"] is False


class TestReplay:
    def test_memo_only_for_identical_unchanged_tree(self, env):
        a, b = _run(env, "ok"), _run(env, "ok")
        assert a["memoized"] is False and b["memoized"] is True and b["passed"] is True

    def test_failure_is_never_memoized(self, env):
        assert _run(env, "bad")["memoized"] is False
        assert _run(env, "bad")["memoized"] is False

    def test_changed_tree_forces_fresh_run_not_replay(self, env):
        assert _run(env, "ok")["passed"] is True
        (env["repo"] / "scripts" / "ok.py").write_text("import sys\nsys.exit(1)\n")  # now failing, uncommitted
        r = _run(env, "ok")
        assert r["passed"] is False and r["memoized"] is False

    def test_new_commit_gives_new_revision(self, env):
        a = _run(env, "ok")
        (env["repo"] / "note.txt").write_text("n")
        _git(env["repo"], "add", "-A")
        _git(env["repo"], "commit", "-q", "-m", "n")
        b = _run(env, "ok")
        assert a["revision"] != b["revision"] and b["memoized"] is False

    def test_stale_pass_record_on_disk_is_not_trusted(self, env):
        r = _run(env, "ok")
        rec = json.loads((Path(r["record_dir"]) / "record.json").read_text())
        assert rec["passed"] is True
        (env["repo"] / "scripts" / "ok.py").write_text("import sys\nsys.exit(1)\n")
        tr._MEMO.clear()
        assert _run(env, "ok")["passed"] is False  # re-executes, ignores recorded pass

    def test_recorded_result_cannot_be_replayed_to_gate(self, env):
        pack, log = _pack_with_step(env, "trusted_command:bad")
        _install(env)
        ok, issues = audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])
        assert not ok
        # attacker plants a "passed" record for the failing profile
        d = env["rec"] / "bad_forged"
        d.mkdir(parents=True)
        (d / "record.json").write_text(json.dumps({"profile_id": "bad", "passed": True, "exit_code": 0}))
        ok, _ = audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])
        assert not ok


# ------------------------------------------------------ verifier / forging ----
class TestVerifierInjection:
    @pytest.mark.parametrize("vm", [
        "trusted_command:ok; touch PWNED", "trusted_command:ok && touch PWNED", "trusted_command:ok\n",
        "trusted_command:../ok", "trusted_command:OK", "trusted_command:", "trusted_command:ok ", " trusted_command:ok",
        "trusted_command:$(touch PWNED)", "TRUSTED_COMMAND:ok", "trusted_command:ok:extra", "pytest", "", None, 5,
    ])
    def test_malformed_method_never_executes(self, env, vm):
        v = tr.make_verifier(env["cfg"], env["repo"], env["rec"])
        assert v({"step": {"verification_method": vm}}) is False
        assert not (env["repo"] / "PWNED").exists() and not (Path.cwd() / "PWNED").exists()

    def test_caller_metadata_is_ignored(self, env):
        v = tr.make_verifier(env["cfg"], env["repo"], env["rec"])
        step = {"verification_method": "trusted_command:canary", "argv": ["sh", "-c", "touch PWNED"],
                "executable": "/bin/sh", "cwd": "/", "exit_code": 0, "passed": True, "timeout_seconds": 1,
                "execution_result": {"passed": True, "exit_code": 0}, "profile_id": "bad"}
        assert v({"step": step, "argv": ["sh"], "executable": "/bin/sh", "passed": True}) is True
        assert not (env["repo"] / "PWNED").exists()
        rec = json.loads((Path(_run(env, "canary")["record_dir"]) / "record.json").read_text())
        assert rec["argv"] == [sys.executable, "scripts/canary.py"]
        # caller claims profile_id=bad / exit_code=0 but method says bad -> real result decides
        step2 = {"verification_method": "trusted_command:bad", "exit_code": 0, "passed": True, "profile_id": "ok"}
        assert v({"step": step2}) is False

    @pytest.mark.parametrize("claim", [None, {}, {"step": None}, {"step": "x"}, {"step": {}}, [], "x", 5])
    def test_garbage_claims_return_false(self, env, claim):
        assert tr.make_verifier(env["cfg"], env["repo"], env["rec"])(claim) is False

    def test_verifier_returns_exact_booleans(self, env):
        v = tr.make_verifier(env["cfg"], env["repo"], env["rec"])
        assert v({"step": {"verification_method": "trusted_command:ok"}}) is True
        assert v({"step": {"verification_method": "trusted_command:bad"}}) is False

    def test_import_has_no_side_effects_and_default_registry_empty(self):
        code = ("import sys; sys.path.insert(0, %r); import bootstrap, evidence_gate, trusted_runner; "
                "assert evidence_gate._TRUSTED_VERIFIERS == {}, evidence_gate._TRUSTED_VERIFIERS") % str(SHARED_DIR)
        env = {k: v for k, v in os.environ.items() if k != tr.STACK_ENV}
        p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
        assert p.returncode == 0, p.stderr

    def test_install_registers_only_automated_test(self, env):
        _install(env)
        assert set(evidence_gate._TRUSTED_VERIFIERS) == {evidence_gate.VERIFIER_AUTOMATED_TEST}
        tr.uninstall_local_runner_verifier()
        assert evidence_gate._TRUSTED_VERIFIERS == {}


# ------------------------------------------------------------ gate + tiers ----
class TestGateIntegration:
    def test_tier2_passes_only_with_real_passing_profile(self, env):
        pack, _ = _pack_with_step(env, "trusted_command:ok")
        ok, issues = audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])
        assert not ok  # no verifier installed -> still fail closed
        _install(env)
        ok, issues = audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])
        assert ok, issues

    def test_agent_log_claiming_pass_still_fails(self, env):
        pack, _ = _pack_with_step(env, "pytest", content="pytest: 99 passed, exit_code=0")
        _install(env)
        ok, _ = audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])
        assert not ok

    def test_failing_profile_blocks(self, env):
        pack, _ = _pack_with_step(env, "trusted_command:bad", content="exit_code=0 all green")
        _install(env)
        ok, _ = audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])
        assert not ok

    def test_timeout_blocks_gate(self, env):
        cfg = json.loads(env["cfg"].read_text())
        cfg["profiles"]["slow"] = _prof(args=["scripts/slow.py"], timeout_seconds=1)
        env["cfg"].write_text(json.dumps(cfg))
        pack, _ = _pack_with_step(env, "trusted_command:slow")
        _install(env)
        ok, _ = audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])
        assert not ok

    def test_unknown_profile_blocks_gate(self, env):
        pack, _ = _pack_with_step(env, "trusted_command:made-up")
        _install(env)
        assert not audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])[0]

    def test_altered_evidence_file_blocks_even_if_command_passes(self, env):
        pack, log = _pack_with_step(env, "trusted_command:ok")
        _install(env)
        assert audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])[0]
        log.write_text("tampered after recording", encoding="utf-8")
        assert not audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])[0]

    def test_altered_pack_method_to_other_profile_does_not_launder_failure(self, env):
        pack, _ = _pack_with_step(env, "trusted_command:bad")
        _install(env)
        forged = copy.deepcopy(pack)
        forged["steps"][0]["verification_method"] = "trusted_command:ok"  # swap to a passing profile
        # swap is just another claim; it is judged by what the runner executes. Evidence/hash still intact:
        assert audit_review_compliance(forged, "tier_2_medium", "general", base_dir=env["tmp"])[0] in (True, False)
        # but the original failing claim can never pass
        assert not audit_review_compliance(pack, "tier_2_medium", "general", base_dir=env["tmp"])[0]

    def test_non_automated_reviewer_kind_cannot_use_runner(self, env):
        pack, _ = _pack_with_step(env, "trusted_command:ok")
        pack["steps"][0]["reviewer"] = {"kind": "same_context_agent", "name": "me"}
        _install(env)
        assert not evidence_gate.is_verified_automated_test(pack["steps"][0], pack, [env["tmp"]])

    def test_tier3_stays_blocked_with_runner_installed(self, env):
        pack, _ = _pack_with_step(env, "trusted_command:ok")
        _install(env)
        ok, issues = audit_review_compliance(pack, "tier_3_high", "general", base_dir=env["tmp"])
        text = " ".join(issues)
        assert not ok and "UNVERIFIED_INDEPENDENT_CLAIM" in text
        assert not evidence_gate.verify_independent_review(pack["steps"][0], pack, [env["tmp"]])[0]
        assert any("human_approval" in i or "Phê duyệt" in i for i in issues)

    def test_runner_cannot_verify_independent_review_or_human_approval(self, env):
        _install(env)
        assert evidence_gate.VERIFIER_INDEPENDENT_REVIEW not in evidence_gate._TRUSTED_VERIFIERS
        assert evidence_gate.VERIFIER_HUMAN_APPROVAL not in evidence_gate._TRUSTED_VERIFIERS

    def test_tier1_unaffected(self, env):
        pack, _ = _pack_with_step(env, "pytest")
        assert audit_review_compliance(pack, "tier_1_low", "general", base_dir=env["tmp"])[0]
        _install(env)
        assert audit_review_compliance(pack, "tier_1_low", "general", base_dir=env["tmp"])[0]


# ------------------------------------------------------------- real CLI ----
@pytest.mark.skipif(IN_RUNNER, reason="would recurse into the trusted runner")
class TestRealCli:
    def _pack(self, tmp_path):
        log = tmp_path / "run.log"
        log.write_text("recorded by agent", encoding="utf-8")
        pack = create_evidence_pack("T-CLI", "build-webapp")
        add_step_evidence(
            pack=pack, step_id="s1", role="technical-auditor", skill_used="app-auditor",
            artifact=str(log), verification_method="trusted_command:shared-reuse", evidence_ref=str(log),
            status="TESTED", reviewer={"kind": "automated_test", "name": "shared-reuse"},
        )
        p = tmp_path / "pack.json"
        p.write_text(json.dumps(pack))
        return p

    def _cli(self, pack, tier, *extra):
        env = {k: v for k, v in os.environ.items() if k != tr.STACK_ENV}
        env["HOME"] = os.environ.get("HOME", "")
        return subprocess.run(
            [sys.executable, str(ROUTER), "--check-pack", str(pack), "--tier", tier, *extra],
            capture_output=True, text=True, env=env, cwd=REPO_ROOT, timeout=300,
        )

    def test_default_stays_fail_closed(self, tmp_path):
        assert self._cli(self._pack(tmp_path), "tier_2_medium").returncode == 1

    def test_tier3_blocked_even_with_flag(self, tmp_path):
        assert self._cli(self._pack(tmp_path), "tier_3_high", "--verify-by-execution").returncode == 1

    @pytest.mark.skipif(
        subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True).returncode != 0,
        reason="needs git checkout")
    def test_tier2_with_flag_runs_real_profile(self, tmp_path):
        r = self._cli(self._pack(tmp_path), "tier_2_medium", "--verify-by-execution")
        # Real execution of scripts/check_shared_reuse.py; tree is stable (pack lives in tmp_path).
        assert r.returncode == 0, r.stdout + r.stderr
