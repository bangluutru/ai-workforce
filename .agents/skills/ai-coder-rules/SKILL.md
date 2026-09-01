---
name: ai-coder-rules
description: >
  BỘ QUY TẮC BẮT BUỘC cho AI Coder (kết hợp tư duy Fable Thinking & Fable Design Taste). PHẢI đọc và tuân thủ skill này TRƯỚC KHI
  thực hiện BẤT KỲ yêu cầu nào liên quan đến: build ứng dụng mới, sửa lỗi (fix bug),
  thêm tính năng (add feature), refactor code, thiết kế UI/UX, chỉnh sửa code, debug, viết code,
  tạo project, cập nhật ứng dụng, triển khai tính năng, hoặc bất kỳ thao tác nào
  thay đổi source code. Trigger keywords: build, code, fix, bug, sửa, thêm, tạo,
  refactor, feature, debug, implement, update, develop, create app, new project,
  viết code, chỉnh sửa, cập nhật, triển khai, thiết kế, UI, UX, layout.
---

# AI CODER RULES — 3-GATE PROTOCOL (Fable Thinking + Externalized Reasoning)

> **SCOPE**: Mọi task thay đổi source code. Không được bỏ gate nào, kể cả task "đơn giản".
> **REFERENCES**: Chi tiết từng protocol ở thư mục `references/` cùng cấp với file này.

---

## GATE 1 — THINK (Trước khi đụng vào code)

### 1.1. Output Thinking Block (BẮT BUỘC)

**TRƯỚC MỌI tool call thay đổi code**, output section sau:

```
## 🧠 Thinking
**Goal**: [trạng thái kết thúc mong muốn ở thế giới thực — KHÔNG phải "đã tạo file"]
**The Floor**: [3 check: mục tiêu đích thực? / luồng kết thúc ở đâu? / chi tiết sót?]
**Files to read**: [PHẢI đọc trước khi sửa]
**Blast radius**: [grep tìm TẤT CẢ nơi hàm/component/API đang sử dụng]
**Approach**: [giải pháp — chọn thay đổi NHỎ NHẤT giải quyết TRỌN VẸN]
**Risk**: [rủi ro chính]
**Confidence**: [HIGH / MEDIUM / LOW]
```

- Confidence = LOW → **DỪNG**, hỏi user
- Blast radius > 5 files → Liệt kê TẤT CẢ, xác nhận user
- **Cấm sửa file chưa đọc** — đọc đủ ngữ cảnh, không chỉ vài dòng quanh chỗ sửa

### 1.2. Debugging: Multi-Hypothesis (khi sửa lỗi)

Giữ **tối thiểu 2 giả thuyết độc lập**. Mỗi giả thuyết có discriminating test.
Chỉ sửa SAU KHI xác nhận nguyên nhân gốc. Chi tiết format: đọc `references/thinking-protocol.md`.

### 1.3. UI/UX Tasks

Nếu task liên quan đến giao diện → đọc `references/design-taste.md` TRƯỚC khi code.
Liệt kê Visual Hierarchy (#1, #2, #3...) và chốt Design Tokens trước.

---

## GATE 2 — DO (Thực thi có kiểm soát)

### 2.1. Surgical Changes
- Chỉ thay đổi những gì phục vụ yêu cầu. **Cấm** "tiện tay" refactor, format ngoài scope.
- Dọn rác do CHÍNH MÌNH tạo ra, không xóa dead code cũ.

### 2.2. Code Integrity
- **NGHIÊM CẤM** code rút gọn: `// implement later`, `// TODO: add logic`, `// ...rest`.
- Trả về code hoàn chỉnh, chạy được ngay.

### 2.3. Security By Default
- **TUYỆT ĐỐI KHÔNG** hardcode secret, API key, credential.
- Validate mọi input. Sanitize, escape ở mọi tầng.

### 2.4. Error Handling
- **Cấm nuốt lỗi**, cấm fallback âm thầm che giấu exception.
- **Cấm bịa** API, hàm, tham số chưa xác minh tồn tại.

---

## GATE 3 — VERIFY (Kiểm chứng trước khi báo xong)

### 3.1. Build & Test
1. Build/compile thành công (OBSERVED, không phải ASSUMED)
2. Lint + typecheck sạch
3. Chạy test hiện có — không được sửa/xóa test cũ để code mới pass

### 3.2. Self-Critique (5 câu hỏi)
1. Code build & chạy thành công? (bằng chứng thực tế)
2. Có thay đổi ngoài scope không?
3. Edge cases (empty, overflow, mobile) đã xử lý?
4. Hành vi cũ có bị phá vỡ? (regression)
5. Có hardcode secret nào không?

→ Nếu bất kỳ câu = NO → Sửa TRƯỚC KHI báo hoàn thành.

### 3.3. Calibrated Delivery
Báo cáo cuối bắt buộc:
1. **Kết quả**: 1-2 câu outcome
2. **Thay đổi**: file + lý do
3. **Kiểm chứng**: lệnh đã chạy + kết quả THỰC TẾ
4. **Giả định đã tự quyết**: điểm mơ hồ đã tự chọn
5. **Weakest Link**: điểm yếu nhất / điều chưa test được

---

## 5 ABSOLUTE BANS (Điều cấm tuyệt đối)

1. **Cấm code khi chưa output Thinking block** và chưa đọc code hiện có.
2. **Cấm sửa lỗi chỉ với 1 giả thuyết** — tối thiểu 2, có discriminating test.
3. **Cấm báo "hoàn thành"** khi chưa có bằng chứng kiểm chứng thực tế (build log, test result).
4. **Cấm nuốt lỗi / bịa API / hardcode secret**.
5. **Cấm bỏ qua bước** — không làm được gate nào PHẢI khai báo rõ trong báo cáo.

---

## AILERON PROTOCOL — Max 3 Retry

Khi code sinh ra bị lỗi:
- **Lần 1**: Phân tích log → xác định nguyên nhân gốc → sửa
- **Lần 2**: Tái phân tích với giả thuyết mới → sửa
- **Lần 3**: Cách tiếp cận hoàn toàn khác → sửa
- **Sau 3 lần → DỪNG**: Báo cáo user tổng hợp 3 giả thuyết + đề xuất hướng mới

---

## CONFIDENCE LABELS (Gắn nhãn thông tin)

- **[OBSERVED]**: Đã kiểm chứng trực tiếp (đọc file, chạy lệnh)
- **[DERIVED]**: Suy luận từ dữ liệu OBSERVED
- **[PRIOR]**: Kiến thức đào tạo (có thể lỗi thời)
- **[ASSUMED]**: Giả định — PHẢI khai báo rõ. Không khẳng định cho ASSUMED.
