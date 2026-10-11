---
name: dieu-phoi
description: >-
  Điều phối nhiều skill AIWF thành một dây chuyền làm việc: chọn skill cho từng chặng, lập thư mục việc chung, chuyển giao đầu ra giữa các skill bằng handoff.json, chạy song song các chặng độc lập bằng subagent và chốt cổng kiểm định cuối. Dùng khi: yêu cầu cần từ 2 skill trở lên (ví dụ săn tin rồi viết bài rồi làm video, scan rồi dịch rồi soạn công văn, đọc sách rồi làm sách nói, viết nội dung rồi dựng landing page rồi kiểm thử), khi người dùng nói "phối hợp", "dây chuyền", "quy trình", "làm trọn gói", hoặc khi tạo một quy trình mới ghép từ các skill có sẵn. Không dùng khi: việc chỉ cần đúng một skill (gọi thẳng skill đó).
---

# Điều phối skill (Orchestrator)

Skill này không tự làm nghiệp vụ. Nó chọn skill, xếp thứ tự, giữ thư mục việc và kiểm tra chỗ nối giữa các skill. Mỗi chặng vẫn chạy đúng skill chuyên môn của nó.

## 1. Bản đồ 5 tầng

Hợp đồng chi tiết của từng skill (đầu vào, đầu ra, nhận từ, giao cho) nằm trong `claude-skills/skill-map.json` và ở cuối mỗi `claude-skills/skills/<skill>/SKILL.md`.

| Tầng | Vai trò | Skill |
|---|---|---|
| 1 Tiếp nhận | Biến tệp người dùng thành chữ đọc được | `boc-tach-pdf` (PDF scan), `scripts/doc_ingest.py` (mọi tệp văn phòng) |
| 2 Chuyên môn | Phân tích, tư vấn, tính toán | `doc-sau`, `tu-van-phap-luat`, `tu-van-phap-luat-nhat-ban`, `tu-van-thue`, `bao-cao-kt` |
| 3 Nội dung | Viết, biên tập, kiểm chứng nguồn | `chotto-newsroom`, `viet-bai` |
| 4 Sản xuất | Dựng thành phẩm | `xu-ly-van-phong`, `ejv-translate`, `dich-thuat`, `thiet-ke`, `tao-landing-page`, `video-studio`, `hand-drawn-animation`, `long-tieng`, `phu-de`, `sach-noi` |
| 5 Kiểm định | Kiểm thử thành phẩm | `app-auditor`, cùng các linter có sẵn (`scripts/claim_guard.py`, `fact_checker.py` của viet-bai) |

Dữ liệu chảy từ tầng thấp lên tầng cao. Chọn skill theo ba thứ cùng lúc: loại đầu vào, ý định, thành phẩm mong muốn. Khi hai skill gần nhau, dùng quy tắc phân định ở `.agents/rules/AGENTS.md` mục 8B.

## 2. Công thức có sẵn

| Công thức | Chuỗi skill | Thành phẩm |
|---|---|---|
| Phòng Media | `chotto-newsroom` → `viet-bai` → `video-studio` | fact_pack, bài viết, video. Có skill riêng `phong-media` |
| Bài fanpage Facebook | `chotto-newsroom` (hoặc brief) → `viet-bai` kênh facebook → ảnh minh họa (`thiet-ke` hoặc ảnh của newsroom) | Gói bài đăng: nội dung, ảnh, nguồn. Đăng lên trang cần kết nối Facebook riêng |
| Tài liệu nước ngoài dạng scan | `boc-tach-pdf` → `ejv-translate` → `xu-ly-van-phong` | DOCX song ngữ + văn bản chuẩn NĐ 30 |
| Sách thành sách nói tóm tắt | `doc-sau` → `sach-noi` (chế độ Audiobook Brief) | Báo cáo đọc sâu + .m4b |
| Landing page | `viet-bai` kênh web → `tao-landing-page` → `app-auditor` | Mã nguồn + báo cáo kiểm định |
| Video có sẵn cần làm lại tiếng | `long-tieng` → `phu-de` | MP4 lồng tiếng có phụ đề |
| Hoạt hình kể chuyện | `viet-bai` (kịch bản) → `hand-drawn-animation` → `long-tieng` → `phu-de` | MP4 hoạt hình |
| Báo cáo doanh nghiệp | `bao-cao-kt` → `tu-van-thue` → `xu-ly-van-phong` hoặc `thiet-ke` | Dashboard, bảng thuế, tờ trình / ấn phẩm |
| Hồ sơ hàng sang Nhật | `tu-van-phap-luat-nhat-ban` → `viet-bai` hoặc `xu-ly-van-phong` | Báo cáo pháp lý + tài liệu cho khách |

