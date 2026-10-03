#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tables_from_source.py - Đọc bảng trong source.md (đầu ra của scripts/doc_ingest.py) → JSON có số đã chuẩn hoá
và địa chỉ nguồn, để Agent ĐỐI CHIẾU rồi tự viết data.json. Script KHÔNG ghi data.json.

    .venv/bin/python scripts/doc_ingest.py "<tệp>" --out <process_dir>/ingest --json          # (gốc repo) trước
    python3 .agents/skills/bao-cao-kt/scripts/tables_from_source.py <process_dir>/ingest -o <process_dir>/tables.json

Đầu ra:
  tables[]          {where: "Sheet 1 'KQKD'" | "trang 3" | "Slide 2" | "bảng 4", kind: sheet|formulas|table,
                     rows: [{cells: [chuỗi], values: [số|null], refs: ["D7"|null]}]}
  pnl_candidates[]  dòng có cột "Mã số" thuộc mã NHẬP của B02: {code, label, curr, prev, src{curr,prev}, notes[]}
  check_totals[]    mã TÍNH (10/20/30/40/50/60) trong nguồn + kết quả tự tính từ pnl_candidates (lệch → kiểm tra lại)
  regime_hint       "TT133" (có mã 24) | "TT200" (có 25/26) | null

Số kiểu Việt Nam: "1.234.567" → 1234567; "1.234,5" → 1234.5; "(1.234)" / "-1.234" → -1234; "28,6%" → 0.286;
"-" hoặc ô trống → null (trên BCTC "-" thường là 0: xác nhận trước khi nhập). Ô của sheet XLSX đã là số máy (không
có dấu phân cách nghìn) nên đọc thẳng. Mã thoát: 0 = có bảng; 3 = không có bảng nào; 2 = không đọc được source.md.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "_shared"))    # .agents/skills/_shared
sys.path.insert(0, str(HERE))
from doc_ingest_bridge import md_blocks, strip_md_inline  # noqa: E402
from pnl_model import LINES  # noqa: E402

INPUT_CODES = {c for r in LINES.values() for c, _, k, _ in r if k in ("input", "sub", "cit")}
CALC_SPECS = {c: spec for r in (LINES["TT200"], LINES["TT133"]) for c, _, k, spec in r if k == "calc"}
COST_CODES = {"02", "11", "22", "23", "24", "25", "26", "32", "51"}   # chi phí nhập số dương
CURR_HDR = re.compile(r"năm nay|kỳ này|kì này|cuối (kỳ|năm)|kỳ báo cáo|số cuối|current|this year", re.I)
PREV_HDR = re.compile(r"năm trước|kỳ trước|kì trước|đầu (kỳ|năm)|cùng kỳ|prior|last year|previous", re.I)
CODE_HDR = re.compile(r"^mã\s*(số|chỉ\s*tiêu)?$", re.I)
NOTE_HDR = re.compile(r"thuyết\s*minh|^tm$", re.I)


def parse_vn_number(text, machine=False):
    """Chuỗi số (kiểu VN hoặc số máy) → float/int; không phải số → None."""
    s = strip_md_inline(str(text or "")).strip()
    s = re.sub(r"(?i)\s*(vnđ|vnd|đồng|đ)\s*$", "", s).replace(" ", "").replace(" ", "")
    if s in ("", "-", "–", "—"):
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    if s[:1] in "-−–":
        neg, s = True, s[1:]
    pct = s.endswith("%")
    s = s.rstrip("%")
    if not re.fullmatch(r"[\d.,]+(?:[eE][+-]?\d+)?", s) or not re.search(r"\d", s):
        return None
    if machine or re.search(r"[eE]", s):
        try:
            v = float(s)
        except ValueError:
            return None
    else:
        if "." in s and "," in s:
            dec = "," if s.rfind(",") > s.rfind(".") else "."
            s = s.replace("." if dec == "," else ",", "").replace(dec, ".")
        elif "." in s:
            s = s.replace(".", "") if re.fullmatch(r"\d{1,3}(\.\d{3})+", s) else s
        elif "," in s:
            s = s.replace(",", "") if re.fullmatch(r"\d{1,3}(,\d{3})+", s) else s.replace(",", ".")
        try:
            v = float(s)
        except ValueError:
            return None
    v = -v if neg else v
    if pct:
        return round(v / 100, 10)
    return int(v) if v == int(v) and abs(v) < 1e15 else v


