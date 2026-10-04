"""Thuế tiêu thụ đặc biệt (TTĐB): tính theo Biểu thuế Luật 66/2025/QH15 Điều 8.

Công thức: thuế TTĐB = giá tính thuế TTĐB x thuế suất (giá chưa có TTĐB, BVMT, GTGT; Điều 6 khoản 1).
Thuốc lá còn có mức thuế tuyệt đối từ 01/01/2027: trả về cả hai thành phần, cần xác minh cách kết hợp.
Không xử lý: hoàn thuế, khấu trừ thuế TTĐB nguyên liệu, giá tính thuế đặc thù (gôn, casino, xổ số).
"""
from __future__ import annotations

from typing import Optional

from rules_loader import ParamError, load, parse_date
from .common import D, Result, fmt, vnd

TOBACCO = {"thuoc_la_dieu": "thuoc_la_dieu_tuyet_doi_bao_20", "xi_ga": "xi_ga_tuyet_doi_dieu_20g",
           "thuoc_la_soi": "thuoc_la_soi_tuyet_doi_100g"}
FACTORS = {"hybrid": "he_so_o_to_hybrid_khi_thien_nhien", "sinh_hoc": "he_so_o_to_sinh_hoc"}


def list_items() -> list:
    rs = load("ttdb")
    return sorted(k for k in rs.data if not k.startswith("he_so") and not k.endswith("_ty_le") and "tuyet_doi" not in k) + sorted(TOBACCO)


def compute(item: str, price: float, quantity: float = 0, on="2026-12-31", factor: Optional[str] = None,
            price_includes_ttdb: bool = False) -> Result:
    """item: khóa trong standards/ttdb.json; price: giá tính thuế (chưa TTĐB) hoặc giá đã gồm TTĐB nếu price_includes_ttdb."""
    d = parse_date(on)
    rs = load("ttdb")
    r = Result(module="ttdb")
    if price < 0 or quantity < 0:
        raise ValueError("Giá và số lượng không được âm")
    key = item + "_ty_le" if item in TOBACCO else item
    rate = D(rs.value(key, d))
    if factor:
        if factor not in FACTORS:
            raise ValueError(f"factor phải là {sorted(FACTORS)}")
        rate = rate * D(rs.value(FACTORS[factor], d))
        r.step(f"Xe thân thiện môi trường ({factor}): thuế suất = hệ số x thuế suất xe cùng loại")
    base = D(price)
    if price_includes_ttdb:
        base = base / (1 + rate)
        r.step(f"Giá đã gồm TTĐB {fmt(price)} -> giá tính thuế = giá / (1 + {rate}) = {fmt(float(base))} (suy ra từ công thức, DERIVED)")
    tax_rate = base * rate
    total_tax = tax_rate
    r.values.update({"hang_hoa_dich_vu": item, "gia_tinh_thue": vnd(base), "thue_suat": float(rate), "thue_ttdb_ty_le": vnd(tax_rate)})
    r.step(f"Thuế TTĐB theo tỷ lệ ({rate*100:.0f}%) = {fmt(float(base))} x {rate} = {fmt(float(tax_rate))}")

    if item in TOBACCO:
        try:
            ab = D(rs.value(TOBACCO[item], d))
            tax_abs = ab * D(quantity)
            r.values["thue_tuyet_doi_moi_don_vi"] = float(ab)
            r.values["thue_tuyet_doi_tong"] = vnd(tax_abs)
            r.step(f"Mức thuế tuyệt đối {fmt(float(ab))} đ/đơn vị x {quantity} = {fmt(float(tax_abs))} (Luật 66/2025 và NĐ 360/2025 Điều 6, 7)")
            if price_includes_ttdb:
                # NĐ 360/2025/NĐ-CP Điều 6 khoản 1 điểm b:
                # Giá tính thuế TTĐB = (Giá bán chưa có thuế GTGT - Thuế tuyệt đối) / (1 + Thuế suất)
                base = (D(price) - tax_abs) / (1 + rate)
                tax_rate = base * rate
                r.values["gia_tinh_thue"] = vnd(base)
                r.values["thue_ttdb_ty_le"] = vnd(tax_rate)
                r.step(f"Theo NĐ 360/2025 Điều 6.1.b: Giá tính thuế theo tỷ lệ = ({fmt(price)} - {fmt(float(tax_abs))}) / (1 + {rate}) = {fmt(float(base))}")
                r.step(f"Thuế TTĐB theo tỷ lệ ({rate*100:.0f}%) = {fmt(float(tax_rate))}")
            total_tax = tax_rate + tax_abs
            r.step(f"Tổng thuế TTĐB phải nộp (tỷ lệ + tuyệt đối) = {fmt(float(total_tax))} đồng")
        except ParamError:
            r.step("Chưa đến mốc áp dụng mức thuế tuyệt đối (áp dụng từ 01/01/2027).")
    r.values["thue_ttdb"] = vnd(total_tax)
    r.provenance.extend(rs.provenance())
    r.flags.extend(rs.flags())
    r.warnings.append("Giá tính thuế phải loại trừ TTĐB, thuế BVMT, GTGT (Điều 6 Luật 66/2025 và NĐ 360/2025). Chưa tính khấu trừ TTĐB đầu vào.")
    return r
