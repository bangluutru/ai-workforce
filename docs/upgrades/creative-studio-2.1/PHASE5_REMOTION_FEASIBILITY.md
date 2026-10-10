# Phase 5 - Remotion Feasibility (research only)

Phạm vi: chỉ nghiên cứu. Không cài Remotion, không đổi renderer mặc định (HyperFrames), không đổi Storyboard contract, không đổi setup scripts.

Nhãn: OBSERVED (đã kiểm chứng trực tiếp) · DERIVED · PRIOR · NOT VERIFIED.

## 1. Bằng chứng thu thập

| Mục | Kết quả | Nhãn |
|---|---|---|
| Giấy phép | `LICENSE.md` của Remotion (không phải SPDX OSI; npm ghi `SEE LICENSE IN LICENSE.md`) | OBSERVED |
| Free License | Cá nhân; công ty vì lợi nhuận ≤ 3 nhân viên; tổ chức phi lợi nhuận; đang đánh giá. Cho phép dùng thương mại | OBSERVED (LICENSE.md) |
| Công ty ≥ 4 nhân viên | Cần Company License (trả phí, có license key khi render) | DERIVED từ LICENSE.md + tóm tắt web (giá: NOT VERIFIED, có thể đổi) |
| Bản fetch LICENSE.md | Bị cắt ở phần "Allowed use cases", chưa đọc hết điều khoản hạn chế | OBSERVED - hạn chế |
| Phiên bản npm | `remotion` 4.0.534; `@remotion/cli` 4.0.534 kéo theo player, studio, bundler, renderer, mediabunny... | OBSERVED (`npm view`) |
| Kích thước gói | remotion ~1.77MB, renderer ~2.9MB unpacked, chưa tính phụ thuộc bắc cầu và Chrome Headless Shell | OBSERVED (một phần) |
| Yêu cầu hệ thống | Node ≥ 16, ffmpeg ≥ 4.1, Chrome Headless Shell tải riêng, Linux glibc ≥ 2.35 | PRIOR/web, NOT VERIFIED trên máy này |
| HyperFrames hiện tại | sandbox `_process/hyperframes_sandbox`, `node_modules` 138MB, gsap + hyperframes | OBSERVED |
| Máy | Node v22.23.1, ffmpeg 9.0.1, Python 3.14.7 | OBSERVED |
| Benchmark / render thử Remotion | Chưa chạy | NOT VERIFIED |

## 2. Trả lời 9 câu hỏi

1. **Giải quyết điều HyperFrames chưa làm được?** Có thể: mô hình component React, ecosystem (player, Lambda render phân tán, thư viện transition/chart). Chưa có bằng chứng HyperFrames hiện tại thiếu năng lực cản trở pilot. Các vấn đề thực tế đã thấy (timeout 120s, fade chồng chữ) là vấn đề preset/thời gian, không phải giới hạn engine. → NOT VERIFIED rằng có lợi thế thực.
2. **Hợp với Python orchestration?** Có, qua subprocess `npx remotion render` truyền props JSON; tương tự cách HyperFrames được gọi. DERIVED.
3. **Chi phí Node/Chrome headless?** Thêm một Chrome Headless Shell (tải riêng) và cây phụ thuộc Remotion lớn hơn gói nhỏ HyperFrames. Chưa đo. NOT VERIFIED.
4. **R0 (git sync)?** Chỉ đạt nếu có `package.json` + lockfile + script cài lại được commit trong workspace. Sandbox hiện tại ở `_process/` (gitignore) nên mẫu hiện hành cũng chưa tự đồng bộ. Cần thiết kế riêng. DERIVED.
5. **R7?** Cần adapter mới đăng ký trong `engines.json`; `render_router` đã có khái niệm adapter nên tái dùng được. Không được chép engine sang skill. DERIVED.
6. **Phụ thuộc/tải hệ thống?** Dự kiến nặng hơn 138MB của sandbox HyperFrames (Chrome + bundler + renderer). Chưa đo. NOT VERIFIED.
7. **Giấy phép thương mại?** Phụ thuộc quy mô pháp nhân. **Số nhân viên công ty của người dùng: KHÔNG BIẾT, không giả định.** Nếu ≥ 4 nhân viên thì cần Company License trả phí + license key; điều này xung đột với nguyên tắc AIWF chạy offline không cần khóa ngoài và đồng bộ qua Git (không commit key). Chưa đọc đủ LICENSE.md (bị cắt).
8. **Cần adapter riêng?** Có (props JSON ↔ composition, đọc audio/sync, báo cáo `renderer_meta`). Không đụng Storyboard contract.
9. **Tắt được mà không ảnh hưởng HyperFrames?** Có, nếu làm theo dạng adapter tuỳ chọn sau cờ cấu hình, mặc định tắt. DERIVED.

## 3. Rủi ro

- Giấy phép và license key là rủi ro lớn nhất, phụ thuộc thông tin chưa biết.
- Hai engine song song làm tăng chi phí bảo trì preset (10 preset hiện viết cho HyperFrames/GSAP; phải port sang React).
- Không có benchmark nên không thể nói nhanh hơn/đẹp hơn.

## 4. Quyết định

**INSUFFICIENT EVIDENCE → không tích hợp trong 2.1 (EXPERIMENT FURTHER khi có điều kiện).**

Điều kiện để mở lại, ngoài phạm vi 2.1:
1. Người dùng xác nhận quy mô pháp nhân và chấp nhận điều khoản giấy phép (đọc trọn LICENSE.md).
2. Pilot Phase 6 cho thấy một nhu cầu cụ thể mà HyperFrames không đáp ứng.
3. Prototype cô lập (thư mục riêng, không đụng default, không sửa setup) kèm benchmark: thời gian render, RAM, dung lượng cài, so sánh khung hình cùng storyboard.

Không có thay đổi mã trong phase này. Rollback: không cần.
