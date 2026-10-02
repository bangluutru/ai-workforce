#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tariff_lookup.py — Tra MỘT dòng Biểu thuế nhập khẩu Nhật (Japan's Tariff Schedule, Statistical Code for
Import) trên customs.go.jp theo ngày, in ĐỦ mọi cột thuế suất kèm tên cột, kế thừa mức của dòng cha,
và xuất khối Markdown để dán nguyên vào báo cáo (bắt buộc với mọi câu trả lời HS/thuế quan).

Chỉ đọc trang công khai (HTTP GET). Không gọi LLM API.

Cách dùng (chạy từ thư mục workspace AIWF):
  python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/tariff_lookup.py --code 1902.19-010 --origin "Viet Nam"
  python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/tariff_lookup.py --code 2101.11-210 --date 2026-10-15
  python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/tariff_lookup.py --code 2101.12 --list   # liệt kê mọi dòng 9 số
  ... --json                      # xuất JSON thay vì Markdown
  ... --html e_19.htm --version 2026_08_08   # dùng file HTML đã tải (offline/kiểm thử)

Quy ước đọc (in sẵn trong đầu ra):
  - Ô trống ở cột EPA của dòng và mọi dòng cha  = KHÔNG có mức ưu đãi theo hiệp định đó → áp mức MFN
    (General/Temporary/WTO theo quy tắc áp dụng), KHÔNG phải 0%.
  - "Free" = 0%. Mức "(x%)" trong ngoặc: đọc chú giải biểu thuế trước khi dùng.
  - Mức "yen/kg" là thuế theo lượng: tính bằng khối lượng, không phải % trị giá.
