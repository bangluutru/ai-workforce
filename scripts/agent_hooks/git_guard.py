#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
git_guard.py - chặn lệnh git phá dữ liệu/lịch sử TRƯỚC khi agent chạy (Luật R1).

Một script, hai host, cùng một bộ luật:

- Claude Code: hook PreToolUse trong `.claude/settings.json`.
  stdin: {"tool_name": "Bash", "tool_input": {"command": "..."}}
  Chặn = thoát mã 2, lý do ghi ra stderr (Claude đọc được).
- Antigravity IDE: hook PreToolUse trong `.agents/hooks.json`.
  stdin: {"toolCall": {"name": "run_command", "args": {"CommandLine": "..."}}}
  Trả JSON ra stdout: {"decision": "deny" | "allow", "reason": "..."}, thoát mã 0.

Bị chặn:
  reset --hard · push ép (--force, -f, --force-with-lease, +refspec, --mirror)
  · push xóa nhánh từ xa (--delete, -d, :nhánh) · clean -f · branch -D / --delete --force
  · checkout/restore cả cây (`.`, `:/`, `*`) · checkout -f · switch --discard-changes / -f
  · stash drop / clear · filter-branch / filter-repo · reflog expire / delete
  · update-ref -d · gc --prune=now · rm -r .git

Được phép (cố ý): push thường, rebase, commit --amend, branch -d (xóa an toàn),
restore một file cụ thể (R1 dùng nó để phục hồi), restore --staged (chỉ bỏ stage).

Kiểm tra tay:
    python3 scripts/agent_hooks/git_guard.py --check "git reset --hard HEAD~1"

GIỚI HẠN (khai báo trung thực): đây là lan can chống thao tác nhầm, KHÔNG phải ranh
giới bảo mật. Agent hoặc người cố tình vẫn vượt được (sửa hook, viết lệnh qua script
trung gian, mã hóa chuỗi lệnh). Người dùng tự gõ lệnh trong terminal không bị chặn.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from typing import List, Optional

SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", "{", "}", "|&", ";;"}
WRAPPERS = {
    "sudo", "env", "command", "exec", "nohup", "time", "nice", "xargs",
    "timeout", "then", "do", "else", "!", "builtin",
}
GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
WHOLE_TREE = {".", "./", ":/", ":/.", "*", ":(top)"}

HUONG_DAN = (
    "Theo Luật R1, agent không tự chạy lệnh này. Nếu thật sự cần: tạo checkpoint "
    "(git tag/branch) rồi hỏi người dùng để họ tự chạy."
)


def _short_flags(args: List[str]) -> str:
    """Gộp các cụm cờ ngắn (-fd, -fu) thành một chuỗi ký tự cờ."""
    out = []
    for a in args:
        if a == "--":
            break
        if re.fullmatch(r"-[A-Za-z]+", a):
            out.append(a[1:])
    return "".join(out)


def _pathspecs(args: List[str]) -> List[str]:
    """Đối số sau `--`, hoặc mọi đối số không phải cờ nếu không có `--`."""
    if "--" in args:
        return args[args.index("--") + 1:]
    return [a for a in args if not a.startswith("-")]


def _rule(sub: str, args: List[str]) -> Optional[str]:
    flags = _short_flags(args)
    long = set(a.split("=", 1)[0] for a in args if a.startswith("--"))

    if sub == "reset" and "--hard" in long:
        return "git reset --hard xóa thay đổi chưa commit và có thể làm mất commit"

    if sub == "push":
        if long & {"--force", "--force-with-lease", "--force-if-includes", "--mirror"} or "f" in flags:
            return "push ép (force) ghi đè lịch sử trên remote"
        if any(a.startswith("+") and len(a) > 1 for a in args):
            return "push với refspec '+' là push ép, ghi đè lịch sử trên remote"
        if "--delete" in long or "d" in flags or any(a.startswith(":") and len(a) > 1 for a in args):
            return "push xóa nhánh/tag trên remote"

    if sub == "clean" and ("--force" in long or "f" in flags):
        return "git clean -f xóa vĩnh viễn file chưa được git theo dõi"

    if sub == "branch":
        if "D" in flags:
            return "git branch -D xóa nhánh kể cả khi chưa merge"
        if ("--delete" in long or "d" in flags) and ("--force" in long or "f" in flags):
            return "xóa nhánh ép buộc (--delete --force) có thể làm mất commit"

    if sub == "checkout":
        if "--force" in long or "f" in flags:
            return "git checkout -f bỏ toàn bộ thay đổi chưa commit"
        if any(p in WHOLE_TREE for p in _pathspecs(args)):
            return "git checkout cả cây làm việc bỏ toàn bộ thay đổi chưa commit"

    if sub == "restore":
        only_staged = ("--staged" in long or "S" in flags) and not ("--worktree" in long or "W" in flags)
        if not only_staged and any(p in WHOLE_TREE for p in _pathspecs(args)):
            return "git restore cả cây làm việc bỏ toàn bộ thay đổi chưa commit"

    if sub == "switch" and ("--discard-changes" in long or "--force" in long or "f" in flags):
        return "git switch --discard-changes/-f bỏ thay đổi chưa commit"

    if sub == "stash" and args and args[0] in ("drop", "clear"):
        return f"git stash {args[0]} xóa vĩnh viễn công việc đang cất trong stash"

    if sub in ("filter-branch", "filter-repo"):
        return f"git {sub} viết lại toàn bộ lịch sử"

    if sub == "reflog" and args and args[0] in ("expire", "delete"):
        return "xóa reflog làm mất đường phục hồi commit"

    if sub == "update-ref" and ("-d" in args or "--delete" in long):
        return "git update-ref -d xóa tham chiếu trực tiếp"

    if sub == "gc" and any(a in ("--prune=now", "--prune=all") for a in args):
        return "git gc --prune=now xóa ngay các object không còn tham chiếu"

    return None


