# HƯỚNG DẪN THẨM ĐỊNH PHÁP LÝ NỘI DUNG QUẢNG CÁO (CHỐNG OVER-CLAIM)

Tuân thủ **Luật R5** (`.agents/rules/R5-legal-claim-compliance.md`). Linter: `scripts/claim_guard.py --profile ads` (được `fact_checker.py` gọi tự động).

## 0. Căn cứ pháp lý (kiểm tra hiệu lực trước khi viện dẫn trong bài)
| Văn bản | Nội dung liên quan | Ghi chú |
|---|---|---|
| Luật Quảng cáo 16/2012/QH13 | Điều 8: hành vi cấm, trong đó khoản 11 cấm dùng từ "nhất", "duy nhất", "tốt nhất", "số một" hoặc từ tương tự khi không có tài liệu hợp pháp chứng minh | |
| Luật 75/2025/QH15 sửa đổi, bổ sung Luật Quảng cáo | Thông qua 16/6/2025, hiệu lực 01/01/2026; bổ sung trách nhiệm của người chuyển tải sản phẩm quảng cáo (KOL/KOC/người nổi tiếng) và siết quảng cáo trên mạng | [CẦN XÁC MINH: số điều/khoản cụ thể trước khi trích dẫn trong bài] |
| NĐ 181/2013/NĐ-CP | Hướng dẫn thi hành Luật Quảng cáo | [CẦN XÁC MINH: điều khoản đã được sửa đổi sau 01/01/2026] |
| NĐ 38/2021/NĐ-CP | Xử phạt vi phạm hành chính lĩnh vực văn hóa và quảng cáo | [CẦN XÁC MINH: mức phạt hiện hành] |
| NĐ 15/2018/NĐ-CP | Thực phẩm bảo vệ sức khỏe: câu "Thực phẩm này không phải là thuốc, không có tác dụng thay thế thuốc chữa bệnh" | |
| TT 06/2011/TT-BYT | Mỹ phẩm: không được quảng cáo như thuốc | |
| Luật Bảo vệ quyền lợi người tiêu dùng 19/2023/QH15 | Cấm thông tin gian dối, gây nhầm lẫn | |

Agent KHÔNG trích số điều/khoản hoặc mức phạt vào bài nếu chưa đối chiếu văn bản gốc; ghi `[CẦN XÁC MINH]`.

## 1. Không được viết (linter chặn)
| Nhóm | Ví dụ cấm | Viết thay bằng |
|---|---|---|
| Tuyệt đối hóa | an toàn tuyệt đối, 100% tự nhiên, không tác dụng phụ, cho mọi loại da, vĩnh viễn, trọn đời | "dịu nhẹ, đã thử nghiệm trên da nhạy cảm (Theo [đơn vị], [năm])" |
| So sánh nhất không nguồn | tốt nhất, rẻ nhất, số 1, Top 1, hàng đầu, dẫn đầu, duy nhất, độc quyền | Giữ chỉ khi có nguồn độc lập cùng dòng: "(Theo Nielsen, 2025)"; "báo cáo nội bộ" không tính |
| Công dụng y tế (mỹ phẩm/TPBVSK) | điều trị, chữa khỏi, trị nám/mụn, đặc trị, dứt điểm, phòng ngừa bệnh, hạ đường huyết, giảm 10kg | "hỗ trợ làm mờ vết thâm", "hỗ trợ kiểm soát cân nặng kết hợp ăn uống và vận động" |
| Gọi mỹ phẩm/TPBVSK là thuốc | thuốc nhuộm, thuốc phủ bạc, thuốc giảm cân | "dầu gội phủ màu", "sản phẩm hỗ trợ" |
| Bảo chứng | Bộ Y tế khuyên dùng, bác sĩ khuyên dùng | Chỉ nêu số phiếu công bố / giấy xác nhận nội dung quảng cáo |
| Tài chính | cam kết lợi nhuận, chắc chắn có lãi, không rủi ro | "lợi nhuận kỳ vọng theo kịch bản..., có rủi ro mất vốn" |
| Bảo mật | bảo mật tuyệt đối/100%, không thể bị hack | "mã hóa AES-256, đạt ISO/IEC 27001 (năm cấp)" |

Nhắc tới cụm cấm để hướng dẫn tránh là được (ví dụ: Không dùng "an toàn tuyệt đối").

## 2. Câu bắt buộc theo nhóm sản phẩm (truyền `--category` cho fact_checker)
- `tpcn`: "Thực phẩm này không phải là thuốc, không có tác dụng thay thế thuốc chữa bệnh."
- `cosmetics`: "Sản phẩm mỹ phẩm, không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh."
- `drug`: "Đọc kỹ hướng dẫn sử dụng trước khi dùng." + số giấy xác nhận nội dung quảng cáo [CẦN XÁC MINH nếu chưa có].
- `finance`: câu cảnh báo rủi ro (có chữ "rủi ro").

## 3. Nguồn hợp lệ cho mọi con số / so sánh
Cùng dòng với tuyên bố: `(Theo <đơn vị độc lập>, <năm>)`, `Nguồn: <đơn vị> <năm>`, chú thích `[^1]` có năm, hoặc viện dẫn văn bản pháp luật. Mọi nguồn phải nằm trong `facts_evidence.md` kèm URL/tài liệu.

## 4. Trích dẫn phát ngôn
Không tự viết lời phát biểu cho người thật. Nếu khách hàng cung cấp ý chính: viết nháp + `[CẦN XÁC NHẬN: <người phát ngôn> duyệt nguyên văn]`. Linter chặn câu "Ông/Bà/CEO ... chia sẻ: "..."" thiếu cờ này.
