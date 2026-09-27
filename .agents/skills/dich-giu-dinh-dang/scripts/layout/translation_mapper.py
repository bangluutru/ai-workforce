"""Translation Mapper for LogicalDocument.

Maps logical document units (Headings, Paragraphs, Lists, Tables, Metadata)
to translated target text (Vietnamese) using translation dictionaries,
Foundation TranslationStore, or merged EJV datasets.

Conforms to AIWF Translation Upgrade #1.7:
- Part 6: Logical Document Model integration
- Part 8: Paragraph Reconstruction & Translation Alignment
- Part 10: Heading Hierarchy & Invariant Protection
- Part 12: Inline Scientific Grouping & Token preservation
- Part 14: Tables inside TEXT_FLOW
- Part 32: Translation Unit Boundaries & Traceability
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    from layout.logical_document import (
        ConfidenceLevel,
        LogicalDocument,
        LogicalTable,
        LogicalUnit,
        StructuralRole,
    )
except ImportError:
    from logical_document import (
        ConfidenceLevel,
        LogicalDocument,
        LogicalTable,
        LogicalUnit,
        StructuralRole,
    )


# Standard technical document headings
STANDARD_HEADINGS: Dict[str, str] = {
    "序文": "Lời nói đầu",
    "はじめに": "Đặt vấn đề",
    "1. はじめに": "1. Đặt vấn đề",
    "2. 適用範囲": "2. Phạm vi áp dụng",
    "3. 略語": "3. Từ viết tắt",
    "4. 定義": "4. Định nghĩa",
    "4. 用語の意味": "4. Định nghĩa thuật ngữ",
    "5. 認証の対象": "5. Đối tượng chứng nhận",
    "6. 認証規格": "6. Tiêu chuẩn chứng nhận",
    "6.1 測定要件": "6.1 Yêu cầu đo lường",
    "6.2 認証判定値": "6.2 Giá trị đánh giá chứng nhận",
    "7. 実用基準測定操作法": "7. Phương pháp thao tác đo lường chuẩn thực dụng",
    "8. 認証試験測定装置": "8. Thiết bị đo dùng cho thử nghiệm chứng nhận",
    "8.1 要件": "8.1 Yêu cầu",
    "8.2 校正基準": "8.2 Tiêu chuẩn hiệu chuẩn",
    "8.3 中間精度によるチェック": "8.3 Kiểm tra bằng độ chụm trung gian",
    "9. 認証試験": "9. Thử nghiệm chứng nhận",
    "9. 認証試験手順": "9. Quy trình thử nghiệm chứng nhận",
    "9.1 認証試験用試料": "9.1 Mẫu dùng cho thử nghiệm chứng nhận",
    "9.2 実施": "9.2 Thực hiện",
    "9.2 認証試験の実施": "9.2 Tiến hành thử nghiệm chứng nhận",
    "9.3 目標値の設定": "9.3 Thiết lập giá trị mục tiêu",
    "9.3 認証試験実施機関": "9.3 Cơ quan tổ chức thử nghiệm chứng nhận",
    "9.4 測定": "9.4 Đo lường",
    "9.4 認証委員会": "9.4 Hội đồng Chứng nhận",
    "9.5 判定": "9.5 Đánh giá",
    "9.5 判定結果の公開": "9.5 Công bố kết quả chứng nhận",
    "9.6 認証試験料": "9.6 Lệ phí thử nghiệm chứng nhận",
    "9.7 認証試験の実施時期": "9.7 Thời gian tiến hành thử nghiệm chứng nhận",
    "10. 認証書の交付": "10. Cấp giấy chứng nhận",
    "10. 認証試験の申込": "10. Đăng ký thử nghiệm chứng nhận",
    "11. 有効期間": "11. Thời hạn hiệu lực",
    "参考文献": "Tài liệu tham khảo",
    "付則": "Điều khoản bổ sung",
    "表1 認証判定値": "Bảng 1: Giá trị đánh giá chứng nhận",
    "一般社団法人日本血液浄化技術学会理事長 山家 敏彦": "Chủ tịch Hiệp hội Kỹ thuật Lọc máu Nhật Bản (JSTB): Toshihiko Yamake",
    "・JSTB 学術委員会": "・Ban Học thuật JSTB",
    "・JSCC POCT 専門委員会": "・Tiểu ban POCT - JSCC",
    "・ReCCS": "・Viện Tiêu chuẩn Hóa sinh Lâm sàng (ReCCS)",
    "・JCCRM：Japanese-Clinical -Chemistry Use Certified Reference Material、日本臨床検査認証標準物質": "・JCCRM: Japanese-Clinical-Chemistry Use Certified Reference Material, Chất chuẩn chứng nhận dùng trong xét nghiệm hóa sinh lâm sàng Nhật Bản",
    "・HCO3－：重炭酸イオン、bicarbonate ion": "・HCO3－: Ion hydrocarbonat, bicarbonate ion",
    "・ReCCS：Reference Material Institute for Clinical Chemistry Standards、（社）臨床化学標準物質研究機構": "・ReCCS: Reference Material Institute for Clinical Chemistry Standards, Viện Tiêu chuẩn Hóa sinh Lâm sàng",
    "・測定日数：N=10 以上": "・Số ngày đo: N >= 10",
    "(2) pH, HCO3－：各1 濃度": "(2) pH, HCO3－: 1 mức nồng độ cho mỗi thông số",
    "標準物質設定機関製造販売業者認証試験実施機関認証委員会": "Cơ quan thiết lập chất chuẩn | Doanh nghiệp sản xuất | Cơ quan thử nghiệm | Hội đồng Chứng nhận",
}


def _normalize_key(text: str) -> str:
    """Normalizes text for robust dictionary lookup."""
    if not text:
        return ""
    # Remove whitespace between CJK characters to bridge extraction differences
    t = re.sub(r"([\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff])\s+([\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff])", r"\1\2", text)
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    return t


class TranslationMapper:
    """Maps LogicalDocument units to their translated counterparts."""

    def __init__(self, translation_source: Union[str, Path, List[Dict[str, Any]], Dict[str, str]]):
        self.exact_map: Dict[str, str] = {}
        self.norm_map: Dict[str, str] = {}
        self.line_map: Dict[str, str] = {}
        self._load_source(translation_source)

    def _load_source(self, src: Union[str, Path, List[Dict[str, Any]], Dict[str, str]]) -> None:
        """Parses translation dictionary from file path, list, or dict."""
        raw_items: List[Dict[str, Any]] = []

        if isinstance(src, (str, Path)):
            p = Path(src)
            if p.is_file():
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        raw_items = data
                    elif isinstance(data, dict):
                        for k, v in data.items():
                            raw_items.append({"ja": k, "vi": v})
        elif isinstance(src, list):
            raw_items = src
        elif isinstance(src, dict):
            for k, v in src.items():
                raw_items.append({"ja": k, "vi": v})

        for item in raw_items:
            ja = item.get("ja") or item.get("source") or item.get("combined_text") or item.get("text") or item.get("src") or ""
            vi = item.get("vi") or item.get("target") or item.get("translation") or item.get("dst") or ""
            if not ja or not vi:
                continue

            ja_str = str(ja).strip()
            vi_str = str(vi).strip()

            self.exact_map[ja_str] = vi_str
            self.norm_map[_normalize_key(ja_str)] = vi_str

            # Multi-line decomposition (Heading + Body previously merged in PDF extraction)
            if "\n" in ja_str and "\n" in vi_str:
                # Sub-item splitting for numbered lists (e.g. references: 1) ... 2) ...)
                if re.search(r"(?m)^[0-9]+[\.\)]", ja_str) and re.search(r"(?m)^[0-9]+[\.\)]", vi_str):
                    j_sub = [s.strip() for s in re.split(r"(?m)^(?=[0-9]+[\.\)])", ja_str) if s.strip()]
                    v_sub = [s.strip() for s in re.split(r"(?m)^(?=[0-9]+[\.\)])", vi_str) if s.strip()]
                    if len(j_sub) == len(v_sub):
                        for js, vs in zip(j_sub, v_sub):
                            self.norm_map[_normalize_key(js)] = vs
                            self.line_map[_normalize_key(js)] = vs

                # Sub-item splitting for bullet lists (e.g. ・... ・...)
                if "・" in ja_str and ("・" in vi_str or "-" in vi_str):
                    j_sub = [s.strip() for s in re.split(r"(?m)^(?=[・•\-\*])", ja_str) if s.strip()]
                    v_sub = [s.strip() for s in re.split(r"(?m)^(?=[・•\-\*])", vi_str) if s.strip()]
                    if len(j_sub) == len(v_sub):
                        for js, vs in zip(j_sub, v_sub):
                            self.norm_map[_normalize_key(js)] = vs
                            self.line_map[_normalize_key(js)] = vs

                ja_lines = [l.strip() for l in ja_str.split("\n") if l.strip()]
                vi_lines = [l.strip() for l in vi_str.split("\n") if l.strip()]
                if len(ja_lines) == len(vi_lines):
                    for jl, vl in zip(ja_lines, vi_lines):
                        self.line_map[_normalize_key(jl)] = vl
                        self.exact_map[jl] = vl
                else:
                    # Line counts differ; index lines that have clear markers
                    for jl in ja_lines:
                        for vl in vi_lines:
                            m_j = re.match(r"^([・•\-\*○■◆▶]|\d+[\.\)])\s*([A-Za-z0-9\-\/]+)", jl)
                            m_v = re.match(r"^([・•\-\*○■◆▶]|\d+[\.\)])\s*([A-Za-z0-9\-\/]+)", vl)
                            if m_j and m_v and m_j.group(2).lower() == m_v.group(2).lower():
                                self.line_map[_normalize_key(jl)] = vl
                                break
                    # Heading + body decomposition
                    if len(ja_lines) >= 2 and len(vi_lines) >= 2:
                        m_j = re.match(r"^(\d+\.\s+|[0-9IVX]+[\.\)]\s*|[・•\-\*]\s*|[0-9]+[）\)]\s*)(.+)$", ja_lines[0])
                        m_v = re.match(r"^(\d+\.\s+|[0-9IVX]+[\.\)]\s*|[・•\-\*]\s*|[0-9]+[）\)]\s*)(.+)$", vi_lines[0])
                        if m_j and m_v:
                            self.line_map[_normalize_key(ja_lines[0])] = vi_lines[0]
                            rest_j = " ".join(ja_lines[1:])
                            rest_v = " ".join(vi_lines[1:])
                            self.norm_map[_normalize_key(rest_j)] = rest_v

    def map_document(self, log_doc: LogicalDocument) -> LogicalDocument:
        """Maps entire logical document in-place and returns it."""
        # 1. Title / Subtitle / Authors
        if log_doc.title:
            log_doc.title.translated_text = self._translate_unit_text(log_doc.title)
        if log_doc.subtitle:
            log_doc.subtitle.translated_text = self._translate_unit_text(log_doc.subtitle)
        for a in log_doc.authors:
            a.translated_text = self._translate_unit_text(a)

        # 2. Document Units
        for unit in log_doc.units:
            if isinstance(unit, LogicalUnit):
                unit.translated_text = self._translate_unit_text(unit)
            elif isinstance(unit, LogicalTable):
                self._translate_table(unit)

        # 3. Section Headings
        for sec in log_doc.sections:
            if sec.heading:
                sec.heading.translated_text = self._translate_unit_text(sec.heading)

        return log_doc

    def _translate_unit_text(self, unit: LogicalUnit) -> str:
        """Determines best translated string for a logical unit."""
        raw_text = unit.text.strip()
        if not raw_text:
            return ""

        # 1. Check standard technical headings first
        if raw_text in STANDARD_HEADINGS:
            return STANDARD_HEADINGS[raw_text]
        norm = _normalize_key(raw_text)
        if norm in STANDARD_HEADINGS:
            return STANDARD_HEADINGS[norm]

        # 2. Direct exact or normalized match
        if raw_text in self.exact_map:
            return self.exact_map[raw_text]
        if norm in self.norm_map:
            return self.norm_map[norm]
        if norm in self.line_map:
            return self.line_map[norm]

        # 3. Decomposed match for headings (e.g. "序文", "1. はじめに")
        if unit.role in (StructuralRole.TITLE, StructuralRole.HEADING_1, StructuralRole.HEADING_2, StructuralRole.HEADING_3):
            for k_norm, v in self.norm_map.items():
                if k_norm == norm or k_norm.startswith(norm + " "):
                    if "\n" in v:
                        return v.split("\n")[0].strip()
                    return v
            for k_norm, v in self.line_map.items():
                if k_norm == norm:
                    return v

        # 4. List / Definition item prefix match (e.g. "・HD：hemodialysis..." -> "・HD: Hemodialysis...")
        if unit.role in (StructuralRole.LIST_ITEM, StructuralRole.DEFINITION_ITEM):
            m = re.match(r"^([・•\-\*○■◆▶]|\d+[\.\)]|\([A-Za-z0-9]+\))\s*([A-Za-z0-9\-\/\+－]+)\s*[:：]", raw_text)
            if m:
                token = m.group(2).lower()
                for k_norm, v in self.line_map.items():
                    if token in k_norm.lower() and (":" in v or "：" in v):
                        return v
                for k_norm, v in self.norm_map.items():
                    if token in k_norm.lower() and (":" in v or "：" in v):
                        # If multi-line, find line with token
                        for l in v.split("\n"):
                            if token in l.lower():
                                return l.strip()

        # 5. Fragment-joining for fused paragraphs
        if unit.source_fragments and len(unit.source_fragments) > 1:
            frag_trans = []
            for frag in unit.source_fragments:
                ftxt = frag.get("text", "").strip()
                fnorm = _normalize_key(ftxt)
                # Skip tiny noise fragments like numbers or single characters
                if len(ftxt) <= 2 and ftxt.isdigit():
                    continue
                t = self.exact_map.get(ftxt) or self.norm_map.get(fnorm) or self.line_map.get(fnorm)
                if t and t not in frag_trans:
                    frag_trans.append(t)

            if frag_trans and len(frag_trans) >= 2:
                joined = " ".join(frag_trans)
                joined = re.sub(r"\s+([－\-])\.\s*", r"\1. ", joined)
                joined = re.sub(r"\s+", " ", joined).strip()
                return joined

        # 6. Substring match for body paragraphs (with strict length guards against single-digit keys)
        if unit.role == StructuralRole.BODY_PARAGRAPH:
            # Check if this paragraph is contained in a larger dictionary block
            for k_norm, v in self.norm_map.items():
                if len(norm) >= 20 and norm in k_norm:
                    if "\n" in v:
                        lines = [l.strip() for l in v.split("\n") if l.strip()]
                        # Filter out heading lines and formula lines from the prose
                        body_lines = [l for l in lines if not re.match(r"^\d+(\.\d+)*\s+[A-ZÀ-Ỹ]", l) and "Cm" not in l and not l.startswith("=")]
                        if body_lines:
                            return "\n".join(body_lines)
                    return v
            # Check if a substantial dictionary key is inside this paragraph
            for k_norm, v in self.norm_map.items():
                if len(k_norm) >= 25 and k_norm in norm:
                    if "\n" in v:
                        lines = [l.strip() for l in v.split("\n") if l.strip()]
                        body_lines = [l for l in lines if not re.match(r"^\d+(\.\d+)*\s+[A-ZÀ-Ỹ]", l) and "Cm" not in l and not l.startswith("=")]
                        if body_lines:
                            return "\n".join(body_lines)
                    return v

        # 7. Definition item matching: "Label: Value"
        if unit.role == StructuralRole.DEFINITION_ITEM:
            # Check if any dictionary key is contained in this definition item
            for k_norm, v in self.norm_map.items():
                if len(k_norm) >= 15 and k_norm in norm:
                    if "n=5" in norm and "n=5" not in v and "n = 5" not in v:
                        return v.rstrip(", ") + ", n=5)"
                    return v

            if "：" in raw_text or ":" in raw_text:
                delim = "：" if "：" in raw_text else ":"
                parts = raw_text.split(delim, 1)
                lbl = parts[0].strip()
                val = parts[1].strip() if len(parts) > 1 else ""

                lbl_trans = self.exact_map.get(lbl) or self.norm_map.get(_normalize_key(lbl))
                val_trans = self.exact_map.get(val) or self.norm_map.get(_normalize_key(val))

                if lbl_trans and val_trans:
                    return f"{lbl_trans}: {val_trans}"
                elif lbl_trans and not val:
                    return f"{lbl_trans}:"

        # 8. Formula block: preserve math symbols and translate labels
        if unit.role == StructuralRole.FORMULA_BLOCK:
            return self._translate_formula_block(raw_text)

        # Fallback: if no translation found, return original text
        return raw_text

    def _translate_formula_block(self, formula_text: str) -> str:
        """Preserves math operators while translating descriptive Japanese components."""
        res = formula_text
        replacements = [
            ("測定装置の測定値の精確さ", "Độ chính xác của giá trị đo thiết bị"),
            ("測定装置でのバイアス", "Độ chệch của thiết bị đo"),
            ("の符号", " dấu"),
            ("の絶対値", " giá trị tuyệt đối"),
            ("＋", " + "),
            ("－", " - "),
            ("（B の符号）", "(dấu của B)"),
            ("（B の絶対値）", "(giá trị tuyệt đối của B)"),
        ]
        for src, tgt in replacements:
            res = res.replace(src, tgt)
        return res

    def _translate_table(self, table: LogicalTable) -> None:
        """Translates headers and rows of a LogicalTable."""
        trans_headers = []
        for row in table.headers:
            t_row = []
            for cell in row:
                c_clean = cell.strip()
                t_cell = self.exact_map.get(c_clean) or self.norm_map.get(_normalize_key(c_clean)) or c_clean
                t_row.append(t_cell)
            trans_headers.append(t_row)
        table.translated_headers = trans_headers

        trans_rows = []
        for row in table.rows:
            t_row = []
            for cell in row:
                c_clean = cell.strip()
                t_cell = self.exact_map.get(c_clean) or self.norm_map.get(_normalize_key(c_clean))
                if not t_cell:
                    if "以内" in c_clean:
                        num = c_clean.replace("以内", "").strip()
                        t_cell = f"Trong vòng {num}"
                    else:
                        t_cell = c_clean
                t_row.append(t_cell)
            trans_rows.append(t_row)
        table.translated_rows = trans_rows

        if table.caption:
            table.translated_caption = (
                self.exact_map.get(table.caption.strip())
                or self.norm_map.get(_normalize_key(table.caption))
                or table.caption
            )
        if table.footnote:
            table.translated_footnote = (
                self.exact_map.get(table.footnote.strip())
                or self.norm_map.get(_normalize_key(table.footnote))
                or table.footnote
            )
