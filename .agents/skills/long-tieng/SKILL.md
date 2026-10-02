---
name: long-tieng
display-name: Lồng Tiếng Video
description: >-
  Lồng tiếng và thuyết minh video tự động chuẩn phòng thu chất lượng cao, tích hợp TTS offline đa vùng miền và đa ngôn ngữ (Việt - Anh - Nhật), đồng bộ khẩu hình và timeline phụ đề, tự động co giãn thời lượng và hòa âm giảm tiếng ồn nền (audio ducking).
  USE WHEN: Người dùng cần tạo bản thuyết minh âm thanh, lồng tiếng video từ file kịch bản hoặc file phụ đề có sẵn.
  DO NOT USE WHEN: Cần dựng toàn bộ video từ ý tưởng/kho stock (dùng 'video-studio'), chỉ cần tạo/dịch phụ đề chữ (dùng 'phu-de'), hoặc tạo hoạt hình vẽ tay (dùng 'hand-drawn-animation').
trigger: Lồng tiếng video, thuyết minh video, video dubbing, lồng tiếng tự động, voiceover clip, ghép giọng vào video
category: content
needs_file: true
file_filter: media
---

# Kỹ Năng Lồng Tiếng Video (long-tieng v3.0)
## Chuẩn Google Antigravity 2.0 & Mô Hình Lõi Gemini 3.8 Multi-Agent

<goal>
Thực hiện quy trình lồng tiếng (Voiceover / AI Dubbing) khép kín chuẩn phòng thu từ video và kịch bản phụ đề đầu vào:
1. Khởi tạo dự án lồng tiếng tự động từ file video và phụ đề SRT/project.json.
2. Khởi chạy phòng dựng tương tác Studio UI (Localhost 8780+) với cơ chế **Dual-Track Realtime Audio Sync** (tự động phát giọng đọc AI đè lên video gốc theo thời gian thực kèm Smart Ducking).
3. Hiển thị phụ đề trực tiếp trên màn hình video bằng **Live Subtitle Overlay 1:1** chuẩn ASS (hỗ trợ 4 preset, đơn ngữ/song ngữ, đổi phông, cỡ chữ, màu sắc, hộp mờ và lề).
4. Cho phép **nghe thử giọng đọc tức thì (Instant Voice Preview)** từ kho giọng chuẩn phòng thu 48 kHz (Thùy Dung, Thái Sơn, Trúc Ly, Mai Anh, Minh Quân Pro, Anh Khôi, Quang Sơn, Ngọc Trân...) và tính năng **Instant Voice Cloning** nhân bản chất giọng diễn viên.
5. Tích hợp công cụ **chia câu tại vị trí phát (`split_segment`)** giúp ngắt các phân đoạn dài khớp hoàn hảo với nhịp nói nhân vật.
6. Hỗ trợ **re-render liên tục** và cơ chế đóng gói **Bulletproof Muxing** đảm bảo 100% xuất bản video MP4 chất lượng cao ra `<output_dir>`.
</goal>

---

<context>
Kỹ năng vận hành theo triết lý kiến trúc 3 trụ cột phối hợp:
1. **Deterministic Media Tools**: FFmpeg, ffprobe, sidechaincompress, atempo, VieNeu-TTS v3 Turbo, edge-tts, VoiceStudio. Chịu trách nhiệm tổng hợp sóng âm 48 kHz, đo đạc thời lượng chính xác từng mili-giây, co giãn nhịp điệu và hòa âm ducking. Tuyệt đối không dùng LLM cho các tác vụ xử lý sóng âm vật lý.
2. **Dual-Track Realtime Audio Engine**: Bộ đồng bộ âm thanh hai luồng Web Audio API kết hợp HTTP 206 Partial Content, giúp trình phát video trên giao diện web phát đồng thời video gốc (đã hạ nhỏ âm lượng nền) và giọng đọc lồng tiếng đè lên đúng mốc thời gian 0ms.
3. **Cognitive Reasoning Engine**: Antigravity nội bộ (Gemini 3.8) tối ưu số lượng từ ngữ phù hợp với thời lượng khung hình, gọt giũa ngữ điệu dịch tự nhiên kèm emotion tags (`[cười]`, `[thở dài]`), và chỉ đạo phong cách lồng tiếng (trang trọng, thời sự, tự nhiên, truyền cảm).
</context>

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Kỹ năng này vận hành hoàn toàn bằng khả năng nội bộ của Antigravity IDE (Gemini 3.8) kết hợp động cơ giọng nói cục bộ (VieNeu-TTS v3 Turbo 48 kHz / Edge-TTS Neural).
> - TUYỆT ĐỐI KHÔNG gọi REST API bên ngoài (OpenAI API, ElevenLabs API, Cloud TTS ngoài) hoặc yêu cầu API key trả phí.
> - Khi được kích hoạt, skill PHẢI tự chạy liên tục (Autonomous Full-Run) từ bước nạp phân đoạn thoại, khởi tạo phòng dựng tương tác, hòa âm ducking đến khi đóng gói video hoàn chỉnh, không tự dừng dở dang để xin phép.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

