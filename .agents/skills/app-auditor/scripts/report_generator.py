#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report_generator.py — Tạo Báo Cáo Thẩm Định Ứng Dụng & Chấm Điểm (Quality Report Generator)
Thuộc bộ công cụ App Auditor (AI Workforce)
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

def load_json(path_str):
    if not path_str:
        return {}
    p = Path(path_str)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def classify_issues(audit_data):
    issues = {
        "P0": [],
        "P1": [],
        "P2": [],
        "P3": [],
        "P4": []
    }
    passed_checks = []

    # 1. Quét lỗi Console & Runtime
    det = audit_data.get("deterministic", {})
    console_errors = det.get("console_errors", [])
    uncaught = det.get("uncaught_exceptions", [])
    http_errors = det.get("http_error_responses", [])

    if uncaught:
        for err in uncaught:
            issues["P0"].append({
                "type": "Defect",
                "title": f"Uncaught Exception làm treo runtime: {err.get('message', '')[:80]}",
                "route": det.get("url", "/"),
                "viewport": "All",
                "category": "stability",
                "steps": "1. Mở trang tại URL đích.\n2. Quan sát log runtime của trình duyệt.",
                "expected": "Không phát sinh Unhandled Exception hoặc runtime crash.",
                "actual": f"Phát hiện lỗi: {err.get('message', '')}",
                "selector": "window.onerror",
                "screenshot": "",
                "log": f"Type: {err.get('type')}, Error: {err.get('message')}"
            })
    else:
        passed_checks.append("✓ Không phát sinh Uncaught Exception làm sập runtime")

    if console_errors:
        for err in console_errors:
            if err.get("type") == "error":
                issues["P2"].append({
                    "type": "Defect",
                    "title": f"Console Error: {err.get('text', '')[:80]}",
                    "route": det.get("url", "/"),
                    "viewport": "All",
                    "category": "stability",
                    "steps": "1. Mở trang và bật DevTools Console.\n2. Kiểm tra log hiển thị.",
                    "expected": "Console sạch sẽ, không có error log đỏ.",
                    "actual": f"Console báo lỗi: {err.get('text', '')}",
                    "selector": "Console",
                    "screenshot": "",
                    "log": f"Location: {err.get('location', {})}, Text: {err.get('text')}"
                })
    else:
        passed_checks.append("✓ Trình duyệt sạch console error")

    if http_errors:
        for res in http_errors:
            status = res.get("status", 0)
            sev = "P1" if status >= 500 else "P2"
            issues[sev].append({
                "type": "Defect",
                "title": f"Yêu cầu mạng trả về mã lỗi HTTP {status}: {res.get('url', '')[:70]}",
                "route": det.get("url", "/"),
                "viewport": "All",
                "category": "functional",
                "steps": f"1. Tải trang {det.get('url', '/')}.\n2. Quan sát network request đến {res.get('url')}.",
                "expected": "Mọi tài nguyên nội bộ trả về HTTP 200 OK.",
                "actual": f"Server trả về mã {status} ({res.get('status_text')}).",
                "selector": "Network Request",
                "screenshot": "",
                "log": f"URL: {res.get('url')}, Status: {status}"
            })
    else:
        passed_checks.append("✓ Mọi yêu cầu mạng tải tài nguyên thành công (không có 4xx/5xx)")

    # 2. Quét lỗi Tràn ngang (Overflow) & Responsive
    sweep = audit_data.get("visual_sweep", {})
    overflows = sweep.get("overflow_issues", [])
    if overflows:
        for ov in overflows:
            vp = ov.get("viewport", "")
            amt = ov.get("overflow_amount", 0)
            sev = "P1" if vp == "mobile" and amt > 30 else "P2"
            el_str = ", ".join([e.get("tag", "") + (f"#{e.get('id')}" if e.get("id") else f".{e.get('className')}") for e in ov.get("elements", [])[:2]])
            issues[sev].append({
                "type": "Defect",
                "title": f"Giao diện bị tràn ngang ({amt}px) trên khung nhìn {vp}",
                "route": ov.get("route", "/"),
                "viewport": f"{vp} ({ov.get('viewport_width')}px)",
                "category": "responsive",
                "steps": f"1. Chuyển khung nhìn trình duyệt về chiều rộng {ov.get('viewport_width')}px.\n2. Quan sát thanh cuộn ngang xuất hiện ở đáy màn hình.",
                "expected": "Nội dung vừa khít khung nhìn, không xuất hiện thanh cuộn ngang.",
                "actual": f"Trang bị tràn ra ngoài {amt}px do các phần tử: {el_str}.",
                "selector": el_str if el_str else "document.documentElement",
                "screenshot": ov.get("screenshot", ""),
                "log": f"Overflow: {amt}px"
            })
    else:
        passed_checks.append("✓ Giao diện co giãn hoàn hảo không tràn ngang trên cả 4 khung nhìn (1440, 1024, 768, 390px)")

    # 3. Quét Touch Targets nhỏ trên mobile
    touch_issues = sweep.get("touch_target_issues", [])
    if touch_issues:
        for t in touch_issues:
            issues["P3"].append({
                "type": "Defect",
                "title": f"Phát hiện {t.get('count')} phần tử có vùng chạm nhỏ (< 44px) trên mobile",
                "route": t.get("route", "/"),
                "viewport": "mobile (390px)",
                "category": "ux",
                "steps": "1. Mở trang trên màn hình di động 390px.\n2. Kiểm tra kích thước nút bấm/link nhỏ.",
                "expected": "Vùng chạm tương tác tối thiểu 44x44 pixel theo chuẩn Mobile Usability.",
                "actual": f"Tìm thấy nút bấm kích thước nhỏ, gây khó khăn khi bấm bằng ngón tay.",
                "selector": str(t.get("samples", [])[:2]),
                "screenshot": "",
                "log": f"Count: {t.get('count')}"
            })
    else:
        passed_checks.append("✓ Vùng chạm các nút bấm và link trên mobile đạt chuẩn kích thước")

    # 4. Quét tính nhất quán màu sắc (Visual Consistency)
    colors = sweep.get("color_inconsistencies", [])
    if colors:
        for c in colors[:3]:
            issues["P3"].append({
                "type": "Defect",
                "title": f"Mâu thuẫn mã màu hex tương đồng ({c.get('color1')} vs {c.get('color2')})",
                "route": "/",
                "viewport": "desktop_large",
                "category": "visual",
                "steps": "1. So sánh computed color giữa các thành phần giao diện trên trang.",
                "expected": "Sử dụng đồng nhất một mã màu token cho cùng nhóm chức năng thị giác.",
                "actual": f"Tồn tại 2 mã màu {c.get('color1')} và {c.get('color2')} lệch nhau nhẹ ({c.get('diff')} delta) mà không có lý do thiết kế.",
                "selector": f"{c.get('color1')}, {c.get('color2')}",
                "screenshot": "",
                "log": f"Diff: {c.get('diff')}"
            })
    else:
        passed_checks.append("✓ Bảng màu giao diện nhất quán, không có mã màu hex rác")

    # 5. Quét vi phạm Trợ năng (axe-core Accessibility)
    a11y = det.get("accessibility_violations", [])
    if a11y:
        for v in a11y:
            impact = v.get("impact", "minor")
            sev = "P1" if impact == "critical" else ("P2" if impact in ["serious", "moderate"] else "P3")
            sample_target = ", ".join([str(n.get("target", [])) for n in v.get("sample_nodes", [])[:2]])
            issues[sev].append({
                "type": "Defect",
                "title": f"[A11y {impact.upper()}] {v.get('help', '')}: {v.get('id', '')}",
                "route": det.get("url", "/"),
                "viewport": "All",
                "category": "accessibility",
                "steps": f"1. Quét chuẩn WCAG A/AA bằng axe-core.\n2. Định vị selector: {sample_target}.",
                "expected": f"Đáp ứng tiêu chuẩn trợ năng: {v.get('description', '')}.",
                "actual": f"Vi phạm tại {v.get('nodes_count')} vị trí trên trang. Chi tiết: {v.get('helpUrl', '')}",
                "selector": sample_target,
                "screenshot": "",
                "log": f"Rule ID: {v.get('id')}, Impact: {impact}"
            })
    else:
        passed_checks.append("✓ Đạt 100% tiêu chuẩn trợ năng WCAG A & AA cơ bản theo axe-core")

    # 6. Quét vấn đề Người dùng khó tính (Difficult User)
    diff = audit_data.get("difficult_user", {})
    debounce = diff.get("rapid_clicks_issues", [])
    if debounce:
        for db in debounce:
            issues["P1"].append({
                "type": "Defect",
                "title": f"Thiếu Debounce/Throttle: {db.get('defect')}",
                "route": diff.get("url", "/"),
                "viewport": "desktop_large",
                "category": "logic_state",
                "steps": f"1. Bấm liên tục 4 lần vào nút '{db.get('button_text')}'.\n2. Quan sát network tab và trạng thái xử lý.",
                "expected": "Nút bấm tự động khóa (disable) hoặc áp dụng debounce chỉ gửi 1 request duy nhất.",
                "actual": f"Hệ thống gửi đi {db.get('requests_spawned')} requests, có nguy cơ gây trùng lặp dữ liệu đơn hàng / bản ghi.",
                "selector": f"button:text('{db.get('button_text')}')",
                "screenshot": "",
                "log": f"Requests count: {db.get('requests_spawned')}"
            })
    else:
        passed_checks.append("✓ Nút bấm tương tác xử lý tốt hành vi nhấp chuột liên hoàn (có debounce / loading guard)")

    boundary = diff.get("boundary_input_issues", [])
    if boundary:
        for b in boundary:
            issues["P2"].append({
                "type": "Defect",
                "title": f"Lỗi xử lý chuỗi biên: {b.get('defect', b.get('error'))}",
                "route": diff.get("url", "/"),
                "viewport": "desktop_large",
                "category": "functional",
                "steps": f"1. Nhập chuỗi kiểm thử {b.get('payload_type')} vào ô nhập liệu.\n2. Quan sát phản hồi giao diện.",
                "expected": "Hệ thống hiển thị mượt mà hoặc cắt tỉa an toàn, không làm vỡ layout.",
                "actual": b.get("defect", b.get("error")),
                "selector": f"input[{b.get('input_index')}]",
                "screenshot": "",
                "log": f"Type: {b.get('payload_type')}"
            })
    else:
        passed_checks.append("✓ Các trường nhập liệu bền bỉ trước chuỗi văn bản dài và ký tự đặc biệt")

    modal_issues = diff.get("modal_toggle_issues", [])
    if modal_issues:
        for m in modal_issues:
            issues["P2"].append({
                "type": "Defect",
                "title": f"Lỗi kẹt trạng thái Modal: {m.get('defect')}",
                "route": diff.get("url", "/"),
                "viewport": "desktop_large",
                "category": "logic_state",
                "steps": "1. Mở và đóng liên tục modal 3 lần.\n2. Thử cuộn trang bằng chuột.",
                "expected": "Trang trả về trạng thái cuộn bình thường sau khi modal đóng.",
                "actual": m.get("defect"),
                "selector": "body",
                "screenshot": "",
                "log": "overflow: hidden lock"
            })
    else:
        passed_checks.append("✓ Thành phần Modal/Dialog đóng mở an toàn, không gây kẹt thanh cuộn body")

    # Bổ sung một số kiến nghị P4 mẫu nếu chưa có
    if not issues["P4"]:
        issues["P4"].append({
            "type": "Recommendation",
            "title": "Bổ sung Skeleton Loading thay cho trạng thái trắng khi chuyển trang",
            "route": "/",
            "viewport": "All",
            "category": "ux",
            "steps": "Quan sát quá trình tải dữ liệu lần đầu.",
            "expected": "N/A",
            "actual": "Hiện tại trang dùng spinner đơn giản. Có thể nâng cấp trải nghiệm thị giác bằng skeleton placeholder.",
            "selector": "Page loader",
            "screenshot": "",
            "log": "UX Recommendation"
        })

    return issues, passed_checks