Mã thoát: 0 = tìm thấy; 2 = không thấy dòng; 1 = lỗi mạng/đầu vào.
"""

import argparse
import html as htmllib
import json
import re
import sys
import urllib.request
from datetime import date, datetime, timezone

BASE = "https://www.customs.go.jp/english/tariff/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

# Cột hiệp định liên quan theo nước xuất xứ (chỉ là gợi ý cột cần đọc; điều kiện xuất xứ vẫn phải kiểm).
ORIGIN_COLUMNS = {
    "viet nam": ["Viet Nam", "ASEAN", "CPTPP", "ASEAN/Australia/New Zealand(RCEP)"],
    "vietnam": ["Viet Nam", "ASEAN", "CPTPP", "ASEAN/Australia/New Zealand(RCEP)"],
    "thailand": ["Thailand", "ASEAN", "ASEAN/Australia/New Zealand(RCEP)"],
    "indonesia": ["Indonesia", "ASEAN", "ASEAN/Australia/New Zealand(RCEP)"],
    "malaysia": ["Malaysia", "ASEAN", "CPTPP", "ASEAN/Australia/New Zealand(RCEP)"],
    "philippines": ["Philippines", "ASEAN", "ASEAN/Australia/New Zealand(RCEP)"],
    "singapore": ["Singapore", "ASEAN", "CPTPP", "ASEAN/Australia/New Zealand(RCEP)"],
    "china": ["China (RCEP)"],
    "korea": ["Korea (RCEP)"],
    "australia": ["Australia", "CPTPP", "ASEAN/Australia/New Zealand(RCEP)"],
    "eu": ["EU"], "uk": ["UK", "CPTPP"], "usa": ["JP-US Trade Agreement"],
}
MFN_COLUMNS = ["General", "Temporary", "WTO"]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="ignore")


def clean(cell_html: str) -> str:
    txt = re.sub(r"<br\s*/?>", " ", cell_html)
    txt = htmllib.unescape(re.sub(r"<[^>]+>", " ", txt))
    return re.sub(r"\s+", " ", txt).strip()


def pick_version(target: date) -> str:
    index = fetch(BASE)
    versions = sorted(set(re.findall(r"/english/tariff/(\d{4}_\d{2}_\d{2})/index\.html?", index)))
    if not versions:
        raise RuntimeError("Không đọc được danh sách phiên bản biểu thuế tại " + BASE)
    eligible = [v for v in versions if datetime.strptime(v, "%Y_%m_%d").date() <= target]
    if not eligible:
        raise RuntimeError(f"Không có phiên bản biểu thuế nào hiệu lực trước {target}")
    return eligible[-1]


def parse_rows(page: str):
    rows = re.findall(r"<tr.*?</tr>", page, flags=re.S)
    header = None
    parsed = []
    for r in rows:
        cells_html = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, flags=re.S)
        cells = [clean(c) for c in cells_html]
        if cells and cells[0] == "H.S.code":
            header = cells[2:] + ["Law"]
            continue
        if header is None or len(cells) < 4:
            continue
        m = re.search(r'class="shell_var1_ITEM_NAME"\s+style="[^"]*padding-left:\s*(\d+)em', r)
        pad = int(m.group(1)) if m else 0
        dashes = len(re.match(r"^(-*)", cells[2].strip()).group(1))
        # Độ sâu = lề (em) + số gạch đầu dòng: "- x" là con của tiêu đề cùng lề, "-- y" là con của "- x".
        parsed.append({"hs": cells[0], "stat": cells[1], "desc": cells[2], "pad": pad * 10 + dashes,
                       "values": dict(zip(header, cells[3:]))})
    if header is None:
        raise RuntimeError("Không nhận ra bảng biểu thuế (không thấy hàng tiêu đề H.S.code).")
    return header, parsed


def find_lines(parsed, hs6: str, stat: str = None):
    """Trả về list (row, ancestors) cho các dòng 9 số thuộc hs6 (hoặc đúng stat)."""
    out = []
    cur_hs = None
    stack = []  # tiêu đề con (không có mã thống kê) trong cùng HS6
    for row in parsed:
        if row["hs"]:
            cur_hs = row["hs"]
            stack = [row]
            if row["stat"] and cur_hs == hs6 and (stat is None or row["stat"] == stat):
                out.append((row, []))
            continue
        if cur_hs != hs6:
            continue
        if not row["stat"]:
            while len(stack) > 1 and stack[-1]["pad"] >= row["pad"]:
                stack.pop()
            stack.append(row)
            continue
        while len(stack) > 1 and stack[-1]["pad"] >= row["pad"]:
            stack.pop()
        ancestors = list(stack)
        if stat is None or row["stat"] == stat:
            out.append((row, ancestors))
    return out


def resolve(row, ancestors, header):
    resolved = {}
    for col in header:
        own = row["values"].get(col, "")
        if own:
            resolved[col] = {"value": own, "from": "dòng này"}
            continue
        for anc in reversed(ancestors):
            v = anc["values"].get(col, "")
            if v:
                resolved[col] = {"value": v, "from": f"dòng cha: {anc['desc'][:60]}"}
                break
        else:
            resolved[col] = {"value": "", "from": ""}
    return resolved


def interpret(value: str, col: str) -> str:
    if col in ("I", "II", "Law"):
        return value or "-"
    if not value:
        if col in MFN_COLUMNS or col in ("GSP", "LDC"):
            return "(trống)"
        return "KHÔNG có ưu đãi → áp MFN"
    if value.lower() == "free":
        return "Free (0%)"
    return value


def main() -> int:
    ap = argparse.ArgumentParser(description="Tra dòng biểu thuế nhập khẩu Nhật theo ngày (customs.go.jp)")
    ap.add_argument("--code", required=True, help="HS6-mã thống kê, VD 1902.19-010; hoặc chỉ HS6 với --list")
    ap.add_argument("--date", default=None, help="Ngày nhập khẩu dự kiến YYYY-MM-DD (mặc định hôm nay)")
    ap.add_argument("--version", default=None, help="Phiên bản biểu thuế, VD 2026_08_08 (bỏ qua --date)")
    ap.add_argument("--origin", default=None, help="Nước xuất xứ, VD 'Viet Nam' (đánh dấu cột hiệp định cần đọc)")
    ap.add_argument("--list", action="store_true", help="Liệt kê mọi dòng 9 số của HS6")
    ap.add_argument("--json", action="store_true", help="Xuất JSON")
    ap.add_argument("--compact", action="store_true",
                    help="Bảng chỉ gồm cột MFN (General/Temporary/WTO/GSP/LDC) và cột hiệp định của --origin")
    ap.add_argument("--html", default=None, help="File HTML chương đã tải (offline)")
    args = ap.parse_args()

    m = re.fullmatch(r"(\d{4})\.?(\d{2})(?:[-.\s]?(\d{3}))?", args.code.strip())
    if not m:
        print("❌ --code phải dạng 1902.19-010 (hoặc 1902.19 với --list)", file=sys.stderr)
        return 1
    hs6 = f"{m.group(1)}.{m.group(2)}"
    stat = m.group(3)
    if not stat and not args.list:
        print("❌ Thiếu mã thống kê 3 số. Dùng --list để xem các dòng của " + hs6, file=sys.stderr)
        return 1

    try:
        target = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()
        version = args.version or pick_version(target)
        chapter = hs6[:2]
        url = f"{BASE}{version}/data/e_{chapter}.htm"
        page = open(args.html, encoding="utf-8", errors="ignore").read() if args.html else fetch(url)
        header, parsed = parse_rows(page)
    except Exception as e:  # noqa: BLE001
        print(f"❌ {e}", file=sys.stderr)
        return 1

    lines = find_lines(parsed, hs6, None if args.list else stat)
    if not lines:
        print(f"❌ Không thấy dòng {args.code} trong {url}. Kiểm tra lại mã (dùng --list).", file=sys.stderr)
        return 2

    fetched_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    schedule_date = version.replace("_", "-")

    if args.list:
        for row, anc in lines:
            path = " > ".join(a["desc"][:40] for a in anc[1:]) if anc else ""
            print(f"{hs6}-{row['stat']}  {path + ' > ' if path else ''}{row['desc']}")
        print(f"\nNguồn: {url} (biểu thuế ngày {schedule_date})")
        return 0

    row, anc = lines[0]
    res = resolve(row, anc, header)
    ALIASES = {"vn": "viet nam", "việt nam": "viet nam", "viet-nam": "viet nam", "th": "thailand", "id": "indonesia",
               "my": "malaysia", "ph": "philippines", "sg": "singapore", "cn": "china", "kr": "korea", "au": "australia"}
    okey = (args.origin or "").strip().lower()
    okey = ALIASES.get(okey, okey)
    if args.origin and okey not in ORIGIN_COLUMNS:
        sys.exit(f"✗ --origin '{args.origin}' không nhận ra. Dùng một trong: {', '.join(sorted(ORIGIN_COLUMNS))}")
    origin_cols = ORIGIN_COLUMNS.get(okey, [])
    origin_cols = [c for c in header if any(c.startswith(o) for o in origin_cols)]

    if args.json:
        print(json.dumps({"code": f"{hs6}-{row['stat']}", "description": row["desc"],
                          "path": [a["desc"] for a in anc], "schedule_version": schedule_date, "url": url,
                          "fetched_at": fetched_at, "origin": args.origin, "origin_columns": origin_cols,
                          "rates": res}, ensure_ascii=False, indent=2))
        return 0

    path = " > ".join(a["desc"] for a in anc)
    out = []
    out.append("<!-- TARIFF_LOOKUP v1 -->")
    out.append(f"**Tra cứu biểu thuế Nhật: `{hs6}-{row['stat']}`** ({row['desc']})")
    out.append("")
    out.append(f"- Nguồn: {url}")
    out.append(f"- Biểu thuế áp dụng: phiên bản ngày **{schedule_date}** (chọn theo ngày nhập {target.isoformat()})")
    out.append(f"- Truy cập: {fetched_at}")
    if path:
        out.append(f"- Nhánh phân loại: {path} > {row['desc']}")
    out.append("")
    out.append("| Cột biểu thuế | Ô gốc | Nguồn ô | Đọc là |")
    out.append("|---|---|---|---|")
    shown = [c for c in header if not args.compact or c in MFN_COLUMNS + ["GSP", "LDC", "Law"] or c in origin_cols]
    for col in shown:
        v = res[col]
        mark = " ★" if col in origin_cols else ""
        out.append(f"| {col}{mark} | {v['value'] or '(trống)'} | {v['from'] or '-'} | {interpret(v['value'], col)} |")
    out.append("")
    if origin_cols:
        out.append(f"**Cột cần đọc cho xuất xứ {args.origin}** (★):")
        for col in origin_cols:
            out.append(f"- {col}: {interpret(res[col]['value'], col)}")
        out.append("")
    out.append("Quy ước: ô trống ở cột hiệp định (kể cả dòng cha) = không có ưu đãi, áp MFN; \"Free\" = 0%; "
               "mức yen/kg là thuế theo lượng; mức trong ngoặc phải đọc chú giải biểu thuế. "
               "Ưu đãi chỉ được hưởng khi hàng đạt quy tắc xuất xứ (PSR) và có chứng từ hợp lệ. "
               "Cột Law liệt kê mã luật khác phải đáp ứng khi nhập (関税法第70条), tra bảng mã ở đầu trang nguồn.")
    out.append("<!-- /TARIFF_LOOKUP -->")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
