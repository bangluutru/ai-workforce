#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fact_checker.py — Công cụ kiểm tra tính toàn vẹn, khử dấu vết AI & thẩm định pháp lý (Rule R5)
Kiểm tra:
  1. Dấu vết AI: em-dash, Oxford comma, dấu hai chấm cuối tiêu đề, các cụm từ sáo rỗng.
  2. An toàn pháp lý: Chống over-claim (an toàn tuyệt đối, đặc trị, số 1 không nguồn...).
"""

import sys
import os
import re
import argparse
from pathlib import Path

# Thêm path tới root để import scripts.claim_guard nếu có
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scripts.claim_guard import check_file as check_legal_claims
except ImportError:
    check_legal_claims = None

BANNED_WORDS = [
    "kỷ nguyên số",
    "đóng vai trò then chốt",
    "như chúng ta đã biết",
    "không thể phủ nhận rằng",
    "bức tranh toàn cảnh",
    "cầu nối vững chắc",
    "mang tính cách mạng",
    "bước chuyển mình mạnh mẽ"
]

def check_file(file_path):
    p = Path(file_path)
    if not p.exists():
        print(f"Lỗi: File không tồn tại: {file_path}")
        return 1

    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = text.split("\n")
    issues = []

    for idx, line in enumerate(lines, 1):
        # 1. Kiểm tra em dash —
        if "—" in line:
            issues.append(f"Dòng {idx}: Phát hiện em-dash '—' (Cần đổi thành ' - ' hoặc từ nối)")

        # 2. Kiểm tra Oxford comma ', và'
        if re.search(r",\s+và\b", line):
            issues.append(f"Dòng {idx}: Phát hiện Oxford comma ', và' (Tiếng Việt chỉ dùng ' và ')")

        # 3. Kiểm tra dấu hai chấm cuối heading
        if re.match(r"^#{1,6}\s+.*:\s*$", line.strip()):
            issues.append(f"Dòng {idx}: Tiêu đề có dấu hai chấm ':' ở cuối dòng")

        # 4. Kiểm tra cụm từ sáo rỗng
        line_lower = line.lower()
        for bw in BANNED_WORDS:
            if bw in line_lower:
                issues.append(f"Dòng {idx}: Phát hiện cụm từ sáo rỗng '{bw}'")

    print(f"\n=== 1. BÁO CÁO KHỬ DẤU VẾT AI: {p.name} ===")
    ai_status = 0
    if issues:
        print(f"⚠️ Phát hiện {len(issues)} điểm cần biên tập:")
        for iss in issues:
            print(f"  • {iss}")
        ai_status = 1
    else:
        print("✅ Hoàn hảo! 0 dấu vết AI, 0 lỗi định dạng tiếng Việt.")

    # 5. Kiểm tra an toàn pháp lý & chống over-claim (Rule R5)
    legal_status = 0
    if check_legal_claims:
        legal_status = check_legal_claims(file_path, quiet=False)
    else:
        # Fallback regex cơ bản nếu không import được
        OVERCLAIM_PATTERNS = [
            (r"\ban toàn tuyệt đối\b", "An toàn tuyệt đối"),
            (r"\btuyệt đối an toàn\b", "Tuyệt đối an toàn"),
            (r"\bđặc trị\b", "Đặc trị"),
            (r"\btrị dứt điểm\b", "Trị dứt điểm"),
            (r"\bcam kết sinh lời\b", "Cam kết sinh lời"),
            (r"\bbảo mật tuyệt đối\b", "Bảo mật tuyệt đối"),
        ]
        overclaims = []
        for idx, line in enumerate(lines, 1):
            line_l = line.lower()
            for pat, name in OVERCLAIM_PATTERNS:
                if re.search(pat, line_l):
                    overclaims.append(f"Dòng {idx}: Phát hiện over-claim '{name}'")
        print(f"\n=== 2. BÁO CÁO PHÁP LÝ NỘI DUNG (RULE R5): {p.name} ===")
        if overclaims:
            print(f"❌ Phát hiện {len(overclaims)} vi phạm over-claim:")
            for oc in overclaims:
                print(f"  • {oc}")
            legal_status = 1
        else:
            print("✅ Đạt chuẩn Rule R5! 0 vi phạm over-claim.")

    return 1 if (ai_status != 0 or legal_status != 0) else 0

def main():
    parser = argparse.ArgumentParser(description="Kiểm tra văn phong, khử dấu vết AI & thẩm định pháp lý (Rule R5)")
    parser.add_argument("--input", "-i", required=True, help="Đường dẫn file cần kiểm tra")
    args = parser.parse_args()

    sys.exit(check_file(args.input))

if __name__ == "__main__":
    main()
