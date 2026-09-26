#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_runner.py — Master Orchestrator Điều Phối Quy Trình Kiểm Định App Auditor
Thuộc bộ công cụ App Auditor (AI Workforce)
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime
from pathlib import Path

# Import các module nội bộ
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from discover import discover_application
from visual_sweep import run_visual_sweep
from deterministic_checker import run_deterministic_checks
from difficult_user import run_difficult_user_simulations
from report_generator import classify_issues, calculate_scores, render_report, load_json

def sanitize_slug(url_or_path):
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', url_or_path.replace('http://', '').replace('https://', '').replace('/', '_'))
    return clean.strip('_')[:30] if clean else "app"

def run_full_audit(target_url, output_dir=None, process_dir=None, max_routes=6, headless=True, skip_difficult=False):
    print("=" * 70)
    print(f"🚀 KHỞI ĐỘNG AI WORKFORCE APP AUDITOR")
    print(f" 🎯 Mục tiêu: {target_url}")
    print(f" 🕒 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    slug = sanitize_slug(target_url)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Xác định process_dir và output_dir
    workspace_root = script_dir.parent.parent.parent.parent
    if not process_dir:
        process_path = workspace_root / "_process" / f"audit_{slug}_{ts}"
    else:
        process_path = Path(process_dir).resolve()

    process_path.mkdir(parents=True, exist_ok=True)
    screenshots_path = process_path / "screenshots"
    screenshots_path.mkdir(parents=True, exist_ok=True)

    if not output_dir:
        out_dir = Path.home() / "Downloads" / "AIWF_Output" / "app-auditor"
    else:
        out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    skill_root = script_dir.parent
    viewports_file = skill_root / "resources" / "viewports.json"
    scoring_file = skill_root / "resources" / "scoring_matrix.json"
    axe_file = skill_root / "resources" / "axe.min.js"
    payloads_file = skill_root / "resources" / "adversarial_payloads.json"
    template_file = skill_root / "templates" / "audit_report_template.md"

    viewports_data = load_json(str(viewports_file))
    if not viewports_data:
        viewports_data = [
            {"id": "desktop_large", "name": "Desktop (1440px)", "width": 1440, "height": 900},
            {"id": "desktop_laptop", "name": "Laptop (1024px)", "width": 1024, "height": 768},
            {"id": "tablet", "name": "Tablet (768px)", "width": 768, "height": 1024, "is_mobile": True},
            {"id": "mobile", "name": "Mobile (390px)", "width": 390, "height": 844, "is_mobile": True}
        ]

    # BƯỚC 1: KHÁM PHÁ CẤU TRÚC ỨNG DỤNG (DISCOVERY & APP MAP)
    print("\n[BƯỚC 1/4] Khám phá ứng dụng và lập bản đồ App Map...")
    app_map = discover_application(target_url, max_routes=max_routes, headless=headless)
    app_map_file = process_path / "app_map.json"
    app_map_file.write_text(json.dumps(app_map, indent=2, ensure_ascii=False), encoding="utf-8")

    routes_to_test = app_map.get("routes", [])
    if not routes_to_test:
        routes_to_test = [{"url": target_url, "path": "/"}]

    # BƯỚC 2: QUÉT ĐA KHUNG NHÌN (VISUAL SWEEP & RESPONSIVE AUDIT)
    print("\n[BƯỚC 2/4] Thực hiện Visual Sweep qua 4 viewports (1440, 1024, 768, 390px)...")
    visual_sweep = run_visual_sweep(routes_to_test, viewports_data, str(screenshots_path), headless=headless)
    visual_file = process_path / "visual_sweep.json"
    visual_file.write_text(json.dumps(visual_sweep, indent=2, ensure_ascii=False), encoding="utf-8")

    # BƯỚC 3: KIỂM TRA TẤT ĐỊNH (CONSOLE, NETWORK, AXE-CORE WCAG A/AA)
    print("\n[BƯỚC 3/4] Kiểm tra tất định Runtime, Network và Accessibility...")
    deterministic = run_deterministic_checks(target_url, axe_script_path=str(axe_file), headless=headless)
    det_file = process_path / "deterministic_results.json"
    det_file.write_text(json.dumps(deterministic, indent=2, ensure_ascii=False), encoding="utf-8")

    # BƯỚC 4: NGƯỜI DÙNG KHÓ TÍNH (DIFFICULT & ADVERSARIAL USER)
    if not skip_difficult:
        print("\n[BƯỚC 4/4] Mô phỏng kịch bản Người dùng khó tính (Rapid clicks, Boundary inputs, Churn)...")
        difficult_user = run_difficult_user_simulations(target_url, payloads_file=str(payloads_file), headless=headless)
    else:
        print("\n[BƯỚC 4/4] Bỏ qua kịch bản Người dùng khó tính (theo cờ --skip-difficult).")
        difficult_user = {}

    diff_file = process_path / "difficult_user_results.json"
    diff_file.write_text(json.dumps(difficult_user, indent=2, ensure_ascii=False), encoding="utf-8")

    # TỔNG HỢP DỮ LIỆU AUDIT
    audit_data = {
        "target_url": target_url,
        "timestamp": ts,
        "app_map": app_map,
        "visual_sweep": visual_sweep,
        "deterministic": deterministic,
        "difficult_user": difficult_user
    }
    audit_data_file = process_path / "audit_data.json"
    audit_data_file.write_text(json.dumps(audit_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # XUẤT BÁO CÁO THẨM ĐỊNH (REPORT GENERATION)
    scoring_matrix = load_json(str(scoring_file))
    template_text = template_file.read_text(encoding="utf-8") if template_file.exists() else "# Báo cáo\n"

    issues, passed_checks = classify_issues(audit_data)
    scores, overall = calculate_scores(issues, scoring_matrix)

    report_filename = f"APP_AUDIT_REPORT_{slug}_{ts}.md"
    report_output_file = out_dir / report_filename

    render_report(target_url, issues, passed_checks, scores, overall, template_text, str(process_path), report_output_file)

    print("\n" + "=" * 70)
    print("🏁 HOÀN TẤT KIỂM ĐỊNH TOÀN DIỆN (AUDIT COMPLETE)")
    print(f" 🏆 ĐIỂM CHẤT LƯỢNG TỔNG HỢP: {overall} / 10.0")
    print(f" 🔴 P0 (Blocker): {len(issues.get('P0', []))} | 🟠 P1 (Serious): {len(issues.get('P1', []))} | 🟡 P2 (UX/Func): {len(issues.get('P2', []))} | 🔵 P3 (Cosmetic): {len(issues.get('P3', []))}")
    print(f" 📄 File báo cáo chính thức: {report_output_file}")
    print(f" 📁 Thư mục bằng chứng (Evidence): {process_path}")
    print("=" * 70 + "\n")

    return {
        "overall_score": overall,
        "scores": scores,
        "issues_count": {k: len(v) for k, v in issues.items()},
        "report_file": str(report_output_file),
        "process_dir": str(process_path)
    }

def main():
    parser = argparse.ArgumentParser(description="AI Workforce App Auditor Master Runner")
    parser.add_argument("--url", required=True, help="URL của ứng dụng web cần kiểm định")
    parser.add_argument("--output-dir", default=str(Path.home() / "Downloads" / "AIWF_Output" / "app-auditor"), help="Thư mục xuất file báo cáo cuối cùng (mặc định: ~/Downloads/AIWF_Output/)")
    parser.add_argument("--process-dir", default=None, help="Thư mục tạm lưu trữ ảnh và artifacts (mặc định: _process/...)")
    parser.add_argument("--max-routes", type=int, default=6, help="Số lượng route tối đa quét")
    parser.add_argument("--skip-difficult", action="store_true", help="Bỏ qua bước mô phỏng người dùng khó tính")
    parser.add_argument("--headed", action="store_true", help="Chạy browser hiển thị cửa sổ trực quan")
    args = parser.parse_args()

    res = run_full_audit(
        target_url=args.url,
        output_dir=args.output_dir,
        process_dir=args.process_dir,
        max_routes=args.max_routes,
        headless=not args.headed,
        skip_difficult=args.skip_difficult
    )

if __name__ == "__main__":
    main()
