#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_coordinates.py — Bộ kiểm tra tọa độ hậu kỳ (Post-Processing Coordinate Auditor)

Tuân thủ:
- Skill: ejv-translate (Architecture v2 — Coordinate-Locked Verification)
- Rule: R2 (Code Quality — Zero-Inference Taxonomy)
- Rule: R3 (Operational Discipline — Per-Task Verification)
- Rule: R6 (Document Layout Preservation — 5 Pillars)

Mục đích:
Đối chiếu tọa độ bounding box giữa bản dịch và bản gốc để phát hiện:
1. Text Overlap — Các block chữ đè lên nhau
2. Boundary Overflow — Text tràn ra ngoài lề trang hoặc container
3. Clip Loss — Text bị cắt do box quá nhỏ (font đã co tối thiểu nhưng vẫn tràn)
4. Whitespace Waste — Khoảng trống dư thừa (text quá ngắn so với box)
5. Border Collision — Bounding box chồng lên đường vector viền

Sử dụng:
    python3 verify_coordinates.py \\
        --source <original.pdf> \\
        --target <translated.pdf> \\
        [--output report.md] \\
        [--json-output report.json]
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        print("❌ Lỗi: Chưa cài đặt thư viện 'pymupdf'. Hãy chạy: pip3 install pymupdf")
        sys.exit(1)

# Terminal Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Severity thresholds
OVERLAP_CRITICAL_AREA = 50.0    # pt² — auto-fix required
OVERLAP_WARNING_AREA = 5.0      # pt² — logged as warning (raised from 2.0 to reduce noise)
CLIP_LOSS_RATIO = 1.35          # text_height > box_height * ratio → CLIP_LOSS (accounts for Typst auto-fit shrinking)
CLIP_LOSS_MIN_BOX_HEIGHT = 15.0 # pt — skip clip-loss check for tiny boxes (page numbers, etc.)
CLIP_LOSS_MIN_BOX_WIDTH = 30.0  # pt — skip clip-loss check for narrow boxes
UNDERUTILIZED_RATIO = 0.40      # text_height < box_height * ratio → UNDERUTILIZED
BORDER_COLLISION_MARGIN = 1.0   # pt — minimum distance from vector borders
PAGE_MARGIN_MIN = 12.0          # pt — minimum page margin (PDF headers can be close to edge)


# ---------------------------------------------------------------------------
# Vector Drawing Analysis
# ---------------------------------------------------------------------------

def extract_vector_borders(page: pymupdf.Page) -> List[pymupdf.Rect]:
    """Extract rectangular borders (lines, rects) from PDF vector drawings.
    
    These represent diagram boxes, table borders, frames, etc.
    Returns list of Rects representing closed rectangular regions.
    """
    borders = []
    try:
        drawings = page.get_drawings()
    except Exception:
        return borders

    for d in drawings:
        # Filter for rectangles and lines that form borders
        items = d.get("items", [])
        rect = d.get("rect")
        if not rect:
            continue

        r = pymupdf.Rect(rect)
        # Only consider non-trivial rectangles (> 10pt in both dimensions)
        if r.width > 10 and r.height > 10:
            # Check if it's a stroke (border) rather than a fill
            stroke_color = d.get("color")
            fill_color = d.get("fill")
            stroke_width = d.get("width", 0)

            if stroke_color and stroke_width > 0:
                borders.append(r)
            elif fill_color and not stroke_color:
                # Filled rectangle (background) — still a container boundary
                borders.append(r)

    return borders


def find_container_for_block(
    block_rect: pymupdf.Rect,
    containers: List[pymupdf.Rect],
) -> Optional[pymupdf.Rect]:
    """Find the smallest container rectangle that fully encloses a text block.
    
    Used to detect diagram regions — text inside a vector box should not
    expand beyond the box boundary.
    """
    best = None
    best_area = float("inf")

    for c in containers:
        if c.contains(block_rect):
            area = c.width * c.height
            if area < best_area:
                best_area = area
                best = c

    return best


# ---------------------------------------------------------------------------
# Text Metrics Estimation
# ---------------------------------------------------------------------------

