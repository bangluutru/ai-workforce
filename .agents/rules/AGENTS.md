---
trigger: always_on
description: "Bản đồ tổ chức tổng. Bắt buộc nạp đầu tiên để định vị môi trường làm việc."
---

# BẢN ĐỒ TỔ CHỨC AI WORKFORCE

> Sơ đồ phòng ban và luật lệ tối cao cho hệ thống tác nhân số. Bất kỳ tác nhân nào được khởi tạo cũng phải đọc file này đầu tiên để định vị không gian làm việc.

---

## 1. 🔴 NGUYÊN TẮC TỐI CAO: MỌI THAY ĐỔI PHẢI ĐỒNG BỘ ĐƯỢC QUA GIT
> **BẤT DI BẤT DỊCH — ƯU TIÊN SỐ 0.**
> Chi tiết: xem `.agents/rules/R0-git-sync-mandatory.md`

AIWF được thiết kế để hoạt động đồng nhất trên mọi máy qua Git. **TRƯỚC KHI** thực hiện bất kỳ thay đổi nào, Agent PHẢI tự hỏi:
1. Thay đổi này nằm trong workspace hay ngoài workspace?
2. Sau `git pull` trên máy khác, thay đổi có tự kích hoạt không?
3. File nào cần `git add/commit`?

**Nếu thay đổi KHÔNG thể đồng bộ qua Git → DỪNG LẠI, tìm giải pháp trước khi tiếp tục.**

> *"Nếu `git pull` trên máy mới không tái tạo được 100% hệ thống → thay đổi đó SAI."*

---

## 2. KHUNG KIẾN TRÚC KWSR TỔNG THỂ
Workspace này được quy hoạch theo nguyên tắc "Company in a Folder" của KWSR:
- **[K] Knowledge**: `.agents/knowledge/` - Nơi chứa Nguồn Sự Thật Duy Nhất (SSOT).
- **[W] Workflow**: `.agents/workflows/` - Nơi chứa sổ tay vận hành và luồng quy trình (Reverse I-P-O).
- **[S] Skill**: `.agents/skills/` - Kho kỹ năng, mô tả công việc (JD) của nhân sự số 5 lớp.
- **[R] Rule**: `.agents/rules/` - Sàn phòng vệ và phân quyền (bao gồm Luật R1 Git-Native bảo toàn lịch sử, không xả rác vào workspace).


---

## 3. NGUYÊN TẮC ZERO-HALLUCINATION
Tuyệt đối KHÔNG BỊA DỮ LIỆU. Bất kỳ tuyên bố nào về chính sách, bảng giá, quy trình công ty đều phải dựa trên các file `artifacts/*.md` nằm trong thư mục `.agents/knowledge/`. Nếu không tìm thấy, AI bắt buộc phải trả lời: "Tôi không có đủ dữ liệu trong kho tri thức" và xin chỉ thị từ con người.

---

## 4. GIAO THỨC BÀN GIAO KHÔNG GHI ĐÈ
- Mỗi tác nhân (skill) chỉ được phép tạo file mới hoặc đọc file của tác nhân khác.
- CẤM ghi đè trực tiếp lên file đang là thành phẩm của người khác. Mọi sửa đổi phải lưu thành file bản nháp mới hoặc append vào cuối tệp.

---

## 5. NGUYÊN TẮC ZERO EXTERNAL LLM API & PHÂN ĐỊNH DỊCH VỤ NGOÀI
Hệ thống AIWF tối ưu hóa tài nguyên và đảm bảo tính độc lập, bảo mật bằng cách phân định rõ ràng 3 loại API/dịch vụ:
1. **EXTERNAL LLM API (CẤM TUYỆT ĐỐI):**
   - TUYỆT ĐỐI KHÔNG gọi REST API bên ngoài (OpenAI API, Gemini API qua HTTP, Anthropic Claude API, v.v.) và KHÔNG yêu cầu người dùng nhập API key cho năng lực suy luận/xử lý AI.
   - Toàn bộ năng lực AI (dịch thuật, phân tích, tóm tắt, viết bài, đánh giá, kiểm thử) được thực thi bởi chính Agent LLM tích hợp sẵn trong Antigravity IDE (hoặc VS Code/Cursor).
   - Scripts Python chỉ xử lý dữ liệu thô (bóc tách file, merge bảng biểu, parse AST, xuất bản tài liệu) — KHÔNG chứa logic AI hay request tới LLM bên ngoài.
