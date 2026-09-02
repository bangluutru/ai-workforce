# 🔄 Sync Gemini Notebook → AI Workforce Knowledge

Hệ thống đồng bộ tự động tri thức từ **Gemini Notebook** (trước đây là NotebookLM)
về thư mục `.agents/knowledge/` của AI Workforce, phục vụ làm **Single Source of Truth (SSOT)** cho các Skill.

## Kiến trúc

```
┌─────────────────────────────┐
│      Gemini Notebook        │  (Nghiên cứu & Grounding tài liệu)
│  notebook.google.com/...    │
└──────────────┬──────────────┘
               │  notebooklm-py (unofficial API)
               ▼
┌─────────────────────────────┐
│    sync_notebook.py         │  (Script đồng bộ tự động)
│    → Trích xuất Notes       │
│    → Trích xuất Sources     │
│    → Archive phiên bản cũ   │
└──────────────┬──────────────┘
               │  Ghi file Markdown chuẩn KWSR
               ▼
┌─────────────────────────────┐
│  .agents/knowledge/         │
│    └── <notebook_slug>/     │  ← SSOT cho AI Workforce Skills
│         ├── metadata.json   │
│         └── artifacts/      │
│              ├── notes/     │
│              └── sources/   │
└─────────────────────────────┘
```

## Cài đặt lần đầu (1 lần duy nhất)

### Cách 1: Chạy script tự động
```bash
bash scripts/setup_notebook_sync.sh
```

### Cách 2: Cài thủ công
```bash
# 1. Cài thư viện
pip3 install "notebooklm-py[browser]"

# 2. Cài trình duyệt cho bước login
playwright install chromium

# 3. Đăng nhập Google (mở trình duyệt, chỉ cần 1 lần)
notebooklm login
```

> ⚠️ **Bước `notebooklm login` bắt buộc**: Lệnh này sẽ mở trình duyệt Chromium,
> bạn đăng nhập tài khoản Google có quyền truy cập notebook.
> Session được lưu tại `~/.notebooklm/profiles/default/storage_state.json`.

## Sử dụng

### Đồng bộ notebook mặc định
```bash
python3 scripts/sync_notebook.py
```

### Đồng bộ notebook cụ thể
```bash
python3 scripts/sync_notebook.py --notebook-id cbcf39b2-2f6c-4df3-b6b5-321712bfd453
```

### Liệt kê tất cả notebook trên tài khoản
```bash
python3 scripts/sync_notebook.py --list
```

### Đồng bộ nhiều notebook cùng lúc
```bash
python3 scripts/sync_notebook.py \
  --notebook-id abc123 \
  --notebook-id def456
```

## Cấu hình Notebook mặc định

Mở file `scripts/sync_notebook.py`, sửa biến `DEFAULT_NOTEBOOK_IDS`:

```python
DEFAULT_NOTEBOOK_IDS = [
    "cbcf39b2-2f6c-4df3-b6b5-321712bfd453",  # Notebook chính
    # Thêm ID notebook khác ở đây
]
```

## Bảo mật & An toàn

| Quy tắc | Triển khai |
|---------|-----------|
| **R1: Zero-Destruction** | File cũ được archive vào `_Archive/` trước khi ghi mới |
| **R2: Code Quality** | Không hardcode credentials, session lưu ở `~/.notebooklm/` |
| **KWSR** | Output chuẩn `metadata.json` + `artifacts/*.md` |

## Lưu ý quan trọng

1. **Unofficial API**: Thư viện `notebooklm-py` sử dụng API không chính thức.
   Google có thể thay đổi endpoint bất kỳ lúc nào. Kiểm tra cập nhật:
   ```bash
   pip3 install --upgrade notebooklm-py
   ```

2. **Session hết hạn**: Nếu script báo lỗi auth, chạy lại `notebooklm login`.

3. **Giới hạn**: Tốc độ trích xuất phụ thuộc vào lượng nội dung trong notebook.
   Notebook lớn (>50 sources) có thể mất vài phút.
