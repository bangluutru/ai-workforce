#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Motion Presets Registry (Luật R7).
Quản lý và xuất bản 10 mẫu chuyển động chuẩn mực (HTML/CSS/GSAP),
hỗ trợ đa tỷ lệ khung hình (1:1, 16:9, 9:16) và nạp thương hiệu động.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

PRESETS_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = PRESETS_DIR.parents[4]  # .agents/skills/_shared/creative/presets -> workspace
LOCAL_GSAP_PATH = WORKSPACE_DIR / "_process" / "hyperframes_sandbox" / "node_modules" / "gsap" / "dist" / "gsap.min.js"

# Định nghĩa siêu dữ liệu cho 10 presets chuẩn mực
PRESET_REGISTRY: Dict[str, Dict[str, Any]] = {
    "01_fade_in": {
        "name": "01_fade_in",
        "category": "typography",
        "display_name": "Fade & Rise Thanh Lịch",
        "description": "Hiệu ứng mờ dần và nâng nhẹ tiêu đề cùng nhãn phụ với đường cong power3.out mượt mà.",
        "default_duration": 5.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["title"],
        "default_props": {
            "tag": "AI WORKFORCE 2.0",
            "title": "Sáng Tạo Đồ Họa Đỉnh Cao",
            "subtitle": "Quy trình tự động hóa chuyển động chuẩn xác từng khung hình",
            "accent_color": "#8B5CF6",
            "bg_color": "#0B0C10",
            "text_color": "#FFFFFF",
        },
        "template_file": "01_fade_in.html",
    },
    "02_slide_reveal": {
        "name": "02_slide_reveal",
        "category": "transition",
        "display_name": "Trượt Mở Khung Cắt (Masked Slide)",
        "description": "Chuyển cảnh trượt ngang hoặc trượt dọc phân tách nội dung với mặt nạ clipping mượt mà.",
        "default_duration": 5.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["title"],
        "default_props": {
            "tag": "CÔNG NGHỆ ĐỘT PHÁ",
            "title": "Tối Ưu Hóa Hiệu Suất",
            "subtitle": "Tăng tốc độ kết xuất gấp 3 lần với bộ khung HyperFrames",
            "accent_color": "#3B82F6",
            "bg_color": "#0F172A",
            "text_color": "#F8FAFC",
        },
        "template_file": "02_slide_reveal.html",
    },
    "03_scale_pop": {
        "name": "03_scale_pop",
        "category": "typography",
        "display_name": "Phóng To Đàn Hồi (Scale Pop)",
        "description": "Hiệu ứng phóng to với độ nảy back.out(1.7) tạo sự chú ý tức thì cho thông điệp cốt lõi.",
        "default_duration": 4.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["title"],
        "default_props": {
            "tag": "THÔNG BÁO QUAN TRỌNG",
            "title": "ĐỒNG BỘ 100% GIT-NATIVE",
            "subtitle": "Bảo toàn lịch sử mã nguồn tuyệt đối theo quy tắc R0 & R1",
            "accent_color": "#10B981",
            "bg_color": "#051610",
            "text_color": "#FFFFFF",
        },
        "template_file": "03_scale_pop.html",
    },
    "04_kinetic_title": {
        "name": "04_kinetic_title",
        "category": "typography",
        "display_name": "Tiêu Đề Động Học (Kinetic Title)",
        "description": "Hiệu ứng chữ nhảy động học theo nhịp ngắt, đổi màu sắc và tỏa hào quang neon thu hút.",
        "default_duration": 6.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["words"],
        "default_props": {
            "tag": "KINETIC ENGINE",
            "words": ["SÁNG TẠO", "TỰ ĐỘNG", "ĐỘT PHÁ"],
            "subtitle": "Khai phóng sức mạnh nhân sự số với Creative Studio 2.0",
            "accent_color": "#EC4899",
            "bg_color": "#180718",
            "text_color": "#FFFFFF",
        },
        "template_file": "04_kinetic_title.html",
    },
    "05_number_counter": {
        "name": "05_number_counter",
        "category": "data",
        "display_name": "Đếm Số Động Chỉ Số KPI (Number Counter)",
        "description": "Con số tăng trưởng nhảy từ 0 đến mục tiêu kèm vòng sáng tròn và nhãn phân tích số liệu.",
        "default_duration": 6.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["target_number", "label"],
        "default_props": {
            "tag": "CHỈ SỐ TĂNG TRƯỞNG",
            "start_number": 0,
            "target_number": 98.7,
            "suffix": "%",
            "label": "Tỷ Lệ Hài Lòng Khách Hàng",
            "sublabel": "Đo lường trên 10.000+ dự án xuất bản tự động",
            "accent_color": "#06B6D4",
            "bg_color": "#031525",
            "text_color": "#FFFFFF",
        },
        "template_file": "05_number_counter.html",
    },
    "06_logo_reveal": {
        "name": "06_logo_reveal",
        "category": "branding",
        "display_name": "Khám Phá Logo Thương Hiệu (Logo Reveal)",
        "description": "Vòng sóng xung kích tỏa sáng bung nở, hiển thị logo trung tâm kèm khẩu hiệu thương hiệu.",
        "default_duration": 5.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["brand_name"],
        "default_props": {
            "brand_name": "AI WORKFORCE",
            "tagline": "The Digital Workforce Operating System",
            "accent_color": "#6366F1",
            "bg_color": "#090A1A",
            "text_color": "#FFFFFF",
        },
        "template_file": "06_logo_reveal.html",
    },
    "07_product_spotlight": {
        "name": "07_product_spotlight",
        "category": "showcase",
        "display_name": "Tâm Điểm Sản Phẩm (Product Spotlight)",
        "description": "Thẻ sản phẩm 3D nổi bật dưới chùm sáng quét, hiển thị giá niêm yết và điểm bán hàng USP.",
        "default_duration": 7.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["product_name", "price"],
        "default_props": {
            "badge": "PHIÊN BẢN MỚI 2026",
            "product_name": "Creative Studio Pro 2.0",
            "specs": ["Chuyển động GSAP 60FPS", "Render Offline 1:1 Realtime", "100% Khử Mùi AI"],
            "price": "1.790.000đ",
            "original_price": "2.490.000đ",
            "accent_color": "#F59E0B",
            "bg_color": "#120E05",
            "text_color": "#FFFFFF",
        },
        "template_file": "07_product_spotlight.html",
    },
    "08_feature_card": {
        "name": "08_feature_card",
        "category": "showcase",
        "display_name": "Bộ Thẻ Tính Năng Kính Mờ (Feature Cards)",
        "description": "Ba thẻ kính mờ (glassmorphism) trượt vào so le với viền phát sáng và icon công nghệ sắc nét.",
        "default_duration": 7.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["features"],
        "default_props": {
            "tag": "TÍNH NĂNG CỐT LÕI",
            "title": "Nền Tảng Đồ Họa Tự Chủ",
            "features": [
                {"title": "Bố Cục Tự Động", "desc": "Chuẩn hóa Safe Zone 16:9, 1:1, 9:16"},
                {"title": "Đồng Bộ Nhịp Âm", "desc": "Bắt beat âm nhạc và voiceover chính xác"},
                {"title": "Bảo Mật Cấp Cao", "desc": "Zero External API, bảo vệ tuyệt đối mã nguồn"}
            ],
            "accent_color": "#8B5CF6",
            "bg_color": "#0D0B18",
            "text_color": "#FFFFFF",
        },
        "template_file": "08_feature_card.html",
    },
    "09_bar_chart": {
        "name": "09_bar_chart",
        "category": "data",
        "display_name": "Biểu Đồ Cột Tăng Trưởng (Bar Chart)",
        "description": "Các cột số liệu so sánh tăng dần chiều cao tuần tự với nhãn số liệu và hiệu ứng tỏa sáng.",
        "default_duration": 6.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["chart_data"],
        "default_props": {
            "tag": "BÁO CÁO HIỆU SUẤT",
            "title": "Tốc Độ Render So Với Chuẩn Cũ",
            "chart_data": [
                {"label": "Legacy Canvas", "value": 8, "display": "8 FPS"},
                {"label": "Puppeteer Raw", "value": 14, "display": "14 FPS"},
                {"label": "HyperFrames 2.0", "value": 30, "display": "30 FPS"}
            ],
            "accent_color": "#10B981",
            "bg_color": "#061510",
            "text_color": "#FFFFFF",
        },
        "template_file": "09_bar_chart.html",
    },
    "10_cta_reveal": {
        "name": "10_cta_reveal",
        "category": "cta",
        "display_name": "Kêu Gọi Hành Động (CTA Reveal)",
        "description": "Màn hình kết với nút bấm phát nhịp thở (pulsing button), cam kết uy tín và đường dẫn liên hệ.",
        "default_duration": 5.0,
        "supported_aspects": ["1:1", "16:9", "9:16"],
        "required_props": ["cta_text"],
        "default_props": {
            "headline": "Sẵn Sàng Nâng Tầm Video?",
            "subheadline": "Khám phá quy trình sản xuất video thông minh tự động hóa ngay hôm nay",
            "cta_text": "BẮT ĐẦU NGAY",
            "guarantee": "Hoàn tiền 100% trong 30 ngày · Không cần thẻ tín dụng",
            "domain": "aiworkforce.vn",
            "accent_color": "#EF4444",
            "bg_color": "#150606",
            "text_color": "#FFFFFF",
        },
        "template_file": "10_cta_reveal.html",
    },
}


