---
trigger: always_on
description: "Bản đồ tổ chức tổng. Bắt buộc nạp đầu tiên để định vị môi trường làm việc."
---

# BẢN ĐỒ TỔ CHỨC AI WORKFORCE

> Sơ đồ phòng ban và luật lệ tối cao cho hệ thống tác nhân số. Bất kỳ tác nhân nào được khởi tạo cũng phải đọc file này đầu tiên để định vị không gian làm việc.

---

## 1. KHUNG KIẾN TRÚC KWSR TỔNG THỂ
Workspace này được quy hoạch theo nguyên tắc "Company in a Folder" của KWSR:
- **[K] Knowledge**: `.agents/knowledge/` - Nơi chứa Nguồn Sự Thật Duy Nhất (SSOT).
- **[W] Workflow**: `.agents/workflows/` - Nơi chứa sổ tay vận hành và luồng quy trình (Reverse I-P-O).
- **[S] Skill**: `.agents/skills/` - Kho kỹ năng, mô tả công việc (JD) của nhân sự số 5 lớp.
- **[R] Rule**: `.agents/rules/` - Sàn phòng vệ và phân quyền.
- **Vùng Cách Ly (Isolation)**: `_Delete/` (Rác) và `_Archive/` (Kho lưu).

---

## 2. NGUYÊN TẮC ZERO-HALLUCINATION
Tuyệt đối KHÔNG BỊA DỮ LIỆU. Bất kỳ tuyên bố nào về chính sách, bảng giá, quy trình công ty đều phải dựa trên các file `artifacts/*.md` nằm trong thư mục `.agents/knowledge/`. Nếu không tìm thấy, AI bắt buộc phải trả lời: "Tôi không có đủ dữ liệu trong kho tri thức" và xin chỉ thị từ con người.

---

## 3. GIAO THỨC BÀN GIAO KHÔNG GHI ĐÈ
- Mỗi tác nhân (skill) chỉ được phép tạo file mới hoặc đọc file của tác nhân khác.
- CẤM ghi đè trực tiếp lên file đang là thành phẩm của người khác. Mọi sửa đổi phải lưu thành file bản nháp mới hoặc append vào cuối tệp.

---

## 4. NGUYÊN TẮC CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)
- Mọi skill AIWF chạy hoàn toàn bằng khả năng tích hợp sẵn của Antigravity IDE (hoặc IDE tương đương như Cursor, VS Code + Gemini/Copilot).
- TUYỆT ĐỐI KHÔNG gọi REST API bên ngoài (Gemini API, OpenAI API, etc.) hoặc yêu cầu API key để vận hành.
- Năng lực AI (dịch thuật, phân tích, tóm tắt, viết bài...) là của chính Agent (LLM tích hợp sẵn trong IDE).
- Python scripts chỉ phục vụ: bóc tách dữ liệu, merge, validate, xuất bản file — KHÔNG chứa logic AI hoặc lời gọi API.

---

## 5. NGUYÊN TẮC TỰ CHẠY ĐẾN KHI HOÀN TẤT (AUTONOMOUS FULL-RUN)
- Khi được kích hoạt, mọi skill PHẢI tự chạy liên tục cho đến khi hoàn tất 100% tác vụ và trả kết quả cho người dùng.
- KHÔNG ĐƯỢC tự dừng lại giữa chừng để xin phép hoặc chờ người dùng nhắc "tiếp tục".
- Chỉ dừng lại khi: (a) gặp lỗi nghiêm trọng không thể tự phục hồi, (b) cần thông tin bổ sung từ người dùng mà không thể suy luận được, hoặc (c) đã hoàn thành 100%.

---

## 6. VỊ TRÍ SKILL DUY NHẤT — SINGLE SOURCE OF TRUTH
- Toàn bộ skill nằm tại `.agents/skills/` trong thư mục workspace `ai-workforce/`.
- Khi mở thư mục `ai-workforce` làm workspace trong Antigravity IDE, mọi skill được nạp tự động từ `.agents/skills/`.
- Git push/pull đồng bộ 100% skill giữa các máy mà không cần cấu hình thêm hay cài đặt API key.
- Không phụ thuộc vào `~/.gemini/config/skills/` (global config) — mọi thứ portable trong 1 thư mục duy nhất.

---

## 7. SKILL REGISTRY — BẢNG TRA CỨU 13 KỸ NĂNG
Khi user yêu cầu thực hiện skill, Agent tìm SKILL.md theo bảng sau rồi đọc và thực hiện:

| STT | Skill | SKILL.md Path | Trigger Keywords |
|:---:|-------|---------------|------------------|
| 1 | **ejv-translate** | `.agents/skills/ejv-translate/SKILL.md` | Dịch 3 ngôn ngữ, EJV Translator, dịch VN/EN/JP |
| 2 | **boc-tach-pdf** | `.agents/skills/boc-tach-pdf/SKILL.md` | OCR PDF, bóc tách scan, scan ra Word |
| 3 | **boc-tach-cv** | `.agents/skills/boc-tach-cv/SKILL.md` | Bóc tách CV, trích xuất CV |
| 4 | **cham-diem-cv** | `.agents/skills/cham-diem-cv/SKILL.md` | Chấm điểm CV, đánh giá CV |
| 5 | **pdf-translate** | `.agents/skills/pdf-translate/SKILL.md` | Dịch PDF song ngữ, translate PDF |
| 6 | **invoice** | `.agents/skills/invoice/SKILL.md` | Xử lý hóa đơn, đề nghị thanh toán |
| 7 | **phan-tich-nhan-su** | `.agents/skills/phan-tich-nhan-su/SKILL.md` | Phân tích nhân sự, báo cáo KPI |
| 8 | **quan-ly-hop-dong** | `.agents/skills/quan-ly-hop-dong/SKILL.md` | Hợp đồng lao động, soạn hợp đồng |
| 9 | **tu-van-phap-luat** | `.agents/skills/tu-van-phap-luat/SKILL.md` | Tư vấn pháp luật, tra cứu luật |
| 10 | **viet-jd** | `.agents/skills/viet-jd/SKILL.md` | Viết JD, mô tả công việc |
| 11 | **viet-chuyen-nghiep** | `.agents/skills/viet-chuyen-nghiep/SKILL.md` | Viết bài chuyên nghiệp, soạn thảo văn bản |
| 12 | **xu-ly-van-phong** | `.agents/skills/xu-ly-van-phong/SKILL.md` | Word Excel PPT PDF, chuẩn NĐ 30 |
| 13 | **ai-coder-rules** | `.agents/skills/ai-coder-rules/SKILL.md` | Lập trình, code, fix bug, refactor |

---

## 8. PYTHON DEPENDENCIES — KIỂM TRA TỰ ĐỘNG
Trước khi chạy bất kỳ script nào trong `.agents/skills/*/scripts/`, Agent PHẢI:
```bash
python3 -c "import docx; import fitz; import pdfplumber" 2>/dev/null || pip3 install python-docx pymupdf pdfplumber lxml markitdown pypandoc
```

---

## 9. WORKSPACE REQUIREMENT — BẮT BUỘC
> ⚠️ Thư mục `ai-workforce/` PHẢI được mở làm workspace (File → Open Folder) trong Antigravity IDE.
> Nếu mở thư mục cha hoặc home thay vì `ai-workforce/`, Agent sẽ KHÔNG nạp được skills và rules → sẽ bị lỗi hoặc yêu cầu API key.
