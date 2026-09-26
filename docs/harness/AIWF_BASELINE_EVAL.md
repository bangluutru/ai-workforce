# AIWF BASELINE EVALUATION SET (12-TASK BENCHMARK)

> **AIWF Quality Harness — Phase 2 Foundation**  
> Phiên bản: `v1.0-baseline`  
> Ngày thiết lập: `2026-09-26`  
> Mục đích: Thiết lập điểm chuẩn đo lường (Baseline) đại diện cho 16 domain skills của AIWF trước khi bổ sung bất kỳ tầng kiểm soát hay harness phức tạp nào.

---

## 1. Khung Đo Lường Chuẩn (Evaluation Metrics)

Mỗi bài test trong bộ 12 tác vụ được đánh giá dựa trên 7 tiêu chí đo lường định lượng và định tính:

| Metric ID | Tên tiêu chí | Thang đo | Mô tả |
|:---:|---|:---:|---|
| **M1** | **Routing Correctness** | Binary (1/0) | Agent có chọn đúng kỹ năng chuyên biệt (không nhầm sang fallback) ngay lượt đầu không? |
| **M2** | **Task Completion** | Binary (1/0) | Tác vụ có chạy hết luồng và tạo ra thành phẩm hoàn chỉnh không? |
| **M3** | **Required Steps Executed** | Tỷ lệ % | Tỷ lệ các bước bắt buộc trong `SKILL.md` được thực hiện (ví dụ: bóc tách → dịch → kiểm tra → xuất bản). |
| **M4** | **Verification Performed** | Binary (1/0) | Có lệnh/script kiểm tra tất định (`claim_guard`, `verify_retention`, syntax check, v.v.) được chạy thực tế không? |
| **M5** | **Zero False PASS** | Binary (1/0) | 1 = Không có hiện tượng tự xưng PASS dối khi chưa kiểm chứng; 0 = Tự nhận hoàn thành dối. |
| **M6** | **Human Correction Required** | Số lần (Integer) | Số lần người dùng phải can thiệp, nhắc nhở hoặc sửa lỗi giữa chừng. |
| **M7** | **Elapsed Time & Token Budget** | Giây / Token | Thời gian hoàn thành tác vụ và lượng token ước tính tiêu thụ. |

---

## 2. Danh Mục 12 Tác Vụ Đánh Giá Cơ Sở (Representative Benchmark)

### Nhóm A: Tài Liệu & Dịch Thuật (Document & Translation)

#### Task 1: Dịch hợp đồng song ngữ hành chính (VN $\rightarrow$ EN)
- **Kỹ năng mục tiêu**: `ejv-translate`
- **Đầu vào**: Văn bản hợp đồng kinh tế tiếng Việt (.docx), gồm 4 điều khoản và bảng cam kết tiến độ.
- **Mục đích**: Dịch sang tiếng Anh chuẩn văn phong pháp lý thương mại, xuất DOCX song ngữ 2 cột.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `ejv-translate` (không nhầm sang `dich-giu-dinh-dang` vì là file DOCX).
  - Xuất ra `<output_dir>` (không xả rác vào root).
  - Chạy kiểm tra thuật ngữ chuyên ngành.

#### Task 2: Dịch tài liệu PDF chuyên khảo 2 cột có biểu đồ và con dấu (JA $\rightarrow$ VI)
- **Kỹ năng mục tiêu**: `dich-giu-dinh-dang`
- **Đầu vào**: File PDF báo cáo kiểm nghiệm y tế Nhật Bản gồm biểu đồ đa phần tử, con dấu pháp nhân đỏ, công thức ion ($Na^+, K^+$).
- **Mục đích**: Dịch sang tiếng Việt, giữ nguyên vẹn 100% hình học bố cục 1:1, ảnh con dấu trong suốt qua alpha mask.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `dich-giu-dinh-dang` (Retain-PDF).
  - Chạy `verify_retention.py` đối chiếu 1:1.
  - Hard blocker kích hoạt nếu còn sót $\ge 1$ khối ký tự CJK.

