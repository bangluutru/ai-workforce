#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
timeline_planner.py — Trình lập lịch dòng thời gian đa tầng (Timeline Planner).
Đồng bộ chuyển động với âm thanh thực tế (TTS, Whisper, beats) và thẩm định tính hợp lệ của sự kiện (Luật R7).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional


class TimelineValidationError(ValueError):
    """Lỗi khi cấu trúc dòng thời gian không hợp lệ."""
    pass


@dataclass
class TimelineEvent:
    """Đại diện một sự kiện xuất hiện hoặc chuyển động trên dòng thời gian."""
    id: str
    target: str
    start_time: float
    end_time: float
    type: str = "custom"
    payload: Dict[str, Any] = field(default_factory=dict)

    @property
    def time(self) -> float:
        return self.start_time

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)


def validate_timeline_events(
    events: List[Any],
    scene_duration: float = 0.0,
    total_duration: Optional[float] = None
) -> Tuple[bool, List[str]]:
    """
    Thẩm định nghiêm ngặt tính toàn vẹn của danh sách sự kiện dòng thời gian:
    1. Thứ tự sự kiện: Thời gian (start_time/time) phải tăng dần hoặc bằng nhau.
    2. Biên độ thời gian: 0.0 <= start_time <= end_time <= max_duration.
    3. Tính duy nhất của ID: Không trùng lặp event ID.
    4. Xung đột chuyển cảnh: Chuyển cảnh (transition_start) phải kết thúc trước hoặc đúng lúc hết cảnh.
    """
    dur = total_duration if total_duration is not None else scene_duration
    errors: List[str] = []

    if not isinstance(events, list):
        return False, ["Danh sách sự kiện phải là một list."]

    seen_ids = set()
    prev_time = -1.0

    for idx, ev in enumerate(events):
        prefix = f"Sự kiện #{idx + 1}"
        if isinstance(ev, TimelineEvent):
            ev_id = ev.id
            s_time = float(ev.start_time)
            e_time = float(ev.end_time)
            ev_type = ev.type
            dur_field = ev.duration
        elif isinstance(ev, dict):
            ev_id = ev.get("id")
            s_time = float(ev.get("start_time", ev.get("time", 0.0)))
            dur_field = float(ev.get("duration", 0.0))
            e_time = float(ev.get("end_time", s_time + dur_field))
            ev_type = ev.get("type", "custom")
        else:
            errors.append(f"{prefix}: Phải là một dict hoặc TimelineEvent object.")
            continue

        if not ev_id or not isinstance(ev_id, str):
            errors.append(f"{prefix}: Thiếu thuộc tính 'id' hoặc không phải chuỗi.")
        elif ev_id in seen_ids:
            errors.append(f"{prefix}: Trùng lặp event ID '{ev_id}'.")
        else:
            seen_ids.add(ev_id)

        # 1. Kiểm tra thời gian âm
        if s_time < 0.0:
            errors.append(f"{prefix} ('{ev_id}'): thời gian bắt đầu âm ({s_time:.3f}s).")

        # 2. Kiểm tra khoảng thời gian hợp lệ
        if s_time > e_time:
            errors.append(
                f"{prefix} ('{ev_id}'): thời gian bắt đầu ({s_time:.3f}s) lớn hơn thời gian kết thúc ({e_time:.3f}s)."
            )

        # 3. Kiểm tra tràn thời lượng phân cảnh
        if dur > 0 and e_time > dur + 0.001:
            errors.append(
                f"{prefix} ('{ev_id}'): vượt quá thời lượng scene ({dur:.3f}s)."
            )

        # 4. Thứ tự thời gian
        if s_time < prev_time:
            errors.append(
                f"{prefix} ('{ev_id}'): Vi phạm thứ tự dòng thời gian. "
                f"Thời gian ({s_time:.3f}s) nhỏ hơn sự kiện trước đó ({prev_time:.3f}s)."
            )
        prev_time = s_time

        # 5. Kiểm tra chuyển cảnh nếu có
        if ev_type == "transition_start":
            if dur_field < 0.0:
                errors.append(f"{prefix} ('{ev_id}'): Thời lượng chuyển cảnh không được âm.")
            elif dur > 0 and s_time + dur_field > dur + 0.05:
                errors.append(
                    f"{prefix} ('{ev_id}'): Chuyển cảnh bắt đầu lúc {s_time:.2f}s kéo dài {dur_field:.2f}s "
                    f"tràn ra ngoài phân cảnh ({dur:.2f}s)."
                )

    return (len(errors) == 0, errors)


