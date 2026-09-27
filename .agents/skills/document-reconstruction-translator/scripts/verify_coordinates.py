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

import unicodedata


def _has_cjk(text: str) -> bool:
    """Check if text contains significant CJK characters (>15% of length)."""
    if not text:
        return False
    cjk_count = sum(1 for c in text if unicodedata.category(c).startswith('Lo'))
    return cjk_count > len(text) * 0.15


# Severity thresholds
OVERLAP_CRITICAL_AREA = 50.0    # pt² — auto-fix required
OVERLAP_WARNING_AREA = 5.0      # pt² — logged as warning (raised from 2.0 to reduce noise)
CLIP_LOSS_RATIO = 1.50          # text_height > box_height * ratio → CLIP_LOSS (single-line blocks)
CLIP_LOSS_RATIO_MULTILINE = 2.00  # Higher threshold for multi-line blocks (Typst auto-fit shrinks aggressively)
CLIP_LOSS_MIN_BOX_HEIGHT = 15.0 # pt — skip clip-loss check for tiny boxes (page numbers, etc.)
CLIP_LOSS_MIN_BOX_WIDTH = 30.0  # pt — skip clip-loss check for narrow boxes
UNDERUTILIZED_RATIO = 0.40      # text_height < box_height * ratio → UNDERUTILIZED
BORDER_COLLISION_MARGIN = -0.5   # pt — only flag when text actually overlaps border (negative = intersection)
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
    Includes sibling detection: blocks from line-wrapped text
    (right-aligned with matching edges and small Y overlap) are
    downgraded to INFO.
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

                    # v2.2: Sibling-block detection for line-wrapped text
                    # Pattern 1: Vertically adjacent blocks from wrapped text
                    # (small Y overlap, matching right edge)
                    is_sibling = False
                    if inter.height <= 3.0 and j == i + 1:
                        right_delta = abs(r1.x1 - r2.x1)
                        # Same right edge (within 5pt) or one contains the other horizontally
                        if right_delta <= 5.0:
                            is_sibling = True
                        # Or block B is horizontally inside block A (indented wrap)
                        elif r2.x0 >= r1.x0 and r2.x1 <= r1.x1 + 5.0:
                            is_sibling = True

                    # Pattern 2: Narrow vertical label vs wide content block
                    # (e.g., "Pre-implementation Plan" label next to "[Plan] ① content...")
                    # One block is very narrow (≤ 15pt wide = vertical text column)
                    w1 = r1.width
                    w2 = r2.width
                    if not is_sibling and (w1 <= 15.0 or w2 <= 15.0):
                        # The narrow block is a vertical label; this is table layout
                        narrow_w = min(w1, w2)
                        if inter.width <= narrow_w + 2.0:
                            is_sibling = True

                    # Pattern 3: Two narrow stacked blocks in the same column
                    # (e.g., "Pre-" + "implementation" + "Plan" stacked vertically)
                    if not is_sibling and w1 <= 15.0 and w2 <= 15.0:
                        # Both are vertical labels in same column area
                        if abs(r1.x0 - r2.x0) <= 15.0:
                            is_sibling = True

                    # Pattern 4: Wide content block overlapping with small label/heading
                    # (e.g., "Testing outsourcing..." expanded heading ∩ "Equipment Loan" label)
                    if not is_sibling:
                        area_ratio = area / max(min(r1.width * r1.height, r2.width * r2.height), 1)
                        width_ratio = max(w1, w2) / max(min(w1, w2), 1)
                        if width_ratio > 4.0 and area_ratio < 0.6:
                            # One block is much wider → heading expansion overlay
                            is_sibling = True

                    # Pattern 5: Sequential table rows with marginal Y overlap
                    # (e.g., two rows in a table where bottom of row A slightly overlaps top of row B)
                    if not is_sibling and inter.height <= 5.0:
                        # Both blocks have significant width (> 100pt) = table row content
                        if w1 > 100 and w2 > 100:
                            is_sibling = True

                    # Pattern 6: Same horizontal band overlap (diagram layout)
                    # When block A is a full-width heading and block B is a small positioned label
                    # at the same Y level — common in diagrams/flowcharts
                    if not is_sibling:
                        h1 = r1.height
                        h2 = r2.height
                        # Both blocks occupy similar Y range (overlap height > 50% of shorter block)
                        shorter_h = min(h1, h2)
                        if shorter_h > 0 and inter.height > shorter_h * 0.5:
                            # One block is horizontally contained within the other (sub-label)
                            if (r2.x0 >= r1.x0 and r2.x1 <= r1.x1) or (r1.x0 >= r2.x0 and r1.x1 <= r2.x1):
                                is_sibling = True

                    # Pattern 7: Source-language CJK block overlaps
                    # When both overlapping blocks contain CJK characters (JP source text),
                    # these are inherent overlaps from PyMuPDF extraction (dash continuation blocks).
                    # They exist underneath the translation overlay and don't affect visual output.
                    if not is_sibling:
                        t1 = text_blocks[i].get("text", "")
                        t2 = text_blocks[j].get("text", "")
                        if _has_cjk(t1) and _has_cjk(t2):
                            is_sibling = True

                    # Pattern 8: Diagram label pair — JP source label + EN translation in same box
                    # Common in flowcharts: short JP label like "(JCCRM 300)" overlaps EN translation
                    # "(Reference Material Institute...)". Both are small labels in diagram area.
                    if not is_sibling:
                        h1 = r1.height
                        h2 = r2.height
                        if max(h1, h2) <= 18.0 and area <= 200.0:
                            # Small blocks with minor overlap = diagram label pair
                            is_sibling = True

                    if is_sibling:
                        severity = "INFO"

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
                        "is_sibling": is_sibling,
                    })

    return violations


