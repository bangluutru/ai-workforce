#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mixed_lang.py — Đọc câu tiếng Việt có chèn từ/cụm tiếng Anh (Luật R7: engine dùng chung).

Vấn đề: VieNeu chỉ đọc theo âm tiết tiếng Việt nên "Facebook", "marketing" bị đọc lệch.
Cách xử lý: tách câu thành các đoạn Việt / Anh -> đoạn Việt đọc bằng VieNeu, đoạn Anh bằng Kokoro
(offline, qua dub_engine -> tts) -> cắt lặng hai đầu, cân âm lượng, ghép lại thành 1 file.

Giới hạn đã biết (không giấu):
  * Giọng Kokoro khác âm sắc với giọng VieNeu; đoạn Anh ngắn nên chỉ giảm chứ không xóa được độ lệch.
  * Nhận diện "từ Anh" dựa trên âm vị học tiếng Việt (không dấu + không hợp cấu trúc âm tiết) + từ điển
    ngoại lệ nhỏ; từ Anh trùng hệt âm tiết Việt không dấu (vd "ban") sẽ bị coi là tiếng Việt.
    Ghi đè được bằng english_words / vietnamese_words.

API:
    split_mixed(text, english_words=(), vietnamese_words=()) -> [(lang, text), ...]
    has_english(text, ...) -> bool
    synthesize_mixed(lines, gender, voice, work, takes, verify, log, ...) -> (res, used_voice)
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
import unicodedata
from typing import Dict, Iterable, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

_VN_DIACRITICS = set(
    "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
)

# Âm tiết Việt KHÔNG dấu: [phụ âm đầu][nguyên âm][phụ âm cuối]
_ONSET = r"(?:ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|[bcdghklmnpqrstvx])?"
_NUCLEUS = r"(?:ieu|yeu|oai|oay|uai|uay|ai|ao|au|ay|eo|ia|iu|oa|oe|oi|ua|ui|uy|a|e|i|o|u|y)"
_CODA = r"(?:ch|ng|nh|c|m|n|p|t)?"
_VN_SYLLABLE = re.compile(rf"^{_ONSET}{_NUCLEUS}{_CODA}$")

# Từ Anh phổ biến TRÙNG cấu trúc âm tiết Việt không dấu (nên phải liệt kê tay)
_EN_COLLISIONS = {"chat", "chip", "top", "net", "pin", "hot", "pop", "tip", "map", "set"}

_TOKEN = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*|\d+[^\W\d_]*|[^\w\s]|\s+|\d+", re.UNICODE)
_WORD = re.compile(r"^[^\W\d_]+(?:['’\-][^\W\d_]+)*$", re.UNICODE)
_ACRONYM = re.compile(r"^[A-Z]{2,6}$")
_MIXED_ALNUM = re.compile(r"^(?=.*\d)(?=.*[A-Za-z])[A-Za-z0-9]+$")
_TRAIL_PUNCT = re.compile(r"[,.;:!?…]+$")


def _is_vietnamese_word(tok: str, vietnamese_words: Iterable[str]) -> bool:
    low = tok.lower()
    if low in {w.lower() for w in vietnamese_words}:
        return True
    if any(ch in _VN_DIACRITICS for ch in low):
        return True
    return bool(_VN_SYLLABLE.match(low)) and low not in _EN_COLLISIONS


def _classify(tok: str, english_words: Iterable[str], vietnamese_words: Iterable[str]) -> str:
    """'en' | 'vi' | 'other' (dấu câu, khoảng trắng, số thuần)."""
    if tok.isspace() or not any(c.isalnum() for c in tok):
        return "other"
    if tok.lower() in {w.lower() for w in english_words}:
        return "en"
    if _ACRONYM.match(tok):
        return "en"                       # SEO, CEO, OK... đọc theo tên chữ cái tiếng Anh
    if _MIXED_ALNUM.match(tok) and not tok.isdigit():
        return "en"                       # 4K, iOS17, mp4
    if tok.isdigit():
        return "other"
    if not _WORD.match(tok):
        return "other"
    return "vi" if _is_vietnamese_word(tok, vietnamese_words) else "en"


