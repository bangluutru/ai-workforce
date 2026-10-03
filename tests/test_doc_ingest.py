"""Kiểm thử scripts/doc_ingest.py (bộ chuyển đổi tài liệu dùng chung).

Chạy được bằng cả python3 hệ thống (script tự chạy lại bằng .venv nếu thiếu markitdown) và .venv/bin/python:
    python3 -m pytest tests/test_doc_ingest.py -q
    .venv/bin/python -m pytest tests/test_doc_ingest.py -q
Phần cần LibreOffice / Apple Vision tự skip khi máy không có.
Fixture: tests/fixtures/doc_ingest/ (sinh lại bằng make_fixtures.py).
"""
import json
import shutil
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "doc_ingest.py"
FX = ROOT / "tests" / "fixtures" / "doc_ingest"
sys.path.insert(0, str(ROOT / "scripts"))
import doc_ingest as di  # noqa: E402  (import chỉ dùng thư viện chuẩn)

HAS_SOFFICE = di.find_soffice() is not None
HAS_VISION = sys.platform == "darwin" and di.MAC_OCR_SWIFT.exists() and bool(shutil.which("swiftc") or shutil.which("swift"))
IN_PROCESS = not di._missing_modules()  # thư viện có sẵn trong tiến trình pytest hiện tại

needs_soffice = pytest.mark.skipif(not HAS_SOFFICE, reason="cần LibreOffice (soffice)")
needs_vision = pytest.mark.skipif(not HAS_VISION, reason="cần macOS + Apple Vision (swift)")

P1 = "Nghị định 30/2020/NĐ-CP quy định thể thức văn bản hành chính tại Thành phố Hồ Chí Minh."
P2 = "Kiểm tra dấu: ấ ầ ẩ ẫ ậ ắ ằ ẳ ẵ ặ ế ề ể ễ ệ ố ồ ổ ỗ ộ ớ ờ ở ỡ ợ ứ ừ ử ữ ự ỳ ỷ ỹ ỵ đ Đ."
P3 = "Mọi nghĩa vụ thuế thu nhập cá nhân phải được thực hiện đúng hạn."
ROW_RE = r"\|\s*Giấy A4 định lượng 80\s*\|\s*15\s*\|\s*72\.?000\s*\|"

GOOD = ["sample.docx", "sample.xlsx", "sample_nocache.xlsx", "sample.pptx", "sample.epub", "sample.csv",
        "cp1258.txt", "tcvn3.txt", "tcvn3.docx", "sample.pdf", "scanned.pdf", "scan.jpg"]
LEGACY = ["sample.odt", "sample.doc", "sample.rtf"]


def run_cli(*args, cwd=None):
    r = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", cwd=cwd, timeout=900)
    return r


def flat(s: str) -> str:
    import re
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s))


@pytest.fixture(scope="module")
def batch(tmp_path_factory):
    """Chạy CLI MỘT lần cho toàn bộ fixture (cũng kiểm tra chế độ nhiều tệp + index.json)."""
    out = tmp_path_factory.mktemp("ingest")
    files = [FX / f for f in GOOD + LEGACY]
    r = run_cli(*files, "--out", out, "--json")
    assert r.stdout.strip(), r.stderr
    payload = json.loads(r.stdout)
    res = {}
    for m in payload["results"]:
        d = Path(m["out_dir"])
        res[m["input_name"]] = {"man": m, "md": (d / "source.md").read_text("utf-8"), "dir": d}
    return {"out": out, "payload": payload, "rc": r.returncode, "res": res}


def get(batch, name):
    item = batch["res"][name]
    man = item["man"]
    if man["status"] == "missing_dependency":
        pytest.skip(man["message"])
    return item


# ── chế độ nhiều tệp ─────────────────────────────────────────────────────────
def test_multi_input_layout(batch):
    out = batch["out"]
    idx = json.loads((out / "index.json").read_text("utf-8"))
    assert {r["folder"] for r in idx["results"]} >= {"sample-docx", "sample-xlsx", "sample-pptx", "scanned-pdf"}
    for r in idx["results"]:
        assert (out / r["folder"] / "manifest.json").exists()
        assert (out / r["folder"] / "source.md").exists()
    # scan → partial (3) là mức nặng nhất khi mọi tệp khác đọc được
    expected = 3 if HAS_SOFFICE else 4
    assert batch["rc"] == expected == batch["payload"]["exit_code"]


