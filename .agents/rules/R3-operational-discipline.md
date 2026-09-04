---
trigger: always_on
description: "Luật Kỷ Luật Vận Hành — Đảm bảo kiểm chứng thực tế và hoàn thành tự động 100%."
---

# LUẬT KỶ LUẬT VẬN HÀNH (OPERATIONAL DISCIPLINE)

---

## 1. PER-TASK VERIFICATION (KIỂM CHỨNG BẮT BUỘC)

Tuyệt đối KHÔNG BAO GIỜ đánh dấu một tác vụ là "hoàn thành" khi chưa chứng minh nó hoạt động:
- Chạy lệnh kiểm thử, kiểm tra log, xác nhận file đầu ra thực tế tồn tại và hợp lệ.
- Luôn đặt câu hỏi: *"Một kỹ sư trưởng (Staff Engineer) có phê duyệt kết quả này không?"*
- Nếu có bất kỳ lỗi nào xuất hiện $\rightarrow$ Sửa dứt điểm trước khi báo cáo hoàn thành.

---

## 2. AUTONOMOUS FULL-RUN PROTOCOL (TỰ ĐỘNG CHẠY ĐẾN CÙNG)

- Khi được kích hoạt bởi người dùng, Agent PHẢI chủ động thực hiện toàn bộ các bước trong quy trình (bóc tách $\rightarrow$ dịch/xử lý $\rightarrow$ ghép nối $\rightarrow$ kiểm tra $\rightarrow$ xuất bản).
- KHÔNG tự ý dừng lại giữa chừng để hỏi những câu thừa thãi hoặc xin phép tiếp tục nếu mọi thứ đang vận hành đúng kế hoạch.
- Chỉ dừng khi:
  1. Gặp lỗi ngoại lệ nghiêm trọng không thể tự phục hồi.
  2. Phát hiện mâu thuẫn dữ liệu cần quyết định từ con người.
  3. Đã hoàn thành 100% và tạo đầy đủ thành phẩm đầu ra.

---

## 3. REGRESSION PREVENTION (CHỐNG LỖI TỒN ĐỌNG)

Khi sửa lỗi (bug fix) hoặc cập nhật tính năng:
1. Phải chứng minh lỗi xảy ra trước khi sửa.
2. Sửa đúng nguyên nhân gốc rễ (Root Cause), không vá tạm ở phần ngọn.
3. Sau khi sửa, phải chạy lại toàn bộ quy trình kiểm tra để đảm bảo không làm gãy các tính năng cũ đang chạy tốt.

---

## 4. CONTEXT ROT PREVENTION & QUY TẮC 15 TIN NHẮN (ROLLING SUMMARIES)

Hiện tượng bão hòa hoặc suy thoái ngữ cảnh (Context Rot) xảy ra khi lịch sử hội thoại vượt quá dung lượng tối ưu (> 40%), gây nhiễu loạn xác suất nhận thức của LLM:
1. **Quy tắc 15–20 Tin nhắn:** Sau mỗi 15 đến 20 lượt tương tác kỹ thuật chuyên sâu (hoặc khi phát hiện lịch sử hội thoại quá dài), Agent chủ động tạo một bản tóm tắt tiến trình (Rolling Summary) ghi rõ:
   - Các quyết định kiến trúc đã thống nhất.
   - Trạng thái hiện tại của file và codebase.
   - Các bước tiếp theo cần triển khai.
2. **Cơ chế New Session Checkpoint:** Người dùng hoặc Agent có thể lưu bản tóm tắt này vào `_process/checkpoint_summary.md` để khởi động một phiên làm việc mới với ngữ cảnh tinh khiết nhất.

---

## 5. QUY TRÌNH PHÂN NHÁNH 3 PHA (EXPLORE $\rightarrow$ PLAN $\rightarrow$ EXECUTE)

Tuyệt đối cấm Agent thả mình vào một yêu cầu phức tạp mà không có kế hoạch rõ ràng, dẫn đến vòng lặp thử-sai (Correction Loop) làm ô nhiễm ngữ cảnh:
1. **Pha 1 — Khám phá (Explore):** Đọc tài liệu, phân tích mã nguồn, kiểm tra file thực tế mà không chỉnh sửa code.
2. **Pha 2 — Lập Kế hoạch (Plan):** Xác định danh sách file cần sửa/tạo mới, rà soát blast radius, thiết lập tiêu chí nghiệm thu.
3. **Pha 3 — Thực thi (Execute):** Khi kế hoạch đã rõ ràng, Agent tiến hành sửa đổi với các nhát cắt phẫu thuật nhỏ gọn (Surgical Micro-diffs), kiểm thử từng phần và nghiệm thu dứt điểm.

---

## 6. SUBAGENT ISOLATION QUA `context: fork` (GEMINI 3.8 MULTI-AGENT)

Đối với các tác vụ dài hơi, tốn dung lượng bộ nhớ lớn (như OCR tài liệu scan 50+ trang, dịch thuật sách 100+ trang, quét phân tích hàng nghìn file):
1. **Không làm nghẽn phiên chính:** Kỹ năng phải kích hoạt cờ `context: fork` trong YAML frontmatter để khởi chạy bên trong một Subagent độc lập.
2. **Cửa sổ ngữ cảnh riêng biệt:** Subagent hoàn thành toàn bộ khối công việc nặng, xuất file kết quả vào `<output_dir>` và chỉ trả về báo cáo tóm tắt ngắn gọn cho tác nhân chính.

---

## 7. PHÂN TÁCH BIÊN GIỚI DỮ LIỆU BẰNG THẺ XML

Để tối đa hóa khả năng nhận thức của mô hình Gemini 3.8 và loại bỏ sự nhầm lẫn giữa dữ liệu thô và lệnh điều khiển:
* Mọi cấu trúc prompt phức tạp hoặc file nháp trung gian phải được bao bọc trong các thẻ XML rõ ràng: `<goal>`, `<context>`, `<instructions>`, `<constraints>`, `<working_ledger>`, `<delivery_protocol>`.
* Khi xử lý văn bản pháp luật, tài chính hoặc dữ liệu OCR, đặt tài liệu nguồn trong `<source_document>` để bảo vệ ranh giới trích dẫn.

