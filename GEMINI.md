# AI WORKFORCE — Hướng dẫn vận hành cho AI Agent

> File này được nạp TỰ ĐỘNG khi mở thư mục `ai-workforce` làm workspace trong Antigravity IDE (hoặc Cursor/VS Code có AI agent).
> Agent PHẢI đọc file này TRƯỚC KHI thực hiện bất kỳ yêu cầu nào.

---

## ⚡ LỆNH KÍCH HOẠT NHANH TỪ NGƯỜI DÙNG

Khi người dùng nhắn bất kỳ câu nào sau đây:
- *"Cập nhật quy tắc từ README"*
- *"Đồng bộ quy tắc từ README.md"*
- *"Khởi tạo môi trường AIWF"*
- Hoặc mở phiên làm việc mới trên máy mới

👉 **Agent PHẢI thực hiện ngay 4 bước sau mà không cần hỏi lại:**
1. **Đọc `README.md` và `.agents/rules/*.md`** để nạp toàn bộ luật và quy trình.
2. **Kiểm tra Python dependencies** bằng lệnh:
   ```bash
   python3 -c "import docx; import fitz; import pdfplumber" 2>/dev/null || pip3 install python-docx pymupdf pdfplumber lxml markitdown pypandoc
   ```
3. **Quét danh mục 7 skills** trong `.agents/skills/` để sẵn sàng nhận lệnh.
4. **Báo cáo tóm tắt trạng thái sẵn sàng**: *"✅ AI Workforce đã đồng bộ toàn bộ 7 skills, 3 bộ quy tắc an toàn và môi trường Python sẵn sàng hoạt động 100% mà không cần bất kỳ API key bên ngoài nào."*

---

## ⚠️ NGUYÊN TẮC BẮT BUỘC — ZERO EXTERNAL API

1. **KHÔNG gọi REST API bên ngoài** (Gemini API, OpenAI API, Claude API, v.v.) và **KHÔNG yêu cầu API key** để vận hành bất kỳ skill nào.
2. **Toàn bộ năng lực AI** (dịch thuật, phân tích, tóm tắt, viết bài, đánh giá...) là của **chính Agent** (LLM tích hợp sẵn trong IDE).
3. **Python scripts** trong `.agents/skills/*/scripts/` chỉ phục vụ xử lý dữ liệu (bóc tách, merge, validate, xuất bản file) — **KHÔNG chứa logic AI hoặc lời gọi API**.
4. Khi được kích hoạt, skill **PHẢI tự chạy liên tục** cho đến khi hoàn tất 100% — **KHÔNG tự dừng giữa chừng** để xin phép.
5. **KHÔNG BỊA DỮ LIỆU**. Mọi thông tin chính sách, bảng giá, quy trình phải dựa trên `.agents/knowledge/`.

---

## 📦 SKILL REGISTRY — Bản đồ 7 kỹ năng

Khi user yêu cầu thực hiện một skill, Agent PHẢI:
1. Tìm skill phù hợp trong bảng dưới đây dựa trên **trigger keywords**.
2. **Đọc file SKILL.md** tương ứng để nắm quy trình chi tiết.
3. Thực hiện đầy đủ các bước trong SKILL.md.

| STT | Skill | Trigger Keywords | SKILL.md Path |
|:---:|-------|------------------|---------------|
| 1 | **ejv-translate** | Dịch tài liệu 3 ngôn ngữ, EJV Translator, dịch VN/EN/JP | `.agents/skills/ejv-translate/SKILL.md` |
| 2 | **boc-tach-pdf** | Bóc tách PDF scan, số hóa tài liệu, OCR PDF, scan ra Word | `.agents/skills/boc-tach-pdf/SKILL.md` |
| 3 | **invoice** | Xử lý hóa đơn, đề nghị thanh toán, invoice | `.agents/skills/invoice/SKILL.md` |
| 4 | **tu-van-phap-luat** | Tư vấn pháp luật, tra cứu luật, xử lý tranh chấp | `.agents/skills/tu-van-phap-luat/SKILL.md` |
| 5 | **viet-chuyen-nghiep** | Viết bài chuyên nghiệp, soạn thảo văn bản | `.agents/skills/viet-chuyen-nghiep/SKILL.md` |
| 6 | **xu-ly-van-phong** | Xử lý văn phòng, tạo sửa Word Excel PPT PDF | `.agents/skills/xu-ly-van-phong/SKILL.md` |
| 7 | **ai-coder-rules** | Lập trình, code, fix bug, refactor, thêm tính năng | `.agents/skills/ai-coder-rules/SKILL.md` |

