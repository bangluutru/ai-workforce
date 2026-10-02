# Quality Gates - Tạo Landing Page

## A. Tự động (phải có bằng chứng từ output script)
- [ ] `landing_builder.py`: status OK, không lỗi tương phản, mọi câu chữ rủi ro có nguồn trong `claims_evidence`.
- [ ] `qa_runner.py` thoát 0: secret scan, token brand-*, typecheck, build:qa, render 375/768/1440 không tràn ngang, không ảnh hỏng, không lỗi console ngoài lỗi kết nối Hub QA, không tài nguyên ngoài, CTA đúng `--color-primary`.
- [ ] Gửi form E2E: ĐẠT (Hub local) - hoặc ghi rõ "CHƯA KIỂM" kèm lý do khi bàn giao. Không được ghi "đã kiểm thử" nếu chưa chạy.
- [ ] `npm run build` (production) chỉ chạy được khi `.env.production` có URL https thật của Hub.

## B. Agent soát bằng mắt (bắt buộc, ghi vào qa_report.md)
- [ ] Đã mở từng ảnh `landing_mobile_375.png`, `landing_tablet_768.png`, `landing_desktop_1440.png`.
- [ ] Màu, font, giọng văn khớp brief/thiết kế; không có câu chữ nào không xuất phát từ brief.
- [ ] Hero rõ 1 thông điệp + 1 CTA chính nổi bật; thứ tự section hợp lý; khoảng cách đều; không chữ chồng/cắt.
- [ ] Form đúng trường brief yêu cầu (không thừa trường như "tình trạng da" cho quán cà phê).
- [ ] Mục `[CẦN XÁC MINH]` hiển thị tô vàng và được liệt kê cho người dùng.

## C. Landing Hub (khi xuất bản thật - cần người dùng xác nhận)
- [ ] `hub_integrator.py --dry-run` đã được người dùng xem; đăng ký thật dùng token của người dùng (`LPHUB_ADMIN_TOKEN`).
- [ ] `allowedDomains` và `--lp-url` là domain thật người dùng cung cấp.
- [ ] Sau khi deploy: chạy `app-auditor` trên URL thật.