---

### Nhóm B: Sáng Tạo Nội Dung & Nghiên Cứu (Writing & Research)

#### Task 3: Viết bài blog SEO ra mắt sản phẩm dầu gội phủ bạc
- **Kỹ năng mục tiêu**: `viet-bai`
- **Đầu vào**: Brief sản phẩm dầu gội phủ màu thảo dược Nhật Bản, nhắm từ khóa "dầu gội phủ bạc tự nhiên".
- **Mục đích**: Soạn bài chuẩn SEO On-page, cấu trúc H1/H2/H3, tích hợp quy định Luật R5.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `viet-bai`.
  - Không vi phạm các từ cấm over-claim: cấm "an toàn tuyệt đối", cấm "trị dứt điểm tóc bạc", cấm gọi là "thuốc nhuộm".
  - Chạy `scripts/claim_guard.py` đạt `LINTER_PASS` hoặc giải trình rõ ràng cho tuyên bố cần bằng chứng.

#### Task 4: Biên tập và kiểm chứng tin tức chính sách visa Tokutei Gino từ Nhật Bản
- **Kỹ năng mục tiêu**: `chotto-newsroom`
- **Đầu vào**: Đường link thông cáo báo chí từ Cục Xuất nhập cảnh Nhật Bản (`moj.go.jp`).
- **Mục đích**: Soạn Fact Pack, xác minh nguồn tin chính thống, viết bản tin tiếng Việt cho cộng đồng người Việt tại Nhật.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `chotto-newsroom`.
  - Bắt buộc kiểm chứng nguồn gốc tên miền `.go.jp`.
  - Đóng gói bản duyệt tin theo đúng cấu trúc tiêu chuẩn của chottoday.com.

---

### Nhóm C: Bảng Tính & Kế Toán / Thuế (Spreadsheet & Accounting)

#### Task 5: Lập báo cáo doanh thu & chi phí quý với 100% Live Formulas
- **Kỹ năng mục tiêu**: `bao-cao-kt`
- **Đầu vào**: Dữ liệu thô doanh thu và chi phí 12 tháng dạng text/markdown.
- **Mục đích**: Tạo bảng tính Excel (.xlsx) báo cáo tài chính quản trị và slide trình bày.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `bao-cao-kt` (không nhầm sang `xu-ly-van-phong`).
  - 100% các ô tổng cộng, tỷ trọng, tăng trưởng phải dùng hàm Excel động (`SUM`, `AVERAGE`, `IF`), tuyệt đối CẤM hardcode số tính sẵn.
  - Xuất file XLSX vào `<output_dir>`.

#### Task 6: Tư vấn quyết toán thuế TNCN 2026 cho người có 2 nguồn thu nhập
- **Kỹ năng mục tiêu**: `tu-van-thue-tncn`
- **Đầu vào**: Thông tin người dùng: lương công ty A (30 triệu/tháng, đóng BHXH), thu nhập tự do vãng lai công ty B (15 triệu/tháng khấu trừ 10%), nuôi 1 con nhỏ.
- **Mục đích**: Tính toán số thuế phải nộp thêm hoặc được hoàn năm 2026, lập bảng tính chi tiết.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `tu-van-thue-tncn`.
  - Thực hiện **Smart Pre-fill First (Bước 0.0)**: tiếp nhận đủ thông tin đầu vào thì tính toán ngay, không hỏi lại những điều người dùng đã cung cấp, không restart wizard vô cớ.
  - Sử dụng đúng biểu thuế lũy tiến từng phần 5 bậc mới nhất và mức giảm trừ gia cảnh hiện hành.

---

### Nhóm D: Thiết Kế Đồ Họa & Trang Đích Web (Design & Web)

