"""bao-cao-kt/scripts/tables_from_source.py: bảng source.md (doc_ingest) → số chuẩn hoá + nguồn + đối chiếu tổng B02."""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / ".agents" / "skills" / "bao-cao-kt" / "scripts" / "tables_from_source.py"
spec = importlib.util.spec_from_file_location("tables_from_source", SCRIPT)
tfs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tfs)


@pytest.mark.parametrize("text,machine,expected", [
    ("1.234.567", False, 1234567),
    ("12.345.678.900", False, 12345678900),
    ("(1.234)", False, -1234),
    ("-1.234", False, -1234),
    ("1.234,5", False, 1234.5),
    ("1,234,567", False, 1234567),
    ("28,6%", False, 0.286),
    ("3.5", False, 3.5),
    ("2.700.000.000 đ", False, 2700000000),
    ("-", False, None),
    ("", False, None),
    ("VI.25", False, None),
    ("1.234", True, 1.234),          # ô sheet XLSX là số máy: không coi '.' là phân cách nghìn
    ("2700000000", True, 2700000000),
])
def test_parse_vn_number(text, machine, expected):
    assert tfs.parse_vn_number(text, machine=machine) == expected


XLSX_MD = """## Sheet 1: KQKD

| # | A | B | C | D | E |
|---|---|---|---|---|---|
| 3 | Chỉ tiêu | Mã số | Thuyết minh | Năm nay | Năm trước |
| 4 | Doanh thu bán hàng | 01 | IV.08 | 2700000000 | 2100000000 |
| 5 | Giá vốn hàng bán | 11 |  | 1600000000 | 1300000000 |
| 6 | Lợi nhuận gộp | 20 |  | 1100000000 | 800000000 |
| 7 | Chi phí quản lý kinh doanh | 24 |  | 550000000 | 480000000 |

### Công thức — KQKD

| Ô | Công thức | Giá trị đã tính |
|---|---|---|
| D6 | `=D4-D5` | 1100000000 |
"""

PDF_MD = """<!-- page 2 -->
|     | Chỉ tiêu | Mã số Thuyết minh | Năm 2025 | Năm 2024 |
| --- | --- | --- | --- | --- |

Doanh thu bán hàng và cung cấp dịch vụ 01 VI.25 12.345.678.900 10.000.000.000

| Giá vốn hàng bán |  | 11 VI.27 | (8.000.000.000) | (7.000.000.000) |
| --- | --- | --- | --- | --- |
| Lợi nhuận gộp |  | 20 | 4.345.678.900 | 3.000.000.000 |
"""


def test_xlsx_cells_and_totals():
    tables = tfs.collect_tables(XLSX_MD)
    cands, totals = tfs.pnl_candidates(tables, XLSX_MD)
    assert cands["01"]["curr"] == 2700000000 and cands["01"]["prev"] == 2100000000
    assert cands["01"]["src"]["curr"] == "Sheet 1 'KQKD' ô D4"
    assert cands["24"]["src"]["prev"] == "Sheet 1 'KQKD' ô E7"
    checks, regime = tfs.reconcile(cands, totals)
    assert regime == "TT133"
    assert [c["code"] for c in checks] == ["20"] and checks[0]["ok"]


def test_pdf_rows_page_negatives_and_text_lines():
    tables = tfs.collect_tables(PDF_MD)
    cands, totals = tfs.pnl_candidates(tables, PDF_MD)
    assert cands["11"]["curr"] == 8000000000          # (8.000.000.000) giá vốn → nhập dương
    assert any("số dương" in n for n in cands["11"]["notes"])
    assert cands["11"]["src"]["curr"].startswith("trang 2")
    assert cands["01"]["curr"] == 12345678900 and cands["01"]["prev"] == 10000000000   # dòng chữ ngoài bảng
    checks, _ = tfs.reconcile(cands, totals)
    assert checks and all(c["ok"] for c in checks)


def test_totals_mismatch_flagged():
    md = XLSX_MD.replace("| 6 | Lợi nhuận gộp | 20 |  | 1100000000 |", "| 6 | Lợi nhuận gộp | 20 |  | 1100000500 |")
    cands, totals = tfs.pnl_candidates(tfs.collect_tables(md), md)
    checks, _ = tfs.reconcile(cands, totals)
    assert not checks[0]["ok"] and checks[0]["diff"]["curr"] == 500
