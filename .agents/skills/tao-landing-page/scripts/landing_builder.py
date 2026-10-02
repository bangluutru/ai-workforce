#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
landing_builder.py - Sinh dự án Landing Page (React + Vite + TS + Tailwind) từ landing_spec.json.

Nguyên tắc:
  * Component trong template là mã TĨNH; mọi chữ nằm trong src/content.json, mọi màu/font nằm trong src/theme.css.
    Builder KHÔNG ghép chuỗi người dùng vào JSX -> không vỡ build vì ký tự { } < > " và không có câu chữ mặc định.
  * Thiếu dữ kiện -> chèn "[CẦN XÁC MINH: ...]" (hiển thị nổi bật trên trang) và liệt kê; --strict -> thoát lỗi.
  * Không màu mặc định: thiếu token màu bắt buộc -> lỗi. Kiểm tra tương phản WCAG ngay khi build.
  * Câu chữ quảng cáo rủi ro (số 1, hơn N khách hàng, x%...) phải có nguồn trong claims_evidence.

  python3 .agents/skills/tao-landing-page/scripts/landing_builder.py --spec _process/<id>/landing_spec.json \
      --hub-config-json _process/<id>/hub_config.json --target-dir <output_dir> [--strict] [--validate-only]
"""

import argparse
import json
import re
import shutil
import sys
from html import escape
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "templates" / "react_vite_template"
SHARED_FONTS = SKILL_DIR.parent / "thiet-ke" / "resources" / "fonts"   # bộ font OFL dùng chung trong repo

FLAG = "[CẦN XÁC MINH"
FONT_FILES = {
    "Be Vietnam Pro": [("BeVietnamPro-Regular.ttf", 400), ("BeVietnamPro-SemiBold.ttf", 600), ("BeVietnamPro-Bold.ttf", 700)],
    "Spectral": [("Spectral-Regular.ttf", 400), ("Spectral-SemiBold.ttf", 600), ("Spectral-Bold.ttf", 700)],
}
RISKY_CLAIMS = [
    (r"\b(số|top)\s*(1|một)\b", "xếp hạng số 1"),
    (r"tốt nhất|duy nhất|hàng đầu|đầu tiên", "so sánh tuyệt đối"),
    (r"hơn\s*[\d.,]+\s*(\+\s*)?(khách|người|đơn|lượt)", "số lượng khách hàng"),
    (r"\d+([.,]\d+)?\s*%", "tỷ lệ phần trăm"),
    (r"cam kết|bảo đảm|đảm bảo", "cam kết/bảo đảm"),
    (r"chữa|điều trị|trị (khỏi|dứt)|khỏi bệnh", "công dụng y tế"),
    (r"chính hãng|nhập khẩu|tiêu chuẩn .{0,20}(nhật|mỹ|châu âu|quốc tế)", "xuất xứ/tiêu chuẩn"),
    (r"chỉ còn|duy nhất hôm nay|\d+\s*(suất|khách hàng) (đầu tiên|sớm nhất)", "khan hiếm"),
]


# ----------------------------------------------------------------------------- màu & tương phản
def _hex_to_rgb(h: str):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"Mã màu không hợp lệ: #{h}")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lum(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = _lum(_hex_to_rgb(a)), _lum(_hex_to_rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def _mix(a: str, b: str, t: float) -> str:
    ra, rb = _hex_to_rgb(a), _hex_to_rgb(b)
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ra, rb))


# ----------------------------------------------------------------------------- chuyển định dạng cũ
def convert_legacy(spec: dict) -> dict:
    """Chuyển đầu ra adapter cũ (sections[].role/content) sang landing_spec mới."""
    secs = spec.get("sections", [])
    get = lambda role: next((s.get("content", {}) for s in secs if s.get("role") == role), {})  # noqa: E731
    header, hero, footer = get("header"), get("hero"), get("footer")
    form_sec = next((s for s in secs if "form" in s.get("role", "")), None)
    content = {
        "meta": {"title": spec.get("title", ""), "description": hero.get("subheadline", ""), "lang": "vi"},
        "brand": {"name": header.get("brand", "")},
        "header": {"ctaLabel": header.get("ctaLabel"), "phone": header.get("hotline")},
        "hero": {"headline": hero.get("headline", ""), "subheadline": hero.get("subheadline"),
                 "primaryCta": {"label": hero.get("primaryCta", ""), "target": "#form"}},
        "sections": [],
        "footer": {"company": footer.get("company", ""), "address": footer.get("address"),
                   "lines": [x for x in [footer.get("license"), footer.get("disclaimer")] if x]},
    }
    if hero.get("secondaryCta"):
        content["hero"]["secondaryCta"] = {"label": hero["secondaryCta"], "target": "#sec-1"}
    if hero.get("stats"):
        content["hero"]["stats"] = hero["stats"]
    for i, s in enumerate(secs):
        c = s.get("content", {})
        if s.get("role") in ("benefits", "features") and c.get("items"):
            content["sections"].append({"type": "cards", "id": f"sec-{i}", "title": s.get("title") or c.get("title", ""),
                                        "items": [{"title": it.get("title", ""), "description": it.get("desc") or it.get("description")}
                                                  for it in c["items"]]})
    if form_sec:
        c = form_sec.get("content", {})
        ftype = "order" if "order" in form_sec.get("role", "") else ("custom" if "custom" in form_sec.get("role", "") else "lead")
        content["form"] = {"id": "form", "type": ftype, "title": form_sec.get("title", ""), "fields": c.get("fields", [])}
    return {"source": {"adapter": spec.get("source", "legacy")}, "tokens": spec.get("tokens", {}), "content": content}


# ----------------------------------------------------------------------------- kiểm tra nội dung
class Report:
    def __init__(self):
        self.errors, self.flags, self.warnings, self.info = [], [], [], []


def need(obj: dict, key: str, label: str, rep: Report, path: str):
    val = obj.get(key)
    if isinstance(val, str) and val.strip():
        if FLAG in val:
            rep.flags.append(f"{path}.{key}: {val}")
        return val
    obj[key] = f"[CẦN XÁC MINH: {label}]"
    rep.flags.append(f"{path}.{key}: thiếu -> {obj[key]}")
    return obj[key]


def walk_strings(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def validate(spec: dict, hub: dict, rep: Report) -> dict:
    tokens = spec.get("tokens") or {}
    colors = dict(tokens.get("colors") or {})
    for k in ("primary", "background", "text"):
        if not colors.get(k):
            rep.errors.append(f"tokens.colors.{k} bắt buộc (lấy từ thiết kế/brief - builder không tự chọn màu thương hiệu)")
    if rep.errors:
        return {}
    try:
        bg, text, primary = colors["background"], colors["text"], colors["primary"]
        colors.setdefault("surface", _mix(bg, text, 0.04))
        colors.setdefault("muted", _mix(text, bg, 0.35))
        colors.setdefault("secondary", primary)
        colors.setdefault("accent", primary)
        colors.setdefault("border", _mix(bg, text, 0.16))
        on_primary = colors.get("onPrimary") or max(("#FFFFFF", "#111111"), key=lambda c: contrast(c, primary))
        colors["onPrimary"] = on_primary
        checks = [("text/background", text, bg, 4.5, True), ("text/surface", text, colors["surface"], 4.5, True),
                  ("muted/background", colors["muted"], bg, 4.5, True), ("muted/surface", colors["muted"], colors["surface"], 4.5, False),
                  ("onPrimary/primary (nút)", on_primary, primary, 4.5, True), ("accent/background (nhãn nhỏ)", colors["accent"], bg, 4.5, False),
                  ("primary/surface (giá, số liệu)", primary, colors["surface"], 3.0, False)]
        for name, a, b, need_ratio, hard in checks:
            r = contrast(a, b)
            msg = f"Tương phản {name} = {r}:1 (cần >= {need_ratio}:1)"
            if r < need_ratio:
                (rep.errors if hard else rep.warnings).append(msg + " -> chỉnh token màu")
            else:
                rep.info.append(msg)
    except ValueError as e:
        rep.errors.append(str(e))
        return {}

    fonts = tokens.get("fonts") or {}
    for role in ("heading", "body"):
        name = fonts.get(role) or "Be Vietnam Pro"
        if name not in FONT_FILES:
            rep.warnings.append(f"Font {role} '{name}' không có trong bộ tự host ({', '.join(FONT_FILES)}) -> dùng Be Vietnam Pro")
            name = "Be Vietnam Pro"
        fonts[role] = name

    content = spec.get("content")
    if not isinstance(content, dict):
        rep.errors.append("Thiếu khối 'content' (xem templates/landing_spec_example.json)")
        return {}
    content.setdefault("meta", {}).setdefault("lang", "vi")
    need(content["meta"], "title", "tiêu đề trang (thẻ title)", rep, "meta")
    need(content["meta"], "description", "mô tả SEO", rep, "meta")
    need(content.setdefault("brand", {}), "name", "tên thương hiệu", rep, "brand")
    content.setdefault("header", {})
    hero = content.setdefault("hero", {})
    need(hero, "headline", "tiêu đề chính hero", rep, "hero")
    cta = hero.setdefault("primaryCta", {})
    need(cta, "label", "nhãn nút CTA chính", rep, "hero.primaryCta")
    cta.setdefault("target", "#form")
    content.setdefault("sections", [])
    for i, s in enumerate(content["sections"]):
        s.setdefault("id", f"sec-{i + 1}")
        if s.get("type") not in ("cards", "pricelist", "faq", "text"):
            rep.errors.append(f"sections[{i}].type '{s.get('type')}' không hỗ trợ (cards | pricelist | faq | text)")
        need(s, "title", "tiêu đề section", rep, f"sections[{i}]")
    footer = content.setdefault("footer", {})
    need(footer, "company", "tên doanh nghiệp ở chân trang", rep, "footer")

    form = content.get("form")
    if form:
        form.setdefault("id", "form")
        form.setdefault("type", hub.get("formType", "lead"))
        need(form, "title", "tiêu đề form", rep, "form")
        need(form, "submitLabel", "nhãn nút gửi", rep, "form")
        form.setdefault("successTitle", "Đã nhận thông tin")
        form.setdefault("successMessage", "Chúng tôi sẽ liên hệ lại với bạn.")
        form.setdefault("errorMessage", "Gửi chưa thành công, vui lòng thử lại.")
        fields = form.get("fields") or []
        if not fields:
            rep.errors.append("form.fields rỗng: liệt kê trường theo brief (key, label, type, required)")
        for j, f in enumerate(fields):
            if not f.get("key") or not f.get("label"):
                rep.errors.append(f"form.fields[{j}] thiếu key/label")
            f.setdefault("type", "text")
            if f["type"] not in ("text", "tel", "email", "number", "date", "time", "textarea", "select"):
                rep.errors.append(f"form.fields[{j}].type '{f['type']}' không hỗ trợ")
            if f["type"] == "select" and not f.get("options"):
                rep.errors.append(f"form.fields[{j}] kiểu select cần 'options'")
        if form["type"] == "order":
            p = form.get("product") or {}
            if not isinstance(p.get("unitPrice"), (int, float)) or p.get("unitPrice", 0) <= 0 or not p.get("name"):
                rep.errors.append("form.type=order cần form.product {id, name, unitPrice>0, currency} từ người dùng (không tự đặt giá)")
            p.setdefault("id", "product-1")
            p.setdefault("currency", "VND")
    elif cta.get("target", "").startswith("#form"):
        rep.warnings.append("CTA trỏ #form nhưng không có khối form")

    # Ảnh hero
    img = hero.get("image")
    if img:
        if not img.get("alt"):
            rep.errors.append("hero.image.alt bắt buộc (mô tả ảnh cho người dùng trình đọc màn hình)")
        if str(img.get("src", "")).startswith(("http://", "https://")):
            rep.warnings.append(f"Ảnh hero hotlink ngoài ({img['src'][:60]}...) - [CẦN XÁC MINH: bản quyền ảnh]; nên tải về và dùng file cục bộ")

    # Câu chữ rủi ro
    evidence = spec.get("claims_evidence") or {}
    for path, s in walk_strings(content):
        if path.startswith("hub"):
            continue
        for pat, kind in RISKY_CLAIMS:
            m = re.search(pat, s, re.I)
            if m and not any(k.lower() in s.lower() for k in evidence):
                rep.warnings.append(f"Câu chữ rủi ro ({kind}) chưa có nguồn trong claims_evidence: {path} = \"{s[:80]}\"")
                break
        if FLAG in s and not any(path in x for x in rep.flags):
            rep.flags.append(f"{path}: {s}")

    content["hub"] = {"projectId": hub.get("projectId", ""), "landingPageId": hub.get("landingPageId", ""),
                      "formId": hub.get("formId", "")}
    for k, v in content["hub"].items():
        if not v:
            rep.warnings.append(f"hub.{k} trống - chạy hub_integrator.py hoặc điền hub_config.json")
    return {"colors": colors, "fonts": fonts, "radius": tokens.get("radius", "0.75rem"), "content": content}


# ----------------------------------------------------------------------------- ghi dự án
def theme_css(t: dict) -> str:
    c = t["colors"]
    faces = []
    for fam in sorted({t["fonts"]["heading"], t["fonts"]["body"]}):
        for fname, w in FONT_FILES[fam]:
            faces.append(f'@font-face {{ font-family: "{fam}"; src: url("/fonts/{fname}") format("truetype"); '
                         f'font-weight: {w}; font-style: normal; font-display: swap; }}')
    fallback = {"Spectral": "Georgia, serif", "Be Vietnam Pro": "system-ui, -apple-system, 'Segoe UI', sans-serif"}
    return "\n".join([
        "/* SINH TỰ ĐỘNG bởi landing_builder.py từ landing_spec.json - sửa token trong spec rồi build lại */",
        *faces,
        ":root {",
        f"  --color-primary: {c['primary']};", f"  --color-on-primary: {c['onPrimary']};",
        f"  --color-secondary: {c['secondary']};", f"  --color-accent: {c['accent']};",
        f"  --color-background: {c['background']};", f"  --color-surface: {c['surface']};",
        f"  --color-text: {c['text']};", f"  --color-muted: {c['muted']};", f"  --color-border: {c['border']};",
        f"  --font-heading: \"{t['fonts']['heading']}\", {fallback[t['fonts']['heading']]};",
        f"  --font-body: \"{t['fonts']['body']}\", {fallback[t['fonts']['body']]};",
        f"  --radius-brand: {t['radius']};",
        "}", "",
    ])


def write_project(t: dict, spec_dir: Path, target: Path, hub: dict) -> list:
    target.mkdir(parents=True, exist_ok=True)
    for item in TEMPLATE_DIR.iterdir():
        dst = target / item.name
        if item.is_dir():
            shutil.copytree(item, dst, dirs_exist_ok=True)
        else:
            shutil.copy(item, dst)
    content = t["content"]
    # Ảnh cục bộ -> public/images
    img = content["hero"].get("image")
    preload = ""
    if img and img.get("src") and not str(img["src"]).startswith(("http://", "https://", "/")):
        src = (spec_dir / img["src"]).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Không thấy ảnh hero: {src}")
        (target / "public" / "images").mkdir(parents=True, exist_ok=True)
        shutil.copy(src, target / "public" / "images" / src.name)
        img["src"] = f"/images/{src.name}"
    if img and img.get("src"):
        preload = f'<link rel="preload" as="image" href="{escape(img["src"])}" fetchpriority="high" />'
    # Font tự host
    (target / "public" / "fonts").mkdir(parents=True, exist_ok=True)
    for fam in {t["fonts"]["heading"], t["fonts"]["body"]}:
        for fname, _ in FONT_FILES[fam]:
            shutil.copy(SHARED_FONTS / fname, target / "public" / "fonts" / fname)
    (target / "src" / "content.json").write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    (target / "src" / "theme.css").write_text(theme_css(t), encoding="utf-8")
    html = (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")
    html = (html.replace("{{TITLE}}", escape(content["meta"]["title"]))
                .replace("{{DESCRIPTION}}", escape(content["meta"]["description"]))
                .replace("{{PRELOAD}}", preload))
    html = html.replace('<html lang="vi">', f'<html lang="{escape(content["meta"].get("lang", "vi"))}">')
    (target / "index.html").write_text(html, encoding="utf-8")
    qa_url = hub.get("apiUrl") if re.match(r"^https?://(localhost|127\.0\.0\.1)", hub.get("apiUrl", "")) else "http://localhost:3001"
    (target / ".env.qa").write_text(f"# Chỉ dùng cho `npm run build:qa` (kiểm thử nội bộ)\nVITE_LPHUB_URL={qa_url}\n", encoding="utf-8")
    (target / ".gitignore").write_text("node_modules\ndist\n.qa\n.env.production\n", encoding="utf-8")
    return [str(p.relative_to(target)) for p in sorted(target.rglob("*")) if p.is_file() and "node_modules" not in p.parts]


def main():
    ap = argparse.ArgumentParser(description="Landing Builder (tao-landing-page)")
    ap.add_argument("--spec", "--design-json", dest="spec", required=True, help="landing_spec.json (hoặc đầu ra adapter cũ)")
    ap.add_argument("--hub-config-json", help="hub_config.json từ hub_integrator.py")
    ap.add_argument("--target-dir", help="Thư mục dự án đầu ra (<output_dir>)")
    ap.add_argument("--strict", action="store_true", help="Còn [CẦN XÁC MINH] hoặc câu chữ rủi ro -> thoát lỗi")
    ap.add_argument("--validate-only", action="store_true", help="Chỉ kiểm tra spec, không sinh dự án")
    ap.add_argument("--report", help="Ghi báo cáo build JSON (mặc định: cạnh spec)")
    args = ap.parse_args()

    spec_path = Path(args.spec).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if "content" not in spec and isinstance(spec.get("sections"), list):
        print("ℹ️  Phát hiện định dạng adapter cũ -> chuyển sang landing_spec.")
        spec = convert_legacy(spec)
    hub = {}
    if args.hub_config_json:
        h = json.loads(Path(args.hub_config_json).read_text(encoding="utf-8"))
        hub = h.get("config", h)
    hub = {**(spec.get("hub") or {}), **hub}

    rep = Report()
    t = validate(spec, hub, rep)
    files = []
    if not rep.errors and not args.validate_only:
        if not args.target_dir:
            rep.errors.append("Thiếu --target-dir")
        else:
            files = write_project(t, spec_path.parent, Path(args.target_dir).expanduser().resolve(), hub)

    strict_fail = args.strict and (rep.flags or any("Câu chữ rủi ro" in w for w in rep.warnings))
    report = {"spec": str(spec_path), "target": args.target_dir, "errors": rep.errors, "verify_flags": rep.flags,
              "warnings": rep.warnings, "contrast": rep.info, "files": files,
              "status": "FAIL" if rep.errors or strict_fail else "OK"}
    out = Path(args.report) if args.report else spec_path.parent / "build_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    for e in rep.errors:
        print(f"❌ {e}")
    for w in rep.warnings:
        print(f"⚠️  {w}")
    for f in rep.flags:
        print(f"🟨 {f}")
    for i in rep.info:
        print(f"✓ {i}")
    print(f"📄 Báo cáo build: {out}")
    if report["status"] == "FAIL":
        print("❌ BUILD SPEC FAIL")
        sys.exit(1)
    print(f"✅ {'Spec hợp lệ' if args.validate_only else 'Đã sinh dự án tại ' + str(args.target_dir)}"
          f" | {len(rep.flags)} mục [CẦN XÁC MINH] | {len(rep.warnings)} cảnh báo")


if __name__ == "__main__":
    main()
