# 🤖 AI Workforce (AIWF)

> **Lực lượng Lao động AI — Company in a Folder**
>
> Hệ thống tác nhân số vận hành trên nền tảng [Antigravity IDE](https://antigravity.dev), giúp tự động hóa quy trình doanh nghiệp bằng AI.

---

## 📋 Mục lục

- [Tổng quan](#-tổng-quan)
- [Cài đặt trên máy mới](#-cài-đặt-trên-máy-mới)
- [Kiến trúc KWSR](#-kiến-trúc-kwsr)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Sử dụng hàng ngày](#-sử-dụng-hàng-ngày)
- [Thêm nhân viên số mới](#-thêm-nhân-viên-số-mới)
- [Auto-Setup & Git Hooks](#-auto-setup--git-hooks)
- [Extension (VS Code / Antigravity IDE)](#-extension)
- [Dashboard (Web)](#-dashboard)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Tổng quan

AI Workforce biến Antigravity IDE thành một **phòng nhân sự số** — mỗi "nhân viên" (Skill) có mô tả công việc, biết khi nào nên làm và không nên làm, tham chiếu dữ liệu thật từ kho tri thức nội bộ.

### Thành phần chính

| Thành phần | Mô tả |
|---|---|
| **Skills** (Nhân sự số) | AI agents với chuyên môn cụ thể — bóc tách CV, dịch PDF... |
| **Workflows** (Quy trình) | Chuỗi thao tác tự động — chuẩn bị tuyển dụng, sàng lọc CV... |
| **Knowledge** (Tri thức) | Dữ liệu thật (SSOT) — bảng lương, chính sách, quy định. |
| **Rules** (Luật) | Rào chắn an toàn — cấm xóa file, cấm bịa dữ liệu. |
| **Extension** | Sidebar icon grid trong IDE — click để kích hoạt skill/workflow. |
| **Dashboard** | Web UI hiển thị toàn bộ skills + workflows dạng cards. |

### Nguyên tắc vận hành

- 🔒 **Zero-Hallucination**: AI bắt buộc trích dẫn từ Knowledge, không được bịa.
- 🛡️ **Zero-Destruction**: Cấm xóa file vĩnh viễn — chỉ di chuyển vào `_Delete/`.
- 📝 **No-Overwrite**: Không ghi đè file của người khác — tạo file mới hoặc append.

---

## 🚀 Cài đặt trên máy mới

### Yêu cầu

- [Antigravity IDE](https://antigravity.dev) (hoặc VS Code / Cursor)
- [Git](https://git-scm.com/) đã cài
- [Node.js](https://nodejs.org/) ≥ 18 (để rebuild dashboard)

### Cách 1: 1-Click Setup (Khuyên dùng)

Sau khi clone hoặc pull repo về máy:

```bash
# macOS / Linux:
./setup.sh

# Windows:
setup.bat
```

Script sẽ tự động:
1. Nhận diện IDE (Antigravity IDE / Cursor / VS Code).
2. Đóng gói & cài đặt Extension mới nhất (`ai-workforce-panel-2.7.0.vsix`).
3. Kích hoạt Git Hook `post-merge` (để mọi lần sau khi gõ `git pull`, extension sẽ tự động cập nhật mà không cần chạy lại setup).
4. Cài đặt các extension hỗ trợ mở tài liệu văn phòng/PDF (`cweijan.vscode-office`).
5. Rebuild Web Dashboard (`dashboard/data.json`).

### Cách 2: Tự động chạy khi mở thư mục trong IDE

Thư mục đã được tích hợp sẵn `.vscode/tasks.json` (`runOn: folderOpen`). Khi bạn mở thư mục `ai-workforce` trong Antigravity IDE hoặc VS Code trên bất kỳ máy nào, IDE sẽ tự động kích hoạt tiến trình cài đặt và cập nhật extension ngầm.

### Cách 3: Đồng bộ tự động sau mỗi lần `git pull`

Nhờ Git Hook `scripts/hooks/post-merge`, mỗi khi bạn gõ:
```bash
git pull origin main
```
Hệ thống sẽ tự động cập nhật extension lên phiên bản mới nhất ngay tức thì.

### Xác nhận cài đặt thành công

Sau khi chạy `auto-setup.sh`, bạn sẽ thấy:

```
📊 AIWF Status:
   Skills:     2
   Workflows:  1
   Knowledge:  1
   Rules:      2

🎉 AI Workforce sẵn sàng!
```

Trong IDE:
- ✅ Sidebar có icon **AI Workforce** (icon grid Samsung-style)
- ✅ Mở `dashboard/index.html` → hiển thị đủ skills + workflows

---

## 🏗️ Kiến trúc KWSR

AIWF được quy hoạch theo nguyên tắc **"Company in a Folder"**:

```
┌─────────────────────────────────────────────────┐
│              AI Workforce (KWSR)                │
├──────────┬──────────┬──────────┬────────────────┤
│ [K]      │ [W]      │ [S]     │ [R]            │
│ Knowledge│ Workflow  │ Skill   │ Rule           │
│          │          │         │                │
│ Nguồn    │ Sổ tay   │ "JD"   │ Rào chắn       │
│ sự thật  │ vận hành │ của AI  │ an toàn        │
│ (SSOT)   │ (I-P-O)  │ agents  │                │
└──────────┴──────────┴──────────┴────────────────┘
```

### Luồng hoạt động

```
User ra lệnh → Agent đọc AGENTS.md (bản đồ tổ chức)
             → Nạp Rules (zero-destruction, zero-hallucination)
             → Phân loại: Workflow hay Skill?
             → Chạy workflow/skill tương ứng
             → Tra Knowledge (SSOT) để lấy dữ liệu thật
             → Xuất output vào thư mục dự án
```

---

## 📂 Cấu trúc thư mục

```
ai-workforce/
│
├── .agents/                          ← 🧠 BỘ NÃO (KWSR)
│   ├── knowledge/                    ← [K] Kho Tri Thức
│   │   └── quan_tri_nhan_su_.../
│   │       ├── metadata.json
│   │       └── artifacts/
│   │           └── bang-luong-level.md
│   │
│   ├── workflows/                    ← [W] Sổ tay Quy trình
│   │   └── W1-chuan-bi-tuyen-dung.md
│   │
│   ├── skills/                       ← [S] Nhân sự số
│   │   ├── boc-tach-cv/
│   │   │   ├── SKILL.md
│   │   │   └── examples/
│   │   ├── boc-tach-pdf/
│   │   │   ├── SKILL.md
│   │   │   ├── icon.svg
│   │   │   └── scripts/
│   │   └── pdf-translate/
│   │       └── SKILL.md
│   │
│   └── rules/                        ← [R] Luật lệ
│       ├── AGENTS.md                 ← Bản đồ tổ chức (always_on)
│       └── R1-zero-destruction.md    ← Bảo toàn dữ liệu (always_on)
│
├── dashboard/                        ← 🖥️ Web Dashboard
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── build_dashboard.js            ← Build: quét .agents → data.json
│
├── extension/                        ← 🔌 IDE Extension (v2.0)
│   ├── package.json
│   ├── extension.js
│   ├── media/
│   └── *.vsix                        ← Extension packages
│
├── scripts/                          ← 🔧 Auto-Setup System
│   ├── auto-setup.sh                 ← Script trung tâm
│   ├── install-hooks.sh              ← Kích hoạt hooks (1 lần)
│   └── hooks/
│       └── post-merge                ← Tự chạy sau git pull
│
├── Tuyen_Dung_*/                     ← 📁 Output dự án
├── manifest.json                     ← Metadata AIWF
├── .gitignore
└── README.md                         ← File này
```

---

## 💼 Sử dụng hàng ngày

### AWF Commands (gõ trong Antigravity Chat)

| Lệnh | Mục đích |
|---|---|
| `/aiwf-setup` | Cài đặt AIWF lần đầu trên máy mới |
| `/aiwf-sync push` | Đẩy thay đổi lên git (auto rebuild + commit + push) |
| `/aiwf-sync pull` | Kéo cập nhật từ git (auto-setup chạy tự động) |

### Kích hoạt Skill / Workflow

**Cách 1 — Sidebar Extension:**
Click icon trên sidebar → click card skill/workflow → trigger tự gửi vào chat.

**Cách 2 — Dashboard:**
Mở `dashboard/index.html` → click card → copy trigger → dán vào chat.

**Cách 3 — Nói trực tiếp:**
Gõ yêu cầu bằng ngôn ngữ tự nhiên trong chat, ví dụ:
- "Bóc tách CV này" → kích hoạt skill `boc-tach-cv`
- "Bóc tách file PDF scan này sang Word" → kích hoạt skill `boc-tach-pdf`
- "Dịch file PDF này sang tiếng Việt" → kích hoạt skill `pdf-translate`
- "Chuẩn bị tuyển dụng vị trí Marketing" → kích hoạt workflow `W1`

### Đồng bộ giữa nhiều máy

```
# Trên máy đã thay đổi:
/aiwf-sync push

# Trên máy cần cập nhật:
/aiwf-sync pull
```

---

## ➕ Thêm nhân viên số mới

### Thêm Skill

1. Tạo thư mục trong `.agents/skills/<tên-skill>/`
2. Tạo file `SKILL.md` với YAML frontmatter:

```markdown
---
name: ten-skill
description: MÔ TẢ NGẮN GỌN skill này làm gì.
trigger: Từ khóa kích hoạt 1, Từ khóa 2, Từ khóa 3
exclusion: KHÔNG dùng cho trường hợp X (dùng skill-khac).
push: Dùng cho MỌI yêu cầu liên quan đến Y.
---

# LÝ LUẬN VÀ TƯ DUY (MINDSET)
- Nguyên tắc hoạt động...

# CÁCH SỬ DỤNG
1. Bước 1...

# TÀI NGUYÊN (RESOURCES)
- Xem `examples/...` để lấy định dạng chuẩn.
```

3. (Tùy chọn) Thêm `examples/`, `templates/` trong thư mục skill
4. Extension tự phát hiện (nhờ FileWatcher)
5. Rebuild dashboard: `node dashboard/build_dashboard.js`

### Thêm Workflow

1. Tạo file `.agents/workflows/<tên-workflow>.md` với frontmatter:

```markdown
---
name: ten-workflow
description: Mô tả quy trình.
---

# Workflow: Tên quy trình (Reverse I-P-O)

## OUTPUT (Khóa trước)
- Tệp output mong muốn...

## INPUT (Truy ngược)
- Từ user: thông tin cần thu thập
- Từ SSOT: tham chiếu knowledge

## PROCESS (Các bước thực thi)
- Bước 1...
- Bước 2...
```

### Thêm Knowledge

1. Tạo thư mục `.agents/knowledge/<tên-knowledge>/`
2. Tạo `metadata.json`:
```json
{
  "id": "ten_knowledge",
  "domain": "Lĩnh vực",
  "subject": "Chủ đề",
  "description": "Mô tả nội dung",
  "last_updated": "2026-08-29"
}
```
3. Tạo `artifacts/` chứa các file `.md` dữ liệu thật

### Icon Mapping (Extension)

Extension đã mapping sẵn icon cho các skill/workflow phổ biến. Thêm mapping mới tại `extension/extension.js` → `ICON_MAP`:

```javascript
const ICON_MAP = {
    'ten-skill': { icon: '🎯', gradient: 'gradient-blue', label: 'Nhãn\\nhiển thị' },
};
```

---

## ⚙️ Auto-Setup & Git Hooks

### auto-setup.sh làm gì?

```
1. Detect IDE (antigravity / cursor / code / code-insiders)
2. Kiểm tra extension đã cài chưa
3. Nếu chưa → tự cài VSIX mới nhất
4. Rebuild dashboard/data.json
5. Kiểm tra git hooks
6. In summary (Skills, Workflows, Knowledge, Rules)
```

### Git hooks hoạt động thế nào?

Sau khi chạy `scripts/install-hooks.sh`:
- Hook `post-merge` được kích hoạt
- Mỗi khi `git pull`, hook tự gọi `auto-setup.sh --quiet`
- Extension tự cài nếu thiếu, dashboard tự rebuild

### Chạy auto-setup thủ công

```bash
bash scripts/auto-setup.sh
```

---

## 🔌 Extension

### Cài đặt thủ công

```bash
# Antigravity IDE
antigravity --install-extension extension/ai-workforce-panel-2.0.0.vsix

# VS Code
code --install-extension extension/ai-workforce-panel-2.0.0.vsix

# Cursor
cursor --install-extension extension/ai-workforce-panel-2.0.0.vsix
```

### Tính năng

- **Sidebar icon grid** (Samsung-style) hiển thị skills + workflows
- **1-Click Run**: Click card → trigger tự gửi vào Antigravity Chat
- **Auto-refresh**: FileWatcher theo dõi `.agents/**/*.md` → tự cập nhật khi thêm/sửa/xóa
- **Refresh thủ công**: Click icon 🔄 trên thanh tiêu đề panel

### Extension tìm dữ liệu ở đâu?

```
1. Ưu tiên: Workspace hiện tại có .agents/ → dùng luôn
2. Fallback 1: ~/.gemini/antigravity-ide/scratch/ai-workforce/.agents/
3. Fallback 2: ~/.gemini/scratch/ai-workforce/.agents/
4. Fallback 3: ~/ai-workforce/.agents/
```

---

## 🖥️ Dashboard

### Mở dashboard

Mở file `dashboard/index.html` trong trình duyệt.

### Rebuild data

```bash
node dashboard/build_dashboard.js
```

Script quét `.agents/skills/` và `.agents/workflows/`, đọc YAML frontmatter, xuất `data.json`.

---

## 🔧 Troubleshooting

### Extension không hiển thị trên sidebar

1. Kiểm tra extension đã cài:
   ```bash
   code --list-extensions | grep ai-workforce
   ```
2. Nếu chưa → cài lại:
   ```bash
   bash scripts/auto-setup.sh
   ```
3. Reload IDE: `Cmd+Shift+P` → "Developer: Reload Window"

### Dashboard không hiển thị skill mới

Chạy rebuild:
```bash
node dashboard/build_dashboard.js
```

### Git hooks không chạy sau git pull

Kiểm tra hooks đã kích hoạt:
```bash
git config core.hooksPath
# Phải trả về: scripts/hooks
```

Nếu chưa → kích hoạt lại:
```bash
bash scripts/install-hooks.sh
```

### Skill mới không hiển thị trên Extension

- Kiểm tra file `SKILL.md` có YAML frontmatter hợp lệ (`---` mở và đóng)
- Kiểm tra thư mục nằm đúng trong `.agents/skills/<tên>/SKILL.md`
- Click icon 🔄 trên panel để refresh

---

## 📄 License

Private repository — Internal use only.
