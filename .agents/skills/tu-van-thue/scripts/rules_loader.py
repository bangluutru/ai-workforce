#!/usr/bin/env python3
"""Nạp tham số thuế có nguồn gốc từ standards/<module>.json.

Mỗi tham số có lịch sử hiệu lực và `verification_status`:
  PRIMARY_VERIFIED  đã đọc văn bản gốc, dùng bình thường
  CORROBORATED      nhiều nguồn trùng khớp, dùng được nhưng phải gắn cờ [CẦN XÁC MINH]
  SECONDARY_ONLY    chỉ có nguồn thứ cấp, KHÔNG dùng để tính
  UNVERIFIED        chưa kiểm chứng, KHÔNG dùng để tính

Schema:
{
  "module": "gtgt", "version": "2026-10-03",
  "params": {
    "ten_tham_so": [
      {"value": 0.08, "effective_from": "2025-07-01", "effective_to": "2026-12-31",
       "source": "NQ ...", "article": "Điều 1", "verification_status": "CORROBORATED",
       "verified_on": "2026-10-03", "quote": "...", "note": "..."}
    ]
  }
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

STANDARDS_DIR = Path(__file__).resolve().parents[1] / "standards"

USABLE = {"PRIMARY_VERIFIED", "CORROBORATED"}
FLAG_TEXT = "[CẦN XÁC MINH]"
ALL_STATUS = USABLE | {"SECONDARY_ONLY", "UNVERIFIED"}


class ParamError(Exception):
    """Tham số không tồn tại, không có hiệu lực tại ngày hỏi, hoặc chưa đủ độ tin cậy."""


@dataclass
class Param:
    name: str
    value: Any
    source: str
    article: str
    effective_from: str
    effective_to: Optional[str]
    status: str
    verified_on: str = ""
    quote: str = ""
    note: str = ""

    @property
    def needs_flag(self) -> bool:
        return self.status != "PRIMARY_VERIFIED"

    def citation(self) -> str:
        c = f"{self.source}, {self.article}" if self.article else self.source
        return f"{c} {FLAG_TEXT}" if self.needs_flag else c


def parse_date(v: Any) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    return datetime.strptime(str(v), "%Y-%m-%d").date()


@dataclass
class RuleSet:
    module: str
    version: str
    data: Dict[str, List[dict]]
    used: Dict[str, Param] = field(default_factory=dict)

    def get(self, name: str, on: Any, allow_unverified: bool = False) -> Param:
        """Lấy tham số hiệu lực tại ngày `on`. Ném ParamError nếu không dùng được."""
        if name not in self.data:
            raise ParamError(f"[{self.module}] không có tham số '{name}'")
        d = parse_date(on)
        for e in self.data[name]:
            start = parse_date(e["effective_from"])
            end = parse_date(e["effective_to"]) if e.get("effective_to") else None
            if start <= d and (end is None or d <= end):
                st = e.get("verification_status", "UNVERIFIED")
                if st not in ALL_STATUS:
                    raise ParamError(f"'{name}': trạng thái kiểm chứng không hợp lệ: {st}")
                if st not in USABLE and not allow_unverified:
                    raise ParamError(
                        f"'{name}' tại {d}: trạng thái {st} ({e.get('source', '?')}), "
                        "chưa đủ độ tin cậy để tính. Cần đọc văn bản gốc hoặc hỏi người dùng.")
                p = Param(name=name, value=e["value"], source=e.get("source", ""),
                          article=e.get("article", ""), effective_from=e["effective_from"],
                          effective_to=e.get("effective_to"), status=st,
                          verified_on=e.get("verified_on", ""), quote=e.get("quote", ""),
                          note=e.get("note", ""))
                self.used[name] = p
                return p
        raise ParamError(f"'{name}' không có hiệu lực tại ngày {d}")

    def value(self, name: str, on: Any, allow_unverified: bool = False) -> Any:
        return self.get(name, on, allow_unverified).value

    def provenance(self) -> List[dict]:
        """Danh sách tham số đã dùng, để ghi vào báo cáo/Excel."""
        return [{"param": p.name, "value": p.value, "citation": p.citation(),
                 "status": p.status, "effective_from": p.effective_from,
                 "effective_to": p.effective_to, "verified_on": p.verified_on}
                for p in self.used.values()]

    def flags(self) -> List[str]:
        return sorted({f"{p.name}: {p.citation()}" for p in self.used.values() if p.needs_flag})


def load(module: str, standards_dir: Optional[Path] = None) -> RuleSet:
    path = (standards_dir or STANDARDS_DIR) / f"{module}.json"
    if not path.exists():
        raise ParamError(f"Chưa có bộ tham số cho module '{module}' ({path.name})")
    raw = json.loads(path.read_text(encoding="utf-8"))
    params = raw.get("params")
    if not isinstance(params, dict):
        raise ParamError(f"{path.name}: thiếu khối 'params'")
    for name, entries in params.items():
        if not isinstance(entries, list) or not entries:
            raise ParamError(f"{path.name}: '{name}' phải là danh sách phiên bản hiệu lực")
        for e in entries:
            for k in ("value", "effective_from", "source", "verification_status"):
                if k not in e:
                    raise ParamError(f"{path.name}: '{name}' thiếu trường '{k}'")
    return RuleSet(module=raw.get("module", module), version=raw.get("version", ""), data=params)


def validate_all(standards_dir: Optional[Path] = None) -> List[str]:
    """Kiểm tra mọi tệp module trong standards/. Trả về danh sách lỗi (rỗng = đạt)."""
    errors: List[str] = []
    base = standards_dir or STANDARDS_DIR
    for p in sorted(base.glob("*.json")):
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            errors.append(f"{p.name}: JSON lỗi: {ex}")
            continue
        if "params" not in raw:
            continue  # tệp kiểu cũ (ví dụ bieu_thue_2026.json) do engine TNCN quản lý
        try:
            rs = load(p.stem, base)
        except ParamError as ex:
            errors.append(str(ex))
            continue
        for name, entries in rs.data.items():
            for e in entries:
                if e["verification_status"] not in ALL_STATUS:
                    errors.append(f"{p.name}: '{name}' trạng thái lạ {e['verification_status']}")
                if e["verification_status"] == "PRIMARY_VERIFIED" and not e.get("quote"):
                    errors.append(f"{p.name}: '{name}' PRIMARY_VERIFIED nhưng thiếu 'quote'")
    return errors


if __name__ == "__main__":
    errs = validate_all()
    for e in errs:
        print("✗", e)
    print("✅ ĐẠT" if not errs else f"{len(errs)} lỗi")
    raise SystemExit(1 if errs else 0)
