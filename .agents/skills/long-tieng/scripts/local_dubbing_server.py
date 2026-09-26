#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local_dubbing_server.py — Local HTTP Bridge Server phục vụ giao diện Lồng Tiếng Studio (long-tieng).
Chạy bằng Python Standard Library (Zero External Dependencies).
Hỗ trợ HTTP Range requests cho video streaming (cả video gốc và video thành phẩm lồng tiếng),
REST API cho project state & style, nghe thử mẫu giọng (voice sample), chia câu (split),
và Render video tiến trình ngầm với khả năng re-render liên tục.
"""

import argparse
import hashlib
import json
import mimetypes
import os
import re
import shutil
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
from dubbing_project_manager import load_dubbing_project, save_dubbing_project, split_segment
from voice_synthesizer import synthesize_line, get_voice_catalog, get_sample_text
from dubbing_pipeline import run_dubbing

GLOBAL_STATE = {
    "project_path": None,
    "project_data": None,
    "render_job": {
        "status": "idle",  # idle | rendering | done | error
        "progress": 0,
        "stage": "",
        "output_path": None,
        "error": None,
    },
    "server": None,
}

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class DubbingRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
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
            self.serve_video_stream(parsed.query)
        elif path == "/audio/speech":
            self.serve_audio_stream("master_speech_44k.wav", fallback="master_speech.wav")
        elif path == "/audio/mixed":
            self.serve_audio_stream("final_mixed_audio.wav")
        elif path == "/api/project":
            self.handle_get_project()
        elif path == "/api/voices":
            self.handle_get_voices()
        elif path == "/api/voice-sample":
            self.handle_get_voice_sample(parsed.query)
        elif path == "/api/audio-preview":
            self.handle_serve_preview_audio(parsed.query)
        elif path == "/api/render-status":
            self.handle_get_render_status()
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
            elif path == "/api/split":
                self.handle_split(payload)
            elif path == "/api/preview-line":
                self.handle_preview_line(payload)
            elif path == "/api/clone-voice":
                self.handle_clone_voice(payload)
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

    def serve_audio_stream(self, filename, fallback=None):
        """Hỗ trợ HTTP 206 Partial Content để tua audio lồng tiếng đồng bộ với video."""
        proj = GLOBAL_STATE.get("project_data") or {}
        process_dir = proj.get("process_dir")
        if not process_dir:
            self.send_error(404, "Process dir not found")
            return

        file_path = os.path.join(process_dir, filename)
        if not os.path.isfile(file_path) and fallback:
            file_path = os.path.join(process_dir, fallback)

        if not os.path.isfile(file_path):
            self.send_error(404, f"Audio file not found: {filename}")
            return

        file_size = os.path.getsize(file_path)
        range_header = self.headers.get("Range")
        content_type = "audio/wav" if file_path.endswith(".wav") else "audio/mpeg"

        if not range_header:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_cors_headers()
            self.end_headers()
            with open(file_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
            return

        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if not match:
            self.send_error(416, "Requested Range Not Satisfiable")
            return

        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else file_size - 1
        end = min(end, file_size - 1)
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
            remaining = length
            buf_size = 64 * 1024
            while remaining > 0:
                chunk = f.read(min(remaining, buf_size))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
                remaining -= len(chunk)

    def serve_video_stream(self, query_str=""):
        """Hỗ trợ HTTP 206 Partial Content để tua mượt mà trên HTML5 Video."""
        proj = GLOBAL_STATE.get("project_data")
        if not proj:
            self.send_error(404, "Project not loaded")
            return

        qs = urllib.parse.parse_qs(query_str)
        req_type = qs.get("type", ["orig"])[0]

        video_path = None
        if req_type == "dubbed":
            # Kiểm tra file video đã lồng tiếng
            candidate_path = GLOBAL_STATE["render_job"].get("output_path")
            if candidate_path and os.path.isfile(candidate_path):
                video_path = candidate_path
            else:
                base_name = os.path.splitext(os.path.basename(proj.get("video", {}).get("source_path", "")))[0]
                fallback_path = os.path.expanduser(f"~/Downloads/AIWF_Output/long-tieng/{base_name}_dubbed.mp4")
                if os.path.isfile(fallback_path):
                    video_path = fallback_path

        if not video_path:
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

        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
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
            buf_size = 64 * 1024
            while remaining > 0:
                chunk = f.read(min(remaining, buf_size))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    break
                remaining -= len(chunk)

    def handle_get_project(self):
        proj = GLOBAL_STATE.get("project_data")
        if not proj:
            self.respond_json(404, {"error": "Chưa nạp dự án"})
            return
        self.respond_json(200, proj)

    def handle_get_voices(self):
        voices = get_voice_catalog()
        self.respond_json(200, {"voices": voices})

    def handle_get_voice_sample(self, query_str):
        """Phát âm thanh mẫu đặc trưng cho từng giọng đọc khi người dùng chọn voice."""
        qs = urllib.parse.parse_qs(query_str)
        voice_id = qs.get("voice", [None])[0]
        if not voice_id:
            self.send_error(400, "Missing voice param")
            return

        # Tìm thông tin giọng
        catalog = get_voice_catalog()
        matched = next((v for v in catalog if v["id"] == voice_id), None)
        lang = matched["lang"] if matched else "vi"
        gender = matched["gender"] if matched else "female"

        sample_text = get_sample_text(voice_id)

        proj = GLOBAL_STATE.get("project_data") or {}
        process_dir = proj.get("process_dir") or "/tmp/dubbing_samples"
        sample_dir = os.path.join(process_dir, "samples")
        os.makedirs(sample_dir, exist_ok=True)

        is_edge = voice_id.startswith("vi-VN-")
        ext = ".mp3" if is_edge else ".wav"
        mime_type = "audio/mpeg" if is_edge else "audio/wav"

        sample_path = os.path.join(sample_dir, f"sample_{voice_id}{ext}")
        if not os.path.isfile(sample_path) or os.path.getsize(sample_path) == 0:
            synth_res = synthesize_line(
                text=sample_text,
                output_path=sample_path,
                lang=lang,
                gender=gender,
                voice=voice_id,
                speed=1.0
            )
            if not synth_res.get("success", False):
                self.send_error(500, synth_res.get("error", "Lỗi tạo mẫu giọng"))
                return

        with open(sample_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def handle_save_project(self, payload):
        proj_file = GLOBAL_STATE["project_path"]
        if not proj_file:
            self.respond_json(400, {"error": "Chưa xác định project_path"})
            return

        current_proj = GLOBAL_STATE["project_data"] or {}
        if "audio_settings" in payload:
            current_proj["audio_settings"] = payload["audio_settings"]
        if "style" in payload:
            current_proj["style"] = payload["style"]
        if "segments" in payload:
            current_proj["segments"] = payload["segments"]

        save_dubbing_project(current_proj, proj_file)
        GLOBAL_STATE["project_data"] = current_proj
        self.respond_json(200, {"success": True, "message": "Đã lưu cấu hình dự án"})

    def handle_split(self, payload):
        """Chia câu tại mốc split_time."""
        proj_file = GLOBAL_STATE["project_path"]
        current_proj = GLOBAL_STATE["project_data"]
        seg_id = payload.get("segment_id")
        split_time = float(payload.get("split_time", 0.0))

        updated_proj = split_segment(current_proj, seg_id, split_time)
        save_dubbing_project(updated_proj, proj_file)
        GLOBAL_STATE["project_data"] = updated_proj
        self.respond_json(200, {"success": True, "segments": updated_proj.get("segments", [])})

    def handle_clone_voice(self, payload):
        """Trích xuất mẫu giọng từ video hoặc nạp audio để nhân bản giọng (Voice Cloning)."""
        proj = GLOBAL_STATE.get("project_data") or {}
        process_dir = proj.get("process_dir") or "/tmp/dubbing_samples"
        samples_dir = os.path.join(process_dir, "samples")
        os.makedirs(samples_dir, exist_ok=True)

        ref_audio = payload.get("ref_audio")
        start = payload.get("start")
        end = payload.get("end")

        if start is not None and end is not None:
            orig_audio = os.path.join(process_dir, "original_audio.wav")
            if not os.path.isfile(orig_audio):
                self.respond_json(400, {"success": False, "error": "Chưa có audio gốc để trích xuất"})
                return

            s = max(0.0, float(start))
            e = max(s + 1.0, float(end))
            dur = min(8.0, e - s)
            target_clip = os.path.join(samples_dir, f"actor_clip_{int(s)}_{int(e)}.wav")
            cmd = [
                "ffmpeg", "-y", "-ss", str(s), "-t", str(dur),
                "-i", orig_audio, "-acodec", "pcm_s16le", "-ar", "48000", "-ac", "1",
                target_clip
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                self.respond_json(200, {
                    "success": True,
                    "ref_audio": target_clip,
                    "duration": dur,
                    "message": f"Đã trích xuất mẫu giọng diễn viên ({dur:.1f}s)"
                })
                return
            except Exception as ex:
                self.respond_json(500, {"success": False, "error": f"Lỗi trích xuất clip: {ex}"})
                return
        elif ref_audio and os.path.isfile(ref_audio):
            self.respond_json(200, {
                "success": True,
                "ref_audio": os.path.abspath(ref_audio),
                "message": "Đã ghi nhận mẫu giọng nhân bản"
            })
            return
        else:
            self.respond_json(400, {"success": False, "error": "Thiếu tham số start/end hoặc ref_audio hợp lệ"})

    def handle_preview_line(self, payload):
        """Tạo file âm thanh thử nghiệm cho một dòng thoại và trả về URL."""
        text = payload.get("text", "").strip()
        if not text:
            self.respond_json(400, {"error": "Nội dung câu thoại trống"})
            return

        lang = payload.get("lang", "vi")
        gender = payload.get("gender", "female")
        voice = payload.get("voice")
        speed = float(payload.get("speed", 1.0))
        ref_audio = payload.get("ref_audio")

        proj = GLOBAL_STATE.get("project_data") or {}
        process_dir = proj.get("process_dir") or "/tmp/dubbing_previews"
        prev_dir = os.path.join(process_dir, "previews")
        os.makedirs(prev_dir, exist_ok=True)

        is_edge = (voice or "").startswith("vi-VN-")
        ext = ".mp3" if (is_edge and not ref_audio) else ".wav"

        text_hash = hashlib.md5(f"{text}_{voice}_{speed}_{lang}_{ref_audio}".encode("utf-8")).hexdigest()[:10]
        preview_filename = f"preview_{text_hash}{ext}"
        preview_file_path = os.path.join(prev_dir, preview_filename)

        if not os.path.isfile(preview_file_path) or os.path.getsize(preview_file_path) == 0:
            synth_res = synthesize_line(
                text=text,
                output_path=preview_file_path,
                lang=lang,
                gender=gender,
                voice=voice,
                speed=speed,
                ref_audio=ref_audio
            )
            if not synth_res.get("success", False):
                self.respond_json(500, {"error": synth_res.get("error", "Lỗi tổng hợp âm thanh")})
                return

        audio_url = f"/api/audio-preview?file={urllib.parse.quote(preview_filename)}"
        self.respond_json(200, {"success": True, "audio_url": audio_url, "filename": preview_filename})

    def handle_serve_preview_audio(self, query_str):
        qs = urllib.parse.parse_qs(query_str)
        filename = qs.get("file", [None])[0]
        if not filename:
            self.send_error(400, "Missing file param")
            return

        proj = GLOBAL_STATE.get("project_data") or {}
        process_dir = proj.get("process_dir") or "/tmp/dubbing_previews"
        prev_file = os.path.join(process_dir, "previews", os.path.basename(filename))

        if not os.path.isfile(prev_file):
            self.send_error(404, "Audio file not found")
            return

        with open(prev_file, "rb") as f:
            data = f.read()

        mime_type = "audio/wav" if prev_file.endswith(".wav") else "audio/mpeg"
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def handle_render(self, payload):
        """Khởi chạy hoặc khởi chạy lại (re-render) video lồng tiếng trong Background Thread."""
        if GLOBAL_STATE["render_job"]["status"] == "rendering":
            self.respond_json(400, {"success": False, "error": "Đang có tiến trình xuất video khác chạy, vui lòng chờ."})
            return

        proj_file = GLOBAL_STATE["project_path"]
        proj = GLOBAL_STATE["project_data"]
        if not proj_file or not proj:
            self.respond_json(400, {"error": "Chưa có dự án hợp lệ để render"})
            return

        # Đồng bộ toàn bộ dữ liệu từ payload trước khi render
        if "audio_settings" in payload and isinstance(payload["audio_settings"], dict):
            proj["audio_settings"].update(payload["audio_settings"])
        if "style" in payload and isinstance(payload["style"], dict):
            proj["style"].update(payload["style"])
        if "segments" in payload and isinstance(payload["segments"], list):
            proj["segments"] = payload["segments"]

        save_dubbing_project(proj, proj_file)

        settings = proj.get("audio_settings", {})
        style_cfg = proj.get("style", {})
        video_path = proj.get("video", {}).get("source_path")
        out_dir = payload.get("output_dir") or os.path.expanduser("~/Downloads")
        os.makedirs(out_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(out_dir, f"{base_name}_dubbed.mp4")

        # Reset trạng thái render sạch sẽ
        GLOBAL_STATE["render_job"] = {
            "status": "rendering",
            "progress": 0,
            "stage": "Bắt đầu khởi động tiến trình hòa âm...",
            "output_path": output_path,
            "error": None,
        }

        def bg_render():
            try:
                def progress_cb(pct, stage_name):
                    GLOBAL_STATE["render_job"]["progress"] = pct
                    GLOBAL_STATE["render_job"]["stage"] = stage_name

                run_dubbing(
                    video_path=video_path,
                    subtitles_path=proj_file,
                    output_path=output_path,
                    lang=settings.get("lang", "vi"),
                    gender=settings.get("gender", "female"),
                    voice=settings.get("voice"),
                    speed=float(settings.get("speed", 1.0)),
                    bg_volume=float(settings.get("bg_volume", 1.0)),
                    voice_volume=float(settings.get("voice_volume", 1.4)),
                    ducking_ratio=float(settings.get("ducking_ratio", 0.20)),
                    include_subtitles=bool(settings.get("include_subtitles", True)),
                    style=style_cfg,
                    process_dir=proj.get("process_dir"),
                    progress_callback=progress_cb
                )
                GLOBAL_STATE["render_job"]["status"] = "done"
                GLOBAL_STATE["render_job"]["progress"] = 100
                GLOBAL_STATE["render_job"]["stage"] = "Hoàn tất lồng tiếng video!"
            except Exception as e:
                GLOBAL_STATE["render_job"]["status"] = "error"
                GLOBAL_STATE["render_job"]["error"] = str(e)
                GLOBAL_STATE["render_job"]["stage"] = f"Lỗi: {str(e)}"

        thread = threading.Thread(target=bg_render, daemon=True)
        thread.start()

        self.respond_json(200, {
            "success": True,
            "message": "Đã khởi chạy tiến trình render lồng tiếng",
            "output_path": output_path
        })

    def handle_get_render_status(self):
        self.respond_json(200, GLOBAL_STATE["render_job"])

    def handle_shutdown(self):
        self.respond_json(200, {"success": True, "message": "Đang tắt phòng dựng lồng tiếng..."})
        def stop():
            time.sleep(0.5)
            if GLOBAL_STATE.get("server"):
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

def find_free_port(start_port=8780):
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
    GLOBAL_STATE["project_data"] = load_dubbing_project(GLOBAL_STATE["project_path"])

    video_path = GLOBAL_STATE["project_data"].get("video", {}).get("source_path")
    if video_path:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        out_path = os.path.expanduser(f"~/Downloads/AIWF_Output/long-tieng/{base_name}_dubbed.mp4")
        if os.path.isfile(out_path):
            GLOBAL_STATE["render_job"] = {
                "status": "done",
                "progress": 100,
                "stage": "Video đã được lồng tiếng sẵn sàng!",
                "output_path": out_path,
                "error": None
            }

    if not port:
        port = find_free_port()

    server = ThreadedHTTPServer(("127.0.0.1", port), DubbingRequestHandler)
    GLOBAL_STATE["server"] = server

    url = f"http://127.0.0.1:{port}"
    print("=" * 64)
    print("🚀 PHÒNG DỰNG LỒNG TIẾNG STUDIO ĐÃ SẴN SÀNG:")
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
        print("\n🛑 Đã tắt phòng dựng lồng tiếng.")
    finally:
        server.server_close()

def main():
    parser = argparse.ArgumentParser(description="Khởi chạy phòng dựng lồng tiếng video tương tác (Studio UI)")
    parser.add_argument("--project", "-p", required=True, help="Đường dẫn file dubbing_project.json")
    parser.add_argument("--port", type=int, help="Cổng kết nối (mặc định tự dò từ 8780)")
    parser.add_argument("--no-open", action="store_true", help="Không tự động mở trình duyệt")

    args = parser.parse_args()
    start_server(args.project, port=args.port, auto_open=not args.no_open)

if __name__ == "__main__":
    main()
