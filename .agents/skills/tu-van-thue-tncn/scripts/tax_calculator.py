#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tax_calculator.py — Công cụ tính toán thuế Thu nhập cá nhân (TNCN) Việt Nam 2026
Theo chuẩn Luật 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP, TT 87/2026/TT-BTC.

Hỗ trợ:
- Tính thuế TNCN tiền lương Gross -> Net (Biểu lũy tiến 5 bậc 2026)
- Quy đổi tiền lương Net -> Gross (Chính xác 100% không sai số)
- Quyết toán thuế năm cho người có thu nhập nhiều nơi (Tính số thuế nộp thêm hoặc hoàn lại)
- Khấu trừ thuế vãng lai 10% (Ngưỡng mới >= 5 triệu đồng/lần)
- Thuế chuyển nhượng bất động sản (2%) và thẩm định miễn thuế nhà đất duy nhất
- Ước tính mức hưởng BHXH rút 1 lần & so sánh định lượng với bảo lưu lương hưu
"""

import sys
import argparse
import json
from typing import Dict, Any, List

# Các hằng số quy chuẩn 2026
BASE_SALARY = 2_530_000                  # Lương cơ sở từ 01/07/2026 (NĐ 161/2026/NĐ-CP)
INSURANCE_CAP_SALARY = 50_600_000       # Trần đóng BHXH, BHYT (20 x lương cơ sở)
RATE_BHXH = 0.08                        # 8% BHXH người lao động
RATE_BHYT = 0.015                       # 1.5% BHYT người lao động
RATE_BHTN = 0.01                        # 1% BHTN người lao động

DEDUCTION_PERSONAL = 15_500_000         # Giảm trừ bản thân: 15,5 tr/tháng (186tr/năm)
DEDUCTION_DEPENDENT = 6_200_000         # Giảm trừ người phụ thuộc: 6,2 tr/người/tháng
MAX_PENSION_DEDUCTION_MONTHLY = 3_000_000 # Tối đa hưu trí tự nguyện: 3 tr/tháng
MAX_MEDICAL_ANNUAL = 23_000_000         # Y tế tối đa 23 tr/năm (~1.916.667đ/tháng)
MAX_EDUCATION_ANNUAL = 24_000_000       # Giáo dục tối đa 24 tr/năm (2 tr/tháng)

ADHOC_WITHHOLDING_THRESHOLD = 5_000_000  # Ngưỡng khấu trừ vãng lai: từ 5 tr trở lên
ADHOC_WITHHOLDING_RATE = 0.10            # Tỷ lệ khấu trừ vãng lai: 10%

# Biểu thuế lũy tiến 5 bậc 2026 (Luật 109/2025/QH15 Điều 22)
TAX_BRACKETS_2026 = [
    {"bracket": 1, "threshold": 10_000_000, "rate": 0.05, "quick_sub": 0},
    {"bracket": 2, "threshold": 30_000_000, "rate": 0.10, "quick_sub": 500_000},
    {"bracket": 3, "threshold": 60_000_000, "rate": 0.20, "quick_sub": 3_500_000},
    {"bracket": 4, "threshold": 100_000_000, "rate": 0.30, "quick_sub": 9_500_000},
    {"bracket": 5, "threshold": float("inf"), "rate": 0.35, "quick_sub": 14_500_000},
]


def calculate_compulsory_insurance(gross_salary: float, bhtn_cap: float = 0.0) -> Dict[str, float]:
    """Tính các khoản bảo hiểm bắt buộc theo tỷ lệ của người lao động."""
    sal_for_shui = min(gross_salary, INSURANCE_CAP_SALARY)
    bhxh = sal_for_shui * RATE_BHXH
    bhyt = sal_for_shui * RATE_BHYT
    
    sal_for_bhtn = min(gross_salary, bhtn_cap) if bhtn_cap > 0 else gross_salary
    bhtn = sal_for_bhtn * RATE_BHTN
    
    total_insurance = bhxh + bhyt + bhtn
    return {
        "bhxh": bhxh,
        "bhyt": bhyt,
        "bhtn": bhtn,
        "total": total_insurance,
        "sal_capped_shui": sal_for_shui,
    }


def calculate_progressive_pit(taxable_income: float) -> Dict[str, Any]:
    """
    Tính thuế TNCN theo biểu thuế lũy tiến từng phần 5 bậc 2026.
    Tách chi tiết từng bậc để người dùng đối soát chính xác.
    """
    if taxable_income <= 0:
        return {
            "taxable_income": 0,
            "total_tax": 0,
            "bracket_details": [],
            "quick_formula": "Thu nhập tính thuế <= 0 -> Thuế = 0 VNĐ"
        }

    bracket_details: List[Dict[str, Any]] = []
    rem = taxable_income
    prev_thresh = 0.0
    total_tax = 0.0

    limits = [10_000_000, 30_000_000, 60_000_000, 100_000_000, float("inf")]
    rates = [0.05, 0.10, 0.20, 0.30, 0.35]

    for i, (lim, rate) in enumerate(zip(limits, rates), start=1):
        span = lim - prev_thresh
        taxable_in_bracket = min(max(rem, 0.0), span)
        tax_bracket = taxable_in_bracket * rate
        total_tax += tax_bracket
        rem -= taxable_in_bracket

        if taxable_in_bracket > 0:
            bracket_details.append({
                "bracket": i,
                "range": f"{prev_thresh:,.0f} - {lim:,.0f}" if lim != float("inf") else f"> {prev_thresh:,.0f}",
                "rate": f"{int(rate*100)}%",
                "amount": taxable_in_bracket,
                "tax": tax_bracket,
            })

        prev_thresh = lim
        if rem <= 0:
            break

    quick_desc = ""
    if taxable_income <= 10_000_000:
        quick_desc = f"{taxable_income:,.0f} * 5% = {taxable_income*0.05:,.0f}"
    elif taxable_income <= 30_000_000:
        quick_desc = f"{taxable_income:,.0f} * 10% - 500,000 = {taxable_income*0.10 - 500_000:,.0f}"
    elif taxable_income <= 60_000_000:
        quick_desc = f"{taxable_income:,.0f} * 20% - 3,500,000 = {taxable_income*0.20 - 3_500_000:,.0f}"
    elif taxable_income <= 100_000_000:
        quick_desc = f"{taxable_income:,.0f} * 30% - 9,500,000 = {taxable_income*0.30 - 9_500_000:,.0f}"
    else:
        quick_desc = f"{taxable_income:,.0f} * 35% - 14,500,000 = {taxable_income*0.35 - 14_500_000:,.0f}"

    return {
        "taxable_income": taxable_income,
        "total_tax": round(total_tax),
        "bracket_details": bracket_details,
        "quick_formula": quick_desc,
    }


def calculate_monthly_salary_tax(
    gross_salary: float,
    num_dependents: int = 0,
    voluntary_pension_monthly: float = 0.0,
    medical_deduction_monthly: float = 0.0,
    education_deduction_monthly: float = 0.0,
    bhtn_cap: float = 0.0
) -> Dict[str, Any]:
    """Tính toán toàn diện thuế TNCN và lương thực nhận (Net) theo tháng từ lương Gross."""
    insurance = calculate_compulsory_insurance(gross_salary, bhtn_cap)
    
    giam_tru_ban_than = DEDUCTION_PERSONAL
    giam_tru_npt = num_dependents * DEDUCTION_DEPENDENT
    giam_tru_pension = min(voluntary_pension_monthly, MAX_PENSION_DEDUCTION_MONTHLY)
    giam_tru_medical = min(medical_deduction_monthly, MAX_MEDICAL_ANNUAL / 12)
    giam_tru_education = min(education_deduction_monthly, MAX_EDUCATION_ANNUAL / 12)

    total_deductions = (
        insurance["total"] +
        giam_tru_ban_than +
        giam_tru_npt +
        giam_tru_pension +
        giam_tru_medical +
        giam_tru_education
    )

    taxable_income = max(0.0, gross_salary - total_deductions)
    tax_result = calculate_progressive_pit(taxable_income)
    pit = tax_result["total_tax"]
    net_salary = gross_salary - insurance["total"] - pit

    return {
        "gross_salary": gross_salary,
        "insurance": insurance,
        "deductions": {
            "personal": giam_tru_ban_than,
            "dependents_count": num_dependents,
            "dependents_total": giam_tru_npt,
            "voluntary_pension": giam_tru_pension,
            "medical": giam_tru_medical,
            "education": giam_tru_education,
            "total_deductions": total_deductions,
        },
        "taxable_income": taxable_income,
        "tax": tax_result,
        "net_salary": round(net_salary),
        "effective_tax_rate_percent": round((pit / gross_salary * 100), 2) if gross_salary > 0 else 0.0,
    }


def convert_net_to_gross(
    net_salary: float,
    num_dependents: int = 0,
    voluntary_pension_monthly: float = 0.0,
    medical_deduction_monthly: float = 0.0,
    education_deduction_monthly: float = 0.0,
    bhtn_cap: float = 0.0
) -> Dict[str, Any]:
    """
    Quy đổi từ lương Net sang lương Gross chính xác 100%.
    Sử dụng thuật toán tìm kiếm nhị phân (Binary Search) trên hàm đơn điệu Net(Gross).
    """
    low = net_salary
    high = max(net_salary * 2.5, 100_000_000)
    
    for _ in range(60):
        mid = (low + high) / 2.0
        calc = calculate_monthly_salary_tax(
            gross_salary=mid,
            num_dependents=num_dependents,
            voluntary_pension_monthly=voluntary_pension_monthly,
            medical_deduction_monthly=medical_deduction_monthly,
            education_deduction_monthly=education_deduction_monthly,
            bhtn_cap=bhtn_cap
        )
        if calc["net_salary"] < net_salary:
            low = mid
        else:
            high = mid

    final_gross = round(high)
    result = calculate_monthly_salary_tax(
        gross_salary=final_gross,
        num_dependents=num_dependents,
        voluntary_pension_monthly=voluntary_pension_monthly,
        medical_deduction_monthly=medical_deduction_monthly,
        education_deduction_monthly=education_deduction_monthly,
        bhtn_cap=bhtn_cap
    )
    result["mode"] = "net_to_gross"
    result["target_net"] = net_salary
    return result


def calculate_annual_settlement(
    annual_gross_income: float,
    annual_insurance_paid: float = 0.0,
    num_dependents: int = 0,
    annual_medical: float = 0.0,
    annual_education: float = 0.0,
    annual_pension: float = 0.0,
    tax_already_withheld: float = 0.0,
    months_worked: int = 12
) -> Dict[str, Any]:
    """
    Quyết toán thuế TNCN năm cho cá nhân có thu nhập từ 1 hoặc nhiều nơi.
    Tính toán số thuế phải nộp cả năm và số tiền được HOÀN hoặc PHẢI NỘP THÊM.
    """
    personal_deduction_annual = DEDUCTION_PERSONAL * months_worked
    dependent_deduction_annual = num_dependents * DEDUCTION_DEPENDENT * months_worked
    medical_deduction = min(annual_medical, MAX_MEDICAL_ANNUAL)
    education_deduction = min(annual_education, MAX_EDUCATION_ANNUAL)
    pension_deduction = min(annual_pension, MAX_PENSION_DEDUCTION_MONTHLY * months_worked)

    total_deductions = (
        annual_insurance_paid +
        personal_deduction_annual +
        dependent_deduction_annual +
        medical_deduction +
        education_deduction +
        pension_deduction
    )

    annual_taxable_income = max(0.0, annual_gross_income - total_deductions)
    
    # Biểu lũy tiến năm = 12 x Biểu tháng
    # Bậc 1: đến 120tr (5%)
    # Bậc 2: 120tr - 360tr (10%)
    # Bậc 3: 360tr - 720tr (20%)
    # Bậc 4: 720tr - 1200tr (30%)
    # Bậc 5: trên 1200tr (35%)
    annual_limits = [120_000_000, 360_000_000, 720_000_000, 1_200_000_000, float("inf")]
    rates = [0.05, 0.10, 0.20, 0.30, 0.35]

    rem = annual_taxable_income
    prev_thresh = 0.0
    annual_pit = 0.0
    brackets = []

    for i, (lim, rate) in enumerate(zip(annual_limits, rates), start=1):
        span = lim - prev_thresh
        in_bracket = min(max(rem, 0.0), span)
        tax_bracket = in_bracket * rate
        annual_pit += tax_bracket
        rem -= in_bracket
        if in_bracket > 0:
            brackets.append({
                "bracket": i,
                "range": f"{prev_thresh:,.0f} - {lim:,.0f}" if lim != float("inf") else f"> {prev_thresh:,.0f}",
                "rate": f"{int(rate*100)}%",
                "amount": in_bracket,
                "tax": tax_bracket,
            })
        prev_thresh = lim
        if rem <= 0:
            break

    annual_pit_rounded = round(annual_pit)
    diff = tax_already_withheld - annual_pit_rounded

    status = "CAN_BANG"
    status_msg = "Số thuế đã tạm nộp khớp chính xác với nghĩa vụ thuế cả năm."
    if diff > 50_000:
        status = "HOAN_THUE"
        status_msg = f"Được hoàn thuế TNCN nộp thừa: {diff:,.0f} VNĐ"
    elif diff < -50_000:
        status = "NOP_THEM"
        status_msg = f"Phải nộp thêm thuế TNCN sau quyết toán: {abs(diff):,.0f} VNĐ"
    else:
        status = "KHONG_PHAI_QUYET_TOAN"
        status_msg = f"Chênh lệch {abs(diff):,.0f} VNĐ (<= 50.000 VNĐ), được miễn thủ tục nộp thêm theo quy định."

    return {
        "annual_gross_income": annual_gross_income,
        "annual_insurance_paid": annual_insurance_paid,
        "deductions": {
            "personal_annual": personal_deduction_annual,
            "dependents_count": num_dependents,
            "dependents_annual": dependent_deduction_annual,
            "medical_annual": medical_deduction,
            "education_annual": education_deduction,
            "pension_annual": pension_deduction,
            "total_deductions": total_deductions,
        },
        "annual_taxable_income": annual_taxable_income,
        "brackets": brackets,
        "annual_pit_liability": annual_pit_rounded,
        "tax_already_withheld": tax_already_withheld,
        "difference": diff,
        "settlement_status": status,
        "status_message": status_msg
    }


def calculate_real_estate_tax(
    transfer_value: float,
    is_relative: bool = False,
    is_sole_property: bool = False,
    ownership_days: int = 0,
    is_full_transfer: bool = True
) -> Dict[str, Any]:
    """
    Tính thuế chuyển nhượng bất động sản và thẩm định điều kiện miễn thuế.
    Căn cứ Điều 18 và Điều 19 Nghị định 253/2026/NĐ-CP.
    """
    if is_relative:
        return {
            "transfer_value": transfer_value,
            "tax_rate": 0.0,
            "tax_amount": 0,
            "is_exempt": True,
            "exemption_ground": "Miễn thuế 100% theo Điều 18 NĐ 253/2026/NĐ-CP (Chuyển nhượng/tặng cho giữa người thân trong gia đình)."
        }

    if is_sole_property:
        conditions_met = []
        conditions_failed = []
        
        conditions_met.append("Điều kiện 1: Sở hữu duy nhất một nhà ở/thửa đất ở tại Việt Nam.")
        
        if ownership_days >= 183:
            conditions_met.append(f"Điều kiện 2: Thời gian sở hữu đạt {ownership_days} ngày (>= 183 ngày tính từ ngày cấp Sổ đỏ).")
        else:
            conditions_failed.append(f"Điều kiện 2 CHƯA ĐẠT: Thời gian sở hữu mới đạt {ownership_days} ngày (yêu cầu tối thiểu 183 ngày).")

        if is_full_transfer:
            conditions_met.append("Điều kiện 3: Chuyển nhượng toàn bộ diện tích nhà ở, đất ở.")
        else:
            conditions_failed.append("Điều kiện 3 CHƯA ĐẠT: Chỉ chuyển nhượng một phần diện tích (không được miễn cho phần chuyển nhượng).")

        if len(conditions_failed) == 0:
            return {
                "transfer_value": transfer_value,
                "tax_rate": 0.0,
                "tax_amount": 0,
                "is_exempt": True,
                "exemption_ground": "Miễn thuế 100% theo Điều 19 NĐ 253/2026/NĐ-CP (Chuyển nhượng nhà ở, quyền sử dụng đất ở duy nhất đáp ứng đủ 3 điều kiện).",
                "checklist": conditions_met
            }
        else:
            tax = transfer_value * 0.02
            return {
                "transfer_value": transfer_value,
                "tax_rate": 0.02,
                "tax_amount": round(tax),
                "is_exempt": False,
                "exemption_ground": "Không đủ điều kiện miễn thuế nhà đất duy nhất do vi phạm tiêu chí sở hữu.",
                "checklist_passed": conditions_met,
                "checklist_failed": conditions_failed
            }

    tax = transfer_value * 0.02
    return {
        "transfer_value": transfer_value,
        "tax_rate": 0.02,
        "tax_amount": round(tax),
        "is_exempt": False,
        "exemption_ground": "Thuộc diện nộp thuế chuyển nhượng BĐS 2% thông thường theo Luật 109/2025/QH15."
    }


def calculate_bhxh_lump_sum(
    years_before_2014: float,
    years_from_2014: float,
    mbqtl: float
) -> Dict[str, Any]:
    """
    Tính mức hưởng BHXH một lần và so sánh với phương án bảo lưu nhận lương hưu.
    Căn cứ Luật Bảo hiểm xã hội 2024 (Số 41/2024/QH15).
    """
    months_before = years_before_2014 * 1.5
    months_from = years_from_2014 * 2.0
    total_months_entitled = months_before + months_from
    lump_sum_amount = round(total_months_entitled * mbqtl)

    total_years = years_before_2014 + years_from_2014
    
    # Ước tính lương hưu nếu bảo lưu đủ 20 năm
    # Tỷ lệ hưởng lương hưu tối thiểu 45% MBQTL
    est_pension_monthly = round(mbqtl * 0.45)
    est_pension_annual = est_pension_monthly * 12
    est_pension_20years = est_pension_annual * 20

    return {
        "years_before_2014": years_before_2014,
        "years_from_2014": years_from_2014,
        "total_years": total_years,
        "mbqtl": mbqtl,
        "months_entitled": total_months_entitled,
        "lump_sum_amount": lump_sum_amount,
        "formula": f"({years_before_2014} năm x 1.5) + ({years_from_2014} năm x 2.0) = {total_months_entitled} tháng x {mbqtl:,.0f} VNĐ",
        "pension_comparison": {
            "monthly_pension_min": est_pension_monthly,
            "annual_pension": est_pension_annual,
            "twenty_year_pension_total": est_pension_20years,
            "free_health_insurance": "Được cấp thẻ BHYT miễn phí với mức thanh toán lên đến 95%",
            "cpi_adjustment": "Lương hưu được Nhà nước điều chỉnh tăng định kỳ theo CPI"
        }
    }


def calculate_adhoc_income_tax(amount: float) -> Dict[str, Any]:
    """
    Tính thuế khấu trừ vãng lai 10% (Theo Thông tư 87/2026/TT-BTC).
    Chỉ khấu trừ khi chi trả từ 5.000.000 VNĐ/lần trở lên.
    """
    if amount < ADHOC_WITHHOLDING_THRESHOLD:
        return {
            "gross_amount": amount,
            "is_withheld": False,
            "tax_rate": 0.0,
            "tax_amount": 0,
            "net_amount": amount,
            "note": "Dưới ngưỡng 5.000.000 VNĐ/lần, không bị khấu trừ tại nguồn 10% (TT 87/2026/TT-BTC)."
        }
    tax = amount * ADHOC_WITHHOLDING_RATE
    return {
        "gross_amount": amount,
        "is_withheld": True,
        "tax_rate": 0.10,
        "tax_amount": round(tax),
        "net_amount": round(amount - tax),
        "note": "Thuộc diện khấu trừ 10% tại nguồn theo TT 87/2026/TT-BTC."
    }


def format_currency(val: float) -> str:
    """Định dạng số tiền sang chuẩn VNĐ dễ đọc."""
    return f"{round(val):,}".replace(",", ".") + " VNĐ"


def main():
    parser = argparse.ArgumentParser(description="Công cụ tính toán thuế TNCN Việt Nam 2026 đa năng")
    parser.add_argument("--gross", type=float, help="Lương Gross hàng tháng (VNĐ)")
    parser.add_argument("--net", type=float, help="Lương Net hàng tháng muốn quy đổi sang Gross (VNĐ)")
    parser.add_argument("--dependents", type=int, default=0, help="Số người phụ thuộc")
    parser.add_argument("--pension", type=float, default=0.0, help="Hưu trí tự nguyện hàng tháng (VNĐ)")
    parser.add_argument("--medical", type=float, default=0.0, help="Chi phí Y tế hàng tháng (VNĐ)")
    parser.add_argument("--education", type=float, default=0.0, help="Chi phí Giáo dục hàng tháng (VNĐ)")
    parser.add_argument("--adhoc", type=float, help="Thu nhập vãng lai / hợp đồng dịch vụ (VNĐ)")
    
    # Quyết toán năm
    parser.add_argument("--settlement-income", type=float, help="Tổng thu nhập chịu thuế cả năm khi quyết toán (VNĐ)")
    parser.add_argument("--settlement-insurance", type=float, default=0.0, help="Tổng bảo hiểm bắt buộc đã nộp trong năm (VNĐ)")
    parser.add_argument("--settlement-tax-withheld", type=float, default=0.0, help="Tổng số thuế TNCN các nơi đã tạm khấu trừ (VNĐ)")
    
    # Bất động sản
    parser.add_argument("--bds-value", type=float, help="Giá trị chuyển nhượng BĐS trên hợp đồng (VNĐ)")
    parser.add_argument("--relative", action="store_true", help="Giao dịch chuyển nhượng giữa người thân trong gia đình")
    parser.add_argument("--sole-owner", action="store_true", help="Cam kết là nhà ở, đất ở duy nhất tại Việt Nam")
    parser.add_argument("--ownership-days", type=int, default=0, help="Số ngày đã đứng tên sở hữu trên Sổ đỏ")

    # BHXH 1 lần
    parser.add_argument("--bhxh-before-2014", type=float, help="Số năm đóng BHXH trước năm 2014")
    parser.add_argument("--bhxh-from-2014", type=float, help="Số năm đóng BHXH từ năm 2014 trở đi")
    parser.add_argument("--mbqtl", type=float, help="Mức bình quân tiền lương tháng đóng BHXH (VNĐ)")

    parser.add_argument("--json", action="store_true", help="Xuất kết quả dưới định dạng JSON")

    args = parser.parse_args()

    # 1. Thu nhập vãng lai
    if args.adhoc is not None:
        res = calculate_adhoc_income_tax(args.adhoc)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("=" * 60)
            print(" THUẾ KHẤU TRỪ VÃNG LAI (10%) — KỲ 2026 (TT 87/2026/TT-BTC)")
            print("=" * 60)
            print(f" • Thu nhập chi trả:             {format_currency(res['gross_amount'])}")
            print(f" • Khấu trừ 10% tại nguồn:       {format_currency(res['tax_amount'])}")
            print(f" • Thực nhận sau khấu trừ:       {format_currency(res['net_amount'])}")
            print(f" • Ghi chú: {res['note']}")
            print("=" * 60)
        return

    # 2. Quy đổi Net sang Gross
    if args.net is not None:
        res = convert_net_to_gross(
            net_salary=args.net,
            num_dependents=args.dependents,
            voluntary_pension_monthly=args.pension,
            medical_deduction_monthly=args.medical,
            education_deduction_monthly=args.education
        )
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("=" * 65)
            print(" KẾT QUẢ QUY ĐỔI LƯƠNG NET SANG GROSS (KỲ 2026)")
            print("=" * 65)
            print(f" • LƯƠNG NET MONG MUỐN:           {format_currency(res['target_net'])}")
            print(f" => LƯƠNG GROSS CẦN THỎA THUẬN:  {format_currency(res['gross_salary'])}")
            print("-" * 65)
            print(f" • Tổng bảo hiểm NLĐ đóng:        {format_currency(res['insurance']['total'])}")
            print(f" • Thu nhập tính thuế (TNTT):     {format_currency(res['taxable_income'])}")
            print(f" • Thuế TNCN phải nộp hàng tháng: {format_currency(res['tax']['total_tax'])}")
            print(f" • Tỷ lệ thuế thực tế:            {res['effective_tax_rate_percent']}%")
            print("=" * 65)
        return

    # 3. Tính thuế lương Gross sang Net
    if args.gross is not None:
        res = calculate_monthly_salary_tax(
            gross_salary=args.gross,
            num_dependents=args.dependents,
            voluntary_pension_monthly=args.pension,
            medical_deduction_monthly=args.medical,
            education_deduction_monthly=args.education
        )
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("=" * 65)
            print(" BẢNG TÍNH THUẾ THU NHẬP CÁ NHÂN & LƯƠNG NET (KỲ 2026)")
            print("=" * 65)
            print(f" • Lương Gross:                   {format_currency(res['gross_salary'])}")
            print(f" • Tổng bảo hiểm NLĐ đóng:        {format_currency(res['insurance']['total'])}")
            print(f" • Tổng giảm trừ gia cảnh:        {format_currency(res['deductions']['total_deductions'])}")
            print(f" • Thu nhập tính thuế (TNTT):     {format_currency(res['taxable_income'])}")
            print(f" • Thuế TNCN phải nộp:            {format_currency(res['tax']['total_tax'])}")
            print(f" => THỰC NHẬN (LƯƠNG NET):        {format_currency(res['net_salary'])}")
            print(f" • Tỷ lệ thuế thực tế:            {res['effective_tax_rate_percent']}%")
            print("=" * 65)
        return

    # 4. Quyết toán thuế năm
    if args.settlement_income is not None:
        res = calculate_annual_settlement(
            annual_gross_income=args.settlement_income,
            annual_insurance_paid=args.settlement_insurance,
            num_dependents=args.dependents,
            annual_medical=args.medical * 12 if args.medical > 0 else 0,
            annual_education=args.education * 12 if args.education > 0 else 0,
            annual_pension=args.pension * 12 if args.pension > 0 else 0,
            tax_already_withheld=args.settlement_tax_withheld
        )
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("=" * 65)
            print(" KẾT QUẢ QUYẾT TOÁN THUẾ TNCN NĂM (KỲ 2026)")
            print("=" * 65)
            print(f" • Tổng thu nhập trong năm:       {format_currency(res['annual_gross_income'])}")
            print(f" • Tổng giảm trừ cả năm:          {format_currency(res['deductions']['total_deductions'])}")
            print(f" • Thu nhập tính thuế cả năm:     {format_currency(res['annual_taxable_income'])}")
            print(f" • Tổng nghĩa vụ thuế cả năm:     {format_currency(res['annual_pit_liability'])}")
            print(f" • Số thuế các nơi đã tạm khấu trừ:{format_currency(res['tax_already_withheld'])}")
            print("-" * 65)
            print(f" => KẾT LUẬN: {res['status_message']}")
            print("=" * 65)
        return

    # 5. Bất động sản
    if args.bds_value is not None:
        res = calculate_real_estate_tax(
            transfer_value=args.bds_value,
            is_relative=args.relative,
            is_sole_property=args.sole_owner,
            ownership_days=args.ownership_days
        )
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("=" * 65)
            print(" TƯ VẤN THUẾ CHUYỂN NHƯỢNG BẤT ĐỘNG SẢN (KỲ 2026)")
            print("=" * 65)
            print(f" • Giá trị chuyển nhượng:         {format_currency(res['transfer_value'])}")
            print(f" • Thuế suất áp dụng:             {int(res['tax_rate']*100)}%")
            print(f" • Số thuế TNCN phải nộp:         {format_currency(res['tax_amount'])}")
            print(f" • Căn cứ pháp lý: {res['exemption_ground']}")
            print("=" * 65)
        return

    # 6. BHXH 1 lần
    if args.mbqtl is not None:
        y_before = args.bhxh_before_2014 if args.bhxh_before_2014 is not None else 0.0
        y_from = args.bhxh_from_2014 if args.bhxh_from_2014 is not None else 0.0
        res = calculate_bhxh_lump_sum(
            years_before_2014=y_before,
            years_from_2014=y_from,
            mbqtl=args.mbqtl
        )
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("=" * 65)
            print(" DỰ TÍNH MỨC HƯỞNG BẢO HIỂM XÃ HỘI RÚT 1 LẦN (LUẬT BHXH 2024)")
            print("=" * 65)
            print(f" • Mức bình quân tiền lương (MBQTL): {format_currency(res['mbqtl'])}")
            print(f" • Thời gian đóng: {res['years_before_2014']} năm (trước 2014) + {res['years_from_2014']} năm (từ 2014)")
            print(f" • Công thức tính: {res['formula']}")
            print(f" => SỐ TIỀN HƯỞNG 1 LẦN:            {format_currency(res['lump_sum_amount'])}")
            print("-" * 65)
            print(f" • So sánh bảo lưu hưởng lương hưu tối thiểu: ~{format_currency(res['pension_comparison']['monthly_pension_min'])}/tháng")
            print(f" • Tổng nhận 20 năm sau hưu: ~{format_currency(res['pension_comparison']['twenty_year_pension_total'])} + Thẻ BHYT miễn phí")
            print("=" * 65)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
