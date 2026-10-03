#!/usr/bin/env python3
"""
ingest.py — Chuẩn bị tài liệu nguồn cho Đọc Sâu: lưu văn bản nguồn thành FILE CỤC BỘ (để kiểm chứng trích dẫn)
và chia thành các đoạn (chunk) đọc tuần tự, kèm bảng độ phủ.

Đầu vào: MỌI định dạng mà scripts/doc_ingest.py đọc được — PDF, DOC/DOCX, ODT, RTF, XLS/XLSX/ODS/CSV, PPT/PPTX/ODP,
EPUB, HTML, MD, TXT (UTF-8/UTF-16/CP1258/TCVN3), ảnh. Tệp luôn đi qua doc_ingest (bảng giữ hàng/cột, ảnh trích ra
media/, trang scan → ảnh PNG cần đọc bằng thị giác). Với URL: Agent tải trang bằng công cụ đọc web, lưu nội dung chữ
vào một file .md/.txt trong <process_dir>/sources/ rồi mới chạy ingest (evidence_verifier không nhận URL).

Usage:
  python3 ingest.py <file_nguon> --process-dir <process_dir> [--chunk-chars 6000] [--as main|ref]
     --as main (mặc định): tài liệu chính -> <process_dir>/source.txt + chunks/ + manifest.json
     --as ref            : tài liệu đối chiếu (Level 4) -> <process_dir>/sources/<tên>.txt (không chia chunk)
Output (main):
  <process_dir>/source.txt                 văn bản thuần (nguồn để kiểm chứng trích dẫn; KHÔNG chứa bản nháp OCR)
  <process_dir>/chunks/chunk_NNN.md        từng đoạn ~6000 ký tự, cắt ở ranh giới đoạn văn, có nhãn trang/slide/sheet/mục
  <process_dir>/manifest.json              danh sách chunk + vị trí + thông tin chuyển đổi (định dạng, cảnh báo, trang scan)
  <process_dir>/coverage.md                bảng độ phủ để chép vào mục 0 của báo cáo
  <process_dir>/_ingest/<tên>/             đầu ra doc_ingest (source.md, manifest.json, media/, ocr_pages/)
Exit:
  0 OK | 3 có trang scan: chunk vẫn tạo, nhưng các trang đó phải đọc từ ảnh ocr_pages/*.png (nháp OCR chưa kiểm chứng)
  2 không đọc được (URL, không thấy tệp, PDF mật khẩu, EPUB DRM, Office mã hoá, tệp hỏng, < 200 ký tự) | 4 thiếu phụ thuộc
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from doc_ingest_bridge import (EXIT_MISSING_DEP, EXIT_OK, EXIT_PARTIAL, EXIT_UNREADABLE,  # noqa: E402
                               explain, ocr_page_paths, run_ingest, strip_md_inline)

_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_LOC = re.compile(r"^(<!--\s*page\s+(\d+)\s*-->|<!--\s*chapter\s+(\d+)[^>]*-->|##\s+Slide\s+(\d+).*|"
                  r"##\s+Sheet\s+\d+:\s*(.+))\s*$", re.M)
DRAFT_OPEN = "⟦BẢN NHÁP OCR tr.{page} — CHƯA KIỂM CHỨNG: đọc ảnh {img} để lấy nguyên văn; KHÔNG trích dẫn từ nháp⟧"
DRAFT_CLOSE = "⟦/BẢN NHÁP OCR⟧"
_DRAFT_BLOCK = re.compile(r"⟦BẢN NHÁP OCR.*?⟦/BẢN NHÁP OCR⟧|⟦LƯU Ý:.*?⟧", re.S)


def _md_to_reading_text(md: str, base: Path) -> str:
    """Markdown của doc_ingest → văn bản đọc: giữ '#' tiêu đề, hàng bảng 'ô | ô', ảnh → [Hình: đường dẫn tuyệt đối],
    bỏ định dạng nội dòng. Bản nháp OCR được bọc trong ⟦BẢN NHÁP OCR⟧…⟦/BẢN NHÁP OCR⟧ (chỉ ở chunk, không vào source.txt)."""
    out: list[str] = []
    in_draft = in_note = False
    for ln in md.split("\n"):
        st = ln.strip()
        if in_note and st.startswith(">"):
            out[-1] = out[-1][:-1] + " " + st.lstrip("> ").strip() + "⟧"
            continue
        in_note = False
        if st.startswith(("> [!WARNING]", "> [!CAUTION]")):
            in_note = True
            body = re.sub(r"^>\s*\[!\w+\]\s*", "", st)
            body = re.sub(r"`(ocr_pages/[^`]+)`", lambda mm: str(base / mm.group(1)), body)
            out += ["", f"⟦LƯU Ý: {body}⟧"]
            continue
        m = re.match(r"<!--\s*ocr-draft:start\s+page=(\d+)", st)
        if m:
            in_draft = True
            img = base / "ocr_pages" / f"page_{int(m.group(1)):03d}.png"
            out += ["", DRAFT_OPEN.format(page=m.group(1), img=img)]
            continue
        if st.startswith("<!-- ocr-draft:end"):
            in_draft = False
            out += [DRAFT_CLOSE, ""]
            continue
        if in_draft:
            out.append(ln)
            continue
        if st.startswith("<!--") and st.endswith("-->"):
            continue
        if "|" in st and _TABLE_SEP.match(st):
            continue
        if st.startswith("|") and st.endswith("|") and len(st) > 1:
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", st[1:-1])]
            out.append(strip_md_inline(" | ".join(cells)).replace("<br>", " "))
            continue
        st = _IMG.sub(lambda mm: "[Hình" + (f" {mm.group(1)}" if mm.group(1) else "") + ": "
                      + (mm.group(2) if re.match(r"^[a-z]+:", mm.group(2)) else str(base / mm.group(2))) + "]", st)
        st = re.sub(r"`(ocr_pages/[^`]+)`", lambda mm: str(base / mm.group(1)), st)
        if st.startswith(">"):
            st = st.lstrip("> ").strip()
        out.append(strip_md_inline(st))
    return "\n".join(out)


def _split_locations(md: str) -> list[tuple[str, str]]:
    """Cắt source.md theo marker vị trí: PDF '<!-- page N -->' → tr.N; PPTX '## Slide N' → slide N;
    XLSX '## Sheet i: tên' → sheet tên; EPUB '<!-- chapter k: ... -->' → chương k."""
    parts, last, loc = [], 0, ""
    for m in _LOC.finditer(md):
        if m.start() > last:
            parts.append((loc, md[last:m.start()]))
        if m.group(2):
            loc = f"tr.{m.group(2)}"
        elif m.group(3):
            loc = f"chương {m.group(3)}"
        elif m.group(4):
            loc = f"slide {m.group(4)}"
        else:
            loc = f"sheet {m.group(5).strip()}"
        # marker trang/chương là chú thích → bỏ; tiêu đề '## Slide/Sheet' giữ lại trong văn bản
        last = m.end() if (m.group(2) or m.group(3)) else m.start()
    parts.append((loc, md[last:]))
    return [(lc, t) for lc, t in parts if t.strip()]


def read_source(path: Path, work: Path) -> tuple[list[tuple[str, str]], dict]:
    """Mọi định dạng → doc_ingest (bảng mã, bảng, ảnh, trang scan) → [(nhãn vị trí, văn bản)], manifest doc_ingest."""
    man = run_ingest(path, work)
    if man.get("exit_code") not in (EXIT_OK, EXIT_PARTIAL):
        return [], man
    base = Path(man.get("out_dir") or work)
    parts = [(loc, _md_to_reading_text(md, base)) for loc, md in _split_locations(man.get("source_md", ""))]
    return parts, man


def clean(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # nối từ bị ngắt dòng ở PDF tiếng Anh
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def verified_text(text: str) -> str:
    """Văn bản dùng để kiểm chứng trích dẫn: bỏ bản nháp OCR chưa kiểm chứng."""
    return re.sub(r"\n{3,}", "\n\n", _DRAFT_BLOCK.sub("", text)).strip()


def _report_ingest(man: dict) -> None:
    for w in man.get("warnings") or []:
        if w != man.get("message"):
            print(f"[WARN] {w}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Lưu nguồn cục bộ + chia chunk cho Đọc Sâu")
    ap.add_argument("source")
    ap.add_argument("--process-dir", required=True)
    ap.add_argument("--chunk-chars", type=int, default=6000)
    ap.add_argument("--as", dest="role", choices=["main", "ref"], default="main")
    a = ap.parse_args()

    src = Path(a.source).expanduser()
    if re.match(r"^https?://", a.source):
        print("[FAIL] Không nhận URL. Tải nội dung trang, lưu thành file trong <process_dir>/sources/ rồi chạy lại.")
        return EXIT_UNREADABLE
    if not src.is_file():
        print(f"[FAIL] Không thấy file {src}")
        return EXIT_UNREADABLE
    pdir = Path(a.process_dir).expanduser()
    pdir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w.-]+", "_", src.stem) or "source"
    work = pdir / "_ingest" / (("ref_" if a.role == "ref" else "") + slug)
    raw_parts, man = read_source(src, work)
    if man.get("exit_code") in (EXIT_UNREADABLE, EXIT_MISSING_DEP):
        print(f"[FAIL] {explain(man, 'doc-sau')}")
        return man["exit_code"]
    _report_ingest(man)
    partial = man.get("exit_code") == EXIT_PARTIAL
    parts = [(loc, clean(t)) for loc, t in raw_parts]
    full_reading = "\n\n".join(t for _, t in parts if t)
    full = verified_text(full_reading)
    if len(full) < 200:
        if partial:
            pngs = ocr_page_paths(man)
            print(f"[PARTIAL] Tài liệu gần như toàn trang scan ({len(man.get('pages_needing_ocr') or [])} trang không có "
                  f"lớp chữ) → không có văn bản để kiểm chứng trích dẫn. Tài liệu ngắn: đọc ảnh {', '.join(pngs[:5])} "
                  "bằng thị giác, chép nguyên văn vào <process_dir>/sources/input.md rồi ingest file đó. Tài liệu dài: "
                  "chạy skill 'boc-tach-pdf' trước, rồi ingest file .md kết quả.")
            return EXIT_PARTIAL
        print(f"[FAIL] Văn bản trích được quá ngắn ({len(full)} < 200 ký tự, định dạng "
              f"{man.get('detected_format')}). Hỏi người dùng tài liệu đầy đủ hơn, hoặc dán nội dung trực tiếp.")
        return EXIT_UNREADABLE

    if a.role == "ref":
        out = pdir / "sources" / (slug + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(full, encoding="utf-8")
        print(f"[OK] Nguồn đối chiếu: {out} ({len(full):,} ký tự, định dạng {man.get('detected_format')})")
        if partial:
            print(f"[PARTIAL] {explain(man, 'doc-sau')} Nội dung trang scan KHÔNG có trong {out.name}.")
            return EXIT_PARTIAL
        return EXIT_OK

    (pdir / "source.txt").write_text(full, encoding="utf-8")
    # chia chunk theo đoạn văn, giữ nhãn trang/tiêu đề (bản nháp OCR giữ nguyên một khối, không cắt giữa chừng)
    chunks, cur, cur_len, cur_loc, heading = [], [], 0, None, ""
    prev_loc = None
    for loc, text in parts:
        paras = []
        if loc and loc != prev_loc and len(parts) > 1:
            paras.append(f"<!-- {loc} -->")  # mốc vị trí trong chunk (để trích dẫn ghi đúng trang/slide/sheet)
        prev_loc = loc
        for seg in re.split(r"(⟦BẢN NHÁP OCR.*?⟦/BẢN NHÁP OCR⟧)", text, flags=re.S):
            if seg.startswith("⟦BẢN NHÁP OCR"):  # khối nháp OCR đi nguyên một đoạn
                paras.append(seg)
            else:
                paras += re.split(r"\n\s*\n", seg)
        for para in paras:
            para = para.strip()
            if not para:
                continue
            first = para.split("\n", 1)[0].strip()
            if re.match(r"^(#{1,6}\s|chương\s|chapter\s|phần\s|part\s|\d+(\.\d+)*\.?\s+[A-ZÀ-Ỹ])", first, re.I) and len(first) < 120:
                heading = first.lstrip("# ").strip().replace("|", "/")
            if cur_loc is None:
                cur_loc = (loc, heading)
            if para.startswith("<!-- ") and cur_len == 0 and cur and all(x.startswith("<!-- ") for x in cur):
                cur = []  # bỏ mốc vị trí liền nhau khi chưa có nội dung
            if cur and cur_len + len(para) > a.chunk_chars:
                chunks.append({"text": "\n\n".join(cur), "start": cur_loc, "end": (loc, heading)})
                cur, cur_len, cur_loc = [], 0, (loc, heading)
            cur.append(para)
            cur_len += 0 if para.startswith("<!-- ") else len(para)
            last_loc = loc
    if cur:
        chunks.append({"text": "\n\n".join(cur), "start": cur_loc, "end": (last_loc, heading)})

    cdir = pdir / "chunks"
    cdir.mkdir(exist_ok=True)
    for old in cdir.glob("chunk_*.md"):
        old.unlink()
    manifest = []
    for i, c in enumerate(chunks, 1):
        locs = [c["start"][0]] + ([c["end"][0]] if c["end"][0] != c["start"][0] else [])
        where = " - ".join(x for x in locs if x) or "-"
        label = c["start"][1] or "(đầu tài liệu)"
        (cdir / f"chunk_{i:03d}.md").write_text(
            f"<!-- chunk {i}/{len(chunks)} | vị trí: {where} | mục: {label} -->\n\n{c['text']}\n", encoding="utf-8")
        manifest.append({"chunk": i, "file": f"chunks/chunk_{i:03d}.md", "location": where, "section": label,
                         "chars": len(c["text"]), "has_ocr_draft": "⟦BẢN NHÁP OCR" in c["text"]})
    (pdir / "manifest.json").write_text(json.dumps({
        "source_file": str(src), "source_txt": str(pdir / "source.txt"), "total_chars": len(full), "chunks": manifest,
        "detected_format": man.get("detected_format"), "ingest_dir": man.get("out_dir"),
        "ingest_warnings": man.get("warnings") or [], "pages_needing_ocr": man.get("pages_needing_ocr") or [],
        "ocr_page_images": ocr_page_paths(man)}, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = ["| Chunk | Vị trí | Mục | Trạng thái | Ý chính (1 câu) |", "|---|---|---|---|---|"]
    rows += [f"| {m['chunk']} | {m['location']} | {m['section'][:50]} | Chưa đọc | |" for m in manifest]
    (pdir / "coverage.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"[OK] {man.get('detected_format')}: {len(full):,} ký tự -> {len(chunks)} chunk tại {cdir}")
    print(f"[OK] Nguồn kiểm chứng trích dẫn: {pdir / 'source.txt'}")
    print(f"[OK] Bảng độ phủ: {pdir / 'coverage.md'} (cập nhật 'Đã đọc' + ý chính sau mỗi chunk)")
    if man.get("images"):
        print(f"[OK] {man['images']} ảnh trích ra {Path(man['out_dir']) / 'media'} (chunk ghi [Hình: đường dẫn])")
    if partial:
        print(f"[PARTIAL] {explain(man, 'doc-sau')} Các trang này có trong chunk dưới dạng ⟦BẢN NHÁP OCR⟧ nhưng KHÔNG có "
              "trong source.txt → trích dẫn từ chúng sẽ không được kiểm chứng; ghi rõ '(trang scan, đọc từ ảnh)'.")
        return EXIT_PARTIAL
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