def test_manifest_contract(batch):
    man = get(batch, "sample.docx")["man"]
    for k in ("input", "detected_format", "converter_chain", "pages", "sheets", "slides", "chapters", "chars",
              "tables", "images", "warnings", "pages_needing_ocr", "legacy_encoding", "status", "exit_code"):
        assert k in man, k
    assert man["status"] == "ok" and man["exit_code"] == 0


# ── DOCX / ODT / DOC / RTF ──────────────────────────────────────────────────
def _assert_word_like(item):
    import re
    md = item["md"]
    f = flat(md)
    assert P1 in f and P2 in f and P3 in f
    assert re.search(ROW_RE, md), md
    assert re.search(r"(?m)^#+ Chương 1: Mở đầu", md)
    assert f.index("Chương 1") < f.index("Chương 2")
    assert item["man"]["tables"] >= 1
    assert item["man"]["images"] >= 1
    import re as _re
    for ref in _re.findall(r"!\[[^\]]*\]\((media/[^)]+)\)", md):
        assert (item["dir"] / ref).exists()
    assert "](media/" in md


def test_docx(batch):
    item = get(batch, "sample.docx")
    _assert_word_like(item)
    assert "Công ty Thử Nghiệm" in item["md"]  # đầu trang (header)
    assert item["man"]["detected_format"] == "docx"


@needs_soffice
@pytest.mark.parametrize("name", LEGACY)
def test_legacy_word_formats(batch, name):
    item = get(batch, name)
    _assert_word_like(item)
    assert any(s.startswith("soffice:") for s in item["man"]["converter_chain"])


# ── XLSX ────────────────────────────────────────────────────────────────────
def test_xlsx_values_and_formulas(batch):
    item = get(batch, "sample.xlsx")
    md, man = item["md"], item["man"]
    assert man["sheets"] == 2
    assert "## Sheet 1: Chi phí" in md and "## Sheet 2: Tổng hợp" in md
    assert "`=SUM(D2:D4)` | 3300000" in md
    assert "`='Chi phí'!D5` | 3300000" in md
    assert "| 3 | Giấy A4 định lượng 80 | 15 | 72000 | 1080000 |" in md


def test_xlsx_without_cached_values(batch):
    item = get(batch, "sample_nocache.xlsx")
    md, man = item["md"], item["man"]
    assert "`=SUM(D2:D4)`" in md
    if HAS_SOFFICE:
        assert "soffice-recalc" in man["converter_chain"]
        assert "| 5 | Tổng cộng | 139 |  | 3300000 |" in md
    else:
        assert any("chưa lưu giá trị công thức" in w for w in man["warnings"])


# ── PPTX ────────────────────────────────────────────────────────────────────
def test_pptx_slides_notes_table_chart_image(batch):
    import re
    item = get(batch, "sample.pptx")
    md, man = item["md"], item["man"]
    assert man["slides"] == 3
    for n in (1, 2, 3):
        assert f"## Slide {n}" in md
    assert md.count("### Ghi chú diễn giả (notes)") == 3
    assert "Ghi chú bảng: đơn giá đã gồm VAT." in md
    assert re.search(r"\| Giấy A4 định lượng 80 \| 15 \| 72000 \|", md)
    assert "| Quý II | 15.0 |" in md  # dữ liệu biểu đồ
    assert man["images"] == 1 and "](media/slide003_img" in md
    assert P2 in flat(md)


# ── EPUB ────────────────────────────────────────────────────────────────────
def test_epub_spine_order_and_image(batch):
    item = get(batch, "sample.epub")
    md, man = item["md"], item["man"]
    assert man["chapters"] == 2
    f = flat(md)
    # z_chuong1.xhtml đứng trước a_chuong2.xhtml theo spine (ngược thứ tự tên tệp)
    assert 0 <= f.index("Chương 1: Mở đầu") < f.index("Chương 2: Kết luận")
    assert P1 in f and man["images"] == 1


def test_epub_drm_is_unreadable(tmp_path):
    drm = tmp_path / "drm.epub"
    with zipfile.ZipFile(FX / "sample.epub") as src, zipfile.ZipFile(drm, "w") as dst:
        for it in src.infolist():
            dst.writestr(it, src.read(it.filename))
        dst.writestr("META-INF/encryption.xml",
                     '<encryption xmlns="urn:oasis:names:tc:opendocument:xmlns:container" '
                     'xmlns:enc="http://www.w3.org/2001/04/xmlenc#"><enc:EncryptedData><enc:EncryptionMethod '
                     'Algorithm="http://www.w3.org/2001/04/xmlenc#aes128-cbc"/><enc:CipherData><enc:CipherReference '
                     'URI="OEBPS/text/z_chuong1.xhtml"/></enc:CipherData></enc:EncryptedData></encryption>')
    r = run_cli(drm, "--out", tmp_path / "o", "--json")
    man = json.loads(r.stdout)
    if man["status"] == "missing_dependency":
        pytest.skip(man["message"])
    assert r.returncode == 2 and man["status"] == "unreadable"
    assert "DRM" in man["message"]


