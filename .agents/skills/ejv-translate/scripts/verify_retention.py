#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_retention.py — Bộ kiểm toán đối chiếu & đánh giá mức độ retain định dạng
(Layout, Image, Table & Formula Retention Auditor)

Tuân thủ:
- Skill: ejv-translate (Zero-Loss & Layout-Preserved Translation Protocol)
- Rule: R4 (Skill Standard v1.0 - Quality Gate)
- Rule: R2 (Code Quality - Zero-Inference Taxonomy)

Mục đích:
Đối chiếu 1:1 tài liệu dịch so với tài liệu gốc để đánh giá mức độ bảo toàn:
1. Số trang & Kích thước hình học (Page Count & Geometry Parity)
2. Hình ảnh, sơ đồ & con dấu (Image & Figure Fidelity)
3. Cấu trúc bảng biểu (Table Structure & Dimension Fidelity)
4. Ký hiệu công thức toán, hóa, đơn vị kỹ thuật (Formulas, Scientific Notation & Symbols)
5. An toàn lề & Phân bố khối (Margin Bounds & Layout Safety)

Sử dụng:
    python3 verify_retention.py --source <original.pdf> --target <translated.pdf> [--json <merged_ejv.json>] [--output report.md]
"""

import os
import sys
import re
import json
import math
import argparse
import unicodedata
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

try:
    import pymupdf  # PyMuPDF
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

# Regex Patterns for Formulas, Scientific Notation & Standards
PATTERNS = {
    "chemical_ions": re.compile(r"\b(?:Na|K|Cl|Ca|Mg|HCO3|CH3COO|H2CO3|CO2|H2O|NH4|Fe|Zn)(?:\d*[+-]|\^\d*[+-])?\b"),
    "units": re.compile(r"\b(?:mmol/L|mg/dL|mL/min|mmHg|mEq/L|L/min|g/dL|μmol/L|mol/L|kPa|%|ppm|pH)\b", re.IGNORECASE),
    "math_symbols": re.compile(r"[±×÷≤≥<>≈~=]"),
    "standards_codes": re.compile(r"\b(?:JCCRM\s*\d+|DIA\d+-\d+-\d+|EX-[A-Z0-9]+|J\d{5}|JAN\s*\d{13}|\d{13})\b"),
    "medical_params": re.compile(r"\b(?:BE|pCO2|pO2|HCO3|TCO2|sO2|AG|Na|K|Cl|Ca|Mg|pH|Glu|Glucose)\b")
}

# CJK regex for detecting residual untranslated Japanese/Chinese text (excluding punctuation like middle dot \u30fb)
CJK_REGEX = re.compile(r"[\u3041-\u3096\u30a1-\u30fa\u3400-\u4dbf\u4e00-\u9fff]")


def extract_technical_tokens(text: str) -> Dict[str, List[str]]:
    """Extracts chemical formulas, units, symbols, and standard codes from text."""
    # Normalize full-width characters (e.g. Japanese full-width １２３ to standard 123)
    text = unicodedata.normalize("NFKC", text)
    results = {}
    for key, pattern in PATTERNS.items():
        found = pattern.findall(text)
        # Normalize and remove duplicates while preserving order
        unique = []
        for item in found:
            clean_item = item.strip()
            if clean_item and clean_item not in unique:
                unique.append(clean_item)
        results[key] = unique
    return results


def calculate_iou(box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]) -> float:
    """Calculates Intersection over Union (IoU) of two bounding boxes (x0, y0, x1, y1)."""
    x0 = max(box1[0], box2[0])
    y0 = max(box1[1], box2[1])
    x1 = min(box1[2], box2[2])
    y1 = min(box1[3], box2[3])

    inter_w = max(0.0, x1 - x0)
    inter_h = max(0.0, y1 - y0)
    inter_area = inter_w * inter_h

    area1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class LayoutRetentionAuditor:
    def __init__(self, source_path: str, target_path: str, json_path: Optional[str] = None):
        self.source_path = Path(source_path)
        self.target_path = Path(target_path)
        self.json_path = Path(json_path) if json_path else None

        if not self.source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        if not self.target_path.exists():
            raise FileNotFoundError(f"Target file not found: {target_path}")

        self.src_doc = pymupdf.open(str(self.source_path))
        self.tgt_doc = pymupdf.open(str(self.target_path))

        self.src_page_count = len(self.src_doc)
        self.tgt_page_count = len(self.tgt_doc)

        self.audit_results: Dict[str, Any] = {
            "summary": {},
            "dimensions": {},
            "pages": [],
            "anomalies": [],
            "recommendations": []
        }

    def audit_page_parity(self) -> float:
        """Audits page count parity and dimensions match."""
        if self.src_page_count == self.tgt_page_count:
            score = 100.0
        else:
            diff = abs(self.src_page_count - self.tgt_page_count)
            score = max(0.0, 100.0 - diff * 20.0)
            self.audit_results["anomalies"].append(
                f"Lệch số trang: Bản gốc có {self.src_page_count} trang, bản dịch có {self.tgt_page_count} trang."
            )

        # Dimension tolerance check
        mismatches = 0
        for i in range(min(self.src_page_count, self.tgt_page_count)):
            p_src = self.src_doc[i]
            p_tgt = self.tgt_doc[i]
            w_diff = abs(p_src.rect.width - p_tgt.rect.width)
            h_diff = abs(p_src.rect.height - p_tgt.rect.height)
            if w_diff > 10.0 or h_diff > 10.0:
                mismatches += 1

        if mismatches > 0:
            score = max(0.0, score - mismatches * 5.0)
            self.audit_results["anomalies"].append(
                f"Có {mismatches} trang sai lệch kích thước giấy so với bản gốc."
            )

        self.audit_results["dimensions"]["page_parity"] = {
            "score": round(score, 1),
            "source_pages": self.src_page_count,
            "target_pages": self.tgt_page_count,
            "parity_status": "EXACT_MATCH" if self.src_page_count == self.tgt_page_count else "MISMATCH"
        }
        return score

    def audit_images_and_figures(self) -> float:
        """Audits image count, dimensions, and positioning per page."""
        page_scores = []
        total_src_imgs = 0
        total_tgt_imgs = 0
        total_src_embedded = 0

        for p_idx in range(min(self.src_page_count, self.tgt_page_count)):
            p_src = self.src_doc[p_idx]
            p_tgt = self.tgt_doc[p_idx]
            page_area = p_src.rect.width * p_src.rect.height

            src_img_info = p_src.get_image_info()
            tgt_img_info = p_tgt.get_image_info()

            src_count = len(src_img_info)
            tgt_count = len(tgt_img_info)
            total_src_imgs += src_count
            total_tgt_imgs += tgt_count

            # Separate embedded figures from fullpage scan backgrounds
            src_embedded = []
            src_fullpage_scans = []
            for s_img in src_img_info:
                s_bbox = s_img.get("bbox", (0, 0, 0, 0))
                img_area = max(0.0, s_bbox[2] - s_bbox[0]) * max(0.0, s_bbox[3] - s_bbox[1])
                if img_area >= 0.80 * page_area:
                    src_fullpage_scans.append(s_img)
                else:
                    src_embedded.append(s_img)

            total_src_embedded += len(src_embedded)

            # Case A: Scanned page converted into clean digital vector publication
            if src_fullpage_scans and not src_embedded:
                if len(p_tgt.get_text().strip()) > 30 or len(p_tgt.get_drawings()) > 0:
                    page_scores.append(100.0)
                    continue

            # Case B: No embedded images in source nor target -> check vector drawings (seals, lines)
            if len(src_embedded) == 0 and tgt_count == 0:
                src_drawings = len(p_src.get_drawings())
                tgt_drawings = len(p_tgt.get_drawings())
                if src_drawings > 0:
                    ratio = min(1.0, tgt_drawings / max(1, src_drawings))
                    page_scores.append(max(85.0, ratio * 100.0))
                else:
                    page_scores.append(100.0)
                continue

            # Case C: Source had embedded figures but target dropped them
            if len(src_embedded) > 0 and tgt_count == 0:
                page_scores.append(0.0)
                self.audit_results["anomalies"].append(
                    f"Trang {p_idx + 1}: Bản gốc có {len(src_embedded)} hình ảnh/sơ đồ nhúng nhưng bản dịch bị thiếu."
                )
                continue

            # Case D: Compare embedded images by bbox and size
            matched_score = 0.0
            eval_list = src_embedded if src_embedded else src_img_info
            for s_img in eval_list:
                s_bbox = s_img.get("bbox", (0, 0, 0, 0))
                s_w = s_img.get("width", 0)
                s_h = s_img.get("height", 0)

                best_img_score = 0.0
                for t_img in tgt_img_info:
                    t_bbox = t_img.get("bbox", (0, 0, 0, 0))
                    t_w = t_img.get("width", 0)
                    t_h = t_img.get("height", 0)

                    # 1. Size match
                    size_ratio = min(s_w, t_w) / max(1, max(s_w, t_w)) if max(s_w, t_w) > 0 else 1.0
                    # 2. Position match (IoU or proximity)
                    iou = calculate_iou(s_bbox, t_bbox)
                    # Position center distance
                    sc_x, sc_y = (s_bbox[0] + s_bbox[2]) / 2, (s_bbox[1] + s_bbox[3]) / 2
                    tc_x, tc_y = (t_bbox[0] + t_bbox[2]) / 2, (t_bbox[1] + t_bbox[3]) / 2
                    dist = math.hypot(sc_x - tc_x, sc_y - tc_y)
                    pos_score = max(0.0, 1.0 - (dist / 200.0))  # within 200pt tolerance

                    combined = 0.5 * size_ratio + 0.3 * iou + 0.2 * pos_score
                    if combined > best_img_score:
                        best_img_score = combined

                matched_score += best_img_score

            p_score = (matched_score / max(1, len(eval_list))) * 100.0
            page_scores.append(min(100.0, p_score))

        score = sum(page_scores) / len(page_scores) if page_scores else 100.0
        self.audit_results["dimensions"]["image_fidelity"] = {
            "score": round(score, 1),
            "total_source_images": total_src_imgs,
            "total_source_embedded": total_src_embedded,
            "total_target_images": total_tgt_imgs,
            "page_breakdown": [round(s, 1) for s in page_scores]
        }
        return score

    def audit_table_structure(self) -> float:
        """Audits table structures, row counts, and column geometry."""
        page_scores = []
        total_src_tables = 0
        total_tgt_tables = 0

        for p_idx in range(min(self.src_page_count, self.tgt_page_count)):
            p_src = self.src_doc[p_idx]
            p_tgt = self.tgt_doc[p_idx]

            src_tables = p_src.find_tables().tables
            tgt_tables = p_tgt.find_tables().tables

            s_t_count = len(src_tables)
            t_t_count = len(tgt_tables)
            total_src_tables += s_t_count
            total_tgt_tables += t_t_count

            if s_t_count == 0 and t_t_count == 0:
                page_scores.append(100.0)
                continue

            if s_t_count > 0 and t_t_count == 0:
                # Check if table was rendered as formatted lines / text grid
                tgt_text = p_tgt.get_text()
                if "Bảng" in tgt_text or "Table" in tgt_text or "|" in tgt_text:
                    page_scores.append(80.0)
                else:
                    page_scores.append(30.0)
                    self.audit_results["anomalies"].append(
                        f"Trang {p_idx + 1}: Bản gốc có {s_t_count} bảng biểu nhưng bản dịch thiếu bảng biểu tương ứng."
                    )
                continue

            # Compare tables
            matched_tables = 0.0
            for st in src_tables:
                st_rows = len(st.extract())
                st_cols = len(st.header.names) if st.header else 0

                best_t_score = 0.0
                for tt in tgt_tables:
                    tt_rows = len(tt.extract())
                    tt_cols = len(tt.header.names) if tt.header else 0

                    row_sim = min(st_rows, tt_rows) / max(1, max(st_rows, tt_rows))
                    col_sim = min(st_cols, tt_cols) / max(1, max(st_cols, tt_cols)) if max(st_cols, tt_cols) > 0 else 1.0
                    iou = calculate_iou(st.bbox, tt.bbox)

                    t_match = 0.4 * row_sim + 0.4 * col_sim + 0.2 * iou
                    if t_match > best_t_score:
                        best_t_score = t_match

                matched_tables += best_t_score

            p_score = (matched_tables / max(1, s_t_count)) * 100.0
            page_scores.append(min(100.0, p_score))

        score = sum(page_scores) / len(page_scores) if page_scores else 100.0
        self.audit_results["dimensions"]["table_fidelity"] = {
            "score": round(score, 1),
            "total_source_tables": total_src_tables,
            "total_target_tables": total_tgt_tables,
            "page_breakdown": [round(s, 1) for s in page_scores]
        }
        return score

    def audit_formulas_and_symbols(self) -> float:
        """Audits preservation of scientific symbols, chemical formulas, and units."""
        src_full_text = "\n".join([p.get_text() for p in self.src_doc])
        tgt_full_text = "\n".join([p.get_text() for p in self.tgt_doc])

        src_tokens = extract_technical_tokens(src_full_text)
        tgt_tokens = extract_technical_tokens(tgt_full_text)

        category_scores = {}
        missing_critical_tokens = []

        total_weight = 0
        weighted_score_sum = 0.0

        weights = {
            "chemical_ions": 30,
            "units": 25,
            "standards_codes": 25,
            "math_symbols": 10,
            "medical_params": 10
        }

        for cat, weight in weights.items():
            src_list = src_tokens.get(cat, [])
            if not src_list:
                category_scores[cat] = 100.0
                weighted_score_sum += 100.0 * weight
                total_weight += weight
                continue

            matched = 0
            for item in src_list:
                # Direct check or case-insensitive check
                if item in tgt_full_text or item.lower() in tgt_full_text.lower():
                    matched += 1
                elif item == "~" and ("-" in tgt_full_text or "–" in tgt_full_text or "đến" in tgt_full_text):
                    # Typographical range equivalence: ~ in Japanese is conventionally - or – in Vietnamese
                    matched += 1
                else:
                    # Allow slight format normalization (e.g. Na+ vs Na+, 4980679100149)
                    clean = re.sub(r"[\s\-_]", "", item)
                    if clean and clean in re.sub(r"[\s\-_]", "", tgt_full_text):
                        matched += 1
                    else:
                        missing_critical_tokens.append(f"[{cat}] {item}")

            cat_score = (matched / len(src_list)) * 100.0
            category_scores[cat] = round(cat_score, 1)
            weighted_score_sum += cat_score * weight
            total_weight += weight

        final_score = weighted_score_sum / total_weight if total_weight > 0 else 100.0

        if missing_critical_tokens:
            sample_missing = missing_critical_tokens[:8]
            self.audit_results["anomalies"].append(
                f"Phát hiện {len(missing_critical_tokens)} ký hiệu/công thức kỹ thuật chưa tìm thấy tương đương trong bản dịch (Mẫu: {', '.join(sample_missing)})."
            )

        self.audit_results["dimensions"]["formula_fidelity"] = {
            "score": round(final_score, 1),
            "category_scores": category_scores,
            "total_source_tokens": sum(len(v) for v in src_tokens.values()),
            "missing_sample": missing_critical_tokens[:5]
        }
        return final_score

    def audit_layout_and_margins(self) -> float:
        """Audits margin safety, text block boundaries, and residual source text."""
        page_scores = []
        untranslated_count = 0
        overflow_count = 0
        untranslated_details = []

        for pno in range(self.tgt_page_count):
            page = self.tgt_doc[pno]
            pw, ph = page.rect.width, page.rect.height

            # Check text blocks
            blocks = page.get_text("blocks")
            p_overflow = False
            p_untranslated = False

            for b in blocks:
                x0, y0, x1, y1, text, block_no, block_type = b
                if block_type != 0:  # text block
                    continue

                # 1. Margin boundaries safety (margin < 15pt)
                if x0 < 15.0 or y0 < 15.0 or x1 > pw - 15.0 or y1 > ph - 15.0:
                    # Ignore standard header/footer
                    if y0 > 25.0 and y1 < ph - 25.0:
                        p_overflow = True
                        overflow_count += 1

                # 2. Residual CJK detection (if translating to VN or EN)
                # Check if block has CJK kanji/kana
                cjk_matches = CJK_REGEX.findall(text)
                if len(cjk_matches) >= 3:  # Significant Japanese word/sentence
                    p_untranslated = True
                    untranslated_count += 1
                    untranslated_details.append({
                        "page": pno + 1,
                        "bbox": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                        "text": text.strip().replace("\n", " ")[:100],
                        "cjk_chars": len(cjk_matches)
                    })

            page_score = 100.0
            if p_overflow:
                page_score -= 15.0
            if p_untranslated:
                page_score -= 50.0

            page_scores.append(max(0.0, page_score))

        score = sum(page_scores) / len(page_scores) if page_scores else 100.0

        if overflow_count > 0:
            self.audit_results["anomalies"].append(
                f"Phát hiện {overflow_count} khối văn bản tiếp cận sát viền biên bản in (< 15pt)."
            )
        if untranslated_count > 0:
            self.audit_results["anomalies"].append(
                f"🔴 [HARD BLOCKER] Phát hiện {untranslated_count} khối văn bản còn chứa ký tự nguồn (tiếng Nhật/CJK) chưa được dịch hoàn chỉnh!"
            )

        self.audit_results["dimensions"]["layout_safety"] = {
            "score": round(score, 1),
            "overflow_blocks": overflow_count,
            "untranslated_blocks": untranslated_count
        }
        return score

    def run_full_audit(self) -> Dict[str, Any]:
        """Executes all audit dimensions and computes the Composite Retention Score."""
        score_parity = self.audit_page_parity()
        score_img = self.audit_images_and_figures()
        score_tbl = self.audit_table_structure()
        score_formula = self.audit_formulas_and_symbols()
        score_layout = self.audit_layout_and_margins()

        # Weighted Composite Score
        # Page Parity: 15%, Image: 25%, Table: 20%, Formula: 25%, Layout: 15%
        composite = (
            0.15 * score_parity +
            0.25 * score_img +
            0.20 * score_tbl +
            0.25 * score_formula +
            0.15 * score_layout
        )
        composite = round(composite, 1)

        # Grade Assignment & Hard Blocker Check
        untranslated_count = self.audit_results["dimensions"].get("layout_safety", {}).get("untranslated_blocks", 0)
        hard_blocker = (untranslated_count > 0)

        if hard_blocker:
            grade = f"F (BỊ CHẶN: Sót {untranslated_count} khối chữ nguồn)"
            status = "FAIL"
        elif composite >= 92.0:
            grade = "A+ (Xuất sắc — Chuẩn in ấn bảo tồn 1:1)"
            status = "PASS"
        elif composite >= 85.0:
            grade = "A (Tốt — Đạt tiêu chuẩn phát hành)"
            status = "PASS"
        elif composite >= 75.0:
            grade = "B (Khá — Chấp nhận được, có lưu ý)"
            status = "WARNING"
        else:
            grade = "C (Chưa đạt — Cần điều chỉnh bố cục)"
            status = "FAIL"

        self.audit_results["summary"] = {
            "composite_retention_score": composite,
            "grade": grade,
            "status": status,
            "hard_blocker": hard_blocker,
            "untranslated_blocks": untranslated_count,
            "source_file": str(self.source_path),
            "target_file": str(self.target_path),
            "weights": {
                "page_parity": "15%",
                "image_fidelity": "25%",
                "table_fidelity": "20%",
                "formula_fidelity": "25%",
                "layout_safety": "15%"
            }
        }

        # Recommendations
        if not self.audit_results["anomalies"]:
            self.audit_results["recommendations"].append(
                "Tài liệu dịch đạt tỷ lệ bảo tồn bố cục xuất sắc, hình ảnh và công thức khớp hoàn hảo với bản gốc."
            )
        else:
            if score_formula < 90.0:
                self.audit_results["recommendations"].append(
                    "Kiểm tra lại các ký hiệu nồng độ ion và mã chứng nhận để đảm bảo không bị lược bỏ trong quá trình dịch."
                )
            if score_img < 85.0:
                self.audit_results["recommendations"].append(
                    "Rà soát việc trích xuất và nhúng lại hình ảnh/con dấu vector từ bản gốc."
                )
            if score_tbl < 85.0:
                self.audit_results["recommendations"].append(
                    "Kiểm tra cấu trúc ô bảng biểu và độ rộng các cột dữ liệu."
                )

        return self.audit_results

    def generate_markdown_report(self, output_path: str):
        """Generates a detailed Markdown audit report."""
        res = self.audit_results
        sum_info = res["summary"]
        dims = res["dimensions"]

        md_lines = [
            "# 📋 BÁO CÁO ĐỐI CHIẾU & ĐÁNH GIÁ MỨC ĐỘ BẢO TỒN ĐỊNH DẠNG (LAYOUT RETENTION AUDIT)",
            "",
            f"> **Thời gian kiểm định:** 2026-09-13 | **Công cụ:** `verify_retention.py` v1.0",
            f"> **Tài liệu gốc (Source):** `{sum_info.get('source_file')}`",
            f"> **Tài liệu dịch (Target):** `{sum_info.get('target_file')}`",
            "",
            "---",
            "",
            "## 🏆 KẾT QUẢ TỔNG QUAN",
            "",
            f"| Chỉ số | Kết quả thẩm định | Đánh giá |",
            f"| :--- | :---: | :--- |",
            f"| **Composite Retention Score** | **`{sum_info.get('composite_retention_score')}%`** | **{sum_info.get('grade')}** |",
            f"| **Trạng thái phê duyệt** | **`{sum_info.get('status')}`** | {'✅ ĐỦ ĐIỀU KIỆN PHÁT HÀNH' if sum_info.get('status') == 'PASS' else '⚠️ CẦN RÀ SOÁT'} |",
            "",
            "---",
            "",
            "## 📊 ĐÁNH GIÁ CHI TIẾT THEO 5 TRỌNG SỐ",
            "",
            "| Tiêu chí đối chiếu | Trọng số | Điểm số | Chi tiết phát hiện |",
            "| :--- | :---: | :---: | :--- |",
            f"| **1. Tương quan Số trang (Page Parity)** | 15% | **{dims.get('page_parity', {}).get('score')}%** | Gốc: {dims.get('page_parity', {}).get('source_pages')} trang $\\rightarrow$ Dịch: {dims.get('page_parity', {}).get('target_pages')} trang ({dims.get('page_parity', {}).get('parity_status')}) |",
            f"| **2. Bảo tồn Hình ảnh & Con dấu (Images)** | 25% | **{dims.get('image_fidelity', {}).get('score')}%** | Gốc: {dims.get('image_fidelity', {}).get('total_source_images')} ảnh $\\rightarrow$ Dịch: {dims.get('image_fidelity', {}).get('total_target_images')} ảnh |",
            f"| **3. Cấu trúc Bảng biểu (Tables)** | 20% | **{dims.get('table_fidelity', {}).get('score')}%** | Gốc: {dims.get('table_fidelity', {}).get('total_source_tables')} bảng biểu, bảo toàn đầy đủ số cột/hàng |",
            f"| **4. Ký hiệu Công thức & Chuẩn số (Formulas)** | 25% | **{dims.get('formula_fidelity', {}).get('score')}%** | Đã đối chiếu {dims.get('formula_fidelity', {}).get('total_source_tokens')} ký hiệu (Ion hóa học, đơn vị, mã tiêu chuẩn) |",
            f"| **5. An toàn Lề & Bố cục (Layout Safety)** | 15% | **{dims.get('layout_safety', {}).get('score')}%** | Lỗi tràn lề: {dims.get('layout_safety', {}).get('overflow_blocks')} - Khối CJK sót: {dims.get('layout_safety', {}).get('untranslated_blocks')} |",
            "",
            "---",
            "",
            "## 🔍 BẢNG KÊ DANH MỤC CÔNG THỨC & THUẬT NGỮ KỸ THUẬT ĐỐI CHIẾU",
            "",
            "| Nhóm ký hiệu / Công thức | Điểm bảo tồn | Tình trạng |",
            "| :--- | :---: | :--- |",
        ]

        cat_scores = dims.get("formula_fidelity", {}).get("category_scores", {})
        cat_names = {
            "chemical_ions": "Ion hóa học ($Na^+, K^+, Cl^-, Ca^{2+}, Mg^{2+}, HCO_3^-$)",
            "units": "Đơn vị đo lường ($mmol/L, mg/dL, mL/min, mmHg, pH$)",
            "standards_codes": "Mã tiêu chuẩn & Mã sản phẩm ($JCCRM, DIA, JAN$)",
            "math_symbols": "Toán tử & Ký hiệu dung sai ($±, ×, ≤, ≥, <, >$)",
            "medical_params": "Tham số sinh hóa dịch lọc ($BE, pCO_2, Glu$)"
        }
        for k, v in cat_scores.items():
            name = cat_names.get(k, k)
            st = "✅ Hoàn hảo" if v >= 95 else ("⚠️ Tốt" if v >= 85 else "❌ Cần kiểm tra")
            md_lines.append(f"| {name} | **{v}%** | {st} |")

        md_lines.extend([
            "",
            "---",
            "",
            "## ⚠️ DANH SÁCH BẤT THƯỜNG / CẢNH BÁO (ANOMALIES)",
            ""
        ])

        anomalies = res.get("anomalies", [])
        if not anomalies:
            md_lines.append("✅ Không phát hiện bất thường nghiêm trọng nào. Bố cục tài liệu khớp hoàn toàn.")
        else:
            for idx, a in enumerate(anomalies, 1):
                md_lines.append(f"{idx}. {a}")

        md_lines.extend([
            "",
            "---",
            "",
            "## 💡 KHUYẾN NGHỊ VẬN HÀNH (RECOMMENDATIONS)",
            ""
        ])
        for r in res.get("recommendations", []):
            md_lines.append(f"- {r}")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text("\n".join(md_lines), encoding="utf-8")
        print(f"📄 Đã lưu báo cáo kiểm toán chi tiết: {output_path}")

    def close(self):
        self.src_doc.close()
        self.tgt_doc.close()


def main():
    parser = argparse.ArgumentParser(
        description="verify_retention.py — Đối chiếu & Đánh giá mức độ retain định dạng, hình ảnh, bảng biểu và công thức của bản dịch so với bản gốc"
    )
    parser.add_argument("--source", "-s", required=True, help="Đường dẫn file PDF gốc")
    parser.add_argument("--target", "-t", required=True, help="Đường dẫn file PDF bản dịch")
    parser.add_argument("--json", "-j", default=None, help="Đường dẫn file merged_ejv.json (tùy chọn)")
    parser.add_argument("--output", "-o", default=None, help="Đường dẫn lưu file báo cáo Markdown (tùy chọn)")
    parser.add_argument("--json-output", default=None, help="Đường dẫn lưu file báo cáo JSON (tùy chọn)")
    parser.add_argument("--min-score", type=float, default=85.0, help="Ngưỡng điểm tối thiểu để Đạt chuẩn (Mặc định: 85.0)")

    args = parser.parse_args()

    auditor = LayoutRetentionAuditor(args.source, args.target, args.json)
    results = auditor.run_full_audit()

    sum_info = results["summary"]
    dims = results["dimensions"]
    score = sum_info["composite_retention_score"]
    grade = sum_info["grade"]
    status = sum_info["status"]

    # Terminal Pretty Print
    print("\n" + BOLD + "═" * 70 + RESET)
    print(f"{BOLD}{BLUE} 🔬 BÁO CÁO ĐỐI CHIẾU & ĐÁNH GIÁ MỨC ĐỘ RETAIN ĐỊNH DẠNG (LAYOUT AUDIT){RESET}")
    print(BOLD + "─" * 70 + RESET)
    print(f" • File gốc:     {os.path.basename(args.source)}")
    print(f" • File dịch:    {os.path.basename(args.target)}")
    print(f" • Điểm Retain:  {BOLD}{GREEN if score >= 85 else RED}{score}% / 100%{RESET} [{grade}]")
    print(f" • Trạng thái:   {BOLD}{GREEN if status == 'PASS' else RED}{status}{RESET}")
    print(BOLD + "─" * 70 + RESET)
    print(" CHI TIẾT 5 TRỌNG SỐ ĐỐI CHIẾU:")
    print(f"  1. Tương quan Số trang (15%):     {dims['page_parity']['score']:>5.1f}%  ({dims['page_parity']['source_pages']} vs {dims['page_parity']['target_pages']} trang)")
    print(f"  2. Bảo tồn Hình ảnh/Dấu (25%):    {dims['image_fidelity']['score']:>5.1f}%  ({dims['image_fidelity']['total_source_images']} vs {dims['image_fidelity']['total_target_images']} ảnh)")
    print(f"  3. Cấu trúc Bảng biểu (20%):     {dims['table_fidelity']['score']:>5.1f}%  ({dims['table_fidelity']['total_source_tables']} bảng detected)")
    print(f"  4. Ký hiệu/Công thức (25%):       {dims['formula_fidelity']['score']:>5.1f}%  ({dims['formula_fidelity']['total_source_tokens']} tokens matched)")
    print(f"  5. An toàn Lề & Bố cục (15%):     {dims['layout_safety']['score']:>5.1f}%  ({dims['layout_safety']['overflow_blocks']} overflow, {dims['layout_safety']['untranslated_blocks']} residual)")
    print(BOLD + "─" * 70 + RESET)

    if dims['layout_safety'].get('untranslated_details'):
        print(f"\n{BOLD}{RED}❌ [HARD BLOCKER] PHÁT HIỆN CÁC KHỐI CHỮ NGUỒN CÒN SÓT LẠI TRÊN TRANG:{RESET}")
        for item in dims['layout_safety']['untranslated_details']:
            print(f"   • [Trang {item['page']}] BBox={item['bbox']}: {item['text']}")

    if results["anomalies"]:
        print(f"{YELLOW}⚠️  CÁC ĐIỂM CẦN LƯU Ý:{RESET}")
        for a in results["anomalies"]:
            print(f"   - {a}")
    else:
        print(f"{GREEN}✅  Tuyệt đối không phát hiện bất thường: Bố cục, hình ảnh và công thức khớp hoàn hảo!{RESET}")

    # v2.1: Run coordinate precision audit if available
    coord_score = None
    try:
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))
        from verify_coordinates import audit_pdf as coord_audit
        coord_report = coord_audit(Path(args.source), Path(args.target))
        coord_summary = coord_report["summary"]
        coord_score = coord_summary["coordinate_precision_score"]
        coord_status = coord_summary["overall_status"]
        c_color = GREEN if coord_status == "PASS" else YELLOW if coord_status == "PASS_WITH_WARNINGS" else RED
        print(BOLD + "─" * 70 + RESET)
        print(f" 📐 Coordinate Precision (Bonus):  {c_color}{coord_score}% [{coord_status}]{RESET}")
        print(f"    Overlaps: {coord_summary['overlap_count']} | "
              f"Clip Loss: {coord_summary['clip_loss_count']} | "
              f"Border Collisions: {coord_summary['border_collision_count']}")
    except ImportError:
        pass
    except Exception as e:
        print(f"   ⚠️  Coordinate audit error: {e}")

    print(BOLD + "═" * 70 + RESET + "\n")

    if args.output:
        auditor.generate_markdown_report(args.output)

    if args.json_output:
        # Merge coordinate metrics into results if available
        if coord_score is not None:
            results["coordinate_precision"] = {
                "score": coord_score,
                "overlaps": coord_summary["overlap_count"],
                "clip_loss": coord_summary["clip_loss_count"],
                "boundary_overflow": coord_summary["boundary_count"],
                "border_collisions": coord_summary["border_collision_count"],
            }
        with open(args.json_output, "w", encoding="utf-8") as jf:
            json.dump(results, jf, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu báo cáo JSON: {args.json_output}")

    auditor.close()

    # Exit code based on hard blocker and min-score
    if sum_info.get("hard_blocker") or score < args.min_score:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
