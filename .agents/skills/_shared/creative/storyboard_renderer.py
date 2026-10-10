#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Storyboard Renderer (Luật R7).
Động cơ kết xuất toàn diện kịch bản phân cảnh Storyboard v2.0 thành video hoàn chỉnh MP4,
tích hợp RenderRouter, 10 Motion Presets, trộn âm thanh narration + BGM và Visual QA 2.0.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Đảm bảo import được các module dùng chung
CREATIVE_DIR = Path(__file__).resolve().parent
SHARED_DIR = CREATIVE_DIR.parent
MEDIA_DIR = SHARED_DIR / "media"
for p in (CREATIVE_DIR, SHARED_DIR, MEDIA_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from .audio_track import LEGACY_MODE, AudioPlanError, mix_audio, parse_audio_spec, plan_audio
from .brand_profile import load_brand_profile
from .presets.registry import (
    PRESET_REGISTRY,
    get_preset_metadata,
    list_presets,
    missing_demo_props,
    render_preset_html,
)
from .qa.report_builder import QAReport, run_visual_qa
from .qa.dom_validator import validate_dom_layout
from .render_router import RenderJob, RenderResult, RenderRouter
from .storyboard_schema import ASPECT_RATIOS
from .storyboard_validator import validate_storyboard
from .transitions import build_concat_filter, plan_transitions

import bootstrap  # noqa: F401 (Luật R7: nạp đường dẫn _shared dùng chung)
from ffmpeg_tools import ffmpeg_bin, ffprobe_bin

logger = logging.getLogger("aiwf.creative.storyboard_renderer")


@dataclass
class StoryboardRenderResult:
    """Kết quả kết xuất toàn bộ storyboard."""
    success: bool
    output_mp4: str = ""
    qa_report: Optional[QAReport] = None
    contact_sheet: str = ""
    technical_report_json: str = ""
    total_duration: float = 0.0
    scene_clips: List[str] = field(default_factory=list)
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)
    # FIX 3 & FIX 4 additions
    fallback_used: bool = False
    degraded: bool = False
    actual_renderers: List[str] = field(default_factory=list)
    dom_qa_results: List[Dict[str, Any]] = field(default_factory=list)
    # Creative Studio 2.1: minh bạch về âm thanh
    audio_mode: str = LEGACY_MODE
    audio_report: Dict[str, Any] = field(default_factory=dict)


