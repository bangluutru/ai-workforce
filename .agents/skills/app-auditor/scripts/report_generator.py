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
import re
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

RISKY_CLAIMS = [
    r"\b(số|top)\s*(1|một)\b", r"tốt nhất|duy nhất|hàng đầu", r"hơn\s*[\d.,]+\s*\+?\s*(khách|người|đơn|lượt)",
    r"\d+([.,]\d+)?\s*%", r"cam kết|bảo đảm|đảm bảo", r"chữa|điều trị|trị (khỏi|dứt)",
    r"chính hãng|tiêu chuẩn .{0,25}(nhật|mỹ|châu âu|quốc tế)|nội địa nhật", r"\d+\s*(suất|khách hàng) (đầu tiên|sớm nhất)",
]


def _issue(title, route, viewport, category, steps, expected, actual, selector="", screenshot="", log="", type_="Defect"):
    return {"type": type_, "title": title, "route": route, "viewport": viewport, "category": category, "steps": steps,
            "expected": expected, "actual": actual, "selector": selector, "screenshot": screenshot, "log": log}


def _shot_index(sweep):
    idx = {}
    for sh in sweep.get("screenshots", []):
        idx[(sh.get("route"), sh.get("viewport"))] = sh.get("file", "")
    return idx


def _norm_digits(t):
    return re.sub(r"[^\d]", "", t)


def brief_vs_page(brief_text, page_text):
    """Tìm số liệu / câu chữ rủi ro có trên trang nhưng KHÔNG có trong brief (dấu hiệu nội dung bịa hoặc sót mẫu)."""
    findings = []
    brief_l = brief_text.lower()
    brief_digits = {_norm_digits(m) for m in re.findall(r"\d[\d.,:\s]{0,14}\d|\d", brief_text)}
    for m in set(re.findall(r"\d[\d.,]{1,14}\d\s*%?|\d+\s*%", page_text)):
        d = _norm_digits(m)
        if len(d) >= 2 and d not in brief_digits and not any(d in bd for bd in brief_digits):
            findings.append(f"Số liệu \"{m.strip()}\" không có trong brief")
    for line in {ln.strip() for ln in page_text.splitlines() if ln.strip()}:
        for pat in RISKY_CLAIMS:
            mm = re.search(pat, line, re.I)
            if mm and mm.group(0).lower() not in brief_l:
                findings.append(f"Câu chữ rủi ro không có trong brief: \"{line[:90]}\"")
                break
    return sorted(set(findings))


