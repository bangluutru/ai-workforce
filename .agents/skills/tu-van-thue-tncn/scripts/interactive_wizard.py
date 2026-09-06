#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interactive_wizard.py — Động cơ Điều hướng Kịch bản Trắc nghiệm Tương tác Thuế TNCN 2026
Tuân thủ Rule R4 (Kiến trúc Module hóa) & Kịch bản chuẩn bị sẵn (Zero Latency Decision Tree)
Căn cứ: Luật 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP, Luật BHXH 2024.
"""

import sys
import os
import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_questionnaire_tree() -> Dict[str, Any]:
    """Tải cây câu hỏi trắc nghiệm chuẩn bị sẵn từ resources/questionnaire_tree.json."""
    script_dir = Path(__file__).resolve().parent
    tree_path = script_dir.parent / "resources" / "questionnaire_tree.json"
    if not tree_path.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp cây kịch bản: {tree_path}")
    with open(tree_path, "r", encoding="utf-8") as f:
        return json.load(f)


def map_answers_to_calculator_args(branch_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ánh xạ các câu trả lời trắc nghiệm sang tập tham số dòng lệnh cho tax_calculator.py
    và export_tax_sheet.py một cách tự động và chuẩn xác.
    """
    params: Dict[str, Any] = {
        "branch_id": branch_id,
        "raw_answers": answers,
        "calculator_flags": [],
        "export_flags": [],
    }

    # 1. Nhánh Tiền Lương Gross - Net
    if branch_id == "luong_gross_net":
        mode = answers.get("lgn_salary_mode", "")
        is_net = "Net" in mode
        
        amt_str = answers.get("lgn_salary_amount", "")
        # Bóc tách số tiền từ chuỗi hoặc giá trị người dùng nhập tự do
        amt = 35_000_000
        num_matches = re.findall(r"\b\d{1,3}(?:\.\d{3})+(?:\s*(?:triệu|tr|đ|vnđ))?\b|\b\d+\s*(?:triệu|tr)\b|\b\d{7,10}\b", amt_str, re.IGNORECASE)
        if "15.500.000" in amt_str and "dưới" in amt_str.lower():
            amt = 15_000_000
        elif "20.000.000" in amt_str:
            amt = 25_000_000
        elif "35.000.000" in amt_str:
            amt = 40_000_000
        elif "60.000.000" in amt_str:
            amt = 70_000_000
        elif "100.000.000" in amt_str:
            amt = 120_000_000
        
        # Nếu người dùng tự gõ số tiền cụ thể
        digits_only = re.sub(r"[^\d]", "", amt_str)
        if digits_only and int(digits_only) > 1_000_000:
            amt = float(digits_only)

        # Số người phụ thuộc
        npt_str = answers.get("lgn_dependents_count", "")
        npt = 0
        if "01" in npt_str or "1" in npt_str:
            npt = 1
        elif "02" in npt_str or "2" in npt_str:
            npt = 2
        elif "03" in npt_str or "3" in npt_str:
            npt = 3

        # Giảm trừ bổ sung
        extra_str = answers.get("lgn_extra_deductions", "")
        medical = 23_000_000 if "Y tế" in extra_str else 0
        education = 24_000_000 if "Giáo dục" in extra_str else 0
        pension = 3_000_000 if "hưu trí" in extra_str.lower() else 0

        if is_net:
            params["calculator_flags"] = ["--net", str(amt), "--dependents", str(npt)]
        else:
            params["calculator_flags"] = ["--gross", str(amt), "--dependents", str(npt)]
        
        if medical > 0:
            params["calculator_flags"] += ["--medical", str(round(medical / 12))]
        if education > 0:
            params["calculator_flags"] += ["--education", str(round(education / 12))]
        if pension > 0:
            params["calculator_flags"] += ["--pension", str(pension)]

        params["export_flags"] = ["--gross", str(amt), "--dependents", str(npt), "--medical", str(medical), "--education", str(education), "--pension", str(pension)]

    # 2. Nhánh Quyết Toán Thuế Năm
    elif branch_id == "quyet_toan_nam":
        inc_str = answers.get("qtt_annual_income_level", "")
        annual_gross = 450_000_000
        if "186 triệu" in inc_str and "dưới" in inc_str.lower():
            annual_gross = 180_000_000
        elif "360 triệu" in inc_str:
            annual_gross = 300_000_000
        elif "720 triệu" in inc_str:
            annual_gross = 500_000_000
        elif "1,2 tỷ" in inc_str:
            annual_gross = 900_000_000

        digits_inc = re.sub(r"[^\d]", "", inc_str)
        if digits_inc and int(digits_inc) > 10_000_000:
            annual_gross = float(digits_inc)

        tax_withheld = annual_gross * 0.08  # Mặc định ước tính đã bị trừ khoảng 8%

        params["calculator_flags"] = [
            "--settlement-income", str(annual_gross),
            "--settlement-insurance", str(round(annual_gross * 0.105)),
            "--settlement-tax-withheld", str(round(tax_withheld)),
            "--dependents", "1"
        ]
        params["export_flags"] = [
            "--settlement-income", str(annual_gross),
            "--tax-withheld", str(round(tax_withheld)),
            "--dependents", "1"
        ]

    # 3. Nhánh Chuyển Nhượng Bất Động Sản
    elif branch_id == "chuyen_nhuong_bds":
        val_str = answers.get("bds_contract_value", "")
        val = 2_500_000_000
        if "1 tỷ" in val_str and "dưới" in val_str.lower():
            val = 800_000_000
        elif "3 tỷ" in val_str:
            val = 2_500_000_000
        elif "5 tỷ" in val_str:
            val = 4_000_000_000
        elif "10 tỷ" in val_str:
            val = 7_000_000_000

        digits_val = re.sub(r"[^\d]", "", val_str)
        if digits_val and int(digits_val) > 10_000_000:
            val = float(digits_val)

        rel_str = answers.get("bds_relationship", "")
        is_rel = any(w in rel_str.lower() for w in ["vợ", "chồng", "cha", "mẹ", "con", "ruột", "ông", "bà", "cháu"])
        
        sole_str = answers.get("bds_sole_property", "")
        is_sole = "duy nhất" in sole_str.lower() and "không" not in sole_str.lower()

        days_str = answers.get("bds_holding_period", "")
        days = 200 if "183 ngày trở lên" in days_str else 90

        flags = ["--bds-value", str(val)]
        if is_rel:
            flags.append("--relative")
        elif is_sole:
            flags.extend(["--sole-owner", "--ownership-days", str(days)])

        params["calculator_flags"] = flags

    # 4. Nhánh Rút BHXH Một Lần
    elif branch_id == "rut_bhxh_mot_lan":
        y_str = answers.get("bhxh_years_contributed", "")
        y_before = 10.0
        y_from = 5.0
        if "dưới 15 năm" in y_str.lower():
            y_before = 4.0
            y_from = 8.0
        elif "15 năm đến dưới 20 năm" in y_str.lower():
            y_before = 6.0
            y_from = 11.0
        elif "20 năm đến 25 năm" in y_str.lower():
            y_before = 11.0
            y_from = 12.0

        digits_y = re.findall(r"\b\d+\b", y_str)
        if digits_y:
            total_y = float(digits_y[0])
            if total_y <= 12:
                y_before = 0.0
                y_from = total_y
            else:
                y_before = total_y - 12.0
                y_from = 12.0

        sal_str = answers.get("bhxh_mbqtl_level", "")
        sal = 8_000_000
        if "dưới 6.000.000" in sal_str.lower():
            sal = 5_500_000
        elif "6.000.000 đến 10.000.000" in sal_str:
            sal = 8_000_000
        elif "10.000.000 đến 15.000.000" in sal_str:
            sal = 12_000_000
        elif "15.000.000 đến 25.000.000" in sal_str:
            sal = 20_000_000

        digits_sal = re.sub(r"[^\d]", "", sal_str)
        if digits_sal and int(digits_sal) > 1_000_000:
            sal = float(digits_sal)

        params["calculator_flags"] = [
            "--bhxh-before-2014", str(y_before),
            "--bhxh-from-2014", str(y_from),
            "--mbqtl", str(sal)
        ]
        params["export_flags"] = [
            "--bhxh-before-2014", str(y_before),
            "--bhxh-from-2014", str(y_from),
            "--mbqtl", str(sal),
            "--months-off", "1"
        ]

    # 5. Nhánh Freelancer
    elif branch_id == "freelancer_kd":
        withholding_str = answers.get("fl_withholding_rate", "")
        adhoc_amt = 15_000_000
        params["calculator_flags"] = ["--adhoc", str(adhoc_amt)]

    return params


