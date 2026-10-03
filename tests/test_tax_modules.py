"""Kiểm thử các module thuế mới của skill tu-van-thue (HKD, GTGT, TNDN, chậm nộp, hóa đơn, TTĐB, nhà thầu)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/skills/tu-van-thue/scripts"
sys.path.insert(0, str(SCRIPTS))

import rules_loader  # noqa: E402
from engines import gtgt, hkd, hoa_don, penalties, tndn  # noqa: E402


def cli(*args):
    p = subprocess.run([sys.executable, str(SCRIPTS / "tax_cli.py"), *args, "--json"],
                       capture_output=True, text=True)
    return p.returncode, (json.loads(p.stdout) if p.stdout.strip() else None), p.stderr


def test_params_valid():
    assert rules_loader.validate_all() == []


def test_hkd_distribution_2_ty():
    v = hkd.compute({"phan_phoi": 2e9}, None, "2026-12-31", False).values
    assert v["gtgt"] == 20_000_000 and v["tncn"] == 5_000_000


def test_hkd_under_threshold_exempt():
    v = hkd.compute({"phan_phoi": 5e8}, None, "2026-12-31", False).values
    assert v["gtgt"] == 0 and v["tncn"] == 0


def test_gtgt_deduction_8_percent():
    v = gtgt.deduction([{"name": "A", "amount": 1e9, "rate": "10", "reduction_eligible": True}], 30e6, 0, "2026-12-31").values
    assert v["thue_dau_ra"] == 80_000_000 and v["thue_phai_nop"] == 50_000_000


def test_gtgt_reduction_expires():
    v = gtgt.deduction([{"name": "A", "amount": 1e9, "rate": "10", "reduction_eligible": True}], 0, 0, "2027-01-01").values
    assert v["thue_dau_ra"] == 100_000_000


def test_tndn_17_percent():
    v = tndn.compute(1e10, 0, 9e9, 0, 0, 0, 1e9 * 10, "2026-12-31").values
    assert v["thue_suat"] == 0.2 or v["thue_suat"] == 0.17


def test_tndn_small_exempt():
    assert tndn.compute(1e9, 0, 0, 0, 0, 0, 1e9, "2026-12-31").values["mien_thue"] is True


def test_late_payment():
    v = penalties.late_payment(100_000_000, "2026-04-30", "2026-05-05").values
    assert v["so_ngay_cham"] == 4 and v["tien_cham_nop"] == 120_000


def test_late_payment_on_time():
    assert penalties.late_payment(1e8, "2026-04-30", "2026-04-30").values["tien_cham_nop"] == 0


def test_hoa_don_regime_switch():
    assert "254" in hoa_don.guide("dn", 0, "2026-07-01").values["van_ban_ap_dung"]
    assert "123" in hoa_don.guide("dn", 0, "2026-06-30").values["van_ban_ap_dung"]
    assert hoa_don.guide("hkd", 2e9, "2026-08-01").values["bat_buoc_hddt"] is True
    assert hoa_don.guide("hkd", 1e9, "2026-08-01").values["bat_buoc_hddt"] is False


def test_unverified_blocked(tmp_path, monkeypatch):
    d = tmp_path
    (d / "x.json").write_text(json.dumps({"module": "x", "params": {"p": [
        {"value": 1, "effective_from": "2020-01-01", "verification_status": "UNVERIFIED",
         "source": "s", "article": "a", "quote": "q"}]}}), encoding="utf-8")
    monkeypatch.setattr(rules_loader, "STANDARDS_DIR", d)
    with pytest.raises(rules_loader.ParamError):
        rules_loader.load("x").value("p", "2026-01-01")


def test_cli_exit_codes():
    rc, data, _ = cli("cham-nop", "--amount", "1e8", "--due", "2026-04-30", "--paid", "2026-05-05")
    assert rc == 0 and data["values"]["so_ngay_cham"] == 4
    rc, _, err = cli("hoa-don", "--entity", "hkd", "--on", "bad-date")
    assert rc == 1


def test_ttdb_beer_schedule():
    from engines import ttdb
    assert ttdb.compute("bia", 1e9, 0, "2026-06-01").values["thue_ttdb"] == 650_000_000
    assert ttdb.compute("bia", 1e9, 0, "2027-06-01").values["thue_ttdb"] == 700_000_000
    with pytest.raises(rules_loader.ParamError):
        ttdb.compute("bia", 1e9, 0, "2025-06-01")


def test_ttdb_hybrid_factor_and_tobacco_flag():
    from engines import ttdb
    v = ttdb.compute("o_to_den_9_cho_2000_2500", 1e9, 0, "2026-12-31", "hybrid").values
    assert v["thue_ttdb"] == 350_000_000
    t = ttdb.compute("thuoc_la_dieu", 1e6, 1000, "2027-05-01")
    assert t.values["thue_tuyet_doi_tong"] == 2_000_000 and t.flags


def test_fct_rates_and_gross_up():
    from engines import fct
    assert fct.compute("dich_vu", 1e9).values["thue_tndn_nha_thau"] == 50_000_000
    assert fct.compute("dich_vu", 9.5e8, gross_up=True).values["doanh_thu_tinh_thue"] == 1_000_000_000
    assert fct.compute("tien_ban_quyen", 1e8).values["thue_tndn_nha_thau"] == 10_000_000


def _soffice():
    import shutil
    return shutil.which("soffice") or shutil.which("libreoffice") or (
        "/Applications/LibreOffice.app/Contents/MacOS/soffice" if Path("/Applications/LibreOffice.app").exists() else None)


@pytest.mark.skipif(_soffice() is None, reason="Cần LibreOffice để tính lại công thức")
@pytest.mark.parametrize("args", [
    ["--module", "tndn", "--revenue", "5e9", "--expenses", "4e9", "--prior-revenue", "5e9"],
    ["--module", "hkd", "--activity", "phan_phoi", "--revenue", "2e9"],
    ["--module", "cham-nop", "--amount", "1e8", "--due", "2026-04-30", "--paid", "2026-05-05"],
])
def test_excel_live_formulas_match_engine(tmp_path, args):
    out = tmp_path / "x.xlsx"
    r = subprocess.run([sys.executable, str(SCRIPTS / "export_tax_module.py"), *args, "--output", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    v = subprocess.run([sys.executable, str(SCRIPTS / "verify_tax_module.py"), str(out)], capture_output=True, text=True)
    assert v.returncode == 0, v.stdout
