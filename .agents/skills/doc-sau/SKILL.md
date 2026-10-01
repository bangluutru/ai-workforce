---
name: doc-sau
display-name: Đọc Sâu
description: >-
  Phân tích chuyên sâu bài viết, sách, tài liệu học thuật và báo cáo phức tạp thông qua 10+ mô hình tư duy (SCQA, 5W2H, Tư duy phản biện, Tư duy đảo ngược, Mô hình đa ngành, Nguyên lý đệ nhất, Tư duy hệ thống, 6 chiếc nón tư duy). Tự động phân tầng độ sâu (Quick 15p, Standard 30p, Deep 60p, Research 120p) và xuất bản báo cáo hành động thực tế.
  USE WHEN: Người dùng muốn đọc hiểu sâu, mổ xẻ cấu trúc bài viết, phát hiện lỗi logic/ngụy biện, phân tích rủi ro tiềm ẩn, tổng hợp đối chiếu đa nguồn hoặc chuyển hóa tri thức thành kế hoạch thực thi 24h.
  DO NOT USE WHEN: Chỉ cần bóc tách OCR tài liệu scan (dùng 'boc-tach-pdf'), dịch văn bản đơn thuần (dùng 'ejv-translate' hoặc 'dich-giu-dinh-dang'), hoặc sáng tạo bài viết mới (dùng 'viet-bai').
trigger: Đọc Sâu, deep reading, phân tích bài viết, mổ xẻ tài liệu, tư duy phản biện, SCQA, tóm tắt sâu, phân tích sách, mổ xẻ báo cáo
category: docs
needs_file: false
file_filter: any
---

# Kỹ Năng Đọc Sâu (Deep Reading Analyst v2.0)
## Chuẩn Kiến Trúc Phân Tích & Kích Hoạt Tri Thức Đa Tầng AIWF

<goal>
Chuyển hóa việc đọc lướt bề mặt (surface-level reading) thành việc học sâu sắc (deep learning) và hành động thực tiễn (knowledge activation). Áp dụng 10+ khung tư duy đã được kiểm chứng (McKinsey SCQA, 5W2H, Tư duy phản biện, Tư duy đảo ngược Charlie Munger, 30+ Mô hình tư duy đa ngành, Nguyên lý đệ nhất Elon Musk, Tư duy hệ thống Donella Meadows, 6 chiếc nón tư duy Edward de Bono, Ma trận so sánh đa nguồn) để mổ xẻ toàn diện bài viết, sách, luận văn hoặc báo cáo chiến lược.
</goal>

---

<context>
Kỹ năng vận hành dựa trên các nguyên tắc thiết kế tối cao của AI Workforce:
1. **Insight Over Framework Completion**: Mục tiêu tối thượng là thấu suốt bản chất và trích xuất tri thức giá trị, không phải việc hoàn thành danh sách kiểm tra các mô hình một cách máy móc. Chất lượng tư duy quan trọng hơn số lượng khung được gọi tên.
2. **Action-Oriented & Quick Win 24h**: Mọi phiên phân tích đều bắt buộc kết thúc bằng việc kích hoạt tri thức — xác định 3 bài học đắt giá nhất và 1 hành động siêu nhỏ có thể thực thi ngay trong vòng 24 giờ.
3. **Evidence Verifier & Zero-Hallucination**: Mọi kết luận, nhận định phải gắn liền với trích dẫn NGUYÊN VĂN từ văn bản gốc, phân định rõ ràng giữa sự thật khách quan (Facts) và ý kiến chủ quan của tác giả (Opinions). Áp dụng Confidence Flagging khi thông tin trong tài liệu nguồn còn mơ hồ.
4. **Kiến trúc Zero External LLM API**: Vận hành 100% qua mô hình Agent nội bộ IDE (Gemini 3.8), hoàn toàn không gọi REST API ngoài, không yêu cầu API key bên thứ ba.
5. **Autonomous Full-Run**: Tự động thực thi xuyên suốt từ bóc tách cấu trúc, phản biện, phân tích rủi ro đến dàn trang báo cáo hoàn chỉnh mà không dừng lại xin phép vụn vặt.
</context>

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Toàn bộ quá trình đọc hiểu, suy luận đa ngành và tổng hợp báo cáo do AI Agent nội bộ đảm trách.
> - Tuyệt đối không gọi REST API ngoài, không yêu cầu API key.
> - Kỹ năng tự chạy liên tục (Autonomous Full-Run) đến khi hoàn tất báo cáo chính thức.

