#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_excel_dashboard.py - Tạo file Excel P&L + Dashboard với 100% Live Formulas từ data.json.

- Dữ liệu vào: data.json theo templates/data_schema.md (bắt buộc -i, thiếu file -> thoát mã 2).
- Chỉ tiêu được định danh bằng MÃ SỐ (01, 02, 10, ...). Công thức Excel được sinh từ bản đồ
  mã số -> dòng thực tế, nên bỏ bớt dòng (vd không có mã 23, 31, 32) không làm lệch công thức.
- Dòng tính toán (10, 20, 30, 40, 50, 60, biên lợi nhuận, tăng trưởng, KPI) đều là công thức sống.
- Thuế TNDN (51): số thực tế (pnl['51']) hoặc ước tính = ROUND(MAX(0, LN trước thuế x ô thuế suất)).
  Ô thuế suất là ô nhập hiển thị trên sheet, không có giá trị mặc định ẩn.
- Sheet ẩn "_map" lưu địa chỉ ô của từng mã/KPI để verify_report.py kiểm tra.
"""

import argparse
import sys
from pathlib import Path

import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.page import PageMargins

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pnl_model import (DataError, OPEX_CODES, REGIME_LABEL, load_data,  # noqa: E402
                       present_lines)

PNL_SHEET = "Báo cáo P&L"
Q = f"'{PNL_SHEET}'!"

NAVY = "1E3A8A"
F_TITLE = Font(name="Calibri", size=15, bold=True, color=NAVY)
F_SUB = Font(name="Calibri", size=10, italic=True, color="475569")
F_HEAD = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
F_BOLD = Font(name="Calibri", size=11, bold=True, color="0F172A")
F_REG = Font(name="Calibri", size=11, color="1E293B")
F_ITAL = Font(name="Calibri", size=10, italic=True, color="475569")
F_INPUT = Font(name="Calibri", size=11, bold=True, color="1D4ED8")
F_KPI = Font(name="Calibri", size=16, bold=True, color=NAVY)
F_KPI_L = Font(name="Calibri", size=9, bold=True, color="64748B")
FILL_HEAD = PatternFill("solid", start_color=NAVY, end_color=NAVY)
FILL_SUB = PatternFill("solid", start_color="F1F5F9", end_color="F1F5F9")
FILL_GRAND = PatternFill("solid", start_color="EFF6FF", end_color="EFF6FF")
FILL_CARD = PatternFill("solid", start_color="F8FAFC", end_color="F8FAFC")
FILL_INPUT = PatternFill("solid", start_color="FEF9C3", end_color="FEF9C3")
THIN = Side(border_style="thin", color="CBD5E1")
HAIR = Side(border_style="hair", color="CBD5E1")
DOUBLE = Side(border_style="double", color=NAVY)
B_ROW = Border(bottom=HAIR)
B_SUBTOTAL = Border(top=THIN, bottom=HAIR)
B_GRAND = Border(top=THIN, bottom=DOUBLE)
B_BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
A_C = Alignment(horizontal="center", vertical="center", wrap_text=True)
A_L = Alignment(horizontal="left", vertical="center", wrap_text=True)
A_R = Alignment(horizontal="right", vertical="center")

FMT_VND = '#,##0;[Red](#,##0);"-"'
FMT_PCT = '0.0%;[Red]-0.0%;"-"'
FMT_PP = '+0.0" điểm %";[Red]-0.0" điểm %";"-"'   # chênh lệch biên lợi nhuận, đơn vị điểm phần trăm
FMT_GROWTH = '▲ 0.0%;[Red]▼ 0.0%;"-"'

SUBTOTAL_CODES = {"10", "20", "30", "50"}


def build_pnl_sheet(wb, data):
    ws = wb.create_sheet(PNL_SHEET)
    has_prev = data["_has_prev"]
    last_col = "F" if has_prev else "C"

    ws.merge_cells(f"A1:{last_col}1")
    ws["A1"] = data["company_name"].upper()
    ws["A1"].font = Font(name="Calibri", size=10, bold=True, color="64748B")
    ws.merge_cells(f"A2:{last_col}2")
    ws["A2"] = "BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH"
    ws["A2"].font = F_TITLE
    ws.merge_cells(f"A3:{last_col}3")
    ws["A3"] = f"{REGIME_LABEL[data['regime']]} | {data['period']} | Đơn vị tính: {data.get('currency_unit', 'đồng')}"
    ws["A3"].font = F_SUB

    labels = data.get("period_labels", {})
    headers = [("A", "Mã số", A_C, 8), ("B", "Chỉ tiêu", A_L, 58),
               ("C", labels.get("curr", "Kỳ này"), A_C, 20)]
    if has_prev:
        headers += [("D", labels.get("prev", "Kỳ trước"), A_C, 20),
                    ("E", "Chênh lệch", A_C, 18), ("F", "Tăng trưởng", A_C, 13)]
    for col, text, al, width in headers:
        c = ws[f"{col}5"]
        c.value, c.font, c.fill, c.alignment, c.border = text, F_HEAD, FILL_HEAD, al, B_BOX
        ws.column_dimensions[col].width = width
    ws.row_dimensions[5].height = 30

    lines = present_lines(data)
    row_of = {}
    r = 6
    for code, *_ in lines:
        row_of[code] = r
        r += 1
    rate_row = r + 1  # dòng giả định thuế suất (chỉ dùng khi ước tính)
    periods = [("C", "curr")] + ([("D", "prev")] if has_prev else [])

    def ref(code, col):
        return f"{col}{row_of[code]}" if code in row_of else None

    for code, name, kind, spec in lines:
        row = row_of[code]
        is_grand = code == "60"
        bold = code in SUBTOTAL_CODES or is_grand
        is_ratio = kind == "ratio"
        font = F_BOLD if bold else (F_ITAL if kind in ("sub", "ratio") else F_REG)
        border = B_GRAND if is_grand else (B_SUBTOTAL if bold else B_ROW)
        fill = FILL_GRAND if is_grand else (FILL_SUB if bold else None)

        ws[f"A{row}"] = "" if is_ratio else code
        ws[f"B{row}"] = ("    " + name) if kind in ("sub", "ratio") else name
        for col, per in periods:
            cell = ws[f"{col}{row}"]
            if kind in ("input", "sub"):
                cell.value = data["pnl"][code][per]
            elif kind == "calc":
                terms = [f"{s}{ref(c, col)}" for s, c in spec if ref(c, col)]
                cell.value = "=" + "".join(terms).lstrip("+") if terms else "=0"
            elif kind == "cit":
                if "51" in data["pnl"]:
                    cell.value = data["pnl"]["51"][per]
                else:
                    cell.value = f"=ROUND(MAX(0,{ref('50', col)}*{col}${rate_row}),0)"
            elif kind == "ratio":
                num, den = spec
                cell.value = f'=IF({ref(den, col)}=0,"",{ref(num, col)}/{ref(den, col)})'
        if has_prev:
            if is_ratio:
                ws[f"E{row}"] = f'=IF(OR(C{row}="",D{row}=""),"",(C{row}-D{row})*100)'
                ws[f"F{row}"] = ""
            else:
                ws[f"E{row}"] = f"=C{row}-D{row}"
                ws[f"F{row}"] = f'=IF(D{row}=0,"",(C{row}-D{row})/ABS(D{row}))'
        for col in ["A", "B"] + [c for c, _ in periods] + (["E", "F"] if has_prev else []):
            c = ws[f"{col}{row}"]
            c.font, c.border = font, border
            if fill:
                c.fill = fill
            if col == "A":
                c.alignment = A_C
            elif col == "B":
                c.alignment = A_L
            else:
                c.alignment = A_R
                if col == "F":
                    c.number_format = FMT_GROWTH
                elif col == "E" and is_ratio:
                    c.number_format = FMT_PP
                else:
                    c.number_format = FMT_PCT if is_ratio else FMT_VND
            if kind == "input" or kind == "sub":
                if col in ("C", "D"):
                    c.font = F_INPUT if not bold else c.font

    note_row = r
    if "51" not in data["pnl"]:
        ws[f"B{rate_row}"] = "Thuế suất TNDN giả định để ước tính mã 51 (ô vàng)"
        ws[f"B{rate_row}"].font = F_BOLD
        for col, per in periods:
            c = ws[f"{col}{rate_row}"]
            c.value = data["_cit_rate"][per]
            c.number_format = "0%"
            c.fill, c.font, c.alignment, c.border = FILL_INPUT, F_INPUT, A_R, B_BOX
        ws[f"B{rate_row + 1}"] = ("Mã 51 là ƯỚC TÍNH = lợi nhuận kế toán trước thuế x thuế suất; chưa điều chỉnh chi phí "
                                  "không được trừ, thu nhập miễn thuế, lỗ chuyển kỳ. Thay bằng số trên tờ khai quyết toán "
                                  "TNDN khi có. [CẦN XÁC MINH]")
        ws[f"B{rate_row + 1}"].font = F_ITAL
        ws[f"B{rate_row + 1}"].alignment = A_L
        ws.row_dimensions[rate_row + 1].height = 45
        note_row = rate_row + 2
    ws[f"B{note_row}"] = "Số màu xanh đậm là số nhập từ sổ sách; các dòng còn lại là công thức Excel."
    ws[f"B{note_row}"].font = F_ITAL

    ws.freeze_panes = "C6"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.6, bottom=0.6)
    return ws, row_of


def build_dashboard(wb, data, row_of):
    ws = wb.active
    ws.title = "Dashboard"
    ws.sheet_view.showGridLines = False
    has_prev = data["_has_prev"]
    for col, w in zip("ABCDEFGHI", [2, 24, 20, 24, 20, 24, 20, 24, 20]):
        ws.column_dimensions[col].width = w

    ws.merge_cells("B2:I2")
    ws["B2"] = data["company_name"].upper()
    ws["B2"].font = Font(name="Calibri", size=11, bold=True, color="64748B")
    ws.merge_cells("B3:I3")
    ws["B3"] = data["report_title"]
    ws["B3"].font = F_TITLE
    ws.merge_cells("B4:I4")
    ws["B4"] = f"{data['period']} | Đơn vị tính: {data.get('currency_unit', 'đồng')}"
    ws["B4"].font = F_SUB

    def pr(code, col="C"):
        return f"{Q}{col}{row_of[code]}"

    kpis = [
        ("DOANH THU THUẦN (10)", f"={pr('10')}", FMT_VND,
         f'=IF({pr("10","D")}=0,"",({pr("10")}-{pr("10","D")})/ABS({pr("10","D")}))' if has_prev else None,
         "Tăng trưởng"),
        ("LỢI NHUẬN GỘP (20)", f"={pr('20')}", FMT_VND, f"={pr('GM')}", "Biên gộp"),
        ("LỢI NHUẬN SAU THUẾ (60)", f"={pr('60')}", FMT_VND, f"={pr('NM')}", "Biên ròng"),
    ]
    cash = data.get("cash")
    if cash:
        kpis.append((cash["label"].upper(), cash["curr"], FMT_VND, None, cash.get("note", "")))

    kpi_cells = {}
    for i, (label, value, fmt, sub, sub_label) in enumerate(kpis):
        c0 = "BDFH"[i]
        c1 = chr(ord(c0) + 1)
        ws.merge_cells(f"{c0}6:{c1}6")
        ws.merge_cells(f"{c0}7:{c1}7")
        ws[f"{c0}6"] = label
        ws[f"{c0}6"].font = F_KPI_L
        ws[f"{c0}7"] = value
        ws[f"{c0}7"].font = F_KPI
        ws[f"{c0}7"].number_format = fmt
        ws[f"{c0}7"].alignment = Alignment(horizontal="left")
        ws[f"{c0}8"] = sub_label
        ws[f"{c0}8"].font = F_KPI_L
        if sub:
            ws[f"{c1}8"] = sub
            ws[f"{c1}8"].number_format = FMT_GROWTH if sub_label == "Tăng trưởng" else FMT_PCT
            ws[f"{c1}8"].font = Font(name="Calibri", size=10, bold=True, color="15803D")
            ws[f"{c1}8"].alignment = A_R
        for rr in (6, 7, 8):
            for cc in (c0, c1):
                ws[f"{cc}{rr}"].fill = FILL_CARD
                ws[f"{cc}{rr}"].border = B_BOX
        kpi_cells[label] = f"Dashboard!{c0}7"
    ws.row_dimensions[7].height = 26

    recon = {}
    q = data.get("quarterly") or []
    if q:
        hdr = 11
        for col, text in zip("BCDE", ["Kỳ", "Doanh thu thuần", "Giá vốn hàng bán", "Chi phí hoạt động"]):
            c = ws[f"{col}{hdr}"]
            c.value, c.font, c.fill, c.alignment, c.border = text, F_HEAD, FILL_HEAD, A_C, B_BOX
        for i, item in enumerate(q):
            rr = hdr + 1 + i
            ws[f"B{rr}"] = item["label"]
            ws[f"C{rr}"], ws[f"D{rr}"], ws[f"E{rr}"] = item["revenue"], item["cogs"], item["opex"]
            for col in "BCDE":
                ws[f"{col}{rr}"].border = B_BOX
                ws[f"{col}{rr}"].font = F_REG
                ws[f"{col}{rr}"].alignment = A_C if col == "B" else A_R
                if col != "B":
                    ws[f"{col}{rr}"].number_format = FMT_VND
        last = hdr + len(q)
        tot, diff = last + 1, last + 2
        ws[f"B{tot}"] = "Cộng các kỳ"
        ws[f"B{diff}"] = "Chênh lệch với P&L (phải = 0)"
        opex_terms = "+".join(pr(c) for c in OPEX_CODES[data["regime"]] if c in row_of) or "0"
        targets = {"C": pr("10"), "D": pr("11"), "E": opex_terms}
        for col in "CDE":
            ws[f"{col}{tot}"] = f"=SUM({col}{hdr + 1}:{col}{last})"
            ws[f"{col}{diff}"] = f"={col}{tot}-({targets[col]})"
            for rr in (tot, diff):
                ws[f"{col}{rr}"].number_format = FMT_VND
                ws[f"{col}{rr}"].font = F_BOLD
                ws[f"{col}{rr}"].border = B_BOX
                ws[f"{col}{rr}"].alignment = A_R
            recon[col] = f"Dashboard!{col}{diff}"
        for rr in (tot, diff):
            ws[f"B{rr}"].font = F_BOLD
            ws[f"B{rr}"].border = B_BOX

        chart = BarChart()
        chart.type = "col"
        chart.title = "Doanh thu thuần, giá vốn và chi phí hoạt động theo kỳ"
        chart.y_axis.title = "Đồng"
        chart.y_axis.numFmt = '#,##0'
        chart.width, chart.height = 22, 9
        chart.add_data(Reference(ws, min_col=3, min_row=hdr, max_col=5, max_row=last), titles_from_data=True)
        chart.set_categories(Reference(ws, min_col=2, min_row=hdr + 1, max_row=last))
        ws.add_chart(chart, f"B{diff + 2}")

    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    return kpi_cells, recon


def write_map(wb, data, row_of, kpi_cells, recon):
    ws = wb.create_sheet("_map")
    ws.append(["key", "ref", "kind"])
    for code, row in row_of.items():
        ws.append([f"pnl.{code}.curr", f"{Q}C{row}", "pnl"])
        if data["_has_prev"]:
            ws.append([f"pnl.{code}.prev", f"{Q}D{row}", "pnl"])
    for label, cell in kpi_cells.items():
        ws.append([f"kpi.{label}", cell, "kpi"])
    for col, cell in recon.items():
        ws.append([f"recon.{col}", cell, "recon"])
    ws.sheet_state = "hidden"


def create_financial_workbook(data, output_file):
    wb = openpyxl.Workbook()
    _, row_of = build_pnl_sheet(wb, data)
    kpi_cells, recon = build_dashboard(wb, data, row_of)
    write_map(wb, data, row_of, kpi_cells, recon)
    out = Path(output_file).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return out


def main():
    ap = argparse.ArgumentParser(description="Tạo Excel P&L + Dashboard 100% Live Formulas từ data.json")
    ap.add_argument("--input", "-i", required=True, help="data.json theo templates/data_schema.md")
    ap.add_argument("--output", "-o", required=True, help="Đường dẫn .xlsx đầu ra (trong <output_dir>)")
    args = ap.parse_args()
    try:
        data = load_data(args.input)
    except DataError as e:
        print(f"❌ LỖI DỮ LIỆU: {e}", file=sys.stderr)
        sys.exit(2)
    out = create_financial_workbook(data, args.output)
    print(f"✅ Đã tạo Excel: {out}")
    print("   Bước tiếp theo BẮT BUỘC: python3 .agents/skills/bao-cao-kt/scripts/verify_report.py "
          f"--xlsx \"{out}\" -i \"{args.input}\" --render-dir <process_dir>/review")


if __name__ == "__main__":
    main()
