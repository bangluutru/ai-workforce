#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Base Render Adapter (Luật R7).
Định nghĩa giao diện hợp đồng trừu tượng (Abstract Interface) và cấu trúc dữ liệu
cho các động cơ kết xuất video chuyển động (Render Engines).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RenderJob:
    """
    Hợp đồng dữ liệu yêu cầu kết xuất một phân cảnh (Scene Render Job).
    """
    job_id: str
    template_path: str  # Đường dẫn file HTML hoặc tên preset (vd: '01_fade_in')
    duration: float  # Thời lượng phân cảnh (giây)
    width: int = 1920
    height: int = 1080
    fps: int = 30
    props: Dict[str, Any] = field(default_factory=dict)
    output_path: str = ""
    brand_profile: Optional[Dict[str, Any]] = None
    timeout_seconds: float = 120.0
    adapter_options: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Kiểm tra tính hợp lệ cơ bản của thông số render job."""
        if not self.job_id:
            raise ValueError("job_id không được để trống")
        if not self.template_path:
            raise ValueError("template_path không được để trống")
        if self.duration <= 0.0:
            raise ValueError(f"duration phải > 0, nhận được {self.duration}")
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Kích thước resolution không hợp lệ: {self.width}x{self.height}")
        if self.fps not in (24, 25, 30, 60):
            raise ValueError(f"Tốc độ khung hình fps phải là 24, 25, 30 hoặc 60, nhận được {self.fps}")
        if self.timeout_seconds <= 0.0:
            raise ValueError(f"timeout_seconds phải > 0, nhận được {self.timeout_seconds}")


@dataclass
class RenderResult:
    """
    Kết quả trả về sau khi thực thi một RenderJob.
    """
    job_id: str
    success: bool
    output_path: str = ""
    duration: float = 0.0
    render_time_seconds: float = 0.0
    frame_count: int = 0
    fps: float = 0.0
    width: int = 0
    height: int = 0
    file_size_bytes: int = 0
    adapter_name: str = ""
    error_message: Optional[str] = None
    stdout: str = ""
    stderr: str = ""

    @property
    def fps_throughput(self) -> float:
        """Tốc độ kết xuất thực tế (FPS throughput = frame_count / render_time_seconds)."""
        if self.render_time_seconds > 0 and self.frame_count > 0:
            return round(self.frame_count / self.render_time_seconds, 2)
        return 0.0

    @property
    def realtime_ratio(self) -> float:
        """Tỷ số thời gian thực (render_time_seconds / duration). Giá trị < 1.0 nghĩa là nhanh hơn thời gian thực."""
        if self.duration > 0 and self.render_time_seconds > 0:
            return round(self.render_time_seconds / self.duration, 2)
        return 0.0


class BaseRenderAdapter(abc.ABC):
    """
    Lớp trừu tượng định nghĩa giao diện chung cho mọi Render Engine trong Creative Studio 2.0.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Tên định danh duy nhất của adapter (vd: 'hyperframes', 'canvas')."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Kiểm tra xem adapter và môi trường thực thi (CLI, runtime) có sẵn sàng không."""
        pass

    @abc.abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Trả về bản đồ năng lực của engine (định dạng hỗ trợ, GPU, concurrency, ...)."""
        pass

    @abc.abstractmethod
    def render(self, job: RenderJob) -> RenderResult:
        """
        Thực thi kết xuất phân cảnh theo mô tả của job.
        
        Args:
            job: Đối tượng RenderJob chứa đầy đủ thông số.
            
        Returns:
            RenderResult: Kết quả kết xuất, file xuất ra, thời gian thực thi hoặc thông báo lỗi.
        """
        pass
