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
        Thực thi RenderJob với cơ chế dự phòng tự động và minh bạch trạng thái fallback (Fix 4).
        """
        job.validate()
        primary_adapter = self.route_job(job)
        requested_renderer = primary_adapter.name

        result = primary_adapter.render(job)
        result.requested_renderer = requested_renderer
        result.actual_renderer = primary_adapter.name
        result.fallback_used = False
        result.degraded = False

        should_fallback = self.allow_fallback if allow_fallback is None else allow_fallback

        # Nếu adapter chính thất bại và cho phép fallback
        if not result.success and should_fallback:
            fallback_name = self.fallback_adapter_name
            if primary_adapter.name != fallback_name:
                fallback_adapter = self._adapters.get(fallback_name)
                if fallback_adapter and fallback_adapter.is_available():
                    # Kiểm tra capabilities bắt buộc của scene trước khi fallback
                    required_caps = job.adapter_options.get("required_capabilities", [])
                    fallback_caps = fallback_adapter.get_capabilities()
                    supported_features = set(fallback_caps.get("features", []))
                    missing_caps = [c for c in required_caps if c not in supported_features]

                    # Nếu scene yêu cầu GPU hoặc capability mà fallback không có -> KHÔNG silently downgrade
                    require_gpu = job.adapter_options.get("require_gpu", False)
                    disallow_fallback = job.adapter_options.get("disallow_fallback", False)

                    if require_gpu or disallow_fallback or missing_caps:
                        logger.warning(
                            f"Render chính '{primary_adapter.name}' thất bại và fallback '{fallback_name}' "
                            f"không đáp ứng capabilities bắt buộc (missing: {missing_caps}, require_gpu: {require_gpu}). "
                            f"Hủy bỏ fallback để tránh silently downgrade."
                        )
                        result.requested_renderer = requested_renderer
                        result.actual_renderer = primary_adapter.name
                        result.fallback_used = False
                        result.degraded = True
                        result.fallback_reason = (
                            f"Primary failed: {result.error_message}. Fallback '{fallback_name}' cannot satisfy "
                            f"required capabilities: {missing_caps or ['gpu_acceleration']}."
                        )
                        result.error_message = (
                            f"{result.error_message}. Fallback unsupported for required capabilities (REQUIRES_USER_REVIEW)."
                        )
                        return result

                    logger.warning(
                        f"Render chính '{primary_adapter.name}' thất bại: {result.error_message}. "
                        f"Kích hoạt chuyển hướng sang '{fallback_name}'."
                    )
                    fallback_result = fallback_adapter.render(job)
                    fallback_result.requested_renderer = requested_renderer
                    fallback_result.actual_renderer = fallback_adapter.name
                    fallback_result.fallback_used = True
                    fallback_result.degraded = True
                    fallback_result.fallback_reason = (
                        f"Primary renderer '{primary_adapter.name}' failed: {result.error_message or 'unavailable'}"
                    )
                    fallback_result.user_warning = (
                        "⚠ Render completed using fallback renderer. "
                        "Visual output may differ from the requested composition."
                    )
                    fallback_result.stderr += (
                        f"\n[AIWF Router Note] Đã tự động phục hồi lỗi từ {primary_adapter.name} "
                        f"bằng {fallback_name} fallback. {fallback_result.user_warning} "
                        f"(Reason: {fallback_result.fallback_reason})"
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
