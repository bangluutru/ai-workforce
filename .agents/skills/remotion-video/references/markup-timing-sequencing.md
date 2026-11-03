# Quy Chuẩn Markup, Thời Gian & Phân Cảnh trong Remotion 4.x

> Tài liệu chắt lọc từ bộ kỹ năng chính thức của `remotion-dev/remotion` (`remotion-best-practices`, `remotion-markup`) và chuẩn hóa cho AI Workforce.

---

## 1. Quy tắc DOM & CSS trong Remotion (`remotion-markup`)

### 1.1 Khung chứa gốc (`AbsoluteFill`)
- Mỗi cảnh (Scene) hoặc lớp chồng (Layer) luôn bọc trong `<AbsoluteFill>` từ `remotion`.
- Đặt kích thước phông chữ, độ dày viền và khoảng cách theo tỷ lệ với `width`/`height` từ `useVideoConfig()` hoặc thiết kế trên hệ quy chiếu chuẩn `1920x1080` rồi co giãn bằng biến tỷ lệ `const scale = Math.min(width, height) / 1080`.

### 1.2 Thuộc tính biến đổi độc lập (Individual Transform Properties)
Ưu tiên sử dụng thuộc tính CSS `scale`, `translate`, `rotate` riêng biệt thay vì gộp chuỗi `transform`, giúp mã rõ ràng và tránh lỗi thứ tự nhân ma trận:

```tsx
// Khuyên dùng
<div
  style={{
    scale: String(scaleValue),
    translate: `${translateX}px ${translateY}px`,
    rotate: `${rotateDeg}deg`,
    opacity,
  }}
/>
```

### 1.3 Cô lập `useCurrentFrame()` ở Component Lá
- `useCurrentFrame()` kích hoạt re-render trên mỗi khung hình.
- Nếu một cảnh có nền phức tạp (lưới SVG, bảng biểu lớn, danh sách thẻ tĩnh) và chỉ có 1 con trỏ hoặc 1 dòng chữ chuyển động, hãy tách phần chuyển động thành component con riêng biệt và chỉ gọi `useCurrentFrame()` bên trong component con đó.

---

## 2. Nội suy Thời gian & Chuyển động (`timing.md`)

### 2.1 Quy đổi thời gian theo `fps`
Không viết cứng số khung hình kiểu `interpolate(frame, [0, 30], ...)`. Luôn lấy `fps` từ `useVideoConfig()` để khi đổi Composition từ `30fps` sang `60fps`, tốc độ chuyển động giữ nguyên:

```tsx
const frame = useCurrentFrame();
const { fps } = useVideoConfig();

const opacity = interpolate(frame, [0, 0.6 * fps], [0, 1], {
  easing: Easing.out(Easing.cubic),
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
});
```

### 2.2 Bắt buộc kẹp biên (`extrapolateLeft` & `extrapolateRight: 'clamp'`)
Mặc định hàm `interpolate()` của Remotion sẽ ngoại suy tuyến tính ra vô cùng nếu `frame` nằm ngoài `inputRange`. Do đó **mọi lệnh gọi `interpolate()` phải truyền cả hai cờ**:
- `extrapolateLeft: 'clamp'`
- `extrapolateRight: 'clamp'`

### 2.3 Nội suy tỷ lệ đều mắt (`output: 'perceptual-scale'`)
Khi phóng to một phần tử qua dải tỷ lệ lớn (ví dụ từ `1` lên `10`), nội suy tuyến tính làm giai đoạn đầu cảm giác cực nhanh và giai đoạn cuối rất chậm. Dùng `perceptual-scale` (hoặc công thức logarit $s_0 \cdot (s_1 / s_0)^u$) để tốc độ phóng to đều mắt:

```tsx
const zoom = interpolate(frame, [0, 2 * fps], [1, 8], {
  easing: Easing.inOut(Easing.quad),
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
  output: 'perceptual-scale',
});
```

### 2.4 Chuyển động đàn hồi vật lý (`spring()`)
Hàm `spring({ frame, fps, config, durationInFrames, delay })` trả về giá trị từ `0` đến `1`:
- Cấu hình mượt không nảy lố (Snappy UI): `config: { damping: 200 }`
- Cấu hình nảy nhẹ sinh động (Bouncy Callout): `config: { damping: 14, stiffness: 160, mass: 0.9 }`
- Kết hợp `spring()` với `interpolate()`:
  ```tsx
  const enter = spring({ frame, fps, config: { damping: 200 }, delay: Math.round(0.2 * fps) });
  const translateY = interpolate(enter, [0, 1], [48, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  ```

---

## 3. Phân cảnh & Dòng thời gian (`sequencing.md` & `multi-scene-video.md`)

### 3.1 `<Sequence>` và thuộc tính `premountFor`
- Bên trong `<Sequence from={startFrame} durationInFrames={dur}>`, lời gọi `useCurrentFrame()` sẽ tự động trả về số frame tính từ `0` (tương đối so với thời điểm bắt đầu của Sequence).
- Luôn thêm `premountFor={Math.round(0.5 * fps)}` cho các `<Sequence>` chứa hình ảnh/video để trình duyệt dựng sẵn DOM trước khi cảnh xuất hiện, tránh nháy trắng ở frame đầu tiên.

### 3.2 `<Series>` so với `<TransitionSeries>`
1. **`<Series>` (Cắt thẳng - Hard Cut)**:
   - Các cảnh nối tiếp nhau tuần tự, tổng thời lượng bằng tổng các cảnh:
     $$T_{\text{total}} = \sum_{i=1}^{n} D_i$$
2. **`<TransitionSeries>` (Chuyển cảnh chồng lấn - `@remotion/transitions`)**:
   - Chuyển cảnh làm hai cảnh kề nhau chồng lên nhau trong khoảng $T_{\text{trans}}$, do đó tổng thời lượng bị rút ngắn:
     $$T_{\text{total}} = \sum_{i=1}^{n} D_i - \sum_{j=1}^{m} T_{\text{trans}, j}$$
   - **Quy tắc vàng khi ghép với thuyết minh (Audio Sync)**: Nếu cảnh $i$ có file thuyết minh dài $D_{\text{audio}, i}$ và phía sau có chuyển cảnh dài $T_{\text{trans}}$, hãy đặt thời lượng của cảnh $i$ trong `<TransitionSeries.Sequence>` là $D_{\text{audio}, i} + T_{\text{trans}}$ để lời đọc kết thúc trước khi cảnh mới chiếm trọn màn hình.

### 3.3 Tính toán Siêu dữ liệu Động (`calculateMetadata`)
Khi thời lượng tổng của video phụ thuộc vào danh sách cảnh truyền qua `props`, khai báo `calculateMetadata` trên `<Composition>` trong `Root.tsx`:

```tsx
<Composition
  id="MainVideo"
  component={MainVideo}
  schema={VideoSchema}
  defaultProps={defaultVideoProps}
  calculateMetadata={async ({ props }) => {
    const fps = props.fps ?? 30;
    const totalSeconds = props.scenes.reduce((acc, s) => acc + s.durationSec, 0);
    return {
      fps,
      width: props.width ?? 1920,
      height: props.height ?? 1080,
      durationInFrames: Math.max(1, Math.round(totalSeconds * fps)),
    };
  }}
/>
```
