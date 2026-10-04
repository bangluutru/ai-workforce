---
name: phu-de
display-name: Tạo Phụ Đề
description: >-
  Tạo, bóc tách và biên tập phụ đề video (SRT, ASS, hardsub MP4) với forced alignment từng từ, phân đoạn ngữ nghĩa CPL/CPS, dịch thuật phụ đề song ngữ và phòng dựng visual review trực quan.
  USE WHEN: Người dùng cần tạo phụ đề, làm sub song ngữ, dịch phụ đề, hoặc dập phụ đề (hardsub) vào video có sẵn.
  DO NOT USE WHEN: Cần sản xuất video tổng thể từ kịch bản/stock media (dùng 'video-studio'), chỉ cần lồng tiếng/thuyết minh audio track (dùng 'long-tieng'), hoặc dịch tài liệu văn bản tĩnh PDF/Docx (dùng 'ejv-translate').
trigger: Tạo phụ đề, làm phụ đề video, dịch phụ đề, auto subtitle, hardsub, xuất phụ đề srt ass
category: content
needs_file: false
file_filter: media
---

# Kỹ Năng Phụ Đề Video Thông Minh & Phòng Dựng Tương Tác (phu-de v2.0)
## Chuẩn Google Antigravity 2.0 & Mô Hình Lõi Gemini 3.8 Multi-Agent

<goal>
Tạo quy trình xử lý phụ đề video khép kín và chuyên nghiệp từ file video đầu vào: bóc tách âm thanh, nhận diện giọng nói chính xác từng từ (word-level alignment), phân đoạn câu tự nhiên theo chuẩn CPL/CPS, tối ưu câu dịch bằng Gemini, khởi chạy phòng dựng tạm thời (Temporary Web UI) để người dùng xem preview và chỉnh sửa trực quan, cho phép tương tác AI Edit hai chiều có snapshot Undo an toàn, và xuất file thành phẩm (SRT, ASS, MP4 hardsub) ra thư mục chỉ định.
</goal>

---

<context>
Kỹ năng vận hành theo triết lý phân định rõ ràng giữa hai động cơ:
1. **Deterministic Media Tools**: FFmpeg, faster-whisper, pysubs2, ASS generator, libass. Chịu trách nhiệm trích xuất âm thanh, tính toán mốc thời gian, căn lề pixel và encode video. Tuyệt đối không dùng LLM cho các tác vụ này.
2. **Cognitive Reasoning Engine**: Antigravity nội bộ (Gemini 3.8) chịu trách nhiệm sửa lỗi chính tả từ đồng âm (homophones), chuẩn hóa thuật ngữ chuyên ngành, tối ưu hóa độ dài câu dịch cho phụ đề (ngắn gọn, xúc tích, giữ trọn ý nghĩa), và thực thi các chỉ thị hiệu chỉnh từ người dùng trong vòng lặp AI Edit loop.
3. **Nguyên tắc Zero-Loss & Evidence Verifier**: Bảo toàn 100% mốc thời gian âm thanh gốc (Zero-Loss timing drift), đối chiếu bằng chứng phát âm chính xác trước khi xuất bản.
</context>

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Kỹ năng này chạy hoàn toàn bằng khả năng tích hợp sẵn của Antigravity IDE (Gemini 3.8) và các công cụ offline cục bộ.
> - TUYỆT ĐỐI KHÔNG gọi REST API bên ngoài (OpenAI API, Anthropic API, Gemini REST API ngoài) hoặc yêu cầu API key để vận hành.
> - Toàn bộ Python scripts chỉ phục vụ xử lý media, quản lý trạng thái dự án và làm cầu nối HTTP server cục bộ.
> - Khi được kích hoạt, skill PHẢI tự chạy liên tục (Autonomous Full-Run) từ bước nhận video đến khi mở phòng dựng tạm thời, không tự dừng dở dang để xin phép.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

Agent PHẢI xác định đường dẫn lưu file trước khi thực hiện quy trình:

