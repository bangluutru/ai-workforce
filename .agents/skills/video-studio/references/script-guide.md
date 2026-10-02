# Viết kịch bản video (agent BẮT BUỘC đọc trước khi viết `script.json`)

Pipeline chỉ dựng đúng những gì kịch bản mô tả. Video hay hay dở quyết định ở đây: lời đọc,
nhịp cảnh, và từ khoá hình ảnh. Ví dụ đầy đủ: `references/example-script.json` (quảng cáo 28 s).

## 1. Cấu trúc theo mục đích

| Loại | Độ dài | Khung |
|---|---|---|
| Quảng cáo / giới thiệu sản phẩm | 20–45 s | Hook (vấn đề/khoảnh khắc) → giải pháp → bằng chứng (số liệu, quy trình) → lợi ích → kêu gọi + tên thương hiệu |
| Giải thích / hướng dẫn | 45–120 s | Hook câu hỏi → bối cảnh 1 câu → 3–5 bước (mỗi bước 1 cảnh) → tóm tắt → bước tiếp theo |
| Du lịch / cảm xúc | 30–60 s | Khoảnh khắc mở → hành trình (địa điểm cụ thể) → chi tiết gần (món ăn, con người) → kết lắng đọng |
| TikTok / Reels / Shorts (9:16) | 15–40 s | Câu đầu ≤ 2 s phải gây tò mò; cảnh 2–3 s; caption chữ lớn từng ý |

## 2. Lời đọc (`narration`)

- **Một ý mỗi cảnh**, 1–2 câu, 8–25 từ (≈ 3–7 s). Cảnh > 8 s làm hình lê thê.
- Viết để NGHE: câu ngắn, động từ mạnh, số liệu cụ thể ("rút từ 6 giờ xuống 40 phút"), không liệt kê dài.
- Câu đầu tiên là hook: không chào hỏi chung chung ("Chào mừng bạn đến với…"), vào thẳng hình ảnh/vấn đề.
- Từ viết tắt/ký hiệu viết theo cách đọc ("AI" → "trí tuệ nhân tạo"); tên riêng nước ngoài giữ nguyên.
- Chỗ muốn ngắt phụ đề: chèn `|` ("Mỗi sáng, hàng triệu người Việt | bắt đầu ngày mới…"). `|` không được đọc.
- Không "—", không ngoặc, không emoji. Pháp lý quảng cáo (R5): không "số 1", "tốt nhất", "chữa khỏi"… nếu không có chứng cứ.

## 3. Hình ảnh (`visuals`)

Mỗi cảnh 1–3 phần tử, theo thứ tự ưu tiên; pipeline lấy shot đầu tiên tìm được cho mỗi ~4.5 s.
- `{"media": "/đường/dẫn/ảnh_hoặc_video"}` — tư liệu của người dùng (logo, sản phẩm thật) LUÔN tốt nhất cho quảng cáo.
- `{"query": "..."}` — từ khoá TIẾNG ANH, **cụ thể, nhìn thấy được**: chủ thể + hành động + bối cảnh
  ("barista pouring milk into iced coffee", "coffee cherries harvest hand", "Hanoi old quarter street night").
  Tránh từ trừu tượng ("success", "quality", "innovation") — kho ảnh trả về hình sáo rỗng.
- Nguồn: Pexels/Pixabay (nếu có key trong `.env`) → ảnh CC từ Wikimedia Commons/Openverse + Ken Burns
  (không cần key) → nền màu (cảnh báo). Ảnh/clip ghép, có chữ/logo người khác, sai ngữ cảnh → thay query.

## 4. Các trường khác

```json
{
  "title": "Tiêu đề hiện 3 s đầu", "subtitle": "dòng phụ",
  "mood": "corporate|energetic|peaceful|emotional|urban|traditional|playful|epic",
  "aspect": "16:9|9:16|1:1|4:5", "lang": "vi|en|ja", "voice": "Minh Quân Pro",
  "scenes": [{"id": "s01", "narration": "...", "visuals": [...], "caption": "chữ lớn đầu khung (tuỳ chọn)",
              "secondary": "phụ đề ngôn ngữ thứ hai (tuỳ chọn → song ngữ)", "min_duration": 4.0}]
}
```
- Giọng VieNeu: nam trầm ấm kể chuyện "Anh Khôi", nam tự nhiên "Minh Quân Pro", nữ tin tức "Mai Anh"/"Thùy Dung",
  nữ miền Bắc tự nhiên "Trúc Ly". Quảng cáo trẻ: Trúc Ly/Minh Quân Pro; tài liệu: Anh Khôi/Mai Anh.
- `caption`: 2–6 từ, nhấn ý chính (giá, lợi ích, bước). Không lặp lại nguyên lời đọc.
- Cảnh cuối: `min_duration` 4–5 s cho logo/kêu gọi và nhạc kết.

## 5. Tự kiểm trước khi chạy

- [ ] Câu đầu là hook cụ thể; cả kịch bản có một mạch (vấn đề → giải pháp → kết)?
- [ ] Mỗi cảnh một ý, ≤ 25 từ; tổng thời lượng phù hợp mục đích?
- [ ] Mỗi cảnh có ≥ 2 query cụ thể (dự phòng) hoặc media của người dùng?
- [ ] Không câu nào cần hình mà kho ảnh khó có (người cụ thể, logo thương hiệu) — nếu có, xin media từ người dùng.
