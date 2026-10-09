#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
motion_director.py — Động cơ điều phối & nội suy chuyển động (Motion Director Engine).
Tính toán tham số chuyển động (toạ độ, phóng to, xoay, độ mờ) theo hàm Easing và tính tất định (Luật R7).
"""

import math
from typing import Dict, Any, List, Tuple, Optional, Callable


# ============================================================
# 1. Thuật toán Easing (Hàm nội suy đường cong chuyển động)
# ============================================================

def linear(t: float) -> float:
    """Nội suy tuyến tính đều."""
    return max(0.0, min(1.0, t))


def ease_in_quad(t: float) -> float:
    """Tăng tốc mượt mà (bậc 2)."""
    t = max(0.0, min(1.0, t))
    return t * t


def ease_out_quad(t: float) -> float:
    """Giảm tốc êm dịu (bậc 2)."""
    t = max(0.0, min(1.0, t))
    return t * (2.0 - t)


def ease_in_out_quad(t: float) -> float:
    """Tăng tốc lúc đầu và giảm tốc lúc kết thúc (bậc 2)."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 2.0 * t * t
    return -1.0 + (4.0 - 2.0 * t) * t


def ease_out_cubic(t: float) -> float:
    """Giảm tốc sâu (bậc 3)."""
    t = max(0.0, min(1.0, t))
    t -= 1.0
    return t * t * t + 1.0