2. **PRODUCT / BUSINESS API (ĐƯỢC PHÉP THEO NGHIỆP VỤ):**
   - Cho phép kết nối các API backend/nghiệp vụ của chính sản phẩm phục vụ vận hành thực tế (ví dụ: Landing Hub API trong `tao-landing-page`, Google Sheet API nếu người dùng kết nối).
3. **MEDIA & DATA SERVICE API (TÙY CHỌN, KHÔNG LẠM DỤNG):**
   - Cho phép tích hợp các dịch vụ dữ liệu/media miễn phí khi cần thiết cho sản phẩm đầu ra (ví dụ: Pexels/Pixabay API để lấy stock video/ảnh trong `video-studio`, tra cứu Web Search SSOT).
   - TUYỆT ĐỐI KHÔNG đưa thêm dịch vụ bên ngoài mới chỉ để cho tiện nếu có thể xử lý nội bộ.

---

## 6. NGUYÊN TẮC TỰ CHẠY ĐẾN KHI HOÀN TẤT (AUTONOMOUS FULL-RUN)
- Khi được kích hoạt, mọi skill PHẢI tự chạy liên tục cho đến khi hoàn tất 100% tác vụ và trả kết quả cho người dùng.
- KHÔNG ĐƯỢC tự dừng lại giữa chừng để xin phép hoặc chờ người dùng nhắc "tiếp tục".
- Chỉ dừng lại khi: (a) gặp lỗi nghiêm trọng không thể tự phục hồi, (b) cần thông tin bổ sung từ người dùng mà không thể suy luận được, hoặc (c) đã hoàn thành 100%.

---

## 7. VỊ TRÍ SKILL DUY NHẤT — SINGLE SOURCE OF TRUTH
- Toàn bộ skill nằm tại `.agents/skills/` trong thư mục workspace `ai-workforce/`.
- Khi mở thư mục `ai-workforce` làm workspace trong Antigravity IDE, mọi skill được nạp tự động từ `.agents/skills/`.
- Git push/pull đồng bộ 100% skill giữa các máy mà không cần cấu hình thêm hay cài đặt API key.
- Không phụ thuộc vào `~/.gemini/config/skills/` (global config) — mọi thứ portable trong 1 thư mục duy nhất.

---

## 8. SKILL REGISTRY & NGUYÊN TẮC ĐỊNH TUYẾN 16 KỸ NĂNG

### A. Ma trận Định tuyến (Routing: Input Type + Intent + Output)
Định tuyến không chỉ dựa vào từ khóa, mà phải xem xét đồng thời: **Loại đầu vào (Input Type)** + **Mục đích người dùng (Intent)** + **Thành phẩm mong muốn (Expected Output)**.
Ưu tiên **kỹ năng chuyên biệt (Specialized)** thay vì kỹ năng tổng quát/dự phòng (General Fallback).

