# MẪU BÁO CÁO KẾT QUẢ KINH DOANH (P&L STATEMENT TEMPLATE)

> Mẫu chuẩn theo Thông tư 200/2014/TT-BTC kết hợp quản trị kinh doanh hiện đại. Kèm công thức Excel động (Live Formulas).

| STT | CHỈ TIÊU BÁO CÁO | MÃ SỐ | THUYẾT MINH | KỲ NÀY (C) | KỲ TRƯỚC (D) | TĂNG TRƯỞNG (%) | CÔNG THỨC EXCEL (KỲ NÀY) |
|:---:|------------------|:-----:|:-----------:|:----------:|:------------:|:---------------:|:-------------------------|
| 1 | **1. Doanh thu bán hàng và cung cấp dịch vụ** | **01** | VI.25 | [Số tiền] | [Số tiền] | `=(E5-F5)/F5` | Nhập thô hoặc `=SUM(...)` |
| 2 | 2. Các khoản giảm trừ doanh thu | 02 | | [Số tiền] | [Số tiền] | `=(E6-F6)/F6` | Nhập thô |
| 3 | **3. Doanh thu thuần về bán hàng và CCDV (10 = 01 - 02)** | **10** | | `=$E$5-$E$6` | `=$F$5-$F$6` | `=(E7-F7)/F7` | `=E5-E6` |
| 4 | 4. Giá vốn hàng bán | 11 | VI.27 | [Số tiền] | [Số tiền] | `=(E8-F8)/F8` | Nhập thô |
| 5 | **5. Lợi nhuận gộp về bán hàng và CCDV (20 = 10 - 11)** | **20** | | `=$E$7-$E$8` | `=$F$7-$F$8` | `=(E9-F9)/F9` | `=E7-E8` |
| | *Biên lợi nhuận gộp (Gross Margin %)* | *GM* | | `=$E$9/$E$7` | `=$F$9/$F$7` | `=(E10-F10)/F10` | `=E9/E7` |
| 6 | 6. Doanh thu hoạt động tài chính | 21 | VI.26 | [Số tiền] | [Số tiền] | `=(E11-F11)/F11` | Nhập thô |
| 7 | 7. Chi phí tài chính | 22 | VI.28 | [Số tiền] | [Số tiền] | `=(E12-F12)/F12` | Nhập thô |
| 8 | *Trong đó: Chi phí lãi vay* | 23 | | [Số tiền] | [Số tiền] | `=(E13-F13)/F13` | Nhập thô |
| 9 | 8. Chi phí bán hàng | 25 | | [Số tiền] | [Số tiền] | `=(E14-F14)/F14` | `=SUM(...)` chi tiết |
| 10 | 9. Chi phí quản lý doanh nghiệp | 26 | | [Số tiền] | [Số tiền] | `=(E15-F15)/F15` | `=SUM(...)` chi tiết |
| 11 | **10. Lợi nhuận thuần từ HĐKD {30 = 20 + (21 - 22) - 25 - 26}** | **30** | | `=E9+(E11-E12)-E14-E15` | `=F9+(F11-F12)-F14-F15` | `=(E16-F16)/F16` | `=E9+(E11-E12)-E14-E15` |
| 12 | 11. Thu nhập khác | 31 | | [Số tiền] | [Số tiền] | `=(E17-F17)/F17` | Nhập thô |
| 13 | 12. Chi phí khác | 32 | | [Số tiền] | [Số tiền] | `=(E18-F18)/F18` | Nhập thô |
| 14 | 13. Lợi nhuận khác (40 = 31 - 32) | 40 | | `=E17-E18` | `=F17-F18` | `=(E19-F19)/F19` | `=E17-E18` |
| 15 | **14. Tổng lợi nhuận kế toán trước thuế (50 = 30 + 40)** | **50** | | `=E16+E19` | `=F16+F19` | `=(E20-F20)/F20` | `=E16+E19` |
| 16 | 15. Chi phí thuế TNDN hiện hành (20%) | 51 | VI.30 | `=MAX(0, E20*0.2)` | `=MAX(0, F20*0.2)` | `=(E21-F21)/F21` | `=MAX(0, E20*0.2)` |
| 17 | **16. Lợi nhuận sau thuế TNDN (60 = 50 - 51)** | **60** | | `=E20-E21` | `=F20-F21` | `=(E22-F22)/F22` | `=E20-E21` |
| | *Biên lợi nhuận ròng (Net Margin %)* | *NM* | | `=$E$22/$E$7` | `=$F$22/$F$7` | | `=E22/E7` |

---

### GHI CHÚ ĐỊNH DẠNG:
- Dòng 60 (Lợi nhuận sau thuế) được định dạng **KẺ ĐÔI DƯỚI CÙNG (Double Bottom Border)** và in đậm.
- Định dạng tiền tệ VND: `#,##0 "₫"`.
- Định dạng biên lợi nhuận: `0.0%`.
