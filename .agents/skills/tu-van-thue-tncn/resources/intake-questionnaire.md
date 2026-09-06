# BỘ KỊCH BẢN CÂU HỎI TRẮC NGHIỆM TƯƠNG TÁC THUẾ TNCN 2026 (QUESTIONNAIRE WIZARD)
> Dành cho Cổng Tư Vấn Thuế TNCN - Antigravity AI Workforce  
> Căn cứ kỳ tính thuế 2026: Luật 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP, TT 87/2026/TT-BTC, NĐ 141/2026/NĐ-CP, Luật BHXH 2024.  
> Tệp cấu trúc máy đọc: `resources/questionnaire_tree.json` | Script điều hướng: `scripts/interactive_wizard.py`

---

## 1. NGUYÊN TẮC VẬN HÀNH KỊCH BẢN CHUẨN BỊ SẴN
1. **Chuyển tiếp tức thì (Zero Latency):** Khi người dùng kích hoạt, hệ thống hiển thị câu hỏi trắc nghiệm gốc (`root_question`). Ngay khi người dùng chọn xong 1 đáp án, hệ thống lập tức chuyển sang câu hỏi tiếp theo trong nhánh kịch bản mà không dừng lại phân tích hay suy luận giữa chừng.
2. **Hỗ trợ nhập số tiền cụ thể (Write-in Support):** Mỗi câu hỏi trắc nghiệm đều tích hợp sẵn ô viết tự do trong hộp thoại UI `ask_question`. Người dùng có thể click chọn mốc phổ biến hoặc gõ số tiền chính xác (ví dụ: *37.500.000 VNĐ*).
3. **Câu hỏi ghi chú cuối cùng (Final Notes):** Mọi nhánh kịch bản đều kết thúc bằng câu hỏi thu thập ghi chú thêm của người dùng trước khi chuyển giao dữ liệu cho động cơ tính toán và xuất bản báo cáo.

---

## 2. BẢN ĐỒ CÂU HỎI TRẮC NGHIỆM 6 CHUYÊN ĐỀ

### CÂU HỎI GỐC (ROOT QUESTION):
*Bạn đang cần Antigravity AI Workforce tư vấn chuyên đề thuế hoặc bảo hiểm nào dưới đây?*
1. Quyết toán thuế TNCN cuối năm, đối soát số thuế và thủ tục hoàn thuế qua eTax Mobile
2. Tính thuế thu nhập tiền lương & Quy đổi 2 chiều Lương Gross <-> Net
3. Thuế chuyển nhượng Bất động sản (2%) & Thẩm định điều kiện miễn thuế nhà đất duy nhất
4. Tư vấn rút BHXH một lần theo Luật BHXH 2024 & So sánh bảo lưu hưởng lương hưu
5. Thuế cho Freelancer, KOL, Hộ kinh doanh & Khấu trừ thuế vãng lai 10%
6. Đăng ký người phụ thuộc (giảm trừ 6,2 tr/tháng) & Tra cứu chuẩn hóa Mã số thuế

---

### NHÁNH 1 - TIỀN LƯƠNG GROSS <-> NET & GIẢM TRỪ GIA CẢNH (`luong_gross_net`)
- **Q1 (`lgn_salary_mode`):** Mức lương bạn đang có hoặc thỏa thuận là Lương Gross hay Lương Net?
  - *Lương Gross (trước khi trừ bảo hiểm và thuế TNCN)*
  - *Lương Net (thực nhận về tay, cần quy đổi sang Gross để thỏa thuận)*
- **Q2 (`lgn_salary_amount`):** Mức lương hàng tháng của bạn khoảng bao nhiêu?
  - *< 15,5 tr | 20 - 30 tr | 35 - 50 tr | 60 - 100 tr | > 100 tr (hoặc nhập số cụ thể)*
