#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate-article-draft.py — Bộ kiểm định tự động bản thảo bài viết ChottoDay
Theo tiêu chuẩn kiến trúc Rule R4, R5 và quy chuẩn kỹ thuật ChottoDay.

Cách sử dụng:
    python3 scripts/validate-article-draft.py --input /path/to/article.js
    python3 scripts/validate-article-draft.py --dir ~/Downloads/AIWF_Output/
    python3 scripts/validate-article-draft.py --input bai.js --fact-pack fact-pack-bai.md
"""

import sys
import os
import re
import argparse
import unicodedata
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

# 3 Loại nguồn tin hợp lệ. Nguồn cũng khai bằng `type:` (không phải `sourceType:`),
# nên phải tách khỏi section type, nếu không `type: 'official'` bị báo là section lạ.
VALID_SOURCE_TYPES = {'official', 'primary', 'reference'}

# Trường mà ArticleRenderer.jsx thật sự đọc. Đúng type mà sai tên trường thì khối
# render ra rỗng, không báo lỗi: bản cũ của skill dạy `text:` cho đoạn văn và
# `detail:` cho bước, và nguồn dùng `name:` hiện ra "• ()" trên bài thật.
SECTION_REQUIRED_FIELD = {
    'intro': 'content',
    'paragraph': 'content',
    'note': 'content',
    'warning': 'content',
    'quote': 'content',
    'heading': 'text',
    'list': 'items',
    'steps': 'items',
    'example': 'items',
    'sources': 'items',
    'term': 'term',
    'toolCTA': 'toolId',
}

# Tên trường không tồn tại trong ChottoDay (schema cũ của skill). Viết vào là
# Studio báo "Thiếu `excerpt`" hoặc dữ liệu bị bỏ qua im lặng.
LEGACY_FIELDS = {
    'publishedDate': 'publishedAt',
    'lastUpdated': 'updatedAt',
    'verifiedDate': 'review.lastVerifiedAt / sources[].accessedAt',
    'sourceType': 'type',
    'relatedArticles': 'relatedArticleIds',
    'targetAudience': 'applicability.audience',
    'canonicalUrl': 'seo.canonical',
    'detail': 'text (trong steps)',
}

# Ảnh bìa bàn giao ở dạng WebP, tên bằng slug. Trên mức này là quên nén.
COVER_MAX_KB = 150

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
    m_slug = re.search(r"slug:\s*['\"`]([^'\"`]+)['\"`]", content)
    if m_slug:
        data['slug'] = m_slug.group(1)
        
    # Bóc tách title
    m_title = re.search(r"title:\s*['\"`]([^'\"`]+)['\"`]", content)
    if m_title:
        data['title'] = m_title.group(1)
        
    # Bóc tách category
    m_cat = re.search(r"category:\s*['\"`]([^'\"`]+)['\"`]", content)
    if m_cat:
        data['category'] = m_cat.group(1)
        
    # Bóc tách status
    m_status = re.search(r"status:\s*['\"`]([^'\"`]+)['\"`]", content)
    if m_status:
        data['status'] = m_status.group(1)
        
    # Bóc tách reviewer
    m_rev = re.search(r"reviewer:\s*['\"`]([^'\"`]+)['\"`]", content)
    if m_rev:
        data['reviewer'] = m_rev.group(1)
        
    # Bóc tách readingTime
    m_rt = re.search(r"readingTime:\s*(\d+)", content)
    if m_rt:
        data['readingTime'] = int(m_rt.group(1))

    # Bóc tách mọi `type:` theo thứ tự, kèm vị trí để cắt từng khối.
    all_types = [(m.group(1), m.start()) for m in re.finditer(r"\btype:\s*['\"`]([a-zA-Z0-9_]+)['\"`]", content)]
    data['section_blocks'] = []
    for i, (t, start) in enumerate(all_types):
        end = all_types[i + 1][1] if i + 1 < len(all_types) else len(content)
        if t not in VALID_SOURCE_TYPES:
            data['section_blocks'].append((t, content[start:end]))
    data['section_types'] = [t for t, _ in data['section_blocks']]
    data['source_types'] = [t for t, _ in all_types if t in VALID_SOURCE_TYPES]

    m_cover = re.search(r"coverImage:\s*['\"`]([^'\"`]+)['\"`]", content)
    if m_cover:
        data['coverImage'] = m_cover.group(1)

    return data


# ---------------------------------------------------------------------------
# Cổng đối chiếu Fact Pack
#
# Vì sao có: bài lương tối thiểu 2026 lên site với số Hyogo 1.174 (thật: 1.172),
# Fukuoka 1.115 (thật: 1.114), "từ 01/10 trên toàn quốc" (thật: 01/10 - 02/12 tùy
# tỉnh) và "Điều 119 Luật Tiêu chuẩn Lao động" (thật: Điều 40 Luật Lương tối
# thiểu). Không số nào trong đó có dòng tương ứng trong Fact Pack, nhưng không
# có gì bắt buộc phải có. Cổng này bắt buộc: số, ngày, điều luật trong bài phải
# truy được về Sổ số liệu / Sổ điều luật (standards/fact-pack-schema.md mục 7, 8).
#
# Bản kiểm thử 2026-10 cho thấy cổng cũ để lọt: số trong chuỗi "..." hoặc `...`
# (chỉ đọc chuỗi '...'), số đúng nhưng ghép sai ngữ cảnh (phí quầy ghi thành phí
# trực tuyến), thời hạn "14 ngày", ngày viết bằng chữ, "Điều N" không kèm tên luật.
# Bản này đọc MỌI chuỗi JS, kiểm cặp số + ngữ cảnh với từng dòng sổ, và buộc
# "Điều N" đứng cạnh tên luật có trong Sổ điều luật.
#
# Giới hạn thật: không kiểm được Fact Pack chép đúng nguồn. Việc đó là của
# scripts/fetch_fact_pack_sources.py (tải nguồn, kiểm nguyên văn) và người duyệt.
# ---------------------------------------------------------------------------

# Chuỗi trong .js là dữ liệu máy (URL, đường dẫn, id, ngày ISO) thì bỏ qua.
_MACHINE_LITERAL = re.compile(r"^(https?://|/)|^\d{4}-\d{2}-\d{2}$|^[a-z0-9-]+$")
_DATE_VN = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_DATE_WORDS = re.compile(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})(?:\s+năm\s+(\d{4}))?", re.IGNORECASE)
_DATE_DM = re.compile(r"(?:ngày|từ|đến|tới|trước|sau|hạn|hết)\s+(\d{1,2})/(\d{1,2})(?![/\d])", re.IGNORECASE)
_MONTH_YEAR = re.compile(r"tháng\s+(\d{1,2})/(\d{4})", re.IGNORECASE)
_UNIT_ALIASES = {
    "yên": ["yên", "円", "yen"], "¥": ["円", "yên", "yen"], "円": ["円", "yên"], "man": ["万", "man"],
    "%": ["%", "％"], "giờ": ["giờ", "時間", "時"], "phút": ["phút", "分"], "ngày": ["ngày", "日"],
    "tuần": ["tuần", "週"], "tháng": ["tháng", "か月", "ヶ月", "ヵ月", "カ月", "月"], "năm": ["năm", "年"],
    "người": ["người", "人", "名"], "lần": ["lần", "回"], "tuổi": ["tuổi", "歳"],
    "triệu": ["triệu", "百万"], "nghìn": ["nghìn", "千"],
}
_UNIT_RE = "|".join(sorted((re.escape(u) for u in _UNIT_ALIASES), key=len, reverse=True))
_NUM_UNIT = re.compile(rf"(?<![\w.,])(\d+(?:[.,]\d+)*)\s*({_UNIT_RE})(?!\w)", re.IGNORECASE)
_NUM_YEN_PREFIX = re.compile(r"[¥￥]\s*(\d+(?:[.,]\d+)*)")
_NUM_BIG = re.compile(r"(?<![\w.,])(\d{1,3}(?:[.,]\d{3})+|\d{3,})(?![\w])")
_LAW_REF = re.compile(r"Điều\s+(\d+)")
_COUNT_UNITS = {"ngày", "tuần", "tháng", "năm", "người", "lần", "giờ", "phút", "tuổi"}

# Từ vựng ngữ cảnh: cùng một phạm trù mà bài và dòng sổ mang giá trị khác nhau => ghép sai.
_PREFS = [
    ("hokkaido", "北海道"), ("aomori", "青森"), ("iwate", "岩手"), ("miyagi", "宮城"), ("akita", "秋田"),
    ("yamagata", "山形"), ("fukushima", "福島"), ("ibaraki", "茨城"), ("tochigi", "栃木"), ("gunma", "群馬"),
    ("saitama", "埼玉"), ("chiba", "千葉"), ("tokyo", "東京"), ("kanagawa", "神奈川"), ("niigata", "新潟"),
    ("toyama", "富山"), ("ishikawa", "石川"), ("fukui", "福井"), ("yamanashi", "山梨"), ("nagano", "長野"),
    ("gifu", "岐阜"), ("shizuoka", "静岡"), ("aichi", "愛知"), ("mie", "三重"), ("shiga", "滋賀"),
    ("kyoto", "京都"), ("osaka", "大阪"), ("hyogo", "兵庫"), ("nara", "奈良"), ("wakayama", "和歌山"),
    ("tottori", "鳥取"), ("shimane", "島根"), ("okayama", "岡山"), ("hiroshima", "広島"), ("yamaguchi", "山口"),
    ("tokushima", "徳島"), ("kagawa", "香川"), ("ehime", "愛媛"), ("kochi", "高知"), ("fukuoka", "福岡"),
    ("saga", "佐賀"), ("nagasaki", "長崎"), ("kumamoto", "熊本"), ("oita", "大分"), ("miyazaki", "宮崎"),
    ("kagoshima", "鹿児島"), ("okinawa", "沖縄"),
]
_QUALIFIERS = {
    "channel": [("WINDOW", [r"tại quầy", r"\bquầy\b", r"trực tiếp tại", r"窓口"]),
                ("ONLINE", [r"trực tuyến", r"\bonline\b", r"オンライン"])],
    "oldnew": [("OLD", [r"mức cũ", r"\bcũ\b", r"trước đây", r"改定前", r"現行"]),
               ("NEW", [r"mức mới", r"\bmới\b", r"改定後", r"引き上げ後"])],
    "pref": [(r[0].upper(), [rf"\b{r[0]}\b", r[1]]) for r in _PREFS],
}


def _nfkc(s):
    return unicodedata.normalize("NFKC", s)


_KANJI_D = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def _kanji_to_int(s):
    total, cur = 0, 0
    for ch in s:
        if ch in _KANJI_D:
            cur = _KANJI_D[ch]
        else:
            total += (cur or 1) * {"十": 10, "百": 100, "千": 1000}[ch]
            cur = 0
    return total + cur


def _kanji_numbers_to_arabic(text):
    return re.sub(r"[〇一二三四五六七八九十百千]+", lambda m: str(_kanji_to_int(m.group(0))), text)


def _norm_number(tok):
    """1.280 / 1,280 / 1280 -> '1280'; 0,5 -> '0.5'."""
    tok = tok.strip()
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", tok):
        return re.sub(r"[.,]", "", tok)
    return tok.replace(",", ".")


def js_string_literals(js):
    """Mọi chuỗi '...', "..." và `...` (bỏ ${...}) ngoài comment, theo thứ tự xuất hiện."""
    out, i, n = [], 0, len(js)
    while i < n:
        c = js[i]
        if js.startswith("//", i):
            j = js.find("\n", i)
            i = n if j < 0 else j
            continue
        if js.startswith("/*", i):
            j = js.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c in "'\"`":
            q, j, buf = c, i + 1, []
            while j < n and js[j] != q:
                if js[j] == "\\" and j + 1 < n:
                    buf.append(js[j + 1])
                    j += 2
                    continue
                if q == "`" and js.startswith("${", j):
                    depth, j = 1, j + 2
                    while j < n and depth:
                        depth += {"{": 1, "}": -1}.get(js[j], 0)
                        j += 1
                    buf.append(" ")
                    continue
                buf.append(js[j])
                j += 1
            out.append("".join(buf))
            i = j + 1
            continue
        i += 1
    return out


def _text_literals(js):
    return [lit for lit in js_string_literals(js) if lit and not _MACHINE_LITERAL.search(lit)]


def _keys(text):
    t = _nfkc(text).lower()
    keys = {}
    for cat, opts in _QUALIFIERS.items():
        found = {name for name, pats in opts if any(re.search(p, t, re.IGNORECASE) for p in pats)}
        if found:
            keys[cat] = found
    durs = set()
    for num, unit in re.findall(r"(\d+)\s*(năm|tháng|年|か月|ヶ月|ヵ月|カ月)", t):
        durs.add(num + ("y" if unit in ("năm", "年") else "m"))
    if durs:
        keys["duration"] = durs
    return keys


def _compatible(article_keys, row_keys):
    for cat, vals in article_keys.items():
        if cat in row_keys and not (vals & row_keys[cat]):
            return False
    return True


def _section(fp, *titles):
    """Nội dung mục '## N. <tiêu đề>' đầu tiên có chứa một trong các titles."""
    for m in re.finditer(r"(?m)^##\s+[^\n]*$", fp):
        if any(t.lower() in m.group(0).lower() for t in titles):
            nxt = re.search(r"(?m)^##\s+", fp[m.end():])
            return fp[m.end(): m.end() + nxt.start()] if nxt else fp[m.end():]
    return ""


def _table_rows(section_text):
    rows = []
    for line in section_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return rows


def parse_ledgers(fp):
    num_rows, law_rows = [], []
    rows = _table_rows(_section(fp, "SỔ SỐ LIỆU", "NUMBER LEDGER"))
    if rows:
        head = [h.lower() for h in rows[0]]
        has_header = any("giá trị" in h or "phép tính" in h or "kết quả" in h for h in head)
        body = rows[1:] if has_header else rows
        i_val = next((i for i, h in enumerate(head) if "giá trị" in h or "kết quả" in h), 2)
        for r in body:
            if r and r[0].lower() in ("mã",):
                i_val = next((i for i, h in enumerate([c.lower() for c in r]) if "giá trị" in h or "kết quả" in h), i_val)
                continue
            text = " ".join(c for j, c in enumerate(r) if j != 3)  # bỏ cột Nguồn (S01) khỏi ngữ cảnh
            value = r[i_val] if i_val < len(r) else ""
            num_rows.append({"id": r[0], "value": value, "text": _nfkc(" | ".join(r)), "ctx": text})
    for r in _table_rows(_section(fp, "SỔ ĐIỀU LUẬT", "LAW CITATIONS"))[1:]:
        if len(r) < 3:
            continue
        art = _nfkc(r[2])
        m = re.search(r"第\s*([〇一二三四五六七八九十百千\d]+)\s*条", art) or re.search(r"(\d+)", art)
        if not m:
            continue
        num = m.group(1)
        num = num if num.isdigit() else str(_kanji_to_int(num))
        aliases = {a.strip() for a in re.split(r"[()（）/;,、]", r[1]) if len(a.strip()) >= 3}
        aliases |= {re.sub(r"^Luật\s+", "", a, flags=re.I) for a in aliases if a.lower().startswith("luật ")}
        law_rows.append({"id": r[0], "article": num, "aliases": {a for a in aliases if len(a) >= 3},
                         "link": " ".join(r[3:4])})
    return num_rows, law_rows


def _clauses(text):
    return [c for c in re.split(r"\.(?!\d)|[;:()\n]|,(?!\d)|\s+và\s+|\s+còn\s+", text) if c.strip()]


def check_fact_pack(content, slug, fact_pack_path, published_year=None):
    errors, warnings = [], []
    fp_path = Path(fact_pack_path)
    if not fp_path.exists():
        errors.append(
            f"Không thấy Fact Pack '{fp_path}'. Mọi số và điều luật trong bài phải truy được về đó "
            f"(Bước 6). Chỉ đường khác bằng --fact-pack.")
        return errors, warnings

    fp_raw = fp_path.read_text(encoding="utf-8", errors="ignore")
    fp = _nfkc(fp_raw)
    fp_arabic = _kanji_numbers_to_arabic(fp)
    num_rows, law_rows = parse_ledgers(fp)
    if not num_rows:
        errors.append("Fact Pack không có Sổ số liệu (mục '## 7. SỔ SỐ LIỆU' dạng bảng). Mọi số trong bài phải có dòng ở đó.")
    ledger_text = " ".join(r["text"] for r in num_rows)
    ledger_numbers = {_norm_number(t) for t in re.findall(r"\d{1,3}(?:[.,]\d{3})+|\d+(?:\.\d+)?", ledger_text)}
    fp_numbers = {_norm_number(t) for t in re.findall(r"\d{1,3}(?:[.,]\d{3})+|\d+(?:\.\d+)?", fp_arabic)}
    year = published_year or (re.search(r"publishedAt:\s*['\"`](\d{4})", content) or [None, None])[1]

    missing, mismatched, missing_dates, law_errors = {}, {}, {}, []
    for lit in _text_literals(content):
        lit = _nfkc(lit)
        scan = lit
        # Ngày
        for d, mth, y in _DATE_VN.findall(scan):
            iso = f"{y}-{int(mth):02d}-{int(d):02d}"
            if iso not in fp:
                missing_dates.setdefault(f"{d}/{mth}/{y}", iso)
        scan = _DATE_VN.sub(" ", scan)
        for m in _DATE_WORDS.finditer(scan):
            y = m.group(3) or year
            iso = f"{y}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
            if iso not in fp:
                missing_dates.setdefault(m.group(0), iso)
        scan = _DATE_WORDS.sub(" ", scan)
        for m in _DATE_DM.finditer(scan):
            iso = f"{year}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
            if year and iso not in fp:
                missing_dates.setdefault(m.group(0), iso)
        scan = _DATE_DM.sub(" ", scan)
        for mth, y in _MONTH_YEAR.findall(scan):
            ym = f"{y}-{int(mth):02d}"
            if ym not in fp:
                missing_dates.setdefault(f"tháng {mth}/{y}", ym)
        scan = _MONTH_YEAR.sub(" ", scan)

        # Điều luật: phải đứng cạnh tên luật có trong Sổ điều luật
        for m in _LAW_REF.finditer(scan):
            n = m.group(1)
            window = scan[max(0, m.start() - 90): m.end() + 90]
            rows = [r for r in law_rows if r["article"] == n]
            if not rows:
                law_errors.append(f"Bài nhắc 'Điều {n}' nhưng Sổ điều luật không có dòng 第{n}条. Tra trên e-Gov và chép nguyên văn.")
            elif not any(any(a.lower() in window.lower() for a in r["aliases"]) for r in rows):
                names = "; ".join(sorted(a for r in rows for a in r["aliases"]))[:120]
                law_errors.append(f"'Điều {n}' không có tên luật đi kèm (…{window.strip()[:70]}…). Ghi rõ tên luật như trong Sổ điều luật: {names}.")
        scan = _LAW_REF.sub(" ", scan)

        # Số
        for clause in _clauses(scan):
            ckeys = _keys(clause)
            toks = []
            for m in _NUM_UNIT.finditer(clause):
                toks.append((m.group(1), m.group(2).lower()))
            for t in _NUM_YEN_PREFIX.findall(clause):
                toks.append((t, "yên"))
            unit_spans = {t for t, _ in toks}
            for t in _NUM_BIG.findall(clause):
                if t not in unit_spans:
                    toks.append((t, ""))
            for tok, unit in toks:
                norm = _norm_number(tok)
                ctx = clause.strip()[:90]
                if unit in _COUNT_UNITS:
                    aliases = _UNIT_ALIASES.get(unit, [unit])
                    pat = rf"(?<![\d.,]){re.escape(norm)}\s*(?:{'|'.join(map(re.escape, aliases))})"
                    if not re.search(pat, _kanji_numbers_to_arabic(ledger_text), re.IGNORECASE):
                        missing.setdefault(f"{tok} {unit}", ctx)
                    continue
                pool = ledger_numbers if num_rows else fp_numbers
                if norm not in pool:
                    missing.setdefault(tok, ctx)
                    continue
                rows = [r for r in num_rows if _norm_number(r["value"]) == norm or
                        norm in {_norm_number(x) for x in re.findall(r"\d{1,3}(?:[.,]\d{3})+|\d+(?:\.\d+)?", r["value"])}]
                if rows and ckeys and not any(_compatible(ckeys, _keys(r["ctx"])) for r in rows):
                    desc = "; ".join(f"{r['id']}: {r['ctx'][:50]}" for r in rows[:3])
                    mismatched.setdefault(tok, (ctx, ckeys, desc))

    for tok, ctx in sorted(missing.items()):
        errors.append(f"Số '{tok}' không có trong Sổ số liệu (…{ctx}…). Thêm dòng kèm vị trí trong nguồn, hoặc bỏ khỏi bài.")
    for tok, (ctx, ck, desc) in sorted(mismatched.items()):
        kk = ", ".join(f"{k}={'/'.join(sorted(v))}" for k, v in ck.items())
        errors.append(f"Số '{tok}' ghép sai ngữ cảnh: bài viết '{ctx}' ({kk}) nhưng Sổ số liệu ghi giá trị này cho [{desc}].")
    for vn, iso in sorted(missing_dates.items()):
        errors.append(f"Ngày '{vn}' không có trong Fact Pack dưới dạng '{iso}'. Ghi ngày vào Sổ số liệu.")
    if law_errors and "laws.e-gov.go.jp" not in fp:
        errors.append("Bài dẫn điều luật nhưng Fact Pack không có link e-Gov (laws.e-gov.go.jp). Tra nguyên văn trên e-Gov (Sổ điều luật).")
    errors.extend(dict.fromkeys(law_errors))

    m_stage = re.search(r"Giai đoạn pháp lý:?\**\s*:?\s*([^\n]+)", fp)
    if m_stage and "答申" in m_stage.group(1):
        if not re.search(r"đề xuất|dự kiến", content):
            warnings.append("Fact Pack ghi giai đoạn 答申 (mới là đề xuất) nhưng bài không có chữ 'đề xuất' hay 'dự kiến'. Đừng viết như đã có hiệu lực chắc chắn.")

    return errors, warnings

def validate_article_file(file_path, fact_pack=None):
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
                
    # 6b. Đúng tên trường mà bộ render đọc
    for st, block in parsed.get('section_blocks', []):
        need = SECTION_REQUIRED_FIELD.get(st)
        if need and not re.search(r"\b" + need + r"\s*:", block):
            errors.append(f"Section '{st}' thiếu trường '{need}:'. Bộ render ChottoDay đọc '{need}', thiếu là khối hiện ra RỖNG.")
        if st == 'sources' and re.search(r"\bname\s*:", block):
            errors.append("Khối 'sources' dùng 'name:'. Bộ render in 'title (organization)'; dùng 'name' thì dòng nguồn hiện '• ()'. Đổi thành title + organization.")

    # 6c. Tên trường không tồn tại trong ChottoDay
    if not re.search(r"\bexcerpt\s*:", content):
        errors.append("Thiếu 'excerpt:'. ChottoDay dùng 'excerpt' (không phải 'description'); Studio chặn bài thiếu excerpt.")
    for old_name, new_name in LEGACY_FIELDS.items():
        if re.search(r"\b" + old_name + r"\s*:", content):
            errors.append(f"Trường '{old_name}:' không tồn tại trong ChottoDay. Dùng '{new_name}'.")

    # 7. Kiểm tra nguồn tin chính thức (Official Sources)
    source_types = parsed.get('source_types', [])
    if 'official' not in source_types:
        warnings.append("Khuyến nghị bài viết phải có ít nhất 1 nguồn `type: 'official'` (.go.jp hoặc cơ quan nhà nước).")
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

    # 10. Ảnh bìa: WebP, tên bằng slug, file có thật cạnh bản thảo
    if slug:
        expected = f"/images/featured/{slug}.webp"
        cover = parsed.get('coverImage')
        if not cover:
            errors.append(f"Thiếu 'coverImage'. Phải là '{expected}'.")
        elif cover != expected:
            errors.append(f"coverImage là '{cover}', phải là '{expected}' (WebP, tên bằng slug, không '-cover'/'-pattern').")
        cover_file = path.parent / f"{slug}.webp"
        if not cover_file.exists():
            errors.append(f"Không thấy ảnh bìa '{cover_file}'. Bước 9 phải xuất '<output_dir>/{slug}.webp'.")
        else:
            head = cover_file.read_bytes()[:12]
            if not (head[:4] == b'RIFF' and head[8:12] == b'WEBP'):
                errors.append(f"'{cover_file.name}' không phải WebP thật (chỉ đổi đuôi?). Chuyển bằng Pillow, xem chotto-image-rules.md mục 1.")
            size_kb = cover_file.stat().st_size / 1024
            if size_kb > COVER_MAX_KB:
                warnings.append(f"Ảnh bìa {size_kb:.0f} KB, trên mức {COVER_MAX_KB} KB. Nén lại (quality 80).")
        for stray in ('jpg', 'jpeg', 'png'):
            if (path.parent / f"{slug}-cover.{stray}").exists() or (path.parent / f"{slug}.{stray}").exists():
                warnings.append(f"Còn ảnh gốc .{stray} cạnh bản thảo. Xoá đi để người đăng không chọn nhầm.")

    # 11. Cổng đối chiếu Fact Pack
    if slug:
        fp_path = Path(fact_pack) if fact_pack else path.parent / f"fact-pack-{slug}.md"
        fp_errors, fp_warnings = check_fact_pack(content, slug, fp_path)
        errors.extend(fp_errors)
        warnings.extend(fp_warnings)

    is_pass = len(errors) == 0
    return is_pass, errors, warnings

def main():
    parser = argparse.ArgumentParser(description="Kiểm tra bản thảo bài viết ChottoDay theo chuẩn R4, R5.")
    parser.add_argument("--input", "-i", help="Đường dẫn đến file .js cần kiểm tra")
    parser.add_argument("--dir", "-d", help="Đường dẫn thư mục chứa các file .js cần kiểm tra")
    parser.add_argument("--fact-pack", "-f", help="Fact Pack để đối chiếu (mặc định: fact-pack-<slug>.md cạnh file .js)")
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
        is_pass, errors, warnings = validate_article_file(t, args.fact_pack)
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