| STT | Skill Name | Display Name | Input Type | User Intent | Expected Output | Trigger Keywords |
|:---:|------------|--------------|------------|-------------|-----------------|------------------|
| 1 | **ejv-translate** | EJV Translate | Text, DOCX, MD, PDF text | Dịch thuật hành chính/kỹ thuật 3 ngôn ngữ VN-EN-JP | DOCX song ngữ, PDF in ấn | Dịch 3 ngôn ngữ, EJV Translator, dịch VN/EN/JP |
| 2 | **boc-tach-pdf** | Bóc Tách PDF | PDF scan, ảnh chụp tài liệu | OCR số hóa tài liệu giấy/scan phức tạp | DOCX có thể chỉnh sửa | OCR PDF, bóc tách scan, scan ra Word |
| 3 | **tu-van-phap-luat** | Tư Vấn Pháp Luật | Tình huống pháp lý, văn bản luật | Tra cứu điều khoản, đối chiếu quy định | Báo cáo tư vấn, thư tư vấn | Tư vấn pháp luật, tra cứu luật |
| 4 | **xu-ly-van-phong** | Xử Lý Văn Phòng | Yêu cầu hành chính, bảng tính, slide | Tạo/sửa tài liệu văn phòng chuẩn NĐ 30 | DOCX, XLSX, PPTX, PDF | Word Excel PPT PDF, chuẩn NĐ 30 |
| 5 | **viet-bai** | Viết Bài Đa Kênh | Brief tiếp thị, chủ đề, từ khóa SEO | Sáng tạo nội dung đa kênh, tuân thủ Luật R5 | Bài blog SEO, post Facebook, bài PR | Viết bài, copywriting, blog SEO, bài Facebook, nội dung web, PR |
| 6 | **thiet-ke** | Thiết Kế Đồ Họa | Brief ấn phẩm, nội dung in ấn/Leaflet | Thiết kế đồ họa in ấn (Leaflet, Brochure, Poster) | PDF in ấn CMYK/300DPI, Leaflet HTML/CSS | Thiết kế leaflet, brochure, xuất PDF in ấn |
| 7 | **bao-cao-kt** | Báo Cáo Kế Toán | Báo cáo tài chính, số liệu kế toán thô | Báo cáo tài chính/quản trị với 100% Live Formulas | XLSX/GSheet Live Formulas, Slides | Báo cáo KT, báo cáo tài chính, dashboard kinh doanh, excel, gsheet, slides |
| 8 | **phu-de** | Tạo Phụ Đề | Video file, audio file | Tạo/dịch phụ đề đơn thuần, xuất phụ đề | File SRT, ASS, video hardsub | Tạo phụ đề, làm phụ đề video, dịch phụ đề, auto subtitle, hardsub, xuất phụ đề srt ass |
| 9 | **app-auditor** | Kiểm Định Ứng Dụng | URL web, localhost web app | Kiểm thử toàn diện QA, UI, console, WCAG | Báo cáo audit, bug report có bằng chứng | Kiểm định ứng dụng, app-auditor, test ứng dụng, audit web, QA web, kiểm thử giao diện, re-test bug |
| 10 | **tu-van-thue-tncn** | Tư Vấn Thuế TNCN | Thu nhập, hoàn cảnh, chứng từ thuế | Tư vấn quyết toán thuế TNCN, tính toán biểu thuế | Bảng tính thuế XLSX, tư vấn quyết toán | Tư vấn thuế TNCN, quyết toán thuế, tính thuế thu nhập cá nhân, tra cứu thuế TNCN, eTax Mobile, giảm trừ gia cảnh, BHXH 1 lần, thuế freelancer, thuế bất động sản |
| 11 | **tao-landing-page** | Tạo Landing Page | Figma link, Google Stitch mockup, HTML/CSS | Xây dựng Landing Page tương tác tương thích Landing Hub | Code React + Vite + TS + Tailwind | Tạo landing page, Design to Landing, Stitch sang landing page, Figma sang landing page, tích hợp Landing Hub |
| 12 | **long-tieng** | Lồng Tiếng Video | Video clip, kịch bản thuyết minh | Lồng giọng đọc AI, thuyết minh video đa ngữ | Video MP4 đã khớp voiceover, audio track | Lồng tiếng video, thuyết minh video, video dubbing, lồng tiếng tự động, voiceover clip, ghép giọng vào video |
| 13 | **dich-giu-dinh-dang** | Dịch Giữ Định Dạng | PDF phức tạp (2 cột, biểu đồ, con dấu) | Dịch giữ nguyên bố cục hình học 1:1, ảnh, vector | PDF Typst/PyMuPDF song ngữ 1:1 | Dịch giữ định dạng, Retain-PDF, dịch PDF giữ nguyên bố cục và hình ảnh |
| 14 | **hand-drawn-animation** | Tạo Hoạt Hình | Ý tưởng hoạt hình, kịch bản visual | Hoạt hình vẽ tay Canvas 2D nghệ thuật | HTML Canvas Animation, MP4 hoạt hình | Hoạt hình vẽ tay, hand drawn animation, canvas animation, phim hoạt hình, rotoscope, sand animation, doodle animation |
| 15 | **chotto-newsroom** | Biên Tập Tin Chotto | Nguồn tin .go.jp, tin tức Nhật Bản | Biên tập tin tức chottoday.com, kiểm chứng Fact Pack | Bản tin chuẩn format, gói duyệt tin | Chotto Newsroom, tin tức Chotto, điểm tin Nhật Bản, biên tập tin ChottoDay, duyệt tin Nhật Bản, tin tức người Việt tại Nhật |
| 16 | **video-studio** | Tạo Video Hoàn Chỉnh | Chủ đề, kịch bản, stock clip, audio BGM | Sản xuất video hoàn chỉnh (BGM ducking, voice, sub, clip) | Video MP4 production-ready hoàn chỉnh | Tạo video, AIWF Video Studio, biên tập video, làm video marketing, video ngắn TikTok/Reels |

