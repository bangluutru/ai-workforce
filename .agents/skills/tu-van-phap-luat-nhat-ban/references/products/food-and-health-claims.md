# Thực phẩm, claim sức khỏe và tiếp xúc thực phẩm

## Dữ kiện quyết định

Công thức/hàm lượng, phụ gia, quy trình, dạng và đóng gói, nguồn động/thực vật, intended use, claim, nhà máy/nước, hạn dùng và điều kiện bảo quản. Với dụng cụ/bao bì: vật liệu, tiếp xúc thực phẩm nào, nhiệt độ/thời gian sử dụng. Chỉ lấy những trường cần cho sản phẩm.

## Các tuyến phải xét

- Phân biệt thực phẩm, phụ gia, dụng cụ/bao bì hoặc sản phẩm có thể thuộc PMD vì thành phần/công dụng/claim. “Viên uống/thực phẩm bổ sung” không tự là một loại pháp lý được phép claim.
- Tra 食品衛生法, tiêu chuẩn thành phần/phụ gia/chất tồn dư/vật liệu và điều kiện nhập tương ứng. [MHLW import procedure](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/shokuhin/yunyu_kanshi/kanshi/index_00004.html).
- Kiểm tra thông báo nhập để bán/dùng kinh doanh, examination/inspection theo hồ sơ và điều kiện certificate theo loại/nước. Không mặc định mọi lô đều bị xét nghiệm như nhau hoặc mọi mẫu được miễn.
- Phần tiêu chuẩn vệ sinh thực phẩm cần xác nhận cơ quan phụ trách hiện hành giữa CAA/MHLW; không lấy bố trí cơ quan từ handbook cũ. [CAA](https://www.caa.go.jp/) và trang MHLW dẫn nguồn liên quan.
- Có nguồn động/thực vật thì xem [animal-plant-special-goods.md](animal-plant-special-goods.md).
- Tra 食品表示法/食品表示基準, ngôn ngữ/nội dung, allergens, dinh dưỡng, xuất xứ, hạn dùng theo loại. [CAA food labeling](https://www.caa.go.jp/policies/policy/food_labeling/).

## Tự kiểm nhãn (thực phẩm chế biến đóng gói nhập khẩu)

Báo cáo nào nói về nhãn phải có bảng tự kiểm đủ các dòng sau, mỗi dòng ghi trạng thái (đã có / cần bổ sung / [CẦN XÁC MINH] miễn trừ). `check_evidence_table.py` báo lỗi nếu thiếu dòng nào:

| Trường | Ghi chú |
|---|---|
| 名称 | tên chung theo 食品表示基準, không phải tên thương mại |
| 原材料名 / 添加物 | thứ tự khối lượng giảm dần; phụ gia ghi tách theo quy định |
| 内容量 | khối lượng/thể tích tịnh |
| 賞味期限 hoặc 消費期限 | cách ghi theo thời hạn bảo quản |
| 保存方法 | |
| 原産国名 | bắt buộc với thực phẩm chế biến nhập khẩu (VD ベトナム); báo cáo cũ từng bỏ sót |
| 輸入者 | tên, địa chỉ nhà nhập khẩu tại Nhật |
| 栄養成分表示 | bắt buộc với thực phẩm chế biến đóng gói, trừ trường hợp miễn: ghi rõ có miễn hay không |
| アレルゲン (特定原材料) | đối chiếu công thức với danh mục hiện hành |

Không chép nội dung nhãn mẫu như kết luận: tên gọi, cách ghi hạn và miễn trừ phải đối chiếu 食品表示基準 và Q&A CAA hiện hành, dẫn ID trong Bảng nguồn.

## Claim sức khỏe

Phân biệt 栄養機能食品 (FNFC), 特定保健用食品 (FOSHU), 機能性表示食品 (FFC), thực phẩm thông thường và chế độ khác nếu liên quan. Tra điều kiện riêng của mỗi chế độ, không dùng tên chung “thực phẩm chức năng” để suy thủ tục.

[CAA FFC](https://www.caa.go.jp/policies/policy/food_labeling/foods_with_function_claims/) giải thích cơ chế notification theo trách nhiệm doanh nghiệp, khác cơ chế FOSHU. Đối chiếu bằng chứng, claim, đối tượng, quality/GMP khi phạm vi yêu cầu, hướng dẫn hiện hành và nghĩa vụ phản ánh tác hại. Không sao chép hạn thông báo hoặc ngưỡng từ leaflet cũ vào kết luận.

Claim chữa/phòng bệnh hoặc sản phẩm ranh giới cần nghiên cứu PMD/MHLW và cảnh báo chưa xác định phân loại; không chỉ sửa câu quảng cáo rồi coi sản phẩm hợp lệ.

## Đầu ra

Phân loại/khả năng → thành phần/claim còn vướng → nghĩa vụ nhập và certificate → tiêu chuẩn/test cần xác minh → nhãn/claim → chủ thể và việc trước bán/sau bán. Nếu hỏi HS/thuế, đọc [customs-and-tariffs.md](../customs-and-tariffs.md); classification thực phẩm không chốt mã thuế quan.