Agent PHẢI xác định đường dẫn lưu file trước khi thực hiện quy trình:

| Placeholder | Quy ước xác định đường dẫn thực tế |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<process_dir>` | Thư mục tạm xử lý: `<workspace>/_process/dubbing_[project_id]/` (đã nằm trong `.gitignore`) |
| `<skill_dir>` | Thư mục kỹ năng: `<workspace>/.agents/skills/long-tieng/` |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi file thành phẩm xuất bản (video MP4 đã lồng tiếng, master audio track) PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/` hoặc nơi user chỉ định).
> - Toàn bộ file tạm (các đoạn WAV từng câu, fitted segments, raw clips, previews, logs) PHẢI lưu trong `<process_dir>` (`_process/dubbing_[id]/`).
> - TUYỆT ĐỐI KHÔNG lưu file video hoặc audio thành phẩm trực tiếp vào thư mục gốc của repository Git để tránh làm phình dung lượng codebase.

---

## 🏗️ Bảng Tọa độ Đầu vào & Phân luồng (Intake Coordinates)

Trước khi thực thi, Agent phân loại tọa độ đầu vào của người dùng theo 5 Trục Tọa độ sau:

| Trục Tọa độ | Giá trị xác định | Hành vi mặc định nếu thiếu |
|---|---|---|
| **1. File Video Nguồn** | Đường dẫn tuyệt đối file MP4 / MOV / MKV / WebM | Yêu cầu người dùng cung cấp đường dẫn video |
| **2. Kịch bản / Phụ đề** | Đường dẫn `project.json` (từ `phu-de`) hoặc `.srt` | Tự động quét file `project.json` gần nhất trong `_process/` |
| **3. Ngôn ngữ Lồng tiếng** | `vi` (Tiếng Việt), `ja` (Tiếng Nhật), `en` (Tiếng Anh) | `vi` (Tiếng Việt) |
| **4. Giới tính Giọng** | `female` (Nữ) hoặc `male` (Nam) | `female` (Nữ - Thùy Dung / Trúc Ly / Mai Anh / Nanami / Ava) hoặc `male` (Nam - Thái Sơn / Minh Quân Pro / Keita / Andrew) |
| **5. Cân bằng Âm lượng** | Giọng gốc: `5% - 20%`, Giọng lồng tiếng: `140%`, Ducking: `15%` | Mặc định hòa âm chuẩn phòng thu |

---

<instructions>
## QUY TRÌNH THỰC THI (SOP AUTONOMOUS FULL-RUN, v3)

> Lồng tiếng hay = (1) LỜI ĐỌC viết để nghe và vừa khung thời gian + (2) giọng đọc đúng, tự nhiên +
> (3) hòa âm sạch. Script lo đo đạc; **agent viết lời đọc và sửa theo báo cáo** cho tới khi mọi câu đạt.
> Ký hiệu: `L=.agents/skills/long-tieng/scripts`, `PD=<process_dir>`.

### BƯỚC 0 — Môi trường
`python3 $L/check_deps.py`. Tiếng Việt dùng **VieNeu-TTS v3 Turbo 48 kHz offline** (gói `vieneu` trong
`.venv`/`.venv-tts`, mô hình tự tải lần đầu); tiếng Anh: Kokoro/Edge; tiếng Nhật: Edge. Cần `faster-whisper`
(mô hình `large-v3-turbo`) để kiểm tra phát âm, ffmpeg có `rubberband` + `libass` (macOS: `brew install ffmpeg-full`).

### BƯỚC 1 — Kịch bản nguồn
Tốt nhất: chạy skill **phu-de** trước (ASR + reflow + proofread + translate) → `project.json` có `translated_text`.
Hoặc dùng `.srt` có sẵn (đã dịch). Không có bản dịch thì dịch trong bước 3.

### BƯỚC 2 — Khởi tạo dự án
`python3 $L/dub_workbench.py init --video "<video>" --subtitles "<project.json|.srt>" --process-dir $PD --lang vi --gender female [--voice "Thùy Dung"]`
Giọng VieNeu: Nữ — Thùy Dung (Nam, tin tức), Trúc Ly (Bắc), Mai Anh (Bắc, tin tức), Ngọc Huyền, Ngọc Trân (Trung)…;
Nam — Minh Quân Pro, Anh Khôi (kể chuyện), Thái Sơn (Nam), Quang Sơn (Trung)… Chọn theo vùng miền/người nói gốc.

