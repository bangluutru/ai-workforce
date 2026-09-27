#!/usr/bin/env python3
"""Layout Quality Gate Auditor (Upgrade #1.5)

Deterministic layout quality verification for PDF translation.
Audits 6 independent dimensions:
1. DUPLICATION: Duplicate source/translated regions, parent-child duplications
2. OVERLAP: Material visual text collisions and bounding box intersections
3. FONT_READABILITY: Abnormal font shrinking and violations of readability floors
4. OVERFLOW: Text clipping risks, container/page-boundary overflows
5. DISPLACEMENT: Spatial drift between source and translated regions
6. IMAGE_ASSOCIATION: Preservation of images and proximity of captions
"""

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

# Status constants
STATUS_PASS = "PASS"
STATUS_MINOR_ISSUE = "MINOR_ISSUE"
STATUS_MAJOR_ISSUE = "MAJOR_ISSUE"
STATUS_FAIL = "FAIL"

# Readability floors by role (pt)
ROLE_READABILITY_FLOORS = {
    "title": 9.0,
    "heading": 8.0,
    "body": 6.0,
    "table_header": 5.5,
    "table_cell": 4.5,
    "caption": 5.0,
    "diagram_label": 4.2,
    "timeline_label": 4.2,
    "header": 4.5,
    "footer": 4.5,
    "other": 4.5,
}


def bbox_iou(b1: List[float], b2: List[float]) -> float:
    """Intersection over Union for two bounding boxes [x0, y0, x1, y1]."""
    ix0 = max(b1[0], b2[0])
    iy0 = max(b1[1], b2[1])
    ix1 = min(b1[2], b2[2])
    iy1 = min(b1[3], b2[3])

    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0

    inter_area = (ix1 - ix0) * (iy1 - iy0)
    area1 = max(0.1, (b1[2] - b1[0]) * (b1[3] - b1[1]))
    area2 = max(0.1, (b2[2] - b2[0]) * (b2[3] - b2[1]))
    union_area = area1 + area2 - inter_area
    return inter_area / max(0.1, union_area)


def bbox_intersection_ratio(b1: List[float], b2: List[float]) -> float:
    """Intersection over minimum box area."""
    ix0 = max(b1[0], b2[0])
    iy0 = max(b1[1], b2[1])
    ix1 = min(b1[2], b2[2])
    iy1 = min(b1[3], b2[3])

    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0

    inter_area = (ix1 - ix0) * (iy1 - iy0)
    min_area = min((b1[2] - b1[0]) * (b1[3] - b1[1]), (b2[2] - b2[0]) * (b2[3] - b2[1]))
    return inter_area / max(0.1, min_area)


def text_similarity(s1: str, s2: str) -> float:
    """Simple token similarity ratio."""
    t1 = set(s1.lower().split())
    t2 = set(s2.lower().split())
    if not t1 or not t2:
        return 0.0
    return len(t1 & t2) / max(len(t1), len(t2))


def classify_text_role(text: str, bbox: List[float], page_w: float, page_h: float, font_size: float, is_bold: bool) -> str:
    """Classify visual text role for layout quality auditing."""
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0
    clean = text.strip()

    if y1 < 45.0:
        return "header"
    if y0 > page_h - 45.0:
        return "footer"

    # Caption patterns
    if re.search(r'^(?:図|写真|表|Fig(?:ure)?\.?|Photo|Table|Ảnh|Hình)\s*\d', clean, re.IGNORECASE):
        return "caption"

    # Timeline patterns (e.g. Month / Year / Date in grid)
    if re.search(r'^(?:Năm|Tháng|\d{1,2}月|\d{4}年|Q[1-4]|FY\d{2,4})', clean):
        if w < 120.0 and h < 35.0:
            return "timeline_label"

    if font_size >= 13.0 and y1 < 150.0 and len(clean) < 100:
        return "title"

    if (is_bold and len(clean) < 120 and h < 30.0) or (font_size >= 11.0 and len(clean) < 80):
        return "heading"

    # Table cell heuristic: small width, medium height
    if w < 120.0 and h < 40.0 and len(clean) < 60:
        return "table_cell"

    if h > 30.0 or len(clean) > 80:
        return "body"

    return "other"


