# Tiêu chuẩn Sinh Mã Nguồn Landing Page (React + Vite + TS + Tailwind)

## 1. Cấu trúc Thư mục Chuẩn
```
landing-page/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── lib/
    │   └── lphub.ts          # Landing Hub Client SDK v1.1.0
    ├── types/
    │   └── landing.ts        # Data structures for sections & forms
    └── components/
        ├── Header.tsx
        ├── Hero.tsx
        ├── Benefits.tsx
        ├── Features.tsx
        ├── ProductDetail.tsx
        ├── OrderForm.tsx     # (Hoặc LeadForm.tsx / CustomForm.tsx)
        ├── Testimonials.tsx
        ├── FAQ.tsx
        └── Footer.tsx
```

## 2. Quy tắc Thiết kế Component
1. **Module hóa sạch sẽ:** Mỗi section là 1 React Functional Component độc lập trong `src/components/`.
2. **Không hardcode credentials:** Không đưa API token quản trị vào client code. `LPHub.init()` chỉ nhận `projectId`, `landingPageId`, `apiUrl`.
3. **Quản lý Form State:** Sử dụng state rõ ràng (`submitting`, `submitted`, `error`, `retrying`). Khi đang gửi form, nút bấm phải bị vô hiệu hóa (`disabled`) và hiển thị spinner/icon xoay.
4. **Attribution & Event Binding:**
   - Nút CTA mua hàng/tư vấn: Gắn `onClick={() => LPHub.track('cta_click', { buttonId: '...', section: '...' })}`.
   - Form gửi qua SDK: Gắn `LPHub.submitOrder()` hoặc `LPHub.submitLead()`.
