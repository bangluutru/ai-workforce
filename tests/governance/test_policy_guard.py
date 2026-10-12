#!/usr/bin/env python3
"""tests/governance/test_policy_guard.py - pre-commit guard for the Tier 3 allowlist policy file.

The guard is NOT a security boundary (hook can be bypassed with --no-verify); these tests only prove
it fails closed and has no in-repo bypass.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD = REPO_ROOT / "scripts" / "check_policy_files.py"
POLICY = ".agents/skills/_shared/governance/trusted_commands.json"
HOOK = REPO_ROOT / "scripts" / "hooks" / "pre-commit"


def _git(root, *a):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
                   cwd=root, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "r"
    (root / Path(POLICY).parent).mkdir(parents=True)
    (root / POLICY).write_text('{"version": 1}\n')
    (root / "other.txt").write_text("a")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _guard(root, **env):
    e = dict(os.environ)
    e.update(env)
    return subprocess.run([sys.executable, str(GUARD), "--repo", str(root)], capture_output=True, text=True, env=e)


def test_unrelated_change_passes(repo):
    (repo / "other.txt").write_text("b")
    _git(repo, "add", "-A")
    assert _guard(repo).returncode == 0


def test_no_changes_passes(repo):
    assert _guard(repo).returncode == 0


def test_modify_blocked(repo):
    (repo / POLICY).write_text('{"version": 1, "profiles": {"x": 1}}\n')
    _git(repo, "add", "-A")
    r = _guard(repo)
    assert r.returncode == 1 and POLICY in r.stderr and "not a security boundary" in r.stderr


def test_delete_blocked(repo):
    (repo / POLICY).unlink()
    _git(repo, "add", "-A")
    assert _guard(repo).returncode == 1


def test_add_blocked(tmp_path):
    root = tmp_path / "r2"
    root.mkdir()
    (root / "o.txt").write_text("a")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "i")
    (root / Path(POLICY).parent).mkdir(parents=True)
    (root / POLICY).write_text("{}")
    _git(root, "add", "-A")
    assert _guard(root).returncode == 1


def test_mode_change_blocked(repo):
    os.chmod(repo / POLICY, 0o755)
    _git(repo, "add", "-A")
    assert _guard(repo).returncode == 1


def test_unstaged_edit_does_not_block_but_staged_rename_does(repo):
    (repo / POLICY).write_text("{}")  # unstaged: commit would not include it
    assert _guard(repo).returncode == 0
    _git(repo, "checkout", "--", POLICY)
    _git(repo, "mv", POLICY, "moved.json")  # staged delete of protected path
    assert _guard(repo).returncode == 1


@pytest.mark.parametrize("env", [
    {"AIWF_POLICY_APPROVED": "1"}, {"POLICY_CHANGE_APPROVED": "true"}, {"SKIP_POLICY_GUARD": "1"},
    {"AIWF_APPROVAL_TOKEN": "abc"}, {"CI": "true"}, {"GIT_AUTHOR_NAME": "approver"},
])
def test_env_vars_cannot_bypass(repo, env):
    (repo / POLICY).write_text('{"changed": true}')
    _git(repo, "add", "-A")
    assert _guard(repo, **env).returncode == 1


def test_approval_token_file_cannot_bypass(repo):
    (repo / POLICY).write_text('{"changed": true}')
    for name in ("policy_approval.json", ".policy-approved", "APPROVED"):
        (repo / name).write_text('{"approved": true, "approver": "agent"}')
    _git(repo, "add", "-A")
    assert _guard(repo).returncode == 1


def test_non_git_directory_fails_closed(tmp_path):
    assert _guard(tmp_path).returncode == 2


def test_hook_wires_the_guard_and_fails_closed_if_missing():
    text = HOOK.read_text(encoding="utf-8")
    assert "check_policy_files.py" in text
    assert 'if [ ! -f "$POLICY_GUARD" ]; then' in text
    assert 'python3 "$POLICY_GUARD" || exit 1' in text
    block = text.split('if [ ! -f "$POLICY_GUARD" ]; then')[1].split("\nfi\n")[0]
    assert "exit 1" in block
    assert subprocess.run(["sh", "-n", str(HOOK)]).returncode == 0
