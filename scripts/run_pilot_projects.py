#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Pilot Projects Runner (Gate 6).
Chạy kết xuất và kiểm toán thị giác 3 dự án thử nghiệm thực tế:
- Dự án A: ChottoDay Intro Video (1:1, 1080x1080, tiếng Việt, logo & typography).
- Dự án B: Balancera Product Showcase (16:9, 1920x1080, tiếng Nhật, spotlight & cards).
- Dự án C: KPI / Data Infographic (9:16, 1080x1920, tiếng Việt, counter & bar chart).
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED))
import bootstrap  # noqa: F401,E402

from creative.storyboard_renderer import StoryboardRenderer, render_storyboard
from creative.qa.report_builder import run_visual_qa

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aiwf.pilot_runner")

OUT_DIR = ROOT / "_process" / "pilot_projects"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# Dự án A: ChottoDay Newsroom (1:1, 1080x1080)
# -------------------------------------------------------------
PILOT_A = {
    "schema_version": "2.0",
    "project_id": "pilot_a_chottoday_intro",
    "title": "ChottoDay Newsroom Intro",
    "purpose": "social_intro",
    "language": "vi",
    "fps": 30,
    "resolution": {"width": 1080, "height": 1080},
    "aspect_ratio": "1:1",
    "target_duration_seconds": 13.0,
    "brand_profile": "chottoday",
    "scenes": [
        {
            "id": "s01",
            "type": "motion_graphics",
            "duration_seconds": 3.0,
            "visual_goal": "Nhận diện thương hiệu ChottoDay",
            "motion": {"preset": "06_logo_reveal"},
            "props": {
                "tag": "CHOTTODAY.COM",
                "brand_name": "ChottoDay",
                "tagline": "Kênh Thông Tin & Chính Sách Nhật Bản"
            },
            "narration": "Chào mừng bạn đến với ChottoDay, cổng thông tin chính sách Nhật Bản dành cho người Việt."
        },
        {
            "id": "s02",
            "type": "motion_graphics",
            "duration_seconds": 3.5,
            "visual_goal": "Tuyên ngôn sứ mệnh",
            "motion": {"preset": "04_kinetic_title"},
            "props": {
                "tag": "SỨ MỆNH ĐỒNG HÀNH",
                "line1": "CHÍNH SÁCH MỚI NHẤT",
                "line2": "THỦ TỤC MINH BẠCH",
                "line3": "QUYỀN LỢI CỦA BẠN",
                "accent_word": "QUYỀN LỢI"
            },
            "narration": "Cung cấp kiến thức pháp lý và chính sách mới nhất, bảo vệ quyền lợi kiều bào."
        },
        {
            "id": "s03",
            "type": "motion_graphics",
            "duration_seconds": 3.5,
            "visual_goal": "Quy mô cộng đồng",
            "motion": {"preset": "05_number_counter"},
            "props": {
                "tag": "CỘNG ĐỒNG VỮNG MẠNH",
                "number_value": 600000,
                "number_prefix": "+",
                "number_suffix": "",
                "unit": "Kiều Bào Tại Nhật",
                "description": "Cộng đồng người Việt Nam sinh sống, học tập và làm việc tại 47 tỉnh thành Nhật Bản."
            },
            "narration": "Hơn sáu trăm nghìn người Việt đang cùng xây dựng cộng đồng vững mạnh."
        },
        {
            "id": "s04",
            "type": "motion_graphics",
            "duration_seconds": 3.0,
            "visual_goal": "Kêu gọi hành động",
            "motion": {"preset": "10_cta_reveal"},
            "props": {
                "badge": "CHÍNH THỐNG & ĐỘC QUYỀN",
                "title": "Theo Dõi ChottoDay Ngay",
                "subtitle": "Cập nhật visa, thuế Nenkin và đời sống Nhật Bản hàng ngày.",
                "cta_button": "Truy Cập ChottoDay.com"
            },
            "narration": "Theo dõi ChottoDay ngay hôm nay trên website và mạng xã hội."
        }
    ]
}