Công thức nào lặp lại thường xuyên thì đóng thành skill quy trình riêng (mục 5).

## 3. Thư mục việc và chuyển giao

1. Đặt `<ten_viec>` dạng không dấu, gạch dưới. Thư mục việc: `<output_dir>/<ten_viec>/` (mặc định `~/Downloads/AIWF_Output/<ten_viec>/`). Nháp và file tạm để ở `_process/<ten_viec>/`. Không ghi vào gốc repo.
2. Ghi `00_brief.md`: yêu cầu nguyên văn của người dùng, thành phẩm cuối, chuỗi skill đã chọn và lý do, giả định đã đặt.
3. Mỗi chặng ghi thành phẩm vào thư mục con có số thứ tự: `01_<skill>/`, `02_<skill>/`, ...
4. Sau mỗi chặng, cập nhật `handoff.json`:

```json
{
  "viec": "<ten_viec>",
  "chuoi": ["chotto-newsroom", "viet-bai", "video-studio"],
  "chang": [
    {
      "so": 1,
      "skill": "chotto-newsroom",
      "trang_thai": "xong",
      "dau_vao": ["00_brief.md"],
      "dau_ra": ["01_chotto-newsroom/fact_pack.md"],
      "kiem_dinh": "2 nguồn .go.jp độc lập, đủ 5 câu hỏi",
      "co_can_xac_minh": []
    }
  ]
}
```

5. Chặng sau chỉ dùng `dau_ra` của chặng trước làm nguồn sự thật. Không bịa thêm dữ kiện ngoài đó; thiếu thì quay lại chặng trước hoặc gắn `[CẦN XÁC MINH]`.
6. Không ghi đè thành phẩm của chặng khác (AGENTS.md mục 4). Cần sửa thì tạo bản mới `..._v2`.

## 4. Chạy

- Đọc `claude-skills/skills/<skill>/SKILL.md` của từng chặng, rồi đọc skill gốc nó trỏ tới, trước khi chạy chặng đó.
- Chặng phụ thuộc nhau chạy tuần tự. Chặng độc lập (ví dụ dịch phụ đề song song với làm ấn phẩm từ cùng một bài) chạy song song bằng subagent; mỗi subagent nhận: tên skill, đường dẫn thư mục việc, danh sách file đầu vào, nơi ghi đầu ra, và yêu cầu trả về danh sách file + kết quả kiểm định.
- Tự chạy đến hết (AGENTS.md mục 6). Chỉ dừng hỏi người dùng khi thiếu thông tin bắt buộc không suy ra được, hoặc trước bước không đảo ngược được (đăng bài công khai, gửi ra ngoài, xóa dữ liệu).
- Mỗi chặng phải qua cổng kiểm định riêng của skill đó rồi mới chuyển giao. Cổng nào trả lỗi thì sửa tại chặng đó, không đẩy lỗi sang chặng sau.

## 5. Tạo skill quy trình mới

Khi một chuỗi được dùng lại, tạo `claude-skills/skills/quy-trinh-<ten>/SKILL.md` (viết tay, không có dòng AUTO nên script đồng bộ không đụng tới), rồi chạy `python3 claude-skills/sync_from_antigravity.py --install` để Claude Code nạp theo khung:

```markdown
---
name: quy-trinh-<ten>
description: >-
  <Thành phẩm cuối là gì>. Dùng khi: <câu người dùng hay nói>. Không dùng khi: <ranh giới>.
---
# <Tên quy trình>
Đầu ra cuối: <danh sách file trong <output_dir>/<ten_viec>/>
Đầu vào: <người dùng đưa gì; mặc định khi không đưa>
Chuỗi: <skill 1> → <skill 2> → ...
Chặng 1 (<skill>): đầu vào, việc chính, file ra, cổng kiểm định
...
Cổng cuối: <checklist>
Bàn giao: <báo gì trong khung chat>
```

Nếu quy trình cũng cần chạy trong Antigravity, viết bản gốc ở `.agents/workflows/` và để skill Claude trỏ tới, giống `phong-media`.

## 6. Bàn giao

Báo ngắn: thành phẩm cuối (đường dẫn), mỗi chặng một dòng kết quả kiểm định, các cờ `[CẦN XÁC MINH]` / `[CẦN XÁC NHẬN]` còn lại cho người dùng xử lý.
