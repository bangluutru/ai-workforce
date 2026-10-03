#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_legal_freshness.py: kiểm tra độ mới của chỉ mục văn bản và tham số thuế (ngoại tuyến, không gọi mạng).

Kiểm tra:
  1. resources/legal_index.json đủ trường; cảnh báo văn bản quá --max-age ngày chưa kiểm lại.
  2. standards/*.json: tham số có effective_to trong vòng --horizon ngày tới (sắp hết hiệu lực) hoặc đã hết hạn.
  3. Tham số không ở trạng thái PRIMARY_VERIFIED được liệt kê để người phụ trách xác minh.

    python3 check_legal_freshness.py [--today 2026-10-03] [--max-age 90] [--horizon 90]
Mã thoát: 0 = không có vấn đề nghiêm trọng, 1 = có lỗi cấu trúc, 2 = lỗi chạy.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("id", "title", "type", "verification_status", "last_verified")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--today", default=date.today().isoformat())
    ap.add_argument("--max-age", type=int, default=90)
    ap.add_argument("--horizon", type=int, default=90)
    a = ap.parse_args(argv)
    try:
        today = date.fromisoformat(a.today)
        idx = json.loads((ROOT / "resources/legal_index.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        print(f"✗ Không đọc được dữ liệu: {ex}", file=sys.stderr)
        return 2
    errors, notes = [], []
    ids = set()
    for d in idx.get("documents", []):
        miss = [k for k in REQUIRED if not d.get(k)]
        if miss:
            errors.append(f"Văn bản {d.get('id', '?')} thiếu trường {miss}")
        ids.add(d.get("id"))
        try:
            age = (today - date.fromisoformat(d["last_verified"])).days
            if age > a.max_age:
                notes.append(f"Văn bản {d['id']} đã {age} ngày chưa kiểm lại")
        except (KeyError, ValueError):
            errors.append(f"Văn bản {d.get('id', '?')} có last_verified không hợp lệ")
        if d.get("verification_status") in ("SECONDARY_ONLY", "UNVERIFIED"):
            notes.append(f"Văn bản {d['id']} chưa xác minh nguyên văn ({d['verification_status']})")
    soon = today + timedelta(days=a.horizon)
    for f in sorted((ROOT / "standards").glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as ex:
            errors.append(f"{f.name}: JSON lỗi {ex}")
            continue
        for name, entries in (data.get("params") or {}).items():
            for e in entries:
                st = e.get("verification_status")
                if st and st != "PRIMARY_VERIFIED":
                    notes.append(f"{f.stem}.{name}: {st}")
                if e.get("effective_to"):
                    end = date.fromisoformat(e["effective_to"])
                    if end < today:
                        notes.append(f"{f.stem}.{name}: đã hết hiệu lực {end}")
                    elif end <= soon:
                        notes.append(f"{f.stem}.{name}: sắp hết hiệu lực {end}")
    for n in notes:
        print("• " + n)
    for e in errors:
        print("✗ " + e)
    print(f"Văn bản trong chỉ mục: {len(ids)}; ghi chú: {len(notes)}; lỗi: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