| Placeholder | Quy ước xác định đường dẫn thực tế |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<process_dir>` | Thư mục tạm xử lý: `<workspace>/_process/subtitles_[project_id]/` (đã nằm trong `.gitignore`) |
| `<skill_dir>` | Thư mục kỹ năng: `<workspace>/.agents/skills/phu-de/` |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi file thành phẩm xuất bản (video MP4 đã khắc phụ đề, file `.srt`, `.ass`) PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/` hoặc nơi user chỉ định).
> - Toàn bộ file tạm (audio WAV, raw transcript, snapshots revision, `project.json`) PHẢI lưu trong `<process_dir>` (`_process/subtitles_[id]/`).
> - TUYỆT ĐỐI KHÔNG lưu file video hoặc phụ đề thành phẩm trực tiếp vào thư mục gốc của repository Git để tránh làm phình dung lượng codebase.

---

## 🏗️ Bảng Tọa độ Đầu vào & Phân luồng (Intake Coordinates)

Trước khi thực thi, Agent phân loại tọa độ đầu vào của người dùng theo bảng sau:

| Trục Tọa độ | Giá trị xác định | Hành vi mặc định nếu thiếu |
|---|---|---|
| **1. File Video Nguồn** | Đường dẫn tuyệt đối file MP4 / MOV / MKV / WebM | Yêu cầu người dùng cung cấp đường dẫn video |
| **2. Ngôn ngữ Gốc (Source)** | `auto`, `en`, `vi`, `ja`, v.v. | `auto` (faster-whisper tự động phát hiện) |
| **3. Ngôn ngữ Đích (Target)** | `vi`, `en`, `ja`, v.v. | `vi` (Tiếng Việt nếu nguồn là tiếng nước ngoài) |
| **4. Chế độ Hiển thị (Mode)** | `bilingual` (Song ngữ) hoặc `monolingual` (Đơn ngữ) | `bilingual` nếu nguồn khác đích; `monolingual` nếu cùng ngôn ngữ |
| **5. Mẫu Kiểu Dáng (Preset)** | `modern_bottom`, `tiktok_box`, `cinema_classic`, `top_banner` | `modern_bottom` (Hiện đại dưới đáy, nền mờ 35%) |

---

<instructions>
## QUY TRÌNH THỰC THI (SOP AUTONOMOUS FULL-RUN, v2)

> Chất lượng phụ đề = (1) nhận dạng đúng chữ + (2) ngắt câu tự nhiên + (3) dịch gọn theo tốc độ đọc
> + (4) hiển thị dễ đọc. Script lo phần đo đạc/thời gian; **agent (Gemini) lo phần ngôn ngữ** qua các
> "lô việc" JSON do `subtitle_workbench.py` xuất ra và kiểm tra khi nạp lại. Không bỏ bước nào.
> Ký hiệu: `S=.agents/skills/phu-de/scripts`, `PD=<process_dir>`.

### BƯỚC 0 — Môi trường
`python3 $S/check_deps.py` → phải có ffmpeg **có libass** (macOS: `brew install ffmpeg-full`), faster-whisper,
pysubs2, pillow, mô hình `large-v3-turbo` (tự tải lần đầu ~1.6 GB).

### BƯỚC 1 — Audio + thông số video
`python3 $S/extract_audio.py --video "<video>" --output-wav $PD/audio.wav --meta-json $PD/video_meta.json`

### BƯỚC 2 — Nhận dạng 2 lượt (glossary)
1. Lập **glossary** từ mọi thứ biết trước: tên file/tiêu đề video, lời người dùng, lĩnh vực (tên riêng,
   thương hiệu, thuật ngữ, cách viết đúng). Ví dụ: `"eTax Mobile, định danh điện tử, giảm trừ gia cảnh"`.
