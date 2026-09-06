# Báo cáo Kiểm thử Thực nghiệm Form Submission (Landing Hub E2E)

> **Mã dự án:** {{PROJECT_ID}}  
> **Trang đích:** {{LANDING_PAGE_ID}}  
> **Form ID:** {{FORM_ID}}  
> **Loại Form:** {{FORM_TYPE}}  
> **Thời gian kiểm thử:** {{TEST_TIMESTAMP}}  

---

## 1. Kết quả Gửi Ban đầu (Initial Submission)
- **Endpoint:** `{{ENDPOINT}}`
- **Idempotency Key:** `{{IDEMPOTENCY_KEY}}`
- **HTTP Status:** `{{INITIAL_HTTP_STATUS}}`
- **Mã bản ghi sinh ra:** `{{RECORD_ID}}`
- **Sự kiện phễu tự động:** `{{FUNNEL_EVENT}}` (đã kích hoạt)

---

## 2. Kết quả Thử nghiệm Chống trùng lặp (Idempotent Replay Test)
- **Gửi lại cùng Key:** `{{IDEMPOTENCY_KEY}}`
- **HTTP Status:** `{{REPLAY_HTTP_STATUS}}`
- **Phản hồi Idempotent:** `idempotentReplay: true`
- **Bản ghi trùng lặp:** 0 (Không tạo bản ghi mới)
- **Sự kiện phễu trùng lặp:** 0 (Không phát sinh sự kiện thứ hai)

---

## 3. Đánh giá Tổng thể
- **Trạng thái:** {{TEST_RESULT_STATUS}}
- **Đạt chuẩn Landing Hub Integration Contract v1.0:** CÓ
