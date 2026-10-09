---
name: sach-noi
display-name: Sách Nói AI
description: >-
  Sản xuất sách nói chất lượng cao (.m4b có mục lục chương và thư mục MP3 ID3 tags) từ file EPUB, Word (DOCX), PDF, Markdown hoặc tóm tắt từ 'doc-sau'.
  Hỗ trợ 4 chế độ đọc: Đọc nguyên văn Cấp 1, Làm mượt Cấp 2, Chuyển thể văn sách nói Cấp 3 (mở đầu câu chuyện, thân bài tối đa 3 ý, kết thúc Ba ý cần nhớ theo phong cách Sano), và Sách nói tóm tắt (Audiobook Brief).
  Sử dụng giọng đọc AI offline chuẩn studio: VieNeu-TTS 48kHz (tiếng Việt 25 giọng Bắc/Trung/Nam) và Kokoro ONNX (tiếng Anh/Nhật), 100% không cần API key.
  USE WHEN: Người dùng muốn chuyển sách, ebook, tài liệu, giáo trình, bài viết hoặc báo cáo tóm tắt thành sách nói để nghe trên điện thoại (BookPlayer/Apple Books), ô tô (CarPlay/Android Auto) hoặc máy tính.
  DO NOT USE WHEN: Chỉ cần bóc tách OCR tài liệu scan đơn thuần (dùng 'boc-tach-pdf'), phân tích phản biện triết học chuyên sâu (dùng 'doc-sau'), dịch thuật tài liệu đa ngữ (dùng 'ejv-translate' hoặc 'dich-thuat'), hoặc sản xuất video có hình ảnh (dùng 'video-studio').
trigger: Tạo sách nói, sách nói AI, sach noi, lam sach noi, chuyen thanh sach noi, audiobook maker, xuat m4b, audio book, doc sach thanh audio
category: media
needs_file: true
file_filter: any
---

# Kỹ Năng Sách Nói AI (Audiobook Production Engine)

<goal>
Biến mọi tài liệu thành phẩm chữ (sách ebook EPUB, file Word DOCX, PDF có chữ, Markdown bài viết, hoặc báo cáo phân tích) thành một cuốn sách nói chuyên nghiệp:
1. **Container M4B chuẩn mực:** 1 file `.m4b` duy nhất có mục lục chương (chapter markers), ảnh bìa nhúng (cover art), nhớ vị trí nghe, tương thích 100% với Apple Books, BookPlayer (chạy trên màn hình xe hơi CarPlay/Android Auto), Audiobookshelf và VLC.
2. **Thư mục MP3 phân tách:** Từng chương đánh số thứ tự kèm đầy đủ thẻ ID3v2 (Title, Artist, Album, Track/Total, Attached Picture).
3. **Chất lượng phát thanh tự nhiên:** Chuẩn hóa câu chữ, số liệu, viết tắt để người nghe nắm bắt trọn vẹn kiến thức khi đang lái xe hoặc làm việc nhà.
</goal>

<context>
1. **Zero External LLM API (Luật R4):** 100% khả năng biên tập, tái cấu trúc câu chữ là của Agent nội bộ Antigravity. Mô hình giọng đọc chạy hoàn toàn offline bằng **VieNeu-TTS 48kHz** (tiếng Việt) và **Kokoro ONNX** (tiếng Anh/Nhật) qua engine dùng chung `_shared/media/tts.py`. Tuyệt đối không gọi REST API ngoài, không yêu cầu API key.
2. **Quy tắc Bảo vệ Codebase (Anti-Repo Bloat - Luật R1/R4):** Mọi file âm thanh thành phẩm (`.m4b`, thư mục `MP3/`) PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/`). Tuyệt đối cấm ghi file âm thanh nặng vào workspace repo. Vùng xử lý tạm đặt tại `<process_dir>` (`_process/audiobook_<ten_sach>/` đã được gitignore).
3. **Tái sử dụng Engine Dùng Chung (Luật R7):** Tái sử dụng tối đa hạ tầng `_shared/` (`doc_ingest_bridge`, `media.tts`, `media.ffmpeg`, `media.spoken_normalizer`, `media.audiobook_packager`).
4. **Autonomous Full-Run (Luật R3 §2):** Tự động thực hiện tuần tự các khâu: Bóc tách $\rightarrow$ Biên tập/Chuẩn hóa $\rightarrow$ Đọc thử mẫu (nếu yêu cầu) $\rightarrow$ Render toàn bộ $\rightarrow$ Đóng gói M4B $\rightarrow$ Bàn giao sạch.
</context>

---

## 🔧 Path Resolution & Thư Mục Lưu Trữ Đầu Ra

| Placeholder | Giá trị thực |
|---|---|
| `<skill_dir>` | `<workspace>/.agents/skills/sach-noi/` |
| `<process_dir>` | `<workspace>/_process/audiobook_<ten_sach>/` (đã gitignore) |
| `<output_dir>` | Nơi người dùng chỉ định, hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<output_book_dir>` | `<output_dir>/<Ten_Sach>/` |

