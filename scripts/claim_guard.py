#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claim_guard.py — Preliminary Claim Linter (Bộ rà soát sơ bộ ngôn từ tiếp thị & over-claim)
Tuân thủ Luật R5: .agents/rules/R5-legal-claim-compliance.md
Căn cứ: Luật Quảng cáo 2012 (sửa đổi bởi Luật 75/2025/QH15, hiệu lực 01/01/2026), NĐ 181/2013/NĐ-CP,
NĐ 38/2021/NĐ-CP, NĐ 15/2018/NĐ-CP (TPBVSK), TT 06/2011/TT-BYT (mỹ phẩm).

QUAN TRỌNG:
Công cụ này là PRELIMINARY CLAIM LINTER (Bộ lọc từ khóa sơ bộ), KHÔNG PHẢI là Legal Correctness Verifier
(Bộ thẩm định tính đúng đắn pháp lý toàn diện) và không thay thế ý kiến tư vấn pháp lý chuyên môn.

Hồ sơ quét (--profile):
  general (mặc định): báo cáo, tư vấn, văn bản nghiệp vụ. Cụm cấm tuyệt đối -> FAIL;
                      từ so sánh nhất/duy nhất/số 1 thiếu nguồn -> REQUIRES_EVIDENCE (FAIL khi --strict).
  ads:                nội dung quảng cáo/tiếp thị (viet-bai, thiet-ke, landing page). Thêm họ từ "...nhất",
                      công dụng y tế, giảm cân, bảo chứng cơ quan y tế, Top 1...; từ so sánh thiếu nguồn = FAIL.

Không bị bắt lỗi:
  - Câu miễn trừ chính thức: "... không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh".
  - Cụm từ được NHẮC ĐẾN để cấm/tránh (trong ngoặc kép + có từ chỉ dẫn: "không dùng", "tránh", "cấm", "thay bằng"...),
    hoặc đứng sau phủ định trực tiếp ("không", "chưa", "không phải").
Nguồn hợp lệ cho từ so sánh (cùng dòng): "(Theo <đơn vị>, <năm>)", "Nguồn: <đơn vị> <năm>", chú thích [^n] có năm,
hoặc viện dẫn văn bản pháp luật (Điều 19 NĐ 253/2026/NĐ-CP ...). "Báo cáo nội bộ" KHÔNG phải nguồn độc lập.

Sử dụng:
    python3 scripts/claim_guard.py --input <file> [--profile general|ads] [--strict] [--json]
    python3 scripts/claim_guard.py <file>                  (tương thích cách gọi cũ)
Exit code: 0 = PASS (hoặc REQUIRES_EVIDENCE ở hồ sơ general không --strict); 1 = có vi phạm; 2 = lỗi chạy/không đọc được file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Màu sắc hiển thị Terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

W = r"[\wÀ-ỹ]"  # một ký tự chữ (kể cả tiếng Việt)

