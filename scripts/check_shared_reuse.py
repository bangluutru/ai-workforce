#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_shared_reuse.py — Cưỡng chế Luật R7 (Shared-Engine-First) cho AI Workforce.

Phát hiện:
  R7-DUP    (FAIL) file giống từng byte ở ≥ 2 chủ sở hữu (skill A, skill B, _shared, scripts/)
  R7-ASSET  (FAIL) font/model nhị phân trùng hash ở ≥ 2 chủ sở hữu
  R7-SIG    (FAIL) chữ ký của engine đã đăng ký trong _shared/engines.json xuất hiện ngoài module sở hữu
  R7-BAN    (FAIL) dùng engine bị cấm (engines.json → banned)
  R7-NEAR   (WARN) file cùng tên ở ≥ 2 skill, nội dung giống ≥ 80 % (dấu hiệu fork)
  R7-SHIM   (WARN) shim chuyển tiếp quá 30 dòng hoặc thiếu dòng "# R7-SHIM"
  R7-DECL   (WARN) skill gọi engine _shared nhưng SKILL.md thiếu mục "Engine dùng chung"

Cách dùng:
  python3 scripts/check_shared_reuse.py                 # báo cáo toàn bộ
  python3 scripts/check_shared_reuse.py --skill phu-de  # chỉ lỗi liên quan một skill
  python3 scripts/check_shared_reuse.py --json          # xuất JSON
  python3 scripts/check_shared_reuse.py --quiet         # chỉ in khi có FAIL (pre-commit)

Mã thoát: 0 = không có FAIL, 1 = có FAIL, 2 = lỗi chạy (vd: engines.json hỏng).
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
SKILLS = WORKSPACE / ".agents" / "skills"
SHARED = SKILLS / "_shared"
REGISTRY = SHARED / "engines.json"

EXCLUDE_DIRS = {"node_modules", "__pycache__", ".venv", ".venv-tts", "models", ".git", "dist", "build",
                ".pytest_cache"}
CODE_EXT = {".py", ".js", ".mjs", ".ts", ".sh"}
ASSET_EXT = {".ttf", ".otf", ".woff", ".woff2", ".onnx", ".bin", ".pt", ".safetensors"}
DUP_EXT = CODE_EXT | {".md", ".json", ".html", ".css", ".txt", ".yaml", ".yml", ".typ"}
MIN_DUP_BYTES = 200          # bỏ qua file rất nhỏ (__init__.py rỗng, config 1 dòng)
NEAR_RATIO = 0.80
SHIM_MAX_LINES = 30
SELF = Path(__file__).resolve()
DECL_USE_RE = re.compile(r"_shared|doc_ingest_bridge")
DECL_HEADING_RE = re.compile(r"^#{2,3}\s.*Engine dùng chung", re.MULTILINE)


def owner_of(path: Path) -> str:
    """Chủ sở hữu logic của một file: tên skill, '_shared' hoặc 'scripts'."""
    rel = path.resolve().relative_to(WORKSPACE)
    parts = rel.parts
    if parts[:2] == (".agents", "skills") and len(parts) > 3:
        return parts[2]
    if parts[0] == "scripts":
        return "scripts"
    return parts[0]


def iter_files(roots):
    for root in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
            for fn in filenames:
                p = Path(dirpath) / fn
                if p.resolve() == SELF:
                    continue
                yield p


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry() -> dict:
    if not REGISTRY.exists():
        return {"engines": [], "banned": []}
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"❌ engines.json không hợp lệ: {e}", file=sys.stderr)
        sys.exit(2)
    data.setdefault("engines", [])
    data.setdefault("banned", [])
    return data


def rel(p: Path) -> str:
    return str(p.resolve().relative_to(WORKSPACE))


