#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claim_guard.py — Bộ lọc & Thẩm định tính pháp lý nội dung (Anti-Overclaim Linter)
Tuân thủ Luật R5: .agents/rules/R5-legal-claim-compliance.md
Căn cứ: Luật Quảng cáo 2012, NĐ 181/2013/NĐ-CP, NĐ 38/2021/NĐ-CP, TT 06/2011/TT-BYT.

Sử dụng:
    python3 scripts/claim_guard.py --input <đường_dẫn_file>
"""

import sys
import os
import re
import argparse
from pathlib import Path

# Màu sắc hiển thị Terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Danh mục các mẫu cụm từ vi phạm pháp lý over-claim
CLAIM_RULES = [
    {
        "category": "KHẲNG ĐỊNH TUYỆT ĐỐI / SUPERLATIVES",
        "severity": "CAO (Vi phạm Luật Quảng cáo Đ.8 K.11)",
        "patterns": [
            (r"\ban toàn tuyệt đối\b", "Dịu nhẹ và lành tính / Được kiểm nghiệm dịu nhẹ"),
            (r"\btuyệt đối an toàn\b", "Lành tính cho làn da / An tâm khi sử dụng"),
            (r"\b100%\s*an toàn\b", "Được chứng minh dịu nhẹ"),
            (r"\bhoàn toàn không có tác dụng phụ\b", "Hạn chế tối đa nguy cơ kích ứng"),
            (r"\bkhông (gây )?kích ứng với mọi loại da\b", "Phù hợp cho cả làn da nhạy cảm"),
            (r"\bvĩnh viễn\b", "Lâu dài / Bền màu theo chu trình chăm sóc"),
            (r"\btrọn đời\b", "Dài hạn / Bền bỉ"),
            (r"\bkhông bao giờ (mọc lại|tái phát)\b", "Hạn chế xuất hiện trở lại"),
            (r"\bđỉnh cao nhất\b", "Nổi bật / Tiêu biểu"),
            (r"\bhoàn hảo nhất\b", "Tối ưu / Toàn diện"),
        ]
    },
    {
        "category": "NHẦM LẪN DƯỢC PHẨM / ĐIỀU TRỊ Y TẾ (MỸ PHẨM & TPCN)",
        "severity": "CAO (Vi phạm TT 06/2011/TT-BYT Phụ lục 03-MP)",
        "patterns": [
            (r"\bđặc trị\b", "Hỗ trợ cải thiện / Chăm sóc chuyên sâu"),
            (r"\btrị dứt điểm\b", "Hỗ trợ che phủ / Cải thiện rõ rệt"),
            (r"\bchữa khỏi\b", "Hỗ trợ phục hồi / Chăm sóc"),
            (r"\btiêu diệt tận gốc\b", "Làm sạch sâu / Loại bỏ nhẹ nhàng"),
            (r"\bkhỏi hẳn\b", "Cải thiện tích cực"),
            (r"\bchữa lành\b", "Phục hồi / Nuôi dưỡng"),
            (r"\bthay thế thuốc\b", "Hỗ trợ chăm sóc sức khỏe"),
            (r"\btái tạo tế bào gốc\b", "Hỗ trợ tái tạo bề mặt da/tóc"),
            (r"\bthuốc phủ bạc\b", "Dầu gội phủ màu / Sản phẩm phủ màu tóc bạc"),
            (r"\bthuốc nhuộm tóc bạc\b", "Dầu gội / Kem ủ phủ màu tóc bạc"),
        ]
    },
    {
        "category": "CAM KẾT TÀI CHÍNH & PHÁP LÝ PHI THỰC TẾ",
        "severity": "TRUNG BÌNH (Rủi ro tranh chấp & lừa dối khách hàng)",
        "patterns": [
            (r"\bcam kết sinh lời 100%\b", "Mục tiêu tối ưu hóa tỷ suất sinh lời"),
            (r"\bchắc chắn có lãi\b", "Kỳ vọng tăng trưởng lợi nhuận"),
            (r"\bkhông có (bất kỳ )?rủi ro nào\b", "Kiểm soát rủi ro ở mức tối thiểu"),
            (r"\bchắc chắn trúng thầu\b", "Tối đa hóa năng lực cạnh tranh hồ sơ thầu"),
            (r"\b(đảm bảo|chắc chắn) thắng kiện\b", "Bảo vệ tối đa quyền lợi hợp pháp"),
        ]
    },
    {
        "category": "BẢO MẬT & CÔNG NGHỆ CỰC ĐOAN",
        "severity": "TRUNG BÌNH (Tuyên bố phi kỹ thuật)",
        "patterns": [
            (r"\bbảo mật (dữ liệu )?tuyệt đối\b", "Bảo mật dữ liệu nhiều tầng theo tiêu chuẩn cao"),
            (r"\bkhông thể bị hack\b", "Khả năng chống chịu tấn công mạng kiên cố"),
            (r"\bmiễn nhiễm (hoàn toàn|100%)\b", "Tăng cường sức đề kháng trước mã độc"),
        ]
    }
]

# Các cụm từ cần kiểm tra nguồn chứng minh (Substantiation Check)
CONDITIONAL_CLAIMS = [
    (r"\bsố (1|một)\b", "Cần kèm trích dẫn nguồn công bố hợp pháp (Theo số liệu của... giai đoạn...)"),
    (r"\bduy nhất\b", "Cần tài liệu chứng minh tính độc quyền hoặc duy nhất"),
    (r"\btốt nhất\b", "Cần có chứng nhận giải thưởng hoặc bình chọn của bên thứ ba độc lập"),
    (r"\bhàng đầu\b", "Cần có căn cứ đo lường thị phần hoặc đánh giá tổ chức uy tín"),
]

def check_file(file_path, quiet=False):
    p = Path(file_path)
    if not p.exists():
        print(f"{RED}Lỗi: File không tồn tại: {file_path}{RESET}")
        return 1

    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = text.split("\n")
    violations = []
    warnings = []

    for idx, line in enumerate(lines, 1):
        line_clean = line.strip()
        line_lower = line_clean.lower()

        # 1. Quét vi phạm cấm tuyệt đối
        for cat in CLAIM_RULES:
            for pattern, suggestion in cat["patterns"]:
                match = re.search(pattern, line_lower)
                if match:
                    violations.append({
                        "line": idx,
                        "matched": match.group(0),
                        "snippet": line_clean[:120],
                        "category": cat["category"],
                        "severity": cat["severity"],
                        "suggestion": suggestion
                    })

        # 2. Quét các từ so sánh có điều kiện (Conditional Claims)
        for pattern, note in CONDITIONAL_CLAIMS:
            match = re.search(pattern, line_lower)
            if match:
                # Kiểm tra xem trong dòng hoặc đoạn có nguồn trích dẫn không
                has_source = any(w in line_lower for w in ["theo số liệu", "công bố", "khảo sát", "nguồn:", "báo cáo", "pyuru", "năm 20"])
                if not has_source:
                    warnings.append({
                        "line": idx,
                        "matched": match.group(0),
                        "snippet": line_clean[:120],
                        "note": note
                    })

    # In báo cáo
    if not quiet:
        print(f"\n{BOLD}=== BÁO CÁO THẨM ĐỊNH PHÁP LÝ NỘI DUNG (RULE R5): {p.name} ==={RESET}")

    if violations:
        print(f"{RED}{BOLD}❌ PHÁT HIỆN {len(violations)} VI PHẠM OVER-CLAIM (CẦN CHỈNH SỬA BẮT BUỘC):{RESET}")
        for v in violations:
            print(f"  {RED}• Dòng {v['line']}:{RESET} Phát hiện cụm từ cấm {YELLOW}'{v['matched']}'{RESET}")
            print(f"    - Phân loại: {v['category']} [{v['severity']}]")
            print(f"    - Trích đoạn: \"{v['snippet']}\"")
            print(f"    - {GREEN}Gợi ý thay thế hợp chuẩn:{RESET} \"{v['suggestion']}\"")
            print()

    if warnings and not quiet:
        print(f"{YELLOW}{BOLD}⚠️ CẢNH BÁO {len(warnings)} TUYÊN BỐ CẦN BỔ SUNG MINH CHỨNG (SUBSTANTIATION):{RESET}")
        for w in warnings:
            print(f"  {YELLOW}• Dòng {w['line']}:{RESET} Sử dụng từ so sánh '{w['matched']}' nhưng thiếu ghi chú nguồn:")
            print(f"    - Yêu cầu: {w['note']}")
            print(f"    - Trích đoạn: \"{w['snippet']}\"")
            print()

    if not violations:
        if not quiet:
            print(f"{GREEN}✅ Đạt chuẩn Rule R5! 0 vi phạm over-claim, an toàn pháp lý theo quy định hiện hành.{RESET}\n")
        return 0
    else:
        return 1

def main():
    parser = argparse.ArgumentParser(description="Kiểm tra tính hợp chuẩn pháp lý nội dung & chống over-claim (Rule R5)")
    parser.add_argument("--input", "-i", required=True, help="Đường dẫn file cần kiểm tra")
    parser.add_argument("--quiet", "-q", action="store_true", help="Chỉ in kết quả ngắn gọn")
    args = parser.parse_args()

    sys.exit(check_file(args.input, args.quiet))

if __name__ == "__main__":
    main()