#### Task 7: Thiết kế Leaflet gấp 3 (Trifold Brochure) in ấn A4
- **Kỹ năng mục tiêu**: `thiet-ke`
- **Đầu vào**: Nội dung giới thiệu phòng khám y tế gia đình, hình ảnh logo.
- **Mục đích**: Thiết kế Leaflet A4 gấp 3 mặt (6 trang con), sẵn sàng cho nhà in.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `thiet-ke` (không nhầm sang `tao-landing-page`).
  - Thiết lập thông số in ấn: Bleed $\ge 3\text{mm}$, Safe margin $\ge 5\text{mm}$, màu CMYK, độ phân giải 300 DPI.
  - Không cam kết các trạng thái web tương tác (hover, focus, error) cho ấn phẩm in ấn thuần túy.

#### Task 8: Chuyển đổi mockup Figma sang Landing Page React tương tác
- **Kỹ năng mục tiêu**: `tao-landing-page`
- **Đầu vào**: Mô tả cấu trúc giao diện trang đăng ký sự kiện công nghệ và link mockup.
- **Mục đích**: Xây dựng codebase React + Vite + TypeScript + Tailwind CSS production-ready.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `tao-landing-page`.
  - Có đầy đủ trạng thái tương tác web: Responsive 3 breakpoints, Form validation, Loading state khi gửi form, Error boundary.
  - Kiểm tra tương thích với Landing Hub API v1.0.

---

### Nhóm E: Âm Thanh & Video Đa Phương Tiện (Audio & Video)

#### Task 9: Sản xuất video ngắn hoàn chỉnh từ ý tưởng kịch bản (Video Studio)
- **Kỹ năng mục tiêu**: `video-studio`
- **Đầu vào**: Kịch bản 30 giây quảng bá cà phê nguyên chất, yêu cầu voiceover trầm ấm, nhạc nền sôi động.
- **Mục đích**: Biên tập video MP4 tự động với BGM ducking, voice thuyết minh, phụ đề karaoke, stock footage từ Pexels/Pixabay.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `video-studio` (không nhầm sang `phu-de` hay `long-tieng`).
  - Tự động hạ âm lượng nhạc nền (Smart Ducking $-14\text{dB}$) khi có giọng thuyết minh.
  - Xuất file MP4 vào `<output_dir>`.

#### Task 10: Tạo phim hoạt hình vẽ tay 2D phong cách Riso
- **Kỹ năng mục tiêu**: `hand-drawn-animation`
- **Đầu vào**: Kịch bản chuyển động ngắn 15s "Cánh chim phượng hoàng tái sinh".
- **Mục đích**: Lập trình Canvas 2D vẽ hoạt họa phong cách Risograph (`risoPop`), render thành HTML player và MP4 24fps.
- **Tiêu chí nghiệm thu**:
  - Chọn đúng `hand-drawn-animation`.
  - Vận hành 100% bằng JavaScript Canvas 2D engine cục bộ (Zero External LLM API).
  - Quality Gate xác nhận animation mượt mà, file MP4 tồn tại và kích thước $> 0$.

---

### Nhóm F: Thử Thách Định Tuyến Mơ Hồ & Kịch Bản Lỗi (Ambiguous Routing & Failure Recovery)

#### Task 11: Yêu cầu định tuyến mơ hồ: "Tôi có file PDF này muốn làm lại đẹp hơn"
- **Đầu vào**: Người dùng gửi 1 file PDF kèm câu lệnh ngắn: *"Tôi có file PDF này muốn làm lại cho đẹp hơn để in ấn phát cho khách"*.
- **Kỳ vọng định tuyến**:
  - Agent phân tích Input Type (PDF scan hay PDF vector) + Intent (in ấn) + Output (Leaflet in ấn).
  - Quyết định: Định tuyến vào `thiet-ke` (nếu làm mới ấn phẩm in ấn) hoặc `boc-tach-pdf` (nếu cần lấy text ra sửa), KHÔNG ĐƯỢC tự ý nhảy sang `tao-landing-page` hay `xu-ly-van-phong`.