class StoryboardRenderer:
    """
    Trình điều phối kết xuất đa cảnh cho Storyboard v2.0.
    """

    def __init__(self, router: Optional[RenderRouter] = None):
        self.router = router or RenderRouter()

    def render_storyboard(
        self,
        storyboard: Union[Dict[str, Any], str, Path],
        output_path: Optional[Union[str, Path]] = None,
        work_dir: Optional[Union[str, Path]] = None,
        run_qa: bool = True,
        force_adapter: Optional[str] = None,
    ) -> StoryboardRenderResult:
        """
        Thực hiện toàn bộ quy trình kết xuất Storyboard v2.0 ra MP4 hoàn chỉnh.
        """
        # 1. Đọc và chuẩn hóa dữ liệu kịch bản
        if isinstance(storyboard, (str, Path)):
            sb_path = Path(storyboard)
            if not sb_path.exists():
                return StoryboardRenderResult(
                    success=False,
                    error_message=f"Tệp storyboard không tồn tại: {sb_path}"
                )
            with open(sb_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        elif isinstance(storyboard, dict):
            raw_data = storyboard
        else:
            return StoryboardRenderResult(
                success=False,
                error_message=f"Dữ liệu storyboard không hợp lệ: {type(storyboard)}"
            )

        # 2. Thẩm định kịch bản theo schema
        is_valid, errors = validate_storyboard(raw_data)
        if not is_valid:
            return StoryboardRenderResult(
                success=False,
                error_message=f"Storyboard không hợp lệ: {'; '.join(errors)}"
            )

        project_id = raw_data.get("project_id", "creative_project")
        fps = raw_data.get("fps", 30)
        resolution = raw_data.get("resolution", {"width": 1920, "height": 1080})
        width = resolution.get("width", 1920)
        height = resolution.get("height", 1080)

        # 3. Xác định Brand Profile
        brand_name = raw_data.get("brand_profile", "default")
        brand_dict = load_brand_profile(brand_name)

        # 4. Xác định đường dẫn đầu ra và thư mục làm việc tạm
        if output_path:
            out_file = Path(output_path).expanduser().resolve()
        else:
            out_root = Path.home() / "Downloads" / "AIWF_Output"
            out_file = out_root / project_id / f"{project_id}.mp4"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        if work_dir:
            temp_dir = Path(work_dir).expanduser().resolve()
        else:
            temp_dir = out_file.parent / f"_{out_file.stem}_work"
        temp_dir.mkdir(parents=True, exist_ok=True)

        scenes = raw_data.get("scenes", [])
        if not scenes:
            return StoryboardRenderResult(
                success=False,
                error_message="Storyboard không chứa phân cảnh nào."
            )

        logger.info(f"Bắt đầu kết xuất Storyboard '{project_id}' ({len(scenes)} cảnh, {width}x{height}@{fps}fps)")

        # 4b. Lập kế hoạch âm thanh (Creative Studio 2.1). Không có khối `audio` = hành vi v2.0 cũ.
        warnings: List[str] = []
        audio_spec = parse_audio_spec(raw_data)
        audio_plan = None
        if audio_spec is not None and audio_spec.audible:
            try:
                audio_plan = plan_audio(scenes, audio_spec, temp_dir, log=logger.info)
            except AudioPlanError as e:
                return StoryboardRenderResult(
                    success=False,
                    error_message=f"Blocker âm thanh: {e}",
                    audio_mode=audio_spec.mode,
                )
            warnings.extend(audio_plan.warnings)

        # 4c. Chuyển cảnh (Creative Studio 2.1). Không khai báo = cắt thẳng như v2.0.
        nominal_durations = [
            audio_plan.scene_durations[i] if audio_plan is not None else float(sc.get("duration_seconds", 3.0))
            for i, sc in enumerate(scenes)
        ]
        transition_plan = plan_transitions(raw_data, nominal_durations)

        # 5. Kết xuất từng phân cảnh
        scene_clips: List[str] = []
        scene_durations: List[float] = []
        fallback_used = False
        degraded = False
        actual_renderers: List[str] = []
        dom_qa_results: List[Dict[str, Any]] = []

        for idx, scene in enumerate(scenes):
            scene_id = scene.get("id", f"scene_{idx+1:02d}")
            duration = (
                audio_plan.scene_durations[idx] if audio_plan is not None
                else float(scene.get("duration_seconds", 3.0))
            )
            scene_durations.append(duration)
            # Cảnh có chuyển cảnh phía sau được dựng dài thêm đúng bằng thời lượng chuyển (đuôi chồng lấn),
            # nhờ đó mốc bắt đầu cảnh kế và tổng thời lượng không đổi -> không lệch lời đọc/BGM.
            tail_overlap = transition_plan[idx][1] if idx < len(transition_plan) else 0.0
            render_duration = round(duration + tail_overlap, 3)

            # Xác định preset hoặc template
            motion = scene.get("motion", {})
            preset_name = motion.get("preset") or self._infer_preset_for_scene(scene)
            
            # Chuẩn bị props cho preset
            props = scene.get("props", {}).copy()
            if "title" not in props and "visual_goal" in scene:
                props["title"] = scene.get("visual_goal", "")
            if "narration" in scene and "subtitle" not in props:
                props["subtitle"] = scene.get("narration", "")

            # P3: prop chữ thiếu hẳn -> để trống (không rò chữ demo như "aiworkforce.vn" vào video thật) + cảnh báo.
            # Khóa khai báo "" là chủ ý để trống, không bị đụng tới.
            if preset_name in PRESET_REGISTRY:
                _missing = missing_demo_props(preset_name, props)
                for _k in _missing["text"]:
                    props[_k] = ""
                if _missing["text"]:
                    warnings.append(
                        f"Cảnh {scene_id} (preset {preset_name}): thiếu prop chữ {_missing['text']} -> để trống "
                        f"(không dùng chữ mẫu). Khai báo giá trị trong props nếu muốn hiển thị."
                    )
                if _missing["data"]:
                    warnings.append(
                        f"Cảnh {scene_id} (preset {preset_name}): thiếu prop dữ liệu {_missing['data']} -> đang dùng "
                        f"DỮ LIỆU MẪU của preset. Truyền dữ liệu thật trong props trước khi xuất bản."
                    )

            # Sinh file HTML dự án cho cảnh
            scene_project_dir = temp_dir / f"scene_{idx+1:02d}_{scene_id}"
            scene_project_dir.mkdir(parents=True, exist_ok=True)
            
            scene_html_path = scene_project_dir / "index.html"
            rendered_html = render_preset_html(
                preset_name=preset_name,
                props=props,
                width=width,
                height=height,
                duration=render_duration,
                brand_profile=brand_dict,
            )
            with open(scene_html_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)

            # Metadata cho HyperFrames
            meta_path = scene_project_dir / "meta.json"
            meta_data = {
                "id": scene_id,
                "fps": fps,
                "width": width,
                "height": height,
                "duration": render_duration,
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, indent=2)

            # DOM / Layout Validation trước khi render (Fix 3)
            try:
                dom_res = validate_dom_layout(
                    html_content_or_path=scene_html_path,
                    width=width,
                    height=height,
                    safe_margin_ratio=0.08,
                    scene_id=scene_id,
                )
                dom_qa_results.append(dom_res.to_dict())
                for issue in dom_res.issues:
                    if issue.severity == "FAIL":
                        warnings.append(f"DOM Lỗi [Cảnh {scene_id}] {issue.code}: {issue.message}")
                    else:
                        warnings.append(f"DOM Cảnh báo [Cảnh {scene_id}] {issue.code}: {issue.message}")
            except Exception as e:
                logger.warning(f"Bỏ qua DOM QA do ngoại lệ: {e}")
                warnings.append(f"DOM QA SKIPPED [Cảnh {scene_id}]: không chạy được ({e}). Kết quả bố cục chưa được kiểm chứng.")

            # Kết xuất cảnh MP4
            scene_mp4_path = temp_dir / f"clip_{idx+1:02d}_{scene_id}.mp4"
            job = RenderJob(
                job_id=f"{project_id}_{scene_id}",
                template_path=preset_name if preset_name in PRESET_REGISTRY else str(scene_project_dir),
                duration=render_duration,
                output_path=str(scene_mp4_path),
                width=width,
                height=height,
                fps=fps,
                props=props,
                brand_profile=brand_dict,
                adapter_options={"force_adapter": force_adapter} if force_adapter else {},
            )

            render_res = self.router.render(job)
            if not render_res.success or not scene_mp4_path.exists():
                return StoryboardRenderResult(
                    success=False,
                    error_message=f"Lỗi khi kết xuất cảnh {scene_id}: {render_res.error_message}",
                    scene_clips=scene_clips,
                    fallback_used=fallback_used,
                    degraded=degraded,
                    actual_renderers=actual_renderers,
                    dom_qa_results=dom_qa_results,
                )

            scene_clips.append(str(scene_mp4_path))
            act_ren = render_res.actual_renderer or render_res.adapter_name
            actual_renderers.append(act_ren)
            if render_res.fallback_used:
                fallback_used = True
                degraded = True
                warnings.append(render_res.user_warning or f"Cảnh {scene_id} đã kích hoạt fallback.")
            elif "[AIWF Router Note]" in render_res.stderr:
                fallback_used = True
                degraded = True
                warnings.append(f"Cảnh {scene_id} đã kích hoạt fallback canvas.")

        # 6. Ghép nối các clip cảnh bằng ffmpeg (cắt thẳng, hoặc xfade nếu có chuyển cảnh)
        temp_video_only = temp_dir / "combined_video.mp4"
        ff = ffmpeg_bin()
        if any(k != "none" for k, _ in transition_plan):
            from ffmpeg_tools import duration as _clip_duration
            clip_lengths = [float(_clip_duration(c)) for c in scene_clips]
            fc, last = build_concat_filter(clip_lengths, transition_plan, fps)
            concat_cmd = [ff, "-y"]
            for c in scene_clips:
                concat_cmd += ["-i", c]
            concat_cmd += ["-filter_complex", fc, "-map", f"[{last}]", "-t", f"{sum(scene_durations):.3f}",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), str(temp_video_only)]
            applied = [f"{scenes[i].get('id', i + 1)}→{scenes[i + 1].get('id', i + 2)}: {k} {t:.2f}s"
                       for i, (k, t) in enumerate(transition_plan) if k != "none"]
            logger.info("Chuyển cảnh: " + "; ".join(applied))
        else:
            concat_list_file = temp_dir / "concat_list.txt"
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for clip_path in scene_clips:
                    f.write(f"file '{clip_path}'\n")
            concat_cmd = [
                ff, "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_list_file),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-r", str(fps),
                str(temp_video_only)
            ]
        res = subprocess.run(concat_cmd, capture_output=True, text=True)
        if res.returncode != 0 or not temp_video_only.exists():
            return StoryboardRenderResult(
                success=False,
                error_message=f"Lỗi khi ghép nối các clip: {res.stderr[-400:]}",
                scene_clips=scene_clips,
            )

        total_duration = sum(scene_durations)

        # 7. Xử lý âm thanh (Audio Layer)
        audio_mode = audio_spec.mode if audio_spec is not None else LEGACY_MODE
        audio_report: Dict[str, Any] = {"mode": audio_mode}
        temp_audio_file = temp_dir / "audio_track.m4a"
        if audio_plan is not None:
            # Track âm thanh THẬT: voice-over (+BGM, ducking) qua media.dub_engine
            try:
                mixed_wav, audio_report = mix_audio(audio_plan, audio_spec, temp_dir)
            except AudioPlanError as e:
                return StoryboardRenderResult(
                    success=False,
                    error_message=f"Blocker âm thanh: {e}",
                    scene_clips=scene_clips,
                    audio_mode=audio_mode,
                )
            audio_src = str(mixed_wav)
        else:
            # Track im lặng: chủ đích (mode='silent') hoặc mặc định v2.0 (không có khối audio)
            if audio_spec is None:
                warnings.append(
                    "Storyboard không có khối 'audio': xuất track im lặng (hành vi mặc định v2.0). "
                    "Thêm audio.mode='silent' nếu chủ đích không tiếng, hoặc 'narration' để có giọng đọc."
                )
            audio_gen_cmd = [
                ff, "-y", "-f", "lavfi",
                "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
                "-t", f"{total_duration:.3f}",
                "-c:a", "aac", "-b:a", "192k",
                str(temp_audio_file)
            ]
            subprocess.run(audio_gen_cmd, capture_output=True, text=True)
            audio_src = str(temp_audio_file)

        # Muxing video + audio vào file cuối cùng
        mux_cmd = [
            ff, "-y",
            "-i", str(temp_video_only),
            "-i", audio_src,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_file)
        ]
        mux_res = subprocess.run(mux_cmd, capture_output=True, text=True)
        if mux_res.returncode != 0 or not out_file.exists():
            return StoryboardRenderResult(
                success=False,
                error_message=f"Lỗi khi hoàn thiện tệp MP4 cuối cùng: {mux_res.stderr[-400:]}",
                scene_clips=scene_clips,
            )

        # 8. Thực hiện Visual QA 2.0 nếu được yêu cầu
        qa_report = None
        contact_sheet_path = ""
        tech_report_path = ""
        if run_qa:
            qa_dir = out_file.parent / f"{out_file.stem}_qa"
            expected_spec = {
                "duration": total_duration,
                "width": width,
                "height": height,
                "fps": fps,
            }
            if audio_plan is not None:
                expected_spec["require_audio"] = True
                expected_spec["require_audible"] = True
            elif audio_spec is not None:      # mode='silent': im lặng là chủ đích, không cảnh báo "quá nhỏ"
                expected_spec["intentional_silence"] = True
            qa_report = run_visual_qa(
                video_path=str(out_file),
                expected_spec=expected_spec,
                output_dir=str(qa_dir),
            )
            contact_sheet_path = qa_report.contact_sheet_path or ""
            tech_report_path = str(qa_dir / f"{out_file.stem}_technical_report.json")

        return StoryboardRenderResult(
            success=True,
            output_mp4=str(out_file),
            qa_report=qa_report,
            contact_sheet=contact_sheet_path,
            technical_report_json=tech_report_path,
            total_duration=total_duration,
            scene_clips=scene_clips,
            warnings=warnings,
            fallback_used=fallback_used,
            degraded=degraded,
            actual_renderers=actual_renderers,
            dom_qa_results=dom_qa_results,
            audio_mode=audio_mode,
            audio_report=audio_report,
        )

    def _infer_preset_for_scene(self, scene: Dict[str, Any]) -> str:
        """Suy luận preset mặc định phù hợp với loại phân cảnh."""
        scene_type = scene.get("type", "motion_graphic")
        type_mapping = {
            "title_card": "04_kinetic_title",
            "kinetic_typography": "04_kinetic_title",
            "infographic": "09_bar_chart",
            "product_highlight": "07_product_spotlight",
            "ui_showcase": "08_feature_card",
            "outro": "10_cta_reveal",
            "motion_graphic": "01_fade_in",
            "b_roll": "02_slide_reveal",
        }
        return type_mapping.get(scene_type, "01_fade_in")


def render_storyboard(
    storyboard: Union[Dict[str, Any], str, Path],
    output_path: Optional[Union[str, Path]] = None,
    work_dir: Optional[Union[str, Path]] = None,
    run_qa: bool = True,
    force_adapter: Optional[str] = None,
) -> StoryboardRenderResult:
    """Hàm tiện ích cấp cao để kết xuất nhanh Storyboard."""
    renderer = StoryboardRenderer()
    return renderer.render_storyboard(
        storyboard=storyboard,
        output_path=output_path,
        work_dir=work_dir,
        run_qa=run_qa,
        force_adapter=force_adapter,
    )