def scan() -> list[dict]:
    findings: list[dict] = []
    reg = load_registry()
    roots = [SKILLS, WORKSPACE / "scripts"]
    files = [p for p in iter_files(roots) if p.is_file()]

    # ---------------- R7-DUP / R7-ASSET
    by_hash: dict[str, list[Path]] = defaultdict(list)
    for p in files:
        ext = p.suffix.lower()
        if ext not in DUP_EXT and ext not in ASSET_EXT:
            continue
        try:
            if p.stat().st_size < MIN_DUP_BYTES:
                continue
            by_hash[md5(p)].append(p)
        except OSError as e:
            print(f"⚠️ Không đọc được {rel(p)}: {e}", file=sys.stderr)
    for h, group in by_hash.items():
        owners = sorted({owner_of(p) for p in group})
        if len(owners) < 2:
            continue
        is_asset = group[0].suffix.lower() in ASSET_EXT
        findings.append({
            "code": "R7-ASSET" if is_asset else "R7-DUP",
            "level": "FAIL",
            "owners": owners,
            "files": sorted(rel(p) for p in group),
            "message": ("Asset nhị phân trùng — chuyển vào _shared/fonts|models" if is_asset
                        else "File giống từng byte ở nhiều nơi — chuyển vào _shared/ và gọi lại"),
        })

    code_files = [p for p in files if p.suffix.lower() in CODE_EXT]
    texts: dict[Path, str] = {}
    for p in code_files:
        try:
            texts[p] = p.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            print(f"⚠️ Không đọc được {rel(p)}: {e}", file=sys.stderr)

    # ---------------- R7-SIG
    for eng in reg["engines"]:
        module = (SHARED / eng["module"]).resolve()
        owned = [module]   # file module, hoặc thư mục package (mọi file con đều thuộc engine)
        for sig in eng.get("signatures", []):
            rx = re.compile(sig, re.M)
            for p, t in texts.items():
                rp = p.resolve()
                if any(rp == o or o in rp.parents for o in owned):
                    continue
                if any(rp == (SHARED / a).resolve() for a in eng.get("allow", [])):
                    continue
                m = rx.search(t)
                if m:
                    line = t.count("\n", 0, m.start()) + 1
                    findings.append({
                        "code": "R7-SIG", "level": "FAIL", "owners": [owner_of(p)],
                        "files": [f"{rel(p)}:{line}"],
                        "message": f"Viết lại engine '{eng['id']}' (đã có tại _shared/{eng['module']}) — hãy import/gọi lại",
                    })

    # ---------------- R7-BAN (code + requirements + shell)
    ban_targets = dict(texts)
    for p in files:
        if p.name.startswith("requirements") and p.suffix == ".txt":
            ban_targets[p] = p.read_text(encoding="utf-8", errors="ignore")
    req_root = WORKSPACE / "requirements.txt"
    if req_root.exists():
        ban_targets[req_root] = req_root.read_text(encoding="utf-8", errors="ignore")
    for ban in reg["banned"]:
        for pat in ban.get("patterns", []):
            rx = re.compile(pat, re.M)
            for p, t in ban_targets.items():
                for m in rx.finditer(t):
                    line_start = t.rfind("\n", 0, m.start()) + 1
                    line_txt = t[line_start:t.find("\n", m.start()) if t.find("\n", m.start()) != -1 else len(t)]
                    if "R7-ALLOW-BANNED-MENTION" in line_txt:
                        continue
                    line = t.count("\n", 0, m.start()) + 1
                    findings.append({
                        "code": "R7-BAN", "level": "FAIL", "owners": [owner_of(p)],
                        "files": [f"{rel(p)}:{line}"],
                        "message": f"Engine bị cấm '{ban['id']}': {ban.get('reason', '')} → dùng {ban.get('replacement', '')}",
                    })
                    break   # một lỗi mỗi file mỗi pattern là đủ

    # ---------------- R7-NEAR
    by_name: dict[str, list[Path]] = defaultdict(list)
    for p in texts:
        if p.name == "__init__.py":
            continue
        by_name[p.name].append(p)
    dup_files = {f for fd in findings if fd["code"] == "R7-DUP" for f in fd["files"]}
    for name, group in by_name.items():
        if len({owner_of(p) for p in group}) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if owner_of(a) == owner_of(b) or rel(a) in dup_files and rel(b) in dup_files:
                    continue
                la, lb = texts[a].splitlines(), texts[b].splitlines()
                if not la or not lb:
                    continue
                sm = difflib.SequenceMatcher(None, la, lb, autojunk=False)
                if sm.real_quick_ratio() < NEAR_RATIO or sm.quick_ratio() < NEAR_RATIO:
                    continue
                r = sm.ratio()
                if r >= NEAR_RATIO:
                    findings.append({
                        "code": "R7-NEAR", "level": "WARN", "owners": sorted({owner_of(a), owner_of(b)}),
                        "files": [rel(a), rel(b)],
                        "message": f"Hai bản '{name}' giống {r:.0%} — có thể là fork, nên hợp nhất vào _shared/",
                    })

    # ---------------- R7-SHIM
    for p, t in texts.items():
        if "R7-SHIM" not in t[:400]:
            continue
        n = t.count("\n") + 1
        if n > SHIM_MAX_LINES:
            findings.append({
                "code": "R7-SHIM", "level": "WARN", "owners": [owner_of(p)], "files": [rel(p)],
                "message": f"Shim dài {n} dòng (> {SHIM_MAX_LINES}) — shim chỉ được chuyển tiếp sang _shared",
            })

    # ---------------- R7-DECL
    uses_shared: set[str] = set()
    for p, t in texts.items():
        o = owner_of(p)
        if o in ("_shared", "scripts") or not (SKILLS / o).is_dir():
            continue
        if DECL_USE_RE.search(t):
            uses_shared.add(o)
    for o in sorted(uses_shared):
        skill_md = SKILLS / o / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            md = skill_md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"⚠️ Không đọc được {rel(skill_md)}: {e}", file=sys.stderr)
            continue
        if not DECL_HEADING_RE.search(md):
            findings.append({
                "code": "R7-DECL", "level": "WARN", "owners": [o], "files": [rel(skill_md)],
                "message": "Skill gọi engine _shared nhưng SKILL.md chưa có mục '## … Engine dùng chung' (R7 §6.1)",
            })
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Kiểm tra Luật R7 — tái sử dụng engine dùng chung")
    ap.add_argument("--skill", help="Chỉ hiển thị lỗi liên quan skill này")
    ap.add_argument("--json", action="store_true", help="Xuất JSON")
    ap.add_argument("--quiet", action="store_true", help="Chỉ in khi có FAIL")
    args = ap.parse_args()

    findings = scan()
    if args.skill:
        findings = [f for f in findings if args.skill in f["owners"]]
    fails = [f for f in findings if f["level"] == "FAIL"]

    if args.json:
        print(json.dumps({"fail": len(fails), "warn": len(findings) - len(fails), "findings": findings},
                         ensure_ascii=False, indent=2))
        return 1 if fails else 0

    if args.quiet and not fails:
        return 0
    if not findings:
        print("✅ R7: không phát hiện trùng lặp / engine viết lại / engine bị cấm.")
        return 0
    for f in sorted(findings, key=lambda x: (x["level"] != "FAIL", x["code"])):
        if args.quiet and f["level"] != "FAIL":
            continue
        icon = "❌" if f["level"] == "FAIL" else "⚠️ "
        print(f"{icon} [{f['code']}] {f['message']}")
        for fp in f["files"]:
            print(f"      - {fp}")
    print(f"\nR7: {len(fails)} FAIL, {len(findings) - len(fails)} WARN "
          f"(chi tiết luật: .agents/rules/R7-shared-engine-reuse.md)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
