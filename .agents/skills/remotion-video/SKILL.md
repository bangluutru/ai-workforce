---
name: remotion-video
display-name: Video Lập Trình Remotion
description: >-
  Thiết kế, lập trình và kết xuất video bằng mã nguồn React + TypeScript trên
  nền tảng Remotion 4.x (Composition, Sequence, TransitionSeries,
  calculateMetadata, chữ karaoke @remotion/captions, hiệu ứng
  @remotion/motion-blur, @remotion/rough-notation, @remotion/layout-utils) kết
  hợp thuyết minh giọng đọc offline AIWF. USE WHEN: Người dùng yêu cầu tạo
  video bằng code React/Remotion, dựng programmatic video đa cảnh có schema tham
  số hóa (Zod), tạo component Remotion tái sử dụng, kiểm tra/sửa lỗi dự án
  Remotion hoặc render MP4 từ Remotion. DO NOT USE WHEN: Cần làm phim hoạt hình
  2D vẽ tay nghệ thuật bằng nét cọ/mực/Riso/chì trên Canvas 2D (dùng
  'hand-drawn-animation'), sản xuất video nhanh từ kịch bản + stock media
  Pexels/Pixabay hoặc 10 preset HTML/GSAP có sẵn (dùng 'video-studio'), hoặc chỉ
  làm phụ đề/dịch phụ đề cho video có sẵn (dùng 'phu-de').
trigger: /remotion-video, remotion, làm video bằng code react, programmatic video, remotion composition, dựng video react typescript
category: content
needs_file: false
file_filter: code
---

# Video Lập Trình Remotion (React + TypeScript Programmatic Video)

<goal>
Xây dựng, kiểm định và kết xuất dự án video lập trình (Programmatic Video) bằng **Remotion 4.x + React + TypeScript** đạt chuẩn kỹ thuật sản xuất:
1. Chuyển động tất định 100% theo `useCurrentFrame()` và `useVideoConfig()`, tuyệt đối không dùng CSS `transition`/`animation` hay `Math.random()`.
2. Bố cục tự co giãn đa tỷ lệ (`16:9`, `9:16`, `1:1`) với cơ chế đo chữ tự động (`fitText`, `fillTextBox`) và vùng an toàn hiển thị.
3. Tích hợp liền mạch với hệ sinh thái âm thanh offline của AIWF (`_shared/media/tts.py`, `dub_engine.py`, `output_manager.py`) mà không phụ thuộc vào dịch vụ đám mây trả phí.
</goal>

<context>
Khi nào chọn `remotion-video` thay vì hai kỹ năng video khác trong AIWF:
- Chọn **`remotion-video`** khi đầu ra cần là **mã nguồn React/TypeScript (`.tsx`)**, cần tái sử dụng UI component web có sẵn, cần truyền `defaultProps` động qua Zod schema để render hàng loạt biến thể, hoặc cần hệ sinh thái `@remotion/*` (`TransitionSeries`, `HtmlInCanvasMotionBlur`, `@remotion/captions`, `@remotion/three`, `@remotion/lottie`).
- Chọn **`hand-drawn-animation`** khi cần phim hoạt hình 2D vẽ tay nghệ thuật (nét bút lông, chì than, màu nước, bản in Risograph, giấy xé) chạy thuần HTML5 Canvas không cần cài đặt gói npm nặng.
- Chọn **`video-studio`** khi cần sản xuất nhanh video marketing/social từ kịch bản chữ kết hợp kho stock Pexels/Pixabay hoặc 10 mẫu Motion Presets HTML/GSAP dựng sẵn.

Tài liệu tham chiếu chuyên sâu trong kỹ năng (đọc theo nhu cầu thực tế của tác vụ):
- [`references/markup-timing-sequencing.md`](references/markup-timing-sequencing.md) hướng dẫn quy chuẩn DOM/CSS trong Remotion, `interpolate` kẹp biên, `spring`, `perceptual-scale`, `Sequence` và `TransitionSeries`.
- [`references/effects-transitions-captions.md`](references/effects-transitions-captions.md) hướng dẫn chuyển cảnh `@remotion/transitions`, nhòe chuyển động `@remotion/motion-blur`, tô sáng văn bản `@remotion/rough-notation`, đo chữ `@remotion/layout-utils` và phụ đề `@remotion/captions`.
- [`references/license-and-rendering.md`](references/license-and-rendering.md) quy định giấy phép Remotion License, quy trình kiểm thử frame tĩnh (`npx remotion still`) và kết xuất MP4 (`npx remotion render`).
</context>

---

## 0. Tiếp nhận & Phân loại Yêu cầu (Intake Protocol - Bước 0)

<instructions>

