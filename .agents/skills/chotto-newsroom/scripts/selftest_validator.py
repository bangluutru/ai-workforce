#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_validator.py — Kiểm thử hồi quy cho validate-article-draft.py.

Bản nháp thật (lệ phí gia hạn tư cách lưu trú từ 2026-10-01, số liệu ISA) phải PASS; mỗi bản đột biến
mô phỏng một lỗi đã gặp phải FAIL với đúng thông báo. Chạy sau mỗi lần sửa validator:

  python3 .agents/skills/chotto-newsroom/scripts/selftest_validator.py

Mã thoát 0 = mọi ca đúng kỳ vọng.
"""

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE.parent / "examples" / "validator-selftest"
SLUG = "le-phi-gia-han-doi-tu-cach-luu-tru-tu-01-10-2026"

spec = importlib.util.spec_from_file_location("vad", HERE / "validate-article-draft.py")
vad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vad)

HEADING = "{ type: 'heading', level: 2, text: 'Mức phí theo thời hạn' },"
MUTANTS = [
    ("ghép sai kênh (phí quầy ghi là trực tuyến)",
     [("trực tuyến 27.000 yên", "trực tuyến 33.000 yên")], "ghép sai ngữ cảnh"),
    ("ghép sai thời hạn (phí 1 năm ghi cho 3 năm)",
     [("3 năm tại quầy là 64.000", "3 năm tại quầy là 27.000")], "ghép sai ngữ cảnh"),
    ("mức cũ ghi thành mức mới",
     [("Mức cũ là 6.000 yên", "Mức mới là 6.000 yên")], "ghép sai ngữ cảnh"),
    ("số bịa trong chuỗi nháy kép",
     [(HEADING, HEADING + "\n    { type: 'warning', content: \"Phạt 300.000 yên nếu nộp muộn.\" },")], "'300.000'"),
    ("số bịa trong template literal",
     [("content: 'Thời hạn 3 năm tại quầy là 64.000 yên.", "content: `Thời hạn 3 năm tại quầy là 99.000 yên."),
      ("cảnh).' }", "cảnh).` }")], "'99.000'"),
    ("thời hạn bịa (ngày/tháng)",
     [("Luật Quản lý xuất nhập cảnh).", "Luật Quản lý xuất nhập cảnh). Phải nộp tem trong 14 ngày.")], "'14 ngày'"),
    ("ngày viết bằng chữ không có trong Fact Pack",
     [("Đơn nhận đến 30/09/2026", "Đơn nhận đến ngày 15 tháng 9")], "2026-09-15"),
    ("Điều N kèm sai tên luật",
     [("(Điều 67 Luật Quản lý xuất nhập cảnh)", "(Điều 67 Luật Tiêu chuẩn Lao động)")], "không có tên luật đi kèm"),
    ("Điều N không có trong Sổ điều luật",
     [("(Điều 67 Luật Quản lý xuất nhập cảnh)", "(Điều 71 Luật Quản lý xuất nhập cảnh)")], "Điều 71"),
    ("status published",
     [("status: 'review'", "status: 'published'")], "'status' phải là 'review'"),
]


def run(text):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / f"{SLUG}.js").write_text(text, encoding="utf-8")
        shutil.copy(FIX / f"fact-pack-{SLUG}.md", d)
        shutil.copy(FIX / f"{SLUG}.webp", d)
        ok, errors, _ = vad.validate_article_file(d / f"{SLUG}.js")
        return ok, errors


def main():
    base = (FIX / f"{SLUG}.mjs").read_text(encoding="utf-8")
    failures = 0
    ok, errors = run(base)
    print(f"{'✅' if ok else '❌'} bản nháp thật phải PASS" + ("" if ok else f": {errors}"))
    failures += not ok
    for name, edits, expect in MUTANTS:
        text = base
        for old, new in edits:
            if old not in text:
                print(f"❌ {name}: fixture không còn chuỗi '{old[:40]}'")
                failures += 1
                break
            text = text.replace(old, new)
        else:
            ok, errors = run(text)
            hit = (not ok) and any(expect in e for e in errors)
            print(f"{'✅' if hit else '❌'} {name}: " + ("FAIL đúng kỳ vọng" if hit else f"không bắt được (lỗi: {errors})"))
            failures += not hit
    print(f"\n{len(MUTANTS) + 1 - failures}/{len(MUTANTS) + 1} ca đúng")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
