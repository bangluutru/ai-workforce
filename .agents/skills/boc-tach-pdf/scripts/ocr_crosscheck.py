#!/usr/bin/env python3
"""
ocr_crosscheck.py — Đối chiếu bản OCR của Agent (02.process/page_NNN.png.md) với một OCR ENGINE độc lập
(Apple Vision qua mac_ocr.swift; dự phòng Tesseract nếu có dữ liệu vie/jpn) để phát hiện:
  - SỐ LIỆU lệch (số tiền, ngày tháng, số hiệu) — ưu tiên cao nhất
  - TỪ lệch dấu tiếng Việt (tầng/tâng, thư/thự ...)
  - DÒNG Agent viết nhưng engine không thấy (nguy cơ bịa/nhầm)  -> agent_line_unsupported
  - DÒNG engine thấy nhưng Agent bỏ sót                         -> possible_omission
Mỗi cờ có ảnh crop phóng to trong 02.process/verify/ để Agent XEM LẠI bằng view_file.

Kết quả: 02.process/needs_verification.json
Giải quyết cờ: (a) sửa page_NNN.png.md rồi chạy lại; hoặc (b) xác nhận bản Agent đúng bằng cách ghi
02.process/verified.json  {"<flag_id>": "lý do / đã xem crop"}; hoặc (c) chạy --finalize để chèn
[CẦN XÁC MINH: ...] vào MD cho các cờ còn mở.

Usage:
  python3 ocr_crosscheck.py <processing_dir> [--pages 1,3-5] [--engine auto|vision|tesseract]
                            [--finalize] [--refresh]
Exit code: 0 = sạch / đã giải quyết / đã đánh dấu; 3 = còn cờ mở; 4 = không có engine; 2 = lỗi.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CJK_RE = re.compile(r"[぀-ヿ㐀-鿿豈-﫿ｦ-ﾟ]")
NUM_RE = re.compile(r"\d+(?:[.,/:\-]\d+)*%?")
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
VI_MARK_RE = re.compile(r"[ăâđêôơưàáạảãầấậẩẫằắặẳẵèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗờớợởỡùúụủũừứựửữỳýỵỷỹ]", re.I)


# ----------------------------------------------------------------------------- text utils
def nfkc(s: str) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFKC", s or ""))


def base_form(w: str) -> str:
    """Bỏ dấu tiếng Việt: dùng để nhận ra 2 từ chỉ khác dấu."""
    w = w.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", w) if not unicodedata.combining(c)).lower()


def strip_markdown(md: str) -> list[str]:
    """Trả về các dòng nội dung thuần (bỏ markup) của trang MD do Agent viết."""
    md = re.sub(r"<!--.*?-->", " ", md, flags=re.S)
    md = re.sub(r"\[CẦN XÁC MINH[^\]]*\]", " ", md)
    md = re.sub(r"\[Không đọc được[^\]]*\]", " ", md)
    md = re.sub(r"\[Hình minh họa:[^\]]*\]", " ", md)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)
    md = re.sub(r"<[^>]+>", " ", md)
    lines = []
    for raw in md.splitlines():
        s = raw.strip()
        if re.match(r"^\|?\s*:?-{3,}", s):  # dòng phân cách bảng
            continue
        s = re.sub(r"^#{1,6}\s+", "", s)
        s = s.replace("**", "").replace("__", "")
        s = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", s)
        s = s.replace("\\", " ")
        cells = [c.strip() for c in s.strip("|").split("|")] if "|" in s else [s]
        for c in cells:
            c = re.sub(r"^[-+]\s+", "", c).strip()
            if c and c != "---":
                lines.append(nfkc(c))
    return lines


def tokens(s: str) -> list[str]:
    """Token để so khớp: từ (chữ Latin/Việt, lowercase giữ dấu), số, và bigram cho chữ Nhật/Hán."""
    s = nfkc(s)
    out = [w.lower() for w in WORD_RE.findall(CJK_RE.sub(" ", s))]
    out += NUM_RE.findall(s)
    for run in re.findall(r"[぀-ヿ㐀-鿿豈-﫿ｦ-ﾟ]+", s):
        out += [run[i:i + 2] for i in range(max(1, len(run) - 1))]
    return out


def numbers(s: str) -> list[str]:
    return NUM_RE.findall(nfkc(s))


def cjk_ratio(s: str) -> float:
    chars = [c for c in s if not c.isspace()]
    return (sum(1 for c in chars if CJK_RE.match(c)) / len(chars)) if chars else 0.0


# ----------------------------------------------------------------------------- engines
def run_vision(images: list[Path], out_dir: Path) -> bool:
    swift = shutil.which("swift")
    if not swift or sys.platform != "darwin":
        return False
    cmd = [swift, str(SCRIPT_DIR / "mac_ocr.swift"), str(out_dir)] + [str(p) for p in images]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60 * max(5, len(images)))
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] Apple Vision lỗi: {e}")
        return False
    if res.returncode != 0:
        print(f"[WARN] mac_ocr.swift trả mã {res.returncode}: {res.stderr.strip()[:400]}")
    return all((out_dir / f"{p.name}.vision.json").exists() for p in images)


def tesseract_langs() -> list[str]:
    if not shutil.which("tesseract"):
        return []
    try:
        out = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout
        return [l.strip() for l in out.splitlines()[1:] if l.strip()]
    except Exception:  # noqa: BLE001
        return []


def run_tesseract(img: Path, out_json: Path, langs: list[str]) -> bool:
    passes = []
    for combo in (["vie", "eng"], ["jpn", "eng"]):
        use = [l for l in combo if l in langs]
        if not use or (combo[0] not in langs):
            continue
        res = subprocess.run(["tesseract", str(img), "stdout", "-l", "+".join(use), "--psm", "4", "tsv"],
                             capture_output=True, text=True)
        rows = [r.split("\t") for r in res.stdout.splitlines()[1:]]
        lines: dict = {}
        for r in rows:
            if len(r) < 12 or not r[11].strip():
                continue
            key = (r[2], r[3], r[4])
            x, y, w, h = map(int, r[6:10])
            e = lines.setdefault(key, {"text": [], "x0": x, "y0": y, "x1": x + w, "y1": y + h, "conf": []})
            e["text"].append(r[11]); e["conf"].append(float(r[10]))
            e["x0"] = min(e["x0"], x); e["y0"] = min(e["y0"], y); e["x1"] = max(e["x1"], x + w); e["y1"] = max(e["y1"], y + h)
        obs = [{"text": " ".join(e["text"]), "confidence": (sum(e["conf"]) / len(e["conf"])) / 100.0,
                "quad": [[e["x0"], e["y0"]], [e["x1"], e["y0"]], [e["x1"], e["y1"]], [e["x0"], e["y1"]]]}
               for e in lines.values()]
        passes.append({"languages": use, "missing_languages": [], "observations": obs})
    if not passes:
        return False
    from PIL import Image
    w, h = Image.open(img).size
    out_json.write_text(json.dumps({"engine": "tesseract", "image": str(img), "width": w, "height": h,
                                    "passes": passes}, ensure_ascii=False), encoding="utf-8")
    return True


# ----------------------------------------------------------------------------- geometry
def bbox(quad):
    xs = [p[0] for p in quad]; ys = [p[1] for p in quad]
    return min(xs), min(ys), max(xs), max(ys)


def iou(a, b):
    ax0, ay0, ax1, ay1 = a; bx0, by0, bx1, by1 = b
    ix = max(0, min(ax1, bx1) - max(ax0, bx0)); iy = max(0, min(ay1, by1) - max(ay0, by0))
    inter = ix * iy
    if inter <= 0:
        return 0.0
    return inter / ((ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter)


def merge_passes(data: dict) -> list[dict]:
    """Chọn lượt ngôn ngữ phù hợp cho TỪNG VÙNG CHỮ: vùng có chữ Nhật lấy lượt ja, còn lại lấy lượt vi."""
    passes = data.get("passes", [])
    if not passes:
        return []
    primary = passes[0]["observations"]
    others = [o for p in passes[1:] for o in p["observations"]]
    used_other = set()
    merged = []
    for o in primary:
        bb = bbox(o["quad"])
        best, best_i = None, 0.0
        for j, q in enumerate(others):
            v = iou(bb, bbox(q["quad"]))
            if v > best_i:
                best, best_i = j, v
        if best is not None and best_i > 0.3:
            used_other.add(best)
            alt = others[best]
            if cjk_ratio(alt["text"]) >= 0.2 and cjk_ratio(o["text"]) < 0.2:
                if VI_MARK_RE.search(o["text"]):
                    # Dòng trộn Việt + Nhật: giữ phần Việt của lượt vi + phần Nhật của lượt ja
                    cjk_part = " ".join(re.findall(r"[　-ヿ㐀-鿿豈-﫿＀-￯]+", alt["text"]))
                    latin_part = re.sub(r"\([^)]*\)$", "", o["text"]).strip()
                    merged.append({**o, "text": f"{latin_part} {cjk_part}".strip()})
                else:
                    merged.append(alt)
            else:
                merged.append(o)
        else:
            merged.append(o)
    for j, q in enumerate(others):
        if j not in used_other and cjk_ratio(q["text"]) >= 0.2:
            merged.append(q)
    return order_lines(merged)


def order_lines(obs: list[dict]) -> list[dict]:
    """Sắp thứ tự đọc theo đường chân chữ ĐÃ KHỬ NGHIÊNG (trang scan bị xoay vài độ vẫn đúng thứ tự)."""
    if not obs:
        return obs
    angles, heights = [], []
    for o in obs:
        (x0, y0), (x1, y1) = o["quad"][0], o["quad"][1]
        wdt = math.hypot(x1 - x0, y1 - y0)
        hgt = math.hypot(o["quad"][3][0] - x0, o["quad"][3][1] - y0)
        heights.append(hgt)
        if wdt > 4 * max(hgt, 1):
            angles.append(math.atan2(y1 - y0, x1 - x0))
    ang = sorted(angles)[len(angles) // 2] if angles else 0.0
    ca, sa = math.cos(-ang), math.sin(-ang)
    med_h = sorted(heights)[len(heights) // 2] or 10
    for o in obs:
        cx = sum(p[0] for p in o["quad"]) / 4; cy = sum(p[1] for p in o["quad"]) / 4
        o["_rx"], o["_ry"] = cx * ca - cy * sa, cx * sa + cy * ca
    obs.sort(key=lambda o: o["_ry"])
    lines, cur = [], [obs[0]]
    for o in obs[1:]:
        if abs(o["_ry"] - cur[-1]["_ry"]) < 0.6 * med_h:
            cur.append(o)
        else:
            lines.append(cur); cur = [o]
    lines.append(cur)
    out = []
    for ln in lines:
        out += sorted(ln, key=lambda o: o["_rx"])
    return out


# ----------------------------------------------------------------------------- comparison
def flag_id(page: int, kind: str, agent: str, engine: str) -> str:
    return hashlib.sha1(f"{page}|{kind}|{agent}|{engine}".encode("utf-8")).hexdigest()[:10]


def compare_page(page: int, agent_md: str, obs: list[dict]) -> tuple[list[dict], dict]:
    agent_lines = strip_markdown(agent_md)
    agent_text = "\n".join(agent_lines)
    eng_text = "\n".join(o["text"] for o in obs)
    a_tok, e_tok = Counter(tokens(agent_text)), Counter(tokens(eng_text))
    flags = []

    # 1) Số liệu: so sánh multiset, rồi ghép cặp số lệch gần giống nhau thành "number_mismatch"
    a_num, e_num = Counter(numbers(agent_text)), Counter(numbers(eng_text))
    digits = lambda n: re.sub(r"[.,]", "", n)  # noqa: E731
    only_a = list((a_num - e_num).elements())
    only_e = list((e_num - a_num).elements())
    def src_of(n):
        return next((o for o in obs if n in nfkc(o["text"])), None)
    for n in list(only_a):
        # cùng chữ số, khác dấu chấm/phẩy (3.750.5 vs 3.750,5)
        same = next((m for m in only_e if digits(m) == digits(n)), None)
        if same is not None:
            only_a.remove(n); only_e.remove(same)
            src = src_of(same)
            flags.append({"type": "number_format", "agent": n, "engine": same,
                          "context": src["text"] if src else "", "quad": src["quad"] if src else None})
    for n in list(only_a):
        best, score = None, 0.0
        for m in only_e:
            r = difflib.SequenceMatcher(None, digits(n), digits(m)).ratio()
            if r > score:
                best, score = m, r
        if best is not None and score >= 0.6:
            only_a.remove(n); only_e.remove(best)
            src = src_of(best)
            flags.append({"type": "number_mismatch", "agent": n, "engine": best,
                          "context": src["text"] if src else "", "quad": src["quad"] if src else None})
    for n in only_a:
        flags.append({"type": "number_not_seen_by_engine", "agent": n, "engine": "", "quad": None})
    for n in only_e:
        src = src_of(n)
        if len(re.sub(r"\D", "", n)) <= 1 and src is None:
            continue
        flags.append({"type": "number_missing_in_agent", "agent": "", "engine": n,
                      "context": src["text"] if src else "", "quad": src["quad"] if src else None})

    # 2) Từ lệch dấu: từ của Agent không có trong engine nhưng engine có từ cùng gốc khác dấu
    e_words = {w for w in e_tok if WORD_RE.fullmatch(w)}
    e_by_base: dict = {}
    for w in e_words:
        e_by_base.setdefault(base_form(w), set()).add(w)
    for w in sorted({w for w in a_tok if WORD_RE.fullmatch(w) and len(w) > 1}):
        if w in e_words:
            continue
        variants = e_by_base.get(base_form(w), set()) - {w}
        if variants:
            v = sorted(variants)[0]
            src = next((o for o in obs if v in nfkc(o["text"]).lower()), None)
            flags.append({"type": "diacritic_mismatch", "agent": w, "engine": v,
                          "context": src["text"] if src else "", "quad": src["quad"] if src else None})

    # 3) Dòng không được engine ủng hộ / dòng engine thấy mà Agent bỏ sót (so theo cặp từ liền kề, bỏ dấu)
    def grams(text: str) -> list[str]:
        t = [base_form(x) for x in tokens(text)]
        words = [x for x in t if not CJK_RE.search(x)]
        cjk = [x for x in t if CJK_RE.search(x)]
        return [f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1)] + cjk

    e_grams = Counter(g for o in obs for g in grams(o["text"]))
    a_grams = Counter(g for ln in agent_lines for g in grams(ln))

    def coverage(gs: list[str], bag: Counter) -> float:
        return (sum(1 for g in gs if bag.get(g)) / len(gs)) if gs else 1.0

    for ln in agent_lines:
        gs = grams(ln)
        if len(gs) >= 3 and coverage(gs, e_grams) < 0.5:
            flags.append({"type": "agent_line_unsupported", "agent": ln[:160], "engine": "", "quad": None})
    for o in obs:
        gs = grams(o["text"])
        if len(gs) >= 3 and o.get("confidence", 1) >= 0.3 and coverage(gs, a_grams) < 0.5:
            flags.append({"type": "possible_omission", "agent": "", "engine": o["text"][:160], "quad": o["quad"]})

    for f in flags:
        f["id"] = flag_id(page, f["type"], f.get("agent", ""), f.get("engine", ""))
        f["page"] = page

    a_all = sum(a_tok.values()) or 1
    stats = {
        "token_agreement": round(sum((a_tok & e_tok).values()) / a_all, 3),
        "agent_numbers": sum(a_num.values()), "engine_numbers": sum(e_num.values()),
        "agent_cjk_chars": len(CJK_RE.findall(agent_text)), "engine_cjk_chars": len(CJK_RE.findall(eng_text)),
    }
    return flags, stats


def save_crop(img_path: Path, quad, out_path: Path) -> str | None:
    if not quad:
        return None
    from PIL import Image
    im = Image.open(img_path)
    x0, y0, x1, y1 = bbox(quad)
    pad = max(12, int((y1 - y0) * 0.8))
    box = (max(0, int(x0 - pad)), max(0, int(y0 - pad)), min(im.width, int(x1 + pad)), min(im.height, int(y1 + pad)))
    crop = im.crop(box)
    if crop.height < 120:
        k = 120 / max(crop.height, 1)
        crop = crop.resize((int(crop.width * k), int(crop.height * k)))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out_path)
    return str(out_path)


def parse_pages(spec: str | None, available: list[int]) -> list[int]:
    if not spec:
        return available
    out = set()
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-"); out.update(range(int(a), int(b) + 1))
        elif part.strip():
            out.add(int(part))
    return [p for p in available if p in out]


def finalize(process_dir: Path, report: dict) -> int:
    """Chèn [CẦN XÁC MINH: ...] vào MD cho mọi cờ còn mở."""
    marked = 0
    for page_s, pdata in report["pages"].items():
        md_path = process_dir / f"page_{int(page_s):03d}.png.md"
        if not md_path.exists():
            continue
        md = md_path.read_text(encoding="utf-8")
        tail = []
        for f in pdata["flags"]:
            if f.get("resolved"):
                continue
            note = f.get("engine") or "engine không thấy"
            if f["type"] in ("number_not_seen_by_engine", "number_format", "number_mismatch", "diacritic_mismatch") and f["agent"]:
                pat = re.compile(r"(?<![\w.,])" + re.escape(f["agent"]) + r"(?![\w])")
                if f["type"] == "diacritic_mismatch":
                    pat = re.compile(r"(?<!\w)" + re.escape(f["agent"]) + r"(?!\w)", re.I)
                new, n = pat.subn(lambda m: f"{m.group(0)} [CẦN XÁC MINH: engine đọc \"{note[:60]}\"]", md, count=1)
                if n:
                    md = new; marked += 1; f["resolved"] = "marked"
                    continue
            if f["type"] == "agent_line_unsupported":
                tail.append(f"[CẦN XÁC MINH: engine không xác nhận dòng \"{f['agent'][:80]}\"]")
            else:
                tail.append(f"[CẦN XÁC MINH: có thể thiếu/lệch so với bản scan: \"{(f.get('engine') or f.get('context') or '')[:80]}\"]")
            f["resolved"] = "marked"; marked += 1
        if tail:
            md = md.rstrip() + "\n\n" + "\n\n".join(tail) + "\n"
        md_path.write_text(md, encoding="utf-8")
    return marked


def main() -> int:
    ap = argparse.ArgumentParser(description="Đối chiếu OCR của Agent với OCR engine độc lập")
    ap.add_argument("processing_dir")
    ap.add_argument("--pages", default=None, help="VD: 1,3-5 (mặc định: tất cả trang đã có MD)")
    ap.add_argument("--engine", default="auto", choices=["auto", "vision", "tesseract"])
    ap.add_argument("--refresh", action="store_true", help="Chạy lại engine kể cả khi đã có cache")
    ap.add_argument("--finalize", action="store_true", help="Chèn [CẦN XÁC MINH] cho các cờ còn mở")
    a = ap.parse_args()

    root = Path(a.processing_dir).resolve()
    input_dir, process_dir = root / "01.input", root / "02.process"
    eng_dir, verify_dir = process_dir / "ocr_engine", process_dir / "verify"
    eng_dir.mkdir(parents=True, exist_ok=True)
    md_pages = sorted(int(m.group(1)) for p in process_dir.glob("page_*.png.md")
                      if (m := re.match(r"page_(\d+)\.png\.md$", p.name)))
    if not md_pages:
        print("[FAIL] Chưa có page_NNN.png.md nào trong 02.process/ (Agent phải OCR trước).")
        return 2
    pages = parse_pages(a.pages, md_pages)
    images = {p: input_dir / f"page_{p:03d}.png" for p in pages}
    missing_img = [p for p, im in images.items() if not im.exists()]
    if missing_img:
        print(f"[FAIL] Thiếu ảnh gốc cho trang {missing_img} trong 01.input/")
        return 2

    todo = [images[p] for p in pages if a.refresh or not (eng_dir / f"{images[p].name}.vision.json").exists()]
    engine = "cache"
    if todo:
        ok = False
        if a.engine in ("auto", "vision"):
            print(f"[INFO] Apple Vision: {len(todo)} trang (2 lượt ngôn ngữ: vi + ja)...")
            ok = run_vision(todo, eng_dir); engine = "apple_vision"
        if not ok and a.engine in ("auto", "tesseract"):
            langs = tesseract_langs()
            if "vie" in langs or "jpn" in langs:
                print(f"[INFO] Tesseract ({'+'.join(l for l in langs if l in ('vie', 'jpn', 'eng'))})...")
                ok = all(run_tesseract(im, eng_dir / f"{im.name}.vision.json", langs) for im in todo)
                engine = "tesseract"
        if not ok:
            report = {"status": "engine_unavailable", "engine": None, "pages": {},
                      "message": ("Không có OCR engine đối chiếu (cần macOS + swift, hoặc tesseract có dữ liệu vie/jpn). "
                                  "Agent BẮT BUỘC làm vòng tự kiểm 2 lượt (SKILL.md Bước 2.3) và ghi kết quả vào "
                                  "02.process/selfcheck.json; mọi chỗ không chắc phải gắn [CẦN XÁC MINH].")}
            (process_dir / "needs_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print("[FAIL] " + report["message"])
            return 4

    verified_path = process_dir / "verified.json"
    verified = json.loads(verified_path.read_text(encoding="utf-8")) if verified_path.exists() else {}
    report = {"status": "open", "engine": engine, "pages": {}}
    open_count = 0
    for p in pages:
        data = json.loads((eng_dir / f"{images[p].name}.vision.json").read_text(encoding="utf-8"))
        obs = merge_passes(data)
        md = (process_dir / f"page_{p:03d}.png.md").read_text(encoding="utf-8")
        flags, stats = compare_page(p, md, obs)
        for k, f in enumerate(flags, 1):
            if f["id"] in verified:
                f["resolved"] = f"verified: {verified[f['id']]}"
            crop = save_crop(images[p], f.pop("quad", None), verify_dir / f"page_{p:03d}_{f['id']}.png")
            if crop:
                f["crop"] = crop
            if not f.get("resolved"):
                open_count += 1
        lang_note = [{"languages": ps["languages"], "missing": ps.get("missing_languages", [])} for ps in data.get("passes", [])]
        report["pages"][str(p)] = {"stats": stats, "engine_passes": lang_note,
                                   "engine_text": [o["text"] for o in obs], "flags": flags}

    if a.finalize and open_count:
        n = finalize(process_dir, report)
        print(f"[INFO] Đã chèn {n} dấu [CẦN XÁC MINH] vào MD.")
        open_count = 0
        report["status"] = "marked"
    else:
        report["status"] = "clean" if open_count == 0 else "open"
    report["open_flags"] = open_count
    out = process_dir / "needs_verification.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] Engine: {engine}. Báo cáo: {out}")
    for p in pages:
        pd = report["pages"][str(p)]
        opened = [f for f in pd["flags"] if not f.get("resolved")]
        print(f"  Trang {p}: token_agreement={pd['stats']['token_agreement']:.0%}  cờ mở={len(opened)}")
        for f in opened[:25]:
            print(f"    - [{f['id']}] {f['type']}: agent='{f.get('agent', '')[:50]}' engine='{f.get('engine', '')[:50]}'"
                  + (f"  crop={Path(f['crop']).name}" if f.get("crop") else ""))
    if open_count:
        print(f"[ACTION] Còn {open_count} cờ mở: xem crop trong {verify_dir}, sửa MD hoặc ghi xác nhận vào {verified_path}, "
              f"rồi chạy lại. Nếu vẫn không chắc: chạy lại với --finalize.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
