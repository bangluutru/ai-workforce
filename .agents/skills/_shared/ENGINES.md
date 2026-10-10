# 🧩 DANH MỤC ENGINE DÙNG CHUNG AIWF (`_shared/`)

> **Đọc file này TRƯỚC KHI viết bất kỳ code nào cho skill** (Luật R7 — `.agents/rules/R7-shared-engine-reuse.md`).
> Năng lực đã có ở đây → **gọi lại**. Thiếu tham số → **mở rộng engine ở đây**. Không chép, không viết lại trong skill.
> Danh mục máy đọc (nguồn sự thật cho bộ kiểm tra): [`engines.json`](engines.json).
> Kiểm tra tự động: `python3 scripts/check_shared_reuse.py` (0 = đạt · 1 = vi phạm · 2 = lỗi chạy).

---

## 1. Cách gọi

**Từ script Python trong skill** (`.agents/skills/<skill>/scripts/x.py`):

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import bootstrap  # noqa: F401,E402  — thêm _shared, _shared/media, _shared/pdf, _shared/docx vào sys.path

from tts import synthesize_line          # rồi import thẳng tên module
```

**Từ SKILL.md / terminal:** gọi thẳng CLI, ví dụ `python3 .agents/skills/_shared/media/tts.py --list-voices`.

**Từ web UI của skill:** server của skill phục vụ file chung (vd `/ui/lib/subtitle_overlay.js` → `_shared/media/ui/`,
`/templates/fonts/*` → `_shared/fonts/`) — xem `phu-de/scripts/local_bridge_server.py`.

> `_shared/docx/` không phải gói Python (trùng tên thư viện `python-docx`): dùng `from legal_report import …`.

---

## 2. Engine

| id | Module | Năng lực | CLI | Dùng bởi |
|---|---|---|---|---|
| `doc_ingest_bridge` | `doc_ingest_bridge.py` | Đọc tệp người dùng qua `scripts/doc_ingest.py`, PDF preflight (lớp chữ, dấu tiếng Việt), tách Markdown thành block | — (CLI gốc: `scripts/doc_ingest.py`) | bao-cao-kt, boc-tach-pdf, chotto-newsroom, dich-thuat, doc-sau, ejv-translate, tao-landing-page, tu-van-phap-luat(-nhat-ban), xu-ly-van-phong |
| `output_manager` | `output_manager.py` | Chọn `<output_dir>` (mặc định `~/Downloads/AIWF_Output`), chặn ghi thành phẩm vào workspace | — | (chưa skill nào import — skill mới PHẢI dùng thay vì tự viết) |
| `docx.legal_report` | `docx/legal_report.py` | Markdown báo cáo → DOCX (bảng, callout, header/footer, số trang, font CJK) | `python3 .agents/skills/_shared/docx/legal_report.py --input r.md [--output r.docx] [--title …]` | tu-van-phap-luat, tu-van-phap-luat-nhat-ban |
| `docx.inspect` | `docx/inspect_docx.py` | Đọc ngược DOCX thành JSON cấu trúc (khối theo thứ tự đọc, bảng ô gộp, ảnh dpi, font đã kế thừa, trường, sửa đổi) + phát hiện cơ học (placeholder, đoạn trống, nhảy cấp tiêu đề, em dash, NFD) + kiểm luật khai báo `--rules` + số trang thật `--pages` (LibreOffice) | `python3 .agents/skills/_shared/docx/inspect_docx.py f.docx [--json o.json] [--text] [--rules r.json] [--pages]` · luật mẫu: `_shared/docx/rules/` | tu-van-phap-luat(-nhat-ban), xu-ly-van-phong, ejv-translate |
| `office.soffice` | `office/soffice_tools.py` | Tìm/chạy LibreOffice headless (profile riêng, shim sandbox Linux), `convert`, `recalc_xlsx` (giá trị công thức), `render_png` (PDF → PNG từng trang) | `python3 .agents/skills/_shared/office/soffice_tools.py --headless --convert-to pdf --outdir d f.docx` | bao-cao-kt, xu-ly-van-phong (qua shim) |
| `html.responsive_builder` | `html/responsive_html_builder.py` | Xuất bản HTML độc lập responsive Mobile & Desktop (Dark/Light mode, TOC scrollspy, tabbed switcher mobile, print A4 sạch, 100% offline không CDN) | `python3 .agents/skills/_shared/html/responsive_html_builder.py --input in.md [--output out.html] [--type generic\|deep-reading\|parallel]` | doc-sau, ejv-translate, dich-thuat |
| `pdf.asset_extractor` | `pdf/pdf_asset_extractor.py` | Trích ảnh giữ SMask alpha, cắt hình 300 DPI, tách con dấu, khung hoa văn | `… /pdf/pdf_asset_extractor.py --help` | dich-thuat |
| `pdf.verify_retention` | `pdf/verify_retention.py` | Cổng dịch sót ký tự nguồn (R3 §8), token kỹ thuật, IoU bố cục | `… /pdf/verify_retention.py --help` | dich-thuat, ejv-translate |
| `pdf.verify_layout_parity` | `pdf/verify_layout_parity.py` | So khớp bố cục bản dịch ↔ bản gốc | `… /pdf/verify_layout_parity.py --help` | dich-thuat |
| `pdf.verify_coordinates` | `pdf/verify_coordinates.py` | Chồng chữ, tràn lề, chữ bị cắt, va chạm khung viền | `… /pdf/verify_coordinates.py --help` | dich-thuat |
| `media.ffmpeg` | `media/ffmpeg_tools.py` | Tìm ffmpeg/ffprobe (ưu tiên ffmpeg-full), `has_filter`, decode/encode WAV, `duration`, `loudness` | — | long-tieng, phu-de, video-studio |
| `media.tts` | `media/tts.py` (+ worker `tts_vieneu_worker.py`, `tts_kokoro_worker.py`) | TTS **offline**: VieNeu-TTS v3 Turbo 48 kHz (vi, 25 giọng chuẩn, nhân bản giọng `--ref-audio`), Kokoro ONNX (en, ja qua misaki, 33 giọng Anh/Mỹ/Nhật) | `… /media/tts.py --text "…" --output a.wav --lang vi\|en\|ja [--voice …]` · `--list-voices` | long-tieng, video-studio, sach-noi |
| `media.dub_engine` | `media/dub_engine.py` | `synthesize` + Whisper nghe lại (CER) và đọc lại câu sai · `plan_fit`/`render_fit` (rubberband ≤ 1.25×) · `mix` (hạ tiếng gốc theo vùng có lời, −16 LUFS) · `dub_audio` một lệnh | — | long-tieng, video-studio |
| `media.ass_generator` | `media/ass_generator.py` | project.json → ASS (hộp bo góc, song ngữ, karaoke) + SRT, đo chữ bằng font thật | `… /media/ass_generator.py --help` | phu-de, long-tieng, video-studio |
| `media.linebreak` | `media/linebreak.py` | Ngắt dòng phụ đề cân bằng (Latin/CJK) | — | phu-de, video-studio (gián tiếp qua ass_generator) |
| `media.semantic_segmenter` | `media/semantic_segmenter.py` | Phân đoạn phụ đề theo câu/mệnh đề, gộp mảnh mồ côi, giới hạn CPS | `… /media/semantic_segmenter.py -i raw.json -o seg.json --max-lines 2\|1` | phu-de, video-studio |
| `media.subtitle_overlay` | `media/ui/subtitle_overlay.js` | Lớp phụ đề HTML xem trước (cùng style ASS) | — | phu-de, long-tieng |
| `media.spoken_normalizer` | `media/spoken_normalizer.py` | Chuẩn hóa phát thanh tiếng Việt (số đếm, La Mã, ngày tháng, phần trăm, viết tắt KPI/CEO/TP.HCM, khử ngoặc kép) | `python3 …/spoken_normalizer.py --input in.txt --output out.txt [--dict d.tsv]` | sach-noi |
| `media.audiobook_packager` | `media/audiobook_packager.py` | Đóng gói sách nói .m4b (AAC mono, faststart, chapter markers ffmetadata, cover art) + thư mục MP3 ID3 tags | `python3 …/audiobook_packager.py --manifest m.json --output b.m4b --title … --author …` | sach-noi |
| `layout.designcraft_bridge` | `layout/designcraft_bridge.py` | Cầu nối điều khiển cỗ máy dàn trang DesignCraft DTP Engine (Rust headless), thực thi script `.dcs`, xuất bản PDF/PNG siêu tốc (40ms), tra cứu catalog 100+ lệnh DTP | `python3 .agents/skills/_shared/layout/designcraft_bridge.py [--check] [--run-script <f.dcs>] [--render-sample] [--page <n>] [--out <f>] [--list-commands [kw]]` | thiet-ke |
| `creative.storyboard` | `creative/storyboard_validator.py` | Thẩm định hợp đồng Storyboard v2.0 JSON Schema, phân định thời lượng target vs planned, chuyển đổi kịch bản legacy sang v2.0 | — (import: `from storyboard_validator import validate_storyboard`) | video-studio |
| `creative.brand_profile` | `creative/brand_profile.py` | Nạp và thẩm định Brand Motion Profile, tính toán hộp an toàn (safe-area box) theo kích thước khung hình | — (import: `from brand_profile import load_brand_profile`) | video-studio |
| `creative.motion` | `creative/motion_director.py` | Nội suy chuyển động Easing (linear, ease-in, ease-out, spring, cubic-bezier), tính cường độ, PRNG tất định | — (import: `from motion_director import evaluate_easing, plan_element_motion`) | video-studio |
| `creative.timeline` | `creative/timeline_planner.py` | Lập lịch dòng thời gian sự kiện phân cảnh đồng bộ âm thanh, thẩm định thứ tự/biên độ, bắt dính nhịp nhạc | — (import: `from timeline_planner import plan_scene_timeline`) | video-studio |
| `creative.renderer` | `creative/render_router.py` | Định tuyến kết xuất thông minh RenderRouter (HyperFrames vs Canvas fallback), xuất bản phân cảnh tự động phục hồi | — (import: `from render_router import RenderRouter, render_scene`) | video-studio |
| `creative.presets` | `creative/presets/registry.py` | Kho 10 motion presets chuẩn mực HTML/CSS/GSAP, kết xuất template động đa tỷ lệ khung hình | — (import: `from presets.registry import list_presets, render_preset_html`) | video-studio |
| `creative.qa` | `creative/qa/report_builder.py` | Kiểm toán kỹ thuật & thị giác Video QA 2.0 (ffprobe, phát hiện màn hình đen, đứng hình, tràn lề, contact sheet) | — (import: `from qa import run_visual_qa, validate_video_technical`) | video-studio |
| `creative.dom_validator` | `creative/qa/dom_validator.py` | Thẩm định bố cục DOM layout (TEXT_OVERFLOW, ELEMENT_OUT_OF_BOUNDS, SAFE_AREA_VIOLATION, TEXT_COLLISION, LOGO_OUT_OF_BOUNDS) | — (import: `from qa import validate_dom_layout, DOMValidationIssue`) | video-studio |
| `creative.storyboard_renderer` | `creative/storyboard_renderer.py` | Kết xuất toàn diện kịch bản phân cảnh Storyboard v2.0 đa cảnh ra MP4 hoàn chỉnh kèm âm thanh và QA | — (import: `from creative import render_storyboard, StoryboardRenderer`) | video-studio |

Kiểu phụ đề mặc định: `media/subtitle_styles.json` (presets `modern_bottom`, `tiktok_box`, …).


## 3. Asset

| id | Đường dẫn | Nội dung | Ghi chú |
|---|---|---|---|
| `fonts` | `fonts/` | Be Vietnam Pro, Spectral (+ `fonts.css` cho in ấn), Montserrat, Roboto, Noto Serif, Noto Sans JP — OFL | thiet-ke chỉ chép bộ in ấn sang thư mục thiết kế; libass dùng `fontsdir=_shared/fonts` |
| `dtp_layout` | `html/dtp_layout.css` | Hệ thống token CSS dàn trang DTP (Baseline Grid, Micro-typography, Optical Margins, Balanced Columns) | thiet-ke, dich-thuat, bao-cao-kt |
| `standards.layout` | `standards/layout_principles.md` | Nguyên lý dàn trang DTP chuẩn mực đúc kết từ DesignCraft (Knuth-Plass, Overset Math) | Tài liệu chuẩn toàn hệ thống AIWF |
| `models.kokoro` | `models/kokoro/` | `kokoro-v1.0(.int8).onnx`, `voices-v1.0.bin` | **gitignored** — `bash scripts/auto-setup.sh` tự tải; đổi chỗ bằng `AIWF_KOKORO_DIR` |

## 3b. Công cụ chung ở `scripts/` (gốc repo)

| Công cụ | Năng lực | Cách gọi | Bắt buộc với |
|---|---|---|---|
| `scripts/doc_ingest.py` | Đọc mọi tệp người dùng (DOCX/PDF/XLSX/PPTX/EPUB/ảnh) → `source.md` + `manifest.json` | `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<việc> --json` | Mọi skill nhận tệp nhị phân (GEMINI.md) |
| `scripts/claim_guard.py` | Quét over-claim Luật R5 | `python3 scripts/claim_guard.py --input "<tệp>" [--profile ads]` | viet-bai, thiet-ke, tu-van-phap-luat, bao-cao-kt, tu-van-thue |

Mỗi SKILL.md kết thúc bằng mục `## 🧩 Engine dùng chung (Luật R7)` liệt kê engine/công cụ đang dùng;
thiếu mục này trong khi code có gọi `_shared` → `check_shared_reuse.py` cảnh báo **R7-DECL**.

## 4. Engine bị cấm

| Engine | Lý do | Thay bằng |
|---|---|---|
| TTS trực tuyến Microsoft Edge (gói `edge-tts`) | Không có giấy phép thương mại rõ ràng — rủi ro bản quyền giọng đọc | `media.tts` (VieNeu / Kokoro offline) |

## 5. Thêm / mở rộng engine (quy trình 4 bước)

1. Viết module trong `_shared/<domain>/` (có docstring + `--help` nếu là CLI, không placeholder, không nuốt lỗi).
2. Đăng ký vào `engines.json`: `id`, `module`, `cli`, `capabilities`, `used_by`, `signatures` (regex định nghĩa hàm/lớp đặc trưng
   — dùng tên riêng, tránh tên chung như `is_cjk`), `allow` (file khác được phép chứa chữ ký, nếu có).
3. Thêm một dòng vào bảng §2 của file này; skill dùng engine ghi đường dẫn CLI/import trong SKILL.md.
4. `python3 scripts/check_shared_reuse.py` = 0 FAIL và `pytest` không phát sinh lỗi mới.