def estimate_text_height(
    text: str,
    font_size: float,
    box_width: float,
    leading_ratio: float = 1.25,
) -> float:
    """Estimate rendered text height given font size and box width.
    
    Uses character-count heuristic with average glyph width estimation:
    - Latin characters: ~0.5 * font_size average width
    - CJK characters: ~1.0 * font_size width
    
    Returns estimated height in points.
    """
    if not text or font_size <= 0 or box_width <= 0:
        return 0.0

    # Count characters by type
    latin_chars = 0
    cjk_chars = 0
    space_chars = 0
    for ch in text:
        cp = ord(ch)
        if ch in (' ', '\t'):
            space_chars += 1
        elif 0x3000 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF:
            cjk_chars += 1
        else:
            latin_chars += 1

    # Estimate total text width (conservative: Typst auto-fit will shrink font)
    # Use slightly smaller avg widths to avoid over-estimation
    avg_latin_width = font_size * 0.48
    avg_cjk_width = font_size * 0.95
    avg_space_width = font_size * 0.22

    total_text_width = (
        latin_chars * avg_latin_width
        + cjk_chars * avg_cjk_width
        + space_chars * avg_space_width
    )

    # Estimate number of lines
    if box_width > 0:
        num_lines = max(1, math.ceil(total_text_width / box_width))
    else:
        num_lines = 1

    # Add explicit newlines
    explicit_newlines = text.count('\n')
    num_lines += explicit_newlines

    # Estimated height
    line_height = font_size * leading_ratio
    return num_lines * line_height


# ---------------------------------------------------------------------------
# Core Audit Functions
# ---------------------------------------------------------------------------

