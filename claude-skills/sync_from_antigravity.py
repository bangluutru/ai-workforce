#!/usr/bin/env python3
"""Sinh bộ skill Claude (claude-skills/skills/<skill>/SKILL.md) từ skill Antigravity (.agents/skills/).

Skill Antigravity vẫn là nguồn sự thật duy nhất: bản Claude chỉ là lớp vỏ có
frontmatter đúng chuẩn Claude (name + description <= 1024 ký tự), bảng chuyển đổi
công cụ và hợp đồng phối hợp lấy từ claude-skills/skill-map.json. Phần quy trình chi
tiết Claude đọc thẳng từ .agents/skills/<skill>/SKILL.md lúc chạy, nên sửa skill
gốc là bản Claude dùng ngay, không cần sinh lại (trừ khi đổi description).

Chạy từ gốc workspace:
    python3 claude-skills/sync_from_antigravity.py --install  # sinh rồi cài vào .claude/skills/
    python3 claude-skills/sync_from_antigravity.py            # chỉ sinh trong claude-skills/skills/
    python3 claude-skills/sync_from_antigravity.py --check    # chỉ báo lệch, exit 1 nếu lệch

Claude Code chỉ nạp skill dự án từ .claude/skills/, nên --install chép toàn bộ
claude-skills/skills/ sang đó (ghi đè bản cài cũ của cùng tên, không xóa skill khác
trong .claude/skills/). claude-skills/ là bản gốc để sửa và commit.

Không ghi đè skill viết tay (không có dòng AUTO_MARK), không động vào .agents/.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / ".agents" / "skills"
DST = ROOT / "claude-skills" / "skills"
MAP = ROOT / "claude-skills" / "skill-map.json"
INSTALL = ROOT / ".claude" / "skills"
AUTO_MARK = "<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py"
MAX_DESC = 480


def parse_frontmatter(text):
    """Đọc frontmatter kiểu `key: value` và `key: >-` (khối gập), không cần PyYAML."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    data, key, buf = {}, None, []
    for line in m.group(1).splitlines():
        if key and (line.startswith(" ") or line.startswith("\t") or not line.strip()):
            if line.strip():
                buf.append(line.strip())
            continue
        if key:
            data[key] = buf
            key, buf = None, []
        km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not km:
            continue
        k, v = km.group(1), km.group(2).strip()
        if v in (">-", ">", "|", "|-"):
            key, buf = k, []
        else:
            data[k] = v.strip("\"'")
    if key:
        data[key] = buf
    return data


def split_description(lines):
    """Tách mô tả gốc thành (tóm tắt, USE WHEN, DO NOT USE WHEN)."""
    if isinstance(lines, str):
        lines = [lines]
    text = " ".join(lines)
    main, use, dont = text, "", ""
    m = re.search(r"DO NOT USE WHEN:\s*(.*)$", main, re.S)
    if m:
        dont, main = m.group(1).strip(), main[: m.start()]
    m = re.search(r"USE WHEN:\s*(.*)$", main, re.S)
    if m:
        use, main = m.group(1).strip(), main[: m.start()]
    return main.strip(), use, dont


def first_sentence(s):
    m = re.match(r"(.+?[.!?])(\s|$)", s)
    return m.group(1) if m else s


def clip(s, n):
    s = s.strip()
    if len(s) <= n:
        return s
    cut = s[: n - 1]
    cut = cut[: cut.rfind(" ")] if " " in cut else cut
    return cut.rstrip(",;: ") + "…"


def build_description(fm):
    """Mô tả ngắn cho Claude: Claude Code có ngân sách chung cho danh sách skill (cùng
    skill của plugin, hệ thống); mô tả dài quá thì một số skill bị rút còn mỗi tên.
    Nên giữ mỗi mô tả quanh 400 ký tự: việc chính, khi dùng, khi không dùng."""
    main, use, dont = split_description(fm.get("description", ""))
    main = clip(first_sentence(main), 170)
    use = clip(use, 130)
    dont = clip(dont, 120)
    parts = [main]
    if use:
        parts.append(f"Dùng khi: {use}")
    if dont:
        parts.append(f"Không dùng khi: {dont}")
    return clip(" ".join(parts), MAX_DESC)


def fmt_list(names):
    return ", ".join(f"`{n}`" for n in names) if names else "—"


def render(name, fm, contract, tiers):
    desc = build_description(fm)
    display = fm.get("display-name", name)
    tang = contract.get("tang", "")
    return f"""---
name: {name}
description: >-
  {desc}
---
{AUTO_MARK} từ .agents/skills/{name}/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# {display} (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/{name}/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/{name}/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/{name}/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/{name}/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | {tang} ({tiers.get(tang, "")}) |
| Đầu vào | {contract.get("vao", "—")} |
| Đầu ra | {contract.get("ra", "—")} |
| Thường nhận từ | {fmt_list(contract.get("nhan_tu", []))} |
| Thường giao cho | {fmt_list(contract.get("giao_cho", []))} |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="chỉ kiểm tra, không ghi")
    ap.add_argument("--install", action="store_true", help="sinh xong thì chép sang .claude/skills/")
    args = ap.parse_args()

    cfg = json.loads(MAP.read_text(encoding="utf-8"))
    contracts, tiers = cfg.get("skills", {}), cfg.get("tang", {})
    changed, written = [], []
    for src in sorted(SRC.glob("*/SKILL.md")):
        name = src.parent.name
        if name.startswith("_"):
            continue
        fm = parse_frontmatter(src.read_text(encoding="utf-8"))
        if fm.get("name", name) != name:
            print(f"! {name}: name trong frontmatter là '{fm.get('name')}', dùng tên thư mục")
        if name not in contracts:
            print(f"! {name}: chưa có trong skill-map.json, hợp đồng phối hợp để trống")
        out = render(name, fm, contracts.get(name, {}), tiers)
        dst = DST / name / "SKILL.md"
        if dst.exists():
            old = dst.read_text(encoding="utf-8")
            if AUTO_MARK not in old:
                print(f"- {name}: bản Claude viết tay, bỏ qua")
                continue
            if old == out:
                continue
        changed.append(name)
        if not args.check:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(out, encoding="utf-8")
            written.append(name)
    for d in sorted(DST.glob("*/SKILL.md")):
        n = d.parent.name
        if AUTO_MARK in d.read_text(encoding="utf-8") and not (SRC / n / "SKILL.md").exists():
            print(f"! {n}: skill gốc đã mất, cân nhắc xóa claude-skills/skills/{n}/")
    if args.check:
        print("Lệch: " + (", ".join(changed) if changed else "không có"))
        sys.exit(1 if changed else 0)
    print(f"Đã ghi {len(written)} skill: " + (", ".join(written) if written else "không có thay đổi"))
    if args.install:
        INSTALL.mkdir(parents=True, exist_ok=True)
        names = []
        for d in sorted(p for p in DST.iterdir() if (p / "SKILL.md").exists()):
            shutil.copytree(d, INSTALL / d.name, dirs_exist_ok=True)
            names.append(d.name)
        print(f"Đã cài {len(names)} skill vào {INSTALL.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
