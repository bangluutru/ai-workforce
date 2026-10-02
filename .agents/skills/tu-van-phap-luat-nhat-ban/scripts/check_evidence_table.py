#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_evidence_table.py — Cổng kiểm báo cáo pháp lý Nhật trước khi xuất DOCX.

Chặn đúng các lỗi đã gặp ở báo cáo thật (bún gạo: "VJEPA 0 JPY/kg" trong khi biểu thuế không có ưu đãi;
cà phê: RCEP "0%" trong khi biểu thuế ghi 5.5%, mã 9 số không tồn tại; công ty Fukuoka: bảng căn cứ
"Đã kiểm chứng" mà không có URL/ngày/trích dẫn).

Kiểm:
  1. Có Bảng nguồn (bảng Markdown có cột ID, URL, Trích/Nguyên văn); mỗi dòng có ID, URL https, ngày truy cập
     (YYYY-MM-DD), và trích đoạn không rỗng. Dòng là luật e-Gov phải có trích đoạn tiếng Nhật.
  2. Mỗi dòng có [XÁC ĐỊNH] phải dẫn ID có trong Bảng nguồn (VD "(E3)" hoặc "[E3]").
  3. [XÁC ĐỊNH] về thuế suất nhập khẩu/EPA phải dẫn ID có URL biểu thuế có ngày
     (customs.go.jp/english/tariff/YYYY_MM_DD) và báo cáo phải có khối TARIFF_LOOKUP.
  4. Mọi mã 9 số (dddd.dd-ddd) nhắc trong báo cáo phải có khối TARIFF_LOOKUP tương ứng.
  5. Câu nói hiệp định (VJEPA/AJCEP/CPTPP/RCEP) "0%/Free/miễn thuế" mà khối TARIFF_LOOKUP của mã đó ghi
     "KHÔNG có ưu đãi" hoặc mức khác → lỗi.
  6. Báo cáo có nhãn thực phẩm (食品表示) phải tự kiểm đủ: 名称, 原材料名, 内容量, 期限 (賞味/消費),
     保存方法, 原産国名, 輸入者, 栄養成分, アレルゲン/アレルギー.
  7. Không lẫn chữ Hán giản thể/cụm tiếng Trung (VD "不是", "这", "们") trong phần tiếng Nhật.
  8. (--sources-dir) trích đoạn tiếng Nhật trong Bảng nguồn phải có NGUYÊN VĂN trong file nguồn đã lưu
     (fetch_jp_source.py), dùng scripts/harness/evidence_verifier.py.

Cách dùng (từ thư mục workspace AIWF):
  python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/check_evidence_table.py \
      --report <research_dir>/legal_report_jp_<chủ_đề>.md --sources-dir <research_dir>/sources
Mã thoát: 0 = PASS, 2 = FAIL, 1 = lỗi đầu vào.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
try:
    from scripts.harness.evidence_verifier import check_single_quote  # noqa: E402
except Exception:  # noqa: BLE001
    check_single_quote = None

CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
ID_RE = re.compile(r"\b([ES]\d{1,3})\b")
CODE9 = re.compile(r"\b(\d{4}\.\d{2})[-.](\d{3})\b")
RATE = re.compile(r"(\d+(?:[.,]\d+)?\s*%|yen/kg|円/kg|JPY\s*/\s*kg|\bFree\b|miễn thuế|無税|0\s*JPY)", re.I)
DUTY_CONTEXT = re.compile(r"(thuế nhập khẩu|thuế quan|duty|tariff|関税|EPA|FTA|VJEPA|AJCEP|CPTPP|RCEP|WTO|MFN|"
                          r"ưu đãi|C/O|Form VJ|Form AJ|mã HS|HS code)", re.I)
TARIFF_URL = re.compile(r"customs\.go\.jp/(?:english/)?tariff/\d{4}_\d{2}_\d{2}")
AGREEMENT_COLUMNS = {
    "VJEPA": "Viet Nam", "JVEPA": "Viet Nam", "AJCEP": "ASEAN", "CPTPP": "CPTPP",
    "RCEP": "ASEAN/Australia/New Zealand(RCEP)",
}
ZERO = re.compile(r"((?<![\d.,])0(?:[.,]0+)?\s*(?:%|JPY|yen|円)|\bFree\b|miễn thuế|無税)", re.I)
FOOD_LABEL_ITEMS = {
    "名称": ["名称"],
    "原材料名": ["原材料名", "原材料"],
    "内容量": ["内容量"],
    "期限 (賞味/消費)": ["賞味期限", "消費期限"],
    "保存方法": ["保存方法"],
    "原産国名": ["原産国名", "原産国"],
    "輸入者": ["輸入者"],
    "栄養成分表示": ["栄養成分"],
    "アレルゲン": ["アレルゲン", "アレルギー", "特定原材料"],
}
CHINESE_ONLY = ["不是", "这", "们", "说", "没有", "对于", "应该", "为了", "时间", "发现", "实际", "关于", "规定的",
                "证明书", "认证", "进口", "业务", "见书", "这个", "我们"]


