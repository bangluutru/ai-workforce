# ĐẶC TẢ KỸ THUẬT: INTERACTIVE SKILL PATTERN (ISP V1.0)
## Chuẩn Tương Tác Hai Chiều Human-in-the-loop (HITL) Cho AI Workforce

> **Mã đặc tả:** SPEC-ISP-01  
> **Quy chuẩn cha:** Rule R4 (Skill Standard v1.2) & Rule R3 (Operational Discipline)  
> **Phạm vi:** Các kỹ năng tương tác đa phương tiện, thị giác, bố cục (`phu-de`, `thiet-ke`, `boc-tach-pdf`, `bao-cao-kt`, `xu-ly-van-phong`)

---

## 1. NGUYÊN LÝ THIẾT KẾ

Interactive Skill Pattern (ISP) ra đời nhằm giải quyết bài toán: **Giao diện chat văn bản thuần túy không thể đáp ứng nhu cầu xem trước trực quan (Visual Preview), điều khiển thông số trực tiếp (Direct Manipulation) và lặp hiệu chỉnh hai chiều (Iterative Refinement).**

### 4 Tiêu chí cốt lõi:
1. **Interaction Surface, Not a Standalone App:** Giao diện là bề mặt tương tác tạm thời (Webview Panel) gắn liền với phiên xử lý của Skill, không phải một phần mềm SaaS độc lập.
2. **Deterministic at Client, Cognitive at Agent:** Mọi thao tác đổi màu, chỉnh font, dịch chuyển pixel, căn lề, crop ảnh xử lý 100% tại client với độ trễ 0ms và 0 token. Chỉ những yêu cầu mang tính ngữ nghĩa, lập luận, viết lại, dịch thuật mới được chuyển giao cho Agent.
3. **Selective Patching Over Full Regeneration:** Khi Agent can thiệp, Agent chỉ sinh ra bản vá (patch) cho đúng các đối tượng được chọn (Target IDs). Cấm ghi đè hoặc sinh lại toàn bộ dự án làm mất dữ liệu chỉnh sửa thủ công của người dùng.
4. **Zero External API & Git-Sync Compliant:** Toàn bộ dữ liệu phiên làm việc lưu trong thư mục `_process/<project_id>/` (đã gitignored). Thành phẩm xuất bản lưu vào `<output_dir>` (`~/Downloads/`). Không yêu cầu API key bên ngoài.

---

## 2. VÒNG ĐỜI DỰ ÁN TƯƠNG TÁC (PROJECT LIFECYCLE)

```
[1. INTAKE & DRAFT]
  User ra lệnh ──► Agent chạy công cụ deterministic + LLM suy luận sơ khởi
               ──► Khởi tạo _process/<id>/project.json (Status: "in_review")

[2. OPEN INTERACTION SURFACE]
  Extension phát hiện project mới ──► Tự động mở Webview Editor Tab trong IDE
                                 ──► Nạp UI miền nghiệp vụ (phu-de, thiet-ke...)

[3. THE COLLABORATIVE EDIT LOOP]
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Local Actions (Direct Edit):                                           │
  │   • Sửa font, màu, căn lề, kéo timeline, sửa text thủ công             │
  │   ──► UI lưu trực tiếp vào project.json & tạo snapshot lịch sử         │
  │                                                                        │
  │ Agent Actions (AI Intent):                                             │
  │   • Chọn đối tượng + gõ: "Rút ngắn câu", "Chuyển tone trang trọng"     │
  │   ──► UI gửi Action Request có cấu trúc qua postMessage                │
  │   ──► Extension chuyển lệnh vào Antigravity Chat                       │
  │   ──► Agent tiếp nhận, dùng tool cập nhật project.json (Selective Patch)│
  │   ──► Webview nhận state_updated, cập nhật preview thời gian thực       │
  │                                                                        │
  │ Undo / Redo:                                                           │
  │   • Người dùng có thể quay lại bất kỳ snapshot nào trong lịch sử       │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │
                                      ▼
[4. FINALIZE & CLEAN DELIVERY]
  User bấm "Xác nhận & Xuất bản" ──► project.json chuyển status: "finalized"
                                 ──► Extension thông báo Agent chạy Render cuối
                                 ──► Công cụ media (FFmpeg, Weasyprint...) xuất file
                                 ──► File kết quả nằm gọn gàng tại ~/Downloads/
                                 ──► Đóng Webview, dọn dẹp tài nguyên
```

---

## 3. KHUNG DỮ LIỆU EDITABLE PROJECT STATE (`project.json`)

