# Tiêu chuẩn mã nguồn Landing Page (React + Vite + TS + Tailwind)

## 1. Kiến trúc dữ liệu -> giao diện
```
landing_spec.json  --landing_builder.py-->  src/content.json   (mọi câu chữ)
                                            src/theme.css      (mọi màu/font/bo góc = CSS variables)
                                            public/fonts, public/images (tự host)
templates/react_vite_template/src/components/*.tsx  (mã TĨNH, không chứa câu chữ marketing)
```
- KHÔNG ghép chuỗi nội dung vào JSX bằng Python. Muốn thêm loại section -> thêm component tĩnh + type trong `types/content.ts`.
- Component chỉ dùng class `brand-*` (`bg-brand-primary`, `text-brand-muted`, `border-brand-border`...). Cấm `slate-*`, `teal-*`, `purple-*`... (qa_runner Gate 2 chặn).
- Chuỗi `[CẦN XÁC MINH: ...]` được `<Text>` tô vàng viền đứt - không bao giờ xuất bản khi còn chuỗi này.

## 2. Landing Hub
- `apiUrl` = `import.meta.env.VITE_LPHUB_URL`. `npm run build` (production) DỪNG nếu URL rỗng / không https / trỏ localhost. Bản kiểm thử: `npm run build:qa` (đọc `.env.qa`).
- `LPHub.init({ projectId, landingPageId, apiUrl, autoPageView: true })` trong `App.tsx`; id lấy từ `content.json.hub`.
- Client chỉ bắn `page_view` (tự động), `cta_click`, `form_view`, `form_start`. `form_submit` / `order_created` / `purchase` do máy chủ ghi - KHÔNG bắn từ client.
- Form gửi qua `LPHub.createSubmission(formId)` -> idempotency key giữ nguyên khi người dùng bấm "Thử gửi lại".
- Không token quản trị, không Firestore, không Google Sheets trong client.

## 3. Nền tảng web hiện đại (không cần thư viện ngoài, không cần tra cứu online)
- Ảnh hero (LCP): `loading="eager"`, `fetchpriority="high"`, có `width/height`, `<link rel="preload">` trong `index.html`.
- Section dưới màn hình đầu: class `below-fold` (`content-visibility: auto`).
- Form: label `htmlFor` gắn đúng ô, `autocomplete`, `inputmode`, lỗi hiển thị bằng `:user-invalid` (chỉ sau khi người dùng tương tác), nút gửi `disabled` + `aria-busy` khi đang gửi.
- FAQ dùng `<details>/<summary>` native; modal (nếu có) dùng `<dialog>` native.
- Vùng chạm tối thiểu 44px; chữ thân >= 16px trên mobile; tương phản >= 4.5:1 (builder kiểm tra token).
- Font tự host (Be Vietnam Pro / Spectral, OFL) - không gọi Google Fonts/CDN; ảnh tự host trong `public/images`.
