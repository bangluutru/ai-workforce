# Extension Architecture — Quy tắc tổ chức module

> File này là quy tắc BẮT BUỘC cho bất kỳ AI Agent nào khi sửa đổi extension AIWF.
> Mục đích: **phòng chống extension.js phình to trở lại** sau mỗi lần nâng cấp.

---

## Cấu trúc thư mục

```
extension/
├── extension.js          ← Entry point DUY NHẤT (~55 dòng) — chỉ require + activate/deactivate
├── lib/
│   ├── config.js         ← Hằng số, đường dẫn cố định
│   ├── utils.js          ← Tiện ích nền tảng: parser, finder, escape, format
│   ├── icons.js          ← Bản đồ icon/gradient cho Skills & Workflows
│   ├── scanner.js        ← Quét .agents/ để tìm Skills, Workflows, Catalog
│   ├── pickers.js        ← File picker, notebook picker, language picker, sendToChat
│   └── panel.js          ← WorkforcePanelProvider (Webview UI + message handlers + HTML)
├── media/
│   ├── webview.css       ← Stylesheet cho sidebar webview
│   ├── icon.svg          ← Activity bar icon
│   └── boc-tach-pdf.svg  ← Skill-specific icon
├── package.json          ← Extension manifest ("main": "./extension.js")
├── .vscodeignore         ← Loại trừ *.vsix khỏi package
└── ARCHITECTURE.md       ← File này — quy tắc tổ chức module
```

---

## Quy tắc khi thêm tính năng mới

### 1. KHÔNG ĐƯỢC thêm code trực tiếp vào extension.js

`extension.js` chỉ chứa `activate()` và `deactivate()`.
Mọi logic mới PHẢI được đặt vào module phù hợp trong `lib/`.

### 2. Chọn đúng module để bổ sung

| Loại thay đổi | Module | Ví dụ |
|----------------|--------|-------|
| Đường dẫn / hằng số mới | `lib/config.js` | Thêm path tìm .agents trên Linux |
| Utility function mới | `lib/utils.js` | Thêm hàm parse CSV, format date |
| Icon/gradient cho skill mới | `lib/icons.js` | Thêm entry cho skill `viet-jd` |
| Logic quét file/data mới | `lib/scanner.js` | Quét thêm thư mục `templates/` |
| UI picker / dialog mới | `lib/pickers.js` | Thêm chọn format xuất bản (PDF/DOCX) |
| Xử lý message mới từ webview | `lib/panel.js` | Thêm handler `exportDoc` |
| Render HTML/UI component mới | `lib/panel.js` | Thêm tab mới trong sidebar |

### 3. Khi nào tách module mới

Nếu một trong các module `lib/*.js` vượt quá **500 dòng**, hãy tách thành module con.
Ví dụ: nếu `pickers.js` quá lớn → tách ra `pickers-notebook.js`, `pickers-language.js`.

### 4. Quy tắc CommonJS

- **LUÔN dùng `require()` / `module.exports`** (CommonJS). Không dùng `import`/`export` (ESM).
- **Dependency 1 chiều**: config → utils → icons → scanner → pickers → panel → extension.
  Không được tạo circular dependency.

### 5. Khi thêm Skill mới

Khi thêm 1 skill mới vào `.agents/skills/`:
1. Bổ sung entry vào `ICON_MAP` trong [`lib/icons.js`](file:///Users/tranhaibang/.gemini/antigravity-ide/scratch/ai-workforce/extension/lib/icons.js)
2. Nếu skill cần file picker đặc biệt → bổ sung vào `FILE_FILTER_MAP` trong [`lib/pickers.js`](file:///Users/tranhaibang/.gemini/antigravity-ide/scratch/ai-workforce/extension/lib/pickers.js)
3. Nếu skill cần xử lý message riêng → thêm handler trong [`lib/panel.js`](file:///Users/tranhaibang/.gemini/antigravity-ide/scratch/ai-workforce/extension/lib/panel.js) `resolveWebviewView()`
4. **KHÔNG chạm vào** `extension.js`

---

## Lưu ý khi build .vsix

```bash
cd extension
npx -y @vscode/vsce package --no-dependencies
```

Thư mục `lib/` sẽ tự động được include trong `.vsix` (không bị `.vscodeignore` loại trừ).

---

## Version History

| Phiên bản | Ngày | Thay đổi |
|-----------|------|----------|
| v3.5.0 | 2026-09-02 | Tách extension.js monolithic (1441 dòng) → 6 module trong lib/ |