def nfkc(s):
    return unicodedata.normalize("NFKC", s)


def split_row(line):
    s = line.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def find_tables(lines):
    tables, i = [], 0
    while i < len(lines):
        if lines[i].strip().startswith("|"):
            start = i
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            rows = [split_row(b) for b in block]
            rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r if c)]
            if rows:
                tables.append((start, rows))
        else:
            i += 1
    return tables


def evidence_table(lines):
    for start, rows in find_tables(lines):
        head = [h.lower() for h in rows[0]]
        has_id = any(re.fullmatch(r"\**id\**", h) for h in head)
        has_url = any("url" in h for h in head)
        if has_id and has_url:
            return start, rows
    return None, None


def col(head, *keys):
    for i, h in enumerate(head):
        if any(k in h.lower() for k in keys):
            return i
    return None


def parse_lookups(text):
    """{code9: {column: reading}} từ các khối TARIFF_LOOKUP."""
    out = {}
    for blk in re.findall(r"<!-- TARIFF_LOOKUP v1 -->(.*?)<!-- /TARIFF_LOOKUP -->", text, flags=re.S):
        m = re.search(r"`(\d{4}\.\d{2}-\d{3})`", blk)
        if not m:
            continue
        cols = {}
        for row in re.findall(r"^\|\s*([^|]+?)\s*(?:★)?\s*\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|", blk, flags=re.M):
            name = row[0].replace("★", "").strip()
            cols[name] = row[3].strip()
        out[m.group(1)] = {"cols": cols, "url": (re.search(r"Nguồn:\s*(\S+)", blk) or [None, ""])[1]}
    return out


