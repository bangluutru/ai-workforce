# Quality Gates Checklist cho Kỹ năng Tạo Landing Page

Trước khi tuyên bố Landing Page đã hoàn thành và đạt chuẩn Production-Ready, kỹ năng bắt buộc phải kiểm tra và đánh dấu toàn bộ các tiêu chí:

## 1. Landing Hub Integration DoD (12 Tiêu chí Bắt buộc)
- [ ] 1. `projectId` tồn tại và đang hoạt động (`status: 'active'`) trong Landing Hub.
- [ ] 2. `landingPageId` được đăng ký và trực thuộc `projectId`.
- [ ] 3. Production domain / URL khớp với `project.allowedDomains` hoặc `landingPage.url`.
- [ ] 4. Toàn bộ form trên trang đều được đăng ký với đúng `formId`.
- [ ] 5. Loại form khớp với phương thức gửi (`lead` -> `submitLead`, `order` -> `submitOrder`, `custom` -> `submitCustomForm`).
- [ ] 6. SDK `LPHub` khởi tạo thành công không có lỗi console.
- [ ] 7. Sự kiện chuẩn (`page_view`, `cta_click`) bắn đúng với payload hợp lệ.
- [ ] 8. Bối cảnh đa kênh (`utm_*`, `referrer`, `firstTouch`, `lastTouch`) được lưu giữ và truyền tải.
- [ ] 9. Nhấp đúp vào nút gửi form chỉ sinh ra ĐÚNG 1 bản ghi (in-flight deduplication đã xác minh).
- [ ] 10. Gửi lại cùng idempotencyKey trả về HTTP 200 `idempotentReplay: true` và không tạo bản ghi trùng lặp.
- [ ] 11. KHÔNG chứa bất kỳ kết nối Firestore hoặc cơ sở dữ liệu trực tiếp nào trong bundle phía client.
- [ ] 12. Bản build production không chứa secret, token quản trị hoặc test credentials.

## 2. Giao diện & Trải nghiệm Người dùng (UI/UX & Responsive)
- [ ] 13. Kiểm thử 3 Viewports: Mobile 375px (không tràn viền), Tablet 768px (lưới cân đối), Desktop 1440px (bố cục sang trọng).
- [ ] 14. Font chữ trên di động tối thiểu 15-16px để chống auto-zoom trên iOS Safari.
- [ ] 15. Nút bấm CTA có trạng thái hover, active và loading rõ ràng khi submit.
- [ ] 16. Mọi hình ảnh có thuộc tính `alt` rõ ràng và được nén tối ưu.

## 3. Tiêu chuẩn Kỹ thuật & Build (Engineering Rigor)
- [ ] 17. `npm run typecheck` vượt qua không có lỗi TypeScript.
- [ ] 18. `npm run build` hoàn tất tạo bundle sạch trong thư mục `dist/`.
- [ ] 19. Kiểm định chất lượng bằng `app-auditor` đạt mức chấp thuận (không có lỗi Critical).
