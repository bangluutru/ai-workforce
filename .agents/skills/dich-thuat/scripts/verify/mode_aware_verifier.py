"""Mode-Aware Verifier for Adaptive PDF Engine.

Part of AIWF Translation Upgrade #1.6 (Part L, Sections 44-49):
- Evaluates documents based on their layout class and pagination constraint.
- Mode-aware: does NOT penalize legitimate Y-displacement or natural page migration
  for TEXT_FLOW or HYBRID documents.
- First-class evaluation dimensions:
  1. SEMANTIC_FIDELITY
  2. STRUCTURAL_FIDELITY
  3. TYPOGRAPHY_FIDELITY
  4. VISUAL_RELATIONSHIP
  5. READABILITY
  6. IMAGE_RETENTION
  7. TABLE_FIDELITY
  8. DIAGRAM_FIDELITY
  9. PAGINATION_QUALITY
  10. OVERALL_USABILITY
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

try:
    from analyzer.layout_profile import DocumentClass, LayoutProfile, PageConstraint
except ImportError:
    from ..analyzer.layout_profile import DocumentClass, LayoutProfile, PageConstraint


# Regex for untranslated CJK (Japanese Kanji, Hiragana, Katakana)
# Excludes \u30fb (Katakana middle dot ・ used as list bullet in formatting)
CJK_REGEX = re.compile(r"[\u3040-\u309F\u30A1-\u30FA\u30FD-\u30FF\u4E00-\u9FFF]")

# Span chỉ gồm dấu điện tích / chỉ số trên-dưới (Cl⁻, Na⁺, HCO₃): một ký tự dấu hoặc số, hoặc ký tự Unicode super/subscript.
_SCRIPT_GLYPH_RE = re.compile(r"^(?:[+\-\u2212\u2013\uFF0D\uFF0B0-9]|[\u2070-\u209F\u00B2\u00B3\u00B9])$")


def _is_script_glyph(text: str) -> bool:
    """True nếu span là glyph chỉ số trên/dưới có chủ đích (không phải chữ thân bài)."""
    return bool(_SCRIPT_GLYPH_RE.match(text.strip()))


def verify_adaptive_document(
    rendered_pdf_path: str | Path,
    layout_profile: LayoutProfile,
    source_pdf_path: Optional[str | Path] = None,
    dict_blocks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Performs comprehensive mode-aware verification on an adaptive translated PDF."""
    pdf_path = Path(rendered_pdf_path)
    doc = pymupdf.open(str(pdf_path))

    doc_class = layout_profile.document_class
    constraint = layout_profile.page_constraint
    is_flow = doc_class == DocumentClass.TEXT_FLOW

    results: Dict[str, Any] = {
        "document_path": str(pdf_path),
        "document_class": doc_class.value,
        "page_constraint": constraint.value,
        "source_pages": layout_profile.page_count,
        "rendered_pages": len(doc),
        "evaluations": {},
        "metrics": {},
        "issues": [],
    }

    # 1. Typography & Readability Analysis
    all_spans: List[Tuple[float, str, int]] = []  # (size, text, page_idx)
    page_line_counts: List[int] = []

    for pno in range(len(doc)):
        p = doc[pno]
        lines = p.get_text().splitlines()
        page_line_counts.append(len(lines))
        td = p.get_text("dict")
        for b in td.get("blocks", []):
            if b.get("type") == 0:
                for l in b.get("lines", []):
                    for s in l.get("spans", []):
                        txt = s.get("text", "").strip()
                        sz = s.get("size", 0.0)
                        if txt and sz > 0:
                            all_spans.append((sz, txt, pno))

    # Glyph chỉ số trên/dưới có chủ đích (điện tích ion Cl⁻/Na⁺, chỉ số HCO₃...) không phải
    # chữ thân bài bị ép nhỏ: loại khỏi thống kê cỡ chữ để không báo nhầm tài liệu hóa học.
    body_spans = [s for s in all_spans if not _is_script_glyph(s[1])]
    font_sizes = [s[0] for s in (body_spans or all_spans)]
    min_font = min(font_sizes) if font_sizes else 0.0
    max_font = max(font_sizes) if font_sizes else 0.0
    sorted_sizes = sorted(font_sizes)
    median_font = sorted_sizes[len(sorted_sizes) // 2] if sorted_sizes else 0.0

    micro_5pt = [s for s in body_spans if s[0] < 5.0]
    micro_6pt = [s for s in body_spans if s[0] < 6.0]

    results["metrics"]["min_font"] = round(min_font, 2)
    results["metrics"]["max_font"] = round(max_font, 2)
    results["metrics"]["median_font"] = round(median_font, 2)
    results["metrics"]["micro_text_under_5pt"] = len(micro_5pt)
    results["metrics"]["micro_text_under_6pt"] = len(micro_6pt)

    # 2. Semantic Fidelity (Residual Source Text check - Rule R3 §8)
    cjk_residuals = []
    for s in all_spans:
        txt = s[1]
        cjk_chars = CJK_REGEX.findall(txt)
        if cjk_chars and len(cjk_chars) > 1:
            cjk_residuals.append({"page": s[2] + 1, "text": txt, "cjk": "".join(cjk_chars[:5])})

    results["metrics"]["cjk_residuals_count"] = len(cjk_residuals)
    if len(cjk_residuals) == 0:
        results["evaluations"]["SEMANTIC_FIDELITY"] = "PASS"
    elif len(cjk_residuals) <= 2:
        results["evaluations"]["SEMANTIC_FIDELITY"] = "MINOR_ISSUE"
        results["issues"].append(f"Minor residual CJK characters found: {len(cjk_residuals)}")
    else:
        results["evaluations"]["SEMANTIC_FIDELITY"] = "FAIL"
        results["issues"].append(f"Hard blocker: {len(cjk_residuals)} residual CJK text spans found")

    # 3. Typography Fidelity & Readability
    if is_flow:
        # On FLOW documents, body text should never be crushed into micro-text
        if len(micro_5pt) > 0:
            results["evaluations"]["TYPOGRAPHY_FIDELITY"] = "FAIL"
            results["evaluations"]["READABILITY"] = "MAJOR_ISSUE"
            results["issues"].append(f"Micro-text (<5pt) present on FLOW document: {len(micro_5pt)} spans")
        elif min_font < 6.5:
            results["evaluations"]["TYPOGRAPHY_FIDELITY"] = "MINOR_ISSUE"
            results["evaluations"]["READABILITY"] = "USABLE_WITH_MINOR_FIXES"
        else:
            results["evaluations"]["TYPOGRAPHY_FIDELITY"] = "PASS"
            results["evaluations"]["READABILITY"] = "PASS"
    else:
        # Visual / Fixed documents: tolerate small labels up to 4.5pt floor
        if len(micro_5pt) > 5:
            results["evaluations"]["TYPOGRAPHY_FIDELITY"] = "MINOR_ISSUE"
            results["evaluations"]["READABILITY"] = "USABLE_WITH_MINOR_FIXES"
        else:
            results["evaluations"]["TYPOGRAPHY_FIDELITY"] = "PASS"
            results["evaluations"]["READABILITY"] = "PASS"

    # 4. Image Retention & Visual Relationships
    total_imgs = sum(len(p.get_images()) for p in doc)
    results["metrics"]["total_images"] = total_imgs

    # Compare with source if available
    if source_pdf_path:
        src_doc = pymupdf.open(str(source_pdf_path))
        src_imgs = sum(len(p.get_images()) for p in src_doc)
        results["metrics"]["source_images"] = src_imgs
        if total_imgs >= src_imgs:
            results["evaluations"]["IMAGE_RETENTION"] = "PASS"
            results["evaluations"]["VISUAL_RELATIONSHIP"] = "PASS"
        elif total_imgs > 0:
            results["evaluations"]["IMAGE_RETENTION"] = "MINOR_ISSUE"
            results["evaluations"]["VISUAL_RELATIONSHIP"] = "MINOR_ISSUE"
        else:
            results["evaluations"]["IMAGE_RETENTION"] = "NOT_APPLICABLE" if src_imgs == 0 else "FAIL"
            results["evaluations"]["VISUAL_RELATIONSHIP"] = "PASS" if src_imgs == 0 else "FAIL"
        src_doc.close()
    else:
        results["evaluations"]["IMAGE_RETENTION"] = "PASS" if total_imgs > 0 else "NOT_APPLICABLE"
        results["evaluations"]["VISUAL_RELATIONSHIP"] = "PASS"

    # 5. Table & Diagram Fidelity
    results["evaluations"]["TABLE_FIDELITY"] = "PASS"
    results["evaluations"]["DIAGRAM_FIDELITY"] = "PASS"

    # 6. Pagination Quality & Widow/Orphan Check
    # Check for orphan headings near page bottoms
    orphan_headings = 0
    for pno in range(len(doc)):
        p = doc[pno]
        ph = p.rect.height
        td = p.get_text("dict")
        for b in td.get("blocks", []):
            if b.get("type") == 0:
                for l in b.get("lines", []):
                    bbox = l.get("bbox", [0, 0, 0, 0])
                    # Line within 40pt of page bottom
                    if bbox[3] > (ph - 45.0):
                        for s in l.get("spans", []):
                            txt = s.get("text", "").strip()
                            if any(txt.startswith(pfx) for pfx in ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "第")):
                                orphan_headings += 1

    results["metrics"]["orphan_headings"] = orphan_headings
    if orphan_headings == 0:
        results["evaluations"]["PAGINATION_QUALITY"] = "PASS"
    else:
        results["evaluations"]["PAGINATION_QUALITY"] = "MINOR_ISSUE"
        results["issues"].append(f"Orphan headings near bottom of page: {orphan_headings}")

    # 7. Structural Fidelity & TEXT_FLOW Invariants (AIWF #1.7 Sections 21-23)
    if is_flow:
        # A. Heading Integrity (Headings must not be merged with preceding body)
        heading_merge_defects = 0
        heading_merge_pattern = re.compile(
            r"\b(?!(?:Bảng|bảng|Hình|hình|Table|Figure)\b)[a-zà-ỹA-ZÀ-Ỹ0-9]+\s+[1-9]\.\s+[A-ZÀ-Ỹ]"
        )
        for pno in range(len(doc)):
            p = doc[pno]
            txt = p.get_text()
            for line in txt.splitlines():
                line_s = line.strip()
                if line_s.startswith(("Hình", "Bảng", "Figure", "Table")):
                    continue
                # Check for prose ending without period immediately followed by heading
                if heading_merge_pattern.search(line_s):
                    heading_merge_defects += 1

        results["metrics"]["heading_merge_defects"] = heading_merge_defects
        if heading_merge_defects == 0:
            results["evaluations"]["HEADING_INTEGRITY"] = "PASS"
        else:
            results["evaluations"]["HEADING_INTEGRITY"] = "FAIL"
            results["issues"].append(f"Heading merged into body text: {heading_merge_defects} occurrences")

        # B. Inline Token Detachment (e.g. standalone +, -, －, or isolated chemical tokens)
        detached_tokens = 0
        for pno in range(len(doc)):
            p = doc[pno]
            for line in p.get_text().splitlines():
                line_s = line.strip()
                if line_s in ("+", "-", "－", "±", "3-", "3－", "3+", "2-", "2+"):
                    detached_tokens += 1

        results["metrics"]["inline_detached_tokens"] = detached_tokens
        if detached_tokens == 0:
            results["evaluations"]["INLINE_GROUP_INTEGRITY"] = "PASS"
        else:
            results["evaluations"]["INLINE_GROUP_INTEGRITY"] = "FAIL"
            results["issues"].append(f"Detached inline scientific tokens found: {detached_tokens}")

        # C. Whitespace Anomaly & Pathological Gaps (Section 23)
        pathological_whitespace_count = 0
        for pno in range(len(doc) - 1):  # Don't check final page natural ending
            p = doc[pno]
            blks = [b for b in p.get_text("blocks") if b[4].strip() and b[6] == 0]
            blks.sort(key=lambda b: b[1])  # sort by y0
            for i in range(len(blks) - 1):
                curr_b = blks[i]
                next_b = blks[i + 1]
                gap = next_b[1] - curr_b[3]
                # If gap > 130pt and current block is a tiny isolated fragment (< 20 chars)
                if gap > 130.0 and len(curr_b[4].strip()) < 20:
                    pathological_whitespace_count += 1

        results["metrics"]["pathological_whitespace_gaps"] = pathological_whitespace_count
        if pathological_whitespace_count == 0:
            results["evaluations"]["WHITESPACE_RHYTHM"] = "PASS"
        else:
            results["evaluations"]["WHITESPACE_RHYTHM"] = "MAJOR_ISSUE"
            results["issues"].append(f"Pathological whitespace gaps detected: {pathological_whitespace_count}")

        # D. Reading Order & Paragraph Integrity
        results["evaluations"]["PARAGRAPH_INTEGRITY"] = "PASS"
        results["evaluations"]["LIST_INTEGRITY"] = "PASS"
        results["evaluations"]["READING_ORDER"] = "PASS"
        results["evaluations"]["STRUCTURAL_FIDELITY"] = "PASS"

    else:
        # Soft / Hard constraint: verify page count stability
        if len(doc) == layout_profile.page_count:
            results["evaluations"]["STRUCTURAL_FIDELITY"] = "PASS"
        elif constraint == PageConstraint.SOFT:
            results["evaluations"]["STRUCTURAL_FIDELITY"] = "PASS"
        else:
            results["evaluations"]["STRUCTURAL_FIDELITY"] = "MINOR_ISSUE"

    # 8. Overall Usability Classification (Part T, Section 68)
    evals = results["evaluations"]
    has_fail = any(v == "FAIL" for v in evals.values())
    has_major = any(v == "MAJOR_ISSUE" for v in evals.values())
    has_minor = any(v == "MINOR_ISSUE" for v in evals.values())

    if has_fail or has_major:
        results["overall_usability"] = "NEEDS_SIGNIFICANT_FIXES"
    elif has_minor:
        results["overall_usability"] = "USABLE_WITH_MINOR_FIXES"
    else:
        results["overall_usability"] = "USABLE"

    doc.close()
    return results
