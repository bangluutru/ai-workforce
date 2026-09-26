# MINIMAL EVIDENCE CONTRACT

> **AIWF Quality Harness — Phase 2 Foundation**  
> Phiên bản: `v1.0-foundation`  
> Trạng thái: **Active Contract**

---

## 1. Mục Đích & Triết Lý Cốt Lõi

1. **Không xây Task Ledger cồng kềnh**: Hệ thống AIWF từ chối việc áp đặt một universal engineering task ledger phức tạp lên tất cả các miền nghiệp vụ khác nhau (dịch thuật, thiết kế in ấn, video, thuế, pháp luật...).
2. **Tôn trọng tính đặc thù miền (Domain-Specific Evidence)**:
   - Bằng chứng kiểm định dịch thuật (`verify_retention.py`): IoU bounding box hình ảnh, sai lệch số trang, token công thức hóa học/toán học, khối chữ nguồn CJK/English còn sót.
   - Bằng chứng thẩm định nội dung (`claim_guard.py`): Dòng văn bản, cụm từ over-claim vi phạm Luật Quảng cáo, tài liệu chứng minh nguồn gốc.
   - Bằng chứng giao diện web (`app-auditor`): Screenshot các viewports (Mobile, Tablet, Desktop), WCAG Axe violations, console error trace.
   - Bằng chứng kế toán / thuế (`tu-van-thue-tncn`, `bao-cao-kt`): Bảng tính XLSX Live Formulas (`SUM`, `VLOOKUP`), tính toàn vẹn biểu thuế lũy tiến.
3. **Envelope Tối Thiểu Dùng Chung (Lightweight Common Result Envelope)**:
   Mọi công cụ xác minh deterministic (scripts kiểm tra) hoặc kiểm định kỹ năng khi xuất bản kết quả máy đọc (JSON) nên cung cấp envelope tối thiểu sau để tích hợp mượt mà vào harness.

---

## 2. Chuẩn Envelope Chung (Shared JSON Envelope)

```json
{
  "status": "PASS | FAIL | BLOCKED | NOT_APPLICABLE",
  "checks": [
    "Tên kiểm tra 1",
    "Tên kiểm tra 2"
  ],
  "failures": [
    "Mô tả chi tiết lỗi phát hiện 1"
  ],
  "warnings": [
    "Cảnh báo cần lưu ý hoặc bằng chứng cần bổ sung"
  ],
  "artifacts": [
    "/đường/dẫn/tuyệt/đối/tới/file_kết_quả"
  ],
  "domain_data": {
    "...": "Chi tiết chuyên sâu thuộc về từng domain skill"
  }
}
```

---

## 3. Bộ Từ Vựng Trạng Thái (Status Vocabulary)

| Trạng thái | Ý nghĩa | Hành vi của Agent / Harness |
|------------|---------|-----------------------------|
| **`PASS`** | Toàn bộ kiểm tra tất định đạt chuẩn 100%. Không có lỗi vi phạm hay blocker. | Cho phép tiến hành bàn giao thành phẩm cho người dùng. |
| **`FAIL`** | Phát hiện ít nhất 1 lỗi vi phạm cứng (Hard Blocker, vi phạm từ cấm, lệch cấu trúc, lỗi cú pháp). | **DỪNG LẠI NGAY LẬP TỨC**. Bắt buộc sửa chữa dứt điểm, không được báo cáo hoàn thành dối. |
| **`BLOCKED`** | Không thể thực hiện kiểm định do điều kiện tiên quyết không thỏa mãn (ví dụ: file đầu vào bị hỏng, định dạng nhị phân chưa bóc tách, thiếu tool hệ thống). | Thông báo lý do bị chặn và yêu cầu đầu vào hợp lệ. |
| **`NOT_APPLICABLE`** | Kiểm tra không áp dụng cho ngữ cảnh hoặc loại tài liệu hiện tại (ví dụ: kiểm tra bleed in ấn trên file HTML thuần). | Ghi nhận bỏ qua có lý do, không tính điểm trừ. |

---

## 4. Nguyên Tắc Bất Biến Về Bằng Chứng (Inviolable Rules)

1. **Hard Blocker không thể bị ghi đè bởi Composite Score:**
   Nếu một kiểm tra bị đánh dấu Hard Blocker (như sót chữ nguồn trong dịch thuật, hoặc lỗi cú pháp script), trạng thái tổng thể BẮT BUỘC là `FAIL`, bất kể điểm trung bình cộng có đạt 99/100.
2. **Không claim PASS khi thiếu bằng chứng:**
   Agent tuyệt đối không được tự ý nói *"Đã kiểm tra thành công"* nếu không có log runtime, file kết quả tồn tại với kích thước $> 0$ bytes, hoặc lệnh kiểm thử thực tế được thực thi.
3. **Phân tách Rõ Ràng Linter vs Verifier:**
   - Các công cụ regex/từ khóa (như `claim_guard.py`) chỉ được gọi là **Preliminary Linter** (Bộ lọc sơ bộ).
   - Chỉ những công cụ đối chiếu dữ liệu gốc 1:1, chạy sandbox hoặc test AST/browser mới được coi là **Deterministic Verifier**.