def snap_to_nearest_beat(
    target_time: float,
    beats: List[float],
    tolerance: float = 0.25,
    max_shift: Optional[float] = None
) -> float:
    """
    Bắt dính thời điểm chuyển cảnh vào nhịp nhạc (Beat snapping) nếu có beat gần đó trong dung sai.
    Giúp chuyển cảnh ăn khớp với tiết tấu âm nhạc tự nhiên.
    """
    shift_limit = max_shift if max_shift is not None else tolerance
    if not beats:
        return target_time
    closest_beat = min(beats, key=lambda b: abs(b - target_time))
    if abs(closest_beat - target_time) <= shift_limit:
        return round(closest_beat, 3)
    return target_time


def plan_scene_timeline(
    scene: Dict[str, Any],
    brand_profile: Optional[Dict[str, Any]] = None,
    scene_duration: Optional[float] = None,
    alignment_mode: str = "estimated_uniform",
    beat_timestamps: Optional[List[float]] = None,
    beats: Optional[List[float]] = None,
    audio_duration: Optional[float] = None,
    word_timestamps: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Sinh dòng thời gian chi tiết cho một phân cảnh:
    - Đồng bộ mốc giọng đọc, chuyển động tiêu đề, thẻ nội dung và chuyển cảnh.
    - Hỗ trợ các chế độ căn chỉnh: sequential, beat_synced, measured_word_alignment, sentence_aligned, estimated_uniform.
    - Đảm bảo tính tất định 100% cho cùng một đầu vào.
    """
    scene_id = scene.get("id", "scene_001")
    scene_dur = float(scene_duration if scene_duration is not None else scene.get("duration_seconds", 4.0))

    # Nếu có audio_duration thực tế, điều chỉnh scene_dur
    if audio_duration is not None and audio_duration > 0:
        scene_dur = max(scene_dur, round(audio_duration + 0.5, 2))

    all_beats = beat_timestamps or beats or []
    elements = scene.get("elements", [])

    # Trường hợp 1: Phân cảnh có danh sách elements tường minh
    if elements:
        events: List[TimelineEvent] = []
        if alignment_mode == "sequential":
            elem_dur = scene_dur / max(1, len(elements))
            current_t = 0.0
            for i, el in enumerate(elements):
                e_end = min(scene_dur, current_t + elem_dur)
                events.append(TimelineEvent(
                    id=el.get("id", f"elem_{i}"),
                    target=el.get("type", "element"),
                    start_time=round(current_t, 3),
                    end_time=round(e_end, 3),
                    type="element",
                    payload=el
                ))
                current_t = e_end
        elif alignment_mode == "beat_synced":
            for i, el in enumerate(elements):
                b_start = all_beats[i] if i < len(all_beats) else (i * (scene_dur / len(elements)))
                b_end = all_beats[i + 1] if (i + 1) < len(all_beats) else scene_dur
                b_start = min(scene_dur, max(0.0, b_start))
                b_end = min(scene_dur, max(b_start, b_end))
                events.append(TimelineEvent(
                    id=el.get("id", f"elem_{i}"),
                    target=el.get("type", "element"),
                    start_time=round(b_start, 3),
                    end_time=round(b_end, 3),
                    type="element",
                    payload=el
                ))
        else:
            # Mặc định chia đều
            elem_dur = scene_dur / max(1, len(elements))
            for i, el in enumerate(elements):
                events.append(TimelineEvent(
                    id=el.get("id", f"elem_{i}"),
                    target=el.get("type", "element"),
                    start_time=round(i * elem_dur, 3),
                    end_time=round(min(scene_dur, (i + 1) * elem_dur), 3),
                    type="element",
                    payload=el
                ))

        is_valid, errs = validate_timeline_events(events, total_duration=scene_dur)
        return {
            "valid": is_valid,
            "scene_id": scene_id,
            "effective_duration_seconds": round(scene_dur, 3),
            "alignment_mode": alignment_mode,
            "event_count": len(events),
            "events": events
        }

    # Trường hợp 2: Phân cảnh tiêu chuẩn theo Storyboard Schema v2.0
    dict_events: List[Dict[str, Any]] = []

    # 1. Cảnh bắt đầu
    dict_events.append({
        "id": f"{scene_id}_start",
        "scene_id": scene_id,
        "time": 0.0,
        "type": "scene_start",
        "target": "scene",
        "payload": {}
    })

    # 2. Xuất hiện visual
    reveal_time = 0.2
    if all_beats:
        reveal_time = snap_to_nearest_beat(reveal_time, all_beats, tolerance=0.2)
    reveal_time = min(reveal_time, max(0.0, scene_dur - 1.0))

    dict_events.append({
        "id": f"{scene_id}_visual_reveal",
        "scene_id": scene_id,
        "time": round(reveal_time, 3),
        "type": "element_enter",
        "target": "primary_subject",
        "payload": {
            "preset": scene.get("motion", {}).get("preset", "fade_in"),
            "intensity": scene.get("motion", {}).get("intensity", "moderate")
        }
    })

    # 3. Đồng bộ narration
    resolved_mode = alignment_mode
    narration_text = scene.get("narration", "").strip()

    if narration_text:
        if word_timestamps and len(word_timestamps) > 0:
            resolved_mode = "measured_word_alignment"
            for w_idx, w_data in enumerate(word_timestamps):
                w_time = float(w_data.get("start", 0.0))
                if w_time <= scene_dur:
                    dict_events.append({
                        "id": f"{scene_id}_word_{w_idx}",
                        "scene_id": scene_id,
                        "time": round(w_time, 3),
                        "type": "word_cue",
                        "target": "caption",
                        "payload": {"word": w_data.get("word", ""), "end": w_data.get("end")}
                    })
        elif audio_duration is not None:
            resolved_mode = "sentence_aligned"
            dict_events.append({
                "id": f"{scene_id}_narration_start",
                "scene_id": scene_id,
                "time": 0.2,
                "type": "audio_start",
                "target": "voice",
                "payload": {"duration": audio_duration, "text": narration_text}
            })
        else:
            resolved_mode = "estimated_uniform"
            dict_events.append({
                "id": f"{scene_id}_narration_start",
                "scene_id": scene_id,
                "time": 0.2,
                "type": "audio_start",
                "target": "voice",
                "payload": {"estimated_duration": max(0.5, scene_dur - 0.6), "text": narration_text}
            })

    # 4. Chuyển cảnh
    trans = scene.get("transition", {})
    t_type = trans.get("type", "fade")
    t_dur = float(trans.get("duration_seconds", 0.4))

    if t_type != "none" and t_dur > 0:
        trans_start = max(0.0, scene_dur - t_dur)
        if all_beats:
            trans_start = snap_to_nearest_beat(trans_start, all_beats, tolerance=0.2)
            trans_start = min(trans_start, scene_dur - 0.1)

        dict_events.append({
            "id": f"{scene_id}_trans_start",
            "scene_id": scene_id,
            "time": round(trans_start, 3),
            "type": "transition_start",
            "target": "scene",
            "duration": t_dur,
            "payload": {"transition_type": t_type}
        })

    dict_events.sort(key=lambda x: (x["time"], x["id"]))

    is_valid, errs = validate_timeline_events(dict_events, total_duration=scene_dur)
    if not is_valid:
        raise TimelineValidationError(f"Lỗi lập lịch timeline cho cảnh '{scene_id}': {'; '.join(errs)}")

    return {
        "valid": is_valid,
        "scene_id": scene_id,
        "effective_duration_seconds": round(scene_dur, 3),
        "alignment_mode": resolved_mode,
        "event_count": len(dict_events),
        "events": dict_events
    }