def split_mixed(text: str, english_words: Iterable[str] = (), vietnamese_words: Iterable[str] = ()) -> List[Tuple[str, str]]:
    """Tách câu thành các đoạn [('vi','...'), ('en','...')]. Từ 'other' bám theo đoạn đang mở."""
    text = unicodedata.normalize("NFC", str(text or ""))
    english_words = list(english_words)
    vietnamese_words = list(vietnamese_words)
    toks = _TOKEN.findall(text)
    segs: List[List] = []   # [lang, [tokens]]
    pending_other: List[str] = []
    for tok in toks:
        kind = _classify(tok, english_words, vietnamese_words)
        if kind == "other":
            pending_other.append(tok)
            continue
        if segs and segs[-1][0] == kind:
            segs[-1][1].extend(pending_other + [tok])
        else:
            if segs:
                # dấu câu/khoảng trắng nằm giữa 2 đoạn: dấu câu đóng đoạn trước, còn lại thuộc đoạn sau
                lead = []
                for p in pending_other:
                    if not p.isspace() and not lead and p in ",.;:!?…)":
                        segs[-1][1].append(p)
                    else:
                        lead.append(p)
                segs.append([kind, lead + [tok]])
            else:
                segs.append([kind, pending_other + [tok]])
        pending_other = []
    if segs:
        segs[-1][1].extend(pending_other)
    out = []
    for lang, tk in segs:
        s = " ".join("".join(tk).split())
        if s:
            out.append((lang, s))
    return out


def has_english(text: str, english_words: Iterable[str] = (), vietnamese_words: Iterable[str] = ()) -> bool:
    return any(l == "en" for l, _ in split_mixed(text, english_words, vietnamese_words))


def _spell_acronyms(seg: str) -> str:
    """'SEO' -> 'S E O' để Kokoro đọc tên chữ cái; từ thường giữ nguyên."""
    return " ".join(". ".join(w) + "." if _ACRONYM.match(re.sub(r"[^\w]", "", w)) else w for w in seg.split())


# ---------------------------------------------------------------- phiên âm (chế độ mặc định)
# Ghép giọng (splice) nghe thiếu tự nhiên -> mặc định viết lại từ Anh thành phiên âm Việt để VieNeu đọc
# TRỌN câu một lượt, cùng giọng, cùng ngữ điệu. Từ không có trong từ điển được báo lại, không đoán.
PHONETIC: Dict[str, str] = {
    "facebook": "phây búc", "youtube": "diu túp", "tiktok": "tích tóc", "instagram": "in sờ ta gram",
    "google": "gu gồ", "chatgpt": "chát gi pi ti", "marketing": "ma két ting", "click": "clích",
    "link": "linh", "download": "đao lốt", "upload": "úp lốt", "file": "phai", "app": "ép",
    "website": "oép sai", "web": "oép", "online": "on lai", "offline": "óp lai", "email": "i meo",
    "game": "ghêm", "video": "vi đi âu", "content": "con ten", "brand": "bren", "digital": "đi gi tồ",
    "design": "đi zai", "designer": "đi zai nơ", "team": "tim", "business": "bít nịt", "feedback": "phít béc",
    "post": "pốt", "like": "lai", "share": "sê", "fanpage": "phan pết", "livestream": "lai trim",
    "hashtag": "hát tát", "landing": "len đinh", "page": "pết", "logo": "lô gô", "slogan": "sờ lô gần",
    "banner": "ben nơ", "ads": "át", "sale": "sên", "free": "phri", "button": "bắt tơn", "demo": "đê mô",
    "iphone": "ai phôn", "android": "an đroi", "ios": "ai ốt", "chat": "chát", "shop": "sóp",
    "shopee": "sốp pi", "lazada": "la za đa", "zalo": "da lô", "messenger": "mét sin giơ", "inbox": "in bóc",
    "comment": "com men", "follow": "pho lâu", "follower": "pho lâu ơ", "trend": "trên", "viral": "vai rồ",
    "startup": "start úp", "software": "sóp quây", "hardware": "hát quây", "cloud": "clao", "data": "đây ta",
    "server": "sơ vơ", "code": "cốt", "coding": "cô đing", "update": "úp đết", "setup": "sét úp",
    "login": "lốc in", "password": "pát quớt", "account": "ơ cao", "profile": "pờ rô phai", "dashboard": "đét bót",
    "report": "ri pót", "workflow": "quớc phlâu", "workspace": "quớc sờ pết", "meeting": "mi ting",
    "deadline": "đét lai", "project": "pờ rô dếch", "manager": "ma na giơ", "leader": "li đơ",
    "sales": "sên", "customer": "cát tơ mơ", "service": "sơ vít", "support": "sơ pót", "hotline": "hót lai",
    "voucher": "vao chơ", "combo": "com bô", "premium": "pờ ri mi âm", "vip": "vi ai pi", "smart": "smát",
    "ok": "ô kê", "okay": "ô kê", "cta": "xi ti ây", "seo": "ét i âu", "ai": "ây ai", "ceo": "xi i âu",
    "kpi": "ca pê i", "roi": "a âu ai", "pdf": "pi đi ép", "usb": "diu ét bi", "wifi": "quai phai",
    "4k": "bốn ca", "hd": "ết đi", "pr": "pi a", "ui": "diu ai", "ux": "diu ích", "api": "ây pi ai",
    "pitch": "pít", "deck": "đéc", "slide": "sờ lai", "template": "tem plết", "style": "sờ tai",
    "minimal": "mi ni mồ", "motion": "mô sần", "graphics": "gờ ráp phíc", "kinetic": "ki nét tích",
    "typography": "tai pó gờ ra phi", "reveal": "ri vồ", "feature": "phi chơ", "cards": "các", "card": "các",
    "chotto": "chốt tô", "chottoday": "chốt tô đây", "balancera": "ba lan xê ra",
}
_LETTER = {"a": "ây", "b": "bi", "c": "xi", "d": "đi", "e": "i", "f": "ép", "g": "gi", "h": "ết", "i": "ai",
           "j": "giây", "k": "kây", "l": "eo", "m": "em", "n": "en", "o": "âu", "p": "pi", "q": "kiu",
           "r": "a", "s": "ét", "t": "ti", "u": "diu", "v": "vi", "w": "đấp bồ liu", "x": "ích", "y": "quai", "z": "di"}


