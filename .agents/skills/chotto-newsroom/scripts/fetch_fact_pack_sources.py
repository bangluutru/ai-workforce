#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_fact_pack_sources.py — Tải mọi nguồn trong Fact Pack về máy và kiểm từng trích dẫn tiếng Nhật
có NGUYÊN VĂN trong nguồn đó (Bước 6 → trước Bước 8).

Vì sao: validate-article-draft.py chỉ kiểm bài khớp Fact Pack; nó không biết Fact Pack có chép đúng
nguồn hay không. Script này đóng khe hở đó cho mọi 「trích dẫn」 trong Ma trận tuyên bố, cột
"Nguyên văn" của Sổ số liệu và Sổ điều luật (điều luật phải nằm đúng 第N条).

Chỉ HTTP GET trang công khai (.go.jp, .lg.jp, e-Gov API). Không gọi LLM API.

Cách dùng (từ thư mục workspace AIWF):
  python3 .agents/skills/chotto-newsroom/scripts/fetch_fact_pack_sources.py \
      --fact-pack "<output_dir>/fact-pack-<slug>.md"
  # Mặc định lưu vào <output_dir>/sources-<slug>/ (S01.txt, L01.txt, manifest.json). --offline để chỉ kiểm lại.

Tệp đính kèm (PDF/DOCX/XLSX/... — VD 別紙 PDF) đọc qua bộ chuyển đổi chung scripts/doc_ingest.py (OCR bật).
Trang SCAN không có lớp chữ: bản nháp OCR vẫn được lưu trong Sxx.txt nhưng nằm giữa
<!-- ocr-draft:start/end -->, nguồn bị gắn "unverifiable" trong manifest.json + dòng "# UNVERIFIABLE" đầu file;
trích dẫn chỉ khớp trong bản nháp OCR = CHƯA KIỂM CHỨNG (không tính là đạt). Ảnh trang ở _ingest/<Sxx>/ocr_pages/.

