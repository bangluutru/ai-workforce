# 📘 SỔ TAY KỊCH BẢN ĐỘI HÌNH (TEAM RUNBOOKS)
## Hệ Thống Điều Phối Đa Vai Trò Tuần Tự AI Workforce (AIWF)

> **Mã quy chuẩn:** SPEC-RUNBOOK-01  
> **Mô hình thực thi:** **Sequential Role-Based Execution with Evidence Gates & HITL Checkpoints**  
> **Nguyên tắc minh bạch:** Antigravity IDE thực thi tuần tự có cấu trúc, phối hợp subagent fork khi cần cách ly ngữ cảnh, tuyệt đối không phóng đại thành "parallel autonomous swarm".

---

## 1. MỤC ĐÍCH & KIẾN TRÚC RUNBOOK

Team Runbook là sổ tay quy trình vận hành tiêu chuẩn (SOP) cấp cao, đóng vai trò là "nhạc trưởng" điều phối một nhóm các **Vai trò (Roles)** và **Kỹ năng (Skills)** để giải quyết những bài toán phức hợp, đa chặng mà một kỹ năng đơn lẻ không thể bao quát hết.

```
┌────────────────────────────────────────────────────────────────────────┐
│                      TEAM RUNBOOK ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────────┤
│ [INTAKE] ──► Tiếp nhận brief, xác định Runbook & khởi tạo Evidence Pack │
│                                                                        │
│ [PHASE 1] ──► Role 1 + Skill A ──► Artifact 1 ──► Handoff Contract     │
│                                                                        │
│ [CHECKPOINT 1] ──► Phê duyệt Kế hoạch & Phạm vi (Plan Approval Gate)    │
│                                                                        │
│ [PHASE 2] ──► Role 2 + Skill B ──► Artifact 2 ──► Verification Gate    │
│                                                                        │
│ [PHASE 3] ──► Role 3 + Skill C ──► Artifact 3 ──► Reality Check Gate   │
│                                                                        │
│ [CHECKPOINT 2] ──► Phê duyệt Bằng chứng Kỹ thuật (Evidence Review Gate) │
│                                                                        │
│ [FINAL PHASE] ──► Project Shepherd ──► Gói Bàn Giao Sạch (Clean Deliv)  │
│                                                                        │
│ [CHECKPOINT 3] ──► Xác nhận Nghiệm thu & Xuất bản (Publish Gate)       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DANH MỤC 4 RUNBOOK CHUẨN MỰC

| Mã Runbook | Tên Kịch Bản | Mục Tiêu & Sản Phẩm Đầu Ra | Đội Hình Vai Trò (Roster) | Kỹ Năng Huy Động |
|---|---|---|---|---|
| `build-webapp` | Xây Dựng Ứng Dụng Web | Mã nguồn web tương tác (React/Vite/Tailwind), báo cáo audit 4 viewports, 0 lỗi console, đạt WCAG AA | `systems-architect`, `minimal-change-engineer`, `evidence-collector`, `reality-checker`, `ux-reviewer`, `project-shepherd` | `tao-landing-page`, `app-auditor` |
| `produce-video` | Sản Xuất Video Truyền Thông | Video MP4 full HD hoàn chỉnh (giọng đọc AI, BGM ducking, phụ đề karaoke, motion graphics), Visual QA report | `research-synthesist`, `legal-compliance-reviewer`, `brand-guardian`, `evidence-collector`, `project-shepherd` | `chotto-newsroom`, `viet-bai`, `video-studio` |
| `marketing-campaign` | Chiến Dịch Nội Dung Đa Kênh | Bộ bài viết Blog/PR/Social, ấn phẩm đồ họa in ấn/digital, 100% đạt chuẩn Luật R5 claim_guard.py | `research-synthesist`, `brand-guardian`, `legal-compliance-reviewer`, `reality-checker`, `project-shepherd` | `viet-bai`, `thiet-ke` |
| `research-repository` | Nghiên Cứu & Đọc Sâu Dữ Liệu | Bản đồ bằng chứng trích dẫn, báo cáo phân tích 10 mô hình tư duy, executive summary, kế hoạch hành động 24h | `research-synthesist`, `systems-architect`, `technical-auditor`, `reality-checker`, `project-shepherd` | `doc-sau`, `chotto-newsroom` |

---

## 3. CÁC QUY TẮC CỐT LÕI KHI THỰC THI RUNBOOK

1. **Tuần Tự & Hợp Đồng Bàn Giao (Strict Sequential Handoff):**
   - Mỗi phase kết thúc bằng một Artifact có cấu trúc và trạng thái bằng chứng xác định trong `evidence_pack.json`. Phase kế tiếp chỉ bắt đầu khi phase trước đạt trạng thái hợp lệ.
2. **Kỷ Luật Phẫu Thuật Vi Mô (Minimal Change - Rule R2):**
   - Trong quá trình phát triển mã nguồn, mọi thay đổi phải tuân thủ nghiêm ngặt nguyên tắc của `minimal-change-engineer`: diff nhỏ nhất giải quyết bài toán, cấm refactor lan man.
3. **Bảo Vệ Codebase (Anti-Repo Bloat - Rule R1 & R0):**
   - Mọi thành phẩm xuất bản (HTML, MP4, DOCX, JSON, ảnh) PHẢI được lưu vào thư mục `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/<runbook_id>_<timestamp>/`). Không lưu file kết quả vào kho mã nguồn Git.
4. **Không Thể Bỏ Qua Cổng Phê Duyệt (Enforced Human Gates):**
   - Tác nhân AI KHÔNG ĐƯỢC phép tự ý giả lập hoặc bỏ qua các Checkpoint phê duyệt của người dùng.
