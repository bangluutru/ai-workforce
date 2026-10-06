#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnl_model.py - Mô hình P&L dùng chung cho build_excel_dashboard.py, export_slides_deck.py, verify_report.py.

Một nguồn định nghĩa duy nhất cho:
- Danh mục chỉ tiêu theo mẫu B02 (TT200 / TT133 / TT99) với MÃ SỐ ngữ nghĩa.
- Công thức của từng chỉ tiêu tính toán (dạng danh sách +/- mã số), từ đó sinh công thức Excel
  theo bản đồ mã số -> dòng thực tế (không hardcode số dòng).
- Kiểm tra (validate) data.json: thiếu trường bắt buộc -> raise DataError (KHÔNG tự điền số mẫu).
- Tính lại toàn bộ P&L bằng Python để đối chiếu chéo với kết quả Excel đã recalc.
"""

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


class DataError(Exception):
    """Lỗi dữ liệu đầu vào. Script gọi phải in thông báo và thoát mã != 0."""


# kind: input | sub (dòng "trong đó", không tham gia công thức) | calc | cit | ratio
_COMMON_HEAD = [
    ("01", "Doanh thu bán hàng và cung cấp dịch vụ", "input", None),
    ("02", "Các khoản giảm trừ doanh thu", "input", None),
    ("10", "Doanh thu thuần về bán hàng và cung cấp dịch vụ (10 = 01 - 02)", "calc", [("+", "01"), ("-", "02")]),
    ("11", "Giá vốn hàng bán", "input", None),
    ("20", "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ (20 = 10 - 11)", "calc", [("+", "10"), ("-", "11")]),
    ("GM", "Biên lợi nhuận gộp (20 / 10)", "ratio", ("20", "10")),
    ("21", "Doanh thu hoạt động tài chính", "input", None),
    ("22", "Chi phí tài chính", "input", None),
    ("23", "Trong đó: Chi phí lãi vay", "sub", None),
]

LINES = {
    # Mẫu B02-DN (TT 200/2014/TT-BTC)
    "TT200": _COMMON_HEAD + [
        ("25", "Chi phí bán hàng", "input", None),
        ("26", "Chi phí quản lý doanh nghiệp", "input", None),
        ("30", "Lợi nhuận thuần từ hoạt động kinh doanh {30 = 20 + (21 - 22) - (25 + 26)}", "calc",
         [("+", "20"), ("+", "21"), ("-", "22"), ("-", "25"), ("-", "26")]),
        ("31", "Thu nhập khác", "input", None),
        ("32", "Chi phí khác", "input", None),
        ("40", "Lợi nhuận khác (40 = 31 - 32)", "calc", [("+", "31"), ("-", "32")]),
        ("50", "Tổng lợi nhuận kế toán trước thuế (50 = 30 + 40)", "calc", [("+", "30"), ("+", "40")]),
        ("51", "Chi phí thuế TNDN hiện hành", "cit", None),
        ("52", "Chi phí thuế TNDN hoãn lại", "input", None),
        ("60", "Lợi nhuận sau thuế thu nhập doanh nghiệp (60 = 50 - 51 - 52)", "calc",
         [("+", "50"), ("-", "51"), ("-", "52")]),
        ("NM", "Biên lợi nhuận ròng (60 / 10)", "ratio", ("60", "10")),
    ],
    # Mẫu B02-DNN (TT 133/2016/TT-BTC)
    "TT133": _COMMON_HEAD + [
        ("24", "Chi phí quản lý kinh doanh", "input", None),
        ("30", "Lợi nhuận thuần từ hoạt động kinh doanh (30 = 20 + 21 - 22 - 24)", "calc",
         [("+", "20"), ("+", "21"), ("-", "22"), ("-", "24")]),
        ("31", "Thu nhập khác", "input", None),
        ("32", "Chi phí khác", "input", None),
        ("40", "Lợi nhuận khác (40 = 31 - 32)", "calc", [("+", "31"), ("-", "32")]),
        ("50", "Tổng lợi nhuận kế toán trước thuế (50 = 30 + 40)", "calc", [("+", "30"), ("+", "40")]),
        ("51", "Chi phí thuế TNDN", "cit", None),
        ("60", "Lợi nhuận sau thuế thu nhập doanh nghiệp (60 = 50 - 51)", "calc", [("+", "50"), ("-", "51")]),
        ("NM", "Biên lợi nhuận ròng (60 / 10)", "ratio", ("60", "10")),
    ],
}
# TT99/2025: dùng bố cục B02-DN của TT200, nhãn căn cứ gắn cờ xác minh (xem SKILL.md).
LINES["TT99"] = LINES["TT200"]

REGIME_LABEL = {
    "TT200": "Mẫu B02-DN - Thông tư 200/2014/TT-BTC",
    "TT133": "Mẫu B02-DNN - Thông tư 133/2016/TT-BTC",
    "TT99": "Mẫu B02-DN - Thông tư 99/2025/TT-BTC [CẦN XÁC MINH mẫu biểu và mã số chỉ tiêu]",
}

OPEX_CODES = {"TT200": ["25", "26"], "TT99": ["25", "26"], "TT133": ["24"]}
REQUIRED_INPUTS = ["01", "11"]
INPUT_KINDS = ("input", "sub")


def _num(v, where):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise DataError(f"{where}: phải là số (VNĐ), nhận được {v!r}. Không dùng chuỗi có dấu chấm/phẩy.")
    return v


def load_data(path):
    p = Path(path).expanduser()
    if not p.is_file():
        raise DataError(f"Không tìm thấy file dữ liệu: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise DataError(f"data.json không hợp lệ: {e}")
    validate(data)
    return data


def validate(data):
    """Kiểm tra data.json. Mọi thiếu sót -> DataError. Không có giá trị mặc định ngầm."""
    for key in ("company_name", "report_title", "period", "regime", "pnl"):
        if key not in data or data[key] in (None, ""):
            raise DataError(f"Thiếu trường bắt buộc '{key}' trong data.json (xem templates/data_schema.md).")
    regime = data["regime"]
    if regime not in LINES:
        raise DataError(f"regime '{regime}' không hỗ trợ. Chọn một trong: {', '.join(LINES)}")
    pnl = data["pnl"]
    if not isinstance(pnl, dict):
        raise DataError("'pnl' phải là object dạng {\"01\": {\"curr\": ..., \"prev\": ...}, ...}")

    lines = LINES[regime]
    allowed_inputs = {c for c, _, k, _ in lines if k in INPUT_KINDS} | {"51"}
    calc_codes = {c for c, _, k, _ in lines if k in ("calc", "ratio")}
    for code in pnl:
        if code in calc_codes:
            raise DataError(f"Mã {code} là chỉ tiêu TÍNH TOÁN (công thức sống), không được nhập số. Xóa '{code}' khỏi pnl.")
        if code not in allowed_inputs:
            raise DataError(f"Mã {code} không thuộc mẫu {regime}. Mã nhập được: {', '.join(sorted(allowed_inputs))}")
    for code in REQUIRED_INPUTS:
        if code not in pnl:
            raise DataError(f"Thiếu chỉ tiêu bắt buộc mã {code} trong pnl.")

    has_prev = any("prev" in v for v in pnl.values() if isinstance(v, dict))
    has_budget = any("budget" in v for v in pnl.values() if isinstance(v, dict))
    for code, v in pnl.items():
        if not isinstance(v, dict) or "curr" not in v:
            raise DataError(f"pnl['{code}'] phải có dạng {{\"curr\": số, ...}}")
        _num(v["curr"], f"pnl['{code}'].curr")
        if has_prev:
            if "prev" not in v:
                raise DataError(f"pnl['{code}'] thiếu 'prev' trong khi các dòng khác có kỳ trước. "
                                "Nhập đủ kỳ trước cho mọi dòng, hoặc bỏ 'prev' ở tất cả.")
            _num(v["prev"], f"pnl['{code}'].prev")
        if has_budget:
            if "budget" in v:
                _num(v["budget"], f"pnl['{code}'].budget")
            else:
                v["budget"] = 0
    data["_has_prev"] = has_prev
    data["_has_budget"] = has_budget

    if "51" not in pnl:
        cit = data.get("cit") or {}
        rate = cit.get("rate")
        if rate is None:
            raise DataError(
                "Thiếu chi phí thuế TNDN: nhập số thực tế vào pnl['51'] HOẶC khai báo cit.rate để ước tính. "
                "Thuế suất theo Luật Thuế TNDN 67/2025/QH15 (từ kỳ tính thuế 2025): 20% phổ thông; "
                "17% DN tổng doanh thu năm trên 3 tỷ đến 50 tỷ; 15% DN tổng doanh thu năm không quá 3 tỷ "
                "[CẦN XÁC MINH điều kiện áp dụng và cách xác định doanh thu tại NĐ 320/2025]. Không có thuế suất mặc định.")
        if isinstance(rate, (int, float)):
            rate = {"curr": rate, "prev": rate, "budget": rate}
        if not isinstance(rate, dict) or "curr" not in rate or (has_prev and "prev" not in rate):
            raise DataError("cit.rate phải là số (vd 0.15) hoặc {\"curr\": 0.15, \"prev\": 0.2}")
        if has_budget and "budget" not in rate:
            rate["budget"] = rate.get("curr", 0.2)
        for k, r in rate.items():
            _num(r, f"cit.rate.{k}")
            if not 0 <= r <= 0.5:
                raise DataError(f"cit.rate.{k}={r} bất thường (nhập dạng thập phân, vd 0.2)")
        data["_cit_rate"] = rate

    for i, q in enumerate(data.get("quarterly") or []):
        for k in ("label", "revenue", "cogs", "opex"):
            if k not in q:
                raise DataError(f"quarterly[{i}] thiếu '{k}'")
        for k in ("revenue", "cogs", "opex"):
            _num(q[k], f"quarterly[{i}].{k}")
    cash = data.get("cash")
    if cash is not None:
        if "label" not in cash or "curr" not in cash:
            raise DataError("cash phải có 'label' và 'curr'")
        _num(cash["curr"], "cash.curr")
    nar = data.get("narrative") or {}
    for h in nar.get("highlights", []):
        if not isinstance(h, str):
            raise DataError("narrative.highlights phải là danh sách chuỗi")
    for r in nar.get("recommendations", []):
        if not isinstance(r, dict) or "title" not in r or ("desc" not in r and "action" not in r):
            raise DataError("narrative.recommendations[] phải có 'title' và 'desc' (hoặc cấu trúc CMA: 'action', 'fact', 'root_cause')")
    return data


def present_lines(data):
    """Danh sách dòng hiển thị: dòng nhập liệu chỉ xuất hiện khi user có số liệu; dòng tính toán luôn có."""
    pnl = data["pnl"]
    out = []
    for code, name, kind, spec in LINES[data["regime"]]:
        if kind in INPUT_KINDS and code not in pnl:
            continue
        out.append((code, name, kind, spec))
    return out


def _round_half_up(x):
    return float(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def compute(data):
    """Tính lại P&L bằng Python, trả về {code: {period: v}} (ratio có thể là None)."""
    pnl = data["pnl"]
    periods = ["curr"]
    if data.get("_has_prev"):
        periods.append("prev")
    if data.get("_has_budget"):
        periods.append("budget")
    vals = {}
    for code, _, kind, spec in LINES[data["regime"]]:
        row = {}
        for p in periods:
            if kind in INPUT_KINDS:
                row[p] = pnl[code][p] if (code in pnl and p in pnl[code]) else 0
            elif kind == "calc":
                row[p] = sum((1 if s == "+" else -1) * vals[c][p] for s, c in spec)
            elif kind == "cit":
                if "51" in pnl and p in pnl["51"]:
                    row[p] = pnl["51"][p]
                else:
                    c_rate = data["_cit_rate"].get(p, data["_cit_rate"].get("curr", 0.2))
                    row[p] = _round_half_up(max(0.0, vals["50"][p] * c_rate))
            elif kind == "ratio":
                num, den = spec
                row[p] = None if vals[den][p] == 0 else vals[num][p] / vals[den][p]
        vals[code] = row
    opex = OPEX_CODES[data["regime"]]
    vals["OPEX"] = {p: sum(vals[c][p] for c in opex) for p in periods}
    return vals


def fmt_vnd(v):
    """Định dạng số tiền kiểu Việt Nam: 1.234.567 (âm trong ngoặc)."""
    if v is None:
        return "-"
    s = f"{abs(round(v)):,}".replace(",", ".")
    return f"({s})" if v < 0 else s


def fmt_pct(v, signed=False):
    if v is None:
        return "-"
    s = f"{v * 100:+.1f}%" if signed else f"{v * 100:.1f}%"
    return s.replace(".", ",")
