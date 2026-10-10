#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
creative/audio_track.py — Audio Contract + dựng track âm thanh cho Storyboard v2.0 (Creative Studio 2.1).

Luật R7: KHÔNG viết lại TTS/mixer. Module này chỉ là lớp keo gọi `media.dub_engine`
(synthesize → TTS offline VieNeu/Kokoro, mix → BGM + ducking + loudnorm).

Hợp đồng `audio` (tùy chọn, cấp storyboard). Không có khối này = hành vi v2.0 cũ (track im lặng).

    "audio": {
      "mode": "narration | narration_bgm | bgm_only | silent",   # mặc định suy từ cờ bên dưới
      "language": "vi | en | ja",            # mặc định "vi"
      "voice": "Minh Quân Pro",              # mặc định: giọng mặc định theo ngôn ngữ
      "gender": "female | male",
      "narration_enabled": true,             # chỉ dùng khi KHÔNG đặt "mode"
      "bgm_enabled": false,                  # chỉ dùng khi KHÔNG đặt "mode"
      "bgm_path": "/duong/dan/nhac.mp3",     # BẮT BUỘC khi mode có BGM (không tự tải nhạc)
      "bgm_volume": 0.5,
      "ducking_enabled": true,
      "duck_level": 0.25,
      "sync_policy": "fit_or_extend | strict",
      "target_lufs": -16,
      "lead_in_seconds": 0.3,
      "tail_seconds": 0.4,
      "verify_voice": false                  # true = Whisper nghe lại từng câu (chậm hơn)
    }

Chính sách đồng bộ (không cắt lời, không tăng tốc giọng):
  - Lời dài hơn cảnh + fit_or_extend → kéo dài thời lượng cảnh (ghi vào báo cáo).
  - Lời dài hơn cảnh + strict        → trả blocker cụ thể, không render.
  - Lời ngắn hơn cảnh                → giữ nguyên thời lượng cảnh, phần dư là khoảng nghỉ.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("aiwf.creative.audio_track")

AUDIO_MODES = ("narration", "narration_bgm", "bgm_only", "silent")
SYNC_POLICIES = ("fit_or_extend", "strict")
AUDIO_LANGUAGES = ("vi", "en", "ja")
LEGACY_MODE = "silent_default"  # không có khối audio: giữ nguyên hành vi v2.0

_NEEDS_NARRATION = ("narration", "narration_bgm")
_NEEDS_BGM = ("narration_bgm", "bgm_only")


class AudioPlanError(RuntimeError):
    """Blocker âm thanh có thể giải thích được (TTS vắng, lời không vừa cảnh, thiếu BGM...)."""


@dataclass
class AudioSpec:
    mode: str = "narration"
    language: str = "vi"
    voice: Optional[str] = None
    gender: str = "female"
    bgm_path: Optional[str] = None
    bgm_volume: float = 0.5
    ducking_enabled: bool = True
    duck_level: float = 0.25
    sync_policy: str = "fit_or_extend"
    target_lufs: float = -16.0
    lead_in_seconds: float = 0.3
    tail_seconds: float = 0.4
    verify_voice: bool = False

    @property
    def needs_narration(self) -> bool:
        return self.mode in _NEEDS_NARRATION

    @property
    def needs_bgm(self) -> bool:
        return self.mode in _NEEDS_BGM

    @property
    def audible(self) -> bool:
        return self.mode != "silent"


@dataclass
class AudioPlan:
    """Kết quả giai đoạn lập kế hoạch: thời lượng cảnh sau đồng bộ + giọng đã tổng hợp."""
    scene_durations: List[float]
    scene_starts: List[float]
    voice_lines: Dict[int, Dict[str, Any]] = field(default_factory=dict)  # idx cảnh -> {path, dur, text}
    extended: List[Dict[str, Any]] = field(default_factory=list)
    voice_used: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


def spoken_text(raw: str) -> str:
    """Văn bản cho TTS: bỏ dấu '|' (chỉ là chỗ ngắt phụ đề, không đọc)."""
    return " ".join(str(raw or "").replace("|", " ").split())


