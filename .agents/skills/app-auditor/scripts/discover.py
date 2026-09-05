#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover.py — Module Khám Phá Cấu Trúc Ứng Dụng (Application Discovery & App Map)
Thuộc bộ công cụ App Auditor (AI Workforce)
"""

import sys
import os
import json
import argparse
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def normalize_url(base_url, href):
    if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
        return None
    joined = urllib.parse.urljoin(base_url, href)
    parsed_base = urllib.parse.urlparse(base_url)
    parsed_joined = urllib.parse.urlparse(joined)
    # Chỉ giữ các link cùng origin / host
    if parsed_base.netloc == parsed_joined.netloc:
        # Bỏ fragment
        return urllib.parse.urlunparse((parsed_joined.scheme, parsed_joined.netloc, parsed_joined.path, '', '', ''))
    return None

def classify_route(path):
    path_lower = path.lower()
    if path == "/" or any(k in path_lower for k in ["login", "signin", "auth", "register", "checkout", "payment", "order"]):
        return "critical"
    if any(k in path_lower for k in ["dashboard", "product", "item", "settings", "profile", "account", "cart", "admin"]):
        return "important"
    return "exploratory"

def discover_application(target_url, max_routes=10, headless=True):
    print(f"[*] Bắt đầu khám phá ứng dụng tại: {target_url}")
    app_map = {
        "target_url": target_url,
        "routes": [],
        "elements_summary": {
            "total_buttons": 0,
            "total_inputs": 0,
            "total_forms": 0,
            "total_modals": 0
        }
    }

    discovered_urls = set()
    queue = [target_url]
    parsed_base = urllib.parse.urlparse(target_url)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        while queue and len(discovered_urls) < max_routes:
            current_url = queue.pop(0)
            if current_url in discovered_urls:
                continue

            discovered_urls.add(current_url)
            parsed_curr = urllib.parse.urlparse(current_url)
            route_path = parsed_curr.path if parsed_curr.path else "/"
            route_info = {
                "url": current_url,
                "path": route_path,
                "category": classify_route(route_path),
                "title": "",
                "buttons": [],
                "inputs": [],
                "forms": [],
                "modals": [],
                "internal_links": []
            }

            try:
                print(f" -> Đang quét route: {route_path} ({current_url})")
                page.goto(current_url, wait_until="domcontentloaded", timeout=15000)
                try:
                    page.wait_for_load_state("networkidle", timeout=3000)
                except Exception:
                    pass

                route_info["title"] = page.title()

                # 1. Trích xuất liên kết nội bộ
                links = page.eval_on_selector_all("a[href]", "elements => elements.map(el => ({href: el.getAttribute('href'), text: el.innerText.trim()}))")
                for l in links:
                    norm = normalize_url(target_url, l.get("href"))
                    if norm and norm not in discovered_urls and norm not in queue:
                        queue.append(norm)
                    if norm:
                        route_info["internal_links"].append({"url": norm, "text": l.get("text", "")[:50]})

                # 2. Trích xuất nút bấm
                buttons = page.eval_on_selector_all(
                    "button, input[type='button'], input[type='submit'], [role='button'], a.btn, .button",
                    """elements => elements.map((el, i) => {
                        const rect = el.getBoundingClientRect();
                        return {
                            id: el.id || ('btn_' + i),
                            text: (el.innerText || el.value || '').trim().substring(0, 50),
                            tag: el.tagName.toLowerCase(),
                            type: el.getAttribute('type') || 'button',
                            is_visible: rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).display !== 'none'
                        };
                    })"""
                )
                route_info["buttons"] = buttons
                app_map["elements_summary"]["total_buttons"] += len(buttons)

                # 3. Trích xuất ô nhập liệu
                inputs = page.eval_on_selector_all(
                    "input:not([type='button']):not([type='submit']):not([type='hidden']), textarea, select",
                    """elements => elements.map((el, i) => {
                        return {
                            id: el.id || ('input_' + i),
                            name: el.name || '',
                            tag: el.tagName.toLowerCase(),
                            type: el.type || 'text',
                            placeholder: el.placeholder || '',
                            required: el.required || false,
                            has_label: !!(el.labels && el.labels.length > 0) || !!el.getAttribute('aria-label')
                        };
                    })"""
                )
                route_info["inputs"] = inputs
                app_map["elements_summary"]["total_inputs"] += len(inputs)

                # 4. Trích xuất Form
                forms = page.eval_on_selector_all(
                    "form",
                    """elements => elements.map((el, i) => {
                        return {
                            id: el.id || ('form_' + i),
                            action: el.action || '',
                            method: (el.method || 'GET').toUpperCase(),
                            inputs_count: el.querySelectorAll('input, textarea, select').length
                        };
                    })"""
                )
                route_info["forms"] = forms
                app_map["elements_summary"]["total_forms"] += len(forms)

                # 5. Phát hiện Dialog / Modal
                modals = page.eval_on_selector_all(
                    "dialog, [role='dialog'], .modal, .popup",
                    """elements => elements.map((el, i) => {
                        const rect = el.getBoundingClientRect();
                        return {
                            id: el.id || ('modal_' + i),
                            is_open: el.open || (rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).display !== 'none')
                        };
                    })"""
                )
                route_info["modals"] = modals
                app_map["elements_summary"]["total_modals"] += len(modals)

            except Exception as e:
                print(f" [!] Cảnh báo lỗi khi quét route {current_url}: {e}")
                route_info["error"] = str(e)

            app_map["routes"].append(route_info)

        browser.close()

    print(f"[+] Hoàn tất khám phá: tìm thấy {len(app_map['routes'])} routes, {app_map['elements_summary']['total_buttons']} buttons, {app_map['elements_summary']['total_inputs']} inputs.")
    return app_map

def main():
    parser = argparse.ArgumentParser(description="Khám phá ứng dụng web và tạo App Map (AIWF App Auditor)")
    parser.add_argument("--url", required=True, help="URL ứng dụng cần kiểm định (localhost hoặc web)")
    parser.add_argument("--output", default="_process/app_map.json", help="Đường dẫn file kết quả App Map JSON")
    parser.add_argument("--max-routes", type=int, default=8, help="Số lượng route tối đa cần crawl")
    parser.add_argument("--headed", action="store_true", help="Chạy browser có giao diện hiển thị")
    args = parser.parse_args()

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = discover_application(args.url, max_routes=args.max_routes, headless=not args.headed)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] Đã lưu App Map tại: {out_path}")

if __name__ == "__main__":
    main()
