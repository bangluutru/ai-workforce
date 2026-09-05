#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
difficult_user.py — Mô Phỏng Người Dùng Khó Tính (Difficult & Adversarial QA)
Thuộc bộ công cụ App Auditor (AI Workforce)
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

def run_difficult_user_simulations(target_url, payloads_file=None, headless=True):
    print(f"[*] Kích hoạt chế độ Người dùng khó tính (Difficult User Mode) tại: {target_url}")

    payloads = {
        "boundary_strings": [
            {"type": "extreme_length", "value": "A" * 600},
            {"type": "special_characters", "value": "<script>alert('X')</script>&quot;'§±!@#$%^&*()_+|}{[]:;?><"},
            {"type": "unicode_emoji", "value": "🚀 👨‍👩‍👧‍👦 𠮷野家 مرحبا بالعالم 123"}
        ]
    }
    if payloads_file and Path(payloads_file).exists():
        try:
            payloads = json.loads(Path(payloads_file).read_text(encoding="utf-8"))
        except Exception:
            pass
    else:
        res_file = Path(__file__).parent.parent / "resources" / "adversarial_payloads.json"
        if res_file.exists():
            try:
                payloads = json.loads(res_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    results = {
        "url": target_url,
        "rapid_clicks_issues": [],
        "empty_input_validation": [],
        "boundary_input_issues": [],
        "modal_toggle_issues": [],
        "history_churn_issues": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
            try:
                page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                pass

            # -------------------------------------------------------------
            # THỬ THÁCH 1: Nhấp chuột liên hoàn (Rapid Multi-clicks / Debounce check)
            # -------------------------------------------------------------
            buttons = page.locator("button:visible, [role='button']:visible, input[type='submit']:visible")
            btn_count = min(buttons.count(), 3)
            for i in range(btn_count):
                btn = buttons.nth(i)
                btn_text = (btn.inner_text() or "").strip()[:30]
                # Theo dõi số lượng request phát sinh khi click liên hoàn
                req_count = 0
                def count_req(req):
                    nonlocal req_count
                    req_count += 1
                page.on("request", count_req)

                try:
                    # Click nhanh 4 lần liên tiếp (50ms interval)
                    for _ in range(4):
                        btn.click(force=True, timeout=500)
                        time.sleep(0.05)

                    time.sleep(0.5)
                    # Nếu nút gửi form / action mà sinh ra 3-4 request giống nhau -> thiếu debounce
                    if req_count >= 3:
                        results["rapid_clicks_issues"].append({
                            "button_index": i,
                            "button_text": btn_text,
                            "requests_spawned": req_count,
                            "defect": f"Nút '{btn_text}' phát sinh {req_count} requests khi click liên hoàn, thiếu cơ chế debounce hoặc loading state vô hiệu hóa nút."
                        })
                except Exception:
                    pass
                finally:
                    page.remove_listener("request", count_req)

            # -------------------------------------------------------------
            # THỬ THÁCH 2: Điền chuỗi cực dài & Ký tự đặc biệt (Boundary Inputs)
            # -------------------------------------------------------------
            inputs = page.locator("input[type='text']:visible, textarea:visible")
            input_count = min(inputs.count(), 3)
            for i in range(input_count):
                inp = inputs.nth(i)
                for item in payloads.get("boundary_strings", [])[:2]:
                    val = item.get("value", "")
                    p_type = item.get("type", "")
                    try:
                        inp.fill(val)
                        # Kiểm tra xem có làm vỡ layout hoặc tràn màn hình không
                        is_overflowing = page.evaluate("""() => {
                            return document.documentElement.scrollWidth > window.innerWidth;
                        }""")
                        if is_overflowing:
                            results["boundary_input_issues"].append({
                                "input_index": i,
                                "payload_type": p_type,
                                "defect": f"Nhập chuỗi {p_type} làm trang xuất hiện thanh cuộn ngang (Horizontal Overflow)."
                            })
                    except Exception as e:
                        results["boundary_input_issues"].append({
                            "input_index": i,
                            "payload_type": p_type,
                            "error": str(e)
                        })

            # -------------------------------------------------------------
            # THỬ THÁCH 3: Thao tác mở/đóng Modal liên tục (Modal Churn)
            # -------------------------------------------------------------
            modal_triggers = page.locator("[data-toggle='modal'], [data-modal-target], button:has-text('Open'), button:has-text('Mở'), button:has-text('Thêm'), button:has-text('New')")
            if modal_triggers.count() > 0:
                trig = modal_triggers.first
                try:
                    for _ in range(3):
                        trig.click(timeout=1000)
                        time.sleep(0.1)
                        # Tìm nút đóng (close button hoặc esc)
                        close_btn = page.locator("[data-dismiss='modal'], [aria-label='Close'], button:has-text('Đóng'), button:has-text('Cancel'), .close")
                        if close_btn.count() > 0:
                            close_btn.first.click(timeout=1000)
                        else:
                            page.keyboard.press("Escape")
                        time.sleep(0.1)

                    # Kiểm tra xem body có bị kẹt khóa cuộn không (overflow: hidden)
                    body_overflow = page.evaluate("() => window.getComputedStyle(document.body).overflow")
                    if "hidden" in body_overflow:
                        results["modal_toggle_issues"].append({
                            "defect": "Body bị kẹt trạng thái 'overflow: hidden' sau khi đóng modal nhanh, khiến trang không thể cuộn được nữa."
                        })
                except Exception:
                    pass

            # -------------------------------------------------------------
            # THỬ THÁCH 4: Điều hướng ngược xuôi & F5 (History Churn & Reload)
            # -------------------------------------------------------------
            try:
                page.reload(wait_until="domcontentloaded", timeout=10000)
                # Kiểm tra xem trang có crash sau reload không
                title = page.title()
                if not title:
                    results["history_churn_issues"].append({
                        "defect": "Trang mất title hoặc hiển thị trang trắng sau khi reload F5."
                    })
            except Exception as e:
                results["history_churn_issues"].append({
                    "defect": f"Lỗi không thể tải lại trang sau reload: {e}"
                })

        except Exception as e:
            print(f" [!] Cảnh báo lỗi chung khi chạy Difficult User: {e}")

        browser.close()

    print(f"[+] Hoàn tất kịch bản Người dùng khó tính. Phát hiện {len(results['rapid_clicks_issues'])} vấn đề debounce, {len(results['boundary_input_issues'])} vấn đề boundary input, {len(results['modal_toggle_issues'])} vấn đề modal.")
    return results

def main():
    parser = argparse.ArgumentParser(description="Kịch bản Người dùng khó tính (Difficult User Mode) cho App Auditor")
    parser.add_argument("--url", required=True, help="URL cần thử nghiệm")
    parser.add_argument("--payloads", default=None, help="File chứa dữ liệu biên")
    parser.add_argument("--output", default="_process/difficult_user_results.json", help="File lưu kết quả")
    parser.add_argument("--headed", action="store_true", help="Chạy browser có hiển thị")
    args = parser.parse_args()

    out_file = Path(args.output).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    data = run_difficult_user_simulations(args.url, payloads_file=args.payloads, headless=not args.headed)
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] Đã lưu kết quả tại: {out_file}")

if __name__ == "__main__":
    main()
