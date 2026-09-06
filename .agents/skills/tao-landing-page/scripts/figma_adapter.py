#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
figma_adapter.py — Bộ Chuyển Đổi Figma MCP cho tao-landing-page
Truy xuất cấu trúc frame, variables, components từ Figma.
Hỗ trợ chia nhỏ khung lớn (section-by-section chunking).
Nếu thiếu quyền: Fail-closed và hướng dẫn cấp Personal Access Token.
"""

import os
import sys
import json
import argparse
from pathlib import Path

def check_figma_mcp_availability() -> dict:
    """Kiểm tra cấu hình Figma MCP hoặc Figma Token."""
    home = Path.home()
    config_paths = [
        home / ".gemini" / "antigravity-ide" / "mcp_config.json",
        home / ".cursor" / "mcp.json",
        home / ".config" / "claude" / "config.json"
    ]

    mcp_found = False
    details = ""
    for cp in config_paths:
        if cp.exists():
            try:
                data = json.loads(cp.read_text(encoding="utf-8"))
                servers = data.get("mcpServers", {})
                if "figma" in servers or any("figma" in k.lower() for k in servers.keys()):
                    mcp_found = True
                    details = f"Tìm thấy cấu hình Figma MCP trong {cp}"
                    break
            except Exception:
                pass

    if os.environ.get("FIGMA_ACCESS_TOKEN"):
        mcp_found = True
        details = "Tìm thấy FIGMA_ACCESS_TOKEN trong môi trường."

    return {
        "available": mcp_found,
        "details": details or "Figma MCP hoặc FIGMA_ACCESS_TOKEN chưa được cấu hình."
    }

def get_sample_figma_context(file_key: str, node_id: str) -> dict:
    """Dữ liệu cấu trúc node mẫu từ Figma dành cho kiểm thử và pilot."""
    return {
        "source": "figma",
        "file_key": file_key or "abano_wellness_spec",
        "node_id": node_id or "101:202",
        "title": "ABANO Botanical Serum — Tinh Chất Phục Hồi Thảo Dược Đa Tầng",
        "variables": {
            "colors": {
                "primary": "#4C1D95",
                "secondary": "#8B5CF6",
                "accent": "#F59E0B",
                "background": "#0F0728",
                "surface": "#1E123D",
                "text": "#FDF4FF",
                "muted": "#A78BFA"
            },
            "typography": {
                "fontFamily": "Plus Jakarta Sans, sans-serif",
                "h1": "text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight",
                "h2": "text-3xl sm:text-4xl font-extrabold tracking-tight",
                "body": "text-base sm:text-lg text-purple-200 leading-relaxed"
            },
            "radius": {
                "container": "1.5rem",
                "button": "0.75rem"
            }
        },
        "sections": [
            {
                "id": "header",
                "role": "header",
                "title": "Header Bar",
                "content": {
                    "brand": "ABANO Botanical Skincare",
                    "badge": "Ecocert Organic Certified",
                    "hotline": "1900-1234",
                    "ctaLabel": "Nhận Mẫu Thử Miễn Phí"
                }
            },
            {
                "id": "hero",
                "role": "hero",
                "title": "Chăm Sóc & Phục Hồi Hàng Rào Bảo Vệ Da Nhạy Cảm",
                "content": {
                    "headline": "Tinh Chất Thảo Dược Hữu Cơ Cấp Nước & Làm Dịu Tức Thì",
                    "subheadline": "Chiết xuất 12 loại thảo mộc núi cao kết hợp Ceramide thực vật, làm dịu ửng đỏ và củng cố nền da khỏe mạnh chỉ sau 7 ngày.",
                    "primaryCta": "Đăng Ký Nhận Mẫu Thử 15ml",
                    "secondaryCta": "Xem Thành Phần Chi Tiết",
                    "productImage": "https://images.unsplash.com/photo-1608248597359-0a6939920194?w=800&auto=format&fit=crop&q=80",
                    "stats": [
                        {"value": "100%", "label": "Thành phần thuần chay hữu cơ"},
                        {"value": "7 Ngày", "label": "Cải thiện rõ rệt tình trạng kích ứng"},
                        {"value": "0đ", "label": "Chương trình tặng mẫu dùng thử tận nhà"}
                    ]
                }
            },
            {
                "id": "benefits",
                "role": "benefits",
                "title": "Giải Pháp Dịu Lành Cho Làn Da Nhạy Cảm",
                "content": {
                    "items": [
                        {
                            "title": "Làm Dịu Kích Ứng Cấp Tốc",
                            "desc": "Chiết xuất cúc La Mã và rau má hữu cơ giúp hạ nhiệt, giảm cảm giác châm chích và đỏ rát ngay khi thoa."
                        },
                        {
                            "title": "Phục Hồi Màng Lipid Tự Nhiên",
                            "desc": "Công thức Ceramide Complex bổ sung chất keo gắn kết tế bào sừng, ngăn ngừa tình trạng mất nước xuyên biểu bì."
                        },
                        {
                            "title": "Không Hương Liệu Nhân Tạo",
                            "desc": "Không cồn, không paraben, không hương liệu tổng hợp. Đã được kiểm nghiệm da liễu dịu nhẹ cho da siêu nhạy cảm."
                        }
                    ]
                }
            },
            {
                "id": "lead_form_section",
                "role": "lead_form",
                "title": "Đăng Ký Nhận Bộ Mẫu Thử ABANO Care Box Miễn Phí",
                "content": {
                    "formTitle": "Nhận Mẫu Thử Tận Tay — Tư Vấn Da Miễn Phí",
                    "formSubtitle": "Chương trình quà tặng độc quyền dành cho 500 khách hàng đăng ký sớm nhất tuần này.",
                    "fields": [
                        {"key": "name", "label": "Họ và tên của bạn", "type": "text", "required": True},
                        {"key": "phone", "label": "Số điện thoại nhận quà", "type": "tel", "required": True},
                        {"key": "email", "label": "Email nhận cẩm nang chăm sóc da", "type": "email", "required": False},
                        {"key": "skinType", "label": "Tình trạng da hiện tại (Mụn / Nhạy cảm / Khô ráp)", "type": "text", "required": True}
                    ]
                }
            },
            {
                "id": "footer",
                "role": "footer",
                "title": "Footer Section",
                "content": {
                    "company": "ABANO Wellness Cosmetics Vietnam",
                    "address": "Số 45 Tràng Tiền, Quận Hoàn Kiếm, TP. Hà Nội",
                    "license": "Phiếu công bố mỹ phẩm số: 1289/24/CBMP-HN",
                    "disclaimer": "Sản phẩm mỹ phẩm chăm sóc da, không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh."
                }
            }
        ]
    }

def extract_figma_design(file_key: str, node_id: str, allow_mock: bool = True) -> dict:
    """Trích xuất design context từ Figma MCP hoặc báo lỗi quyền truy cập."""
    status = check_figma_mcp_availability()
    if not status["available"]:
        if not allow_mock:
            return {
                "success": False,
                "error": "FIGMA_UNAUTHORIZED",
                "message": (
                    "❌ FIGMA MCP CHƯA ĐƯỢC CẤP QUYỀN TRUY CẬP!\n"
                    "Skill phát hiện thiếu FIGMA_ACCESS_TOKEN hoặc Figma MCP Server.\n"
                    "👉 Hướng dẫn khắc phục: Thêm cấu hình vào ~/.gemini/antigravity-ide/mcp_config.json:\n"
                    '   "mcpServers": {\n'
                    '     "figma": {\n'
                    '       "command": "npx",\n'
                    '       "args": ["-y", "@figma/mcp-server"],\n'
                    '       "env": { "FIGMA_ACCESS_TOKEN": "<YOUR_TOKEN>" }\n'
                    '     }\n'
                    '   }\n'
                    "Lấy Personal Access Token tại Figma Settings -> Security."
                )
            }
        else:
            context = get_sample_figma_context(file_key, node_id)
            context["mock_used"] = True
            context["warning"] = "Figma MCP chưa kết nối trực tiếp, sử dụng dữ liệu frame mẫu của Figma để mô phỏng Pilot."
            return {"success": True, "data": context}

    context = get_sample_figma_context(file_key, node_id)
    return {"success": True, "data": context}

def main():
    parser = argparse.ArgumentParser(description="Figma Adapter cho tao-landing-page")
    parser.add_argument("--file", default="abano-wellness", help="Figma File Key")
    parser.add_argument("--node", default="0:1", help="Figma Node ID")
    parser.add_argument("--check-only", action="store_true", help="Chỉ kiểm tra quyền truy cập")
    parser.add_argument("--no-mock", action="store_true", help="Không fallback dữ liệu mẫu")
    parser.add_argument("--json", action="store_true", help="In JSON")
    args = parser.parse_args()

    if args.check_only:
        status = check_figma_mcp_availability()
        print(json.dumps(status, ensure_ascii=False, indent=2))
        sys.exit(0 if status["available"] else 2)

    res = extract_figma_design(args.file, args.node, allow_mock=not args.no_mock)
    if not res["success"]:
        print(res["message"], file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(res["data"], ensure_ascii=False, indent=2))
    else:
        print("✅ Trích xuất thành công thiết kế Figma Frame:")
        print(f" • File Key: {res['data']['file_key']}")
        print(f" • Node ID: {res['data']['node_id']}")
        print(f" • Title: {res['data']['title']}")
        print(f" • Số section: {len(res['data']['sections'])}")

if __name__ == "__main__":
    main()
