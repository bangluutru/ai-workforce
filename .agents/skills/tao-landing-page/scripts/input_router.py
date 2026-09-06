#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
input_router.py — Bộ Định Tuyến Đầu Vào cho Kỹ năng Tạo Landing Page (tao-landing-page)
Tự động nhận diện Stitch URL/ID, Figma URL/Node hoặc Fallback Image.
"""

import re
import sys
import json
import argparse
from urllib.parse import urlparse, parse_qs

def route_input(raw_input: str) -> dict:
    raw_input = raw_input.strip()

    # 1. Kiểm tra Google Stitch
    # Ví dụ: https://stitch.google.com/projects/proj-123/screens/screen-456
    # hoặc: stitch:proj-123/screen-456
    stitch_pattern = r"(?:https?://)?(?:www\.)?stitch\.(?:google|internal)\.com/projects/([a-zA-Z0-9_\-]+)(?:/screens/([a-zA-Z0-9_\-]+))?"
    stitch_short_pattern = r"^stitch:([a-zA-Z0-9_\-]+)(?:/([a-zA-Z0-9_\-]+))?$"
    
    m_stitch = re.search(stitch_pattern, raw_input) or re.search(stitch_short_pattern, raw_input)
    if m_stitch or "stitch" in raw_input.lower():
        project_id = m_stitch.group(1) if m_stitch else "sample-stitch-project"
        screen_id = m_stitch.group(2) if m_stitch and len(m_stitch.groups()) > 1 and m_stitch.group(2) else "screen-main"
        return {
            "adapter": "stitch",
            "raw_input": raw_input,
            "project_id": project_id,
            "screen_id": screen_id,
            "is_structured": True,
            "confidence": 1.0,
            "message": f"Nhận diện thành công Google Stitch (Project: {project_id}, Screen: {screen_id})"
        }

    # 2. Kiểm tra Figma
    # Ví dụ: https://www.figma.com/design/AbCdEf12345/My-Landing-Page?node-id=101-202
    # hoặc: https://www.figma.com/file/AbCdEf12345/...
    figma_pattern = r"figma\.com/(?:design|file)/([a-zA-Z0-9]+)(?:/[^?#]+)?(?:\?[^#]*node-id=([0-9%:\-]+))?"
    m_figma = re.search(figma_pattern, raw_input)
    if m_figma or "figma.com" in raw_input.lower():
        file_key = m_figma.group(1) if m_figma else "sample_figma_key"
        raw_node = m_figma.group(2) if m_figma and m_figma.group(2) else "0:1"
        node_id = raw_node.replace("%3A", ":").replace("-", ":")
        return {
            "adapter": "figma",
            "raw_input": raw_input,
            "file_key": file_key,
            "node_id": node_id,
            "is_structured": True,
            "confidence": 1.0,
            "message": f"Nhận diện thành công Figma Frame (FileKey: {file_key}, NodeId: {node_id})"
        }

    # 3. Fallback: Ảnh chụp màn hình / File ảnh
    image_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.svg')
    if any(raw_input.lower().endswith(ext) for ext in image_extensions) or raw_input.startswith("image:") or "screenshot" in raw_input.lower():
        return {
            "adapter": "fallback_image",
            "raw_input": raw_input,
            "is_structured": False,
            "confidence": 0.65,
            "flag": "[CẦN XÁC MINH - FIDELITY FALLBACK]",
            "message": "Nhận diện ảnh thiết kế tĩnh fallback. Độ trung thực về token và component có thể thấp hơn dữ liệu structured context từ Stitch/Figma MCP."
        }

    # Mặc định: Trả về fallback với cảnh báo
    return {
        "adapter": "fallback_image",
        "raw_input": raw_input,
        "is_structured": False,
        "confidence": 0.5,
        "flag": "[CẦN XÁC MINH - UNKNOWN INPUT FORMAT]",
        "message": f"Đầu vào '{raw_input}' không khớp URL chuẩn của Stitch hoặc Figma. Chuyển sang luồng phân tích thị giác fallback."
    }

def main():
    parser = argparse.ArgumentParser(description="Input Router cho tao-landing-page")
    parser.add_argument("input", help="URL Stitch, URL Figma hoặc đường dẫn ảnh thiết kế")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả dạng JSON")
    args = parser.parse_args()

    route = route_input(args.input)
    if args.json:
        print(json.dumps(route, ensure_ascii=False, indent=2))
    else:
        print(f"🎯 Adapter Được Chọn: {route['adapter'].upper()}")
        print(f"📌 Thông tin: {route['message']}")
        if "flag" in route:
            print(f"⚠️  Cảnh báo: {route['flag']}")

if __name__ == "__main__":
    main()
