#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate-article-draft.py — Bộ kiểm định tự động bản thảo bài viết ChottoDay
Theo tiêu chuẩn kiến trúc Rule R4, R5 và quy chuẩn kỹ thuật ChottoDay.

Cách sử dụng:
    python3 scripts/validate-article-draft.py --input /path/to/article.js
    python3 scripts/validate-article-draft.py --dir ~/Downloads/
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

# 12 Loại section hợp lệ tuyệt đối trong ChottoDay (src/services/content/articleModel.js)
VALID_SECTION_TYPES = {
    'intro', 'heading', 'paragraph', 'list', 'steps',
    'term', 'note', 'warning', 'example', 'quote',
    'toolCTA', 'sources'
}

# 9 Danh mục hợp lệ trong ChottoDay
VALID_CATEGORIES = {
    'life', 'doc', 'work', 'health', 'study',
    'tool', 'newcomer', 'job', 'family'
}

# 3 Loại nguồn tin hợp lệ
VALID_SOURCE_TYPES = {'official', 'primary', 'reference'}

# Danh sách từ ngữ sáo rỗng AI tiếng Việt
AI_BUZZWORDS = [
    r"trong kỷ nguyên số",
    r"đóng vai trò then chốt",
    r"như chúng ta đã biết",
    r"hãy cùng khám phá",
    r"là một giải pháp hoàn hảo",
    r"cần lưu ý rằng",
    r"không thể phủ nhận rằng",
    r"bước tiến vượt bậc",
    r"bức tranh toàn cảnh"
]

# Danh mục từ ngữ over-claim vi phạm Luật R5
BANNED_CLAIMS = [
    r"an toàn tuyệt đối",
    r"tuyệt đối an toàn",
    r"100% an toàn",
    r"chắc chắn có lãi",
    r"không có bất kỳ rủi ro nào",
    r"đảm bảo thắng kiện 100%",
    r"100% đậu visa",
    r"chắc chắn đậu visa",
    r"triệt để 100%"
]

def parse_js_article(content):
    """Bóc tách nhanh các trường cơ bản từ file JavaScript ES module."""
    data = {}
    
    # Bóc tách slug
    m_slug = re.search(r"slug:\s*['\"]([^'\"]+)['\"]", content)
    if m_slug:
        data['slug'] = m_slug.group(1)
        
    # Bóc tách title
    m_title = re.search(r"title:\s*['\"]([^'\"]+)['\"]", content)
    if m_title:
        data['title'] = m_title.group(1)
        
    # Bóc tách category
    m_cat = re.search(r"category:\s*['\"]([^'\"]+)['\"]", content)
    if m_cat:
        data['category'] = m_cat.group(1)
        
    # Bóc tách status
    m_status = re.search(r"status:\s*['\"]([^'\"]+)['\"]", content)
    if m_status:
        data['status'] = m_status.group(1)
        
    # Bóc tách reviewer
    m_rev = re.search(r"reviewer:\s*['\"]([^'\"]+)['\"]", content)
    if m_rev:
        data['reviewer'] = m_rev.group(1)
        
    # Bóc tách readingTime
    m_rt = re.search(r"readingTime:\s*(\d+)", content)
    if m_rt:
        data['readingTime'] = int(m_rt.group(1))

    # Bóc tách các section types
    section_types = re.findall(r"type:\s*['\"]([a-zA-Z0-9_]+)['\"]", content)
    data['section_types'] = section_types
    
    # Bóc tách các source types
    source_types = re.findall(r"sourceType:\s*['\"]([a-zA-Z0-9_]+)['\"]", content)
    data['source_types'] = source_types
    
    return data