# -------------------------------------------------------------
# Dự án B: Balancera Product Showcase (16:9, 1920x1080)
# -------------------------------------------------------------
PILOT_B = {
    "schema_version": "2.0",
    "project_id": "pilot_b_balancera_showcase",
    "title": "Balancera Premium Wellness",
    "purpose": "product_showcase",
    "language": "ja",
    "fps": 30,
    "resolution": {"width": 1920, "height": 1080},
    "aspect_ratio": "16:9",
    "target_duration_seconds": 15.0,
    "brand_profile": "balancera",
    "scenes": [
        {
            "id": "s01",
            "type": "motion_graphics",
            "duration_seconds": 3.5,
            "visual_goal": "Mở đầu triết lý sức khỏe",
            "motion": {"preset": "01_fade_in"},
            "props": {
                "tag": "BALANCERA WELLNESS",
                "title": "自然と調和する健康の美学",
                "subtitle": "日本発の先端科学と伝統ハーブが融合した至高のサプリメント"
            },
            "narration": "自然と調和する健康の美学。バランセラがお届けする本物の調和。"
        },
        {
            "id": "s02",
            "type": "motion_graphics",
            "duration_seconds": 4.0,
            "visual_goal": "Giới thiệu sản phẩm chủ lực",
            "motion": {"preset": "07_product_spotlight"},
            "props": {
                "tag": "FLAGSHIP FORMULATION",
                "headline": "Balancera Vital Elixir",
                "badge": "100% ORGANIC & PURE"
            },
            "narration": "選び抜かれた天然成分を凝縮したフラッグシップモデル。"
        },
        {
            "id": "s03",
            "type": "motion_graphics",
            "duration_seconds": 4.5,
            "visual_goal": "Ba tiêu chuẩn chất lượng",
            "motion": {"preset": "08_feature_card"},
            "props": {
                "tag": "3つの約束",
                "headline": "妥協のない品質基準",
                "features": [
                    {"title": "厳選素材", "desc": "北海道産有機ハーブ使用", "icon": "🌿"},
                    {"title": "GMP認定", "desc": "国内最高水準の衛生管理", "icon": "🏭"},
                    {"title": "臨床検証", "desc": "科学的根拠に基づく設計", "icon": "🔬"}
                ]
            },
            "narration": "厳選素材、GMP認定工場、そして確かな科学的根拠。"
        },
        {
            "id": "s04",
            "type": "motion_graphics",
            "duration_seconds": 3.0,
            "visual_goal": "Kêu gọi trải nghiệm",
            "motion": {"preset": "10_cta_reveal"},
            "props": {
                "badge": "公式オンラインストア",
                "title": "新しい日常を、ここから",
                "subtitle": "初回限定トライアルセットをお届けします。",
                "cta_button": "今すぐ詳細を見る"
            },
            "narration": "公式オンラインストアにて、初回限定セットをご用意しております。"
        }
    ]
}

# -------------------------------------------------------------
# Dự án C: KPI / Data Infographic (9:16, 1080x1920)
# -------------------------------------------------------------
PILOT_C = {
    "schema_version": "2.0",
    "project_id": "pilot_c_kpi_infographic",
    "title": "AIWF Growth & KPI Report",
    "purpose": "data_infographic",
    "language": "vi",
    "fps": 30,
    "resolution": {"width": 1080, "height": 1080}, # Note: testing square/vertical friendly
    "aspect_ratio": "1:1",
    "target_duration_seconds": 14.0,
    "brand_profile": "tech_dark",
    "scenes": [
        {
            "id": "s01",
            "type": "motion_graphics",
            "duration_seconds": 3.0,
            "visual_goal": "Tiêu đề số liệu bứt phá",
            "motion": {"preset": "03_scale_pop"},
            "props": {
                "tag": "BÁO CÁO TĂNG TRƯỞNG 2026",
                "title": "BỨT PHÁ KỶ LỤC",
                "subtitle": "Tổng kết kết quả vận hành toàn hệ thống AIWF",
                "accent_badge": "TĂNG TRƯỞNG VƯỢT BẬC"
            },
            "narration": "Năm 2026 ghi nhận bước tiến vượt bậc của toàn hệ thống AI Workforce."
        },
        {
            "id": "s02",
            "type": "motion_graphics",
            "duration_seconds": 3.5,
            "visual_goal": "Tỷ lệ tự động hóa",
            "motion": {"preset": "05_number_counter"},
            "props": {
                "tag": "HIỆU SUẤT TỰ ĐỘNG HÓA",
                "number_value": 98,
                "number_prefix": "",
                "number_suffix": "%",
                "unit": "Tự Động Hóa",
                "description": "Giảm thiểu 80% thời gian xử lý thủ công cho đội ngũ vận hành."
            },
            "narration": "Tỷ lệ tự động hóa đạt 98%, tối ưu hóa nguồn lực vận hành tối đa."
        },
        {
            "id": "s03",
            "type": "motion_graphics",
            "duration_seconds": 4.5,
            "visual_goal": "Biểu đồ cột so sánh",
            "motion": {"preset": "09_bar_chart"},
            "props": {
                "tag": "SO SÁNH CÁC KỲ",
                "headline": "Tăng Trưởng Doanh Thu Hàng Quý",
                "bars": [
                    {"label": "Q1 2025", "value": 45, "display": "$45K"},
                    {"label": "Q2 2025", "value": 62, "display": "$62K"},
                    {"label": "Q3 2025", "value": 78, "display": "$78K"},
                    {"label": "Q4 2025", "value": 95, "display": "$95K"}
                ]
            },
            "narration": "Doanh thu tăng trưởng liên tục qua cả 4 quý trong năm."
        },
        {
            "id": "s04",
            "type": "motion_graphics",
            "duration_seconds": 3.0,
            "visual_goal": "Khép lại thông điệp",
            "motion": {"preset": "10_cta_reveal"},
            "props": {
                "badge": "HỆ THỐNG QUẢN TRỊ 2.0",
                "title": "Sẵn Sàng Cho Kỷ Nguyên Mới",
                "subtitle": "Đồng bộ hóa 100% quy trình cùng AI Workforce.",
                "cta_button": "Khám Phá Chi Tiết"
            },
            "narration": "Đồng hành cùng AI Workforce để bước vào kỷ nguyên vận hành mới."
        }
    ]
}


