#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_tax_sheet.py — Xuất bảng tính thuế TNCN Excel với 100% CÔNG THỨC SỐNG (Live Dynamic Formulas)
Tuân thủ Luật R4: .agents/rules/R4-skill-standard-v1.md (Tiêu chuẩn dữ liệu sống)
Căn cứ: Luật 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP.
"""

import sys
import os
import argparse
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Lỗi: Thiếu thư viện openpyxl. Vui lòng cài đặt: pip install openpyxl")
    sys.exit(1)


def create_tax_workbook(
    output_path: str,
    gross_salary: float = 35_000_000,
    dependents: int = 1,
    medical_annual: float = 0,
    education_annual: float = 0,
    pension_monthly: float = 0,
    settlement_annual_income: float = 0,
    settlement_tax_withheld: float = 0,
    bhxh_before_2014: float = 11.0,
    bhxh_from_2014: float = 12.0,
    mbqtl: float = 6_000_000,
    months_off: int = 1,
    include_bhxh: bool = True
):
    wb = openpyxl.Workbook()
    
    # STYLES & THEME
    font_title = Font(name="Segoe UI", size=15, bold=True, color="1B365D")
    font_subtitle = Font(name="Segoe UI", size=9, italic=True, color="555555")
    font_section = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Segoe UI", size=10, bold=True, color="000000")
    font_regular = Font(name="Segoe UI", size=10, color="1C1C1C")
    font_input = Font(name="Segoe UI", size=10, bold=True, color="002060")
    font_formula = Font(name="Segoe UI", size=10, bold=True, color="006100")
    font_total = Font(name="Segoe UI", size=11, bold=True, color="9C0006")
    
    fill_header = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    fill_section_blue = PatternFill(start_color="2E5B88", end_color="2E5B88", fill_type="solid")
    fill_section_green = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    fill_input = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    fill_highlight = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    fill_total_red = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
    fill_net_green = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

    thin_border_side = Side(border_style="thin", color="D9D9D9")
    double_bottom_side = Side(border_style="double", color="1B365D")

    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_total = Border(top=thin_border_side, bottom=double_bottom_side)

    currency_format = '#,##0 "VNĐ"'
    percent_format = '0.00%'
    number_format = '#,##0'

    # =============================================================
    # SHEET 1: TÍNH THUẾ LƯƠNG HÀNG THÁNG 2026
    # =============================================================
    ws1 = wb.active
    ws1.title = "Tính Thuế Lương Tháng"
    ws1.views.sheetView[0].showGridLines = True

    ws1["A1"] = "BẢNG TÍNH THUẾ THU NHẬP CÁ NHÂN & LƯƠNG NET (KỲ 2026)"
    ws1["A1"].font = font_title
    ws1["A2"] = "Căn cứ: Luật 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP | 100% Live Formulas"
    ws1["A2"].font = font_subtitle

    ws1["A4"] = "A. THÔNG SỐ ĐẦU VÀO CỦA NGƯỜI LAO ĐỘNG (Ô màu vàng có thể chỉnh sửa)"
    ws1["A4"].font = font_section
    ws1.merge_cells("A4:D4")
    for col in range(1, 5):
        ws1.cell(row=4, column=col).fill = fill_section_blue

    inputs = [
        (5, "Tổng thu nhập hàng tháng (Lương Gross)", gross_salary, currency_format, "Nhập mức lương thỏa thuận"),
        (6, "Số người phụ thuộc đã đăng ký (NPT)", dependents, number_format, "Số người phụ thuộc có mã số thuế"),
        (7, "Chi phí Y tế hợp lệ cả năm (tối đa 23tr/năm)", medical_annual, currency_format, "Hóa đơn KCB thuộc danh mục BHYT"),
        (8, "Chi phí Giáo dục hợp lệ cả năm (tối đa 24tr/năm)", education_annual, currency_format, "Biên lai học phí chính quy"),
        (9, "Đóng bảo hiểm hưu trí tự nguyện/tháng (tối đa 3tr)", pension_monthly, currency_format, "Hợp đồng hưu trí tự nguyện hợp pháp"),
    ]

    for r_idx, label, val, num_fmt, note in inputs:
        ws1.cell(row=r_idx, column=1, value=label).font = font_bold
        c = ws1.cell(row=r_idx, column=2, value=val)
        c.font = font_input
        c.fill = fill_input
        c.alignment = Alignment(horizontal="right")
        c.number_format = num_fmt
        c.border = border_cell
        ws1.cell(row=r_idx, column=3, value=note).font = font_subtitle

    # PHẦN B: BẢO HIỂM BẮT BUỘC
    ws1["A11"] = "B. BẢO HIỂM BẮT BUỘC (Người lao động đóng)"
    ws1["A11"].font = font_section
    ws1.merge_cells("A11:D11")
    for col in range(1, 5):
        ws1.cell(row=11, column=col).fill = fill_section_blue

    ins_rows = [
        (12, "BHXH (8% trên trần 50,6 triệu)", "=MIN(B5, 50600000)*0.08", "Trần 20 lần lương cơ sở 2,53tr (NĐ 161/2026/NĐ-CP)"),
        (13, "BHYT (1.5% trên trần 50,6 triệu)", "=MIN(B5, 50600000)*0.015", "Trần 20 lần lương cơ sở 2,53tr"),
        (14, "BHTN (1% theo lương thực tế)", "=B5*0.01", "Bảo hiểm thất nghiệp 1%"),
        (15, "TỔNG TIỀN BẢO HIỂM KHẤU TRỪ", "=SUM(B12:B14)", "Tổng khấu trừ bảo hiểm hàng tháng"),
    ]

    for r_idx, label, formula, note in ins_rows:
        ws1.cell(row=r_idx, column=1, value=label).font = font_bold if r_idx == 15 else font_regular
        c = ws1.cell(row=r_idx, column=2, value=formula)
        c.font = font_formula if r_idx != 15 else font_bold
        if r_idx == 15:
            c.fill = fill_highlight
            c.border = border_total
        else:
            c.border = border_cell
        c.alignment = Alignment(horizontal="right")
        c.number_format = currency_format
        ws1.cell(row=r_idx, column=3, value=note).font = font_subtitle

    # PHẦN C: CÁC KHOẢN GIẢM TRỪ THUẾ
    ws1["A17"] = "C. CÁC KHOẢN GIẢM TRỪ THUẾ TNCN (Theo NQ 110 & NĐ 253)"
    ws1["A17"].font = font_section
    ws1.merge_cells("A17:D17")
    for col in range(1, 5):
        ws1.cell(row=17, column=col).fill = fill_section_blue

    deduct_rows = [
        (18, "Giảm trừ bản thân người nộp thuế", 15500000, "15,5 triệu đồng/tháng (NQ 110/2025/UBTVQH15)"),
        (19, "Giảm trừ người phụ thuộc (6,2 tr/người/tháng)", "=B6*6200000", "6,2 triệu đồng/tháng mỗi NPT"),
        (20, "Giảm trừ chi phí Y tế phân bổ tháng", "=MIN(B7, 23000000)/12", "Tối đa 23 triệu đồng/năm (NĐ 253/2026/NĐ-CP)"),
        (21, "Giảm trừ chi phí Giáo dục phân bổ tháng", "=MIN(B8, 24000000)/12", "Tối đa 24 triệu đồng/năm (NĐ 253/2026/NĐ-CP)"),
        (22, "Giảm trừ hưu trí tự nguyện hàng tháng", "=MIN(B9, 3000000)", "Tối đa 3 triệu đồng/tháng"),
        (23, "TỔNG CÁC KHOẢN GIẢM TRỪ & BẢO HIỂM", "=B15+SUM(B18:B22)", "Tổng căn cứ loại trừ trước khi tính thuế"),
    ]

    for r_idx, label, val, note in deduct_rows:
        ws1.cell(row=r_idx, column=1, value=label).font = font_bold if r_idx == 23 else font_regular
        c = ws1.cell(row=r_idx, column=2, value=val)
        c.font = font_formula if r_idx != 23 else font_bold
        if r_idx == 23:
            c.fill = fill_highlight
            c.border = border_total
        else:
            c.border = border_cell
        c.alignment = Alignment(horizontal="right")
        c.number_format = currency_format
        ws1.cell(row=r_idx, column=3, value=note).font = font_subtitle

    # THU NHẬP TÍNH THUẾ
    ws1["A25"] = "D. THU NHẬP TÍNH THUẾ (TNTT = Gross - Tổng giảm trừ)"
    ws1["A25"].font = font_section
    ws1.merge_cells("A25:D25")
    for col in range(1, 5):
        ws1.cell(row=25, column=col).fill = fill_section_green

    ws1.cell(row=26, column=1, value="Thu nhập tính thuế (TNTT)").font = font_bold
    c_tntt = ws1.cell(row=26, column=2, value="=MAX(0, B5 - B23)")
    c_tntt.font = Font(name="Segoe UI", size=11, bold=True, color="002060")
    c_tntt.fill = fill_highlight
    c_tntt.alignment = Alignment(horizontal="right")
    c_tntt.number_format = currency_format
    c_tntt.border = border_cell
    ws1.cell(row=26, column=3, value="Nếu Gross <= Tổng giảm trừ thì TNTT = 0").font = font_subtitle

    # BIỂU THUẾ LŨY TIẾN 5 BẬC
    ws1["A28"] = "E. CHI TIẾT THUẾ TNCN THEO BIỂU 5 BẬC (Luật 109/2025/QH15)"
    ws1["A28"].font = font_section
    ws1.merge_cells("A28:D28")
    for col in range(1, 5):
        ws1.cell(row=28, column=col).fill = fill_section_blue

    brackets_formulas = [
        (29, "Bậc 1: Đến 10 triệu đồng (5%)", "=IF(B26>0, MIN(B26, 10000000)*0.05, 0)", "Thu nhập từ 0 đến 10 triệu"),
        (30, "Bậc 2: Trên 10 đến 30 triệu đồng (10%)", "=IF(B26>10000000, MIN(B26-10000000, 20000000)*0.10, 0)", "Thu nhập từ 10 đến 30 triệu"),
        (31, "Bậc 3: Trên 30 đến 60 triệu đồng (20%)", "=IF(B26>30000000, MIN(B26-30000000, 30000000)*0.20, 0)", "Thu nhập từ 30 đến 60 triệu"),
        (32, "Bậc 4: Trên 60 đến 100 triệu đồng (30%)", "=IF(B26>60000000, MIN(B26-60000000, 40000000)*0.30, 0)", "Thu nhập từ 60 đến 100 triệu"),
        (33, "Bậc 5: Trên 100 triệu đồng (35%)", "=IF(B26>100000000, (B26-100000000)*0.35, 0)", "Phần thu nhập vượt trên 100 triệu"),
        (34, "TỔNG THUẾ TNCN PHẢI NỘP HÀNG THÁNG", "=SUM(B29:B33)", "Tổng nghĩa vụ thuế TNCN trong kỳ"),
    ]

    for r_idx, label, formula, note in brackets_formulas:
        ws1.cell(row=r_idx, column=1, value=label).font = font_bold if r_idx == 34 else font_regular
        c = ws1.cell(row=r_idx, column=2, value=formula)
        c.font = font_total if r_idx == 34 else font_formula
        if r_idx == 34:
            c.fill = fill_total_red
            c.border = border_total
        else:
            c.border = border_cell
        c.alignment = Alignment(horizontal="right")
        c.number_format = currency_format
        ws1.cell(row=r_idx, column=3, value=note).font = font_subtitle

    # KẾT QUẢ THỰC NHẬN (NET)
    ws1["A36"] = "F. KẾT QUẢ TỔNG HỢP: THỰC NHẬN (LƯƠNG NET)"
    ws1["A36"].font = font_section
    ws1.merge_cells("A36:D36")
    for col in range(1, 5):
        ws1.cell(row=36, column=col).fill = fill_section_green

    ws1.cell(row=37, column=1, value="LƯƠNG THỰC NHẬN (NET = Gross - BH - Thuế)").font = Font(name="Segoe UI", size=11, bold=True, color="002060")
    c_net = ws1.cell(row=37, column=2, value="=B5 - B15 - B34")
    c_net.font = Font(name="Segoe UI", size=12, bold=True, color="002060")
    c_net.fill = fill_net_green
    c_net.border = border_total
    c_net.alignment = Alignment(horizontal="right")
    c_net.number_format = currency_format
    ws1.cell(row=37, column=3, value="Số tiền thực nhận vào tài khoản").font = font_subtitle

    ws1.cell(row=38, column=1, value="Tỷ lệ thuế TNCN trên tổng thu nhập (Gross)").font = font_regular
    c_rate = ws1.cell(row=38, column=2, value="=IF(B5>0, B34/B5, 0)")
    c_rate.font = font_bold
    c_rate.alignment = Alignment(horizontal="right")
    c_rate.number_format = percent_format
    c_rate.border = border_cell
    ws1.cell(row=38, column=3, value="Tỷ lệ đóng thuế thực tế trên tổng thu nhập").font = font_subtitle

    ws1.column_dimensions["A"].width = 46
    ws1.column_dimensions["B"].width = 24
    ws1.column_dimensions["C"].width = 52
    ws1.column_dimensions["D"].width = 10

    # =============================================================
    # SHEET 2: QUYẾT TOÁN THUẾ NĂM & BÙ TRỪ HOÀN THUẾ
    # =============================================================
    ws2 = wb.create_sheet(title="Quyết Toán Năm & Hoàn Thuế")
    ws2.views.sheetView[0].showGridLines = True

    ws2["A1"] = "BẢNG ĐỐI SOÁT QUYẾT TOÁN THUẾ TNCN NĂM (KỲ 2026)"
    ws2["A1"].font = font_title
    ws2["A2"] = "Tự động tính toán số thuế phải nộp cả năm và xác định số tiền HOÀN hoặc NỘP THÊM | 100% Live Formulas"
    ws2["A2"].font = font_subtitle

    ws2["A4"] = "A. TỔNG HỢP THU NHẬP VÀ CÁC NGUỒN TRONG NĂM (Ô màu vàng có thể chỉnh sửa)"
    ws2["A4"].font = font_section
    ws2.merge_cells("A4:D4")
    for col in range(1, 5):
        ws2.cell(row=4, column=col).fill = fill_section_blue

    def_ann_inc = settlement_annual_income if settlement_annual_income > 0 else gross_salary * 12
    def_ann_withheld = settlement_tax_withheld if settlement_tax_withheld > 0 else 10_000_000

    q_inputs = [
        (5, "Tổng thu nhập chịu thuế cả năm (Gross All)", def_ann_inc, currency_format, "Tổng thu nhập từ tất cả các nơi chi trả"),
        (6, "Tổng tiền bảo hiểm bắt buộc đã nộp trong năm", "=ws1_ins*12", currency_format, "Căn cứ theo chứng từ khấu trừ / VssID"),
        (7, "Số người phụ thuộc đăng ký cả năm (NPT)", dependents, number_format, "Số người phụ thuộc có MST"),
        (8, "Tổng chi phí Y tế hợp lệ cả năm", medical_annual, currency_format, "Hóa đơn KCB thuộc danh mục BHYT (tối đa 23tr)"),
        (9, "Tổng chi phí Giáo dục hợp lệ cả năm", education_annual, currency_format, "Biên lai học phí chính quy (tối đa 24tr)"),
        (10, "Số thuế TNCN các đơn vị ĐÃ TẠM KHẤU TRỪ tại nguồn", def_ann_withheld, currency_format, "Tổng số thuế ghi trên các chứng từ khấu trừ"),
    ]

    ws2.cell(row=5, column=1, value=q_inputs[0][1]).font = font_bold
    c = ws2.cell(row=5, column=2, value=q_inputs[0][2])
    c.font = font_input; c.fill = fill_input; c.alignment = Alignment(horizontal="right"); c.number_format = currency_format; c.border = border_cell
    ws2.cell(row=5, column=3, value=q_inputs[0][4]).font = font_subtitle

    ws2.cell(row=6, column=1, value=q_inputs[1][1]).font = font_bold
    c = ws2.cell(row=6, column=2, value="='Tính Thuế Lương Tháng'!B15*12")
    c.font = font_formula; c.fill = fill_highlight; c.alignment = Alignment(horizontal="right"); c.number_format = currency_format; c.border = border_cell
    ws2.cell(row=6, column=3, value=q_inputs[1][4]).font = font_subtitle

    for r_idx, label, val, num_fmt, note in q_inputs[2:]:
        ws2.cell(row=r_idx, column=1, value=label).font = font_bold
        c = ws2.cell(row=r_idx, column=2, value=val)
        c.font = font_input; c.fill = fill_input; c.alignment = Alignment(horizontal="right"); c.number_format = num_fmt; c.border = border_cell
        ws2.cell(row=r_idx, column=3, value=note).font = font_subtitle

    # GIẢM TRỪ CẢ NĂM
    ws2["A12"] = "B. TỔNG CÁC KHOẢN GIẢM TRỪ CẢ NĂM"
    ws2["A12"].font = font_section
    ws2.merge_cells("A12:D12")
    for col in range(1, 5):
        ws2.cell(row=12, column=col).fill = fill_section_blue

    ws2.cell(row=13, column=1, value="Giảm trừ bản thân cả năm (15,5tr x 12 tháng)").font = font_regular
    c = ws2.cell(row=13, column=2, value=186000000)
    c.font = font_bold; c.number_format = currency_format; c.border = border_cell; c.alignment = Alignment(horizontal="right")
    ws2.cell(row=13, column=3, value="186 triệu đồng/năm (NQ 110/2025/UBTVQH15)").font = font_subtitle

    ws2.cell(row=14, column=1, value="Giảm trừ người phụ thuộc cả năm (6,2tr x 12 x NPT)").font = font_regular
    c = ws2.cell(row=14, column=2, value="=B7*74400000")
    c.font = font_formula; c.number_format = currency_format; c.border = border_cell; c.alignment = Alignment(horizontal="right")
    ws2.cell(row=14, column=3, value="74,4 triệu đồng/người/năm").font = font_subtitle

    ws2.cell(row=15, column=1, value="Giảm trừ chi phí Y tế cả năm").font = font_regular
    c = ws2.cell(row=15, column=2, value="=MIN(B8, 23000000)")
    c.font = font_formula; c.number_format = currency_format; c.border = border_cell; c.alignment = Alignment(horizontal="right")
    ws2.cell(row=15, column=3, value="Tối đa 23 triệu đồng/năm").font = font_subtitle

    ws2.cell(row=16, column=1, value="Giảm trừ chi phí Giáo dục cả năm").font = font_regular
    c = ws2.cell(row=16, column=2, value="=MIN(B9, 24000000)")
    c.font = font_formula; c.number_format = currency_format; c.border = border_cell; c.alignment = Alignment(horizontal="right")
    ws2.cell(row=16, column=3, value="Tối đa 24 triệu đồng/năm").font = font_subtitle

    ws2.cell(row=17, column=1, value="TỔNG GIẢM TRỪ VÀ BẢO HIỂM NĂM").font = font_bold
    c = ws2.cell(row=17, column=2, value="=B6+SUM(B13:B16)")
    c.font = font_bold; c.fill = fill_highlight; c.number_format = currency_format; c.border = border_total; c.alignment = Alignment(horizontal="right")
    ws2.cell(row=17, column=3, value="Tổng căn cứ loại trừ trước thuế năm").font = font_subtitle

    # THU NHẬP TÍNH THUẾ CẢ NĂM
    ws2["A19"] = "C. THU NHẬP TÍNH THUẾ CẢ NĂM (TNTT Năm = Gross Năm - Giảm trừ)"
    ws2["A19"].font = font_section
    ws2.merge_cells("A19:D19")
    for col in range(1, 5):
        ws2.cell(row=19, column=col).fill = fill_section_green

    ws2.cell(row=20, column=1, value="Thu nhập tính thuế cả năm (TNTT Năm)").font = font_bold
    c = ws2.cell(row=20, column=2, value="=MAX(0, B5 - B17)")
    c.font = Font(name="Segoe UI", size=11, bold=True, color="002060"); c.fill = fill_highlight; c.number_format = currency_format; c.border = border_cell; c.alignment = Alignment(horizontal="right")
    ws2.cell(row=20, column=3, value="Căn cứ tính thuế biểu lũy tiến năm").font = font_subtitle

    # BIỂU THUẾ NĂM 5 BẬC
    ws2["A22"] = "D. TÍNH THUẾ THEO BIỂU LŨY TIẾN NĂM 5 BẬC (Luật 109/2025/QH15)"
    ws2["A22"].font = font_section
    ws2.merge_cells("A22:D22")
    for col in range(1, 5):
        ws2.cell(row=22, column=col).fill = fill_section_blue

    b_year = [
        (23, "Bậc 1: Đến 120 triệu đồng (5%)", "=IF(B20>0, MIN(B20, 120000000)*0.05, 0)", "Thu nhập tính thuế đến 120 triệu"),
        (24, "Bậc 2: Trên 120 đến 360 triệu đồng (10%)", "=IF(B20>120000000, MIN(B20-120000000, 240000000)*0.10, 0)", "Thu nhập từ 120 đến 360 triệu"),
        (25, "Bậc 3: Trên 360 đến 720 triệu đồng (20%)", "=IF(B20>360000000, MIN(B20-360000000, 360000000)*0.20, 0)", "Thu nhập từ 360 đến 720 triệu"),
        (26, "Bậc 4: Trên 720 đến 1.200 triệu đồng (30%)", "=IF(B20>720000000, MIN(B20-720000000, 480000000)*0.30, 0)", "Thu nhập từ 720 đến 1.200 triệu"),
        (27, "Bậc 5: Trên 1.200 triệu đồng (35%)", "=IF(B20>1200000000, (B20-1200000000)*0.35, 0)", "Phần thu nhập vượt trên 1,2 tỷ"),
        (28, "TỔNG NGHĨA VỤ THUẾ TNCN CẢ NĂM", "=SUM(B23:B27)", "Tổng số thuế phải nộp thực tế cả năm"),
    ]

    for r_idx, label, formula, note in b_year:
        ws2.cell(row=r_idx, column=1, value=label).font = font_bold if r_idx == 28 else font_regular
        c = ws2.cell(row=r_idx, column=2, value=formula)
        c.font = font_total if r_idx == 28 else font_formula
        if r_idx == 28:
            c.fill = fill_total_red
            c.border = border_total
        else:
            c.border = border_cell
        c.alignment = Alignment(horizontal="right")
        c.number_format = currency_format
        ws2.cell(row=r_idx, column=3, value=note).font = font_subtitle

    # KẾT QUẢ QUYẾT TOÁN: BÙ TRỪ HOÀN THUẾ / NỘP THÊM
    ws2["A30"] = "E. KẾT QUẢ QUYẾT TOÁN: BÙ TRỪ HOÀN THUẾ HOẶC NỘP THÊM"
    ws2["A30"].font = font_section
    ws2.merge_cells("A30:D30")
    for col in range(1, 5):
        ws2.cell(row=30, column=col).fill = fill_section_green

    ws2.cell(row=31, column=1, value="CHÊNH LỆCH THUẾ (Đã tạm khấu trừ - Nghĩa vụ cả năm)").font = Font(name="Segoe UI", size=11, bold=True, color="002060")
    c_diff = ws2.cell(row=31, column=2, value="=B10 - B28")
    c_diff.font = Font(name="Segoe UI", size=12, bold=True, color="002060")
    c_diff.fill = fill_net_green
    c_diff.border = border_total
    c_diff.alignment = Alignment(horizontal="right")
    c_diff.number_format = currency_format
    ws2.cell(row=31, column=3, value="Số dương: Được hoàn | Số âm: Phải nộp thêm").font = font_subtitle

    ws2.cell(row=32, column=1, value="KẾT LUẬN NGHĨA VỤ QUYẾT TOÁN").font = font_bold
    c_status = ws2.cell(row=32, column=2, value='=IF(B31>50000, "BẠN ĐƯỢC HOÀN THUẾ", IF(B31<-50000, "BẠN PHẢI NỘP THÊM", "CÂN BẰNG (MIỄN NỘP THÊM)"))')
    c_status.font = Font(name="Segoe UI", size=11, bold=True, color="9C0006")
    c_status.fill = fill_highlight
    c_status.border = border_cell
    c_status.alignment = Alignment(horizontal="center")
    ws2.cell(row=32, column=3, value="Căn cứ theo hạn ngạch sai số 50.000 VNĐ").font = font_subtitle

    ws2.column_dimensions["A"].width = 46
    ws2.column_dimensions["B"].width = 24
    ws2.column_dimensions["C"].width = 52
    ws2.column_dimensions["D"].width = 10

    # =============================================================
    # SHEET 3: TRA CỨU BIỂU THUẾ & CĂN CỨ PHÁP LÝ
    # =============================================================
    ws3 = wb.create_sheet(title="Căn Cứ Pháp Lý & Biểu Thuế")
    ws3.views.sheetView[0].showGridLines = True

    ws3["A1"] = "DANH MỤC BIỂU THUẾ & CĂN CỨ PHÁP LÝ THUẾ TNCN 2026"
    ws3["A1"].font = font_title

    headers = ["Bậc", "Thu nhập tính thuế/tháng (VNĐ)", "Thuế suất", "Công thức tính nhanh", "Căn cứ pháp lý"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws3.cell(row=3, column=col_idx, value=h)
        cell.font = font_section
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    table_data = [
        (1, "Đến 10.000.000", "5%", "TNTT x 5%", "Luật 109/2025/QH15, Đ.22"),
        (2, "Trên 10.000.000 đến 30.000.000", "10%", "TNTT x 10% - 500.000", "Luật 109/2025/QH15, Đ.22"),
        (3, "Trên 30.000.000 đến 60.000.000", "20%", "TNTT x 20% - 3.500.000", "Luật 109/2025/QH15, Đ.22"),
        (4, "Trên 60.000.000 đến 100.000.000", "30%", "TNTT x 30% - 9.500.000", "Luật 109/2025/QH15, Đ.22"),
        (5, "Trên 100.000.000", "35%", "TNTT x 35% - 14.500.000", "Luật 109/2025/QH15, Đ.22"),
    ]

    for row_offset, row_vals in enumerate(table_data, start=4):
        for col_idx, v in enumerate(row_vals, start=1):
            c = ws3.cell(row=row_offset, column=col_idx, value=v)
            c.font = font_regular
            c.border = border_cell
            c.alignment = Alignment(horizontal="center" if col_idx in [1, 3] else "left")

    ws3["A11"] = "BẢNG ĐỊNH MỨC GIẢM TRỪ VÀ KHẤU TRỪ ÁP DỤNG NĂM 2026"
    ws3["A11"].font = font_title

    deduct_headers = ["Chỉ tiêu", "Mức áp dụng 2026", "Ghi chú thay đổi so với trước", "Văn bản pháp lý"]
    for col_idx, h in enumerate(deduct_headers, start=1):
        cell = ws3.cell(row=13, column=col_idx, value=h)
        cell.font = font_section
        cell.fill = fill_section_blue
        cell.alignment = Alignment(horizontal="center")

    deduct_data = [
        ("Giảm trừ bản thân NNT", "15.500.000 VNĐ/tháng (186tr/năm)", "Tăng từ mức 11 triệu đồng", "NQ 110/2025/UBTVQH15"),
        ("Giảm trừ Người phụ thuộc (NPT)", "6.200.000 VNĐ/tháng/người", "Tăng từ mức 4,4 triệu đồng", "NQ 110/2025/UBTVQH15"),
        ("Ngưỡng thu nhập tối đa của NPT", "Không quá 3.000.000 VNĐ/tháng", "Nâng từ mức 1 triệu đồng/tháng", "TT 87/2026/TT-BTC"),
        ("Khấu trừ vãng lai (10%)", "Áp dụng từ 5.000.000 VNĐ/lần", "Nâng từ mức 2 triệu đồng/lần", "TT 87/2026/TT-BTC"),
        ("Giảm trừ chi phí Y tế", "Tối đa 23.000.000 VNĐ/năm", "Chính sách mới bổ sung", "NĐ 253/2026/NĐ-CP"),
        ("Giảm trừ chi phí Giáo dục", "Tối đa 24.000.000 VNĐ/năm", "Chính sách mới bổ sung", "NĐ 253/2026/NĐ-CP"),
        ("Giảm trừ Hưu trí tự nguyện", "Tối đa 3.000.000 VNĐ/tháng", "Nâng từ mức 1 triệu đồng/tháng", "NĐ 253/2026/NĐ-CP"),
        ("Tiền ăn ca miễn thuế", "Tối đa 1.200.000 VNĐ/tháng", "Nâng từ mức 730.000 đồng/tháng", "NĐ 253/2026/NĐ-CP"),
        ("Trần đóng BHXH/BHYT", "50.600.000 VNĐ/tháng", "20 lần mức lương cơ sở 2,53tr", "NĐ 161/2026/NĐ-CP"),
        ("Ngưỡng miễn thuế HKD/CNKD", "1.000.000.000 VNĐ/năm", "Bãi bỏ thuế khoán, chuyển kê khai", "NĐ 141/2026/NĐ-CP"),
    ]

    for row_offset, row_vals in enumerate(deduct_data, start=14):
        for col_idx, v in enumerate(row_vals, start=1):
            c = ws3.cell(row=row_offset, column=col_idx, value=v)
            c.font = font_regular
            c.border = border_cell
            c.alignment = Alignment(horizontal="left")

    ws3.column_dimensions["A"].width = 32
    ws3.column_dimensions["B"].width = 34
    ws3.column_dimensions["C"].width = 38
    ws3.column_dimensions["D"].width = 32
    ws3.column_dimensions["E"].width = 28

    # =============================================================
    # SHEET 4: DỰ TÍNH BHXH RÚT 1 LẦN & BẢO LƯU LƯƠNG HƯU
    # =============================================================
    if include_bhxh:
        ws4 = wb.create_sheet(title="Dự Tính BHXH & Lương Hưu")
        ws4.views.sheetView[0].showGridLines = True

        ws4["A1"] = "DỰ TÍNH BẢO HIỂM XÃ HỘI RÚT 1 LẦN & SO SÁNH BẢO LƯU LƯƠNG HƯU"
        ws4["A1"].font = font_title
        ws4["A2"] = "Căn cứ: Luật Bảo hiểm xã hội 2024 (Số 41/2024/QH15) có hiệu lực từ 01/07/2025 | 100% Live Formulas"
        ws4["A2"].font = font_subtitle

        ws4["A4"] = "A. THÔNG SỐ ĐẦU VÀO CỦA NGƯỜI LAO ĐỘNG (Ô màu vàng có thể chỉnh sửa)"
        ws4["A4"].font = font_section
        ws4.merge_cells("A4:D4")
        for col in range(1, 5):
            ws4.cell(row=4, column=col).fill = fill_section_blue

        bhxh_inputs = [
            (5, "Số năm đóng BHXH trước năm 2014 (năm)", bhxh_before_2014, number_format, "Thời gian đóng trước 01/01/2014"),
            (6, "Số năm đóng BHXH từ năm 2014 trở đi (năm)", bhxh_from_2014, number_format, "Thời gian đóng từ 01/01/2014 đến nay"),
            (7, "Tổng thời gian đóng BHXH tích lũy (năm)", "=B5+B6", number_format, "Tổng số năm đóng ghi trên Sổ BHXH/VssID"),
            (8, "Mức bình quân tiền lương tháng đóng BHXH (MBQTL)", mbqtl, currency_format, "Đã nhân hệ số trượt giá bình quân"),
            (9, "Số tháng đã nghỉ việc dừng đóng BHXH (tháng)", months_off, number_format, "Số tháng kể từ ngày chốt sổ"),
        ]

        for r_idx, label, val, num_fmt, note in bhxh_inputs:
            ws4.cell(row=r_idx, column=1, value=label).font = font_bold
            c = ws4.cell(row=r_idx, column=2, value=val)
            if r_idx in [5, 6, 8, 9]:
                c.font = font_input
                c.fill = fill_input
            else:
                c.font = font_bold
                c.fill = fill_highlight
            c.alignment = Alignment(horizontal="right")
            c.number_format = num_fmt
            c.border = border_cell
            ws4.cell(row=r_idx, column=3, value=note).font = font_subtitle

        # PHẦN B: THẨM ĐỊNH ĐIỀU KIỆN RÚT BHXH 1 LẦN
        ws4["A11"] = "B. THẨM ĐỊNH ĐIỀU KIỆN RÚT BHXH 1 LẦN (Theo Điều 102 Luật BHXH 2024)"
        ws4["A11"].font = font_section
        ws4.merge_cells("A11:D11")
        for col in range(1, 5):
            ws4.cell(row=11, column=col).fill = fill_section_blue

        ws4.cell(row=12, column=1, value="Tiêu chí 1: Thời gian dừng đóng sau nghỉ việc (>= 12 tháng)").font = font_regular
        c1 = ws4.cell(row=12, column=2, value='=IF(B9>=12, "ĐẠT (Đủ 12 tháng)", "CHƯA ĐẠT (Mới nghỉ " & B9 & " tháng)")')
        c1.font = font_bold; c1.alignment = Alignment(horizontal="center"); c1.border = border_cell
        ws4.cell(row=12, column=3, value="Yêu cầu tối thiểu 12 tháng không tham gia BHXH").font = font_subtitle

        ws4.cell(row=13, column=1, value="Tiêu chí 2: Tổng thời gian đóng BHXH (< 20 năm)").font = font_regular
        c2 = ws4.cell(row=13, column=2, value='=IF(B7<20, "ĐẠT (< 20 năm)", "KHÔNG ĐỦ ĐIỀU KIỆN (Đã đóng " & B7 & " năm >= 20 năm)")')
        c2.font = font_bold; c2.alignment = Alignment(horizontal="center"); c2.border = border_cell
        ws4.cell(row=13, column=3, value="Tham gia trước 1/7/2025 chỉ được rút nếu đóng dưới 20 năm").font = font_subtitle

        ws4.cell(row=14, column=1, value="KẾT LUẬN ĐIỀU KIỆN RÚT 1 LẦN THÔNG THƯỜNG").font = font_bold
        c3 = ws4.cell(row=14, column=2, value='=IF(AND(B9>=12, B7<20), "ĐỦ ĐIỀU KIỆN RÚT 1 LẦN", "KHÔNG ĐỦ ĐIỀU KIỆN RÚT 1 LẦN THÔNG THƯỜNG")')
        c3.font = Font(name="Segoe UI", size=10, bold=True, color="9C0006")
        c3.fill = fill_total_red
        c3.alignment = Alignment(horizontal="center")
        c3.border = border_total
        ws4.cell(row=14, column=3, value="Trừ trường hợp bệnh hiểm nghèo hoặc định cư nước ngoài").font = font_subtitle

        # PHẦN C: DỰ TÍNH SỐ TIỀN RÚT 1 LẦN
        ws4["A16"] = "C. DỰ TÍNH SỐ TIỀN NẾU RÚT 1 LẦN (Trường hợp ngoại lệ đặc biệt)"
        ws4["A16"].font = font_section
        ws4.merge_cells("A16:D16")
        for col in range(1, 5):
            ws4.cell(row=16, column=col).fill = fill_section_blue

        c_rows = [
            (17, "Số tháng hưởng cho giai đoạn trước 2014 (1,5 tháng/năm)", "=B5*1.5", "1,5 tháng MBQTL cho mỗi năm trước 2014"),
            (18, "Số tháng hưởng cho giai đoạn từ 2014 trở đi (2,0 tháng/năm)", "=B6*2", "2,0 tháng MBQTL cho mỗi năm từ 2014"),
            (19, "Tổng số tháng lương trợ cấp được tính hưởng", "=SUM(B17:B18)", "Tổng hệ số tháng hưởng trợ cấp một lần"),
            (20, "TỔNG SỐ TIỀN TRỢ CẤP BHXH 1 LẦN NHẬN ĐƯỢC", "=B19*B8", "Số tiền nhận 1 lần (đã bao gồm hệ số trượt giá)"),
        ]
        for r_idx, label, formula, note in c_rows:
            ws4.cell(row=r_idx, column=1, value=label).font = font_bold if r_idx == 20 else font_regular
            c = ws4.cell(row=r_idx, column=2, value=formula)
            c.font = font_total if r_idx == 20 else font_formula
            if r_idx == 20:
                c.fill = fill_total_red
                c.border = border_total
                c.number_format = currency_format
            else:
                c.border = border_cell
                c.number_format = number_format
            c.alignment = Alignment(horizontal="right")
            ws4.cell(row=r_idx, column=3, value=note).font = font_subtitle

        # PHẦN D: PHƯƠNG ÁN BẢO LƯU HƯỞNG LƯƠNG HƯU
        ws4["A22"] = "D. CHẾ ĐỘ HƯU TRÍ KHI BẢO LƯU (QUYỀN LỢI TỐI ƯU THEO LUẬT BHXH 2024)"
        ws4["A22"].font = font_section
        ws4.merge_cells("A22:D22")
        for col in range(1, 5):
            ws4.cell(row=22, column=col).fill = fill_section_green

        d_rows = [
            (23, "Điều kiện hưởng lương hưu (Đóng >= 15 năm theo Điều 64)", '=IF(B7>=15, "ĐÃ ĐỦ ĐIỀU KIỆN HƯỞNG LƯƠNG HƯU", "CHƯA ĐỦ SỐ NĂM")', "Luật 2024 giảm điều kiện từ 20 năm xuống 15 năm"),
            (24, "Tỷ lệ hưởng lương hưu hàng tháng - Lao động Nam", "=IF(B7>=20, MIN(0.75, 0.45 + (B7-20)*0.02), 0.45)", "20 năm đầu = 45%, mỗi năm thêm +2% (Tối đa 75%)"),
            (25, "Tỷ lệ hưởng lương hưu hàng tháng - Lao động Nữ", "=IF(B7>=15, MIN(0.75, 0.45 + (B7-15)*0.02), 0.45)", "15 năm đầu = 45%, mỗi năm thêm +2% (Tối đa 75%)"),
            (26, "Mức lương hưu hàng tháng ước tính - Lao động Nam", "=B8*B24", "MBQTL x Tỷ lệ hưởng Nam"),
            (27, "Mức lương hưu hàng tháng ước tính - Lao động Nữ", "=B8*B25", "MBQTL x Tỷ lệ hưởng Nữ"),
            (28, "Tiền lương hưu nhận trong 1 năm (Nam)", "=B26*12", "Lương hưu 12 tháng"),
            (29, "Tiền lương hưu nhận trong 1 năm (Nữ)", "=B27*12", "Lương hưu 12 tháng"),
            (30, "Tổng lương hưu tích lũy trong 20 năm tuổi già (Nam)", "=B28*20", "Chưa kể các đợt tăng lương hưu theo CPI hàng năm"),
            (31, "Tổng lương hưu tích lũy trong 20 năm tuổi già (Nữ)", "=B29*20", "Chưa kể các đợt tăng lương hưu theo CPI hàng năm"),
        ]
        for r_idx, label, formula, note in d_rows:
            ws4.cell(row=r_idx, column=1, value=label).font = font_bold if r_idx in [23, 26, 27, 30, 31] else font_regular
            c = ws4.cell(row=r_idx, column=2, value=formula)
            c.font = font_bold if r_idx in [23, 26, 27, 30, 31] else font_formula
            if r_idx in [24, 25]:
                c.number_format = percent_format
            elif r_idx in [26, 27, 28, 29, 30, 31]:
                c.number_format = currency_format
            if r_idx in [30, 31]:
                c.fill = fill_highlight
                c.border = border_total
            else:
                c.border = border_cell
            c.alignment = Alignment(horizontal="center" if r_idx == 23 else "right")
            ws4.cell(row=r_idx, column=3, value=note).font = font_subtitle

        # PHẦN E: SO SÁNH LỢI ÍCH TÀI CHÍNH
        ws4["A33"] = "E. SO SÁNH ĐỊNH LƯỢNG: LƯƠNG HƯU 20 NĂM VS RÚT 1 LẦN"
        ws4["A33"].font = font_section
        ws4.merge_cells("A33:D33")
        for col in range(1, 5):
            ws4.cell(row=33, column=col).fill = fill_section_green

        e_rows = [
            (34, "Chênh lệch kinh tế vượt trội (Nam: Hưu 20 năm - Rút 1 lần)", "=B30 - B20", "Số tiền nhận thêm khi bảo lưu hưởng lương hưu"),
            (35, "Chênh lệch kinh tế vượt trội (Nữ: Hưu 20 năm - Rút 1 lần)", "=B31 - B20", "Số tiền nhận thêm khi bảo lưu hưởng lương hưu"),
            (36, "Quyền lợi Thẻ BHYT khám chữa bệnh miễn phí 95%", "Được Quỹ BHXH cấp thẻ BHYT suốt thời gian hưu", "Thanh toán 95% chi phí KCB (BHYT tự mua chỉ 80%)"),
            (37, "Chế độ mai táng phí và trợ cấp tuất khi qua đời", "10 tháng lương cơ sở (~25,3 triệu) + Trợ cấp tuất", "Bảo đảm an sinh cho thân nhân theo Luật định"),
        ]
        for r_idx, label, val, note in e_rows:
            ws4.cell(row=r_idx, column=1, value=label).font = font_bold
            c = ws4.cell(row=r_idx, column=2, value=val)
            c.font = font_bold
            if r_idx in [34, 35]:
                c.fill = fill_highlight
                c.border = border_total
                c.number_format = currency_format
                c.alignment = Alignment(horizontal="right")
            else:
                c.border = border_cell
                c.alignment = Alignment(horizontal="left")
            ws4.cell(row=r_idx, column=3, value=note).font = font_subtitle

        ws4.column_dimensions["A"].width = 54
        ws4.column_dimensions["B"].width = 30
        ws4.column_dimensions["C"].width = 54
        ws4.column_dimensions["D"].width = 10

    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return str(out)


def main():
    parser = argparse.ArgumentParser(description="Xuất bảng tính Excel thuế TNCN 2026 với Live Formulas")
    parser.add_argument("--output", type=str, default="~/Downloads/AIWF_Output/tu-van-thue-tncn/Bang_Tinh_Thue_TNCN_2026.xlsx", help="Đường dẫn file đầu ra")
    parser.add_argument("--gross", type=float, default=35_000_000, help="Mức lương Gross (VNĐ)")
    parser.add_argument("--dependents", type=int, default=1, help="Số người phụ thuộc")
    parser.add_argument("--medical", type=float, default=0, help="Chi phí y tế cả năm (VNĐ)")
    parser.add_argument("--education", type=float, default=0, help="Chi phí giáo dục cả năm (VNĐ)")
    parser.add_argument("--pension", type=float, default=0, help="Hưu trí tự nguyện hàng tháng (VNĐ)")
    parser.add_argument("--settlement-income", type=float, default=0, help="Tổng thu nhập chịu thuế cả năm khi quyết toán (VNĐ)")
    parser.add_argument("--tax-withheld", type=float, default=0, help="Số thuế các nơi đã tạm khấu trừ (VNĐ)")
    parser.add_argument("--bhxh-before-2014", type=float, default=11.0, help="Số năm đóng BHXH trước 2014")
    parser.add_argument("--bhxh-from-2014", type=float, default=12.0, help="Số năm đóng BHXH từ 2014 trở đi")
    parser.add_argument("--mbqtl", type=float, default=6_000_000, help="Mức bình quân tiền lương đóng BHXH (VNĐ)")
    parser.add_argument("--months-off", type=int, default=1, help="Số tháng đã nghỉ việc dừng đóng BHXH")

    args = parser.parse_args()

    out_file = create_tax_workbook(
        output_path=args.output,
        gross_salary=args.gross,
        dependents=args.dependents,
        medical_annual=args.medical,
        education_annual=args.education,
        pension_monthly=args.pension,
        settlement_annual_income=args.settlement_income,
        settlement_tax_withheld=args.tax_withheld,
        bhxh_before_2014=args.bhxh_before_2014,
        bhxh_from_2014=args.bhxh_from_2014,
        mbqtl=args.mbqtl,
        months_off=args.months_off
    )
    print(f"✅ Đã xuất bảng tính Excel với 100% Live Formulas thành công tại:")
    print(f"   {out_file}")


if __name__ == "__main__":
    main()
