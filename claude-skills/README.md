# Bộ skill Claude cho AI Workforce

Thư mục này đưa bộ skill Antigravity (`.agents/skills/`) vào Claude. Không file nào trong `.agents/` bị sửa.

## Kích hoạt (một lần trên mỗi máy)

Mở Terminal tại thư mục `ai-workforce` và chạy:

```bash
python3 claude-skills/sync_from_antigravity.py --install
```

Lệnh này chép bộ skill sang `.claude/skills/`, nơi Claude Code nạp skill của dự án. Sau đó mở thư mục `ai-workforce` trong Claude Code (tab Code của ứng dụng Claude, hoặc gõ `claude` trong Terminal tại đây). Claude tự đọc `CLAUDE.md` ở gốc; gõ `/skills` để xem danh sách.

## Cấu trúc

```
CLAUDE.md                          luật và quy ước cho Claude (tương đương GEMINI.md)
claude-skills/
├── README.md                      file này
├── skill-map.json                 hợp đồng phối hợp của 19 skill (tầng, vào, ra, nhận từ, giao cho)
├── sync_from_antigravity.py       sinh skill Claude từ skill gốc, --install để cài
└── skills/
    ├── dieu-phoi/                 điều phối nhiều skill thành dây chuyền (viết tay)
    ├── phong-media/               quy trình W1: tin Nhật → bài viết → video (viết tay)
    └── <19 skill>/                lớp vỏ Claude trỏ về .agents/skills/<skill>/ (sinh tự động)
.claude/skills/                    bản cài (do --install tạo), không sửa tay
```

## Vì sao là lớp vỏ, không phải bản sao

Skill gốc có scripts, engine `_shared/` (khoảng 220 MB), mô hình giọng đọc và tài liệu tham chiếu. Chép sang sẽ thành hai bản lệch nhau và trái luật R7 (cấm nhân bản engine). Bản Claude chỉ giữ phần Claude cần để biết khi nào dùng skill (`description` ≤ 1024 ký tự), bảng đổi công cụ và hợp đồng phối hợp. Quy trình chi tiết Claude đọc thẳng từ skill gốc lúc chạy, nên sửa skill gốc là cả Antigravity lẫn Claude cùng dùng bản mới.

## 5 tầng phối hợp

1. Tiếp nhận: `boc-tach-pdf`
2. Chuyên môn: `doc-sau`, `tu-van-phap-luat`, `tu-van-phap-luat-nhat-ban`, `tu-van-thue`, `bao-cao-kt`
3. Nội dung: `chotto-newsroom`, `viet-bai`
4. Sản xuất: `xu-ly-van-phong`, `ejv-translate`, `dich-thuat`, `thiet-ke`, `tao-landing-page`, `video-studio`, `hand-drawn-animation`, `long-tieng`, `phu-de`, `sach-noi`
5. Kiểm định: `app-auditor`

Các công thức ghép sẵn (Phòng Media, bài fanpage, scan → dịch → công văn, sách → sách nói, landing page → kiểm định, ...) nằm trong `skills/dieu-phoi/SKILL.md`. Ví dụ câu lệnh: *"Dùng dieu-phoi: lấy tin mới nhất về visa Tokutei Gino, viết bài Facebook và làm video dọc 60 giây."*

## Khi skill gốc thay đổi

```bash
python3 claude-skills/sync_from_antigravity.py --install  # sinh lại và cài
python3 claude-skills/sync_from_antigravity.py --check    # chỉ báo lệch
```

Skill mới trong `.agents/skills/` tự có bản Claude; thêm một dòng cho nó vào `skill-map.json` để có hợp đồng phối hợp. Quy trình mới ghép nhiều skill: tạo `claude-skills/skills/quy-trinh-<ten>/SKILL.md` theo khung ở mục 5 của `dieu-phoi`, rồi chạy `--install`.

## Đồng bộ sang máy khác (luật R0)

Commit `claude-skills/` và `CLAUDE.md`. Trên máy khác, sau `git pull` chạy lại lệnh `--install` ở trên. Nếu muốn máy khác dùng được ngay không cần chạy lệnh, commit thêm `.claude/skills/`.
