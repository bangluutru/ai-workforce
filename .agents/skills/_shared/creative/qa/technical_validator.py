#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Technical Video Validator (Luật R7).
Kiểm tra tự động các thông số kỹ thuật cốt lõi: codec, độ dài, tốc độ khung hình,
độ phân giải, luồng âm thanh, đồng bộ AV và chuẩn phát thanh EBU R128.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_CURRENT_DIR = Path(__file__).resolve().parent
_SHARED_DIR = _CURRENT_DIR.parents[1]


def _get_ffmpeg_tools():
    try:
        from ffmpeg_tools import ffmpeg_bin, ffprobe_bin, loudness
        return ffmpeg_bin, ffprobe_bin, loudness
    except ImportError:
        import sys
        media_path = str(_SHARED_DIR / "media")
        if media_path not in sys.path:
            sys.path.insert(0, media_path)
        from ffmpeg_tools import ffmpeg_bin, ffprobe_bin, loudness
        return ffmpeg_bin, ffprobe_bin, loudness


@dataclass
class TechnicalFinding:
    level: str  # "FAIL", "WARN", "INFO"
    code: str
    message: str


@dataclass
class TechnicalValidationResult:
    video_path: str
    success: bool
    verdict: str  # "PASS", "WARN", "FAIL"
    score: int  # 0 -> 100
    metrics: Dict[str, Any] = field(default_factory=dict)
    findings: List[TechnicalFinding] = field(default_factory=list)