# ----------------------------------------------------------------------------- cụm cấm tuyệt đối (mọi hồ sơ)
CLAIM_RULES = [
    {
        "category": "KHẲNG ĐỊNH TUYỆT ĐỐI / SUPERLATIVES",
        "severity": "CAO (Vi phạm Luật Quảng cáo Đ.8 K.11)",
        "patterns": [
            (r"\ban toàn tuyệt đối\b", "Dịu nhẹ và lành tính / Được kiểm nghiệm dịu nhẹ"),
            (r"\btuyệt đối an toàn\b", "Lành tính cho làn da / An tâm khi sử dụng"),
            (r"\b100\s*%\s*(an toàn|tự nhiên|thiên nhiên|hữu cơ|organic|lành tính|hiệu quả|khỏi|sạch khuẩn)\b",
             "Bỏ '100%' hoặc dẫn kết quả kiểm nghiệm cụ thể (đơn vị, năm)"),
            (r"\b(hoàn toàn )?không (có |gây )?(bất kỳ )?tác dụng phụ\b", "Hạn chế tối đa nguy cơ kích ứng"),
            (r"\bkhông (gây )?kích ứng (với|cho) mọi (loại )?da\b", "Phù hợp cho cả làn da nhạy cảm (đã thử nghiệm ...)"),
            (r"\bvĩnh viễn\b", "Lâu dài / Bền màu theo chu trình chăm sóc"),
            (r"\btrọn đời\b", "Dài hạn / Bền bỉ"),
            (r"\bkhông bao giờ (mọc lại|tái phát|quay lại)\b", "Hạn chế xuất hiện trở lại"),
            (r"\bđỉnh cao nhất\b", "Nổi bật / Tiêu biểu"),
            (r"\bhoàn hảo nhất\b", "Tối ưu / Toàn diện"),
            (r"\btriệt để 100\s*%", "Hiệu quả rõ rệt (kèm dữ liệu thử nghiệm)"),
            (r"\bhiệu quả 100\s*%", "Hiệu quả đã được ghi nhận trong thử nghiệm (nêu nguồn)"),
        ],
    },
    {
        "category": "NHẦM LẪN DƯỢC PHẨM / ĐIỀU TRỊ Y TẾ (MỸ PHẨM & TPCN)",
        "severity": "CAO (TT 06/2011/TT-BYT Phụ lục 03-MP; NĐ 15/2018/NĐ-CP)",
        "patterns": [
            (r"\bđặc trị\b", "Hỗ trợ cải thiện / Chăm sóc chuyên sâu"),
            (r"\btrị dứt điểm\b", "Hỗ trợ che phủ / Cải thiện rõ rệt"),
            (r"\bchữa khỏi\b", "Hỗ trợ phục hồi / Chăm sóc"),
            (r"\btiêu diệt tận gốc\b", "Làm sạch sâu / Loại bỏ nhẹ nhàng"),
            (r"\bkhỏi hẳn\b", "Cải thiện tích cực"),
            (r"\bchữa lành\b", "Phục hồi / Nuôi dưỡng"),
            (r"\bthay thế (được )?thuốc\b", "Hỗ trợ chăm sóc sức khỏe"),
            (r"\btác dụng như thuốc\b", "Hỗ trợ chăm sóc sức khỏe"),
            (r"\btái tạo tế bào gốc\b", "Hỗ trợ tái tạo bề mặt da/tóc"),
            (r"\bthuốc (phủ bạc|nhuộm tóc|mọc tóc|trắng da)\b", "Dầu gội phủ màu / Sản phẩm phủ màu tóc bạc"),
        ],
    },
    {
        "category": "CAM KẾT TÀI CHÍNH & PHÁP LÝ PHI THỰC TẾ",
        "severity": "TRUNG BÌNH (Rủi ro tranh chấp & lừa dối khách hàng)",
        "patterns": [
            (r"\bcam kết (sinh lời|lợi nhuận|lãi|hoàn vốn)\b", "Mục tiêu tối ưu hóa tỷ suất sinh lời theo kịch bản thị trường"),
            (r"\blợi nhuận (cố định|đảm bảo|chắc chắn)\b", "Lợi nhuận kỳ vọng theo kịch bản (kèm rủi ro)"),
            (r"\b(chắc chắn|đảm bảo|bảo đảm) (có lãi|sinh lời|có lợi nhuận)\b", "Kỳ vọng tăng trưởng lợi nhuận"),
            (r"\bkhông có (bất kỳ )?rủi ro( nào)?\b", "Kiểm soát rủi ro ở mức tối thiểu"),
            (r"\bkhông rủi ro\b", "Kiểm soát rủi ro (nêu cơ chế cụ thể)"),
            (r"\bchắc chắn trúng thầu\b", "Tối đa hóa năng lực cạnh tranh hồ sơ thầu"),
            (r"\b(đảm bảo|chắc chắn|bảo đảm) thắng kiện\b", "Bảo vệ tối đa quyền lợi hợp pháp"),
        ],
    },
    {
        "category": "BẢO MẬT & CÔNG NGHỆ CỰC ĐOAN",
        "severity": "TRUNG BÌNH (Tuyên bố phi kỹ thuật)",
        "patterns": [
            (r"\bbảo mật (dữ liệu )?(tuyệt đối|100\s*%|hoàn toàn)", "Bảo mật dữ liệu nhiều lớp theo tiêu chuẩn (nêu chuẩn: ISO 27001...)"),
            (r"\bkhông thể (bị )?(hack|xâm phạm|tấn công|đánh cắp|bẻ khóa)\b", "Tăng cường khả năng chống chịu tấn công mạng"),
            (r"\bmiễn nhiễm (hoàn toàn|100\s*%)", "Tăng cường sức đề kháng trước mã độc"),
        ],
    },
]

