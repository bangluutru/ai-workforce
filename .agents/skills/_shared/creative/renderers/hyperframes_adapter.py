#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — HyperFrames Render Adapter (Luật R7).
Động cơ kết xuất đồ họa chuyển động HTML5/GSAP sang MP4 với hiệu năng cao,
tận dụng GPU Metal/Vulkan và cơ chế Static Frame Deduplication.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseRenderAdapter, RenderJob, RenderResult
from ..presets.registry import PRESET_REGISTRY, render_preset_html

# Đường dẫn mặc định trong sandbox tách biệt (bảo vệ codebase)
_CURRENT_DIR = Path(__file__).resolve().parent
_WORKSPACE_DIR = _CURRENT_DIR.parents[4]  # .agents/skills/_shared/creative/renderers -> workspace
_SANDBOX_BIN = _WORKSPACE_DIR / "_process" / "hyperframes_sandbox" / "node_modules" / ".bin" / "hyperframes"


def find_hyperframes_binary() -> Optional[str]:
    """Tìm kiếm nhị phân HyperFrames CLI theo thứ tự ưu tiên."""
    # 1. Biến môi trường chỉ định rõ
    env_bin = os.getenv("HYPERFRAMES_BIN")
    if env_bin and os.path.isfile(env_bin) and os.access(env_bin, os.X_OK):
        return env_bin

    # 2. Thư mục sandbox cô lập của dự án
    if _SANDBOX_BIN.is_file() and os.access(_SANDBOX_BIN, os.X_OK):
        return str(_SANDBOX_BIN)

    # 3. PATH toàn cục của hệ điều hành
    which_bin = shutil.which("hyperframes")
    if which_bin:
        return which_bin

    return None


class HyperFramesAdapter(BaseRenderAdapter):
    """
    Adapter kết xuất video sử dụng HyperFrames CLI và Headless Chrome.
    """

    def __init__(self, binary_path: Optional[str] = None):
        self._custom_binary = binary_path

    @property
    def name(self) -> str:
        return "hyperframes"

    def is_available(self) -> bool:
        """Kiểm tra sự tồn tại của nhị phân HyperFrames CLI."""
        bin_path = self._custom_binary or find_hyperframes_binary()
        return bool(bin_path and os.path.isfile(bin_path) and os.access(bin_path, os.X_OK))

    def get_capabilities(self) -> Dict[str, Any]:
        """Bản đồ năng lực của HyperFrames Engine."""
        return {
            "name": "hyperframes",
            "engine_type": "html5_gsap",
            "hardware_acceleration": True,
            "supported_aspect_ratios": ["1:1", "16:9", "9:16", "4:5"],
            "supported_formats": ["mp4"],
            "max_fps": 60,
            "features": [
                "static_frame_deduplication",
                "metal_gpu_compositing",
                "css_glassmorphism",
                "deterministic_capture",
            ],
            "is_available": self.is_available(),
        }

    def render(self, job: RenderJob) -> RenderResult:
        """
        Thực thi RenderJob thông qua HyperFrames CLI.
        """
        job.validate()

        bin_path = self._custom_binary or find_hyperframes_binary()
        if not bin_path or not os.path.isfile(bin_path) or not os.access(bin_path, os.X_OK):
            return RenderResult(
                job_id=job.job_id,
                success=False,
                error_message="HyperFrames CLI không khả dụng hoặc chưa được cài đặt trong môi trường sandbox.",
                adapter_name=self.name,
            )

        # Chuẩn bị file HTML
        temp_html_file: Optional[Path] = None
        html_path: str = ""
        # Chuẩn bị project directory tạm thời cho HyperFrames CLI
        work_dir = _WORKSPACE_DIR / "_process" / "creative_temp" / job.job_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # 1. Ghi meta.json định nghĩa thông số kỹ thuật video
        meta_dict = {
            "fps": job.fps,
            "width": job.width,
            "height": job.height,
            "duration": job.duration,
        }
        (work_dir / "meta.json").write_text(json.dumps(meta_dict, indent=2), encoding="utf-8")

        # 2. Chuẩn bị index.html
        clean_preset = job.template_path.removesuffix(".html")
        if clean_preset in PRESET_REGISTRY:
            rendered_html = render_preset_html(
                preset_name=clean_preset,
                props=job.props,
                width=job.width,
                height=job.height,
                duration=job.duration,
                brand_profile=job.brand_profile,
            )
            (work_dir / "index.html").write_text(rendered_html, encoding="utf-8")
        else:
            provided_path = Path(job.template_path)
            if provided_path.is_dir() and (provided_path / "index.html").is_file():
                shutil.copy2(provided_path / "index.html", work_dir / "index.html")
            elif provided_path.is_file():
                shutil.copy2(provided_path, work_dir / "index.html")
            else:
                return RenderResult(
                    job_id=job.job_id,
                    success=False,
                    error_message=f"Không tìm thấy template HTML: {job.template_path}",
                    adapter_name=self.name,
                )

        # 3. Chuẩn bị đường dẫn đầu ra
        if job.output_path:
            out_file = Path(job.output_path)
        else:
            default_out_dir = Path.home() / "Downloads" / "AIWF_Output" / "creative"
            default_out_dir.mkdir(parents=True, exist_ok=True)
            out_file = default_out_dir / f"{job.job_id}.mp4"

        out_file.parent.mkdir(parents=True, exist_ok=True)
        final_output_path = str(out_file.resolve())

        # 4. Xây dựng lệnh CLI chuẩn mực của HyperFrames
        cmd: List[str] = [
            bin_path,
            "render",
            str(work_dir),
            "-o",
            final_output_path,
            "-f",
            str(job.fps),
        ]

        if "concurrency" in job.adapter_options:
            cmd.extend(["--batch-concurrency", str(job.adapter_options["concurrency"])])

        env = dict(os.environ)
        env["HYPERFRAMES_TELEMETRY"] = "0"
        env["DO_NOT_TRACK"] = "1"

        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=job.timeout_seconds,
                env=env,
            )
            render_time = time.perf_counter() - t0

            if proc.returncode != 0 or not os.path.isfile(final_output_path):
                return RenderResult(
                    job_id=job.job_id,
                    success=False,
                    output_path=final_output_path if os.path.isfile(final_output_path) else "",
                    render_time_seconds=render_time,
                    adapter_name=self.name,
                    error_message=f"HyperFrames render thất bại (exit code {proc.returncode}): {proc.stderr[:400]}",
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                )

            # Đọc kích thước file và thông tin video qua ffprobe nếu có
            file_size = os.path.getsize(final_output_path)
            frame_count = int(round(job.duration * job.fps))

            # Thử lấy duration chính xác từ file xuất ra
            measured_duration = job.duration
            try:
                from ffmpeg_tools import duration as ffprobe_duration
                measured_duration = ffprobe_duration(final_output_path)
            except Exception:
                pass

            return RenderResult(
                job_id=job.job_id,
                success=True,
                output_path=final_output_path,
                duration=measured_duration,
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
                error_message=f"Render bị quá thời gian giới hạn ({job.timeout_seconds}s).",
            )
        except Exception as e:
            return RenderResult(
                job_id=job.job_id,
                success=False,
                adapter_name=self.name,
                error_message=f"Lỗi ngoại lệ khi thực thi render: {str(e)}",
            )
        finally:
            # Dọn dẹp file HTML tạm nếu cần và nếu không yêu cầu giữ lại debug
            if temp_html_file and temp_html_file.is_file() and not job.adapter_options.get("keep_temp_html"):
                try:
                    temp_html_file.unlink(missing_ok=True)
                except Exception:
                    pass