def inspect_media_streams(video_path: str) -> Dict[str, Any]:
    """Truy vấn thông số chi tiết của file media thông qua ffprobe JSON."""
    _, ffprobe_bin, _ = _get_ffmpeg_tools()
    ffp = ffprobe_bin()

    cmd = [
        ffp,
        "-v",
        "error",
        "-show_entries",
        "format=duration,size,bit_rate:stream=index,codec_type,codec_name,pix_fmt,width,height,r_frame_rate,nb_frames,sample_rate,channels",
        "-of",
        "json",
        video_path,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def validate_video_technical(
    video_path: str,
    expected_spec: Optional[Dict[str, Any]] = None,
) -> TechnicalValidationResult:
    """
    Kiểm định toàn diện thông số kỹ thuật của file video.
    
    Args:
        video_path: Đường dẫn file video thành phẩm
        expected_spec: Yêu cầu kỹ thuật kỳ vọng (duration, width, height, fps, require_audio...)
    """
    path_obj = Path(video_path)
    if not path_obj.is_file() or path_obj.stat().st_size == 0:
        return TechnicalValidationResult(
            video_path=video_path,
            success=False,
            verdict="FAIL",
            score=0,
            findings=[TechnicalFinding("FAIL", "file_not_found", f"File video không tồn tại hoặc rỗng: {video_path}")],
        )

    try:
        data = inspect_media_streams(video_path)
    except Exception as e:
        return TechnicalValidationResult(
            video_path=video_path,
            success=False,
            verdict="FAIL",
            score=0,
            findings=[TechnicalFinding("FAIL", "ffprobe_error", f"Lỗi đọc metadata video: {str(e)}")],
        )

    streams = data.get("streams", [])
    fmt = data.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    findings: List[TechnicalFinding] = []
    score = 100

    if not video_stream:
        return TechnicalValidationResult(
            video_path=video_path,
            success=False,
            verdict="FAIL",
            score=0,
            findings=[TechnicalFinding("FAIL", "no_video_stream", "Tệp tin không chứa luồng video hợp lệ.")],
        )

    # 1. Đo lường thông số video
    v_codec = video_stream.get("codec_name", "")
    pix_fmt = video_stream.get("pix_fmt", "")
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    duration_val = float(fmt.get("duration", 0.0))
    file_size = int(fmt.get("size", 0))

    # Tính FPS từ rational (vd: "30/1")
    r_fps = video_stream.get("r_frame_rate", "30/1")
    fps_val = 30.0
    if "/" in r_fps:
        num, den = r_fps.split("/")
        fps_val = round(float(num) / float(den), 2)
    else:
        fps_val = float(r_fps)

    nb_frames = int(video_stream.get("nb_frames") or round(duration_val * fps_val))

    metrics: Dict[str, Any] = {
        "video_codec": v_codec,
        "pix_fmt": pix_fmt,
        "width": width,
        "height": height,
        "aspect_ratio": f"{width}:{height}",
        "fps": fps_val,
        "duration": duration_val,
        "nb_frames": nb_frames,
        "file_size_bytes": file_size,
        "has_audio": audio_stream is not None,
    }

    # 2. Kiểm tra Codec và Pixel Format
    if v_codec not in ("h264", "vp9", "hevc", "prores"):
        findings.append(TechnicalFinding("WARN", "uncommon_codec", f"Codec video '{v_codec}' có thể không tương thích web tối đa (khuyên dùng h264)."))
        score -= 10

    if pix_fmt not in ("yuv420p", "yuv444p"):
        findings.append(TechnicalFinding("WARN", "pix_fmt_warning", f"Định dạng màu '{pix_fmt}' có thể gây lỗi hiển thị trên một số trình duyệt cũ (khuyên dùng yuv420p)."))
        score -= 5

    # 3. Đối chiếu với thông số kỳ vọng (nếu có)
    spec = expected_spec or {}
    if "duration" in spec:
        exp_dur = float(spec["duration"])
        dur_diff = abs(duration_val - exp_dur)
        if dur_diff > 0.5:
            findings.append(TechnicalFinding("FAIL", "duration_mismatch", f"Thời lượng thực tế ({duration_val:.2f}s) lệch quá 0.5s so với kịch bản ({exp_dur:.2f}s)."))
            score -= 30
        elif dur_diff > 0.1:
            findings.append(TechnicalFinding("WARN", "duration_drift", f"Thời lượng thực tế ({duration_val:.2f}s) lệch nhẹ so với kịch bản ({exp_dur:.2f}s)."))
            score -= 10

    if "width" in spec and "height" in spec:
        exp_w, exp_h = int(spec["width"]), int(spec["height"])
        if width != exp_w or height != exp_h:
            findings.append(TechnicalFinding("FAIL", "resolution_mismatch", f"Độ phân giải ({width}x{height}) không khớp yêu cầu ({exp_w}x{exp_h})."))
            score -= 30

    if "fps" in spec:
        exp_fps = float(spec["fps"])
        if abs(fps_val - exp_fps) > 0.5:
            findings.append(TechnicalFinding("FAIL", "fps_mismatch", f"Tốc độ khung hình ({fps_val} FPS) không khớp kịch bản ({exp_fps} FPS)."))
            score -= 20

    if "aspect_ratio" in spec:
        exp_ar = spec["aspect_ratio"]
        current_ratio = width / height if height > 0 else 0
        expected_ratio = 1.0
        if exp_ar == "16:9":
            expected_ratio = 16 / 9
        elif exp_ar == "9:16":
            expected_ratio = 9 / 16
        elif exp_ar == "1:1":
            expected_ratio = 1.0

        if abs(current_ratio - expected_ratio) > 0.05:
            findings.append(TechnicalFinding("FAIL", "aspect_mismatch", f"Tỷ lệ khung hình ({width}:{height}) không khớp tỷ lệ yêu cầu '{exp_ar}'."))
            score -= 25

    # 4. Kiểm tra luồng âm thanh
    if spec.get("require_audio", False) and not audio_stream:
        findings.append(TechnicalFinding("FAIL", "missing_required_audio", "Kịch bản yêu cầu âm thanh nhưng video không có luồng audio nào."))
        score -= 25

    if audio_stream:
        a_codec = audio_stream.get("codec_name", "")
        sample_rate = int(audio_stream.get("sample_rate", 0))
        channels = int(audio_stream.get("channels", 0))
        metrics["audio_codec"] = a_codec
        metrics["audio_sample_rate"] = sample_rate
        metrics["audio_channels"] = channels

        # Thử đo độ lớn âm thanh theo chuẩn EBU R128
        try:
            _, _, loudness_func = _get_ffmpeg_tools()
            lufs, peak = loudness_func(video_path)
            metrics["audio_lufs"] = lufs
            metrics["audio_peak_dbfs"] = peak
            if lufs is not None:
                if lufs < -28.0:
                    findings.append(TechnicalFinding("WARN", "audio_too_quiet", f"Âm lượng trung bình quá nhỏ ({lufs:.1f} LUFS < -28 LUFS)."))
                    score -= 10
                elif lufs > -10.0:
                    findings.append(TechnicalFinding("WARN", "audio_too_loud", f"Âm lượng quá lớn có thể bị vỡ âm ({lufs:.1f} LUFS > -10 LUFS)."))
                    score -= 10
        except Exception:
            pass

    # Kết luận verdict
    has_fail = any(f.level == "FAIL" for f in findings)
    has_warn = any(f.level == "WARN" for f in findings)
    final_score = max(0, score)

    if has_fail or final_score < 70:
        verdict = "FAIL"
    elif has_warn or final_score < 90:
        verdict = "WARN"
    else:
        verdict = "PASS"

    return TechnicalValidationResult(
        video_path=video_path,
        success=not has_fail,
        verdict=verdict,
        score=final_score,
        metrics=metrics,
        findings=findings,
    )
