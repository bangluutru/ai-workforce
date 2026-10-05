#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_vn_source.py — Tải văn bản quy phạm pháp luật Việt Nam từ nguồn CHÍNH THỐNG và lưu thành
file text trong <research_dir>/sources/ để evidence_verifier.py đối chiếu nguyên văn.

Chỉ đọc (HTTP GET) trang công khai; không gửi dữ liệu. Không gọi LLM API.

Cách dùng (chạy từ thư mục workspace AIWF):
  # Trang văn bản trên Công báo (tự tìm file .docx/.pdf đính kèm):
  python3 .agents/skills/tu-van-phap-luat/scripts/fetch_vn_source.py \
      --url "https://congbao.chinhphu.vn/van-ban/luat-so-76-2025-qh15-45505.htm" \
      --out-dir "<research_dir>/sources" --name luat-76-2025-qh15

  # File người dùng cung cấp (khi nguồn web bị chặn 403) — PDF/DOCX/DOC/ODT/RTF/HTML/TXT (cả bảng mã cũ
  # TCVN3/VNI/CP1258), đọc bằng bộ chuyển đổi chung scripts/doc_ingest.py:
  python3 .agents/skills/tu-van-phap-luat/scripts/fetch_vn_source.py \
      --file "~/Downloads/59-2020-QH14.pdf" --out-dir "<research_dir>/sources" --name luat-59-2020-qh14
  (Bản chuyển đổi đầy đủ + ảnh trang scan nằm ở <research_dir>/_ingest/<name>/, KHÔNG nằm trong sources/.)

Mã thoát:
  0 = đã lưu <out-dir>/<name>.txt
  3 = BỊ CHẶN (403/Cloudflare/captcha)  → áp dụng giao thức 403 trong SKILL.md
  4 = Trang chỉ là khung JavaScript / không có nội dung Điều → thử nguồn chính thống khác
  2 = (--file) KHÔNG ĐỌC ĐƯỢC: mật khẩu / DRM / tệp hỏng / rỗng / không hỗ trợ → hỏi người dùng bản khác; không lưu gì
  5 = (--file) PDF/ảnh SCAN không có lớp chữ (toàn bộ hoặc một phần) → KHÔNG lưu bản nháp OCR làm nguồn;
      đọc ảnh trang trong _ingest/<name>/ocr_pages/, số hoá bằng skill boc-tach-pdf rồi chạy lại --file trên bản kết quả
  6 = thiếu phụ thuộc (thông báo nói cần cài gì)
  1 = lỗi khác
