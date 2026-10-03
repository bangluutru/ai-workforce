---
name: doc-sau
display-name: Đọc Sâu
description: >-
  Phân tích chuyên sâu bài viết, sách, tài liệu học thuật và báo cáo phức tạp bằng các mô hình tư duy (SCQA, 5W2H, phản biện, đảo ngược, mô hình đa ngành, nguyên lý đệ nhất, tư duy hệ thống, 6 chiếc nón, đối chiếu đa nguồn). Đọc hết tài liệu theo từng đoạn có bảng độ phủ, mọi trích dẫn được kiểm chứng nguyên văn, kết thúc bằng 3 bài học và Quick Win 24h.
  USE WHEN: Người dùng muốn đọc hiểu sâu, mổ xẻ cấu trúc bài viết, phát hiện lỗi logic/ngụy biện, phân tích rủi ro tiềm ẩn, tổng hợp đối chiếu đa nguồn hoặc chuyển hóa tri thức thành kế hoạch thực thi 24h.
  DO NOT USE WHEN: Chỉ cần bóc tách OCR tài liệu scan (dùng 'boc-tach-pdf'), dịch văn bản đơn thuần (dùng 'ejv-translate' hoặc 'dich-giu-dinh-dang'), hoặc sáng tạo bài viết mới (dùng 'viet-bai').
trigger: Đọc Sâu, deep reading, phân tích bài viết, mổ xẻ tài liệu, tư duy phản biện, SCQA, tóm tắt sâu, phân tích sách, mổ xẻ báo cáo
category: docs
needs_file: false
file_filter: doc
---

# Kỹ Năng Đọc Sâu (v3)

<goal>
Biến việc đọc lướt thành hiểu sâu và hành động. Báo cáo đạt chuẩn khi người dùng có thể kiểm tra từng nhận định bằng câu nguyên văn trong tài liệu, thấy rõ lập luận mạnh/yếu ở đâu, và biết đúng một việc làm ngay trong 24 giờ.
</goal>

<context>
1. **Insight hơn số lượng khung**: dùng ít khung nhưng đi tới cơ chế; cấm gắn nhãn mô hình mà không giải thích nó tác động vào lập luận thế nào.
2. **Bằng chứng nguyên văn**: mọi nhận định quan trọng đi kèm câu nguyên văn, được `check_report.py` kiểm chứng tự động bằng `scripts/harness/evidence_verifier.py`.
3. **Đọc hết**: tài liệu dài được chia chunk và đọc tuần tự; bảng độ phủ cho biết đã đọc phần nào. Không kết luận về phần chưa đọc.
4. **Zero External LLM API**: toàn bộ phân tích là của Agent trong IDE; không gọi REST API ngoài, không yêu cầu API key.
5. **Autonomous Full-Run**: chạy liên tục từ tiếp nhận đến bàn giao, không dừng xin phép vụn vặt.
</context>

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Không gọi REST API ngoài, không yêu cầu API key. Script chỉ làm việc cơ học (trích văn bản, chia chunk, kiểm chứng trích dẫn).
> - Không có "đường tắt tiết kiệm token": không bỏ chunk, không bỏ bước kiểm chứng. Nếu tài liệu quá dài cho một phiên, ghi nốt ghi chú chunk và tiếp tục ở phiên sau, không tóm tắt phần chưa đọc.

---

## 🔧 Path Resolution & Thư Mục Lưu Trữ Đầu Ra