---

## 🛡️ HỆ THỐNG QUY TẮC AN TOÀN (RULES)

| Rule File | Mục đích |
|-----------|----------|
| `.agents/rules/AGENTS.md` | Bản đồ tổ chức tổng, nguyên tắc KWSR, Zero-Hallucination |
| `.agents/rules/R1-zero-destruction.md` | Cấm xóa vĩnh viễn, cơ chế xóa mềm `_Delete/` và lưu trữ `_Archive/` |
| `.agents/rules/R2-code-quality.md` | Zero-Inference Taxonomy, Codebase-first, Token Economics, 5 Absolute Bans |
| `.agents/rules/R3-operational-discipline.md` | Per-Task Verification, Autonomous Full-Run, Regression Prevention |

---

## 🔧 PATH RESOLUTION — Quy ước đường dẫn

Khi SKILL.md sử dụng các placeholder như `<skill_dir>`, `<process_dir>`, agent PHẢI resolve như sau:

| Placeholder | Giá trị thực |
|-------------|-------------|
| `<workspace>` | Thư mục root của workspace hiện tại (chứa file `GEMINI.md` này) |
| `<skill_dir>` | `<workspace>/.agents/skills/<tên_skill>/` |
| `<process_dir>` | Thư mục tạm để xử lý, tạo tại nơi thuận tiện (ví dụ: `<workspace>/_process/<tên_tài_liệu>/` hoặc artifact directory) |
| `<output_dir>` | Mặc định: `~/Downloads/` hoặc nơi user chỉ định |
| `<file_goc>` | File đầu vào do user cung cấp |

---

## 🐍 PYTHON DEPENDENCIES — Cài đặt tự động

Trước khi chạy bất kỳ Python script nào trong `.agents/skills/*/scripts/`, Agent PHẢI kiểm tra và cài dependencies nếu chưa có:

```bash
python3 -c "import docx; import fitz; import pdfplumber" 2>/dev/null || pip3 install python-docx pymupdf pdfplumber lxml markitdown pypandoc
```

Danh sách packages cần thiết (xem `requirements.txt`):
- `python-docx` — Tạo/đọc file DOCX
- `pymupdf` (fitz) — Đọc/render PDF
- `pdfplumber` — Trích xuất bảng biểu từ PDF
- `lxml` — Xử lý XML
- `markitdown` — Chuyển đổi Markdown
- `pypandoc` — Chuyển đổi định dạng tài liệu

---

## 🆘 TROUBLESHOOTING

### "Agent yêu cầu API key"
**Nguyên nhân**: Thư mục `ai-workforce` chưa được mở làm workspace $\rightarrow$ Agent không nạp được GEMINI.md và AGENTS.md.
**Giải pháp**: Mở thư mục `ai-workforce` làm workspace trong Antigravity IDE: **File $\rightarrow$ Open Folder $\rightarrow$ chọn thư mục `ai-workforce`**.

### "Skill không tìm thấy"
**Nguyên nhân**: Agent chưa đọc GEMINI.md hoặc SKILL.md.
**Giải pháp**: Gõ câu lệnh: *"Đồng bộ quy tắc từ README.md"* hoặc gõ yêu cầu kèm tên skill rõ ràng.

### "Python script lỗi import"
**Nguyên nhân**: Chưa cài Python dependencies.
**Giải pháp**: Chạy `pip3 install -r requirements.txt` trong thư mục `ai-workforce`.