Mã thoát: 0 = mọi trích dẫn có nguyên văn; 2 = có trích dẫn không tìm thấy / nguồn tải hỏng / không đọc được
(mật khẩu...); 3 = không có lỗi nào khác nhưng còn trích dẫn chỉ khớp bản nháp OCR (nguồn scan) → đối chiếu ảnh
trang; 1 = lỗi đầu vào.
"""

import argparse
import hashlib
import html
import json
import re
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.harness.evidence_verifier import check_single_quote, extract_article_block  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from doc_ingest_bridge import (EXIT_OK, EXIT_PARTIAL, explain, ocr_page_paths, run_ingest,  # noqa: E402
                               sniff_kind, strip_md_inline)

DRAFT_START, DRAFT_END = "<!-- ocr-draft:start", "<!-- ocr-draft:end -->"
UNVERIFIABLE_HDR = "# UNVERIFIABLE:"
KNOWN_EXTS = {"pdf", "docx", "xlsx", "xlsb", "pptx", "doc", "xls", "ppt", "odt", "ods", "odp", "epub", "rtf", "html",
              "png", "jpg", "tiff", "gif", "bmp", "webp", "heic", "txt", "md", "csv"}

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
EGOV_API = "https://laws.e-gov.go.jp/api/2/law_data/{law_id}?response_format=xml"
OFFICIAL = re.compile(r"\.go\.jp|\.lg\.jp|e-gov\.go\.jp|pref\.[a-z]+\.jp|city\.[a-z.]+\.jp")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, "", b""
    except Exception as e:  # noqa: BLE001
        return 0, str(e), b""


def egov_text(xml):
    out = []
    for art in re.findall(r"<Article [^>]*>.*?</Article>", xml, flags=re.S):
        title = re.search(r"<ArticleTitle>([^<]*)</ArticleTitle>", art)
        body = re.sub(r"<ArticleCaption>.*?</ArticleCaption>|<ArticleTitle>.*?</ArticleTitle>", "", art, flags=re.S)
        body = re.sub(r"<ParagraphNum>([^<]*)</ParagraphNum>", r"\n\1 ", body)
        body = html.unescape(re.sub(r"<[^>]+>", "", body))
        out.append(f"\n{title.group(1) if title else ''} \n{body.strip()}")
    return "\n".join(out)


def to_text(body, ctype):
    raw = body.decode("utf-8", errors="ignore")
    m = re.search(r'charset=["\']?(shift_jis|sjis|euc-jp)', raw[:3000], re.I) or re.search(r"(shift_jis|euc-jp)", ctype, re.I)
    if m:
        raw = body.decode(m.group(1).lower().replace("sjis", "shift_jis"), errors="ignore")
    raw = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>|</td>|</th>", "\n", raw)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return "\n".join(ln for ln in (re.sub(r"[ \t　]+", " ", x).strip() for x in txt.splitlines()) if ln)


def is_html(body, ctype):
    head = body[:600].lstrip().lower()
    return "html" in ctype.lower() or head.startswith((b"<!doctype", b"<html", b"<?xml")) or b"<html" in head


def md_to_text(md):
    """source.md (doc_ingest) → chữ trơn theo dòng; ô bảng nối bằng khoảng trắng (trích theo ô: 「窓口 33,000 円」).
    GIỮ marker <!-- ocr-draft:start/end --> quanh bản nháp OCR để phần đó không được tính là nguyên văn."""
    out, in_warn = [], False
    for ln in md.replace("\r\n", "\n").split("\n"):
        st = ln.strip()
        if st.startswith(DRAFT_START) or st.startswith(DRAFT_END):
            out.append(st)
            continue
        if st.startswith("<!--") or st == "_(trang trống)_" or re.match(r"^!\[[^\]]*\]\([^)]*\)$", st):
            continue
        if st.startswith("> [!"):
            in_warn = True
            continue
        if in_warn and st.startswith(">"):
            continue
        in_warn = False
        if st.startswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", st.strip("|"))]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            st = "  ".join(c.replace("<br>", " ") for c in cells)
        st = re.sub(r"^#{1,6}\s+", "", st)
        out.append(strip_md_inline(st))
    return "\n".join(out).strip()


def verified_part(text):
    """Bỏ bản nháp OCR (chưa kiểm chứng) khỏi văn bản nguồn."""
    return re.sub(r"(?s)<!-- ocr-draft:start.*?(?:<!-- ocr-draft:end -->|\Z)", "\n", text)


def ingest_attachment(body, work):
    """Tệp đính kèm (PDF/Office/ảnh...) → (text, info) qua doc_ingest, OCR bật."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "source.bin"
        tmp.write_bytes(body)
        kind = sniff_kind(tmp)  # đặt đúng đuôi theo magic bytes (openpyxl từ chối đuôi .bin)
        ext = {"jpeg": "jpg", "text": "txt", "markdown": "md"}.get(kind, kind)
        if ext in KNOWN_EXTS:
            tmp = tmp.rename(tmp.with_suffix("." + ext))
        man = run_ingest(tmp, work, ocr=True)
    code = man.get("exit_code")
    info = {"format": man.get("detected_format"), "ingest_exit": code, "ingest_dir": str(work)}
    if code not in (EXIT_OK, EXIT_PARTIAL):
        info["error"] = explain(man, "chotto-newsroom").replace(tmp.name, "tệp tải về")
        return "", info
    if code == EXIT_PARTIAL:
        info.update(unverifiable=True, pages_needing_ocr=man.get("pages_needing_ocr") or [],
                    ocr_pages=ocr_page_paths(man))
    return md_to_text(man.get("source_md") or ""), info


def download(url, path):
    m = re.search(r"laws\.e-gov\.go\.jp/law/([0-9A-Za-z]{12,})", url)
    fetch_url = EGOV_API.format(law_id=m.group(1)) if m else url
    status, ctype, body = fetch(fetch_url)
    if status != 200 or not body:
        return {"url": url, "fetch_url": fetch_url, "status": status, "ok": False}
    extra, min_chars = {}, 200
    if m:
        text = egov_text(body.decode("utf-8", errors="ignore"))
    elif is_html(body, ctype):
        text = to_text(body, ctype)
    else:
        text, extra = ingest_attachment(body, path.parent / "_ingest" / path.stem)
        min_chars = 20  # 別紙 ngắn vẫn hợp lệ; trang JS rỗng chỉ gặp ở HTML
        if extra.get("error"):
            if path.exists():
                path.unlink()  # không để lại file cũ làm "nguồn" giả
            return {"url": url, "fetch_url": fetch_url, "status": status, "ok": False, **extra}
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    hdr = f"# SOURCE_URL: {url}\n# FETCH_URL: {fetch_url}\n# FETCHED_AT: {now}\n"
    if extra.get("unverifiable"):
        hdr += (f"{UNVERIFIABLE_HDR} trang {', '.join(map(str, extra['pages_needing_ocr']))} là SCAN; chữ nằm giữa hai dấu "
                "ocr-draft:start / ocr-draft:end là bản nháp OCR CHƯA KIỂM CHỨNG, không dùng làm nguyên văn. "
                f"Ảnh trang: {path.parent / '_ingest' / path.stem / 'ocr_pages'}\n")
    path.write_text(f"{hdr}\n{text}", encoding="utf-8")
    real = len(re.sub(r"\s", "", verified_part(text)))
    ok = real > min_chars or bool(extra.get("unverifiable") and text.strip())
    return {"url": url, "fetch_url": fetch_url, "status": status, "ok": ok,
            "chars": len(text), "sha256": hashlib.sha256(body).hexdigest(), "fetched_at": now,
            "official": bool(OFFICIAL.search(url)), **extra}


