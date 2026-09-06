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
    pension_monthly: float = 0
):
    wb = openpyxl.Workbook()
    
    # -------------------------------------------------------------
    # STYLES & THEME
    # -------------------------------------------------------------
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
    fill_input = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid") # Vàng nhạt cho ô nhập
    fill_highlight = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid") # Xanh nhạt cho kết quả
    fill_total_red = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid") # Cam nhạt cho thuế
    fill_net_green = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid") # Xanh dương cho Net

    thin_border_side = Side(border_style="thin", color="D9D9D9")
    thick_bottom_side = Side(border_style="medium", color="1B365D")
    double_bottom_side = Side(border_style="double", color="1B365D")

    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_total = Border(top=thin_border_side, bottom=double_bottom_side)

    currency_format = '#,##0 "VNĐ"'
    percent_format = '0.00%'
    number_format = '#,##0'

    # -------------------------------------------------------------
    # SHEET 1: TÍNH THUẾ LƯƠNG 2026
    # -------------------------------------------------------------
    ws1 = wb.active
    ws1.title = "Tính Thuế TNCN 2026"
    ws1.views.sheetView[0].showGridLines = True

    # Tiêu đề
    ws1["A1"] = "BẢNG TÍNH THUẾ THU NHẬP CÁ NHÂN & LƯƠNG NET (KỲ 2026)"
    ws1["A1"].font = font_title
    ws1["A2"] = "Căn cứ: Luật 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP | 100% Live Formulas"
    ws1["A2"].font = font_subtitle

    # PHẦN A: THÔNG SỐ ĐẦU VÀO (INPUT)
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

    # PHẦN B: BẢO HIỂM BẮT BUỘC (LIVE FORMULAS)
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

    # PHẦN C: CÁC KHOẢN GIẢM TRỪ THUẾ (LIVE FORMULAS)
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

    # THU NHẬP TÍNH THUẾ (TNTT)
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

    # PHẦN E: BIỂU THUẾ LŨY TIẾN 5 BẬC (LIVE FORMULAS)
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

    # PHẦN F: KẾT QUẢ CUỐI CÙNG (NET & HIỆU QUẢ)
    ws1["A36"] = "F. KẾT QUẢ TỔNG HỢP: THỰC NHẬN (LƯƠNG NET)"
    ws1["A36"].font = font_section
    ws1.merge_cells("A36:D36")
    for col in range(1, 5):
        ws1.cell(row=36, column=col).fill = fill_section_green

    ws1.cell(row=37, column=1, value="LƯƠNG THỰC NHẬN (NET = Gross - BH - Thuế)").font = Font(name="Segoe UI", size=11, bold=True, color="002060")
    c_net = ws1.cell(row=37, column=2, value="=B5 - B15 - B34")
    c_net.font = Font(name="Segoe UI", size=12, bold=True, color="002060")
    c_net.fill = fill_net_green
    c_net.border = Border(top=thin_border_side, bottom=double_bottom_side, left=thin_border_side, right=thin_border_side)
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

    # Set column widths
    ws1.column_dimensions["A"].width = 46
    ws1.column_dimensions["B"].width = 24
    ws1.column_dimensions["C"].width = 52
    ws1.column_dimensions["D"].width = 10

    # -------------------------------------------------------------
    # SHEET 2: TRA CỨU BIỂU THUẾ & CĂN CỨ PHÁP LÝ
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Căn Cứ Pháp Lý & Biểu Thuế")
    ws2.views.sheetView[0].showGridLines = True

    ws2["A1"] = "DANH MỤC BIỂU THUẾ & CĂN CỨ PHÁP LÝ THUẾ TNCN 2026"
    ws2["A1"].font = font_title

    headers = ["Bậc", "Thu nhập tính thuế/tháng (VNĐ)", "Thuế suất", "Công thức tính nhanh", "Căn cứ pháp lý"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
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
            c = ws2.cell(row=row_offset, column=col_idx, value=v)
            c.font = font_regular
            c.border = border_cell
            c.alignment = Alignment(horizontal="center" if col_idx in [1, 3] else "left")

    # Bảng phụ: Các định mức giảm trừ
    ws2["A11"] = "BẢNG ĐỊNH MỨC GIẢM TRỪ VÀ KHẤU TRỪ ÁP DỤNG NĂM 2026"
    ws2["A11"].font = font_title

    deduct_headers = ["Chỉ tiêu", "Mức áp dụng 2026", "Ghi chú thay đổi so với trước", "Văn bản pháp lý"]
    for col_idx, h in enumerate(deduct_headers, start=1):
        cell = ws2.cell(row=13, column=col_idx, value=h)
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
            c = ws2.cell(row=row_offset, column=col_idx, value=v)
            c.font = font_regular
            c.border = border_cell
            c.alignment = Alignment(horizontal="left")

    ws2.column_dimensions["A"].width = 32
    ws2.column_dimensions["B"].width = 34
    ws2.column_dimensions["C"].width = 38
    ws2.column_dimensions["D"].width = 32
    ws2.column_dimensions["E"].width = 28

    # Lưu workbook
    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return str(out)


def main():
    parser = argparse.ArgumentParser(description="Xuất bảng tính Excel thuế TNCN 2026 với Live Formulas")
    parser.add_argument("--output", type=str, default="~/Downloads/Bang_Tinh_Thue_TNCN_2026.xlsx", help="Đường dẫn file đầu ra")
    parser.add_argument("--gross", type=float, default=35_000_000, help="Mức lương Gross (VNĐ)")
    parser.add_argument("--dependents", type=int, default=1, help="Số người phụ thuộc")
    parser.add_argument("--medical", type=float, default=0, help="Chi phí y tế cả năm (VNĐ)")
    parser.add_argument("--education", type=float, default=0, help="Chi phí giáo dục cả năm (VNĐ)")
    parser.add_argument("--pension", type=float, default=0, help="Hưu trí tự nguyện hàng tháng (VNĐ)")

    args = parser.parse_args()

    out_file = create_tax_workbook(
        output_path=args.output,
        gross_salary=args.gross,
        dependents=args.dependents,
        medical_annual=args.medical,
        education_annual=args.education,
        pension_monthly=args.pension
    )
    print(f"✅ Đã xuất bảng tính Excel với 100% Live Formulas thành công tại:")
    print(f"   {out_file}")


if __name__ == "__main__":
    main()
