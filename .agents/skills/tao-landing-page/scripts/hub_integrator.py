#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hub_integrator.py — Tích Hợp & Đăng Ký Thực Thể Landing Hub v1.0
Kiểm tra và đăng ký projectId -> landingPageId -> formId trên Landing Hub Ingestion / Admin API.
Tuân thủ nghiêm ngặt Landing Hub Integration Contract v1.0.
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

DEFAULT_API_URL = "http://localhost:3001"
DEFAULT_TEST_TOKEN = "test-super_admin"

def make_request(url: str, method: str = "GET", data: dict = None, token: str = None) -> dict:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    encoded_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {"success": True, "status": resp.status}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return json.loads(body)
        except Exception:
            return {"success": False, "error": {"code": f"HTTP_{e.code}", "message": str(e)}}
    except Exception as e:
        return {"success": False, "error": {"code": "CONNECTION_ERROR", "message": str(e)}}

def verify_and_register_hierarchy(
    api_url: str,
    project_id: str,
    project_name: str,
    landing_page_id: str,
    landing_page_title: str,
    form_id: str,
    form_type: str,
    form_fields: list,
    token: str = DEFAULT_TEST_TOKEN
) -> dict:
    """
    Thực hiện kiểm tra và đăng ký an toàn:
    1. Kiểm tra health của server Landing Hub
    2. Kiểm tra/Tạo Project
    3. Kiểm tra/Tạo Landing Page
    4. Kiểm tra/Tạo Form Definition
    """
    api_url = api_url.rstrip('/')

    # 1. Health Probe
    health = make_request(f"{api_url}/api/health")
    if not health.get("status") == "ok":
        return {
            "success": False,
            "error": "HUB_UNREACHABLE",
            "message": f"Không thể kết nối đến Landing Hub API tại {api_url}. Hãy chắc chắn server đang chạy (npm run server trong thư mục landing-hub).",
            "details": health
        }

    # 2. Kiểm tra/Tạo Project
    projects_res = make_request(f"{api_url}/api/projects", token=token)
    existing_projects = projects_res.get("data", []) if isinstance(projects_res.get("data"), list) else []
    
    target_project = next((p for p in existing_projects if p.get("id") == project_id or p.get("code") == project_id.upper()), None)
    if not target_project:
        # Đăng ký mới project
        create_p = make_request(
            f"{api_url}/api/projects",
            method="POST",
            data={
                "code": project_id.upper(),
                "name": project_name or project_id.capitalize(),
                "description": f"Dự án {project_name or project_id}",
                "allowedDomains": ["localhost", "127.0.0.1", f"{project_id}.vn", f"{project_id}.pages.dev"]
            },
            token=token
        )
        if not create_p.get("success"):
            return {
                "success": False,
                "error": "PROJECT_REGISTRATION_FAILED",
                "message": f"Không thể tạo dự án {project_id}: {create_p.get('error', {}).get('message')}"
            }
        target_project = create_p.get("data", {})

    actual_project_id = target_project.get("id", project_id)

    # 3. Kiểm tra/Tạo Landing Page
    lps_res = make_request(f"{api_url}/api/landing-pages?projectId={actual_project_id}", token=token)
    existing_lps = lps_res.get("data", []) if isinstance(lps_res.get("data"), list) else []
    
    target_lp = next((lp for lp in existing_lps if lp.get("id") == landing_page_id or lp.get("name") == landing_page_title), None)
    if not target_lp:
        lp_name = landing_page_title or landing_page_id
        create_lp = make_request(
            f"{api_url}/api/landing-pages",
            method="POST",
            data={
                "projectId": actual_project_id,
                "name": lp_name,
                "url": "http://localhost:3000",
                "description": f"Trang đích cho {actual_project_id}"
            },
            token=token
        )
        if not create_lp.get("success"):
            return {
                "success": False,
                "error": "LP_REGISTRATION_FAILED",
                "message": f"Không thể tạo landing page: {create_lp.get('error', {}).get('message')}"
            }
        target_lp = create_lp.get("data", {})

    actual_lp_id = target_lp.get("id", landing_page_id)

    # 4. Kiểm tra/Tạo Form Definition
    forms_res = make_request(f"{api_url}/api/forms?projectId={actual_project_id}&landingPageId={actual_lp_id}", token=token)
    existing_forms = forms_res.get("data", []) if isinstance(forms_res.get("data"), list) else []

    target_form = next((f for f in existing_forms if f.get("id") == form_id or f.get("type") == form_type), None)
    if not target_form:
        formatted_fields = []
        for fld in form_fields:
            formatted_fields.append({
                "key": fld.get("key", "field"),
                "label": fld.get("label", fld.get("key")),
                "type": fld.get("type", "text"),
                "required": bool(fld.get("required", False))
            })

        create_form = make_request(
            f"{api_url}/api/forms",
            method="POST",
            data={
                "projectId": actual_project_id,
                "landingPageId": actual_lp_id,
                "name": f"Form {form_type.capitalize()} {form_id}",
                "type": form_type,
                "fields": formatted_fields
            },
            token=token
        )
        if not create_form.get("success"):
            return {
                "success": False,
                "error": "FORM_REGISTRATION_FAILED",
                "message": f"Không thể tạo form schema: {create_form.get('error', {}).get('message')}"
            }
        target_form = create_form.get("data", {})

    actual_form_id = target_form.get("id", form_id)

    return {
        "success": True,
        "message": f"Đăng ký phân cấp Landing Hub thành công: {actual_project_id} -> {actual_lp_id} -> {actual_form_id}",
        "config": {
            "projectId": actual_project_id,
            "landingPageId": actual_lp_id,
            "formId": actual_form_id,
            "formType": form_type,
            "apiUrl": api_url
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Đăng ký Landing Hub cho tao-landing-page")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="Base URL của Landing Hub API")
    parser.add_argument("--project-id", required=True, help="Mã định danh dự án (e.g. genki-fami, abano)")
    parser.add_argument("--project-name", default="", help="Tên hiển thị dự án")
    parser.add_argument("--lp-id", required=True, help="Mã landing page (e.g. abano-serum-promo)")
    parser.add_argument("--lp-title", default="", help="Tiêu đề landing page")
    parser.add_argument("--form-id", required=True, help="Mã form định nghĩa (e.g. abano-lead-form-01)")
    parser.add_argument("--form-type", choices=["lead", "order", "custom"], default="lead", help="Loại form")
    parser.add_argument("--token", default=DEFAULT_TEST_TOKEN, help="Bearer token quản trị")
    parser.add_argument("--fields-json", default="[]", help="JSON danh sách trường dữ liệu của form")
    args = parser.parse_args()

    try:
        fields = json.loads(args.fields_json)
    except Exception:
        fields = []

    res = verify_and_register_hierarchy(
        api_url=args.api_url,
        project_id=args.project_id,
        project_name=args.project_name,
        landing_page_id=args.lp_id,
        landing_page_title=args.lp_title,
        form_id=args.form_id,
        form_type=args.form_type,
        form_fields=fields,
        token=args.token
    )

    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(0 if res["success"] else 1)

if __name__ == "__main__":
    main()
