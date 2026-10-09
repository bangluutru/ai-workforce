#!/usr/bin/env python3
"""
AIWF Video Studio — Backend Server
Flask API server cho Video Studio UI.
Bảo mật tăng cường (Security Hardened):
- Kiểm soát đường dẫn chặt chẽ chống Path Traversal (LFI/Arbitrary File Read)
- Whitelist các định dạng file media an toàn
- Giới hạn CORS cục bộ (localhost / 127.0.0.1)
"""
import json
import os
import sys
import subprocess
import tempfile
import shutil
from typing import Tuple, List, Optional, Set

# Optional Flask import cho phép test các hàm an toàn và logic độc lập
try:
    from flask import Flask, request, jsonify, send_file, send_from_directory
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    Flask = None
    CORS = None
    HAS_FLASK = False

# Add scripts dir to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE_ROOT = os.path.abspath(os.path.join(SKILL_DIR, "..", "..", ".."))
UI_DIR = os.path.join(SKILL_DIR, "ui")
sys.path.insert(0, SCRIPT_DIR)

# Whitelist các phần mở rộng media được phép xử lý
ALLOWED_MEDIA_EXTENSIONS: Set[str] = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm",
    ".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg",
    ".png", ".jpg", ".jpeg", ".webp", ".svg",
    ".ass", ".srt", ".vtt", ".json"
}

def get_allowed_roots() -> List[str]:
    """Trả về danh sách thư mục gốc được phép truy cập."""
    roots = [
        os.path.realpath(os.path.expanduser("~/Downloads")),
        os.path.realpath(os.path.expanduser("~/Downloads/AIWF_Output")),
        os.path.realpath(tempfile.gettempdir()),
        os.path.realpath(WORKSPACE_ROOT)
    ]
    # Khử trùng lặp giữ nguyên thứ tự
    seen = set()
    unique_roots = []
    for r in roots:
        if r not in seen:
            seen.add(r)
            unique_roots.append(r)
    return unique_roots

def is_safe_path(
    path: str,
    allowed_extensions: Optional[Set[str]] = None,
    must_exist: bool = False,
    is_dir: bool = False
) -> Tuple[bool, str]:
    """
    Xác thực đường dẫn an toàn:
    - Loại bỏ ký tự độc hại / null bytes
    - Ngăn chặn Path Traversal ('..')
    - Chỉ cho phép nằm trong các thư mục gốc hợp lệ (Downloads, temp, workspace)
    - Kiểm tra whitelist đuôi file nếu được chỉ định
    - Kiểm tra tồn tại nếu must_exist=True

    Returns:
        (is_valid: bool, resolved_path_or_error_msg: str)
    """
    if not path or not isinstance(path, str):
        return False, "Đường dẫn không hợp lệ hoặc rỗng."

    if "\x00" in path:
        return False, "Phát hiện ký tự null byte trong đường dẫn."

    # Mở rộng user home và chuẩn hóa đường dẫn tuyệt đối (giải mã symlink & ..)
    real_path = os.path.realpath(os.path.expanduser(path))

    # Kiểm tra xem đường dẫn có nằm dưới một trong các thư mục cho phép không
    allowed_roots = get_allowed_roots()
    is_allowed = False
    for root in allowed_roots:
        if real_path == root or real_path.startswith(root + os.sep):
            is_allowed = True
            break

    if not is_allowed:
        return False, f"Truy cập bị từ chối: Đường dẫn nằm ngoài phạm vi cho phép ({real_path})."

    # Kiểm tra phần mở rộng file (nếu không phải kiểm tra thư mục)
    if not is_dir and allowed_extensions is not None:
        ext = os.path.splitext(real_path)[1].lower()
        if ext not in allowed_extensions:
            return False, f"Định dạng tệp không được phép: '{ext}'."

    # Kiểm tra tồn tại
    if must_exist:
        if is_dir:
            if not os.path.isdir(real_path):
                return False, f"Thư mục không tồn tại: {real_path}"
        else:
            if not os.path.exists(real_path):
                return False, f"Tệp không tồn tại: {real_path}"

    return True, real_path


# Khởi tạo Flask App nếu có thư viện
if HAS_FLASK:
    app = Flask(__name__, static_folder=UI_DIR)
    # Restrict CORS to local origins only
    ALLOWED_ORIGINS = [
        "http://127.0.0.1:8800",
        "http://localhost:8800",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://localhost:3000"
    ]
    CORS(app, origins=ALLOWED_ORIGINS)
else:
    app = None

# Project state
current_project = {
    "clips": [],
    "audio_tracks": [],
    "subtitle_tracks": [],
    "beats": [],
    "tempo": 0,
    "duration": 0,
    "output_dir": os.path.expanduser("~/Downloads")
}

# ============================================================
# UI Routes
# ============================================================