def run_cli_wizard():
    """Chạy quy trình khảo sát tương tác trực tiếp trên giao diện dòng lệnh (CLI)."""
    tree = load_questionnaire_tree()
    root_q = tree["root_question"]

    print("\n" + "=" * 70)
    print(" 🏛️  CỔNG TƯ VẤN THUẾ TNCN 2026 — INTERACTIVE QUESTIONNAIRE WIZARD")
    print("=" * 70)
    print(f"\n{root_q['question']}\n")
    for idx, opt in enumerate(root_q["options"], 1):
        print(f"  [{idx}] {opt}")

    choice = input("\n👉 Nhập lựa chọn của bạn (1-6): ").strip()
    branch_map = {
        "1": "quyet_toan_nam",
        "2": "luong_gross_net",
        "3": "chuyen_nhuong_bds",
        "4": "rut_bhxh_mot_lan",
        "5": "freelancer_kd",
        "6": "nguoi_phu_thuoc_mst",
    }
    selected_branch = branch_map.get(choice, "quyet_toan_nam")
    branch_data = tree["branches"][selected_branch]

    print(f"\n✅ Đã chọn chuyên đề: {branch_data['display_name']}")
    print("-" * 70)

    collected_answers = {}
    for q in branch_data["questions"]:
        print(f"\n❓ {q['question']}\n")
        for idx, opt in enumerate(q["options"], 1):
            print(f"   [{idx}] {opt}")
        ans_idx = input("\n👉 Lựa chọn của bạn (hoặc gõ trực tiếp số tiền/ý kiến): ").strip()
        
        # Nếu nhập số thứ tự
        if ans_idx.isdigit() and 1 <= int(ans_idx) <= len(q["options"]):
            selected_text = q["options"][int(ans_idx) - 1]
        else:
            selected_text = ans_idx if ans_idx else q["options"][0]

        collected_answers[q["id"]] = selected_text
        print(f"   ✓ Đã ghi nhận: {selected_text}")

    # Ánh xạ sang tham số
    mapped = map_answers_to_calculator_args(selected_branch, collected_answers)
    
    # Ghi nhận kết quả vào file tạm _process
    process_dir = Path("_process")
    process_dir.mkdir(parents=True, exist_ok=True)
    out_file = process_dir / f"intake_{selected_branch}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(mapped, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(" 🎉 KHẢO SÁT HOÀN TẤT! ĐÃ SẴN SÀNG THỰC THI ĐỘNG CƠ TÍNH TOÁN")
    print("=" * 70)
    print(f" • Hồ sơ dữ liệu lưu tại: {out_file}")
    print(f" • Tham số tax_calculator: {' '.join(mapped['calculator_flags'])}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Động cơ Điều hướng Kịch bản Trắc nghiệm Thuế TNCN 2026")
    parser.add_argument("--cli", action="store_true", help="Chạy khảo sát tương tác trực tiếp trên Terminal")
    parser.add_argument("--dump-tree", action="store_true", help="In toàn bộ cây kịch bản dưới định dạng JSON")
    parser.add_argument("--branch", type=str, help="Lấy câu hỏi của một nhánh cụ thể")
    args = parser.parse_args()

    if args.dump_tree:
        tree = load_questionnaire_tree()
        print(json.dumps(tree, ensure_ascii=False, indent=2))
        return

    if args.branch:
        tree = load_questionnaire_tree()
        if args.branch in tree["branches"]:
            print(json.dumps(tree["branches"][args.branch], ensure_ascii=False, indent=2))
        else:
            print(f"Lỗi: Không tìm thấy nhánh '{args.branch}'")
        return

    if args.cli:
        run_cli_wizard()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