# ----------------------------------------------------------------------------- thêm cho hồ sơ quảng cáo
ADS_RULES = [
    {
        "category": "CÔNG DỤNG Y TẾ / BỆNH LÝ TRONG QUẢNG CÁO",
        "severity": "CAO (mỹ phẩm/TPBVSK không được quảng cáo công dụng chữa bệnh; thuốc cần giấy xác nhận nội dung QC)",
        "patterns": [
            (r"\bđiều trị\b", "Bỏ; chỉ dùng cho thuốc/dịch vụ y tế đã có giấy xác nhận nội dung quảng cáo"),
            (r"\bchữa (trị|bệnh|dứt|tận gốc)\b", "Bỏ công dụng chữa bệnh"),
            (r"(?<!giá )(?<!quản )(?<!chính )(?<!cai )(?<!thống )(?<!điều )(?<!đặc )(?<!đề )\btrị (mụn|nám|thâm|tàn nhang|rụng tóc|hôi|ho|viêm|đau|gàu|nấm|sẹo|tiểu đường|mỡ|béo)",
             "Hỗ trợ cải thiện / giảm sự xuất hiện của ... (không dùng 'trị')"),
            (r"\bkhỏi (bệnh|hết|hoàn toàn)\b", "Bỏ khẳng định khỏi bệnh"),
            (r"\b(dứt điểm|tận gốc)\b", "Cải thiện rõ rệt (kèm dữ liệu)"),
            (r"\b(phòng|ngăn) (ngừa|chống) (bệnh|ung thư|đột quỵ|tiểu đường|tim mạch|covid)", "Bỏ công dụng phòng bệnh"),
            (r"\b(hạ|giảm) (đường huyết|huyết áp|mỡ máu|cholesterol)\b", "Bỏ (công dụng dược lý)"),
            (r"\bgiảm cân (cấp tốc|thần tốc|nhanh|siêu tốc)|\bgiảm \d+\s*kg\b|\bđánh tan mỡ\b", "Hỗ trợ kiểm soát cân nặng kết hợp chế độ ăn và vận động"),
            (r"\bkhông (có |gây )?(bất kỳ )?tác dụng phụ\b", "Bỏ; mọi sản phẩm đều có thể gây phản ứng ở một số người"),
            (r"\b(an toàn|phù hợp|dùng được) (cho|với) (mọi|tất cả)( mọi)? (người|loại da|lứa tuổi|đối tượng)\b",
             "Phù hợp với ... (nêu đối tượng đã thử nghiệm)"),
            (r"\bmọi (loại )?(da|làn da|cơ địa)\b", "Phù hợp với ... (nêu loại da đã thử nghiệm)"),
            (r"\bthuốc (giảm cân|bổ|tăng cân|tăng chiều cao)\b", "Không gọi TPBVSK là thuốc"),
        ],
    },
    {
        "category": "BẢO CHỨNG CƠ QUAN / CHUYÊN GIA Y TẾ",
        "severity": "CAO (cấm dùng danh nghĩa cơ quan nhà nước/tổ chức, cán bộ y tế để quảng cáo) [CẦN XÁC MINH điều khoản cụ thể]",
        "patterns": [
            (r"\b(bộ y tế|who|bác sĩ|dược sĩ|chuyên gia|viện|bệnh viện)[^.;\n]{0,25}(khuyên dùng|khuyến (nghị|cáo) (sử )?dùng|bảo chứng|tin dùng|chứng nhận hiệu quả)",
             "Bỏ bảo chứng; chỉ nêu giấy tờ pháp lý (số công bố, giấy xác nhận nội dung QC)"),
        ],
    },
    {
        "category": "KHẲNG ĐỊNH TUYỆT ĐỐI (QUẢNG CÁO)",
        "severity": "CAO (Luật Quảng cáo Đ.8)",
        "patterns": [
            (r"\btuyệt đối\b", "Bỏ 'tuyệt đối' hoặc nêu số liệu kiểm chứng"),
            (r"\b(cam kết|đảm bảo|bảo đảm) (hiệu quả|kết quả|khỏi|trắng|mọc)\b", "Kết quả có thể khác nhau tùy cơ địa (nêu dữ liệu thử nghiệm)"),
            (r"\bhiệu quả (ngay|tức thì) (lập tức|sau \d+)", "Có thể thấy thay đổi sau ... (theo thử nghiệm, nêu nguồn)"),
            (r"\b100\s*%\s*(khách hàng|người dùng) (hài lòng|thành công)", "Nêu tỷ lệ thật + nguồn khảo sát"),
        ],
    },
]