def _strip_wrappers(tokens: List[str]) -> List[str]:
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", t):
            i += 1
        elif t in WRAPPERS:
            i += 1
            while i < len(tokens) and (tokens[i].startswith("-") or re.fullmatch(r"\d+[smhd]?", tokens[i])):
                i += 1
        else:
            break
    return tokens[i:]


def _check_segment(tokens: List[str], depth: int) -> Optional[str]:
    # Chuỗi lệnh lồng: bash -c "...", sh -lc '...', eval "..."
    for idx, t in enumerate(tokens[:-1]):
        if re.fullmatch(r"-[a-z]*c", t) or t == "eval":
            nested = check(tokens[idx + 1], depth + 1)
            if nested:
                return nested

    cmd = _strip_wrappers(tokens)
    if not cmd:
        return None
    prog = os.path.basename(cmd[0])

    if prog == "rm":
        flags = _short_flags(cmd[1:])
        recursive = "r" in flags or "R" in flags or "--recursive" in cmd
        if recursive and any(os.path.basename(a.rstrip("/")) == ".git" for a in cmd[1:]):
            return "xóa thư mục .git là xóa toàn bộ lịch sử repo"
        return None

    if prog != "git":
        return None

    rest = cmd[1:]
    i = 0
    while i < len(rest) and rest[i].startswith("-"):
        opt = rest[i]
        i += 2 if (opt in GIT_VALUE_OPTS and "=" not in opt) else 1
    if i >= len(rest):
        return None
    reason = _rule(rest[i], rest[i + 1:])
    return f"{reason}: `{' '.join(cmd)}`" if reason else None


def _tokenize(command: str) -> List[List[str]]:
    lex = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=";&|(){}")
    lex.whitespace_split = True
    lex.commenters = ""
    segments, cur = [], []
    for tok in lex:
        if tok in SEPARATORS or (tok and set(tok) <= set(";&|(){}")):
            if cur:
                segments.append(cur)
            cur = []
        else:
            cur.append(tok)
    if cur:
        segments.append(cur)
    return segments


FALLBACK = re.compile(
    r"\bgit\b[^;&|\n]*\b("
    r"reset\s+[^;&|\n]*--hard|push\s+[^;&|\n]*(--force|--mirror|\s-[a-z]*f)|"
    r"clean\s+[^;&|\n]*(-[a-z]*f|--force)|branch\s+[^;&|\n]*-[a-z]*D|"
    r"stash\s+(drop|clear)|filter-branch|filter-repo)"
)


def check(command: str, depth: int = 0) -> Optional[str]:
    """Trả lý do chặn, hoặc None nếu được phép."""
    if not command or depth > 3:
        return None
    try:
        segments = _tokenize(command)
    except ValueError:
        # Dấu nháy không cân: không phân tích được thì dò bằng regex, nghiêng về chặn.
        return "lệnh git nguy hiểm (không phân tích được cú pháp, dò bằng mẫu)" if FALLBACK.search(command) else None
    for seg in segments:
        reason = _check_segment(seg, depth)
        if reason:
            return reason
    return None


def main(argv: List[str]) -> int:
    if len(argv) >= 2 and argv[0] == "--check":
        reason = check(" ".join(argv[1:]))
        print(f"BỊ CHẶN: {reason}" if reason else "ĐƯỢC PHÉP")
        return 1 if reason else 0

    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}

    if "toolCall" in data:  # Antigravity
        args = (data.get("toolCall") or {}).get("args") or {}
        command = args.get("CommandLine") or args.get("command") or ""
        reason = check(command) if isinstance(command, str) else None
        out = {"decision": "deny", "reason": f"git_guard: {reason}. {HUONG_DAN}"} if reason else {"decision": "allow"}
        print(json.dumps(out, ensure_ascii=False))
        return 0

    command = (data.get("tool_input") or {}).get("command") or ""  # Claude Code
    reason = check(command) if isinstance(command, str) else None
    if reason:
        print(f"BLOCKED by git_guard: {reason}. {HUONG_DAN}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