def classify_issues(audit_data):
    issues = {"P0": [], "P1": [], "P2": [], "P3": [], "P4": []}
    checks = []   # (trạng thái, mô tả): trạng thái ∈ {"✓", "N/A"}
    sweep = audit_data.get("visual_sweep", {})
    shots = _shot_index(sweep)
    det = audit_data.get("deterministic", {})
    pages = det.get("pages")
    if pages is None and det:  # tương thích dữ liệu cũ (1 trang, desktop)
        pages = [{**det, "route": det.get("url", "/"), "viewport": "desktop_large"}]
    pages = pages or []
    shot = lambda route, vp: shots.get((route, vp), "")  # noqa: E731

    # ---------- 1. Runtime & network (gộp trùng giữa các viewport)
    groups = {}
    for pg in pages:
        r, vp = pg.get("route", "/"), pg.get("viewport", "")
        for e in pg.get("uncaught_exceptions", []):
            groups.setdefault(("uncaught", r, e.get("message", "")[:160]), []).append(vp)
        for e in pg.get("console_errors", []):
            if e.get("type") == "error":
                groups.setdefault(("console", r, e.get("text", "")[:160]), []).append(vp)
        for e in pg.get("failed_network_requests", []):
            groups.setdefault(("reqfail", r, f"{e.get('method')} {e.get('url')} -> {e.get('failure')}"), []).append(vp)
        for e in pg.get("http_error_responses", []):
            groups.setdefault(("http", r, f"{e.get('status')} {e.get('url')}"), []).append(vp)
        for e in pg.get("broken_images", []):
            groups.setdefault(("img", r, e.get("src", "")), []).append(vp)
    for (kind, r, key), vps in groups.items():
        vps = sorted(set(vps))
        sc = shot(r, vps[0])
        vtxt = ", ".join(vps)
        if kind == "uncaught":
            issues["P0"].append(_issue(f"Uncaught exception: {key[:80]}", r, vtxt, "stability", f"1. Mở {r}.\n2. Xem DevTools Console.",
                                       "Không có lỗi JS không được bắt.", key, "window.onerror", sc, key))
        elif kind == "console":
            if "Failed to load resource" in key:
                continue  # đã được báo qua http/reqfail cụ thể hơn
            issues["P2"].append(_issue(f"Console error: {key[:80]}", r, vtxt, "stability", f"1. Mở {r}.\n2. Xem DevTools Console.",
                                       "Console không có lỗi.", key, "Console", sc, key))
        elif kind == "reqfail":
            issues["P2"].append(_issue(f"Request thất bại: {key[:90]}", r, vtxt, "functional", f"1. Mở {r}.\n2. Xem tab Network.",
                                       "Mọi request cần thiết hoàn tất.", key, "Network", sc, key))
        elif kind == "http":
            sev = "P1" if key.startswith("5") else "P2"
            issues[sev].append(_issue(f"HTTP {key[:90]}", r, vtxt, "functional", f"1. Mở {r}.\n2. Xem tab Network.",
                                      "Tài nguyên trả về 2xx/3xx.", key, "Network", sc, key))
        elif kind == "img":
            issues["P2"].append(_issue(f"Ảnh hỏng (không tải được): {key[:90]}", r, vtxt, "visual", f"1. Mở {r}.\n2. Quan sát vị trí ảnh.",
                                       "Ảnh hiển thị đầy đủ.", f"img.naturalWidth = 0 cho {key}", f"img[src='{key}']", sc, key))
    for sev_kind, label in (("uncaught", "Không có uncaught exception"), ("console", "Không có console error"),
                            ("reqfail", "Không có request thất bại"), ("http", "Không có HTTP >= 400"), ("img", "Không có ảnh hỏng")):
        if not pages:
            checks.append(("N/A", f"{label} - chưa kiểm (không có dữ liệu tất định)"))
        elif not any(k[0] == sev_kind for k in groups):
            checks.append(("✓", f"{label} trên {len({p.get('route') for p in pages})} route x {len({p.get('viewport') for p in pages})} viewport"))

    # ---------- 2. Responsive
    for ov in sweep.get("overflow_issues", []):
        vp, amt = ov.get("viewport", ""), ov.get("overflow_amount", 0)
        sev = "P1" if vp in ("mobile", "tablet") and amt > 30 else "P2"
        els = ", ".join(f"{e.get('tag')}{'#' + e['id'] if e.get('id') else ''} \"{e.get('text', '')[:30]}\"" for e in ov.get("elements", [])[:3])
        issues[sev].append(_issue(f"Tràn ngang {amt}px ở {vp} ({ov.get('viewport_width')}px)", ov.get("route", "/"), vp, "responsive",
                                  f"1. Mở trang ở chiều rộng {ov.get('viewport_width')}px.\n2. Vuốt ngang.",
                                  "Không có thanh cuộn ngang.", f"scrollWidth vượt clientWidth {amt}px do: {els}", els, ov.get("screenshot", ""),
                                  f"Overflow {amt}px"))
    for cl in sweep.get("clipped_content", []):
        els = "; ".join(f"{e.get('tag')}.{e.get('className', '')[:25]} \"{e.get('text', '')[:40]}\" (right={e.get('right')}px)"
                        for e in cl.get("elements", [])[:3])
        issues["P2"].append(_issue(f"Nội dung vượt mép bị cắt/ẩn ở {cl.get('viewport')}", cl.get("route", "/"), cl.get("viewport"), "responsive",
                                   f"1. Mở trang ở {cl.get('viewport_width')}px.\n2. Đọc hết nội dung các khối bên dưới.",
                                   "Toàn bộ nội dung nằm trong khung nhìn.", f"Phần tử vượt clientWidth nhưng bị overflow:hidden cắt: {els}",
                                   els, cl.get("screenshot", "")))
    for b in sweep.get("broken_images", []):
        if not any(k[0] == "img" and k[2] == b.get("src") for k in groups):
            issues["P2"].append(_issue(f"Ảnh hỏng: {b.get('src', '')[:90]}", b.get("route"), b.get("viewport"), "visual", "Mở trang.",
                                       "Ảnh hiển thị.", "naturalWidth = 0", "", b.get("screenshot", "")))
    if sweep.get("viewports_tested"):
        if not sweep.get("overflow_issues") and not sweep.get("clipped_content"):
            checks.append(("✓", f"Không tràn ngang/không cắt nội dung (đo theo clientWidth) ở {', '.join(sweep['viewports_tested'])}"))
    else:
        checks.append(("N/A", "Responsive - chưa chạy visual sweep"))
    touch = {}
    for t in sweep.get("touch_target_issues", []):
        touch.setdefault(t.get("route"), []).append(t)
    for route, ts in touch.items():
        t0 = ts[-1]
        issues["P3"].append(_issue(f"{t0.get('count')} vùng chạm < 44px", route, ", ".join(t.get("viewport") for t in ts), "ux",
                                   "Mở trên di động, thử chạm các nút/link nhỏ.", "Vùng chạm >= 44x44px.",
                                   f"Mẫu: {t0.get('samples', [])[:3]}", "", t0.get("screenshot", "")))
    for c in sweep.get("color_inconsistencies", [])[:3]:
        issues["P3"].append(_issue(f"Mã màu gần trùng ({c.get('color1')} vs {c.get('color2')})", "/", "desktop_large", "visual",
                                   "So sánh computed color.", "Một token màu cho cùng vai trò.", f"Lệch {c.get('diff')}", "",
                                   shot(sweep.get("screenshots", [{}])[0].get("route") if sweep.get("screenshots") else "", "desktop_large")))

    # ---------- 3. Accessibility (gộp theo route + rule)
    if pages and det.get("axe_available", True):
        a11y = {}
        review = {}
        for pg in pages:
            for v in pg.get("accessibility_violations", []):
                a11y.setdefault((pg.get("route"), v.get("id")), {"v": v, "vps": []})["vps"].append(pg.get("viewport"))
            if pg.get("contrast_needs_review"):
                review.setdefault(pg.get("route"), pg["contrast_needs_review"])
        for (route, rid), d in a11y.items():
            v, impact = d["v"], d["v"].get("impact") or "minor"
            sev = "P1" if impact == "critical" else ("P2" if impact in ("serious", "moderate") else "P3")
            tgt = ", ".join(str(n.get("target")) for n in v.get("sample_nodes", [])[:3])
            vps = sorted(set(d["vps"]))
            issues[sev].append(_issue(f"[A11y {impact.upper()}] {v.get('help')} ({rid})", route, ", ".join(vps), "accessibility",
                                      f"axe-core WCAG 2.1 A/AA; phần tử: {tgt}", v.get("description", ""),
                                      f"{v.get('nodes_count')} vị trí. HTML: {(v.get('sample_nodes') or [{}])[0].get('html', '')}",
                                      tgt, shot(route, vps[0]), v.get("helpUrl", "")))
        for route, nodes in review.items():
            tgt = ", ".join(str(n.get("target")) for n in nodes[:4])
            issues["P3"].append(_issue("[CẦN XÁC MINH] Tương phản chữ axe không tự tính được - soát bằng mắt", route, "desktop_large, mobile",
                                       "accessibility", "Mở ảnh chụp, kiểm tra chữ tại các phần tử này (chữ trên ảnh/nền chồng lớp).",
                                       "Tương phản >= 4.5:1.", f"axe 'incomplete' color-contrast: {tgt}", tgt, shot(route, "desktop_large")))
        if not a11y:
            checks.append(("✓", "axe-core không phát hiện vi phạm WCAG A/AA tự động (axe chỉ bao phủ một phần WCAG - vẫn cần soát mắt)"))
    else:
        checks.append(("N/A", "Accessibility - chưa chạy axe-core"))

    # ---------- 4. Người dùng khó tính
    diff = audit_data.get("difficult_user", {}) or {}
    ex = diff.get("exercised", {})
    if diff.get("skipped"):
        checks.append(("N/A", f"Người dùng khó tính - chưa kiểm: {diff['skipped']}"))
    for db in diff.get("rapid_clicks_issues", []):
        issues["P1"].append(_issue(f"Gửi trùng khi bấm liên hoàn: '{db.get('button_text')}'", diff.get("url", "/"), "desktop_large", "logic_state",
                                   f"1. Điền form hợp lệ.\n2. Bấm 4 lần liên tiếp nút '{db.get('button_text')}'.",
                                   "Chỉ 1 request; nút bị khóa khi đang gửi.", db.get("defect", ""), f"button:has-text('{db.get('button_text')}')",
                                   shot(diff.get("url"), "desktop_large"), str(db.get("endpoints"))))
    for ir in diff.get("idempotent_retries", []):
        checks.append(("✓", f"Bấm liên hoàn '{ir['button_text']}' gửi lại {ir['endpoints']} nhưng CÙNG idempotency key -> máy chủ không tạo bản ghi trùng"))
    if not diff.get("skipped") and diff:
        if ex.get("rapid_click_buttons"):
            if not diff.get("rapid_clicks_issues"):
                note = "có điền dữ liệu hợp lệ" if ex.get("submit_with_valid_data") else "KHÔNG có form được điền -> chưa kiểm gửi form thật"
                checks.append(("✓", f"Bấm liên hoàn {ex['rapid_click_buttons']} nút không sinh request trùng ({note}); bỏ qua nút nguy hiểm: {diff.get('skipped_buttons') or 'không'}"))
        else:
            checks.append(("N/A", "Bấm liên hoàn - chưa kiểm (không có nút an toàn để bấm)"))
    for b in diff.get("boundary_input_issues", []):
        issues["P2"].append(_issue(f"Chuỗi biên: {b.get('defect', b.get('error', ''))[:90]}", diff.get("url", "/"), "desktop_large", "functional",
                                   f"Nhập chuỗi {b.get('payload_type')} vào ô #{b.get('input_index')}.", "Không vỡ bố cục.",
                                   b.get("defect", b.get("error", "")), f"input[{b.get('input_index')}]", shot(diff.get("url"), "desktop_large")))
    if diff and not diff.get("skipped"):
        if not ex.get("boundary_inputs"):
            checks.append(("N/A", "Chuỗi biên - chưa kiểm (không có ô nhập chữ)"))
        elif not diff.get("boundary_input_issues"):
            checks.append(("✓", f"{ex['boundary_inputs']} lượt nhập chuỗi biên không làm vỡ bố cục"))
    for m in diff.get("modal_toggle_issues", []):
        issues["P2"].append(_issue("Kẹt cuộn trang sau khi đóng modal", diff.get("url", "/"), "desktop_large", "logic_state",
                                   "Mở/đóng modal 3 lần, thử cuộn.", "Trang cuộn bình thường.", m.get("defect"), "body", ""))
    if diff and not diff.get("skipped") and not ex.get("modal_cycles"):
        checks.append(("N/A", "Modal - chưa kiểm (không tìm thấy modal)"))
    for h in diff.get("history_churn_issues", []):
        issues["P1"].append(_issue(h.get("defect", "")[:90], diff.get("url", "/"), "desktop_large", "stability", "Tải lại trang (F5).",
                                   "Trang hiển thị lại bình thường.", h.get("defect", ""), "document", ""))

    # ---------- 5. Đối chiếu brief
    brief = audit_data.get("brief_text") or ""
    brief_findings = []
    if brief:
        for pg in pages:
            if pg.get("viewport") != "desktop_large":
                continue
            found = brief_vs_page(brief, pg.get("page_text", ""))
            brief_findings += found
            claims = [f for f in found if f.startswith("Câu chữ")]
            numbers = [f for f in found if f.startswith("Số liệu")]
            for f in claims:
                issues["P2"].append(_issue(f"Nội dung không có trong brief: {f[:90]}", pg.get("route"), "desktop_large", "ux",
                                           "So sánh nội dung trang với brief của người dùng.", "Mọi khẳng định đều có nguồn trong brief.",
                                           f, "", shot(pg.get("route"), "desktop_large")))
            if numbers:
                issues["P2"].append(_issue(f"{len(numbers)} số liệu trên trang không có trong brief", pg.get("route"), "desktop_large", "ux",
                                           "Đối chiếu từng số với brief / tài liệu của người dùng.", "Mọi giá, số liệu đều có nguồn.",
                                           "; ".join(numbers[:12]), "", shot(pg.get("route"), "desktop_large")))
    audit_data["_brief_findings"] = brief_findings

    # ---------- 6. Phát hiện thị giác của Agent (bắt buộc có ảnh làm bằng chứng)
    for vf in audit_data.get("visual_findings", []) or []:
        sev = vf.get("severity", "P2") if vf.get("severity") in issues else "P2"
        if not vf.get("screenshot") or not Path(vf["screenshot"]).exists():
            audit_data.setdefault("_rejected_visual", []).append(vf)
            continue
        issues[sev].append(_issue(vf.get("title", ""), vf.get("route", "/"), vf.get("viewport", ""), vf.get("category", "visual"),
                                  vf.get("steps", "Xem ảnh chụp."), vf.get("expected", ""), vf.get("actual", ""), vf.get("selector", ""),
                                  vf["screenshot"], "Soát thị giác (Agent)", type_="Visual review"))
    return issues, checks

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