if HAS_FLASK:
    @app.route("/")
    def index():
        return send_from_directory(UI_DIR, "index.html")

    @app.route("/style.css")
    def style():
        return send_from_directory(UI_DIR, "style.css")

    @app.route("/app.js")
    def appjs():
        return send_from_directory(UI_DIR, "app.js")

    # ============================================================
    # Media Routes (Hardened)
    # ============================================================

    @app.route("/api/media")
    def serve_media():
        """Serve media file for preview (hardened against traversal & arbitrary file read)."""
        raw_path = request.args.get("path", "")
        ok, res = is_safe_path(raw_path, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS, must_exist=True)
        if not ok:
            return jsonify({"error": res}), 403
        return send_file(res)

    # ============================================================
    # Analysis Routes
    # ============================================================

    @app.route("/api/analyze", methods=["POST"])
    def analyze():
        """Phân tích beat + waveform từ file media."""
        data = request.json or {}
        raw_path = data.get("file_path", "")
        ok, file_path = is_safe_path(raw_path, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS, must_exist=True)
        if not ok:
            return jsonify({"error": file_path}), 400

        try:
            from beat_detector import analyze_media
            result = analyze_media(file_path)
            current_project["beats"] = result.get("beats", [])
            current_project["tempo"] = result.get("tempo", 0)
            current_project["duration"] = result.get("duration", 0)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/extract-audio", methods=["POST"])
    def extract_audio():
        """Trích xuất audio từ video để WaveSurfer load."""
        data = request.json or {}
        raw_path = data.get("file_path", "")
        ok, file_path = is_safe_path(raw_path, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS, must_exist=True)
        if not ok:
            return jsonify({"error": file_path}), 400

        output_path = os.path.join(tempfile.gettempdir(), "vs_audio_preview.wav")
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", file_path,
                "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
                output_path
            ], capture_output=True, check=True)
            return jsonify({"audio_path": output_path})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ============================================================
    # Timeline & Render Routes
    # ============================================================

    @app.route("/api/render", methods=["POST"])
    def render():
        """Render video từ timeline project (hardened)."""
        data = request.json or {}
        clips = data.get("clips", [])
        music_path = data.get("music_path")
        music_volume = data.get("music_volume", 0.3)
        subtitle_path = data.get("subtitle_path")
        output_name = data.get("output_name", "output.mp4")
        output_dir = data.get("output_dir", os.path.expanduser("~/Downloads"))

        if not clips:
            return jsonify({"error": "No clips to render"}), 400

        # Validate clips
        for clip in clips:
            c_path = clip.get("path", "")
            ok, res = is_safe_path(c_path, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS, must_exist=True)
            if not ok:
                return jsonify({"error": f"Clip invalid: {res}"}), 400
            clip["path"] = res

        # Validate optional music
        if music_path:
            ok, res = is_safe_path(music_path, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS, must_exist=True)
            if not ok:
                return jsonify({"error": f"Music invalid: {res}"}), 400
            music_path = res

        # Validate optional subtitles
        if subtitle_path:
            ok, res = is_safe_path(subtitle_path, allowed_extensions={".ass", ".srt", ".vtt"}, must_exist=True)
            if not ok:
                return jsonify({"error": f"Subtitle invalid: {res}"}), 400
            subtitle_path = res

        # Validate output directory
        ok, res_dir = is_safe_path(output_dir, is_dir=True, must_exist=False)
        if not ok:
            return jsonify({"error": f"Output dir invalid: {res_dir}"}), 400
        os.makedirs(res_dir, exist_ok=True)
        output_path = os.path.join(res_dir, os.path.basename(output_name))

        try:
            inputs = []
            filter_parts = []

            for i, clip in enumerate(clips):
                inputs.extend(["-i", clip["path"]])
                trim = ""
                if "start" in clip and "end" in clip:
                    trim = f"trim={clip['start']}:{clip['end']},setpts=PTS-STARTPTS,"
                filter_parts.append(f"[{i}:v]{trim}scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2[v{i}]")

            # Concat video
            concat_inputs = "".join(f"[v{i}]" for i in range(len(clips)))
            filter_parts.append(f"{concat_inputs}concat=n={len(clips)}:v=1:a=0[outv]")

            filter_complex = ";".join(filter_parts)

            cmd = ["ffmpeg", "-y"]
            cmd.extend(inputs)

            if music_path and os.path.exists(music_path):
                cmd.extend(["-i", music_path])
                music_idx = len(clips)
                audio_filter = f"[0:a]volume=1.0[voice];[{music_idx}:a]volume={music_volume}[bg];[voice][bg]amix=inputs=2:duration=first[outa]"
                filter_complex += ";" + audio_filter
                cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "[outa]"])
            else:
                cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "0:a?"])

            if subtitle_path and os.path.exists(subtitle_path):
                cmd.extend(["-vf", f"ass={subtitle_path}"])

            cmd.extend([
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                output_path
            ])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                return jsonify({"success": True, "output_path": output_path})
            else:
                return jsonify({"error": result.stderr[-500:]}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/trim", methods=["POST"])
    def trim_clip():
        """Cắt video clip theo thời gian."""
        data = request.json or {}
        input_path = data.get("input_path", "")
        ok_in, resolved_in = is_safe_path(input_path, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS, must_exist=True)
        if not ok_in:
            return jsonify({"error": resolved_in}), 400

        start = data.get("start", 0)
        end = data.get("end")
        raw_out_dir = data.get("output_dir", tempfile.gettempdir())
        ok_out, resolved_out_dir = is_safe_path(raw_out_dir, is_dir=True, must_exist=False)
        if not ok_out:
            return jsonify({"error": resolved_out_dir}), 400

        os.makedirs(resolved_out_dir, exist_ok=True)
        basename = os.path.splitext(os.path.basename(resolved_in))[0]
        output_path = os.path.join(resolved_out_dir, f"{basename}_trim_{start}_{end}.mp4")

        cmd = ["ffmpeg", "-y", "-i", resolved_in, "-ss", str(start)]
        if end:
            cmd.extend(["-to", str(end)])
        cmd.extend(["-c", "copy", output_path])

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return jsonify({"success": True, "output_path": output_path})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ============================================================
    # Project Management
    # ============================================================

    @app.route("/api/project/save", methods=["POST"])
    def save_project():
        """Lưu project JSON an toàn."""
        data = request.json or {}
        default_save = os.path.join(os.path.expanduser("~/Downloads"), "video_studio_project.json")
        output_path = data.get("path", default_save)
        ok, resolved_path = is_safe_path(output_path, allowed_extensions={".json"}, must_exist=False)
        if not ok:
            return jsonify({"error": resolved_path}), 403

        os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
        with open(resolved_path, "w", encoding="utf-8") as f:
            json.dump(data.get("project", current_project), f, indent=2, ensure_ascii=False)
        return jsonify({"success": True, "path": resolved_path})

    @app.route("/api/project/load", methods=["POST"])
    def load_project():
        """Load project JSON an toàn."""
        data = request.json or {}
        path = data.get("path", "")
        ok, resolved_path = is_safe_path(path, allowed_extensions={".json"}, must_exist=True)
        if not ok:
            return jsonify({"error": resolved_path}), 400
        with open(resolved_path, "r", encoding="utf-8") as f:
            project = json.load(f)
        return jsonify(project)

    # ============================================================
    # AIWF Integration
    # ============================================================

    @app.route("/api/tts", methods=["POST"])
    def text_to_speech():
        """Tạo lời thoại qua engine TTS dùng chung (_shared/media/tts.py: VieNeu vi · Kokoro en/ja)."""
        data = request.json or {}
        text = data.get("text", "")
        lang = data.get("lang", "vi")
        voice = data.get("voice")
        output_dir = data.get("output_dir", tempfile.gettempdir())
        ok_dir, resolved_dir = is_safe_path(output_dir, is_dir=True, must_exist=False)
        if not ok_dir:
            return jsonify({"error": resolved_dir}), 400

        os.makedirs(resolved_dir, exist_ok=True)
        output_path = os.path.join(resolved_dir, "tts_output.wav")

        synthesizer_path = os.path.join(os.path.dirname(SKILL_DIR), "_shared", "media", "tts.py")
        if not os.path.exists(synthesizer_path):
            return jsonify({"error": f"Không thấy engine TTS dùng chung: {synthesizer_path}"}), 500
        cmd = [sys.executable, synthesizer_path, "--text", text, "--lang", lang, "--output", output_path]
        if voice:
            cmd.extend(["--voice", voice])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({"success": True, "output_path": output_path})
        return jsonify({"error": (result.stdout + result.stderr).strip()[-800:] or "TTS thất bại"}), 500

    @app.route("/api/list-files", methods=["POST"])
    def list_files():
        """Liệt kê file media trong thư mục (hardened against traversal)."""
        data = request.json or {}
        raw_dir = data.get("directory", os.path.expanduser("~/Downloads"))
        ok, resolved_dir = is_safe_path(raw_dir, is_dir=True, must_exist=True)
        if not ok:
            return jsonify({"error": resolved_dir}), 403

        extensions = data.get("extensions", [".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".webm"])
        valid_exts = {e.lower() for e in extensions if e.lower() in ALLOWED_MEDIA_EXTENSIONS}
        files = []
        for f in sorted(os.listdir(resolved_dir)):
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                full_path = os.path.join(resolved_dir, f)
                if os.path.isfile(full_path):
                    size_mb = round(os.path.getsize(full_path) / 1048576, 1)
                    files.append({"name": f, "path": full_path, "size_mb": size_mb})
        return jsonify({"files": files, "directory": resolved_dir})

# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    if not HAS_FLASK:
        print("Lỗi: Cần cài đặt flask và flask-cors để chạy server (pip install flask flask-cors).")
        sys.exit(1)

    import argparse
    parser = argparse.ArgumentParser(description="AIWF Video Studio Server")
    parser.add_argument("--port", type=int, default=8800)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    # Enforce loopback binding by default for security
    if args.host not in ("127.0.0.1", "localhost"):
        print(f"⚠️ Cảnh báo bảo mật: Host '{args.host}' mở ra mạng bên ngoài. Khuyến nghị dùng 127.0.0.1.")

    print(f"🎬 AIWF Video Studio running at http://{args.host}:{args.port}")
    print(f"📁 UI: {UI_DIR}")
    app.run(host=args.host, port=args.port, debug=False)
