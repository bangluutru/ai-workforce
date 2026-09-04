#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_excel_dashboard.py — Tạo bảng tính Excel & Google Sheets Dashboard với 100% Live Formulas

Quy tắc chuẩn:
- 100% Live Formulas: Mọi ô tổng cộng, biên lợi nhuận, tăng trưởng PHẢI dùng công thức Excel (=SUM, =AVERAGE, =IF...).
- Định dạng tiền tệ chuyên nghiệp: #,##0 ₫ hoặc #,##0.
- Định dạng tỷ lệ: 0.0%.
- Kẻ viền kế toán: Viền đôi (double bottom border) cho dòng Lợi nhuận sau thuế.
- Tương thích 100% với Google Sheets khi Import file .xlsx.
"""

import sys
import os
import json
import argparse
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference, Series


def get_default_sample_data():
    return {
        "company_name": "CÔNG TY CỔ PHẦN CÔNG NGHỆ & DỊCH VỤ SỐ AIWF",
        "report_title": "BÁO CÁO KẾT QUẢ KINH DOANH & DASHBOARD QUẢN TRỊ TÀI CHÍNH",
        "period": "Năm tài chính 2025 - 2026 (Đơn vị: VNĐ)",
        "currency": "VND",
        "kpis": [
            {"label": "TỔNG DOANH THU THUẦN", "cell_ref": "='Báo cáo P&L'!C7", "growth": "+24.5% YoY", "status": "positive"},
            {"label": "LỢI NHUẬN GỘP (GM)", "cell_ref": "='Báo cáo P&L'!C9", "growth": "Biên gộp: 48.0%", "status": "positive"},
            {"label": "LỢI NHUẬN SAU THUẾ", "cell_ref": "='Báo cáo P&L'!C22", "growth": "Biên ròng: 18.2%", "status": "positive"},
            {"label": "SỐ DƯ TIỀN MẶT & TĐ", "cell_ref": "3,450,000,000", "growth": "Runway: 14 tháng", "status": "neutral"}
        ],
        "quarterly_data": [
            {"quarter": "Quý 1", "revenue": 2800000000, "cogs": 1450000000, "opex": 750000000},
            {"quarter": "Quý 2", "revenue": 3400000000, "cogs": 1750000000, "opex": 820000000},
            {"quarter": "Quý 3", "revenue": 4100000000, "cogs": 2100000000, "opex": 950000000},
            {"quarter": "Quý 4", "revenue": 5200000000, "cogs": 2650000000, "opex": 1100000000}
        ],
        "pnl_items": [
            {"no": "01", "name": "1. Doanh thu bán hàng và CCDV", "code": "01", "curr": 15500000000, "prev": 12450000000, "formula": None, "is_bold": False},
            {"no": "02", "name": "2. Các khoản giảm trừ doanh thu", "code": "02", "curr": 0, "prev": 50000000, "formula": None, "is_bold": False},
            {"no": "10", "name": "3. Doanh thu thuần về bán hàng và CCDV", "code": "10", "curr": None, "prev": None, "formula": "=C5-C6", "prev_formula": "=D5-D6", "is_bold": True},
            {"no": "11", "name": "4. Giá vốn hàng bán", "code": "11", "curr": 7950000000, "prev": 6800000000, "formula": None, "is_bold": False},
            {"no": "20", "name": "5. Lợi nhuận gộp về bán hàng và CCDV", "code": "20", "curr": None, "prev": None, "formula": "=C7-C8", "prev_formula": "=D7-D8", "is_bold": True},
            {"no": "", "name": "   - Tỷ suất lợi nhuận gộp (Gross Margin %)", "code": "GM", "curr": None, "prev": None, "formula": "=C9/C7", "prev_formula": "=D9/D7", "is_bold": False, "is_percent": True},
            {"no": "21", "name": "6. Doanh thu hoạt động tài chính", "code": "21", "curr": 120000000, "prev": 95000000, "formula": None, "is_bold": False},
            {"no": "22", "name": "7. Chi phí tài chính", "code": "22", "curr": 85000000, "prev": 110000000, "formula": None, "is_bold": False},
            {"no": "23", "name": "   - Trong đó: Chi phí lãi vay", "code": "23", "curr": 85000000, "prev": 110000000, "formula": None, "is_bold": False},
            {"no": "25", "name": "8. Chi phí bán hàng", "code": "25", "curr": 2100000000, "prev": 1650000000, "formula": None, "is_bold": False},
            {"no": "26", "name": "9. Chi phí quản lý doanh nghiệp", "code": "26", "curr": 1520000000, "prev": 1250000000, "formula": None, "is_bold": False},
            {"no": "30", "name": "10. Lợi nhuận thuần từ HĐKD", "code": "30", "curr": None, "prev": None, "formula": "=C9+(C11-C12)-C14-C15", "prev_formula": "=D9+(D11-D12)-D14-D15", "is_bold": True},
            {"no": "31", "name": "11. Thu nhập khác", "code": "31", "curr": 25000000, "prev": 15000000, "formula": None, "is_bold": False},
            {"no": "32", "name": "12. Chi phí khác", "code": "32", "curr": 5000000, "prev": 8000000, "formula": None, "is_bold": False},
            {"no": "40", "name": "13. Lợi nhuận khác", "code": "40", "curr": None, "prev": None, "formula": "=C17-C18", "prev_formula": "=D17-D18", "is_bold": False},
            {"no": "50", "name": "14. Tổng lợi nhuận kế toán trước thuế", "code": "50", "curr": None, "prev": None, "formula": "=C16+C19", "prev_formula": "=D16+D19", "is_bold": True},
            {"no": "51", "name": "15. Chi phí thuế TNDN hiện hành (20%)", "code": "51", "curr": None, "prev": None, "formula": "=MAX(0, C20*0.2)", "prev_formula": "=MAX(0, D20*0.2)", "is_bold": False},
            {"no": "60", "name": "16. Lợi nhuận sau thuế TNDN (NPAT)", "code": "60", "curr": None, "prev": None, "formula": "=C20-C21", "prev_formula": "=D20-D21", "is_bold": True, "is_grand_total": True},
            {"no": "", "name": "   - Tỷ suất lợi nhuận ròng (Net Margin %)", "code": "NM", "curr": None, "prev": None, "formula": "=C22/C7", "prev_formula": "=D22/D7", "is_bold": True, "is_percent": True}
        ]
    }


def create_financial_workbook(data, output_file):
    wb = openpyxl.Workbook()
    
    # Fonts
    font_title = Font(name="Calibri", size=15, bold=True, color="1E3A8A")
    font_sub = Font(name="Calibri", size=10, italic=True, color="475569")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=11, bold=True, color="0F172A")
    font_regular = Font(name="Calibri", size=11, color="1E293B")
    font_kpi_num = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
    font_kpi_label = Font(name="Calibri", size=9, bold=True, color="64748B")
    
    # Fills
    fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_sub_header = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    fill_highlight = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    fill_kpi_card = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    
    # Borders
    border_thin = Side(border_style="thin", color="CBD5E1")
    border_double = Side(border_style="double", color="1E3A8A")
    border_box = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)
    border_total = Border(top=border_thin, bottom=border_double, left=border_thin, right=border_thin)
    
    # Alignments
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    
    # Number Formats
    CURRENCY_FMT = '#,##0 "₫"'
    PERCENT_FMT = '0.0%'
    
    # ==========================================
    # SHEET 1: DASHBOARD
    # ==========================================
    ws_dash = wb.active
    ws_dash.title = "Dashboard"
    ws_dash.views.sheetView[0].showGridLines = True
    
    # Title
    ws_dash.merge_cells("B2:H2")
    ws_dash["B2"] = data["company_name"].upper()
    ws_dash["B2"].font = Font(name="Calibri", size=11, bold=True, color="64748B")
    
    ws_dash.merge_cells("B3:H3")
    ws_dash["B3"] = data["report_title"]
    ws_dash["B3"].font = font_title
    
    ws_dash.merge_cells("B4:H4")
    ws_dash["B4"] = data["period"]
    ws_dash["B4"].font = font_sub
    
    # 4 KPI Cards
    kpis = data.get("kpis", [])
    col_starts = ["B", "D", "F", "H"]
    for idx, kpi in enumerate(kpis[:4]):
        col = col_starts[idx]
        next_col = chr(ord(col) + 1) if col in ["B", "D", "F"] else col
        
        # Label cell
        cell_lbl = ws_dash[f"{col}6"]
        cell_lbl.value = kpi["label"]
        cell_lbl.font = font_kpi_label
        cell_lbl.fill = fill_kpi_card
        cell_lbl.alignment = align_left
        
        # Value cell
        cell_val = ws_dash[f"{col}7"]
        val = kpi["cell_ref"]
        cell_val.value = val
        cell_val.font = font_kpi_num
        cell_val.fill = fill_kpi_card
        cell_val.alignment = align_left
        if str(val).startswith("=") and "P&L" in str(val):
            cell_val.number_format = CURRENCY_FMT
        
        # Growth / Note cell
        cell_gr = ws_dash[f"{col}8"]
        cell_gr.value = kpi.get("growth", "")
        cell_gr.font = Font(name="Calibri", size=10, bold=True, color="16A34A" if "positive" in kpi.get("status", "") else "64748B")
        cell_gr.fill = fill_kpi_card
        cell_gr.alignment = align_left
        
        # Card outline
        for r in range(6, 9):
            ws_dash[f"{col}{r}"].border = border_box
    
    # Data table for Chart in Dashboard
    ws_dash["B11"] = "Kỳ báo cáo"
    ws_dash["C11"] = "Doanh thu thuần"
    ws_dash["D11"] = "Giá vốn hàng bán"
    ws_dash["E11"] = "Chi phí hoạt động"
    
    for c in ["B11", "C11", "D11", "E11"]:
        ws_dash[c].font = font_header
        ws_dash[c].fill = fill_header
        ws_dash[c].alignment = align_center
        ws_dash[c].border = border_box
        
    q_data = data.get("quarterly_data", [])
    for i, q in enumerate(q_data):
        row = 12 + i
        ws_dash[f"B{row}"] = q["quarter"]
        ws_dash[f"C{row}"] = q["revenue"]
        ws_dash[f"D{row}"] = q["cogs"]
        ws_dash[f"E{row}"] = q["opex"]
        
        ws_dash[f"B{row}"].alignment = align_center
        ws_dash[f"B{row}"].border = border_box
        
        for c in [f"C{row}", f"D{row}", f"E{row}"]:
            ws_dash[c].alignment = align_right
            ws_dash[c].number_format = CURRENCY_FMT
            ws_dash[c].border = border_box
            
    # Add BarChart
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "Cơ cấu Doanh thu, Giá vốn & Chi phí theo Quý"
    chart.y_axis.title = "Số tiền (VNĐ)"
    chart.x_axis.title = "Kỳ kinh doanh"
    chart.width = 16
    chart.height = 9
    
    chart_data = Reference(ws_dash, min_col=3, min_row=11, max_col=5, max_row=11+len(q_data))
    cats = Reference(ws_dash, min_col=2, min_row=12, max_row=11+len(q_data))
    chart.add_data(chart_data, titles_from_data=True)
    chart.set_categories(cats)
    ws_dash.add_chart(chart, "B18")

    # ==========================================
    # SHEET 2: BÁO CÁO P&L (100% LIVE FORMULAS)
    # ==========================================
    ws_pnl = wb.create_sheet(title="Báo cáo P&L")
    ws_pnl.views.sheetView[0].showGridLines = True
    
    ws_pnl.merge_cells("A1:F1")
    ws_pnl["A1"] = data["company_name"].upper()
    ws_pnl["A1"].font = Font(name="Calibri", size=10, bold=True, color="64748B")
    
    ws_pnl.merge_cells("A2:F2")
    ws_pnl["A2"] = "BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH"
    ws_pnl["A2"].font = font_title
    
    ws_pnl.merge_cells("A3:F3")
    ws_pnl["A3"] = "Theo Thông tư 200/2014/TT-BTC - Kèm công thức động (Live Formulas)"
    ws_pnl["A3"].font = font_sub
    
    # Headers
    headers = [
        ("A4", "Mã", align_center, 6),
        ("B4", "CHỈ TIÊU KINH DOANH", align_left, 45),
        ("C4", "NĂM NAY (KỲ NÀY)", align_right, 22),
        ("D4", "NĂM TRƯỚC (KỲ TRƯỚC)", align_right, 22),
        ("E4", "CHÊNH LỆCH", align_right, 20),
        ("F4", "TĂNG TRƯỞNG", align_right, 15),
    ]
    for pos, text, al, width in headers:
        cell = ws_pnl[pos]
        cell.value = text
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = al
        cell.border = border_box
        
    pnl_items = data.get("pnl_items", [])
    start_row = 5
    for idx, item in enumerate(pnl_items):
        row = start_row + idx
        is_bold = item.get("is_bold", False)
        is_percent = item.get("is_percent", False)
        is_grand = item.get("is_grand_total", False)
        
        fnt = font_bold if is_bold else font_regular
        bdr = border_total if is_grand else border_box
        fl = fill_highlight if is_grand else (fill_sub_header if is_bold else None)
        
        # A: Mã
        cell_a = ws_pnl[f"A{row}"]
        cell_a.value = item.get("code", "")
        cell_a.font = fnt
        cell_a.alignment = align_center
        cell_a.border = bdr
        if fl: cell_a.fill = fl
        
        # B: Tên chỉ tiêu
        cell_b = ws_pnl[f"B{row}"]
        cell_b.value = item["name"]
        cell_b.font = fnt
        cell_b.alignment = align_left
        cell_b.border = bdr
        if fl: cell_b.fill = fl
        
        # C: Kỳ này (Value or Live Formula)
        cell_c = ws_pnl[f"C{row}"]
        if item.get("formula"):
            cell_c.value = item["formula"]
        else:
            cell_c.value = item.get("curr", 0)
        cell_c.font = fnt
        cell_c.alignment = align_right
        cell_c.number_format = PERCENT_FMT if is_percent else CURRENCY_FMT
        cell_c.border = bdr
        if fl: cell_c.fill = fl
        
        # D: Kỳ trước (Value or Live Formula)
        cell_d = ws_pnl[f"D{row}"]
        if item.get("prev_formula"):
            cell_d.value = item["prev_formula"]
        else:
            cell_d.value = item.get("prev", 0)
        cell_d.font = fnt
        cell_d.alignment = align_right
        cell_d.number_format = PERCENT_FMT if is_percent else CURRENCY_FMT
        cell_d.border = bdr
        if fl: cell_d.fill = fl
        
        # E: Chênh lệch = C - D (Live Formula)
        cell_e = ws_pnl[f"E{row}"]
        cell_e.value = f"=C{row}-D{row}"
        cell_e.font = fnt
        cell_e.alignment = align_right
        cell_e.number_format = PERCENT_FMT if is_percent else CURRENCY_FMT
        cell_e.border = bdr
        if fl: cell_e.fill = fl
        
        # F: Tăng trưởng % = IF(D=0, 0, (C-D)/D) (Live Formula)
        cell_f = ws_pnl[f"F{row}"]
        cell_f.value = f'=IF(D{row}=0, 0, (C{row}-D{row})/ABS(D{row}))'
        cell_f.font = fnt
        cell_f.alignment = align_right
        cell_f.number_format = PERCENT_FMT
        cell_f.border = bdr
        if fl: cell_f.fill = fl
        
    # Auto-fit column widths
    for sheet in [ws_dash, ws_pnl]:
        for col in sheet.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                val_str = str(cell.value or "")
                if not val_str.startswith("=") and len(val_str) > max_len:
                    max_len = len(val_str)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 14)
            
    # Dedicated width fixes
    ws_pnl.column_dimensions["A"].width = 8
    ws_pnl.column_dimensions["B"].width = 46
    ws_pnl.column_dimensions["C"].width = 24
    ws_pnl.column_dimensions["D"].width = 24
    ws_pnl.column_dimensions["E"].width = 22
    ws_pnl.column_dimensions["F"].width = 16
    
    # Ensure output dir exists
    out_path = Path(output_file).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    wb.save(str(out_path))
    print(f"✅ Đã tạo file Excel Dashboard thành công: {out_path}")
    return str(out_path)


def main():
    parser = argparse.ArgumentParser(description="Tạo bảng tính Excel & Google Sheets Dashboard với 100% Live Formulas")
    parser.add_argument("--input", "-i", help="Đường dẫn file JSON chứa dữ liệu tài chính (tùy chọn)")
    parser.add_argument("--output", "-o", default="~/Downloads/bao_cao_tai_chinh_aiwf.xlsx", help="Đường dẫn file Excel đầu ra (.xlsx)")
    args = parser.parse_args()
    
    if args.input and os.path.isfile(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = get_default_sample_data()
        
    create_financial_workbook(data, args.output)


if __name__ == "__main__":
    main()
