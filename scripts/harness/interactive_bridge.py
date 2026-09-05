#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/harness/interactive_bridge.py — Shared Interactive Runtime Helper.

Cung cấp các tiện ích nền tảng chuẩn cho mọi Interactive Skill trong AI Workforce:
- Quản lý Editable Project State (project.json)
- Lưu vết lịch sử Revisions và Snapshots (Undo / Redo an toàn)
- Thực thi bản vá có chọn lọc (Selective Patching)
- Hỗ trợ máy chủ HTTP cục bộ nhẹ nhàng (Python Standard Library) phục vụ media streaming
  và giao tiếp HTTP dự phòng (Dual-mode).

Tuân thủ:
- Rule R0: 100% portable, Git-sync compliant.
- Rule R1: Toàn bộ dữ liệu tạm lưu trong _process/, không ghi rác vào codebase.
- Rule R4: Zero External API, 100% Python Standard Library.
"""

import os
import sys
import json
import time
import shutil
import socket
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn


# ==============================================================================
# 1. CORE PROJECT STATE MANAGEMENT (SINGLE SOURCE OF TRUTH)
# ==============================================================================

def create_project_state(
    project_id: str,
    skill_name: str,
    source_file: str,
    data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Khởi tạo một bản ghi Project State chuẩn theo đặc tả ISP v1.0."""
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out_dir = output_dir or os.path.expanduser("~/Downloads")
    
    state = {
        "$schema_version": "1.0",
        "project_id": project_id,
        "skill": skill_name,
        "status": "in_review",
        "meta": {
            "source_file": os.path.abspath(source_file) if source_file else "",
            "created_at": now_iso,
            "updated_at": now_iso
        },
        "config": {
            "output_dir": out_dir,
            **(config or {})
        },
        "history": {
            "current_revision": 1,
            "snapshots": ["rev_001.json"]
        },
        "data": data
    }
    return state


