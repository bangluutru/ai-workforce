# Externalized Thinking Protocol — Bù đắp Cognitive Gap cho LLM

> **Mục đích**: Buộc model "viết ra" quá trình suy nghĩ trước khi code,
> thay vì dựa vào reasoning nội bộ (có thể bị cắt xén hoặc skip).
> Protocol này biến implicit thinking thành explicit output — giúp MỌI model
> (kể cả model không có extended thinking) đạt chất lượng reasoning cao.

---

## 1. PRE-CODE THINKING BLOCK (Bắt buộc)

**TRƯỚC MỌI thay đổi code**, output một section có format sau:

```markdown
## 🧠 Thinking

**Goal**: [1 câu — trạng thái kết thúc mong muốn ở thế giới thực]
**The Floor**:
- Mục tiêu đích thực? → [answer]
- Luồng hoạt động kết thúc ở đâu? → [answer]
- Chi tiết nào bị bỏ quên? → [answer]
**Files to read**: [danh sách file PHẢI đọc trước khi sửa]
**Blast radius**: [danh sách file/component bị ảnh hưởng bởi thay đổi]
**Approach**: [mô tả ngắn giải pháp được chọn]
**Risk**: [1-2 rủi ro chính]
**Confidence**: [HIGH / MEDIUM / LOW — nếu LOW thì DỪNG và hỏi user]
```

**Quy tắc cứng:**
- Nếu Confidence = LOW → KHÔNG code, hỏi user
- Nếu Blast radius > 5 files → Phải liệt kê TẤT CẢ và xác nhận user
- Nếu không viết Thinking block → VI PHẠM quy tắc

---

## 2. MULTI-HYPOTHESIS DEBUGGING (Khi sửa lỗi)

Khi gặp bug/error, PHẢI output format sau TRƯỚC KHI sửa:

```markdown
## 🔍 Hypotheses

**Error**: [mô tả lỗi]
**Evidence**: [log/output thực tế đã quan sát]

| # | Giả thuyết | Bằng chứng ủng hộ | Bằng chứng phản bác | Discriminating Test |
|---|-----------|-------------------|---------------------|---------------------|
| 1 | [hypothesis] | [evidence for] | [evidence against] | [test to confirm/deny] |
| 2 | [hypothesis] | [evidence for] | [evidence against] | [test to confirm/deny] |

**Chọn kiểm tra trước**: Hypothesis #[X] vì [lý do]
```

**Quy tắc cứng:**
- Tối thiểu 2 giả thuyết, KHÔNG được chỉ có 1
- Mỗi giả thuyết PHẢI có discriminating test (phép thử phân loại)
- Chỉ sửa code SAU KHI đã chạy discriminating test và xác nhận hypothesis

---

## 3. SELF-CRITIQUE CHECKLIST (Sau mỗi change)

Sau khi code xong, TRƯỚC KHI báo hoàn thành, tự hỏi 5 câu:

```markdown
## ✅ Self-Critique

1. [ ] Code có build/chạy thành công không? (OBSERVED, không phải ASSUMED)
2. [ ] Có thay đổi nào NGOÀI phạm vi yêu cầu không?
3. [ ] Edge cases: empty data, chuỗi dài, mobile viewport — đã xử lý?
4. [ ] Hành vi cũ có bị phá vỡ không? (regression check)
5. [ ] Có hardcode secret/API key/URL nào không?
```

Nếu bất kỳ câu nào = NO → Sửa TRƯỚC KHI báo hoàn thành.

---

## 4. CALIBRATED DELIVERY (Báo cáo rút gọn)

```markdown
## Kết quả
[1-2 câu: outcome thực tế]

## Thay đổi
- [file] — [lý do]

## Kiểm chứng
- Build: [lệnh] → [kết quả THỰC TẾ]
- Test: [X pass / Y fail]

## Giả định đã tự quyết
- [điểm mơ hồ đã tự chọn]

## Weakest Link
- [điểm yếu nhất hoặc điều chưa test được]
```

---

## 5. INFORMATION CONFIDENCE LABELS

Khi trình bày thông tin, PHẢI gắn nhãn mức độ tin cậy:

- **[OBSERVED]**: Đã kiểm chứng trực tiếp (đọc file, chạy lệnh, xem output)
- **[DERIVED]**: Suy luận logic từ dữ liệu OBSERVED
- **[PRIOR]**: Kiến thức đào tạo (có thể lỗi thời)
- **[ASSUMED]**: Giả định — PHẢI khai báo rõ

**Quy tắc**: Không dùng văn phong khẳng định cho thông tin [ASSUMED] hoặc [PRIOR].
