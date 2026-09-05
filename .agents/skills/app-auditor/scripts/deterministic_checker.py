#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deterministic_checker.py — Kiểm Tra Tất Định (Console, Network, Axe-core WCAG A/AA)
Thuộc bộ công cụ App Auditor (AI Workforce)
"""

import sys
import os
import json
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

def run_deterministic_checks(target_url, axe_script_path=None, headless=True):
    print(f"[*] Bắt đầu kiểm tra tất định tại: {target_url}")

    results = {
        "url": target_url,
        "console_errors": [],
        "uncaught_exceptions": [],
        "failed_network_requests": [],
        "http_error_responses": [],
        "accessibility_violations": [],
        "keyboard_navigation": {
            "total_focusable": 0,
            "missing_focus_indicator": 0
        }
    }

    axe_code = ""
    if axe_script_path and Path(axe_script_path).exists():
        axe_code = Path(axe_script_path).read_text(encoding="utf-8", errors="ignore")
    else:
        # Fallback tìm trong resources
        res_axe = Path(__file__).parent.parent / "resources" / "axe.min.js"
        if res_axe.exists():
            axe_code = res_axe.read_text(encoding="utf-8", errors="ignore")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Lắng nghe Console
        def on_console(msg):
            if msg.type in ["error", "warning"]:
                results["console_errors"].append({
                    "type": msg.type,
                    "text": msg.text,
                    "location": msg.location
                })
        page.on("console", on_console)

        # 2. Lắng nghe Uncaught Page Errors
        def on_page_error(err):
            results["uncaught_exceptions"].append({
                "message": str(err),
                "type": type(err).__name__
            })
        page.on("pageerror", on_page_error)

        # 3. Lắng nghe Network Requests thất bại
        def on_request_failed(req):
            results["failed_network_requests"].append({
                "url": req.url,
                "method": req.method,
                "resource_type": req.resource_type,
                "failure": req.failure
            })
        page.on("requestfailed", on_request_failed)

        # 4. Lắng nghe HTTP status >= 400
        def on_response(res):
            if res.status >= 400:
                results["http_error_responses"].append({
                    "url": res.url,
                    "status": res.status,
                    "status_text": res.status_text
                })
        page.on("response", on_response)

        # Điều hướng đến trang
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
            try:
                page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                pass

            # 5. Kiểm tra Trợ Năng bằng axe-core
            if axe_code:
                print(" -> Bơm axe-core và quét WCAG A & AA...")
                page.evaluate(axe_code)
                axe_res = page.evaluate("""() => {
                    return new Promise((resolve) => {
                        axe.run({
                            runOnly: {
                                type: 'tag',
                                values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']
                            }
                        }, (err, results) => {
                            if (err) resolve({ error: String(err), violations: [] });
                            resolve(results);
                        });
                    });
                }""")

                if isinstance(axe_res, dict) and "violations" in axe_res:
                    for v in axe_res["violations"]:
                        clean_nodes = []
                        for node in v.get("nodes", [])[:5]:
                            clean_nodes.append({
                                "target": node.get("target", []),
                                "html": (node.get("html", "")[:120]),
                                "failureSummary": node.get("failureSummary", "")
                            })
                        results["accessibility_violations"].append({
                            "id": v.get("id"),
                            "impact": v.get("impact"),
                            "description": v.get("description"),
                            "help": v.get("help"),
                            "helpUrl": v.get("helpUrl"),
                            "nodes_count": len(v.get("nodes", [])),
                            "sample_nodes": clean_nodes
                        })
                    print(f" -> Phát hiện {len(results['accessibility_violations'])} nhóm vi phạm Accessibility.")
            else:
                print(" [!] Cảnh báo: Không tìm thấy file axe.min.js để quét Accessibility.")

            # 6. Kiểm tra Focusable Elements
            focus_metrics = page.evaluate("""() => {
                const focusables = document.querySelectorAll('button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
                let count = focusables.length;
                let missingCount = 0;
                focusables.forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.outlineStyle === 'none' && style.boxShadow === 'none' && style.borderStyle === 'none') {
                        missingCount++;
                    }
                });
                return { total: count, missing: missingCount };
            }""")
            results["keyboard_navigation"]["total_focusable"] = focus_metrics["total"]
            results["keyboard_navigation"]["missing_focus_indicator"] = focus_metrics["missing"]

        except Exception as e:
            print(f" [!] Lỗi trong quá trình kiểm tra tất định: {e}")
            results["runtime_error"] = str(e)

        browser.close()

    return results

def main():
    parser = argparse.ArgumentParser(description="Kiểm tra tất định (Console, Network, Axe-core) cho App Auditor")
    parser.add_argument("--url", required=True, help="URL cần kiểm tra")
    parser.add_argument("--axe", default=None, help="Đường dẫn file axe.min.js")
    parser.add_argument("--output", default="_process/deterministic_results.json", help="File lưu kết quả JSON")
    parser.add_argument("--headed", action="store_true", help="Chạy browser có hiển thị")
    args = parser.parse_args()

    out_file = Path(args.output).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    data = run_deterministic_checks(args.url, axe_script_path=args.axe, headless=not args.headed)
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] Đã lưu kết quả kiểm tra tất định tại: {out_file}")

if __name__ == "__main__":
    main()
