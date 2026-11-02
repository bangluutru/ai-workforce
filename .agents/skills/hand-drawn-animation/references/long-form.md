# Phim dài: nhiều phân đoạn, một nhân vật, một timeline

Áp dụng khi phim > 30 s hoặc > 6 shot. Đọc cùng [`character-rig.md`](character-rig.md).
Khung: [`assets/long-film.html`](../assets/long-film.html) + [`assets/seq-01.js`](../assets/seq-01.js).
Ví dụ 60 s đã làm theo cách tách file: [`examples/becoming-phoenix/`](../examples/becoming-phoenix/).

## 0. Vì sao phim dài hỏng

| Triệu chứng | Nguyên nhân | Cách làm đúng |
|---|---|---|
| Nhân vật ở phút 2 khác phút 1 | mỗi phân đoạn (hoặc mỗi phiên làm việc) vẽ lại nhân vật | `character-<ten>.js` dùng chung + `qa.mjs` FAIL `rig-drift` |
| Vết cắt nhảy vị trí/hướng, đạo cụ biến mất | không ai nhớ trạng thái cuối phân đoạn trước | `continuity.md`: đọc trước, ghi sau mỗi phân đoạn |
| Nhạc bị "nối" lệch nhịp ở chỗ ghép | mỗi phân đoạn là một HTML/MP4 riêng, ghép bằng ffmpeg | MỘT file master, MỘT timeline, MỘT score |
| Sửa 1 cảnh phải render lại cả phim | render một lần toàn bộ | `render.mjs --range` vào cache, `--assemble` một lần |
| Agent quên chuẩn đã chốt giữa chừng | ngữ cảnh làm việc quá dài | file nhỏ theo phân đoạn + bible + ledger: mỗi lần chỉ cần đọc 3 file |

## 1. Cấu trúc thư mục

```
<process_dir>/<ten_phim>/
├── <ten_phim>.html          # copy từ assets/long-film.html: bảng màu, thế giới, hành trình nhân vật, ghép timeline, score
├── character-<ten>.js       # CHARACTER BIBLE (rig) — mọi phân đoạn dùng chung, không chứa thời gian
├── model-sheet.html         # duyệt nhân vật (frame 0 bản vẽ, frame 1 có xương)
├── seq-01.js … seq-NN.js    # mỗi phân đoạn 15–30 s: beat sheet ở đầu file + addShot(...)
├── continuity.md            # sổ liên tục (mẫu ở §3)
├── core.js, rig.js, …       # copy từ assets/
└── preview/                 # grid, crops, model sheet theo từng vòng
```

- **Thời gian phim T** đi xuyên suốt: `addShot(seq, name, dur, (c, T, tau) => …)`. Vị trí nhân vật, giờ trong ngày,
  thời tiết, camera là hàm của `T`, không phải của `tau`. Vì vậy vết cắt giữa hai phân đoạn tự liên tục.
- **Thế giới** (bối cảnh, đường, ánh sáng theo `T`) viết một lần trong master; phân đoạn chỉ chọn camera và diễn xuất.
- Đạo cụ đổi trạng thái theo thời gian (cá trong giỏ → trong túi mỏ) cũng là hàm của `T` trong master hoặc bible.

## 2. Quy trình

**L1 — Kịch bản toàn phim.** Logline, cấu trúc phân đoạn (bảng trong master), mỗi phân đoạn có mục tiêu nhỏ +
trở ngại + kết. Ghi cue âm nhạc chính.

**L2 — Character bible + model sheet** (một lần, `character-rig.md` §2–4). Thêm vào model sheet MỌI tư thế khó của
cả phim. Không qua bước này thì không viết phân đoạn.

**L3 — Thế giới + hành trình** trong master: `drawWorld(c, T, view)`, `heroX(T)`, ánh sáng theo `T`. Render
`--grid 24` toàn phim với camera đơn giản để kiểm tra nhân vật đi đúng đường trong suốt thời lượng.

