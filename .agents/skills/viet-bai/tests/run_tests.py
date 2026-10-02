#!/usr/bin/env python3
"""
run_tests.py — Bộ kiểm thử hồi quy cho cổng chất lượng viet-bai (claim_guard --profile ads + fact_checker).

  - tests/bad.md:  MỌI vi phạm liệt kê trong tests/expected_bad.json phải bị bắt (recall 100%).
  - tests/clean.md: phải ĐẠT (exit 0) với --category cosmetics (không báo nhầm câu disclaimer bắt buộc,
                    trích dẫn có nguồn, câu ghép ", và", "ít nhất", "thống nhất", "giá trị", "quản trị", "Nghị định số 1/...").
  - Các template trong templates/ chỉ được phép báo lỗi placeholder (không chứa câu vi phạm R5 làm mẫu).

Usage: python3 .agents/skills/viet-bai/tests/run_tests.py     (exit 0 = tất cả đạt)
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ROOT = SKILL.parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SKILL / "scripts"))

from scripts.claim_guard import check_file as claim_check  # noqa: E402
import fact_checker  # noqa: E402


def findings(path: Path, category: str = "general"):
    text = path.read_text(encoding="utf-8")
    errors, warns = fact_checker.style_checks(text, category)
    res = claim_check(str(path), quiet=True, strict=True, profile="ads")
    out = []
    for e in errors + warns:
        if e.startswith("Dòng "):
            ln = int(e.split(":")[0].split()[1])
            out.append((ln, e.lower()))
        else:
            out.append((0, e.lower()))
    for v in res.get("violations", []):
        out.append((v["line"], f"{v['matched']} {v['category']}".lower()))
    return out


def main() -> int:
    ok = True
    exp = json.loads((HERE / "expected_bad.json").read_text(encoding="utf-8"))
    got = findings(HERE / "bad.md")
    missed = [e for e in exp if not any(ln == e["line"] and e["term"].lower() in msg for ln, msg in got)]
    print(f"[bad.md] recall: {len(exp) - len(missed)}/{len(exp)}")
    for m in missed:
        print(f"   ❌ BỎ SÓT dòng {m['line']}: {m['term']}")
    ok &= not missed

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fact_checker.check_file(str(HERE / "clean.md"), category="cosmetics")
    print(f"[clean.md] exit={rc} (mong đợi 0)")
    if rc != 0:
        print(buf.getvalue())
    ok &= rc == 0

    for tpl in sorted((SKILL / "templates").glob("*.md")):
        bad = [(ln, msg) for ln, msg in findings(tpl) if "placeholder" not in msg]
        print(f"[{tpl.name}] lỗi ngoài placeholder: {len(bad)}")
        for ln, msg in bad[:10]:
            print(f"   ❌ dòng {ln}: {msg[:120]}")
        ok &= not bad

    import re
    import tempfile
    for ex in sorted((SKILL / "examples").glob("*.md")):
        txt = ex.read_text(encoding="utf-8")
        cat = (re.search(r"category:\s*(\w+)", txt) or [None, "general"])[1]
        blocks = dict(re.findall(r"## (TRƯỚC|SAU)[^\n]*\n```text\n(.*?)```", txt, re.S))
        for kind, want in (("TRƯỚC", 1), ("SAU", 0)):
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
                tf.write(blocks.get(kind, ""))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = fact_checker.check_file(tf.name, category=cat)
            Path(tf.name).unlink()
            print(f"[{ex.name} {kind}] exit={rc} (mong đợi {want})")
            if rc != want:
                print(buf.getvalue())
            ok &= rc == want

    print("✅ TẤT CẢ ĐẠT" if ok else "❌ CÓ TEST HỎNG")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