---

## Bảng Tọa Độ Đầu Vào (Intake Coordinates)

| Trục | Giá trị tùy chọn | Mặc định nếu người dùng không nói |
|---|---|---|
| **1. Tệp nguồn** | File EPUB, DOCX, PDF có chữ, Markdown, TXT, hoặc báo cáo `_Doc_Sau.md` | Bắt buộc phải có file hoặc văn bản nguồn |
| **2. Chế độ đọc** | **Cấp 1:** Đọc nguyên bản<br>**Cấp 2:** Làm mượt (Smoothing)<br>**Cấp 3:** Viết lại văn sách nói (Sano Adaptive Storytelling)<br>**Cấp 4:** Sách nói tóm tắt (Audiobook Brief) | **Cấp 2** đối với sách/tài liệu thông thường; **Cấp 3** khi người dùng muốn nghe cuốn hút/dễ hiểu |
| **3. Giọng đọc** | • **Tiếng Việt (VieNeu 48kHz):** Thái Sơn (Nam Nam trầm ấm kể chuyện), Thùy Dung (Nữ Nam truyền cảm), Trúc Ly (Nữ Bắc dịu dàng), Mai Anh (Nữ Bắc thời sự), Minh Quân Pro (Nam Bắc đĩnh đạc), Quang Sơn (Nam Trung mộc mạc), Ngọc Trân (Nữ Huế sâu lắng).<br>• **Tiếng Anh/Nhật (Kokoro):** af_heart, am_adam, jf_alpha, jm_kumo. | **Thái Sơn** (cho sách kỹ năng/kinh doanh) hoặc **Trúc Ly** (cho tâm lý/văn học) |
| **4. Định dạng xuất** | • File `.m4b` đơn có chapter markers<br>• Thư mục MP3 từng chương gắn thẻ ID3v2<br>• Cả hai (.m4b + MP3) | **Cả hai** (.m4b và thư mục MP3) |

---

## 4 Chế Độ Đọc Chi Tiết (Reading Modes)

### 📌 CẤP 1 — Đọc Nguyên Bản (Verbatim Reading)
- Giữ nguyên 100% câu chữ của tác giả, giữ nguyên thứ tự chương mục.
- Chỉ đưa qua `spoken_normalizer.py` để chuẩn hóa cách đọc: mở rộng từ viết tắt (TP.HCM $\rightarrow$ Thành phố Hồ Chí Minh), số La Mã (Chương IV $\rightarrow$ Chương bốn), tỷ lệ phần trăm, phân số, và khử ngoặc kép tránh lỗi phát âm.

### 📌 CẤP 2 — Làm Mượt, Giữ Nguyên Ý (Smoothing)
- Giữ nguyên toàn bộ nội dung, quan điểm và cấu trúc của tác giả.
- Biến đổi hình thức để dễ tiếp nhận bằng tai:
  - Bảng biểu: Diễn giải thành câu văn mạch lạc, nêu rõ từng hàng/cột.
  - Sơ đồ/Hình vẽ: Tóm lược thành 1 đoạn ngắn mô tả thông điệp cốt lõi.
  - Lược bỏ các câu phụ thuộc thị giác trang giấy (*"xem hình bên dưới"*, *"như bảng trên"*, số trang, chú thích chân trang).
  - Tách các câu ghép quá dài thành câu đơn ngắn gọn, ngắt nhịp thở tự nhiên.

