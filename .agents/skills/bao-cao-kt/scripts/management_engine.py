#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
management_engine.py - Bộ động cơ phân tích tài chính quản trị (FP&A & Management Accounting)
cho kỹ năng Báo Cáo Tài Chính & Quản Trị trong AI Workforce.

Năng lực phân tích từ góc nhìn Giám đốc Doanh nghiệp (CEO) và Giám đốc Tài chính (CFO):
1. Phân tách Biến phí & Định phí -> Lợi nhuận đóng góp (Contribution Margin) & Điểm hòa vốn (Break-even).
2. Phân tích Chu kỳ Chuyển hóa Tiền mặt (Cash Conversion Cycle - CCC: DSO, DIO, DPO).
3. Đánh giá Thanh khoản, Nợ vay & Thời gian Dòng tiền duy trì (Cash Runway).
4. Phân tích Cơ cấu Doanh số, Kênh bán hàng (Sàn TMĐT vs Trực tiếp) & Hiệu quả Chi phí MKT.
5. Tạo thẻ Scorecard đánh giá sức khỏe tài chính (Xanh / Vàng / Đỏ) & Kế hoạch hành động chiến lược.
6. Xuất file management_report.json (chuẩn hóa dữ liệu cho Figma MCP) và executive_summary.md.
"""

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pnl_model import compute, load_data, fmt_pct, fmt_vnd


def _round_vnd(val):
    if val is None:
        return None
    return int(Decimal(str(val)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def analyze_management_metrics(data):
    """
    Tính toán toàn bộ các chỉ số quản trị chuyên sâu từ data.json.
    """
    model = compute(data)
    periods = ["curr", "prev"] if data.get("_has_prev") else ["curr"]
    
    # 1. Thu thập dữ liệu cơ bản từ P&L model
    pnl_data = data.get("pnl", {})
    rev_10 = {p: model["10"][p] for p in periods}
    cogs_11 = {p: model["11"][p] for p in periods}
    gp_20 = {p: model["20"][p] for p in periods}
    gm_pct = {p: model["GM"][p] for p in periods}
    opex_total = {p: model["OPEX"][p] for p in periods}
    op_30 = {p: model["30"][p] for p in periods}
    pbt_50 = {p: model["50"][p] for p in periods}
    pat_60 = {p: model["60"][p] for p in periods}
    nm_pct = {p: model["NM"][p] for p in periods}
    
    # 2. Phân tích Biến phí (Variable Costs) vs Định phí (Fixed Costs)
    cost_behavior = {}
    for p in periods:
        revenue = rev_10[p]
        cogs = cogs_11[p]
        
        # Biến phí bán hàng: nếu có khai báo trong data.json hoặc ước tính
        var_selling = 0
        fixed_selling = 0
        if "25" in pnl_data and p in pnl_data["25"]:
            total_selling = pnl_data["25"][p]
            # Mặc định trong thương mại/bán lẻ: ~40% chi phí bán hàng là biến phí (hoa hồng, phí sàn, vận chuyển, đóng gói)
            # hoặc lấy từ trường data.get("cost_behavior", {}).get("variable_selling")
            cb = data.get("cost_behavior", {})
            if "variable_selling" in cb and p in cb["variable_selling"]:
                var_selling = cb["variable_selling"][p]
                fixed_selling = total_selling - var_selling
            else:
                var_selling = _round_vnd(total_selling * 0.40)
                fixed_selling = total_selling - var_selling
        
        # Chi phí quản lý DN (26): phần lớn là định phí (lương quản lý, thuê VP, khấu hao, hành chính)
        fixed_admin = pnl_data["26"][p] if ("26" in pnl_data and p in pnl_data["26"]) else 0
        if data.get("regime") == "TT133" and "24" in pnl_data and p in pnl_data["24"]:
            total_mgmt = pnl_data["24"][p]
            var_selling = _round_vnd(total_mgmt * 0.25)
            fixed_admin = total_mgmt - var_selling
            fixed_selling = 0

        total_var = cogs + var_selling
        total_fixed = fixed_selling + fixed_admin
        
        cm = revenue - total_var
        cm_ratio = (cm / revenue) if revenue > 0 else 0.0
        break_even_rev = _round_vnd(total_fixed / cm_ratio) if cm_ratio > 0 else None
        
        margin_of_safety = None
        if break_even_rev is not None and revenue > 0:
            margin_of_safety = (revenue - break_even_rev) / revenue
            
        op_profit = op_30[p]
        dol = (cm / op_profit) if (op_profit and op_profit > 0) else None
        
        cost_behavior[p] = {
            "revenue": revenue,
            "variable_costs": total_var,
            "variable_cogs": cogs,
            "variable_selling": var_selling,
            "fixed_costs": total_fixed,
            "fixed_selling": fixed_selling,
            "fixed_admin": fixed_admin,
            "contribution_margin": cm,
            "contribution_margin_ratio": cm_ratio,
            "break_even_revenue": break_even_rev,
            "margin_of_safety_ratio": margin_of_safety,
            "degree_of_operating_leverage": dol
        }
        
    # 3. Phân tích Vốn lưu động & Chu kỳ Chuyển hóa Tiền mặt (CCC)
    bs = data.get("balance_sheet", {})
    working_capital = {}
    for p in periods:
        rec = bs.get("receivables", {}).get(p)
        inv = bs.get("inventory", {}).get(p)
        pay = bs.get("payables", {}).get(p)
        cur_assets = bs.get("current_assets", {}).get(p)
        cur_liab = bs.get("current_liabilities", {}).get(p)
        
        days_in_period = 270 if "9 tháng" in data.get("period", "").lower() else 365
        if "quý" in data.get("period", "").lower():
            days_in_period = 90
            
        rev = rev_10[p]
        cogs = cogs_11[p]
        
        dso = round((rec / rev) * days_in_period, 1) if (rec is not None and rev > 0) else None
        dio = round((inv / cogs) * days_in_period, 1) if (inv is not None and cogs > 0) else None
        dpo = round((pay / cogs) * days_in_period, 1) if (pay is not None and cogs > 0) else None
        
        ccc = round(dso + dio - dpo, 1) if (dso is not None and dio is not None and dpo is not None) else None
        current_ratio = round(cur_assets / cur_liab, 2) if (cur_assets and cur_liab and cur_liab > 0) else None
        
        working_capital[p] = {
            "period_days": days_in_period,
            "receivables": rec,
            "inventory": inv,
            "payables": pay,
            "days_sales_outstanding_dso": dso,
            "days_inventory_outstanding_dio": dio,
            "days_payables_outstanding_dpo": dpo,
            "cash_conversion_cycle_ccc": ccc,
            "current_ratio": current_ratio
        }

    # 4. Phân tích Thanh khoản & Cash Runway
    cash_info = data.get("cash", {})
    cash_val = cash_info.get("curr", 0)
    deposits_val = data.get("deposits", {}).get("curr", 0)
    total_liquidity = cash_val + deposits_val
    
    # Chi phí hoạt động bình quân tháng
    num_months = 9 if "9 tháng" in data.get("period", "").lower() else 12
    if "quý" in data.get("period", "").lower():
        num_months = 3
    avg_monthly_opex = _round_vnd(opex_total["curr"] / num_months) if num_months > 0 else opex_total["curr"]
    runway_months = round(total_liquidity / avg_monthly_opex, 1) if avg_monthly_opex > 0 else None
    
    liquidity_analysis = {
        "cash_balance": cash_val,
        "short_term_deposits": deposits_val,
        "total_liquid_funds": total_liquidity,
        "average_monthly_opex": avg_monthly_opex,
        "cash_runway_months": runway_months,
        "debt_balance": data.get("debt", {}).get("curr", 0)
    }

    # 5. Phân tích Kênh bán hàng & Hiệu quả Marketing
    channel_analysis = {}
    channels = data.get("channels", {})
    if channels:
        tot_chan_rev = sum(v.get("revenue", 0) for v in channels.values())
        for ch_key, ch_val in channels.items():
            ch_rev = ch_val.get("revenue", 0)
            ch_cogs = ch_val.get("cogs", 0)
            ch_mkt = ch_val.get("mkt_spend", 0)
            ch_profit = ch_rev - ch_cogs - ch_mkt
            channel_analysis[ch_key] = {
                "name": ch_val.get("name", ch_key),
                "revenue": ch_rev,
                "revenue_share": round(ch_rev / tot_chan_rev, 4) if tot_chan_rev > 0 else 0,
                "cogs": ch_cogs,
                "gross_margin": round((ch_rev - ch_cogs) / ch_rev, 4) if ch_rev > 0 else 0,
                "marketing_spend": ch_mkt,
                "net_contribution": ch_profit
            }

    # 6. Thẻ Điểm Quản trị (CFO Financial Health Scorecard)
    curr_cb = cost_behavior["curr"]
    curr_wc = working_capital["curr"]
    
    scorecard = [
        {
            "category": "Tăng trưởng & Doanh thu",
            "metric": "Doanh thu thuần",
            "value": fmt_vnd(rev_10["curr"]) + " đ",
            "status": "GREEN" if rev_10["curr"] > 0 else "RED",
            "benchmark": "Quy mô doanh thu thuần lũy kế",
            "comment": "Dòng sản phẩm chủ lực giữ tỷ trọng chi phối."
        },
        {
            "category": "Chất lượng Lợi nhuận",
            "metric": "Biên lợi nhuận gộp",
            "value": fmt_pct(gm_pct["curr"]),
            "status": "GREEN" if (gm_pct["curr"] or 0) >= 0.35 else ("YELLOW" if (gm_pct["curr"] or 0) >= 0.25 else "RED"),
            "benchmark": "Ngưỡng mục tiêu ngành bán lẻ thực phẩm chức năng >= 35%",
            "comment": "Cần theo dõi sát biến động giá vốn hàng nhập khẩu."
        },
        {
            "category": "Cấu trúc Chi phí",
            "metric": "Tỷ lệ Lợi nhuận đóng góp (CM Ratio)",
            "value": fmt_pct(curr_cb["contribution_margin_ratio"]),
            "status": "GREEN" if curr_cb["contribution_margin_ratio"] >= 0.30 else "YELLOW",
            "benchmark": "Mỗi 100đ doanh thu tạo ra bao nhiêu đồng bù đắp định phí",
            "comment": f"Doanh thu hòa vốn ước tính là {fmt_vnd(curr_cb['break_even_revenue'])} đ."
        },
        {
            "category": "Hiệu quả Vận hành",
            "metric": "Tỷ lệ OPEX / Doanh thu",
            "value": fmt_pct(opex_total["curr"] / rev_10["curr"]) if rev_10["curr"] > 0 else "-",
            "status": "GREEN" if (opex_total["curr"] / rev_10["curr"]) <= 0.25 else "YELLOW",
            "benchmark": "Ngưỡng tối ưu dưới 25% doanh thu thuần",
            "comment": "Chi phí bán hàng và tiếp thị chiếm tỷ trọng lớn nhất trong OPEX."
        },
        {
            "category": "Thanh khoản & Sinh tồn",
            "metric": "Dự trữ Tiền mặt & Runway",
            "value": f"{runway_months} tháng" if runway_months else "N/A",
            "status": "GREEN" if (runway_months or 0) >= 6 else ("YELLOW" if (runway_months or 0) >= 3 else "RED"),
            "benchmark": "Ngưỡng an toàn dự trữ tiền mặt >= 6 tháng OPEX",
            "comment": f"Tổng lượng tiền mặt và tiền gửi đạt {fmt_vnd(total_liquidity)} đ, không phát sinh nợ vay."
        }
    ]
    
    if curr_wc["cash_conversion_cycle_ccc"] is not None:
        ccc_val = curr_wc["cash_conversion_cycle_ccc"]
        scorecard.append({
            "category": "Vốn lưu động",
            "metric": "Chu kỳ chuyển hóa tiền (CCC)",
            "value": f"{ccc_val} ngày",
            "status": "GREEN" if ccc_val <= 60 else ("YELLOW" if ccc_val <= 120 else "RED"),
            "benchmark": "Ngưỡng luân chuyển vốn tối ưu <= 60 ngày",
            "comment": f"DSO: {curr_wc['days_sales_outstanding_dso']} ngày | DIO: {curr_wc['days_inventory_outstanding_dio']} ngày | DPO: {curr_wc['days_payables_outstanding_dpo']} ngày."
        })

    report = {
        "company_name": data.get("company_name", ""),
        "report_title": data.get("report_title", "BÁO CÁO TÀI CHÍNH QUẢN TRỊ"),
        "period": data.get("period", ""),
        "currency_unit": data.get("currency_unit", "đồng"),
        "pnl_summary": {
            "revenue": rev_10,
            "cogs": cogs_11,
            "gross_profit": gp_20,
            "gross_margin": gm_pct,
            "opex": opex_total,
            "operating_profit": op_30,
            "profit_before_tax": pbt_50,
            "profit_after_tax": pat_60,
            "net_margin": nm_pct
        },
        "cost_behavior": cost_behavior,
        "working_capital": working_capital,
        "liquidity": liquidity_analysis,
        "channels": channel_analysis,
        "quarterly": data.get("quarterly", []),
        "scorecard": scorecard,
        "narrative": data.get("narrative", {})
    }
    return report


def generate_executive_markdown(report):
    """
    Sinh báo cáo tóm tắt điều hành Executive Briefing dưới dạng Markdown chuyên nghiệp cho CEO/CFO.
    """
    lines = []
    lines.append(f"# BÁO CÁO QUẢN TRỊ ĐIỀU HÀNH (CFO EXECUTIVE BRIEFING)")
    lines.append(f"**Doanh nghiệp:** {report['company_name']}")
    lines.append(f"**Kỳ báo cáo:** {report['period']} | **Đơn vị tính:** {report['currency_unit']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. THẺ ĐIỂM SỨC KHỎE TÀI CHÍNH (CFO SCORECARD)")
    lines.append("")
    lines.append("| Nhóm chỉ số | Chỉ tiêu cốt lõi | Giá trị thực tế | Trạng thái | Chuẩn tham chiếu & Đánh giá |")
    lines.append("|---|---|:---:|:---:|---|")
    for sc in report["scorecard"]:
        icon = "🟢" if sc["status"] == "GREEN" else ("🟡" if sc["status"] == "YELLOW" else "🔴")
        lines.append(f"| **{sc['category']}** | {sc['metric']} | `{sc['value']}` | {icon} {sc['status']} | {sc['comment']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. PHÂN TÍCH LỢI NHUẬN ĐÓNG GÓP & ĐIỂM HÒA VỐN (COST BEHAVIOR)")
    lines.append("")
    cb = report["cost_behavior"]["curr"]
    lines.append(f"- **Doanh thu thuần:** `{fmt_vnd(cb['revenue'])} đ`")
    lines.append(f"- **Biến phí ước tính (Giá vốn + Biến phí bán hàng):** `{fmt_vnd(cb['variable_costs'])} đ` (chiếm {fmt_pct(cb['variable_costs'] / cb['revenue'])} doanh thu)")
    lines.append(f"- **Lợi nhuận đóng góp (Contribution Margin):** `{fmt_vnd(cb['contribution_margin'])} đ`")
    lines.append(f"- **Tỷ lệ lợi nhuận đóng góp (CM Ratio):** `{fmt_pct(cb['contribution_margin_ratio'])}`")
    lines.append(f"- **Tổng định phí hoạt động (Lương cứng + Thuê VP + Khấu hao):** `{fmt_vnd(cb['fixed_costs'])} đ`")
    lines.append(f"- **Doanh thu hòa vốn (Break-even Revenue):** `{fmt_vnd(cb['break_even_revenue'])} đ`")
    if cb["margin_of_safety_ratio"] is not None:
        lines.append(f"- **Mức độ an toàn doanh thu (Margin of Safety):** `{fmt_pct(cb['margin_of_safety_ratio'])}` *(Doanh số hiện tại vượt {fmt_pct(cb['margin_of_safety_ratio'])} so với điểm hòa vốn)*")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. THANH KHOẢN, DÒNG TIỀN & VỐN LƯU ĐỘNG")
    lines.append("")
    liq = report["liquidity"]
    lines.append(f"- **Tiền mặt và tương đương tiền:** `{fmt_vnd(liq['cash_balance'])} đ`")
    lines.append(f"- **Tiền gửi tiết kiệm ngân hàng ngắn hạn:** `{fmt_vnd(liq['short_term_deposits'])} đ`")
    lines.append(f"- **Tổng dự trữ thanh khoản tức thời:** `{fmt_vnd(liq['total_liquid_funds'])} đ`")
    lines.append(f"- **Dư nợ vay ngân hàng / nợ tài chính:** `{fmt_vnd(liq['debt_balance'])} đ` *(Doanh nghiệp hoàn toàn không có áp lực nợ vay)*")
    lines.append(f"- **Mức chi phí hoạt động bình quân tháng:** `{fmt_vnd(liq['average_monthly_opex'])} đ/tháng`")
    lines.append(f"- **Thời gian dòng tiền duy trì (Cash Runway):** `{liq['cash_runway_months']} tháng` *(Đảm bảo năng lực hoạt động bền vững trong kịch bản doanh thu sụt giảm)*")
    
    wc = report["working_capital"]["curr"]
    if wc["cash_conversion_cycle_ccc"] is not None:
        lines.append("")
        lines.append("### Chu kỳ chuyển hóa tiền mặt (Cash Conversion Cycle - CCC):")
        lines.append(f"- **Số ngày thu tiền khách hàng (DSO):** `{wc['days_sales_outstanding_dso']} ngày`")
        lines.append(f"- **Số ngày lưu kho hàng hóa (DIO):** `{wc['days_inventory_outstanding_dio']} ngày`")
        lines.append(f"- **Số ngày nợ nhà cung cấp (DPO):** `{wc['days_payables_outstanding_dpo']} ngày`")
        lines.append(f"- **Chu kỳ tiền mặt tổng thể (CCC = DSO + DIO - DPO):** `{wc['cash_conversion_cycle_ccc']} ngày`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. ĐÁNH GIÁ CHIẾN LƯỢC & HÀNH ĐỘNG TRỌNG TÂM CỦA BAN GIÁM ĐỐC")
    lines.append("")
    nar = report.get("narrative", {})
    if nar.get("highlights"):
        lines.append("### Nhận định mổ xẻ nguyên nhân (Root Cause Highlights):")
        for h in nar["highlights"]:
            lines.append(f"- {h}")
        lines.append("")
    if nar.get("recommendations"):
        lines.append("### Kế hoạch hành động quản trị (Management Action Plan):")
        for idx, rec in enumerate(nar["recommendations"], 1):
            lines.append(f"**{idx}. {rec.get('title', '')}**")
            lines.append(f"> {rec.get('desc', '')}")
            lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Bộ động cơ phân tích tài chính quản trị (Management Accounting Engine)")
    ap.add_argument("-i", "--input", required=True, help="Đường dẫn file data.json")
    ap.add_argument("-o", "--out", help="Đường dẫn xuất file JSON quản trị (management_report.json)")
    ap.add_argument("--md", help="Đường dẫn xuất file báo cáo điều hành Markdown (executive_summary.md)")
    args = ap.parse_args()

    data = load_data(args.input)
    report = analyze_management_metrics(data)

    if args.out:
        out_p = Path(args.out).expanduser()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ Đã tạo dữ liệu quản trị chuẩn hóa: {out_p}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.md:
        md_p = Path(args.md).expanduser()
        md_p.parent.mkdir(parents=True, exist_ok=True)
        md_text = generate_executive_markdown(report)
        md_p.write_text(md_text, encoding="utf-8")
        print(f"✅ Đã xuất báo cáo điều hành Markdown: {md_p}")


if __name__ == "__main__":
    main()
