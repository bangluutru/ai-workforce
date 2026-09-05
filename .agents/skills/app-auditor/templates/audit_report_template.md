# BÁO CÁO THẨM ĐỊNH CHẤT LƯỢNG ỨNG DỤNG (APP AUDIT REPORT)

> **Ứng dụng mục tiêu:** {target_url}  
> **Thời gian thực hiện:** {timestamp}  
> **Môi trường thử nghiệm:** Chromium Headless (macOS Apple Silicon)  
> **Chế độ kiểm thử:** {mode} (Adversarial QA + Multi-Viewport Visual Sweep)  

---

## 1. TỔNG KẾT ĐIỂM CHẤT LƯỢNG (OVERALL SCORE)

### 🏆 ĐIỂM TỔNG HỢP: **{overall_score} / 10.0**

| Danh mục kiểm tra | Trọng số | Điểm số | Trạng thái |
|---|:---:|:---:|:---:|
| ⚙️ Chức năng (Functional) | 25% | {functional_score}/10 | {functional_status} |
| 🧠 Logic & State Management | 20% | {logic_score}/10 | {logic_status} |
| 📱 Tính phản hồi & Di động (Responsive) | 15% | {responsive_score}/10 | {responsive_status} |
| 👁️ Trải nghiệm người dùng (UX) | 15% | {ux_score}/10 | {ux_status} |
| 🎨 Giao diện & Nhất quán (Visual) | 10% | {visual_score}/10 | {visual_status} |
| ♿ Trợ năng (Accessibility WCAG A/AA) | 10% | {a11y_score}/10 | {a11y_status} |
| 🛡️ Độ ổn định Runtime (Console/Network) | 5% | {stability_score}/10 | {stability_status} |

---

## 2. DANH SÁCH VẤN ĐỀ THEO MỨC ĐỘ ƯU TIÊN (ISSUES BY PRIORITY)

### 🔴 Mức Độ Nguy Cấp (P0 - Blocker)
{p0_issues_block}

### 🟠 Mức Độ Nghiêm Trọng (P1 - Serious)
{p1_issues_block}

### 🟡 Vấn Đề Giao Diện & Trải Nghiệm (P2 - UX & Functional)
{p2_issues_block}

### 🔵 Sai Lệch Thiết Kế & Nhất Quán (P3 - Cosmetic & Consistency)
{p3_issues_block}

### 💡 Kiến Nghị Cải Thiện (P4 - Recommendations)
{p4_issues_block}

---

## 3. CÁC HẠNG MỤC ĐÃ KIỂM TRA ĐẠT CHUẨN (PASSED CHECKS)
{passed_checks_list}

---

## 4. LỘ TRÌNH KHẮC PHỤC KHUYẾN NGHỊ (RECOMMENDED FIX ORDER)
{recommended_fix_order}

---

## 5. THÔNG TIN BẰNG CHỨNG KỸ THUẬT (TECHNICAL ARTIFACTS)
- Thư mục ảnh chụp màn hình kiểm chứng: `{screenshot_dir}`
- File dữ liệu thô (JSON): `{data_json_path}`