### 📌 CẤP 3 — Viết Lại Thành Văn Sách Nói (Sano Adaptive Storytelling)
- Áp dụng triết lý biên tập của Sano dành cho người nghe đang di chuyển, làm việc nhà hoặc tập thể dục:
  1. **Không làm mất kiến thức:** Giữ đủ mọi định nghĩa, khung nguyên tắc, điều kiện và ngoại lệ.
  2. **Không bịa đặt:** Tuyệt đối không thêm số liệu, sự kiện hay danh xưng không có trong tài liệu.
  3. **Khung mỗi chương (5 - 10 phút nghe ~ 800 - 1.800 từ):**
     - *Mục đầu chương:* Một câu chuyện hoặc tình huống thực tế dẫn nhập vấn đề.
     - *Thân bài:* Tối đa 3 luận điểm/ý lớn. Danh sách dài phải gom nhóm rõ ràng.
     - *Mục cuối chương:* Luôn có phần **"Ba ý cần nhớ"** đúc kết các khái niệm chính và 1 câu nối gợi mở sang chương sau.
  4. **Viết để nghe bằng tai:** Câu ngắn dưới 35 chữ, xen kẽ nhịp điệu, không dùng ngoặc đơn (ý trong ngoặc viết thành câu riêng).

### 📌 CẤP 4 — Sách Nói Tóm Tắt (Audiobook Brief)
- Nhận đầu vào là báo cáo tóm tắt chuyên sâu từ kỹ năng `doc-sau` (`<Ten>_Doc_Sau.md`).
- Bóc tách:
  - Phần 1: Tóm tắt điều hành & Luận điểm tối thượng (Executive Brief).
  - Phần 2: Hành trình các chương & Case study đắt giá (Chapter Journey).
  - Phần 3: 3 Bài học cốt lõi & Hành động 24h (Quick Win).
- Đóng gói thành 1 file sách nói tóm tắt ngắn (15 - 25 phút nghe) để nắm trọn cuốn sách trong một chuyến đi xe buýt hoặc lái xe ngắn.

---

<instructions>
## QUY TRÌNH SẢN XUẤT SÁCH NÓI 5 BƯỚC

### BƯỚC 1: Tiếp nhận tài liệu & Phân tích cấu trúc chương mục
1. Chạy công cụ bóc tách chung để chuyển tài liệu về Markdown cấu trúc:
   ```bash
   .venv/bin/python scripts/doc_ingest.py "<file_nguon>" --out <process_dir>/ingest --json
   ```
2. Phân tích `source.md`:
   - Xác định danh sách chương mục (Heading 1, "Chương N", TOC của EPUB/PDF).
   - Trích xuất ảnh bìa sách (nếu file EPUB/PDF có bìa) lưu vào `<process_dir>/cover.jpg`. Nếu không có bìa, sử dụng ảnh bìa mặc định hoặc tạo bìa đồ họa tối giản qua công cụ hỗ trợ.

### BƯỚC 2: Biên tập kịch bản đọc & Phân tách rõ ràng Phần Giới Thiệu vs. Nội Dung
- Tùy theo chế độ (Cấp 1, Cấp 2, Cấp 3, Cấp 4), Agent biên tập nội dung từng chương vào thư mục:
  `<process_dir>/chapters/chapter_01.txt`, `chapter_02.txt`, ...
- **Quy chuẩn bắt buộc phân tách Phần Giới Thiệu (Intro) và Phần Nội Dung (Body):**
  Để tạo nhịp thở tự nhiên như phát thanh viên chuyên nghiệp, mỗi chương phải phân định rõ 2 phần:
  1. **Hình thức 1 (Khuyến nghị — Thẻ tường minh):**
     ```markdown
     [GIỚI THIỆU]
     Chương 01: Lời Nói Đầu — Khởi Nguồn Của Những Mô Hình Tư Duy.
     (hoặc: Chào mừng bạn đến với sách nói [Tên Sách], tập một...)
     
     [NỘI DUNG]
     Vào một buổi sáng tháng 9 năm 2001, Shane Parrish mới vào làm việc...
     ```
  2. **Hình thức 2 (Dòng phân cách Markdown):**
     Đặt câu giới thiệu/tựa đề ở đầu, theo sau là dòng phân cách `---` trước khi bắt đầu nội dung.
- Lưu file kịch bản hoàn chỉnh `<output_book_dir>/<Ten_Sach>_Kich_Ban_Doc.docx` (hoặc `.md`) để người dùng có thể đọc đối chiếu.

