#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_ingest_bridge.py — Cầu nối dùng chung giữa các skill AIWF và bộ chuyển đổi scripts/doc_ingest.py.

Mọi skill đọc tệp người dùng (DOCX/XLSX/PPTX/PDF/EPUB/ODF/RTF/HTML/CSV/TXT/ảnh) gọi qua đây để:
  - chạy doc_ingest (Python API; tự chạy lại bằng .venv nếu thiếu thư viện) → source.md + manifest.json;
  - diễn giải mã thoát 0/3/2/4 thành thông điệp tiếng Việt thống nhất cho agent;
  - tách source.md thành khối (tiêu đề / đoạn / mục liệt kê / bảng / ảnh / marker trang) cho skill cần "blocks";
  - kiểm tra trước (preflight) một PDF: đúng PDF thật, không mật khẩu, có lớp chữ, dấu tiếng Việt không vỡ.

Dùng trong skill (đường dẫn tính từ <skill>/scripts/xxx.py):
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
    from doc_ingest_bridge import run_ingest, explain, md_blocks, pdf_preflight

Không gửi dữ liệu ra ngoài; không ghi gì vào repo (thư mục đầu ra do skill truyền vào).
"""
from __future__ import annotations

import os
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPTS = REPO / "scripts"
DOC_INGEST = SCRIPTS / "doc_ingest.py"

EXIT_OK, EXIT_UNREADABLE, EXIT_PARTIAL, EXIT_MISSING_DEP = 0, 2, 3, 4

# Phần mở rộng mà skill có thể đọc thẳng như văn bản thuần (vẫn nên qua doc_ingest để xử lý bảng mã).
PLAIN_TEXT_EXTS = {".txt", ".md", ".markdown"}
OFFICE_EXTS = {".doc", ".docx", ".docm", ".dot", ".dotx", ".odt", ".rtf",
               ".xls", ".xlsx", ".xlsm", ".ods", ".csv", ".tsv",
               ".ppt", ".pptx", ".pptm", ".odp"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".heif", ".webp", ".bmp", ".gif"}


def default_ingest_dir(job: str) -> Path:
    """Thư mục đầu ra mặc định cho bản chuyển đổi (ngoài repo, theo GEMINI.md)."""
    base = os.environ.get("AIWF_INGEST_DIR")
    root = Path(base).expanduser() if base else Path.home() / "Downloads" / "AIWF_Output" / "_ingest"
    slug = re.sub(r"[^\w.-]+", "_", job, flags=re.U).strip("_.") or "job"
    return root / slug


def load_doc_ingest():
    """Nhập module doc_ingest của repo (scripts/doc_ingest.py)."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import doc_ingest  # noqa: E402
    return doc_ingest


def run_ingest(path, out_dir, ocr: bool = True, max_chars: int | None = None) -> dict:
    """Chạy doc_ingest cho MỘT tệp. Trả về manifest (dict) và thêm khoá:
       'source_md_path', 'source_md' (nội dung), 'out_dir'. Không ném lỗi với tệp xấu."""
    out = Path(out_dir).expanduser()
    try:
        di = load_doc_ingest()
    except Exception as e:  # noqa: BLE001 — repo hỏng/thiếu tệp
        return {"status": "missing_dependency", "exit_code": EXIT_MISSING_DEP, "out_dir": str(out),
                "message": f"Không nạp được {DOC_INGEST} ({type(e).__name__}: {e}). Kiểm tra repo ai-workforce đầy đủ.",
                "warnings": [], "pages_needing_ocr": [], "ocr_pages": [], "source_md": "", "source_md_path": None}
    man = di.ingest(str(path), str(out), ocr=ocr, max_chars=max_chars)
    md_path = Path(man.get("out_dir") or out) / "source.md"
    man["source_md_path"] = str(md_path)
    try:
        man["source_md"] = md_path.read_text(encoding="utf-8")
    except OSError:
        man["source_md"] = ""
    return man


def ocr_page_paths(man: dict) -> list[str]:
    base = Path(man.get("out_dir") or ".")
    return [str(base / p["image"]) for p in man.get("ocr_pages") or [] if p.get("image")]


