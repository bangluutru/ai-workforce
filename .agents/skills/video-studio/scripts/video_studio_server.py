#!/usr/bin/env python3
"""
AIWF Video Studio — Backend Server
Flask API server cho Video Studio UI.
"""
import json
import os
import sys
import subprocess
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Add scripts dir to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
UI_DIR = os.path.join(SKILL_DIR, "ui")
sys.path.insert(0, SCRIPT_DIR)

app = Flask(__name__, static_folder=UI_DIR)
CORS(app)

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
# Media Routes
# ============================================================

@app.route("/api/media")
def serve_media():
    """Serve media file for preview."""
    path = request.args.get("path", "")
    if not path or not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path)

# ============================================================
# Analysis Routes
# ============================================================

@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Phân tích beat + waveform từ file media."""
    data = request.json
    file_path = data.get("file_path", "")
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": f"File not found: {file_path}"}), 400

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
    data = request.json
    file_path = data.get("file_path", "")
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 400

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
    """Render video từ timeline project."""
    data = request.json
    clips = data.get("clips", [])
    music_path = data.get("music_path")
    music_volume = data.get("music_volume", 0.3)
    subtitle_path = data.get("subtitle_path")
    output_name = data.get("output_name", "output.mp4")
    output_dir = data.get("output_dir", os.path.expanduser("~/Downloads"))
    output_path = os.path.join(output_dir, output_name)

    if not clips:
        return jsonify({"error": "No clips to render"}), 400

    try:
        # Build FFmpeg filter complex
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

        # Add music if provided
        if music_path and os.path.exists(music_path):
            cmd.extend(["-i", music_path])
            music_idx = len(clips)
            # Audio: mix original audio with music
            audio_filter = f"[0:a]volume=1.0[voice];[{music_idx}:a]volume={music_volume}[bg];[voice][bg]amix=inputs=2:duration=first[outa]"
            filter_complex += ";" + audio_filter
            cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "[outa]"])
        else:
            cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", "0:a?"])

        # Add subtitles
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
    data = request.json
    input_path = data.get("input_path", "")
    start = data.get("start", 0)
    end = data.get("end")
    output_dir = data.get("output_dir", tempfile.gettempdir())
    
    basename = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{basename}_trim_{start}_{end}.mp4")

    cmd = ["ffmpeg", "-y", "-i", input_path, "-ss", str(start)]
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
    """Lưu project JSON."""
    data = request.json
    output_path = data.get("path", os.path.join(os.path.expanduser("~/Downloads"), "video_studio_project.json"))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data.get("project", current_project), f, indent=2, ensure_ascii=False)
    return jsonify({"success": True, "path": output_path})

@app.route("/api/project/load", methods=["POST"])
def load_project():
    """Load project JSON."""
    data = request.json
    path = data.get("path", "")
    if not path or not os.path.exists(path):
        return jsonify({"error": "File not found"}), 400
    with open(path, "r", encoding="utf-8") as f:
        project = json.load(f)
    return jsonify(project)

# ============================================================
# AIWF Integration
# ============================================================

@app.route("/api/tts", methods=["POST"])
def text_to_speech():
    """Gọi Voice Synthesizer để tạo lời thoại."""
    data = request.json
    text = data.get("text", "")
    lang = data.get("lang", "vi")
    voice = data.get("voice")
    output_dir = data.get("output_dir", tempfile.gettempdir())
    output_path = os.path.join(output_dir, "tts_output.wav")

    synthesizer_path = os.path.join(
        os.path.dirname(SKILL_DIR), "long-tieng", "scripts", "voice_synthesizer.py"
    )
    if os.path.exists(synthesizer_path):
        cmd = [sys.executable, synthesizer_path, "--text", text, "--lang", lang, "--output", output_path]
        if voice:
            cmd.extend(["--voice", voice])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({"success": True, "output_path": output_path})
    return jsonify({"error": "Voice synthesizer not available"}), 500

@app.route("/api/list-files", methods=["POST"])
def list_files():
    """Liệt kê file media trong thư mục."""
    data = request.json
    directory = data.get("directory", os.path.expanduser("~/Downloads"))
    extensions = data.get("extensions", [".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".webm"])
    files = []
    if os.path.isdir(directory):
        for f in sorted(os.listdir(directory)):
            if any(f.lower().endswith(ext) for ext in extensions):
                full_path = os.path.join(directory, f)
                size_mb = round(os.path.getsize(full_path) / 1048576, 1)
                files.append({"name": f, "path": full_path, "size_mb": size_mb})
    return jsonify({"files": files, "directory": directory})

# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIWF Video Studio Server")
    parser.add_argument("--port", type=int, default=8800)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    
    print(f"🎬 AIWF Video Studio running at http://{args.host}:{args.port}")
    print(f"📁 UI: {UI_DIR}")
    app.run(host=args.host, port=args.port, debug=False)