2. Lượt 1: `python3 $S/transcribe_align.py --audio $PD/audio.wav --output $PD/raw_transcript.json --glossary "<glossary>" [--language vi|en|ja]`
   (mặc định `large-v3-turbo`; **cấm dùng `base`/`small` cho sản phẩm** — đo thực tế: tiếng Việt sai 16.5% với base so với 5% với large-v3-turbo).
3. Đọc nhanh toàn văn transcript (`segments[].text`). Thấy tên riêng/thuật ngữ bị nghe sai lặp lại → bổ sung
   glossary và chạy lại lượt 2 (rẻ: ~0.5× thời lượng video). Đo thực tế: glossary sửa hết lỗi thuật ngữ
   (ETAF→eTax, điện danh→định danh, 定管→定款, 交渉役場→公証役場).

### BƯỚC 3 — Phân đoạn theo câu
`python3 .agents/skills/_shared/media/semantic_segmenter.py -i $PD/raw_transcript.json -o $PD/segmented_subtitles.json --max-lines <2|1>` (engine dùng chung — Luật R7)
- Đơn ngữ: `--max-lines 2` (≤ 2 dòng × 42 ký tự; CJK 2 × 16). Song ngữ: `--max-lines 1` (mỗi ngôn ngữ 1 dòng).
- Thuật toán ngắt tại ranh giới câu/mệnh đề, gộp mảnh mồ côi, tự kéo dài thời gian hiển thị đủ đọc
  (≥ 1.0 s, ≤ 17 CPS Latin / 7 CPS CJK), khép khoảng hở < 0.5 s để không chớp.

### BƯỚC 4 — Khởi tạo dự án
`python3 $S/subtitle_workbench.py init --meta $PD/video_meta.json --segments $PD/segmented_subtitles.json --process-dir $PD --source-lang <src> --target-lang <tgt> [--mode bilingual|monolingual|source_only] --preset modern_bottom --glossary "<glossary>"`
(Video dọc 9:16 tự dùng 32 ký tự/dòng và đẩy phụ đề lên khỏi vùng UI mạng xã hội.)

### BƯỚC 5 — Ba lượt ngôn ngữ của agent (theo đúng thứ tự)
Mỗi lượt: `export` → mở từng `$PD/tasks/<task>_NN.json`, đọc `instructions`, điền trường `"output"` →
`apply --input <file>`. Lỗi kiểm tra → sửa đúng chỗ báo rồi `apply` lại.
1. **reflow** (`export --project $PD/project.json --task reflow`): ngắt lại phụ đề thành ý trọn vẹn và đặt `\n`
   ngắt dòng. KHÔNG đổi chữ (script so từng ký tự và tự tính lại thời gian từ timestamp từng từ).
   Quy tắc: không tách từ ghép tiếng Việt ("ứng dụng", "khai báo", "chăm sóc"), tên riêng, số + đơn vị;
   không để "của/các/những/the/of/to..." cuối dòng; dòng trên ≤ dòng dưới; không phụ đề 1–2 từ.
2. **proofread** (`--task proofread`): sửa lỗi nhận dạng theo ngữ cảnh toàn bài + glossary (dấu tiếng Việt,
   đồng âm, tên riêng, chữ Hán sai, số liệu). Chỉ trả về câu có sửa. Không chắc → thêm `[CẦN XÁC MINH]`.
3. **translate** (chỉ khi `target ≠ source`, `--task translate`): dịch theo ý cả đoạn, mỗi câu ≤ `max_chars`
   (giới hạn tính từ thời lượng × tốc độ đọc). Kỹ thuật rút gọn: bỏ từ đệm/lặp, dùng từ ngắn, đổi cấu trúc
   bị động→chủ động, giữ tên riêng + số. Xưng hô nhất quán toàn video (mình–các bạn / tôi–quý vị...).
   Bản dịch quá dài bị cảnh báo khi apply → rút gọn rồi apply lại.