def phonetic_respell(text: str, extra: Optional[Dict[str, str]] = None, vietnamese_words: Iterable[str] = (),
                     english_words: Iterable[str] = ()) -> Tuple[str, List[str]]:
    """
    Thay từ Anh bằng phiên âm Việt. Trả (văn bản đọc, danh sách từ Anh CHƯA có phiên âm).
    Từ viết tắt viết hoa chưa có trong từ điển được đọc theo tên chữ cái (ESG -> ét-ê-gi...).
    `extra`: {từ: cách đọc} của người dùng, ưu tiên cao nhất.
    """
    lex = dict(PHONETIC)
    lex.update({k.lower(): v for k, v in (extra or {}).items()})
    english_words = list(english_words)
    vietnamese_words = list(vietnamese_words)
    text = unicodedata.normalize("NFC", str(text or ""))
    unknown: List[str] = []
    out = []
    toks = _TOKEN.findall(text)
    i = 0
    while i < len(toks):
        tok = toks[i]
        # cụm hai từ trong từ điển (vd "landing page" tách riêng từng từ vẫn đọc đúng)
        kind = _classify(tok, english_words, vietnamese_words)
        low = tok.lower()
        if low in lex and (kind == "en" or low in {k.lower() for k in (extra or {})}):
            out.append(lex[low])
        elif kind == "en":
            if _ACRONYM.match(tok):
                out.append(" ".join(_LETTER[c.lower()] for c in tok))
            else:
                out.append(tok)
                unknown.append(tok)
        else:
            out.append(tok)
        i += 1
    return " ".join("".join(out).split()).replace(" ,", ",").replace(" .", "."), unknown


# ---------------------------------------------------------------- ghép âm thanh
def _trim(arr, sr, thresh_db=-45.0, keep_ms=15):
    import numpy as np
    if arr.size == 0:
        return arr
    th = 10 ** (thresh_db / 20.0) * max(1e-9, float(np.max(np.abs(arr))))
    idx = np.where(np.abs(arr) > th)[0]
    if idx.size == 0:
        return arr
    keep = int(sr * keep_ms / 1000)
    return arr[max(0, idx[0] - keep): min(arr.size, idx[-1] + 1 + keep)]


def _rms(arr):
    import numpy as np
    return float(np.sqrt(np.mean(np.square(arr)))) if arr.size else 0.0


