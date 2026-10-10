#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Fallback Transparency and Capability Downgrade Protection (Fix 4).
Kiểm tra tính minh bạch của cơ chế fallback trong RenderRouter:
- Bổ sung trường requested_renderer, actual_renderer, fallback_used, degraded, fallback_reason
- Cảnh báo rõ ràng cho người dùng khi sử dụng fallback renderer
- Ngăn chặn silently downgrade khi thiếu capability bắt buộc của scene
"""

import pytest
from pathlib import Path
import sys

SHARED_DIR = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

from creative.renderers.base import BaseRenderAdapter, RenderJob, RenderResult
from creative.render_router import RenderRouter


class MockFailingPrimaryAdapter(BaseRenderAdapter):
    """Adapter chính giả lập bị lỗi (ví dụ GPU driver crash hoặc CLI timeout)."""

    @property
    def name(self) -> str:
        return "hyperframes"

    def is_available(self) -> bool:
        return True

    def get_capabilities(self):
        return {"name": "hyperframes", "features": ["gpu_acceleration", "webgl", "html5_gsap"]}

    def render(self, job: RenderJob) -> RenderResult:
        return RenderResult(
            job_id=job.job_id,
            success=False,
            adapter_name=self.name,
            error_message="Headless Chrome GPU process crashed with exit code 1",
        )


class MockWorkingPrimaryAdapter(BaseRenderAdapter):
    """Adapter chính hoạt động bình thường."""

    @property
    def name(self) -> str:
        return "hyperframes"

    def is_available(self) -> bool:
        return True

    def get_capabilities(self):
        return {"name": "hyperframes", "features": ["gpu_acceleration", "webgl"]}

    def render(self, job: RenderJob) -> RenderResult:
        return RenderResult(
            job_id=job.job_id,
            success=True,
            adapter_name=self.name,
            duration=job.duration,
            output_path="/tmp/output.mp4",
        )


class MockFallbackAdapter(BaseRenderAdapter):
    """Adapter dự phòng hoạt động qua Canvas 2D."""

    @property
    def name(self) -> str:
        return "canvas"

    def is_available(self) -> bool:
        return True

    def get_capabilities(self):
        return {"name": "canvas", "features": ["cpu_compositing", "ffmpeg_direct_fallback"]}

    def render(self, job: RenderJob) -> RenderResult:
        return RenderResult(
            job_id=job.job_id,
            success=True,
            adapter_name=self.name,
            duration=job.duration,
            output_path="/tmp/canvas_output.mp4",
        )


def test_primary_render_success_metadata():
    """Khi render chính thành công, không kích hoạt fallback và không degraded."""
    router = RenderRouter(allow_fallback=True)
    router.register_adapter(MockWorkingPrimaryAdapter())
    router.register_adapter(MockFallbackAdapter())

    job = RenderJob(job_id="job_01", template_path="01_fade_in", duration=3.0)
    result = router.render(job)

    assert result.success is True
    assert result.requested_renderer == "hyperframes"
    assert result.actual_renderer == "hyperframes"
    assert result.fallback_used is False
    assert result.degraded is False
    assert result.fallback_reason is None
    assert result.user_warning is None


def test_fallback_activation_transparency():
    """Khi render chính thất bại và fallback thành công, thông tin degradation phải minh bạch."""
    router = RenderRouter(allow_fallback=True)
    router.register_adapter(MockFailingPrimaryAdapter())
    router.register_adapter(MockFallbackAdapter())

    job = RenderJob(job_id="job_fallback", template_path="01_fade_in", duration=3.0)
    result = router.render(job)

    # Thành công nhờ fallback nhưng phải minh bạch degradation
    assert result.success is True
    assert result.requested_renderer == "hyperframes"
    assert result.actual_renderer == "canvas"
    assert result.fallback_used is True
    assert result.degraded is True
    assert "Headless Chrome GPU process crashed" in (result.fallback_reason or "")
    assert result.user_warning is not None
    assert "Render completed using fallback renderer" in result.user_warning
    assert "Visual output may differ" in result.user_warning


def test_prevent_silent_downgrade_when_gpu_required():
    """Khi scene yêu cầu bắt buộc GPU, không được silently downgrade sang Canvas."""
    router = RenderRouter(allow_fallback=True)
    router.register_adapter(MockFailingPrimaryAdapter())
    router.register_adapter(MockFallbackAdapter())

    job = RenderJob(
        job_id="job_gpu_strict",
        template_path="01_fade_in",
        duration=3.0,
        adapter_options={"require_gpu": True},
    )
    result = router.render(job)

    assert result.success is False
    assert result.fallback_used is False
    assert result.degraded is True
    assert "REQUIRES_USER_REVIEW" in (result.error_message or "")


def test_prevent_silent_downgrade_when_capability_missing():
    """Khi scene yêu cầu capability mà fallback không hỗ trợ, không được silently fallback."""
    router = RenderRouter(allow_fallback=True)
    router.register_adapter(MockFailingPrimaryAdapter())
    router.register_adapter(MockFallbackAdapter())

    job = RenderJob(
        job_id="job_cap_strict",
        template_path="01_fade_in",
        duration=3.0,
        adapter_options={"required_capabilities": ["webgl", "3d_transforms"]},
    )
    result = router.render(job)

    assert result.success is False
    assert result.fallback_used is False
    assert result.degraded is True
    assert "Fallback unsupported for required capabilities" in (result.error_message or "")