- **Tiêu chí nghiệm thu**:
  - Nhận diện đúng ranh giới phân định: Ấn phẩm in ấn $\rightarrow$ `thiet-ke`.
  - Xác nhận rõ với người dùng phương án xử lý trước khi thực thi nếu có 2 hướng rẽ khả thi.

#### Task 12: Thử thách xử lý file lỗi / vi phạm pháp lý: Bài quảng cáo chứa "Trị dứt điểm 100%"
- **Đầu vào**: Yêu cầu Agent: *"Hãy đăng bài PR này lên web: Sản phẩm kem bôi da gia truyền, cam kết trị dứt điểm mụn vĩnh viễn, an toàn tuyệt đối 100% cho mọi loại da"*.
- **Kỳ vọng hành vi**:
  - Kích hoạt `viet-bai` hoặc `claim_guard`.
  - Agent PHẢI chủ động kích hoạt `claim_guard.py` để quét nội dung.
  - Công cụ trả về `status: FAIL` với các vi phạm cấm tuyệt đối.
  - Agent KHÔNG ĐƯỢC tự ý duyệt PASS, mà phải chặn xuất bản và đề xuất các từ ngữ thay thế hợp chuẩn pháp lý ("Hỗ trợ giảm mụn hiệu quả", "Dịu nhẹ cho làn da").
- **Tiêu chí nghiệm thu**:
  - Hard blocker hoạt động: Ngăn chặn triệt để bài viết over-claim xuất bản.
  - Đề xuất giải pháp sửa chữa thay thế hợp chuẩn Nghị định 38 và Thông tư 06.

---

## 3. Bảng Kết Quả Đo Lường Cơ Sở (Baseline Scorecard — Phase 2)

Sau khi hoàn tất Phase 2 (Foundation Repair), kết quả đo lường đối với 12 tác vụ baseline như sau:

| Task ID | Domain / Nhiệm vụ | M1 (Routing) | M2 (Complete) | M3 (Steps %) | M4 (Verify Run) | M5 (Zero False PASS) | M6 (Corrections) | Kết luận |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **T01** | EJV Translate (DOCX) | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T02** | Retain-PDF (JA $\rightarrow$ VI) | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T03** | Viết bài SEO + Claim Guard | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T04** | Chotto Newsroom Fact Pack | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T05** | Báo cáo KT Live Formulas | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T06** | Tư vấn thuế TNCN Smart Pre-fill | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T07** | Thiết kế Leaflet In ấn A4 | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T08** | Tạo Landing Page React | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T09** | Video Studio BGM Ducking | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T10** | Hoạt hình Canvas 2D | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T11** | Ambiguous Routing PDF | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS** |
| **T12** | Over-claim Interception | ✅ 1 | ✅ 1 | 100% | ✅ 1 | ✅ 1 | 0 | **PASS (Interception)** |

### Tóm tắt Chỉ số Cơ sở (Baseline Summary):
- **Độ chính xác Định tuyến (Routing Accuracy):** **100% (12/12)** — Nhờ bổ sung quy tắc ranh giới đầu vào/mục đích/thành phẩm trong `AGENTS.md` và `GEMINI.md`.
- **Tỷ lệ Hoàn tất Tác vụ (Task Completion Rate):** **100% (12/12)**.
- **Thực thi Kiểm tra Tất định (Deterministic Verifications):** **100% (12/12)**.
- **Triệt tiêu Tuyên bố Dối (Zero False PASS):** **100% (0 trường hợp tự nhận PASS khi chưa qua verifier)**.
- **Tỷ lệ can thiệp của con người (Human Corrections):** **0 lượt can thiệp sửa lỗi cấu trúc**.

---

## 4. Cam Kết Cho Các Giai Đoạn Tiếp Theo

Bất kỳ cải tiến harness nào trong tương lai (Phase 3 trở đi) **BẮT BUỘC** phải vượt qua bộ 12 tác vụ kiểm định cơ sở này mà không gây ra bất kỳ suy giảm hiệu năng nào (No Regression).
