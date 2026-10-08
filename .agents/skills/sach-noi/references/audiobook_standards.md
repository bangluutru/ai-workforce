# TIÊU CHUẨN KỸ THUẬT SÁCH NÓI (AUDIOBOOK STANDARDS)

Tài liệu quy định các tham số kỹ thuật đóng gói định dạng `.m4b` và `MP3` đảm bảo tương thích 100% với hệ sinh thái thiết bị di động, app sách nói và màn hình xe hơi thông minh.

---

## 1. TIÊU CHUẨN ĐỊNH DẠNG M4B (.m4b)

File `.m4b` là định dạng container MPEG-4 Part 14 chuyên dụng cho sách nói, kế thừa khả năng đánh dấu chương và lưu vết tiến trình nghe (resume bookmarking).

| Tham số kỹ thuật | Giá trị chuẩn mực | Lý do lựa chọn |
|---|---|---|
| **Audio Codec** | **AAC-LC** (Advanced Audio Coding Low Complexity) | Tiêu chuẩn phát thanh được hỗ trợ tự nhiên trên 100% thiết bị Apple, Android, Windows |
| **Channels** | **Mono (1 kênh)** | Sách nói giọng đọc một người; mono tiết kiệm 50% dung lượng so với stereo mà không giảm chất lượng giọng |
| **Sample Rate** | **44.1 kHz** hoặc **48 kHz** | Đảm bảo dải tần đầy đủ của giọng người (20Hz - 20kHz) |
| **Bitrate** | **64 kbps CBR** (hoặc 96 kbps cho nội dung có nhạc nền) | Mức 64k AAC cho giọng nói tương đương 128k MP3, chỉ tốn khoảng **~28 MB mỗi giờ nghe** |
| **Container Flag** | `-movflags +faststart` | Đẩy bảng Atom `moov` lên đầu file, cho phép phát ngay lập tức không cần đợi tải hết file |
| **Chapter Markers** | Chuẩn **FFMETADATA1** (Timebase 1/1000) | Ghi nhận mốc START và END chính xác đến từng mili-giây |
| **Cover Art** | Ảnh nhúng JPEG vuông (1400x1400 px, tối thiểu 600x600 px) | Chuẩn hiển thị của Apple Books, Audible, BookPlayer và màn hình CarPlay |

---

## 2. QUY CHUẨN QUÃNG NGHỈ (GAPS & PACING)

Việc ghép nối liên tục các đoạn âm thanh mà không có quãng nghỉ sẽ gây cảm giác ngột ngạt và vội vã. Hệ thống áp dụng quy tắc quãng nghỉ chuẩn studio:
- **Quãng nghỉ giữa các tiểu mục (Section Gap):** **1.5 giây** im lặng.
- **Quãng nghỉ giữa các chương (Chapter Gap):** **2.0 giây** im lặng.

---

## 3. KHẢ NĂNG TƯƠNG THÍCH ỨNG DỤNG NGHE SÁCH

| Môi trường / Thiết bị | Ứng dụng khuyến nghị | Tính năng hỗ trợ |
|---|---|---|
| **iPhone / iPad** | **Apple Books** (có sẵn)<br>**BookPlayer** (miễn phí) | Tự nhận bìa sách, hiện danh sách chương, nhớ vị trí nghe dở, hẹn giờ tắt, tăng giảm tốc độ đọc (1.25x, 1.5x) |
| **Màn hình Xe hơi** | **Apple CarPlay**<br>**Android Auto** | BookPlayer tự động hiển thị trên màn hình trung tâm của xe hơi: chuyển chương, tua 30s bằng phím vô lăng |
| **Android** | **BookPlayer**<br>**Smart AudioBook Player**<br>**Voice Audiobook Player** | Quản lý thư viện, tự đồng bộ mục lục chương M4B |
| **Máy tính (macOS/PC)** | **Apple Books** (macOS)<br>**VLC Media Player**<br>**Audiobookshelf** (tự lưu trữ) | Xem mục lục chương và nghe trực tiếp |
| **Máy nghe nhạc / USB xe hơi** | Bất kỳ máy nghe MP3 nào | Sử dụng thư mục `MP3/` đi kèm (đã được đánh số `01 - ...mp3`, `02 - ...mp3` và gắn thẻ ID3v2) |