def section(fp, *titles):
    for m in re.finditer(r"(?m)^##\s+[^\n]*$", fp):
        if any(t.lower() in m.group(0).lower() for t in titles):
            nxt = re.search(r"(?m)^##\s+", fp[m.end():])
            return fp[m.end(): m.end() + nxt.start()] if nxt else fp[m.end():]
    return ""


def table_rows(text):
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                rows.append(cells)
    return rows


def source_registry(fp):
    reg = {}
    sec = section(fp, "NGUỒN", "SOURCE REGISTRY") or fp
    blocks = re.split(r"(?=\bS\d{2}\b)", sec)
    for b in blocks:
        m = re.match(r"(S\d{2})\b", b)
        u = re.search(r"https?://[^\s)>\]|]+", b)
        if m and u and m.group(1) not in reg:
            reg[m.group(1)] = u.group(0).rstrip(".,")
    return reg


def quotes_in(cell):
    q = re.findall(r"「([^」]+)」", cell)
    if q:
        return q
    c = cell.strip()
    if re.search(r"[぀-ヿ㐀-鿿]", c) and c not in ("(như trên)",):
        return [c]
    return []


def main():
    ap = argparse.ArgumentParser(description="Tải nguồn Fact Pack và kiểm nguyên văn trích dẫn")
    ap.add_argument("--fact-pack", required=True)
    ap.add_argument("--out-dir", default=None, help="Mặc định <thư mục fact pack>/sources-<slug>/")
    ap.add_argument("--offline", action="store_true", help="Không tải lại; chỉ kiểm với file đã có")
    a = ap.parse_args()

    fpp = Path(a.fact_pack).expanduser()
    if not fpp.is_file():
        print(f"❌ Không thấy Fact Pack {fpp}", file=sys.stderr)
        return 1
    fp = unicodedata.normalize("NFKC", fpp.read_text(encoding="utf-8", errors="ignore"))
    slug = re.sub(r"^fact-pack-", "", fpp.stem)
    out = Path(a.out_dir).expanduser() if a.out_dir else fpp.parent / f"sources-{slug}"
    out.mkdir(parents=True, exist_ok=True)

    reg = source_registry(fp)
    laws = {}
    law_rows = table_rows(section(fp, "SỔ ĐIỀU LUẬT", "LAW CITATIONS"))[1:]
    for r in law_rows:
        u = re.search(r"https?://laws\.e-gov\.go\.jp/\S+", " ".join(r))
        if u and r:
            laws[r[0]] = u.group(0).rstrip(".,|")
    if not reg:
        print("❌ Không đọc được Danh mục nguồn (Sxx + URL) trong Fact Pack.", file=sys.stderr)
        return 1

    mpath = out / "manifest.json"
    try:
        manifest = json.loads(mpath.read_text(encoding="utf-8")) if a.offline and mpath.exists() else {}
    except (OSError, ValueError):
        manifest = {}
    problems, unverified = [], []
    for sid, url in list(reg.items()) + list(laws.items()):
        path = out / f"{sid}.txt"
        if not a.offline or not path.exists():
            info = download(url, path)
            manifest[sid] = info
            if info.get("error"):
                problems.append(f"{sid}: KHÔNG ĐỌC ĐƯỢC tệp {url} — {info['error']}")
            elif not info["ok"]:
                problems.append(f"{sid}: tải hỏng ({info['status']}) {url}")
            elif not info.get("official"):
                problems.append(f"{sid}: {url} không phải nguồn .go.jp/.lg.jp; bài cần ít nhất một nguồn chính thức cho mỗi tuyên bố.")
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def full_text(sid):
        p = out / f"{sid}.txt"
        return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

    def text_of(sid):
        """Chỉ phần nguyên văn đáng tin (bỏ bản nháp OCR của trang scan)."""
        return verified_part(full_text(sid))

    def only_in_draft(sids, q, label):
        """Trích dẫn không khớp nguyên văn nhưng khớp bản nháp OCR → CHƯA KIỂM CHỨNG (không tính là đạt)."""
        hit = [s for s in sids if DRAFT_START in full_text(s) and check_single_quote(full_text(s), q)[0]]
        if hit:
            unverified.append(f"{label}: 「{q[:50]}」 chỉ có trong bản nháp OCR của {hit} (trang scan) — CHƯA KIỂM CHỨNG. "
                              f"Đối chiếu ảnh trang trong {out / '_ingest'}/<Sxx>/ocr_pages/, rồi thay bằng nguồn có lớp "
                              "chữ hoặc ghi rõ [CHƯA XÁC MINH] trong Fact Pack.")
        return bool(hit)

    def scan_hint(sids):
        scans = [s for s in sids if DRAFT_START in full_text(s)]
        return f" (nguồn {scans} là SCAN: đối chiếu ảnh trang trong {out / '_ingest'}/<Sxx>/ocr_pages/)" if scans else ""

    checked = 0
    # Ma trận tuyên bố: | Mã | Tuyên bố | Mã Nguồn | Trích dẫn | ...
    for r in table_rows(section(fp, "TUYÊN BỐ", "KEY CLAIMS"))[1:]:
        sids = [c for c in r if re.fullmatch(r"S\d{2}", c.strip("* "))]
        for cell in r:
            for q in re.findall(r"「([^」]+)」", cell):
                checked += 1
                srcs = [s.strip("* ") for s in sids] or list(reg)
                if not any(check_single_quote(text_of(s), q)[0] for s in srcs) and \
                        not only_in_draft(srcs, q, r[0]):
                    problems.append(f"{r[0]}: 「{q[:50]}」 không có nguyên văn trong {srcs}{scan_hint(srcs)}")
    # Sổ số liệu: | Mã | Nội dung | Giá trị | Nguồn | Vị trí | Nguyên văn |
    for r in table_rows(section(fp, "SỔ SỐ LIỆU", "NUMBER LEDGER"))[1:]:
        if len(r) < 6:
            continue
        sid = r[3].strip("* ")
        for q in quotes_in(r[5]):
            checked += 1
            if not check_single_quote(text_of(sid), q)[0] and not only_in_draft([sid], q, r[0]):
                problems.append(f"{r[0]}: nguyên văn 「{q[:50]}」 không có trong {sid} ({reg.get(sid, '?')}){scan_hint([sid])}")
    # Sổ điều luật: | Mã | Luật | Điều | Link | Nguyên văn |
    for r in law_rows:
        if len(r) < 5 or r[0] not in laws:
            continue
        txt = text_of(r[0])
        for q in quotes_in(r[4]):
            checked += 1
            q_clean = q.replace("…", "[...]")
            found, _ = check_single_quote(txt, q_clean)
            block = extract_article_block(txt, r[2]) if found else None
            if not found and only_in_draft([r[0]], q_clean, r[0]):
                continue
            if not found:
                problems.append(f"{r[0]}: nguyên văn điều luật 「{q[:50]}」 không có trong {laws[r[0]]}")
            elif block is None or not check_single_quote(block, q_clean)[0]:
                problems.append(f"{r[0]}: nguyên văn có trong luật nhưng KHÔNG nằm trong {r[2]}")

    print(f"Nguồn: {len(reg)} + điều luật: {len(laws)} → {out}")
    print(f"Đã kiểm {checked} trích dẫn.")
    if checked == 0:
        problems.append("Không có trích dẫn tiếng Nhật nào để kiểm: Ma trận tuyên bố/Sổ số liệu phải có nguyên văn.")
    for sid, info in manifest.items():
        if info.get("unverifiable"):
            print(f"  ⚠️  {sid}: nguồn SCAN (trang {info.get('pages_needing_ocr')}) — bản nháp OCR chưa kiểm chứng; "
                  f"ảnh trang: {', '.join(info.get('ocr_pages', [])[:3])}")
    for p in problems:
        print(f"  ❌ {p}")
    for u in unverified:
        print(f"  ⚠️  {u}")
    if problems:
        print("FAIL")
        return 2
    if unverified:
        print(f"CHƯA KIỂM CHỨNG: {len(unverified)} trích dẫn chỉ khớp bản nháp OCR (không tính là PASS).")
        return 3
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
