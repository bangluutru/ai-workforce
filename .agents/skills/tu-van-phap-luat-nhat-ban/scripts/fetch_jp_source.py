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

Mã thoát: 0 = đã lưu; 3 = bị chặn (403...); 4 = không có nội dung; 1 = lỗi khác.
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Lưu nguồn chính thức Nhật thành text cho kiểm chứng trích dẫn")
    ap.add_argument("--url", help="URL e-Gov (laws.e-gov.go.jp/law/<ID>) hoặc trang/PDF .go.jp")
    ap.add_argument("--law-id", help="e-Gov LawID, VD 329AC0000000061 (関税法)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--name", required=True)
    a = ap.parse_args()
    if not a.url and not a.law_id:
        ap.error("cần --url hoặc --law-id")

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
