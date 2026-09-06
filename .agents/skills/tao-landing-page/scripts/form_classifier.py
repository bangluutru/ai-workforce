#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
form_classifier.py — Bộ Phân Loại & Ánh Xạ Form cho tao-landing-page
Xác định loại form (lead / order / custom) dựa trên trường nhập liệu và nút kêu gọi hành động (CTA).
Ánh xạ chính xác theo Landing Hub Integration Contract v1.0.
"""

import sys
import json
import argparse

def classify_form(form_data: dict, surrounding_cta: str = "") -> dict:
    """
    Phân loại form từ dữ liệu section hoặc fields:
    - order: có sản phẩm, số lượng, tổng tiền, hoặc địa chỉ giao hàng
    - lead: có thông tin liên hệ, nhận tư vấn, nhận quà tặng
    - custom: có câu hỏi trắc nghiệm, điểm số, tính toán
    """
    fields = form_data.get("fields", [])
    field_keys = [str(f.get("key", "")).lower() for f in fields]
    form_title = form_data.get("title", "") or form_data.get("formTitle", "")
    full_context = (form_title + " " + surrounding_cta + " " + " ".join(field_keys)).lower()

    # 1. Kiểm tra dấu hiệu Order Form
    order_indicators = [
        "regularprice", "saleprice", "items", "productname", "quantity", 
        "giá", "đặt hàng", "mua ngay", "order", "thanh toán", "cod", "phương thức thanh toán"
    ]
    has_order_sign = any(ind in full_context for ind in order_indicators)
    has_address = any("address" in k or "địa chỉ" in k for k in field_keys)
    
    if has_order_sign and has_address:
        return {
            "form_type": "order",
            "endpoint": "/api/order",
            "sdk_method": "LPHub.submitOrder",
            "reason": "Phát hiện thông tin đặt hàng gồm địa chỉ giao nhận và giá/sản phẩm.",
            "fields": fields,
            "sample_payload_schema": {
                "formId": "string",
                "customer": { "name": "string", "phone": "string", "address": "string", "note": "string" },
                "items": [{ "name": "string", "quantity": 1, "price": 0 }],
                "total": 0,
                "currency": "VND",
                "paymentMethod": "cod"
            }
        }

    # 2. Kiểm tra dấu hiệu Custom Form (Quiz / Survey / Calculator)
    custom_indicators = [
        "quiz", "khảo sát", "chẩn đoán", "survey", "score", "điểm", "mục tiêu",
        "calculator", "tính toán", "trắc nghiệm", "phác đồ"
    ]
    has_custom_sign = any(ind in full_context for ind in custom_indicators)
    if has_custom_sign and not has_order_sign:
        return {
            "form_type": "custom",
            "endpoint": "/api/custom-form",
            "sdk_method": "LPHub.submitCustomForm",
            "reason": "Phát hiện form trắc nghiệm / chẩn đoán / tính toán số liệu đa bước.",
            "fields": fields,
            "sample_payload_schema": {
                "formId": "string",
                "data": {}
            }
        }

    # 3. Mặc định: Lead Form (Tư vấn, Nhận tin, Đăng ký quà)
    return {
        "form_type": "lead",
        "endpoint": "/api/lead",
        "sdk_method": "LPHub.submitLead",
        "reason": "Phát hiện form tư vấn hoặc đăng ký nhận quà/thông tin liên hệ.",
        "fields": fields,
        "sample_payload_schema": {
            "formId": "string",
            "name": "string",
            "phone": "string",
            "email": "string",
            "data": {}
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Bộ phân loại form cho tao-landing-page")
    parser.add_argument("--json-input", help="Chuỗi JSON đặc tả form hoặc đường dẫn file")
    parser.add_argument("--cta", default="", help="Text của nút CTA xung quanh")
    args = parser.parse_args()

    form_dict = {}
    if args.json_input:
        try:
            if args.json_input.endswith('.json'):
                with open(args.json_input, 'r', encoding='utf-8') as f:
                    form_dict = json.load(f)
            else:
                form_dict = json.loads(args.json_input)
        except Exception as e:
            print(f"Lỗi đọc JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Form mặc định để test
        form_dict = {
            "title": "Đăng ký nhận quà",
            "fields": [
                {"key": "name", "label": "Họ và tên"},
                {"key": "phone", "label": "Số điện thoại"},
                {"key": "address", "label": "Địa chỉ"}
            ]
        }

    result = classify_form(form_dict, args.cta)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
