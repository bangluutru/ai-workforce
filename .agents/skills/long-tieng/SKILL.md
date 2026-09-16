---
name: long-tieng
display-name: Lồng Tiếng Video
description: Lồng tiếng và thuyết minh video tự động thông minh chuẩn studio, đồng bộ giọng đọc AI với khẩu hình và mốc thời gian phụ đề, co giãn thời lượng tự động (FFmpeg atempo), hòa âm thông minh giảm tiếng nền (Smart Audio Ducking), hỗ trợ đa ngôn ngữ Tiếng Việt, Tiếng Nhật, Tiếng Anh chất lượng 5 sao cục bộ. Kích hoạt khi user yêu cầu 'lồng tiếng video', 'thuyết minh video', 'dubbing video', 'làm voiceover video', 'ghép giọng đọc vào clip'. KHÔNG dùng cho việc chỉ bóc tách chữ hoặc tạo phụ đề thuần túy (hãy chuyển sang phu-de) hoặc dịch tài liệu văn bản tĩnh (dùng ejv-translate/boc-tach-pdf).
trigger: Lồng tiếng video, thuyết minh video, video dubbing, lồng tiếng tự động, voiceover clip, ghép giọng vào video
argument-hint: [video_file_path] [subtitles_path: project.json|srt] [target_lang: vi|ja|en] [gender: female|male]
allowed-tools: [run_command, view_file, write_to_file, replace_file_content, browser_subagent]
effort: high
context: fork
interaction-mode: interactive
needs_file: true
file_filter: video
---

# Kỹ Năng Lồng Tiếng Video Tự Động & Thuyết Minh Studio (long-tieng v1.0)
## Chuẩn Google Antigravity 2.0 & Mô Hình Lõi Gemini 3.8 Multi-Agent

<goal>
Thực hiện quy trình lồng tiếng (Voiceover / AI Dubbing) khép kín từ video và kịch bản phụ đề đầu vào: phân tích mốc thời gian từng câu thoại, tạo giọng đọc truyền cảm chất lượng 5 sao (Tiếng Việt, Tiếng Nhật, Tiếng Anh) qua động cơ cục bộ, co giãn tốc độ nói thông minh (Time-Stretching) để khớp mốc phụ đề, tự động hạ âm lượng nhạc nền video gốc (Audio Ducking) khi có lời thoại, và render xuất bản video MP4 hoàn thiện ra thư mục chỉ định.
</goal>

---

<context>
Kỹ năng vận hành theo triết lý kiến trúc 2 động cơ phối hợp:
1. **Deterministic Media Tools**: FFmpeg, ffprobe, sidechaincompress, atempo, edge-tts, VoiceStudio. Chịu trách nhiệm tổng hợp sóng âm, đo đạc thời lượng chính xác từng mili-giây, co giãn nhịp điệu và hòa âm ducking. Tuyệt đối không dùng LLM cho các tác vụ xử lý sóng âm vật lý.
2. **Cognitive Reasoning Engine**: Antigravity nội bộ (Gemini 3.8) chịu trách nhiệm tối ưu nhịp điệu câu thoại (phân bổ số lượng từ ngữ phù hợp với thời lượng khung hình), gọt giũa ngữ điệu dịch tự nhiên, và chỉ đạo phong cách lồng tiếng (trang trọng, thời sự, tự nhiên, truyền cảm).
3. **Nguyên tắc Zero-Loss & Evidence Verifier**: Giữ nguyên 100% chất lượng hình ảnh gốc (-c:v copy), đồng bộ chặt chẽ âm thanh lồng tiếng với dòng thời gian của phụ đề.
</context>

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Kỹ năng này vận hành hoàn toàn bằng khả năng nội bộ của Antigravity IDE (Gemini 3.8) kết hợp động cơ giọng nói cục bộ (VoiceStudio / Edge-TTS Neural).
> - TUYỆT ĐỐI KHÔNG gọi REST API bên ngoài (OpenAI API, ElevenLabs API, Cloud TTS ngoài) hoặc yêu cầu API key trả phí.
> - Khi được kích hoạt, skill PHẢI tự chạy liên tục (Autonomous Full-Run) từ bước nạp phân đoạn thoại, tạo âm thanh, hòa âm ducking đến khi đóng gói video hoàn chỉnh, không tự dừng dở dang để xin phép.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

Agent PHẢI xác định đường dẫn lưu file trước khi thực hiện quy trình:

