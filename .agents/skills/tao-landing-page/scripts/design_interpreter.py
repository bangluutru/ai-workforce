#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design_interpreter.py — Tầng Thông Dịch & Chuẩn Hóa Thiết Kế (DESIGN.md)
Hội tụ dữ liệu từ Stitch Adapter hoặc Figma Adapter thành một đặc tả trung gian duy nhất: DESIGN.md.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

def spec_to_design_md(spec: dict) -> str:
    """DESIGN.md từ landing_spec.json (định dạng mới) - để người dùng duyệt trước khi build."""
    c, t = spec.get("content", {}), spec.get("tokens", {})
    lines = [f"# DESIGN.md - {c.get('brand', {}).get('name', '[CẦN XÁC MINH: tên]')}", "",
             f"> Nguồn: `{spec.get('source', {}).get('adapter', '?')}`", "", "## Màu"]
    lines += [f"- {k}: `{v}`" for k, v in (t.get("colors") or {}).items()] or ["- [CẦN XÁC MINH: bảng màu]"]
    lines += ["", f"## Font: {t.get('fonts', {})}", "", "## Hero",
              f"- Tiêu đề: {c.get('hero', {}).get('headline', '[CẦN XÁC MINH]')}",
              f"- CTA: {c.get('hero', {}).get('primaryCta', {}).get('label', '[CẦN XÁC MINH]')}", "", "## Sections"]
    for s_ in c.get("sections", []):
        lines.append(f"- `{s_.get('id')}` ({s_.get('type')}): {s_.get('title')}")
    f = c.get("form")
    if f:
        lines += ["", f"## Form ({f.get('type')}): {f.get('title')}"]
        lines += [f"- `{x.get('key')}` {x.get('label')} ({x.get('type')}{', bắt buộc' if x.get('required') else ''})" for x in f.get("fields", [])]
    return "\n".join(lines) + "\n"