def parse_audio_spec(storyboard: Dict[str, Any]) -> Optional[AudioSpec]:
    """Trả None nếu storyboard không có khối `audio` (hành vi v2.0 cũ). Giả định đã qua validate_audio_spec."""
    block = storyboard.get("audio")
    if block is None:
        return None
    mode = block.get("mode")
    if mode is None:
        narr = block.get("narration_enabled", True)
        bgm = block.get("bgm_enabled", False)
        mode = "narration_bgm" if (narr and bgm) else "narration" if narr else "bgm_only" if bgm else "silent"
    return AudioSpec(
        mode=mode,
        language=block.get("language", "vi"),
        voice=block.get("voice") if block.get("voice") not in (None, "", "default") else None,
        gender=block.get("gender", "female"),
        bgm_path=block.get("bgm_path"),
        bgm_volume=float(block.get("bgm_volume", 0.5)),
        ducking_enabled=bool(block.get("ducking_enabled", True)),
        duck_level=float(block.get("duck_level", 0.25)),
        sync_policy=block.get("sync_policy", "fit_or_extend"),
        target_lufs=float(block.get("target_lufs", -16)),
        lead_in_seconds=float(block.get("lead_in_seconds", 0.3)),
        tail_seconds=float(block.get("tail_seconds", 0.4)),
        verify_voice=bool(block.get("verify_voice", False)),
    )


def validate_audio_spec(storyboard: Dict[str, Any]) -> List[str]:
    """Thẩm định khối `audio` (nếu có). Không có khối audio → không lỗi (tương thích ngược)."""
    block = storyboard.get("audio")
    if block is None:
        return []
    if not isinstance(block, dict):
        return ["audio phải là một object."]
    errors: List[str] = []

    mode = block.get("mode")
    if mode is not None and mode not in AUDIO_MODES:
        errors.append(f"audio.mode '{mode}' không hợp lệ (hỗ trợ: {list(AUDIO_MODES)}).")
    lang = block.get("language", "vi")
    if lang not in AUDIO_LANGUAGES:
        errors.append(f"audio.language '{lang}' không hợp lệ (hỗ trợ: {list(AUDIO_LANGUAGES)}).")
    pol = block.get("sync_policy", "fit_or_extend")
    if pol not in SYNC_POLICIES:
        errors.append(f"audio.sync_policy '{pol}' không hợp lệ (hỗ trợ: {list(SYNC_POLICIES)}).")
    if block.get("gender", "female") not in ("female", "male"):
        errors.append("audio.gender phải là 'female' hoặc 'male'.")

    def _num(key: str, lo: float, hi: float) -> None:
        v = block.get(key)
        if v is None:
            return
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not (lo <= v <= hi):
            errors.append(f"audio.{key} phải là số trong [{lo}, {hi}], nhận được: {v!r}.")

    _num("target_lufs", -30, -8)
    _num("duck_level", 0, 1)
    _num("bgm_volume", 0, 1)
    _num("lead_in_seconds", 0, 2)
    _num("tail_seconds", 0, 3)

    # Ràng buộc chéo theo mode hiệu lực
    spec_mode = mode if mode in AUDIO_MODES else None
    if spec_mode is None and mode is None:
        narr = block.get("narration_enabled", True)
        bgm = block.get("bgm_enabled", False)
        spec_mode = "narration_bgm" if (narr and bgm) else "narration" if narr else "bgm_only" if bgm else "silent"
    if spec_mode in _NEEDS_BGM and not block.get("bgm_path"):
        errors.append(f"audio.bgm_path là bắt buộc khi mode='{spec_mode}' (hệ thống không tự tải nhạc nền).")
    if spec_mode in _NEEDS_NARRATION:
        scenes = storyboard.get("scenes") or []
        if not any(spoken_text(s.get("narration", "")) for s in scenes if isinstance(s, dict)):
            errors.append(f"audio.mode='{spec_mode}' cần ít nhất một scene có 'narration' không rỗng.")
    return errors


