# Legal Phase 1 — Sang chiết, đóng gói lại hoá chất xét nghiệm y tế

## Định danh 5 Trục Pháp lý

| Trục | Nội dung |
|---|---|
| **ĐỐI TƯỢNG** | Hoá chất xét nghiệm dùng cho y tế (TTBYT chẩn đoán in vitro / IVD) |
| **HÀNH VI** | Sang chiết, đóng gói lại sản phẩm — KHÔNG thay đổi bản chất lý hoá |
| **TÁC ĐỘNG** | Xác định hành vi này có thuộc "hoạt động sản xuất" TTBYT hay không → nghĩa vụ công bố đủ điều kiện sản xuất, ISO 13485... |
| **PHẠM VI** | Doanh nghiệp tại Việt Nam |
| **THỜI ĐIỂM** | 29/08/2026 |

## Target (Câu hỏi cốt lõi)
Việc sang chiết, đóng gói lại hoá chất xét nghiệm y tế mà KHÔNG thay đổi bản chất lý hoá có được pháp luật VN xem là "hoạt động sản xuất TTBYT" không?

## Exit Condition
- ≥3 trích dẫn nguyên văn xác định khái niệm "sản xuất" bao gồm sang chiết/đóng gói. ✅ (đạt 6 trích dẫn)
- Xác định VB đang hiệu lực tại 29/08/2026. ✅
- Trả lời CÓ/KHÔNG rõ ràng. ✅ → CÓ.

---

## PDCA Cascade Log

### Vòng 1 — Tra cứu NĐ 98/2021 & VB sửa đổi

**[P] Plan:** Tìm định nghĩa "sản xuất" trong NĐ 98/2021/NĐ-CP (VB gốc quản lý TTBYT). Đồng thời kiểm tra VB sửa đổi.

**[D] Do:**
- `search_web`: NĐ 98/2021 Điều 2 — thu được giải thích từ ngữ "TTBYT" và "TTBYT IVD".
- `search_web`: VB sửa đổi NĐ 98/2021 → phát hiện NĐ 07/2023/NĐ-CP và NĐ 04/2025/NĐ-CP.
- `search_web`: "sang chiết" "đóng gói" "sản xuất" TTBYT → phát hiện định nghĩa "sản xuất" gồm san chia, sang chiết, đóng gói từ Luật CLSPHH & NĐ hướng dẫn.

**[C] Check:**
- NĐ 98/2021 Điều 2 KHÔNG định nghĩa "sản xuất" trực tiếp → GAP: cần tra VB định nghĩa "sản xuất" ở cấp chung.
- Phát hiện NĐ 37/2026/NĐ-CP (thay thế NĐ 43/2017 về nhãn + hướng dẫn Luật CLSPHH) có định nghĩa rõ.

**[A] Act:** → Đào sâu: tra NĐ 37/2026 Điều 3 (định nghĩa sản xuất) và Điều 44 K.8 (quy định san chia, sang chiết).

---

### Vòng 2 — Tra cứu NĐ 37/2026 & điều kiện sản xuất TTBYT

**[P] Plan:** Lấy nguyên văn định nghĩa "sản xuất" từ NĐ 37/2026 Điều 3 và quy định san chia/sang chiết từ Điều 44 K.8. Đồng thời tra NĐ 98/2021 Điều 8 (điều kiện sản xuất TTBYT).

**[D] Do:**
- `search_web` + `read_url_content`: NĐ 37/2026 Điều 3 → nguyên văn: "Sản xuất là việc thực hiện một, một số hoặc tất cả các hoạt động chế tạo, chế biến, chiết xuất, tái chế, lắp ráp, pha trộn, pha chế, san chia, sang chiết, nạp, đóng gói và hoạt động khác làm ra sản phẩm, hàng hóa."
- `search_web`: NĐ 37/2026 Điều 44 K.8 → quy định: hàng hóa chỉ được san chia, sang chiết khi có sự cho phép bằng văn bản của nhà sản xuất gốc + phải bảo đảm chất lượng + phải ghi nhãn đầy đủ.
- `search_web`: NĐ 98/2021 Điều 8 → cơ sở sản xuất TTBYT phải đạt ISO 13485.
- `search_web`: NĐ 98/2021 Điều 9-10 → phải công bố đủ điều kiện sản xuất tại Sở Y tế.

**[C] Check:**
- NĐ 37/2026 Điều 3: SANG CHIẾT nằm trong danh sách hoạt động cấu thành "sản xuất" → KHÔNG có ngoại trừ cho trường hợp "không thay đổi bản chất lý hoá".
- NĐ 98/2021 Điều 8: Cơ sở sản xuất TTBYT phải có ISO 13485 → áp dụng cho mọi hình thức sản xuất (kể cả sang chiết, đóng gói lại).
- Không có xung đột giữa NĐ 37/2026 và NĐ 98/2021 (bổ sung nhau: NĐ 37 định nghĩa chung, NĐ 98 quy định chuyên ngành TTBYT).

**[A] Act:** SOT đã hoàn chỉnh. Exit Condition thỏa mãn. Chuyển sang đóng gói.

---

## Source of Truth (SOT)