- **Q3 (`lgn_insurance_base`):** Công ty đóng bảo hiểm (BHXH, BHYT, BHTN) trên căn cứ nào?
  - *Đóng trên toàn bộ lương (tối đa trần 50,6tr) | Đóng trên lương cơ bản | Theo mức tối thiểu vùng | Không đóng BH*
- **Q4 (`lgn_dependents_count`):** Bạn đã đăng ký giảm trừ cho bao nhiêu người phụ thuộc?
  - *0 người (15,5tr) | 01 người (21,7tr) | 02 người (27,9tr) | 03 người trở lên*
- **Q5 (`lgn_extra_deductions`):** Bạn có chi phí giảm trừ bổ sung mới theo NĐ 253/2026/NĐ-CP không?
  - *Không có | Chi phí Y tế (tối đa 23tr/năm) | Học phí Giáo dục (tối đa 24tr/năm) | Hưu trí tự nguyện (3tr/tháng) | Cả Y tế và Giáo dục*
- **Q6 [FINAL] (`lgn_final_notes`):** Bạn có ghi chú hoặc yêu cầu đặc biệt nào thêm cho bảng tính lương này không?
  - *(Khuyến nghị) Không có ghi chú thêm, xuất bảng tính Excel và báo cáo ngay*
  - *So sánh chi phí công ty trả giữa Gross và Net | Tối ưu bảo hiểm giảm thuế | Ghi chú cụ thể khác*

---

### NHÁNH 2 - QUYẾT TOÁN THUẾ TNCN CUỐI NĂM (`quyet_toan_nam`)
- **Q1 (`qtt_income_sources`):** Trong năm 2026 bạn phát sinh thu nhập tiền lương từ bao nhiêu nơi?
  - *01 nơi duy nhất (ủy quyền) | 02 công ty trở lên (tự quyết toán) | 01 công ty + vãng lai | Nghỉ việc giữa năm*
- **Q2 (`qtt_withholding_docs`):** Bạn đã có Chứng từ khấu trừ thuế TNCN điện tử chưa?
  - *Đã có đủ chứng từ điện tử | Mới có một số nơi | Chưa có chứng từ nào | Công ty đã giải thể/phá sản*
- **Q3 (`qtt_annual_income_level`):** Ước tính tổng thu nhập chịu thuế cả năm (Gross) từ tất cả các nguồn?
  - *< 186 tr | 186 - 360 tr | 360 - 720 tr | 720 tr - 1,2 tỷ | > 1,2 tỷ (hoặc nhập số cụ thể)*
- **Q4 (`qtt_tax_withheld_status`):** Tổng số tiền thuế các bên ĐÃ TẠM KHẤU TRỪ trong năm như thế nào?
  - *Tạm trừ nhiều (dự kiến hoàn thuế) | Tạm trừ ít (lo nộp thêm) | Đã trừ 10% vãng lai | Chưa nắm rõ*
- **Q5 (`qtt_etax_mobile_account`):** Tình trạng tài khoản eTax Mobile liên kết VNeID mức 2 của bạn?
  - *Đã cài đặt và liên kết VNeID mức 2 | Đã có tài khoản MST cá nhân | Chưa cài đặt | Bị khóa/lỗi thông tin*
- **Q6 [FINAL] (`qtt_final_notes`):** Bạn có ghi chú hoặc yêu cầu đặc biệt nào thêm cho hồ sơ này không?
  - *(Khuyến nghị) Không có ghi chú thêm, tiến hành tra cứu và lập báo cáo ngay*
  - *Hoàn thuế trực tiếp vào tài khoản ngân hàng | Chuyển bù trừ sang năm sau | Ghi chú cụ thể khác*

---

### NHÁNH 3 - CHUYỂN NHƯỢNG BẤT ĐỘNG SẢN & MIỄN THUẾ (`chuyen_nhuong_bds`)
- **Q1 (`bds_contract_value`):** Giá trị chuyển nhượng quyền sử dụng đất/nhà ở trên hợp đồng công chứng?
  - *< 1 tỷ | 1 - 3 tỷ | 3 - 5 tỷ | 5 - 10 tỷ | > 10 tỷ (hoặc nhập số cụ thể)*