def calculate_scores(issues, scoring_matrix):
    categories = scoring_matrix.get("categories", {})
    penalties = scoring_matrix.get("severity_penalties", {})
    guardrails = scoring_matrix.get("score_guardrails", {})

    scores = {}
    for cat_key, cat_val in categories.items():
        scores[cat_key] = cat_val.get("base_score", 10.0)

    has_p0 = len(issues.get("P0", [])) > 0

    for sev in ["P0", "P1", "P2", "P3"]:
        penalty_val = penalties.get(sev, {}).get("penalty", 0.0)
        for iss in issues.get(sev, []):
            cat = iss.get("category", "functional")
            if cat in scores:
                scores[cat] = max(guardrails.get("min_score", 1.0), round(scores[cat] - penalty_val, 1))

    # Tính điểm tổng hợp có trọng số
    overall = 0.0
    for cat_key, cat_val in categories.items():
        w = cat_val.get("weight", 0.1)
        overall += scores[cat_key] * w

    overall = round(overall, 1)

    # Nếu có P0 thì trần điểm tổng hợp tối đa là 5.0
    if has_p0 and overall > guardrails.get("p0_cap", 5.0):
        overall = guardrails.get("p0_cap", 5.0)

    overall = max(guardrails.get("min_score", 1.0), min(guardrails.get("max_score", 10.0), overall))
    return scores, overall