### BƯỚC 3 — Agent viết LỜI ĐỌC vừa khung (bắt buộc)
`python3 $L/dub_workbench.py export --project $PD/dubbing_project.json` → mở `$PD/tasks/adapt_NN.json`,
đọc `instructions`, điền `"output"` cho mọi id → `python3 $L/dub_workbench.py apply --input <file>`.
- `max_chars` = khung thời gian (tới khi câu sau bắt đầu) × tốc độ nói tự nhiên. Lời đọc dài hơn = giọng phải
  đọc nhanh hoặc tràn — RÚT GỌN ý, không nhồi chữ.
- Viết theo cách ĐỌC: từ viết tắt/ký hiệu viết theo âm hoặc thay bằng từ Việt ("AI" → "trí tuệ nhân tạo"/"trợ lý ảo",
  "%" → "phần trăm" khi cần), tránh cụm dễ đọc nhầm (đo thực tế: "nối" bị đọc thành "núi", "tra tồn kho" → "ra tụng kho").
- Lời đọc ≠ phụ đề: phụ đề rút gọn để đọc bằng mắt; lời đọc phải trôi chảy khi nói, đúng ngữ khí người nói.

### BƯỚC 4 — Render
`python3 $L/dubbing_pipeline.py --video "<video>" --subtitles $PD/dubbing_project.json --output <output_dir>/<tên>_dubbed.mp4 --voice "<giọng>" --process-dir $PD [--ducking 0.2] [--bg-volume 1.0]`
Pipeline (dub_engine.py): tổng hợp theo lô → **Whisper nghe lại từng câu** (CER), câu đọc sai được đọc lại tối
đa 3 lượt và giữ lượt tốt nhất → khung mỗi câu = tới lúc câu sau bắt đầu; **chỉ tăng tốc khi cần** (nhịp nền
chung ≤ 1.08×, trần 1.25×, rubberband giữ formant), không bao giờ làm chậm → đặt đúng mốc → tiếng gốc hạ
còn `ducking` (mặc định 20% ≈ −14 dB, kiểu thuyết minh) chỉ trong vùng có lời, fade 150/350 ms →
chuẩn hoá −16 LUFS, đỉnh −1.5 dBTP → khắc phụ đề bằng bộ sinh của phu-de (Be Vietnam Pro, hộp bo góc).

### BƯỚC 5 — Báo cáo & sửa (lặp tới khi sạch)
`python3 $L/dub_workbench.py report --process-dir $PD` (exit 2 nếu còn lỗi):
- **TRÀN khung** → rút gọn `dub_text` câu đó. **ĐỌC SAI** (kèm câu Whisper nghe được) → viết lại cụm khó đọc.
- **đọc nhanh > 1.15×** → nên rút gọn cho tự nhiên.
Sửa `dub_text` trong `$PD/dubbing_project.json` (hoặc export/apply lại) rồi chạy lại BƯỚC 4 — câu không đổi
được dùng lại từ cache, chỉ câu đã sửa được tổng hợp lại (render lại ~30 s cho video 1 phút).

### BƯỚC 6 — Phòng dựng (tùy chọn) & kiểm chứng
- UI: `python3 $L/local_dubbing_server.py --project "$PD/dubbing_project.json"` (nghe thử giọng, chỉnh mức nền, chia câu).
- Kiểm chứng: `ffprobe` thời lượng = video gốc, có audio AAC 48 kHz; trích 1–2 khung hình xem phụ đề;
  `report` sạch; LUFS trong khoảng −17…−15.
</instructions>

---