def render_report(target_url, issues, passed_checks, scores, overall_score, template_text, process_dir, output_file, audit_data=None):
    audit_data = audit_data or {}
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

    passed_text = "\n".join(
        [f"- {st} {txt}" if st == "✓" else f"- N/A - {txt}" for st, txt in passed_checks]) if passed_checks else "*Không có hạng mục nào.*"
    sweep = audit_data.get("visual_sweep", {})
    shots = [sh.get("file") for sh in sweep.get("screenshots", [])]
    det = audit_data.get("deterministic", {})
    routes = det.get("routes") or [target_url]
    scope = (f"{len(routes)} route ({', '.join(routes[:6])}) | sweep: {', '.join(sweep.get('viewports_tested', []))} | "
             f"tất định: {', '.join(det.get('viewports', []) or ['desktop_large'])}")
    vf = audit_data.get("visual_findings")
    if vf is None:
        vstatus = ("❌ CHƯA SOÁT - báo cáo CHƯA HOÀN TẤT. Agent phải mở từng ảnh ở mục 5, ghi lỗi thị giác vào "
                   "visual_findings.json rồi chạy lại report_generator.py --visual-findings.")
    else:
        rej = audit_data.get("_rejected_visual", [])
        vstatus = f"✅ Đã soát {len(shots)} ảnh, {len(vf) - len(rej)} phát hiện thị giác" + (f", {len(rej)} bị loại vì thiếu ảnh bằng chứng" if rej else "")
    if audit_data.get("brief_text"):
        bf = audit_data.get("_brief_findings", [])
        brief_block = "\n".join(f"- {x}" for x in bf) if bf else "- ✓ Không thấy số liệu/khẳng định rủi ro nằm ngoài brief (vẫn cần Agent đọc đối chiếu)"
    else:
        brief_block = "- N/A - không có brief (dùng --brief <file> khi audit landing page để phát hiện nội dung bịa/sót mẫu)"
    screenshot_list = "\n".join(f"  - `{x}`" for x in shots) or "  - (không có)"
    report_content = report_content.replace("{scope}", scope).replace("{visual_review_status}", vstatus)
    report_content = report_content.replace("{brief_block}", brief_block).replace("{screenshot_list}", screenshot_list)
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
    parser.add_argument("--output-dir", default=str(Path.home() / "Downloads" / "AIWF_Output" / "app-auditor"), help="Thư mục xuất báo cáo mặc định (~/Downloads/AIWF_Output/)")
    parser.add_argument("--brief", help="File brief/nội dung gốc để đối chiếu nội dung trang (landing page)")
    parser.add_argument("--visual-findings", help="visual_findings.json do Agent ghi sau khi xem ảnh chụp")
    args = parser.parse_args()

    audit_data = load_json(args.data)
    if args.brief:
        audit_data["brief_text"] = Path(args.brief).read_text(encoding="utf-8")
    if args.visual_findings:
        audit_data["visual_findings"] = json.loads(Path(args.visual_findings).read_text(encoding="utf-8"))
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

    render_report(target_url, issues, passed_checks, scores, overall, template_text, process_dir, out_file, audit_data)
    print(f"\n[+] Đã tạo báo cáo thẩm định thành công!")
    print(f" -> Điểm tổng hợp: {overall} / 10.0")
    print(f" -> Đường dẫn file báo cáo: {out_file}")

if __name__ == "__main__":
    main()
