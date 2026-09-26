#!/usr/bin/env python3
"""
scripts/benchmark_t10_direct.py — Direct Render Compute Benchmark for Hand-drawn Animation (T10)

Isolates pure render compute cost from Agent reasoning/harness overhead.
Measures:
- Setup & HTML load
- Full frame generation via Puppeteer
- FFmpeg encoding & muxing
- Total wall-clock runtime
- Frame count, effective FPS, resolution, output size
"""

import os
import sys
import time
import json
import shutil
import subprocess
from pathlib import Path

WORKSPACE = Path("/Users/tranhaibang/.gemini/antigravity-ide/scratch/ai-workforce")
RENDER_SCRIPT = WORKSPACE / ".agents/skills/hand-drawn-animation/scripts/render.mjs"
HTML_24FPS = Path.home() / "Downloads/canh-chim-phuong-hoang-tai-sinh.html"

def prepare_12fps_html(src_html: Path, dst_html: Path):
    with open(src_html, "r", encoding="utf-8") as f:
        content = f.read()
    # Replace fps: 24 with fps: 12
    content_12 = content.replace("fps: 24", "fps: 12")
    with open(dst_html, "w", encoding="utf-8") as f:
        f.write(content_12)
    print(f"Created 12fps test HTML at: {dst_html}")

def run_render_benchmark(html_path: Path, out_dir: Path, label: str):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"🎬 [T10 DIRECT COMPUTE BENCHMARK] Running {label}")
    print(f"   Input HTML: {html_path}")
    print(f"   Output Dir: {out_dir}")
    print(f"{'='*70}")

    t_start = time.time()
    cmd = ["node", str(RENDER_SCRIPT), str(html_path), "--out", str(out_dir)]

    # We track output in real time
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    first_meta_time = None
    frame_render_start = None
    frame_render_end = None
    frames_rendered = 0
    total_frames = 0
    meta_line = ""

    for line in proc.stdout:
        line_s = line.strip()
        print(f"   [{label}] {line_s}")
        if "frames," in line_s and "fps," in line_s:
            first_meta_time = time.time()
            frame_render_start = first_meta_time
            meta_line = line_s
            try:
                parts = line_s.split(":")
                if len(parts) > 1:
                    info = parts[1].strip().split(",")
                    total_frames = int(info[0].replace("frames", "").strip())
            except Exception:
                pass
        elif line_s.startswith("Rendered "):
            frames_rendered = line_s

    stderr_out = proc.stderr.read()
    proc.wait()
    t_end = time.time()
    total_wall_clock = t_end - t_start

    print(f"\n🏁 Finished {label} in {total_wall_clock:.2f}s (Exit code: {proc.returncode})")
    if stderr_out:
        print(f"   Stderr: {stderr_out[:300]}")

    # Inspect produced artifacts
    mp4_files = list(out_dir.glob("*.mp4"))
    final_mp4 = [f for f in mp4_files if "final" in f.name] or mp4_files
    mp4_path = final_mp4[0] if final_mp4 else None
    
    ffprobe_info = {}
    if mp4_path and mp4_path.exists():
        size_mb = mp4_path.stat().st_size / (1024 * 1024)
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size:stream=width,height,r_frame_rate,codec_name",
            "-of", "json", str(mp4_path)
        ]
        probe_proc = subprocess.run(probe_cmd, capture_output=True, text=True)
        try:
            ffprobe_info = json.loads(probe_proc.stdout)
        except Exception:
            pass
    else:
        size_mb = 0

    result = {
        "label": label,
        "html_file": str(html_path),
        "total_wall_clock_seconds": round(total_wall_clock, 2),
        "exit_code": proc.returncode,
        "meta_line": meta_line,
        "total_frames": total_frames,
        "mp4_file": str(mp4_path) if mp4_path else None,
        "size_mb": round(size_mb, 2),
        "ffprobe": ffprobe_info
    }
    return result

def main():
    if not HTML_24FPS.exists():
        print(f"Error: {HTML_24FPS} does not exist. Run node _process/make_phoenix_film.mjs first!")
        sys.exit(1)

    # 1. Run 12fps benchmark first (faster, tests if 12fps reduces compute by ~50%)
    html_12fps = Path("/tmp/t10_canh_chim_12fps.html")
    prepare_12fps_html(HTML_24FPS, html_12fps)
    res_12fps = run_render_benchmark(html_12fps, Path("/tmp/t10_direct_bench/12fps"), "12fps-Archival")

    # 2. Run 24fps benchmark (the exact setting T10 ran)
    res_24fps = run_render_benchmark(HTML_24FPS, Path("/tmp/t10_direct_bench/24fps"), "24fps-Default")

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "12fps": res_12fps,
        "24fps": res_24fps
    }

    out_json = WORKSPACE / "tests/agent_eval/results/phase4a1/t10_pure_render_benchmark.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("📊 [T10 DIRECT COMPUTE BENCHMARK SUMMARY]")
    print(f"  12 FPS: {res_12fps['total_wall_clock_seconds']}s | Frames: {res_12fps['total_frames']} | MP4: {res_12fps['size_mb']}MB")
    print(f"  24 FPS: {res_24fps['total_wall_clock_seconds']}s | Frames: {res_24fps['total_frames']} | MP4: {res_24fps['size_mb']}MB")
    print(f"  Saved benchmark record to: {out_json}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
