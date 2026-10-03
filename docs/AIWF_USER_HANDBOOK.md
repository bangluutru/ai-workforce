# CẨM NANG HƯỚNG DẪN SỬ DỤNG AI WORKFORCE (AIWF) v2.1

> **Mục tiêu cẩm nang:** Hướng dẫn nhanh, thực chiến và dễ hiểu nhất để bất kỳ ai cũng có thể khai thác tối đa sức mạnh của AI Workforce ngay trên Antigravity IDE (hoặc VS Code).  
> **Cam kết cốt lõi:** 100% Chạy cục bộ nội bộ, Không chi phí API bên ngoài, Ưu tiên **TỐC ĐỘ** xử lý và **ĐỘ CHÍNH XÁC** của kết quả.

---

## <a id="muc-luc" name="muc-luc"></a>Mục Lục Điều Hướng Nhanh

*Nhấp vào bất kỳ mục nào dưới đây để di chuyển ngay đến nội dung tương ứng:*

1. [1. AIWF Làm Được Gì Cho Bạn?](#1-aiwf-lam-duoc-gi)
2. [2. Bản Đồ 18 Kỹ Năng Đầy Đủ](#2-ban-do-18-ky-nang)
3. [3. Hướng Dẫn Chi Tiết 18 Kỹ Năng Thực Chiến](#3-huong-dan-chi-tiet)
   - [3.1 Bóc Tách PDF](#31-boc-tach-pdf)
   - [3.2 EJV Translate](#32-ejv-translate)
   - [3.3 Dịch Thuật](#33-dich-thuat)
   - [3.4 Xử Lý Văn Phòng](#34-xu-ly-van-phong)
   - [3.5 Báo Cáo Kế Toán](#35-bao-cao-kt)
   - [3.6 Tư Vấn Pháp Luật](#36-tu-van-phap-luat)
   - [3.7 Tư Vấn Thuế](#37-tu-van-thue)
   - [3.8 Viết Bài Đa Kênh](#38-viet-bai)
   - [3.9 Thiết Kế Đồ Họa](#39-thiet-ke)
   - [3.10 Tạo Landing Page](#310-tao-landing-page)
   - [3.11 Kiểm Định Ứng Dụng](#311-app-auditor)
   - [3.12 Studio Video](#312-video-studio)
   - [3.13 Tạo Phụ Đề](#313-phu-de)
   - [3.14 Lồng Tiếng Video](#314-long-tieng)
   - [3.15 Tạo Hoạt Hình](#315-hand-drawn-animation)
   - [3.16 Biên Tập Tin Chotto](#316-chotto-newsroom)
   - [3.17 Đọc Sâu](#317-doc-sau)
   - [3.18 Tư Vấn Pháp Luật Nhật Bản](#318-tu-van-phap-luat-nhat-ban)
4. [4. Sử Dụng Giao Diện AIWF Panel Trên IDE](#4-giao-dien-panel)
5. [5. Khai Thác Kho Tri Thức và Đồng Bộ NotebookLM](#5-kho-tri-thuc)
6. [6. Cơ Chế Đảm Bảo Tốc Độ và Độ Chính Xác](#6-evidence-verifier)
7. [7. Xử Lý Nhanh Sự Cố Thường Gặp (FAQ)](#7-faq)

---

## <a id="1-aiwf-lam-duoc-gi" name="1-aiwf-lam-duoc-gi"></a>1. AIWF Làm Được Gì Cho Bạn?

AI Workforce (AIWF) là nền tảng trợ lý số chuyên môn cao, tích hợp sẵn **18 kỹ năng nghiệp vụ thực chiến** và kho tri thức offline phong phú:

> [!TIP]
> **Vị trí lưu file thành phẩm:** Mọi file Word, Excel, Slide, PDF, Video sau khi hoàn thành sẽ được lưu mặc định vào thư mục **`~/Downloads/AIWF_Output/`** (hoặc thư mục bạn chỉ định) để bạn mở xem ngay mà không làm bẩn thư mục dự án.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

## <a id="2-ban-do-18-ky-nang" name="2-ban-do-18-ky-nang"></a>2. Bản Đồ 18 Kỹ Năng Đầy Đủ

| # | Kỹ năng | Mô tả | Thành phẩm đầu ra |
|---|---|---|---|
| 1 | 📄 **Bóc Tách PDF** | Số hóa PDF scan, tài liệu cũ mờ, OCR, trích xuất bảng biểu | File `.docx` giữ nguyên cấu trúc bảng, có thể chỉnh sửa |
| 2 | 🌐 **EJV Translate** | Dịch 3–4 ngôn ngữ (Việt – Anh – Nhật – Trung) hành chính, kỹ thuật, y tế | File Word song ngữ/đơn ngữ, thuật ngữ chuẩn 100% |
| 3 | 🔄 **Dịch Thuật** | Dịch PDF với 2 chế độ: preserve (giữ 1:1 bố cục, con dấu SMask) hoặc reconstruct (tái dựng reflow, bảng, công thức) | File PDF dịch 1:1 hoặc PDF dàn trang tự nhiên |
| 4 | 📝 **Xử Lý Văn Phòng** | Soạn văn bản hành chính NĐ 30, báo cáo, Excel công thức sống, Slide | `.docx` chuẩn NĐ 30/2020; `.xlsx` Live Formulas; `.pptx` |
| 5 | 📊 **Báo Cáo Kế Toán** | Lập P&L (mẫu B02 theo TT200 / TT133 / TT99), Dashboard KPI, 100% Live Formulas | `.xlsx` công thức sống, slide thuyết trình `.pptx` |
| 6 | ⚖️ **Tư Vấn Pháp Luật** | Tra cứu điều khoản, án lệ, tư vấn tranh chấp theo PDCA Cascade, Evidence Verifier | Báo cáo pháp lý kèm trích dẫn điều luật nguyên văn |
| 7 | 💰 **Tư Vấn Thuế** | Thuế TNCN (quyết toán, Gross-Net, eTax Mobile), TNDN, GTGT, hộ kinh doanh, hóa đơn điện tử, tiền chậm nộp | Bảng tính thuế XLSX Live Formulas, văn bản tư vấn |
| 8 | ✍️ **Viết Bài Đa Kênh** | Viết blog SEO, Facebook, bài PR, nội dung web đa kênh tuân thủ Luật R5 | Bài viết hoàn chỉnh theo format kênh, chuẩn pháp lý |
| 9 | 🎨 **Thiết Kế Đồ Họa** | Thiết kế ấn phẩm in ấn (Leaflet, Brochure gấp 2/3, Poster, Tờ rơi, Slide PDF) | PDF in ấn có bleed 3mm, TrimBox/BleedBox, chuẩn CMYK |
| 10 | 🖥️ **Tạo Landing Page** | Chuyển đổi Figma/Stitch/mockup thành Landing Page React + Vite + TS + Tailwind | Mã nguồn trang đích hoàn chỉnh, tích hợp Landing Hub |
| 11 | 🔍 **Kiểm Định Ứng Dụng** | Kiểm định toàn diện web app: Playwright crawler, visual sweep 4 viewports, console/WCAG | Báo cáo audit chi tiết, danh sách bug P0-P4 có ảnh bằng chứng |
| 12 | 🎬 **Studio Video** | Sản xuất video tự động từ ý tưởng: kịch bản → TTS → stock footage → BGM ducking → phụ đề karaoke → MP4 | File `.mp4` hoàn chỉnh (Free HD / Premium 4K) |
| 13 | 📑 **Tạo Phụ Đề** | Tạo, bóc tách và biên tập phụ đề video (SRT, ASS, hardsub MP4) với forced alignment | File `.srt`/`.ass` hoặc video MP4 đã gắn phụ đề cứng |
| 14 | 🎤 **Lồng Tiếng Video** | Lồng tiếng và thuyết minh video tự động bằng TTS offline đa ngữ/vùng miền, Smart Ducking | Video MP4 đã khớp voiceover, audio track chuẩn |
| 15 | 🎞️ **Tạo Hoạt Hình** | Phim hoạt hình vẽ tay Canvas 2D (ink, riso, screen, pencil, doodle), rotoscope, sand | HTML player tương tác + file video MP4 offline |
| 16 | 📰 **Biên Tập Tin Chotto** | Tòa soạn tin tức hàng ngày chottoday.com, quét nguồn chính phủ Nhật (.go.jp), Fact Pack | Gói duyệt tin và bài viết hoàn chỉnh kèm ảnh minh họa |
| 17 | 🧠 **Đọc Sâu** | Mổ xẻ cấu trúc bài viết/sách qua 10+ mô hình tư duy (SCQA, 5W2H, phản biện, đảo ngược) | Báo cáo phân tích chuyên sâu, Executive Summary, Kế hoạch 24h |
| 18 | ⚖️ **Tư Vấn Pháp Luật Nhật Bản** | Tư vấn pháp lý Nhật Bản theo tình huống, tra cứu mã HS hải quan Nhật, thuế quan, EPA/FTA, lưu hành hàng hóa | Báo cáo pháp lý Nhật Bản, bảng thuế ước tính |

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

## <a id="3-huong-dan-chi-tiet" name="3-huong-dan-chi-tiet"></a>3. Hướng Dẫn Chi Tiết 18 Kỹ Năng Thực Chiến

### <a id="31-boc-tach-pdf" name="31-boc-tach-pdf"></a>3.1 Bóc Tách PDF

- **Khi nào nên dùng:** Khi bạn có file PDF scan từ máy in, hợp đồng chụp ảnh, hóa đơn chứng từ hoặc tài liệu scan bị nghiêng, mờ cần chuyển thành file Word để chỉnh sửa.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Hãy bóc tách file scan này sang file Word giúp tôi: `/duong_dan/hop_dong_scan.pdf`"*  
  > *(Hoặc chỉ cần kéo file vào chat và gõ: "Bóc tách file PDF scan này sang Word")*
- **Quy trình tự động:**
  1. AI tự động kiểm tra xem PDF là dạng text hay dạng scan ảnh.
  2. Bóc tách từng trang, phát hiện bảng biểu (Table Detection) bằng `pdfplumber`.
  3. Ghép nối và xuất thành file Word hoàn chỉnh (`.docx`) lưu tại `~/Downloads/AIWF_Output/`.
- **Mẹo:** Nếu tài liệu có nhiều trang và bạn chỉ cần một phần, ghi rõ số trang: *"Chỉ bóc tách từ trang 3 đến trang 7"*.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="32-ejv-translate" name="32-ejv-translate"></a>3.2 EJV Translate

- **Khi nào nên dùng:** Dịch tài liệu y tế (hồ sơ bệnh án, hướng dẫn thiết bị), hợp đồng kinh tế, tài liệu kỹ thuật giữa các thứ tiếng: **Việt – Anh – Nhật – Trung**. Đầu ra là file Word đơn ngữ hoặc đối chiếu song ngữ.
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

### <a id="33-dich-thuat" name="33-dich-thuat"></a>3.3 Dịch Thuật

- **Khi nào nên dùng:** Dịch tài liệu PDF có lớp chữ mà kết quả bắt buộc phải là file PDF hoàn chỉnh. Tích hợp 2 chế độ chuyên sâu:
  - **Chế độ preserve (bảo toàn):** Giữ nguyên 1:1 bố cục, số trang, hình ảnh, con dấu pháp nhân trong suốt (SMask Alpha), khung hoa văn an toàn, đồ thị đa phần tử. Thích hợp cho chứng chỉ, bằng khen, công văn có con dấu, chuyên khảo 2 cột.
  - **Chế độ reconstruct (tái cấu trúc):** Tái dựng tài liệu bằng reflow tự nhiên, khôi phục bảng biểu, công thức toán học/LaTeX, diagram, đồ thị cho dễ đọc. Thích hợp cho kỷ yếu học thuật, báo cáo chuyên sâu.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Dịch file chứng chỉ PDF này sang tiếng Việt, giữ nguyên 1:1 bố cục và con dấu pháp nhân: `/duong_dan/chung_chi.pdf`"*  
  > *(Hoặc: "Dịch tài liệu PDF này sang tiếng Anh theo chế độ tái cấu trúc reflow cho dễ đọc")*
- **Quy trình tự động:**
  1. Bóc tách tài nguyên đồ họa (ảnh, dấu, biểu đồ) bằng engine xử lý cục bộ.
  2. Khảo sát thuật ngữ chuyên ngành (Domain Review) và dịch 2 lượt không sót chữ nguồn (Luật R6 & R3 §8).
  3. Dàn trang Typst và chạy cổng kiểm định đối chiếu 3 lớp trước khi xuất bản.
- **Thành phẩm:** File PDF dịch hoàn chỉnh kèm báo cáo kiểm định toàn vẹn lưu tại `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="34-xu-ly-van-phong" name="34-xu-ly-van-phong"></a>3.4 Xử Lý Văn Phòng

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
  - Tự động chạy script sinh file `.docx`, `.xlsx` hoặc `.pptx` và lưu ra `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="35-bao-cao-kt" name="35-bao-cao-kt"></a>3.5 Báo Cáo Kế Toán

- **Khi nào nên dùng:** Lập Báo cáo kết quả hoạt động kinh doanh (P&L, mẫu B02 theo TT200 / TT133 / TT99), phân tích biên lợi nhuận, so sánh kỳ này với kỳ trước, dựng dashboard KPI kinh doanh có biểu đồ.
- **100% Live Formulas:** Toàn bộ chỉ tiêu tổng (mã 10, 20, 30, 40, 50, 60), biên gộp, biên ròng, chênh lệch, tăng trưởng và ô KPI đều dùng công thức sống của Excel, tuyệt đối không tính nhẩm gõ số chết.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Lập báo cáo kết quả kinh doanh P&L quý 3 theo Thông tư 200 từ bảng số liệu này, có dashboard KPI và slide tóm tắt: `/duong_dan/so_lieu_quy3.xlsx`"*
- **Quy trình tự động:**
  1. Intake số liệu từ bảng tính, text hoặc PDF báo cáo.
  2. Chuẩn hóa dữ liệu sang cấu trúc P&L chuẩn theo chế độ kế toán đã chọn.
  3. Dựng file Excel `.xlsx` gồm sheet Dashboard và sheet Báo cáo P&L có công thức liên kết động.
  4. Xuất bộ slide thuyết trình `.pptx` tóm tắt lấy số liệu đồng bộ từ cùng một nguồn.
- **Thành phẩm:** File `.xlsx` và slide `.pptx` lưu tại `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="36-tu-van-phap-luat" name="36-tu-van-phap-luat"></a>3.6 Tư Vấn Pháp Luật

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

### <a id="37-tu-van-thue" name="37-tu-van-thue"></a>3.7 Tư Vấn Thuế

- **Khi nào nên dùng:** Tư vấn và tính thuế Việt Nam cho cá nhân, hộ kinh doanh và doanh nghiệp: thuế TNCN (quyết toán, giảm trừ gia cảnh, Gross - Net, freelancer, bất động sản, BHXH một lần), thuế TNDN, thuế GTGT, thuế khoán hộ kinh doanh, hóa đơn điện tử, tiền chậm nộp và hoàn thuế.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tôi thu nhập 35 triệu/tháng, có 1 người phụ thuộc, đã đóng BHXH. Tính thuế TNCN phải nộp và hướng dẫn quyết toán trên eTax Mobile"*
- **Quy trình tự động:**
  1. Thu thập các thông số thu nhập, người phụ thuộc, các khoản giảm trừ và đóng bảo hiểm.
  2. Áp dụng biểu thuế lũy tiến từng phần và quy định giảm trừ gia cảnh hiện hành.
  3. Lập bảng tính thuế Excel chi tiết với 100% công thức sống Live Formulas.
  4. Cung cấp lộ trình từng bước quyết toán thuế thực tế qua ứng dụng eTax Mobile.
- **Thành phẩm:** Văn bản tư vấn chi tiết kèm bảng tính `.xlsx` lưu tại `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="38-viet-bai" name="38-viet-bai"></a>3.8 Viết Bài Đa Kênh

- **Khi nào nên dùng:** Viết bài blog SEO, caption Facebook/Instagram/LinkedIn, bài PR thương hiệu, nội dung website, bản tin nội bộ.
- **Lưu ý R5:** Mọi nội dung tiếp thị được tự động kiểm duyệt pháp lý (Luật Quảng cáo 2012, NĐ 181, NĐ 38, TT 06/2011/TT-BYT) qua `claim_guard` — triệt tiêu các từ ngữ over-claim như "số 1", "an toàn tuyệt đối", "trị dứt điểm".
- **Cách ra lệnh (Prompt mẫu):**
  > *"Viết bài blog SEO 1500 từ về chủ đề chăm sóc sức khỏe mùa lạnh, tối ưu từ khóa chính, giọng văn chuyên nghiệp nhưng gần gũi"*  
  > *"Viết 5 caption Facebook cho sản phẩm mới, tone vui tươi, có call-to-action rõ ràng"*
- **Thành phẩm:** Bài viết hoàn chỉnh định dạng Markdown hoặc Word tại `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="39-thiet-ke" name="39-thiet-ke"></a>3.9 Thiết Kế Đồ Họa

- **Khi nào nên dùng:** Thiết kế ấn phẩm in ấn tiếp thị: Leaflet, Brochure gấp 2 / gấp 3, Poster A3, Tờ rơi, Slide trình chiếu dạng PDF sẵn sàng gửi xưởng in.
- **Chuẩn in ấn chuyên nghiệp:**
  - Tự động thiết lập vùng xén lề bleed 3mm, khung TrimBox/BleedBox chuẩn kỹ thuật in.
  - Tự động tạo dấu cắt (crop marks), nhúng sẵn font tiếng Việt chuẩn đẹp, bảo đảm độ phân giải ảnh $\ge 300\text{ ppi}$.
  - Chạy bộ kiểm tra tiền in (Preflight) và soát ảnh xem trước trước khi bàn giao.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Thiết kế brochure A4 gấp 3 giới thiệu dịch vụ doanh nghiệp từ nội dung này: `/duong_dan/noi_dung.md`"*  
  > *"Thiết kế poster A3 thông báo chương trình hội thảo sẵn sàng gửi nhà in"*
- **Thành phẩm:** File PDF in ấn chuẩn kèm ảnh xem trước từng trang tại `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="310-tao-landing-page" name="310-tao-landing-page"></a>3.10 Tạo Landing Page

- **Khi nào nên dùng:** Chuyển đổi bản thiết kế từ Figma, Google Stitch, ảnh mockup hoặc brief nội dung thành trang đích web (Landing Page) hoàn chỉnh bằng React + Vite + TypeScript + Tailwind CSS.
- **Tích hợp Landing Hub:**
  - Tách rời dữ liệu nội dung (`content.json`) khỏi mã nguồn, dễ dàng cập nhật câu chữ mà không cần sửa code.
  - Sử dụng hệ thống token màu sắc và font chữ đồng bộ nhận diện thương hiệu.
  - Tích hợp chuẩn form lead/order với Landing Hub SDK, kiểm thử tự động trên 3 khung nhìn (Mobile 375px, Tablet 768px, Desktop 1440px).
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tạo landing page bán sản phẩm chăm sóc tóc từ thiết kế Figma này: [link]"*  
  > *"Chuyển bản vẽ mockup ảnh này thành trang landing page React production-ready"*
- **Thành phẩm:** Mã nguồn trang đích hoàn chỉnh tại `~/Downloads/AIWF_Output/landing-pages/<project_id>/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="311-app-auditor" name="311-app-auditor"></a>3.11 Kiểm Định Ứng Dụng

- **Khi nào nên dùng:** Kiểm định toàn diện chất lượng giao diện và trải nghiệm web app hoặc landing page đang chạy (trên localhost hoặc URL công khai); re-test kiểm chứng sau khi sửa bug.
- **Năng lực kiểm định toàn diện:**
  - Quét visual sweep trên 4 khung nhìn màn hình: Mobile (375px), Tablet (768px), Laptop (1280px), Desktop (1440px).
  - Tự động phát hiện lỗi tràn ngang màn hình, hình ảnh hỏng, lỗi console và network failure.
  - Kiểm tra chuẩn trợ năng WCAG A/AA bằng axe-core offline, phân loại lỗi từ P0 đến P4 kèm ảnh chụp bằng chứng thực tế.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Kiểm định toàn diện ứng dụng web đang chạy tại http://localhost:3000"*  
  > *"Chạy audit kiểm thử giao diện và lỗi console cho trang landing page này"*
- **Thành phẩm:** Báo cáo audit chi tiết (kèm danh sách bug và ảnh chụp bằng chứng) tại `~/Downloads/AIWF_Output/app-auditor/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="312-video-studio" name="312-video-studio"></a>3.12 Studio Video

- **Khi nào nên dùng:** Khi cần tạo video giới thiệu sản phẩm, video giáo dục, video tin tức, reel truyền thông xã hội — hoàn toàn tự động không cần phần mềm edit video phức tạp.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tạo video giới thiệu về cuộc sống tại Nhật Bản, thuyết minh tiếng Việt, có nhạc nền và phụ đề song ngữ Việt–Nhật"*
- **2 chế độ sử dụng:**
  - **Chế độ Chat (đơn giản nhất):** Gõ yêu cầu trực tiếp trong chat, AI sẽ tự chạy pipeline khép kín.
  - **Chế độ CLI:**
    ```bash
    source .venv-tts/bin/activate
    # Free Tier — HD 1080p
    python3 .agents/skills/video-studio/scripts/video_pipeline.py \
      --topic "Chủ đề video của bạn" --tier free --lang vi
    # Premium Tier — 4K UHD
    python3 .agents/skills/video-studio/scripts/video_pipeline.py \
      --topic "Chủ đề video của bạn" --tier premium --lang vi \
      --output ~/Downloads/AIWF_Output/ten_video.mp4
    ```
  - **Chế độ Web Studio** (giao diện đồ họa):
    ```bash
    python3 .agents/skills/video-studio/scripts/video_studio_server.py --port 8800
    # Mở trình duyệt tại: http://localhost:8800
    ```
- **Pipeline tự động (7 bước):**
  1. AI viết kịch bản từ chủ đề bạn cung cấp.
  2. Thuyết minh TTS offline (VieNeu-TTS cho tiếng Việt, Kokoro cho tiếng Anh/Nhật).
  3. Tìm và tải video stock từ Pexels/Pixabay (Free: HD, Premium: 4K UHD).
  4. Tìm nhạc nền phù hợp tâm trạng kịch bản, tự động ducking sidechain.
  5. Render phụ đề karaoke song ngữ (chữ chạy từng ký tự).
  6. Ghép nối timeline hoàn chỉnh bằng FFmpeg.
  7. Xuất file `.mp4` vào `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="313-phu-de" name="313-phu-de"></a>3.13 Tạo Phụ Đề

- **Khi nào nên dùng:** Khi bạn có video (tiếng Việt, tiếng Nhật, tiếng Anh) cần tạo phụ đề để đăng mạng xã hội, hoặc cần dịch phụ đề sang ngôn ngữ khác, gắn phụ đề cứng vào video.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tạo phụ đề tiếng Việt cho video này và gắn phụ đề cứng vào video: `/duong_dan/video.mp4`"*  
  > *"Dịch file phụ đề SRT này từ tiếng Nhật sang tiếng Việt và xuất file ASS"*
- **Thành phẩm:** File phụ đề rời `.srt` / `.ass` hoặc video MP4 đã gắn phụ đề cứng (hardsub), sẵn sàng chia sẻ.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="314-long-tieng" name="314-long-tieng"></a>3.14 Lồng Tiếng Video

- **Khi nào nên dùng:** Thuyết minh, lồng tiếng cho video clip có sẵn từ kịch bản hoặc file phụ đề; ghép giọng đọc AI chuẩn phòng thu vào video và tự động hòa âm hạ nhạc nền (Smart Ducking).
- **Phòng dựng Studio UI:**
  - Tích hợp phòng dựng đồ họa tương tác (port 8780+) nghe thử giọng đọc tức thì với kho giọng 48 kHz đa vùng miền.
  - Live Subtitle Overlay hiển thị phụ đề trực tiếp trên màn hình video.
  - Hỗ trợ công cụ chia đoạn câu khớp hoàn hảo với nhịp nói nhân vật và xuất video MP4 chất lượng cao.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Lồng tiếng thuyết minh tiếng Việt cho đoạn video này từ kịch bản có sẵn, tự động hạ nhỏ âm lượng video gốc khi có giọng đọc: `/duong_dan/clip.mp4`"*
- **Thành phẩm:** Video `.mp4` hoàn chỉnh đã lồng tiếng khớp nhịp tại `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="315-hand-drawn-animation" name="315-hand-drawn-animation"></a>3.15 Tạo Hoạt Hình

- **Khi nào nên dùng:** Sáng tạo phim hoạt hình vẽ tay Canvas 2D ngắn, video hoạt họa nghệ thuật, minh họa đồ họa chuyển động cho chiến dịch truyền thông hoặc giải thích khái niệm.
- **5 phong cách nghệ thuật:**
  - Nét mực truyền thống (`ink`), in lưới Riso (`riso`), chất liệu màn chiếu (`screen`), chì phác thảo tối giản (`pencil`), vẽ phấn màu pastel (`doodle`).
  - Hỗ trợ kỹ thuật rotoscope, hoạt hình cát (sand) và hiệu ứng pop-up paper 3D.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tạo một đoạn hoạt hình vẽ tay phong cách chì kể về câu chuyện hạt mầm vươn lên thành cây lớn"*  
  > *"Làm animation 2D ngắn minh họa dòng chảy ý tưởng bằng phong cách ink"*
- **Thành phẩm:** Trình phát HTML player tương tác và file video MP4 độ phân giải cao tại `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="316-chotto-newsroom" name="316-chotto-newsroom"></a>3.16 Biên Tập Tin Chotto

- **Khi nào nên dùng:** Biên tập, tổng hợp và thẩm định tin tức chính sách, đời sống, thủ tục hành chính, cư trú và việc làm tại Nhật Bản dành cho cộng đồng người Việt (chottoday.com).
- **Cơ chế Fact Pack & Thẩm định nguồn:**
  - Quét và xác thực thông tin từ các cổng thông tin chính phủ Nhật Bản có tên miền `.go.jp`, đối chiếu văn bản gốc.
  - Tạo ảnh minh họa chuẩn tòa soạn và xuất gói duyệt tin tức hoàn chỉnh cho biên tập viên.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Biên tập bản tin về quy định mới về visa kỹ năng đặc định Nhật Bản từ thông báo mới nhất của Bộ Tư pháp Nhật"*  
  > *"Quét tin tức chính sách Nhật Bản hôm nay và lập gói duyệt tin"*
- **Thành phẩm:** Bản tin chuẩn cấu trúc ChottoDay kèm ảnh minh họa và bảng Fact Pack tại `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="317-doc-sau" name="317-doc-sau"></a>3.17 Đọc Sâu

- **Khi nào nên dùng:** Đọc hiểu và phân tích chuyên sâu các bài viết dài, sách, kỷ yếu nghiên cứu, báo cáo thị trường phức tạp bằng các mô hình tư duy kinh điển (SCQA, 5W2H, Tư duy phản biện, Tư duy đảo ngược, Nguyên lý đệ nhất, Tư duy hệ thống, 6 chiếc nón tư duy).
- **Bằng chứng nguyên văn & Quick Win:**
  - Đọc tuần tự từng phần theo bảng độ phủ, đối chiếu trích dẫn nguyên văn qua Evidence Verifier.
  - Phát hiện ngụy biện và lỗ hổng lập luận, chuyển hóa tri thức thành Kế hoạch hành động 24 giờ.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Đọc sâu và mổ xẻ cấu trúc bài viết này bằng mô hình SCQA và tư duy phản biện: `/duong_dan/tai_lieu.pdf`"*  
  > *"Phân tích chuyên sâu cuốn sách này, tìm ra các rủi ro tiềm ẩn và đề xuất kế hoạch thực thi 24h"*
- **Thành phẩm:** Báo cáo phân tích chuyên sâu `<Tên_Tài_Liệu>_Doc_Sau.md` (kèm Executive Summary và Kế hoạch 24h) tại `~/Downloads/AIWF_Output/`.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

### <a id="318-tu-van-phap-luat-nhat-ban" name="318-tu-van-phap-luat-nhat-ban"></a>3.18 Tư Vấn Pháp Luật Nhật Bản

- **Khi nào nên dùng:** Nghiên cứu và tư vấn sơ bộ các tình huống pháp lý có yếu tố Nhật Bản (hợp đồng kinh doanh, thành lập doanh nghiệp, lao động, cư trú, thuế, sở hữu trí tuệ, tranh chấp thương mại); chuyên sâu xuất nhập khẩu hàng hóa sang Nhật Bản, tra cứu mã HS hải quan Nhật, thuế quan, ưu đãi thuế EPA/FTA (VJEPA, CPTPP, RCEP), điều kiện lưu hành thực phẩm, mỹ phẩm, thiết bị điện tử, quy định ghi nhãn và quảng cáo tại Nhật.
- **Căn cứ tiếng Nhật chuẩn xác:**
  - Trích dẫn văn bản luật chính thức từ e-Gov Nhật Bản, biểu thuế Hải quan Nhật (Customs Tariff Schedule) và đối chiếu thông tư các bộ ngành Nhật (MHLW, METI, MAFF).
  - Tự động lập bảng tính thuế ước tính theo từng kịch bản hiệp định thương mại.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tư vấn điều kiện nhập khẩu và lưu hành sản phẩm mỹ phẩm từ Việt Nam sang Nhật Bản, tra cứu mã HS và thuế suất theo VJEPA"*  
  > *"Rà soát các rủi ro pháp lý theo luật lao động Nhật Bản trong trường hợp hợp đồng phái cử này"*
- **Thành phẩm:** Báo cáo pháp lý chuyên sâu bằng tiếng Việt kèm căn cứ điều luật tiếng Nhật và bảng tính thuế ước tính tại `~/Downloads/AIWF_Output/`.

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
     - **Văn bản & Dịch thuật:** Bóc Tách PDF, EJV Translate, Dịch Thuật, Xử Lý Văn Phòng, Đọc Sâu
     - **Pháp lý & Tài chính:** Tư Vấn Pháp Luật, Tư Vấn Pháp Luật Nhật Bản, Báo Cáo Kế Toán, Tư Vấn Thuế
     - **Nội dung & Sáng tạo:** Viết Bài Đa Kênh, Thiết Kế Đồ Họa, Tạo Landing Page, Kiểm Định Ứng Dụng, Biên Tập Tin Chotto
     - **Media & Hoạt hình:** Studio Video, Tạo Phụ Đề, Lồng Tiếng Video, Tạo Hoạt Hình
3. **Xem Dashboard tổng quan:**
   - Mở file `dashboard/index.html` trên trình duyệt để xem bản đồ trực quan toàn bộ kỹ năng và danh mục tài liệu.

[⬆ Về đầu trang / Mục lục](#muc-luc)

---

## <a id="5-kho-tri-thuc" name="5-kho-tri-thuc"></a>5. Khai Thác Kho Tri Thức và Đồng Bộ NotebookLM

AIWF đã tích hợp sẵn kho tri thức với hơn **750 tài liệu chuyên sâu** nằm trong thư mục `.agents/knowledge/`. Toàn bộ dữ liệu này có thể tra cứu ngay lập tức mà không cần kết nối mạng.

### Khi bạn muốn kéo thêm tài liệu mới từ tài khoản Google NotebookLM cá nhân:

Chỉ cần thực hiện 2 bước đơn giản qua Terminal:

1. **Đăng nhập Google NotebookLM (Chỉ cần thực hiện 1 lần):**
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
File gốc / Đề bài       →    Thư mục tạm _process/     →    Xuất file ra ~/Downloads/AIWF_Output/
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

### ❓ "Kỹ năng Studio Video báo lỗi thiếu thư viện?"
- **Cách xử lý:** Chạy lệnh kích hoạt virtual environment trước:
  ```bash
  source .venv-tts/bin/activate
  pip install -r .agents/skills/video-studio/requirements.txt
  ```

### ❓ "Dữ liệu của tôi có bị gửi ra bên ngoài không?"
- **Trả lời:** Tuyệt đối không. AIWF chạy 100% cục bộ trên mô hình LLM tích hợp sẵn của Antigravity IDE, không gọi bất kỳ REST API bên thứ ba nào (ngoại trừ Pexels/Pixabay khi dùng Studio Video để tải stock footage), không phát sinh chi phí token bên ngoài.

### ❓ "Làm sao để xem danh sách đầy đủ 18 skills?"
- Xem [Bản Đồ 18 Kỹ Năng](#2-ban-do-18-ky-nang) ở mục 2, hoặc gõ trong chat: *"Liệt kê tất cả skills AIWF hiện có"*.

---

[⬆ Về đầu trang / Mục lục](#muc-luc)

*AI Workforce Handbook v2.1 — Cập nhật 2026-10-03 — 18 skills đầy đủ, chuẩn hoá giao diện và tên gọi.*