### BƯỚC 3: Chuẩn hóa phát thanh tiếng Việt
Chạy engine dùng chung `spoken_normalizer.py` để biến đổi toàn bộ kịch bản sang văn nói chuẩn xác:
```bash
python3 .agents/skills/_shared/media/spoken_normalizer.py --input <process_dir>/chapters/chapter_NN.txt --output <process_dir>/spoken/chapter_NN.txt
```

### BƯỚC 4: Tạo giọng đọc AI Offline & Chèn Quãng Nghỉ Tách Biệt Giới Thiệu - Nội Dung
Sử dụng pipeline điều phối `build_audiobook.py` hoặc tổng hợp qua engine `tts.py`:
- Hệ thống tự động nhận diện `[GIỚI THIỆU]` và `[NỘI DUNG]`, tổng hợp thành 2 clip riêng và ghép nối với **quãng nghỉ 1.5s - 2.0s (mặc định 1.8s)** qua `concat_audio_files`.
- Phát thanh viên đọc xong câu giới thiệu/tựa đề $\rightarrow$ **nghỉ 1.8s lấy hơi** $\rightarrow$ bắt đầu đọc nội dung câu chuyện một cách trầm ấm, tự nhiên.
```bash
python3 .agents/skills/sach-noi/scripts/build_audiobook.py \
  --input "<process_dir>/source.md" \
  --title "<Tên Sách>" \
  --author "<Tác Giả>" \
  --voice "<tên_giọng>" \
  --intro-gap 1.8 \
  --output-dir "<output_dir>"
```
- Nếu sách dài, tiến trình ghi nhận trạng thái vào `<process_dir>/progress.json` để có thể tiếp tục (resume) nếu gián đoạn.

### BƯỚC 5: Đóng gói Sách nói M4B & MP3 tags
Sử dụng engine dùng chung `audiobook_packager.py` để tạo thành phẩm hoàn chỉnh:
```bash
python3 .agents/skills/_shared/media/audiobook_packager.py \
  --manifest <process_dir>/chapters_manifest.json \
  --output "<output_book_dir>/<Ten_Sach>.m4b" \
  --title "<Tên Sách>" \
  --author "<Tác Giả>" \
  --narrator "<Tên Giọng AI>" \
  --cover "<process_dir>/cover.jpg" \
  --gap 2.0 \
  --mp3-dir "<output_book_dir>/MP3"
```
</instructions>

---

<quality_gate>
## GIAO THỨC KIỂM ĐỊNH KÉP BẮT BUỘC TRƯỚC KHI BÀN GIAO (Luật R3 §9 & Luật R4 §2.6)

Trước khi gửi báo cáo hoàn thành cho người dùng, Agent **PHẢI** thực hiện kiểm tra thực tế và ghi nhận kết quả ở 2 góc nhìn độc lập:

### 1. Góc nhìn 1 — Thẩm định Kỹ thuật (Technical Perspective)
- [ ] **Kiểm tra File M4B:** File `.m4b` tồn tại, dung lượng $>0$, mở đọc bằng `ffprobe` xác nhận container AAC mono (bitrate 64k/96k, sample rate 44.1kHz).
- [ ] **Kiểm tra Mục lục Chương (Chapter Markers):** `ffprobe -show_chapters` hiển thị đúng $100\%$ số lượng chương, thời gian bắt đầu (START) và kết thúc (END) khớp chính xác, tiêu đề chương không bị lỗi font/dấu tiếng Việt.
- [ ] **Kiểm tra Bìa nhúng (Cover Art):** Stream video của file M4B có format `mjpeg` (`attached_pic`), hiển thị đúng ảnh bìa.
- [ ] **Kiểm tra Thư mục MP3:** Toàn bộ file MP3 được đánh số (`01 - ...mp3`, `02 - ...mp3`), thẻ ID3v2 có đủ Title, Artist, Album, Track/Total.
- [ ] **Tuân thủ Kiến trúc R7:** Script gọi lại 100% engine từ `_shared/media/`, không có file nhân bản, chạy `python3 scripts/check_shared_reuse.py` đạt 0 lỗi.

