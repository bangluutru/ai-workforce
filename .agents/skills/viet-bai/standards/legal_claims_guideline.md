# HƯỚNG DẪN THẨM ĐỊNH PHÁP LÝ NỘI DUNG & CHỐNG OVER-CLAIM CHO BÀI VIẾT (LEGAL CLAIMS GUIDELINE)

Tuân thủ **Luật R5** (`.agents/rules/R5-legal-claim-compliance.md`) và hệ thống pháp luật Việt Nam (Luật Quảng cáo 2012, Nghị định 181/2013/NĐ-CP, Nghị định 38/2021/NĐ-CP, Thông tư Bộ Y tế 06/2011/TT-BYT).

---

## 1. Nguyên Tắc Cốt Lõi Khi Soạn Thảo
1. **Tuyệt đối không dùng từ ngữ khẳng định tuyệt đối**:
   - Tránh xa: *"an toàn tuyệt đối"*, *"100% không tác dụng phụ"*, *"không kích ứng với mọi loại da"*, *"vĩnh viễn"*, *"trọn đời"*.
   - Thay thế bằng: *"dịu nhẹ và lành tính"*, *"công thức được kiểm nghiệm dịu nhẹ"*, *"hạn chế nguy cơ kích ứng cho da nhạy cảm"*, *"hiệu quả bền lâu theo chu trình sử dụng"*.
2. **Không biến mỹ phẩm/TPCN thành thuốc điều trị**:
   - Tránh xa: *"đặc trị"*, *"trị dứt điểm"*, *"chữa khỏi"*, *"tiêu diệt tận gốc"*, *"thuốc phủ bạc"*, *"thuốc nhuộm"*.
   - Thay thế bằng: *"hỗ trợ che phủ tóc bạc tự nhiên"*, *"phủ màu tóc bạc"*, *"dầu gội phủ màu"*, *"kem ủ phủ màu"*.
3. **Minh bạch bằng chứng khi dùng từ so sánh**:
   - Nếu viết *"dẫn đầu thị phần"*, *"bán chạy hàng đầu"*, *"37 triệu chai"*, bắt buộc ghi rõ: *"Theo số liệu do Pyuru công bố giai đoạn 2011 - 2025"*.
4. **Luôn có Disclaimer chuẩn**:
   - Mỹ phẩm: *"Sản phẩm mỹ phẩm chăm sóc tóc, không phải là thuốc."*

---

## 2. Quy Trình Kiểm Thử Trước Khi Bàn Giao
Trước khi xuất bản bất kỳ bài viết nào, Agent bắt buộc chạy:
```bash
python3 .agents/skills/viet-bai/scripts/fact_checker.py --input "<đường_dẫn_file>"
```
File chỉ được phép bàn giao khi kết quả báo cáo:
- ✅ 0 dấu vết AI (em-dash, Oxford comma, colon at end of heading, banned buzzwords).
- ✅ 0 vi phạm over-claim theo Rule R5.