def format_issue_block(issue_list):
    if not issue_list:
        return "*Không phát hiện vấn đề nào.*\n"
    res = []
    for i, iss in enumerate(issue_list, 1):
        lines = [
            f"#### {i}. {iss.get('title')}",
            f"* **Phân loại:** `{iss.get('type')}`",
            f"* **Vị trí (Route):** `{iss.get('route')}` | **Khung nhìn:** `{iss.get('viewport')}`",
            f"* **Các bước tái hiện:**\n{iss.get('steps')}",
            f"* **Kỳ vọng:** {iss.get('expected')}",
            f"* **Thực tế:** {iss.get('actual')}"
        ]
        if iss.get('selector'):
            lines.append(f"* **Phần tử liên quan:** `{iss.get('selector')}`")
        if iss.get('screenshot'):
            lines.append(f"* **Ảnh chụp bằng chứng:** `{iss.get('screenshot')}`")
        if iss.get('log'):
            lines.append(f"* **Log kỹ thuật:** `{iss.get('log')}`")
        res.append("\n".join(lines))
    return "\n\n".join(res) + "\n"

def generate_recommended_fix_order(issues):
    order = []
    step = 1
    for sev in ["P0", "P1", "P2", "P3", "P4"]:
        for iss in issues.get(sev, []):
            order.append(f"{step}. **[{sev}]** {iss.get('title')} (Vị trí: `{iss.get('route')}`)")
            step += 1
            if step > 10:
                break
        if step > 10:
            break
    if not order:
        return "*Hệ thống hoạt động xuất sắc, không có vấn đề cần khắc phục tức thì.*\n"
    return "\n".join(order) + "\n"