def audit_page_overlaps(
    text_blocks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Detect overlapping text blocks on a single page.
    
    Returns list of overlap violations with severity.
    """
    violations = []

    for i in range(len(text_blocks)):
        for j in range(i + 1, len(text_blocks)):
            r1 = pymupdf.Rect(text_blocks[i]["bbox"])
            r2 = pymupdf.Rect(text_blocks[j]["bbox"])
            inter = r1 & r2  # intersection

            if not inter.is_empty:
                area = inter.width * inter.height
                if area > OVERLAP_WARNING_AREA:
                    severity = "CRITICAL" if area > OVERLAP_CRITICAL_AREA else "WARNING"
                    violations.append({
                        "type": "OVERLAP",
                        "severity": severity,
                        "block_a": i,
                        "block_b": j,
                        "block_a_text": text_blocks[i].get("text", "")[:50],
                        "block_b_text": text_blocks[j].get("text", "")[:50],
                        "block_a_bbox": list(r1),
                        "block_b_bbox": list(r2),
                        "intersection_area_pt2": round(area, 1),
                        "intersection_rect": [
                            round(inter.x0, 1), round(inter.y0, 1),
                            round(inter.x1, 1), round(inter.y1, 1),
                        ],
                    })

    return violations


def audit_page_boundaries(
    text_blocks: List[Dict[str, Any]],
    page_width: float,
    page_height: float,
) -> List[Dict[str, Any]]:
    """Detect text blocks that overflow page margins.
    
    Returns list of boundary violations.
    """
    violations = []

    for i, b in enumerate(text_blocks):
        bx = b["bbox"]
        x0, y0, x1, y1 = bx

        issues = []
        if x0 < PAGE_MARGIN_MIN:
            issues.append(f"LEFT overflow: x0={x0:.1f} < {PAGE_MARGIN_MIN}")
        if x1 > page_width - PAGE_MARGIN_MIN:
            issues.append(f"RIGHT overflow: x1={x1:.1f} > {page_width - PAGE_MARGIN_MIN:.1f}")
        if y0 < 0:
            issues.append(f"TOP overflow: y0={y0:.1f} < 0")
        if y1 > page_height:
            issues.append(f"BOTTOM overflow: y1={y1:.1f} > {page_height:.1f}")

        if issues:
            violations.append({
                "type": "BOUNDARY_OVERFLOW",
                "severity": "WARNING",
                "block_idx": i,
                "block_text": b.get("text", "")[:50],
                "bbox": [round(v, 1) for v in bx],
                "issues": issues,
            })

    return violations


def audit_page_clip_loss(
    text_blocks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Detect text blocks where content is likely clipped (text too large for box).
    
    Uses font metric estimation to compare rendered text height vs box height.
    """
    violations = []

    for i, b in enumerate(text_blocks):
        bx = b["bbox"]
        box_width = bx[2] - bx[0]
        box_height = bx[3] - bx[1]
        text = b.get("text", "")
        font_size = b.get("font_size", 10.0)

        if not text or box_height < CLIP_LOSS_MIN_BOX_HEIGHT or box_width < CLIP_LOSS_MIN_BOX_WIDTH:
            continue

        # Use a smaller effective font size to account for Typst auto-fit (binary search shrinking)
        effective_font_size = min(font_size, box_height * 0.85)
        est_height = estimate_text_height(text, effective_font_size, box_width)

        if est_height > box_height * CLIP_LOSS_RATIO:
            overflow_pct = ((est_height - box_height) / box_height) * 100
            severity = "CRITICAL" if overflow_pct > 30 else "WARNING"
            violations.append({
                "type": "CLIP_LOSS",
                "severity": severity,
                "block_idx": i,
                "block_text": text[:50],
                "bbox": [round(v, 1) for v in bx],
                "box_height_pt": round(box_height, 1),
                "estimated_text_height_pt": round(est_height, 1),
                "overflow_pct": round(overflow_pct, 1),
                "font_size": font_size,
            })

    return violations


def audit_page_whitespace(
    text_blocks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Detect text blocks with excessive unused whitespace.
    
    Flags blocks where estimated text height is less than 50% of box height,
    indicating potential for font size increase.
    """
    violations = []

    for i, b in enumerate(text_blocks):
        bx = b["bbox"]
        box_width = bx[2] - bx[0]
        box_height = bx[3] - bx[1]
        text = b.get("text", "")
        font_size = b.get("font_size", 10.0)

        if not text or box_height < 20 or box_width < 20:
            continue

        est_height = estimate_text_height(text, font_size, box_width)

        if est_height < box_height * UNDERUTILIZED_RATIO and box_height > 40:
            utilization_pct = (est_height / box_height) * 100
            violations.append({
                "type": "WHITESPACE_WASTE",
                "severity": "INFO",
                "block_idx": i,
                "block_text": text[:50],
                "bbox": [round(v, 1) for v in bx],
                "box_height_pt": round(box_height, 1),
                "estimated_text_height_pt": round(est_height, 1),
                "utilization_pct": round(utilization_pct, 1),
            })

    return violations


def audit_page_border_collisions(
    text_blocks: List[Dict[str, Any]],
    vector_borders: List[pymupdf.Rect],
) -> List[Dict[str, Any]]:
    """Detect text blocks that collide with vector borders (lines/rects).
    
    Checks if any text bounding box edge is within BORDER_COLLISION_MARGIN
    of a vector border edge, potentially causing visual artifacts.
    """
    violations = []

    for i, b in enumerate(text_blocks):
        bx = b["bbox"]
        block_rect = pymupdf.Rect(bx)

        for border in vector_borders:
            # Check if block partially overlaps a border edge
            inter = block_rect & border
            if inter.is_empty:
                continue

            # If the block is mostly inside the border container, skip
            # (it's expected to be inside)
            if border.contains(block_rect):
                continue

            # The block extends beyond a container border
            overlap_area = inter.width * inter.height
            block_area = block_rect.width * block_rect.height

            if 0 < overlap_area < block_area * 0.9:
                # Partial overlap = border collision
                violations.append({
                    "type": "BORDER_COLLISION",
                    "severity": "WARNING",
                    "block_idx": i,
                    "block_text": b.get("text", "")[:50],
                    "block_bbox": [round(v, 1) for v in bx],
                    "border_rect": [
                        round(border.x0, 1), round(border.y0, 1),
                        round(border.x1, 1), round(border.y1, 1),
                    ],
                    "overlap_area_pt2": round(overlap_area, 1),
                })

    return violations


# ---------------------------------------------------------------------------
# Main Audit Pipeline
# ---------------------------------------------------------------------------

def extract_text_blocks_from_page(page: pymupdf.Page) -> List[Dict[str, Any]]:
    """Extract text blocks with metadata from a PDF page."""
    text_dict = page.get_text("dict")
    blocks = []

    for b in text_dict.get("blocks", []):
        if b.get("type") != 0 or "lines" not in b:
            continue

        bbox = b.get("bbox")
        if not bbox or len(bbox) < 4:
            continue

        lines_text = []
        font_size = 10.0
        for line in b.get("lines", []):
            line_text = "".join(s.get("text", "") for s in line.get("spans", []))
            lines_text.append(line_text.strip())
            if line.get("spans"):
                font_size = line["spans"][0].get("size", font_size)

        full_text = " ".join(lines_text)

        blocks.append({
            "bbox": list(bbox),
            "text": full_text,
            "font_size": font_size,
        })

    return blocks


def audit_pdf(
    source_path: Path,
    target_path: Path,
) -> Dict[str, Any]:
    """Run full coordinate audit comparing source and target PDFs.
    
    Returns comprehensive audit report as a dictionary.
    """
    src_doc = pymupdf.open(source_path)
    tgt_doc = pymupdf.open(target_path)

    report = {
        "source_file": str(source_path),
        "target_file": str(target_path),
        "source_pages": len(src_doc),
        "target_pages": len(tgt_doc),
        "pages": [],
        "summary": {
            "total_critical": 0,
            "total_warning": 0,
            "total_info": 0,
            "overlap_count": 0,
            "boundary_count": 0,
            "clip_loss_count": 0,
            "whitespace_count": 0,
            "border_collision_count": 0,
        },
    }

    for pg_idx in range(min(len(src_doc), len(tgt_doc))):
        tgt_page = tgt_doc[pg_idx]
        src_page = src_doc[pg_idx]

        page_w = tgt_page.rect.width
        page_h = tgt_page.rect.height

        tgt_blocks = extract_text_blocks_from_page(tgt_page)
        src_blocks = extract_text_blocks_from_page(src_page)

        # Extract vector borders from SOURCE (original structure)
        vector_borders = extract_vector_borders(src_page)

        # Run all audits
        overlaps = audit_page_overlaps(tgt_blocks)
        boundaries = audit_page_boundaries(tgt_blocks, page_w, page_h)
        clip_losses = audit_page_clip_loss(tgt_blocks)
        whitespace = audit_page_whitespace(tgt_blocks)
        border_cols = audit_page_border_collisions(tgt_blocks, vector_borders)

        all_violations = overlaps + boundaries + clip_losses + whitespace + border_cols

        page_report = {
            "page_index": pg_idx,
            "page_dimensions": {"width": round(page_w, 1), "height": round(page_h, 1)},
            "source_text_blocks": len(src_blocks),
            "target_text_blocks": len(tgt_blocks),
            "vector_borders_detected": len(vector_borders),
            "violations": all_violations,
            "violation_counts": {
                "OVERLAP": len(overlaps),
                "BOUNDARY_OVERFLOW": len(boundaries),
                "CLIP_LOSS": len(clip_losses),
                "WHITESPACE_WASTE": len(whitespace),
                "BORDER_COLLISION": len(border_cols),
            },
        }

        report["pages"].append(page_report)

        # Update summary
        for v in all_violations:
            sev = v.get("severity", "INFO")
            if sev == "CRITICAL":
                report["summary"]["total_critical"] += 1
            elif sev == "WARNING":
                report["summary"]["total_warning"] += 1
            else:
                report["summary"]["total_info"] += 1

        report["summary"]["overlap_count"] += len(overlaps)
        report["summary"]["boundary_count"] += len(boundaries)
        report["summary"]["clip_loss_count"] += len(clip_losses)
        report["summary"]["whitespace_count"] += len(whitespace)
        report["summary"]["border_collision_count"] += len(border_cols)

    src_doc.close()
    tgt_doc.close()

    # Calculate overall score
    total_blocks = sum(p["target_text_blocks"] for p in report["pages"])
    total_violations = report["summary"]["total_critical"] + report["summary"]["total_warning"]
    if total_blocks > 0:
        report["summary"]["coordinate_precision_score"] = round(
            max(0, (1 - total_violations / total_blocks)) * 100, 1
        )
    else:
        report["summary"]["coordinate_precision_score"] = 100.0

    report["summary"]["overall_status"] = (
        "FAIL" if report["summary"]["total_critical"] > 0
        else "PASS" if report["summary"]["total_warning"] <= 3
        else "PASS_WITH_WARNINGS"
    )

    return report


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_markdown_report(report: Dict[str, Any]) -> str:
    """Generate human-readable Markdown report from audit results."""
    lines = []
    summary = report["summary"]
    status = summary["overall_status"]

    status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PASS_WITH_WARNINGS" else "❌"
    score = summary["coordinate_precision_score"]

    lines.append("# 📐 BÁO CÁO KIỂM TRA TỌA ĐỘ HẬU KỲ (COORDINATE PRECISION AUDIT)")
    lines.append("")
    lines.append(f"> **Tài liệu gốc (Source):** `{report['source_file']}`")
    lines.append(f"> **Tài liệu dịch (Target):** `{report['target_file']}`")
    lines.append(f"> **Số trang:** {report['source_pages']} → {report['target_pages']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🏆 KẾT QUẢ TỔNG QUAN")
    lines.append("")
    lines.append("| Chỉ số | Kết quả | Đánh giá |")
    lines.append("| :--- | :---: | :--- |")
    lines.append(f"| **Coordinate Precision Score** | **`{score}%`** | {status_emoji} **{status}** |")
    lines.append(f"| Lỗi nghiêm trọng (CRITICAL) | `{summary['total_critical']}` | {'❌ CẦN SỬA' if summary['total_critical'] > 0 else '✅'} |")
    lines.append(f"| Cảnh báo (WARNING) | `{summary['total_warning']}` | {'⚠️' if summary['total_warning'] > 0 else '✅'} |")
    lines.append(f"| Thông tin (INFO) | `{summary['total_info']}` | ℹ️ |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📊 PHÂN BỔ LỖI THEO LOẠI")
    lines.append("")
    lines.append("| Loại lỗi | Số lượng | Mô tả |")
    lines.append("| :--- | :---: | :--- |")
    lines.append(f"| **Text Overlap** | `{summary['overlap_count']}` | Các block chữ đè lên nhau |")
    lines.append(f"| **Boundary Overflow** | `{summary['boundary_count']}` | Text tràn ra ngoài lề trang |")
    lines.append(f"| **Clip Loss** | `{summary['clip_loss_count']}` | Text bị cắt do box quá nhỏ |")
    lines.append(f"| **Whitespace Waste** | `{summary['whitespace_count']}` | Khoảng trống dư thừa |")
    lines.append(f"| **Border Collision** | `{summary['border_collision_count']}` | Chữ chồng lên viền |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📋 CHI TIẾT THEO TỪNG TRANG")
    lines.append("")

    for page in report["pages"]:
        pg_idx = page["page_index"]
        violations = page["violations"]
        counts = page["violation_counts"]
        total_v = sum(counts.values())

        lines.append(f"### Trang {pg_idx + 1}")
        lines.append(f"- Kích thước: {page['page_dimensions']['width']}×{page['page_dimensions']['height']}pt")
        lines.append(f"- Text blocks (gốc/dịch): {page['source_text_blocks']}/{page['target_text_blocks']}")
        lines.append(f"- Vector borders: {page['vector_borders_detected']}")
        lines.append(f"- Tổng vi phạm: **{total_v}**")

        if not violations:
            lines.append("- ✅ Không có vi phạm")
        else:
            lines.append("")
            lines.append("| # | Loại | Mức | Chi tiết |")
            lines.append("| :---: | :--- | :---: | :--- |")
            for idx, v in enumerate(violations):
                vtype = v["type"]
                sev = v["severity"]
                sev_icon = "❌" if sev == "CRITICAL" else "⚠️" if sev == "WARNING" else "ℹ️"

                if vtype == "OVERLAP":
                    detail = (
                        f"Block {v['block_a']} ∩ Block {v['block_b']}: "
                        f"{v['intersection_area_pt2']}pt² — "
                        f"\"{v['block_a_text'][:25]}\" ↔ \"{v['block_b_text'][:25]}\""
                    )
                elif vtype == "BOUNDARY_OVERFLOW":
                    detail = f"Block {v['block_idx']}: {'; '.join(v['issues'])}"
                elif vtype == "CLIP_LOSS":
                    detail = (
                        f"Block {v['block_idx']}: box={v['box_height_pt']}pt, "
                        f"text≈{v['estimated_text_height_pt']}pt (+{v['overflow_pct']}%) — "
                        f"\"{v['block_text'][:30]}\""
                    )
                elif vtype == "WHITESPACE_WASTE":
                    detail = (
                        f"Block {v['block_idx']}: {v['utilization_pct']}% utilized — "
                        f"\"{v['block_text'][:30]}\""
                    )
                elif vtype == "BORDER_COLLISION":
                    detail = (
                        f"Block {v['block_idx']}: overlap={v['overlap_area_pt2']}pt² — "
                        f"\"{v['block_text'][:30]}\""
                    )
                else:
                    detail = str(v)

                lines.append(f"| {idx + 1} | {vtype} | {sev_icon} {sev} | {detail} |")

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Coordinate Precision Auditor — Kiểm tra tọa độ hậu kỳ bản dịch PDF"
    )
    parser.add_argument("--source", required=True, help="Đường dẫn PDF gốc")
    parser.add_argument("--target", required=True, help="Đường dẫn PDF dịch")
    parser.add_argument("--output", help="Đường dẫn xuất báo cáo Markdown (mặc định: stdout)")
    parser.add_argument("--json-output", help="Đường dẫn xuất báo cáo JSON")

    args = parser.parse_args()

    source = Path(args.source)
    target = Path(args.target)

    if not source.exists():
        print(f"❌ File gốc không tồn tại: {source}")
        sys.exit(1)
    if not target.exists():
        print(f"❌ File dịch không tồn tại: {target}")
        sys.exit(1)

    print(f"{CYAN}🔍 Đang kiểm tra tọa độ...{RESET}")
    print(f"   Gốc:  {source}")
    print(f"   Dịch:  {target}")
    print()

    report = audit_pdf(source, target)
    summary = report["summary"]

    # Console summary
    status = summary["overall_status"]
    score = summary["coordinate_precision_score"]
    status_color = GREEN if status == "PASS" else YELLOW if status == "PASS_WITH_WARNINGS" else RED
    print(f"{BOLD}📐 Coordinate Precision Score: {status_color}{score}%{RESET}")
    print(f"   Status: {status_color}{status}{RESET}")
    print(f"   Critical: {RED if summary['total_critical'] > 0 else GREEN}{summary['total_critical']}{RESET}")
    print(f"   Warning:  {YELLOW if summary['total_warning'] > 0 else GREEN}{summary['total_warning']}{RESET}")
    print(f"   Info:     {summary['total_info']}")
    print()

    # Per-page summary
    for page in report["pages"]:
        pg_idx = page["page_index"]
        total_v = sum(page["violation_counts"].values())
        critical = sum(1 for v in page["violations"] if v["severity"] == "CRITICAL")
        if critical > 0:
            print(f"   {RED}Page {pg_idx + 1}: {total_v} violations ({critical} CRITICAL){RESET}")
        elif total_v > 0:
            print(f"   {YELLOW}Page {pg_idx + 1}: {total_v} violations{RESET}")
        else:
            print(f"   {GREEN}Page {pg_idx + 1}: ✅ Clean{RESET}")

    print()

    # Output Markdown report
    md_report = generate_markdown_report(report)

    if args.output:
        out_path = Path(args.output).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_report, encoding="utf-8")
        print(f"{GREEN}📄 Markdown report: {out_path}{RESET}")

    # Output JSON report
    if args.json_output:
        json_path = Path(args.json_output).expanduser()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{GREEN}📄 JSON report: {json_path}{RESET}")

    # Exit code based on status
    if status == "FAIL":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
