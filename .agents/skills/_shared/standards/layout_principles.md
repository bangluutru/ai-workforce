# NGUYÊN LÝ THIẾT KẾ DÀN TRANG DTP CHUẨN MỰC CHO AI WORKFORCE
## Đúc kết từ Kiến trúc Cỗ máy DTP DesignCraft & Adobe InDesign

> **Vị trí tài liệu:** `.agents/skills/_shared/standards/layout_principles.md`  
> **Phạm vi áp dụng:** Toàn bộ các kỹ năng xuất bản ấn phẩm in ấn, tài liệu đa trang và báo cáo chuyên nghiệp trong AIWF (`thiet-ke`, `dich-thuat`, `bao-cao-kt`, `xu-ly-van-phong`).  
> **Nguyên tắc cốt lõi:** Chuyển hóa tư duy từ "viết code HTML/CSS thông thường" sang **"Desktop Publishing (DTP) có kỷ luật toán học"**: kiểm soát chặt chẽ nhịp điệu dọc, vi sắp chữ (micro-typography), căn lề quang học và bắt lỗi tràn chữ (overset detection).

---

## 1. NGUYÊN LÝ LƯỚI CƠ SỞ (VERTICAL RHYTHM & BASELINE GRID)

### 1.1 Vấn đề trong dàn trang thông thường
Khi trình bày tài liệu nhiều cột (2 cột hoặc 3 cột như báo chí, brochure, tài liệu học thuật), các dòng văn bản của Cột 1 và Cột 2 thường bị so le nhau theo chiều dọc do khoảng cách dòng (`line-height`) và khoảng cách đệm (`margin-top`, `margin-bottom`) của các tiêu đề bị đặt ngẫu nhiên. Điều này làm trang in trông lộn xộn và thiếu tính chuyên nghiệp.

### 1.2 Giải pháp Lưới Cơ sở (Baseline Grid)
* **Khái niệm:** Lưới cơ sở là tập hợp các đường kẻ ngang vô hình cách đều nhau chạy suốt trang, làm điểm tựa cho đáy các con chữ (baseline) bám vào.
* **Module chuẩn:**
  * **Module cơ bản:** $4\text{pt}$ (dành cho lưới vi mô) hoặc $12\text{pt}$ / $14.4\text{pt}$ (dành cho dòng văn bản chính).
  * **Công thức đồng bộ:** Mọi phần tử trên trang (Tiêu đề $H_1, H_2$, Đoạn văn $P$, Hình ảnh $IMG$, Bảng biểu $TABLE$) bắt buộc phải có **tổng chiều cao bao gồm cả margin là một bội số nguyên của nhịp lưới cơ sở**:
    $$\text{Total Height} = \text{Element Height} + \text{Margin Top} + \text{Margin Bottom} = k \times \text{Baseline Module} \quad (k \in \mathbb{N}^*)$$
* **Ứng dụng thực tế:**
  * Thân bài (Body text): Cỡ chữ $10\text{pt}$, `line-height: 14.4pt` (hoặc $12\text{pt}$ tùy khổ giấy).
  * Tiêu đề mục (Heading 2): Cỡ chữ $16\text{pt}$, `line-height: 20pt` $\rightarrow$ Thêm `margin-top: 5.2pt` và `margin-bottom: 3.6pt` để tổng khối chiếm đúng $28.8\text{pt} = 2 \times 14.4\text{pt}$.
  * Kết quả: Dù Cột 1 có tiêu đề lớn chen ngang, dòng chữ tiếp theo của Cột 1 vẫn luôn thẳng hàng tăm tắp với dòng chữ tương ứng của Cột 2.

---

## 2. VI SẮP CHỮ & CĂN CHỈNH KHỐI CHỮ (KNUTH-PLASS & MICRO-TYPOGRAPHY)

### 2.1 Hiện tượng "Sông chữ" (Rivers of White Space) và Rách mép
Khi căn đều 2 bên (`text-align: justify`), các trình duyệt thông thường chỉ ngắt dòng theo thuật toán tham lam (Greedy First-Fit). Khi gặp các từ dài, trình duyệt ép giãn khoảng cách giữa các từ trên một dòng, tạo ra những khoảng trắng kéo dài xuyên qua các dòng liên tiếp trông như "dòng sông trắng" cắt dọc trang sách.

### 2.2 Quy tắc Justification 3 chiều (DesignCraft Typography Standard)
Để căn đều hoàn hảo như InDesign và Knuth-Plass, việc dãn chữ phải được phân bổ đều trên cả 3 trục:
1. **Khoảng cách giữa các từ (`word-spacing`):**
   * Tối thiểu: $85\%$ độ rộng dấu cách chuẩn.
   * Tối ưu (Desired): $100\%$.
   * Tối đa: $125\%$.
