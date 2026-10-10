# Creative Studio 2.1 — Baseline Manifest

> Tài liệu theo dõi. Nguồn khôi phục chính thức là Git tag `pre-creative-studio-2.1`.

## Định danh

| Mục | Giá trị | Trạng thái |
|---|---|---|
| Repository | https://github.com/bangluutru/ai-workforce.git | OBSERVED |
| Baseline SHA (đầy đủ) | `9e4ccb4a0188ca22fa7bb09e650af3370fc85ba6` | OBSERVED |
| Commit tham chiếu trong directive | `f59a369ecd399dce619c9932b9d22ff0c888dd5e` | OBSERVED: là tổ tiên của baseline |
| Khác biệt f59a369 → baseline | Chỉ `.agents/skills/.certified.json` (dấu thời gian/hash audit) | OBSERVED (`git diff --stat`) |
| Checkpoint tag | `pre-creative-studio-2.1` (annotated, object `a1ca8bc`) | OBSERVED, đã push remote |
| Feature branch | `feature/creative-studio-2.1` | OBSERVED |
| Branch gốc | `main`, khớp `origin/main` (0 ahead, 0 behind) | OBSERVED |
| Thời điểm lập | 2026-10-10 18:02 (JST) | |
| Working tree | Sạch (0 thay đổi chưa commit) | OBSERVED |

## Môi trường

| Công cụ | Phiên bản | Trạng thái |
|---|---|---|
| Python | 3.14.7 | OBSERVED |
| Node | v22.23.1 | OBSERVED |
| FFmpeg | 9.0.1 | OBSERVED |
| Git | 2.54.0 (Apple Git-157) | OBSERVED |
| HyperFrames | Không có bản cài sẵn dạng `npx --no-install`; npx đề xuất `hyperframes@0.8.145` | OBSERVED: chưa cài cục bộ; **NOT VERIFIED** cách renderer được gọi trong runtime |

## Feature flags hiện hành

File: `.agents/skills/video-studio/config/creative_studio_v2.json` (OBSERVED)

```json
{"creative_studio_v2": {"enabled": true, "motion_renderer": "hyperframes",
 "visual_qa_v2": true, "audio_driven_timeline": true, "motion_presets": true, "legacy_fallback": true}}
```

## Test baseline

| Lệnh | Kết quả | Trạng thái |
|---|---|---|
| `python3 -m pytest tests/creative -q` | 116 passed trong 3.65s | TESTED |
| `python3 scripts/check_shared_reuse.py` | Exit 0, không vi phạm R7 | TESTED |
| Các bộ test khác ngoài `tests/creative` | Chưa chạy ở Phase 0 | NOT VERIFIED |
| Render end-to-end HyperFrames thực tế | Chưa chạy ở Phase 0 | NOT VERIFIED |

## Quan sát ban đầu liên quan Phase 1 (chưa kết luận)

- `storyboard_renderer.py:280` tạo audio im lặng bằng `anullsrc`. OBSERVED vị trí; **chưa xác định** đây là silent fallback chủ đích hay đường xử lý chưa hoàn thiện (việc của Phase 1).
- Flag `audio_driven_timeline: true` tồn tại. **ASSUMED** có liên quan đường audio; cần đọc mã để xác nhận.

## Thành phần ngoài Git (Git không khôi phục)

- Model TTS (VieNeu, Kokoro) trong `_shared/models/` hoặc cache: tải lúc setup, không nằm trong repo.
- Cache nhạc nền: `~/.cache/aiwf/music/`.
- Dependencies Node (HyperFrames) và Python cài ngoài repo.
- Khóa `.env` (Pexels/Pixabay): không nằm trong repo.
- Thư mục output `~/Downloads/AIWF_Output/`.

## Stash đã có từ trước (bảo toàn, không đụng)

`stash@{0}: On main: local-changes-before-pull` chứa thay đổi nhị phân `extension/ai-workforce-panel-2.8.0.vsix`. Có từ trước nâng cấp này; không thuộc phạm vi v2.1 và giữ nguyên.

## Xác minh rollback (Gate 0)

| Kiểm tra | Kết quả |
|---|---|
| Baseline commit tồn tại | PASS: `git cat-file -t` = commit |
| Tag trỏ đúng commit | PASS: `pre-creative-studio-2.1^{commit}` = `9e4ccb4…` |
| Tag có trên remote | PASS: `git ls-remote --tags origin` |
| Worktree thử nghiệm từ tag | PASS: `git worktree add --detach /tmp/aiwf-rollback-check pre-creative-studio-2.1` |
| Baseline sạch trong worktree | PASS: 0 thay đổi; 22 file Python của `_shared/creative` parse hợp lệ |
| Dọn worktree, không mất dữ liệu | PASS: `git worktree remove` + `prune` |
| Chạy lại test trong worktree riêng | NOT VERIFIED (test chạy trên working tree chính ở cùng SHA) |

## Cách tái hiện baseline

```bash
git worktree add --detach /tmp/aiwf-baseline pre-creative-studio-2.1
cd /tmp/aiwf-baseline && python3 -m pytest tests/creative -q
```

## Quy trình revert (4 mức)

1. **Feature toggle:** tắt riêng cờ v2.1 trong `creative_studio_v2.json`, giữ Creative Studio 2.0.
2. **Revert commit feature:** `git revert <sha>` các commit v2.1 trên branch.
3. **Đã merge vào main:** `git revert -m 1 <merge_sha>`. Không force-push, không reset main.
4. **Khôi phục từ checkpoint:** worktree mới từ tag, kiểm tra dependencies/model/cache ngoài repo rồi mới triển khai.
