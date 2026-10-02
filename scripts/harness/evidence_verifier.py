#!/usr/bin/env python3
"""
scripts/harness/evidence_verifier.py

Bộ kiểm chứng trích dẫn nguyên văn (Evidence Verifier).
Chống bịa điều luật, số liệu, trích dẫn: mỗi trích dẫn phải có NGUYÊN VĂN trong file nguồn
đã lưu trên máy, và (nếu khai `article`) phải nằm TRONG khối của đúng Điều/条 được viện dẫn.
100% Python Standard Library.

Sử dụng:
    # Một trích dẫn:
    python3 scripts/harness/evidence_verifier.py --source <file_nguon.txt> --quote "<câu>" [--article "Điều 75"]

    # Danh sách trích dẫn (khuyến nghị):
    python3 scripts/harness/evidence_verifier.py --claims <claims.json>

    Format claims.json:
    [
      {
        "claim": "Luật 59/2020/QH14 – Điều 75, Khoản 2",
        "verbatim_quote": "Chủ sở hữu công ty phải góp đủ [...] trong thời hạn 90 ngày",
        "source": "<research_dir>/sources/luat-59-2020.txt",   # FILE trên máy, không phải URL
        "article": "Điều 75"                                    # hoặc "第67条", "67"; tùy chọn nhưng nên có
      }
    ]

Quy tắc (mặc định, nghiêm ngặt):
    - Danh sách claims rỗng = FAIL (không có gì được kiểm chứng thì không được báo đạt).
    - Ngưỡng mặc định 1.0: MỘT trích dẫn không tìm thấy là FAIL.
    - Trích dẫn quá ngắn (< 30 ký tự sau khi bỏ khoảng trắng/dấu câu, chữ Hán/kana tính 2; mỗi đoạn giữa "[...]" < 8) = FAIL.
    - `source` là URL = FAIL: phải lưu nội dung đã tải vào file trong <research_dir>/sources/ rồi trỏ tới file.
    - Có `article` thì trích dẫn phải nằm trong khối của Điều đó (từ tiêu đề "Điều N." tới tiêu đề Điều kế tiếp).
    - "[...]" hoặc "…" trong trích dẫn = phần lược; các đoạn còn lại phải xuất hiện đúng thứ tự.

    Import trong Python (giữ tương thích):
    from scripts.harness.evidence_verifier import verify_evidence, check_single_quote
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_THRESHOLD = 1.0
DEFAULT_MIN_QUOTE_CHARS = 30
MIN_SEGMENT_CHARS = 8

_ELLIPSIS = re.compile(r"\[\s*(?:\.\.\.|…)\s*\]|\(\s*(?:\.\.\.|…)\s*\)|…|\.\.\.")
_PUNCT = re.compile(r"[,\.;:!?\"'«»“”‘’「」『』、。・（）()\[\]]")
_KANJI_DIGITS = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def normalize_text(text: str) -> str:
    """NFKC (gộp dấu tiếng Việt tổ hợp, chữ số toàn góc, bộ thủ Kangxi) + gộp khoảng trắng."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


# Giữ tên cũ cho mã gọi cũ
def normalize_whitespace(text: str) -> str:
    return normalize_text(text)


def _compact(text: str) -> str:
    """Bỏ khoảng trắng và dấu câu: dùng cho so khớp chịu lỗi xuống dòng / ngắt bảng PDF."""
    return re.sub(r"\s+", "", _PUNCT.sub("", text))


def to_kanji_number(n: int) -> str:
    """67 -> 六十七 (đủ cho số điều luật Nhật < 10000)."""
    digits = "〇一二三四五六七八九"
    if n == 0:
        return "〇"
    out = ""
    for value, unit in ((1000, "千"), (100, "百"), (10, "十")):
        q, n = divmod(n, value)
        if q:
            out += ("" if q == 1 else digits[q]) + unit
    if n:
        out += digits[n]
    return out


def _article_number(article: str) -> Optional[str]:
    m = re.search(r"(\d+)", normalize_text(article))
    if m:
        return m.group(1)
    m = re.search(r"第([〇一二三四五六七八九十百千]+)条", article)
    if m:
        return str(_kanji_to_int(m.group(1)))
    return None


def _kanji_to_int(s: str) -> int:
    total, cur = 0, 0
    for ch in s:
        if ch in _KANJI_DIGITS:
            cur = _KANJI_DIGITS[ch]
        else:
            unit = {"十": 10, "百": 100, "千": 1000}[ch]
            total += (cur or 1) * unit
            cur = 0
    return total + cur