def get_preset_metadata(name: str) -> Dict[str, Any]:
    """Lấy thông tin mô tả chi tiết của một preset theo tên."""
    clean_name = name.removesuffix(".html")
    if clean_name not in PRESET_REGISTRY:
        raise KeyError(f"Preset '{name}' không tồn tại. Danh sách hỗ trợ: {list(PRESET_REGISTRY.keys())}")
    return PRESET_REGISTRY[clean_name]


def list_presets() -> List[Dict[str, Any]]:
    """Liệt kê toàn bộ 10 motion presets có sẵn trong hệ thống."""
    return list(PRESET_REGISTRY.values())


def render_preset_html(
    preset_name: str,
    props: Optional[Dict[str, Any]] = None,
    width: int = 1920,
    height: int = 1080,
    duration: Optional[float] = None,
    brand_profile: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Kết xuất chuỗi HTML hoàn chỉnh từ preset với các thuộc tính truyền vào.
    
    Args:
        preset_name: Tên preset (vd: '01_fade_in')
        props: Từ điển thuộc tính người dùng ghi đè
        width: Chiều rộng khung hình
        height: Chiều cao khung hình
        duration: Thời lượng mong muốn (nếu None sẽ dùng default_duration)
        brand_profile: Hồ sơ thương hiệu (tùy chọn để ghi đè màu sắc)
        
    Returns:
        str: Chuỗi mã nguồn HTML hoàn chỉnh chứa CSS và GSAP timeline.
    """
    clean_name = preset_name.removesuffix(".html")
    meta = get_preset_metadata(clean_name)
    
    # Gộp props
    merged_props = dict(meta["default_props"])
    if brand_profile and "colors" in brand_profile:
        colors = brand_profile["colors"]
        if "primary" in colors:
            merged_props["accent_color"] = colors["primary"]
        if "background" in colors:
            merged_props["bg_color"] = colors["background"]
        if "text" in colors:
            merged_props["text_color"] = colors["text"]
            
    if props:
        merged_props.update(props)
        
    actual_duration = float(duration if duration is not None and duration > 0 else meta["default_duration"])
    
    # Đọc template gốc
    template_file = PRESETS_DIR / meta["template_file"]
    if not template_file.is_file():
        raise FileNotFoundError(f"Không tìm thấy file template preset: {template_file}")
        
    html_content = template_file.read_text(encoding="utf-8")
    
    # Chuẩn bị mã nhúng GSAP (ưu tiên nhúng offline nếu có bundle cục bộ, ngược lại dùng CDN fallback)
    gsap_script_tag = '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>'
    if LOCAL_GSAP_PATH.is_file():
        # Dùng relative path tới local node_modules hoặc nhúng trực tiếp nếu cần
        try:
            rel_path = os.path.relpath(LOCAL_GSAP_PATH, template_file.parent)
            gsap_script_tag = f'<script src="{rel_path}"></script>'
        except ValueError:
            pass
            
    # Tính toán aspect ratio
    aspect_ratio_str = f"{width}/{height}"
    
    # Thay thế placeholders cấu trúc
    html_content = html_content.replace("__GSAP_SCRIPT_TAG__", gsap_script_tag)
    html_content = html_content.replace("__DURATION__", str(actual_duration))
    html_content = html_content.replace("__WIDTH__", str(width))
    html_content = html_content.replace("__HEIGHT__", str(height))
    html_content = html_content.replace("__ASPECT_RATIO__", aspect_ratio_str)
    html_content = html_content.replace("__PROPS_JSON__", json.dumps(merged_props, ensure_ascii=False))

    # Tự động chèn meta tags chuẩn HyperFrames và CSS variables độ phân giải vào <head>
    resolution_meta = (
        f'  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'  <meta name="hf:width" content="{width}">\n'
        f'  <meta name="hf:height" content="{height}">\n'
        f'  <meta name="hf:aspect-ratio" content="{aspect_ratio_str}">\n'
        f'  <style>\n'
        f'    :root {{\n'
        f'      --render-width: {width}px;\n'
        f'      --render-height: {height}px;\n'
        f'      --render-aspect: {aspect_ratio_str};\n'
        f'    }}\n'
        f'  </style>'
    )
    if "<head>" in html_content:
        html_content = html_content.replace("<head>", f"<head>\n{resolution_meta}", 1)

    # Đảm bảo có root container data-composition-id cho HyperFrames runtime
    if 'data-composition-id=' not in html_content:
        html_content = html_content.replace(
            "<body>",
            f'<body>\n  <div id="hf-root" data-composition-id="main" data-start="0" data-duration="{actual_duration}" data-width="{width}" data-height="{height}" style="width:100%;height:100%;position:relative;overflow:hidden;">',
            1
        )
        html_content = html_content.replace("</body>", "  </div>\n</body>", 1)

    # Tự động đăng ký GSAP timeline vào window.__timelines["main"] nếu template dùng const tl
    if "window.__timelines" not in html_content and "const tl" in html_content:
        timeline_reg = (
            f"\n    // HyperFrames runtime timeline hook\n"
            f"    window.__timelines = window.__timelines || {{}};\n"
            f"    window.__timelines['main'] = tl;\n"
            f"    if (typeof tl.seek === 'function') tl.seek(0);\n"
        )
        html_content = html_content.replace("</script>", f"{timeline_reg}  </script>", 1)

    return html_content
