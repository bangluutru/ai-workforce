# KIẾN TRÚC EXTENSION AI WORKFORCE (v3.4.0) & TÍNH NĂNG CHỌN NGUỒN TÀI LIỆU ĐA KÊNH

---

## 1. Tổng Quan Kiến Trúc (Architecture Overview)

Extension **AI Workforce Panel** (`extension/extension.js`) hoạt động như một trung tâm điều phối trực quan cho toàn bộ hệ thống nhân sự số AI Workforce:
- **Tab 1: Tác Vụ (Workflows & Skills)**: Quản lý và kích hoạt nhanh các quy trình nghiệp vụ và kỹ năng chuyên sâu.
- **Tab 2: Tri Thức (Smart Knowledge Catalog)**: Hiển thị bản đồ 3 cấp (Lĩnh vực $\rightarrow$ Notebook $\rightarrow$ Tài liệu) liên kết trực tiếp với Google NotebookLM.

---

## 2. Các Cơ Chế Cốt Lõi trong v3.4.0

### 2.1. Bộ Chọn Nguồn Tài Liệu Đa Kênh (`selectDocumentSourceForSkill`)
Khi người dùng kích hoạt bất kỳ Skill nào (ví dụ `ejv-translate`, `pdf-translate`, `boc-tach-pdf`, `xu-ly-van-phong`...):
1. **📁 Chọn tệp từ máy tính (Local Disk):**
   - Mở `vscode.window.showOpenDialog` với bộ lọc file tương ứng (`.pdf`, `.docx`, `.xlsx`...).
2. **📚 Chọn tài liệu từ Gemini Notebook (Mục lục tri thức):**
   - Mở `selectNotebookDocument()` cho phép tìm kiếm nhanh toàn bộ 753+ tài liệu hoặc chọn theo từng Notebook.
3. **⚡ Thực hiện trực tiếp:**
   - Gửi prompt yêu cầu trực tiếp vào Chat mà không kèm file đính kèm.

### 2.2. Trình Duyệt Notebook & Tìm Kiếm Toàn Cục (`selectNotebookDocument`)
- Đọc dữ liệu từ `.agents/knowledge/catalog.json`.
- Tự động map đường dẫn file offline nếu Notebook đã sync (`.agents/knowledge/<notebook_slug>/artifacts/sources/source_XX_<slug>.md`).
- QuickPick với 2 tùy chọn:
  - `🔍 [Tìm kiếm nhanh] Toàn bộ N tài liệu trong M Notebooks...`: Lọc theo từ khóa tức thì.
  - `📓 Danh sách Notebooks`: Hiển thị icon, tên danh mục, số lượng tài liệu, trạng thái sync.

### 2.3. Tương Tác 2 Chiều Trên Knowledge Catalog
- Trong danh sách tài liệu của từng Notebook (Tab Tri thức), hỗ trợ 3 nút thao tác:
  - `⚡` (**Áp dụng Skill**): Bật QuickPick chọn Skill (`EJV Translate`, `PDF Translate`, `Bóc Tách PDF`, `Tư Vấn Pháp Luật`, `Xử Lý Văn Phòng`...).
  - `🌐` (**Dịch EJV**): Hỏi ngôn ngữ đích và chạy EJV Translate.
  - `💬` (**Hỏi AI**): Gửi lệnh tóm tắt/phân tích tài liệu vào Chat.

### 2.4. Pipeline Gửi Lệnh Vào Antigravity Chat 4 Tầng (`sendToAntigravityChat`)
1. **Tầng 1 (Clipboard):** Lưu prompt an toàn vào clipboard hệ thống (`vscode.env.clipboard.writeText`).
2. **Tầng 2 (Native Command):** Gọi `antigravity.sendPromptToAgentPanel` với chuỗi prompt hoàn chỉnh.
3. **Tầng 3 (Standard Commands):** Gọi `workbench.action.chat.open`, `interactiveEditor.start`, v.v.
4. **Tầng 4 (Type/Paste & Fallback):** Tự động focus input và điền lệnh.

---

## 3. Quy Trình Đóng Gói & Tự Động Triển Khai (`auto-setup.sh`)

- Build package: `npx -y @vscode/vsce package --no-git-tag-version` $\rightarrow$ `extension/ai-workforce-panel-3.4.0.vsix`.
- Tự động cài đè (`--force`) vào tất cả các thư mục extensions phát hiện trên máy:
  - `~/.gemini/antigravity-ide/extensions/`
  - `~/.antigravity-ide/extensions/`
  - `~/.vscode/extensions/`
  - `~/.cursor/extensions/`
- Tự động kích hoạt Git hook `post-merge` để mọi máy khác sau `git pull` đều tự động cập nhật extension mới nhất.
