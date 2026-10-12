#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_policy_files.py - pre-commit guard cho file chinh sach (Tier 3).

Moi thay doi (them/sua/xoa/doi kieu) toi
  .agents/skills/_shared/governance/trusted_commands.json
la thay doi chinh sach Tier 3. Guard nay CHAN commit (fail closed).

GIOI HAN (khai bao trung thuc):
- Hien KHONG co co che uy quyen ben ngoai co the cuong che duoc. Guard khong co
  bypass bang bien moi truong, co hay token; khong co co che tu phe duyet.
- Hook KHONG phai ranh gioi bao mat: `git commit --no-verify` hoac sua hook se
  vo hieu hoa no. Chi review thu cong ben ngoai (PR/nguoi) moi la kiem soat that.

Ma thoat: 0 = khong dung toi file chinh sach, 1 = bi chan, 2 = loi chay (cung chan).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROTECTED = (".agents/skills/_shared/governance/trusted_commands.json",)


def staged_changes(repo: Path):
    proc = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--name-status", "--no-renames", "-z"],
        capture_output=True, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or "git diff failed")
    parts = proc.stdout.decode("utf-8", "surrogateescape").split("\0")
    parts = [p for p in parts if p != ""]
    if len(parts) % 2:
        raise RuntimeError("unexpected git diff output")
    return list(zip(parts[0::2], parts[1::2]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    args = ap.parse_args(argv)
    try:
        changes = staged_changes(Path(args.repo))
    except Exception as exc:  # fail closed
        print(f"BLOCKED: policy guard error: {exc}", file=sys.stderr)
        return 2
    hits = [(s, p) for s, p in changes if p in PROTECTED]
    if not hits:
        return 0
    print("BLOCKED: staged change to a Tier 3 policy file:", file=sys.stderr)
    for status, path in hits:
        print(f"  [{status}] {path}", file=sys.stderr)
    print(
        "This requires external authorization and manual review. No in-repo approval\n"
        "mechanism exists. NOTE: this hook is not a security boundary.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