def collect_tables(md):
    tables, sheet, sheet_n, page, slide, formulas, n = [], None, None, None, None, False, 0
    for b in md_blocks(md):
        t = b["type"]
        if t == "page":
            page, slide = b["page"], None
        elif t == "heading":
            m = re.match(r"Sheet\s+(\d+):\s*(.*)$", b["text"])
            sm = re.match(r"Slide\s+(\d+)", b["text"])
            if m:
                sheet_n, sheet, formulas = m.group(1), m.group(2).strip(), False
            elif sm:
                slide = int(sm.group(1))
            elif b["text"].startswith("Công thức"):
                formulas = True
        elif t == "table":
            n += 1
            rows = [[strip_md_inline(c) for c in r] for r in b["rows"]]
            if sheet and formulas:
                kind, where = "formulas", f"Sheet {sheet_n} '{sheet}' (công thức)"
            elif sheet:
                kind, where = "sheet", f"Sheet {sheet_n} '{sheet}'"
            else:
                kind = "table"
                where = f"trang {page}" if page else (f"Slide {slide}" if slide else f"bảng {n}")
            tables.append(_table(kind, where, rows, sheet))
    return tables


def _table(kind, where, rows, sheet):
    out = {"where": where, "kind": kind, "rows": []}
    if kind == "sheet" and rows and rows[0][:1] == ["#"]:
        letters = rows[0][1:]
        for r in rows[1:]:
            cells = r[1:]
            out["rows"].append({"cells": cells, "values": [parse_vn_number(c, machine=True) for c in cells],
                                "refs": [f"{letters[j]}{r[0]}" if j < len(letters) else None for j in range(len(cells))]})
    elif kind == "formulas":
        for r in rows[1:]:
            out["rows"].append({"cells": r, "values": [None, None, parse_vn_number(r[-1], machine=True)],
                                "refs": [r[0], r[0], r[0]]})
    else:
        for r in rows:
            out["rows"].append({"cells": r, "values": [parse_vn_number(c) for c in r], "refs": [None] * len(r)})
    return out


def _code(text):
    """'01' | '1' | '11 VI.27' (mã + thuyết minh dính nhau trong PDF) → '01'/'11'; khác → None."""
    m = re.fullmatch(r"(\d{1,2})(?:\s+[A-Z]{1,4}[.\d]*)?", text.strip())
    c = m.group(1).zfill(2) if m else None
    return c if c in INPUT_CODES or c in CALC_SPECS else None


def _period_cols(hdr):
    cur = next((k for k, h in enumerate(hdr) if CURR_HDR.search(h)), None)
    prv = next((k for k, h in enumerate(hdr) if PREV_HDR.search(h)), None)
    years = [(int(m.group(0)), k) for k, h in enumerate(hdr) for m in [re.search(r"(19|20)\d{2}", h)] if m]
    if (cur is None or prv is None) and len(years) >= 2:          # "Năm 2025 | Năm 2024"
        years.sort(reverse=True)
        cur, prv = years[0][1], years[1][1]
    return cur, prv


def _add(store, code, label, vals, srcs, notes):
    ent = {"code": code, "label": label.strip(" .:-"), "src": {}, "notes": list(notes)}
    for p, v, src in zip(("curr", "prev"), vals, srcs):
        if src is None:
            continue
        ent[p], ent["src"][p] = v, src
        if v is not None and v < 0 and code in COST_CODES:
            ent[p] = -v
            ent["notes"].append(f"{p}: nguồn ghi âm/(…) cho khoản chi phí → đổi thành số dương (B02 tự trừ); xác nhận")
        if v is None:
            ent["notes"].append(f"{p}: ô trống hoặc '-' → hỏi; chỉ ghi 0 khi sổ sách bằng 0")
    store.setdefault(code, ent)


ORDER_NOTE = "cột kỳ suy theo thứ tự (số thứ 1 = kỳ này, thứ 2 = kỳ trước): xác nhận với tiêu đề cột trong nguồn"


