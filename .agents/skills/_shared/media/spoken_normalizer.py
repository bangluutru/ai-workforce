#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spoken_normalizer.py — Bộ chuẩn hóa văn bản phát thanh tiếng Việt dùng chung (Luật R7).

Mục tiêu:
  Chuyển đổi văn bản viết (sách, ebook, báo cáo, tài liệu) thành kịch bản đọc tự nhiên
  cho các mô hình Text-To-Speech (đặc biệt là VieNeu-TTS 48kHz và Kokoro).

Các quy tắc xử lý:
  1. Khử ký tự điều khiển, byte order mark (BOM), zero-width spaces (\u200b-\u200d, \ufeff).
  2. Khử dấu ngoặc kép (", “ ”, „) — chống lỗi VieNeu-TTS đọc thành "dấu ngoặc kép".
  3. Lược bỏ dòng số trang (vd: "Trang 12", "- 45 -", "12").
  4. Mở rộng từ viết tắt hành chính/xã hội (TP.HCM, PGS., GS., ThS., TS., v.v., vd.).
  5. Phát âm thuật ngữ viết tắt quốc tế (KPI -> ca pê i, CEO -> xi i ô, AI -> a i, 4P -> bốn Pê).
  6. Chuyển đổi số La Mã trong tiêu đề (Chương IV -> Chương bốn, Phần II -> Phần hai).
  7. Chuẩn hóa tỷ lệ phần trăm (%), phân số, khoảng số (2-3 -> 2 đến 3), tiền tệ (VNĐ, $).
  8. Chuyển đổi danh sách gạch đầu dòng và số thứ tự (1. -> Thứ nhất,, 2. -> Thứ hai,).
  9. Hỗ trợ từ điển phát âm tùy chỉnh (Custom Pronunciation Dictionary qua dict hoặc file TSV/JSON).

CLI:
  python3 spoken_normalizer.py --text "Chương IV: Quản lý KPI và OKR tại TP.HCM"
  python3 spoken_normalizer.py --input input.txt --output spoken.txt [--dict custom_dict.tsv]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 1. Ký tự điều khiển & rác unicode
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200B-\u200D\u2060\uFEFF]")

# Dòng chỉ chứa số trang
PAGE_NUM_RE = re.compile(r"(?i)^\s*(trang\s+)?[-–—]?\s*\d{1,4}\s*[-–—]?\s*$")

# Khử ngoặc kép mà giữ nội dung bên trong
QUOTE_TRANSLATION = str.maketrans({
    '"': "",
    '“': "",
    '”': "",
    '„': "",
    '«': "",
    '»': "",
})

# 2. Bảng mở rộng từ viết tắt tiếng Việt
ABBREVIATIONS: List[Tuple[str, str]] = [
    ("TP.HCM", "Thành phố Hồ Chí Minh"),
    ("TP. HCM", "Thành phố Hồ Chí Minh"),
    ("Tp.HCM", "Thành phố Hồ Chí Minh"),
    ("TPHCM", "Thành phố Hồ Chí Minh"),
    ("TP.", "Thành phố "),
    ("Tp.", "Thành phố "),
    ("PGS.TS.", "Phó giáo sư Tiến sĩ "),
    ("GS.TS.", "Giáo sư Tiến sĩ "),
    ("PGS.", "Phó giáo sư "),
    ("GS.", "Giáo sư "),
    ("ThS.", "Thạc sĩ "),
    ("TS.", "Tiến sĩ "),
    ("BS.", "Bác sĩ "),
    ("Thầy thuốc ưu tú", "Thầy thuốc ưu tú"),
    ("TTƯT", "Thầy thuốc ưu tú"),
    ("vd.", "ví dụ"),
    ("VD.", "ví dụ"),
    ("v.v.", "vân vân"),
    ("vv.", "vân vân"),
    ("tr.", "trang "),
    ("BHXH", "bảo hiểm xã hội"),
    ("BHYT", "bảo hiểm y tế"),
    ("BHTN", "bảo hiểm thất nghiệp"),
    ("TNHH", "trách nhiệm hữu hạn"),
    ("CP", "cổ phần"),
    ("UBND", "Ủy ban nhân dân"),
    ("HĐND", "Hội đồng nhân dân"),
    ("TW", "Trung ương"),
    ("TƯ", "Trung ương"),
    ("KCN", "Khu công nghiệp"),
    ("KCX", "Khu chế xuất"),
]

