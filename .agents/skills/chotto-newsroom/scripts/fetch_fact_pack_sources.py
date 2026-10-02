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

Mã thoát: 0 = mọi trích dẫn có nguyên văn; 2 = có trích dẫn không tìm thấy / nguồn tải hỏng; 1 = lỗi đầu vào.
"""

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
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
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>|</td>|</th>", "\n", raw)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return "\n".join(ln for ln in (re.sub(r"[ \t　]+", " ", x).strip() for x in txt.splitlines()) if ln)


def download(url, path):
    m = re.search(r"laws\.e-gov\.go\.jp/law/([0-9A-Za-z]{12,})", url)
    fetch_url = EGOV_API.format(law_id=m.group(1)) if m else url
    status, ctype, body = fetch(fetch_url)
    if status != 200 or not body:
        return {"url": url, "fetch_url": fetch_url, "status": status, "ok": False}
    text = egov_text(body.decode("utf-8", errors="ignore")) if m else to_text(body, ctype)
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    path.write_text(f"# SOURCE_URL: {url}\n# FETCH_URL: {fetch_url}\n# FETCHED_AT: {now}\n\n{text}", encoding="utf-8")
    return {"url": url, "fetch_url": fetch_url, "status": status, "ok": len(text.strip()) > 200,
            "chars": len(text), "sha256": hashlib.sha256(body).hexdigest(), "fetched_at": now,
            "official": bool(OFFICIAL.search(url))}


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

    manifest, problems = {}, []
    for sid, url in list(reg.items()) + list(laws.items()):
        path = out / f"{sid}.txt"
        if not a.offline or not path.exists():
            info = download(url, path)
            manifest[sid] = info
            if not info["ok"]:
                problems.append(f"{sid}: tải hỏng ({info['status']}) {url}")
            elif not info.get("official"):
                problems.append(f"{sid}: {url} không phải nguồn .go.jp/.lg.jp; bài cần ít nhất một nguồn chính thức cho mỗi tuyên bố.")
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def text_of(sid):
        p = out / f"{sid}.txt"
        return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

    checked = 0
    # Ma trận tuyên bố: | Mã | Tuyên bố | Mã Nguồn | Trích dẫn | ...
    for r in table_rows(section(fp, "TUYÊN BỐ", "KEY CLAIMS"))[1:]:
        sids = [c for c in r if re.fullmatch(r"S\d{2}", c.strip("* "))]
        for cell in r:
            for q in re.findall(r"「([^」]+)」", cell):
                checked += 1
                srcs = [s.strip("* ") for s in sids] or list(reg)
                if not any(check_single_quote(text_of(s), q)[0] for s in srcs):
                    problems.append(f"{r[0]}: 「{q[:50]}」 không có nguyên văn trong {srcs}")
    # Sổ số liệu: | Mã | Nội dung | Giá trị | Nguồn | Vị trí | Nguyên văn |
    for r in table_rows(section(fp, "SỔ SỐ LIỆU", "NUMBER LEDGER"))[1:]:
        if len(r) < 6:
            continue
        sid = r[3].strip("* ")
        for q in quotes_in(r[5]):
            checked += 1
            if not check_single_quote(text_of(sid), q)[0]:
                problems.append(f"{r[0]}: nguyên văn 「{q[:50]}」 không có trong {sid} ({reg.get(sid, '?')})")
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
            if not found:
                problems.append(f"{r[0]}: nguyên văn điều luật 「{q[:50]}」 không có trong {laws[r[0]]}")
            elif block is None or not check_single_quote(block, q_clean)[0]:
                problems.append(f"{r[0]}: nguyên văn có trong luật nhưng KHÔNG nằm trong {r[2]}")

    print(f"Nguồn: {len(reg)} + điều luật: {len(laws)} → {out}")
    print(f"Đã kiểm {checked} trích dẫn.")
    if checked == 0:
        problems.append("Không có trích dẫn tiếng Nhật nào để kiểm: Ma trận tuyên bố/Sổ số liệu phải có nguyên văn.")
    for p in problems:
        print(f"  ❌ {p}")
    print("PASS" if not problems else "FAIL")
    return 0 if not problems else 2


if __name__ == "__main__":
    sys.exit(main())
