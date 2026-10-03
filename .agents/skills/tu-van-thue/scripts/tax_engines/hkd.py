"""Thuế hộ kinh doanh, cá nhân kinh doanh (GTGT + TNCN) từ kỳ tính thuế 2026.

Căn cứ: Luật TNCN 109/2025/QH15 Điều 7; Luật GTGT 48/2024/QH15 Điều 12; NĐ 68/2026/NĐ-CP (sửa bởi NĐ 141/2026/NĐ-CP).
Tham số lấy từ standards/hkd.json và standards/gtgt.json (có nguồn, có trạng thái kiểm chứng).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

from rules_loader import ParamError, load, parse_date
from .common import D, Result, fmt, vnd

# loại hoạt động -> (tham số TNCN theo doanh thu, tham số GTGT tỷ lệ trực tiếp, cờ giả định)
ACTIVITIES = {
    "phan_phoi":      ("tncn_dt_phan_phoi",      "ty_le_truc_tiep_phan_phoi", ""),
    "dich_vu":        ("tncn_dt_dich_vu",        "ty_le_truc_tiep_dich_vu", ""),
    "san_xuat":       ("tncn_dt_san_xuat",       "ty_le_truc_tiep_san_xuat", ""),
    "khac":           ("tncn_dt_khac",           "ty_le_truc_tiep_khac", ""),
    "cho_thue_tai_san": ("tncn_dt_cho_thue_dai_ly", "ty_le_truc_tiep_dich_vu",
                         "GTGT cho thuê tài sản xếp vào nhóm dịch vụ (5%) theo suy luận, cần đối chiếu NĐ 181/2025"),
    "dai_ly":         ("tncn_dt_cho_thue_dai_ly", "ty_le_truc_tiep_dich_vu",
                       "GTGT đại lý (bảo hiểm, xổ số, đa cấp) xếp vào nhóm dịch vụ (5%) theo suy luận, cần đối chiếu NĐ 181/2025"),
    "noi_dung_so":    ("tncn_dt_noi_dung_so",    "ty_le_truc_tiep_dich_vu",
                       "GTGT nội dung thông tin số xếp vào nhóm dịch vụ (5%) theo suy luận, cần đối chiếu văn bản"),
    "cho_thue_bds":   ("tncn_cho_thue_bds",      "ty_le_truc_tiep_dich_vu",
                       "GTGT cho thuê bất động sản xếp vào nhóm dịch vụ (5%) theo suy luận, cần đối chiếu văn bản"),
}


def compute(activities: Dict[str, float], expenses: Optional[float] = None, on="2026-12-31",
            vat_reduction: bool = False) -> Result:
    """activities: {loại_hoạt_động: doanh_thu_năm}. expenses: chi phí hợp lệ cả năm (nếu muốn tính theo lợi nhuận)."""
    bad = [k for k in activities if k not in ACTIVITIES]
    if bad:
        raise ValueError(f"Loại hoạt động không hợp lệ: {bad}. Hợp lệ: {sorted(ACTIVITIES)}")
    if any(v < 0 for v in activities.values()):
        raise ValueError("Doanh thu không được âm")
    d = parse_date(on)
    hk, gt = load("hkd"), load("gtgt")
    r = Result(module="hkd")
    revenue = sum(D(v) for v in activities.values())
    threshold = D(hk.value("nguong_mien_thue", d))
    r.values.update({"doanh_thu_nam": vnd(revenue), "nguong_mien_thue": vnd(threshold)})
    r.step(f"Tổng doanh thu năm = {fmt(revenue)}; ngưỡng không phải nộp GTGT, TNCN = {fmt(threshold)}")

    if revenue <= threshold:
        r.values.update({"gtgt": 0, "tncn": 0, "tong_thue": 0})
        r.step("Doanh thu không vượt ngưỡng: không chịu GTGT và không phải nộp TNCN (vẫn thực hiện thông báo doanh thu theo quy định).")
        _finish(r, hk, gt)
        return r

    # --- GTGT: tỷ lệ % x toàn bộ doanh thu ---
    gtgt = D(0)
    reduction = D(gt.value("giam_ty_le_truc_tiep", d)) if vat_reduction else D(0)
    if vat_reduction:
        r.warnings.append("Đã giảm 20% tỷ lệ % GTGT (NĐ 174/2025, đến hết 31/12/2026). Chỉ áp dụng cho hàng hóa, dịch vụ thuộc diện được giảm; "
                          "không áp dụng nhóm loại trừ (viễn thông, tài chính, bất động sản, kim loại, khai khoáng, hàng chịu TTĐB). [CẦN XÁC MINH]")
    for act, rev in activities.items():
        if not rev:
            continue
        rate = D(gt.value(ACTIVITIES[act][1], d)) * (1 - reduction)
        line = D(rev) * rate
        gtgt += line
        r.step(f"GTGT {act}: {fmt(rev)} x {rate*100:.2f}% = {fmt(line)}")
        if ACTIVITIES[act][2]:
            r.warnings.append(f"[CẦN XÁC MINH] {ACTIVITIES[act][2]}")

    # --- TNCN ---
    method_a = None
    if revenue <= D(hk.value("nguong_pp_doanh_thu", d)):
        method_a = _tncn_by_revenue(activities, threshold, hk, d, r)
    method_b = None
    if expenses is not None:
        method_b = _tncn_by_profit(revenue, D(expenses), hk, d, r)
    if method_a is None and method_b is None:
        raise ValueError("Doanh thu trên 3 tỷ đồng bắt buộc tính TNCN theo lợi nhuận: cần nhập chi phí hợp lệ (--expenses)")
    if method_a is not None and method_b is not None:
        choice = "doanh_thu" if method_a <= method_b else "loi_nhuan"
        r.step(f"Doanh thu từ trên ngưỡng đến 3 tỷ được chọn 1 trong 2 cách: theo doanh thu = {fmt(method_a)}, theo lợi nhuận = {fmt(method_b)}. "
               f"Cách thấp hơn: {'theo doanh thu' if choice=='doanh_thu' else 'theo lợi nhuận'}.")
        r.warnings.append("Phương pháp đã chọn phải ổn định tối thiểu 02 năm liên tục kể từ năm đầu áp dụng (NĐ 68/2026 Điều 4 khoản 5 điểm d). "
                          "Chọn theo lợi nhuận đòi hỏi hóa đơn, chứng từ chi phí hợp lệ.")
        tncn = min(method_a, method_b)
        r.values["tncn_theo_doanh_thu"] = vnd(method_a)
        r.values["tncn_theo_loi_nhuan"] = vnd(method_b)
        r.values["phuong_phap_tncn"] = choice
    elif method_a is not None:
        tncn, r.values["phuong_phap_tncn"] = method_a, "doanh_thu"
        r.values["tncn_theo_doanh_thu"] = vnd(method_a)
    else:
        tncn, r.values["phuong_phap_tncn"] = method_b, "loi_nhuan"
        r.values["tncn_theo_loi_nhuan"] = vnd(method_b)
    r.values.update({"gtgt": vnd(gtgt), "tncn": vnd(tncn), "tong_thue": vnd(gtgt + tncn)})
    r.step(f"Tổng thuế phải nộp = GTGT {fmt(gtgt)} + TNCN {fmt(tncn)} = {fmt(gtgt + tncn)} đồng")
    _finish(r, hk, gt)
    return r


def _tncn_by_revenue(activities, threshold, hk, d, r) -> Decimal:
    """Doanh thu tính thuế = doanh thu vượt ngưỡng. Phần được trừ (ngưỡng) phân bổ vào hoạt động thuế suất cao nhất (có lợi nhất)."""
    rates = {a: D(hk.value(ACTIVITIES[a][0], d)) for a in activities if activities[a]}
    remaining = threshold
    total = D(0)
    for act in sorted(rates, key=lambda a: rates[a], reverse=True):
        rev = D(activities[act])
        deduct = min(rev, remaining)
        remaining -= deduct
        base = rev - deduct
        t = base * rates[act]
        total += t
        r.step(f"TNCN theo doanh thu {act}: ({fmt(rev)} - phần trừ {fmt(deduct)}) x {rates[act]*100:.2f}% = {fmt(t)}")
    r.warnings.append("Phần trừ ngưỡng được phân bổ vào hoạt động có thuế suất cao nhất để có lợi nhất cho người nộp thuế "
                      "(NĐ 68/2026 Điều 4 khoản 3: tổng mức trừ không vượt ngưỡng trong một năm).")
    if "cho_thue_bds" in activities and len([a for a in activities if activities[a]]) > 1:
        r.warnings.append("[CẦN XÁC MINH] Có cả cho thuê bất động sản và kinh doanh khác: NĐ 68 Điều 4 khoản 3 và 4 quy định mức trừ riêng cho từng nhóm, cần đối chiếu cách phân bổ.")
    return total


def _tncn_by_profit(revenue, expenses, hk, d, r) -> Decimal:
    if revenue <= D(hk.value("nguong_pp_doanh_thu", d)):
        rate = D(hk.value("tncn_loi_nhuan_den_3ty", d))
    elif revenue <= D(50_000_000_000):
        rate = D(hk.value("tncn_loi_nhuan_3_50ty", d))
    else:
        rate = D(hk.value("tncn_loi_nhuan_tren_50ty", d))
    profit = revenue - expenses
    t = max(D(0), profit) * rate
    r.step(f"TNCN theo lợi nhuận: ({fmt(revenue)} - chi phí {fmt(expenses)}) x {rate*100:.0f}% = {fmt(t)}")
    if profit < 0:
        r.warnings.append("Chi phí lớn hơn doanh thu: thu nhập tính thuế bằng 0.")
    return t


def _finish(r: Result, *rulesets) -> None:
    for rs in rulesets:
        r.provenance += rs.provenance()
        r.flags += rs.flags()
