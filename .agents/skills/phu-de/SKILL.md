---
name: phu-de
display-name: Tạo Phụ Đề
description: >-
  Tạo, bóc tách và biên tập phụ đề video (SRT, ASS, hardsub MP4) với forced alignment từng từ, phân đoạn ngữ nghĩa CPL/CPS, dịch thuật phụ đề song ngữ và phòng dựng visual review trực quan.
  USE WHEN: Người dùng cần tạo phụ đề, làm sub song ngữ, dịch phụ đề, hoặc dập phụ đề (hardsub) vào video có sẵn.
  DO NOT USE WHEN: Cần sản xuất video tổng thể từ kịch bản/stock media (dùng 'video-studio'), chỉ cần lồng tiếng/thuyết minh audio track (dùng 'long-tieng'), hoặc dịch tài liệu văn bản tĩnh PDF/Docx (dùng 'ejv-translate').
trigger: Tạo phụ đề, làm phụ đề video, dịch phụ đề, auto subtitle, hardsub, xuất phụ đề srt ass
category: content
needs_file: true
file_filter: media
---

# Kỹ Năng Phụ Đề Video Thông Minh & Phòng Dựng Tương Tác (phu-de v1.2)
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
## QUY TRÌNH THỰC THI 6 BƯỚC (SOP AUTONOMOUS FULL-RUN)

### BƯỚC 0: KIỂM TRA MÔI TRƯỜNG & PHỤ THUỘC (CHẠY ĐẦU TIÊN)
Agent chạy script kiểm tra:
```bash
python3 .agents/skills/phu-de/scripts/check_deps.py
```
- Nếu thiếu `ffmpeg` trên macOS: hướng dẫn cài đặt qua `brew install ffmpeg`.
- Nếu thiếu thư viện Python: tự động cài đặt qua `pip3 install faster-whisper pysubs2`.

---

### BƯỚC 1: TRÍCH XUẤT AUDIO VÀ THÔNG SỐ VIDEO (DETERMINISTIC)
Agent tạo thư mục xử lý tạm `<process_dir>` và chạy:
```bash
python3 .agents/skills/phu-de/scripts/extract_audio.py \
  --video "<đường_dẫn_video>" \
  --output-wav "<process_dir>/audio.wav" \
  --meta-json "<process_dir>/video_meta.json"
```
Kết quả: Thu được file âm thanh chuẩn 16kHz mono WAV và file JSON chứa các thông số: thời lượng, độ phân giải, FPS, tỷ lệ khung hình.

---

### BƯỚC 2: NHẬN DẠNG GIỌNG NÓI & WORD-LEVEL ALIGNMENT
Agent chạy mô hình offline để trích xuất mốc thời gian chính xác từng từ:
```bash
python3 .agents/skills/phu-de/scripts/transcribe_align.py \
  --audio "<process_dir>/audio.wav" \
  --output "<process_dir>/raw_transcript.json" \
  --model "base"
```
Kết quả: Tạo file `raw_transcript.json` chứa danh sách các từ kèm `[word, start, end, probability]`.

---

### BƯỚC 3: PHÂN ĐOẠN PHỤ ĐỀ NGỮ NGHĨA (SEMANTIC CHUNKING)
Agent gom các từ thành các dòng phụ đề tự nhiên, dễ đọc theo chuẩn CPL/CPS (VideoLingo/Anchor Sub Sync logic):
```bash
python3 .agents/skills/phu-de/scripts/semantic_segmenter.py \
  --input "<process_dir>/raw_transcript.json" \
  --output "<process_dir>/segmented_subtitles.json" \
  --max-cpl 42 \
  --max-duration 5.0
```

---

### BƯỚC 4: HIỆU CHỈNH CHÍNH TẢ & DỊCH THUẬT PHỤ ĐỀ (GEMINI REASONING)
Agent nạp danh sách segments từ `segmented_subtitles.json`. Với mỗi phân đoạn, Agent thực hiện:
1. Sửa lỗi từ đồng âm (homophones), tên riêng, loại bỏ từ đệm thừa.
2. Dịch sang ngôn ngữ đích (nếu cần), bảo đảm độ dài câu dịch súc tích, tự nhiên, vừa vặn với tốc độ đọc phụ đề.
3. **KHÓA BẤT BIẾN TỌA ĐỘ THỜI GIAN:** Tuyệt đối giữ nguyên `start` và `end` của từng segment.
4. Khởi tạo `project.json` (Single Source of Truth) và lưu bản snapshot đầu tiên:
```bash
python3 -c "
import json
from .agents.skills.phu-de.scripts.project_manager import create_project
with open('<process_dir>/video_meta.json') as f: v = json.load(f)
with open('<process_dir>/segmented_subtitles.json') as f: s = json.load(f)
create_project(v, s.get('segments', []), source_lang='auto', target_lang='vi', mode='bilingual', project_dir='<process_dir>')
"
```

