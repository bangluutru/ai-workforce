#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
translation_qa.py — Kiểm định bản dịch EJV TRƯỚC khi xuất file (cổng chặn cứng).

Phát hiện những lỗi mà validate_json.py cũ bỏ lọt (bản dịch thật từng giao file "_ja.docx" có 3/863
đoạn tiếng Nhật, phần còn lại là tiếng Việt chèn vào do bộ xuất tự lấy ngôn ngữ khác bù chỗ trống):
  • THIẾU      ô dịch trống / placeholder
  • CHÉP GỐC   bản dịch y hệt câu nguồn (chưa dịch)
  • SAI CHỮ    'ja' không có kana/kanji; 'vn' câu dài không có dấu tiếng Việt; 'en' lẫn chữ Việt/Nhật
  • SỐ LIỆU    con số trong câu nguồn biến mất ở bản dịch
  • ĐỘ DÀI     bản dịch quá ngắn so với nguồn (dịch sót / tóm tắt) hoặc dài bất thường
  • CẤU TRÚC   số mục list / hàng-cột bảng lệch nhau
  • VĂN PHONG  '—' trong tiếng Việt
Exit 1 nếu có lỗi chặn (THIẾU, CHÉP GỐC, SAI CHỮ, CẤU TRÚC) ở ngôn ngữ đích được yêu cầu.

    python3 translation_qa.py --input merged_ejv.json --langs vn,ja [--source-lang en] [--json qa.json]
