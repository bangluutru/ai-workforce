"""Tiện ích chung cho các engine thuế: làm tròn, định dạng, kết quả có vết tính."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List


def vnd(x) -> int:
    """Làm tròn VNĐ về số nguyên theo quy tắc half-up (không dùng banker's rounding)."""
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def D(x) -> Decimal:
    """Chuyển số sang Decimal qua chuỗi để tránh nhiễu dấu phẩy động khi nhân thuế suất."""
    return Decimal(str(x))


def fmt(x: float) -> str:
    return f"{vnd(x):,}".replace(",", ".")


@dataclass
class Result:
    """Kết quả tính: số liệu + từng bước (để ghi báo cáo) + nguồn tham số + cờ cảnh báo."""
    module: str
    values: Dict[str, Any] = field(default_factory=dict)
    steps: List[str] = field(default_factory=list)
    provenance: List[dict] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def step(self, text: str) -> None:
        self.steps.append(text)

    def to_dict(self) -> dict:
        return {"module": self.module, "values": self.values, "steps": self.steps,
                "provenance": self.provenance, "flags": self.flags, "warnings": self.warnings}
