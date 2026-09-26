# CẨM NANG HƯỚNG DẪN SỬ DỤNG AI WORKFORCE (AIWF) v2.0

> **Mục tiêu cẩm nang:** Hướng dẫn nhanh, thực chiến và dễ hiểu nhất để bất kỳ ai cũng có thể khai thác tối đa sức mạnh của AI Workforce ngay trên Antigravity IDE (hoặc VS Code).  
> **Cam kết cốt lõi:** 100% Chạy cục bộ nội bộ, Không chi phí API bên ngoài, Ưu tiên **TỐC ĐỘ** xử lý và **ĐỘ CHÍNH XÁC** của kết quả.

---

## <a id="muc-luc" name="muc-luc"></a>Mục Lục Điều Hướng Nhanh

*Nhấp vào bất kỳ mục nào dưới đây để di chuyển ngay đến nội dung tương ứng:*

1. [1. AIWF Làm Được Gì Cho Bạn?](#1-aiwf-lam-duoc-gi)
2. [2. Bản Đồ 16 Kỹ Năng Đầy Đủ](#2-ban-do-16-ky-nang)
3. [3. Hướng Dẫn Chi Tiết Các Kỹ Năng Thường Dùng](#3-huong-dan-chi-tiet)
   - [3.1 Bóc Tách PDF Scan (boc-tach-pdf)](#31-boc-tach-pdf)
   - [3.2 Dịch Thuật Đa Ngôn Ngữ (ejv-translate)](#32-ejv-translate)
   - [3.3 Xử Lý Văn Phòng (xu-ly-van-phong)](#33-xu-ly-van-phong)
   - [3.4 Tư Vấn Pháp Lý (tu-van-phap-luat)](#34-tu-van-phap-luat)
   - [3.5 Tạo Video Tự Động (video-studio) 🆕](#35-video-studio)
   - [3.6 Viết Bài Đa Kênh (viet-bai)](#36-viet-bai)
   - [3.7 Tạo Phụ Đề Video (phu-de)](#37-phu-de)
   - [3.8 Tư Vấn Thuế TNCN (tu-van-thue-tncn)](#38-tu-van-thue-tncn)
4. [4. Sử Dụng Giao Diện AIWF Panel Trên IDE](#4-giao-dien-panel)
5. [5. Khai Thác Kho Tri Thức và Đồng Bộ NotebookLM](#5-kho-tri-thuc)
6. [6. Cơ Chế Đảm Bảo Tốc Độ và Độ Chính Xác](#6-evidence-verifier)
7. [7. Xử Lý Nhanh Sự Cố Thường Gặp (FAQ)](#7-faq)

---

## <a id="1-aiwf-lam-duoc-gi" name="1-aiwf-lam-duoc-gi"></a>1. AIWF Làm Được Gì Cho Bạn?

AI Workforce (AIWF) là nền tảng trợ lý số chuyên môn cao, tích hợp sẵn **16 kỹ năng nghiệp vụ thực chiến** và kho tri thức offline khổng lồ:

> [!TIP]
> **Vị trí lưu file thành phẩm:** Mọi file Word, Excel, Slide, Video sau khi hoàn thành sẽ được lưu mặc định vào thư mục **`~/Downloads/`** (hoặc thư mục bạn chỉ định) để bạn mở xem ngay mà không làm bẩn thư mục dự án.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

## <a id="2-ban-do-16-ky-nang" name="2-ban-do-16-ky-nang"></a>2. Bản Đồ 16 Kỹ Năng Đầy Đủ

| # | Kỹ năng | Mô tả | Thành phẩm đầu ra |
|---|---------|-------|-------------------|
| 1 | 📄 **`boc-tach-pdf`** | Số hóa PDF scan, tài liệu cũ mờ, OCR, trích xuất bảng biểu | File `.docx` giữ nguyên cấu trúc bảng, có thể chỉnh sửa |
| 2 | 🌐 **`ejv-translate`** | Dịch 3–4 ngôn ngữ: Việt – Anh – Nhật – Trung (y tế, hợp đồng, kỹ thuật) | File Word song ngữ/đơn ngữ, thuật ngữ chuẩn 100% |
| 3 | 📝 **`xu-ly-van-phong`** | Soạn văn bản hành chính NĐ 30, báo cáo, Excel, Slide | `.docx` chuẩn NĐ 30/2020; `.xlsx` công thức sống; `.pptx` |
| 4 | ⚖️ **`tu-van-phap-luat`** | Tra cứu pháp lý, án lệ, tranh chấp hợp đồng/đất đai/lao động | Báo cáo pháp lý 5 phần kèm dẫn chiếu điều luật nguyên văn |
| 5 | 💰 **`tu-van-thue-tncn`** | Tính thuế TNCN, quyết toán thuế, giảm trừ gia cảnh, BHXH | Báo cáo thuế chi tiết, hướng dẫn nộp eTax Mobile |
| 6 | ✍️ **`viet-bai`** | Viết bài blog SEO, Facebook, bài PR, nội dung web đa kênh | Bài viết hoàn chỉnh theo format kênh, chuẩn R5 pháp lý |
| 7 | 🎨 **`thiet-ke`** | Thiết kế leaflet, brochure, banner, xuất PDF in ấn | File PDF/SVG chuẩn CMYK, sẵn gửi nhà in |
| 8 | 📊 **`bao-cao-kt`** | Báo cáo tài chính, dashboard kinh doanh, Excel, Google Sheets | Excel/GSheets/Slides có biểu đồ trực quan |
| 9 | 🎬 **`video-studio`** 🆕 | Tạo video tự động từ ý tưởng: kịch bản → TTS → stock → BGM → phụ đề → MP4 | File `.mp4` hoàn chỉnh (Free HD / Premium 4K) |
| 10 | 🎤 **`long-tieng`** | Lồng tiếng, thuyết minh, dubbing video tự động | Video MP4 có giọng đọc lồng vào, BGM ducking |
| 11 | 📑 **`phu-de`** | Tạo phụ đề SRT/ASS, dịch phụ đề, hardsub, karaoke subtitle | File `.srt`/`.ass` hoặc video đã burn phụ đề cứng |
| 12 | 🖥️ **`tao-landing-page`** | Chuyển thiết kế/Figma/Stitch sang landing page HTML | File HTML/CSS hoàn chỉnh, deploy-ready |
| 13 | 🎞️ **`hand-drawn-animation`** | Phim hoạt hình vẽ tay: ink, riso, pencil, doodle, sand, rotoscope | HTML player + file MP4 offline |
| 14 | 🔍 **`app-auditor`** | Kiểm định ứng dụng, QA web, test giao diện, re-test bug | Báo cáo audit chi tiết, danh sách bug + severity |
| 15 | 📰 **`chotto-newsroom`** | Biên tập tin tức Chotto, điểm tin Nhật Bản cho người Việt | Bản tin ChottoDay hoàn chỉnh, ready-to-publish |
| 16 | 🔄 **`dich-giu-dinh-dang`** | Dịch PDF giữ nguyên bố cục, đồ họa, khung hoa văn (RetainPDF) | PDF song ngữ với bố cục 1:1 nguyên bản |

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

## <a id="3-huong-dan-chi-tiet" name="3-huong-dan-chi-tiet"></a>3. Hướng Dẫn Chi Tiết Các Kỹ Năng Thường Dùng

### <a id="31-boc-tach-pdf" name="31-boc-tach-pdf"></a>3.1 Bóc Tách PDF Scan và OCR Ra Word (`boc-tach-pdf`)

- **Khi nào nên dùng:** Khi bạn có file PDF scan từ máy in, hợp đồng chụp ảnh, hóa đơn chứng từ hoặc tài liệu scan bị nghiêng/mờ cần chuyển thành file Word để chỉnh sửa.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Hãy dùng skill `boc-tach-pdf` để bóc tách file scan này sang file Word giúp tôi: `/duong_dan/toi_file/hop_dong_scan.pdf`"*  
  > *(Hoặc chỉ cần kéo file vào chat và gõ: "Bóc tách file PDF scan này sang Word")*
- **Quy trình tự động:**
  1. AI tự động kiểm tra xem PDF là dạng text hay dạng scan ảnh.
  2. Bóc tách từng trang, phát hiện bảng biểu (Table Detection) bằng `pdfplumber`.
  3. Ghép nối và xuất thành file Word hoàn chỉnh (`.docx`) lưu tại `~/Downloads/`.
- **Mẹo:** Nếu tài liệu có nhiều trang và bạn chỉ cần 1 phần, ghi rõ số trang: *"Chỉ bóc tách từ trang 3 đến trang 7"*.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="32-ejv-translate" name="32-ejv-translate"></a>3.2 Dịch Thuật Đa Ngôn Ngữ Chuyên Sâu (`ejv-translate`)

- **Khi nào nên dùng:** Dịch tài liệu y tế (hồ sơ bệnh án, hướng dẫn thiết bị), hợp đồng kinh tế, tài liệu kỹ thuật giữa các thứ tiếng: **Việt – Anh – Nhật – Trung**.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Dịch file hợp đồng này từ tiếng Nhật sang tiếng Việt, giữ nguyên toàn bộ bảng biểu và căn lề: `/duong_dan/hop_dong_tieng_nhat.docx`"*  
  > *(Hoặc: "Dịch tài liệu y tế này sang tiếng Anh theo bảng thuật ngữ chuẩn")*
- **Quy trình tự động:**
  1. AI trích xuất nội dung và đối chiếu bộ từ điển thuật ngữ chuyên ngành có sẵn.
  2. Dịch theo từng đoạn (chunk) để không bị sót ý hoặc mất liên kết.
  3. Ráp nối lại thành file Word: bản dịch đơn ngữ hoặc bản đối chiếu song ngữ (cột song song).
- **Mẹo:** Ghi rõ bạn muốn xuất dạng song ngữ hay đơn ngữ: *"Xuất file Word song ngữ Nhật–Việt dạng bảng 2 cột"*.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="33-xu-ly-van-phong" name="33-xu-ly-van-phong"></a>3.3 Xử Lý Văn Phòng Chuẩn Hóa (`xu-ly-van-phong`)

- **Khi nào nên dùng:** Soạn thảo công văn, tờ trình, quyết định, biên bản họp chuẩn thể thức; tạo bảng tính Excel có công thức tính tự động; tạo slide thuyết trình chuyên nghiệp.
- **Cách ra lệnh (Prompt mẫu):**
  - *Soạn văn bản hành chính:*
    > *"Soạn thảo Tờ trình xin phê duyệt kế hoạch ngân sách quý 4 theo đúng chuẩn thể thức Nghị định 30/2020/NĐ-CP"*
  - *Tạo bảng tính Excel:*
    > *"Tạo bảng theo dõi doanh thu và công nợ khách hàng quý 3 bằng file Excel, có sẵn các công thức tính tổng và tỷ lệ tự động"*
  - *Tạo bài thuyết trình Slide:*
    > *"Tạo slide PowerPoint giới thiệu dự án chuyển đổi số gồm 7 trang từ dàn ý này..."*
- **Quy trình tự động:**
  - AI hỏi bạn chọn: `[1] Chuẩn công quyền NĐ 30` (font Times New Roman, thể thức nghiêm ngặt) hoặc `[2] Chuẩn doanh nghiệp hiện đại` (màu sắc nhận diện thương hiệu, bố cục hiện đại).
  - Tự động chạy script sinh file `.docx`, `.xlsx` hoặc `.pptx` và lưu ra `~/Downloads/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="34-tu-van-phap-luat" name="34-tu-van-phap-luat"></a>3.4 Tư Vấn Pháp Lý và Tra Cứu Luật (`tu-van-phap-luat`)

- **Khi nào nên dùng:** Khi cần tra cứu xem một hành vi/sự việc có vi phạm pháp luật hay không, tranh chấp hợp đồng kinh doanh, thủ tục đất đai, tranh chấp lao động, bảo hiểm.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tư vấn giúp tôi trường hợp công ty đơn phương chấm dứt hợp đồng lao động với nhân viên mang thai thì rủi ro pháp lý là gì và điều khoản nào quy định?"*
- **Quy trình tự động:**
  1. AI xác định 5 trục tọa độ: Lĩnh vực, Chủ thể, Hành vi, Mốc thời gian, Yêu cầu.
  2. Tra cứu đối chiếu với kho văn bản quy phạm pháp luật và án lệ.
  3. Chạy công cụ **Evidence Verifier** để đối chiếu trích dẫn nguyên văn điều luật, không đoán mò.
  4. Xuất báo cáo pháp lý đầy đủ: Tóm tắt $\rightarrow$ Căn cứ pháp lý $\rightarrow$ Đánh giá rủi ro $\rightarrow$ Phương án xử lý cụ thể.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="35-video-studio" name="35-video-studio"></a>3.5 Tạo Video Tự Động (`video-studio`) 🆕

> [!NOTE]
> **Skill mới nhất** — AIWF Video Studio cho phép tạo video hoàn chỉnh từ ý tưởng đến file MP4 chỉ trong một lệnh duy nhất.

- **Khi nào nên dùng:** Khi cần tạo video giới thiệu sản phẩm, video giáo dục, video tin tức, reel truyền thông xã hội — hoàn toàn tự động không cần phần mềm edit video.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tạo video giới thiệu về cuộc sống tại Nhật Bản, thuyết minh tiếng Việt, có nhạc nền và phụ đề song ngữ Việt–Nhật"*
- **2 chế độ sử dụng:**
  - **Chế độ Chat (đơn giản nhất):** Gõ yêu cầu trực tiếp trong chat, AI sẽ tự chạy pipeline.
  - **Chế độ CLI:**
    ```bash
    source .venv-tts/bin/activate
    # Free Tier — HD 1080p
    python3 .agents/skills/video-studio/scripts/video_pipeline.py \
      --topic "Chủ đề video của bạn" --tier free --lang vi
    # Premium Tier — 4K UHD
    python3 .agents/skills/video-studio/scripts/video_pipeline.py \
      --topic "Chủ đề video của bạn" --tier premium --lang vi \
      --output ~/Downloads/ten_video.mp4
    ```
  - **Chế độ Web Studio** (giao diện đồ họa):
    ```bash
    python3 .agents/skills/video-studio/scripts/video_studio_server.py --port 8800
    # Mở trình duyệt tại: http://localhost:8800
    ```
- **Pipeline tự động (7 bước):**
  1. 🤖 AI viết kịch bản từ chủ đề bạn cung cấp.
  2. 🗣️ Thuyết minh TTS (Edge-TTS Neural, giọng Việt/Nhật chuẩn truyền cảm).
  3. 🎥 Tìm và tải video stock từ Pexels/Pixabay (Free: HD, Premium: 4K UHD).
  4. 🎧 Tìm nhạc nền phù hợp tâm trạng kịch bản, tự động ducking sidechain.
  5. 📑 Render phụ đề karaoke song ngữ (chữ chạy từng ký tự).
  6. ✂️ Ghép nối timeline hoàn chỉnh bằng FFmpeg.
  7. 💾 Xuất file `.mp4` vào `~/Downloads/`.
- **Cấu hình API Keys:** Tạo file `.env` tại workspace root với `PEXELS_API_KEY` và `PIXABAY_API_KEY` (xem `.agents/skills/video-studio/templates/.env.example`).

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="36-viet-bai" name="36-viet-bai"></a>3.6 Viết Bài Đa Kênh (`viet-bai`)

- **Khi nào nên dùng:** Viết bài blog SEO, caption Facebook/Instagram, bài PR thương hiệu, nội dung landing page, bản tin nội bộ.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Viết bài blog SEO 1500 từ về chủ đề [X], tối ưu từ khóa [Y], giọng văn chuyên nghiệp nhưng gần gũi"*  
  > *"Viết 5 caption Facebook cho sản phẩm [tên], tone vui tươi, có call-to-action"*
- **Lưu ý R5:** Mọi nội dung tiếp thị được tự động kiểm duyệt pháp lý (Luật Quảng cáo 2012) — không sinh ra từ ngữ over-claim như "số 1", "an toàn tuyệt đối".

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="37-phu-de" name="37-phu-de"></a>3.7 Tạo Phụ Đề Video (`phu-de`)

- **Khi nào nên dùng:** Khi bạn có video (Nhật/Anh/Việt) cần tạo phụ đề để đăng mạng xã hội, hoặc cần dịch phụ đề sang ngôn ngữ khác.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tạo phụ đề tiếng Việt cho video này và burn phụ đề cứng vào video: `/duong_dan/video.mp4`"*  
  > *"Dịch file phụ đề SRT này từ tiếng Nhật sang tiếng Việt"*
- **Thành phẩm:** File `.srt` / `.ass` hoặc video MP4 đã có phụ đề burn cứng (hardsub), sẵn sàng upload.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="38-tu-van-thue-tncn" name="38-tu-van-thue-tncn"></a>3.8 Tư Vấn Thuế TNCN (`tu-van-thue-tncn`)

- **Khi nào nên dùng:** Tính thuế thu nhập cá nhân, quyết toán thuế cuối năm, tra cứu giảm trừ gia cảnh, tư vấn thuế freelancer, thuế bất động sản, BHXH một lần.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tôi thu nhập 25 triệu/tháng, có 1 người phụ thuộc, đã đóng BHXH. Tính thuế TNCN phải nộp và hướng dẫn quyết toán trên eTax Mobile"*
- **Lưu ý:** Kết quả tư vấn dựa trên kho tri thức nội bộ (văn bản pháp luật thuế hiện hành), có đính kèm điều luật tham chiếu — không phải lời khuyên pháp lý chính thức.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

## <a id="4-giao-dien-panel" name="4-giao-dien-panel"></a>4. Sử Dụng Giao Diện AIWF Panel Trên IDE (Click Chuột 1-Chạm)

Nếu bạn không muốn gõ lệnh dài trong khung chat, bạn có thể thao tác bằng chuột trực tiếp qua Extension **AI Workforce Panel**:

1. **Mở thanh công cụ:**
   - Trên thanh bên trái (Activity Bar) của Antigravity IDE hoặc VS Code, nhấp vào biểu tượng **AI Workforce** (hình robot/thư mục).
2. **Chọn Nguồn & Kỹ năng:**
   - **Mục Workflows:** Nhấp biểu tượng 📖 **Sổ tay AIWF** để mở trực tiếp cẩm nang này bất kỳ lúc nào.
   - **Mục 1 — Workspace Files:** Duyệt và nhấp chọn file tài liệu bạn muốn xử lý.
   - **Mục 2 — Smart Knowledge:** Nhấp chọn Notebook chuyên môn cần tra cứu (ví dụ: *Bộ Luật Dân Sự*, *Tài liệu Y tế EJV*, *Sổ tay Quản trị*).
   - **Mục 3 — Skill Actions:** Nhấp trực tiếp vào nút kỹ năng tương ứng:
     - 🖨️ `Bóc tách PDF`
     - 🈂️ `EJV Translate`
     - 📝 `Xử lý Văn phòng`
     - ⚖️ `Tư vấn Pháp luật`
3. **Xem Dashboard tổng quan:**
   - Mở file `dashboard/index.html` trên trình duyệt để xem bản đồ trực quan toàn bộ kỹ năng và danh mục tài liệu.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

## <a id="5-kho-tri-thuc" name="5-kho-tri-thuc"></a>5. Khai Thác Kho Tri Thức và Đồng Bộ NotebookLM

AIWF đã tích hợp sẵn kho tri thức với hơn **750 tài liệu chuyên sâu** nằm trong thư mục `.agents/knowledge/`. Toàn bộ dữ liệu này có thể tra cứu ngay lập tức mà không cần kết nối mạng.

### Khi bạn muốn kéo thêm tài liệu mới từ tài khoản Google NotebookLM cá nhân:

Chỉ cần thực hiện 2 bước đơn giản qua Terminal:

1. **Đăng nhập Google NotebookLM (Chỉ cần làm 1 lần duy nhất):**
   ```bash
   notebooklm login
   ```
   *(Trình duyệt sẽ tự động bật lên để bạn đăng nhập tài khoản Google và cấp quyền)*

2. **Kéo dữ liệu mới về máy:**
   ```bash
   python3 scripts/sync_notebook.py --all
   ```
   *(Hệ thống sẽ tự động tải các tài liệu mới nhất về lưu dưới dạng Markdown chuẩn trong `.agents/knowledge/` để AIWF sử dụng)*

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

## <a id="6-evidence-verifier" name="6-evidence-verifier"></a>6. Cơ Chế Đảm Bảo Tốc Độ và Độ Chính Xác (Evidence Verifier)

Để phục vụ môi trường làm việc thực chiến, AIWF áp dụng quy tắc **Vòng đời 3 Bước Tinh gọn**:

```
[1. Tiếp nhận (Intake)]      [2. Xử lý & Kiểm chứng]       [3. Bàn giao sạch (Delivery)]
File gốc / Đề bài       →    Thư mục tạm _process/     →    Xuất file ra ~/Downloads/
Đối chiếu mẫu chuẩn          Chạy Evidence Verifier         Chat chỉ tóm tắt ngắn + Link
                             (Chống bịa số/điều luật)
```

### Công cụ Kiểm chứng Bằng chứng (`scripts/harness/evidence_verifier.py`)
- **Tốc độ:** Chạy 100% bằng Python thuần (`stdlib`), hoàn thành kiểm tra trong dưới 10 mili-giây.
- **Nhiệm vụ:** Kiểm tra xem mọi điều luật, số liệu hoặc trích dẫn mà AI đưa ra có xuất hiện nguyên văn trong tài liệu gốc hay không.
- **Kết quả:** Nếu phát hiện trích dẫn không có thật hoặc bịa đặt $\rightarrow$ Hệ thống lập tức cảnh báo để chỉnh sửa trước khi xuất bản thành phẩm.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

## <a id="7-faq" name="7-faq"></a>7. Xử Lý Nhanh Sự Cố Thường Gặp (FAQ và Troubleshooting)

### ❓ "AI báo không tìm thấy skill hoặc không hiểu lệnh?"
- **Cách xử lý:** Nhắn trực tiếp câu lệnh chuẩn: *"Đồng bộ quy tắc từ README.md"* hoặc chạy lệnh:
  ```bash
  bash scripts/auto-setup.sh
  ```
  Hệ thống sẽ tự động quét lại toàn bộ kỹ năng và kích hoạt môi trường trong 5 giây.

### ❓ "File Word hoặc Excel tải về mở ra có bị lỗi định dạng không?"
- **Trả lời:** Không. AIWF sử dụng bộ thư viện native của Microsoft Office (`python-docx`, `openpyxl`) và bộ mã UTF-8 chuẩn nên file hiển thị chuẩn 100% trên cả Microsoft Word, Excel máy tính lẫn Google Docs/Sheets.

### ❓ "Tôi muốn đổi nơi lưu file kết quả sang Desktop thay vì Downloads thì làm thế nào?"
- **Cách xử lý:** Trong câu lệnh yêu cầu, thêm câu: *"Lưu file kết quả ra Desktop giúp tôi"*. AIWF sẽ tự động điều hướng file thành phẩm về `~/Desktop/`.

### ❓ "Skill `video-studio` báo lỗi thiếu thư viện?"
- **Cách xử lý:** Chạy lệnh kích hoạt virtual environment trước:
  ```bash
  source .venv-tts/bin/activate
  pip install -r .agents/skills/video-studio/requirements.txt
  ```

### ❓ "Dữ liệu của tôi có bị gửi ra bên ngoài không?"
- **Trả lời:** Tuyệt đối không. AIWF chạy 100% cục bộ trên mô hình LLM tích hợp sẵn của Antigravity IDE, không gọi bất kỳ REST API bên thứ ba nào (ngoại trừ Pexels/Pixabay khi dùng `video-studio` để tải stock footage), không phát sinh chi phí token bên ngoài.

### ❓ "Làm sao để xem danh sách đầy đủ 16 skills?"
- Xem [Bản Đồ 16 Kỹ Năng](#2-ban-do-16-ky-nang) ở mục 2, hoặc gõ trong chat: *"Liệt kê tất cả skills AIWF hiện có"*.

---

[⬆ Về đầu trang / Mục lục](#muc-luc)

*AI Workforce Handbook v2.0 — Cập nhật 2026-09-26 — 16 skills đầy đủ bao gồm Video Studio mới nhất.*
