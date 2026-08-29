# Kiến Trúc AI Workforce Extension & Cơ Chế File Picker (v2.4.0)

> **Mục đích:** Lưu trữ tri thức kỹ thuật để phục vụ việc bảo trì, phát triển và sửa lỗi trong các phiên làm việc tiếp theo mà không bị mất bối cảnh (Context Drift).

---

## 1. Bối cảnh & Lịch sử Khắc phục Sự cố (29/08/2026)

### Vấn đề gặp phải:
- Khi người dùng click vào icon **Dịch PDF** (hoặc các kỹ năng xử lý tài liệu) trên bảng điều khiển AI Workforce (Sidebar), hệ thống không mở hộp thoại chọn tệp mà chỉ hiển thị cảnh báo: `⚠️ Đã copy lệnh. Mở Chat (Cmd+Shift+I) rồi nhấn Cmd+V`.

### 3 Nguyên nhân Gốc rễ:
1. **Extension không được cập nhật khi chạy `auto-setup.sh`:**
   - Script `auto-setup.sh` chỉ kiểm tra nếu extension đã tồn tại trong danh sách `--list-extensions` thì bỏ qua việc cài đặt. Do đó, IDE giữ mãi phiên bản cũ `2.2.0` (chưa có code xử lý `needs_file` và `showOpenDialog`).
2. **Ký tự xuống dòng CRLF (`\r\n`) làm hỏng Regex Parser:**
   - Regex `^---\n` cũ trong `extension.js` và `build_dashboard.js` không khớp được các file `.md` có định dạng Windows CRLF (như `xu-ly-van-phong/SKILL.md`), dẫn đến mất thuộc tính `needs_file: true`.
3. **Thiếu lệnh Native Chat của Antigravity IDE:**
   - Antigravity IDE hỗ trợ lệnh `antigravity.sendPromptToAgentPanel`, nhưng extension cũ chỉ thử các lệnh standard VS Code nên rơi vào fallback thông báo clipboard.

---

## 2. Kiến Trúc Kỹ Thuật Extension v2.4.0

### 2.1. Cấu trúc thư mục Extension:
```
extension/
├── extension.js            # Logic chính: WebviewViewProvider, Parser, File Picker, Chat dispatcher
├── package.json            # Manifest: ID, version (2.4.0), activationEvents, contributes views/commands
├── .vscodeignore           # Loại bỏ file thừa khi đóng gói
└── media/
    ├── icon.svg            # Icon extension trên thanh Activity Bar
    └── webview.css         # Styling lưới icon, top bar, badges (📎 Chọn tệp)
```

### 2.2. Luồng Xử Lý Sự Kiện (Event Flow):
```
[User Click vào Card Skill/Workflow]
               │
               ▼
   [Webview JS bắt sự kiện 'click']
               │
               ├──> [Workflow / Skill không cần file] ──> [Gửi trigger vào Antigravity Chat]
               │
               └──> [Skill cần file (needs_file: true)]
                           │
                           ▼
             [Gọi vscode.window.showOpenDialog]
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
      [User Chọn File(s)]        [User Hủy / Cancel]
             │                           │
             ▼                           ▼
   [Định dạng prompt kèm       [Hiện QuickPick: Chọn lại
   đường dẫn tuyệt đối file]   hoặc mở Chat nhập thủ công]
             │
             ▼
[Gọi sendToAntigravityChat()]
   ├─ 1. antigravity.sendPromptToAgentPanel (Native AGY IDE)
   ├─ 2. antigravity.openChatView / antigravity.openAgent
   └─ 3. Clipboard + Paste fallback
```

### 2.3. Cấu hình Frontmatter cho Skill:
Mỗi file `.agents/skills/<skill-name>/SKILL.md` khai báo:
```yaml
---
name: pdf-translate
description: DỊCH TÀI LIỆU PDF sang tiếng Việt...
trigger: Dịch PDF, translate PDF...
needs_file: true          # true: tự động mở File Picker khi click
file_filter: pdf          # pdf | office | cv
---
```

### 2.4. Bảng Tra Cứu Bộ Lọc Tệp (`FILE_FILTER_MAP`):
| Loại Filter (`file_filter`) | Các định dạng hỗ trợ |
| :--- | :--- |
| **`pdf`** | `.pdf` |
| **`cv`** | `.pdf`, `.docx`, `.doc` |
| **`office`** | `.docx`, `.xlsx`, `.pptx`, `.pdf`, `.doc`, `.xls`, `.ppt`, `.txt`, `.csv` |

---

## 3. Quy Trình Đóng Gói & Tự Động Triển Khai (`scripts/auto-setup.sh`)

Mỗi khi có thay đổi trong `extension/`, script `scripts/auto-setup.sh` sẽ thực hiện tự động:
1. Đóng gói VSIX: `(cd extension && npx -y @vscode/vsce package --no-dependencies --allow-missing-repository)`
2. Cài đặt cưỡng bức: `antigravity-ide --install-extension "$VSIX_FILE" --force`
3. Quét và cập nhật `dashboard/data.json` qua `node dashboard/build_dashboard.js`.

---

## 4. Checklist Khắc Phục Nhanh Cho Tương Lai

- **Nếu sửa code extension mà IDE chưa nhận:**
  1. Chạy `bash scripts/auto-setup.sh`
  2. Mở IDE -> `Cmd+Shift+P` -> `Developer: Reload Window`.
- **Nếu thêm Skill mới có yêu cầu file:**
  1. Thêm `needs_file: true` và `file_filter: <pdf|cv|office>` vào YAML header của `SKILL.md`.
  2. Chạy `bash scripts/auto-setup.sh` để cập nhật cả Extension lẫn Dashboard.