2. **Khoảng cách giữa các ký tự (`letter-spacing` / Tracking):**
   * Dung sai cho phép: $-0.02\text{em}$ đến $+0.02\text{em}$ (tối đa $\pm 2\%$).
3. **Độ co dãn bề ngang con chữ (Glyph Scaling):**
   * Dung sai an toàn thị giác: $98\%$ đến $102\%$ (mắt người không thể phát hiện độ biến dạng trong biên độ $2\%$, nhưng giúp loại bỏ $90\%$ lỗi ngắt dòng xấu).
4. **Tự động ngắt từ có gạch nối (`hyphens: auto`):**
   * Bắt buộc bật `hyphens: auto` kèm gói từ điển phân tiết tiếng Việt/tiếng Anh để các từ kỹ thuật dài tự động xuống dòng mượt mà.

### 2.3 Bù trừ Ngân sách Chữ khi Dịch thuật (Language Expansion Budget)
* Tiếng Việt khi dịch từ tiếng Anh hoặc tiếng Nhật có xu hướng **dài hơn từ 25% đến 35%**.
* **Quy tắc điều chỉnh:**
  * Giảm cỡ chữ nhẹ: $9.5\text{pt} \rightarrow 9.0\text{pt}$ hoặc $8.8\text{pt}$.
  * Thu hẹp dãn dòng (`leading`): $1.4\times \rightarrow 1.25\times$.
  * Co tracking nhẹ: `letter-spacing: -0.015em`.
  * Tuyệt đối không để cỡ chữ thân bài rơi xuống dưới $7.5\text{pt}$ đối với ấn phẩm in và dưới $8.5\text{pt}$ đối với tài liệu đọc trên màn hình.

---

## 3. CĂN LỀ QUANG HỌC (OPTICAL MARGIN ALIGNMENT)

### 3.1 Bản chất thị giác
Dấu ngoặc kép mở `“`, dấu chấm câu `.`, dấu phẩy `,` hoặc gạch đầu dòng `-` có trọng lượng thị giác (visual weight) nhẹ hơn nhiều so với một con chữ cái hoa như `H`, `M`, `W`. Khi đặt dấu ngoặc kép thẳng lề trái cùng với chữ cái, mắt người sẽ cảm thấy đoạn trích dẫn đó bị thụt vào trong (thụt lề giả).

### 3.2 Kỹ thuật Treo lề Quang học (Hanging Punctuation / Optical Hang)
* **Nguyên tắc:** Đẩy dấu ngoặc kép, dấu chấm, dấu gạch nhô ra ngoài lề (hang outside the margin) từ $50\%$ đến $100\%$ độ rộng của dấu:
  * Đầu đoạn trích dẫn (Blockquote): Dấu mở ngoặc kép `“` nhô ra ngoài lề trái để mép chữ cái đầu tiên của câu thẳng hàng tuyệt đối với mép lề các đoạn văn khác.
  * Danh sách có gạch đầu dòng: Ký tự gạch đầu dòng nhô lề nhẹ để con chữ đầu tiên bắt đầu đúng tọa độ căn lề.
* **Cách thực thi trong CSS:**
  ```css
  .dtp-quote {
    hanging-punctuation: first last allow-end;
  }
  /* Fallback cho trình duyệt chưa hỗ trợ full hanging-punctuation: */
  .dtp-quote-hang {
    text-indent: -0.45em;
    padding-left: 0.45em;
  }
  ```

---

## 4. CHUỖI KHUNG CHỮ & BẮT LỖI TRÀN CHỮ (THREADED FRAMES & OVERSET DETECTION)

### 4.1 Phân định Cấu trúc: Story vs. Frame
* **Story (Dòng chảy Nội dung):** Toàn bộ bài viết hoàn chỉnh (văn bản thô, danh sách, tiêu đề).
* **Frame (Khung Bố cục):** Các hộp chứa chữ cụ thể trên trang (ví dụ: Khung Cột 1, Khung Cột 2, Khung Nắp gấp, Khung Bìa).
* **Threading (Liên thông):** Một Story chảy xuyên suốt qua nhiều Frames. Khi Frame 1 đầy, chữ tự động rót sang Frame 2 mà không cần người dùng tự cắt xén nội dung.

### 4.2 Công thức Toán học Đo sức chứa Khung chữ (Overset Capacity Math)
Trước khi đưa nội dung vào khung chữ, Agent có thể ước tính sức chứa lý thuyết:
$$\text{Line Capacity} = \left\lfloor \frac{\text{Frame Height} - \text{Padding Top} - \text{Padding Bottom}}{\text{Line Height}} \right\rfloor$$
$$\text{Chars per Line} \approx \frac{\text{Frame Width} - \text{Padding Left} - \text{Padding Right}}{\text{Average Char Width (tùy font)}}$$
$$\text{Max Story Characters} \approx \text{Line Capacity} \times \text{Chars per Line} \times 0.95$$