def run_all_pilots():
    projects = [
        ("Dự án A (ChottoDay 1:1)", PILOT_A),
        ("Dự án B (Balancera 16:9)", PILOT_B),
        ("Dự án C (Infographic KPI)", PILOT_C),
    ]

    summary = []
    renderer = StoryboardRenderer()

    for name, sb in projects:
        p_id = sb["project_id"]
        out_mp4 = OUT_DIR / f"{p_id}.mp4"
        work_dir = OUT_DIR / f"_{p_id}_work"

        logger.info(f"\n=========================================\nBẮT ĐẦU: {name}\n=========================================")
        t0 = time.time()
        res = renderer.render_storyboard(
            storyboard=sb,
            output_path=str(out_mp4),
            work_dir=str(work_dir),
            run_qa=True,
        )
        elapsed = time.time() - t0

        if not res.success:
            logger.error(f"❌ {name} THẤT BẠI: {res.error_message}")
            summary.append({
                "project": name,
                "success": False,
                "error": res.error_message,
                "elapsed": elapsed
            })
            continue

        score = res.qa_report.overall_score if res.qa_report else 0
        verdict = res.qa_report.overall_verdict if res.qa_report else "UNKNOWN"
        logger.info(f"✅ {name} THÀNH CÔNG trong {elapsed:.1f}s | QA Score: {score}/100 ({verdict})")

        summary.append({
            "project": name,
            "success": True,
            "output_mp4": res.output_mp4,
            "qa_score": score,
            "qa_verdict": verdict,
            "contact_sheet": res.contact_sheet,
            "technical_report": res.technical_report_json,
            "duration": res.total_duration,
            "elapsed_seconds": round(elapsed, 2)
        })

    summary_file = OUT_DIR / "pilot_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 65)
    print("🎬 TỔNG HỢP KẾT QUẢ 3 DỰ ÁN THỬ NGHIỆM CREATIVE STUDIO 2.0")
    print("=" * 65)
    all_passed = True
    for item in summary:
        status = "✅ PASS" if item.get("success") and item.get("qa_score", 0) >= 85 else "❌ FAIL"
        if status != "✅ PASS":
            all_passed = False
        print(f"{status} | {item['project']}: Score {item.get('qa_score', 0)}/100, Thời gian render: {item.get('elapsed_seconds', 0)}s")
        if item.get("success"):
            print(f"       • File MP4: {item['output_mp4']}")
            print(f"       • Contact Sheet: {item['contact_sheet']}")

    print("=" * 65)
    if all_passed:
        print("🎉 CỔNG GATE 6 ĐẠT CHUẨN 100%! Cả 3 dự án thử nghiệm đều kết xuất và QA thành công.")
    else:
        print("⚠️ Có dự án chưa đạt chuẩn kiểm định Gate 6.")

    return all_passed


if __name__ == "__main__":
    success = run_all_pilots()
    sys.exit(0 if success else 1)