Khi kích hoạt kỹ năng, thực hiện **Bước 0 (Intake)** để xác định bối cảnh:
1. **Trường hợp A (Đã có dự án Remotion trong workspace hoặc đường dẫn người dùng cung cấp)**:
   - Chạy `python3 .agents/skills/remotion-video/scripts/remotion_helper.py --lint <project_dir>` để kiểm toán mã nguồn hiện tại.
   - Đọc `src/Root.tsx` và các composition liên quan trước khi chỉnh sửa (Luật R2 Codebase-First).
2. **Trường hợp B (Tạo mới video Remotion từ yêu cầu/kịch bản)**:
   - Nếu người dùng đã nêu chủ đề, tỷ lệ khung hình hoặc thời lượng thì bắt tay thiết kế ngay, không hỏi lại những thông số có thể dùng mặc định hợp lý (`1920x1080`, `30fps`, `12-20s`).
   - Chỉ hỏi tối đa 1 lượt nếu yêu cầu hoàn toàn trống rỗng về nội dung.
   - Khởi tạo khung dự án chuẩn vào `<process_dir>` hoặc `<output_dir>` bằng lệnh:
     ```bash
     python3 .agents/skills/remotion-video/scripts/remotion_helper.py --scaffold "<project_dir>" --id "<ten_composition>" --aspect "16:9" --fps 30 --duration 15
     ```

---

## 1. Quy trình Thực thi 5 Bước (Autonomous Workflow)

Khi đã rõ yêu cầu, agent **tự chạy liên tục** từ bước thiết kế đến khi xuất xong thành phẩm và kiểm định, **không tự dừng** giữa chừng để xin phép.

### Bước 1 - Thiết kế Kiến trúc Composition & Schema Dữ liệu
- Tách bạch dữ liệu nội dung (`defaultProps` + `z.object(...)` Zod schema) khỏi logic hiển thị để dễ dàng thay đổi văn bản, bảng màu và thời lượng.
- Sử dụng `calculateMetadata` khi thời lượng hoặc kích thước video phụ thuộc vào dữ liệu đầu vào (ví dụ độ dài mảng phân cảnh hoặc thời lượng file âm thanh).
- Nếu video có thuyết minh tiếng Việt/Anh/Nhật, sử dụng cầu nối TTS offline của AIWF (`--bridge-audio`) để sinh file âm thanh `.wav` vào `public/audio/` và đo chính xác thời lượng từng câu.

### Bước 2 - Lập trình Component Cảnh (`src/scenes/*.tsx`)
Tuân thủ nghiêm ngặt quy tắc cốt lõi của Remotion 4.x (chi tiết tại [`references/markup-timing-sequencing.md`](references/markup-timing-sequencing.md)):
1. **Cô lập `useCurrentFrame()` ở component lá nhỏ nhất**: không đặt `useCurrentFrame()` ở component cha chứa các nhánh DOM tĩnh nặng để tránh re-render toàn bộ cây mỗi frame.
2. **Nội suy thời gian theo `fps`**: mọi mốc thời gian phải nhân với `fps` từ `useVideoConfig()` (ví dụ `0.8 * fps`). Luôn bật `extrapolateLeft: 'clamp'` và `extrapolateRight: 'clamp'` trong `interpolate()`.
3. **Biến đổi CSS độc lập**: ưu tiên thuộc tính CSS `scale`, `translate`, `rotate` riêng biệt (`style={{ scale: String(s), translate: `${x}px ${y}px` }}`) thay vì nối chuỗi `transform` phức tạp.
4. **Đo và co chữ tự động**: sử dụng `fitText` / `fillTextBox` từ `@remotion/layout-utils` hoặc helper `fitHeadlineFontSize()` được tạo sẵn trong scaffold để chữ tiếng Việt có dấu không bao giờ tràn khỏi vùng an toàn.
5. **Tài nguyên tĩnh**: mọi ảnh, font, âm thanh trong `public/` phải truy cập qua `staticFile('...')` và dùng thẻ `<Img>`, `<Audio>`, `<OffthreadVideo>` từ `remotion` (không dùng thẻ `<img>`, `<video>`, `<audio>` HTML thô vì sẽ gây lệch frame khi render).

### Bước 3 - Ghép Chuỗi Cảnh & Âm Thanh (`src/MainVideo.tsx`)
- Dùng `<Series>` hoặc `<TransitionSeries>` (từ `@remotion/transitions`) để ghép nối các phân cảnh.
- Lưu ý toán học thời gian của `<TransitionSeries>`: mỗi `<TransitionSeries.Transition>` làm **rút ngắn tổng thời lượng** đi đúng bằng thời lượng chuyển cảnh (`total = sum(scenes) - sum(transitions)`). Nếu cần giữ nguyên tổng thời lượng khớp với lời đọc, phải cộng bù số frame chuyển cảnh vào `durationInFrames` của cảnh trước.

