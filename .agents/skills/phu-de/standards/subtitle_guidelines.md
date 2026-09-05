# QUY CHUẨN KỸ THUẬT PHỤ ĐỀ (SUBTITLE GUIDELINES)
## Tiêu chuẩn Phân đoạn, Tốc độ Đọc & Trình bày Phụ đề Video (AIWF Standard)

---

## 1. RÀNG BUỘC KỸ THUẬT CỐT LÕI (TECHNICAL CONSTRAINTS)

| Tiêu chí | Ngưỡng chuẩn (Latin / Tiếng Việt) | Ngưỡng chuẩn (CJK / Nhật / Trung) | Mục đích & Trải nghiệm người dùng |
|---|---|---|---|
| **CPL (Characters Per Line)** | **38 - 42 ký tự** | **18 - 22 ký tự** | Tránh tràn khung hình trên thiết bị di động (375px) và giữ tầm mắt người xem không phải đảo ngang quá rộng. |
| **Số dòng tối đa / segment** | **Tối đa 2 dòng** (ưu tiên 1 dòng) | **Tối đa 2 dòng** | Bảo vệ không gian thị giác của video, không che khuất nhân vật hoặc chi tiết quan trọng. |
| **Thời lượng tối thiểu (Min Duration)** | **0.8 giây** | **0.8 giây** | Chống hiện tượng phụ đề chớp tắt quá nhanh (flash frames) khiến não bộ không kịp tiếp nhận. |
| **Thời lượng tối đa (Max Duration)** | **5.0 - 6.0 giây** | **5.0 - 6.0 giây** | Tránh phụ đề "chết" treo quá lâu trên màn hình khi người nói đã chuyển sang ý khác. |
| **Tốc độ đọc (CPS - Characters/Sec)** | **15 - 20 CPS** | **6 - 9 CPS** | Tương thích tốc độ đọc trung bình của người trưởng thành (khoảng 180 - 240 từ/phút). |
| **Khoảng lặng ngắt câu (Pause threshold)** | **≥ 0.35 - 0.45 giây** | **≥ 0.35 - 0.45 giây** | Điểm ngắt tự nhiên trong ngữ điệu giọng nói để tách phân đoạn phụ đề. |

---

## 2. NGUYÊN TẮC PHÂN TÁCH NGỮ NGHĨA (SEMANTIC CHUNKING RULES)

1. **Tuyệt đối không ngắt rời cụm từ cố định (No Orphan Words):**
   - ❌ Sai: `Chào mừng bạn đến với lực lượng / lao động AI.`
   - ✅ Đúng: `Chào mừng bạn đến với / lực lượng lao động AI.`
2. **Ngắt tại ranh giới ngữ pháp tự nhiên:**
   - Ưu tiên ngắt dòng hoặc ngắt phân đoạn tại:
     - Dấu kết câu: chấm `.`, hỏi `?`, than `!`.
     - Dấu liên kết mệnh đề: phẩy `,`, hai chấm `:`, chấm phẩy `;`.
     - Trước liên từ phụ thuộc: *và, nhưng, hoặc, vì, do đó, mặc dù, nếu, khi*.
3. **Cân bằng độ dài giữa 2 dòng (Visual Pyramid):**
   - Khi phụ đề có 2 dòng, nên bố trí dòng trên ngắn hơn hoặc bằng dòng dưới để tạo khối hình thang vững chãi, dễ đọc.

---

## 3. QUY CHUẨN PHỤ ĐỀ SONG NGỮ (BILINGUAL SUBTITLES)

1. **Phân cấp thị giác (Visual Hierarchy):**
   - **Dòng chính (Primary Line):** Thường là câu dịch sang tiếng bản ngữ (tiếng Việt), phông chữ to hơn (100%), màu sáng trắng (`#FFFFFF`).
   - **Dòng phụ (Secondary Line):** Thường là câu thoại gốc (tiếng Anh hoặc tiếng Nhật), phông chữ nhỏ hơn (80%), màu sắc phân biệt rõ như vàng kim (`#FFD700`) hoặc xanh cyan (`#00FFFF`).
2. **Khoảng cách 2 dòng (Line Spacing):**
   - Đặt từ 4px đến 8px để hai dòng tách bạch, không dính chân ký tự với dấu móc tiếng Việt (ă, â, đ, ê, ô, ơ, ư).

---

## 4. QUY CHUẨN MÀU SẮC & TƯƠNG PHẢN (WCAG AA COMPLIANCE)

1. **Viền chữ (Text Outline):**
   - Phụ đề bắt buộc phải có viền màu tương phản (Outline Width từ 2.0px đến 2.5px màu đen `#000000`) để đọc rõ trên cả khung hình video nền sáng lẫn nền tối.
2. **Hộp nền mờ (Box Opacity):**
   - Khuyến nghị nền hộp bán trong suốt (Opacity 30% - 45%) cho video hội thảo, bài giảng hoặc vlog có phông nền chuyển động phức tạp.

---

## 5. BẢNG MÃ MÀU ASS (BGR CONVENTION)

| Màu hiển thị | Mã HEX chuẩn RGB | Mã ASS BGR (`&H00BBGGRR&`) | Ứng dụng |
|---|---|---|---|
| Trắng sáng | `#FFFFFF` | `&H00FFFFFF&` | Dòng chữ chính |
| Vàng kim | `#FFD700` | `&H0000D7FF&` | Dòng phụ đề song ngữ |
| Vàng nhạt | `#FFF275` | `&H0075F2FF&` | Phụ đề rạp phim cổ điển |
| Xanh Cyan | `#00FFFF` | `&H00FFFF00&` | Phụ đề TikTok / Reels nổi bật |
| Đen viền | `#000000` | `&H00000000&` | Màu viền và bóng đổ |
| Hộp nền đen mờ (40%) | `#000000` (60% alpha) | `&H99000000&` | Nền hộp bảo vệ mắt |
