---
name: invoice
description: >-
  Automates the processing of invoice files (XML, PDF) in a directory to generate an Excel Payment Request (Đề Nghị Thanh Toán). Use this skill when the user asks to process invoices, create a payment request from a folder of receipts/invoices, or run the invoice automation.
---

# Invoice Processing Skill

Tự động xử lý hoá đơn điện tử (XML) và biên lai (PDF) từ một thư mục, điền vào template `Mẫu ĐNTT.xlsx` để tạo file Đề Nghị Thanh Toán hoàn chỉnh.

## Khả năng xử lý

### Loại file hỗ trợ
- **XML e-invoices**: Xanh SM (GSM), Green Car, Phú Hoàng, Saco, Đại Thành Công, Vietjet Air, Vietnam Airlines, và mọi hoá đơn GTGT điện tử chuẩn Việt Nam
- **PDF receipts**: Vietjet Air, Vietnam Airlines, bảo hiểm PVI, khách sạn, nhà hàng, và các biên lai khác

### Tính năng chi tiết
- **Trích xuất route taxi**: Tự động lấy điểm đi/đến từ `PICK_UP_ADDRESS`, `DROP_OFF_ADDRESS`, `THHDVu` (nhiều pattern: Điểm đón/trả, Điểm đón/đến, từ X đến Y)
- **Trích xuất route bay**: Tự động lấy PNR và lộ trình (VD: HAN-HUI) từ tên file
- **Loại trùng lặp**: Tự động skip file Itinerary PDF khi đã có Receipt XML cùng PNR; skip PDF khi có XML cùng tên
- **Xoá dữ liệu cũ trong template**: Tự động phát hiện và xoá dữ liệu cũ trong template đã dùng trước đó
- **Sắp xếp theo ngày**: Đúng thứ tự thời gian (ngày xa nhất → gần nhất)
- **Chuyển đổi số → chữ**: Tự động viết tổng tiền bằng chữ tiếng Việt
- **Xử lý nhiều format ngày**: DD/MM/YYYY, YYYY-MM-DD, "DD Tháng MM Năm YYYY", YYYYMMDD từ tên file

## Prerequisites

Script yêu cầu `openpyxl` và `pdfplumber`:
```bash
pip install openpyxl pdfplumber
```

## Quy trình thực hiện

1. **Xác định thư mục và template**:
   - Hỏi user đường dẫn thư mục chứa hoá đơn (nếu chưa cung cấp)
   - Template `Mẫu ĐNTT.xlsx` thường nằm trong cùng thư mục hoặc trên Google Drive gốc
   - Nếu user chỉ định tên file output thì dùng tên đó, mặc định là `ĐNTT_filled.xlsx`

2. **Chạy script xử lý**:
   **CRITICAL**: PHẢI set `BypassSandbox: true` ngay từ đầu. Thư mục hoá đơn luôn nằm ngoài sandbox (Downloads, Google Drive).

   ```bash
   python3 ~/.gemini/config/skills/invoice/scripts/process_invoices.py \
       --input_dir "/path/to/invoices_folder" \
       --template "/path/to/Mẫu ĐNTT.xlsx" \
       --output "/path/to/output/ĐNTT_filled.xlsx"
   ```

3. **Báo cáo kết quả**: Thông báo số lượng hoá đơn, tổng tiền, và đường dẫn file output.

## Lưu ý quan trọng

- Script quét **đệ quy** tất cả thư mục con (VD: thư mục `Taxi/`)
- Ưu tiên XML hơn PDF: nếu có cả 2 file cùng tên thì chỉ xử lý XML
- File Itinerary (lịch trình bay) tự động bị loại nếu đã có Receipt XML tương ứng
- Template có thể chứa dữ liệu cũ — script tự động xoá sạch trước khi ghi mới
