# AI WORKFORCE — Hướng dẫn cho Claude

File này Claude Code tự nạp khi mở thư mục `ai-workforce`. Đây là bản tương đương của `GEMINI.md` (dành cho Antigravity). Hai bản dùng chung một bộ skill, luật và tri thức trong `.agents/`; không nhân bản nội dung.

## Bố cục

| Thư mục | Vai trò |
|---|---|
| `.agents/skills/<skill>/` | Skill gốc (SKILL.md, scripts, standards, references, templates). Nguồn sự thật duy nhất |
| `.agents/skills/_shared/` | Engine dùng chung (danh mục: `_shared/ENGINES.md`) |
| `.agents/rules/` | Luật R0–R7 và `AGENTS.md` (bản đồ tổ chức, ma trận định tuyến) |
| `.agents/workflows/` | Quy trình nhiều skill (W1 Phòng Media, ...) |
| `.agents/knowledge/` | Kho tri thức SSOT |
| `claude-skills/skills/` | Bộ skill Claude (bản để sửa và commit): 19 skill bọc skill gốc + `dieu-phoi` (điều phối) + `phong-media` |
| `claude-skills/skill-map.json` | Hợp đồng phối hợp: tầng, đầu vào, đầu ra, nhận từ, giao cho |
| `claude-skills/sync_from_antigravity.py` | Sinh lại bộ skill Claude từ skill gốc và cài vào `.claude/skills/` (nơi Claude Code nạp skill) |

## Dùng skill

- Một việc, một skill: dùng skill tương ứng (Claude Code nạp từ `.claude/skills/`, bản gốc ở `claude-skills/skills/`). Skill Claude sẽ bảo đọc `.agents/skills/<skill>/SKILL.md`; làm đúng từng bước trong đó.
- Việc cần từ 2 skill trở lên: dùng skill `dieu-phoi`.
- Chọn skill theo loại đầu vào + ý định + thành phẩm mong muốn. Khi hai skill gần nhau, xem quy tắc phân định ở `.agents/rules/AGENTS.md` mục 8B.
- Thêm hoặc sửa skill gốc trong `.agents/skills/`, rồi chạy `python3 claude-skills/sync_from_antigravity.py --install`. Skill viết tay trong `claude-skills/skills/` (không có dòng `AUTO`) không bị script ghi đè. Luôn sửa trong `claude-skills/`, không sửa bản cài trong `.claude/skills/`.

## Đổi công cụ (skill gốc viết cho Antigravity)

| Skill gốc nói | Claude làm |
|---|---|
| `search_web` | WebSearch |
| `read_url_content`, mở trang nguồn | WebFetch |
| `view_file` (kể cả xem ảnh chụp, khung hình) | Read |
| `run_command`, chạy lệnh | Bash |
| `generate_image` | Không có công cụ tạo ảnh tích hợp: dùng engine ảnh có trong skill nếu có; nếu không, làm theo phương án dự phòng skill gốc ghi (mảng màu, typography, SVG) hoặc ghi mô tả ảnh và báo người dùng |
| "Agent Antigravity", "Gemini 3.8", "LLM tích hợp trong IDE" | Chính Claude trong phiên này |
| "Multi-Agent", "chia lô dịch song song" | Subagent (Agent tool), mỗi subagent nhận đúng phần việc và file đầu vào |
| `GEMINI.md` | File này |

## Luật bắt buộc (chi tiết trong `.agents/rules/`)

- **R0 Git là nguồn đồng bộ.** Mọi thay đổi cho AIWF phải tái tạo được sau `git pull` trên máy khác. Bộ skill Claude nằm trong repo (`claude-skills/`, `CLAUDE.md`) vì lý do này; trên máy mới chạy `python3 claude-skills/sync_from_antigravity.py --install` một lần. Chỉ commit khi người dùng yêu cầu.
- **R1 Không phá dữ liệu.** Không xóa khi chưa có bản sao; không xả rác vào workspace.
- **Zero external LLM API.** Năng lực suy luận là của chính Claude. Không gọi API mô hình ngôn ngữ bên ngoài, không đòi API key cho việc đó. API sản phẩm (Landing Hub) và API dữ liệu/media (Pexels, Pixabay) được dùng khi nghiệp vụ cần.
- **Không bịa dữ liệu.** Chính sách, giá, quy trình phải dựa trên `.agents/knowledge/` hoặc nguồn tra được; thiếu thì gắn `[CẦN XÁC MINH]` hoặc nói không đủ dữ liệu.
- **Tự chạy đến khi xong.** Không dừng giữa chừng xin phép; chỉ dừng khi lỗi không tự phục hồi được, thiếu thông tin bắt buộc, hoặc trước bước công khai / không đảo ngược được (đăng bài, gửi ra ngoài, xóa).
- **R4** chuẩn skill, chấm bằng `python3 scripts/audit_skill.py`. **R5** nội dung tiếp thị qua `scripts/claim_guard.py`. **R6** bảo toàn bố cục PDF. **R7** tra `_shared/ENGINES.md` trước khi viết code mới, kiểm bằng `python3 scripts/check_shared_reuse.py`.
- **Không ghi đè thành phẩm của skill khác**; sửa thì tạo bản mới.

## Đọc tệp người dùng

Không đọc thẳng tệp nhị phân (DOC/DOCX, XLS/XLSX, PPT/PPTX, PDF, EPUB, ODT, RTF). Chuyển trước:

```bash
.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<tên_việc> --json
```

Rồi đọc `source.md` và `manifest.json`. Mã thoát: `0` đủ; `3` có trang scan → xem ảnh trong `ocr_pages/` (tài liệu scan dài → skill `boc-tach-pdf`); `2` không đọc được → hỏi người dùng đúng điều trong `manifest.message`; `4` thiếu phụ thuộc → làm theo `manifest.message`. Ảnh (PNG, JPG) thì Read trực tiếp được.

## Đường dẫn

| Placeholder | Giá trị |
|---|---|
| `<workspace>` | Gốc repo (thư mục chứa file này) |
| `<skill_dir>` | `.agents/skills/<skill>/` |
| `<process_dir>` | `_process/<tên_việc>/` (đã gitignore) |
| `<output_dir>` | Nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/` |

Thành phẩm không lưu vào gốc repo.

## Môi trường

Lần đầu trên máy mới, hoặc khi script báo thiếu thư viện:

```bash
python3 -c "import docx, fitz, pdfplumber" 2>/dev/null || pip3 install -r requirements.txt
bash scripts/auto-setup.sh --quiet
```

Mô hình giọng đọc (VieNeu-TTS, Kokoro) được `auto-setup.sh` tải về `_shared/models/` (gitignored). Sổ tay người dùng: `docs/AIWF_USER_HANDBOOK.md`.
