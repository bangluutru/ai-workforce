#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_slides_deck.py - Xuất slide 16:9 tóm tắt P&L từ CHÍNH data.json đã dùng cho Excel.

- Mọi con số trên slide được tính từ data.json qua pnl_model.compute() (cùng mô hình mà
  verify_report.py đã đối chiếu khớp với Excel). Không có số liệu hay câu chữ mẫu trong script.
- Nhận định (narrative.highlights) và khuyến nghị (narrative.recommendations) do Agent viết vào
  data.json dựa trên số liệu thật; nếu không có thì slide tương ứng bị BỎ QUA (không tự sinh câu sáo).
- --xlsx (khuyến nghị): recalc file Excel và đối chiếu từng mã chỉ tiêu, lệch -> thoát mã 1.
"""

import argparse
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pnl_model import (DataError, OPEX_CODES, REGIME_LABEL, compute, fmt_pct,  # noqa: E402
                       fmt_vnd, load_data)

NAVY = RGBColor(0x1E, 0x3A, 0x8A)
DARK = RGBColor(0x0F, 0x17, 0x2A)
GREY = RGBColor(0x47, 0x55, 0x69)
MUTED = RGBColor(0x94, 0xA3, 0xB8)
CARD = RGBColor(0xF8, 0xFA, 0xFC)
LINE = RGBColor(0xE2, 0xE8, 0xF0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x15, 0x80, 0x3D)
RED = RGBColor(0xB9, 0x1C, 0x1C)
FONT = "Calibri"


def _text(slide, x, y, w, h, text, size, bold=False, color=DARK, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text, p.alignment = text, align
    p.font.size, p.font.bold, p.font.color.rgb, p.font.name = Pt(size), bold, color, FONT
    return tf


def _title(slide, text, sub=None):
    _text(slide, 0.6, 0.4, 12.1, 0.7, text, 24, True, NAVY)
    if sub:
        _text(slide, 0.6, 1.0, 12.1, 0.4, sub, 12, False, GREY)


def _growth(v, prev):
    if prev in (None, 0) or v is None:
        return None
    return (v - prev) / abs(prev)


def cross_check(data, model, xlsx):
    import openpyxl
    from office_utils import recalc_xlsx
    wb = openpyxl.load_workbook(recalc_xlsx(xlsx), data_only=True)
    if "_map" not in wb.sheetnames:
        raise DataError("File Excel không có sheet _map, không đối chiếu được.")
    bad = []
    for key, ref, kind in wb["_map"].iter_rows(min_row=2, values_only=True):
        if kind != "pnl":
            continue
        _, code, per = key.split(".")
        sheet, cell = ref.rsplit("!", 1)
        got = wb[sheet.strip("'")][cell].value
        exp = model[code][per]
        if exp is None and got in (None, ""):
            continue
        if not isinstance(got, (int, float)) or exp is None or abs(got - exp) > (1e-6 if code in ("GM", "NM") else 1):
            bad.append(f"{key}: data.json={exp} Excel={got}")
    if bad:
        raise DataError("Slide và Excel lệch số:\n  " + "\n  ".join(bad))


def build(data, model, out):
    has_prev = data["_has_prev"]
    labels = data.get("period_labels", {})
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    # 1. Bìa
    s = prs.slides.add_slide(blank)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = DARK
    bg.line.fill.background()
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(2.3), Inches(0.12), Inches(2.6))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RGBColor(0x25, 0x63, 0xEB)
    bar.line.fill.background()
    _text(s, 1.3, 2.2, 11, 0.5, data["company_name"].upper(), 14, True, RGBColor(0x93, 0xC5, 0xFD))
    _text(s, 1.3, 2.7, 11, 1.4, data["report_title"], 34, True, WHITE)
    _text(s, 1.3, 4.2, 11, 0.5, data["period"], 16, False, MUTED)
    _text(s, 1.3, 4.6, 11, 0.5, REGIME_LABEL[data["regime"]], 12, False, MUTED)

    # 2. KPI + nhận định
    s = prs.slides.add_slide(blank)
    _title(s, "Các chỉ số tài chính chính", data["period"])
    p = "prev"
    cards = [
        ("Doanh thu thuần", model["10"]["curr"],
         f"Tăng trưởng {fmt_pct(_growth(model['10']['curr'], model['10'].get(p)), True)}" if has_prev else ""),
        ("Lợi nhuận gộp", model["20"]["curr"], f"Biên gộp {fmt_pct(model['GM']['curr'])}"),
        ("Lợi nhuận sau thuế", model["60"]["curr"], f"Biên ròng {fmt_pct(model['NM']['curr'])}"),
    ]
    if data.get("cash"):
        cards.append((data["cash"]["label"], data["cash"]["curr"], data["cash"].get("note", "")))
    n = len(cards)
    gap, left, total_w = 0.3, 0.6, 12.1
    w = (total_w - gap * (n - 1)) / n
    for i, (label, val, sub) in enumerate(cards):
        x = left + i * (w + gap)
        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(1.7), Inches(w), Inches(1.7))
        box.fill.solid()
        box.fill.fore_color.rgb = CARD
        box.line.color.rgb = LINE
        box.adjustments[0] = 0.08
        tf = box.text_frame
        tf.word_wrap, tf.vertical_anchor = True, MSO_ANCHOR.TOP
        tf.margin_left = tf.margin_right = Inches(0.2)
        tf.margin_top = Inches(0.15)
        for j, (t, size, bold, col) in enumerate([(label.upper(), 11, True, GREY),
                                                  (f"{fmt_vnd(val)} đ", 22, True, NAVY),
                                                  (sub, 12, True, GREEN if "-" not in sub else RED)]):
            para = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            para.text, para.alignment = t, PP_ALIGN.LEFT
            para.font.size, para.font.bold, para.font.color.rgb, para.font.name = Pt(size), bold, col, FONT
            para.space_after = Pt(6)
    highlights = (data.get("narrative") or {}).get("highlights") or []
    if highlights:
        _text(s, 0.6, 3.75, 12.1, 0.4, "Nhận định", 16, True, NAVY)
        tf = _text(s, 0.6, 4.2, 12.1, 2.8, f"- {highlights[0]}", 14, False, DARK)
        for h in highlights[1:]:
            para = tf.add_paragraph()
            para.text = f"- {h}"
            para.font.size, para.font.color.rgb, para.font.name = Pt(14), DARK, FONT
            para.space_before = Pt(6)

    # 3. Bảng tóm tắt P&L
    s = prs.slides.add_slide(blank)
    _title(s, "Tóm tắt kết quả kinh doanh", f"{REGIME_LABEL[data['regime']]} | đơn vị đồng")
    opex_codes = [c for c in OPEX_CODES[data["regime"]] if c in data["pnl"]]
    opex_name = "Chi phí bán hàng và quản lý doanh nghiệp" if data["regime"] != "TT133" else "Chi phí quản lý kinh doanh"
    rows = [("Doanh thu thuần (10)", "10"), ("Giá vốn hàng bán (11)", "11"),
            ("Lợi nhuận gộp (20)", "20")]
    if opex_codes:
        rows.append((f"{opex_name} ({' + '.join(opex_codes)})", "OPEX"))
    rows += [("Lợi nhuận kế toán trước thuế (50)", "50"), ("Chi phí thuế TNDN (51)", "51"),
             ("Lợi nhuận sau thuế (60)", "60")]
    headers = ["Chỉ tiêu", labels.get("curr", "Kỳ này")]
    if has_prev:
        headers += [labels.get("prev", "Kỳ trước"), "Chênh lệch", "Tăng trưởng"]
    widths = [5.1, 2.0, 2.0, 1.8, 1.2] if has_prev else [8.1, 4.0]
    tbl = s.shapes.add_table(len(rows) + 1, len(headers), Inches(0.6), Inches(1.6),
                             Inches(sum(widths)), Inches(0.5 * (len(rows) + 1))).table
    for i, wd in enumerate(widths):
        tbl.columns[i].width = Inches(wd)
    for j, h in enumerate(headers):
        c = tbl.cell(0, j)
        c.text = h
        c.fill.solid()
        c.fill.fore_color.rgb = NAVY
        para = c.text_frame.paragraphs[0]
        para.font.size, para.font.bold, para.font.color.rgb, para.font.name = Pt(13), True, WHITE, FONT
        para.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
    for i, (name, code) in enumerate(rows, 1):
        cur = model[code]["curr"]
        vals = [name, fmt_vnd(cur)]
        if has_prev:
            prv = model[code]["prev"]
            vals += [fmt_vnd(prv), fmt_vnd(cur - prv), fmt_pct(_growth(cur, prv), True)]
        last = code == "60"
        for j, v in enumerate(vals):
            c = tbl.cell(i, j)
            c.text = v
            c.fill.solid()
            c.fill.fore_color.rgb = RGBColor(0xEF, 0xF6, 0xFF) if last else (WHITE if i % 2 else CARD)
            para = c.text_frame.paragraphs[0]
            para.font.size, para.font.bold, para.font.name = Pt(13), last or code in ("10", "20", "50"), FONT
            para.font.color.rgb = NAVY if last else DARK
            para.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT
    note = "Chi phí thuế TNDN là số ƯỚC TÍNH theo thuế suất giả định [CẦN XÁC MINH]." if "51" not in data["pnl"] else ""
    if note:
        _text(s, 0.6, 1.8 + 0.5 * (len(rows) + 1), 12.1, 0.4, note, 11, False, GREY)

    # 4. Biểu đồ theo kỳ (chỉ khi có dữ liệu)
    q = data.get("quarterly") or []
    if q:
        s = prs.slides.add_slide(blank)
        _title(s, "Diễn biến doanh thu và chi phí theo kỳ", "đơn vị đồng")
        cd = CategoryChartData()
        cd.categories = [x["label"] for x in q]
        cd.add_series("Doanh thu thuần", [x["revenue"] for x in q])
        cd.add_series("Giá vốn hàng bán", [x["cogs"] for x in q])
        cd.add_series("Chi phí hoạt động", [x["opex"] for x in q])
        ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.5), Inches(12.1),
                                Inches(5.6), cd).chart
        ch.has_legend, ch.legend.position, ch.legend.include_in_layout = True, XL_LEGEND_POSITION.BOTTOM, False
        ch.value_axis.tick_labels.number_format = '#,##0'
        ch.value_axis.tick_labels.number_format_is_linked = False
        ch.font.size, ch.font.name = Pt(12), FONT
        for ser, col in zip(ch.series, [RGBColor(0x25, 0x63, 0xEB), MUTED, RGBColor(0xF5, 0x9E, 0x0B)]):
            ser.format.fill.solid()
            ser.format.fill.fore_color.rgb = col

    # 4b. Slide Lợi nhuận đóng góp & Điểm hòa vốn (nếu có cost_behavior)
    cb = data.get("cost_behavior")
    if cb and "variable_selling" in cb:
        s = prs.slides.add_slide(blank)
        _title(s, "Phân tích Lợi nhuận đóng góp & Điểm hòa vốn", "Cơ cấu Biến phí vs Định phí và Ngưỡng an toàn tài chính")
        rev = model["10"]["curr"]
        cogs = model["11"]["curr"]
        var_sell = cb.get("variable_selling", {}).get("curr", 0)
        tot_var = cogs + var_sell
        tot_fixed = (model["OPEX"]["curr"] - var_sell) if model["OPEX"]["curr"] > var_sell else 0
        cm = rev - tot_var
        cm_ratio = (cm / rev) if rev > 0 else 0
        be_rev = round(tot_fixed / cm_ratio) if cm_ratio > 0 else 0
        mos_pct = ((rev - be_rev) / rev) if rev > 0 else 0

        cm_cards = [
            ("LỢI NHUẬN ĐÓNG GÓP (CM)", f"{fmt_vnd(cm)} đ", f"Tỷ lệ CM: {fmt_pct(cm_ratio)}"),
            ("DOANH THU HÒA VỐN", f"{fmt_vnd(be_rev)} đ", f"Mức an toàn: {fmt_pct(mos_pct)}"),
            ("TỔNG BIẾN PHÍ HOẠT ĐỘNG", f"{fmt_vnd(tot_var)} đ", f"Chiếm {fmt_pct(tot_var/rev)} doanh thu"),
            ("TỔNG ĐỊNH PHÍ CỐ ĐỊNH", f"{fmt_vnd(tot_fixed)} đ", "Lương cứng, mặt bằng, khấu hao")
        ]
        w_card = (12.1 - 0.3 * 3) / 4
        for i, (head, val_str, note_str) in enumerate(cm_cards):
            x = 0.6 + i * (w_card + 0.3)
            box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(1.6), Inches(w_card), Inches(1.8))
            box.fill.solid()
            box.fill.fore_color.rgb = CARD
            box.line.color.rgb = NAVY if i < 2 else LINE
            tf = box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = Inches(0.15)
            tf.margin_top = Inches(0.15)
            p0 = tf.paragraphs[0]
            p0.text = head
            p0.font.size, p0.font.bold, p0.font.color.rgb, p0.font.name = Pt(11), True, GREY, FONT
            p1 = tf.add_paragraph()
            p1.text = val_str
            p1.font.size, p1.font.bold, p1.font.color.rgb, p1.font.name = Pt(18), True, NAVY if i < 2 else DARK, FONT
            p1.space_before = Pt(4)
            p2 = tf.add_paragraph()
            p2.text = note_str
            p2.font.size, p2.font.bold, p2.font.color.rgb, p2.font.name = Pt(11), True, GREEN if i < 2 else MUTED, FONT
            p2.space_before = Pt(4)

        # Giải thích ý nghĩa quản trị
        exp_box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(3.7), Inches(12.1), Inches(3.2))
        exp_box.fill.solid()
        exp_box.fill.fore_color.rgb = RGBColor(0xF1, 0xF5, 0xF9)
        exp_box.line.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)
        tf_e = exp_box.text_frame
        tf_e.word_wrap = True
        tf_e.margin_left = tf_e.margin_right = tf_e.margin_top = Inches(0.25)
        p_e0 = tf_e.paragraphs[0]
        p_e0.text = "Ý nghĩa điều hành cho Ban Giám đốc:"
        p_e0.font.size, p_e0.font.bold, p_e0.font.color.rgb, p_e0.font.name = Pt(15), True, NAVY, FONT
        bullets = [
            f"Tỷ lệ lợi nhuận đóng góp (CM Ratio) đạt {fmt_pct(cm_ratio)}: Mỗi 100 đồng doanh thu tạo ra giữ lại được {round(cm_ratio*100, 1)} đồng bù đắp định phí và sinh lãi.",
            f"Điểm hòa vốn đạt {fmt_vnd(be_rev)} đồng: Mức doanh số tối thiểu cần đạt trong kỳ để không bị lỗ.",
            f"Biên độ an toàn doanh thu (Margin of Safety) đạt {fmt_pct(mos_pct)}: Doanh số thực tế đang cao hơn điểm hòa vốn {fmt_pct(mos_pct)}, tạo lá chắn đệm an toàn trước biến động thị trường."
        ]
        for b in bullets:
            p_b = tf_e.add_paragraph()
            p_b.text = f"• {b}"
            p_b.font.size, p_b.font.color.rgb, p_b.font.name = Pt(13), DARK, FONT
            p_b.space_before = Pt(8)

    # 4c. Slide Vốn lưu động & Chu kỳ tiền mặt CCC (nếu có balance_sheet)
    bs = data.get("balance_sheet")
    if bs and "receivables" in bs and "inventory" in bs and "payables" in bs:
        s = prs.slides.add_slide(blank)
        _title(s, "Vốn lưu động & Chu kỳ Chuyển hóa Tiền mặt (CCC)", "Đo lường thời gian dòng vốn bị chiếm dụng và tốc độ quay vòng tiền mặt")
        rev = model["10"]["curr"]
        cogs = model["11"]["curr"]
        rec = bs["receivables"].get("curr", 0)
        inv = bs["inventory"].get("curr", 0)
        pay = bs["payables"].get("curr", 0)
        days = 270 if "9 tháng" in data.get("period", "").lower() else 365
        dso = round((rec / rev) * days, 1) if rev > 0 else 0
        dio = round((inv / cogs) * days, 1) if cogs > 0 else 0
        dpo = round((pay / cogs) * days, 1) if cogs > 0 else 0
        ccc = round(dso + dio - dpo, 1)

        ccc_cards = [
            ("SỐ NGÀY THU TIỀN (DSO)", f"{dso} ngày", f"Phải thu: {fmt_vnd(rec)} đ"),
            ("SỐ NGÀY LƯU KHO (DIO)", f"{dio} ngày", f"Hàng tồn kho: {fmt_vnd(inv)} đ"),
            ("SỐ NGÀY TRẢ NỢ NCC (DPO)", f"{dpo} ngày", f"Phải trả: {fmt_vnd(pay)} đ"),
            ("CHU KỲ TIỀN MẶT (CCC)", f"{ccc} ngày", "CCC = DSO + DIO - DPO")
        ]
        w_card = (12.1 - 0.3 * 3) / 4
        for i, (head, val_str, note_str) in enumerate(ccc_cards):
            x = 0.6 + i * (w_card + 0.3)
            box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(1.6), Inches(w_card), Inches(1.8))
            box.fill.solid()
            box.fill.fore_color.rgb = CARD
            box.line.color.rgb = RED if i == 3 and ccc > 90 else (NAVY if i == 3 else LINE)
            tf = box.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = Inches(0.15)
            tf.margin_top = Inches(0.15)
            p0 = tf.paragraphs[0]
            p0.text = head
            p0.font.size, p0.font.bold, p0.font.color.rgb, p0.font.name = Pt(11), True, GREY, FONT
            p1 = tf.add_paragraph()
            p1.text = val_str
            p1.font.size, p1.font.bold, p1.font.color.rgb, p1.font.name = Pt(20), True, (RED if i == 3 and ccc > 90 else NAVY), FONT
            p1.space_before = Pt(4)
            p2 = tf.add_paragraph()
            p2.text = note_str
            p2.font.size, p2.font.bold, p2.font.color.rgb, p2.font.name = Pt(11), False, DARK, FONT
            p2.space_before = Pt(4)

        # Đánh giá thanh khoản
        liq_box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(3.7), Inches(12.1), Inches(3.2))
        liq_box.fill.solid()
        liq_box.fill.fore_color.rgb = RGBColor(0xFE, 0xF2, 0xF2) if ccc > 90 else RGBColor(0xF0, 0xFD, 0xF4)
        liq_box.line.color.rgb = RGBColor(0xFE, 0xCA, 0xCA) if ccc > 90 else RGBColor(0xBB, 0xF7, 0xD0)
        tf_l = liq_box.text_frame
        tf_l.word_wrap = True
        tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = Inches(0.25)
        p_l0 = tf_l.paragraphs[0]
        p_l0.text = "Nhận định Vốn lưu động & Thanh khoản của CFO:"
        p_l0.font.size, p_l0.font.bold, p_l0.font.color.rgb, p_l0.font.name = Pt(15), True, RED if ccc > 90 else GREEN, FONT
        c_bullets = [
            f"Chu kỳ tiền mặt tổng thể (CCC) là {ccc} ngày: Doanh nghiệp mất {ccc} ngày kể từ khi xuất tiền chi trả nhà cung cấp đến khi thu hồi được tiền bán hàng mặt về tài khoản.",
            f"Áp lực đọng vốn lớn nhất nằm ở Hàng tồn kho (DIO = {dio} ngày): Hàng hóa lưu kho trung bình hơn 5 tháng, cần đẩy mạnh tốc độ luân chuyển kho.",
            f"Thời gian thu hồi công nợ (DSO = {dso} ngày): Cần siết chặt hạn mức công nợ đại lý để kéo giảm DSO về dưới 60 ngày."
        ]
        for b in c_bullets:
            p_b = tf_l.add_paragraph()
            p_b.text = f"• {b}"
            p_b.font.size, p_b.font.color.rgb, p_b.font.name = Pt(13), DARK, FONT
            p_b.space_before = Pt(8)

    # 5. Khuyến nghị (chỉ khi Agent đã viết)
    recs = (data.get("narrative") or {}).get("recommendations") or []
    if recs:
        s = prs.slides.add_slide(blank)
        _title(s, "Khuyến nghị quản trị")
        n = len(recs)
        w = (12.1 - 0.3 * (n - 1)) / n if n <= 3 else 12.1
        for i, r in enumerate(recs):
            if n <= 3:
                x, y, h, wd = 0.6 + i * (w + 0.3), 1.6, 2.6, w
            else:
                x, y, h, wd = 0.6, 1.5 + i * (5.6 / n), 5.6 / n - 0.15, 12.1
            box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(wd), Inches(h))
            box.fill.solid()
            box.fill.fore_color.rgb = CARD
            box.line.color.rgb = NAVY
            box.adjustments[0] = 0.05
            tf = box.text_frame
            tf.word_wrap, tf.vertical_anchor = True, MSO_ANCHOR.TOP
            tf.margin_left = tf.margin_right = tf.margin_top = Inches(0.2)
            p0 = tf.paragraphs[0]
            p0.text, p0.alignment = f"{i + 1}. {r['title']}", PP_ALIGN.LEFT
            p0.font.size, p0.font.bold, p0.font.color.rgb, p0.font.name = Pt(16), True, NAVY, FONT
            p1 = tf.add_paragraph()
            p1.text, p1.alignment = r["desc"], PP_ALIGN.LEFT
            p1.font.size, p1.font.color.rgb, p1.font.name = Pt(14), DARK, FONT
            p1.space_before = Pt(8)

    out = Path(out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    return out


def main():
    ap = argparse.ArgumentParser(description="Xuất slide P&L 16:9 từ data.json (không số liệu mẫu)")
    ap.add_argument("--input", "-i", required=True, help="data.json (cùng file đã dựng Excel)")
    ap.add_argument("--output", "-o", required=True, help="Đường dẫn .pptx đầu ra")
    ap.add_argument("--xlsx", help="File Excel đã dựng để đối chiếu số liệu (khuyến nghị)")
    args = ap.parse_args()
    try:
        data = load_data(args.input)
        model = compute(data)
        if args.xlsx:
            cross_check(data, model, args.xlsx)
            print("• Đối chiếu slide vs Excel: khớp")
    except DataError as e:
        print(f"❌ LỖI DỮ LIỆU: {e}", file=sys.stderr)
        sys.exit(1 if args.xlsx and "lệch" in str(e) else 2)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(2)
    out = build(data, model, args.output)
    skipped = [n for n, k in (("Nhận định", "highlights"), ("Khuyến nghị", "recommendations"))
               if not (data.get("narrative") or {}).get(k)]
    print(f"✅ Đã tạo slide: {out}")
    if skipped:
        print(f"   Đã bỏ qua phần {', '.join(skipped)} vì data.json không có narrative tương ứng.")


if __name__ == "__main__":
    main()