---

## 🔧 Path Resolution & Thư Mục Lưu Trữ Đầu Ra

Agent PHẢI xác định đường dẫn lưu file trước khi thực hiện quy trình:

| Placeholder | Quy ước xác định đường dẫn thực tế |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<process_dir>` | Thư mục tạm xử lý: `<workspace>/_process/deep_reading_[timestamp]/` (nằm trong `.gitignore`) |
| `<skill_dir>` | Thư mục kỹ năng: `<workspace>/.agents/skills/doc-sau/` |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi file báo cáo thành phẩm xuất bản (`[Ten_Tai_Lieu]_Deep_Reading_Analysis.md` hoặc `.docx`) PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/`).
> - Toàn bộ ghi chú trung gian, trích xuất thô PHẢI lưu trong `<process_dir>`.
> - TUYỆT ĐỐI KHÔNG xả file kết quả trực tiếp vào thư mục gốc repository Git.

---

## 🏗️ Bảng Tọa Độ Đầu Vào & Phân Luồng (Intake Coordinates)

Trước khi tiến hành phân tích sâu, Agent xác định tọa độ đầu vào theo 4 Trục:

| Trục Tọa độ | Giá trị xác định | Hành vi mặc định nếu thiếu |
|---|---|---|
| **1. Nội dung Nguồn** | Văn bản dán trực tiếp, file tài liệu (PDF, Word, Markdown) hoặc URL | Yêu cầu người dùng cung cấp tài liệu cần đọc |
| **2. Mục đích Đọc** | 1. Giải quyết vấn đề (Problem-solving)<br>2. Học tập / Nghiên cứu (Learning)<br>3. Tham khảo viết lách (Writing Reference)<br>4. Ra quyết định (Decision-making) | Mặc định: Học tập & Thấu suốt bản chất (Learning) |
| **3. Cấp độ Độ sâu** | • **Level 1**: Nhanh (15 phút)<br>• **Level 2**: Chuẩn mực (30 phút)<br>• **Level 3**: Chuyên sâu (60 phút)<br>• **Level 4**: Nghiên cứu đối chiếu (120+ phút) | Mặc định: **Level 2 (Chuẩn mực - 30 phút)** |
| **4. Thư mục Xuất bản** | Đường dẫn thư mục lưu file kết quả | Mặc định: `~/Downloads/AIWF_Output/` |

---

<instructions>
## QUY TRÌNH THỰC THI 5 BƯỚC (SOP AUTONOMOUS FULL-RUN)

### BƯỚC 1: TIẾP NHẬN & ĐỊNH HÌNH MỤC TIÊU (INTAKE & INITIALIZATION)
1. Xác định nhanh thể loại bài viết và tự động đề xuất tổ hợp mô hình phù hợp:
   - 📄 *Bài viết Chiến lược / Doanh thương:* SCQA + Mô hình Đa ngành (Kinh tế học) + Tư duy Đảo ngược.
   - 📊 *Báo cáo Khoa học / Luận văn:* 5W2H + Tư duy Phản biện + Tư duy Hệ thống.
   - 💡 *Tài liệu Hướng dẫn (How-to) / Kỹ thuật:* SCQA + 5W2H + Nguyên lý Đệ nhất.
   - 🎯 *Bài chính luận / Quan điểm xã hội:* Tư duy Phản biện + Tư duy Đảo ngược + 6 Chiếc nón.
   - 📈 *Nghiên cứu Tình huống (Case Study):* SCQA + Mô hình Đa ngành + Tư duy Hệ thống.