### BƯỚC 6 — Kiểm định (lặp tới khi đạt)
1. `python3 $S/subtitle_workbench.py qa --project $PD/project.json --json $PD/qa.json` → sửa mọi **FAIL**
   (chưa dịch, quá số dòng, chồng lấn, dấu "—"); xử lý WARN: CPS cao → rút gọn bản dịch; dòng kết thúc bằng
   từ chức năng → đặt lại `\n`; còn `[CẦN XÁC MINH]` → nghe lại đoạn đó hoặc báo người dùng.
   Sửa nhỏ: chỉnh `project.json` trực tiếp (giữ `start/end`) hoặc chạy lại lượt tương ứng.
2. `python3 $S/subtitle_workbench.py preview --project $PD/project.json --frames 6` → **MỞ ẢNH**
   `$PD/preview_grid.jpg`: dấu tiếng Việt đủ, không tràn khung, không che mặt/chữ có sẵn trong video
   (nếu che → preset `top_banner` hoặc tăng `margin_v`), tương phản đọc được trên nền sáng lẫn tối.

### BƯỚC 7 — Phòng dựng tương tác (tùy chọn khi người dùng muốn chỉnh tay)
Extension AIWF tự mở Webview khi thấy `$PD/project.json`; hoặc
`python3 $S/local_bridge_server.py --project "$PD/project.json"`. Local Action (sửa chữ, style, split/merge)
không tốn token; Agent Action: chỉ sửa đúng các segment được chọn trong `project.json`, giữ `start/end`.

### BƯỚC 8 — Xuất bản
- File phụ đề: `python3 $S/subtitle_workbench.py export-subs --project $PD/project.json --output-dir <output_dir>` → `.srt`, `.ass`, `.vtt`.
- Hardsub: `python3 $S/render_video.py --project $PD/project.json --output-dir <output_dir>` → `<tên>_subtitled.mp4`.
- Kiểm chứng: `ffprobe` thời lượng MP4 = video gốc; trích 1 khung hình giữa video có phụ đề và nhìn.
</instructions>

---

<constraints>
## NĂM ĐIỀU CẤM TUYỆT ĐỐI (5 ABSOLUTE BANS - RULE R4 & R2)
1. ❌ **CẤM ĐÒI HỎI EXTERNAL API KEY:** 100% logic AI do Antigravity đảm nhiệm; các công cụ media là offline deterministic. Cấm gọi API ngoài.
2. ❌ **CẤM XUẤT FILE THÀNH PHẨM VÀO CODEBASE:** File video MP4, SRT, ASS bắt buộc xuất ra `<output_dir>` (`~/Downloads/AIWF_Output/`), cấm ghi bừa bãi vào root repo.
3. ❌ **CẤM LÀM LỆCH MỐC THỜI GIAN KHI AI SỬA CHỮ:** Khi thực hiện chỉ thị sửa câu, viết lại, rút gọn, cấm tự ý thay đổi `start` và `end` trừ khi có lệnh split rõ ràng.
4. ❌ **CẤM DỪNG DỞ DANG ĐỂ XIN PHÉP:** Phải tự động chạy liên tục qua các bước bóc tách, nhận dạng, tạo project và mở phòng dựng.
5. ❌ **CẤM VĂN PHONG MÙI AI TIẾNG VIỆT:** Trong câu dịch phụ đề, cấm dùng em dash dài `—` (thay bằng gạch nối ` - `), cấm Oxford comma `, và`, cấm từ sáo rỗng.
</constraints>

---

<working_ledger>
## ĐỊNH DẠNG LƯU VẾT TIẾN TRÌNH VẬT LÝ
Toàn bộ tiến trình làm việc được lưu vết trong thư mục `<process_dir>`:
- `audio.wav`: File âm thanh bóc tách 16kHz mono.
- `video_meta.json`: Báo cáo thông số video từ ffprobe.
- `raw_transcript.json`: Danh sách từ kèm word-level timestamps.
- `segmented_subtitles.json`: Các phân đoạn phụ đề chuẩn CPL/CPS.
- `tasks/reflow_NN.json`, `proofread_NN.json`, `translate_NN.json`: lô việc ngôn ngữ của agent (đã điền `output`).
- `qa.json`, `preview_grid.jpg`: bằng chứng kiểm định.
- `project.json`: Nguồn sự thật duy nhất (Single Source of Truth).
- `snapshots/rev_001.json`, `rev_002.json`...: Bản ghi lịch sử cho cơ chế Undo/Redo.
- `temp_render.ass`: File ASS trung gian phục vụ FFmpeg libass render.
</working_ledger>