"""

import argparse
import hashlib
import html
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from doc_ingest_bridge import (EXIT_MISSING_DEP, EXIT_PARTIAL, EXIT_UNREADABLE, explain,  # noqa: E402
                               ocr_page_paths, run_ingest, sniff_kind, strip_md_inline)

SKILL = "tu-van-phap-luat"
RC_UNREADABLE, RC_SCAN, RC_MISSING_DEP = 2, 5, 6

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
BLOCK_MARKERS = ("Just a moment", "Attention Required", "cf-browser-verification", "Enable JavaScript and cookies",
                 "captcha", "Access denied")
OFFICIAL_HOSTS = ("congbao.chinhphu.vn", "congbaocdn.chinhphu.vn", "vanban.chinhphu.vn", "datafiles.chinhphu.vn",
                  "cdnchinhphu.vn", "vbpl.vn", "chinhphu.vn", ".gov.vn", "quochoi.vn")


def fetch(url: str, timeout: int = 60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "vi,en;q=0.8"})
    import ssl
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", e.read() if e.fp else b"", url
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e) or (hasattr(e, "reason") and isinstance(e.reason, ssl.SSLCertVerificationError)):
            ctx = ssl._create_unverified_context()
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                    return r.status, r.headers.get("Content-Type", ""), r.read(), r.geturl()
            except urllib.error.HTTPError as e2:
                return e2.code, e2.headers.get("Content-Type", "") if e2.headers else "", e2.read() if e2.fp else b"", url
        raise


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</h\d>|</li>", "\n", raw)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in txt.splitlines()]
    return "\n".join(ln for ln in lines if ln)


class IngestError(RuntimeError):
    """Tệp không lấy được chữ đáng tin. rc: mã thoát; text: phần có lớp chữ thật (khi scan một phần)."""

    def __init__(self, msg: str, rc: int, text: str = "", man: dict | None = None):
        super().__init__(msg)
        self.rc, self.text, self.man = rc, text, man or {}


_TABLE_SEP = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$")


def md_to_plain(md: str) -> str:
    """source.md của doc_ingest → chữ trơn GIỮ DÒNG cho evidence_verifier: bỏ marker trang, ảnh, cảnh báo,
    BỎ HẲN bản nháp OCR (chưa kiểm chứng); bỏ định dạng Markdown (#, **, \\.) để trích dẫn khớp nguyên văn."""
    out, in_draft, in_warn = [], False, False
    for ln in md.replace("\r\n", "\n").split("\n"):
        st = ln.strip()
        if st.startswith("<!--"):
            in_draft = ("ocr-draft:start" in st) or (in_draft and "ocr-draft:end" not in st)
            continue
        if in_draft:
            continue
        if st.startswith("> [!"):
            in_warn = True
            continue
        if in_warn and st.startswith(">"):
            continue
        in_warn = False
        if _TABLE_SEP.match(st) or re.match(r"^!\[[^\]]*\]\([^)]*\)$", st) or st == "_(trang trống)_":
            continue
        if st.startswith("|") and st.endswith("|"):
            st = " | ".join(c.strip() for c in re.split(r"(?<!\\)\|", st.strip("|"))).replace("<br>", " ")
        st = re.sub(r"^#{1,6}\s+", "", st)
        st = re.sub(r"^[-*+]\s+", "", st)
        st = re.sub(r"\\([.\-+()\[\]!>~`])", r"\1", strip_md_inline(st))
        out.append(st)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def file_to_text(path: Path, work_dir: Path) -> tuple[str, dict]:
    """Đọc mọi định dạng qua doc_ingest (bridge). Trả (chữ trơn, manifest) hoặc ném IngestError."""
    man = run_ingest(path, work_dir, ocr=True)
    code = man.get("exit_code")
    if code == EXIT_MISSING_DEP:
        raise IngestError(explain(man, SKILL), RC_MISSING_DEP, man=man)
    if code == EXIT_UNREADABLE:
        raise IngestError(explain(man, SKILL), RC_UNREADABLE, man=man)
    text = md_to_plain(man.get("source_md") or "")
    if code == EXIT_PARTIAL:
        raise IngestError(explain(man, SKILL), RC_SCAN, text=text, man=man)
    if len(re.sub(r"\s", "", text)) == 0:
        raise IngestError(f"[{SKILL}] {path.name}: đọc được 0 ký tự — tệp rỗng hoặc chỉ có hình. "
                          "Hỏi người dùng bản có chữ (PDF/DOCX từ Công báo).", RC_UNREADABLE, man=man)
    return text, man


def find_attachments(page_html: str, base: str):
    links = re.findall(r'href="([^"]+)"', page_html)
    out = []
    for raw in links:
        u = html.unescape(raw)
        low = urllib.parse.unquote(u).lower()
        for ext, rank in ((".docx", 0), (".pdf", 1), (".doc", 2)):
            if low.endswith(ext):
                out.append((rank, urllib.parse.urljoin(base, u), ext))
                break
    out.sort(key=lambda x: x[0])
    return out


def looks_blocked(status: int, body: bytes) -> bool:
    if status in (401, 403, 429, 503):
        return True
    head = body[:5000].decode("utf-8", errors="ignore")
    return any(m.lower() in head.lower() for m in BLOCK_MARKERS) and len(body) < 20000


def has_articles(text: str) -> bool:
    return len(re.findall(r"(?m)^\W*Điều\s+\d+\s*[\.:]", text)) >= 1


def save(out_dir: Path, name: str, text: str, meta: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.txt"
    header = "".join(f"# {k}: {v}\n" for k, v in meta.items())
    path.write_text(header + "\n" + text, encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="Tải/chuyển VBQPPL chính thống thành text cho evidence_verifier")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="Trang văn bản (congbao.chinhphu.vn, vanban.chinhphu.vn, vbpl.vn) hoặc link .pdf/.docx")
    src.add_argument("--file", help="File người dùng cung cấp: .pdf/.docx/.doc/.odt/.rtf/.html/.txt (qua doc_ingest)")
    ap.add_argument("--out-dir", required=True, help="<research_dir>/sources")
    ap.add_argument("--name", required=True, help="Tên file, VD luat-59-2020-qh14")
    args = ap.parse_args()

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    out_dir = Path(args.out_dir).expanduser()

    ingest_root = out_dir.parent / "_ingest"
    if args.file:
        p = Path(args.file).expanduser()
        if not p.is_file():
            print(f"❌ Không thấy file: {p}", file=sys.stderr)
            return 1
        meta = {"SOURCE": f"user-file:{p.name}", "FETCHED_AT": now,
                "SHA256": hashlib.sha256(p.read_bytes()).hexdigest(), "OFFICIAL": "người dùng cung cấp - ghi rõ trong báo cáo"}
        try:
            text, man = file_to_text(p, ingest_root / args.name)
        except IngestError as e:
            print(f"⛔ {e}", file=sys.stderr)
            if e.rc != RC_SCAN:
                return e.rc
            pages = e.man.get("pages_needing_ocr") or []
            stale = out_dir / f"{args.name}.txt"
            if has_articles(e.text):
                # Scan MỘT PHẦN: chỉ lưu các trang có lớp chữ thật; trang scan không có trong nguồn → trích dẫn
                # từ các trang đó sẽ không qua evidence_verifier (đúng ý: chưa đối chiếu được).
                meta["FORMAT"] = f"{e.man.get('detected_format')} (doc_ingest)"
                meta["MISSING_PAGES"] = (f"{', '.join(map(str, pages))} (scan, KHÔNG có trong file này — "
                                         "trích dẫn từ các trang đó ghi [CẦN XÁC MINH])")
                path = save(out_dir, args.name, e.text, meta)
                print(f"⚠️  Đã lưu PHẦN CÓ LỚP CHỮ vào {path}; thiếu trang scan {pages}.", file=sys.stderr)
            else:
                if stale.exists():
                    stale.unlink()
                print(f"⛔ SCAN: không lưu nguồn {stale.name} (bản nháp OCR chưa kiểm chứng KHÔNG được dùng làm nguồn "
                      f"đối chiếu). Đọc ảnh trang: {', '.join(ocr_page_paths(e.man)[:5])}. Muốn trích dẫn nguyên văn: "
                      "số hoá bằng skill boc-tach-pdf (có đối chiếu OCR) rồi chạy lại --file trên bản .docx/.md kết quả, "
                      "hoặc tìm bản có lớp chữ trên Công báo; nếu không: trích dẫn ghi [CẦN XÁC MINH: bản scan].",
                      file=sys.stderr)
            return RC_SCAN
        meta["FORMAT"] = f"{man.get('detected_format')} (doc_ingest)"
        if man.get("legacy_encoding") or man.get("text_encoding"):
            meta["ENCODING"] = man.get("legacy_encoding") or man.get("text_encoding")
        path = save(out_dir, args.name, text, meta)
        for w in man.get("warnings") or []:
            print(f"⚠️  {w}", file=sys.stderr)
        print(f"✅ Đã lưu {path} ({len(text)} ký tự, {len(re.findall(r'Điều\s+\d+', text))} lần 'Điều N')")
        return 0 if has_articles(text) else 4

    url = args.url
    host = urllib.parse.urlparse(url).netloc
    if not any(h in host for h in OFFICIAL_HOSTS):
        print(f"⚠️  {host} không phải nguồn chính thống. Chỉ dùng để tìm số hiệu; trích dẫn phải lấy từ nguồn chính thống.",
              file=sys.stderr)

    status, ctype, body, final = fetch(url)
    if looks_blocked(status, body):
        print(f"⛔ BLOCKED ({status}) {url}\n   → Thử nguồn chính thống khác (congbao.chinhphu.vn, vanban.chinhphu.vn); "
              f"nếu vẫn không được: xin người dùng file PDF/DOCX (--file) hoặc gắn [CẦN XÁC MINH] cho mọi trích dẫn.",
              file=sys.stderr)
        return 3
    if status != 200:
        print(f"❌ HTTP {status} {url}", file=sys.stderr)
        return 1

    file_url = final
    with tempfile.TemporaryDirectory() as td:
        if "html" in ctype.lower() or body[:200].lstrip().lower().startswith((b"<!doctype", b"<html")):
            page = body.decode("utf-8", errors="ignore")
            text = html_to_text(page)
            if not has_articles(text):
                atts = find_attachments(page, final)
                for _, att_url, ext in atts:
                    st, _ct, data, fin = fetch(att_url)
                    if st == 200 and data and not looks_blocked(st, data):
                        tmp = Path(td) / f"doc{ext}"
                        tmp.write_bytes(data)
                        try:
                            text, _man = file_to_text(tmp, ingest_root / f"{args.name}-url")
                        except IngestError as e:
                            print(f"⚠️  {att_url}: {e}", file=sys.stderr)
                            continue
                        file_url, body = att_url, data
                        if has_articles(text):
                            break
        else:
            tmp = Path(td) / "doc.bin"
            tmp.write_bytes(body)
            kind = sniff_kind(tmp)  # đặt đúng đuôi theo magic bytes (openpyxl từ chối đuôi sai)
            if kind in ("pdf", "docx", "doc", "odt", "rtf", "html", "xlsx", "xls", "pptx", "epub"):
                tmp = tmp.rename(tmp.with_suffix("." + kind))
            try:
                text, _man = file_to_text(tmp, ingest_root / f"{args.name}-url")
            except IngestError as e:
                print(f"⛔ {url}: {e}", file=sys.stderr)
                return e.rc

    if not has_articles(text):
        print(f"⛔ NO_CONTENT: {url} không có nội dung 'Điều N' (trang JavaScript hoặc không có file đính kèm). "
              f"Thử trang Công báo của cùng văn bản hoặc xin người dùng file.", file=sys.stderr)
        return 4

    meta = {"SOURCE_URL": url, "FILE_URL": file_url, "FETCHED_AT": now,
            "SHA256": hashlib.sha256(body).hexdigest()}
    path = save(out_dir, args.name, text, meta)
    print(f"✅ Đã lưu {path} ({len(text)} ký tự). Dùng làm 'source' trong claims.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
