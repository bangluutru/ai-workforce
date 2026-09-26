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

# Kỹ Năng Lồng Tiếng Video (long-tieng v2.3)
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
## QUY TRÌNH THỰC THI 6 BƯỚC (SOP AUTONOMOUS FULL-RUN)

### BƯỚC 0: KIỂM TRA MÔI TRƯỜNG & PHỤ THUỘC (CHẠY ĐẦU TIÊN)
Agent chạy script kiểm tra:
```bash
python3 .agents/skills/long-tieng/scripts/check_deps.py
```
- Kiểm tra `ffmpeg` trên macOS và engine giọng nói cục bộ (VoiceStudio / edge-tts).

---

### BƯỚC 1: KHỞI TẠO DỰ ÁN LỒNG TIẾNG (PROJECT INITIALIZATION)
Agent khởi tạo file cấu hình `dubbing_project.json` từ video và phụ đề:
```bash
python3 -c "
import sys; sys.path.insert(0, '.agents/skills/long-tieng/scripts')
from dubbing_project_manager import create_dubbing_project
proj_file, _ = create_dubbing_project('<video_path>', '<subtitles_path>', '<process_dir>')
print('Created project:', proj_file)
"
```

---

### BƯỚC 2: KHỞI CHẠY PHÒNG DỰNG TƯƠNG TÁC (INTERACTIVE STUDIO UI)
Agent khởi chạy Local Bridge Server trên cổng 8780+:
```bash
python3 .agents/skills/long-tieng/scripts/local_dubbing_server.py --project "<process_dir>/dubbing_project.json"
```
Người dùng tương tác trực tiếp trên giao diện:
1. **Dual-Track Audio Playback**: Bấm Play ▶ để nghe trực tiếp giọng đọc AI tiếng Việt phát đè lên nền tiếng gốc của video với Smart Ducking tự động.
2. **Bộ Chọn Giọng Studio & Nghe Thử Tức Thì**: Bấm vào nút `🔊 Nghe thử` hoặc đổi giọng trong danh mục 10 giọng chuẩn 5 sao để nghe mẫu thoại đặc trưng.
3. **Chỉnh Kiểu Chữ Phụ Đề Trực Quan (Live Subtitle Overlay)**: Chuyển sang Tab 🎨 Kiểu Chữ Phụ Đề để chọn Preset (Modern Bottom, TikTok Box, Cinema Classic, Top Banner), điều chỉnh màu chữ, màu viền, cỡ chữ, phông chữ và độ mờ nền hộp nổi trực tiếp trên video.
4. **Chia Câu Tại Vị Trí Phát (`✂ Chia câu tại đây`)**: Cắt phân đoạn dài thành các câu nhỏ khớp từng nhịp thở nhân vật.
5. **Re-render & Xem Thành Phẩm**: Bấm "Xuất Video Lồng Tiếng", theo dõi tiến trình và bấm "Xem Ngay Trên Trình Phát" hoặc "Render Lại Phiên Bản Mới".

---

### BƯỚC 3: TỔNG HỢP ÂM THANH & UNIFORM ATEMPO (Two-Pass Speed Calibration)

> [!IMPORTANT]
> **QUY TẮC UNIFORM ATEMPO (BẮT BUỘC):**
> Thuật toán co giãn thời gian PHẢI sử dụng phương pháp **hai lượt (Two-Pass)** để đảm bảo tốc độ đọc ĐỒNG NHẤT xuyên suốt video. NGHIÊM CẤM tính atempo riêng lẻ cho từng phân đoạn vì sẽ gây hiện tượng giọng đọc lúc nhanh lúc chậm, méo tiếng.

**PASS 1 — Tổng hợp giọng nói & Đo thời lượng thô:**
- Gọi `voice_synthesizer.py` tạo file âm thanh từng câu thoại theo giọng đọc đã chọn.
- **Auto-detect file format thực tế:** Voice engine có thể lưu file `.mp3` thay vì `.wav`. Pipeline PHẢI kiểm tra sự tồn tại file theo thứ tự: (1) path gốc đã truyền, (2) quét các extension thay thế `.mp3`, `.ogg`, `.m4a`, `.wav`, (3) path `output_path` từ kết quả trả về của synthesizer.
- Đo thời lượng thực tế (`actual_dur`) của từng file thô bằng `ffprobe`.

**PASS 2 — Tính atempo ĐỒNG NHẤT toàn cục & Áp dụng đều:**
- Công thức tính:
  $$\text{global\_atempo} = \frac{\sum_{i=1}^{N} \text{actual\_dur}_i}{\sum_{i=1}^{N} \text{target\_dur}_i \times 0.88}$$
  - Tổng thời lượng AI thô chia cho tổng mục tiêu (88% thời lượng phân đoạn gốc, 12% dành cho khoảng thở tự nhiên).
- **Dải an toàn:** Kẹp `global_atempo` trong $[0.70, 1.15]$ để tránh méo tiếng.
- **Áp dụng CÙNG MỘT hệ số atempo cho TẤT CẢ phân đoạn**, đảm bảo nhịp đọc bằng nhau xuyên suốt video.
- Sử dụng bộ lọc `atempo` của FFmpeg (chain nếu cần, hỗ trợ range `[0.50, 2.0]`).
- Output fitted segments PHẢI là WAV PCM 16-bit (`-acodec pcm_s16le`).

---