- **Q2 (`bds_relationship`):** Quan hệ pháp lý giữa bên bán và bên mua?
  - *Người ngoài (mua bán thông thường) | Vợ - Chồng | Cha mẹ - Con | Ông bà - Cháu | Anh chị em ruột*
- **Q3 (`bds_sole_property`):** BĐS này có phải là nhà ở, đất ở DUY NHẤT của bạn tại Việt Nam không?
  - *Đúng, là tài sản duy nhất toàn quốc | Không, sở hữu từ 2 BĐS trở lên | Đồng sở hữu | Chưa rõ*
- **Q4 (`bds_holding_period`):** Thời gian đứng tên trên Sổ đỏ/Sổ hồng tính đến ngày công chứng?
  - *Đã đủ 183 ngày trở lên (đạt chuẩn NĐ 253/2026) | Chưa đủ 183 ngày | Đang chờ cấp Sổ | Nhà hình thành tương lai*
- **Q5 (`bds_transfer_scope`):** Chuyển nhượng toàn bộ hay chỉ một phần diện tích?
  - *Chuyển nhượng toàn bộ diện tích | Chỉ chuyển nhượng một phần | Chuyển nhượng phần sở hữu chung*
- **Q6 [FINAL] (`bds_final_notes`):** Bạn có ghi chú hoặc câu hỏi gì thêm về hồ sơ kê khai BĐS không?
  - *(Khuyến nghị) Không có ghi chú thêm, tiến hành thẩm định ngay*
  - *Hướng dẫn đơn cam kết nhà duy nhất | Tư vấn lệ phí trước bạ | Ghi chú cụ thể khác*

---

### NHÁNH 4 - RÚT BHXH MỘT LẦN & LƯƠNG HƯU (`rut_bhxh_mot_lan`)
- **Q1 (`bhxh_start_time`):** Thời điểm bắt đầu tham gia đóng BHXH lần đầu tiên?
  - *Trước ngày 01/07/2025 (chuyển tiếp Điều 102) | Từ ngày 01/07/2025 trở đi*
- **Q2 (`bhxh_years_contributed`):** Tổng thời gian đóng BHXH tích lũy ghi trên sổ hoặc VssID?
  - *< 15 năm | 15 - 19 năm (Đủ điều kiện hưu trí theo Luật 2024) | 20 - 25 năm | > 25 năm (hoặc nhập cụ thể)*
- **Q3 (`bhxh_months_stopped`):** Thời gian dừng đóng sau khi chấm dứt hợp đồng lao động?
  - *Đã đủ 12 tháng trở lên | Mới nghỉ việc dưới 12 tháng | Vẫn đang đi làm | Chuẩn bị nghỉ việc*
- **Q4 (`bhxh_mbqtl_level`):** Mức bình quân tiền lương tháng đóng BHXH (MBQTL)?
  - *< 6 triệu | 6 - 10 triệu | 10 - 15 triệu | 15 - 25 triệu | > 25 triệu (hoặc nhập số cụ thể)*
- **Q5 (`bhxh_special_cases`):** Trường hợp nghỉ việc có thuộc ngoại lệ đặc biệt nào không?
  - *Nghỉ việc thông thường | Mắc bệnh hiểm nghèo | Ra nước ngoài định cư | Suy giảm LĐ từ 81% | Đủ tuổi chưa đủ 15 năm*
- **Q6 [FINAL] (`bhxh_final_notes`):** Bạn có ghi chú hoặc băn khoăn cụ thể nào cần so sánh thiệt hơn không?
  - *(Khuyến nghị) Không có ghi chú thêm, tiến hành tính toán và so sánh chi tiết ngay*
  - *So sánh tiền rút 1 lần vs Lương hưu 20 năm | Hướng dẫn thủ tục nhận BHTN | Ghi chú cụ thể khác*

