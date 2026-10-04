#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
linebreak.py — Điểm ngắt câu/dòng theo ngữ pháp (dùng chung cho segmenter và ASS/SRT).

Một điểm ngắt tốt nằm SAU dấu câu, TRƯỚC liên từ, tại khoảng lặng giọng nói, và
KHÔNG BAO GIỜ tách từ chức năng khỏi cụm của nó ("của / tôi", "the / checklist",
"説明 / します"). Hàm `break_cost` trả về chi phí: càng thấp càng nên ngắt.
"""

import re

MAJOR_PUNCT = re.compile(r'[.!?…。！？]["”’»」』)]?$')
MINOR_PUNCT = re.compile(r'[,;:、，；：]["”’»」』)]?$')

# Liên từ / từ mở mệnh đề: ngắt TRƯỚC chúng là tự nhiên
CONJ_BEFORE = {
    "vi": {"và", "nhưng", "hoặc", "hay", "vì", "nên", "để", "khi", "nếu", "mà", "thì", "rồi", "sau", "trước",
           "nhờ", "do", "tuy", "dù", "mặc", "bởi", "cho", "trong", "khiến", "giúp", "rằng",
           "bằng", "vào", "ở", "tại", "từ", "theo", "qua", "trên", "dưới", "với", "đến", "tới", "về"},
    "en": {"and", "but", "or", "because", "so", "which", "who", "that", "when", "while", "if", "although",
           "though", "since", "unless", "until", "where", "after", "before", "then", "to", "with", "for",
           "in", "on", "at", "from", "by", "how", "what", "why", "about", "into", "through", "without", "during"},
}
# Từ chức năng: KHÔNG được đứng cuối một dòng/phân đoạn
NO_END = {
    "vi": {"của", "các", "những", "một", "cho", "với", "để", "là", "được", "bị", "rất", "đã", "sẽ", "đang",
           "không", "và", "hoặc", "nhưng", "thì", "mà", "này", "cái", "con", "người", "từ", "tại", "về", "theo",
           "bằng", "trên", "dưới", "trong", "ngoài", "khi", "nếu", "vì", "do", "có", "phải", "cần", "hãy", "đừng"},
    "en": {"the", "a", "an", "of", "to", "in", "on", "at", "for", "with", "by", "from", "my", "your", "his",
           "her", "its", "our", "their", "this", "that", "these", "those", "and", "or", "but", "is", "are", "was",
           "were", "be", "will", "would", "can", "could", "should", "i", "we", "you", "they", "he", "she", "it",
           "not", "very", "so", "as", "than", "if", "when"},
}
# Tiếng Nhật: ngắt sau trợ từ / 、 là tự nhiên; giữa hai chữ Hán hoặc trước trợ động từ là sai
JA_GOOD_END = ("、", "。", "は", "が", "を", "に", "で", "と", "も", "へ", "から", "まで", "ので", "けど", "って", "て", "たら", "れば", "ながら")
JA_BAD_START = ("ます", "ました", "です", "でした", "し", "した", "する", "させ", "され", "ない", "た", "だ", "ん", "っ", "ょ", "ゃ", "ゅ", "ー", "、", "。")


def is_cjk(text):
    return any('一' <= ch <= '鿿' or '぀' <= ch <= 'ヿ' for ch in text)


def lang_of(text):
    if is_cjk(text):
        return "ja"
    if re.search(r'[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]', text.lower()):
        return "vi"
    return "en"


def _bare(w):
    return re.sub(r'^[\W_]+|[\W_]+$', '', w.lower())


def break_cost(left, right, gap=0.0, lang="en"):
    """Chi phí ngắt giữa token `left` (kết thúc phần trước) và `right` (bắt đầu phần sau)."""
    l, r = left.strip(), right.strip()
    if not l or not r:
        return 0.0
    if MAJOR_PUNCT.search(l):
        cost = 0.0
    elif MINOR_PUNCT.search(l):
        cost = 1.0
    elif lang == "ja":
        cost = 2.5 if l.endswith(JA_GOOD_END) else 7.0
        if r.startswith(JA_BAD_START):
            cost += 8.0
        if '一' <= l[-1] <= '鿿' and '一' <= r[0] <= '鿿':
            cost += 6.0                                     # đang ở giữa một từ Hán tự
    else:
        cost = 6.0
        if _bare(r) in CONJ_BEFORE.get(lang, set()):
            cost = 3.0
    if lang != "ja" and _bare(l) in NO_END.get(lang, set()):
        cost += 6.0                                         # treo từ chức năng cuối dòng
    if lang != "ja" and cost > 1.0:
        if l[:1].isupper() and r[:1].isupper():
            cost += 6.0                                     # giữa một tên riêng: "Tanaka / Logistics"
        if re.match(r'^\d[\d.,]*%?$', l):
            cost += 6.0                                     # số tách khỏi đơn vị: "15 / ngày"
    if gap >= 0.25:
        cost -= min(3.0, gap * 4)                           # khoảng lặng giọng nói là ranh giới tự nhiên
    return cost


def join_tokens(tokens, cjk=None):
    cjk = is_cjk("".join(tokens)) if cjk is None else cjk
    if cjk:
        return "".join(t.strip() for t in tokens).strip()
    return re.sub(r'\s+([,.:;?!…%])', r'\1', " ".join(t.strip() for t in tokens if t.strip())).strip()


def best_wrap(text, max_chars=42):
    """(dòng, chi phí) cho cách ngắt 2 dòng tốt nhất. Chi phí < 5 = ngắt tại ranh giới ngữ pháp thật."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text], 0.0
    lang = lang_of(text)
    tokens = list(text) if lang == "ja" else text.split(" ")
    if len(tokens) < 2:
        return [text], 99.0
    best, best_i = None, 1
    for i in range(1, len(tokens)):
        a, b = join_tokens(tokens[:i], lang == "ja"), join_tokens(tokens[i:], lang == "ja")
        over = max(0, len(a) - max_chars) + max(0, len(b) - max_chars)
        # dòng trên ngắn hơn hoặc bằng dòng dưới (kim tự tháp) được ưu tiên nhẹ
        balance = abs(len(a) - len(b)) / max(1, len(text)) * 6 + (0.5 if len(a) > len(b) else 0)
        left, right = (a, b) if lang == "ja" else (tokens[i - 1], tokens[i])   # tiếng Nhật: xét cả chuỗi (trợ từ nhiều ký tự)
        score = over * 4 + balance + break_cost(left, right, 0.0, lang)
        if best is None or score < best:
            best, best_i = score, i
    return [join_tokens(tokens[:best_i], lang == "ja"), join_tokens(tokens[best_i:], lang == "ja")], best


def wrap_balanced(text, max_chars=42, max_lines=2):
    """Ngắt một phụ đề thành các dòng cân bằng tại điểm ngắt ngữ pháp tốt nhất; tôn trọng '\\n' thủ công."""
    text = text.strip()
    if not text:
        return []
    if "\n" in text:
        out = []
        for part in text.split("\n"):
            out.extend(wrap_balanced(part, max_chars, max_lines))
        return out
    lines, _ = best_wrap(text, max_chars)
    if len(lines) == 2 and (len(lines[0]) > max_chars or len(lines[1]) > max_chars):
        out = []
        if len(lines[0]) > max_chars:
            out.extend(wrap_balanced(lines[0], max_chars, max_lines))
        else:
            out.append(lines[0])
        if len(lines[1]) > max_chars:
            out.extend(wrap_balanced(lines[1], max_chars, max_lines))
        else:
            out.append(lines[1])
        return out
    return lines