### BƯỚC 4: HÒA ÂM AUDIO DUCKING & MASTER TRACK
- Ghép tất cả các đoạn lồng tiếng vào dòng thời gian khớp từng mili-giây bằng bộ lọc `adelay`.
- Kích hoạt cơ chế **Smart Audio Ducking** (`sidechaincompress`):
  - Khi giọng thuyết minh cất lên: Nhạc nền và âm thanh gốc tự động giảm xuống mức ducking đã chọn (mặc định 15% - 20%).
  - Khi dứt câu thoại: Nhạc nền tự động trở lại mức âm lượng gốc mượt mà.

---

### BƯỚC 5: ĐÓNG GÓI VIDEO THÀNH PHẨM BULLETPROOF (CLEAN DELIVERY)
- Tự động phát hiện năng lực bộ lọc FFmpeg:
  - Nếu có filter `ass`/`subtitles`: Khắc cứng phụ đề hardsub lên video.
  - Nếu thiếu filter `ass`: Tự động chuyển sang chế độ **Muxing Siêu Tốc (`-c:v copy`)** ghép 100% âm thanh hòa âm `final_mixed_audio.wav` vào video và nhúng phụ đề mềm `mov_text`.
- Xuất video hoàn chỉnh vào `<output_dir>/<tên_video>_dubbed.mp4` (mặc định `~/Downloads/AIWF_Output/`).
</instructions>

---

<constraints>
## BẢY ĐIỀU CẤM TUYỆT ĐỐI (7 ABSOLUTE BANS)
1. ❌ **CẤM ĐÒI HỎI EXTERNAL API KEY:** 100% giọng đọc được tạo bằng động cơ cục bộ. Cấm gọi REST API trả phí bên ngoài.
2. ❌ **CẤM XUẤT FILE THÀNH PHẨM VÀO CODEBASE:** File video lồng tiếng bắt buộc xuất ra `<output_dir>` (`~/Downloads/AIWF_Output/`), cấm ghi bừa bãi vào root repo.
3. ❌ **CẤM LỆCH MỐC THỜI GIAN ÂM THANH:** Âm thanh lồng tiếng bắt buộc phải khớp với khung thời gian của phụ đề, không để câu nói tràn sang phân đoạn kế tiếp.
4. ❌ **CẤM DỪNG DỞ DANG ĐỂ XIN PHÉP:** Phải tự động chạy liên tục qua toàn bộ chuỗi quy trình từ tạo tiếng, ducking đến đóng gói video.
5. ❌ **CẤM VĂN PHONG MÙI AI TIẾNG VIỆT:** Câu thoại lồng tiếng cấm dùng em dash `—`, cấm Oxford comma `, và`, cấm từ ngữ dịch máy sáo rỗng.
6. ❌ **CẤM TÍNH ATEMPO RIÊNG LẺ CHO TỪNG CÂU (Per-Segment Atempo):** Việc tính hệ số `atempo` khác nhau cho mỗi phân đoạn tạo hiện tượng giọng đọc lúc nhanh lúc chậm, có thể gây méo tiếng. BẮT BUỘC dùng thuật toán **Uniform Atempo Two-Pass** (1 hệ số duy nhất cho toàn bộ video).
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
- `segments/raw_seg_*.mp3`: Âm thanh thô từng phân đoạn lời thoại.
- `segments/fitted_seg_*.wav`: Âm thanh đã co giãn tốc độ theo thời lượng chuẩn.
- `master_speech.wav` & `master_speech_44k.wav`: Toàn bộ lời thuyết minh hòa âm mốc thời gian hoàn chỉnh.
- `final_mixed_audio.wav`: Âm thanh cuối cùng sau khi áp dụng Audio Ducking.
- `subtitles.ass` & `subtitles.srt`: File phụ đề theo chuẩn kiểu dáng đã thiết lập.
</working_ledger>

---

<quality_gate>
## CHECKLIST TỰ THẨM ĐỊNH CHẤT LƯỢNG (QUALITY GATE)
Trước khi bàn giao kết quả cho người dùng, Agent kiểm tra:
1. ✅ **Tốc độ đọc đồng nhất (Uniform Pace Verification):** In ra bảng phân tích nhịp đọc toàn cục gồm: tổng thời lượng AI thô, tổng mục tiêu 88%, hệ số `global_atempo` duy nhất. Xác nhận tất cả phân đoạn dùng CÙNG MỘT atempo — nếu phát hiện per-segment atempo → `FAIL`.
2. ✅ **File format auto-detection:** Xác nhận pipeline đã tìm đúng file âm thanh thô (`.mp3`/`.wav`) thay vì đọc cứng extension. Kiểm tra `fitted_dur ≠ actual_dur` khi `atempo ≠ 1.0` — nếu bằng nhau nghĩa là atempo chưa được áp dụng → `FAIL`.
3. ✅ **Độ đồng bộ âm thanh - hình ảnh:** Lời thoại lồng tiếng cất lên và kết thúc khớp với sự xuất hiện của phụ đề / nhân vật (Dual-Track Audio Sync & Overlay).
4. ✅ **Chất lượng hòa âm Ducking:** Âm nền không bị lấn át lời thuyết minh và không bị giật tiếng khi chuyển cảnh.
5. ✅ **Tự động gắn cờ nghi ngờ (Confidence Flagging):** Khi câu thoại quá dài so với thời lượng khung hình (coverage > 115%), tự động gắn cờ `[CẦN XÁC MINH]` để xem xét chia câu hoặc rút ngắn câu chữ.
6. ✅ **Khử dấu vết AI:** Lời thoại tự nhiên, chuẩn văn phong khẩu ngữ đời thường, không có dấu nối dài `—`.
7. ✅ **Kiểm chứng file thành phẩm:** File video MP4 lồng tiếng thực sự tồn tại trong `<output_dir>` và có thể mở xem bình thường.
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
