# Landing Hub Integration Contract (v1.0 Reference)

> Nguồn Sự Thật Duy Nhất (SSOT): `/Users/tranhaibang/.gemini/antigravity-ide/scratch/landing-hub/docs/INTEGRATION-CONTRACT-v1.md`
> Phiên bản: 1.0 (Frozen)

Mọi Landing Page do kỹ năng `tao-landing-page` sinh ra BẮT BUỘC tuân thủ 10 bất biến kiến trúc sau:

## 1. 10 Bất biến Kiến trúc (10 Invariants)
1. **Zero Direct Database Writes**: Tuyệt đối không kết nối hoặc ghi trực tiếp vào Cloud Firestore hoặc cơ sở dữ liệu nội bộ. Toàn bộ tương tác phải đi qua Ingestion API hoặc SDK `LPHub`.
2. **Mandatory Ingestion Gateway**: Mọi tương tác, lead, đơn hàng, custom form và sự kiện chuyển đổi phải gửi qua Ingestion endpoints.
3. **Strict Hierarchy Verification**: Phân cấp `projectId` -> `landingPageId` -> `formId` bắt buộc phải tồn tại, đang hoạt động (`status: 'active'`), và thuộc đúng cha.
4. **Endpoint-to-FormType Alignment**:
   - `form.type === 'lead'` -> `/api/lead` (`LPHub.submitLead()`).
   - `form.type === 'order'` -> `/api/order` (`LPHub.submitOrder()`).
   - `form.type === 'custom'` -> `/api/custom-form` (`LPHub.submitCustomForm()`).
5. **Origin & Domain Validation**: Request từ trình duyệt trong production phải thuộc `project.allowedDomains` hoặc khớp `landingPage.url`.
6. **Stable Submission Identity**: Một lần bấm gửi form tương ứng một `submissionId` / `idempotencyKey` duy nhất, giữ nguyên khi retry.
7. **Authoritative Backend Idempotency**: Gửi lại cùng key trả về HTTP 200 `idempotentReplay: true`, không tạo bản ghi mới hay bắn lại sự kiện chuyển đổi.
8. **Conversion Semantics Separation**: Tuyệt đối KHÔNG gộp `order_created` thành `purchase`. Sự kiện `purchase` chỉ bắn khi có xác nhận thanh toán tin cậy.
9. **Unverified Client Revenue**: Giá trị tổng tiền từ client chỉ ghi nhận `verifiedRevenue: false` cho đến khi đối soát catalog.
10. **Zero Custom Storage Bypass**: Tuyệt đối không lưu form qua Google Sheets tạm, email script tự chế hoặc database thứ ba.

## 2. Phương thức SDK Chuẩn (`lphub.ts`)
```typescript
LPHub.init(config: LPHubConfig): void;
LPHub.track(eventName: string, metadata?: Record<string, any>): Promise<ApiResponse>;
LPHub.submitLead(payload: LeadSubmissionPayload): Promise<ApiResponse>;
LPHub.submitOrder(payload: OrderSubmissionPayload): Promise<ApiResponse>;
LPHub.submitCustomForm(payload: CustomFormPayload): Promise<ApiResponse>;
LPHub.createSubmission(formId: string): SubmissionSession;
```
