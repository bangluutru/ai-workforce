"""Tiền chậm nộp thuế (module quản lý thuế).

Công thức: tiền chậm nộp = tiền thuế chậm nộp x mức/ngày x số ngày chậm nộp.
Số ngày tính liên tục từ ngày liền sau hạn nộp đến ngày liền trước ngày thực nộp (đã gồm cả hai đầu).
Mức/ngày lấy từ standards/quan_ly_thue.json (có nguồn, có ngày hiệu lực).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from rules_loader import load, parse_date
from .common import Result, fmt, vnd


def late_payment(amount: float, due_date, paid_date, rate_override: Optional[float] = None) -> Result:
    """Tính tiền chậm nộp.

    due_date: hạn nộp thuế (ngày cuối cùng được nộp không bị phạt).
    paid_date: ngày thực nộp vào NSNN. Số ngày chậm = (paid_date - due_date) - 1; nộp đúng hạn hoặc sát hạn = 0.
    Ví dụ: hạn 30/04, nộp 05/05 -> chậm các ngày 01,02,03,04 tháng 5 = 4 ngày (không tính ngày nộp).
    """
    due, paid = parse_date(due_date), parse_date(paid_date)
    r = Result(module="quan_ly_thue.cham_nop")
    if amount < 0:
        raise ValueError("Số thuế chậm nộp không được âm")
    days = max(0, (paid - due).days - 1)  # từ ngày liền sau hạn đến ngày liền trước ngày nộp
    rs = load("quan_ly_thue")
    if rate_override is not None:
        rate = rate_override
        r.warnings.append("Dùng mức/ngày do người dùng nhập, không phải tham số có nguồn.")
    else:
        # Mức áp dụng theo giai đoạn: xét theo từng ngày chậm; hiện chỉ có 1 mức cho mọi giai đoạn.
        first_late = due + timedelta(days=1)
        rate = rs.value("muc_cham_nop_ngay", first_late)
        if days:
            end_rate = rs.value("muc_cham_nop_ngay", paid - timedelta(days=1))
            if end_rate != rate:
                r.warnings.append("Mức chậm nộp thay đổi trong thời gian chậm; cần tách từng giai đoạn.")
    interest = amount * rate * days
    r.values.update({"so_thue_cham_nop": vnd(amount), "han_nop": due.isoformat(),
                     "ngay_nop": paid.isoformat(), "so_ngay_cham": days,
                     "muc_ngay": rate, "tien_cham_nop": vnd(interest),
                     "tong_phai_nop": vnd(amount + interest)})
    r.step(f"Số ngày chậm = ({paid.isoformat()} - {due.isoformat()}) - 1 = {days} ngày")
    r.step(f"Tiền chậm nộp = {fmt(amount)} x {rate*100:.2f}% x {days} = {fmt(interest)} đồng")
    r.provenance = rs.provenance()
    r.flags = rs.flags()
    return r
