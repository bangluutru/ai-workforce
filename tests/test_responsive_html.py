#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_responsive_html.py — Kiểm thử tự động tính năng xuất bản HTML Responsive (Mobile & Desktop).
Bao gồm:
1. Unit tests: Chuyển đổi Markdown, phân tích TOC, EJV Trilingual Dual-View.
2. Playwright Multi-Viewport Tests: iOS (iPhone SE, iPhone 14 Pro), Android (Pixel 7), Desktop HD/FHD.
   - Kiểm tra Zero Horizontal Overflow (không tràn ngang trên màn hình điện thoại).
   - Kiểm tra Console errors (0 error).
   - Kiểm tra tương tác: Theme toggle, Mobile Drawer, Language Tabs, Checkboxes.
"""

import json
import os
import sys
from pathlib import Path
import pytest

WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE / ".agents" / "skills" / "_shared"))
import bootstrap  # noqa: F401,E402

from responsive_html_builder import build_responsive_html, MarkdownHtmlConverter, EjvHtmlConverter


@pytest.fixture
def sample_md_file(tmp_path):
    f = tmp_path / "sample_report.md"
    content = """# Đọc Sâu: Thử Nghiệm

**Tác giả:** Antigravity Lab | **Năm:** 2026
**Mục đích:** Học tập | **Level:** 3

## 1. Luận điểm cốt lõi

- **Luận điểm:** Thử nghiệm xuất bản HTML đa thiết bị.
  > "Đây là câu trích dẫn nguyên văn đầy đủ để kiểm chứng bằng chứng." (vị trí: tr.10)

## 2. SCQA Phân tích

| Thành tố | Mô tả | Bằng chứng |
|---|---|---|
| S - Tình huống | Nhu cầu đọc tài liệu trên điện thoại tăng cao | tr.1 |
| C - Vướng mắc | File PDF và Markdown bị vỡ khung trên màn hình nhỏ | tr.2 |
| Q - Câu hỏi | Làm sao xuất bản HTML responsive đẹp mắt? | tr.3 |
| A - Câu trả lời | Sử dụng Shared Responsive HTML Builder | tr.4 |

## 3. Kế hoạch hành động 24h