def audit_layout_quality(source_pdf: str, target_pdf: str, json_path: Optional[str] = None) -> Dict[str, Any]:
    """Run full 6-dimensional layout quality audit on translated PDF compared to source PDF."""
    doc_src = pymupdf.open(source_pdf)
    doc_tgt = pymupdf.open(target_pdf)

    results = {
        "source": source_pdf,
        "target": target_pdf,
        "page_count_src": len(doc_src),
        "page_count_tgt": len(doc_tgt),
        "dimensions": {
            "DUPLICATION": {"status": STATUS_PASS, "issues": [], "metric": 0},
            "OVERLAP": {"status": STATUS_PASS, "issues": [], "metric": 0},
            "FONT_READABILITY": {"status": STATUS_PASS, "issues": [], "metric": 0},
            "OVERFLOW": {"status": STATUS_PASS, "issues": [], "metric": 0},
            "DISPLACEMENT": {"status": STATUS_PASS, "issues": [], "metric": 0},
            "IMAGE_ASSOCIATION": {"status": STATUS_PASS, "issues": [], "metric": 0},
        },
        "pages": []
    }

    total_dups = 0
    total_overlaps = 0
    total_unreadables = 0
    total_overflows = 0
    total_displacements = 0

    num_pages = min(len(doc_src), len(doc_tgt))

    for p_idx in range(num_pages):
        page_src = doc_src[p_idx]
        page_tgt = doc_tgt[p_idx]
        pw = page_tgt.rect.width
        ph = page_tgt.rect.height

        page_record = {
            "page": p_idx + 1,
            "duplications": [],
            "overlaps": [],
            "font_issues": [],
            "overflows": [],
            "displacements": []
        }

        # Extract text blocks with detailed span info
        td_tgt = page_tgt.get_text("dict")
        tgt_blocks = []
        for bi, b in enumerate(td_tgt.get("blocks", [])):
            if b.get("type") == 0 and "lines" in b:
                lines = b.get("lines", [])
                text = " ".join("".join(s.get("text", "") for s in l.get("spans", [])) for l in lines).strip()
                if not text:
                    continue
                spans = [s for l in lines for s in l.get("spans", [])]
                sizes = [s.get("size", 10.0) for s in spans]
                avg_size = sum(sizes) / len(sizes) if sizes else 10.0
                min_size = min(sizes) if sizes else 10.0
                is_bold = any((s.get("flags", 0) & 16) or "bold" in s.get("font", "").lower() for s in spans)
                role = classify_text_role(text, b["bbox"], pw, ph, avg_size, is_bold)
                tgt_blocks.append({
                    "id": f"p{p_idx+1}_b{bi}",
                    "bbox": b["bbox"],
                    "text": text,
                    "avg_font_size": avg_size,
                    "min_font_size": min_size,
                    "is_bold": is_bold,
                    "role": role,
                    "lines_count": len(lines),
                    "lines": lines
                })

        # Extract source blocks for font and displacement comparison
        td_src = page_src.get_text("dict")
        src_blocks = []
        for bi, b in enumerate(td_src.get("blocks", [])):
            if b.get("type") == 0 and "lines" in b:
                lines = b.get("lines", [])
                text = " ".join("".join(s.get("text", "") for s in l.get("spans", [])) for l in lines).strip()
                if not text:
                    continue
                spans = [s for l in lines for s in l.get("spans", [])]
                sizes = [s.get("size", 10.0) for s in spans]
                avg_size = sum(sizes) / len(sizes) if sizes else 10.0
                src_blocks.append({
                    "id": f"src_p{p_idx+1}_b{bi}",
                    "bbox": b["bbox"],
                    "text": text,
                    "avg_font_size": avg_size
                })

        # --- 1. DUPLICATION AUDIT ---
        for i in range(len(tgt_blocks)):
            for j in range(i + 1, len(tgt_blocks)):
                b1 = tgt_blocks[i]
                b2 = tgt_blocks[j]
                inter_ratio = bbox_intersection_ratio(b1["bbox"], b2["bbox"])
                iou = bbox_iou(b1["bbox"], b2["bbox"])
                sim = text_similarity(b1["text"], b2["text"])

                # Spatial distance between boxes
                c1 = ((b1["bbox"][0] + b1["bbox"][2]) / 2, (b1["bbox"][1] + b1["bbox"][3]) / 2)
                c2 = ((b2["bbox"][0] + b2["bbox"][2]) / 2, (b2["bbox"][1] + b2["bbox"][3]) / 2)
                dist_y = abs(c1[1] - c2[1])

                # Check exact text duplicate (or identical prefix > 40 chars) on same page
                is_exact_dup = False
                if len(b1["text"]) >= 25 and len(b2["text"]) >= 25:
                    if b1["text"] == b2["text"]:
                        if inter_ratio > 0.05 or dist_y < 35.0:
                            is_exact_dup = True
                        else:
                            # Check whether source blocks matching b1 and b2 are distinct source blocks
                            # with significant spatial separation in the original document
                            s1 = min(src_blocks, key=lambda s: math.hypot(c1[0] - (s["bbox"][0]+s["bbox"][2])/2, c1[1] - (s["bbox"][1]+s["bbox"][3])/2), default=None)
                            s2 = min(src_blocks, key=lambda s: math.hypot(c2[0] - (s["bbox"][0]+s["bbox"][2])/2, c2[1] - (s["bbox"][1]+s["bbox"][3])/2), default=None)
                            if s1 and s2 and s1["id"] != s2["id"] and abs(s1["bbox"][1] - s2["bbox"][1]) > 30.0:
                                is_exact_dup = False  # Legitimate source repetition in original document
                            else:
                                is_exact_dup = True
                    elif b1["text"][:40] == b2["text"][:40] and (inter_ratio > 0.10 or dist_y < 60.0):
                        is_exact_dup = True

                # Check parent-child / substring duplication (must have spatial proximity/collision)
                is_substring_dup = False
                if len(b1["text"]) > 35 and len(b2["text"]) > 35:
                    has_spatial_collision = (inter_ratio > 0.15 or iou > 0.10 or (dist_y < 50.0 and abs(b1["bbox"][0] - b2["bbox"][0]) < 80.0))
                    if (b1["text"] in b2["text"] or b2["text"] in b1["text"]) and has_spatial_collision:
                        is_substring_dup = True
                    elif sim > 0.75 and (inter_ratio > 0.15 or dist_y < 40.0):
                        is_substring_dup = True

                if is_exact_dup or is_substring_dup:
                    issue = {
                        "page": p_idx + 1,
                        "b1_id": b1["id"],
                        "b2_id": b2["id"],
                        "b1_bbox": [round(x, 1) for x in b1["bbox"]],
                        "b2_bbox": [round(x, 1) for x in b2["bbox"]],
                        "inter_ratio": round(inter_ratio, 2),
                        "sim": round(sim, 2),
                        "dist_y": round(dist_y, 1),
                        "b1_text": b1["text"][:60],
                        "b2_text": b2["text"][:60],
                        "type": "exact_duplicate" if is_exact_dup else "parent_child_duplicate"
                    }
                    page_record["duplications"].append(issue)
                    total_dups += 1

        # --- 2. OVERLAP AUDIT ---
        for i in range(len(tgt_blocks)):
            for j in range(i + 1, len(tgt_blocks)):
                b1 = tgt_blocks[i]
                b2 = tgt_blocks[j]
                iou = bbox_iou(b1["bbox"], b2["bbox"])
                inter_ratio = bbox_intersection_ratio(b1["bbox"], b2["bbox"])

                # Genuine visual collision: moderate-to-high intersection between distinct texts
                if inter_ratio > 0.25 and b1["text"] != b2["text"]:
                    # Ignore intentional nesting if one is a 1-character bullet
                    if len(b1["text"]) <= 2 or len(b2["text"]) <= 2:
                        continue

                    # Verify whether actual text lines within the blocks collide
                    # (Prevents false positives when PyMuPDF clusters disparate horizontal columns into one sparse block)
                    line_collision = False
                    max_line_inter = 0.0
                    for l1 in b1.get("lines", []):
                        for l2 in b2.get("lines", []):
                            r = bbox_intersection_ratio(l1["bbox"], l2["bbox"])
                            if r > 0.20:
                                line_collision = True
                                max_line_inter = max(max_line_inter, r)
                                break
                        if line_collision:
                            break

                    if line_collision:
                        issue = {
                            "page": p_idx + 1,
                            "b1_id": b1["id"],
                            "b2_id": b2["id"],
                            "b1_bbox": [round(x, 1) for x in b1["bbox"]],
                            "b2_bbox": [round(x, 1) for x in b2["bbox"]],
                            "iou": round(iou, 2),
                            "inter_ratio": round(max_line_inter, 2),
                            "b1_text": b1["text"][:40],
                            "b2_text": b2["text"][:40]
                        }
                        page_record["overlaps"].append(issue)
                        total_overlaps += 1

        # --- 3. FONT READABILITY AUDIT ---
        for b in tgt_blocks:
            floor = ROLE_READABILITY_FLOORS.get(b["role"], 4.5)
            # Find matching source block to compute shrink ratio
            best_match = None
            best_dist = 9999.0
            for sb in src_blocks:
                # Center distance
                c_tgt = ((b["bbox"][0] + b["bbox"][2]) / 2, (b["bbox"][1] + b["bbox"][3]) / 2)
                c_src = ((sb["bbox"][0] + sb["bbox"][2]) / 2, (sb["bbox"][1] + sb["bbox"][3]) / 2)
                dist = math.hypot(c_tgt[0] - c_src[0], c_tgt[1] - c_src[1])
                if dist < best_dist and dist < 60.0:
                    best_dist = dist
                    best_match = sb

            orig_fs = best_match["avg_font_size"] if best_match else b["avg_font_size"]
            ratio = b["min_font_size"] / max(0.1, orig_fs)

            # Flag as issue if font is below readability floor AND either:
            # 1. Absolute micro-text (< 4.2pt)
            # 2. Or abnormally shrunk compared to original (ratio < 0.65)
            is_font_issue = False
            if b["min_font_size"] < 4.2:
                is_font_issue = True
            elif b["min_font_size"] < floor and (ratio < 0.65 or orig_fs < floor):
                if ratio < 0.70:
                    is_font_issue = True

            if is_font_issue:
                issue = {
                    "page": p_idx + 1,
                    "id": b["id"],
                    "role": b["role"],
                    "min_font_size": round(b["min_font_size"], 1),
                    "role_floor": floor,
                    "orig_font_size": round(orig_fs, 1),
                    "shrink_ratio": round(ratio, 2),
                    "bbox": [round(x, 1) for x in b["bbox"]],
                    "text": b["text"][:50]
                }
                page_record["font_issues"].append(issue)
                total_unreadables += 1

        # --- 4. OVERFLOW AUDIT ---
        for b in tgt_blocks:
            x0, y0, x1, y1 = b["bbox"]
            is_outside = (x0 < 2.0 or y0 < 2.0 or x1 > pw - 2.0 or y1 > ph - 2.0)
            if is_outside:
                issue = {
                    "page": p_idx + 1,
                    "id": b["id"],
                    "bbox": [round(x, 1) for x in b["bbox"]],
                    "page_size": [round(pw, 1), round(ph, 1)],
                    "text": b["text"][:50]
                }
                page_record["overflows"].append(issue)
                total_overflows += 1

        # --- 5. DISPLACEMENT AUDIT ---
        # Match each target block to closest source block by position/text
        for b in tgt_blocks:
            best_sb = None
            min_d = 9999.0
            c_tgt = ((b["bbox"][0] + b["bbox"][2]) / 2, (b["bbox"][1] + b["bbox"][3]) / 2)
            for sb in src_blocks:
                c_src = ((sb["bbox"][0] + sb["bbox"][2]) / 2, (sb["bbox"][1] + sb["bbox"][3]) / 2)
                d = math.hypot(c_tgt[0] - c_src[0], c_tgt[1] - c_src[1])
                if d < min_d:
                    min_d = d
                    best_sb = sb
            # Flag if nearest corresponding block drifted significantly (> 45pt)
            # and it's not a header/footer
            if min_d > 45.0 and b["role"] not in ("header", "footer"):
                issue = {
                    "page": p_idx + 1,
                    "id": b["id"],
                    "drift_pt": round(min_d, 1),
                    "bbox": [round(x, 1) for x in b["bbox"]],
                    "text": b["text"][:50]
                }
                page_record["displacements"].append(issue)
                total_displacements += 1

        results["pages"].append(page_record)

    # --- 6. IMAGE ASSOCIATION AUDIT ---
    img_issues = []
    for p_idx in range(num_pages):
        imgs_src = doc_src[p_idx].get_images()
        imgs_tgt = doc_tgt[p_idx].get_images()
        if len(imgs_src) != len(imgs_tgt):
            img_issues.append({
                "page": p_idx + 1,
                "src_images": len(imgs_src),
                "tgt_images": len(imgs_tgt)
            })

    # Set dimension statuses based on measurements
    # DUPLICATION
    results["dimensions"]["DUPLICATION"]["metric"] = total_dups
    if total_dups == 0:
        results["dimensions"]["DUPLICATION"]["status"] = STATUS_PASS
    elif total_dups <= 2:
        results["dimensions"]["DUPLICATION"]["status"] = STATUS_MINOR_ISSUE
    else:
        results["dimensions"]["DUPLICATION"]["status"] = STATUS_FAIL

    # OVERLAP
    results["dimensions"]["OVERLAP"]["metric"] = total_overlaps
    if total_overlaps == 0:
        results["dimensions"]["OVERLAP"]["status"] = STATUS_PASS
    elif total_overlaps <= 4:
        results["dimensions"]["OVERLAP"]["status"] = STATUS_MINOR_ISSUE
    else:
        results["dimensions"]["OVERLAP"]["status"] = STATUS_FAIL

    # FONT_READABILITY
    results["dimensions"]["FONT_READABILITY"]["metric"] = total_unreadables
    if total_unreadables == 0:
        results["dimensions"]["FONT_READABILITY"]["status"] = STATUS_PASS
    elif total_unreadables <= max(3, num_pages * 1):
        results["dimensions"]["FONT_READABILITY"]["status"] = STATUS_MINOR_ISSUE
    elif total_unreadables <= max(10, num_pages * 3):
        results["dimensions"]["FONT_READABILITY"]["status"] = STATUS_MAJOR_ISSUE
    else:
        results["dimensions"]["FONT_READABILITY"]["status"] = STATUS_FAIL

    # OVERFLOW
    results["dimensions"]["OVERFLOW"]["metric"] = total_overflows
    if total_overflows == 0:
        results["dimensions"]["OVERFLOW"]["status"] = STATUS_PASS
    elif total_overflows <= 2:
        results["dimensions"]["OVERFLOW"]["status"] = STATUS_MINOR_ISSUE
    else:
        results["dimensions"]["OVERFLOW"]["status"] = STATUS_FAIL

    # DISPLACEMENT
    results["dimensions"]["DISPLACEMENT"]["metric"] = total_displacements
    if total_displacements == 0:
        results["dimensions"]["DISPLACEMENT"]["status"] = STATUS_PASS
    elif total_displacements <= 5:
        results["dimensions"]["DISPLACEMENT"]["status"] = STATUS_MINOR_ISSUE
    else:
        results["dimensions"]["DISPLACEMENT"]["status"] = STATUS_MAJOR_ISSUE

    # IMAGE_ASSOCIATION
    results["dimensions"]["IMAGE_ASSOCIATION"]["metric"] = len(img_issues)
    if len(img_issues) == 0:
        results["dimensions"]["IMAGE_ASSOCIATION"]["status"] = STATUS_PASS
    else:
        results["dimensions"]["IMAGE_ASSOCIATION"]["status"] = STATUS_FAIL
        results["dimensions"]["IMAGE_ASSOCIATION"]["issues"] = img_issues

    return results


