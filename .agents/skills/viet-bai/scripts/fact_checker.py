#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fact_checker.py — Cổng chất lượng của viet-bai: (1) pháp lý quảng cáo R5, (2) dấu vết văn phong AI,
(3) lỗi bàn giao (placeholder chưa điền, trích dẫn phát ngôn chưa xác nhận, thiếu disclaimer bắt buộc).

Phần pháp lý dùng scripts/claim_guard.py ở gốc repo với hồ sơ --profile ads (nghiêm ngặt: từ "nhất", "số 1",
"hàng đầu"... thiếu nguồn = LỖI). Không có fallback im lặng: không nạp được claim_guard -> exit 2.

Usage:
  python3 .agents/skills/viet-bai/scripts/fact_checker.py --input <bài.md>
         [--category general|cosmetics|tpcn|drug|finance|medical_service] [--channel blog|web|facebook|pr]
Exit: 0 = đạt; 1 = còn lỗi phải sửa; 2 = lỗi chạy (file không đọc được / thiếu claim_guard).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Cụm sáo rỗng kiểu văn máy (LỖI). Mỗi mục: (regex, gợi ý)
AI_CLICHES = [
    (r"kỷ nguyên (số|4\.0|công nghệ)", "Nêu bối cảnh cụ thể: năm, thị trường, con số"),
    (r"(trong )?thời đại (số|số hóa|4\.0|công nghệ)", "Nêu bối cảnh cụ thể"),
    (r"trong (thế giới|bối cảnh) (ngày nay|hiện nay|hiện đại)", "Đi thẳng vào tình huống của khách hàng"),
    (r"đóng (một )?vai trò (then chốt|quan trọng|chủ chốt|trọng yếu|cốt lõi)", "Nêu thẳng tác dụng đo được"),
    (r"như chúng ta (đã )?(biết|thấy)", "Bỏ, khẳng định trực tiếp"),
    (r"không thể phủ nhận", "Bỏ, khẳng định trực tiếp"),
    (r"bức tranh toàn cảnh", "Toàn bộ diễn biến thị trường"),
    (r"cầu nối (vững chắc|hoàn hảo)", "Cách thức kết nối cụ thể"),
    (r"mang tính cách mạng", "Thay đổi đo được"),
    (r"bước chuyển mình", "Thay đổi cụ thể nào, khi nào"),
    (r"hãy cùng (chúng tôi )?(khám phá|tìm hiểu)", "Đi thẳng vào nội dung"),
    (r"bạn (đã )?(có )?bao giờ tự hỏi", "Mở bằng tình huống/con số thật"),
    (r"nâng tầm", "Nêu kết quả cụ thể"),
    (r"khai phá (tiềm năng|sức mạnh)", "Nêu kết quả cụ thể"),
    (r"chìa khóa (vàng|thành công)|bí quyết vàng", "Nêu cách làm cụ thể"),
    (r"hành trình (chinh phục|khám phá|chuyển đổi)", "Mô tả quá trình cụ thể"),
    (r"giải pháp (toàn diện|tối ưu|đột phá|hoàn hảo)", "Giải pháp làm gì, cho ai, kết quả bao nhiêu"),
]
# Văn phong nên tránh (CẢNH BÁO, không chặn)
STYLE_WARN = [
    (r"không chỉ\b[^.!?\n]{1,80}\bmà còn\b", "Cấu trúc 'không chỉ... mà còn' lặp kiểu văn máy"),
    (r"^(tóm lại|nhìn chung|hơn nữa|ngoài ra|bên cạnh đó),", "Từ nối mở câu kiểu văn máy"),
]
EXEC_QUOTE = re.compile(
    r"(ông|bà|ceo|giám đốc|tổng giám đốc|đại diện|founder|nhà sáng lập|chủ tịch|trưởng phòng|chuyên gia|bác sĩ)\b"
    r"[^\n]{0,100}(cho biết|chia sẻ|phát biểu|nhấn mạnh|khẳng định|nói)", re.I)
PLACEHOLDER = re.compile(r"\[(?!\^)(?!CẦN XÁC MINH)(?!CẦN XÁC NHẬN)[^\]\n]{2,80}\](?!\()")
REQUIRED_DISCLAIMERS = {
    "tpcn": (r"không phải là thuốc,?\s*(và\s*)?không có tác dụng thay thế thuốc chữa bệnh",
             "Thực phẩm này không phải là thuốc, không có tác dụng thay thế thuốc chữa bệnh."),
    "cosmetics": (r"không phải là thuốc", "Sản phẩm mỹ phẩm, không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh."),
    "drug": (r"đọc kỹ hướng dẫn sử dụng trước khi dùng", "Đọc kỹ hướng dẫn sử dụng trước khi dùng. (+ số giấy xác nhận nội dung quảng cáo)"),
    "finance": (r"rủi ro", "Câu cảnh báo rủi ro: lợi nhuận quá khứ không bảo đảm kết quả tương lai..."),
}


