#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
visual_sweep.py — Quét Giao Diện Đa Khung Nhìn (Visual Sweep & Responsive Audit)
Thuộc bộ công cụ App Auditor (AI Workforce)
"""

import sys
import os
import re
import json
import argparse
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright

def sanitize_slug(text):
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', text.strip('/').replace('/', '_'))
    return clean if clean else "root"

def rgb_to_hex(rgb_str):
    match = re.search(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', rgb_str)
    if match:
        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return f"#{r:02X}{g:02X}{b:02X}"
    return rgb_str

def check_overflow_and_metrics(page, viewport_id, is_mobile=False):
    metrics = page.evaluate("""() => {
        const docWidth = document.documentElement.scrollWidth;
        const winWidth = window.innerWidth;
        const hasOverflow = docWidth > winWidth + 1; // 1px dung sai
        
        let overflowingElements = [];
        if (hasOverflow) {
            const all = document.querySelectorAll('*');
            for (let el of all) {
                const rect = el.getBoundingClientRect();
                if (rect.right > winWidth + 2 && window.getComputedStyle(el).display !== 'none' && rect.width > 0) {
                    overflowingElements.push({
                        tag: el.tagName.toLowerCase(),
                        id: el.id || '',
                        className: (el.className || '').toString().substring(0, 40),
                        width: Math.round(rect.width),
                        right: Math.round(rect.right),
                        overflowAmount: Math.round(rect.right - winWidth)
                    });
                    if (overflowingElements.length >= 5) break;
                }
            }
        }

        // Bóc tách bảng màu của các nút và tiêu đề
        let colorSamples = [];
        const buttonsAndHeadings = document.querySelectorAll('button, .btn, [role="button"], h1, h2, h3, a');
        buttonsAndHeadings.forEach((el, idx) => {
            if (idx < 25) {
                const style = window.getComputedStyle(el);
                colorSamples.push({
                    tag: el.tagName.toLowerCase(),
                    text: (el.innerText || '').substring(0, 20),
                    color: style.color,
                    backgroundColor: style.backgroundColor,
                    borderColor: style.borderColor,
                    borderRadius: style.borderRadius,
                    fontSize: style.fontSize
                });
            }
        });

        // Kiểm tra touch target nhỏ trên mobile (<44px)
        let smallTouchTargets = [];
        const interactables = document.querySelectorAll('button, a, input, select');
        interactables.forEach((el) => {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                if (rect.width < 44 || rect.height < 44) {
                    smallTouchTargets.push({
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || '').substring(0, 30),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    });
                }
            }
        });

        return {
            docWidth: docWidth,
            winWidth: winWidth,
            hasOverflow: hasOverflow,
            overflowAmount: Math.max(0, docWidth - winWidth),
            overflowingElements: overflowingElements,
            colorSamples: colorSamples,
            smallTouchTargetsCount: smallTouchTargets.length,
            smallTouchTargetsSample: smallTouchTargets.slice(0, 5)
        };
    }""")
    return metrics

def detect_color_inconsistencies(color_samples):
    hex_colors = set()
    for s in color_samples:
        for key in ["color", "backgroundColor", "borderColor"]:
            val = s.get(key)
            if val and "rgba(0, 0, 0, 0)" not in val and "transparent" not in val:
                hex_val = rgb_to_hex(val)
                if hex_val.startswith("#"):
                    hex_colors.add(hex_val)
    
    # Tìm các mã màu xanh dương hoặc xám quá gần nhau (nghi vấn biến thể không chủ đích)
    suspicious_pairs = []
    hex_list = sorted(list(hex_colors))
    for i in range(len(hex_list)):
        for j in range(i + 1, len(hex_list)):
            c1, c2 = hex_list[i], hex_list[j]
            try:
                r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
                r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
                diff = abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)
                if 1 <= diff <= 18:
                    suspicious_pairs.append({"color1": c1, "color2": c2, "diff": diff})
            except Exception:
                pass
    return suspicious_pairs

def run_visual_sweep(routes, viewports_data, screenshots_dir, headless=True):
    print(f"[*] Bắt đầu Visual Sweep trên {len(routes)} routes x {len(viewports_data)} viewports")
    screenshots_dir = Path(screenshots_dir)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    sweep_results = {
        "viewports_tested": [v["id"] for v in viewports_data],
        "routes_tested": len(routes),
        "screenshots": [],
        "overflow_issues": [],
        "color_inconsistencies": [],
        "touch_target_issues": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )

        for vp in viewports_data:
            vp_id = vp["id"]
            vp_width = vp["width"]
            vp_height = vp["height"]
            is_mobile = vp.get("is_mobile", False)

            print(f"\n[Viewport] {vp['name']} ({vp_width}x{vp_height})")
            context = browser.new_context(
                viewport={"width": vp_width, "height": vp_height},
                device_scale_factor=vp.get("device_scale_factor", 1),
                is_mobile=is_mobile,
                has_touch=vp.get("has_touch", False)
            )
            page = context.new_page()

            for r in routes:
                target_url = r.get("url") if isinstance(r, dict) else r
                slug = sanitize_slug(r.get("path") if isinstance(r, dict) else target_url)
                shot_filename = f"{slug}_{vp_id}.png"
                shot_path = screenshots_dir / shot_filename

                try:
                    page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=2000)
                    except Exception:
                        pass

                    # Chụp ảnh toàn trang
                    page.screenshot(path=str(shot_path), full_page=True)
                    print(f"  ✓ Chụp {shot_filename}")

                    sweep_results["screenshots"].append({
                        "route": target_url,
                        "viewport": vp_id,
                        "file": str(shot_path),
                        "filename": shot_filename
                    })

                    # Kiểm tra metrics và overflow
                    metrics = check_overflow_and_metrics(page, vp_id, is_mobile=is_mobile)
                    if metrics["hasOverflow"]:
                        print(f"  ❌ Phát hiện tràn ngang ({metrics['overflowAmount']}px) trên viewport {vp_id}")
                        sweep_results["overflow_issues"].append({
                            "route": target_url,
                            "viewport": vp_id,
                            "viewport_width": vp_width,
                            "overflow_amount": metrics["overflowAmount"],
                            "elements": metrics["overflowingElements"],
                            "screenshot": str(shot_path)
                        })

                    if is_mobile and metrics["smallTouchTargetsCount"] > 0:
                        sweep_results["touch_target_issues"].append({
                            "route": target_url,
                            "viewport": vp_id,
                            "count": metrics["smallTouchTargetsCount"],
                            "samples": metrics["smallTouchTargetsSample"]
                        })

                    # Phân tích biến thể màu sắc trên desktop 1440px
                    if vp_id == "desktop_large":
                        inconsistent_colors = detect_color_inconsistencies(metrics["colorSamples"])
                        if inconsistent_colors:
                            sweep_results["color_inconsistencies"].extend(inconsistent_colors)

                except Exception as e:
                    print(f"  [!] Lỗi khi quét {target_url} ở {vp_id}: {e}")

            context.close()

        browser.close()

    return sweep_results

def main():
    parser = argparse.ArgumentParser(description="Quét giao diện đa khung nhìn cho App Auditor")
    parser.add_argument("--app-map", default="_process/app_map.json", help="Đường dẫn file App Map JSON")
    parser.add_argument("--url", default=None, help="URL trực tiếp nếu không dùng app map")
    parser.add_argument("--viewports", default=".agents/skills/app-auditor/resources/viewports.json", help="File cấu hình viewports")
    parser.add_argument("--screenshots-dir", default="_process/screenshots", help="Thư mục lưu ảnh chụp màn hình")
    parser.add_argument("--output", default="_process/visual_sweep.json", help="File lưu kết quả quét")
    parser.add_argument("--headed", action="store_true", help="Chạy browser có hiển thị")
    args = parser.parse_args()

    # Load viewports
    vp_path = Path(args.viewports).resolve()
    if not vp_path.exists():
        # Fallback viewports nếu file chưa tạo
        viewports_data = [
            {"id": "desktop_large", "name": "Desktop (1440px)", "width": 1440, "height": 900},
            {"id": "desktop_laptop", "name": "Laptop (1024px)", "width": 1024, "height": 768},
            {"id": "tablet", "name": "Tablet (768px)", "width": 768, "height": 1024, "is_mobile": True},
            {"id": "mobile", "name": "Mobile (390px)", "width": 390, "height": 844, "is_mobile": True}
        ]
    else:
        viewports_data = json.loads(vp_path.read_text(encoding="utf-8"))

    routes = []
    if args.url:
        routes = [{"url": args.url, "path": "/"}]
    else:
        map_path = Path(args.app_map).resolve()
        if map_path.exists():
            app_map_data = json.loads(map_path.read_text(encoding="utf-8"))
            routes = app_map_data.get("routes", [])
        else:
            print(f"[!] Không tìm thấy file {map_path}, yêu cầu truyền --url")
            sys.exit(1)

    out_file = Path(args.output).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    results = run_visual_sweep(routes, viewports_data, args.screenshots_dir, headless=not args.headed)
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[+] Hoàn tất Visual Sweep. Đã lưu kết quả tại: {out_file}")

if __name__ == "__main__":
    main()