# 3. Bảng phát âm từ viết tắt tiếng Anh & Thuật ngữ quốc tế
ACRONYMS: List[Tuple[str, str]] = [
    (r"\bKPIs?\b", "ca pê i"),
    (r"\bOKRs?\b", "ô ca rờ"),
    (r"\bCEOs?\b", "xi i ô"),
    (r"\bCFOs?\b", "xi ép ô"),
    (r"\bCTOs?\b", "xi ti ô"),
    (r"\bCOOs?\b", "xi ô ô"),
    (r"\bCMOs?\b", "xi em ô"),
    (r"\bAIs?\b", "a i"),
    (r"\bIT\b", "ai ti"),
    (r"\bHR\b", "hát rờ"),
    (r"\bPR\b", "pê rờ"),
    (r"\bROI\b", "rờ ô i"),
    (r"\bB2B\b", "bi to bi"),
    (r"\bB2C\b", "bi to xi"),
    (r"\bGDP\b", "giê đê pê"),
    (r"\bP&L\b", "pê và en"),
    (r"\bSOPs?\b", "ét ô pê"),
    (r"\bMVP\b", "em vê pê"),
    (r"\bUI\b", "u i"),
    (r"\bUX\b", "u ích"),
    (r"\bQA\b", "kiu a"),
    (r"\bQC\b", "kiu xi"),
]

# 4. Số La Mã trong đề mục (1..30)
ROMAN_DICT = {
    "I": "một", "II": "hai", "III": "ba", "IV": "bốn", "V": "năm",
    "VI": "sáu", "VII": "bảy", "VIII": "tám", "IX": "chín", "X": "mười",
    "XI": "mười một", "XII": "mười hai", "XIII": "mười ba", "XIV": "mười bốn", "XV": "mười lăm",
    "XVI": "mười sáu", "XVII": "mười bảy", "XVIII": "mười tám", "XIX": "mười chín", "XX": "hai mươi",
    "XXI": "hai mươi mốt", "XXII": "hai mươi hai", "XXIII": "hai mươi ba", "XXIV": "hai mươi bốn", "XXV": "hai mươi lăm",
    "XXVI": "hai mươi sáu", "XXVII": "hai mươi bảy", "XXVIII": "hai mươi tám", "XXIX": "hai mươi chín", "XXX": "ba mươi"
}

# Khớp "Chương/Phần/Mục/Bài/Chapter/Tập <La Mã>"
ROMAN_HEADING_RE = re.compile(
    r"(?i)\b(Chương|Phần|Mục|Bài|Chapter|Tập|Quyển|Hồi|Tiết)\s+([IVXLCDM]+)([\s.,:;)\]!?]|$)"
)

# Mô hình Marketing 4P, 7P... (VieNeu hay nhầm 4p thành 4 phút)
MARKETING_P_RE = re.compile(r"(^|[^\w\d])(\d{1,2})Ps?([^\w]|$)")

# Thứ tự danh sách (1. 2. 3. -> Thứ nhất, Thứ hai...)
ORDINAL_WORDS = [
    "", "Thứ nhất", "Thứ hai", "Thứ ba", "Thứ tư", "Thứ năm",
    "Thứ sáu", "Thứ bảy", "Thứ tám", "Thứ chín", "Thứ mười",
    "Thứ mười một", "Thứ mười hai", "Thứ mười ba", "Thứ mười bốn", "Thứ mười lăm"
]


def _replace_roman_heading(match: re.Match) -> str:
    prefix = match.group(1)
    roman = match.group(2).upper()
    suffix = match.group(3)
    if roman in ROMAN_DICT:
        return f"{prefix} {ROMAN_DICT[roman]}{suffix}"
    return match.group(0)


def _replace_marketing_p(match: re.Match) -> str:
    lead = match.group(1)
    num = match.group(2)
    trail = match.group(3)
    return f"{lead}{num} Pê{trail}"