| Placeholder | Quy ước xác định đường dẫn thực tế |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/`** |
| `<process_dir>` | Thư mục tạm xử lý: `<workspace>/_process/dubbing_[project_id]/` (đã nằm trong `.gitignore`) |
| `<skill_dir>` | Thư mục kỹ năng: `<workspace>/.agents/skills/long-tieng/` |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi file thành phẩm xuất bản (video MP4 đã lồng tiếng, master audio track) PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/` hoặc nơi user chỉ định).
> - Toàn bộ file tạm (các đoạn WAV từng câu, fitted segments, raw clips, logs) PHẢI lưu trong `<process_dir>` (`_process/dubbing_[id]/`).
> - TUYỆT ĐỐI KHÔNG lưu file video hoặc audio thành phẩm trực tiếp vào thư mục gốc của repository Git để tránh làm phình dung lượng codebase.

---

## 🏗️ Bảng Tọa độ Đầu vào & Phân luồng (Intake Coordinates)

Trước khi thực thi, Agent phân loại tọa độ đầu vào của người dùng theo 5 Trục Tọa độ sau:

| Trục Tọa độ | Giá trị xác định | Hành vi mặc định nếu thiếu |
|---|---|---|
| **1. File Video Nguồn** | Đường dẫn tuyệt đối file MP4 / MOV / MKV / WebM | Yêu cầu người dùng cung cấp đường dẫn video |
| **2. Kịch bản / Phụ đề** | Đường dẫn `project.json` (từ `phu-de`) hoặc `.srt` | Tự động quét file `project.json` gần nhất trong `_process/` |
| **3. Ngôn ngữ Lồng tiếng** | `vi` (Tiếng Việt), `ja` (Tiếng Nhật), `en` (Tiếng Anh) | `vi` (Tiếng Việt) |
| **4. Giới tính Giọng** | `female` (Nữ) hoặc `male` (Nam) | `female` (Nữ - Hoài My / Nanami / Jenny) |
| **5. Mức Audio Ducking** | Tỷ lệ âm nền khi có lời thoại (ví dụ: `0.15` đến `0.25`) | `0.20` (Giảm nền xuống còn 20% âm lượng) |

---

<instructions>
## QUY TRÌNH THỰC THI 5 BƯỚC (SOP AUTONOMOUS FULL-RUN)

### BƯỚC 0: KIỂM TRA MÔI TRƯỜNG & PHỤ THUỘC (CHẠY ĐẦU TIÊN)
Agent chạy script kiểm tra:
```bash
python3 .agents/skills/long-tieng/scripts/check_deps.py
```
- Kiểm tra `ffmpeg` trên macOS và engine giọng nói cục bộ (VoiceStudio / edge-tts).

---

### BƯỚC 1: TRÍCH XUẤT AUDIO NỀN VÀ PHÂN TÍCH PHÂN ĐOẠN LỜI THOẠI
Agent nạp kịch bản từ `project.json` hoặc file phụ đề `.srt`:
- Kiểm tra danh sách các phân đoạn: `start`, `end`, và nội dung câu thoại đã dịch.
- Nếu kịch bản là tiếng nước ngoài và cần lồng tiếng Việt: Agent sử dụng năng lực nội bộ Gemini 3.8 để hiệu chỉnh độ dài câu dịch cho tự nhiên, vừa vặn với thời lượng từng phân đoạn.

---

### BƯỚC 2: TỔNG HỢP ÂM THANH TỪNG PHÂN ĐOẠN (NEURAL SYNTHESIS)
Hệ thống gọi động cơ giọng đọc 5 sao cục bộ:
- **Tiếng Việt**: `vi-VN-HoaiMyNeural` (Nữ truyền cảm) hoặc `vi-VN-NamMinhNeural` (Nam phóng sự).
- **Tiếng Nhật**: `ja-JP-NanamiNeural` (Nữ chuẩn Tokyo) hoặc `ja-JP-KeitaNeural` (Nam năng động).
- **Tiếng Anh**: `en-US-JennyNeural` hoặc profile VoiceStudio Studio Grade.
Mỗi phân đoạn được lưu tại `<process_dir>/segments/raw_seg_[id].mp3`.

---

### BƯỚC 3: CO GIÃN THỜI GIAN THÔNG MINH (AUTO TIME-STRETCHING)
- Đối chiếu độ dài âm thanh thực tế với thời lượng phân đoạn `dur_target = end - start`.
- Nếu âm thanh đọc dài hơn hoặc ngắn hơn, tự động áp dụng Live Formulas qua bộ lọc `atempo` của FFmpeg:
  $$\text{speed\_factor} = \frac{\text{duration\_thực\_tế}}{\text{duration\_mục\_tiêu}}$$
- Giới hạn dải an toàn $[0.75, 1.35]$ để giữ nguyên độ tự nhiên và cao độ giọng nói gốc.

---