**Vấn đề:** Sang chiết, đóng gói lại hoá chất xét nghiệm y tế — có phải sản xuất TTBYT không?
**Mốc thời điểm:** 29/08/2026
**Lĩnh vực:** Y tế — Trang thiết bị y tế (TTBYT)

| # | Tọa độ pháp lý | Trích dẫn nguyên văn | Trạng thái | Hiệu lực | Vai trò |
|---|---|---|---|---|---|
| 1 | NĐ 37/2026/NĐ-CP – Đ.3 | "Sản xuất là việc thực hiện một, một số hoặc tất cả các hoạt động chế tạo, chế biến, chiết xuất, tái chế, lắp ráp, pha trộn, pha chế, san chia, sang chiết, nạp, đóng gói và hoạt động khác làm ra sản phẩm, hàng hóa." | đang hiệu lực | 23/01/2026 | **Định nghĩa cốt lõi** — sang chiết, đóng gói = sản xuất |
| 2 | NĐ 37/2026/NĐ-CP – Đ.44, K.8 | "Hàng hóa chỉ được thực hiện việc san chia, sang chiết để đóng gói, đóng chai khi có sự cho phép bằng văn bản của tổ chức, cá nhân sản xuất ra hàng hóa đó [và] phải bảo đảm chất lượng hàng hóa như công bố của nhà sản xuất trên nhãn gốc." | đang hiệu lực | 23/01/2026 | Điều kiện bắt buộc khi san chia/sang chiết |
| 3 | NĐ 98/2021/NĐ-CP – Đ.2, K.2 | "Trang thiết bị y tế chẩn đoán in vitro gồm thuốc thử, chất hiệu chuẩn, vật liệu kiểm soát, dụng cụ, máy, thiết bị hoặc hệ thống và các sản phẩm khác tham gia hoặc hỗ trợ quá trình thực hiện xét nghiệm được sử dụng riêng rẽ hoặc kết hợp theo chỉ định của chủ sở hữu [...]" | đang hiệu lực (sửa đổi bởi NĐ 07/2023, NĐ 04/2025) | 01/01/2022 | Xác nhận hoá chất xét nghiệm = TTBYT IVD |
| 4 | NĐ 98/2021/NĐ-CP – Đ.8, K.1 | "Cơ sở sản xuất trang thiết bị y tế phải đạt tiêu chuẩn hệ thống quản lý chất lượng ISO 13485." | đang hiệu lực | 01/01/2022 | Điều kiện sản xuất TTBYT — bắt buộc ISO 13485 |
| 5 | NĐ 98/2021/NĐ-CP – Đ.9-10 | Trước khi sản xuất TTBYT, cơ sở phải nộp hồ sơ công bố đủ điều kiện sản xuất về Sở Y tế nơi đặt địa điểm sản xuất. Hồ sơ gồm: văn bản công bố, GCN ISO 13485, các giấy tờ chứng minh điều kiện nhân sự, CSVC, hệ thống QLCL. | đang hiệu lực | 01/01/2022 | Thủ tục công bố đủ điều kiện sản xuất |
| 6 | NĐ 37/2026/NĐ-CP – Đ.44 (nhãn) | "Trên nhãn hàng hóa sau khi san chia, sang chiết, nạp để đóng gói, đóng chai phải ghi tên và địa chỉ của tổ chức, cá nhân đóng gói, đóng chai và tên, địa chỉ của tổ chức, cá nhân sản xuất ra hàng hóa đó." | đang hiệu lực | 23/01/2026 | Nghĩa vụ ghi nhãn khi sang chiết |

### Xung đột
Không có xung đột trong SOT. NĐ 37/2026 (VB chung về CLSPHH) và NĐ 98/2021 (VB chuyên ngành TTBYT) bổ trợ nhau: NĐ 37 cung cấp định nghĩa "sản xuất" bao gồm sang chiết, NĐ 98 quy định điều kiện riêng cho sản xuất TTBYT.

---

## Tổng kết Phase 1

### Sự thật (Truth)
- Pháp luật VN **định nghĩa rõ** sang chiết, đóng gói lại là hoạt động SẢN XUẤT (NĐ 37/2026 Đ.3).
- Không có ngoại trừ cho trường hợp "không thay đổi bản chất lý hoá" — miễn bạn thực hiện sang chiết hoặc đóng gói lại, đó đã là sản xuất.
- Hoá chất xét nghiệm = TTBYT IVD → phải tuân thủ NĐ 98/2021 (ISO 13485 + Công bố đủ điều kiện SX).

### Hành động (Actionable)
- DN PHẢI công bố đủ điều kiện sản xuất TTBYT tại Sở Y tế.
- DN PHẢI đạt ISO 13485.
- DN PHẢI có sự cho phép bằng văn bản của nhà sản xuất gốc (NĐ 37/2026 Đ.44 K.8).
- DN PHẢI ghi nhãn đầy đủ theo NĐ 37/2026.

### Khoảng trống (Next Gap)
- Chưa tra cứu Thông tư hướng dẫn NĐ 98/2021 (TT 05/2022/TT-BYT) về quy trình chi tiết công bố đủ điều kiện SX.
- Chưa kiểm tra quy định riêng cho IVD trong NĐ 04/2025/NĐ-CP (sửa đổi NĐ 98).
- Chưa tra quy định xử phạt nếu DN sang chiết mà không có giấy phép SX.
