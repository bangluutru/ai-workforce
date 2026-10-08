# BẢNG KIỂM ĐỊNH KÉP NGHIỆM THU SÁCH NÓI (DUAL-PERSPECTIVE AUDIT CHECKLIST)

Tài liệu nghiệm thu bắt buộc theo Luật R3 §9 & Luật R4 §2.6 trước khi bàn giao file sách nói cho người dùng.

---

## 1. THÔNG TIN XUẤT BẢN

- **Tên sách:** `{{BOOK_TITLE}}`
- **Tác giả:** `{{AUTHOR}}`
- **Giọng đọc AI:** `{{VOICE_NAME}}` (VieNeu 48kHz / Kokoro)
- **Chế độ biên tập:** `{{READING_MODE}}` (Cấp 1 / Cấp 2 / Cấp 3 / Cấp 4)
- **Đường dẫn file thành phẩm:** `{{OUTPUT_DIR}}/{{SAFE_TITLE}}.m4b`

---

## 2. GÓC NHÌN 1 — THẨM ĐỊNH KỸ THUẬT (TECHNICAL PERSPECTIVE)

| STT | Hạng mục kiểm tra | Tiêu chuẩn kỹ thuật | Dữ liệu đo đạc thực tế | Kết quả |
|:---:|---|---|---|:---:|
| 1 | File M4B tồn tại & dung lượng | File `.m4b` tồn tại, kích thước $> 0$ bytes | `{{M4B_SIZE_BYTES}}` bytes | PASS / FAIL |
| 2 | Codec & Container | AAC mono, faststart enabled | AAC LC mono @ `{{BITRATE}}` | PASS / FAIL |
| 3 | Tần số lấy mẫu (Sample Rate) | 44.1 kHz hoặc 48 kHz | `{{SAMPLE_RATE}}` Hz | PASS / FAIL |
| 4 | Tổng thời lượng thực tế | Thời lượng đo qua `ffprobe` khớp tổng các chương + gaps | `{{TOTAL_DURATION_SEC}}` giây (~ `{{TOTAL_DURATION_MIN}}` phút) | PASS / FAIL |
| 5 | Mục lục phân chương (Chapters) | `ffprobe -show_chapters` hiển thị đủ $100\%$ chương, mốc START/END không chồng lấn | `{{CHAPTER_COUNT}}` chương | PASS / FAIL |
| 6 | Nhúng ảnh bìa (Cover Art) | Stream video định dạng `mjpeg` (`attached_pic`) | `{{HAS_COVER_ART}}` | PASS / FAIL |
| 7 | Thư mục MP3 phụ | Thư mục `MP3/` chứa các file đánh số `01 - ...mp3`, có thẻ ID3v2 | `{{MP3_COUNT}}` files | PASS / FAIL |
| 8 | Tuân thủ Luật R7 | Không chép lại file, gọi lại engine `_shared/media/` | `check_shared_reuse.py` = 0 lỗi | PASS / FAIL |

---

## 3. GÓC NHÌN 2 — THẨM ĐỊNH TRẢI NGHIỆM NGƯỜI DÙNG (USER EXPERIENCE PERSPECTIVE)

| STT | Tiêu chí trải nghiệm | Yêu cầu nghiệm thu | Đánh giá thực tế | Kết quả |
|:---:|---|---|---|:---:|
| 1 | Khử lỗi phát âm dấu ngoặc kép | Không còn dấu ngoặc kép khiến TTS đọc thành chữ "dấu ngoặc kép" | Đã khử 100% qua `spoken_normalizer` | PASS / FAIL |
| 2 | Phát âm tự nhiên số & từ viết tắt | Số La Mã (Chương IV $\rightarrow$ Chương bốn), viết tắt (TP.HCM, KPI, CEO) đọc êm tai | Đã chuyển đổi chuẩn xác | PASS / FAIL |
| 3 | Quãng nghỉ thư thái (Pacing) | Giữa 2 chương có quãng nghỉ 2.0s tự nhiên | Chèn silence gap 2.0s | PASS / FAIL |
| 4 | Tương thích thiết bị di động | Mở được trên Apple Books, BookPlayer (hỗ trợ CarPlay/Android Auto) | Định dạng M4B chuẩn quốc tế | PASS / FAIL |
| 5 | Chống phình repo (Anti-Repo Bloat) | File lưu trong `~/Downloads/AIWF_Output/`, không xả rác vào workspace | `{{CLEAN_WORKSPACE}}` | PASS / FAIL |
| 6 | Bàn giao sạch (Clean Delivery) | Khung chat tóm tắt súc tích, kèm bảng mục lục và hướng dẫn chép sách | Đầy đủ và trực quan | PASS / FAIL |

---

## 4. KẾT LUẬN NGHIỆM THU

- [ ] **ĐẠT CHUẨN 100%:** Cả 2 góc nhìn Kỹ thuật và Người dùng đều đạt `PASS`. Cho phép xuất bản và bàn giao.
- [ ] **KHÔNG ĐẠT:** Phát hiện lỗi hoặc chưa kiểm chứng thực tế $\rightarrow$ Bắt buộc khắc phục trước khi báo cáo.