def interpret_and_generate_design_md(design_data: dict, output_path: str = None) -> str:
    """Chuyển đổi dữ liệu thiết kế từ Stitch/Figma (hoặc landing_spec.json) sang DESIGN.md."""
    if "content" in design_data:
        md = spec_to_design_md(design_data)
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(md, encoding="utf-8")
        return md
    source_type = design_data.get("source", "unknown")
    project_id = design_data.get("project_id") or design_data.get("file_key") or "landing-page-project"
    title = design_data.get("title", "Landing Page Chuyển Đổi Cao")
    tokens = design_data.get("tokens") or design_data.get("variables") or {}
    # KHÔNG có token mặc định: thiếu -> hiển thị [CẦN XÁC MINH] để Agent bổ sung từ thiết kế/brief
    colors = tokens.get("colors", {})
    typography = tokens.get("typography", tokens.get("fonts", {}))
    radius = tokens.get("radius", {
        "container": "1.25rem",
        "button": "9999px"
    })
    sections = design_data.get("sections", [])

    # Phân loại form nếu có
    form_section = None
    for sec in sections:
        if "form" in sec.get("role", "") or "form" in sec.get("id", ""):
            form_section = sec
            break

    form_type = "lead"
    form_id = f"{project_id}-form-01"
    if form_section:
        if form_section.get("role") == "order_form" or "order" in form_section.get("id", ""):
            form_type = "order"
        elif form_section.get("role") == "custom_form":
            form_type = "custom"

    md_lines = [
        f"# ĐẶC TẢ THIẾT KẾ TRUNG GIAN CHUẨN HÓA (DESIGN.MD)",
        "",
        f"> **Dự án:** `{project_id}`  ",
        f"> **Tiêu đề Trang:** {title}  ",
        f"> **Nguồn Adapter:** `{source_type.upper()}`  ",
        f"> **Thời gian khởi tạo:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"> **Phân loại Form:** `{form_type.upper()}` (Target Form ID: `{form_id}`)  ",
        "",
        "---",
        "",
        "## 1. Hệ Thống Token Thiết Kế (Design System Tokens)",
        "",
        "### 1.1. Bảng màu (Color Palette)",
        f"- **Primary (Chủ đạo / CTA):** `{colors.get('primary', '[CẦN XÁC MINH]')}`",
        f"- **Secondary (Phụ trợ):** `{colors.get('secondary', '[CẦN XÁC MINH]')}`",
        f"- **Accent (Điểm nhấn / Giá sốc):** `{colors.get('accent', '[CẦN XÁC MINH]')}`",
        f"- **Background (Nền trang):** `{colors.get('background', '[CẦN XÁC MINH]')}`",
        f"- **Surface (Thẻ / Container):** `{colors.get('surface', '[CẦN XÁC MINH]')}`",
        f"- **Text (Văn bản chính):** `{colors.get('text', '[CẦN XÁC MINH]')}`",
        f"- **Muted (Văn bản phụ):** `{colors.get('muted', '[CẦN XÁC MINH]')}`",
        "",
        "### 1.2. Kiểu chữ & Đo lường (Typography & Metrics)",
        f"- **Font Family:** `{typography.get('fontFamily', '[CẦN XÁC MINH]')}`",
        f"- **H1 Hero Headline:** `{typography.get('h1', '[CẦN XÁC MINH]')}`",
        f"- **H2 Section Heading:** `{typography.get('h2', '[CẦN XÁC MINH]')}`",
        f"- **Body Text:** `{typography.get('body', '[CẦN XÁC MINH]')}`",
        f"- **Container Max-Width:** `1280px (max-w-7xl mx-auto px-4 sm:px-6 lg:px-8)`",
        f"- **Border Radius:** Container=`{radius.get('container', '1.25rem')}`, Button=`{radius.get('button', '9999px')}`",
        "- **Shadow:** `shadow-2xl shadow-black/20`",
        "",
        "---",
        "",
        "## 2. Phân Cấp Cấu Trúc Các Phần (Section Hierarchy)",
        ""
    ]

    for idx, sec in enumerate(sections, start=1):
        s_id = sec.get("id", f"section_{idx}")
        s_role = sec.get("role", "custom")
        s_title = sec.get("title", f"Phần {idx}")
        content = sec.get("content", {})

        md_lines.append(f"### 2.{idx}. Section: `{s_id}` (Role: `{s_role}`)")
        md_lines.append(f"- **Tiêu đề:** {s_title}")
        if "headline" in content:
            md_lines.append(f"- **Headline:** {content['headline']}")
        if "subheadline" in content:
            md_lines.append(f"- **Subheadline:** {content['subheadline']}")
        if "primaryCta" in content:
            md_lines.append(f"- **Nút Hành Động:** `{content['primaryCta']}` (Gắn sự kiện `cta_click`)")
        if "items" in content:
            md_lines.append(f"- **Danh sách Thành phần:** {len(content['items'])} mục nổi bật")
            for item in content["items"]:
                md_lines.append(f"  * **{item.get('title', '')}**: {item.get('desc', '')}")
        if "fields" in content:
            md_lines.append(f"- **Các trường nhập liệu Form:**")
            for fld in content["fields"]:
                req = "bắt buộc" if fld.get("required") else "tùy chọn"
                md_lines.append(f"  * `{fld.get('key')}` ({fld.get('label')}) — {fld.get('type')}, {req}")
        md_lines.append("")

    md_lines.extend([
        "---",
        "",
        "## 3. Quy Chuẩn Tích Hợp Landing Hub v1.0",
        f"- **Project ID:** `{project_id}`",
        f"- **Landing Page ID:** `{project_id}-lp-01`",
        f"- **Form ID:** `{form_id}`",
        f"- **Form Type:** `{form_type}`",
        f"- **Phương thức SDK:** `LPHub.submit{form_type.capitalize()}()`",
        "- **Event Tracking Bắt Buộc:**",
        "  * `page_view` (Tự động khi tải trang)",
        "  * `cta_click` (Mọi nút CTA chính)",
        "  * `form_view` / `form_start` (Khi bắt đầu nhập form)",
        "",
        "---",
        "",
        "## 4. Dự Định Hành Vi Co Dãn (Responsive Intent)",
        "- **Mobile (< 640px):** 1 cột dọc, font chữ tối thiểu 15-16px, nút CTA cố định dính chân màn hình.",
        "- **Tablet (640px - 1024px):** Lưới 2 cột cân đối cho lợi ích và đánh giá.",
        "- **Desktop (> 1024px):** Bố cục 2-3 cột đối xứng, hiệu ứng hover viền gradient mượt mà."
    ])

    result_md = "\n".join(md_lines)
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(result_md, encoding="utf-8")

    return result_md

def main():
    parser = argparse.ArgumentParser(description="Tầng thông dịch DESIGN.md cho tao-landing-page")
    parser.add_argument("--input", required=True, help="File JSON chứa raw design data từ adapter")
    parser.add_argument("--output", default="DESIGN.md", help="Đường dẫn file DESIGN.md xuất ra")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Lỗi đọc file: {e}", file=sys.stderr)
        sys.exit(1)

    design_md = interpret_and_generate_design_md(data, args.output)
    print(f"✅ Đã tạo thành công đặc tả thiết kế trung gian: {args.output}")

if __name__ == "__main__":
    main()