def extract_article_block(source_text: str, article: str) -> Optional[str]:
    """Trả về đoạn văn bản của đúng một Điều (VN) hoặc 条 (JP); None nếu không tìm thấy tiêu đề."""
    num = _article_number(article)
    if not num:
        return None
    text = normalize_text_keep_lines(source_text)
    n = int(num)
    vn_head = re.compile(r"(?m)^[\s\*#>“\"|]*Điều\s+(\d+)\s*[\.:]")
    jp_head = re.compile(r"(?m)^[\s\*#>（(|]*第([〇一二三四五六七八九十百千\d]+)条(?:の[〇一二三四五六七八九十百千\d]+)?[\s　]")
    heads = []
    for m in vn_head.finditer(text):
        heads.append((m.start(), int(m.group(1))))
    for m in jp_head.finditer(text):
        g = m.group(1)
        heads.append((m.start(), int(g) if g.isdigit() else _kanji_to_int(g)))
    heads.sort()
    blocks = []
    for i, (pos, val) in enumerate(heads):
        if val == n:
            end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
            blocks.append(text[pos:end])
    # VB sửa đổi trích lại "Điều N" của VB gốc trong ngoặc kép, nên một số Điều có thể có
    # nhiều khối; gộp tất cả các khối mang đúng số N (không gộp khối của Điều khác).
    return "\n".join(blocks) if blocks else None