### B. Quy Tắc Phân Định Ranh Giới (Disambiguation Rules)
1. **`thiet-ke` vs `tao-landing-page`:**
   - Dùng `thiet-ke`: Khi cần ấn phẩm đồ họa in ấn (Leaflet gấp 2/3, Brochure, Poster, Banner, Card) hoặc xuất bản PDF có bleed/margin/300 DPI.
   - Dùng `tao-landing-page`: Khi cần trang web tương tác trên trình duyệt, mã nguồn React/Vite/Tailwind, có nút bấm, form đăng ký, tích hợp Landing Hub API.
2. **`video-studio` vs `phu-de` vs `long-tieng` vs `hand-drawn-animation`:**
   - Dùng `video-studio`: Khi cần sản xuất video trọn gói từ đầu (kịch bản + ghép stock video + lồng tiếng + BGM ducking + phụ đề karaoke).
   - Dùng `phu-de`: Khi đã có sẵn video/audio và CHỈ cần tạo/dịch phụ đề (file SRT, ASS, hoặc hardsub).
   - Dùng `long-tieng`: Khi đã có sẵn video và CHỈ cần thu/ghép voiceover thuyết minh vào video.
   - Dùng `hand-drawn-animation`: Khi muốn tạo hoạt hình vẽ tay, hiệu ứng nét vẽ nghệ thuật 2D Canvas (Rotoscope, Sand, Pop-up paper), không phải ghép stock footage đời thực.
3. **`bao-cao-kt` vs `xu-ly-van-phong`:**
   - Dùng `bao-cao-kt`: Khi tác vụ liên quan đến báo cáo tài chính, phân tích chỉ số kinh doanh chuyên sâu, yêu cầu 100% công thức động (Live Formulas) trong bảng tính, dashboard KPI.
   - Dùng `xu-ly-van-phong`: Khi soạn thảo công văn, tờ trình, quy chế, mẫu biểu hành chính văn phòng chuẩn Nghị định 30, hoặc tác vụ văn phòng tổng quát.
4. **`ejv-translate` vs `dich-giu-dinh-dang`:**
   - Dùng `dich-giu-dinh-dang`: Khi tài liệu đầu vào là PDF chuyên khảo phức tạp (bố cục 2 cột, con dấu pháp nhân, đồ thị đa phần tử) cần giữ nguyên vẹn bố cục hình học 1:1 qua Typst/Retain-PDF.
   - Dùng `ejv-translate`: Khi tài liệu là văn bản văn phòng tiêu chuẩn (DOCX, text, Markdown) hoặc văn bản dịch thuật thông thường.

---

## 9. PYTHON DEPENDENCIES — KIỂM TRA TỰ ĐỘNG
Trước khi chạy bất kỳ script nào trong `.agents/skills/*/scripts/`, Agent PHẢI:
```bash
python3 -c "import docx; import fitz; import pdfplumber" 2>/dev/null || pip3 install python-docx pymupdf pdfplumber lxml markitdown pypandoc
```

---

## 10. WORKSPACE REQUIREMENT — BẮT BUỘC
> ⚠️ Thư mục `ai-workforce/` PHẢI được mở làm workspace (File → Open Folder) trong Antigravity IDE.
> Nếu mở thư mục cha hoặc home thay vì `ai-workforce/`, Agent sẽ KHÔNG nạp được skills và rules → sẽ bị lỗi hoặc yêu cầu API key.

---