def _fade(arr, sr, ms=12):
    import numpy as np
    n = min(int(sr * ms / 1000), arr.size // 2)
    if n > 0:
        ramp = np.linspace(0.0, 1.0, n, dtype=arr.dtype)
        arr[:n] *= ramp
        arr[-n:] *= ramp[::-1]
    return arr


def _concat(parts, sr, gap_ms=45, punct_gap_ms=220):
    """parts: [(lang, array, trailing_punct_bool)] -> mảng đã cân âm lượng EN theo VI."""
    import numpy as np
    vi_rms = [ _rms(a) for l, a, _ in parts if l == "vi" and a.size ]
    ref = float(np.median(vi_rms)) if vi_rms else 0.0
    out = []
    for i, (lang, a, punct) in enumerate(parts):
        a = _trim(a.astype("float32"), sr)
        if lang == "en" and ref > 0 and _rms(a) > 0:
            g = min(2.0, max(0.5, ref / _rms(a)))      # ±6 dB
            a = a * g
        a = _fade(a.copy(), sr)
        out.append(a)
        if i < len(parts) - 1:
            ms = punct_gap_ms if punct else gap_ms
            out.append(np.zeros(int(sr * ms / 1000), dtype="float32"))
    return np.concatenate(out) if out else np.zeros(0, dtype="float32")


# ---------------------------------------------------------------- tổng hợp
def synthesize_mixed(lines, gender="female", voice=None, work=".", takes=2, verify=True,
                     log=print, english_words=(), vietnamese_words=(), max_cer=0.08):
    """
    lines: [{"key","text"}] (tiếng Việt, có thể chèn từ Anh).
    Trả ({key: {path, dur, cer, heard, engine, take, segments}}, giọng Việt thực dùng).
    Câu không có từ Anh được đọc nguyên văn bằng VieNeu như cũ (không đổi hành vi).
    """
    import bootstrap  # noqa: F401  (R7)
    import dub_engine
    from ffmpeg_tools import SR, decode, encode, duration  # noqa: F401

    os.makedirs(work, exist_ok=True)
    plain, mixed = [], {}
    for ln in lines:
        segs = split_mixed(ln["text"], english_words, vietnamese_words)
        if any(l == "en" for l, _ in segs):
            mixed[ln["key"]] = (ln, segs)
        else:
            plain.append(ln)

    results: Dict[str, dict] = {}
    used = voice
    if plain:
        r, used = dub_engine.synthesize(plain, "vi", voice, gender, os.path.join(work, "vi_plain"),
                                        takes=takes, verify=verify, max_cer=max_cer, log=log)
        results.update(r)
    if not mixed:
        return results, used

    vi_items, en_items, key_of = [], [], {}
    for k, (ln, segs) in mixed.items():
        for j, (lang, txt) in enumerate(segs):
            sk = f"{k}_s{j:02d}"
            body = _TRAIL_PUNCT.sub("", txt) if lang == "en" else txt
            body = _spell_acronyms(body) if lang == "en" else body
            if not any(c.isalnum() for c in body):
                continue
            (en_items if lang == "en" else vi_items).append({"key": sk, "text": body})
            key_of[(k, j)] = sk

    log(f"   🌐 Câu chèn từ Anh: {len(mixed)} câu, {len(en_items)} đoạn Anh (Kokoro) + {len(vi_items)} đoạn Việt (VieNeu)")
    vres, vused = ({}, used)
    if vi_items:
        vres, vused = dub_engine.synthesize(vi_items, "vi", voice, gender, os.path.join(work, "vi_seg"),
                                            takes=takes, verify=verify, max_cer=max_cer, log=log)
    eres, _ = dub_engine.synthesize(en_items, "en", None, gender, os.path.join(work, "en_seg"),
                                    takes=1, verify=verify, max_cer=0.5, log=log)
    used = vused or used

    for k, (ln, segs) in mixed.items():
        parts, desc = [], []
        for j, (lang, txt) in enumerate(segs):
            sk = key_of.get((k, j))
            if not sk:
                continue
            src = (eres if lang == "en" else vres).get(sk)
            if not src:
                raise RuntimeError(f"Không tổng hợp được đoạn {lang} '{txt}' (câu {k})")
            parts.append((lang, decode(src["path"]), bool(_TRAIL_PUNCT.search(txt))))
            desc.append({"lang": lang, "text": txt, "cer": src.get("cer")})
        sr = SR
        audio = _concat(parts, sr)
        h = hashlib.sha1(ln["text"].encode()).hexdigest()[:12]
        outp = os.path.join(work, f"mixed_{h}.wav")
        encode(audio, outp)
        cers = [d["cer"] for d in desc if d.get("cer") is not None]
        results[k] = {"path": outp, "dur": round(len(audio) / sr, 3), "cer": round(max(cers), 3) if cers else 0.0,
                      "heard": None, "engine": "VieNeu+Kokoro (mixed vi/en)", "take": 1, "segments": desc}
    return results, used


if __name__ == "__main__":
    import json
    t = " ".join(sys.argv[1:]) or "Chúng tôi dùng Facebook và YouTube cho marketing."
    print(json.dumps(split_mixed(t), ensure_ascii=False))