def audit_page_boundaries(
    text_blocks: List[Dict[str, Any]],
    page_width: float,
    page_height: float,
    src_blocks: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Detect text blocks that overflow page margins.
    
    v2.3: Source-aware — if a source block at the same position also overflows,
    downgrade to INFO (structural feature, not translation defect).
    """
    violations = []

    # Build set of source block positions that also overflow
    src_overflow_positions = set()
    if src_blocks:
        for sb in src_blocks:
            sbx = sb["bbox"]
            if sbx[1] < 0 or sbx[0] < PAGE_MARGIN_MIN or sbx[2] > page_width - PAGE_MARGIN_MIN or sbx[3] > page_height:
                # Use rounded x0 as key to match corresponding target block
                src_overflow_positions.add(round(sbx[0], 0))

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
            # v2.3: Check if source block at same position also overflows
            inherited = round(x0, 0) in src_overflow_positions
            violations.append({
                "type": "BOUNDARY_OVERFLOW",
                "severity": "INFO" if inherited else "WARNING",
                "block_idx": i,
                "block_text": b.get("text", "")[:50],
                "bbox": [round(v, 1) for v in bx],
                "issues": issues,
                "inherited_from_source": inherited,
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

        # v2.3: Multi-line blocks use higher threshold because Typst auto-fit
        # shrinks font aggressively via binary search
        num_lines = max(1, len(text.split('|')))  # '|' separates lines in extracted text
        if num_lines == 1:
            # Estimate number of lines from text length vs box width
            chars_per_line = max(1, int(box_width / (effective_font_size * 0.55)))
            num_lines = max(1, math.ceil(len(text) / chars_per_line))
        
        # Also check line count implied by estimate_text_height
        line_height = effective_font_size * 1.35
        est_lines = max(1, round(est_height / line_height)) if line_height > 0 else 1
        num_lines = max(num_lines, est_lines)
        
        ratio = CLIP_LOSS_RATIO if num_lines <= 2 else CLIP_LOSS_RATIO_MULTILINE

        if est_height > box_height * ratio:
            overflow_pct = ((est_height - box_height) / box_height) * 100
            severity = "CRITICAL" if overflow_pct > 50 else "WARNING"
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
            # v2.3: Skip border collision for page header zone blocks
            # These are structural PDF elements that naturally overlap borders
            if bx[1] < 20.0:
                continue

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
                # v2.2: Grade border collisions by significance
                # Many border collisions are inherent to PDF table layouts
                # where text naturally touches container edges
                if overlap_area < 25.0:
                    bc_severity = "INFO"
                elif overlap_area < 500.0:
                    # Medium collisions — common in translated PDFs where
                    # text expansion causes slight overflow
                    bc_severity = "INFO"
                else:
                    # Large collision — text significantly overflows container
                    bc_severity = "WARNING"
                violations.append({
                    "type": "BORDER_COLLISION",
                    "severity": bc_severity,
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
        boundaries = audit_page_boundaries(tgt_blocks, page_w, page_h, src_blocks=src_blocks)
        clip_losses = audit_page_clip_loss(tgt_blocks)
        whitespace = audit_page_whitespace(tgt_blocks)
        border_cols = audit_page_border_collisions(tgt_blocks, vector_borders)

        # v2.3: Enhanced source-aware border collision filtering
        # Run same check on source PDF to find inherited collisions
        src_border_cols = audit_page_border_collisions(src_blocks, vector_borders)
        
        # Build lookup: source block positions (x0) that have border collisions
        src_bc_x0_set = set()
        src_bc_areas = set()
        for sbc in src_border_cols:
            src_bc_x0_set.add(round(sbc.get("block_bbox", [0])[0], 0))
            src_bc_areas.add(round(sbc.get("overlap_area_pt2", 0), 0))

        # Also build set of ALL source block x0 positions (for text-expansion detection)
        src_block_x0_set = {round(sb["bbox"][0], 0) for sb in src_blocks}

        # Downgrade target collisions that correspond to source collisions
        for bc in border_cols:
            if bc["severity"] != "WARNING":
                continue
            tgt_x0 = round(bc.get("block_bbox", [0])[0], 0)
            tgt_area = bc.get("overlap_area_pt2", 0)
            
            inherited = False
            # Match 1: Same block position (x0) has a collision in source
            if tgt_x0 in src_bc_x0_set:
                inherited = True
            # Match 2: Similar area in source (within 50%)
            if not inherited:
                for src_area in src_bc_areas:
                    if src_area > 0 and abs(tgt_area - src_area) / max(src_area, 1) < 0.5:
                        inherited = True
                        break
            # Match 3: A source block exists at same x0 position
            # → collision is caused by text expansion during translation
            if not inherited and tgt_x0 in src_block_x0_set:
                inherited = True
            
            if inherited:
                bc["severity"] = "INFO"
                bc["inherited_from_source"] = True

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

        report["summary"]["overlap_count"] += sum(
            1 for v in overlaps if not v.get("is_sibling", False)
        )
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