### BƯỚC 4: HÒA ÂM AUDIO DUCKING & MASTER TRACK
- Ghép tất cả các đoạn lồng tiếng vào dòng thời gian khớp từng mili-giây bằng bộ lọc `adelay`.
- Kích hoạt cơ chế **Smart Audio Ducking** (`sidechaincompress`):
  - Khi giọng thuyết minh cất lên: Nhạc nền và âm thanh gốc tự động giảm xuống 20%.
  - Khi dứt câu thoại: Nhạc nền tự động trở lại mức bình thường mượt mà.

---

### BƯỚC 5: ĐÓNG GÓI VIDEO THÀNH PHẨM (CLEAN DELIVERY)
- Đóng gói video bằng FFmpeg với cờ `-c:v copy` (Zero re-encoding, tốc độ siêu tốc, chất lượng hình ảnh nguyên bản 100%).
- Xuất video hoàn chỉnh vào `<output_dir>/<tên_video>_dubbed.mp4` (mặc định `~/Downloads/`).
</instructions>

---

<constraints>
## NĂM ĐIỀU CẤM TUYỆT ĐỐI (5 ABSOLUTE BANS)
1. ❌ **CẤM ĐÒI HỎI EXTERNAL API KEY:** 100% giọng đọc được tạo bằng động cơ cục bộ. Cấm gọi REST API trả phí bên ngoài.
2. ❌ **CẤM XUẤT FILE THÀNH PHẨM VÀO CODEBASE:** File video lồng tiếng bắt buộc xuất ra `<output_dir>` (`~/Downloads/`), cấm ghi bừa bãi vào root repo.
3. ❌ **CẤM LỆCH MỐC THỜI GIAN ÂM THANH:** Âm thanh lồng tiếng bắt buộc phải khớp với khung thời gian của phụ đề, không để câu nói tràn sang phân đoạn kế tiếp.
4. ❌ **CẤM DỪNG DỞ DANG ĐỂ XIN PHÉP:** Phải tự động chạy liên tục qua toàn bộ chuỗi quy trình từ tạo tiếng, ducking đến đóng gói video.
5. ❌ **CẤM VĂN PHONG MÙI AI TIẾNG VIỆT:** Câu thoại lồng tiếng cấm dùng em dash `—`, cấm Oxford comma `, và`, cấm từ ngữ dịch máy sáo rỗng.
</constraints>

---

<working_ledger>
## ĐỊNH DẠNG LƯU VẾT TIẾN TRÌNH VẬT LÝ
Toàn bộ tiến trình làm việc được lưu vết trong thư mục `<process_dir>`:
- `original_audio.wav`: File âm thanh gốc trích xuất từ video.
- `segments/raw_seg_*.mp3`: Âm thanh thô từng phân đoạn lời thoại.
- `segments/fitted_seg_*.wav`: Âm thanh đã co giãn tốc độ theo thời lượng chuẩn.
- `master_speech.wav`: Toàn bộ lời thuyết minh đã hòa âm mốc thời gian hoàn chỉnh.
- `final_mixed_audio.wav`: Âm thanh cuối cùng sau khi áp dụng Audio Ducking.
</working_ledger>

---

<quality_gate>
## CHECKLIST TỰ THẨM ĐỊNH CHẤT LƯỢNG (QUALITY GATE)
Trước khi bàn giao kết quả cho người dùng, Agent kiểm tra:
1. ✅ **Độ đồng bộ âm thanh - hình ảnh:** Lời thoại lồng tiếng cất lên và kết thúc khớp với sự xuất hiện của phụ đề / nhân vật.
2. ✅ **Chất lượng hòa âm Ducking:** Âm nền không bị lấn át lời thuyết minh và không bị giật tiếng khi chuyển cảnh.
3. ✅ **Tự động gắn cờ nghi ngờ (Confidence Flagging):** Khi câu thoại quá dài so với thời lượng khung hình (cần tăng tốc > 1.3x), tự động gắn cờ `[CẦN XÁC MINH]` để xem xét rút ngắn câu chữ.
4. ✅ **Khử dấu vết AI:** Lời thoại tự nhiên, chuẩn văn phong khẩu ngữ đời thường, không có dấu nối dài `—`.
5. ✅ **Kiểm chứng file thành phẩm:** File video MP4 lồng tiếng thực sự tồn tại trong `<output_dir>` và có thể mở xem bình thường.
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (CLEAN DELIVERY PROTOCOL)
- Khung chat chỉ hiển thị bản tóm tắt ngắn gọn:
  - Tên video, thời lượng, số lượng phân đoạn đã lồng tiếng.
  - Ngôn ngữ và giọng đọc đã sử dụng.
  - Mức giảm âm lượng nền (Ducking level).
  - Đường dẫn tuyệt đối đến file video hoàn chỉnh trong `<output_dir>`.
- Không xả mã lệnh thô hoặc danh sách sóng âm vào khung chat làm tràn bộ nhớ ngữ cảnh.
</delivery_protocol>
