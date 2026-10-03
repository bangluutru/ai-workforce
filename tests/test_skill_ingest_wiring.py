"""Kiểm thử nối các skill đọc tài liệu với bộ chuyển đổi dùng chung (scripts/doc_ingest.py).

- .agents/skills/_shared/doc_ingest_bridge.py: md_blocks, pdf_preflight
- doc-sau/scripts/ingest.py: mọi định dạng → source.txt + chunk; mã thoát 0/2/3
- ejv-translate/scripts/extract_text.py: định tuyến theo magic bytes, DOCX giữ thứ tự thân, XLSX/PPTX qua doc_ingest,
  PDF scan → 3, PDF mật khẩu → 2

Chạy: .venv/bin/python -m pytest tests/test_skill_ingest_wiring.py -q
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "tests" / "fixtures" / "doc_ingest"
SKILLS = ROOT / ".agents" / "skills"
sys.path.insert(0, str(SKILLS / "_shared"))
import doc_ingest_bridge as bridge  # noqa: E402

DOC_SAU = SKILLS / "doc-sau" / "scripts" / "ingest.py"
EJV = SKILLS / "ejv-translate" / "scripts" / "extract_text.py"
ROW = "Giấy A4 định lượng 80"


def run(args, **kw):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8", **kw)


# ── bridge ──────────────────────────────────────────────────────────────────
def test_md_blocks_structure():
    md = ("<!-- page 1 -->\n# Tiêu đề\n\nĐoạn một\ndòng hai.\n\n- mục A\n- mục B\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
          "![hình](media/x.png)\n\n<!-- page 2 -->\n> [!WARNING] Trang 2 cần OCR\n\n"
          "<!-- ocr-draft:start page=2 engine=x -->\nnháp chưa kiểm chứng\n<!-- ocr-draft:end -->\n")
    blocks = bridge.md_blocks(md)
    types = [b["type"] for b in blocks]
    assert types == ["page", "heading", "paragraph", "list_item", "list_item", "table", "image", "page", "ocr_notice"]
    assert blocks[2]["text"] == "Đoạn một dòng hai."
    assert blocks[5]["rows"] == [["a", "b"], ["1", "2"]]
    assert not any("nháp" in (b.get("text") or "") for b in blocks)


@pytest.mark.parametrize("name,code,kind", [
    ("sample.pdf", 0, "pdf"), ("password.pdf", 2, "pdf"), ("scanned.pdf", 3, "pdf"),
    ("sample.docx", 2, "docx"), ("scan.jpg", 2, "jpeg"),
])
def test_pdf_preflight(name, code, kind):
    pf = bridge.pdf_preflight(FX / name)
    assert pf["code"] == code and pf["kind"] == kind, pf
    if name == "password.pdf":
        assert "mật khẩu" in pf["message"]
    if name == "sample.docx":
        assert "--outdir" in pf["message"]  # không gợi ý lệnh soffice ghi đè tệp nguồn


# ── doc-sau ─────────────────────────────────────────────────────────────────
def test_doc_sau_xlsx_tables_rows(tmp_path):
    r = run([DOC_SAU, FX / "sample.xlsx", "--process-dir", tmp_path])
    assert r.returncode == 0, r.stdout + r.stderr
    src = (tmp_path / "source.txt").read_text("utf-8")
    assert re.search(ROW + r" \| 15 \| 72\.?000", src), src[:400]
    man = json.loads((tmp_path / "manifest.json").read_text("utf-8"))
    assert man["detected_format"] == "xlsx" and man["chunks"][0]["location"].startswith("sheet")


def test_doc_sau_cp1258_decoded(tmp_path):
    big = tmp_path / "cp.txt"
    big.write_bytes((FX / "cp1258.txt").read_bytes() * 4)
    r = run([DOC_SAU, big, "--process-dir", tmp_path / "p"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Nghị định" in (tmp_path / "p" / "source.txt").read_text("utf-8")


@pytest.mark.parametrize("name,code", [("password.pdf", 2), ("scanned.pdf", 3)])
def test_doc_sau_unreadable_and_scan(tmp_path, name, code):
    r = run([DOC_SAU, FX / name, "--process-dir", tmp_path])
    assert r.returncode == code, r.stdout + r.stderr
    assert not (tmp_path / "source.txt").exists() or "OCR" not in (tmp_path / "source.txt").read_text("utf-8")


# ── ejv-translate ───────────────────────────────────────────────────────────
def ejv(tmp_path, name):
    out = tmp_path / "extracted_blocks.json"
    r = run([EJV, "--input", FX / name, "--output", out])
    blocks = json.loads(out.read_text("utf-8")) if out.exists() else None
    return r, blocks


def test_ejv_docx_body_order_and_image(tmp_path):
    r, blocks = ejv(tmp_path, "sample.docx")
    assert r.returncode == 0, r.stderr
    types = [b["type"] for b in blocks]
    i_table = types.index("table")
    i_ch2 = next(i for i, b in enumerate(blocks) if (b.get("text") or "").startswith("Chương 2"))
    assert i_table < i_ch2, "bảng DOCX phải nằm đúng vị trí trong thân văn bản, không dồn xuống cuối"
    img = [b for b in blocks if b["type"] == "image"]
    assert img and Path(img[0]["src"]).is_file()


@pytest.mark.parametrize("name", ["sample.xlsx", "sample.pptx", "sample.epub", "sample.csv"])
def test_ejv_tables_via_ingest_or_native(tmp_path, name):
    r, blocks = ejv(tmp_path, name)
    assert r.returncode == 0, r.stderr
    tables = [b for b in blocks if b["type"] == "table"]
    flat = json.dumps(tables, ensure_ascii=False)
    assert ROW in flat
    assert "Công thức" not in flat and "=SUM" not in flat  # bảng công thức XLSX không đưa đi dịch
    rep = json.loads((tmp_path / "extraction_report.json").read_text("utf-8"))
    assert rep["exit_code"] == 0


@pytest.mark.parametrize("name,code", [("scanned.pdf", 3), ("password.pdf", 2), ("scan.jpg", 3)])
def test_ejv_refuses_scan_and_password(tmp_path, name, code):
    r, blocks = ejv(tmp_path, name)
    assert r.returncode == code, r.stdout + r.stderr
    assert blocks is None and "✅" not in r.stdout


def test_ejv_cp1258_text(tmp_path):
    r, blocks = ejv(tmp_path, "cp1258.txt")
    assert r.returncode == 0
    assert "Nghị định" in json.dumps(blocks, ensure_ascii=False)