def validate_article_file(file_path):
    """Kiểm tra toàn diện 1 file bản thảo bài viết .js."""
    path = Path(file_path)
    errors = []
    warnings = []
    
    if not path.exists():
        return False, [f"Tệp không tồn tại: {file_path}"], []
        
    content = path.read_text(encoding="utf-8", errors="ignore")
    parsed = parse_js_article(content)
    
    # 1. Kiểm tra status (Bắt buộc là 'review')
    status = parsed.get('status')
    if not status:
        errors.append("Thiếu trường 'status'.")
    elif status != 'review':
        errors.append(f"Quy tắc an toàn vi phạm: 'status' phải là 'review' (hiện tại: '{status}'). Chỉ biên tập viên con người mới được chuyển sang 'published'.")
        
    # 2. Kiểm tra reviewer (Bắt buộc là 'CHƯA DUYỆT')
    reviewer = parsed.get('reviewer')
    if not reviewer:
        errors.append("Thiếu trường 'reviewer'.")
    elif reviewer != 'CHƯA DUYỆT':
        warnings.append(f"'reviewer' hiện là '{reviewer}'. Bản thảo tự động khuyến nghị giữ nguyên 'CHƯA DUYỆT' để chặn CI xuất bản nhầm.")
        
    # 3. Kiểm tra category
    category = parsed.get('category')
    if not category:
        errors.append("Thiếu trường 'category'.")
    elif category not in VALID_CATEGORIES:
        errors.append(f"Mã category '{category}' không hợp lệ. Phải thuộc 9 danh mục: {sorted(list(VALID_CATEGORIES))}")
        
    # 4. Kiểm tra slug
    slug = parsed.get('slug')
    if not slug:
        errors.append("Thiếu trường 'slug'.")
    elif not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug):
        errors.append(f"Slug '{slug}' không đúng chuẩn kebab-case chữ thường.")
        
    # 5. Kiểm tra export syntax
    if not re.search(r"export\s+const\s+article[A-Za-z0-9]+\s*=", content):
        errors.append("Thiếu khai báo export const article[CamelCase] = { ... }.")
    if not re.search(r"export\s+default\s+article[A-Za-z0-9]+;", content):
        errors.append("Thiếu khai báo export default article[CamelCase];.")
        
    # 6. Kiểm tra 12 section types (Cấm tuyệt đối loại lạ làm hỏng giao diện)
    section_types = parsed.get('section_types', [])
    if not section_types:
        errors.append("Bài viết không có bất kỳ section nào trong mảng sections.")
    else:
        for st in section_types:
            if st not in VALID_SECTION_TYPES:
                errors.append(f"Phát hiện section type KHÔNG HỢP LỆ: '{st}'. Sẽ bị renderer ChottoDay bỏ qua và render trắng trơn! Chỉ được dùng 12 loại: {sorted(list(VALID_SECTION_TYPES))}")
                
    # 7. Kiểm tra nguồn tin chính thức (Official Sources)
    source_types = parsed.get('source_types', [])
    if 'official' not in source_types:
        warnings.append("Khuyến nghị bài viết phải có ít nhất 1 nguồn 'sourceType: official' (.go.jp hoặc cơ quan nhà nước).")
    if '.go.jp' not in content and '.lg.jp' not in content:
        warnings.append("Không tìm thấy tên miền chính phủ (.go.jp hoặc .lg.jp) trong danh sách nguồn tin.")
        
    # 8. Kiểm tra Khử Dấu Vết AI (Anti-AI Footprint)
    em_dashes = content.count("—")
    if em_dashes > 0:
        errors.append(f"Phát hiện {em_dashes} dấu gạch ngang dài em-dash ('—'). Vi phạm Anti-AI standard! Hãy đổi thành ' - ' hoặc liên từ.")
        
    oxford_commas = len(re.findall(r",\s*và\b", content))
    if oxford_commas > 0:
        errors.append(f"Phát hiện {oxford_commas} dấu phẩy Oxford (', và'). Tiếng Việt chuẩn chỉ dùng 'và'.")
        
    heading_colons = len(re.findall(r"type:\s*['\"]heading['\"].*?text:\s*['\"][^'\"]+:\s*['\"]", content, re.DOTALL))
    if heading_colons > 0:
        warnings.append("Phát hiện heading kết thúc bằng dấu hai chấm ':'. Nên bỏ dấu hai chấm ở cuối tiêu đề.")
        
    for bw in AI_BUZZWORDS:
        m = re.search(bw, content, re.IGNORECASE)
        if m:
            warnings.append(f"Phát hiện cụm từ sáo rỗng AI: '{m.group(0)}'.")

    # 9. Kiểm tra Luật R5: Banned Legal Claims
    for claim in BANNED_CLAIMS:
        m = re.search(claim, content, re.IGNORECASE)
        if m:
            errors.append(f"Vi phạm Luật R5 (Over-claim): Phát hiện cụm từ cấm '{m.group(0)}'.")

    is_pass = len(errors) == 0
    return is_pass, errors, warnings

def main():
    parser = argparse.ArgumentParser(description="Kiểm tra bản thảo bài viết ChottoDay theo chuẩn R4, R5.")
    parser.add_argument("--input", "-i", help="Đường dẫn đến file .js cần kiểm tra")
    parser.add_argument("--dir", "-d", help="Đường dẫn thư mục chứa các file .js cần kiểm tra")
    args = parser.parse_args()

    if not args.input and not args.dir:
        parser.print_help()
        sys.exit(1)

    targets = []
    if args.input:
        targets.append(Path(args.input))
    if args.dir:
        p_dir = Path(args.dir)
        if p_dir.exists():
            targets.extend(p_dir.glob("*.js"))

    if not targets:
        print(f"{YELLOW}Không tìm thấy file .js nào để kiểm tra.{RESET}")
        sys.exit(0)

    total_pass = 0
    total_fail = 0

    print(f"\n{BOLD}═══════════════════════════════════════════════════════════════════{RESET}")
    print(f" {BOLD}CHOTTODAY ARTICLE DRAFT VALIDATOR{RESET}")
    print(f"{BOLD}═══════════════════════════════════════════════════════════════════{RESET}")

    for t in targets:
        is_pass, errors, warnings = validate_article_file(t)
        status_text = f"{GREEN}{BOLD}PASS{RESET}" if is_pass else f"{RED}{BOLD}FAIL{RESET}"
        print(f"\n📄 {BOLD}{t.name}{RESET} [{status_text}]")
        
        if errors:
            print(f"  {RED}{BOLD}Lỗi bắt buộc sửa:{RESET}")
            for err in errors:
                print(f"    ❌ {err}")
            total_fail += 1
        else:
            total_pass += 1

        if warnings:
            print(f"  {YELLOW}{BOLD}Cảnh báo tối ưu:{RESET}")
            for warn in warnings:
                print(f"    ⚠️  {warn}")

    print(f"\n{BOLD}───────────────────────────────────────────────────────────────────{RESET}")
    print(f" Kết quả: {GREEN}{total_pass} ĐẠT{RESET} | {RED}{total_fail} KHÔNG ĐẠT{RESET}")
    print(f"{BOLD}═══════════════════════════════════════════════════════════════════{RESET}\n")

    sys.exit(0 if total_fail == 0 else 1)

if __name__ == "__main__":
    main()
