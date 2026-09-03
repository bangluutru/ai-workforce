# CẨM NANG HƯỚNG DẪN SỬ DỤNG AI WORKFORCE (AIWF)

> **Mục tiêu cẩm nang:** Hướng dẫn nhanh, thực chiến và dễ hiểu nhất để bất kỳ ai cũng có thể khai thác tối đa sức mạnh của AI Workforce ngay trên Antigravity IDE (hoặc VS Code).  
> **Cam kết cốt lõi:** 100% Chạy cục bộ nội bộ, Không chi phí API bên ngoài, Ưu tiên **TỐC ĐỘ** xử lý và **ĐỘ CHÍNH XÁC** của kết quả.

---

## <a id="muc-luc" name="muc-luc"></a>Mục Lục Điều Hướng Nhanh

*Nhấp vào bất kỳ mục nào dưới đây để di chuyển ngay đến nội dung tương ứng:*

1. [1. AIWF Làm Được Gì Cho Bạn?](#1-aiwf-làm-được-gì-cho-bạn)
2. [2. Hướng Dẫn Sử Dụng 4 Kỹ Năng Cốt Lõi (Step-by-Step)](#2-hướng-dẫn-sử-dụng-4-kỹ-năng-cốt-lõi-step-by-step)
   - [2.1 Bóc Tách PDF Scan và OCR Ra Word (boc-tach-pdf)](#21-bóc-tách-pdf-scan-và-ocr-ra-word-boc-tach-pdf)
   - [2.2 Dịch Thuật Đa Ngôn Ngữ Chuyên Sâu (ejv-translate)](#22-dịch-thuật-đa-ngôn-ngữ-chuyên-sâu-ejv-translate)
   - [2.3 Xử Lý Văn Phòng Chuẩn Hóa (xu-ly-van-phong)](#23-xử-lý-văn-phòng-chuẩn-hóa-xu-ly-van-phong)
   - [2.4 Tư Vấn Pháp Lý và Tra Cứu Luật (tu-van-phap-luat)](#24-tư-vấn-pháp-lý-và-tra-cứu-luật-tu-van-phap-luat)
3. [3. Sử Dụng Giao Diện AIWF Panel Trên IDE (Click Chuột 1-Chạm)](#3-sử-dụng-giao-diện-aiwf-panel-trên-ide-click-chuột-1-chạm)
4. [4. Khai Thác Kho Tri Thức 38 Notebooks và Đồng Bộ NotebookLM](#4-khai-thác-kho-tri-thức-38-notebooks-và-đồng-bộ-notebooklm)
5. [5. Cơ Chế Đảm Bảo Tốc Độ và Độ Chính Xác (Evidence Verifier)](#5-cơ-chế-đảm-bảo-tốc-độ-và-độ-chính-xác-evidence-verifier)
6. [6. Xử Lý Nhanh Sự Cố Thường Gặp (FAQ và Troubleshooting)](#6-xử-lý-nhanh-sự-cố-thường-gặp-faq-và-troubleshooting)

---

## <a id="aiwf-lam-duoc-gi-cho-ban" name="aiwf-lam-duoc-gi-cho-ban"></a>1. AIWF Làm Được Gì Cho Bạn?

AI Workforce (AIWF) là nền tảng trợ lý số chuyên môn cao, được tích hợp sẵn 4 kỹ năng nghiệp vụ thực chiến và 1 kho tri thức offline khổng lồ:

| Kỹ năng / Công cụ | Lĩnh vực chuyên trách | Thành phẩm đầu ra |
|---|---|---|
| 📄 **`boc-tach-pdf`** | Số hóa tài liệu PDF scan, tài liệu cũ mờ, trích xuất bảng biểu phức tạp. | File Word (`.docx`) giữ nguyên cấu trúc bảng và văn bản có thể chỉnh sửa. |
| 🌐 **`ejv-translate`** | Dịch thuật tài liệu 3 ngôn ngữ: Tiếng Việt, Tiếng Anh, Tiếng Nhật, Tiếng Trung (Y tế, Hợp đồng, Kỹ thuật). | File Word song ngữ/đơn ngữ, bảo toàn 100% định dạng bảng biểu và thuật ngữ chuẩn. |
| 📝 **`xu-ly-van-phong`** | Soạn thảo văn bản hành chính nhà nước, báo cáo quản trị, bảng tính và bài trình chiếu. | File Word (`.docx`) chuẩn Nghị định 30/2020/NĐ-CP; File Excel (`.xlsx`) có công thức sống; Slide (`.pptx`). |
| ⚖️ **`tu-van-phap-luat`** | Nghiên cứu pháp lý, tra cứu án lệ, giải quyết tranh chấp hợp đồng, đất đai, lao động, doanh nghiệp. | Báo cáo pháp lý 5 phần (`legal_report_*.md`) kèm bảng dẫn chiếu điều luật nguyên văn. |
| 🧠 **Smart Knowledge** | 38 Gemini Notebooks với 750+ tài liệu chuyên môn nội bộ. | Tra cứu dữ liệu gốc tức thì (offline 100%) hoặc sync thêm tài liệu mới từ Google. |

> [!TIP]
> **Vị trí lưu file thành phẩm:** Mọi file Word, Excel, Slide sau khi hoàn thành sẽ được lưu mặc định vào thư mục **`~/Downloads/`** (hoặc thư mục bạn chỉ định) để bạn mở xem ngay mà không làm bẩn thư mục làm việc của dự án.

[⬆ Về đầu trang / Mục lục](#mục-lục-điều-hướng-nhanh)

---

## <a id="huong-dan-su-dung-4-ky-nang-cot-loi" name="huong-dan-su-dung-4-ky-nang-cot-loi"></a>2. Hướng Dẫn Sử Dụng 4 Kỹ Năng Cốt Lõi (Step-by-Step)

### <a id="boc-tach-pdf" name="boc-tach-pdf"></a>2.1 Bóc Tách PDF Scan và OCR Ra Word (boc-tach-pdf)

- **Khi nào nên dùng:** Khi bạn có file PDF scan từ máy in, hợp đồng chụp ảnh, hóa đơn chứng từ hoặc tài liệu scan bị nghiêng/mờ cần chuyển thành file Word để chỉnh sửa nội dung.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Hãy dùng skill `boc-tach-pdf` để bóc tách file scan này sang file Word giúp tôi: `/duong_dan/toi_file/hop_dong_scan.pdf`"*  
  > *(Hoặc chỉ cần kéo file vào chat và gõ: "Bóc tách file PDF scan này sang Word")*
- **Quy trình tự động:**
  1. AI tự động kiểm tra xem PDF là dạng text hay dạng scan ảnh.
  2. Bóc tách từng trang, phát hiện bảng biểu (Table Detection) bằng `pdfplumber`.
  3. Ghép nối và xuất thành file Word hoàn chỉnh (`.docx`) lưu tại `~/Downloads/`.
- **Mẹo để nhanh và chính xác nhất:** Nếu tài liệu có nhiều trang và bạn chỉ cần 1 phần, hãy ghi rõ số trang: *"Chỉ bóc tách từ trang 3 đến trang 7 của file này"*.

[⬆ Về đầu trang / Mục lục](#mục-lục-điều-hướng-nhanh)

---

### <a id="ejv-translate" name="ejv-translate"></a>2.2 Dịch Thuật Đa Ngôn Ngữ Chuyên Sâu (ejv-translate)

- **Khi nào nên dùng:** Dịch tài liệu y tế (hồ sơ bệnh án, hướng dẫn thiết bị), hợp đồng kinh tế, tài liệu kỹ thuật giữa các thứ tiếng: **Việt – Anh – Nhật – Trung**.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Dịch file hợp đồng này từ tiếng Nhật sang tiếng Việt, giữ nguyên toàn bộ bảng biểu và căn lề: `/duong_dan/hop_dong_tieng_nhat.docx`"*  
  > *(Hoặc: "Dịch tài liệu y tế này sang tiếng Anh theo bảng thuật ngữ chuẩn")*
- **Quy trình tự động:**
  1. AI trích xuất nội dung và đối chiếu bộ từ điển thuật ngữ chuyên ngành có sẵn.
  2. Dịch theo từng đoạn (chunk) để không bị sót ý hoặc mất liên kết.
  3. Ráp nối lại thành file Word với tùy chọn: Bản dịch đơn ngữ hoặc Bản dịch đối chiếu song ngữ (cột song song).
- **Mẹo để nhanh và chính xác nhất:** Hãy nói rõ bạn muốn xuất bản dịch dạng song ngữ hay đơn ngữ: *"Xuất cho tôi file Word song ngữ Nhật - Việt dạng bảng 2 cột"*.

[⬆ Về đầu trang / Mục lục](#mục-lục-điều-hướng-nhanh)

---

### <a id="xu-ly-van-phong" name="xu-ly-van-phong"></a>2.3 Xử Lý Văn Phòng Chuẩn Hóa (xu-ly-van-phong)

- **Khi nào nên dùng:** Soạn thảo công văn, tờ trình, quyết định, biên bản họp chuẩn thể thức; tạo bảng tính Excel có công thức tính tự động; tạo slide thuyết trình chuyên nghiệp.
- **Cách ra lệnh (Prompt mẫu):**
  - *Soạn văn bản hành chính:*
    > *"Soạn thảo Tờ trình xin phê duyệt kế hoạch ngân sách quý 4 theo đúng chuẩn thể thức Nghị định 30/2020/NĐ-CP"*
  - *Tạo bảng tính Excel:*
    > *"Tạo bảng theo dõi doanh thu và công nợ khách hàng quý 3 bằng file Excel, có sẵn các công thức tính tổng và tỷ lệ tự động"*
  - *Tạo bài thuyết trình Slide:*
    > *"Tạo slide PowerPoint giới thiệu dự án chuyển đổi số gồm 7 trang từ dàn ý này..."*
- **Quy trình tự động:**
  - AI hỏi bạn chọn: `[1] Chuẩn công quyền NĐ 30` (đen trắng, font Times New Roman, thể thức nghiêm ngặt) hoặc `[2] Chuẩn doanh nghiệp hiện đại` (có màu sắc nhận diện thương hiệu, bố cục hiện đại).
  - Tự động chạy script sinh file `.docx`, `.xlsx` hoặc `.pptx` chuẩn chỉnh và lưu ra `~/Downloads/`.

[⬆ Về đầu trang / Mục lục](#mục-lục-điều-hướng-nhanh)

---

### <a id="tu-van-phap-luat" name="tu-van-phap-luat"></a>2.4 Tư Vấn Pháp Lý và Tra Cứu Luật (tu-van-phap-luat)

- **Khi nào nên dùng:** Khi cần tra cứu xem một hành vi/sự việc có vi phạm pháp luật hay không, tranh chấp hợp đồng kinh doanh, thủ tục đất đai, tranh chấp lao động, bảo hiểm.
- **Cách ra lệnh (Prompt mẫu):**
  > *"Tư vấn giúp tôi trường hợp công ty đơn phương chấm dứt hợp đồng lao động với nhân viên mang thai thì rủi ro pháp lý là gì và điều khoản nào quy định?"*
- **Quy trình tự động:**
  1. AI xác định 5 trục tọa độ: Lĩnh vực, Chủ thể, Hành vi, Mốc thời gian, Yêu cầu.
  2. Tra cứu đối chiếu với kho văn bản quy phạm pháp luật và án lệ.
  3. Chạy công cụ **Evidence Verifier** để đối chiếu trích dẫn nguyên văn điều luật, không đoán mò.
  4. Xuất báo cáo pháp lý đầy đủ gồm: Tóm tắt sự việc $\rightarrow$ Căn cứ pháp lý $\rightarrow$ Đánh giá rủi ro $\rightarrow$ Phương án xử lý cụ thể.

[⬆ Về đầu trang / Mục lục](#mục-lục-điều-hướng-nhanh)

---

## <a id="su-dung-giao-dien-aiwf-panel-tren-ide" name="su-dung-giao-dien-aiwf-panel-tren-ide"></a>3. Sử Dụng Giao Diện AIWF Panel Trên IDE (Click Chuột 1-Chạm)

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

[⬆ Về đầu trang / Mục lục](#mục-lục-điều-hướng-nhanh)

---

## <a id="khai-thac-kho-tri-thuc-38-notebooks" name="khai-thac-kho-tri-thuc-38-notebooks"></a>4. Khai Thác Kho Tri Thức 38 Notebooks và Đồng Bộ NotebookLM

AIWF đã tích hợp sẵn **38 Gemini Notebooks** với hơn **750 tài liệu chuyên sâu** nằm sẵn trong thư mục `.agents/knowledge/`. Toàn bộ dữ liệu này có thể tra cứu ngay lập tức mà không cần kết nối mạng.

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

[⬆ Về đầu trang / Mục lục](#mục-lục-điều-hướng-nhanh)

---

## <a id="co-che-toc-do-chinh-xac" name="co-che-toc-do-chinh-xac"></a>5. Cơ Chế Đảm Bảo Tốc Độ và Độ Chính Xác (Evidence Verifier)

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

[⬆ Về đầu trang / Mục lục](#mục-lục-điều-hướng-nhanh)

---

## <a id="faq-troubleshooting" name="faq-troubleshooting"></a>6. Xử Lý Nhanh Sự Cố Thường Gặp (FAQ và Troubleshooting)

### ❓ "AI báo không tìm thấy skill hoặc không hiểu lệnh?"
- **Cách xử lý:** Nhắn trực tiếp câu lệnh chuẩn: *"Đồng bộ quy tắc từ README.md"* hoặc chạy lệnh:
  ```bash
  bash scripts/auto-setup.sh
  ```
  Hệ thống sẽ tự động quét lại toàn bộ kỹ năng và kích hoạt môi trường trong 5 giây.

### ❓ "File Word hoặc Excel tải về mở ra có bị lỗi định dạng không?"
- **Trả lời:** Không. AIWF sử dụng bộ thư viện native của Microsoft Office (`python-docx`, `openpyxl`) và bộ mã UTF-8 chuẩn nên file hiển thị chuẩn 100% trên cả Microsoft Word, Excel máy tính lẫn Google Docs/Sheets.

### ❓ "Tôi muốn đổi nơi lưu file kết quả sang Desktop thay vì Downloads thì làm thế nào?"
- **Cách xử lý:** Trong câu lệnh yêu cầu, chỉ cần thêm câu: *"Lưu file kết quả ra Desktop giúp tôi"*. AIWF sẽ tự động điều hướng file thành phẩm về `~/Desktop/`.

### ❓ "Dữ liệu của tôi có bị gửi ra bên ngoài không?"
- **Trả lời:** Tuyệt đối không. AIWF chạy 100% cục bộ trên mô hình LLM tích hợp sẵn của Antigravity IDE, không gọi bất kỳ REST API bên thứ ba nào, không phát sinh chi phí token bên ngoài và bảo mật dữ liệu tuyệt đối.

---

[⬆ Về đầu trang / Mục lục](#mục-lục-điều-hướng-nhanh)

*AI Workforce Handbook v1.1 — Sổ tay vận hành nội bộ chính thức.*
