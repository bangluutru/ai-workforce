

# LUẬT TỐI CAO: MỌI THAY ĐỔI PHẢI ĐỒNG BỘ ĐƯỢC QUA GIT

> **ĐÂY LÀ NGUYÊN TẮC SỐ 0 — BẤT DI BẤT DỊCH — ƯU TIÊN CAO NHẤT TRONG TOÀN BỘ HỆ THỐNG AIWF.**

---

## TUYÊN BỐ NGUYÊN TẮC

AI Workforce được thiết kế để **hoạt động đồng nhất trên mọi máy**, đồng bộ 100% qua Git.
Bất kỳ thay đổi nào — dù nhỏ nhất — đều **PHẢI** đảm bảo rằng khi `git push` từ máy hiện tại và `git pull` trên máy khác, hệ thống ở máy khác **hoạt động giống hệt** mà không cần bất kỳ bước thủ công nào ngoài:

```
git pull → bash scripts/auto-setup.sh → Reload IDE → Hoạt động 100%
```

---

## CHECKLIST BẮT BUỘC TRƯỚC MỌI THAY ĐỔI

Trước khi thực hiện BẤT KỲ thay đổi nào cho AIWF, Agent **PHẢI** tự hỏi và trả lời 3 câu hỏi sau:

### ❓ CÂU 1: Thay đổi này nằm trong workspace hay ngoài workspace?
- ✅ **Trong workspace** (`ai-workforce/`) → OK, sẽ được git track.
- ❌ **Ngoài workspace** (ví dụ: `~/.gemini/`, `~/.vscode/`, `/Applications/`, `~/Library/`) → **PHẢI có cơ chế tự động cài lại** từ dữ liệu trong workspace (qua `auto-setup.sh`, `post-merge` hook, hoặc SKILL.md instructions).

### ❓ CÂU 2: Sau khi git pull trên máy trắng, thay đổi này có tự kích hoạt không?
- ✅ **Có** → OK.
- ❌ **Không** → PHẢI bổ sung logic vào `scripts/auto-setup.sh` hoặc `scripts/hooks/post-merge` để tự động kích hoạt.

### ❓ CÂU 3: File nào cần được git add/commit?
- Liệt kê rõ ràng tất cả file liên quan.
- Nếu có file binary (VSIX, hình ảnh, font...) → chỉ giữ bản mới nhất, xóa bản cũ khỏi git.

---

## CÁC TRƯỜNG HỢP THƯỜNG GẶP

### Extension IDE (VSIX)
- Source code (`extension/extension.js`, `package.json`, CSS) → **git track**.
- File `.vsix` mới nhất → **git track** (chỉ giữ 1 bản mới nhất).
- `auto-setup.sh` tự build + cài extension vào IDE mỗi khi setup.

### Cấu hình IDE (settings, keybindings)
- KHÔNG lưu vào `~/.gemini/` hay `~/.vscode/`.
- Nếu cần → tạo file trong workspace (ví dụ: `.vscode/settings.json`) để git track.

### Python dependencies
- Liệt kê trong `requirements.txt` → **git track**.
- `auto-setup.sh` tự cài khi setup.

### Knowledge / SSOT
- Nằm trong `.agents/knowledge/` → **git track**.
- KHÔNG lưu dữ liệu tri thức ở nơi khác.

### Scripts, tools, binaries
- Source code → **git track**.
- Binary tạo lại được → **gitignore**, `auto-setup.sh` tự build.
- Binary không tạo lại được → **git track** (kiểm soát kích thước).

---

## VI PHẠM VÀ XỬ LÝ

Nếu Agent phát hiện một thay đổi **KHÔNG THỂ đồng bộ qua Git**:
1. **DỪNG LẠI** — Không tiếp tục thực hiện.
2. **Báo cáo** cho user: nêu rõ file/thay đổi nào nằm ngoài workspace.
3. **Đề xuất giải pháp**: di chuyển vào workspace hoặc bổ sung logic tự động trong `auto-setup.sh`.
4. Chỉ thực hiện khi đã có cơ chế đồng bộ rõ ràng.

---

## TÓM TẮT MỘT DÒNG

> **"Nếu `git pull` trên máy mới không tái tạo được 100% hệ thống → thay đổi đó SAI."**
