#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Render Router (Luật R7).
Bộ điều phối kết xuất thông minh, tự động định tuyến RenderJob tới engine tối ưu nhất
(HyperFrames GPU/Metal Compositing hoặc Canvas 2D Fallback) kèm cơ chế tự phục hồi lỗi.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .renderers.base import BaseRenderAdapter, RenderJob, RenderResult
from .renderers.hyperframes_adapter import HyperFramesAdapter
from .renderers.canvas_adapter import Canvas2DAdapter

logger = logging.getLogger("aiwf.creative.router")


class RenderRouter:
    """
    Bộ định tuyến kết xuất thông minh cho Creative Studio 2.0.
    """

    def __init__(
        self,
        default_adapter: str = "hyperframes",
        fallback_adapter: str = "canvas",
        allow_fallback: bool = True,
    ):
        self.default_adapter_name = default_adapter
        self.fallback_adapter_name = fallback_adapter
        self.allow_fallback = allow_fallback
        self._adapters: Dict[str, BaseRenderAdapter] = {}

        # Tự động đăng ký các adapters chuẩn
        self.register_adapter(HyperFramesAdapter())
        self.register_adapter(Canvas2DAdapter())

    def register_adapter(self, adapter: BaseRenderAdapter) -> None:
        """Đăng ký một adapter mới vào router."""
        self._adapters[adapter.name] = adapter

    def get_adapter(self, name: str) -> Optional[BaseRenderAdapter]:
        """Lấy adapter theo tên định danh."""
        return self._adapters.get(name)

    def list_available_adapters(self) -> List[str]:
        """Liệt kê danh sách các adapter đang thực sự khả dụng trên máy hiện tại."""
        return [name for name, adapter in self._adapters.items() if adapter.is_available()]

    def route_job(self, job: RenderJob) -> BaseRenderAdapter:
        """
        Xác định adapter thích hợp nhất cho RenderJob.
        
        Quy tắc định tuyến:
        1. Nếu job chỉ định 'force_adapter' trong adapter_options: ưu tiên tuyệt đối adapter đó.
        2. Nếu default_adapter ('hyperframes') khả dụng: chọn default_adapter.
        3. Nếu fallback_adapter ('canvas') khả dụng: chọn fallback_adapter.
        4. Nếu không có adapter nào khả dụng: báo lỗi RuntimeError.
        """
        # 1. Kiểm tra force_adapter
        forced = job.adapter_options.get("force_adapter")
        if forced:
            adapter = self._adapters.get(forced)
            if not adapter:
                raise ValueError(f"Adapter được yêu cầu '{forced}' chưa được đăng ký trong router.")
            if not adapter.is_available():
                raise RuntimeError(f"Adapter được yêu cầu '{forced}' hiện không khả dụng trong môi trường.")
            return adapter

        # 2. Thử default adapter
        default_adapter = self._adapters.get(self.default_adapter_name)
        if default_adapter and default_adapter.is_available():
            return default_adapter

        # 3. Thử fallback adapter
        fallback_adapter = self._adapters.get(self.fallback_adapter_name)
        if fallback_adapter and fallback_adapter.is_available():
            return fallback_adapter

        # 4. Tìm bất kỳ adapter nào khả dụng
        available = self.list_available_adapters()
        if available:
            return self._adapters[available[0]]

        raise RuntimeError("Không có Render Adapter nào khả dụng trên hệ thống.")

    def render(self, job: RenderJob, allow_fallback: Optional[bool] = None) -> RenderResult:
        """
        Thực thi RenderJob với cơ chế dự phòng tự động (Automatic Fallback).
        """
        job.validate()
        primary_adapter = self.route_job(job)
        result = primary_adapter.render(job)

        should_fallback = self.allow_fallback if allow_fallback is None else allow_fallback

        # Nếu adapter chính thất bại và cho phép fallback
        if not result.success and should_fallback:
            fallback_name = self.fallback_adapter_name
            if primary_adapter.name != fallback_name:
                fallback_adapter = self._adapters.get(fallback_name)
                if fallback_adapter and fallback_adapter.is_available():
                    logger.warning(
                        f"Render chính '{primary_adapter.name}' thất bại: {result.error_message}. "
                        f"Kích hoạt chuyển hướng sang '{fallback_name}'."
                    )
                    fallback_result = fallback_adapter.render(job)
                    if fallback_result.success:
                        fallback_result.stderr += (
                            f"\n[AIWF Router Note] Đã tự động phục hồi lỗi từ {primary_adapter.name} "
                            f"bằng {fallback_name} fallback."
                        )
                        return fallback_result

        return result


def render_scene(
    job_id: str,
    template_path: str,
    duration: float,
    output_path: str = "",
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    props: Optional[Dict[str, Any]] = None,
    brand_profile: Optional[Dict[str, Any]] = None,
    router: Optional[RenderRouter] = None,
) -> RenderResult:
    """
    Hàm tiện ích cấp cao để kết xuất nhanh một phân cảnh.
    """
    router_instance = router or RenderRouter()
    job = RenderJob(
        job_id=job_id,
        template_path=template_path,
        duration=duration,
        output_path=output_path,
        width=width,
        height=height,
        fps=fps,
        props=props or {},
        brand_profile=brand_profile,
    )
    return router_instance.render(job)