2. Nếu người dùng không chỉ định cấp độ, tự động chọn **Level 2 (Standard - 30 phút)** để bảo đảm tính chuẩn xác và tiết kiệm token.

---

### BƯỚC 2: BÓC TÁCH CẤU TRÚC NỀN TẢNG (STRUCTURAL UNDERSTANDING)
*Luôn luôn thực hiện bước này cho mọi cấp độ phân tích.*

#### 2A. Sơ đồ Cấu trúc & Luận điểm Cốt lõi
- **Thể loại văn bản:** [Bài báo / Luận văn / Sách / Báo cáo / Hướng dẫn]
- **Thời lượng đọc ước tính:** [Số phút]
- **Luận điểm Tối thượng (Core Thesis):** Tóm tắt trong 1 câu duy nhất.
- **Cấu trúc luận cứ:**
  - Luận cứ 1 $\rightarrow$ Các dẫn chứng hỗ trợ.
  - Luận cứ 2 $\rightarrow$ Các dẫn chứng hỗ trợ.
  - Luận cứ 3 $\rightarrow$ Các dẫn chứng hỗ trợ.
- **Khái niệm then chốt:** Định nghĩa cô đọng 3-5 thuật ngữ then chốt.

#### 2B. Bóc tách Cấu trúc SCQA (McKinsey Framework)
Tham chiếu tài liệu: `<skill_dir>/references/scqa_framework.md`
- **S (Situation - Tình huống):** Bối cảnh thực tế không thể chối cãi mà tác giả thiết lập.
- **C (Complication - Thách thức/Khủng hoảng):** Biến cố, trở ngại hoặc xung đột nảy sinh.
- **Q (Question - Câu hỏi Then chốt):** Câu hỏi trọng tâm mà tài liệu cần trả lời.
- **A (Answer - Câu trả lời/Giải pháp):** Lời giải hoặc quan điểm mà tác giả đề xuất.
- Đánh giá chất lượng cấu trúc logic: Tính rõ ràng, mạch lạc và độ thuyết phục (thang điểm 1-5 sao).

#### 2C. Kiểm tra Độ toàn vẹn Thông tin 5W2H
Tham chiếu tài liệu: `<skill_dir>/references/5w2h_analysis.md`
- Quét nhanh 7 khía cạnh: **What** (Cái gì), **Why** (Tại sao), **Who** (Ai), **When** (Khi nào), **Where** (Ở đâu), **How** (Như thế nào), **How much** (Chi phí/Cái giá).
- Chỉ rõ những mảng thông tin tác giả bỏ quên hoặc cố tình tránh né (Information Gaps).

---

### BƯỚC 3: ÁP DỤNG CÁC MÔ HÌNH TƯ DUY THEO CẤP ĐỘ ĐỘ SÂU

#### 🔹 CẤP ĐỘ 1: QUICK MODE (15 PHÚT)
- Bóc tách cấu trúc cơ bản + SCQA + 5W2H Completeness Check.
- Rút ra TOP 3 Insight đắt giá nhất.
- Xác định 1 hành động khả thi ngay trong 24h.

#### 🔹 CẤP ĐỘ 2: STANDARD MODE (30 PHÚT) — Bổ sung Phản biện & Đảo ngược
1. **Tư duy Phản biện (Critical Thinking):**
   - Tham chiếu: `<skill_dir>/references/critical_thinking.md`
   - Chấm điểm độ vững chắc của lập luận (Thang điểm 1-10).
   - Phát hiện các lỗi ngụy biện logic (Fallacies): Khái quát hóa vội vã, tương quan ngộ nhận nhân quả (Correlation vs Causation), công kích cá nhân, dốc trượt...
   - Đánh giá chất lượng bằng chứng: Dữ liệu thực nghiệm hay giai thoại cá nhân?