def normalize_text_keep_lines(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").replace(" ", " ")
    return "\n".join(re.sub(r"[ \t]+", " ", ln) for ln in text.splitlines())


def _quote_segments(quote: str) -> List[str]:
    return [s.strip() for s in _ELLIPSIS.split(normalize_text(quote)) if s.strip()]


def check_single_quote(source_text: str, quote: str, case_sensitive: bool = False) -> Tuple[bool, Optional[int]]:
    """
    Kiểm tra trích dẫn có trong văn bản nguồn hay không (các đoạn ngăn bởi "[...]" phải theo đúng thứ tự).
    Trả về: (found, vị trí ký tự của đoạn đầu trong văn bản đã chuẩn hóa).
    Không áp ngưỡng độ dài ở đây; dùng verify_evidence để có đầy đủ quy tắc.
    """
    if not quote or not source_text:
        return False, None
    src = normalize_text(source_text)
    segs = _quote_segments(quote)
    if not segs:
        return False, None
    if not case_sensitive:
        src = src.lower()
        segs = [s.lower() for s in segs]

    # Lượt 1: khớp nguyên văn (chỉ chuẩn hóa khoảng trắng)
    pos, first = 0, None
    ok = True
    for s in segs:
        idx = src.find(s, pos)
        if idx == -1:
            ok = False
            break
        first = idx if first is None else first
        pos = idx + len(s)
    if ok:
        return True, first

    # Lượt 2: bỏ dấu câu và khoảng trắng (PDF ngắt dòng/ô bảng)
    csrc = _compact(src)
    pos, first = 0, None
    for s in segs:
        cs = _compact(s)
        idx = csrc.find(cs, pos)
        if idx == -1:
            return False, None
        first = idx if first is None else first
        pos = idx + len(cs)
    return True, first


_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")


def _weighted_len(text: str) -> int:
    """Độ dài có trọng số: chữ Hán/kana mang nhiều nghĩa hơn nên tính 2."""
    c = _compact(text)
    return len(c) + len(_CJK.findall(c))


def _too_short(quote: str, min_chars: int) -> Optional[str]:
    segs = _quote_segments(quote)
    total = sum(_weighted_len(s) for s in segs)
    if total < min_chars:
        return f"trích dẫn quá ngắn ({total} ký tự < {min_chars}); trích đủ câu chứa quy định"
    short = [s for s in segs if _weighted_len(s) < MIN_SEGMENT_CHARS]
    if short:
        return f"đoạn giữa '[...]' quá ngắn: {short[:2]}"
    return None


def verify_evidence(
    claims: List[Dict[str, Any]],
    default_source_files: Optional[List[str]] = None,
    threshold: float = DEFAULT_THRESHOLD,
    case_sensitive: bool = False,
    min_quote_chars: int = DEFAULT_MIN_QUOTE_CHARS,
) -> Dict[str, Any]:
    """
    Kiểm chứng danh sách claims. Trả về dict: passes, confidence_score, total_claims,
    verified_count, missing_count, details[...]. Mỗi detail có status VERIFIED / MISSING /
    INVALID (quote ngắn, source là URL, thiếu quote) / WRONG_ARTICLE.
    """
    if not claims:
        return {
            "passes": False,
            "confidence_score": 0.0,
            "threshold": threshold,
            "total_claims": 0,
            "verified_count": 0,
            "missing_count": 0,
            "details": [],
            "error": "Danh sách claims rỗng: không có trích dẫn nào được kiểm chứng.",
        }

    cache: Dict[str, str] = {}

    def read(path_str: str) -> str:
        if path_str not in cache:
            p = Path(path_str).expanduser()
            try:
                cache[path_str] = p.read_text(encoding="utf-8", errors="ignore") if p.is_file() else ""
            except Exception:
                cache[path_str] = ""
        return cache[path_str]

    details = []
    verified = 0
    for item in claims:
        claim = item.get("claim", "")
        quote = item.get("verbatim_quote", "") or ""
        source = item.get("source", "") or ""
        article = item.get("article", "") or ""
        base = {"claim": claim, "quote": quote, "source": source, "article": article}

        if not quote.strip():
            details.append({**base, "status": "INVALID", "reason": "thiếu verbatim_quote"})
            continue
        short = _too_short(quote, min_quote_chars)
        if short:
            details.append({**base, "status": "INVALID", "reason": short})
            continue
        if re.match(r"^https?://", source):
            details.append({**base, "status": "INVALID",
                            "reason": "source là URL; lưu nội dung đã tải vào file (<research_dir>/sources/...) rồi trỏ tới file"})
            continue

        candidates = [source] if source else []
        for d in default_source_files or []:
            if d not in candidates:
                candidates.append(d)
        if not candidates:
            details.append({**base, "status": "INVALID", "reason": "thiếu source"})
            continue

        result = None
        for cand in candidates:
            text = read(cand)
            if not text:
                continue
            found, off = check_single_quote(text, quote, case_sensitive)
            if not found:
                continue
            if article:
                block = extract_article_block(text, article)
                if block is None:
                    result = {**base, "source": cand, "status": "WRONG_ARTICLE",
                              "reason": f"không tìm thấy tiêu đề '{article}' trong nguồn"}
                    continue
                in_block, _ = check_single_quote(block, quote, case_sensitive)
                if not in_block:
                    result = {**base, "source": cand, "status": "WRONG_ARTICLE",
                              "reason": f"trích dẫn có trong nguồn nhưng KHÔNG nằm trong {article}"}
                    continue
            result = {**base, "source": cand, "status": "VERIFIED", "match_offset": off}
            break

        if result is None:
            missing_files = [c for c in candidates if not read(c)]
            reason = "không tìm thấy nguyên văn trong nguồn"
            if missing_files:
                reason += f"; file rỗng/không tồn tại: {missing_files}"
            result = {**base, "status": "MISSING", "reason": reason, "searched_in": candidates}
        if result["status"] == "VERIFIED":
            verified += 1
        details.append(result)

    total = len(claims)
    confidence = round(verified / total, 3)
    return {
        "passes": confidence >= threshold,
        "confidence_score": confidence,
        "threshold": threshold,
        "total_claims": total,
        "verified_count": verified,
        "missing_count": total - verified,
        "details": details,
    }


def main():
    parser = argparse.ArgumentParser(description="AIWF Evidence Verifier (trích dẫn nguyên văn)")
    parser.add_argument("--source", type=str, help="File nguồn đã lưu trên máy (.txt/.md)")
    parser.add_argument("--quote", type=str, help="Câu trích dẫn nguyên văn")
    parser.add_argument("--article", type=str, default="", help="Điều/条 được viện dẫn, VD 'Điều 75' hoặc '第67条'")
    parser.add_argument("--claims", type=str, help="File JSON danh sách claims")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help="Tỷ lệ trích dẫn phải đạt (mặc định 1.0 = tất cả)")
    parser.add_argument("--min-chars", type=int, default=DEFAULT_MIN_QUOTE_CHARS,
                        help="Độ dài tối thiểu của trích dẫn (ký tự, không tính khoảng trắng/dấu câu)")
    parser.add_argument("--case-sensitive", action="store_true", help="Phân biệt chữ hoa/thường")
    args = parser.parse_args()

    if args.source and args.quote:
        res = verify_evidence(
            [{"claim": "cli", "verbatim_quote": args.quote, "source": args.source, "article": args.article}],
            threshold=1.0, case_sensitive=args.case_sensitive, min_quote_chars=args.min_chars)
        d = res["details"][0]
        if d["status"] == "VERIFIED":
            print(f"✅ VERIFIED: tìm thấy trích dẫn trong {args.source}" + (f" ({args.article})" if args.article else ""))
            sys.exit(0)
        print(f"❌ {d['status']}: {d.get('reason', '')} [{args.source}]", file=sys.stderr)
        sys.exit(2)

    if args.claims:
        p = Path(args.claims)
        if not p.is_file():
            print(f"❌ Không tìm thấy file claims: {args.claims}", file=sys.stderr)
            sys.exit(1)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ Lỗi đọc JSON claims: {e}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(data, list):
            print("❌ claims.json phải là một mảng JSON", file=sys.stderr)
            sys.exit(1)
        res = verify_evidence(data, threshold=args.threshold, case_sensitive=args.case_sensitive,
                              min_quote_chars=args.min_chars)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if res["passes"] else 2)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