# Các cụm từ cần kiểm tra nguồn chứng minh (Substantiation Check)
CONDITIONAL_CLAIMS = [
    (r"(?<!định )(?<!nghị )(?<!tư )(?<!văn bản )(?<!phòng )(?<!tầng )(?<!nhà )(?<!lô )(?<!khoản )(?<!điểm )(?<!mục )(?<!bước )(?<!trang )(?<!bảng )(?<!hình )(?<!câu )\bsố (1|một)\b(?!\s*/)",
     "Cần kèm trích dẫn nguồn công bố hợp pháp (Theo số liệu của... giai đoạn...)"),
    (r"\bduy nhất\b", "Cần tài liệu chứng minh tính độc quyền hoặc duy nhất"),
    (r"\btốt nhất\b", "Cần có chứng nhận giải thưởng hoặc bình chọn của bên thứ ba độc lập"),
    (r"\bhàng đầu\b", "Cần có căn cứ đo lường thị phần hoặc đánh giá tổ chức uy tín"),
]
ADS_CONDITIONAL = [
    (r"\btop\s*(1|một|đầu)\b|\bno\.?\s*1\b|#1\b", "Cần nguồn xếp hạng độc lập (đơn vị, năm, tiêu chí)"),
    (r"\bdẫn đầu\b", "Cần số liệu thị phần (đơn vị, năm, phân khúc)"),
    (r"\bđộc quyền\b", "Cần văn bằng/giấy phép chứng minh"),
    (r"\b(đầu tiên|tiên phong) (tại|ở|trên) (việt nam|thị trường|thế giới|châu á)|\b(thương hiệu|sản phẩm|công ty|doanh nghiệp|đơn vị) (đầu tiên|tiên phong)\b",
     "Cần bằng chứng 'đầu tiên/tiên phong' (đơn vị xác nhận, năm)"),
    (r"\b(?!(ít|thống|hợp|đồng|duy|thứ|đệ|gần|sớm|muộn|chậm|mới|tốt)\s)" + W + r"+ nhất\b(?!\s*(định|quán|trí|là|thiết|thời|thể))",
     "Từ 'nhất' (Luật QC Đ.8 K.11): cần tài liệu hợp pháp chứng minh + ghi nguồn"),
]

# Câu miễn trừ CHÍNH THỨC (bắt buộc theo R5 §4 / NĐ 15/2018): không được tính là vi phạm
DISCLAIMER_ALLOW = [
    r"không phải là thuốc,?\s*(và\s*)?không có tác dụng thay thế thuốc chữa bệnh",
    r"không phải là thuốc",
    r"không thay thế (cho )?(ý kiến|chẩn đoán|tư vấn|chỉ định)( của)? (bác sĩ|chuyên gia|luật sư|chuyên môn)",
    r"đọc kỹ hướng dẫn sử dụng trước khi dùng",
]
INSTRUCTION_CUES = re.compile(
    r"(không (được )?dùng|tránh|cấm|thay (vì|bằng|thế cho cụm)|đừng|vi phạm|❌|sai:|trước:|before|không viết|loại bỏ|xóa|"
    r"cụm từ cấm|từ cấm|over-claim|không ghi)", re.I)