- [ ] Bước 1: Mở tài liệu trên điện thoại
- [x] Bước 2: Kiểm tra độ mượt mà
- [ ] Bước 3: Đọc hiểu và ghi chép
"""
    f.write_text(content, encoding="utf-8")
    return f


@pytest.fixture
def sample_ejv_file(tmp_path):
    f = tmp_path / "sample_ejv.json"
    data = [
        {
            "type": "h1",
            "vn": "Hợp Đồng Dịch Vụ Mẫu",
            "en": "Master Service Agreement",
            "ja": "基本業務委託契約書"
        },
        {
            "type": "p",
            "vn": "Hợp đồng này được xác lập giữa Bên A và Bên B.",
            "en": "This Agreement is entered into between Party A and Party B.",
            "ja": "本契約は、甲と乙との間で締結される。"
        },
        {
            "type": "p",
            "vn": "Các điều khoản bảo mật được thực hiện nghiêm ngặt.",
            "en": "Confidentiality obligations shall be strictly observed.",
            "ja": "秘密保持義務は厳格に遵守されるものとする。"
        }
    ]
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return f


def test_markdown_to_html_converter(sample_md_file, tmp_path):
    out_html = tmp_path / "output_md.html"
    result = build_responsive_html(
        input_file=sample_md_file,
        output_file=out_html,
        doc_type="deep-reading",
        title="Đọc Sâu: Thử Nghiệm"
    )
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Đọc Sâu: Thử Nghiệm" in content
    assert "table-responsive" in content
    assert "evidence-quote" in content
    assert "quick-win" in content or "task-checkbox" in content
    assert "toc-link" in content


def test_ejv_parallel_to_html_converter(sample_ejv_file, tmp_path):
    out_html = tmp_path / "output_ejv.html"
    result = build_responsive_html(
        input_file=sample_ejv_file,
        output_file=out_html,
        doc_type="parallel",
        langs=["vn", "en", "ja"],
        title="Bản Dịch Đối Chiếu Tam Ngữ"
    )
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "lang-selector-mobile" in content
    assert "parallel-row" in content
    assert "parallel-col" in content
    assert "Tiếng Việt (VN)" in content
    assert "English (EN)" in content
    assert "日本語 (JA)" in content


def test_multi_viewport_playwright(sample_md_file, sample_ejv_file, tmp_path):
    """Kiểm thử thực tế trên trình duyệt Chromium không đầu qua Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Playwright chưa được cài đặt trong môi trường này")

    md_html = tmp_path / "pw_md.html"
    build_responsive_html(sample_md_file, md_html, doc_type="deep-reading")

    ejv_html = tmp_path / "pw_ejv.html"
    build_responsive_html(sample_ejv_file, ejv_html, doc_type="parallel", langs=["vn", "en", "ja"])

    evidence_dir = WORKSPACE / "_process" / "test_html_artifacts"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    viewports = [
        {"name": "ios_iphone_se", "width": 375, "height": 667, "is_mobile": True},
        {"name": "ios_iphone_14_pro", "width": 393, "height": 852, "is_mobile": True},
        {"name": "android_pixel_7", "width": 412, "height": 915, "is_mobile": True},
        {"name": "tablet_ipad", "width": 820, "height": 1180, "is_mobile": True},
        {"name": "desktop_hd", "width": 1440, "height": 900, "is_mobile": False},
        {"name": "desktop_fhd", "width": 1920, "height": 1080, "is_mobile": False},
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for target_file, file_tag in [(md_html, "doc_sau"), (ejv_html, "ejv_parallel")]:
            for vp in viewports:
                context = browser.new_context(
                    viewport={"width": vp["width"], "height": vp["height"]},
                    is_mobile=vp["is_mobile"]
                )
                page = context.new_page()

                console_errors = []
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

                page.goto(f"file://{target_file.resolve()}")
                page.wait_for_load_state("domcontentloaded")

                # 1. Kiểm tra 0 lỗi Console
                assert len(console_errors) == 0, f"Có lỗi console tại {vp['name']}: {console_errors}"

                # 2. Kiểm tra Zero Horizontal Overflow (Thân trang không bị tràn ngang)
                overflow_diff = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                assert overflow_diff <= 1, f"Bị tràn ngang {overflow_diff}px tại {vp['name']}!"

                # Chụp ảnh Light Mode
                shot_path_light = evidence_dir / f"{file_tag}_{vp['name']}_light.png"
                page.screenshot(path=str(shot_path_light), full_page=False)

                # 3. Thử nghiệm đổi sang Dark Theme
                page.evaluate("window.toggleTheme()")
                theme_val = page.evaluate("document.documentElement.getAttribute('data-theme')")
                assert theme_val == "dark"

                # Chụp ảnh Dark Mode
                shot_path_dark = evidence_dir / f"{file_tag}_{vp['name']}_dark.png"
                page.screenshot(path=str(shot_path_dark), full_page=False)

                # 4. Thử nghiệm Mobile Drawer trên mobile
                if vp["is_mobile"]:
                    page.evaluate("window.toggleMobileSidebar()")
                    page.wait_for_timeout(300)
                    is_open = page.evaluate("document.querySelector('.app-sidebar').classList.contains('open')")
                    assert is_open is True
                    # Chụp ảnh khi mở drawer trên mobile
                    shot_path_drawer = evidence_dir / f"{file_tag}_{vp['name']}_drawer.png"
                    page.screenshot(path=str(shot_path_drawer), full_page=False)
                    page.evaluate("window.toggleMobileSidebar()")
                    page.wait_for_timeout(300)

                # 5. Thử nghiệm đổi Tab ngôn ngữ trên EJV Mobile
                if vp["is_mobile"] and file_tag == "ejv_parallel":
                    page.evaluate("window.switchMobileLang('en')")
                    page.wait_for_timeout(200)
                    en_visible = page.evaluate("""
                        document.querySelector('.parallel-col[data-lang="en"]').classList.contains('mobile-active-lang')
                    """)
                    assert en_visible is True
                    shot_path_en = evidence_dir / f"{file_tag}_{vp['name']}_en_tab.png"
                    page.screenshot(path=str(shot_path_en), full_page=False)

                context.close()

        browser.close()
