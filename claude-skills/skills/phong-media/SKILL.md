---
name: phong-media
description: >-
  Dây chuyền Phòng Media khép kín: săn tin chính sách Nhật Bản từ nguồn .go.jp và lập fact pack (chotto-newsroom), viết bài phân tích đa kênh qua kiểm duyệt Luật R5 (viet-bai), rồi dựng video ngắn có giọng đọc AI, phụ đề karaoke và nhạc nền (video-studio). Dùng khi: người dùng nói "Phòng Media", "chạy phòng media", "sản xuất tin tức và video", hoặc muốn từ một chủ đề / link tin Nhật Bản ra trọn bộ fact pack + bài viết + video. Không dùng khi: chỉ cần một trong ba thành phẩm (gọi thẳng chotto-newsroom, viet-bai hoặc video-studio).
---

# Phòng Media (bản Claude)

Quy trình gốc (nguồn sự thật duy nhất): `.agents/workflows/W1-phong-media.md`. Đọc toàn bộ file đó rồi làm đúng 3 chặng và cổng kiểm định kép trong đó.

## Ghép với khung điều phối

Chạy theo cách của skill `dieu-phoi` (thư mục việc, `handoff.json`, không ghi đè):

| Chặng | Skill (đọc `claude-skills/skills/<skill>/SKILL.md`) | Thành phẩm |
|---|---|---|
| 1 | `chotto-newsroom` | `01_chotto-newsroom/fact_pack.md` (5 câu hỏi cốt lõi, bảng trích dẫn, ≥ 2 nguồn độc lập) |
| 2 | `viet-bai` | `02_viet-bai/bai_viet.md`, `bai_viet.docx`, `video_script.json` (45–60 giây) |
| 3 | `video-studio` | `03_video-studio/video_media.mp4` (phương án 3A stock footage hoặc 3B đồ họa chuyển động) |

Thư mục việc: `<output_dir>/phong_media_<chu_de>/` như quy trình gốc quy định.

## Đổi công cụ

`search_web` → WebSearch, mở trang nguồn → WebFetch, kiểm tra ảnh/khung hình → Read, chạy lệnh → Bash. Nếu quy trình gốc cần tạo ảnh minh họa (`generate_image`) mà phiên Claude không có công cụ tạo ảnh, dùng engine ảnh có trong skill nếu có; nếu không, ghi mô tả ảnh vào `fact_pack.md` và báo người dùng ở bước bàn giao.

## Không tự đăng

Bài và video chỉ được chuẩn bị sẵn để đăng. Đăng lên fanpage, website hay kênh video là bước công khai: chỉ làm khi người dùng yêu cầu rõ và đã có kết nối tới kênh đó.