---

### BƯỚC 5: KHỞI CHẠY PHÒNG DỰNG TƯƠNG TÁC (INTERACTIVE WEBVIEW PANEL — ISP V1.0)
Sau khi `project.json` được tạo lập, phòng dựng tương tác được kích hoạt theo chuẩn **Cách B (IDE Extension Webview Panel)**:
- **Tự động kích hoạt:** Extension AIWF tự động nhận diện file `project.json` mới tại `<process_dir>` và mở Webview Editor Tab ngay bên trong IDE (song song với cửa sổ chat).
- **Hoặc kích hoạt thủ công:** Nhấn vào thẻ phiên tương tác trên Sidebar AIWF hoặc chạy lệnh:
  ```bash
  # Tùy chọn: Khởi chạy local bridge nếu cần stream video ngoại vi
  python3 .agents/skills/phu-de/scripts/local_bridge_server.py --project "<process_dir>/project.json"
  ```
Người dùng thực hiện trên giao diện phòng dựng:
1. **Local Action (Tức thời, 0 token):** Xem video preview khớp mốc phụ đề; chỉnh màu sắc, cỡ chữ, phông chữ, canh lề, nền mờ; kéo thả timeline; gõ sửa từ ngữ trực tiếp; bấm Split hoặc Merge câu. Trạng thái tự động lưu vào `project.json` và tạo snapshot lịch sử.
2. **Agent Action (Vòng lặp AI Edit có cấu trúc):** Chọn 1 hoặc nhiều câu và nhập chỉ thị (ví dụ: *"Rút ngắn câu này cho tự nhiên"*, *"Chuyển sang tone trang trọng"*). Giao diện gửi Action Request có cấu trúc vào chat $\rightarrow$ Agent tiếp nhận và dùng tool `replace_file_content` cập nhật chính xác các câu đó trong `project.json` $\rightarrow$ Webview tự động re-render tức thì.
3. **Undo / Redo an toàn:** Bấm hoàn tác / làm lại bất kỳ lúc nào để quay về các snapshot trước.

---

### BƯỚC 6: XUẤT BẢN THÀNH PHẨM (EXPORT & CLEAN DELIVERY)
1. Khi người dùng bấm **Xuất phụ đề** hoặc gõ lệnh trong chat:
   - Sinh file `.srt` và `.ass` lưu vào `<output_dir>` (mặc định `~/Downloads/AIWF_Output/`).
2. Khi người dùng bấm **Render Video MP4**:
   - Hệ thống gọi `render_video.py` để khắc phụ đề bằng FFmpeg + libass.
   - Video hoàn tất được xuất ra `<output_dir>/<tên_video>_subtitled.mp4`.
3. Người dùng bấm **✕ Đóng** trên giao diện để giải phóng máy chủ tạm thời.
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
- `project.json`: Nguồn sự thật duy nhất (Single Source of Truth).
- `snapshots/rev_001.json`, `rev_002.json`...: Bản ghi lịch sử cho cơ chế Undo/Redo.
- `temp_render.ass`: File ASS trung gian phục vụ FFmpeg libass render.
</working_ledger>

---

<quality_gate>
## CHECKLIST TỰ THẨM ĐỊNH CHẤT LƯỢNG (QUALITY GATE)
Trước khi bàn giao kết quả cho người dùng, Agent kiểm tra:
1. ✅ **Độ đồng bộ âm thanh - chữ:** Mốc thời gian `start` và `end` khớp với khẩu hình và giọng nói người phát âm.
2. ✅ **Độ dài câu hợp chuẩn:** Không có phân đoạn nào vượt quá 42 ký tự/dòng hoặc thời lượng dưới 0.8 giây.
3. ✅ **Tự động gắn cờ nghi ngờ (Confidence Flagging):** Khi đoạn âm thanh bị rè hoặc độ tin cậy < 85%, gắn cờ `[CẦN XÁC MINH]` trong nội dung để người dùng kiểm tra trên UI.
4. ✅ **Khử dấu vết AI:** Câu dịch tự nhiên, chuẩn văn phong đời thường, không có dấu nối dài `—`.
5. ✅ **Kiểm chứng file thành phẩm:** File video MP4 hoặc file phụ đề `.srt`/`.ass` thực sự tồn tại trong `<output_dir>` và mở phát bình thường.
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
