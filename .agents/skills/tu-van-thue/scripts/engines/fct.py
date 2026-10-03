"""Thuế nhà thầu nước ngoài, phần thuế TNDN tính theo tỷ lệ % trên doanh thu tính thuế.

Căn cứ: NĐ 320/2025/NĐ-CP Điều 12 khoản 3 (bảng tỷ lệ); TT 20/2026/TT-BTC Điều 7 (công thức, gộp thuế vào giá).
Phần thuế GTGT của nhà thầu nước ngoài chưa được đưa vào tham số (chưa đọc nguyên văn): chỉ hướng dẫn.
"""
from __future__ import annotations

from rules_loader import load, parse_date
from .common import D, Result, fmt, vnd


def list_items() -> list:
    return sorted(load("fct").data)


def compute(item: str, revenue: float, on="2026-12-31", gross_up: bool = False) -> Result:
    """revenue: doanh thu tính thuế; nếu gross_up=True thì revenue là doanh thu THỰC NHẬN (net), bên Việt Nam chịu thuế hộ."""
    d = parse_date(on)
    rs = load("fct")
    r = Result(module="fct.tndn")
    if revenue < 0:
        raise ValueError("Doanh thu không được âm")
    rate = D(rs.value(item, d))
    base = D(revenue)
    if gross_up:
        base = base / (1 - rate)
        r.step(f"Gộp thuế vào giá: doanh thu tính thuế = doanh thu thực nhận / (1 - {rate}) = {fmt(float(base))} (TT 20/2026 Điều 7)")
    tax = base * rate
    r.values.update({"loai_thu_nhap": item, "doanh_thu_tinh_thue": vnd(base), "ty_le": float(rate), "thue_tndn_nha_thau": vnd(tax)})
    r.step(f"Thuế TNDN nhà thầu = {fmt(float(base))} x {rate} = {fmt(float(tax))}")
    r.provenance.extend(rs.provenance())
    r.flags.extend(rs.flags())
    r.warnings.append("Chỉ là phần thuế TNDN. Thuế GTGT nhà thầu, hiệp định tránh đánh thuế hai lần, điều kiện miễn thuế cần đối chiếu riêng.")
    return r
