#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
input_router.py — Bộ Định Tuyến Đầu Vào cho Kỹ năng Tạo Landing Page (tao-landing-page)
Tự động nhận diện Stitch URL/ID, Figma URL/Node, ảnh mockup hoặc brief dạng chữ.
Brief là TỆP (PDF/PPTX/DOCX/HTML/DOC/ODT/RTF/EPUB/XLSX/MD/TXT...) → chạy doc_ingest (cầu nối _shared) → text_brief
đọc từ source.md. Ảnh vẫn là fallback_image. Tệp không đọc được → adapter "unreadable" (mã thoát 2) hoặc
"missing_dependency" (mã thoát 4) kèm thông điệp nói rõ cần hỏi/cài gì.
"""

import re
import sys
import json
import argparse
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))   # .agents/skills/_shared
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.heic', '.heif', '.gif', '.bmp', '.tif', '.tiff')
DOC_EXTENSIONS = ('.pdf', '.pptx', '.ppt', '.odp', '.docx', '.doc', '.odt', '.rtf', '.epub', '.html', '.htm',
                  '.xlsx', '.xls', '.ods', '.csv', '.md', '.markdown', '.txt')
BRIEF_MSG = ("Brief dạng chữ. Agent tự lập landing_spec.json theo templates/landing_spec_example.json: "
             "chỉ dùng câu chữ/dữ kiện có trong brief, tự chọn bảng màu phù hợp brief (ghi lý do), "
             "mục thiếu -> [CẦN XÁC MINH: ...]. Sau đó chạy landing_builder.py --validate-only.")
NEXT_CMD = "python3 .agents/skills/tao-landing-page/scripts/landing_builder.py --spec <process_dir>/landing_spec.json --validate-only"


def _looks_like_path(raw: str) -> bool:
    return "\n" not in raw and len(raw) < 1024 and (raw.lower().endswith(DOC_EXTENSIONS) or raw.startswith(("/", "~", "./", "file://")))


def route_file_brief(raw_input: str, ingest_dir=None) -> dict:
    """Tệp brief → doc_ingest → text_brief (source.md). Không đọc được → unreadable/missing_dependency."""
    from doc_ingest_bridge import run_ingest, explain, ocr_page_paths, default_ingest_dir
    path = Path(raw_input[7:] if raw_input.startswith("file://") else raw_input).expanduser()
    if not path.is_file():
        return {"adapter": "unreadable", "raw_input": raw_input, "is_structured": False, "exit_code": 2,
                "flag": "[CẦN XÁC MINH - FILE NOT FOUND]",
                "message": f"Không tìm thấy tệp brief '{path}'. Hỏi người dùng đường dẫn đúng hoặc dán nội dung brief."}
    out = Path(ingest_dir).expanduser() if ingest_dir else default_ingest_dir(f"landing_{path.stem}")
    man = run_ingest(path, out)
    code = man.get("exit_code")
    base = {"raw_input": raw_input, "is_structured": False, "exit_code": code,
            "ingest": {"out_dir": man.get("out_dir"), "detected_format": man.get("detected_format"),
                       "warnings": man.get("warnings") or [], "chars": man.get("chars")},
            "ingest_message": explain(man, "tao-landing-page")}
    if code in (0, 3):
        r = dict(base, adapter="text_brief", brief_md=man.get("source_md_path"), message=BRIEF_MSG
                 + f" Đọc brief tại {man.get('source_md_path')} (không đọc thẳng tệp gốc).", next=NEXT_CMD)
        if code == 3:
            r["ocr_pages"] = ocr_page_paths(man)
            r["flag"] = "[CẦN XÁC MINH - OCR]"
            r["message"] += (" Có trang scan: đọc ảnh trong ocr_pages bằng thị giác; nháp OCR chưa kiểm chứng. "
                             "Nếu các trang là bản mockup thiết kế thì xử lý như fallback_image với các ảnh này.")
        return r
    return dict(base, adapter="missing_dependency" if code == 4 else "unreadable",
                flag="[CẦN XÁC MINH - UNREADABLE BRIEF]", message=base["ingest_message"])

def route_input(raw_input: str, ingest_dir=None) -> dict:
    raw_input = raw_input.strip()

    # 1. Kiểm tra Google Stitch
    # Ví dụ: https://stitch.withgoogle.com/projects/12679839070991793857
    # hoặc: https://stitch.google.com/projects/proj-123/screens/screen-456
    # hoặc: projects/12679839070991793857 hoặc stitch:12679839070991793857
    stitch_pattern = r"(?:https?://)?(?:www\.)?stitch\.(?:google|withgoogle|internal)\.com/projects/([a-zA-Z0-9_\-]+)(?:/screens/([a-zA-Z0-9_\-]+))?"
    stitch_short_pattern = r"^(?:stitch:|projects/)?([0-9]{10,25}|[a-zA-Z0-9_\-]+)(?:/screens?/([a-zA-Z0-9_\-]+))?$"
    
    m_stitch = re.search(stitch_pattern, raw_input) or re.search(stitch_short_pattern, raw_input)
    if m_stitch and ("stitch" in raw_input.lower() or "projects/" in raw_input or raw_input.isdigit()):
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
    if raw_input.lower().endswith(IMAGE_EXTENSIONS) or raw_input.startswith("image:") or "screenshot" in raw_input.lower():
        return {
            "adapter": "fallback_image",
            "raw_input": raw_input,
            "is_structured": False,
            "confidence": 0.65,
            "flag": "[CẦN XÁC MINH - FIDELITY FALLBACK]",
            "message": "Nhận diện ảnh thiết kế tĩnh fallback. Độ trung thực về token và component có thể thấp hơn dữ liệu structured context từ Stitch/Figma MCP."
        }

    # 4. Brief là tệp (PDF/PPTX/DOCX/HTML/DOC/ODT/RTF/EPUB/MD/TXT...) → doc_ingest → source.md
    if _looks_like_path(raw_input):
        return route_file_brief(raw_input, ingest_dir)

    # 5. Brief dạng chữ dán trực tiếp
    if len(raw_input.split()) >= 4:
        return {
            "adapter": "text_brief",
            "raw_input": raw_input,
            "is_structured": False,
            "message": BRIEF_MSG,
            "next": NEXT_CMD
        }

    # Mặc định: không nhận diện được -> hỏi lại người dùng thay vì đoán
    return {
        "adapter": "unknown",
        "raw_input": raw_input,
        "is_structured": False,
        "flag": "[CẦN XÁC MINH - UNKNOWN INPUT FORMAT]",
        "message": f"Đầu vào '{raw_input}' không phải URL Stitch/Figma, ảnh, hay brief chữ. Hỏi người dùng nguồn thiết kế/brief."
    }

def main():
    parser = argparse.ArgumentParser(description="Input Router cho tao-landing-page")
    parser.add_argument("input", help="URL Stitch, URL Figma, đường dẫn ảnh thiết kế, tệp brief hoặc brief chữ")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả dạng JSON")
    parser.add_argument("--ingest-dir", help="Thư mục đầu ra doc_ingest cho tệp brief "
                        "(mặc định ~/Downloads/AIWF_Output/_ingest/landing_<tên tệp>)")
    args = parser.parse_args()

    route = route_input(args.input, args.ingest_dir)
    if args.json:
        print(json.dumps(route, ensure_ascii=False, indent=2))
    else:
        print(f"🎯 Adapter Được Chọn: {route['adapter'].upper()}")
        print(f"📌 Thông tin: {route['message']}")
        if "flag" in route:
            print(f"⚠️  Cảnh báo: {route['flag']}")
    if route["adapter"] in ("unreadable", "missing_dependency"):
        sys.exit(4 if route["adapter"] == "missing_dependency" else 2)

if __name__ == "__main__":
    main()
