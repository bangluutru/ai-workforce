#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm thử bộ định tuyến kết xuất (Render Router) và Render Adapters.
"""

import sys
from pathlib import Path
import pytest

SHARED_DIR = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED_DIR))
import bootstrap  # noqa: F401,E402

from creative.renderers.base import BaseRenderAdapter, RenderJob, RenderResult
from creative.renderers.hyperframes_adapter import HyperFramesAdapter, find_hyperframes_binary
from creative.renderers.canvas_adapter import Canvas2DAdapter
from creative.render_router import RenderRouter, render_scene


class MockFailingAdapter(BaseRenderAdapter):
    """Adapter giả lập lỗi để kiểm thử cơ chế fallback."""
    @property
    def name(self) -> str:
        return "mock_failing"

    def is_available(self) -> bool:
        return True

    def get_capabilities(self) -> dict:
        return {"name": "mock_failing"}

    def render(self, job: RenderJob) -> RenderResult:
        return RenderResult(
            job_id=job.job_id,
            success=False,
            adapter_name=self.name,
            error_message="Lỗi giả lập từ mock adapter",
        )


class MockSucceedingAdapter(BaseRenderAdapter):
    """Adapter giả lập thành công cho fallback."""
    @property
    def name(self) -> str:
        return "mock_succeeding"

    def is_available(self) -> bool:
        return True

    def get_capabilities(self) -> dict:
        return {"name": "mock_succeeding"}

    def render(self, job: RenderJob) -> RenderResult:
        return RenderResult(
            job_id=job.job_id,
            success=True,
            output_path="/tmp/mock_output.mp4",
            duration=job.duration,
            render_time_seconds=1.5,
            frame_count=int(job.duration * job.fps),
            fps=float(job.fps),
            width=job.width,
            height=job.height,
            file_size_bytes=10240,
            adapter_name=self.name,
        )


def test_render_job_validation():
    """Kiểm tra thẩm định tính hợp lệ của RenderJob."""
    # Hợp lệ
    job = RenderJob(job_id="job_01", template_path="01_fade_in", duration=5.0)
    job.validate()
    assert job.width == 1920
    assert job.height == 1080
    assert job.fps == 30

    # Rỗng job_id
    with pytest.raises(ValueError, match="job_id không được để trống"):
        RenderJob(job_id="", template_path="01_fade_in", duration=5.0).validate()

    # Rỗng template_path
    with pytest.raises(ValueError, match="template_path không được để trống"):
        RenderJob(job_id="j1", template_path="", duration=5.0).validate()

    # Thời lượng âm
    with pytest.raises(ValueError, match="duration phải > 0"):
        RenderJob(job_id="j1", template_path="01_fade_in", duration=-2.0).validate()

    # Resolution không hợp lệ
    with pytest.raises(ValueError, match="Kích thước resolution không hợp lệ"):
        RenderJob(job_id="j1", template_path="01_fade_in", duration=5.0, width=0).validate()

    # FPS không chuẩn
    with pytest.raises(ValueError, match="fps phải là 24, 25, 30 hoặc 60"):
        RenderJob(job_id="j1", template_path="01_fade_in", duration=5.0, fps=45).validate()


def test_render_result_metrics():
    """Kiểm tra các chỉ số tính toán trong RenderResult."""
    res = RenderResult(
        job_id="j_metric",
        success=True,
        output_path="/tmp/v.mp4",
        duration=10.0,
        render_time_seconds=5.0,
        frame_count=300,
        fps=30.0,
    )
    assert res.fps_throughput == 60.0  # 300 / 5.0
    assert res.realtime_ratio == 0.5   # 5.0 / 10.0


def test_hyperframes_adapter_capabilities():
    """Kiểm tra bản đồ năng lực của HyperFramesAdapter."""
    adapter = HyperFramesAdapter()
    caps = adapter.get_capabilities()
    assert caps["name"] == "hyperframes"
    assert caps["engine_type"] == "html5_gsap"
    assert caps["hardware_acceleration"] is True
    assert "static_frame_deduplication" in caps["features"]
    assert adapter.is_available() is True  # Khả dụng do có sandbox trong _process


def test_canvas_adapter_capabilities():
    """Kiểm tra bản đồ năng lực của Canvas2DAdapter."""
    adapter = Canvas2DAdapter()
    caps = adapter.get_capabilities()
    assert caps["name"] == "canvas"
    assert caps["engine_type"] == "canvas_2d_fallback"
    assert adapter.is_available() is True  # Có ffmpeg trên macOS


def test_render_router_lifecycle():
    """Kiểm tra chu trình định tuyến của RenderRouter."""
    router = RenderRouter()
    available = router.list_available_adapters()
    assert "hyperframes" in available
    assert "canvas" in available

    job = RenderJob(job_id="test_route", template_path="01_fade_in", duration=4.0)
    routed = router.route_job(job)
    assert routed.name == "hyperframes"

    # Kiểm tra ép buộc adapter qua force_adapter
    job_forced = RenderJob(
        job_id="test_forced",
        template_path="01_fade_in",
        duration=4.0,
        adapter_options={"force_adapter": "canvas"}
    )
    routed_canvas = router.route_job(job_forced)
    assert routed_canvas.name == "canvas"

    # Yêu cầu adapter không tồn tại
    job_invalid = RenderJob(
        job_id="test_err",
        template_path="01_fade_in",
        duration=4.0,
        adapter_options={"force_adapter": "unknown_adapter"}
    )
    with pytest.raises(ValueError, match="chưa được đăng ký"):
        router.route_job(job_invalid)


def test_render_router_automatic_fallback():
    """Kiểm tra cơ chế tự động chuyển tiếp sang fallback adapter khi adapter chính lỗi."""
    router = RenderRouter(default_adapter="mock_failing", fallback_adapter="mock_succeeding", allow_fallback=True)
    router.register_adapter(MockFailingAdapter())
    router.register_adapter(MockSucceedingAdapter())

    job = RenderJob(job_id="fb_job", template_path="01_fade_in", duration=3.0)
    result = router.render(job)

    assert result.success is True
    assert result.adapter_name == "mock_succeeding"
    assert "Đã tự động phục hồi lỗi" in result.stderr


def test_canvas_adapter_actual_render(tmp_path):
    """Kiểm tra Canvas2DAdapter thực hiện kết xuất thực tế một video ngắn 1 giây bằng FFmpeg."""
    adapter = Canvas2DAdapter()
    out_file = str(tmp_path / "test_canvas.mp4")
    job = RenderJob(
        job_id="canvas_test",
        template_path="01_fade_in",
        duration=1.0,
        width=640,
        height=360,
        fps=24,
        output_path=out_file,
        props={"title": "Test Canvas Direct", "bg_color": "#0B0C10"}
    )
    res = adapter.render(job)
    assert res.success is True
    assert Path(out_file).is_file()
    assert Path(out_file).stat().st_size > 0
    assert res.duration == pytest.approx(1.0, abs=0.1)