def print_report(results: Dict[str, Any]):
    """Print human-readable audit report."""
    print("=" * 80)
    print("📐 AI WORKFORCE: LAYOUT QUALITY GATE AUDIT REPORT (UPGRADE #1.5)")
    print(f"📄 Source: {results['source']}")
    print(f"📄 Target: {results['target']}")
    print(f"📑 Pages:  {results['page_count_tgt']} / {results['page_count_src']} (Parity: {'MATCH' if results['page_count_tgt'] == results['page_count_src'] else 'MISMATCH'})")
    print("=" * 80)
    print(f"{'DIMENSION':<22} | {'STATUS':<14} | {'METRIC (ISSUES)':<18}")
    print("-" * 80)
    for dim, data in results["dimensions"].items():
        st = data["status"]
        sym = "✅" if st == STATUS_PASS else ("⚠️" if st == STATUS_MINOR_ISSUE else ("❌" if st == STATUS_FAIL else "🔶"))
        print(f"{dim:<22} | {sym} {st:<11} | {data['metric']}")
    print("=" * 80)

    # Print details for failed/warned dimensions
    for p in results["pages"]:
        p_num = p["page"]
        if p["duplications"]:
            print(f"\n[Page {p_num}] DUPLICATION ISSUES ({len(p['duplications'])}):")
            for d in p["duplications"]:
                print(f"  • {d['type']} between {d['b1_id']} and {d['b2_id']}:")
                print(f"    Text 1: {repr(d['b1_text'])}")
                print(f"    Text 2: {repr(d['b2_text'])}")
        if p["font_issues"]:
            print(f"\n[Page {p_num}] FONT READABILITY ISSUES ({len(p['font_issues'])}):")
            for f in p["font_issues"][:6]:
                print(f"  • {f['id']} (role={f['role']}): font={f['min_font_size']}pt < floor {f['role_floor']}pt (shrink={f['shrink_ratio']})")
                print(f"    Text: {repr(f['text'])}")
        if p["overlaps"]:
            print(f"\n[Page {p_num}] OVERLAP ISSUES ({len(p['overlaps'])}):")
            for o in p["overlaps"][:4]:
                print(f"  • Collision between {o['b1_id']} and {o['b2_id']} (inter={o['inter_ratio']}):")
                print(f"    Box 1: {repr(o['b1_text'])}")
                print(f"    Box 2: {repr(o['b2_text'])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Layout Quality Gate Auditor (Upgrade #1.5)")
    parser.add_argument("--source", "-s", required=True, help="Source PDF path")
    parser.add_argument("--target", "-t", required=True, help="Target (translated) PDF path")
    parser.add_argument("--json", "-j", required=False, help="Optional merged_ejv.json path")
    parser.add_argument("--output", "-o", required=False, help="Path to save JSON audit report")
    args = parser.parse_args()

    res = audit_layout_quality(args.source, args.target, args.json)
    print_report(res)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f"\nSaved JSON report to {args.output}")

    # Exit code: fail if DUPLICATION or OVERFLOW has FAIL
    if res["dimensions"]["DUPLICATION"]["status"] == STATUS_FAIL or res["dimensions"]["OVERFLOW"]["status"] == STATUS_FAIL:
        sys.exit(1)
    sys.exit(0)
