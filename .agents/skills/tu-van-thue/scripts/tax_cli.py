#!/usr/bin/env python3
"""CLI chung cho các module thuế mới của skill tu-van-thue (ngoài TNCN lương/quyết toán, dùng tax_calculator.py).

  tax_cli.py hkd        --activity phan_phoi=2000000000 --activity dich_vu=300000000 [--expenses N] [--vat-reduction] [--on 2026-12-31] --json
  tax_cli.py tndn       --revenue N [--other-income N] [--expenses N] [--non-deductible N] [--exempt N] [--loss N] [--prior-revenue N] --json
  tax_cli.py gtgt       --line "Tên|doanh thu|rate|reduction(0/1)" ... [--input-vat N] [--carry N] --json
  tax_cli.py gtgt-direct --activity phan_phoi=N ... [--vat-reduction] --json
  tax_cli.py cham-nop   --amount N --due 2026-07-30 --paid 2026-08-05 --json
  tax_cli.py hoa-don    --entity hkd|dn --revenue N [--on 2026-07-01] --json
  tax_cli.py params     [--module gtgt] : in tham số, nguồn, trạng thái kiểm chứng

Mã thoát: 0 thành công; 1 dữ liệu đầu vào sai hoặc tham số chưa đủ độ tin cậy (ParamError); 2 lỗi khác.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tax_engines import gtgt, hkd, hoa_don, penalties, tndn, ttdb, fct  # noqa: E402
from rules_loader import ParamError, load, validate_all  # noqa: E402


def _acts(items):
    out = {}
    for it in items or []:
        if "=" not in it:
            raise ValueError(f"--activity phải có dạng loại=doanh_thu, nhận '{it}'")
        k, v = it.split("=", 1)
        out[k.strip()] = float(v)
    return out


def _lines(items):
    out = []
    for it in items or []:
        p = [x.strip() for x in it.split("|")]
        if len(p) < 3:
            raise ValueError(f"--line phải có dạng 'Tên|doanh thu|rate[|0/1]', nhận '{it}'")
        out.append({"name": p[0], "amount": float(p[1]), "rate": p[2],
                    "reduction_eligible": len(p) > 3 and p[3] in ("1", "true", "True")})
    return out


def build_parser():
    ap = argparse.ArgumentParser(description="Tư vấn thuế: HKD, TNDN, GTGT, chậm nộp, hóa đơn")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--json", action="store_true", help="Xuất JSON")
        p.add_argument("--on", default="2026-12-31", help="Ngày xét hiệu lực tham số (YYYY-MM-DD)")

    p = sub.add_parser("hkd"); common(p)
    p.add_argument("--activity", action="append", help="loại=doanh_thu_năm (phan_phoi, dich_vu, san_xuat, khac, cho_thue_tai_san, dai_ly, noi_dung_so, cho_thue_bds)")
    p.add_argument("--expenses", type=float, help="Chi phí hợp lệ cả năm (tính TNCN theo lợi nhuận)")
    p.add_argument("--vat-reduction", action="store_true", help="Giảm 20%% tỷ lệ GTGT (NĐ 174/2025)")

    p = sub.add_parser("tndn"); common(p)
    p.add_argument("--revenue", type=float, required=True)
    p.add_argument("--other-income", type=float, default=0)
    p.add_argument("--expenses", type=float, default=0)
    p.add_argument("--non-deductible", type=float, default=0)
    p.add_argument("--exempt", type=float, default=0)
    p.add_argument("--loss", type=float, default=0)
    p.add_argument("--prior-revenue", type=float, help="Tổng doanh thu kỳ tính thuế liền kề trước")

    p = sub.add_parser("gtgt"); common(p)
    p.add_argument("--line", action="append", help="'Tên|doanh thu|rate(0/5/10/KCT)|reduction(0/1)'")
    p.add_argument("--input-vat", type=float, default=0)
    p.add_argument("--carry", type=float, default=0)

    p = sub.add_parser("gtgt-direct"); common(p)
    p.add_argument("--activity", action="append")
    p.add_argument("--vat-reduction", action="store_true")

    p = sub.add_parser("cham-nop"); common(p)
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--due", required=True, help="Hạn nộp thuế (YYYY-MM-DD)")
    p.add_argument("--paid", required=True, help="Ngày thực nộp (YYYY-MM-DD)")

    p = sub.add_parser("hoa-don"); common(p)
    p.add_argument("--entity", required=True, choices=["hkd", "dn"])
    p.add_argument("--revenue", type=float, default=0)

    p = sub.add_parser("ttdb"); common(p)
    p.add_argument("--item", help="khóa hàng hóa/dịch vụ (xem --list)")
    p.add_argument("--price", type=float, default=0, help="Giá tính thuế (chưa TTĐB, BVMT, GTGT)")
    p.add_argument("--quantity", type=float, default=0, help="Số lượng (cho mức thuế tuyệt đối thuốc lá)")
    p.add_argument("--factor", choices=["hybrid", "sinh_hoc"], help="Xe xăng-điện/khí thiên nhiên (hybrid) hoặc nhiên liệu sinh học")
    p.add_argument("--price-includes-ttdb", action="store_true")
    p.add_argument("--list", action="store_true", help="Liệt kê khóa hàng hóa/dịch vụ")

    p = sub.add_parser("nha-thau"); common(p)
    p.add_argument("--item", help="loại thu nhập (xem lỗi gợi ý khi bỏ trống)")
    p.add_argument("--revenue", type=float, default=0)
    p.add_argument("--gross-up", action="store_true", help="Doanh thu nhập là số thực nhận, nhà thầu chịu thuế hộ")

    p = sub.add_parser("params")
    p.add_argument("--module", help="gtgt | tndn | hkd | ttdb | fct | quan_ly_thue")
    p.add_argument("--json", action="store_true")
    return ap


def run(a):
    if a.cmd == "hkd":
        return hkd.compute(_acts(a.activity), a.expenses, a.on, a.vat_reduction)
    if a.cmd == "tndn":
        return tndn.compute(a.revenue, a.other_income, a.expenses, a.non_deductible, a.exempt, a.loss, a.prior_revenue, a.on)
    if a.cmd == "gtgt":
        return gtgt.deduction(_lines(a.line), a.input_vat, a.carry, a.on)
    if a.cmd == "gtgt-direct":
        return gtgt.direct(_acts(a.activity), a.on, a.vat_reduction)
    if a.cmd == "cham-nop":
        return penalties.late_payment(a.amount, a.due, a.paid)
    if a.cmd == "hoa-don":
        return hoa_don.guide(a.entity, a.revenue, a.on)
    if a.cmd == "ttdb":
        if a.list or not a.item:
            raise ValueError("Khóa hợp lệ: " + ", ".join(ttdb.list_items()))
        return ttdb.compute(a.item, a.price, a.quantity, a.on, a.factor, a.price_includes_ttdb)
    if a.cmd == "nha-thau":
        if not a.item:
            raise ValueError("Khóa hợp lệ: " + ", ".join(fct.list_items()))
        return fct.compute(a.item, a.revenue, a.on, a.gross_up)
    raise ValueError(a.cmd)


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    try:
        if a.cmd == "params":
            errs = validate_all()
            mods = [a.module] if a.module else ["quan_ly_thue", "gtgt", "tndn", "hkd", "ttdb", "fct"]
            rows = []
            for m in mods:
                rs = load(m)
                for name, ents in rs.data.items():
                    for e in ents:
                        rows.append({"module": m, "param": name, "value": e["value"], "from": e["effective_from"],
                                     "to": e.get("effective_to"), "status": e["verification_status"],
                                     "source": e["source"], "article": e.get("article", "")})
            if a.json:
                print(json.dumps({"errors": errs, "params": rows}, ensure_ascii=False, indent=2))
            else:
                for x in rows:
                    print(f"[{x['status']}] {x['module']}.{x['param']} = {x['value']}  ({x['from']} -> {x['to'] or '...'})  {x['source']}, {x['article']}")
                print("✅ ĐẠT" if not errs else "\n".join(errs))
            return 1 if errs else 0
        res = run(a)
    except (ParamError, ValueError) as ex:
        print(f"✗ {ex}", file=sys.stderr)
        return 1
    except Exception as ex:  # noqa: BLE001 - báo lỗi rõ cho agent, không nuốt
        print(f"✗ Lỗi không mong đợi: {type(ex).__name__}: {ex}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
    else:
        for s in res.steps:
            print("•", s)
        for k, v in res.values.items():
            print(f"{k}: {v}")
        for w in res.warnings:
            print("⚠", w)
        for f in res.flags:
            print("[CẦN XÁC MINH]", f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