## 11. LUẬT R4 & KIỂM ĐỊNH SKILL CHUẨN MẪU (SKILL STANDARD V1.0)
- Mọi kỹ năng trong `.agents/skills/` phải tuân thủ Luật R4 (`.agents/rules/R4-skill-standard-v1.md`).
- Bắt buộc kiểm tra và cấp chứng chỉ qua công cụ `scripts/audit_skill.py`.
- Khi có skill mới hoặc sửa đổi code, hệ thống tự động kiểm duyệt đạt điểm $\ge 85/100$ và không vi phạm 5 Điều cấm tuyệt đối mới được đưa vào vận hành.

---

## 12. LUẬT R5 & KIỂM SOÁT TÍNH PHÁP LÝ NỘI DUNG (LEGAL CLAIM COMPLIANCE)
- Mọi nội dung tiếp thị, bài viết, trang đích, tư vấn pháp lý và báo cáo kinh doanh phải tuân thủ nghiêm ngặt Luật R5 (`.agents/rules/R5-legal-claim-compliance.md`).
- Tuyệt đối cấm các phát ngôn over-claim vi phạm Luật Quảng cáo 2012, NĐ 181/2013/NĐ-CP, NĐ 38/2021/NĐ-CP và Thông tư 06/2011/TT-BYT: *"an toàn tuyệt đối"*, *"100% không kích ứng"*, *"đặc trị"*, *"trị dứt điểm"*, *"số một"*, *"duy nhất"* (khi thiếu căn cứ chứng minh).
- Mọi tài liệu xuất bản phải được quét tự động qua công cụ `scripts/claim_guard.py` đạt chuẩn trước khi bàn giao.

---

## 13. LUẬT R6 & TIÊU CHUẨN BẢO TOÀN BỐ CỤC, ĐỒ HỌA & NỘI DUNG CHUYÊN NGÀNH (RETAIN-PDF STANDARD)
- Mọi tài liệu PDF phức tạp (chuyên khảo 2 cột, đồ thị đa phần tử, con dấu pháp nhân, chứng chỉ khung hoa văn) phải tuân thủ Luật R6 (`.agents/rules/R6-document-layout-preservation.md`).
- Bắt buộc tuân thủ 7 Trụ cột Retain-PDF:
  1. **Mặt nạ mềm SMask trong suốt**: Sử dụng `scripts/pdf_asset_extractor.py` giải mã kênh alpha mặt nạ mềm, triệt tiêu lỗi bôi đen nền con dấu/chữ ký.
  2. **Trích xuất toàn vẹn biểu đồ đa phần tử**: Bounding box bao trọn cả hàng đồ thị $\bar{X}$ và $R$, các đường giới hạn UCL/LCL và thước đo trục hoành.
  3. **Cô lập khung viền & lề an toàn**: Tách sạch nội dung lõi của bằng khen/chứng chỉ, thiết lập Safe Zone Margins (top $\ge 105\text{pt}$, bottom $\ge 90\text{pt}$, x $\ge 75\text{pt}$) chống đè viền hoa văn.
  4. **Cân bằng bố cục đa cột & ngân sách chữ**: Bù trừ độ giãn nở tiếng Việt (+25-35%), cân đối đáy 2 cột qua dãn dòng và `#colbreak()`, tự động gộp bounding box đoạn văn triệt tiêu đè dòng.
  5. **Cơ chế Ánh xạ Kép & Chống dịch sót (Dual-Level Mapping)**: Cung cấp ánh xạ đồng thời ở Cấp độ Đoạn Gộp (`combined_text`) và Cấp độ Khối Đơn/Từng Dòng (`single_block` / `line_text`), cấm tuyệt đối placeholder `.`.
  6. **Bước Đánh giá & Chuẩn hóa Thuật ngữ Chuyên ngành (Mandatory Domain Review)**: Khảo sát phân ngành sâu, lập Ma trận Tra cứu Thuật ngữ Chuyên ngành, cấm dịch máy thô từng chữ (word-by-word).
  7. **Cổng kiểm toán đối chiếu toàn vẹn 3 lớp (Tri-Layer Quality Gate)**: Khóa chặn cứng 3 lớp (Lớp 1: Bố cục hình học 1:1; Lớp 2: Quét sạch 100% ký tự nguồn theo Rule R3 §8; Lớp 3: Toàn vẹn nội dung 100% và chuẩn hóa thuật ngữ chuyên ngành) trước khi bàn giao.