def main():
    ap = argparse.ArgumentParser(description="Cổng kiểm Bảng nguồn và thuế suất của báo cáo pháp lý Nhật")
    ap.add_argument("--report", required=True)
    ap.add_argument("--sources-dir", default=None, help="<research_dir>/sources (file từ fetch_jp_source.py)")
    a = ap.parse_args()
    p = Path(a.report).expanduser()
    if not p.is_file():
        print(f"❌ Không thấy báo cáo: {p}", file=sys.stderr)
        return 1
    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    errors, warns = [], []

    # 1. Bảng nguồn
    start, rows = evidence_table(lines)
    ids = {}
    if rows is None:
        errors.append("Thiếu Bảng nguồn (bảng có cột ID, URL, Trích đoạn). Xem references/evidence-and-output.md.")
    else:
        head = rows[0]
        c_id, c_url = col(head, "id"), col(head, "url")
        c_quote = col(head, "trích", "nguyên văn", "quote", "nội dung hỗ trợ")
        if c_quote is None:
            errors.append("Bảng nguồn thiếu cột trích đoạn ('Trích đoạn hoặc nội dung hỗ trợ').")
        for r_i, r in enumerate(rows[1:], start=1):
            rid = re.sub(r"[*`\[\]]", "", r[c_id]).strip() if c_id is not None and c_id < len(r) else ""
            row_text = " | ".join(r)
            if not rid:
                errors.append(f"Bảng nguồn dòng {r_i}: thiếu ID.")
                continue
            url = r[c_url] if c_url is not None and c_url < len(r) else ""
            ids[rid] = row_text
            if not re.search(r"https?://\S+", url):
                errors.append(f"Bảng nguồn {rid}: thiếu URL trực tiếp (http/https).")
            if not re.search(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}", row_text):
                errors.append(f"Bảng nguồn {rid}: thiếu ngày truy cập/ngày biểu thuế (YYYY-MM-DD).")
            quote = r[c_quote] if c_quote is not None and c_quote < len(r) else ""
            if not quote.strip() or quote.strip() in ("-", "…", "..."):
                errors.append(f"Bảng nguồn {rid}: trích đoạn rỗng. 'Đã kiểm chứng' mà không có trích đoạn là không hợp lệ.")
            if "e-gov.go.jp" in url and not CJK.search(quote):
                errors.append(f"Bảng nguồn {rid}: nguồn luật e-Gov phải có trích đoạn NGUYÊN VĂN tiếng Nhật.")
            if a.sources_dir and CJK.search(quote) and check_single_quote:
                segs = re.findall(r"「([^」]{6,})」", quote) or [re.sub(r"^[^\u3040-\u9fff]*", "", quote)]
                files = list(Path(a.sources_dir).expanduser().glob("*.txt"))
                for seg in segs:
                    if len(re.sub(r"\s", "", seg)) < 6:
                        continue
                    if not any(check_single_quote(f.read_text(encoding="utf-8", errors="ignore"), seg)[0] for f in files):
                        errors.append(f"Bảng nguồn {rid}: trích đoạn 「{seg[:40]}…」 KHÔNG có nguyên văn trong {a.sources_dir}.")

    lookups = parse_lookups(text)

    # 2-5. Dòng có cờ / mã / thuế suất
    current_code = None
    in_lookup = False
    for n, line in enumerate(lines, start=1):
        if "<!-- TARIFF_LOOKUP v1 -->" in line:
            in_lookup = True
        if "<!-- /TARIFF_LOOKUP -->" in line:
            in_lookup = False
            continue
        if in_lookup or (start is not None and rows is not None and start <= n - 1 < start + len(rows) + 1):
            continue
        for m in CODE9.finditer(line):
            code = f"{m.group(1)}-{m.group(2)}"
            current_code = code
            if code not in lookups:
                errors.append(f"Dòng {n}: mã {code} chưa có khối TARIFF_LOOKUP (chạy scripts/tariff_lookup.py và dán kết quả).")
        cited = [i for i in ID_RE.findall(line)]
        if "[XÁC ĐỊNH]" in line:
            if not cited:
                errors.append(f"Dòng {n}: [XÁC ĐỊNH] không dẫn ID nguồn (VD (E1)).")
            for c in cited:
                if c not in ids:
                    errors.append(f"Dòng {n}: dẫn {c} nhưng Bảng nguồn không có {c}.")
            if RATE.search(line) and DUTY_CONTEXT.search(line):
                if not any(TARIFF_URL.search(ids.get(c, "")) for c in cited):
                    errors.append(f"Dòng {n}: [XÁC ĐỊNH] thuế suất nhập khẩu phải dẫn nguồn biểu thuế có ngày "
                                  f"(customs.go.jp/english/tariff/YYYY_MM_DD).")
                if not lookups:
                    errors.append(f"Dòng {n}: [XÁC ĐỊNH] thuế suất nhưng báo cáo không có khối TARIFF_LOOKUP.")
        # 5. đối chiếu claim 0% theo hiệp định với khối tra cứu
        if ZERO.search(line):
            codes_here = [f"{m.group(1)}-{m.group(2)}" for m in CODE9.finditer(line)] or ([current_code] if current_code else [])
            for ag, colname in AGREEMENT_COLUMNS.items():
                if re.search(rf"\b{ag}\b", line):
                    for code in codes_here:
                        reading = lookups.get(code, {}).get("cols", {}).get(colname)
                        if reading is None:
                            if code in lookups:
                                errors.append(f"Dòng {n}: nói {ag} cho {code} nhưng khối TARIFF_LOOKUP không có cột {colname} "
                                              f"(chạy lại tariff_lookup.py với --origin đúng nước hoặc bỏ --compact).")
                            else:
                                errors.append(f"Dòng {n}: nói {ag} 0%/Free cho {code} nhưng không có khối TARIFF_LOOKUP để đối chiếu.")
                        elif not reading.startswith("Free"):
                            errors.append(f"Dòng {n}: nói {ag} 0%/Free cho {code} nhưng biểu thuế ghi '{reading}' (cột {colname}).")
            if re.search(r"\bEPA\b|FTA", line) and not codes_here:
                warns.append(f"Dòng {n}: nói EPA/FTA 0% mà không gắn mã 9 số; ghi rõ mã và hiệp định.")

    # 6. Nhãn thực phẩm
    if re.search(r"食品表示|nhãn phụ tiếng Nhật|Ghi nhãn Thực phẩm|food label", text, re.I):
        missing = [k for k, alts in FOOD_LABEL_ITEMS.items() if not any(x in text for x in alts)]
        if missing:
            errors.append("Mục nhãn thực phẩm thiếu tự kiểm các trường bắt buộc: " + ", ".join(missing)
                          + " (references/products/food-and-health-claims.md, mục Nhãn).")

    # 7. Lẫn tiếng Trung
    hits = sorted({w for w in CHINESE_ONLY if w in nfkc(text)})
    if hits:
        errors.append(f"Có chữ/cụm tiếng Trung giản thể trong báo cáo: {hits}. Viết lại bằng tiếng Nhật chuẩn.")

    status = "PASS" if not errors else "FAIL"
    print(f"{status}: {p.name}  ({len(ids)} nguồn, {len(lookups)} khối TARIFF_LOOKUP)")
    for e in errors:
        print(f"  ❌ {e}")
    for w in warns:
        print(f"  ⚠️  {w}")
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
