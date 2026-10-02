# Hải quan, HS, thuế quan và xuất xứ

## 1. Chọn điểm bắt đầu

- Có mã HS: xác nhận quốc gia, số chữ số, phiên bản danh mục và hàng thực tế. Kiểm tra lại mã theo hệ thống Nhật; không chuyển nguyên phân dòng quốc gia xuất sang Nhật.
- Có tên sản phẩm: lấy mô tả kỹ thuật, cấu tạo, công dụng, thành phần/hàm lượng, dạng và mức chế biến cần thiết cho phân loại.
- Có thành phần: xác định chất đơn hay hỗn hợp/thành phẩm, hàm lượng, dạng đóng gói, mục đích, trạng thái hóa học khi cần. Một thành phần không tự quyết định HS của thành phẩm.
- Chỉ hỏi thuế: nếu chưa chốt mã, trình bày các ứng viên/điều kiện trước; có thể tính kịch bản nhưng không gắn thuế suất một ứng viên thành kết luận cuối.

HS 6 chữ số và phân dòng/mã thống kê nhập khẩu Nhật 9 chữ số có vai trò khác nhau. [Biểu thuế nhập khẩu Nhật](https://www.customs.go.jp/english/tariff/) là điểm chọn bảng theo ngày; không đóng cứng phiên bản trong skill. Kiểm tra tiêu đề, chú giải, đơn vị và ghi chú của dòng liên quan.

**Công cụ bắt buộc:** `scripts/tariff_lookup.py` chọn phiên bản biểu thuế theo ngày nhập, in đủ ~30 cột kèm tên cột, kế thừa mức từ dòng cha và đánh dấu cột hiệp định theo nước xuất xứ. Đọc bảng HTML bằng mắt là nguồn lỗi chính đã gặp (nhầm cột RCEP, coi ô trống là 0%, bịa mã 9 số). Lệnh (từ workspace AIWF):

```sh
python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/tariff_lookup.py --code 1902.19 --list
python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/tariff_lookup.py --code 1902.19-010 --origin "Viet Nam" --date 2026-10-15
```

Ví dụ thật (biểu thuế 2026-08-08): 1902.19-010 Biefun có General 32 yen/kg, WTO 27.20 yen/kg, cột Viet Nam/ASEAN/RCEP **trống** (không ưu đãi), CPTPP 4.95 yen/kg. Một báo cáo cũ đã viết "VJEPA/CPTPP/AJCEP/RCEP 0 JPY/kg": sai cả bốn. Dán khối đầu ra vào báo cáo; `check_evidence_table.py` đối chiếu mọi câu "hiệp định X 0%" với khối này.

## 2. Phân loại có căn cứ

Đọc General Rules for Interpretation, chú giải section/chapter, heading/subheading và phân dòng liên quan trong biểu thuế. Khi hồ sơ có hàng hỗn hợp, bộ hàng, bộ phận, chưa hoàn thiện hoặc nhiều công dụng, kiểm tra quy tắc tương ứng; không tìm mã bằng tên gần giống rồi bỏ chú giải.

Đối chiếu trường hợp phân loại công khai/事前教示 có mô tả kỹ thuật tương tự khi tìm được. Ghi khác biệt thành phần, công dụng hoặc thông số có thể đổi mã; không coi ruling của hàng khác là ruling cho hàng của người dùng. Không giả vờ có quyền truy cập dữ liệu HS thương mại/WCO trả phí.

Đầu ra phân loại: `SKU → đặc tính đã xác nhận → ứng viên mã Nhật → mô tả dòng → chú giải/quy tắc hỗ trợ → ứng viên loại bỏ và lý do → thông tin thiếu → mức xác nhận`. Đừng bịa số quy tắc/điều chưa đọc.

Chưa đủ căn cứ thì chuẩn bị câu hỏi [事前教示](https://www.customs.go.jp/english/c-answer_e/imtsukan/1202_e.htm), kèm specification, ảnh, thành phần, công dụng, sơ đồ hoặc mẫu khi phù hợp. Phân biệt trả lời bằng văn bản với hỏi miệng/email và các ngoại lệ hiệu lực. Không suy trả lời thuế quan xác nhận toàn bộ luật chuyên ngành.

## 3. Chọn chế độ thuế

Tại ngày nhập dự kiến, tra từng dòng và cột General/Temporary/WTO/GSP/EPA khi hiện diện. Đọc điều kiện nước, xuất xứ, hạn ngạch, lộ trình và chú thích. Không dùng cột thấp nhất chỉ vì nhìn thấy mức thấp; không mặc định mọi nước hưởng mọi chế độ. Dấu gạch/ô trống không tự có nghĩa 0%; đọc quy ước bảng.

Với EPA/FTA, xác định hiệp định có thể dùng, phiên bản HS trong quy tắc xuất xứ, PSR, tiêu chí hoàn toàn có được/chuyển đổi mã/hàm lượng giá trị hoặc điều kiện khác khi liên quan; kiểm tra cộng gộp, vận chuyển và chứng từ thích hợp. Nước gửi hàng, nước sản xuất và xuất xứ ưu đãi có thể khác. C/O không đủ nếu tiêu chí khác chưa đáp ứng. [Japan Customs: Rules of Origin](https://www.customs.go.jp/roo/english/index.htm).

Ghi nguồn dòng thuế, ngày áp dụng, mức/đơn vị và lý do chọn chế độ. Nếu nhiều chế độ khả thi, so sánh có điều kiện. Khi thuế phụ thuộc quota, giá, khối lượng hoặc phân loại đặc biệt, nêu dữ kiện quyết định.

## 4. Cơ sở và phép tính

Xác định loại duty: theo tỷ lệ, theo đơn vị, hỗn hợp hoặc chế độ đặc biệt. Với ad valorem: `duty chưa làm tròn = trị giá hải quan JPY × tỷ lệ`. Với thuế theo lượng: xác minh lượng/đơn vị và công thức của dòng. Không ép mọi dòng thành phần trăm.

Trị giá hải quan phải theo quy tắc áp dụng; hóa đơn hoặc CIF không mặc nhiên là trị giá cuối. Kiểm tra chi phí phải cộng/trừ, vận chuyển/bảo hiểm, royalty, assists, quan hệ bên mua/bán hoặc phương pháp khác nếu liên quan. Dùng tỷ giá Customs của kỳ thích hợp khi cần; không dùng tỷ giá thị trường hiện tại thay. [Customs valuation](https://www.customs.go.jp/english/c-answer_e/imtsukan/1401_e.htm), [Customs Answer](https://www.customs.go.jp/english/c-answer_e/customsanswer_e.htm).

Tra riêng consumption tax khi nhập, phần national/local, thuế suất giảm hoặc miễn theo hàng/giao dịch, excise khi áp dụng. Xác minh cơ sở gồm những khoản nào và quy tắc làm tròn theo thuế/thời điểm. Không gọi duty 0% là “không có thuế nhập hàng”. Phí đại lý, cảng, vận chuyển và lưu kho không tự là thuế nhà nước.

Nếu cần tính số nộp cuối, kiểm chứng cơ sở/thuế suất/đơn vị/làm tròn và đối chiếu khai báo; helper dưới đây không làm việc đó.

### Helper tính kịch bản

Chạy từ workspace AIWF:

```sh
python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/estimate_import_taxes.py --help
python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/estimate_import_taxes.py --input <research_dir>/scenario.json
```

Mẫu input dùng **số giả định cho kiểm thử**, không phải thuế suất của một sản phẩm:

```json
{
  "scenario": "illustrative-only",
  "rate_source": "https://www.customs.go.jp/english/tariff/2026_08_08/data/e_19.htm",
  "customs_value_jpy": "100000",
  "duty_rate_percent": "5",
  "consumption_tax_base_jpy": "105000",
  "consumption_tax_rate_percent": "10"
}
```

Thuế theo lượng (dòng ghi `yen/kg`): thay `duty_rate_percent` bằng `"duty_specific_jpy_per_unit": "27.20", "quantity": "2000", "quantity_unit": "kg"`. Thuế hỗn hợp: thêm `"duty_method": "compound_sum"` (VD "35% + 799 yen/kg"), `"greater_of"` ("x% or y yen/kg, whichever is the greater") hoặc `"lesser_of"`, và nhập cả hai phần.

Input là số thập phân viết dạng chuỗi, không dấu phân nhóm. `consumption_tax_base_jpy` phải nhập riêng sau khi xác định; script không tự giả định cơ sở từ duty. Bỏ cả hai trường consumption tax nếu chưa xác định cơ sở/tỷ lệ.

Output là `arithmetic_estimate_unrounded`, chỉ gồm các thuế được nhập, không tổng chi phí landed cost. Không có thuế suất mặc định, miễn trừ, tra HS, luật làm tròn, national/local breakdown, hạn ngạch hay thuế điều chỉnh đường (調整金). Không chạy script để che việc thiếu căn cứ thuế suất: thuế suất phải đến từ khối TARIFF_LOOKUP.

## 5. Checklist kết quả

| Hạng mục | Nội dung cần xuất |
|---|---|
| Phân loại | Mã Nhật/ứng viên, phiên bản, lý do và mức xác nhận |
| Thuế quan | Dòng/cột, mức/đơn vị, điều kiện và ngày |
| Xuất xứ | Hiệp định, tiêu chí, chứng từ, điểm chưa đáp ứng |
| Trị giá/lượng | Cơ sở, JPY/tỷ giá hoặc đơn vị lượng; khoản cộng/trừ |
| Thuế khác | Consumption tax/excise hoặc khoảng trống chưa xác định |
| Tính tiền | Đầu vào, công thức, giả định, làm tròn nếu đã xác minh |
| Tiếp theo | Hồ sơ thiếu, 事前教示 hoặc xác nhận chuyên ngành |

Nhập cá nhân, mẫu, tạm nhập, hàng sửa chữa, tái nhập, thương mại điện tử và hàng giá trị thấp cần tra chế độ riêng; không suy “mẫu/miễn phí” tự miễn thuế hoặc nghĩa vụ ngành. [Luật khác tại nhập khẩu](https://www.customs.go.jp/english/c-answer_e/imtsukan/1801_e.htm) vẫn cần kiểm tra khi liên quan.
