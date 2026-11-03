# Hiệu Ứng, Đo Chữ, Chú Giải & Phụ Đề trong Remotion 4.x

> Tài liệu chắt lọc từ `remotion-dev/remotion` (`transitions.md`, `measuring-text.md`, `text-highlights.md`, `motion-blur.md`, `remotion-captions`) và tích hợp với engine âm thanh của AI Workforce.

---

## 1. Đo Chữ & Chống Tràn Khung (`@remotion/layout-utils`)

Với tiếng Việt có dấu (như `Nguyễn`, `Hệ thống`, `Đột phá`), chiều dài từ và dấu thanh dễ làm tiêu đề bị rớt dòng xấu hoặc tràn khỏi vùng an toàn (Safe Zone 8%).

### 1.1 Tự co cỡ chữ vừa khung (`fitText`)
```tsx
import { fitText } from '@remotion/layout-utils';

const { fontSize } = fitText({
  text: title,
  withinWidth: width * 0.84, // Giữ lề an toàn 8% mỗi bên
  fontFamily: 'Inter, sans-serif',
  fontWeight: '800',
});
const clampedSize = Math.min(84, Math.max(28, fontSize));
```

### 1.2 Ngắt dòng thông minh trong hộp giới hạn (`fillTextBox`)
Khi cần kiểm soát số dòng tối đa của đoạn mô tả:
```tsx
import { fillTextBox } from '@remotion/layout-utils';

const box = fillTextBox({ maxBoxWidth: width * 0.8, maxLines: 3 });
// Thêm từng từ vào box.add({ text: word + ' ', fontFamily, fontSize })
```

---

## 2. Chú Giải Vẽ Tay Động (`@remotion/rough-notation` / SVG Progress)

Để nhấn mạnh từ khóa quan trọng trong video giải thích (Explainer / EdTech / Legal Summary), đặt từ khóa trong phần tử `inline-block` có `position: relative` và vẽ lớp chú giải bên dưới (`zIndex: 0`) trong khi chữ nằm ở `zIndex: 1`:

1. **Tô dạ quang (`highlight`)**: Dùng hình chữ nhật bo góc hoặc nét cọ SVG với `strokeDashoffset` giảm dần từ `length` về `0` theo `spring({ frame, fps, config: { damping: 200 } })`.
2. **Khoanh tròn (`circle`) & Gạch chân (`underline`)**: Tính `progress` trong khoảng `[0, 1]` và truyền vào thuộc tính `strokeDasharray={pathLength}` / `strokeDashoffset={pathLength * (1 - progress)}`.

---

## 3. Nhòe Chuyển Động Theo Góc Màn Trập (`@remotion/motion-blur`)

Gói `@remotion/motion-blur` có hai cách:

1. **`<HtmlInCanvasMotionBlur>`** (cách mới, màu chuẩn hơn): lấy mẫu nội dung HTML ở các frame phân số bên trong canvas rồi lấy trung bình điểm ảnh. Bắt buộc truyền `width`, `height`; `shutterAngle` mặc định `180`, `samples` mặc định `8`. Component con phải tự gọi `useCurrentFrame()` bên trong. Lưu ý: xem trước trong Studio cần trình duyệt hỗ trợ HTML-in-canvas (Chrome bật cờ tương ứng); khi render phía server thì không cần cấu hình thêm.

```tsx
import { HtmlInCanvasMotionBlur } from '@remotion/motion-blur';

const { width, height } = useVideoConfig();
<HtmlInCanvasMotionBlur width={width} height={height} shutterAngle={180} samples={8}>
  <FastMovingCard />
</HtmlInCanvasMotionBlur>
```

2. **`<CameraMotionBlur>`** (cách cũ, xếp chồng lớp DOM mờ): dùng khi cần xem trước trên mọi trình duyệt.

```tsx
import { CameraMotionBlur } from '@remotion/motion-blur';

<CameraMotionBlur shutterAngle={180} samples={6}>
  <FastMovingCard />
</CameraMotionBlur>
```

> Lưu ý: Không bọc toàn bộ video tĩnh trong component nhòe vì `samples` nhân số lần vẽ mỗi frame. Chỉ bọc đúng cảnh hoặc phần tử có tốc độ dịch chuyển lớn.

---

## 4. Phụ Đề Karaoke Theo Từng Từ (`@remotion/captions`)

### 4.1 Cấu trúc dữ liệu `Caption`
Mỗi mục phụ đề trong `@remotion/captions` tuân theo chuẩn:
```ts
export interface Caption {
  text: string;      // Lưu ý: giữ khoảng trắng đầu từ (ví dụ: " xin", " chào")
  startMs: number;
  endMs: number;
  timestampMs: number | null;
  confidence: number | null;
}
```

### 4.2 Chia trang kiểu TikTok / Reels (`createTikTokStyleCaptions`)
```tsx
import { createTikTokStyleCaptions } from '@remotion/captions';

const { pages } = createTikTokStyleCaptions({
  captions,
  combineTokensWithinMilliseconds: 1200,
});
```
Khi hiển thị từng `page`, so sánh `currentTimeMs = (frame / fps) * 1000` với `token.fromMs` và `token.toMs` để đổi màu nổi bật (Highlight Color) cho đúng từ đang được phát âm.

---

## 5. Cầu Nối Thuyết Minh Offline AIWF (`--bridge-audio`)

Khác với workflow mặc định của Remotion thường gợi ý gọi API trả phí bên ngoài, kỹ năng `remotion-video` trong AIWF tái sử dụng trực tiếp **Offline TTS Engine** (`.agents/skills/_shared/media/tts.py` với VieNeu-TTS cho tiếng Việt và Kokoro cho tiếng Anh/Nhật):

1. Tạo file `scenes_audio.json` mô tả lời thoại từng cảnh:
   ```json
   [
     { "id": "scene_01", "text": "Chào mừng bạn đến với hệ thống nhân sự số AI Workforce." },
     { "id": "scene_02", "text": "Tự động hóa quy trình dựng video bằng mã nguồn React và TypeScript." }
   ]
   ```
2. Chạy lệnh cầu nối:
   ```bash
   python3 .agents/skills/remotion-video/scripts/remotion_helper.py \
     --bridge-audio scenes_audio.json \
     --project-dir "<project_dir>" \
     --lang vi
   ```
3. Công cụ sẽ sinh các file `public/audio/scene_01.wav`, `public/audio/scene_02.wav` cùng file `src/audio-manifest.json` chứa thời lượng chính xác (`durationSec`, `durationInFrames`) để nạp thẳng vào `<Sequence>` và `<Audio src={staticFile('audio/scene_01.wav')} />`.