---

<quality_gate>
## CHECKLIST TỰ THẨM ĐỊNH CHẤT LƯỢNG (QUALITY GATE)
1. ✅ ASR bằng `large-v3-turbo` (hoặc `large-v3`) có glossary; đã đọc toàn văn và chạy lượt 2 nếu cần.
2. ✅ Đã chạy đủ reflow → proofread → (translate); `qa` **0 FAIL**, mọi WARN còn lại có lý do.
3. ✅ Thời gian: không chồng lấn; mỗi phụ đề ≥ 0.8 s; ≤ 20 CPS (Latin) / 9 CPS (CJK) cho dòng chính.
4. ✅ Trình bày: ≤ 2 dòng (song ngữ: 1 dòng mỗi ngôn ngữ), ≤ 42 ký tự/dòng (dọc: 32; CJK: 16),
   không từ chức năng cuối dòng, không tách từ ghép/tên riêng/số + đơn vị.
5. ✅ Confidence Flagging: chỗ nghe không chắc mang `[CẦN XÁC MINH]`; báo số lượng cho người dùng.
6. ✅ Khử dấu vết AI: câu dịch tự nhiên, xưng hô nhất quán, không "—".
7. ✅ Đã MỞ `preview_grid.jpg` và kiểm tra bằng mắt; file SRT/ASS/MP4 tồn tại trong `<output_dir>`, MP4 phát được, đúng thời lượng (bằng chứng: `qa.json`, `preview_grid.jpg`).
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (CLEAN DELIVERY PROTOCOL)
- Khung chat chỉ hiển thị bản tóm tắt ngắn gọn:
  - Tên video, thời lượng, số lượng câu phụ đề.
  - Ngôn ngữ gốc và ngôn ngữ đích.
  - Trạng thái phòng dựng tạm thời (Link truy cập cục bộ: `http://127.0.0.1:8765`).
  - Đường dẫn tuyệt đối đến file video đã render hoặc file phụ đề xuất bản trong `<output_dir>`.
- Không xả toàn bộ nội dung phụ đề hàng trăm dòng vào khung chat làm tràn bộ nhớ ngữ cảnh.
</delivery_protocol>

---

## 🧩 Engine dùng chung (Luật R7)

> Năng lực dưới đây đã có trong `.agents/skills/_shared/` hoặc `scripts/` — **gọi lại, KHÔNG viết lại** trong skill. Cần năng lực mới: tra [`_shared/ENGINES.md`](../_shared/ENGINES.md) trước; thiếu thì mở rộng/đăng ký ở `_shared`, rồi chạy `python3 scripts/check_shared_reuse.py`.

| Engine / công cụ | Dùng cho | Cách gọi |
|---|---|---|
| `media.ass_generator` | Sinh ASS/SRT, đo chữ theo font thật | `from ass_generator import generate_ass, generate_srt` |
| `media.linebreak` | Ngắt dòng cân bằng Latin/CJK | `from linebreak import wrap_balanced` |
| `media.semantic_segmenter` | Phân đoạn theo câu, giới hạn CPS | CLI `_shared/media/semantic_segmenter.py` · `from semantic_segmenter import make_cfg, retime` |
| `media.subtitle_overlay` + `subtitle_styles.json` | Xem trước phụ đề trên workbench, preset kiểu | server phục vụ `/ui/lib/` từ `_shared/media/ui` |
| `_shared/fonts/` | Font OFL dùng chung (Be Vietnam Pro, Spectral, Noto Sans JP…) | đường dẫn `.agents/skills/_shared/fonts` |