# ── Văn bản / CSV / mã cũ ───────────────────────────────────────────────────
def test_csv(batch):
    item = get(batch, "sample.csv")
    assert "| Giấy A4 định lượng 80 | 15 | 72000 | 1080000 |" in item["md"]
    assert item["man"]["tables"] == 1


def test_cp1258_text(batch):
    item = get(batch, "cp1258.txt")
    assert P1 in item["md"] and P3 in item["md"]
    assert item["md"] == unicodedata.normalize("NFC", item["md"])
    assert item["man"]["legacy_encoding"] == "cp1258"


@pytest.mark.parametrize("name", ["tcvn3.txt", "tcvn3.docx"])
def test_tcvn3_converted(batch, name):
    item = get(batch, name)
    md = item["md"]
    assert "Cộng hoà xã hội chủ nghĩa Việt Nam" in md
    assert "Độc lập - Tự do - Hạnh phúc" in md
    assert "Người lao động phải được trả lương đúng hạn." in md
    assert item["man"]["legacy_encoding"] == "tcvn3"
    if name.endswith(".docx"):
        assert "CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM" in md  # .VnTimeH


# ── PDF ─────────────────────────────────────────────────────────────────────
def test_text_pdf(batch):
    import re
    item = get(batch, "sample.pdf")
    md, man = item["md"], item["man"]
    assert md.lstrip().startswith("<!-- page 1 -->")
    f = flat(md)
    assert P1 in f and P3 in f
    assert re.search(ROW_RE, md)
    assert man["pages"] == 1 and man["pages_needing_ocr"] == [] and man["exit_code"] == 0


def test_scanned_pdf_partial(batch):
    item = get(batch, "scanned.pdf")
    man = item["man"]
    assert man["exit_code"] == 3 and man["status"] == "partial"
    assert man["pages_needing_ocr"] == [1]
    assert (item["dir"] / "ocr_pages" / "page_001.png").exists()
    assert "ocr_pages/page_001.png" in item["md"]


@needs_vision
def test_scanned_pdf_vision_draft(batch):
    item = get(batch, "scanned.pdf")
    assert item["man"]["ocr_pages"][0]["draft_engine"] == "apple_vision"
    assert "30/2020" in item["md"] and "ocr-draft:start" in item["md"]


def test_image_input_is_one_page_scan(batch):
    item = get(batch, "scan.jpg")
    assert item["man"]["detected_format"] == "jpeg"
    assert item["man"]["exit_code"] == 3 and item["man"]["pages_needing_ocr"] == [1]


def test_password_pdf(tmp_path):
    r = run_cli(FX / "password.pdf", "--out", tmp_path, "--json")
    man = json.loads(r.stdout)
    if man["status"] == "missing_dependency":
        pytest.skip(man["message"])
    assert r.returncode == 2 and man["status"] == "unreadable"
    assert "mật khẩu" in man["message"]
    assert "KHÔNG ĐỌC ĐƯỢC" in (tmp_path / "source.md").read_text("utf-8")


def test_no_ocr_flag(tmp_path):
    r = run_cli(FX / "scanned.pdf", "--out", tmp_path, "--json", "--no-ocr")
    man = json.loads(r.stdout)
    if man["status"] == "missing_dependency":
        pytest.skip(man["message"])
    assert r.returncode == 3
    assert man["ocr_pages"][0]["draft_engine"] is None
    assert (tmp_path / "ocr_pages" / "page_001.png").exists()


# ── Lỗi & tuỳ chọn ──────────────────────────────────────────────────────────
def test_empty_file(tmp_path):
    e = tmp_path / "rong.docx"
    e.write_bytes(b"")
    r = run_cli(e, "--out", tmp_path / "o", "--json")
    man = json.loads(r.stdout)
    assert r.returncode == 2 and man["detected_format"] in ("empty", None)
    assert "rỗng" in man["message"] or man["status"] == "missing_dependency"


def test_unknown_binary_and_missing_file(tmp_path):
    b = tmp_path / "la.bin"
    b.write_bytes(bytes(range(256)) * 8)
    r = run_cli(b, tmp_path / "khong-co.pdf", "--out", tmp_path / "o")
    assert r.returncode in (2, 4)
    idx = json.loads((tmp_path / "o" / "index.json").read_text("utf-8"))
    assert all(x["exit_code"] in (2, 4) for x in idx["results"])