"""
import argparse
import json
import re
import sys
from collections import defaultdict

PLACEHOLDER = re.compile(r"^\s*(\[?(todo|tbd|chưa dịch|untranslated|translate|cần dịch)\]?|\.\.\.|…)\s*$", re.I)
JA = re.compile(r"[぀-ヿ一-鿿]")
_VI_CHARS = "ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹàáãèéìíòóõùúýỳ"
VI = re.compile("[" + _VI_CHARS + _VI_CHARS.upper() + "]")   # liệt kê tường minh: khoảng À-Ỹ + re.I khớp nhầm cả 's' (qua 'ſ')
WORD = re.compile(r"[^\W\d_]+", re.U)
NUM = re.compile(r"\d+(?:[.,]\d+)*")
BLOCKING = {"THIẾU", "CHÉP GỐC", "SAI CHỮ", "CẤU TRÚC"}
# tỉ lệ ký tự đích/nguồn hợp lý (rộng): dưới min → nghi dịch sót/tóm tắt
RATIO = {("en", "vn"): (0.75, 2.2), ("en", "ja"): (0.25, 1.1), ("vn", "en"): (0.5, 1.6), ("vn", "ja"): (0.2, 0.9),
         ("ja", "vn"): (1.2, 6.0), ("ja", "en"): (1.0, 5.5)}


def detect(text):
    if JA.search(text) and len(JA.findall(text)) > len(text) * 0.15:
        return "ja"
    return "vn" if VI.search(text) else "en"


def strings(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)]


def check_text(src, tgt, lang, src_lang, where, out):
    t = (tgt or "").strip()
    if not t or PLACEHOLDER.match(t):
        out.append(("THIẾU", where, f"ô '{lang}' trống")); return
    s = (src or "").strip()
    if s and lang != src_lang and t == s and len(WORD.findall(s)) >= 3:
        out.append(("CHÉP GỐC", where, f"'{lang}' y hệt câu nguồn: \"{s[:60]}\"")); return
    letters = len(WORD.findall(t))
    if lang == "ja" and letters >= 1 and not JA.search(t):
        out.append(("SAI CHỮ", where, f"'ja' không có chữ Nhật: \"{t[:60]}\""))
    elif lang in ("vn", "en") and len(JA.findall(t)) >= 4 and len(JA.findall(t)) > 0.3 * len(re.sub(r"\s", "", t)):
        out.append(("SAI CHỮ", where, f"'{lang}' phần lớn vẫn là chữ Nhật (chưa dịch): \"{t[:40]}\""))
    elif lang == "vn" and len(t.split()) >= 6 and not VI.search(t) and not JA.search(t):
        out.append(("SAI CHỮ", where, f"'vn' không có dấu tiếng Việt: \"{t[:60]}\""))
    elif lang == "en" and (VI.search(t) or len(JA.findall(t)) > 2):
        out.append(("SAI CHỮ", where, f"'en' lẫn chữ Việt/Nhật: \"{t[:60]}\""))
    if lang == "vn" and "—" in t:
        out.append(("VĂN PHONG", where, "'vn' có dấu '—'"))
    if s:
        import unicodedata
        sN, tN = unicodedata.normalize("NFKC", s), unicodedata.normalize("NFKC", t)   # ３０ = 30
        tD = re.sub(r"(?<=\d)[.,\s](?=\d{3}\b)", "", tN)                              # 1.000.000 = 1,000,000 = 1000000
        miss = [n for n in set(NUM.findall(sN)) if len(n) >= 2 and n not in tN and re.sub(r"[.,]", "", n) not in tD]
        if miss:
            out.append(("SỐ LIỆU", where, f"'{lang}' thiếu số {miss[:4]}"))
        lo_hi = RATIO.get((src_lang, lang))
        if lo_hi and len(s) >= 40:
            r = len(t) / len(s)
            if r < lo_hi[0]:
                out.append(("ĐỘ DÀI", where, f"'{lang}' ngắn bất thường ({r:.2f}× nguồn) — dịch sót/tóm tắt?"))
            elif r > lo_hi[1]:
                out.append(("ĐỘ DÀI", where, f"'{lang}' dài bất thường ({r:.2f}× nguồn)"))


def qa(blocks, langs, src_lang=None):
    issues = []
    if not src_lang:
        votes = defaultdict(int)
        for b in blocks[:200]:
            if b.get("text"):
                votes[detect(str(b["text"]))] += 1
        src_lang = max(votes, key=votes.get) if votes else None
    for i, b in enumerate(blocks):
        typ = b.get("type")
        if typ == "hr":
            continue
        where = f"#{i + 1}({typ})"
        src_field = b.get("text") if b.get("text") is not None else b.get(src_lang) if src_lang else None
        if typ in ("ul", "ol"):
            src_items = strings(b.get("items") or src_field)
            for lang in langs:
                items = strings(b.get(lang))
                if src_items and len(items) != len(src_items):
                    issues.append(("CẤU TRÚC", where, f"'{lang}' có {len(items)} mục, nguồn {len(src_items)}"))
                for k, it in enumerate(items):
                    check_text(src_items[k] if k < len(src_items) else "", it, lang, src_lang, f"{where}[{k + 1}]", issues)
                if not items:
                    issues.append(("THIẾU", where, f"list '{lang}' trống"))
        elif typ == "table":
            H, R = b.get("headers") or {}, b.get("rows") or {}
            sh = b.get("text_headers") or (H.get(src_lang) if isinstance(H, dict) else None)
            sr = b.get("text_rows") or (R.get(src_lang) if isinstance(R, dict) else None)
            for lang in langs:
                h, r = (H.get(lang) if isinstance(H, dict) else None), (R.get(lang) if isinstance(R, dict) else None)
                if not r and not h:
                    issues.append(("THIẾU", where, f"bảng '{lang}' trống")); continue
                if sr and r and (len(r) != len(sr) or any(len(x) != len(y) for x, y in zip(r, sr))):
                    issues.append(("CẤU TRÚC", where, f"bảng '{lang}' lệch hàng/cột so với nguồn"))
                if sh and h and len(h) != len(sh):
                    issues.append(("CẤU TRÚC", where, f"tiêu đề cột '{lang}' lệch số cột"))
                for ri, row in enumerate(r or []):
                    for ci, cell in enumerate(row):
                        src_cell = sr[ri][ci] if sr and ri < len(sr) and ci < len(sr[ri]) else ""
                        if str(cell).strip() or str(src_cell).strip():
                            check_text(str(src_cell), str(cell), lang, src_lang, f"{where}[{ri + 1},{ci + 1}]", issues)
        elif typ == "meta_table":
            for k, it in enumerate(b.get("items") or []):
                for key in ("label", "value"):
                    v = it.get(key) if isinstance(it, dict) else None
                    if isinstance(v, dict):
                        for lang in langs:
                            check_text(v.get(src_lang, ""), v.get(lang, ""), lang, src_lang, f"{where}[{k + 1}].{key}", issues)
        else:
            for lang in langs:
                check_text(str(src_field or ""), str(b.get(lang) or ""), lang, src_lang, where, issues)
    return src_lang, issues


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--langs", required=True, help="ngôn ngữ ĐÍCH thực sự được yêu cầu, ví dụ vn hoặc vn,ja")
    ap.add_argument("--source-lang", default=None, choices=["vn", "en", "ja"])
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    blocks = json.load(open(a.input, encoding="utf-8"))
    langs = [l.strip() for l in a.langs.split(",") if l.strip()]
    src_lang, issues = qa(blocks, langs, a.source_lang)
    by = defaultdict(list)
    for kind, where, msg in issues:
        by[kind].append(f"{where}: {msg}")
    n_blocks = sum(1 for b in blocks if b.get("type") != "hr")
    print(f"QA bản dịch — {n_blocks} khối · nguồn '{src_lang}' · đích {langs}")
    if not src_lang:
        print("  ℹ️  Không có trường 'text' (câu nguồn) → bỏ qua kiểm tra chép gốc/số liệu/độ dài. Truyền --source-lang để bật.")
    for lang in langs:
        bad = {w.split("(")[0] for k, w, m in issues if k in BLOCKING and f"'{lang}'" in m}
        print(f"  {lang}: {100 * (1 - len(bad) / max(1, n_blocks)):.1f}% khối đạt")
    for kind in ["THIẾU", "CHÉP GỐC", "SAI CHỮ", "CẤU TRÚC", "SỐ LIỆU", "ĐỘ DÀI", "VĂN PHONG"]:
        if by[kind]:
            tag = "✗" if kind in BLOCKING else "!"
            print(f"{tag} {kind}: {len(by[kind])}")
            for x in by[kind][:12]:
                print(f"    {x}")
    blocking = sum(len(by[k]) for k in BLOCKING)
    if a.json:
        json.dump({"source_lang": src_lang, "langs": langs, "blocks": n_blocks, "issues": [{"kind": k, "where": w, "msg": m} for k, w, m in issues]},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n{'✗ CHẶN XUẤT: ' + str(blocking) + ' lỗi phải sửa (dịch lại các khối trên).' if blocking else '✅ Không lỗi chặn. Xem lại cảnh báo SỐ LIỆU/ĐỘ DÀI trước khi xuất.'}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