**L4 — Từng phân đoạn, theo thứ tự.** Với mỗi `seq-XX.js`:
1. **Đọc `continuity.md`** (dòng cuối của phân đoạn trước).
2. Viết beat sheet + shot. Chỉ thêm tư thế mới vào bible khi model sheet đã có tư thế đó.
3. Xem trước RIÊNG phân đoạn (thời gian toàn phim được giữ nguyên):
   ```bash
   node scripts/render.mjs <film> --seq XX --grid 24 --out <process_dir>/preview
   node scripts/render.mjs <film> --seq XX --crops 12 --out <process_dir>/preview
   node scripts/qa.mjs <film> --seq XX
   ```
   → MỞ grid và crop sheet (`view_file`), sửa mọi FAIL, chấm rubric cho phân đoạn (≥ 16/20).
4. **Ghi `continuity.md`**: trạng thái ở cuối phân đoạn (mẫu §3).
5. Render phân đoạn vào cache. Lệnh xem trước `--seq XX` in sẵn khoảng frame TOÀN PHIM
   (`Sequence XX = film frames A..B-1 … --range A,B`). Nhãn frame trên grid/crops khi dùng `--seq` là frame cục bộ
   của phân đoạn, KHÔNG dùng cho `--range`:
   `node scripts/render.mjs <film> --range START,END --out <output_dir>/<ten_phim>`

**L5 — Toàn phim.** `qa.mjs <film> --contact-frames 1200` (kiểm tra điểm chạm dày hơn), `--grid 48`, `--crops 24`
toàn phim; xem kỹ các vết cắt giữa phân đoạn bằng `--strip (t_cắt×24 − 6),12`.

**L6 — Ghép.** `node scripts/render.mjs <film> --assemble --out <output_dir>/<ten_phim>` → MP4 + score một lần.
Nếu lệnh báo đoạn render từ code cũ (`WARNING: ranges rendered from an older version`), render lại các đoạn bị ảnh hưởng
bằng `--range … --force`. Sửa thế giới, bible hoặc master thì ảnh hưởng MỌI đoạn.

## 3. Mẫu `continuity.md`

```markdown
# Continuity — <ten_phim>
Bible: character-<ten>.js · rig sig: <sig trên model sheet> · bảng màu: <tên>

| Cuối phân đoạn | T (s) | Vị trí (heroX) | Hướng màn hình | Đạo cụ / trạng thái | Biểu cảm | Giờ / ánh sáng | Cỡ cảnh cuối |
|---|---|---|---|---|---|---|---|
| 01 | 8.0 | -116 | trái → phải | cá trong giỏ, mũ trên đầu | vui | 7h sáng | medium |
| 02 | 16.0 | 268 | trái → phải | cá trong túi mỏ | nheo mắt, mệt | 7h15 | close |
```

Quy tắc: phân đoạn sau BẮT ĐẦU đúng trạng thái dòng trên. Muốn đổi (nhảy thời gian, đổi trang phục) thì có
shot chuyển cảnh có chủ đích và ghi lý do vào bảng.

## 4. Âm thanh

Một `score(ac, t0, dest)` trong master. Cue theo tên shot: `cue('03-crash')` trả về t0 của shot đó, nên sửa độ dài
phân đoạn không làm lệch nhạc. Motif chính mở đầu, biến tấu theo phân đoạn, trở lại hoàn chỉnh ở kết.
Kiểm tra `max_volume` < −0.5 dB trên MP4 cuối.

## 5. Chi phí render

Ước lượng: doodle/pencil 1080p ≈ 0.1–0.3 s/frame; riso 3 plate ≈ 0.5 s/frame. Phim 3 phút = 4320 frame. Vì vậy
mọi vòng review dùng preview (giây), chỉ render cache khi phân đoạn đã đạt, và chỉ render lại đoạn đã sửa.