2. **Tư duy Đảo ngược (Inversion Thinking):**
   - Tham chiếu: `<skill_dir>/references/inversion_thinking.md`
   - Phương pháp Charlie Munger: "Nếu muốn thất bại thảm hại khi áp dụng lời khuyên này, ta phải làm gì?"
   - Tiền khám nghiệm (Pre-mortem Analysis): Liệt kê 2-3 kịch bản tồi tệ nhất dẫn đến sụp đổ và biện pháp phòng ngừa.

#### 🔹 CẤP ĐỘ 3: DEEP MODE (60 PHÚT) — Bổ sung Mô hình Đa ngành & Hệ thống
1. **Mô hình Tư duy Đa ngành (Mental Models):**
   - Tham chiếu: `<skill_dir>/references/mental_models.md`
   - Áp dụng 3-5 lăng kính liên ngành (Vật lý: Đòn bẩy, Quán tính; Sinh học: Tiến hóa, Hiệu ứng Nữ hoàng Đỏ; Tâm lý học: Thiên kiến xác nhận, Ác cảm mất mát; Kinh tế: Chi phí cơ hội, Động lực khuyến khích; Toán học: Luật lũy thừa 80/20, Phân phối chuẩn).
2. **Nguyên lý Đệ nhất (First Principles Thinking):**
   - Tham chiếu: `<skill_dir>/references/first_principles.md`
   - Bóc trần mọi giả định ngầm định của tác giả. Giả định nào đúng, giả định nào sai?
   - Tái dựng sự thật nguyên bản còn lại sau khi bóc tách hết giả định.
3. **Tư duy Hệ thống (Systems Thinking):**
   - Tham chiếu: `<skill_dir>/references/systems_thinking.md`
   - Vẽ sơ đồ vòng lặp nhân quả (Causal Loop): Vòng tăng cường (Reinforcing) vs Vòng cân bằng (Balancing).
   - Xác định Điểm đòn bẩy (Leverage Point) — nơi thay đổi nhỏ mang lại chuyển biến đột phá.
4. **Sáu Chiếc nón Tư duy (Six Thinking Hats):**
   - Tham chiếu: `<skill_dir>/references/six_hats.md`
   - Đánh giá đa chiều qua 6 lăng kính: Trắng (Dữ liệu), Đỏ (Trực giác), Đen (Rủi ro), Vàng (Lợi ích), Lục (Ý tưởng sáng tạo), Lam (Điều phối tiến trình).

#### 🔹 CẤP ĐỘ 4: RESEARCH MODE (120+ PHÚT) — So sánh Đa nguồn
1. Tìm kiếm 2-3 tài liệu đối trọng độc lập qua công cụ tra cứu.
2. Tham chiếu: `<skill_dir>/references/comparison_matrix.md`
3. Lập ma trận so sánh đa nguồn:
   - Điểm đồng thuận (Consensus): Những gì các chuyên gia đều nhất trí.
   - Điểm phân kỳ (Divergence): Những góc nhìn mâu thuẫn nảy lửa.
   - Góc nhìn tích hợp (Integrated Synthesis): Đúc kết góc nhìn toàn diện độc bản.

---

### BƯỚC 4: TỔNG HỢP & DÀN TRANG THÀNH PHẨM (SYNTHESIS & REPORT GENERATION)
Lựa chọn mẫu báo cáo phù hợp nhất từ `<skill_dir>/templates/output_templates.md`:
1. **Bản ghi chép học tập tiêu chuẩn (Standard Learning Notes)**
2. **Bản đồ khái niệm mạng lưới (Concept Map)**
3. **Hồ sơ phản biện lập luận (Argument Analysis)**
4. **Kế hoạch ứng dụng thực chiến (Practical Application Plan)**
5. **Ma trận so sánh đa tài liệu (Comparison Matrix)**
6. **Thẻ tóm tắt bỏ túi 1 trang (Quick Reference Card)**
7. **Bản truyền đạt theo Kỹ thuật Feynman (Feynman ELI5)**
8. **Ma trận trọng số ra quyết định (Decision Matrix)**

