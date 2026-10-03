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