---

### NHÁNH 5 - FREELANCER, HỘ KINH DOANH & KHẤU TRỪ 10% (`freelancer_kd`)
- **Q1 (`fl_income_sources`):** Thu nhập chủ yếu phát sinh từ nguồn nào?
  - *Hợp đồng dịch vụ doanh nghiệp VN | Nền tảng quốc tế (Google/YouTube/Upwork) | Sàn TMĐT Shopee/TikTok | Hộ kinh doanh*
- **Q2 (`fl_revenue_scale`):** Ước tính tổng doanh thu/thù lao trong năm?
  - *Dưới 1 tỷ đồng/năm (Miễn thuế theo NĐ 141/2026) | Từ 1 - 3 tỷ đồng/năm | Trên 3 tỷ đồng/năm*
- **Q3 (`fl_withholding_rate`):** Mức chi trả từng lần từ doanh nghiệp Việt Nam và tình trạng khấu trừ?
  - *Từ 5 triệu/lần trở lên (bị trừ 10% theo TT 87/2026) | Dưới 5 triệu/lần | Đã làm cam kết 08/CK | Không bị trừ và không có chứng từ*
- **Q4 (`fl_electronic_invoices`):** Bạn đã có mã số thuế cá nhân và chứng từ khấu trừ thuế điện tử chưa?
  - *Đã có MST và chứng từ điện tử | Chưa có MST cá nhân | Chưa xin được chứng từ | Cần hướng dẫn mở MST*
- **Q5 [FINAL] (`fl_final_notes`):** Bạn có câu hỏi hoặc ghi chú thêm nào cho mô hình của mình không?
  - *(Khuyến nghị) Không có ghi chú thêm, tiến hành lập báo cáo ngay*
  - *Cách hoàn lại thuế 10% bị tạm trừ | Hướng dẫn kê khai thuế TMĐT | Ghi chú cụ thể khác*

---

### NHÁNH 6 - ĐĂNG KÝ NGƯỜI PHỤ THUỘC & MÃ SỐ THUẾ (`nguoi_phu_thuoc_mst`)
- **Q1 (`npt_target_need`):** Nhu cầu nghiệp vụ cụ thể bạn đang cần thực hiện?
  - *Đăng ký NPT mới (giảm trừ 6,2tr/tháng) | Tra cứu chuẩn hóa MST theo CCCD 12 số | Chuyển nơi đăng ký NPT | Cắt giảm NPT*
- **Q2 (`npt_relationship_type`):** Người phụ thuộc thuộc nhóm đối tượng nào?
  - *Con dưới 18 tuổi | Con trên 18 tuổi đang học ĐH | Cha mẹ hết tuổi lao động | Vợ/chồng khuyết tật | Cá nhân không nơi nương tựa*
- **Q3 (`npt_income_ceiling`):** Mức thu nhập bình quân của người phụ thuộc có vượt quá 3 triệu đồng/tháng không?
  - *Không có thu nhập (0đ) | Có thu nhập dưới 3 triệu/tháng (Đủ điều kiện TT 87/2026) | Thu nhập trên 3 triệu/tháng | Chưa rõ*
- **Q4 (`npt_document_readiness`):** Tình trạng chuẩn bị hồ sơ chứng minh người phụ thuộc?
  - *Đã có đủ CCCD/Giấy khai sinh | Đang xin xác nhận UBND | Chưa rõ giấy tờ cần gì | Đăng ký qua eTax Mobile*
- **Q5 [FINAL] (`npt_final_notes`):** Bạn có ghi chú hoặc yêu cầu gì thêm về thủ tục này không?
  - *(Khuyến nghị) Không có ghi chú thêm, xuất hướng dẫn chi tiết ngay*
  - *Thời hạn đăng ký để giảm trừ lùi về trước | Mẫu tờ khai theo TT 80/2021 | Ghi chú cụ thể khác*
