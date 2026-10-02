# Quyết định (cá biệt)

## Đặc điểm
- Có tên loại: "QUYẾT ĐỊNH" (IN HOA, đứng, đậm, cỡ 13-14)
- Có trích yếu: "Về việc ..." (thường, đứng, đậm)
- Có phần căn cứ pháp lý: chữ nghiêng, mỗi căn cứ một dòng, kết thúc chấm phẩy
- Nội dung chia thành các Điều
- Số ký hiệu: Số/QĐ-Viết tắt CQ (VD: `05/QĐ-UBND`). Quyết định cá biệt (văn bản hành chính) KHÔNG ghi năm; năm chỉ có trong ký hiệu văn bản quy phạm pháp luật

## Cấu trúc

```
[HEADER 2 CỘT - chuẩn chung]

                    QUYẾT ĐỊNH
              Về việc ...............

[CĂN CỨ]
Căn cứ .....;         ← in nghiêng, chấm phẩy
Căn cứ .....;         ← in nghiêng, chấm phẩy
Theo đề nghị của .... ← dòng cuối, in nghiêng, kết thúc dấu chấm (.)

                    QUYẾT ĐỊNH:

Điều 1. [Nội dung chính của quyết định]

Điều 2. [Điều khoản thi hành / hiệu lực]

Điều 3. [Trách nhiệm thi hành]./.

[FOOTER 2 CỘT - chuẩn chung]
```

## Sinh file

Viết JSON theo `standards/nd30.md` (ví dụ `examples/nd30-quyet-dinh.json`), chạy `scripts/generator/nd30_docx.py`, rồi `scripts/qa/check_nd30.py --render-dir`. Không tự vẽ header bằng code riêng.

## Lưu ý kỹ thuật

- "QUYẾT ĐỊNH" dòng 1: IN HOA, đậm, cỡ 14 (size 28), canh giữa
- "QUYẾT ĐỊNH:" dòng sau căn cứ: IN HOA, đậm, cỡ 13-14, canh giữa — đây là dấu hiệu bắt đầu phần quyết định
- Trích yếu: có gạch dưới phía dưới
- Căn cứ: Mỗi dòng bắt đầu bằng "Căn cứ" hoặc "Xét" hoặc "Theo", in nghiêng
- "Điều X.": in đậm, thường, đứng. Nội dung sau "Điều X." cùng dòng
- Điều cuối kết thúc bằng "./."
- Khoảng cách giữa "QUYẾT ĐỊNH" (tiêu đề) và phần căn cứ: 240 DXA
