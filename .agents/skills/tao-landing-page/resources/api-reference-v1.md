# Landing Hub API Reference (v1.0 Reference)

> Nguồn Sự Thật Duy Nhất (SSOT): `/Users/tranhaibang/.gemini/antigravity-ide/scratch/landing-hub/docs/API-REFERENCE-v1.md`

## 1. Ingestion Endpoints
- `POST /api/track`: Ghi nhận sự kiện hành vi và phễu chuyển đổi.
- `POST /api/lead`: Gửi form tư vấn, đăng ký nhận mẫu quà tặng (`form.type === 'lead'`).
- `POST /api/order`: Gửi đơn đặt hàng, COD, pre-order (`form.type === 'order'`).
- `POST /api/custom-form`: Gửi dữ liệu trắc nghiệm, tính điểm, khảo sát (`form.type === 'custom'`).
- `GET /api/health`: Kiểm tra trạng thái hoạt động backend (`{ "status": "ok", "persistence": "Cloud Firestore" }`).

## 2. Admin Endpoints (Yêu cầu Bearer Token)
- `GET /api/projects` & `POST /api/projects`: Quản trị dự án.
- `GET /api/landing-pages` & `POST /api/landing-pages`: Quản trị trang đích.
- `GET /api/forms` & `POST /api/forms`: Quản trị định nghĩa form.
- `GET /api/leads` & `GET /api/orders` & `GET /api/events`: Truy vấn dữ liệu thực tế.

## 3. Mã Lỗi Chuẩn (Error Codes)
- `MISSING_REQUIRED_FIELDS` (400)
- `PROJECT_NOT_FOUND` (400)
- `PROJECT_INACTIVE` (400)
- `LP_NOT_FOUND` (400)
- `LP_INACTIVE` (400)
- `INVALID_LP_HIERARCHY` (400)
- `FORM_NOT_FOUND` (400)
- `FORM_INACTIVE` (400)
- `INVALID_FORM_HIERARCHY` (400)
- `INVALID_FORM_TYPE` (400)
- `EMPTY_ITEMS` (400)
- `UNAUTHORIZED` (401)
- `ORIGIN_NOT_ALLOWED` (403)
- `RATE_LIMIT_EXCEEDED` (429)
