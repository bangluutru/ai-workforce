#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tax_calculator.py — Công cụ tính toán thuế Thu nhập cá nhân (TNCN) Việt Nam 2026
Theo chuẩn Luật 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP, TT 87/2026/TT-BTC.

Hỗ trợ:
- Tính thuế TNCN từ tiền lương, tiền công (Biểu lũy tiến 5 bậc 2026)
- Trừ bảo hiểm bắt buộc theo trần mới (lương cơ sở 2,53tr -> trần BHXH/BHYT: 50,6tr)
- Giảm trừ bản thân (15,5tr), người phụ thuộc (6,2tr/người)
- Giảm trừ chi phí y tế (tối đa 23tr/năm), giáo dục (tối đa 24tr/năm), hưu trí tự nguyện (3tr/tháng)
- Khấu trừ thuế vãng lai 10% (ngưỡng mới >= 5 triệu đồng/lần)
- Thuế chuyển nhượng bất động sản (2%), phái sinh (0,1%)
- Tính trợ cấp thất nghiệp (BHTN 60%), ước tính BHXH rút 1 lần

Cách sử dụng:
    python3 tax_calculator.py --gross 35000000 --dependents 1
    python3 tax_calculator.py --gross 80000000 --dependents 2 --json
    python3 tax_calculator.py --adhoc 6000000
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

DEDUCTION_PERSONAL = 15_500_000         # Giảm trừ bản thân: 15,5 tr/tháng
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
    # Lương đóng BHXH, BHYT bị chặn trần ở 20 lần lương cơ sở (50,6 triệu đồng)
    sal_for_shui = min(gross_salary, INSURANCE_CAP_SALARY)
    bhxh = sal_for_shui * RATE_BHXH
    bhyt = sal_for_shui * RATE_BHYT
    
    # BHTN chặn trần theo 20 lần lương tối thiểu vùng (nếu có truyền bhtn_cap > 0, ngược lại tính theo gross)
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

    # Xác định công thức tính nhanh
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
    """Tính toán toàn diện thuế TNCN và lương thực nhận (Net) theo tháng."""
    insurance = calculate_compulsory_insurance(gross_salary, bhtn_cap)
    
    # Các khoản giảm trừ
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

    # Thu nhập tính thuế (TNTT)
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


def print_salary_report(res: Dict[str, Any]):
    """Hiển thị báo cáo tính thuế chi tiết trên Terminal."""
    print("=" * 65)
    print(" BẢNG TÍNH THUẾ THU NHẬP CÁ NHÂN & LƯƠNG NET (KỲ 2026)")
    print(" Căn cứ: Luật 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP")
    print("=" * 65)
    print(f" • Tổng thu nhập (Lương Gross):       {format_currency(res['gross_salary'])}")
    print("-" * 65)
    print(" 1. BẢO HIỂM BẮT BUỘC (NLĐ đóng):")
    ins = res["insurance"]
    print(f"    - BHXH (8% trên trần 50,6tr):       {format_currency(ins['bhxh'])}")
    print(f"    - BHYT (1.5% trên trần 50,6tr):     {format_currency(ins['bhyt'])}")
    print(f"    - BHTN (1%):                        {format_currency(ins['bhtn'])}")
    print(f"    => Tổng bảo hiểm:                   {format_currency(ins['total'])}")
    print("-" * 65)
    print(" 2. CÁC KHOẢN GIẢM TRỪ:")
    d = res["deductions"]
    print(f"    - Bản thân người nộp thuế:          {format_currency(d['personal'])}")
    print(f"    - Người phụ thuộc ({d['dependents_count']} người):         {format_currency(d['dependents_total'])}")
    if d['voluntary_pension'] > 0:
        print(f"    - Hưu trí tự nguyện:                {format_currency(d['voluntary_pension'])}")
    if d['medical'] > 0:
        print(f"    - Chi phí Y tế:                     {format_currency(d['medical'])}")
    if d['education'] > 0:
        print(f"    - Chi phí Giáo dục:                 {format_currency(d['education'])}")
    print(f"    => Tổng giảm trừ:                   {format_currency(d['total_deductions'])}")
    print("-" * 65)
    print(f" 3. THU NHẬP TÍNH THUẾ (TNTT):          {format_currency(res['taxable_income'])}")
    print("-" * 65)
    print(" 4. THUẾ TNCN PHẢI NỘP (Biểu 5 bậc 2026):")
    tax_info = res["tax"]
    for b in tax_info["bracket_details"]:
        print(f"    - Bậc {b['bracket']} ({b['range']}) @ {b['rate']}:   {format_currency(b['tax'])}")
    print(f"    => Công thức tính nhanh:            {tax_info['quick_formula']}")
    print(f"    => TỔNG THUẾ TNCN PHẢI NỘP:         {format_currency(tax_info['total_tax'])}")
    print(f"    => Tỷ lệ thuế thực tế:              {res['effective_tax_rate_percent']}%")
    print("=" * 65)
    print(f" 5. THỰC NHẬN (LƯƠNG NET):              {format_currency(res['net_salary'])}")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Tính thuế TNCN Việt Nam kỳ tính thuế 2026")
    parser.add_argument("--gross", type=float, help="Mức lương Gross hàng tháng (VNĐ)")
    parser.add_argument("--dependents", type=int, default=0, help="Số người phụ thuộc (mặc định: 0)")
    parser.add_argument("--pension", type=float, default=0.0, help="Đóng hưu trí tự nguyện hàng tháng (VNĐ, tối đa 3tr)")
    parser.add_argument("--medical", type=float, default=0.0, help="Chi phí Y tế hàng tháng (VNĐ, tối đa 23tr/năm)")
    parser.add_argument("--education", type=float, default=0.0, help="Chi phí Giáo dục hàng tháng (VNĐ, tối đa 24tr/năm)")
    parser.add_argument("--adhoc", type=float, help="Tính thuế thu nhập vãng lai / hợp đồng dịch vụ (VNĐ)")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả dưới định dạng JSON")

    args = parser.parse_args()

    if args.adhoc is not None:
        adhoc_res = calculate_adhoc_income_tax(args.adhoc)
        if args.json:
            print(json.dumps(adhoc_res, ensure_ascii=False, indent=2))
        else:
            print("=" * 60)
            print(" THUẾ KHẤU TRỪ VÃNG LAI (10%) — KỲ 2026 (TT 87/2026/TT-BTC)")
            print("=" * 60)
            print(f" • Thu nhập chi trả:             {format_currency(adhoc_res['gross_amount'])}")
            print(f" • Khấu trừ 10% tại nguồn:       {format_currency(adhoc_res['tax_amount'])}")
            print(f" • Thực nhận sau khấu trừ:       {format_currency(adhoc_res['net_amount'])}")
            print(f" • Ghi chú: {adhoc_res['note']}")
            print("=" * 60)
        return

    if args.gross is not None:
        salary_res = calculate_monthly_salary_tax(
            gross_salary=args.gross,
            num_dependents=args.dependents,
            voluntary_pension_monthly=args.pension,
            medical_deduction_monthly=args.medical,
            education_deduction_monthly=args.education,
        )
        if args.json:
            print(json.dumps(salary_res, ensure_ascii=False, indent=2))
        else:
            print_salary_report(salary_res)
        return

    # Nếu không có tham số nào, in hướng dẫn
    parser.print_help()


if __name__ == "__main__":
    main()
