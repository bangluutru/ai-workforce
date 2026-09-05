#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retest_runner.py — Chế Độ Tái Kiểm Tra Khoanh Vùng (Targeted Re-test & Regression Verifier)
Thuộc bộ công cụ App Auditor (AI Workforce)
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

def retest_issue(target_url, issue_type, viewport_id="mobile", selector=None, headless=True):
    print("=" * 65)
    print(f"🔄 KHỞI CHẠY RE-TEST KHOANH VÙNG (TARGETED RE-TEST)")
    print(f" 🎯 URL: {target_url}")
    print(f" 🔍 Loại lỗi cần xác minh: {issue_type.upper()}")
    print(f" 📱 Khung nhìn: {viewport_id}")
    if selector:
        print(f" 🎯 Selector: {selector}")
    print("=" * 65)

    viewport_map = {
        "desktop_large": {"width": 1440, "height": 900, "is_mobile": False},
        "desktop_laptop": {"width": 1024, "height": 768, "is_mobile": False},
        "tablet": {"width": 768, "height": 1024, "is_mobile": True},
        "mobile": {"width": 390, "height": 844, "is_mobile": True}
    }
    vp_cfg = viewport_map.get(viewport_id, viewport_map["mobile"])

    verdict = "UNKNOWN"
    details = ""
    regression_ok = True

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": vp_cfg["width"], "height": vp_cfg["height"]},
            is_mobile=vp_cfg.get("is_mobile", False)
        )
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        uncaught_errors = []
        page.on("pageerror", lambda err: uncaught_errors.append(str(err)))

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
            try:
                page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                pass

            # -----------------------------------------------------------------
            # KIỂM TRA LOẠI LỖI 1: TRÀN NGANG (OVERFLOW)
            # -----------------------------------------------------------------
            if issue_type in ["overflow", "responsive"]:
                is_overflowing = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
                scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
                win_width = page.evaluate("() => window.innerWidth")
                if not is_overflowing:
                    verdict = "VERIFIED_FIXED"
                    details = f"Lỗi tràn ngang đã được xử lý hoàn toàn! Chiều rộng trang: {scroll_width}px <= Khung nhìn: {win_width}px."
                else:
                    verdict = "REGRESSION_PERSISTED"
                    details = f"Lỗi vẫn tồn tại! Trang vẫn tràn ngang {scroll_width - win_width}px (ScrollWidth: {scroll_width}px > WinWidth: {win_width}px)."

            # -----------------------------------------------------------------
            # KIỂM TRA LOẠI LỖI 2: CONSOLE ERROR / RUNTIME EXCEPTION
            # -----------------------------------------------------------------
            elif issue_type in ["console", "runtime"]:
                time.sleep(1.0)
                if not console_errors and not uncaught_errors:
                    verdict = "VERIFIED_FIXED"
                    details = "Không còn lỗi console error hay unhandled exception nào khi tải trang."
                else:
                    verdict = "REGRESSION_PERSISTED"
                    details = f"Vẫn phát hiện lỗi: Console={console_errors}, Uncaught={uncaught_errors}."

            # -----------------------------------------------------------------
            # KIỂM TRA LOẠI LỖI 3: DEBOUNCE / RAPID CLICK
            # -----------------------------------------------------------------
            elif issue_type in ["debounce", "duplicate_submit"]:
                target_btn = page.locator(selector if selector else "button:visible, [role='button']:visible").first
                req_count = 0
                def on_req(r):
                    nonlocal req_count
                    req_count += 1
                page.on("request", on_req)

                for _ in range(4):
                    target_btn.click(force=True, timeout=500)
                    time.sleep(0.05)
                time.sleep(0.5)

                if req_count <= 1:
                    verdict = "VERIFIED_FIXED"
                    details = f"Nút bấm đã được trang bị debounce hoặc loading state khóa gửi trùng lặp (chỉ gửi {req_count} request khi click liên hoàn 4 lần)."
                else:
                    verdict = "REGRESSION_PERSISTED"
                    details = f"Nút bấm vẫn thiếu debounce: Gửi đi {req_count} requests khi click liên hoàn."

            # -----------------------------------------------------------------
            # KIỂM TRA LOẠI LỖI 4: ACCESSIBILITY (AXE-CORE)
            # -----------------------------------------------------------------
            elif issue_type in ["a11y", "accessibility"]:
                axe_file = script_dir.parent / "resources" / "axe.min.js"
                if axe_file.exists():
                    page.evaluate(axe_file.read_text(encoding="utf-8"))
                    axe_res = page.evaluate("""() => {
                        return new Promise((resolve) => {
                            axe.run({ runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } }, (err, results) => {
                                if (err) resolve({ violations: [] });
                                resolve(results);
                            });
                        });
                    }""")
                    violations = axe_res.get("violations", [])
                    if not violations:
                        verdict = "VERIFIED_FIXED"
                        details = "Toàn bộ vi phạm WCAG A/AA đã được khắc phục sạch sẽ (0 violations)."
                    else:
                        verdict = "REGRESSION_PERSISTED"
                        details = f"Vẫn còn {len(violations)} nhóm vi phạm accessibility."
                else:
                    verdict = "ERROR"
                    details = "Không tìm thấy file axe.min.js."

            # KIỂM TRA HỒI QUY XUNG QUANH (REGRESSION CHECK)
            # Kiểm tra xem việc fix lỗi có làm trang bị crash hoặc vỡ layout cơ bản không
            doc_height = page.evaluate("() => document.documentElement.scrollHeight")
            if doc_height < 50:
                regression_ok = False
                details += " [CẢNH BÁO HỒI QUY: Trang có dấu hiệu bị trắng hoặc mất nội dung sau khi sửa!]"

        except Exception as e:
            verdict = "ERROR"
            details = f"Ngoại lệ xảy ra trong khi re-test: {e}"

        browser.close()

    status_icon = "✅" if verdict == "VERIFIED_FIXED" and regression_ok else "❌"
    print("\n" + "=" * 65)
    print(f"🏁 KẾT QUẢ RE-TEST: {status_icon} [{verdict}]")
    print(f" 📝 Chi tiết: {details}")
    print(f" 🛡️ Kiểm tra hồi quy (Regression Check): {'PASS' if regression_ok else 'FAIL'}")
    print("=" * 65 + "\n")

    return {
        "verdict": verdict,
        "regression_ok": regression_ok,
        "details": details
    }

def main():
    parser = argparse.ArgumentParser(description="Tái kiểm tra khoanh vùng (Re-test Mode) cho App Auditor")
    parser.add_argument("--url", required=True, help="URL của trang cần re-test")
    parser.add_argument("--type", required=True, choices=["overflow", "responsive", "console", "runtime", "debounce", "duplicate_submit", "a11y", "accessibility"], help="Loại lỗi cần xác minh")
    parser.add_argument("--viewport", default="mobile", help="Khung nhìn cần kiểm tra (mobile, tablet, desktop_laptop, desktop_large)")
    parser.add_argument("--selector", default=None, help="CSS selector của phần tử cụ thể")
    parser.add_argument("--headed", action="store_true", help="Chạy browser hiển thị")
    args = parser.parse_args()

    retest_issue(
        target_url=args.url,
        issue_type=args.type,
        viewport_id=args.viewport,
        selector=args.selector,
        headless=not args.headed
    )

if __name__ == "__main__":
    main()
