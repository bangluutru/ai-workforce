#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deterministic_checker.py - Kiểm tra tất định cho MỌI route ở desktop + mobile:
console error, uncaught exception, request thất bại, HTTP >= 400, ảnh hỏng, axe-core WCAG 2.1 A/AA
(kể cả mục 'incomplete' về tương phản cần soát mắt), và trích văn bản trang để đối chiếu brief.
Thuộc bộ công cụ App Auditor (AI Workforce).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditor_common import BROKEN_IMG_JS, require_playwright  # noqa: E402

DEFAULT_VIEWPORTS = [
    {"id": "desktop_large", "width": 1440, "height": 900, "is_mobile": False},
    {"id": "mobile", "width": 390, "height": 844, "is_mobile": True, "has_touch": True, "device_scale_factor": 3},
]

AXE_RUN = """() => new Promise((resolve) => {
  axe.run({ runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } },
    (err, results) => resolve(err ? { error: String(err), violations: [], incomplete: [] } : results));
})"""


def _clean_nodes(nodes):
    return [{"target": n.get("target", []), "html": n.get("html", "")[:120], "failureSummary": n.get("failureSummary", "")}
            for n in nodes[:5]]


def check_page(context, url, vp_id, axe_code):
    page = context.new_page()
    res = {"route": url, "viewport": vp_id, "console_errors": [], "uncaught_exceptions": [], "failed_network_requests": [],
           "http_error_responses": [], "broken_images": [], "accessibility_violations": [], "contrast_needs_review": [],
           "keyboard_navigation": {}, "page_text": ""}
    page.on("console", lambda m: res["console_errors"].append({"type": m.type, "text": m.text, "location": m.location})
            if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: res["uncaught_exceptions"].append({"message": str(e)}))
    page.on("requestfailed", lambda r: res["failed_network_requests"].append(
        {"url": r.url, "method": r.method, "resource_type": r.resource_type, "failure": r.failure}))
    page.on("response", lambda r: res["http_error_responses"].append({"url": r.url, "status": r.status, "status_text": r.status_text})
            if r.status >= 400 else None)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        try:
            page.wait_for_load_state("networkidle", timeout=4000)
        except Exception:  # noqa: BLE001
            pass
        page.wait_for_timeout(300)
        res["broken_images"] = page.evaluate(BROKEN_IMG_JS)
        if axe_code:
            page.evaluate(axe_code)
            axe = page.evaluate(AXE_RUN)
            for v in axe.get("violations", []):
                res["accessibility_violations"].append({
                    "id": v.get("id"), "impact": v.get("impact"), "description": v.get("description"), "help": v.get("help"),
                    "helpUrl": v.get("helpUrl"), "nodes_count": len(v.get("nodes", [])), "sample_nodes": _clean_nodes(v.get("nodes", []))})
            for v in axe.get("incomplete", []):
                if v.get("id") == "color-contrast":
                    res["contrast_needs_review"] = _clean_nodes(v.get("nodes", []))
        res["keyboard_navigation"] = page.evaluate("""() => ({ total_focusable:
            document.querySelectorAll('button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])').length })""")
        res["page_text"] = page.evaluate("() => document.body ? document.body.innerText.slice(0, 20000) : ''")
    except Exception as e:  # noqa: BLE001
        res["runtime_error"] = str(e)
    page.close()
    return res


def run_deterministic_checks(routes, axe_script_path=None, headless=True, viewports=None):
    """routes: URL (str) hoặc danh sách route dict {url,...}. Kiểm tra từng route x từng viewport."""
    if isinstance(routes, str):
        routes = [{"url": routes}]
    urls = [r["url"] if isinstance(r, dict) else r for r in routes]
    viewports = viewports or DEFAULT_VIEWPORTS
    axe_path = Path(axe_script_path) if axe_script_path else Path(__file__).parent.parent / "resources" / "axe.min.js"
    axe_code = axe_path.read_text(encoding="utf-8", errors="ignore") if axe_path.exists() else ""
    if not axe_code:
        print(" [!] Không tìm thấy axe.min.js -> bỏ qua quét a11y (sẽ ghi N/A trong báo cáo)")

    print(f"[*] Kiểm tra tất định: {len(urls)} route x {len(viewports)} viewport")
    pages = []
    sync_playwright = require_playwright()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--disable-dev-shm-usage", "--no-sandbox"])
        for vp in viewports:
            ctx = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]}, is_mobile=vp.get("is_mobile", False),
                                      has_touch=vp.get("has_touch", False), device_scale_factor=vp.get("device_scale_factor", 1))
            for u in urls:
                r = check_page(ctx, u, vp["id"], axe_code)
                print(f"  -> {vp['id']:<14} {u}: console {len(r['console_errors'])}, uncaught {len(r['uncaught_exceptions'])}, "
                      f"failed req {len(r['failed_network_requests'])}, http>=400 {len(r['http_error_responses'])}, "
                      f"ảnh hỏng {len(r['broken_images'])}, a11y {len(r['accessibility_violations'])}")
                pages.append(r)
            ctx.close()
        browser.close()
    return {"url": urls[0] if urls else "", "routes": urls, "viewports": [v["id"] for v in viewports],
            "axe_available": bool(axe_code), "pages": pages}


def main():
    ap = argparse.ArgumentParser(description="Kiểm tra tất định (console, network, ảnh, axe) cho App Auditor")
    ap.add_argument("--url", required=True, help="URL cần kiểm tra (lặp lại --url để thêm route)", action="append")
    ap.add_argument("--app-map", help="app_map.json để kiểm tra mọi route đã khám phá")
    ap.add_argument("--axe", default=None)
    ap.add_argument("--output", default="_process/deterministic_results.json")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    routes = list(args.url)
    if args.app_map and Path(args.app_map).exists():
        routes = [r["url"] for r in json.loads(Path(args.app_map).read_text(encoding="utf-8")).get("routes", [])] or routes
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    data = run_deterministic_checks(routes, axe_script_path=args.axe, headless=not args.headed)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] Đã lưu: {out}")


if __name__ == "__main__":
    main()
