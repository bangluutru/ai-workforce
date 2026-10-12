# 🎭 BẢN ĐỒ VAI TRÒ TÁC NHÂN (AGENT ROLE REGISTRY)
## Hệ Thống Quản Trị Đa Vai Trò AI Workforce (AIWF)

> **Mã quy chuẩn:** SPEC-ROLE-01  
> **Nguyên tắc phân định cốt lõi:** **ROLE $\ne$ SKILL $\ne$ ENGINE**

---

## 1. PHÂN BIỆT RÕ RÀNG BA TẦNG KIẾN TRÚC

Trong AI Workforce, mọi thành phần được tổ chức thành 3 tầng rành mạch, triệt tiêu sự trùng lặp (Luật R7):

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. ROLE (Vai Trò & Trách Nhiệm) — Thư mục: .agents/roles/              │
│    Định vị "AI NÀO LÀM GÌ, THEO GÓC NHÌN NÀO, TRÁCH NHIỆM TỚI ĐÂU".  │
│    - Không chứa mã nguồn thực thi hay scripts nhị phân.               │
│    - Khai báo: purpose, responsibilities, allowed_skills,            │
│      quality_criteria, permission_boundaries, handoff_contract.      │
├────────────────────────────────────────────────────────────────────────┤
│ 2. SKILL (Kỹ Năng Nghiệp Vụ) — Thư mục: .agents/skills/               │
│    Định vị "NĂNG LỰC NGHIỆP VỤ THỰC CHIẾN VÀ QUY TRÌNH THỰC THI".    │
│    - 19 Kỹ năng chuẩn mực: boc-tach-pdf, dich-thuat, video-studio...   │
│    - Chứa SKILL.md, tài liệu nghiệp vụ, scripts xử lý dữ liệu.         │
├────────────────────────────────────────────────────────────────────────┤
│ 3. ENGINE (Cỗ Máy Dùng Chung) — Thư mục: .agents/skills/_shared/      │
│    Định vị "CÔNG CỤ NỀN TẢNG DETERMINISTIC VÀ TÍNH TOÁN DÙNG CHUNG".   │
│    - Đăng ký máy đọc trong engines.json và ENGINES.md.                 │
│    - doc_ingest, docx, pdf, media (TTS, ffmpeg, ASS), creative, layout│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DANH MỤC 10 VAI TRÒ CHUẨN MỰC (10 ROLES)

| ID Vai Trò | Tên Hiển Thị | Mục Đích Cốt Lõi | Kỹ Năng Được Gọi (`allowed_skills`) |
|---|---|---|---|
| `systems-architect` | Multi-Agent Systems Architect | Phân rã cấu trúc luồng, kiểm soát context budget, định nghĩa hợp đồng I/O | `tao-landing-page`, `app-auditor` |
| `reality-checker` | Reality Checker | Chống phê duyệt ảo tưởng, mặc định "NEEDS WORK", kiểm chứng bằng chứng thực tế | `app-auditor`, `dich-thuat`, `boc-tach-pdf` |
| `evidence-collector` | Evidence Collector | Thu thập và xác thực bằng chứng kỹ thuật (exit code, logs, screenshots, hashes) | `app-auditor`, `video-studio`, `bao-cao-kt` |
| `minimal-change-engineer` | Minimal Change Engineer | Phẫu thuật vi mô (Rule R2), diff nhỏ nhất giải quyết vấn đề, chống phình code | `tao-landing-page`, `xu-ly-van-phong` |
| `project-shepherd` | Project Shepherd | Điều phối tiến độ runbook, theo dõi handoff giữa các phase, báo cáo bàn giao | Mọi skill thông qua runbook |
| `ux-reviewer` | UX & Usability Reviewer | Thẩm định trải nghiệm người dùng, độ nhạy responsive, tương thích WCAG a11y | `app-auditor`, `thiet-ke` |
| `brand-guardian` | Brand Guardian | Bảo vệ nhận diện thương hiệu, hệ thống màu sắc, typography token, tone & voice | `thiet-ke`, `viet-bai`, `video-studio` |
| `research-synthesist` | Research & Evidence Synthesist | Truy vết nguồn gốc dữ liệu, phân loại trọng số bằng chứng, đối chiếu SSOT | `doc-sau`, `chotto-newsroom` |
| `legal-compliance-reviewer` | Legal & Regulatory Reviewer | Thẩm định tính hợp chuẩn tiếp thị (Rule R5), trích dẫn quy phạm pháp luật | `tu-van-phap-luat`, `tu-van-thue`, `viet-bai` |
| `technical-auditor` | Technical & Security Auditor | Kiểm toán an toàn mã nguồn, hiệu năng, kiểm tra R7 shared reuse, cú pháp | `app-auditor`, `bao-cao-kt` |

---

## 3. HỢP ĐỒNG BẮT BUỘC CỦA MỖI FILE ROLE (`.agents/roles/<role_id>.md`)

Mỗi file vai trò bắt buộc phải có đầy đủ 11 trường thông tin sau trong YAML frontmatter:
1. `role_id`: Mã định danh dạng kebab-case.
2. `display_name`: Tên hiển thị giao diện tiếng Việt hoặc chuẩn chính tả.
3. `purpose`: Mục đích tối thượng của vai trò.
4. `responsibilities`: Danh sách các trách nhiệm cụ thể.
5. `allowed_skills`: Danh sách các skill thuộc `.agents/skills/` mà role được phép ủy nhiệm thực thi.
6. `required_inputs`: Dữ liệu đầu vào bắt buộc để role hoạt động.
7. `expected_outputs`: Sản phẩm đầu ra mà role phải bàn giao.
8. `quality_criteria`: Tiêu chuẩn nghiệm thu chất lượng công việc của role.
9. `permission_boundaries`: Ranh giới quyền hạn (những gì ĐƯỢC và KHÔNG ĐƯỢC phép làm).
10. `handoff_contract`: Quy chuẩn chuyển giao artifact cho vai trò kế tiếp.
11. `escalation_conditions`: Điều kiện bắt buộc phải leo thang lên người dùng.