def style_checks(text: str, category: str) -> tuple[list[str], list[str]]:
    errors, warns = [], []
    lines = text.split("\n")
    in_code = False
    for idx, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not s:
            continue
        low = s.lower()
        if "—" in s:
            errors.append(f"Dòng {idx}: em dash '—' -> dùng ' - ' hoặc từ nối")
        # dấu phẩy Oxford: chỉ khi là LIỆT KÊ >= 3 phần tử ("A, B, và C"), không bắt câu ghép "..., và chúng tôi..."
        for m in re.finditer(r",\s+và\s", s):
            seg = re.split(r"[.!?;:]", s[:m.start()])[-1]
            if seg.count(",") >= 1 and len(seg.split(",")[-1].split()) <= 4:
                errors.append(f"Dòng {idx}: dấu phẩy trước 'và' trong liệt kê (', và') -> bỏ dấu phẩy")
                break
        if re.match(r"^#{1,6}\s+.*:\s*$", s):
            errors.append(f"Dòng {idx}: tiêu đề kết thúc bằng dấu ':'")
        for pat, tip in AI_CLICHES:
            m = re.search(pat, low)
            if m:
                errors.append(f"Dòng {idx}: cụm sáo rỗng '{m.group(0)}' -> {tip}")
        for pat, tip in STYLE_WARN:
            m = re.search(pat, low)
            if m:
                warns.append(f"Dòng {idx}: {tip} ('{m.group(0)[:40]}')")
        for m in PLACEHOLDER.finditer(s):
            errors.append(f"Dòng {idx}: còn placeholder chưa điền {m.group(0)} (điền dữ liệu thật hoặc xóa)")
        if EXEC_QUOTE.search(s) and re.search(r"[\"“”]", s) and "[CẦN XÁC NHẬN" not in s:
            errors.append(f"Dòng {idx}: trích dẫn phát ngôn chưa được xác nhận -> thêm '[CẦN XÁC NHẬN: người phát ngôn duyệt]' "
                          f"hoặc dùng trích dẫn thật có nguồn")
        words = len(re.findall(r"\w+", s))
        if words > 45 and not s.startswith("|"):
            warns.append(f"Dòng {idx}: câu/đoạn dài {words} từ (nên tách)")
    if category in REQUIRED_DISCLAIMERS:
        pat, sample = REQUIRED_DISCLAIMERS[category]
        if not re.search(pat, text.lower()):
            errors.append(f"Thiếu câu bắt buộc cho nhóm '{category}': \"{sample}\"")
    return errors, warns


def check_file(file_path: str, category: str = "general", channel: str = "") -> int:
    p = Path(file_path)
    if not p.is_file():
        print(f"Lỗi: File không tồn tại: {file_path}")
        return 2
    try:
        from scripts.claim_guard import check_file as check_legal_claims
    except Exception as e:  # noqa: BLE001
        print(f"[CRASH] Không nạp được scripts/claim_guard.py ({type(e).__name__}: {e}). KHÔNG được coi là đạt.")
        return 2

    text = p.read_text(encoding="utf-8", errors="ignore")
    errors, warns = style_checks(text, category)

    print(f"\n=== 1. VĂN PHONG & BÀN GIAO: {p.name} (nhóm: {category}{', kênh: ' + channel if channel else ''}) ===")
    if errors:
        print(f"❌ {len(errors)} lỗi phải sửa:")
        for e in errors:
            print(f"  • {e}")
    else:
        print("✅ 0 lỗi văn phong/bàn giao.")
    for w in warns:
        print(f"  ⚠️ {w}")

    res = check_legal_claims(str(p), quiet=False, strict=True, profile="ads")
    legal_status = res.get("status")
    if legal_status == "BLOCKED":
        return 2
    legal_fail = legal_status != "PASS"

    ok = not errors and not legal_fail
    print("\n=== KẾT LUẬN ===")
    print("✅ ĐẠT: được phép bàn giao." if ok else
          f"❌ CHƯA ĐẠT: {len(errors)} lỗi văn phong/bàn giao, {res.get('violations_count', 0)} vi phạm R5. Sửa rồi chạy lại.")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Cổng chất lượng viet-bai: R5 + văn phong + bàn giao")
    parser.add_argument("--input", "-i", required=True, help="File bài viết (.md/.txt/.html/.docx)")
    parser.add_argument("--category", default="general",
                        choices=["general", "cosmetics", "tpcn", "drug", "finance", "medical_service"],
                        help="Nhóm sản phẩm (quyết định câu disclaimer bắt buộc)")
    parser.add_argument("--channel", default="", help="blog | web | facebook | pr (chỉ để ghi báo cáo)")
    args = parser.parse_args()
    return check_file(args.input, args.category, args.channel)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"[CRASH] fact_checker.py: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(2)