### 4.3 Khóa chặn Bắt lỗi Tràn chữ (Overset Text Hard Blocker)
* Trong ấn phẩm in, nếu chữ tràn khung bị `overflow: hidden` cắt cụt, người đọc sẽ bị mất chữ nghiêm trọng (ví dụ mất số điện thoại, mất câu chốt giá).
* **Cơ chế cưỡng chế tự động:** Mọi công cụ xuất bản (Playwright / PyMuPDF) PHẢI chạy script kiểm tra:
  $$\Delta = \text{element.scrollHeight} - \text{element.clientHeight}$$
  * Nếu $\Delta > 2\text{px}$ $\rightarrow$ Đánh dấu **`LỖI OVERSET TEXT: Khung [ID] bị tràn chữ`** $\rightarrow$ **CẤM XUẤT BẢN** cho đến khi Agent tự sửa bằng 1 trong 3 cách:
    1. Tinh chỉnh rút gọn câu từ (giữ nguyên thông điệp).
    2. Kích hoạt giảm font-size / leading trong biên độ dung sai an toàn ($\le 10\%$).
    3. Mở rộng khung chữ hoặc chuyển sang bố cục nhiều khung nối (Threaded Frame).

---

## 5. THANG TỶ LỆ CHỮ VÀ PHÂN CẤP THỊ GIÁC (TYPOGRAPHIC HIERARCHY)

Áp dụng thang tỷ lệ Major Second ($1.125$) hoặc Minor Third ($1.200$) cho ấn phẩm in ấn thanh lịch:

| Cấp bậc | Tên vai trò | Cỡ chữ tương đối | Cỡ chữ Leaflet/Brochure | Cỡ chữ Slide 16:9 | Cỡ chữ Báo cáo A4 |
|:---:|---|:---:|:---:|:---:|:---:|
| **Display** | Tiêu đề bìa lớn | $2.5\times - 3.0\times$ | $28 - 32\text{pt}$ | $36 - 44\text{pt}$ | $24 - 28\text{pt}$ |
| **H1** | Tiêu đề chương / Tiêu đề mặt | $1.75\times - 2.0\times$ | $18 - 22\text{pt}$ | $24 - 28\text{pt}$ | $18 - 20\text{pt}$ |
| **H2** | Tiêu đề phần / Mục lớn | $1.35\times - 1.5\times$ | $14 - 16\text{pt}$ | $18 - 20\text{pt}$ | $14 - 15\text{pt}$ |
| **H3** | Tiêu đề nhóm con | $1.15\times - 1.2\times$ | $11 - 12\text{pt}$ | $14 - 16\text{pt}$ | $11 - 12\text{pt}$ |
| **Body** | Thân bài chuẩn | $1.0\times$ (Gốc) | $9.5 - 10\text{pt}$ | $12 - 14\text{pt}$ | $9.5 - 10.5\text{pt}$ |
| **Caption** | Chú thích ảnh, nguồn, footer | $0.75\times - 0.8\times$ | $7.5 - 8\text{pt}$ | $9 - 10\text{pt}$ | $7.5 - 8.5\text{pt}$ |

---

## 6. HƯỚNG DẪN ÁP DỤNG CHO TỪNG SKILL TRONG AIWF

1. **Skill `thiet-ke`**:
   - Nhúng `_shared/html/dtp_layout.css` vào tất cả các template (`trifold`, `bifold`, `poster`, `slides`).
   - Sử dụng lớp `.dtp-justified` cho các đoạn văn thân bài để triệt tiêu lỗi rách mép.
   - Bổ sung bước kiểm tra Overset Guard trong `export_print_pdf.py` và `preflight.py`.
2. **Skill `dich-thuat`**:
   - Chế độ `preserve`: Áp dụng công thức co chữ 3 chiều (font-size + tracking + leading) khi tiếng Việt giãn nở, triệt tiêu lỗi font chữ co vụn dưới $7\text{pt}$.
   - Chế độ `reconstruct`: Sử dụng Typst baseline grid và cân đối đáy 2 cột qua `#colbreak()`.
3. **Skill `bao-cao-kt`**:
   - Xây dựng mẫu dàn trang tài chính cao cấp (Executive Financial Dossier) dựa trên tỷ lệ lưới 12 cột, zebra striping bảng số liệu và nhịp điệu typography chuẩn.
4. **Skill `xu-ly-van-phong`**:
   - Cân bằng khoảng cách lề chuẩn Nghị định 30 với nhịp lưới dòng để tạo văn bản hành chính chỉn chu nhất.
