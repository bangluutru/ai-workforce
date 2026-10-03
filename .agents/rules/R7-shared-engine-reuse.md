# LUẬT R7: TÁI SỬ DỤNG ENGINE DÙNG CHUNG (SHARED-ENGINE-FIRST)

> **Phạm vi:** mọi skill hiện có và mọi skill mới trong `.agents/skills/`, mọi script trong `scripts/`.
> **Mục tiêu:** một năng lực chỉ được hiện thực ở **một nơi duy nhất**; skill gọi lại thay vì chép/viết lại → AIWF không phình dung lượng, sửa lỗi một lần là mọi skill được hưởng.
> **Công cụ cưỡng chế:** `scripts/check_shared_reuse.py` (chạy trong `scripts/audit_skill.py` và git pre-commit hook).

---

## 1. NGUYÊN TẮC

1. **Reuse-before-build.** Trước khi viết bất kỳ engine/hàm/asset nào cho skill, Agent PHẢI tra
   [`.agents/skills/_shared/ENGINES.md`](../skills/_shared/ENGINES.md) (danh mục cho người & agent) hoặc
   `.agents/skills/_shared/engines.json` (danh mục máy đọc). Đã có → **gọi lại**, không viết lại.
2. **Một năng lực = một chủ sở hữu.** Mỗi engine trong `engines.json` có đúng một `module` sở hữu. Mã có
   chữ ký (signature) của engine đó xuất hiện ở nơi khác = vi phạm.
3. **Cấm sao chép file giữa các skill.** Hai file giống nhau từng byte ở hai skill khác nhau = vi phạm cứng.
   Ghi chú kiểu *"sửa ở một nơi thì chép sang nơi kia"* là dấu hiệu phải chuyển file vào `_shared/`.
4. **Asset nặng dùng chung.** Font, model, template nhị phân dùng ≥ 2 skill → đặt ở `_shared/fonts/`,
   `_shared/models/` (model tải về lúc cài, không commit), không nhân bản theo skill.
5. **Skill = quy trình + tri thức miền.** Skill chứa SKILL.md, references, templates và mã **đặc thù miền**.
   Mã hạ tầng (đọc file, ffmpeg, TTS, ASS, render PDF, xuất DOCX, kiểm tra phụ thuộc…) thuộc `_shared/`.

---

## 2. CÂY QUYẾT ĐỊNH KHI THÊM CODE

```
Cần năng lực X
 ├─ X có trong engines.json?            → GỌI LẠI (import / CLI của _shared). Hết.
 ├─ Gần giống engine Y nhưng thiếu tham số? → MỞ RỘNG Y trong _shared (thêm tham số, giữ tương thích). Hết.
 ├─ X là hạ tầng chung, hoặc đã/ sẽ có ≥ 2 skill cần? → TẠO MỚI trong _shared/<domain>/ + đăng ký engines.json.
 └─ X đặc thù một miền (vd: biểu thuế TNCN, tra mã HS Nhật) → để trong skill/scripts/, KHÔNG đăng ký.
```

Khi skill thứ hai cần một hàm đang nằm trong skill khác → **thăng cấp (promote)** hàm đó vào `_shared/`
trong cùng commit, không import chéo `skills/A/scripts` từ `skills/B`.

---

## 3. CẤU TRÚC `_shared/`

```
.agents/skills/_shared/
├── ENGINES.md            ← danh mục engine (đọc trước khi viết code)
├── engines.json          ← registry máy đọc: id, module, cli, capabilities, used_by, signatures
├── bootstrap.py          ← add _shared vào sys.path từ mọi script skill
├── doc_ingest_bridge.py  ← đọc tệp người dùng (DOCX/PDF/XLSX…)
├── output_manager.py     ← đường dẫn <output_dir>
├── deps.py               ← kiểm tra phụ thuộc hệ thống/Python dùng chung
├── docx/                 ← xuất DOCX (báo cáo pháp lý…)
├── pdf/                  ← trích xuất asset PDF, kiểm định toạ độ/bố cục/dịch sót (engine dàn trang dịch ở skill dich-thuat)
├── media/                ← ffmpeg, TTS (VieNeu, Kokoro), ASS/karaoke, ducking
├── fonts/                ← font dùng chung (OFL)
└── models/               ← (gitignored) model tải về bởi scripts/auto-setup.sh
```

**Cách gọi từ script trong skill:**

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))   # .agents/skills/_shared
from media.tts import synthesize            # ví dụ
```

**Cách gọi từ SKILL.md:** ghi thẳng đường dẫn CLI của `_shared`, ví dụ
`python3 .agents/skills/_shared/docx/legal_report.py --input report.md`.
Shim (file mỏng trong skill chỉ chuyển tiếp sang `_shared`) chỉ được giữ **tạm** để tương thích ngược, phải có
dòng `# R7-SHIM → <đích>` ở đầu file và tối đa 30 dòng.

---

## 4. ENGINE BỊ CẤM

| Engine | Lý do | Thay bằng |
|---|---|---|
| `edge-tts` / `edge_tts` (Microsoft Edge Read Aloud) | Dịch vụ trực tuyến không có giấy phép thương mại rõ ràng — rủi ro bản quyền giọng đọc | `_shared/media/tts.py`: **VieNeu-TTS** (vi, vi-en) và **Kokoro** (en, ja), chạy offline |

Danh sách cấm được khai báo trong `engines.json → banned` và quét tự động.

---

## 5. CƯỠNG CHẾ TỰ ĐỘNG

`python3 scripts/check_shared_reuse.py` (mã thoát 0 = đạt, 1 = vi phạm, 2 = lỗi chạy):

| Mã | Kiểm tra | Mức |
|---|---|---|
| R7-DUP | File giống từng byte ở ≥ 2 skill (hoặc skill ↔ `_shared`, skill ↔ `scripts/`) | FAIL |
| R7-SIG | Chữ ký của engine đã đăng ký xuất hiện ngoài module sở hữu | FAIL |
| R7-BAN | Dùng engine bị cấm | FAIL |
| R7-ASSET | Font/model nhị phân trùng hash giữa các thư mục | FAIL |
| R7-NEAR | File cùng tên ở ≥ 2 skill, giống ≥ 80 % (khả năng fork) | WARN |
| R7-SHIM | Shim quá 30 dòng hoặc thiếu dòng `# R7-SHIM` | WARN |

- `scripts/audit_skill.py` trừ điểm L3 và chặn chứng nhận nếu skill có lỗi R7 mức FAIL.
- Git pre-commit hook (`bash scripts/install-hooks.sh`) chạy `check_shared_reuse.py --quiet` và chặn commit có FAIL.

---

## 6. CHECKLIST KHI TẠO / SỬA SKILL

1. ✅ Đã đọc `_shared/ENGINES.md` và liệt kê engine sẽ dùng lại trong SKILL.md (mục "Engine dùng chung").
2. ✅ Không có file nào chép từ skill khác; hàm cần dùng chung đã được promote vào `_shared/`.
3. ✅ Engine mới dùng chung đã đăng ký `engines.json` (id, module, cli, capabilities, used_by, signatures) và cập nhật `ENGINES.md`.
4. ✅ `python3 scripts/check_shared_reuse.py` = 0 FAIL.
5. ✅ `python3 scripts/audit_skill.py <skill>` ≥ 85 điểm.