def explain(man: dict, skill: str = "") -> str:
    """Thông điệp thống nhất cho agent theo mã thoát doc_ingest."""
    code = man.get("exit_code")
    name = man.get("input_name") or Path(str(man.get("input", "?"))).name
    tag = f"[{skill}] " if skill else ""
    if code == EXIT_OK:
        w = man.get("warnings") or []
        return f"{tag}Đã đọc {name} ({man.get('detected_format')}, {man.get('chars', 0):,} ký tự)." + (
            " Lưu ý: " + " | ".join(w) if w else "")
    if code == EXIT_PARTIAL:
        pages = man.get("pages_needing_ocr") or []
        imgs = ocr_page_paths(man)
        shown = ", ".join(imgs[:5]) + (f" … (+{len(imgs) - 5})" if len(imgs) > 5 else "")
        return (f"{tag}{name}: {len(pages)} trang/ảnh KHÔNG có lớp chữ (scan) — trang {', '.join(map(str, pages[:30]))}. "
                f"Agent PHẢI đọc ảnh trang bằng thị giác: {shown}. Bản nháp OCR trong source.md "
                "(giữa <!-- ocr-draft:start/end -->) CHƯA kiểm chứng — không trích dẫn nguyên văn khi chưa đối chiếu ảnh. "
                "Tài liệu scan dài → dùng skill boc-tach-pdf.")
    if code == EXIT_UNREADABLE:
        return f"{tag}KHÔNG ĐỌC ĐƯỢC {name}: {man.get('message')}"
    if code == EXIT_MISSING_DEP:
        return f"{tag}THIẾU PHỤ THUỘC khi đọc {name}: {man.get('message')}"
    return f"{tag}{name}: trạng thái lạ {man.get('status')!r} — {man.get('message')}"


# ════════════════════════════════════════════════════════════════════════════
# Markdown (source.md) → khối
# ════════════════════════════════════════════════════════════════════════════
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_IMG = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
_LIST = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
_COMMENT = re.compile(r"^<!--\s*(.*?)\s*-->$")


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells = re.split(r"(?<!\\)\|", s)
    return [c.strip().replace("\\|", "|").replace("<br>", "\n") for c in cells]


def md_blocks(md: str, keep_ocr_drafts: bool = False) -> list[dict]:
    """Tách Markdown của doc_ingest thành khối theo thứ tự:
       {'type': 'heading', 'level': n, 'text'} | {'type': 'paragraph', 'text'} | {'type': 'list_item', 'text'}
       {'type': 'table', 'rows': [[...]], 'text'} | {'type': 'image', 'alt', 'src'} | {'type': 'page', 'page': n}
       {'type': 'ocr_notice', 'text'} (cảnh báo trang scan). Bản nháp OCR bị bỏ (trừ keep_ocr_drafts)."""
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[dict] = []
    para: list[str] = []
    in_draft = False
    in_fence = False
    fence: list[str] = []

    def flush():
        if para:
            text = " ".join(x.strip() for x in para).strip()
            if text:
                out.append({"type": "paragraph", "text": text})
            para.clear()

    i = 0
    while i < len(lines):
        ln = lines[i]
        st = ln.strip()
        if in_fence:
            if st.startswith("```"):
                in_fence = False
                out.append({"type": "paragraph", "text": "\n".join(fence), "code": True})
                fence = []
            else:
                fence.append(ln)
            i += 1
            continue
        if st.startswith("```"):
            flush()
            in_fence = True
            i += 1
            continue
        m = _COMMENT.match(st)
        if m:
            flush()
            body = m.group(1)
            if body.startswith("ocr-draft:start"):
                in_draft = True
            elif body.startswith("ocr-draft:end"):
                in_draft = False
            else:
                pm = re.match(r"page\s+(\d+)$", body)
                if pm:
                    out.append({"type": "page", "page": int(pm.group(1))})
            i += 1
            continue
        if in_draft and not keep_ocr_drafts:
            i += 1
            continue
        if not st:
            flush()
            i += 1
            continue
        if st.startswith("> [!WARNING]") or st.startswith("> [!CAUTION]"):
            flush()
            txt = [st.lstrip("> ").strip()]
            i += 1
            while i < len(lines) and lines[i].strip().startswith(">"):
                txt.append(lines[i].strip().lstrip("> ").strip())
                i += 1
            out.append({"type": "ocr_notice", "text": " ".join(txt)})
            continue
        hm = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", st)
        if hm:
            flush()
            out.append({"type": "heading", "level": len(hm.group(1)), "text": hm.group(2).strip()})
            i += 1
            continue
        if st.startswith("|") and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1].strip()):
            flush()
            rows = [_split_row(st)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_split_row(lines[i]))
                i += 1
            out.append({"type": "table", "rows": rows,
                        "text": "\n".join(" | ".join(r) for r in rows)})
            continue
        im = _IMG.match(st)
        if im:
            flush()
            out.append({"type": "image", "alt": im.group(1), "src": im.group(2)})
            i += 1
            continue
        lm = _LIST.match(ln)
        if lm and lm.group(1).strip():
            flush()
            out.append({"type": "list_item", "text": lm.group(1).strip()})
            i += 1
            continue
        para.append(st.lstrip("> ").strip() if st.startswith(">") else st)
        i += 1
    flush()
    if in_fence and fence:
        out.append({"type": "paragraph", "text": "\n".join(fence), "code": True})
    return out


