#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qa_runner.py - Kiểm định THẬT dự án landing page trước khi bàn giao (tao-landing-page).

Gate 1  Bảo mật mã nguồn: không Firestore client, không token/secret trong src/ và .env*.
Gate 2  Token thương hiệu: component không dùng màu Tailwind cố định (slate-*, teal-*...).
Gate 3  TypeScript: npm run typecheck.
Gate 4  Build: npm run build:qa (vite --mode qa) -> dist/.
Gate 5  Nội dung: liệt kê [CẦN XÁC MINH] trong src/content.json (--strict -> FAIL).
Gate 6  Render thật: phục vụ dist/ trên 127.0.0.1, chụp 375 / 768 / 1440px, đo tràn ngang theo clientWidth,
        phần tử vượt mép, ảnh hỏng, lỗi console/JS, tài nguyên ngoài, màu CTA = --color-primary.
Gate 7  Gửi form E2E: CHỈ khi Hub là localhost và đang chạy, hoặc có --allow-test-data. Không thì ghi "CHƯA KIỂM".

Chạy bằng Python của repo (cần Playwright):
  .venv/bin/python .agents/skills/tao-landing-page/scripts/qa_runner.py --project-dir <output_dir> \
      --report-dir _process/<project_id>/qa
Mã thoát: 0 = không có FAIL, 1 = có FAIL, 2 = thiếu môi trường.
"""

import argparse
import functools
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
VIEWPORTS = [("mobile", 375, 812, True), ("tablet", 768, 1024, True), ("desktop", 1440, 900, False)]
SECRET_PATTERNS = [
    (r"firebase/firestore|getFirestore\(", "Firestore SDK phía client"),
    (r"test-super_admin|demo-token", "token quản trị thử nghiệm"),
    (r"Bearer\s+[A-Za-z0-9._\-]{16,}", "Bearer token cứng"),
    (r"sk_live_[0-9A-Za-z]{10,}|AIza[0-9A-Za-z_\-]{35}", "API key"),
]
PALETTE_CLASS = re.compile(r"\b(?:bg|text|border|from|via|to|ring|outline|shadow|divide|fill|stroke)-"
                           r"(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|"
                           r"indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}\b")


def run(cmd, cwd, timeout=300):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode == 0, (p.stdout or "") + (p.stderr or "")
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def is_local(url: str) -> bool:
    return bool(re.match(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?", url or ""))


def hub_health(api_url: str) -> bool:
    try:
        with urllib.request.urlopen(api_url.rstrip("/") + "/api/health", timeout=3) as r:
            return json.loads(r.read().decode() or "{}").get("status") == "ok"
    except Exception:  # noqa: BLE001
        return False


def form_e2e(api_url, project_id, lp_id, form_id, form_type) -> dict:
    endpoint = f"{api_url.rstrip('/')}/api/{'custom-form' if form_type == 'custom' else form_type}"
    key = f"ik_qa_test_{int(time.time())}_{os.urandom(3).hex()}"
    base = {"projectId": project_id, "landingPageId": lp_id, "formId": form_id, "idempotencyKey": key, "submissionId": key}
    if form_type == "order":
        payload = {**base, "customer": {"name": "QA TEST - xóa", "phone": "0900000000", "address": "QA TEST"},
                   "items": [{"id": "qa", "name": "QA TEST", "quantity": 1, "price": 1}], "total": 1, "currency": "VND",
                   "paymentMethod": "cod", "data": {"qa_test": True}}
    elif form_type == "lead":
        payload = {**base, "name": "QA TEST - xóa", "phone": "0900000000", "data": {"qa_test": True}}
    else:
        payload = {**base, "data": {"qa_test": True}}
    body = json.dumps(payload).encode()

    def post():
        req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode() or "{}")
            except Exception:  # noqa: BLE001
                return e.code, {}
    s1, b1 = post()
    s2, b2 = post()
    ok1 = s1 in (200, 201) and b1.get("success")
    ok2 = s2 == 200 and ((b2.get("data") or {}).get("idempotentReplay") is True)
    return {"ok": bool(ok1 and ok2), "first": [s1, b1.get("success")], "replay": [s2, (b2.get("data") or {}).get("idempotentReplay")]}


def serve(directory: Path):
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):  # noqa: D401
            pass
    handler = functools.partial(Quiet, directory=str(directory))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


PAGE_PROBE = """() => {
  const de = document.documentElement, cw = de.clientWidth;
  const over = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if (r.right > cw + 1 || r.left < -1) {
      over.push({tag: el.tagName.toLowerCase(), id: el.id, cls: String(el.className).slice(0, 60),
                 text: (el.innerText || '').trim().slice(0, 50), left: Math.round(r.left), right: Math.round(r.right)});
      if (over.length >= 8) break;
    }
  }
  const broken = [...document.images].filter(i => i.complete && i.naturalWidth === 0)
                  .map(i => ({src: i.currentSrc || i.src, alt: i.alt}));
  const noAlt = [...document.images].filter(i => !i.hasAttribute('alt')).map(i => i.src);
  const root = getComputedStyle(de);
  const btn = document.querySelector('a[href="#form"], button[type=submit]');
  return {scrollWidth: de.scrollWidth, clientWidth: cw, overflowing: over, broken, noAlt,
          primary: root.getPropertyValue('--color-primary').trim(),
          ctaBg: btn ? getComputedStyle(btn).backgroundColor : null,
          bodyBg: getComputedStyle(document.body).backgroundColor,
          bodyFont: getComputedStyle(document.body).fontFamily,
          fontsOk: [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight)};
}"""


def hex_to_rgb_str(h: str) -> str:
    h = h.strip().lstrip("#")
    return f"rgb({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)})" if len(h) == 6 else h


def render_checks(dist: Path, shots_dir: Path, hub_url: str, R: dict):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        R["fails"].append(f"Thiếu Playwright trong {sys.executable}. Chạy bằng {WORKSPACE / '.venv/bin/python'}")
        return
    httpd, base = serve(dist)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for name, w, h, mobile in VIEWPORTS:
                ctx = browser.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile,
                                          device_scale_factor=2 if mobile else 1)
                page = ctx.new_page()
                console, failed, external = [], [], []
                page.on("console", lambda m, c=console: c.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e, c=console: c.append(f"Uncaught: {e}"))
                page.on("requestfailed", lambda rq, f=failed: f.append(f"{rq.url} ({rq.failure})"))

                def route(r, ext=external):
                    u = r.request.url
                    if u.startswith(base) or u.startswith("data:") or (hub_url and u.startswith(hub_url.rstrip("/"))):
                        r.continue_()
                    else:
                        ext.append(u)
                        r.abort()
                page.route("**/*", route)
                page.goto(base, wait_until="networkidle")
                # content-visibility:auto bỏ qua render phần ngoài màn hình -> ảnh full-page bị trống; ép hiển thị khi chụp
                page.add_style_tag(content="*{content-visibility:visible !important}")
                page.wait_for_timeout(400)
                probe = page.evaluate(PAGE_PROBE)
                shot = shots_dir / f"landing_{name}_{w}.png"
                page.screenshot(path=str(shot), full_page=True)
                R["screenshots"].append(str(shot))
                tag = f"[{name} {w}px]"
                if probe["scrollWidth"] > probe["clientWidth"] + 1:
                    R["fails"].append(f"{tag} Tràn ngang: scrollWidth {probe['scrollWidth']} > clientWidth {probe['clientWidth']} "
                                      f"- phần tử: {probe['overflowing'][:3]}")
                elif probe["overflowing"]:
                    R["fails"].append(f"{tag} Phần tử vượt mép màn hình (bị cắt/ẩn): {probe['overflowing'][:3]}")
                for b in probe["broken"]:
                    R["fails"].append(f"{tag} Ảnh hỏng: {b}")
                for s in probe["noAlt"]:
                    R["fails"].append(f"{tag} Ảnh thiếu alt: {s}")
                hub_noise = [c for c in console if "LPHub" in c or (hub_url and hub_url.split('//')[-1] in c)
                             or "ERR_CONNECTION_REFUSED" in c]
                for c in console:
                    if c in hub_noise:
                        continue
                    R["fails"].append(f"{tag} Console error: {c[:200]}")
                if hub_noise and name == "desktop":
                    R["warnings"].append(f"Lỗi kết nối Landing Hub khi render ({len(hub_noise)}): Hub QA chưa chạy -> tracking chưa kiểm")
                if external and name == "desktop":
                    R["fails"].append(f"Trang tải tài nguyên bên ngoài (đã chặn khi QA): {sorted(set(external))[:5]} "
                                      "-> tự host ảnh/font trong public/")
                if name == "desktop":
                    want = hex_to_rgb_str(probe["primary"]) if probe["primary"] else None
                    R["brand"] = {"--color-primary": probe["primary"], "cta_background": probe["ctaBg"],
                                  "body_background": probe["bodyBg"], "body_font": probe["bodyFont"], "fonts_loaded": probe["fontsOk"]}
                    if not want or probe["ctaBg"] != want:
                        R["fails"].append(f"Nút CTA không dùng màu thương hiệu: {probe['ctaBg']} != {want} (--color-primary)")
                    if not probe["fontsOk"]:
                        R["warnings"].append("Không font tự host nào được tải - kiểm tra public/fonts và theme.css")
                ctx.close()
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()


def main():
    ap = argparse.ArgumentParser(description="QA Runner thật cho tao-landing-page")
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--report-dir", help="Nơi lưu ảnh + báo cáo (mặc định <project-dir>/.qa)")
    ap.add_argument("--hub-api-url", default="", help="URL Landing Hub để kiểm thử gửi form (chỉ localhost trừ khi --allow-test-data)")
    ap.add_argument("--project-id", default="")
    ap.add_argument("--lp-id", default="")
    ap.add_argument("--form-id", default="")
    ap.add_argument("--form-type", default="lead", choices=["lead", "order", "custom"])
    ap.add_argument("--allow-test-data", action="store_true", help="Cho phép gửi bản ghi QA TEST tới Hub không phải localhost")
    ap.add_argument("--strict", action="store_true", help="Còn [CẦN XÁC MINH] -> FAIL")
    args = ap.parse_args()
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        print(f"❌ Thiếu Playwright trong {sys.executable}. Chạy bằng Python của repo: {WORKSPACE / '.venv/bin/python'}", file=sys.stderr)
        sys.exit(2)

    proj = Path(args.project_dir).expanduser().resolve()
    rdir = Path(args.report_dir).expanduser().resolve() if args.report_dir else proj / ".qa"
    shots = rdir / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    R = {"project": str(proj), "fails": [], "warnings": [], "passed": [], "screenshots": [], "verify_flags": [],
         "form_e2e": "CHƯA KIỂM", "brand": {}}

    # Gate 1
    hits = []
    files = [f for f in (proj / "src").rglob("*") if f.suffix in (".ts", ".tsx", ".js", ".jsx", ".json")]
    files += [f for f in proj.glob(".env*") if f.name not in (".env.qa", ".env.production.example")]
    for f in files:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, txt):
                hits.append(f"{label} trong {f.relative_to(proj)}")
    (R["fails"].extend(hits) if hits else R["passed"].append(f"Gate 1: quét {len(files)} file, không có secret/Firestore client"))

    # Gate 2
    bad = []
    for f in (proj / "src").rglob("*.tsx"):
        for m in PALETTE_CLASS.finditer(f.read_text(encoding="utf-8")):
            bad.append(f"{f.name}: {m.group(0)}")
    (R["fails"].append(f"Màu Tailwind cố định thay vì token brand-*: {bad[:8]}") if bad
     else R["passed"].append("Gate 2: component chỉ dùng token brand-*"))

    # Gate 3 + 4
    if not (proj / "node_modules").exists():
        R["fails"].append("Chưa có node_modules: chạy `npm install` trong thư mục dự án rồi chạy lại QA")
    else:
        ok, out = run(["npm", "run", "typecheck"], proj)
        (R["passed"].append("Gate 3: tsc --noEmit sạch") if ok else R["fails"].append("TypeScript lỗi:\n" + out[-1500:]))
        ok, out = run(["npm", "run", "build:qa"], proj)
        (R["passed"].append("Gate 4: vite build --mode qa thành công") if ok and (proj / "dist" / "index.html").exists()
         else R["fails"].append("Build lỗi:\n" + out[-1500:]))

    # Gate 5
    cpath = proj / "src" / "content.json"
    if cpath.exists():
        flags = re.findall(r"\[CẦN XÁC MINH[^\]]*\]", cpath.read_text(encoding="utf-8"))
        R["verify_flags"] = flags
        if flags:
            (R["fails"] if args.strict else R["warnings"]).append(f"{len(flags)} mục [CẦN XÁC MINH] còn trên trang: {flags[:6]}")

    # Gate 6
    env_qa = proj / ".env.qa"
    qa_hub = ""
    if env_qa.exists():
        m = re.search(r"VITE_LPHUB_URL=(\S+)", env_qa.read_text())
        qa_hub = m.group(1) if m else ""
    if (proj / "dist" / "index.html").exists():
        render_checks(proj / "dist", shots, qa_hub, R)
        if R["screenshots"]:
            R["passed"].append(f"Gate 6: đã render {len(R['screenshots'])} khung nhìn")

    # Gate 7
    hub = args.hub_api_url
    if hub and args.project_id and args.lp_id and args.form_id:
        if not is_local(hub) and not args.allow_test_data:
            R["form_e2e"] = "CHƯA KIỂM (Hub không phải localhost; cần --allow-test-data để gửi bản ghi QA TEST)"
        elif not hub_health(hub):
            R["form_e2e"] = f"CHƯA KIỂM (Hub {hub} không phản hồi /api/health)"
        else:
            res = form_e2e(hub, args.project_id, args.lp_id, args.form_id, args.form_type)
            R["form_e2e"] = f"{'ĐẠT' if res['ok'] else 'LỖI'} {res}"
            if not res["ok"]:
                R["fails"].append(f"Gửi form E2E lỗi: {res}")
    if R["form_e2e"].startswith("CHƯA KIỂM"):
        R["warnings"].append(f"Gửi form: {R['form_e2e']}")

    R["status"] = "FAIL" if R["fails"] else "PASS_PENDING_VISUAL_REVIEW"
    (rdir / "qa_report.json").write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [f"# QA landing page: {proj.name}", f"Trạng thái: **{R['status']}** | Gửi form: {R['form_e2e']}", "",
          "## Lỗi (FAIL)", *([f"- {x}" for x in R["fails"]] or ["- (không)"]), "",
          "## Cảnh báo", *([f"- {x}" for x in R["warnings"]] or ["- (không)"]),
          "", "## Đạt", *[f"- {x}" for x in R["passed"]], "", "## Ảnh chụp (BẮT BUỘC mở xem từng ảnh)", *[f"- {x}" for x in R["screenshots"]],
          "", "## Nhận xét thị giác của Agent (điền sau khi xem ảnh)", "- mobile 375: ", "- tablet 768: ", "- desktop 1440: "]
    (rdir / "qa_report.md").write_text("\n".join(md), encoding="utf-8")

    print("=" * 70)
    print(f"QA LANDING PAGE: {proj}")
    for x in R["passed"]:
        print(f"  ✅ {x}")
    for x in R["warnings"]:
        print(f"  ⚠️  {x}")
    for x in R["fails"]:
        print(f"  ❌ {x}")
    print("-" * 70)
    print("BẮT BUỘC: mở (view_file) TỪNG ảnh dưới đây và ghi nhận xét vào qa_report.md mục 'Nhận xét thị giác':")
    for s in R["screenshots"]:
        print(f"   {s}")
    print("   Soát: màu/font đúng brief, nội dung đúng brief (không câu chữ lạ), CTA nổi bật, form đúng trường,")
    print("   không chữ bị cắt/chồng, khoảng cách đều, ảnh không vỡ, mục [CẦN XÁC MINH] được tô vàng.")
    print(f"📄 {rdir / 'qa_report.md'}")
    print("=" * 70)
    if R["fails"]:
        print(f"❌ QA FAIL ({len(R['fails'])} lỗi)")
        sys.exit(1)
    print("✅ QA tự động đạt - CHƯA bàn giao cho tới khi đã xem hết ảnh chụp.")


if __name__ == "__main__":
    main()