def ease_in_out_cubic(t: float) -> float:
    """Tăng tốc và giảm tốc sâu (bậc 3)."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4.0 * t * t * t
    p = 2.0 * t - 2.0
    return 0.5 * p * p * p + 1.0


def spring_out(t: float, damping: float = 0.6) -> float:
    """Hiệu ứng đàn hồi (Spring bounce nhẹ, không làm lố)."""
    t = max(0.0, min(1.0, t))
    if t >= 1.0:
        return 1.0
    return 1.0 - math.exp(-damping * 10.0 * t) * math.cos(8.0 * math.pi * t)


def cubic_bezier(t: float, p1x: float = 0.25, p1y: float = 0.1, p2x: float = 0.25, p2y: float = 1.0) -> float:
    """
    Nội suy Bezier bậc 3 xấp xỉ chuẩn CSS.
    Đơn giản hóa cho tính toán nhanh: giải x(u) ≈ t rồi tính y(u).
    """
    t = max(0.0, min(1.0, t))
    # Sử dụng Newton-Raphson để tìm tham số u
    u = t
    for _ in range(5):
        # x(u) = 3*(1-u)^2*u*p1x + 3*(1-u)*u^2*p2x + u^3
        xu = 3 * ((1 - u) ** 2) * u * p1x + 3 * (1 - u) * (u ** 2) * p2x + (u ** 3)
        dx = 3 * (1 - u) ** 2 * p1x + 6 * (1 - u) * u * (p2x - p1x) + 3 * (u ** 2) * (1 - p2x)
        if abs(dx) < 1e-6:
            break
        u -= (xu - t) / dx
        u = max(0.0, min(1.0, u))
    # y(u) = 3*(1-u)^2*u*p1y + 3*(1-u)*u^2*p2y + u^3
    yu = 3 * ((1 - u) ** 2) * u * p1y + 3 * (1 - u) * (u ** 2) * p2y + (u ** 3)
    return max(0.0, min(1.5, yu))


EASING_MAP: Dict[str, Callable[[float], float]] = {
    "linear": linear,
    "ease-in": ease_in_quad,
    "ease-out": ease_out_quad,
    "ease-in-out": ease_in_out_quad,
    "ease-out-cubic": ease_out_cubic,
    "ease-in-out-cubic": ease_in_out_cubic,
    "spring": spring_out,
}


def evaluate_easing(easing_name: str, progress: float) -> float:
    """
    Đánh giá giá trị nội suy theo tên Easing.
    progress nằm trong khoảng [0.0, 1.0].
    """
    fn = EASING_MAP.get(easing_name.lower().strip(), linear)
    return fn(progress)


# Alias tương thích ngược và tiện lợi
calculate_easing = evaluate_easing


# ============================================================
# 2. Cường Độ Chuyển Động (Motion Intensity Profiles)
# ============================================================

INTENSITY_PROFILES = {
    "subtle": {
        "travel_distance_px": 20.0,
        "scale_delta": 0.05,
        "rotation_max_deg": 1.5,
        "stagger_delay_sec": 0.10,
        "duration_factor": 1.2
    },
    "moderate": {
        "travel_distance_px": 50.0,
        "scale_delta": 0.15,
        "rotation_max_deg": 3.0,
        "stagger_delay_sec": 0.06,
        "duration_factor": 1.0
    },
    "energetic": {
        "travel_distance_px": 90.0,
        "scale_delta": 0.30,
        "rotation_max_deg": 6.0,
        "stagger_delay_sec": 0.03,
        "duration_factor": 0.8
    }
}


def get_intensity_params(intensity: str = "moderate") -> Dict[str, float]:
    """Lấy tham số chuyển động vật lý theo cường độ mong muốn."""
    return INTENSITY_PROFILES.get(intensity.lower().strip(), INTENSITY_PROFILES["moderate"])


# ============================================================
# 3. Tính Tất Định Tuyệt Đối (Deterministic PRNG)
# ============================================================

def deterministic_hash(*keys, seed: Any = 42) -> float:
    """
    Hàm băm sinh số thực tất định trong khoảng [0.0, 1.0).
    Tuyệt đối không dùng Math.random() hay random() không có seed.
    Cùng các key và seed luôn trả về kết quả giống hệt nhau trên mọi nền tảng.
    """
    import hashlib
    key_str = ":".join(str(k) for k in keys) if keys else "default"
    combined = f"{seed}:{key_str}".encode("utf-8")
    h = hashlib.sha256(combined).hexdigest()
    # Lấy 8 ký tự hex đầu tiên chuyển thành int
    val = int(h[:8], 16)
    return val / float(0xFFFFFFFF)


def deterministic_float(*keys, min_val: float = 0.0, max_val: float = 1.0, seed: Any = 42) -> float:
    """Sinh số thực tất định trong khoảng [min_val, max_val]."""
    r = deterministic_hash(*keys, seed=seed)
    return min_val + r * (max_val - min_val)


def deterministic_choice(options: List[Any], *keys, seed: Any = 42) -> Any:
    """Chọn phần tử tất định từ danh sách."""
    if not options:
        return None
    r = deterministic_hash(*keys, seed=seed)
    idx = int(r * len(options))
    return options[min(idx, len(options) - 1)]


# ============================================================
# 4. Trạng Thái Chuyển Động & Nội Suy Khung Hình (Keyframing)
# ============================================================

class MotionState:
    """Đặc tả trạng thái thị giác của một phần tử tại một thời điểm."""
    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        rotation_deg: float = 0.0,
        opacity: float = 1.0
    ):
        self.x = x
        self.y = y
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.rotation_deg = rotation_deg
        self.opacity = max(0.0, min(1.0, opacity))

    def to_dict(self) -> Dict[str, float]:
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "scale_x": round(self.scale_x, 4),
            "scale_y": round(self.scale_y, 4),
            "rotation_deg": round(self.rotation_deg, 2),
            "opacity": round(self.opacity, 3)
        }


def interpolate_motion(
    start: MotionState,
    end: MotionState,
    progress: float,
    easing_name: str = "ease-out",
    easing: Optional[str] = None
) -> MotionState:
    """
    Nội suy trạng thái chuyển động giữa start và end theo tiến trình progress [0.0, 1.0].
    """
    resolved_easing = easing if easing is not None else easing_name
    progress = max(0.0, min(1.0, progress))
    factor = evaluate_easing(resolved_easing, progress)

    lerp = lambda a, b, f: a + (b - a) * f

    return MotionState(
        x=lerp(start.x, end.x, factor),
        y=lerp(start.y, end.y, factor),
        scale_x=lerp(start.scale_x, end.scale_x, factor),
        scale_y=lerp(start.scale_y, end.scale_y, factor),
        rotation_deg=lerp(start.rotation_deg, end.rotation_deg, factor),
        opacity=lerp(start.opacity, end.opacity, factor)
    )


# ============================================================
# 5. Kế Hoạch Chuyển Động Phân Cảnh (Scene Motion Planning)
# ============================================================

def plan_element_motion(
    *args,
    element_id: Optional[str] = None,
    motion_type: Optional[str] = None,
    duration: float = 3.0,
    intensity: str = "moderate",
    width: int = 1920,
    height: int = 1080,
    easing: str = "ease-out",
    seed: Any = 42,
    **kwargs
) -> Dict[str, Any]:
    """
    Sinh hướng dẫn chuyển động chi tiết (Start state, End state, Keyframes, Duration, Easing)
    cho một phần tử đồ họa dựa trên preset/motion_type và kích thước khung hình.
    Hỗ trợ cả 3 cách gọi linh hoạt:
    1. plan_element_motion(element_id="btn", motion_type="bounce", duration=3.0, intensity="moderate", seed=...)
    2. plan_element_motion("card", "slide_up", 2.0, "subtle", seed=...)
    3. plan_element_motion("scale_pop", 1920, 1080, intensity="moderate", easing="spring")
    """
    el_id = element_id
    m_type = motion_type
    dur = duration
    inten = intensity
    w = width
    h = height
    eas = easing
    s = seed

    if len(args) >= 1:
        first_arg = args[0]
        if len(args) >= 3 and isinstance(args[1], (int, float)) and isinstance(args[2], (int, float)):
            # Pattern 3: (preset_name, width, height, ...)
            m_type = str(first_arg)
            w = int(args[1])
            h = int(args[2])
            if len(args) >= 4:
                inten = str(args[3])
            if len(args) >= 5:
                eas = str(args[4])
            if len(args) >= 6:
                dur = float(args[5])
        else:
            # Pattern 2: (element_id, motion_type, duration, intensity, ...)
            el_id = str(first_arg)
            if len(args) >= 2:
                m_type = str(args[1])
            if len(args) >= 3 and isinstance(args[2], (int, float)):
                dur = float(args[2])
            if len(args) >= 4:
                inten = str(args[3])

    if not el_id:
        el_id = kwargs.get("id", "element")
    if not m_type:
        m_type = kwargs.get("preset", kwargs.get("preset_name", "fade_in"))

    params = get_intensity_params(inten)
    travel = params["travel_distance_px"]
    scale_d = params["scale_delta"]

    center_x = w / 2.0
    center_y = h / 2.0

    m_norm = str(m_type).lower().strip()

    if m_norm in ("slide_reveal", "slide_left"):
        start = MotionState(x=center_x - travel, y=center_y, scale_x=1.0, scale_y=1.0, opacity=0.0)
        end = MotionState(x=center_x, y=center_y, scale_x=1.0, scale_y=1.0, opacity=1.0)
    elif m_norm in ("slide_up", "kinetic_title"):
        start = MotionState(x=center_x, y=center_y + travel, scale_x=1.0 + scale_d, scale_y=1.0 + scale_d, opacity=0.0)
        end = MotionState(x=center_x, y=center_y, scale_x=1.0, scale_y=1.0, opacity=1.0)
    elif m_norm in ("scale_pop", "bounce"):
        start = MotionState(x=center_x, y=center_y, scale_x=max(0.0, 1.0 - scale_d), scale_y=max(0.0, 1.0 - scale_d), opacity=0.0)
        end = MotionState(x=center_x, y=center_y, scale_x=1.0, scale_y=1.0, opacity=1.0)
        eas = "spring" if eas == "ease-out" else eas
    else:
        # Mặc định: fade_in
        start = MotionState(x=center_x, y=center_y, scale_x=1.0, scale_y=1.0, opacity=0.0)
        end = MotionState(x=center_x, y=center_y, scale_x=1.0, scale_y=1.0, opacity=1.0)

    # Sinh keyframes tất định
    mid_state = interpolate_motion(start, end, 0.5, easing=eas)
    offset_rot = deterministic_float(el_id, "rot", min_val=-0.5, max_val=0.5, seed=s)
    mid_state.rotation_deg += offset_rot

    keyframes = [
        {"progress": 0.0, "time": 0.0, "state": start.to_dict()},
        {"progress": 0.5, "time": round(dur * 0.5, 3), "state": mid_state.to_dict()},
        {"progress": 1.0, "time": round(dur, 3), "state": end.to_dict()}
    ]

    return {
        "element_id": el_id,
        "motion_type": m_norm,
        "preset": m_norm,
        "intensity": inten,
        "easing": eas,
        "duration": dur,
        "duration_seconds": round(dur, 2),
        "seed": str(s),
        "start_state": start.to_dict(),
        "end_state": end.to_dict(),
        "keyframes": keyframes
    }
