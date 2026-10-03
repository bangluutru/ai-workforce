"""Thuế thu nhập doanh nghiệp: thuế suất theo doanh thu năm trước, miễn thuế dưới ngưỡng, kết chuyển lỗ.

Căn cứ: Luật TNDN 67/2025/QH15 Điều 10; NĐ 320/2025/NĐ-CP khoản 15 Điều 4 (bổ sung bởi NĐ 141/2026/NĐ-CP).
Không tính: ưu đãi thuế theo dự án, chuyển giá, thuế tối thiểu toàn cầu (chỉ hướng dẫn).
"""
from __future__ import annotations

from typing import Optional

from rules_loader import load, parse_date
from .common import D, Result, fmt, vnd


def compute(revenue: float, other_income: float = 0.0, deductible_expenses: float = 0.0,
            non_deductible_expenses: float = 0.0, exempt_income: float = 0.0,
            loss_carry: float = 0.0, prior_year_revenue: Optional[float] = None,
            on="2026-12-31") -> Result:
    """
    revenue: doanh thu bán hàng, dịch vụ của kỳ tính thuế.
    deductible_expenses: chi phí kế toán đã ghi nhận (tổng).
    non_deductible_expenses: phần chi phí không được trừ cần cộng lại.
    exempt_income: thu nhập được miễn thuế cần trừ.
    loss_carry: lỗ các năm trước còn được kết chuyển (người dùng xác nhận trong thời hạn luật định).
    prior_year_revenue: tổng doanh thu kỳ trước liền kề để chọn thuế suất và xét miễn thuế;
        bỏ trống thì dùng doanh thu kỳ này kèm cảnh báo.
    """
    d = parse_date(on)
    rs = load("tndn")
    r = Result(module="tndn")
    basis = prior_year_revenue
    if basis is None:
        basis = revenue + other_income
        r.warnings.append("Chưa có tổng doanh thu kỳ tính thuế liền kề trước; tạm dùng doanh thu kỳ này để chọn thuế suất. [CẦN XÁC MINH]")
    b = D(basis)
    exempt_limit = D(rs.value("nguong_mien_tndn", d))
    small = D(rs.value("nguong_dn_nho", d))
    mid = D(rs.value("nguong_dn_vua", d))

    income_total = D(revenue) + D(other_income)
    taxable = income_total - D(deductible_expenses) + D(non_deductible_expenses) - D(exempt_income)
    r.step(f"Thu nhập chịu thuế trước kết chuyển lỗ = doanh thu {fmt(revenue)} + thu nhập khác {fmt(other_income)} "
           f"- chi phí {fmt(deductible_expenses)} + chi phí không được trừ {fmt(non_deductible_expenses)} "
           f"- thu nhập miễn thuế {fmt(exempt_income)} = {fmt(taxable)}")
    r.values["thu_nhap_chiu_thue_truoc_lo"] = vnd(taxable)

    if b <= exempt_limit:
        r.values.update({"mien_thue": True, "thue_suat": 0, "thue_tndn": 0, "tong_doanh_thu_xet": vnd(b)})
        r.step(f"Tổng doanh thu xét {fmt(b)} không quá {fmt(exempt_limit)}: được miễn thuế TNDN")
        r.warnings.append("Miễn thuế không áp dụng nếu là công ty con hoặc có quan hệ liên kết mà doanh nghiệp trong quan hệ liên kết "
                          "không đáp ứng điều kiện (NĐ 141/2026 Điều 2). [CẦN XÁC MINH]")
        r.provenance, r.flags = rs.provenance(), rs.flags()
        return r

    if b <= small:
        rate = D(rs.value("thue_suat_dn_nho", d))
    elif b <= mid:
        rate = D(rs.value("thue_suat_dn_vua", d))
    else:
        rate = D(rs.value("thue_suat_chuan", d))
    after_loss = taxable
    used = D(0)
    if taxable > 0 and loss_carry > 0:
        used = min(taxable, D(loss_carry))
        after_loss = taxable - used
        r.step(f"Kết chuyển lỗ: {fmt(used)}")
        r.warnings.append("Lỗ chỉ được kết chuyển trong thời hạn luật định; người dùng cần xác nhận số lỗ còn được chuyển. [CẦN XÁC MINH]")
    tax = max(D(0), after_loss) * rate
    r.values.update({"mien_thue": False, "thue_suat": float(rate), "tong_doanh_thu_xet": vnd(b),
                     "lo_da_ket_chuyen": vnd(used), "thu_nhap_tinh_thue": vnd(max(D(0), after_loss)), "thue_tndn": vnd(tax)})
    r.step(f"Thuế suất {rate*100:.0f}% (theo tổng doanh thu xét {fmt(b)})")
    r.step(f"Thuế TNDN phải nộp = {fmt(max(D(0), after_loss))} x {rate*100:.0f}% = {fmt(tax)} đồng")
    if taxable < 0:
        r.warnings.append(f"Kỳ này lỗ {fmt(-taxable)}; có thể kết chuyển theo quy định.")
    r.provenance, r.flags = rs.provenance(), rs.flags()
    return r
