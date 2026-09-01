---
trigger: always_on
description: "Luật Code Quality — Đảm bảo chất lượng code và tính toàn vẹn khi chỉnh sửa hệ thống."
---

# LUẬT CODE QUALITY & KỶ LUẬT THỰC THI

> Áp dụng cho mọi tác nhân khi lập trình, sửa lỗi, thêm tính năng, refactor hoặc bảo trì source code trong AI Workforce.

---

## 1. ZERO-INFERENCE TAXONOMY (PHÂN LOẠI TUYÊN BỐ)

Khi đưa ra bất kỳ kết luận hoặc đề xuất nào, tác nhân PHẢI phân loại rõ ràng nguồn gốc thông tin:
- **OBSERVED**: Đã kiểm chứng trực tiếp từ file thực tế, lệnh terminal, hoặc log runtime.
- **DERIVED**: Suy luận logic chặt chẽ từ dữ liệu đã được OBSERVED.
- **PRIOR**: Kiến thức tổng quát từ dữ liệu đào tạo sẵn có.
- **ASSUMED**: Giả định chưa có bằng chứng thực tế — PHẢI khai báo rõ ràng cho User trước khi thực hiện.

> ⚠️ Khi không chắc chắn hoặc thiếu thông tin $\rightarrow$ **HỎI USER**, tuyệt đối KHÔNG tự suy diễn.

---

## 2. CODEBASE-FIRST EXECUTION (ĐỌC TRƯỚC KHI SỬA)

1. **LUÔN ĐỌC FILE THỰC TẾ TRƯỚC KHI ĐỀ XUẤT THAY ĐỔI**: Cấm viết code hoặc sửa đổi dựa trên phỏng đoán về cấu trúc tệp.
2. **KIỂM TRA BLAST RADIUS**: Dùng grep/ripgrep tìm TẤT CẢ các nơi hàm, component, biến hoặc API đang được sử dụng trước khi thay đổi chữ ký (signature) hoặc logic cốt lõi.
3. **SURGICAL CHANGES**: Chỉ thay đổi đúng phạm vi yêu cầu. Cấm "tiện tay" refactor, format lại những đoạn mã không liên quan.

---

## 3. TOKEN ECONOMICS (TỐI ƯU NGỮ CẢNH)

1. **Context Tối Thiểu**: Chỉ tải context cần thiết cho task hiện tại — tránh làm tràn bộ nhớ ngữ cảnh.
2. **Signal-over-Noise**: Ưu tiên tín hiệu có giá trị cao, tránh đọc các file sinh tự động, thư mục `node_modules`, `__pycache__`, build outputs.
3. **Cấu Trúc Rút Gọn**: Khi cần bối cảnh toàn cục, hãy đọc cấu trúc signatures, export, schema thay vì nạp toàn bộ nội dung tệp.

---

## 4. 5 ĐIỀU CẤM TUYỆT ĐỐI (5 ABSOLUTE BANS)

1. ❌ **CẤM code placeholder**: Không viết `// TODO`, `// implement later`, `/* ...rest */`. Code trả về phải hoàn chỉnh 100%.
2. ❌ **CẤM nuốt lỗi ngầm**: Không dùng `except: pass` hoặc catch lỗi mà không log hay xử lý rõ ràng.
3. ❌ **CẤM sửa file chưa đọc**: Phải đọc và hiểu rõ nội dung tệp trước khi dùng lệnh ghi đè/sửa.
4. ❌ **CẤM bịa API/hàm**: Không sử dụng hàm hoặc tham số chưa được xác minh tồn tại trong thư viện/codebase.
5. ❌ **CẤM hardcode credentials**: Không ghi secret, token, mật khẩu trực tiếp vào mã nguồn.