def plan_audio(
    scenes: List[Dict[str, Any]],
    spec: AudioSpec,
    work_dir: Path,
    log: Callable[[str], None] = logger.info,
) -> AudioPlan:
    """
    Tổng hợp giọng đọc TRƯỚC khi render cảnh để biết độ dài thật, rồi đồng bộ thời lượng cảnh.
    Ném AudioPlanError (blocker cụ thể) thay vì âm thầm cắt lời hay giả lập thành công.
    """
    base = [float(s.get("duration_seconds", 3.0)) for s in scenes]
    plan = AudioPlan(scene_durations=list(base), scene_starts=[])

    if spec.needs_narration:
        lines = []
        for i, s in enumerate(scenes):
            txt = spoken_text(s.get("narration", ""))
            if txt:
                lines.append({"key": f"i{i:03d}", "text": txt, "_idx": i})
        try:
            import bootstrap  # noqa: F401  (R7: nạp đường dẫn _shared/media)
            import dub_engine
            res, used = dub_engine.synthesize(
                [{"key": l["key"], "text": l["text"]} for l in lines],
                spec.language, spec.voice, spec.gender, str(Path(work_dir) / "voice"),
                takes=2, verify=spec.verify_voice, log=log,
            )
        except Exception as e:  # engine vắng / model thiếu / lỗi TTS
            raise AudioPlanError(
                f"Không tổng hợp được giọng đọc (lang={spec.language}, voice={spec.voice or 'mặc định'}): {e}. "
                f"Không dùng track im lặng để thay thế. Dùng audio.mode='silent' nếu muốn video không tiếng."
            ) from e

        plan.voice_used = used
        missing = [l["_idx"] for l in lines if l["key"] not in res]
        if missing:
            ids = [scenes[i].get("id", f"scene_{i + 1:02d}") for i in missing]
            raise AudioPlanError(f"TTS không tạo được giọng cho cảnh: {ids}.")

        overflow_blockers = []
        for l in lines:
            i, r = l["_idx"], res[l["key"]]
            dur_voice = float(r["dur"])
            plan.voice_lines[i] = {"path": r["path"], "dur": dur_voice, "text": l["text"]}
            need = round(dur_voice + spec.lead_in_seconds + spec.tail_seconds, 2)
            if need > base[i]:
                sid = scenes[i].get("id", f"scene_{i + 1:02d}")
                if spec.sync_policy == "strict":
                    overflow_blockers.append(f"{sid}: lời {dur_voice:.2f}s cần ≥{need:.2f}s, cảnh chỉ {base[i]:.2f}s")
                else:
                    plan.scene_durations[i] = need
                    plan.extended.append({"scene": sid, "from": base[i], "to": need, "voice_seconds": round(dur_voice, 3)})
        if overflow_blockers:
            raise AudioPlanError("sync_policy='strict': lời không vừa thời lượng cảnh → " + "; ".join(overflow_blockers))
        if plan.extended:
            plan.warnings.append(
                f"Đã kéo dài {len(plan.extended)} cảnh để lời đọc không bị cắt: "
                + ", ".join(f"{e['scene']} {e['from']:.1f}s→{e['to']:.1f}s" for e in plan.extended)
            )

    t = 0.0
    for d in plan.scene_durations:
        plan.scene_starts.append(round(t, 3))
        t += d
    return plan


def _loop_bgm(src: str, total: float, dst: str) -> str:
    from ffmpeg_tools import ffmpeg_bin
    r = subprocess.run(
        [ffmpeg_bin(), "-v", "error", "-y", "-stream_loop", "-1", "-i", src, "-t", f"{total:.3f}",
         "-af", f"afade=t=in:d=1.0,afade=t=out:st={max(0.0, total - 2.0):.3f}:d=2.0",
         "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", dst],
        capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(dst):
        raise AudioPlanError(f"Không xử lý được BGM '{src}': {r.stderr[-300:]}")
    return dst


def mix_audio(plan: AudioPlan, spec: AudioSpec, work_dir: Path) -> Tuple[str, Dict[str, Any]]:
    """Trộn voice-over (+BGM, ducking) thành WAV stereo 48 kHz chuẩn hóa độ lớn. Trả (đường dẫn, báo cáo)."""
    import bootstrap  # noqa: F401
    import dub_engine
    from ffmpeg_tools import loudness

    work_dir = Path(work_dir)
    total = round(sum(plan.scene_durations), 3)

    bg_wav = None
    if spec.needs_bgm:
        if not spec.bgm_path or not Path(spec.bgm_path).expanduser().is_file():
            raise AudioPlanError(f"BGM không tồn tại: {spec.bgm_path!r}.")
        bg_wav = _loop_bgm(str(Path(spec.bgm_path).expanduser()), total, str(work_dir / "bgm_loop.wav"))

    placed = [
        (plan.scene_starts[i] + spec.lead_in_seconds, v["path"])
        for i, v in sorted(plan.voice_lines.items())
    ]
    out = str(work_dir / "audio_mix.wav")
    dub_engine.mix(
        bg_wav, placed, out, total,
        bg_volume=spec.bgm_volume if bg_wav else 0.0,
        duck_level=spec.duck_level if spec.ducking_enabled else 1.0,
        voice_volume=1.0, lufs=spec.target_lufs,
    )
    if not os.path.isfile(out) or os.path.getsize(out) < 1000:
        raise AudioPlanError("Trộn âm thanh không tạo được tệp hợp lệ.")

    lufs, peak = loudness(out)
    report = {
        "mode": spec.mode,
        "language": spec.language,
        "voice_used": plan.voice_used,
        "sync_policy": spec.sync_policy,
        "narration_scenes": len(plan.voice_lines),
        "extended_scenes": plan.extended,
        "bgm": bool(bg_wav),
        "ducking": bool(bg_wav and spec.ducking_enabled and plan.voice_lines),
        "duck_level": spec.duck_level if spec.ducking_enabled else None,
        "target_lufs": spec.target_lufs,
        "measured_lufs": lufs,
        "measured_peak_dbfs": peak,
        "total_seconds": total,
    }
    return out, report