def _clean_page_numbers(text: str) -> str:
    lines = text.split("\n")
    kept = []
    for line in lines:
        if PAGE_NUM_RE.match(line):
            continue
        kept.append(line)
    return "\n".join(kept)


def _convert_list_markers(text: str) -> str:
    """Chuyển gạch đầu dòng và số thứ tự đầu đoạn thành văn xuôi phát thanh."""
    lines = text.split("\n")
    processed_lines = []
    current_counter = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            processed_lines.append(line)
            current_counter = 0
            continue

        # Bỏ bullet đơn: •, -, *, +
        if re.match(r"^[\s]*[•\-\*\+]\s+", line):
            cleaned = re.sub(r"^[\s]*[•\-\*\+]\s+", "", line)
            processed_lines.append(cleaned)
            continue

        # Đổi số thứ tự đầu mục "1.", "1)", "(1)" thành "Thứ nhất,", "Thứ hai,"
        m = re.match(r"^[\s]*(?:\(?(\d{1,2})[\.\)]|\b(\d{1,2})\.)\s+(.+)$", line)
        if m:
            num = int(m.group(1) or m.group(2))
            rest = m.group(3)
            if 1 <= num < len(ORDINAL_WORDS):
                current_counter = num
                ordinal = ORDINAL_WORDS[num]
                processed_lines.append(f"{ordinal}, {rest}")
                continue

        processed_lines.append(line)

    return "\n".join(processed_lines)


def _convert_symbols_and_numbers(text: str) -> str:
    """Chuẩn hóa ký hiệu số học, tỷ lệ, tiền tệ, dấu nối."""
    s = text

    # % -> phần trăm
    s = re.sub(r"(\d+)\s*%", r"\1 phần trăm", s)

    # Tiền tệ VNĐ / đ
    s = re.sub(r"(\d+[\d\.,]*)\s*(?:VNĐ|VND|đồng|đ)\b", r"\1 đồng", s, flags=re.IGNORECASE)

    # Đô la Mỹ $
    s = re.sub(r"\$(\d+[\d\.,]*)", r"\1 đô la", s)

    # Phân số thông dụng
    s = re.sub(r"\b1/2\b", "một nửa", s)
    s = re.sub(r"\b1/3\b", "một phần ba", s)
    s = re.sub(r"\b2/3\b", "hai phần ba", s)
    s = re.sub(r"\b1/4\b", "một phần tư", s)
    s = re.sub(r"\b3/4\b", "ba phần tư", s)

    # Khoảng số (2-3 -> 2 đến 3, 10 - 15 -> 10 đến 15)
    s = re.sub(r"(\d+)\s*[-–—]\s*(\d+)", r"\1 đến \2", s)

    # Dấu gạch chéo chọn lựa giữa chữ (nam/nữ -> nam hoặc nữ)
    s = re.sub(r"\b([a-zA-Zà-ỹÀ-Ỹ]+)/([a-zA-Zà-ỹÀ-Ỹ]+)\b", r"\1 hoặc \2", s)

    # Dấu & -> và
    s = re.sub(r"\s+&\s+", " và ", s)

    # Mũi tên -> dẫn tới
    s = re.sub(r"\s*(?:->|→|=>)\s*", " dẫn tới ", s)

    return s


def load_user_dictionary(dict_path: str | Path) -> Dict[str, str]:
    """Tải từ điển tùy chỉnh từ file TSV hoặc JSON."""
    p = Path(dict_path)
    if not p.exists():
        return {}
    res = {}
    if p.suffix.lower() == ".json":
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    else:  # Mặc định TSV (term \t pronunciation)
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                res[parts[0].strip()] = parts[1].strip()
    return res


