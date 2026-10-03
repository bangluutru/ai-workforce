#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_jp_source.py — Lưu nguồn chính thức Nhật (luật e-Gov, trang/PDF .go.jp) thành file text trong
<research_dir>/sources/ để check_evidence_table.py đối chiếu trích dẫn nguyên văn.

Chỉ HTTP GET trang công khai. Không gọi LLM API.

Cách dùng (từ thư mục workspace AIWF):
  # Luật trên e-Gov: dùng URL https://laws.e-gov.go.jp/law/<LawID> hoặc --law-id
  python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/fetch_jp_source.py \
      --url https://laws.e-gov.go.jp/law/322AC0000000233 --out-dir <research_dir>/sources --name shokuhin-eiseiho
  # Trang/PDF cơ quan (.go.jp):
  python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/fetch_jp_source.py \
      --url https://www.mhlw.go.jp/.../index_00004.html --out-dir <research_dir>/sources --name mhlw-import

  # File người dùng cung cấp (PDF/DOCX/DOC/ODT/RTF/HTML/TXT/XLSX..., đọc bằng scripts/doc_ingest.py):
  python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/fetch_jp_source.py \
      --file ~/Downloads/tsuuchi.pdf --out-dir <research_dir>/sources --name mhlw-tsuuchi
  (Bản chuyển đổi đầy đủ + ảnh trang scan nằm ở <research_dir>/_ingest/<name>/, KHÔNG nằm trong sources/.)

Mã thoát: 0 = đã lưu; 3 = bị chặn (403...); 4 = không có nội dung; 1 = lỗi khác.
  Riêng --file: 2 = không đọc được (mật khẩu/DRM/hỏng/rỗng) — không lưu gì; 5 = PDF/ảnh SCAN (toàn bộ hoặc một phần)
  — KHÔNG lưu bản nháp OCR làm nguồn (chỉ lưu các trang có lớp chữ thật, nếu có); 6 = thiếu phụ thuộc.
