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
| `html.responsive_builder` | `html/responsive_html_builder.py` | Xuất bản HTML độc lập responsive Mobile & Desktop (Dark/Light mode, TOC scrollspy, tabbed switcher mobile, print A4 sạch, 100% offline không CDN) | `python3 .agents/skills/_shared/html/responsive_html_builder.py --input in.md [--output out.html] [--type generic\|deep-reading\|parallel]` | doc-sau, ejv-translate, dich-thuat |
| `pdf.asset_extractor` | `pdf/pdf_asset_extractor.py` | Trích ảnh giữ SMask alpha, cắt hình 300 DPI, tách con dấu, khung hoa văn | `… /pdf/pdf_asset_extractor.py --help` | dich-thuat |
| `pdf.verify_retention` | `pdf/verify_retention.py` | Cổng dịch sót ký tự nguồn (R3 §8), token kỹ thuật, IoU bố cục | `… /pdf/verify_retention.py --help` | dich-thuat, ejv-translate |
| `pdf.verify_layout_parity` | `pdf/verify_layout_parity.py` | So khớp bố cục bản dịch ↔ bản gốc | `… /pdf/verify_layout_parity.py --help` | dich-thuat |
| `pdf.verify_coordinates` | `pdf/verify_coordinates.py` | Chồng chữ, tràn lề, chữ bị cắt, va chạm khung viền | `… /pdf/verify_coordinates.py --help` | dich-thuat |
| `media.ffmpeg` | `media/ffmpeg_tools.py` | Tìm ffmpeg/ffprobe (ưu tiên ffmpeg-full), `has_filter`, decode/encode WAV, `duration`, `loudness` | — | long-tieng, phu-de, video-studio |
| `media.tts` | `media/tts.py` (+ worker `tts_vieneu_worker.py`, `tts_kokoro_worker.py`) | TTS **offline**: VieNeu-TTS 48 kHz (vi, nhân bản giọng `--ref-audio`), Kokoro ONNX (en, ja qua misaki) | `… /media/tts.py --text "…" --output a.wav --lang vi\|en\|ja [--voice …]` · `--list-voices` | long-tieng, video-studio |
| `media.dub_engine` | `media/dub_engine.py` | `synthesize` + Whisper nghe lại (CER) và đọc lại câu sai · `plan_fit`/`render_fit` (rubberband ≤ 1.25×) · `mix` (hạ tiếng gốc theo vùng có lời, −16 LUFS) · `dub_audio` một lệnh | — | long-tieng, video-studio |
| `media.ass_generator` | `media/ass_generator.py` | project.json → ASS (hộp bo góc, song ngữ, karaoke) + SRT, đo chữ bằng font thật | `… /media/ass_generator.py --help` | phu-de, long-tieng, video-studio |
| `media.linebreak` | `media/linebreak.py` | Ngắt dòng phụ đề cân bằng (Latin/CJK) | — | phu-de, video-studio (gián tiếp qua ass_generator) |
| `media.semantic_segmenter` | `media/semantic_segmenter.py` | Phân đoạn phụ đề theo câu/mệnh đề, gộp mảnh mồ côi, giới hạn CPS | `… /media/semantic_segmenter.py -i raw.json -o seg.json --max-lines 2\|1` | phu-de, video-studio |
| `media.subtitle_overlay` | `media/ui/subtitle_overlay.js` | Lớp phụ đề HTML xem trước (cùng style ASS) | — | phu-de, long-tieng |

Kiểu phụ đề mặc định: `media/subtitle_styles.json` (presets `modern_bottom`, `tiktok_box`, …).

## 3. Asset

| id | Đường dẫn | Nội dung | Ghi chú |
|---|---|---|---|
| `fonts` | `fonts/` | Be Vietnam Pro, Spectral (+ `fonts.css` cho in ấn), Montserrat, Roboto, Noto Serif, Noto Sans JP — OFL | thiet-ke chỉ chép bộ in ấn sang thư mục thiết kế; libass dùng `fontsdir=_shared/fonts` |
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
