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
# KHÔNG có token mặc định. Token quản trị lấy từ --token hoặc biến môi trường LPHUB_ADMIN_TOKEN.

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
    token: str = "",
    lp_url: str = "",
    allowed_domains: list = None,
    dry_run: bool = False
) -> dict:
    """
    Thực hiện kiểm tra và đăng ký an toàn:
    1. Kiểm tra health của server Landing Hub
    2. Kiểm tra/Tạo Project
    3. Kiểm tra/Tạo Landing Page
    4. Kiểm tra/Tạo Form Definition
    """
    api_url = api_url.rstrip('/')

    planned = {
        "project": {"code": project_id.upper(), "name": project_name or project_id,
                    "allowedDomains": allowed_domains or []},
        "landing_page": {"name": landing_page_title or landing_page_id, "url": lp_url},
        "form": {"name": f"Form {form_type.capitalize()} {form_id}", "type": form_type, "fields": form_fields},
    }
    if dry_run:
        return {"success": True, "dry_run": True, "api_url": api_url,
                "message": "DRY RUN - không gửi request nào. Đây là dữ liệu sẽ đăng ký lên Landing Hub.",
                "planned_requests": planned}
    if not token:
        return {"success": False, "error": "MISSING_TOKEN",
                "message": "Thiếu token quản trị: truyền --token hoặc đặt LPHUB_ADMIN_TOKEN (không có token mặc định)."}
    if not lp_url:
        return {"success": False, "error": "MISSING_LP_URL", "message": "Thiếu --lp-url (URL thật của landing page)."}

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
                "allowedDomains": allowed_domains or []
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
                "url": lp_url,
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

    # Chỉ khớp theo đúng formId - KHÔNG tái dùng form khác chỉ vì cùng loại
    target_form = next((f for f in existing_forms if f.get("id") == form_id), None)
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
    parser.add_argument("--token", default=os.environ.get("LPHUB_ADMIN_TOKEN", ""), help="Bearer token quản trị (hoặc env LPHUB_ADMIN_TOKEN)")
    parser.add_argument("--fields-json", default="[]", help="JSON danh sách trường dữ liệu của form")
    parser.add_argument("--lp-url", default="", help="URL công khai của landing page")
    parser.add_argument("--allowed-domain", action="append", default=[], help="Domain được phép gửi form (lặp lại được)")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in dữ liệu sẽ gửi, không gọi API")
    parser.add_argument("--output", help="Ghi kết quả (hub_config.json) ra file khi thành công")
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
        token=args.token,
        lp_url=args.lp_url,
        allowed_domains=args.allowed_domain,
        dry_run=args.dry_run
    )

    print(json.dumps(res, ensure_ascii=False, indent=2))
    if args.output and res.get("success") and not res.get("dry_run"):
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=2)
    sys.exit(0 if res["success"] else 1)

if __name__ == "__main__":
    main()
