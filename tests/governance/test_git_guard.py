#!/usr/bin/env python3
"""tests/governance/test_git_guard.py - lan can chặn lệnh git phá dữ liệu (Luật R1).

Guard KHÔNG phải ranh giới bảo mật. Test chỉ chứng minh: (1) chặn đúng các lệnh phá
dữ liệu/lịch sử thường gặp, (2) không chặn nhầm lệnh git hằng ngày, (3) đúng giao thức
hook của cả Claude Code (mã 2 + stderr) và Antigravity (JSON decision ra stdout).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD = REPO_ROOT / "scripts" / "agent_hooks" / "git_guard.py"
INSTALLER = REPO_ROOT / "scripts" / "agent_hooks" / "install_global.py"

sys.path.insert(0, str(GUARD.parent))
import git_guard  # noqa: E402

BLOCKED = [
    "git reset --hard",
    "git reset --hard HEAD~3",
    "git -C /tmp/repo reset --hard origin/main",
    "cd sub && git reset --hard",
    "git status; git reset --hard",
    "git push --force",
    "git push -f origin main",
    "git push -fu origin main",
    "git push --force-with-lease origin feat",
    "git push origin +main",
    "git push --mirror backup",
    "git push origin --delete feat",
    "git push origin :feat",
    "git clean -fd",
    "git clean -xdf",
    "git clean --force",
    "git branch -D feat",
    "git branch --delete --force feat",
    "git checkout .",
    "git checkout -- .",
    "git checkout -f main",
    "git restore .",
    "git restore --worktree --staged .",
    "git switch --discard-changes main",
    "git stash drop",
    "git stash clear",
    "git filter-branch --tree-filter x HEAD",
    "git filter-repo --path secret",
    "git reflog expire --expire=now --all",
    "git update-ref -d refs/heads/feat",
    "git gc --prune=now",
    "rm -rf .git",
    "rm -r ./.git/",
    'bash -c "git reset --hard"',
    "sh -lc 'git push -f'",
    'eval "git clean -fd"',
    "sudo git reset --hard",
    "GIT_TRACE=1 git push --force",
    "timeout 30 git push -f",
    "git status\ngit reset --hard",
    "/usr/bin/git reset --hard",
]

ALLOWED = [
    "git status",
    "git log --oneline -5",
    "git diff HEAD~1",
    "git add -A",
    'git commit -m "sửa lỗi reset --hard trong tài liệu"',
    "git push",
    "git push -u origin feat/chat-van",
    "git pull --rebase",
    "git fetch origin main",
    "git rebase origin/main",
    "git commit --amend --no-edit",
    "git branch -d merged-feature",
    "git checkout main",
    "git checkout -b feat/x",
    "git switch -c feat/x",
    "git restore src/app.py",
    "git restore --staged .",
    "git stash",
    "git stash pop",
    "git clean -n",
    "git tag checkpoint/truoc-sua HEAD",
    'echo "git reset --hard"',
    "grep -r 'push --force' docs/",
    "rm -rf _process/tmp",
    "rm .gitignore.bak",
    "ls -la",
    "",
]


@pytest.mark.parametrize("cmd", BLOCKED)
def test_blocks_destructive(cmd):
    assert git_guard.check(cmd), f"phải chặn: {cmd!r}"


@pytest.mark.parametrize("cmd", ALLOWED)
def test_allows_everyday(cmd):
    assert git_guard.check(cmd) is None, f"chặn nhầm: {cmd!r} -> {git_guard.check(cmd)}"


def test_unbalanced_quotes_fall_back_to_pattern():
    assert git_guard.check("git reset --hard 'oops")
    assert git_guard.check("echo 'oops") is None


def _run(payload):
    return subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=30)


def test_claude_protocol_block():
    r = _run({"tool_name": "Bash", "tool_input": {"command": "git push --force"}})
    assert r.returncode == 2
    assert "git_guard" in r.stderr


def test_claude_protocol_allow():
    r = _run({"tool_name": "Bash", "tool_input": {"command": "git status"}})
    assert r.returncode == 0 and r.stderr == ""


def test_antigravity_protocol_block():
    r = _run({"toolCall": {"name": "run_command", "args": {"CommandLine": "git reset --hard", "Cwd": "/x"}}})
    assert r.returncode == 0
    assert json.loads(r.stdout)["decision"] == "deny"


def test_antigravity_protocol_allow():
    r = _run({"toolCall": {"name": "run_command", "args": {"CommandLine": "git status"}}})
    assert json.loads(r.stdout) == {"decision": "allow"}


def test_garbage_stdin_does_not_block():
    r = subprocess.run([sys.executable, str(GUARD)], input="not json", capture_output=True, text=True)
    assert r.returncode == 0


def test_repo_configs_point_to_guard():
    claude = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
    cmd = claude["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "scripts/agent_hooks/git_guard.py" in cmd
    ag = json.loads((REPO_ROOT / ".agents" / "hooks.json").read_text())
    h = ag["aiwf-git-guard"]["PreToolUse"][0]
    assert h["matcher"] == "run_command"
    assert "scripts/agent_hooks/git_guard.py" in h["hooks"][0]["command"]


def _install(home, *a):
    return subprocess.run([sys.executable, str(INSTALLER), "--home", str(home), *a],
                          capture_output=True, text=True, timeout=30)


def test_installer_dry_run_writes_nothing(tmp_path):
    r = _install(tmp_path)
    assert r.returncode == 0
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".gemini").exists()


def test_installer_preserves_existing_config_and_is_idempotent(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    existing = {"model": "opus", "hooks": {"PreToolUse": [
        {"matcher": "Edit", "hooks": [{"type": "command", "command": "lint.sh"}]}]}}
    settings.write_text(json.dumps(existing))

    assert _install(tmp_path, "--apply").returncode == 0
    data = json.loads(settings.read_text())
    assert data["model"] == "opus"
    cmds = [h["command"] for e in data["hooks"]["PreToolUse"] for h in e["hooks"]]
    assert "lint.sh" in cmds and sum("git_guard.py" in c for c in cmds) == 1
    assert list(settings.parent.glob("settings.json.bak-*")), "phải có bản sao lưu"

    assert "không cần thay đổi" in _install(tmp_path, "--apply").stdout
    ag = json.loads((tmp_path / ".gemini" / "config" / "hooks.json").read_text())
    assert ag["aiwf-git-guard"]["enabled"] is True

    assert _install(tmp_path, "--uninstall", "--apply").returncode == 0
    data = json.loads(settings.read_text())
    cmds = [h["command"] for e in data["hooks"]["PreToolUse"] for h in e["hooks"]]
    assert cmds == ["lint.sh"]
    assert "aiwf-git-guard" not in json.loads((tmp_path / ".gemini" / "config" / "hooks.json").read_text())


def test_installer_refuses_broken_json(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text("{broken")
    r = _install(tmp_path, "--apply")
    assert r.returncode == 2
    assert settings.read_text() == "{broken"
    assert not (tmp_path / ".gemini").exists()