### Bước 4 - Kiểm toán Tĩnh & Soát Ảnh Khung Hình (Static Lint + Still QA)
1. Chạy công cụ kiểm toán mã nguồn Remotion:
   ```bash
   python3 .agents/skills/remotion-video/scripts/remotion_helper.py --lint "<project_dir>" --json "<output_dir>/remotion_lint.json"
   ```
   Phải đạt **0 lỗi FAIL** trước khi render. Lint là kiểm tra regex tĩnh, không thay cho biên dịch TypeScript.
2. Nếu máy có Node.js, chạy `npm run setup` trong thư mục dự án (cài gói, `npx remotion add zod` để lấy đúng bản zod mà Remotion yêu cầu, rồi `npx remotion versions` để chắc mọi gói `remotion` / `@remotion/*` cùng một phiên bản). Sau đó:
   - `npm run typecheck` (`tsc --noEmit`) để kiểm lỗi kiểu TypeScript.
   - Kết xuất ít nhất 3 ảnh tĩnh đại diện (đầu, giữa, cuối) bằng `npx remotion still` để kiểm tra bố cục mắt thường trước khi chạy render MP4 toàn cục.
   - Nếu `still`/`render` treo ở bước "Waiting for root component to load", thêm `--browser-executable` trỏ tới Chrome hệ thống (xem mục Xử Lý Sự Cố trong [`references/license-and-rendering.md`](references/license-and-rendering.md)).

### Bước 5 - Kết xuất MP4 & Nghiệm thu Kỹ thuật
- Kết xuất video MP4 vào `<output_dir>`:
  ```bash
  npx remotion render src/index.ts <CompositionId> "<output_dir>/<ten_video>.mp4" --codec=h264
  ```
- Kiểm tra file MP4 đầu ra bằng `ffprobe` (độ phân giải, số khung hình, thời lượng, luồng âm thanh) hoặc chạy Visual QA từ `_shared/creative` nếu cần bảng contact sheet.

</instructions>

---

## 2. Các Lệnh Cấm Tuyệt Đối trong Mã Nguồn Remotion

<constraints>

1. **CẤM CSS `transition` và `animation`**: mọi chuyển động bằng CSS `transition: ...`, `@keyframes` hoặc các lớp Tailwind `animate-*`, `transition-*` đều không đồng bộ với bộ đếm frame của Remotion, gây nhấp nháy và nhảy hình khi render đa luồng.
2. **CẤM `Math.random()`**: sử dụng `random('seed-string-' + i)` từ gói `remotion` để đảm bảo mỗi frame có kết quả giống hệt nhau trên mọi luồng render.
3. **CẤM `setTimeout` / `setInterval` / `requestAnimationFrame`**: thời gian trong Remotion hoàn toàn do `useCurrentFrame()` quyết định.
4. **CẤM thẻ `<img>`, `<video>`, `<audio>` HTML gốc**: bắt buộc dùng `<Img>`, `<OffthreadVideo>` (hoặc `<Video>` từ `@remotion/media`), `<Audio>` từ `remotion` để trình kết xuất đợi tải xong tài nguyên trước khi chụp frame.
5. **CẤM gọi LLM REST API bên ngoài (ZERO EXTERNAL API / Zero External LLM API)**: kỹ năng không gọi REST API mô hình ngoài và không yêu cầu API key trả phí (như ElevenLabs hay OpenAI); phần thuyết minh dùng trực tiếp engine TTS offline của AIWF (`_shared/media/tts.py`).
6. **Tuân thủ Giấy phép Remotion License**: thông báo rõ cho người dùng nếu dự án dùng trong doanh nghiệp thương mại có từ 4 nhân sự trở lên (xem [`references/license-and-rendering.md`](references/license-and-rendering.md)).

</constraints>

---

## 3. Công cụ CLI Nội bộ (`scripts/remotion_helper.py`)

```bash
# 1. Khởi tạo dự án Remotion chuẩn mực (kèm TypeScript, Zod schema, Scene mẫu, helper đo chữ)
python3 .agents/skills/remotion-video/scripts/remotion_helper.py \
  --scaffold "<project_dir>" \
  --id "MainVideo" \
  --title "Tiêu đề Video" \
  --aspect "16:9" \
  --fps 30 \
  --duration 15

# 2. Kiểm toán tĩnh mã nguồn Remotion (.tsx / .ts) phát hiện lỗi chống chỉ định
python3 .agents/skills/remotion-video/scripts/remotion_helper.py \
  --lint "<project_dir>" \
  --json "<output_dir>/remotion_lint.json"

# 3. Sinh thuyết minh giọng đọc offline (VieNeu / Kokoro) vào public/audio/ kèm manifest thời lượng
python3 .agents/skills/remotion-video/scripts/remotion_helper.py \
  --bridge-audio "<scenes_json_path>" \
  --project-dir "<project_dir>" \
  --lang vi
```