NEGATION_BEFORE = re.compile(r"(không|chưa|chẳng|không phải|không hề|không được)\s*$", re.I)
QUOTE_SPANS = re.compile(r"[\"“”«»'‘’][^\"“”«»'‘’\n]{1,120}[\"“”«»'‘’]|\*[^*\n]{1,120}\*")
CITATION_RE = re.compile(
    r"(\(\s*(theo|nguồn)\b[^)]{3,}?(19|20)\d{2}[^)]*\))"
    r"|((theo|nguồn\s*:)\s+[^.;\n]{3,100}?\b(19|20)\d{2})"
    r"|(\[\^\w+\])"
    r"|(\b(điều|khoản)\s+\d+)"
    r"|(\b(luật|nghị định|nđ|thông tư|tt|nghị quyết|nq|quyết định|qđ)\b[^.;\n]{0,25}\d+/\d{4})", re.I)
WEAK_SOURCE_RE = re.compile(r"nội bộ|tự công bố|tự khảo sát", re.I)
BINARY_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".zip", ".tar", ".gz", ".png", ".jpg", ".jpeg", ".mp4", ".mp3"}


def extract_text_safely(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Trích xuất text từ tệp an toàn. Không bao giờ đọc file nhị phân như text thô."""
    ext = file_path.suffix.lower()
    if ext in {".txt", ".md", ".json", ".html", ".htm", ".js", ".ts", ".jsx", ".tsx", ".csv", ".typ"}:
        try:
            return file_path.read_text(encoding="utf-8", errors="replace"), None
        except Exception as e:
            return None, f"Lỗi đọc text file: {e}"
    if ext == ".docx":
        try:
            import docx
            doc = docx.Document(str(file_path))
            full_text = [p.text for p in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        full_text.append(cell.text)
            return "\n".join(full_text), None
        except ImportError:
            return None, "File .docx yêu cầu thư viện 'python-docx'. Chạy: pip3 install python-docx"
        except Exception as e:
            return None, f"Lỗi bóc tách text từ file .docx: {e}"
    if ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(str(file_path))
            full_text = [page.get_text() for page in doc]
            doc.close()
            return "\n".join(full_text), None
        except ImportError:
            return None, "File .pdf yêu cầu thư viện 'pymupdf'. Chạy: pip3 install pymupdf"
        except Exception as e:
            return None, f"Lỗi bóc tách text từ file .pdf: {e}"
    if ext in BINARY_EXTENSIONS:
        return None, f"Định dạng nhị phân '{ext}' không được hỗ trợ đọc trực tiếp. Vui lòng trích xuất text trước khi rà soát."
    try:
        raw_bytes = file_path.read_bytes()
        if b"\x00" in raw_bytes[:1024]:
            return None, "File chứa ký tự nhị phân (binary content). Vui lòng cung cấp file văn bản thuần."
        return raw_bytes.decode("utf-8", errors="replace"), None
    except Exception as e:
        return None, f"Không thể đọc file: {e}"


def _mask_disclaimers(line_lower: str) -> str:
    for pat in DISCLAIMER_ALLOW:
        line_lower = re.sub(pat, lambda m: " " * len(m.group(0)), line_lower)
    return line_lower


def _is_mention_not_claim(line_lower: str, start: int, end: int) -> bool:
    """Cụm từ được nhắc tới để cấm/tránh, hoặc bị phủ định trực tiếp -> không phải tuyên bố."""
    if NEGATION_BEFORE.search(line_lower[max(0, start - 14):start]):
        return True
    if INSTRUCTION_CUES.search(line_lower):
        for q in QUOTE_SPANS.finditer(line_lower):
            if q.start() <= start and end <= q.end():
                return True
    return False


def _cited(line_lower: str, footnotes: Dict[str, str]) -> Tuple[bool, str]:
    m = CITATION_RE.search(line_lower)
    if not m:
        return False, ""
    src = m.group(0)
    fn = re.match(r"\[\^(\w+)\]", src)
    if fn:
        body = footnotes.get(fn.group(1), "")
        if not re.search(r"(19|20)\d{2}", body):
            return False, f"chú thích [^{fn.group(1)}] thiếu đơn vị/năm"
        src = body
    if WEAK_SOURCE_RE.search(src):
        return False, "nguồn nội bộ/tự công bố không phải bằng chứng độc lập"
    return True, src


def check_file(file_path, quiet=False, strict=False, profile="general"):
    p = Path(file_path)
    if not p.exists():
        if not quiet:
            print(f"{RED}Lỗi: File không tồn tại: {file_path}{RESET}")
        return {"status": "BLOCKED", "failures": [f"File không tồn tại: {file_path}"], "warnings": [],
                "artifacts": [], "violations_count": 0, "warnings_count": 0, "profile": profile}

    text, err = extract_text_safely(p)
    if err:
        if not quiet:
            print(f"{RED}❌ {err}{RESET}")
        return {"status": "BLOCKED", "failures": [err], "warnings": [], "artifacts": [str(p)],
                "violations_count": 0, "warnings_count": 0, "profile": profile}

    lines = text.split("\n")
    footnotes = {m.group(1): m.group(2).lower() for m in re.finditer(r"^\[\^(\w+)\]:\s*(.+)$", text, re.M)}
    rules = CLAIM_RULES + (ADS_RULES if profile == "ads" else [])
    conditional = CONDITIONAL_CLAIMS + (ADS_CONDITIONAL if profile == "ads" else [])
    violations: List[dict] = []
    warnings: List[dict] = []

    in_code = False
    for idx, line in enumerate(lines, 1):
        line_clean = line.strip()
        if line_clean.startswith("```"):
            in_code = not in_code
            continue
        if in_code or re.match(r"^\[\^\w+\]:", line_clean):
            continue
        line_lower = _mask_disclaimers(line_clean.lower())
        seen_spans: List[Tuple[int, int]] = []

        for cat in rules:
            for pattern, suggestion in cat["patterns"]:
                for match in re.finditer(pattern, line_lower):
                    if _is_mention_not_claim(line_lower, match.start(), match.end()):
                        continue
                    if any(a <= match.start() < b for a, b in seen_spans):
                        continue
                    seen_spans.append((match.start(), match.end()))
                    violations.append({"line": idx, "matched": match.group(0), "snippet": line_clean[:120],
                                       "category": cat["category"], "severity": cat["severity"],
                                       "suggestion": suggestion})

        for pattern, note in conditional:
            for match in re.finditer(pattern, line_lower):
                if _is_mention_not_claim(line_lower, match.start(), match.end()):
                    continue
                if any(a <= match.start() < b for a, b in seen_spans):
                    continue
                seen_spans.append((match.start(), match.end()))
                ok, why = _cited(line_lower, footnotes)
                if ok:
                    continue
                item = {"line": idx, "matched": match.group(0), "snippet": line_clean[:120],
                        "note": note + (f" ({why})" if why else "")}
                if profile == "ads":
                    violations.append({**item, "category": "TỪ SO SÁNH/NHẤT THIẾU NGUỒN (QUẢNG CÁO)",
                                       "severity": "CAO (Luật Quảng cáo Đ.8 K.11)",
                                       "suggestion": "Thêm '(Theo <đơn vị độc lập>, <năm>)' cùng dòng hoặc bỏ từ so sánh"})
                else:
                    warnings.append(item)

    if violations:
        status = "FAIL"
    elif warnings:
        status = "FAIL" if strict else "REQUIRES_EVIDENCE"
    else:
        status = "PASS"

    if not quiet:
        print(f"\n{BOLD}=== PRELIMINARY CLAIM LINTER (RULE R5, hồ sơ: {profile}): {p.name} ==={RESET}")
        print(f"{BLUE}ℹ️  Lưu ý: Đây là bộ lọc từ khóa sơ bộ, không xác nhận tính đúng đắn pháp lý toàn diện.{RESET}\n")
        if violations:
            print(f"{RED}{BOLD}❌ PHÁT HIỆN {len(violations)} VI PHẠM OVER-CLAIM (LUẬT R5):{RESET}")
            for v in violations:
                print(f"  {RED}• Dòng {v['line']}:{RESET} Phát hiện cụm từ cấm {YELLOW}'{v['matched']}'{RESET}")
                print(f"    - Phân loại: {v['category']} [{v['severity']}]")
                print(f"    - Trích đoạn: \"{v['snippet']}\"")
                print(f"    - {GREEN}Gợi ý thay thế hợp chuẩn:{RESET} \"{v['suggestion']}\"")
                print()
        if warnings:
            print(f"{YELLOW}{BOLD}⚠️ CẢNH BÁO {len(warnings)} TUYÊN BỐ CẦN MINH CHỨNG (REQUIRES EVIDENCE):{RESET}")
            for w in warnings:
                print(f"  {YELLOW}• Dòng {w['line']}:{RESET} Sử dụng từ so sánh '{w['matched']}' nhưng thiếu ghi chú nguồn:")
                print(f"    - Yêu cầu: {w['note']}")
                print(f"    - Trích đoạn: \"{w['snippet']}\"")
                print()
        if status == "PASS":
            print(f"{GREEN}✅ LINTER_PASS: Không phát hiện từ khóa cấm trong từ điển linter.{RESET}")
            print(f"{GREEN}   (Lưu ý: Không thay thế thẩm định pháp lý nội dung chuyên sâu).{RESET}\n")
        elif status == "REQUIRES_EVIDENCE":
            print(f"{YELLOW}⚠️  LINTER_REQUIRES_EVIDENCE: Không có từ cấm, nhưng có tuyên bố cần bằng chứng nguồn.{RESET}\n")

    return {
        "status": status,
        "profile": profile,
        "violations_count": len(violations),
        "warnings_count": len(warnings),
        "failures": [f"Dòng {v['line']}: {v['matched']} ({v['category']})" for v in violations],
        "warnings": [f"Dòng {w['line']}: {w['matched']} ({w['note']})" for w in warnings],
        "violations": violations,
        "artifacts": [str(p)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Preliminary Claim Linter (Rule R5)")
    parser.add_argument("input_pos", nargs="?", help="Đường dẫn file cần kiểm tra (tương thích cách gọi cũ)")
    parser.add_argument("--input", "-i", help="Đường dẫn file cần kiểm tra")
    parser.add_argument("--quiet", "-q", action="store_true", help="Chỉ in kết quả ngắn gọn")
    parser.add_argument("--strict", action="store_true", help="Bắt buộc fail cả khi có cảnh báo cần minh chứng")
    parser.add_argument("--profile", choices=["general", "ads"], default="general",
                        help="general (báo cáo/tư vấn) | ads (nội dung quảng cáo, nghiêm ngặt hơn)")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả JSON")
    args = parser.parse_args()
    path = args.input or args.input_pos
    if not path:
        parser.print_usage(sys.stderr)
        print("Lỗi: thiếu file cần kiểm tra (--input <file>)", file=sys.stderr)
        return 2

    result = check_file(path, args.quiet, args.strict, args.profile)
    if args.json:
        print(json.dumps({k: v for k, v in result.items() if k != "violations"}, ensure_ascii=False, indent=2))

    if result["status"] == "FAIL":
        return 1
    if result["status"] == "BLOCKED":
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # crash != vi phạm: trả mã 2 để Agent không hiểu nhầm là "có từ cấm"
        print(f"[CRASH] claim_guard.py lỗi nội bộ: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(2)
