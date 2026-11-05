#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_global.py - bật git_guard cho MỌI repo trên máy (không chỉ AIWF).

Trong repo AIWF, guard đã tự bật qua `.claude/settings.json` và `.agents/hooks.json`
(git track, không cần cài). Script này chỉ dành cho các repo khác (Docs Manager,
Toolio, JLPT Guru...): nó thêm hook vào cấu hình toàn cục, trỏ tới git_guard.py của
bản AIWF trên máy này.

  Claude Code  : ~/.claude/settings.json      (hooks.PreToolUse, matcher "Bash")
  Antigravity  : ~/.gemini/config/hooks.json  (hook "aiwf-git-guard", matcher "run_command")

Mặc định chỉ IN ra thay đổi, không ghi. Ghi thật phải có --apply.
Trước khi ghi luôn sao lưu file cũ thành <file>.bak-<thời_gian>. Chạy lại nhiều lần
không tạo hook trùng. --uninstall gỡ đúng hook này, giữ nguyên mọi cấu hình khác.

    python3 scripts/agent_hooks/install_global.py              # xem trước
    python3 scripts/agent_hooks/install_global.py --apply      # cài
    python3 scripts/agent_hooks/install_global.py --uninstall --apply
"""
from __future__ import annotations

import argparse
import datetime
import json
import shutil
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent / "git_guard.py"
MARK = "git_guard.py"
AG_NAME = "aiwf-git-guard"


def _command() -> str:
    return f'python3 "{GUARD}"'


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    data = json.loads(text)  # JSON hỏng thì dừng, không ghi đè cấu hình người dùng
    if not isinstance(data, dict):
        raise ValueError(f"{path} không phải object JSON")
    return data


def claude_apply(data: dict, uninstall: bool) -> dict:
    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    kept = []
    for entry in pre:
        handlers = [h for h in entry.get("hooks", []) if MARK not in str(h.get("command", ""))]
        if handlers:
            kept.append({**entry, "hooks": handlers})
    if not uninstall:
        kept.append({"matcher": "Bash", "hooks": [{"type": "command", "command": _command(), "timeout": 10}]})
    hooks["PreToolUse"] = kept
    if not kept:
        del hooks["PreToolUse"]
    if not hooks:
        del data["hooks"]
    return data


def antigravity_apply(data: dict, uninstall: bool) -> dict:
    data.pop(AG_NAME, None)
    if not uninstall:
        data[AG_NAME] = {
            "enabled": True,
            "PreToolUse": [{
                "matcher": "run_command",
                "hooks": [{"type": "command", "command": _command(), "timeout": 10}],
            }],
        }
    return data


def plan(path: Path, fn, uninstall: bool):
    before = _load(path)
    after = fn(json.loads(json.dumps(before)), uninstall)
    return None if before == after else after


def write(path: Path, after: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = path.with_name(f"{path.name}.bak-{stamp}")
        shutil.copy2(path, backup)
        print(f"  sao lưu: {backup}")
    path.write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  đã ghi")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Bật/gỡ git_guard toàn cục cho Claude Code và Antigravity.")
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ xem trước)")
    ap.add_argument("--uninstall", action="store_true", help="gỡ hook git_guard")
    ap.add_argument("--only", choices=["claude", "antigravity"], help="chỉ xử lý một host")
    ap.add_argument("--home", default=str(Path.home()), help=argparse.SUPPRESS)  # dùng cho test
    args = ap.parse_args(argv)

    home = Path(args.home)
    targets = {
        "claude": (home / ".claude" / "settings.json", claude_apply),
        "antigravity": (home / ".gemini" / "config" / "hooks.json", antigravity_apply),
    }
    changes = []
    try:  # tính hết trước, ghi sau: một file JSON hỏng thì không file nào bị ghi
        for name, (path, fn) in targets.items():
            if args.only and args.only != name:
                continue
            changes.append((path, plan(path, fn, args.uninstall)))
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"DỪNG: {exc}. Không ghi gì cả; sửa file JSON trước.", file=sys.stderr)
        return 2
    for path, after in changes:
        if after is None:
            print(f"= {path}: không cần thay đổi")
            continue
        print(f"~ {path}:")
        print(json.dumps(after, ensure_ascii=False, indent=2))
        if args.apply:
            write(path, after)
    if not args.apply:
        print("\n(Xem trước. Thêm --apply để ghi.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
