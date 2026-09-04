# DANH MỤC BIỂU ĐỒ BÁO CÁO TÀI CHÍNH & QUẢN TRỊ (CHART DEFINITIONS)

Tài liệu này quy định các loại biểu đồ chuẩn được hỗ trợ sinh tự động trong bảng tính Excel (`openpyxl`), Google Sheets và slide báo cáo (`python-pptx`).

---

## 1. BIỂU ĐỒ DOANH THU & LỢI NHUẬN (DUAL AXIS / COLUMN & LINE)
- **Mục đích:** So sánh quy mô doanh thu (Cột - Trục chính) với biên lợi nhuận ròng % (Đường - Trục phụ) qua 12 tháng hoặc các quý.
- **Loại biểu đồ:** Combo Chart (Clustered Column + Line with Markers).
- **Màu sắc khuyến nghị:**
  - Doanh thu: Cột màu `#2563EB` (Royal Blue).
  - Chi phí: Cột màu `#94A3B8` (Slate Muted).
  - Biên lợi nhuận ròng (%): Đường kẻ màu `#10B981` (Emerald Green) kèm điểm tròn (markers).

---

## 2. BIỂU ĐỒ CƠ CẤU CHI PHÍ (DONUT CHART)
- **Mục đích:** Thể hiện tỷ trọng các nhóm chi phí chính trong tổng chi phí hoạt động (OPEX).
- **Loại biểu đồ:** Doughnut Chart (Lỗ khoét giữa 50% tạo cảm giác hiện đại).
- **Phân khúc:**
  1. Chi phí nhân sự & lương thưởng (Thường 40 - 60%)
  2. Chi phí Marketing & Bán hàng (Thường 15 - 30%)
  3. Chi phí vận hành & mặt bằng (10 - 20%)
  4. Chi phí quản lý & công nghệ (5 - 15%)
  5. Chi phí khác (1 - 5%)
- **Quy tắc hiển thị:** Luôn kèm Data Labels gồm `Tên nhóm: ##%`.

---

## 3. BIỂU ĐỒ THÁC NƯỚC (WATERFALL CHART / MARGIN BRIDGE)
- **Mục đích:** Thuyết minh sự hao hụt từ Doanh thu thuần (100%) qua Giá vốn, Chi phí bán hàng, Chi phí QLDN, Thuế để còn lại Lợi nhuận sau thuế.
- **Thành phần:**
  - Bắt đầu: Doanh thu thuần (Cột xanh dương dương).
  - Trừ (-) Giá vốn hàng bán (Cột đỏ âm).
  - Trừ (-) Chi phí Bán hàng (Cột đỏ âm).
  - Trừ (-) Chi phí Quản lý doanh nghiệp (Cột đỏ âm).
  - Trừ (-) Thuế TNDN (Cột đỏ âm).
  - Kết thúc: Lợi nhuận ròng sau thuế (Cột xanh lá cây chốt sổ).

---

## 4. BẢNG THẺ CHỈ SỐ KPI (EXECUTIVE KPI CARDS)
- **Bố cục:** Hàng ngang gồm 4 thẻ chỉ số nổi bật trên đầu Dashboard:
  - **Thẻ 1: TỔNG DOANH THU** (Số tiền VND/USD + % Tăng trưởng MoM/YoY so với cùng kỳ).
  - **Thẻ 2: LỢI NHUẬN GỘP & BIÊN GỘP** (Số tiền + % Gross Margin).
  - **Thẻ 3: LỢI NHUẬN RÒNG & BIÊN RÒNG** (Số tiền + % Net Margin).
  - **Thẻ 4: SỐ DƯ TIỀN MẶT & RUNWAY** (Số dư tiền tại quỹ/ngân hàng + số tháng vận hành an toàn).
