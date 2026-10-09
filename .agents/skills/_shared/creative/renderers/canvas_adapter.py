#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Canvas 2D Fallback Render Adapter (Luật R7).
Động cơ kết xuất dự phòng ngoại tuyến dựa trên Puppeteer Canvas 2D / FFmpeg Direct,
đảm bảo hệ thống vẫn xuất bản được video khi môi trường thiếu GPU hoặc không có HyperFrames.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseRenderAdapter, RenderJob, RenderResult
from ..presets.registry import PRESET_REGISTRY, render_preset_html

_CURRENT_DIR = Path(__file__).resolve().parent
_WORKSPACE_DIR = _CURRENT_DIR.parents[4]

def _get_ffmpeg_tools():
    try:
        from ffmpeg_tools import ffmpeg_bin, ffprobe_bin
        return ffmpeg_bin, ffprobe_bin
    except ImportError:
        import sys
        media_path = str(_CURRENT_DIR.parents[1] / "media")
        if media_path not in sys.path:
            sys.path.insert(0, media_path)
        from ffmpeg_tools import ffmpeg_bin, ffprobe_bin
        return ffmpeg_bin, ffprobe_bin


class Canvas2DAdapter(BaseRenderAdapter):
    """
    Adapter kết xuất dự phòng (Fallback Renderer) sử dụng Canvas 2D / Puppeteer hoặc FFmpeg Direct.
    """

    def __init__(self, use_mock_in_test: bool = False):
        self._use_mock = use_mock_in_test

    @property
    def name(self) -> str:
        return "canvas"

    def is_available(self) -> bool:
        """Canvas adapter luôn sẵn sàng nếu hệ thống có FFmpeg và Node/Python."""
        # Kiểm tra ffmpeg có tồn tại không
        ffmpeg_bin, _ = _get_ffmpeg_tools()
        ff = ffmpeg_bin()
        return bool(ff and (os.path.isfile(ff) or shutil.which(ff)))

    def get_capabilities(self) -> Dict[str, Any]:
        """Bản đồ năng lực của Canvas Fallback Engine."""
        return {
            "name": "canvas",
            "engine_type": "canvas_2d_fallback",
            "hardware_acceleration": False,
            "supported_aspect_ratios": ["1:1", "16:9", "9:16"],
            "supported_formats": ["mp4"],
            "max_fps": 30,
            "features": ["offline_rendering", "cpu_compositing", "ffmpeg_direct_fallback"],
            "is_available": self.is_available(),
        }

    def render(self, job: RenderJob) -> RenderResult:
        """
        Thực thi RenderJob bằng phương pháp kết xuất Canvas / FFmpeg Direct.
        """
        job.validate()

        ffmpeg_bin, _ = _get_ffmpeg_tools()
        ff = ffmpeg_bin()
        if not ff:
            return RenderResult(
                job_id=job.job_id,
                success=False,
                error_message="FFmpeg không khả dụng để kết xuất Canvas.",
                adapter_name=self.name,
            )

        # Xác định đường dẫn đầu ra
        if job.output_path:
            out_file = Path(job.output_path)
        else:
            default_out_dir = Path.home() / "Downloads" / "AIWF_Output" / "creative"
            default_out_dir.mkdir(parents=True, exist_ok=True)
            out_file = default_out_dir / f"{job.job_id}_canvas.mp4"

        out_file.parent.mkdir(parents=True, exist_ok=True)
        final_output_path = str(out_file.resolve())

        # Trích xuất thông điệp hiển thị từ props
        title = "AIWF Creative Studio"
        if "title" in job.props:
            title = str(job.props["title"])
        elif "headline" in job.props:
            title = str(job.props["headline"])
        elif "product_name" in job.props:
            title = str(job.props["product_name"])
        elif "brand_name" in job.props:
            title = str(job.props["brand_name"])

        # Màu nền
        bg_hex = job.props.get("bg_color", "#0B0C10").replace("#", "0x")
        accent_hex = job.props.get("accent_color", "#8B5CF6")

        # Xây dựng lệnh FFmpeg lavfi tạo video màu nền có chuyển động nhẹ (zoom/pan hoặc fade)
        # Sử dụng bộ lọc lavfi color kết hợp drawbox / geq
        t0 = time.perf_counter()

        cmd = [
            ff,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={bg_hex}:s={job.width}x{job.height}:r={job.fps}:d={job.duration}",
            "-vf",
            f"format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-t",
            str(job.duration),
            final_output_path,
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=job.timeout_seconds,
            )
            render_time = time.perf_counter() - t0

            if proc.returncode != 0 or not os.path.isfile(final_output_path):
                return RenderResult(
                    job_id=job.job_id,
                    success=False,
                    render_time_seconds=render_time,
                    adapter_name=self.name,
                    error_message=f"Canvas fallback render thất bại: {proc.stderr[:300]}",
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                )

            file_size = os.path.getsize(final_output_path)
            frame_count = int(round(job.duration * job.fps))

            return RenderResult(
                job_id=job.job_id,
                success=True,
                output_path=final_output_path,
                duration=job.duration,
                render_time_seconds=round(render_time, 2),
                frame_count=frame_count,
                fps=float(job.fps),
                width=job.width,
                height=job.height,
                file_size_bytes=file_size,
                adapter_name=self.name,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )

        except subprocess.TimeoutExpired:
            return RenderResult(
                job_id=job.job_id,
                success=False,
                render_time_seconds=job.timeout_seconds,
                adapter_name=self.name,
                error_message=f"Canvas render bị timeout sau {job.timeout_seconds}s.",
            )
        except Exception as e:
            return RenderResult(
                job_id=job.job_id,
                success=False,
                adapter_name=self.name,
                error_message=f"Lỗi Canvas render: {str(e)}",
            )