def strip_md_inline(text: str) -> str:
    """Bỏ định dạng Markdown nội dòng (**đậm**, *nghiêng*, `code`, [liên kết](url)) để lấy chữ trơn."""
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"(\*\*|__)(.+?)\1", r"\2", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = t.replace("\\*", "*").replace("\\_", "_").replace("\\#", "#").replace("\\|", "|")
    return t


# ════════════════════════════════════════════════════════════════════════════
# Kiểm tra trước một PDF (cho skill dịch giữ bố cục / tái dựng)
# ════════════════════════════════════════════════════════════════════════════
def sniff_kind(path) -> str:
    """Nhận dạng nhanh theo magic bytes (dùng detect_format của doc_ingest)."""
    p = Path(path)
    if not p.exists():
        return "missing"
    if p.is_dir():
        return "dir"
    try:
        fmt, info = load_doc_ingest().detect_format(p)
        return fmt
    except Exception:  # noqa: BLE001
        with open(p, "rb") as f:
            head = f.read(1024)
        return "pdf" if b"%PDF-" in head else "unknown"


_SOFFICE_HINT = ("`soffice --headless --convert-to pdf --outdir <thư_mục_mới> \"<tệp>.{ext}\"` (phần mở rộng phải đúng loại "
                 "tệp: nếu tệp đang mang đuôi '.pdf' thì đổi tên về '.{ext}' trước, tránh ghi đè tệp gốc)")
PDF_NOT_PDF_MSG = {
    "docx": "Tệp {name} là Word (DOCX), không phải PDF. Chuyển sang PDF trước: " + _SOFFICE_HINT.format(ext="docx")
            + " (hoặc Word → Lưu thành PDF), hoặc dịch trực tiếp bằng skill ejv-translate.",
    "pptx": "Tệp {name} là PowerPoint (PPTX), không phải PDF. Chuyển sang PDF trước: " + _SOFFICE_HINT.format(ext="pptx")
            + " rồi chạy lại; hoặc dùng skill ejv-translate cho bản dịch văn bản.",
    "xlsx": "Tệp {name} là Excel (XLSX), không phải PDF. Skill này chỉ nhận PDF; với bảng tính dùng doc_ingest/ejv-translate.",
}