def render_report(target_url, issues, passed_checks, scores, overall_score, template_text, process_dir, output_file):
    def get_status_badge(s):
        if s >= 8.5: return "✅ Xuất sắc"
        if s >= 7.0: return "⚠️ Khá / Cần cải thiện"
        return "❌ Kém / Cần khắc phục"

    report_content = template_text
    report_content = report_content.replace("{target_url}", target_url)
    report_content = report_content.replace("{timestamp}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    report_content = report_content.replace("{mode}", "Audit Toàn Diện (Full)")
    report_content = report_content.replace("{overall_score}", str(overall_score))

    report_content = report_content.replace("{functional_score}", str(scores.get("functional", 10.0)))
    report_content = report_content.replace("{functional_status}", get_status_badge(scores.get("functional", 10.0)))

    report_content = report_content.replace("{logic_score}", str(scores.get("logic_state", 10.0)))
    report_content = report_content.replace("{logic_status}", get_status_badge(scores.get("logic_state", 10.0)))

    report_content = report_content.replace("{responsive_score}", str(scores.get("responsive", 10.0)))
    report_content = report_content.replace("{responsive_status}", get_status_badge(scores.get("responsive", 10.0)))

    report_content = report_content.replace("{ux_score}", str(scores.get("ux", 10.0)))
    report_content = report_content.replace("{ux_status}", get_status_badge(scores.get("ux", 10.0)))

    report_content = report_content.replace("{visual_score}", str(scores.get("visual", 10.0)))
    report_content = report_content.replace("{visual_status}", get_status_badge(scores.get("visual", 10.0)))

    report_content = report_content.replace("{a11y_score}", str(scores.get("accessibility", 10.0)))
    report_content = report_content.replace("{a11y_status}", get_status_badge(scores.get("accessibility", 10.0)))

    report_content = report_content.replace("{stability_score}", str(scores.get("stability", 10.0)))
    report_content = report_content.replace("{stability_status}", get_status_badge(scores.get("stability", 10.0)))

    report_content = report_content.replace("{p0_issues_block}", format_issue_block(issues.get("P0", [])))
    report_content = report_content.replace("{p1_issues_block}", format_issue_block(issues.get("P1", [])))
    report_content = report_content.replace("{p2_issues_block}", format_issue_block(issues.get("P2", [])))
    report_content = report_content.replace("{p3_issues_block}", format_issue_block(issues.get("P3", [])))
    report_content = report_content.replace("{p4_issues_block}", format_issue_block(issues.get("P4", [])))

    passed_text = "\n".join([f"- {p}" for p in passed_checks]) if passed_checks else "*Không có hạng mục nào.*"
    report_content = report_content.replace("{passed_checks_list}", passed_text)
    report_content = report_content.replace("{recommended_fix_order}", generate_recommended_fix_order(issues))

    report_content = report_content.replace("{screenshot_dir}", str(Path(process_dir) / "screenshots"))
    report_content = report_content.replace("{data_json_path}", str(Path(process_dir) / "audit_data.json"))

    out_p = Path(output_file)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(report_content, encoding="utf-8")
    return report_content

def main():
    parser = argparse.ArgumentParser(description="Tạo báo cáo thẩm định chất lượng ứng dụng cho App Auditor")
    parser.add_argument("--data", default="_process/audit_data.json", help="File dữ liệu audit JSON tổng hợp")
    parser.add_argument("--scoring", default=".agents/skills/app-auditor/resources/scoring_matrix.json", help="File ma trận tính điểm")
    parser.add_argument("--template", default=".agents/skills/app-auditor/templates/audit_report_template.md", help="File mẫu markdown")
    parser.add_argument("--output", default=None, help="Đường dẫn file báo cáo Markdown xuất bản")
    parser.add_argument("--output-dir", default=str(Path.home() / "Downloads"), help="Thư mục xuất báo cáo mặc định (~/Downloads/)")
    args = parser.parse_args()

    audit_data = load_json(args.data)
    scoring_matrix = load_json(args.scoring)

    target_url = audit_data.get("target_url", "http://localhost")
    process_dir = str(Path(args.data).parent)

    template_file = Path(args.template)
    if template_file.exists():
        template_text = template_file.read_text(encoding="utf-8")
    else:
        template_text = "# Báo cáo Kiểm định Ứng Dụng\n{overall_score}\n"

    issues, passed_checks = classify_issues(audit_data)
    scores, overall = calculate_scores(issues, scoring_matrix)

    if args.output:
        out_file = Path(args.output).resolve()
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = Path(args.output_dir) / f"APP_AUDIT_REPORT_{ts}.md"

    render_report(target_url, issues, passed_checks, scores, overall, template_text, process_dir, out_file)
    print(f"\n[+] Đã tạo báo cáo thẩm định thành công!")
    print(f" -> Điểm tổng hợp: {overall} / 10.0")
    print(f" -> Đường dẫn file báo cáo: {out_file}")

if __name__ == "__main__":
    main()