---

## 4. Cổng Kiểm Định Chất Lượng (Quality Gate & Evidence Verifier)

<quality_gate>

Trước khi bàn giao, tác nhân bắt buộc chạy kiểm định kép (Technical + User Experience) và đối chiếu **bằng chứng** thực tế (Evidence Verifier / Confidence Flagging):

### Checklist Nghiệm thu Bắt buộc
- [ ] **Kiểm toán mã nguồn (`--lint`)**: Đạt `0 FAIL` trên toàn bộ tệp `.tsx`/`.ts` (không có `Math.random()`, không có CSS `transition`/`animation`, không dùng `<img>`/`<video>` trần, mọi `interpolate` có `extrapolateLeft`/`extrapolateRight: "clamp"`).
- [ ] **Biên dịch cú pháp**: Mã nguồn TypeScript/JSX sạch lỗi cú pháp.
- [ ] **Bảo toàn bố cục & dấu tiếng Việt**: Chữ tiêu đề và phụ đề nằm gọn trong vùng an toàn 8% mỗi cạnh, không tràn khung trên tỷ lệ đã chọn (`16:9`, `9:16` hoặc `1:1`).
- [ ] **Kiểm chứng thành phẩm (Confidence Flagging)**:
  - Nếu đã chạy `npx remotion render` thành công: đính kèm bằng chứng `ffprobe` (độ phân giải, `fps`, `duration`, dung lượng file MP4) và ảnh chụp still frame.
  - Nếu môi trường máy hiện tại chưa cài gói npm `remotion` hoặc chưa chạy lệnh tải package: ghi rõ trạng thái `[CHƯA RENDER MP4 - ĐÃ KIỂM ĐỊNH MÃ NGUỒN & LINT PASS]` kèm lệnh `npm install && npx remotion render` một dòng để người dùng chạy, tuyệt đối không báo cáo khống là đã xuất MP4.

</quality_gate>

---

## 5. Giao thức Bàn giao & Bảo vệ Codebase

<delivery_protocol>

- **Clean Delivery**: Tin nhắn phản hồi trên khung chat chỉ tóm tắt ngắn gọn cấu trúc Composition (số cảnh, độ phân giải, fps, thời lượng), kết quả chạy `remotion_helper.py --lint`, trạng thái giấy phép Remotion và đường dẫn tuyệt đối tới thư mục dự án / file MP4 tại `<output_dir>`. Không dán hàng trăm dòng mã nguồn `.tsx` lên khung chat khi đã lưu vào file.
- **Hướng dẫn sử dụng nhanh**: Cung cấp lệnh mở phòng dựng trực quan (`npx remotion studio`) và lệnh xuất MP4 (`npx remotion render`).

</delivery_protocol>

> [!IMPORTANT]
> **BẢO VỆ CODEBASE (Anti-Repo Bloat)**
> Toàn bộ dự án Remotion được khởi tạo cho người dùng, các tệp âm thanh thuyết minh, ảnh chụp still và video MP4 thành phẩm PHẢI lưu vào `<output_dir>` (mặc định `~/Downloads/AIWF_Output/<ten_du_an>/` thông qua `output_manager.py`). File nháp tạm đặt tại `<process_dir>` (`_process/`). Tuyệt đối không tạo dự án Remotion hoặc cài `node_modules` vào thư mục gốc của repository AIWF.

---

## 🧩 Engine dùng chung (Luật R7)

> Năng lực dưới đây đã có trong `.agents/skills/_shared/` hoặc `scripts/` và được gọi lại trực tiếp, không viết lại trong skill.

| Engine / Module dùng chung | Đường dẫn | Vai trò trong `remotion-video` |
|---|---|---|
| **Output Manager** | `.agents/skills/_shared/output_manager.py` | Cấp phát đường dẫn `<output_dir>` chuẩn tại `~/Downloads/AIWF_Output/` chống xả rác vào repo |
| **Offline TTS Engine** | `.agents/skills/_shared/media/tts.py` | Tổng hợp giọng đọc tiếng Việt (VieNeu-TTS) và Anh/Nhật (Kokoro) offline cho các cảnh Remotion qua `--bridge-audio` |
| **FFmpeg Tools** | `.agents/skills/_shared/media/ffmpeg_tools.py` | Đo thời lượng chính xác (`duration`) của từng đoạn audio thuyết minh để quy đổi ra `durationInFrames` |
