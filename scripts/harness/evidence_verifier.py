#!/usr/bin/env python3
"""
scripts/harness/evidence_verifier.py

Bộ công cụ kiểm chứng bằng chứng tốc độ cao (Fast Evidence Verifier).
Chống hallucination / bịa số liệu, điều luật, trích dẫn trong văn bản.
100% Python Standard Library — Tốc độ xử lý tính bằng mili-giây, không phụ thuộc thư viện ngoài.

Sử dụng:
    # CLI đơn giản:
    python3 scripts/harness/evidence_verifier.py --source <file_nguon> --quote "<cau_trich_dan>"
    
    # CLI với danh sách trích dẫn JSON:
    python3 scripts/harness/evidence_verifier.py --claims <claims.json>
    
    # Import trong Python:
    from scripts.harness.evidence_verifier import verify_evidence, check_single_quote
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def normalize_whitespace(text: str) -> str:
    """Chuẩn hóa khoảng trắng để tránh sai lệch do xuống dòng hoặc nhiều dấu cách."""
    return re.sub(r"\s+", " ", text).strip()


def check_single_quote(source_text: str, quote: str, case_sensitive: bool = False) -> Tuple[bool, Optional[int]]:
    """
    Kiểm tra một đoạn trích dẫn (quote) có tồn tại chính xác trong văn bản nguồn hay không.
    Trả về: (found: bool, char_index: Optional[int])
    """
    if not quote or not source_text:
        return False, None
    
    norm_source = normalize_whitespace(source_text)
    norm_quote = normalize_whitespace(quote)
    
    if not case_sensitive:
        norm_source = norm_source.lower()
        norm_quote = norm_quote.lower()
    
    idx = norm_source.find(norm_quote)
    if idx != -1:
        return True, idx
    
    # Thử phương án bỏ dấu câu cơ bản nếu trích dẫn có sai lệch nhỏ ở dấu kết thúc
    cleaned_source = re.sub(r"[,\.;:!?\"'«»“”]", "", norm_source)
    cleaned_quote = re.sub(r"[,\.;:!?\"'«»“”]", "", norm_quote)
    idx_clean = cleaned_source.find(cleaned_quote)
    if idx_clean != -1:
        return True, idx_clean
        
    return False, None


def verify_evidence(
    claims: List[Dict[str, Any]], 
    default_source_files: Optional[List[str]] = None,
    threshold: float = 0.85,
    case_sensitive: bool = False
) -> Dict[str, Any]:
    """
    Kiểm chứng danh sách các claims / trích dẫn đối chiếu với văn bản nguồn.
    
    Format claims:
    [
        {
            "claim": "Tên khẳng định hoặc điều luật",
            "verbatim_quote": "Câu trích dẫn nguyên văn",
            "source": "path/to/source_file.md" (tùy chọn, nếu có sẽ ưu tiên)
        }
    ]
    
    Trả về:
    {
        "passes": bool,
        "confidence_score": float (0.0 - 1.0),
        "total_claims": int,
        "verified_count": int,
        "missing_count": int,
        "details": [...]
    }
    """
    if not claims:
        return {
            "passes": True,
            "confidence_score": 1.0,
            "total_claims": 0,
            "verified_count": 0,
            "missing_count": 0,
            "details": []
        }

    # Cache nội dung file nguồn để đọc siêu tốc một lần
    file_cache: Dict[str, str] = {}
    
    def get_file_content(path_str: str) -> str:
        if path_str not in file_cache:
            p = Path(path_str)
            if p.is_file():
                try:
                    file_cache[path_str] = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    file_cache[path_str] = ""
            else:
                file_cache[path_str] = ""
        return file_cache[path_str]

    details = []
    verified_count = 0

    for item in claims:
        claim_name = item.get("claim", "")
        quote = item.get("verbatim_quote", "")
        source_path = item.get("source", "")
        
        found = False
        match_location = None
        searched_sources = []
        
        # 1. Tìm trong source cụ thể nếu được khai báo
        if source_path:
            searched_sources.append(source_path)
            content = get_file_content(source_path)
            if content:
                found, match_location = check_single_quote(content, quote, case_sensitive)
        
        # 2. Nếu chưa tìm thấy và có danh sách default_source_files -> tìm lần lượt
        if not found and default_source_files:
            for d_source in default_source_files:
                if d_source not in searched_sources:
                    searched_sources.append(d_source)
                    content = get_file_content(d_source)
                    if content:
                        found, match_location = check_single_quote(content, quote, case_sensitive)
                        if found:
                            source_path = d_source
                            break

        if found:
            verified_count += 1
            details.append({
                "claim": claim_name,
                "quote": quote,
                "status": "VERIFIED",
                "source": source_path,
                "match_offset": match_location
            })
        else:
            details.append({
                "claim": claim_name,
                "quote": quote,
                "status": "MISSING",
                "source": source_path,
                "searched_in": searched_sources
            })

    total = len(claims)
    confidence = round(verified_count / total, 3) if total > 0 else 1.0
    passes = confidence >= threshold

    return {
        "passes": passes,
        "confidence_score": confidence,
        "threshold": threshold,
        "total_claims": total,
        "verified_count": verified_count,
        "missing_count": total - verified_count,
        "details": details
    }


def main():
    parser = argparse.ArgumentParser(description="AIWF Fast Evidence Verifier")
    parser.add_argument("--source", type=str, help="Đường dẫn file nguồn cần đối chiếu")
    parser.add_argument("--quote", type=str, help="Câu trích dẫn nguyên văn cần kiểm tra")
    parser.add_argument("--claims", type=str, help="Đường dẫn file JSON chứa danh sách claims")
    parser.add_argument("--threshold", type=float, default=0.85, help="Ngưỡng tin cậy đạt chuẩn (mặc định: 0.85)")
    parser.add_argument("--case-sensitive", action="store_true", help="Phân biệt chữ hoa/thường")
    
    args = parser.parse_args()
    
    if args.source and args.quote:
        p = Path(args.source)
        if not p.is_file():
            print(f"❌ Không tìm thấy file nguồn: {args.source}", file=sys.stderr)
            sys.exit(1)
        content = p.read_text(encoding="utf-8", errors="ignore")
        found, idx = check_single_quote(content, args.quote, args.case_sensitive)
        if found:
            print(f"✅ VERIFIED: Tìm thấy trích dẫn tại ký tự {idx} trong {args.source}")
            sys.exit(0)
        else:
            print(f"❌ NOT FOUND: Không tìm thấy trích dẫn trong {args.source}", file=sys.stderr)
            sys.exit(2)
            
    elif args.claims:
        claims_path = Path(args.claims)
        if not claims_path.is_file():
            print(f"❌ Không tìm thấy file claims: {args.claims}", file=sys.stderr)
            sys.exit(1)
        try:
            claims_data = json.loads(claims_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ Lỗi đọc JSON claims: {e}", file=sys.stderr)
            sys.exit(1)
            
        res = verify_evidence(claims_data, threshold=args.threshold, case_sensitive=args.case_sensitive)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if res["passes"] else 2)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
