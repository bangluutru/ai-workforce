#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
difficult_user.py - Mô phỏng Người dùng khó tính (Difficult & Adversarial QA). Thuộc App Auditor (AI Workforce).

AN TOÀN: chỉ thao tác (bấm, điền form) trên môi trường local (localhost / 127.0.0.1 / *.localhost / *.test).
URL thật (staging/production) -> bỏ qua toàn bộ, trừ khi người dùng cho phép rõ ràng bằng --allow-prod-actions.
Kể cả khi được phép, KHÔNG bấm nút phá hủy / thanh toán (xóa, hủy, thanh toán, đăng xuất...).
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditor_common import OVERFLOW_JS, is_local_url, require_playwright  # noqa: E402

DESTRUCTIVE = re.compile(r"xóa|xoá|delete|remove|hủy|huỷ|cancel|thanh toán|pay|checkout|đăng xuất|logout|sign out|"
                         r"chuyển khoản|transfer|purchase|unsubscribe", re.I)

FILL_JS = """(form) => {
  const today = new Date().toISOString().slice(0, 10);
  let filled = 0;
  for (const el of form.querySelectorAll('input, select, textarea')) {
    if (el.disabled || el.type === 'hidden' || el.type === 'submit' || el.type === 'button') continue;
    const t = (el.type || '').toLowerCase();
    let v = 'QA Test';
    if (t === 'tel') v = '0900000000';
    else if (t === 'email') v = 'qa@example.test';
    else if (t === 'number') v = String(el.min || 1);
    else if (t === 'date') v = today;
    else if (t === 'time') v = '10:00';
    else if (t === 'checkbox' || t === 'radio') { el.checked = true; filled++; continue; }
    if (el.tagName === 'SELECT') { const o = [...el.options].find(o => o.value); if (o) v = o.value; else continue; }
    const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set;
    setter.call(el, v);
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    filled++;
  }
  return filled;
}"""