def load_project_state(project_path: str) -> Dict[str, Any]:
    """Đọc Project State từ đĩa."""
    if not os.path.isfile(project_path):
        raise FileNotFoundError(f"Không tìm thấy file project.json tại: {project_path}")
    with open(project_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_project_state(
    state: Dict[str, Any],
    project_path: str,
    create_snap: bool = True,
    description: str = ""
) -> Tuple[bool, str]:
    """
    Lưu Project State xuống đĩa và tự động tạo snapshot nếu được yêu cầu.
    """
    project_dir = os.path.dirname(os.path.abspath(project_path))
    os.makedirs(project_dir, exist_ok=True)
    
    state["meta"]["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    if create_snap:
        snap_dir = os.path.join(project_dir, "snapshots")
        os.makedirs(snap_dir, exist_ok=True)
        
        history = state.setdefault("history", {"current_revision": 0, "snapshots": []})
        rev_num = history.get("current_revision", 0) + 1
        rev_filename = f"rev_{rev_num:03d}.json"
        rev_path = os.path.join(snap_dir, rev_filename)
        
        # Cập nhật danh sách snapshot (giới hạn tối đa 20 bản ghi gần nhất)
        history["current_revision"] = rev_num
        snapshots = history.setdefault("snapshots", [])
        snapshots.append(rev_filename)
        if len(snapshots) > 20:
            oldest = snapshots.pop(0)
            oldest_path = os.path.join(snap_dir, oldest)
            if os.path.exists(oldest_path):
                try:
                    os.remove(oldest_path)
                except Exception:
                    pass
        
        # Ghi file snapshot
        with open(rev_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    # Ghi file project.json chính
    with open(project_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    return True, f"Đã lưu thành công (Revision {state.get('history', {}).get('current_revision', 1)})"


def undo_snapshot(project_path: str) -> Tuple[bool, str]:
    """Khôi phục trạng thái về bản snapshot liền trước."""
    state = load_project_state(project_path)
    project_dir = os.path.dirname(os.path.abspath(project_path))
    snap_dir = os.path.join(project_dir, "snapshots")
    
    history = state.get("history", {})
    rev_num = history.get("current_revision", 1)
    if rev_num <= 1:
        return False, "Đã ở bản ghi đầu tiên, không thể hoàn tác tiếp."
    
    target_rev = rev_num - 1
    target_filename = f"rev_{target_rev:03d}.json"
    target_path = os.path.join(snap_dir, target_filename)
    
    if not os.path.isfile(target_path):
        return False, f"Không tìm thấy file snapshot: {target_filename}"
        
    with open(target_path, "r", encoding="utf-8") as f:
        restored_state = json.load(f)
        
    restored_state["history"]["current_revision"] = target_rev
    save_project_state(restored_state, project_path, create_snap=False)
    return True, f"Đã hoàn tác về Revision {target_rev}"


def redo_snapshot(project_path: str) -> Tuple[bool, str]:
    """Tiến tới bản snapshot liền sau."""
    state = load_project_state(project_path)
    project_dir = os.path.dirname(os.path.abspath(project_path))
    snap_dir = os.path.join(project_dir, "snapshots")
    
    history = state.get("history", {})
    rev_num = history.get("current_revision", 1)
    snapshots = history.get("snapshots", [])
    
    target_rev = rev_num + 1
    target_filename = f"rev_{target_rev:03d}.json"
    target_path = os.path.join(snap_dir, target_filename)
    
    if target_filename not in snapshots or not os.path.isfile(target_path):
        return False, "Không có thao tác kế tiếp để làm lại."
        
    with open(target_path, "r", encoding="utf-8") as f:
        restored_state = json.load(f)
        
    restored_state["history"]["current_revision"] = target_rev
    save_project_state(restored_state, project_path, create_snap=False)
    return True, f"Đã làm lại tới Revision {target_rev}"


def apply_selective_patches(
    project_path: str,
    patches: List[Dict[str, Any]],
    description: str = "Agent Patch"
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Áp dụng danh sách các bản vá cục bộ (Selective Patches) lên các thực thể mang Stable ID.
    Mỗi patch có dạng: { "id": "seg_002", "field": "text", "new_value": "..." }
    """
    state = load_project_state(project_path)
    data = state.get("data", {})
    
    # Tìm danh sách entities (hoặc segments/blocks)
    entities = data.get("entities") or data.get("segments") or data.get("blocks")
    if not isinstance(entities, list):
        return False, "Dữ liệu dự án không chứa danh sách thực thể (entities/segments/blocks).", state
        
    entity_map = {item.get("id"): item for item in entities if isinstance(item, dict) and "id" in item}
    updated_count = 0
    
    for patch in patches:
        t_id = patch.get("id")
        if t_id in entity_map:
            target = entity_map[t_id]
            field = patch.get("field", "content")
            target[field] = patch.get("new_value")
            if "style" in patch and isinstance(patch["style"], dict):
                target.setdefault("style", {}).update(patch["style"])
            updated_count += 1
            
    save_project_state(state, project_path, create_snap=True, description=description)
    return True, f"Đã áp dụng thành công {updated_count} bản vá.", state


# ==============================================================================
# 2. LIGHTWEIGHT MEDIA STREAMING & DUAL-MODE HTTP BRIDGE
# ==============================================================================

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def find_free_port(start_port: int = 8765, end_port: int = 8799) -> int:
    """Tự động tìm kiếm một cổng mạng trống trong dải chỉ định."""
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


class StreamingBridgeHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler hỗ trợ HTTP 206 Partial Content (Range requests)
    để stream file video/audio lớn một cách mượt mà trên mọi trình duyệt/webview.
    """
    def log_message(self, format, *args):
        # Tránh làm ồn terminal log
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def serve_range_file(self, file_path: str, content_type: str = "video/mp4"):
        if not os.path.isfile(file_path):
            self.send_error(404, "File not found")
            return

        file_size = os.path.getsize(file_path)
        range_header = self.headers.get("Range")

        if range_header:
            range_match = range_header.strip().lower()
            if range_match.startswith("bytes="):
                parts = range_match[6:].split("-")
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.send_cors_headers()
                self.end_headers()

                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_left = length
                    chunk_size = 64 * 1024
                    while bytes_left > 0:
                        chunk = f.read(min(bytes_left, chunk_size))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        bytes_left -= len(chunk)
                return

        # Trường hợp không có Range header
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_cors_headers()
        self.end_headers()

        with open(file_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIWF Shared Interactive Runtime Utility")
    parser.add_argument("--test-state", action="store_true", help="Kiểm thử tạo và khôi phục Project State")
    args = parser.parse_args()
    
    if args.test_state:
        test_path = "/tmp/test_project.json"
        state = create_project_state("test_01", "test-skill", "/tmp/sample.mp4", {"entities": [{"id": "item_1", "text": "Hello"}]})
        save_project_state(state, test_path)
        print("Tạo thành công:", load_project_state(test_path)["project_id"])
        if os.path.exists(test_path):
            os.remove(test_path)
        print("✅ Kiểm thử hoàn tất!")