File luật được ghi theo từng điều, mỗi điều bắt đầu bằng dòng "第N条" để kiểm được trích dẫn nằm đúng điều.
"""

import argparse
import hashlib
import html
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from doc_ingest_bridge import (EXIT_MISSING_DEP, EXIT_PARTIAL, EXIT_UNREADABLE, explain,  # noqa: E402
                               ocr_page_paths, run_ingest, strip_md_inline)

SKILL = "tu-van-phap-luat-nhat-ban"
RC_UNREADABLE, RC_SCAN, RC_MISSING_DEP = 2, 5, 6
_TABLE_SEP = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?$")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
EGOV_API = "https://laws.e-gov.go.jp/api/2/law_data/{law_id}?response_format=xml"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, "", b""


def egov_xml_to_text(xml: str) -> str:
    out = []
    m = re.search(r"<LawTitle[^>]*>([^<]+)</LawTitle>", xml)
    if m:
        out.append(m.group(1))
    m = re.search(r"<LawNum>([^<]+)</LawNum>", xml)
    if m:
        out.append(m.group(1))
    body = xml[xml.find("<MainProvision"):] if "<MainProvision" in xml else xml
    for art in re.findall(r"<Article [^>]*>.*?</Article>", body, flags=re.S):
        cap = re.search(r"<ArticleCaption>([^<]*)</ArticleCaption>", art)
        title = re.search(r"<ArticleTitle>([^<]*)</ArticleTitle>", art)
        text = re.sub(r"<ArticleCaption>.*?</ArticleCaption>|<ArticleTitle>.*?</ArticleTitle>", "", art, flags=re.S)
        text = re.sub(r"<ParagraphNum>([^<]*)</ParagraphNum>", r"\n\1 ", text)
        text = re.sub(r"<ItemTitle>([^<]*)</ItemTitle>", r"\n\1 ", text)
        text = html.unescape(re.sub(r"<[^>]+>", "", text))
        text = re.sub(r"[ \t]+", " ", text)
        head = (title.group(1) if title else "").strip()
        out.append(f"\n{head} {cap.group(1) if cap else ''}".rstrip() + "\n" + text.strip())
    return "\n".join(out)


def page_to_text(body: bytes, ctype: str) -> str:
    if body.startswith(b"%PDF"):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(body)
            tmp = f.name
        if shutil.which("pdftotext"):
            r = subprocess.run(["pdftotext", "-layout", tmp, "-"], capture_output=True, text=True)
            if r.returncode == 0:
                return r.stdout
        import fitz
        with fitz.open(tmp) as d:
            return "\n".join(p.get_text() for p in d)
    raw = body.decode("utf-8", errors="ignore")
    m = re.search(r'charset=["\']?(shift_jis|sjis|euc-jp)', raw[:3000], re.I) or re.search(r"(shift_jis|euc-jp)", ctype, re.I)
    if m:
        raw = body.decode(m.group(1).lower().replace("sjis", "shift_jis"), errors="ignore")
    raw = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>|</td>", "\n", raw)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    lines = [re.sub(r"[ \t　]+", " ", ln).strip() for ln in txt.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def md_to_plain(md: str) -> str:
    """source.md của doc_ingest → chữ trơn giữ dòng cho check_evidence_table: bỏ marker trang/ảnh/cảnh báo,
    BỎ HẲN bản nháp OCR (chưa kiểm chứng), bỏ định dạng Markdown để trích đoạn khớp nguyên văn."""
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


def save_source(out_dir: str, name: str, header: dict, text: str) -> Path:
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.txt"
    path.write_text("".join(f"# {k}: {v}\n" for k, v in header.items()) + "\n" + text, encoding="utf-8")
    return path


def from_file(a) -> int:
    """--file: đọc tệp người dùng qua doc_ingest, lưu cùng bố cục với chế độ URL."""
    p = Path(a.file).expanduser()
    if not p.is_file():
        print(f"❌ Không thấy file: {p}", file=sys.stderr)
        return 1
    body = p.read_bytes()
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    man = run_ingest(p, Path(a.out_dir).expanduser().parent / "_ingest" / a.name, ocr=True)
    code = man.get("exit_code")
    if code in (EXIT_UNREADABLE, EXIT_MISSING_DEP):
        print(f"⛔ {explain(man, SKILL)}", file=sys.stderr)
        return RC_UNREADABLE if code == EXIT_UNREADABLE else RC_MISSING_DEP
    text = md_to_plain(man.get("source_md") or "")
    header = {"SOURCE_URL": f"user-file:{p.name}", "FETCH_URL": str(p.resolve()), "FETCHED_AT": now,
              "SHA256": hashlib.sha256(body).hexdigest(), "FORMAT": f"{man.get('detected_format')} (doc_ingest)",
              "OFFICIAL": "người dùng cung cấp - ghi rõ trong Bảng nguồn"}
    stale = Path(a.out_dir).expanduser() / f"{a.name}.txt"
    if code == EXIT_PARTIAL:
        pages = man.get("pages_needing_ocr") or []
        print(f"⛔ {explain(man, SKILL)}", file=sys.stderr)
        if sum(c.isalnum() for c in text) >= 20:
            header["MISSING_PAGES"] = (f"{', '.join(map(str, pages))} (scan, KHÔNG có trong file này — "
                                       "trích đoạn từ các trang đó ghi 'chưa đọc được')")
            path = save_source(a.out_dir, a.name, header, text)
            print(f"⚠️  Đã lưu PHẦN CÓ LỚP CHỮ vào {path}; thiếu trang scan {pages}.", file=sys.stderr)
        else:
            if stale.exists():
                stale.unlink()
            print(f"⛔ SCAN: không lưu {stale.name} (bản nháp OCR chưa kiểm chứng KHÔNG được dùng làm nguồn đối chiếu). "
                  f"Đọc ảnh trang: {', '.join(ocr_page_paths(man)[:5])}. Ghi 'chưa đọc được' trong Bảng nguồn và dùng "
                  "[GIẢ ĐỊNH / CHƯA XÁC MINH]; hoặc số hoá bằng skill boc-tach-pdf rồi chạy lại --file trên bản kết quả.",
                  file=sys.stderr)
        return RC_SCAN
    if not text.strip():
        print(f"⛔ {p.name}: đọc được 0 ký tự — tệp rỗng hoặc chỉ có hình. Hỏi người dùng bản có chữ.", file=sys.stderr)
        return RC_UNREADABLE
    path = save_source(a.out_dir, a.name, header, text)
    for w in man.get("warnings") or []:
        print(f"⚠️  {w}", file=sys.stderr)
    print(f"✅ Đã lưu {path} ({len(text)} ký tự)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Lưu nguồn chính thức Nhật thành text cho kiểm chứng trích dẫn")
    ap.add_argument("--url", help="URL e-Gov (laws.e-gov.go.jp/law/<ID>) hoặc trang/PDF .go.jp")
    ap.add_argument("--law-id", help="e-Gov LawID, VD 329AC0000000061 (関税法)")
    ap.add_argument("--file", help="File người dùng cung cấp (PDF/DOCX/DOC/ODT/RTF/HTML/TXT...), đọc qua doc_ingest")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--name", required=True)
    a = ap.parse_args()
    if sum(bool(x) for x in (a.url, a.law_id, a.file)) == 0:
        ap.error("cần --url, --law-id hoặc --file")
    if a.file:
        if a.url or a.law_id:
            ap.error("--file không dùng chung với --url/--law-id")
        return from_file(a)

    law_id = a.law_id
    if a.url and not law_id:
        m = re.search(r"laws\.e-gov\.go\.jp/(?:law|document\?lawid=)/?([0-9A-Z]{12,})", a.url)
        law_id = m.group(1) if m else None
    src_url = a.url or f"https://laws.e-gov.go.jp/law/{law_id}"
    fetch_url = EGOV_API.format(law_id=law_id) if law_id else a.url

    status, ctype, body = fetch(fetch_url)
    if status in (401, 403, 429, 503):
        print(f"⛔ BLOCKED ({status}) {fetch_url}: ghi trạng thái 'chưa đọc được' trong bảng nguồn, tìm bản PDF chính thức khác.",
              file=sys.stderr)
        return 3
    if status != 200 or not body:
        print(f"❌ HTTP {status} {fetch_url}", file=sys.stderr)
        return 1
    text = egov_xml_to_text(body.decode("utf-8", errors="ignore")) if law_id else page_to_text(body, ctype)
    if len(text.strip()) < 200:
        print(f"⛔ NO_CONTENT: {fetch_url} gần như không có chữ (trang JavaScript/PDF ảnh).", file=sys.stderr)
        return 4
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    out = Path(a.out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{a.name}.txt"
    path.write_text(f"# SOURCE_URL: {src_url}\n# FETCH_URL: {fetch_url}\n# FETCHED_AT: {now}\n"
                    f"# SHA256: {hashlib.sha256(body).hexdigest()}\n\n{text}", encoding="utf-8")
    print(f"✅ Đã lưu {path} ({len(text)} ký tự)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