def run_difficult_user_simulations(target_url, payloads_file=None, headless=True, allow_prod_actions=False):
    print(f"[*] Người dùng khó tính tại: {target_url}")
    results = {"url": target_url, "rapid_clicks_issues": [], "empty_input_validation": [], "boundary_input_issues": [],
               "modal_toggle_issues": [], "history_churn_issues": [], "skipped_buttons": [],
               "exercised": {"rapid_click_buttons": 0, "submit_with_valid_data": 0, "boundary_inputs": 0, "modal_cycles": 0}}
    if not is_local_url(target_url) and not allow_prod_actions:
        results["skipped"] = ("URL không phải môi trường local -> KHÔNG bấm/điền form để tránh tạo đơn, gửi dữ liệu hay xóa dữ liệu thật. "
                              "Chạy trên localhost/staging-local, hoặc thêm --allow-prod-actions khi người dùng cho phép.")
        print(f" [!] {results['skipped']}")
        return results

    payloads = {"boundary_strings": [{"type": "extreme_length", "value": "A" * 600},
                                     {"type": "special_characters", "value": "<script>alert('X')</script>&quot;'§±!@#$%^&*()"}]}
    pf = Path(payloads_file) if payloads_file else Path(__file__).parent.parent / "resources" / "adversarial_payloads.json"
    if pf.exists():
        try:
            payloads = json.loads(pf.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass

    sync_playwright = require_playwright()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--disable-dev-shm-usage", "--no-sandbox"])
        page = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()

        def load():
            page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
            try:
                page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:  # noqa: BLE001
                pass
        try:
            load()
            # ---- 1. Bấm liên hoàn (có điền dữ liệu hợp lệ nếu nút nằm trong form)
            buttons = page.locator("button:visible, [role='button']:visible, input[type='submit']:visible")
            idxs = list(range(min(buttons.count(), 6)))
            tested = 0
            for i in idxs:
                if tested >= 3:
                    break
                btn = buttons.nth(i)
                try:
                    text = (btn.inner_text(timeout=500) or btn.get_attribute("value") or "").strip()[:40]
                except Exception:  # noqa: BLE001
                    text = ""
                if DESTRUCTIVE.search(text):
                    results["skipped_buttons"].append(text)
                    continue
                in_form = btn.evaluate("b => !!b.closest('form')")
                if in_form:
                    filled = btn.evaluate(f"b => ({FILL_JS})(b.closest('form'))")
                    if filled:
                        results["exercised"]["submit_with_valid_data"] += 1
                reqs = []
                handler = lambda r, acc=reqs: acc.append(r) if r.resource_type in ("xhr", "fetch") else None  # noqa: E731
                page.on("request", handler)
                try:
                    for _ in range(4):
                        btn.click(force=True, timeout=800)
                        time.sleep(0.05)
                    time.sleep(0.8)
                except Exception:  # noqa: BLE001
                    pass
                finally:
                    page.remove_listener("request", handler)
                tested += 1
                counts = Counter((r.method, urllib.parse.urlsplit(r.url).path) for r in reqs)
                dup = {f"{m} {path}": n for (m, path), n in counts.items() if n >= 2}
                # Gửi lại cùng idempotency key (retry sau lỗi mạng) không tạo bản ghi trùng -> không phải lỗi debounce
                for ep in list(dup):
                    keys = set()
                    for r in reqs:
                        if f"{r.method} {urllib.parse.urlsplit(r.url).path}" != ep:
                            continue
                        try:
                            body = json.loads(r.post_data or "{}")
                            keys.add(body.get("idempotencyKey") or body.get("submissionId") or r.headers.get("idempotency-key"))
                        except Exception:  # noqa: BLE001
                            keys.add(None)
                    if len(keys) == 1 and None not in keys:
                        results.setdefault("idempotent_retries", []).append(
                            {"button_text": text, "endpoints": {ep: dup[ep]}, "idempotency_key": keys.pop()})
                        del dup[ep]
                if dup:
                    results["rapid_clicks_issues"].append({
                        "button_index": i, "button_text": text, "requests_spawned": sum(dup.values()), "endpoints": dup,
                        "defect": f"Nút '{text}' gửi trùng {dup} khi bấm 4 lần liên tiếp - thiếu khóa nút/idempotency."})
                if page.url.split("#")[0] != target_url.split("#")[0]:
                    load()
            results["exercised"]["rapid_click_buttons"] = tested

            # ---- 2. Chuỗi biên
            load()
            inputs = page.locator("input:visible:not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox])"
                                  ":not([type=radio]):not([type=number]):not([type=date]):not([type=time]), textarea:visible")
            for i in range(min(inputs.count(), 4)):
                for item in payloads.get("boundary_strings", [])[:2]:
                    try:
                        inputs.nth(i).fill(item.get("value", ""), timeout=1000)
                        results["exercised"]["boundary_inputs"] += 1
                        ov = page.evaluate(OVERFLOW_JS, 1440)
                        if ov["hasOverflow"]:
                            results["boundary_input_issues"].append({
                                "input_index": i, "payload_type": item.get("type"),
                                "defect": f"Nhập chuỗi {item.get('type')} làm trang tràn ngang {ov['overflowAmount']}px."})
                    except Exception as e:  # noqa: BLE001
                        results["boundary_input_issues"].append({"input_index": i, "payload_type": item.get("type"), "error": str(e)[:200]})

            # ---- 3. Mở/đóng modal
            load()
            trig = page.locator("[data-toggle='modal'], [data-modal-target], [aria-haspopup='dialog'], button:has-text('Mở'), button:has-text('Open')")
            if trig.count() > 0:
                try:
                    for _ in range(3):
                        trig.first.click(timeout=1000)
                        time.sleep(0.1)
                        close = page.locator("[data-dismiss='modal'], [aria-label='Close'], [aria-label='Đóng'], button:has-text('Đóng')")
                        (close.first.click(timeout=1000) if close.count() else page.keyboard.press("Escape"))
                        time.sleep(0.1)
                        results["exercised"]["modal_cycles"] += 1
                    if "hidden" in page.evaluate("() => getComputedStyle(document.body).overflow"):
                        results["modal_toggle_issues"].append({"defect": "Body kẹt 'overflow: hidden' sau khi đóng modal -> không cuộn được trang."})
                except Exception:  # noqa: BLE001
                    pass

            # ---- 4. Tải lại trang
            try:
                page.reload(wait_until="domcontentloaded", timeout=10000)
                if not page.title() and not page.evaluate("() => document.body.innerText.trim().length"):
                    results["history_churn_issues"].append({"defect": "Trang trắng sau khi tải lại (F5)."})
            except Exception as e:  # noqa: BLE001
                results["history_churn_issues"].append({"defect": f"Không tải lại được trang: {e}"})
        except Exception as e:  # noqa: BLE001
            results["runtime_error"] = str(e)
        browser.close()

    print(f"[+] Người dùng khó tính: {results['exercised']} | debounce lỗi {len(results['rapid_clicks_issues'])}, "
          f"bỏ qua nút nguy hiểm {results['skipped_buttons']}")
    return results


def main():
    ap = argparse.ArgumentParser(description="Người dùng khó tính (App Auditor)")
    ap.add_argument("--url", required=True)
    ap.add_argument("--payloads", default=None)
    ap.add_argument("--output", default="_process/difficult_user_results.json")
    ap.add_argument("--allow-prod-actions", action="store_true", help="Cho phép bấm/điền form trên URL không phải local (cần người dùng đồng ý)")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    data = run_difficult_user_simulations(args.url, payloads_file=args.payloads, headless=not args.headed,
                                          allow_prod_actions=args.allow_prod_actions)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] Đã lưu: {out}")


if __name__ == "__main__":
    main()