def normalize_spoken_vietnamese(
    text: str,
    user_dict: Optional[Dict[str, str]] = None,
    keep_heading_numbers: bool = False,
) -> str:
    """
    Chuẩn hóa toàn diện văn bản sang kịch bản phát thanh tiếng Việt.

    Args:
        text: Chuỗi văn bản gốc cần xử lý
        user_dict: Từ điển bổ sung tùy chỉnh {từ_gốc: cách_đọc}
        keep_heading_numbers: Giữ số mục (1.2.3) hay lược bỏ để đọc thanh thoát

    Returns:
        Văn bản đã được chuẩn hóa để nạp vào TTS
    """
    if not text:
        return ""

    # 1. Khử ký tự điều khiển rác
    s = CONTROL_CHAR_RE.sub("", text)

    # 2. Khử dấu ngoặc kép (tránh đọc chữ "dấu ngoặc kép")
    s = s.translate(QUOTE_TRANSLATION)

    # 3. Lược bỏ dòng số trang
    s = _clean_page_numbers(s)

    # 4. Xử lý số La Mã trong tiêu đề chương/mục
    s = ROMAN_HEADING_RE.sub(_replace_roman_heading, s)

    # 5. Xử lý mô hình Marketing (4P, 7P)
    s = MARKETING_P_RE.sub(_replace_marketing_p, s)

    # 6. Chuyển đổi danh sách gạch đầu dòng & số thứ tự
    s = _convert_list_markers(s)

    # 7. Ký hiệu số học, tỷ lệ, tiền tệ, phân số
    s = _convert_symbols_and_numbers(s)

    # 8. Mở rộng từ viết tắt tiếng Việt
    for src, dst in ABBREVIATIONS:
        # Khớp chính xác cụm viết tắt
        s = s.replace(src, dst)

    # 9. Phát âm từ viết tắt quốc tế (ACRONYMS)
    for pattern, spoken in ACRONYMS:
        s = re.sub(pattern, spoken, s)

    # 10. Áp dụng từ điển người dùng (nếu có)
    if user_dict:
        # Sắp từ dài trước để tránh thế đè từ ngắn
        sorted_keys = sorted(user_dict.keys(), key=len, reverse=True)
        for k in sorted_keys:
            replacement = user_dict[k]
            pattern = rf"\b{re.escape(k)}\b"
            s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

    # 11. Bỏ số mục nhiều cấp nếu keep_heading_numbers = False (vd: "4.1.2. Tên bài" -> "Tên bài")
    if not keep_heading_numbers:
        s = re.sub(r"(?m)^\s*(?:\d+\.)+\d*\s+", "", s)

    # 12. Dọn dẹp khoảng trắng thừa nhưng bảo tồn cấu trúc đoạn văn (double newline)
    paragraphs = s.split("\n\n")
    cleaned_paras = []
    for para in paragraphs:
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in para.split("\n") if line.strip()]
        if lines:
            cleaned_paras.append("\n".join(lines))

    return "\n\n".join(cleaned_paras).strip()


def main():
    parser = argparse.ArgumentParser(description="Chuẩn hóa văn bản phát thanh tiếng Việt dùng cho sách nói & TTS (Luật R7).")
    parser.add_argument("--text", type=str, help="Văn bản trực tiếp cần chuẩn hóa")
    parser.add_argument("--input", "-i", type=str, help="Đường dẫn file văn bản đầu vào (.txt, .md)")
    parser.add_argument("--output", "-o", type=str, help="Đường dẫn file đầu ra")
    parser.add_argument("--dict", "-d", type=str, help="Đường dẫn file từ điển phát âm tùy chỉnh (.tsv, .json)")
    parser.add_argument("--keep-heading-numbers", action="store_true", help="Giữ nguyên số mục đầu dòng (vd: 1.2.3)")

    args = parser.parse_args()

    content = ""
    if args.text:
        content = args.text
    elif args.input:
        in_path = Path(args.input)
        if not in_path.exists():
            print(f"❌ Không tìm thấy file: {args.input}", file=sys.stderr)
            sys.exit(1)
        content = in_path.read_text(encoding="utf-8")
    else:
        # Đọc từ stdin nếu không có tham số
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            parser.print_help()
            sys.exit(0)

    user_dict = {}
    if args.dict:
        user_dict = load_user_dictionary(args.dict)

    result = normalize_spoken_vietnamese(
        content,
        user_dict=user_dict,
        keep_heading_numbers=args.keep_heading_numbers
    )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result, encoding="utf-8")
        print(f"✅ Đã xuất văn bản phát thanh chuẩn hóa ra: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
