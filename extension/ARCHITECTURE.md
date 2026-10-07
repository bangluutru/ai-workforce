# Extension Architecture — Quy tắc tổ chức module

> File này là quy tắc BẮT BUỘC cho bất kỳ AI Agent nào khi sửa đổi extension AIWF.
> Mục đích: **phòng chống extension.js phình to trở lại** sau mỗi lần nâng cấp.

---

## Cấu trúc thư mục

```
extension/
├── extension.js          ← Entry point DUY NHẤT (~65 dòng) — chỉ require + activate/deactivate
├── lib/
│   ├── config.js         ← Hằng số, đường dẫn cố định
│   ├── frontmatter.js    ← Parser YAML frontmatter thuần (không cần vscode), dùng chung với dashboard/
│   ├── utils.js          ← Tiện ích nền tảng: parser, finder, escape, format
│   ├── icons.js          ← Bản đồ Lucide icon & semantic category màu
│   ├── scanner.js        ← Quét .agents/ để tìm Skills, Workflows, Catalog
│   ├── pickers.js        ← File picker, notebook picker, language picker, sendToChat
│   ├── panel.js          ← WorkforcePanelProvider (Webview Sidebar + message handlers)
│   └── interactive_panel.js ← Interactive Skill Pattern: Webview Editor Tab & State Bridge
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
| Icon/màu cho skill mới | `lib/icons.js` | Thêm entry Lucide icon & semantic category |
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
2. Khai báo `needs_file` (true = tệp là bắt buộc, nguồn "tệp" lên đầu; false = "Thực hiện trực tiếp" lên đầu) và `file_filter` (`pdf` | `scan` | `doc` | `office` | `media` | `any`) trong frontmatter SKILL.md. Cần bộ lọc mới / chọn nhiều tệp / bỏ qua doc_ingest → bổ sung `FILE_FILTER_MAP`, `MULTI_SELECT_SKILLS`, `NATIVE_INPUT_SKILLS` trong [`lib/pickers.js`](file:///Users/tranhaibang/.gemini/antigravity-ide/scratch/ai-workforce/extension/lib/pickers.js)
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
| v3.6.0 | 2026-09-06 | Bổ sung module interactive_panel.js hỗ trợ Interactive Skill Pattern (ISP v1.0) |
| v3.6.1 | 2026-10-03 | Bộ lọc tệp theo skill (pdf/scan/doc/office/media), tôn trọng `needs_file`, chọn nhiều tệp, hướng dẫn chạy `scripts/doc_ingest.py`, parser frontmatter hỗ trợ block scalar gập/nguyên văn (lib/frontmatter.js) |
| v3.6.2 | 2026-10-03 | Tối ưu hóa icon và hiển thị giao diện control panel |
| v3.7.0 | 2026-10-07 | Chuyển đổi visual language sang Phosphor Duotone (thử nghiệm) |
| v3.8.0 | 2026-10-07 | Trở về chuẩn Lucide Professional Monochrome: Icon monochrome stroke 1.9, bảng màu kiềm chế Slate/Monochrome (#475569 / #94a3b8), nhấn màu danh mục thứ cấp tại filter chip & badge, triệt tiêu 100% emoji. |
| v3.8.1 | 2026-10-07 | Tối ưu hóa không gian hiển thị (Compact Density): Khôi phục kích thước khung chứa skill cao 40px (padding 5x8px, gap 7px) và icon 26x26px (SVG 15px) như ban đầu trước khi thử nghiệm Phosphor, loại bỏ khoảng trống thừa, căn chỉnh action play inline gọn gàng. |

---

## Hệ thống Visual Language: Lucide Professional Monochrome

Giao diện AI Workforce Control Panel áp dụng triết lý thiết kế công cụ kỹ thuật chuyên nghiệp (Developer Tool / AI Operating Console):
- **Lucide Icon System (`fill="none" stroke="currentColor" stroke-width="1.9"`)**: Đường nét hình học thanh mảnh, chính xác, nhất quán cho toàn bộ Skill, Workflow và UI Control Panel (15px trong container siêu gọn 26x26px, thẻ cao 40px).
- **Monochrome & Restrained Color Palette**: Loại bỏ hoàn toàn hệ màu sặc sỡ kiểu Odoo hay App Launcher. Khung icon mặc định dùng tông Slate trung tính (`#475569`, dark mode `#94a3b8`) với nền xám mờ (`rgba(71,85,105, 0.07)`) và viền thanh lịch.
- **Secondary Category Semantic Accent**: Màu sắc phân nhóm chỉ đóng vai trò thông tin thứ cấp, hiện diện chủ đạo tại Filter Pills và Category Badges:
  - `content` (`#7C3AED`): Sáng tạo nội dung, copywriting, đồ họa, landing page.
  - `document` (`#2563EB`): Xử lý tài liệu, bóc tách PDF, dịch thuật, đọc sâu.
  - `legal` (`#D97706`): Pháp luật Việt Nam & Nhật Bản, thuế, tài chính kế toán.
  - `technical` (`#0F766E`): Kiểm định ứng dụng, bảo mật, mã nguồn.
  - `system` (`#475569`): Sổ tay, quy trình vận hành, chuẩn hóa workspace.
- **Visual Hierarchy Tối Ưu**: Ưu tiên đọc lướt: (1) Tên kỹ năng → (2) Danh mục/Mô tả → (3) Icon bổ trợ → (4) Launch action. Không để icon hay màu sắc lấn át tên kỹ năng.
- **VS Code Codicons**: Sử dụng độc quyền trên các bề mặt native của VS Code (`quickPickIcon`, command palette).
- **Zero Emojis trong Control Panel UI**: Triệt tiêu toàn bộ emoji trên thanh điều hướng, nút bấm, empty state, badges.
- **Tuân thủ Tuyệt đối R0, R7 & CSP**: 100% offline, embedded SVG thuần, zero CDN, zero external dependencies, tương thích hoàn toàn CSP của VS Code.