def test_magic_bytes_not_extension(tmp_path):
    fake = tmp_path / "thuc-ra-la-word.pdf"
    shutil.copy(FX / "sample.docx", fake)
    r = run_cli(fake, "--out", tmp_path / "o", "--json")
    man = json.loads(r.stdout)
    if man["status"] == "missing_dependency":
        pytest.skip(man["message"])
    assert man["detected_format"] == "docx" and r.returncode == 0
    assert di.detect_format(FX / "sample.epub")[0] == "epub"
    assert di.detect_format(FX / "sample.xlsx")[0] == "xlsx"
    assert di.detect_format(FX / "sample.doc")[0] == "doc"


def test_max_chars_truncates_with_warning(tmp_path):
    r = run_cli(FX / "sample.docx", "--out", tmp_path, "--json", "--max-chars", "120")
    man = json.loads(r.stdout)
    if man["status"] == "missing_dependency":
        pytest.skip(man["message"])
    assert r.returncode == 0 and man["truncated"] is True
    assert (tmp_path / "source_full.md").exists()
    assert len((tmp_path / "source.md").read_text("utf-8")) < len((tmp_path / "source_full.md").read_text("utf-8"))
    assert any("--max-chars" in w for w in man["warnings"])


def test_rerun_same_out_dir_cleans_previous(tmp_path):
    run_cli(FX / "sample.docx", "--out", tmp_path)
    assert (tmp_path / "media").exists()
    r = run_cli(FX / "sample.csv", "--out", tmp_path, "--json")
    man = json.loads(r.stdout)
    if man["status"] == "missing_dependency":
        pytest.skip(man["message"])
    assert not (tmp_path / "media").exists()


def test_python_api(tmp_path):
    man = di.ingest(FX / "sample.csv", tmp_path)
    if man["status"] == "missing_dependency":
        pytest.skip(man["message"])
    assert man["status"] == "ok" and man["exit_code"] == 0
    assert "Giấy A4" in (tmp_path / "source.md").read_text("utf-8")


@pytest.mark.skipif(not IN_PROCESS, reason="cần thư viện trong tiến trình hiện tại để giả lập thiếu LibreOffice")
def test_missing_soffice_exit_4(tmp_path, monkeypatch):
    monkeypatch.setattr(di, "find_soffice", lambda: None)
    man = di.ingest(FX / "sample.doc", tmp_path)
    assert man["exit_code"] == 4 and man["status"] == "missing_dependency"
    assert "brew install --cask libreoffice" in man["message"]


# ── Đơn vị: mã TCVN3, giải mã, rơi dấu ─────────────────────────────────────
def test_tcvn3_table_is_bijective():
    vals = list(di._TCVN3.values())
    assert len(vals) == len(set(vals)) == 74
    assert all(0xA1 <= k <= 0xFE for k in di._TCVN3)


def test_detect_legacy_no_false_positive():
    assert di.detect_legacy(P1 + " " + P3) is None
    assert di.detect_legacy("Le café « crème » coûte trop cher à Paris, où l'été est chaud.") is None
    assert di.detect_legacy("Coäng hoøa xaõ hoäi chuû nghóa Vieät Nam. Ñoäc laäp - Töï do - Haïnh phuùc") == "vni"


def test_decode_utf16_and_utf8_bom():
    assert di.decode_bytes(("﻿" + P1).encode("utf-16-le"))[0].lstrip("﻿") == P1
    assert di.decode_bytes(b"\xef\xbb\xbf" + P1.encode())[0] == P1


def test_diacritic_damage_prefers_intact_extractor():
    damaged = ("Ngh đ nh 30/2020/NĐ-CP quy đ nh th th c văn b n hành chính t i Thành ph H Chí Minh "
               "ịị ị ể ứ ả ạ ố ồ. M i nghĩa v thu thu nh p cá nhân ph i đ c th c hi n đúng h n.")
    good = P1 + " " + P3 + " " + P1
    assert di.diacritic_damage(damaged) > 0.08
    assert di.diacritic_damage(good) < 0.02
    name, text, _ = di.choose_least_damaged(("pymupdf", damaged), [("pdftotext-layout", good)])
    assert name == "pdftotext-layout" and text == good
    assert di.choose_least_damaged(("pdfplumber", good), [("x", damaged)])[0] == "pdfplumber"
