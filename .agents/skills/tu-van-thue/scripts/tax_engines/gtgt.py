"""Thuế GTGT: phương pháp khấu trừ và phương pháp trực tiếp trên doanh thu (doanh nghiệp).

Căn cứ: Luật GTGT 48/2024/QH15 (Điều 9, 11, 12); NĐ 174/2025/NĐ-CP (giảm 2% đến 31/12/2026).
Hộ kinh doanh dùng engine hkd.py.
"""
from __future__ import annotations

from typing import Dict, List

from rules_loader import ParamError, load, parse_date
from .common import D, Result, fmt, vnd

RATE_CODES = {"0": None, "5": "thue_suat_uu_dai", "10": "thue_suat_chuan"}


def deduction(lines: List[dict], input_vat: float = 0.0, carry_forward: float = 0.0, on="2026-12-31") -> Result:
    """Phương pháp khấu trừ.

    lines: [{"name": str, "amount": doanh thu chưa thuế, "rate": "0"|"5"|"10"|"KCT", "reduction_eligible": bool}]
      rate "KCT" = không chịu thuế (không tính thuế đầu ra).
      reduction_eligible=True và rate "10": áp 8% nếu ngày `on` còn trong hiệu lực giảm thuế.
    input_vat: thuế GTGT đầu vào được khấu trừ trong kỳ. carry_forward: thuế đầu vào kỳ trước chuyển sang.
    """
    d = parse_date(on)
    gt = load("gtgt")
    r = Result(module="gtgt.khau_tru")
    out = D(0)
    for ln in lines:
        code = str(ln.get("rate", "10"))
        name = ln.get("name", "")
        amt = D(ln["amount"])
        if amt < 0:
            raise ValueError(f"Doanh thu âm ở dòng '{name}'")
        if code == "KCT":
            r.step(f"{name}: {fmt(amt)} không chịu thuế GTGT")
            continue
        if code not in RATE_CODES:
            raise ValueError(f"Thuế suất không hợp lệ '{code}' (0, 5, 10, KCT)")
        rate = D(0) if code == "0" else D(gt.value(RATE_CODES[code], d))
        if code == "10" and ln.get("reduction_eligible"):
            try:
                rate = D(gt.value("thue_suat_giam", d))
                r.warnings.append(f"'{name}' áp 8% theo NĐ 174/2025; cần xác nhận hàng hóa, dịch vụ không thuộc nhóm loại trừ (Phụ lục I, II). [CẦN XÁC MINH]")
            except ParamError:
                r.warnings.append(f"Ngày {d} nằm ngoài thời hạn giảm thuế GTGT: áp 10% cho '{name}'.")
        tax = amt * rate
        out += tax
        r.step(f"{name}: {fmt(amt)} x {rate*100:.0f}% = {fmt(tax)}")
    avail = D(input_vat) + D(carry_forward)
    net = out - avail
    r.values.update({"thue_dau_ra": vnd(out), "thue_dau_vao_khau_tru": vnd(avail),
                     "thue_phai_nop": vnd(max(D(0), net)), "thue_chuyen_ky_sau": vnd(max(D(0), -net))})
    r.step(f"Thuế phải nộp = đầu ra {fmt(out)} - đầu vào được khấu trừ {fmt(avail)} = {fmt(net)}")
    if net < 0:
        r.warnings.append("Số âm: chuyển kỳ sau; đề nghị hoàn thuế phải đáp ứng điều kiện riêng của Điều 15 Luật GTGT.")
    r.provenance, r.flags = gt.provenance(), gt.flags()
    return r


def direct(revenues: Dict[str, float], on="2026-12-31", reduction: bool = False) -> Result:
    """Phương pháp trực tiếp trên doanh thu cho doanh nghiệp có doanh thu năm dưới 1 tỷ (Điều 12 khoản 2 điểm a1)."""
    names = {"phan_phoi": "ty_le_truc_tiep_phan_phoi", "dich_vu": "ty_le_truc_tiep_dich_vu",
             "san_xuat": "ty_le_truc_tiep_san_xuat", "khac": "ty_le_truc_tiep_khac"}
    bad = [k for k in revenues if k not in names]
    if bad:
        raise ValueError(f"Loại hoạt động không hợp lệ: {bad}. Hợp lệ: {sorted(names)}")
    d = parse_date(on)
    gt = load("gtgt")
    r = Result(module="gtgt.truc_tiep")
    total = D(0)
    cut = D(gt.value("giam_ty_le_truc_tiep", d)) if reduction else D(0)
    tot_rev = sum(D(v) for v in revenues.values())
    limit = D(gt.value("nguong_dn_phuong_phap_truc_tiep", d))
    if tot_rev >= limit:
        r.warnings.append(f"Doanh thu {fmt(tot_rev)} từ 1 tỷ trở lên: doanh nghiệp thuộc diện phương pháp khấu trừ, "
                          "không áp dụng phương pháp trực tiếp (Điều 12 khoản 2 điểm a1).")
    for k, v in revenues.items():
        rate = D(gt.value(names[k], d)) * (1 - cut)
        t = D(v) * rate
        total += t
        r.step(f"{k}: {fmt(v)} x {rate*100:.2f}% = {fmt(t)}")
    r.values.update({"doanh_thu": vnd(tot_rev), "thue_phai_nop": vnd(total)})
    if reduction:
        r.warnings.append("Đã giảm 20% tỷ lệ % theo NĐ 174/2025 (đến hết 31/12/2026), chỉ cho hàng hóa, dịch vụ thuộc diện giảm. [CẦN XÁC MINH]")
    r.provenance, r.flags = gt.provenance(), gt.flags()
    return r