| Placeholder | Giá trị |
|---|---|
| `<skill_dir>` | `<workspace>/.agents/skills/doc-sau/` |
| `<process_dir>` | `<workspace>/_process/deep_reading_<ten_tai_lieu>/` (đã gitignore) |
| `<output_dir>` | Nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/` |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):** báo cáo `<Ten_Tai_Lieu>_Doc_Sau.md` (hoặc .docx nếu yêu cầu) lưu trong `<output_dir>`; source.txt, chunk, ghi chú, claims.json lưu trong `<process_dir>`. Không ghi vào gốc repo.

---

## Bảng Tọa Độ Đầu Vào (Intake Coordinates)

| Trục | Giá trị | Mặc định nếu người dùng không nói |
|---|---|---|
| 1. Nguồn | File (PDF có lớp chữ, DOCX, MD, TXT, HTML), văn bản dán, URL | URL: tải trang, lưu chữ vào `<process_dir>/sources/<ten>.md` rồi ingest. PDF scan: chạy `boc-tach-pdf` trước |
| 2. Mục đích đọc | Giải quyết vấn đề / Học tập / Tham khảo viết / Ra quyết định | Học tập. Mục đích quyết định 3 bài học và Quick Win |
| 3. Level | 1 Nhanh / 2 Chuẩn / 3 Sâu / 4 Nghiên cứu đối chiếu | **Level 2**; Level 3 nếu người dùng nói "phân tích kỹ", "mổ xẻ", hoặc tài liệu là chiến lược/đầu tư; Level 1 chỉ khi người dùng muốn tóm tắt nhanh |
| 4. Thư mục xuất | | `~/Downloads/AIWF_Output/` |

### Level được định nghĩa bằng ĐẦU RA (không bằng thời gian)
| Level | Mục bắt buộc trong báo cáo | Trích dẫn nguyên văn đã kiểm chứng | Độ phủ |
|---|---|---|---|
| 1 Nhanh | 0, 1, 2, 3, 4, 10, 11 | ≥ 3 | Được đọc một phần, mục 11 phải nêu phần chưa đọc |
| 2 Chuẩn | + 5 (phản biện, ≥ 2 điểm yếu có tên ngụy biện), 6 (2-3 kịch bản thất bại) | ≥ 6 | 100% chunk "Đã đọc" |
| 3 Sâu | + 7 (≥ 3 mô hình từ ≥ 2 tập Vol), 8 (đệ nhất, vòng lặp nhân quả, sáu nón) | ≥ 10 | 100% |
| 4 Nghiên cứu | + 9 (ma trận với ≥ 2 nguồn đối chiếu lưu trong `sources/`) | ≥ 14, mỗi nguồn ngoài ≥ 2 | 100% |

---

<instructions>
## QUY TRÌNH 6 BƯỚC

### BƯỚC 1: Tiếp nhận và nạp tài liệu
```bash
python3 <skill_dir>/scripts/ingest.py "<file_nguồn>" --process-dir <process_dir>
```
→ `source.txt` (nguồn để kiểm chứng trích dẫn), `chunks/chunk_NNN.md` (~6.000 ký tự/chunk), `manifest.json`, `coverage.md`.
- Văn bản dán trong chat: lưu vào `<process_dir>/sources/input.md` rồi ingest file đó.
- Level 4: tìm 2-3 tài liệu đối trọng độc lập, lưu nội dung chữ từng tài liệu vào file, rồi `ingest.py <file> --process-dir <process_dir> --as ref` → `sources/<ten>.txt`.
- Xác định thể loại và chọn tổ hợp mô hình từ `<skill_dir>/references/mental_models.md` (ma trận "Thể loại → tổ hợp").

### BƯỚC 2: Đọc tuần tự từng chunk (bắt buộc với mọi Level ≥ 2)
Với mỗi chunk theo thứ tự:
1. Đọc toàn bộ chunk.
2. Ghi `<process_dir>/notes/chunk_NNN.md`: ý chính (2-3 câu), luận điểm/bằng chứng mới, 1-3 câu nguyên văn đáng trích (chép CHÍNH XÁC, ≥ 30 ký tự), câu hỏi cần đối chiếu ở chunk sau.
3. Cập nhật dòng chunk đó trong bảng độ phủ: "Đã đọc" + ý chính 1 câu.
Không bắt đầu viết báo cáo khi còn chunk "Chưa đọc" (trừ Level 1, phải ghi rõ ở mục 11).

### BƯỚC 3: Bóc tách cấu trúc (mọi Level)
Theo `<skill_dir>/templates/bao_cao_doc_sau.md`, mục 0-4:
- Luận điểm 1 câu, 3 luận cứ + bằng chứng, khái niệm then chốt, phân loại Fact/Opinion.
- SCQA (`references/scqa_framework.md`; khung của Barbara Minto, McKinsey) + chấm độ rõ 1-5 theo thang trong template.
- 5W2H (`references/5w2h_analysis.md`): chỉ rõ thông tin thiếu/né tránh.
- Khung định hình & ẩn ý (`references/mental_models_vol4_economics_art.md`, mục Framing/Subtext).

### BƯỚC 4: Áp dụng mô hình theo Level
- **Level 2** (mục 5-6): `references/critical_thinking.md` (danh sách ngụy biện, ma trận bằng chứng) + `references/inversion_thinking.md`. Chấm độ vững 1-10 theo thang trong template; mỗi điểm yếu phải có tên lỗi + câu nguyên văn + giải thích khác có thể.
- **Level 3** (mục 7-8): chọn 3-5 mô hình từ ≥ 2 tập (`references/mental_models_vol1_general.md` … `vol4_economics_art.md`), dùng đúng "Bộ câu hỏi chất vấn" của mô hình và trả lời bằng trích dẫn; `references/first_principles.md`, `references/systems_thinking.md`, `references/six_hats.md`.
- **Level 4** (mục 9): `references/comparison_matrix.md`; mỗi ô của nguồn ngoài dẫn `(nguồn: ten_file.txt)`.

### BƯỚC 5: Viết báo cáo và kiểm chứng
1. Viết `<process_dir>/report.md` theo đúng khung `templates/bao_cao_doc_sau.md` (giữ nguyên tên mục, xóa mục không thuộc Level).
2. Trích dẫn nguyên văn đúng cú pháp: `> "câu chép đúng từng chữ, ≥ 30 ký tự" (vị trí: tr.12)`; chữ Hán/kana tính 2 ký tự. Đoạn lược dùng `[...]`. Diễn giải thì KHÔNG đặt trong ngoặc kép.
3. Chạy cổng chất lượng (lặp đến khi exit 0):
   ```bash
   python3 <skill_dir>/scripts/check_report.py --report <process_dir>/report.md --process-dir <process_dir> --level <N>
   ```
   Script kiểm tra mục bắt buộc, độ phủ, 3 bài học + Quick Win, số mô hình (Level 3), rồi gửi mọi trích dẫn vào `scripts/harness/evidence_verifier.py --claims <process_dir>/claims.json` (khớp 100%, nguồn là file cục bộ). Trích dẫn MISSING → mở lại chunk, chép lại đúng nguyên văn hoặc bỏ nhận định đó. Không sửa nguồn để khớp trích dẫn.

### BƯỚC 6: Kích hoạt tri thức và bàn giao
- Mục 10: đúng 3 bài học (mỗi bài: vì sao quan trọng với mục đích đọc + 1 hành động), đúng 1 Quick Win 24h (≤ 30 phút, có tiêu chí xong), lộ trình đi tiếp (chỉ tài liệu có thật), danh mục khung đã dùng.
- Sao chép báo cáo đạt sang `<output_dir>/<Ten_Tai_Lieu>_Doc_Sau.md`.
</instructions>

---

<quality_gate>
## TIÊU CHÍ KIỂM ĐỊNH CHẤT LƯỢNG (QUALITY GATE CHECKLIST)

- [ ] **1. check_report.py exit 0** ở đúng Level (đủ mục, đủ độ phủ, mọi trích dẫn khớp nguyên văn).
- [ ] **2. Evidence Verifier:** `evidence_result.json` có verified = total; không có trích dẫn "trang trí" (mỗi trích dẫn đỡ một nhận định cụ thể).
- [ ] **3. Trung thực (Fidelity):** không bóp méo luận điểm tác giả; tách Fact/Opinion; trình bày cách hiểu thiện chí nhất trước khi phản biện.
- [ ] **4. Không hời hợt:** mỗi mô hình nêu cơ chế + kết luận nó củng cố hay làm yếu luận điểm nào.
- [ ] **5. Rủi ro:** ≥ 2 kịch bản thất bại có dấu hiệu sớm và cách phòng (Level ≥ 2).
- [ ] **6. Hành động:** đúng 3 bài học, đúng 1 Quick Win 24h đo được.
- [ ] **7. Confidence Flagging:** chỗ tài liệu mơ hồ hoặc chưa đọc được nêu ở mục 11 với `[CẦN XÁC MINH]`.
- [ ] **8. Bảo vệ Codebase:** báo cáo ở `<output_dir>`, file trung gian ở `<process_dir>`; không gọi API ngoài.
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (CLEAN DELIVERY PROTOCOL)

1. File báo cáo: `<output_dir>/<Ten_Tai_Lieu>_Doc_Sau.md` (hoặc `.docx` nếu người dùng yêu cầu).
2. Khung chat chỉ hiển thị tóm tắt điều hành:
   - Luận điểm cốt lõi (1 câu) và độ vững lập luận (x/10).
   - SCQA rút gọn (bảng 4 dòng).
   - 3 bài học + Quick Win 24h.
   - Độ phủ (x/y chunk) và số trích dẫn đã kiểm chứng.
   - Link: `[Xem báo cáo phân tích đầy đủ](file://<duong_dan_tuyet_doi>)`.
3. Không dán toàn bộ báo cáo dài vào chat.
</delivery_protocol>