def pdf_preflight(path, min_text_ratio: float = 0.5, check_diacritics: bool = True,
                  max_check_pages: int = 60) -> dict:
    """Kiểm tra một PDF trước khi dịch giữ bố cục/tái dựng.
    Trả về {'ok': bool, 'code': 0/2/3, 'kind', 'pages', 'text_pages', 'scan_pages', 'damaged_pages',
            'message': str, 'warnings': [...]}. code 2 = không phải PDF/mật khẩu/hỏng; 3 = chủ yếu là scan."""
    p = Path(path)
    res = {"ok": False, "code": EXIT_UNREADABLE, "kind": None, "pages": 0, "text_pages": [], "scan_pages": [],
           "damaged_pages": [], "message": "", "warnings": []}
    kind = sniff_kind(p)
    res["kind"] = kind
    if kind == "missing":
        res["message"] = f"Không tìm thấy tệp: {p}"
        return res
    if kind != "pdf":
        tmpl = PDF_NOT_PDF_MSG.get(kind)
        if tmpl is None and kind in ("doc", "odt", "rtf", "ppt", "odp"):
            tmpl = ("Tệp {name} là tài liệu Office/OpenDocument ({kind}), không phải PDF. Chuyển sang PDF trước: "
                    + _SOFFICE_HINT.format(ext=kind) + ", hoặc dùng skill ejv-translate.")
        if tmpl is None and kind in ("png", "jpeg", "tiff", "heic", "webp", "bmp", "gif"):
            tmpl = "Tệp {name} là ảnh ({kind}), không có lớp chữ → dùng skill boc-tach-pdf để OCR/bóc tách trước."
        if tmpl is None:
            tmpl = ("Tệp {name} không phải PDF (nhận dạng: {kind}, dù phần mở rộng là '{ext}'). "
                    "Hãy hỏi người dùng tệp PDF gốc; đọc nội dung bằng scripts/doc_ingest.py.")
        res["message"] = tmpl.format(name=p.name, kind=kind, ext=p.suffix)
        return res
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz  # type: ignore
        except ImportError:
            res["code"] = EXIT_MISSING_DEP
            res["message"] = "Thiếu PyMuPDF: `.venv/bin/pip install pymupdf` (hoặc bash scripts/auto-setup.sh)."
            return res
    try:
        doc = fitz.open(str(p))
    except Exception as e:  # noqa: BLE001
        res["message"] = f"PDF hỏng, không mở được ({e}). Hãy hỏi người dùng gửi lại bản gốc."
        return res
    if doc.needs_pass or doc.is_encrypted:
        res["message"] = ("PDF được bảo vệ bằng mật khẩu nên không xử lý được. Hãy hỏi người dùng gửi bản PDF không "
                          "đặt mật khẩu (mở bằng mật khẩu → In → Lưu thành PDF). KHÔNG đoán mật khẩu.")
        doc.close()
        return res
    n = doc.page_count
    res["pages"] = n
    if n == 0:
        res["message"] = "PDF 0 trang."
        doc.close()
        return res
    texts = {}
    for i in range(n):
        t = doc[i].get_text()
        letters = sum(c.isalnum() for c in t)
        bad = sum(1 for c in t if c == "�" or 0xE000 <= ord(c) <= 0xF8FF)
        if letters >= 20 and bad / max(1, letters + bad) <= 0.3:
            res["text_pages"].append(i + 1)
            texts[i + 1] = t
        elif letters < 20 and doc[i].get_images() or bad / max(1, letters + bad) > 0.3:
            res["scan_pages"].append(i + 1)
    doc.close()
    ratio = len(res["text_pages"]) / n
    if not res["text_pages"]:
        res["code"] = EXIT_PARTIAL
        res["message"] = ("PDF không có lớp chữ (scan/ảnh) ở mọi trang → không dịch giữ bố cục được. Dùng skill "
                          "boc-tach-pdf để OCR/bóc tách trước (hoặc `.venv/bin/python scripts/doc_ingest.py` để đọc).")
        return res
    if ratio < min_text_ratio:
        res["code"] = EXIT_PARTIAL
        res["message"] = (f"Chỉ {len(res['text_pages'])}/{n} trang có lớp chữ (còn lại là scan: "
                          f"{', '.join(map(str, res['scan_pages'][:20]))}). Dùng skill boc-tach-pdf cho bản scan.")
        return res
    if res["scan_pages"]:
        res["warnings"].append(f"Trang scan không có lớp chữ (sẽ giữ nguyên, không dịch): "
                               f"{', '.join(map(str, res['scan_pages'][:30]))}.")
    if check_diacritics:
        res["damaged_pages"] = diacritic_cross_check(p, texts, max_pages=max_check_pages)
        if res["damaged_pages"]:
            res["warnings"].append(
                "⚠️ DẤU TIẾNG VIỆT BỊ VỠ trong lớp chữ PyMuPDF (font nhúng/ToUnicode lỗi) ở trang "
                + ", ".join(str(d["page"]) for d in res["damaged_pages"][:30])
                + ": bộ trích khác ("
                + ", ".join(sorted({d['better'] for d in res['damaged_pages']}))
                + ") đọc đúng hơn. Bản dịch các trang này có thể sai nghĩa — đối chiếu ảnh trang trước khi giao.")
    res["ok"], res["code"] = True, EXIT_OK
    res["message"] = f"PDF hợp lệ: {len(res['text_pages'])}/{n} trang có lớp chữ."
    return res


def diacritic_cross_check(path, pymupdf_texts: dict, max_pages: int = 60) -> list[dict]:
    """So độ vỡ dấu của chữ PyMuPDF với pdfplumber/pdftotext trên từng trang.
    Trả về [{'page', 'pymupdf', 'better', 'better_score'}] cho trang PyMuPDF vỡ dấu rõ rệt."""
    try:
        di = load_doc_ingest()
    except Exception:  # noqa: BLE001
        return []
    damaged = []
    suspects = [(pg, t) for pg, t in sorted(pymupdf_texts.items()) if di.diacritic_damage(t) >= 0.06][:max_pages]
    if not suspects:
        return []
    import shutil
    import subprocess
    plumber = None
    try:
        import pdfplumber
        plumber = pdfplumber.open(str(path))
    except Exception:  # noqa: BLE001
        plumber = None
    exe = shutil.which("pdftotext")
    for pg, t in suspects:
        cands = []
        if plumber is not None:
            try:
                cands.append(("pdfplumber", plumber.pages[pg - 1].extract_text() or ""))
            except Exception:  # noqa: BLE001
                pass
        if exe:
            try:
                r = subprocess.run([exe, "-enc", "UTF-8", "-f", str(pg), "-l", str(pg), str(path), "-"],
                                   capture_output=True, timeout=60)
                if r.returncode == 0:
                    cands.append(("pdftotext", r.stdout.decode("utf-8", "replace")))
            except (OSError, subprocess.TimeoutExpired):
                pass
        name, _, score = di.choose_least_damaged(("pymupdf", t), cands)
        base = di.diacritic_damage(t)
        if name != "pymupdf":
            damaged.append({"page": pg, "pymupdf": round(base, 3), "better": name, "better_score": round(score, 3)})
        elif base >= 0.08:
            damaged.append({"page": pg, "pymupdf": round(base, 3), "better": "none", "better_score": round(base, 3)})
    if plumber is not None:
        plumber.close()
    return damaged


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)
