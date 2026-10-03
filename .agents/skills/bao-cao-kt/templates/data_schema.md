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
| `sources` | `{"01": {"curr": "Sheet 1 'KQKD' ô D4", "prev": "... ô E4"}}` | Nguồn từng số nhập (ô/trang trong tệp người dùng). Script bỏ qua, dùng cho bàn giao và kiểm tra |

`opex` trong `quarterly` phải cùng phạm vi với P&L: TT200/TT99 = mã 25 + 26; TT133 = mã 24.

## Nhập từ tệp (XLSX / CSV / PDF qua doc_ingest)

`tables_from_source.py <thư mục ingest> -o <process_dir>/tables.json` đọc `source.md` và trả về `tables[]`, `pnl_candidates[]`, `check_totals[]`, `regime_hint`. Agent đối chiếu rồi tự viết data.json (script không ghi data.json).

| Nguồn trong `source.md` | Cách đọc | Ghi nguồn |
|---|---|---|
| XLSX/XLS/ODS: `## Sheet i: tên` + bảng có cột `#` (số dòng Excel) và cột chữ `A, B, …` | Ô = chữ cột + số dòng; giá trị là số máy (không có dấu phân cách) | `Sheet i 'tên' ô D7` |
| XLSX: bảng `### Công thức — tên` (Ô, Công thức, Giá trị đã tính) | Ô có công thức là dòng tổng/tính: KHÔNG nhập vào `pnl`, chỉ dùng để đối chiếu | ô công thức |
| PDF: bảng pipe sau `<!-- page N -->`; dòng B02 có thể vỡ thành dòng chữ `… 01 VI.25 12.345.678.900 10.000.000.000` | Số kiểu VN; script đọc cả bảng và dòng chữ | `trang N` |
| CSV: một bảng pipe | Số kiểu VN | `bảng 1, dòng mã 01, cột 3` |

Quy tắc map:
1. `pnl_candidates[i]` có `code` thuộc mã NHẬP → `pnl["<code>"] = {"curr": curr, "prev": prev}`; `src` → `sources["<code>"]`. Mã TÍNH (10, 20, 30, 40, 50, 60) chỉ nằm trong `check_totals`, không nhập.
2. Cột kỳ: lấy theo tiêu đề "Năm nay/Kỳ này/Năm 2025" và "Năm trước/Kỳ trước/Năm 2024". Ghi chú "cột kỳ suy theo thứ tự" → mở `source.md` (hoặc ảnh trang) xác nhận cột trước khi dùng.
3. Số VN: `1.234.567` → `1234567`; `1.234,5` → `1234.5`; `(1.234)` hoặc `-1.234` → âm; `28,6%` → `0.286`. Khoản chi phí (02, 11, 22–26, 32, 51) trình bày trong ngoặc → nhập số DƯƠNG (B02 tự trừ). Ô `-` hoặc trống → `null`: hỏi, chỉ ghi 0 khi sổ sách thực sự bằng 0, nếu không thì bỏ mã đó.
4. `check_totals[].ok = false` (tổng tự tính lệch tổng trong nguồn quá 1 đồng) → tìm dòng bị sót/sai dấu/sai cột; nguồn thật sự lệch thì ghi `[CẦN XÁC MINH]` vào narrative.
5. `regime_hint`: có mã 24 → TT133; có 25/26 → TT200. Vẫn ưu tiên mẫu biểu ghi trên báo cáo nguồn.
6. Bảng không có cột "Mã số" (sổ chi tiết, bảng theo quý): tự map từ `tables[]` (mỗi dòng có `cells`, `values` đã chuẩn hoá, `refs` ô) sang `pnl`/`quarterly`, ghi nguồn vào `sources`; cộng lại so với tổng trong tệp trước khi chạy script.