### 2. Góc nhìn 2 — Thẩm định Trải nghiệm Người dùng (User Experience & Delivery Perspective)
- [ ] **Chất lượng lời đọc phát thanh:** Không còn dấu ngoặc kép rác khiến TTS đọc thành chữ *"dấu ngoặc kép"*; các từ viết tắt phổ biến (TP.HCM, KPI, CEO, AI) và số La Mã (Chương IV) phát âm tự nhiên, êm tai.
- [ ] **Phân tách rành mạch Giới thiệu & Nội dung:** Phần Giới thiệu (tựa đề chương, lời dẫn nhập đầu sách) được tách riêng biệt với Phần Nội Dung bằng khoảng lặng 1.5s - 2.0s (mặc định 1.8s), tuyệt đối không đọc dính chùm xộc ngay vào thân bài.
- [ ] **Quãng nghỉ tự nhiên giữa các chương:** Giữa 2 chương có quãng nghỉ 2.0 giây tạo nhịp thở thư thái, không bị nuốt âm hay đọc dính liền vào nhau.
- [ ] **Tương thích thiết bị di động:** Người dùng chép file `.m4b` vào iPhone (qua AirDrop hoặc app BookPlayer) hoặc Android máy tự nhận đúng sách, đúng bìa, hiện mục lục chương trên màn hình ô tô (CarPlay/Android Auto).
- [ ] **Chống phình repository (Anti-Repo Bloat):** Thành phẩm nằm trọn vẹn trong `<output_book_dir>` (`~/Downloads/AIWF_Output/<Ten_Sach>/`), workspace hoàn toàn sạch sẽ.

### ⚠️ LỆNH CẤM: Zero Unverified Claims Ban (Luật R4 §3.6)
Tuyệt đối KHÔNG báo cáo "đã hoàn thành 100%" nếu chưa thực sự chạy lệnh kiểm tra dung lượng file và kiểm tra `ffprobe`. Mọi thông số thời lượng (phút, giây), số chương, dung lượng file bắt buộc phải trích xuất từ dữ liệu đo đạc thực tế.
- **Evidence Verifier & Confidence Flagging:** Mọi thông số thời lượng, dung lượng, số chương đều dựa trên bằng chứng đo đạc thực tế từ ffprobe và hệ thống file, ghi nhận trong `audit_report.json`. Khung chat chỉ tóm tắt ngắn gọn các chỉ số cốt lõi và link trỏ đến file thành phẩm.
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (Clean Delivery)

1. **Vị trí tệp bàn giao:**
   - File sách nói chính: `<output_book_dir>/<Ten_Sach>.m4b`
   - Thư mục MP3 từng chương: `<output_book_dir>/MP3/`
   - Kịch bản chữ phát thanh: `<output_book_dir>/<Ten_Sach>_Kich_Ban.docx`
2. **Nội dung tin nhắn trong chat:**
   - Khung chat chỉ tóm tắt ngắn thông số nghiệm thu: Tên sách, Tác giả, Giọng đọc AI, Tổng thời lượng nghe (phút:giây), Số chương mục, Dung lượng file M4B.
   - Bảng mục lục chương và thời lượng từng chương kèm link trỏ đến file thành phẩm.
   - Hướng dẫn nhanh cách nghe trên điện thoại (iPhone dùng app BookPlayer/Apple Books, Android dùng Smart AudioBook Player/BookPlayer) và trên màn hình ô tô qua CarPlay.
</delivery_protocol>

---

## 🧩 Engine dùng chung (Luật R7)

Kỹ năng này tái sử dụng các engine hạ tầng chung từ `.agents/skills/_shared/`:
- `doc_ingest_bridge` (`scripts/doc_ingest.py`): Đọc và bóc tách tệp EPUB, DOCX, PDF, MD.
- `media.spoken_normalizer` (`_shared/media/spoken_normalizer.py`): Chuẩn hóa phát thanh tiếng Việt.
- `media.tts` (`_shared/media/tts.py`): Tổng hợp giọng nói offline bằng VieNeu-TTS (48kHz) và Kokoro.
- `media.audiobook_packager` (`_shared/media/audiobook_packager.py`): Đóng gói M4B chaptered và xuất MP3 tags.
- `media.ffmpeg` (`_shared/media/ffmpeg_tools.py`): Quản lý binary ffmpeg/ffprobe và đo đạc thời lượng.
- `output_manager` (`_shared/output_manager.py`): Quản trị đường dẫn xuất bản chống phình repo.

