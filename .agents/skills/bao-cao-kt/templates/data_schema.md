# Schema `data.json` cho bao-cao-kt (v2)

Ví dụ đầy đủ, chạy được: `templates/data_example.json`. Cả 3 script (`build_excel_dashboard.py`, `export_slides_deck.py`, `verify_report.py`) đọc CÙNG một file này. Script KHÔNG tự điền số mẫu: thiếu trường bắt buộc thì in `❌ LỖI DỮ LIỆU` và thoát mã 2. Đọc thông báo lỗi, sửa data.json, chạy lại.

## Trường bắt buộc

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `company_name` | chuỗi | Tên doanh nghiệp thật của người dùng |
| `report_title` | chuỗi | Ví dụ "BÁO CÁO KẾT QUẢ KINH DOANH NĂM 2025" |
| `period` | chuỗi | Ví dụ "Năm 2025 so với năm 2024" |
| `regime` | `"TT200"` \| `"TT133"` \| `"TT99"` | Chọn mẫu B02 theo chế độ kế toán của DN (xem SKILL.md mục 3) |
| `pnl` | object | Số liệu NHẬP theo mã chỉ tiêu, dạng `{"01": {"curr": số, "prev": số}}` |

## `pnl` - chỉ nhập các mã NHẬP LIỆU

| Mã | Chỉ tiêu | TT200/TT99 | TT133 |
|---|---|:---:|:---:|
| 01 | Doanh thu bán hàng và CCDV (**bắt buộc**) | ✓ | ✓ |
| 02 | Các khoản giảm trừ doanh thu | ✓ | ✓ |
| 11 | Giá vốn hàng bán (**bắt buộc**) | ✓ | ✓ |
| 21 | Doanh thu hoạt động tài chính | ✓ | ✓ |
| 22 | Chi phí tài chính | ✓ | ✓ |
| 23 | Trong đó chi phí lãi vay (không tham gia công thức) | ✓ | ✓ |
| 24 | Chi phí quản lý kinh doanh | - | ✓ |
| 25 | Chi phí bán hàng | ✓ | - |
| 26 | Chi phí quản lý doanh nghiệp | ✓ | - |
| 31 | Thu nhập khác | ✓ | ✓ |
| 32 | Chi phí khác | ✓ | ✓ |
| 51 | Chi phí thuế TNDN hiện hành THỰC TẾ (nếu có tờ khai quyết toán) | ✓ | ✓ |
| 52 | Chi phí thuế TNDN hoãn lại | ✓ | - |

- Mã TÍNH TOÁN (10, 20, 30, 40, 50, 60, GM, NM) **không được nhập**. Script tự sinh công thức Excel theo vị trí dòng thực tế.
- Mã nhập liệu không có số liệu thì **bỏ khỏi pnl** (dòng đó không hiện, công thức tự bỏ số hạng). Không nhập 0 giả cho khoản không biết; chỉ nhập 0 khi sổ sách thực sự bằng 0.
- Số tiền là **số nguyên đồng**, không phải chuỗi ("2.700.000.000" là SAI, `2700000000` là ĐÚNG).
- Có kỳ trước thì MỌI dòng phải có `prev`; báo cáo một kỳ thì bỏ `prev` ở tất cả.

## Thuế TNDN (mã 51)

Chọn MỘT trong hai:
1. Có số thực tế: `"pnl": {"51": {"curr": 80250000, "prev": 59600000}}`.
2. Ước tính: `"cit": {"rate": {"curr": 0.15, "prev": 0.20}}` (hoặc `"rate": 0.2` cho cả hai kỳ). Excel hiển thị ô thuế suất màu vàng và dòng ghi chú `[CẦN XÁC MINH]`.

Không có thuế suất mặc định. Bảng tham chiếu thuế suất ở SKILL.md mục 3.

## Trường tùy chọn

| Trường | Dạng | Tác dụng |
|---|---|---|
| `period_labels` | `{"curr": "Năm 2025", "prev": "Năm 2024"}` | Tiêu đề cột |
| `currency_unit` | `"đồng"` | Đơn vị tính in trên sheet |
| `cash` | `{"label": "...", "curr": số, "note": "..."}` | Thẻ KPI thứ 4 (số nhập, lấy từ bảng cân đối/sổ quỹ) |
| `quarterly` | `[{"label": "Quý 1", "revenue": số, "cogs": số, "opex": số}]` | Bảng + biểu đồ theo kỳ; Excel tự lập dòng "Chênh lệch với P&L" phải bằng 0 |
| `narrative.highlights` | `["câu 1", "câu 2"]` | Ô "Nhận định" trên slide 2. Agent viết từ số thật, có số cụ thể |
| `narrative.recommendations` | `[{"title": "...", "desc": "..."}]` | Slide "Khuyến nghị quản trị". Không có thì slide bị bỏ |

`opex` trong `quarterly` phải cùng phạm vi với P&L: TT200/TT99 = mã 25 + 26; TT133 = mã 24.