Mọi Interactive Skill phải xuất và duy trì một file `project.json` duy nhất tại `<process_dir>/project.json`:

```json
{
  "$schema_version": "1.0",
  "project_id": "unique_string_id",
  "skill": "ten-skill",
  "status": "draft | in_review | finalized | exported",
  "meta": {
    "source_file": "/path/to/source.mp4",
    "created_at": "2026-09-06T00:30:00Z",
    "updated_at": "2026-09-06T00:35:10Z"
  },
  "config": {
    "output_dir": "/Users/username/Downloads",
    "export_preset": "default"
  },
  "history": {
    "current_revision": 3,
    "snapshots": ["rev_001.json", "rev_002.json", "rev_003.json"]
  },
  "data": {
    /* KHU VỰC DỮ LIỆU ĐẶC THÙ (DOMAIN DATA) */
    /* QUY TẮC BẮT BUỘC: Mọi đối tượng có thể sửa đổi PHẢI có Stable ID duy nhất dạng chuỗi */
    "entities": [
      {
        "id": "item_001",
        "content": "Nội dung văn bản hoặc thông số",
        "style": { "fontSize": 24, "color": "#FFFFFF" },
        "metadata": { "confidence": 0.95 }
      }
    ]
  }
}
```

---

## 4. HỢP ĐỒNG GIAO TIẾP AGENT ↔ UI (COMMUNICATION CONTRACT)

### 4.1 Gói tin Yêu cầu từ UI (Agent Action Request)

Khi người dùng kích hoạt một lệnh AI trên giao diện:

```json
{
  "request_id": "req_20260906_01",
  "action": "rewrite_text | translate | reformat | restyle | summarize",
  "instruction": "Yêu cầu chi tiết từ người dùng (ví dụ: Rút ngắn câu, giữ nguyên ý)",
  "scope": "selection | all | filter",
  "target_ids": ["item_002", "item_005"],
  "context_snapshot": {
    "item_002": { "content": "Văn bản hiện tại trước khi sửa" }
  }
}
```

### 4.2 Gói tin Prompt Chuyển tiếp vào Chat (`sendToAntigravityChat`)

Extension nhận Action Request từ Webview và tự động định dạng thành prompt có cấu trúc:

```text
[INTERACTIVE ACTION: <skill_name>]
Dự án: <đường_dẫn_project.json>
Hành động: <action>
Yêu cầu người dùng: <instruction>
Các đối tượng tác động (Target IDs): [<id_1>, <id_2>]

Chỉ dẫn thực thi cho Agent:
1. Đọc nội dung hiện tại của các đối tượng trên trong file project.json.
2. Áp dụng tư duy ngôn ngữ / thẩm mỹ để tạo giá trị mới phù hợp với yêu cầu.
3. Sử dụng công cụ `replace_file_content` để cập nhật trực tiếp vào file project.json.
4. TUYỆT ĐỐI KHÔNG sửa đổi các trường khác hoặc các đối tượng không nằm trong danh sách Target IDs.
```

### 4.3 Phản hồi của Agent (Selective Patch)

Agent thực thi và cập nhật file `project.json` trên đĩa. Webview bắt sự kiện file thay đổi (thông qua FileWatcher của Extension) và gửi `state_updated` để re-render giao diện mà không cần reload trang.

---

## 5. CƠ CHẾ SNAPSHOTS & UNDO / REDO

* Mỗi khi có thay đổi trạng thái mang tính bước ngoặt:
  - Hành động Agent Action hoàn tất.
  - Phân tách (Split) hoặc Gộp (Merge) khối đối tượng.
  - Phục hồi (Reset) về thiết lập ban đầu.
* Runtime tự động tạo một bản ghi tại `<process_dir>/snapshots/rev_<revision_number>.json`.
* Thao tác **Undo**: Khôi phục `project.json` từ snapshot trước đó.
* Thao tác **Redo**: Tiến tới snapshot kế tiếp.

---

## 6. QUY ĐỊNH BẢO VỆ & AN TOÀN HỆ THỐNG

1. **Giới hạn số lượng Snapshots**: Tối đa 20 bản ghi gần nhất để tránh tiêu tốn dung lượng ổ đĩa.
2. **Tự động giải phóng (Auto Cleanup)**: Khi người dùng đóng tab hoặc tác vụ hoàn tất, runtime ghi nhận và dọn dẹp các tệp tạm nếu được yêu cầu.
3. **Claim Guard Scanner**: Các tác vụ viết lại text thông qua Agent Action phải tuân thủ nghiêm ngặt **Luật R5 (Legal Claim Compliance)**.
