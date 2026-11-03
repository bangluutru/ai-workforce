# Giấy Phép Remotion License, Kiểm Thử Khung Tĩnh & Kết Xuất MP4

> Tài liệu tham chiếu về điều khoản bản quyền Remotion và quy trình kiểm định kết xuất thực tế.

---

## 1. Quy Định Bản Quyền Remotion License (`remotion-license`)

Remotion sử dụng mô hình cấp phép kép (**Remotion License** + **MIT** cho một số gói phụ trợ):

1. **Trường hợp ĐƯỢC miễn phí bản quyền (Free License)**:
   - Cá nhân làm dự án cá nhân hoặc học tập.
   - Tổ chức phi lợi nhuận (Non-profit organization).
   - Doanh nghiệp thương mại (For-profit company) có **tối đa 3 thành viên** (tính tổng số người làm việc trong công ty, không chỉ riêng lập trình viên).
2. **Trường hợp BẮT BUỘC mua Company License**:
   - Doanh nghiệp thương mại có **từ 4 thành viên trở lên** sử dụng các gói mang giấy phép `Remotion License` (`remotion`, `@remotion/cli`, `@remotion/renderer`, `@remotion/player`, `@remotion/transitions`, `@remotion/motion-blur`, `@remotion/layout-utils`, `@remotion/captions`).
3. **Trách nhiệm của Agent khi bàn giao**:
   - Luôn ghi chú 1 dòng ngắn gọn trong phần bàn giao nhắc người dùng về ngưỡng 3 nhân sự của Remotion License nếu triển khai cho doanh nghiệp.
   - Nếu doanh nghiệp cần giải pháp **100% giấy phép mở miễn phí cho mọi quy mô công ty**, khuyến nghị dùng `video-studio` (HTML/GSAP + Canvas/HyperFrames) hoặc `hand-drawn-animation` (Canvas 2D thuần) sẵn có trong AIWF.

---

## 2. Quy Trình Soát Ảnh Tĩnh Trước Khi Render (`npx remotion still`)

Kết xuất toàn bộ video MP4 tốn nhiều thời gian CPU. Trước khi chạy `npx remotion render`, hãy xuất các khung hình tĩnh tại những thời điểm quan trọng (frame đầu, giữa cảnh 1, lúc chuyển cảnh, cảnh kết) để kiểm tra bố cục:

```bash
# Chụp khung hình tại frame thứ 45 (1.5s ở 30fps)
npx remotion still src/index.ts MainVideo "<output_dir>/preview_f045.png" --frame=45
```

Kiểm tra trên ảnh chụp:
- Chữ tiếng Việt không bị lỗi font hoặc mất dấu thanh.
- Tiêu đề và thẻ thông tin không chạm sát mép khung hình (đảm bảo vùng an toàn $\ge 8\%$).
- Độ tương phản giữa chữ và nền dễ đọc.

---

## 3. Lệnh Kết Xuất Sản Xuất (`npx remotion render`)

```bash
# Xuất MP4 chuẩn H.264 tương thích mọi trình phát (QuickTime, trình duyệt, điện thoại)
npx remotion render src/index.ts MainVideo "<output_dir>/video_final.mp4" \
  --codec=h264 \
  --pixel-format=yuv420p \
  --crf=18

# Truyền dữ liệu props động từ file JSON để render hàng loạt biến thể
npx remotion render src/index.ts MainVideo "<output_dir>/video_custom.mp4" \
  --props="./custom-props.json"
```

Sau khi xuất file MP4, luôn chạy `ffprobe` để xác minh thông số kỹ thuật thực tế. Nếu máy không có `ffprobe` hệ thống, dùng bản đi kèm Remotion (`npx remotion ffprobe ...`, cùng cú pháp):
```bash
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate -of json "<output_dir>/video_final.mp4"
```

---

## 4. Xử Lý Sự Cố Đã Gặp Thực Tế

| Triệu chứng | Nguyên nhân đã xác minh | Cách xử lý |
|---|---|---|
| `delayRender() "Waiting for root component to load" ... not cleared`, kể cả với composition tối giản | Chrome Headless Shell do Remotion tự tải về không chạy được trong môi trường hiện tại (lỗi môi trường, không phải lỗi mã) | Thêm cờ `--browser-executable="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"` (macOS) cho `still` và `render` |
| `npx remotion versions` báo `zod: installed 3.x, required 4.x` | Remotion 4 bản mới yêu cầu zod 4 | `npx remotion add zod` (script `npm run setup` của scaffold đã gọi sẵn) |
| `ffmpeg ... No such filter: 'volumedetect'` khi dùng `npx remotion ffmpeg` | Bản ffmpeg đi kèm Remotion là bản rút gọn | Giải mã ra WAV (`-c:a pcm_s16le`) rồi đo bằng công cụ khác, hoặc dùng ffmpeg đầy đủ của hệ thống |