def pnl_candidates(tables, md=""):
    """Dòng B02 trong bảng (có/không có tiêu đề 'Mã số') và dòng chữ PDF '... 01 VI.25 1.234 1.000'."""
    found = {}
    for tb in tables:
        if tb["kind"] == "formulas":
            continue
        code_col = hdr = cur = prv = None
        for row in tb["rows"]:
            cells, vals = row["cells"], row["values"]
            hj = next((j for j, c in enumerate(cells) if CODE_HDR.match(c.strip()) or re.match(r"(?i)mã\s*số\b", c.strip())), None)
            if hj is not None:
                code_col, hdr = hj, cells
                cur, prv = _period_cols(hdr)
                continue
            j = code_col if code_col is not None and code_col < len(cells) and _code(cells[code_col]) else \
                next((k for k, c in enumerate(cells) if k > 0 and _code(c)), None)
            if j is None:
                continue
            code = _code(cells[j])
            cols, notes = ([cur, prv], []) if code_col is not None and cur is not None else (None, [ORDER_NOTE])
            if cols is None:
                nums = [k for k in range(j + 1, len(cells)) if vals[k] is not None or cells[k].strip() in ("-", "–")]
                if hdr:
                    nums = [k for k in nums if k >= len(hdr) or not NOTE_HDR.search(hdr[k])]
                cols = (nums + [None, None])[:2]
            label = " ".join(c for k, c in enumerate(cells[:j]) if c and vals[k] is None)
            def where(k):
                ref = row["refs"][k]
                return f"{tb['where']} ô {ref}" if ref else f"{tb['where']}, dòng mã {code}, cột {k + 1}"
            _add(found, code, label, [vals[k] if k is not None and k < len(vals) else None for k in cols],
                 [where(k) if k is not None and k < len(cells) else None for k in cols], notes)
    page = None
    num = r"\(?-?[\d.,]*\d\)?|-"
    line_re = re.compile(rf"^(?P<label>[^|<#\d].*?)\s+(?P<code>\d{{2}})(?:\s+[A-Z]{{1,4}}[.\d]*)?\s+(?P<a>{num})(?:\s+(?P<b>{num}))?\s*$")
    for ln in md.splitlines():
        pm = re.match(r"<!--\s*page\s+(\d+)\s*-->", ln.strip())
        if pm:
            page = pm.group(1)
            continue
        m = line_re.match(ln.strip())
        if not m or not _code(m.group("code")):
            continue
        code, where = _code(m.group("code")), f"trang {page}" if page else "văn bản"
        a, b = m.group("a"), m.group("b")
        _add(found, code, m.group("label"), [parse_vn_number(a), parse_vn_number(b) if b else None],
             [f"{where}, dòng chữ mã {code}", f"{where}, dòng chữ mã {code}" if b else None], [ORDER_NOTE])
    cands = {c: e for c, e in found.items() if c not in CALC_SPECS}
    totals = {c: e for c, e in found.items() if c in CALC_SPECS}
    return cands, totals


def reconcile(cands, totals):
    vals = {c: {p: e.get(p) for p in ("curr", "prev")} for c, e in cands.items()}
    regime = "TT133" if "24" in cands else ("TT200" if {"25", "26"} & set(cands) else None)
    spec_src = LINES[regime or "TT200"]
    out = []
    for code, _, kind, spec in spec_src:
        if kind != "calc":
            continue
        row = {}
        for p in ("curr", "prev"):
            terms = [(s, vals.get(c, {}).get(p)) for s, c in spec]
            row[p] = None if all(v is None for _, v in terms) else sum((1 if s == "+" else -1) * (v or 0) for s, v in terms)
        vals[code] = row
        if code in totals:
            t = totals[code]
            diff = {p: (t.get(p) - row[p]) for p in ("curr", "prev")
                    if t.get(p) is not None and row[p] is not None}
            out.append({"code": code, "source": {p: t.get(p) for p in ("curr", "prev")}, "src": t["src"],
                        "computed": row, "diff": diff, "ok": all(abs(d) <= 1 for d in diff.values())})
    return out, regime


def main():
    ap = argparse.ArgumentParser(description="Bảng trong source.md (doc_ingest) → JSON số + nguồn cho bao-cao-kt")
    ap.add_argument("source", help="source.md hoặc thư mục đầu ra của doc_ingest")
    ap.add_argument("-o", "--out", help="Ghi JSON ra file (mặc định in ra màn hình)")
    a = ap.parse_args()
    p = Path(a.source).expanduser()
    p = p / "source.md" if p.is_dir() else p
    try:
        md = p.read_text(encoding="utf-8")
    except OSError as e:
        print(f"❌ Không đọc được {p}: {e}. Chạy doc_ingest.py trước (xem SKILL.md Bước 0).", file=sys.stderr)
        sys.exit(2)
    tables = collect_tables(md)
    cands, totals = pnl_candidates(tables, md)
    checks, regime = reconcile(cands, totals)
    res = {"source_md": str(p), "regime_hint": regime, "pnl_candidates": list(cands.values()),
           "check_totals": checks, "tables": tables}
    js = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).expanduser().write_text(js, encoding="utf-8")
        print(f"Đã ghi {a.out}: {len(tables)} bảng, {len(cands)} mã nhập, {len(checks)} mã tổng để đối chiếu.")
    else:
        print(js)
    bad = [c["code"] for c in checks if not c["ok"]]
    if bad:
        print(f"⚠️  Tổng tự tính lệch nguồn ở mã {', '.join(bad)}: kiểm tra cột/dấu/ô bị bỏ sót trước khi viết data.json.",
              file=sys.stderr)
    if not tables:
        print("⚠️  source.md không có bảng nào: đọc nội dung/ảnh trang và nhập tay có trích nguồn.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