---

### BƯỚC 5: KÍCH HOẠT TRI THỨC & BÀN GIAO SẠCH (KNOWLEDGE ACTIVATION)
Bắt buộc đính kèm phần kết luận kích hoạt hành động:
- **🎯 TOP 3 BÀI HỌC CỐT TỬ**: Mỗi bài học đi kèm phân tích "Tại sao quan trọng" và "1 hành động tương ứng".
- **💡 QUICK WIN 24H**: Đúng 1 việc cực nhỏ, rõ ràng, thực thi được ngay trong 24 giờ tới.
- **🔗 LỘ TRÌNH ĐI TIẾP**: Đề xuất sách đọc tiếp, giả thuyết cần thử nghiệm hoặc đối tượng cần thảo luận.
- **🧭 DANH MỤC KHUNG TƯ DUY ĐÃ DÙNG**: Tích chọn rõ ràng các mô hình đã vận dụng trong bài phân tích.
</instructions>

---

<quality_gate>
## TIÊU CHÍ KIỂM ĐỊNH CHẤT LƯỢNG (QUALITY GATE CHECKLIST)

Trước khi xuất bản file và bàn giao cho người dùng, Agent tự kiểm định theo 7 tiêu chí:
- [ ] **1. Tính trung thực nguyên bản (Fidelity):** Tuyệt đối không bóp méo luận điểm của tác giả; phân biệt rõ Fact vs Opinion.
- [ ] **2. Evidence Verifier:** Các nhận định phản biện phải trích dẫn NGUYÊN VĂN từ văn bản nguồn, có chỉ dẫn vị trí/đoạn văn.
- [ ] **3. Tránh hời hợt (Anti-Superficiality):** Khi dùng khung tư duy, phải đi sâu vào cơ chế thay vì chỉ gắn nhãn tiêu đề.
- [ ] **4. Bóc tách rủi ro (Inversion):** Phải nêu rõ ít nhất 1-2 kịch bản thất bại hoặc điểm mù mà bài viết chưa giải quyết.
- [ ] **5. Tinh thần hành động (Action-Oriented):** Bắt buộc có Quick Win 24h cụ thể, đo lường được.
- [ ] **6. Bảo vệ Codebase (Anti-Repo Bloat):** File kết quả được ghi vào `<output_dir>`, tuyệt đối không lưu rác vào root Git.
- [ ] **7. Tối ưu Token & Không gọi API ngoài:** Hoàn thành nhiệm vụ 100% bằng nội lực Agent, không viện dẫn API bên ngoài.
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (CLEAN DELIVERY PROTOCOL)

1. **Xuất bản file vật lý:**
   - Tạo file báo cáo hoàn chỉnh tại `<output_dir>/[Ten_Tai_Lieu]_Deep_Reading_Analysis.md` (hoặc `.docx` nếu người dùng yêu cầu).
2. **Phản hồi trên khung chat IDE:**
   - **Khung chat chỉ hiển thị bản tóm tắt điều hành ngắn gọn (Executive Summary):**
     - Luận điểm cốt lõi (1 câu).
     - Kết quả SCQA & Chấm điểm phản biện (1 bảng ngắn).
     - Top 3 Insights & Quick Win 24 giờ.
     - **Đường dẫn file vật lý có thể nhấn click trực tiếp:** `[Xem báo cáo phân tích đầy đủ](file://<duong_dan_tuyet_doi>)`.
   - Tuyệt đối không xả toàn bộ báo cáo dài hàng nghìn từ lên màn hình chat gây trôi context của phiên làm việc.
</delivery_protocol>