<constraints>
## BẢY ĐIỀU CẤM TUYỆT ĐỐI (7 ABSOLUTE BANS)
1. ❌ **CẤM ĐÒI HỎI EXTERNAL API KEY:** 100% giọng đọc được tạo bằng động cơ cục bộ. Cấm gọi REST API trả phí bên ngoài.
2. ❌ **CẤM XUẤT FILE THÀNH PHẨM VÀO CODEBASE:** File video lồng tiếng bắt buộc xuất ra `<output_dir>` (`~/Downloads/AIWF_Output/`), cấm ghi bừa bãi vào root repo.
3. ❌ **CẤM LỆCH MỐC THỜI GIAN ÂM THANH:** Âm thanh lồng tiếng bắt buộc phải khớp với khung thời gian của phụ đề, không để câu nói tràn sang phân đoạn kế tiếp.
4. ❌ **CẤM DỪNG DỞ DANG ĐỂ XIN PHÉP:** Phải tự động chạy liên tục qua toàn bộ chuỗi quy trình từ tạo tiếng, ducking đến đóng gói video.
5. ❌ **CẤM VĂN PHONG MÙI AI TIẾNG VIỆT:** Câu thoại lồng tiếng cấm dùng em dash `—`, cấm Oxford comma `, và`, cấm từ ngữ dịch máy sáo rỗng.
6. ❌ **CẤM LÀM CHẬM GIỌNG HOẶC ÉP NHANH QUÁ 1.25×:** Giọng kéo lê (atempo < 1) hoặc đọc dồn (> 1.25×) đều mất tự nhiên. Câu không vừa khung phải được agent RÚT GỌN lời đọc, không được tăng tốc thêm. (Luật cũ "một atempo duy nhất cho cả video" đã bỏ vì làm câu dài tràn sang câu sau mà không báo.)
7. ❌ **CẤM GIẢ ĐỊNH ĐỊNH DẠNG FILE ÂM THANH THÔ:** Voice engine (VieNeu-TTS, Edge-TTS) có thể xuất `.mp3` thay vì `.wav` dù được truyền path `.wav`. Pipeline PHẢI auto-detect file thực tế thay vì đọc cứng extension đã truyền — nếu không, `ffmpeg atempo` sẽ thất bại âm thầm và file fitted sẽ giữ nguyên thời lượng thô.
</constraints>

---

<working_ledger>
## ĐỊNH DẠNG LƯU VẾT TIẾN TRÌNH VẬT LÝ
Toàn bộ tiến trình làm việc được lưu vết trong thư mục `<process_dir>`:
- `dubbing_project.json`: Hồ sơ dự án và cấu hình âm lượng, kịch bản, kiểu dáng phụ đề.
- `original_audio.wav`: File âm thanh gốc trích xuất từ video.
- `previews/preview_*.mp3`: File âm thanh nghe thử từng câu thoại.
- `samples/sample_*.mp3`: File âm thanh nghe thử mẫu chất giọng đặc trưng.
- `tasks/adapt_NN.json`: lô lời đọc agent viết.
- `takes/*.wav` + `takes/cache_index.json`: các lượt đọc và cache theo câu.
- `fitted/*.wav`: câu đã khớp khung.
- `dub_report.json`: báo cáo từng câu (khung, tốc độ, tràn, CER, câu Whisper nghe được).
- `master_speech.wav` & `master_speech_44k.wav`: Toàn bộ lời thuyết minh hòa âm mốc thời gian hoàn chỉnh.
- `final_mixed_audio.wav`: Âm thanh cuối cùng sau khi áp dụng Audio Ducking.
- `subtitles.ass` & `subtitles.srt`: File phụ đề theo chuẩn kiểu dáng đã thiết lập.
</working_ledger>

---

<quality_gate>
## CHECKLIST TỰ THẨM ĐỊNH CHẤT LƯỢNG (QUALITY GATE)
1. ✅ `dub_workbench.py report` sạch: **0 câu TRÀN khung**, **0 câu ĐỌC SAI** (CER ≤ 8% khi Whisper nghe lại), không câu nào lỗi tổng hợp.
2. ✅ Nhịp đọc: nhịp nền ≤ 1.08×, tối đa ≤ 1.25×; số câu > 1.15× càng ít càng tốt (ghi trong báo cáo).
3. ✅ Đúng engine: tiếng Việt chạy **VieNeu-TTS** (dòng `engine` trong `dub_report.json`), không lặng lẽ rơi về Edge-TTS.
4. ✅ Hòa âm: −16 ± 1 LUFS, đỉnh ≤ −1 dBTP; tiếng gốc chỉ hạ khi có lời (thuyết minh) hoặc theo yêu cầu.
5. ✅ Lời đọc tự nhiên, xưng hô nhất quán, không "—"; từ viết tắt đã viết theo cách đọc.
6. ✅ Confidence Flagging: câu agent không thể sửa cho đạt → báo `[CẦN XÁC MINH]` kèm thời điểm trong tin nhắn bàn giao.
7. ✅ File `<tên>_dubbed.mp4` tồn tại trong `<output_dir>`, đúng thời lượng, có phụ đề (nếu bật); bằng chứng: `dub_report.json`.
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (CLEAN DELIVERY PROTOCOL)
- Khung chat chỉ hiển thị bản tóm tắt ngắn gọn:
  - Tên video, thời lượng, số lượng phân đoạn đã lồng tiếng.
  - Ngôn ngữ và giọng đọc đã sử dụng.
  - Mức cân bằng âm lượng (giọng gốc, giọng lồng tiếng, ducking).
  - Đường dẫn truy cập phòng dựng localhost và đường dẫn tuyệt đối đến file video hoàn chỉnh trong `<output_dir>`.
- Không xả mã lệnh thô hoặc danh sách sóng âm vào khung chat làm tràn bộ nhớ ngữ cảnh.
</delivery_protocol>
