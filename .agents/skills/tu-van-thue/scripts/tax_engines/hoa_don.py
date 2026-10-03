"""Hướng dẫn sử dụng hóa đơn điện tử (chỉ hướng dẫn, không tính thuế).

Căn cứ đã đọc nguyên văn:
- HKD: NĐ 68/2026/NĐ-CP khoản 5 Điều 8 (sửa đổi bởi NĐ 141/2026/NĐ-CP Điều 1 khoản 2).
- Quy định chung: NĐ 123/2020/NĐ-CP (và NĐ 70/2025) đến hết 30/06/2026;
  từ 01/07/2026 theo NĐ 254/2026/NĐ-CP (hiệu lực 01/07/2026, Điều khoản thi hành) và TT 91/2026/TT-BTC.
"""
from __future__ import annotations

from rules_loader import parse_date
from .common import Result, fmt

NGUONG_HKD = 1_000_000_000
CUTOVER = "2026-07-01"


def guide(entity: str, revenue: float = 0.0, on="2026-12-31") -> Result:
    d = parse_date(on)
    r = Result(module="hoa_don.huong_dan")
    new_regime = d >= parse_date(CUTOVER)
    base = ("NĐ 254/2026/NĐ-CP và TT 91/2026/TT-BTC (từ 01/07/2026)" if new_regime
            else "NĐ 123/2020/NĐ-CP và NĐ 70/2025/NĐ-CP (đến hết 30/06/2026)")
    r.values["van_ban_ap_dung"] = base
    r.values["doi_tuong"] = entity
    if entity == "dn":
        r.values["bat_buoc_hddt"] = True
        r.step(f"Doanh nghiệp: sử dụng hóa đơn điện tử theo {base}.")
    elif entity == "hkd":
        r.values["doanh_thu_nam"] = revenue
        if revenue > NGUONG_HKD:
            r.values["bat_buoc_hddt"] = True
            r.step(f"Doanh thu năm {fmt(revenue)} đ > 1 tỷ: phải dùng hóa đơn điện tử có mã của cơ quan thuế "
                   "hoặc hóa đơn điện tử khởi tạo từ máy tính tiền kết nối dữ liệu với cơ quan thuế "
                   "(NĐ 68/2026 khoản 5 Điều 8, sửa đổi bởi NĐ 141/2026 Điều 1 khoản 2 điểm a).")
            r.step("Nếu năm trước chưa vượt 1 tỷ nhưng trong năm lũy kế vượt: đăng ký trong 30 ngày kể từ ngày "
                   "cuối cùng của kỳ tính thuế có doanh thu lũy kế vượt 1 tỷ (điểm c).")
        else:
            r.values["bat_buoc_hddt"] = False
            r.step(f"Doanh thu năm {fmt(revenue)} đ ≤ 1 tỷ: không bắt buộc; nếu đủ điều kiện và có nhu cầu thì "
                   "đăng ký hóa đơn điện tử có mã hoặc từ máy tính tiền (điểm b).")
        r.step("Nhiều địa điểm kinh doanh: dùng mã số thuế của hộ cho mọi cửa hàng và ghi rõ mã địa điểm trên hóa đơn (điểm a).")
    else:
        raise ValueError("entity phải là 'hkd' hoặc 'dn'")
    r.provenance.append({"source": "NĐ 68/2026/NĐ-CP, NĐ 141/2026/NĐ-CP, " + base, "status": "PRIMARY_VERIFIED"})
    r.warnings.append("Chi tiết nội dung, thời điểm lập hóa đơn, xử lý sai sót cần đối chiếu NĐ 254/2026 và TT 91/2026; "
                      "đây là hướng dẫn sơ bộ, không phải kết luận của cơ quan thuế.")
    return r
