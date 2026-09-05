#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local_bridge_server.py — Local HTTP Bridge Server phục vụ Temporary UI và AI Edit loop.
Chạy bằng Python Standard Library (Zero External Dependencies).
Hỗ trợ HTTP Range requests cho video streaming, REST API cho project state,
hàng đợi AI Edit, Undo/Redo, Export và Render tiến trình ngầm.
"""

import argparse
import json
import mimetypes
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project_manager import load_project, save_project, undo, redo, split_segment, merge_segment
from ass_generator import generate_ass, generate_srt
from render_video import render_hardsub

# Biến trạng thái toàn cục
GLOBAL_STATE = {
    "project_path": None,
    "project_data": None,
    "render_job": {
        "status": "idle",  # idle | rendering | done | error
        "progress": 0,
        "output_path": None,
        "error": None,
    },
    "server": None,
}


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class BridgeRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Giảm thiểu log rác terminal
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            self.serve_ui_file("index.html", "text/html")
        elif path.startswith("/ui/"):
            rel_path = path[4:]
            self.serve_ui_file(rel_path)
        elif path == "/video":
            self.serve_video_stream()
        elif path == "/api/project":
            self.handle_get_project()
        elif path == "/api/render-status":
            self.handle_get_render_status()
        elif path.startswith("/templates/"):
            self.serve_template_file(path[len("/templates/"):])
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        try:
            if path == "/api/project":
                self.handle_save_project(payload)
            elif path == "/api/ai-edit":
                self.handle_ai_edit(payload)
            elif path == "/api/undo":
                self.handle_undo()
            elif path == "/api/redo":
                self.handle_redo()
            elif path == "/api/split":
                self.handle_split(payload)
            elif path == "/api/merge":
                self.handle_merge(payload)
            elif path == "/api/export":
                self.handle_export(payload)
            elif path == "/api/render":
                self.handle_render(payload)
            elif path == "/api/shutdown":
                self.handle_shutdown()
            else:
                self.send_error(404, "Unknown API Endpoint")
        except Exception as e:
            self.respond_json(500, {"success": False, "error": f"Lỗi máy chủ nội bộ: {str(e)}"})

    def serve_ui_file(self, filename, content_type=None):
        skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(skill_root, "ui", filename)

        if not os.path.isfile(file_path):
            self.send_error(404, f"File UI không tồn tại: {filename}")
            return

        if not content_type:
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"

        with open(file_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def serve_template_file(self, rel_path):
        """Phục vụ file từ thư mục templates/ (font files, v.v.)."""
        skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(skill_root, "templates", rel_path)

        # Bảo mật: không cho phép traversal ngoài thư mục templates
        real_templates = os.path.realpath(os.path.join(skill_root, "templates"))
        real_file = os.path.realpath(file_path)
        if not real_file.startswith(real_templates):
            self.send_error(403, "Forbidden")
            return

        if not os.path.isfile(file_path):
            self.send_error(404, f"Template file không tồn tại: {rel_path}")
            return

        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            if file_path.endswith(".otf"):
                content_type = "font/otf"
            elif file_path.endswith(".ttf"):
                content_type = "font/ttf"
            else:
                content_type = "application/octet-stream"

        with open(file_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def serve_video_stream(self):
        """Hỗ trợ HTTP 206 Partial Content để tua mượt mà trên HTML5 Video."""
        proj_file = GLOBAL_STATE["project_path"]
        if not proj_file or not os.path.isfile(proj_file):
            self.send_error(404, "Project not loaded")
            return

        with open(proj_file, "r", encoding="utf-8") as f:
            proj = json.load(f)

        video_path = proj.get("video", {}).get("source_path")
        if not video_path or not os.path.isfile(video_path):
            self.send_error(404, "Video file not found")
            return

        file_size = os.path.getsize(video_path)
        range_header = self.headers.get("Range")

        if not range_header:
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_cors_headers()
            self.end_headers()
            with open(video_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
            return

        match = re.search(r"bytes=(\d+)-(\d*)", range_header)
        if not match:
            self.send_error(416, "Requested Range Not Satisfiable")
            return

        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else file_size - 1
        end = min(end, file_size - 1)
        length = end - start + 1

        self.send_response(206)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_cors_headers()
        self.end_headers()

        with open(video_path, "rb") as f:
            f.seek(start)
            remaining = length
            chunk_size = 64 * 1024
            while remaining > 0:
                to_read = min(remaining, chunk_size)
                chunk = f.read(to_read)
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
                remaining -= len(chunk)

    def handle_get_project(self):
        proj_file = GLOBAL_STATE["project_path"]
        try:
            data = load_project(proj_file)
            GLOBAL_STATE["project_data"] = data
            self.respond_json(200, data)
        except Exception as e:
            self.respond_json(500, {"error": str(e)})

    def handle_save_project(self, payload):
        proj_file = GLOBAL_STATE["project_path"]
        try:
            make_snapshot = payload.pop("_make_snapshot", False)
            desc = payload.pop("_description", "Cập nhật từ giao diện")
            updated = save_project(payload, proj_file, description=desc, make_snapshot=make_snapshot)
            GLOBAL_STATE["project_data"] = updated
            self.respond_json(200, {"success": True, "revision": updated.get("history", {}).get("current_revision")})
        except Exception as e:
            self.respond_json(500, {"error": str(e)})

    def handle_ai_edit(self, payload):
        """
        Xử lý yêu cầu AI Edit từ giao diện người dùng.
        """
        proj_file = GLOBAL_STATE["project_path"]
        instruction = payload.get("instruction", "").strip()
        scope = payload.get("scope", "current")  # current | selected | all
        target_ids = payload.get("segment_ids", [])

        if not instruction:
            self.respond_json(400, {"error": "Thiếu nội dung instruction"})
            return

        try:
            # Ghi nhận action request theo chuẩn ISP v1.0
            try:
                req_path = os.path.join(os.path.dirname(proj_file), "action_request.json")
                with open(req_path, "w", encoding="utf-8") as rf:
                    json.dump({
                        "requestId": f"req_{int(time.time())}",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "action": "ai_edit",
                        "instruction": instruction,
                        "scope": scope,
                        "targetIds": target_ids
                    }, rf, ensure_ascii=False, indent=2)
            except Exception:
                pass

            proj = load_project(proj_file)
            # Lưu snapshot trước khi thực hiện sửa đổi
            save_project(proj, proj_file, description=f"Trước AI Edit: {instruction[:40]}", make_snapshot=True)

            segments = proj.get("segments", [])
            updated_count = 0

            # Lọc danh sách segments cần sửa
            for seg in segments:
                should_edit = False
                if scope == "all":
                    should_edit = True
                elif scope in ["current", "selected"] and seg.get("id") in target_ids:
                    should_edit = True

                if should_edit:
                    src = seg.get("source_text", "")
                    trans = seg.get("translated_text", "")

                    # Áp dụng logic hiệu chỉnh (deterministic + heuristic; các prompt phức tạp có thể gọi subagent)
                    new_trans = self.apply_ai_instruction(src, trans, instruction)
                    seg["translated_text"] = new_trans
                    # TUYỆT ĐỐI KHÔNG SỬA TIMESTAMPS để tránh lệch hình/tiếng
                    updated_count += 1

            # Lưu lại dữ liệu sau khi AI sửa
            proj["segments"] = segments
            save_project(proj, proj_file, description=f"Sau AI Edit ({updated_count} câu)", make_snapshot=False)
            GLOBAL_STATE["project_data"] = proj

            self.respond_json(200, {
                "success": True,
                "updated_count": updated_count,
                "segments": segments,
                "revision": proj.get("history", {}).get("current_revision"),
            })
        except Exception as e:
            self.respond_json(500, {"error": str(e)})

    def apply_ai_instruction(self, source_text, translated_text, instruction):
        """
        Mô phỏng bộ xử lý hiệu chỉnh ngôn ngữ theo lệnh (khử rườm rà, rút ngắn, dịch).
        """
        text = translated_text if translated_text else source_text
        inst_lower = instruction.lower()

        # 1. Rút ngắn câu (Shorten)
        if any(w in inst_lower for w in ["rút ngắn", "ngắn gọn", "ngắn lại", "shorten"]):
            # Loại bỏ các từ đệm, trạng từ thừa
            fillers = ["thì", "là", "mà", "ở đây", "chúng ta thấy rằng", "có thể nói là", "thực sự", "rất là", "của chúng tôi"]
            res = text
            for f in fillers:
                res = re.sub(rf'\b{f}\b', '', res, flags=re.IGNORECASE)
            res = re.sub(r'\s+', ' ', res).strip()
            return res if len(res) >= 3 else text

        # 2. Viết tự nhiên bằng tiếng Việt (Natural phrasing)
        if any(w in inst_lower for w in ["tự nhiên", "thuần việt", "dễ hiểu", "natural"]):
            res = text.replace("được thực hiện bởi", "do").replace("có khả năng", "có thể")
            return res

        # 3. Văn phong trang trọng (Formal tone)
        if any(w in inst_lower for w in ["trang trọng", "lịch thiệp", "formal"]):
            res = text.replace("mình", "chúng tôi").replace("các bạn", "quý vị")
            return res

        # 4. Viết hoa đầu câu / Chuẩn hóa dấu câu
        if any(w in inst_lower for w in ["viết hoa", "dấu câu", "capitalize"]):
            if text:
                return text[0].upper() + text[1:]
            return text

        # Mặc định giữ nguyên nếu instruction là ghi chú chung
        return text

    def handle_undo(self):
        proj_file = GLOBAL_STATE["project_path"]
        try:
            ok, msg = undo(proj_file)
            proj = load_project(proj_file)
            GLOBAL_STATE["project_data"] = proj
            self.respond_json(200, {"success": ok, "message": msg, "project": proj})
        except Exception as e:
            self.respond_json(500, {"error": str(e)})

    def handle_redo(self):
        proj_file = GLOBAL_STATE["project_path"]
        try:
            ok, msg = redo(proj_file)
            proj = load_project(proj_file)
            GLOBAL_STATE["project_data"] = proj
            self.respond_json(200, {"success": ok, "message": msg, "project": proj})
        except Exception as e:
            self.respond_json(500, {"error": str(e)})

    def handle_split(self, payload):
        proj_file = GLOBAL_STATE["project_path"]
        seg_id = payload.get("segment_id")
        split_time = float(payload.get("split_time", 0.0))
        try:
            proj = load_project(proj_file)
            proj = split_segment(proj, seg_id, split_time)
            save_project(proj, proj_file, description=f"Chia câu {seg_id} tại {split_time}s", make_snapshot=True)
            GLOBAL_STATE["project_data"] = proj
            self.respond_json(200, {"success": True, "segments": proj.get("segments", [])})
        except Exception as e:
            self.respond_json(500, {"error": str(e)})

    def handle_merge(self, payload):
        proj_file = GLOBAL_STATE["project_path"]
        seg_id = payload.get("segment_id")
        try:
            proj = load_project(proj_file)
            proj = merge_segment(proj, seg_id)
            save_project(proj, proj_file, description=f"Gộp câu {seg_id} với câu sau", make_snapshot=True)
            GLOBAL_STATE["project_data"] = proj
            self.respond_json(200, {"success": True, "segments": proj.get("segments", [])})
        except Exception as e:
            self.respond_json(500, {"error": str(e)})

    def handle_export(self, payload):
        proj_file = GLOBAL_STATE["project_path"]
        out_dir = payload.get("output_dir") or os.path.expanduser("~/Downloads")
        os.makedirs(out_dir, exist_ok=True)

        try:
            proj = load_project(proj_file)
            base_name = os.path.splitext(proj.get("video", {}).get("filename", "subtitles"))[0]

            ass_path = os.path.join(out_dir, f"{base_name}.ass")
            srt_path = os.path.join(out_dir, f"{base_name}.srt")

            generate_ass(proj, ass_path)
            generate_srt(proj, srt_path)

            self.respond_json(200, {
                "success": True,
                "ass_path": ass_path,
                "srt_path": srt_path,
                "output_dir": out_dir,
            })
        except Exception as e:
            self.respond_json(500, {"error": str(e)})

    def handle_render(self, payload):
        try:
            proj_file = GLOBAL_STATE["project_path"]
            out_dir = payload.get("output_dir") or os.path.expanduser("~/Downloads")

            # Cập nhật ngay style live từ preview nếu có gửi kèm trong payload
            if "style" in payload and isinstance(payload["style"], dict):
                if GLOBAL_STATE.get("project_data") is not None:
                    GLOBAL_STATE["project_data"]["style"] = payload["style"]
                    save_project(GLOBAL_STATE["project_data"], proj_file, description="Đồng bộ style từ Preview trước khi xuất video", make_snapshot=False)
                else:
                    proj = load_project(proj_file)
                    proj["style"] = payload["style"]
                    GLOBAL_STATE["project_data"] = proj
                    save_project(proj, proj_file, description="Đồng bộ style từ Preview trước khi xuất video", make_snapshot=False)

            if GLOBAL_STATE["render_job"]["status"] == "rendering":
                self.respond_json(400, {"success": False, "error": "Đang có một tiến trình xuất video chạy dở, vui lòng chờ."})
                return

            GLOBAL_STATE["render_job"]["status"] = "idle"
            GLOBAL_STATE["render_job"]["progress"] = 0
            GLOBAL_STATE["render_job"]["error"] = None
            GLOBAL_STATE["render_job"]["output_path"] = None

            def render_worker():
                job = GLOBAL_STATE["render_job"]
                job["status"] = "rendering"
                job["progress"] = 0
                job["error"] = None

                def on_progress(pct):
                    job["progress"] = pct

                try:
                    import importlib
                    import render_video
                    importlib.reload(render_video)

                    out_mp4 = render_video.render_hardsub(
                        proj_file,
                        output_dir=out_dir,
                        progress_callback=on_progress,
                    )
                    job["status"] = "done"
                    job["progress"] = 100
                    job["output_path"] = out_mp4
                except Exception as e:
                    job["status"] = "error"
                    job["error"] = str(e)

            threading.Thread(target=render_worker, daemon=True).start()
            self.respond_json(200, {"success": True, "message": "Đã bắt đầu tiến trình xuất video"})
        except Exception as ex:
            self.respond_json(500, {"success": False, "error": f"Lỗi khi bắt đầu xuất video: {str(ex)}"})

    def handle_get_render_status(self):
        self.respond_json(200, GLOBAL_STATE["render_job"])

    def handle_shutdown(self):
        self.respond_json(200, {"success": True, "message": "Đang tắt máy chủ tạm thời..."})

        def stop():
            time.sleep(0.5)
            if GLOBAL_STATE["server"]:
                GLOBAL_STATE["server"].shutdown()

        threading.Thread(target=stop, daemon=True).start()

    def respond_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)


def find_free_port(start_port=8765):
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


def start_server(project_path, port=None, auto_open=True):
    if not os.path.isfile(project_path):
        raise FileNotFoundError(f"Project file not found: {project_path}")

    GLOBAL_STATE["project_path"] = os.path.abspath(project_path)
    GLOBAL_STATE["project_data"] = load_project(GLOBAL_STATE["project_path"])

    if not port:
        port = find_free_port()

    server = ThreadedHTTPServer(("127.0.0.1", port), BridgeRequestHandler)
    GLOBAL_STATE["server"] = server

    url = f"http://127.0.0.1:{port}"
    print("=" * 64)
    print(f"🚀 PHÒNG DỰNG PHỤ ĐỀ TẠM THỜI ĐÃ SẴN SÀNG:")
    print(f"👉 Link truy cập: {url}")
    print(f"📁 Dự án: {GLOBAL_STATE['project_path']}")
    print("=" * 64)

    if auto_open:
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", url])
            elif sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", url])
            else:
                import webbrowser
                webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Đã tắt phòng dựng tạm thời.")
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Khởi chạy phòng dựng phụ đề tạm thời (SubEdit-style).")
    parser.add_argument("--project", "-p", required=True, help="Đường dẫn file project.json")
    parser.add_argument("--port", type=int, help="Cổng kết nối (mặc định tự dò từ 8765)")
    parser.add_argument("--no-open", action="store_true", help="Không tự động mở trình duyệt")

    args = parser.parse_args()
    start_server(args.project, port=args.port, auto_open=not args.no_open)


if __name__ == "__main__":
    main()
