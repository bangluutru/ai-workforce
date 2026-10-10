#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIWF Creative Studio 2.0 — Visual QA Report Builder (Luật R7).
Tổng hợp kết quả thẩm định kỹ thuật và thị giác thành báo cáo cấu trúc JSON
và định dạng Markdown tóm tắt, xuất bản khuyến nghị sửa chữa cụ thể.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .frame_sampler import sample_video_frames
from .technical_validator import validate_video_technical, TechnicalValidationResult
from .visual_inspector import inspect_visual_frames, VisualInspectionResult
from .contact_sheet import generate_contact_sheet


@dataclass
class QAReport:
    video_path: str
    overall_verdict: str  # "PASS", "WARN", "FAIL"
    overall_score: int  # 0 -> 100
    technical: Dict[str, Any]
    visual: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)
    contact_sheet_path: Optional[str] = None

    def to_json(self, output_path: str) -> str:
        """Xuất báo cáo sang file JSON."""
        data = asdict(self)
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(out_file.resolve())

    def to_markdown(self) -> str:
        """Xuất báo cáo dạng Markdown bảng chuẩn."""
        status_icon = "✅" if self.overall_verdict == "PASS" else ("⚠️" if self.overall_verdict == "WARN" else "❌")
        tech_m = self.technical.get("metrics", {})
        
        md_lines = [
            f"# {status_icon} BÁO CÁO KIỂM TOÁN THỊ GIÁC & KỸ THUẬT (VISUAL QA 2.0)",
            "",
            f"**Tệp video:** `{self.video_path}`  ",
            f"**Kết luận chung:** **{self.overall_verdict}** ({self.overall_score}/100 điểm)  ",
            f"**Ảnh tiếp xúc (Contact Sheet):** `{self.contact_sheet_path or 'Không tạo'}`  ",
            "",
            "## 1. Thông số kỹ thuật đo lường",
            "",
            "| Chỉ số kỹ thuật | Giá trị đo được | Đánh giá |",
            "|:---|:---:|:---:|",
            f"| **Độ phân giải** | {tech_m.get('width', 0)}x{tech_m.get('height', 0)} ({tech_m.get('aspect_ratio', 'N/A')}) | {'✅ Chuẩn' if self.technical.get('success') else '⚠️ Cần kiểm tra'} |",
            f"| **Tốc độ khung hình (FPS)** | {tech_m.get('fps', 0)} FPS | Chuẩn |",
            f"| **Thời lượng thực tế** | {tech_m.get('duration', 0):.2f}s ({tech_m.get('nb_frames', 0)} frames) | Chuẩn |",
            f"| **Video Codec / PixFmt** | {tech_m.get('video_codec', 'N/A')} / {tech_m.get('pix_fmt', 'N/A')} | Chuẩn Web |",
            f"| **Luồng âm thanh (Audio)** | {'Có sẵn (' + str(tech_m.get('audio_codec')) + ')' if tech_m.get('has_audio') else 'Không có'} | Thông tin |",
            "",
            "## 2. Phát hiện chi tiết",
            "",
        ]

        all_findings = []
        for f in self.technical.get("findings", []):
            all_findings.append(("Kỹ thuật", f.get("level"), f.get("code"), f.get("message")))
        for f in self.visual.get("findings", []):
            all_findings.append(("Thị giác", f.get("level"), f.get("code"), f.get("message")))

        if all_findings:
            md_lines.extend([
                "| Phân loại | Mức độ | Mã lỗi | Chi tiết phát hiện |",
                "|:---|:---:|:---|:---|",
            ])
            for cat, lvl, code, msg in all_findings:
                lvl_icon = "🔴" if lvl == "FAIL" else ("🟡" if lvl == "WARN" else "🔵")
                md_lines.append(f"| {cat} | {lvl_icon} {lvl} | `{code}` | {msg} |")
        else:
            md_lines.append("✅ Không phát hiện bất kỳ lỗi kỹ thuật hoặc thị giác nào.")

        if self.recommendations:
            md_lines.extend([
                "",
                "## 3. Khuyến nghị khắc phục",
                "",
            ])
            for rec in self.recommendations:
                md_lines.append(f"- 💡 {rec}")

        return "\n".join(md_lines)


def run_visual_qa(
    video_path: str,
    expected_spec: Optional[Dict[str, Any]] = None,
    generate_sheet: bool = True,
    sample_count: int = 12,
    output_dir: Optional[str] = None,
) -> QAReport:
    """
    Điểm vào chuẩn để thực hiện toàn bộ chu trình kiểm định Visual QA 2.0 cho một video.
    """
    # 1. Thẩm định kỹ thuật qua ffprobe
    tech_res: TechnicalValidationResult = validate_video_technical(video_path, expected_spec)

    # 2. Lấy mẫu khung hình
    work_out = Path(output_dir) if output_dir else Path(video_path).parent / "qa_output"
    work_out.mkdir(parents=True, exist_ok=True)

    frames = sample_video_frames(
        video_path=video_path,
        count=sample_count,
        target_width=480,
    )

    # 3. Phân tích thị giác trên các khung hình
    visual_res: VisualInspectionResult = inspect_visual_frames(frames)

    # 4. Tạo Contact Sheet nếu được yêu cầu
    sheet_path: Optional[str] = None
    if generate_sheet and frames:
        sheet_file = str(work_out / f"{Path(video_path).stem}_contact_sheet.jpg")
        try:
            sheet_path = generate_contact_sheet(frames, sheet_file)
        except Exception:
            sheet_path = None

    # 5. Tổng hợp điểm số và kết luận chung
    overall_score = int(round(tech_res.score * 0.5 + visual_res.score * 0.5))

    if tech_res.verdict == "FAIL" or visual_res.verdict == "FAIL":
        overall_verdict = "FAIL"
    elif tech_res.verdict == "WARN" or visual_res.verdict == "WARN":
        overall_verdict = "WARN"
    else:
        overall_verdict = "PASS"

    # 6. Xây dựng khuyến nghị sửa chữa tự động
    recommendations: List[str] = []
    for f in tech_res.findings:
        if f.code == "duration_mismatch":
            recommendations.append("Điều chỉnh lại thông số duration trong kịch bản phân cảnh hoặc storyboard.")
        elif f.code == "aspect_mismatch":
            recommendations.append("Đảm bảo CSS composition và lệnh render cùng khớp với tỷ lệ khung hình mục tiêu.")

    for vf in visual_res.findings:
        if vf.code == "excessive_black_frames":
            recommendations.append("Kiểm tra thời điểm bắt đầu/kết thúc các hiệu ứng fade-in và timeline GSAP, tránh để màn hình tối quá lâu.")
        elif vf.code == "completely_frozen_video":
            recommendations.append("Đảm bảo GSAP timeline đã được đăng ký vào window.__timelines['main'] và không có lỗi JS làm đứng hình.")

    report = QAReport(
        video_path=video_path,
        overall_verdict=overall_verdict,
        overall_score=overall_score,
        technical=asdict(tech_res),
        visual=asdict(visual_res),
        recommendations=recommendations,
        contact_sheet_path=sheet_path,
    )

    # Xuất file json nếu có output_dir
    report.to_json(str(work_out / f"{Path(video_path).stem}_technical_report.json"))

    return report
