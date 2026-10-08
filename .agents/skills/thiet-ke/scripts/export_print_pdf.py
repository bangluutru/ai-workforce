#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_print_pdf.py - Xuất HTML thiết kế (leaflet / brochure / poster / slide) sang PDF in ấn.

- Kích thước trang lấy ĐÚNG từ CSS @page (prefer_css_page_size) = khổ thành phẩm + 2 x bleed.
- Ghi TrimBox / BleedBox chuẩn PDF/X; --marks thêm dấu cắt (crop marks) ngoài vùng bleed.
- Font tiếng Việt đóng gói sẵn (Be Vietnam Pro, Spectral) được nạp offline; chặn tài nguyên mạng mặc định.
- KHÔNG có phương án dự phòng giả: thiếu Playwright / sai kích thước -> thoát mã lỗi khác 0.

Chạy bằng Python của repo:
  .venv/bin/python .agents/skills/thiet-ke/scripts/export_print_pdf.py \
      --input <process_dir>/design.html --output <output_dir>/ten_an_pham_print.pdf --marks
"""

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from print_common import (bundled_fontface_css, mm2pt, parse_size, pt2mm,  # noqa: E402
                          read_print_meta, require_fitz, require_playwright)

MARK_LEN_MM = 5.0
MARK_GAP_MM = 1.0      # khoảng trống thêm ngoài dấu cắt
MARK_WIDTH_PT = 0.25


def render_html(html: Path, raw_pdf: Path, allow_network: bool) -> tuple:
    sync_playwright = require_playwright()
    blocked = []
    font_errors = []
    oversets = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def route(r):
            url = r.request.url
            if url.startswith(("file:", "data:", "blob:")) or allow_network:
                r.continue_()
            else:
                blocked.append(url)
                r.abort()
        page.route("**/*", route)
        page.goto(html.resolve().as_uri(), wait_until="load")
        page.add_style_tag(content=bundled_fontface_css())
        page.evaluate("document.fonts.ready.then(() => true)")
        # Ép tải các font được khai báo rồi kiểm tra font nào lỗi
        font_errors = page.evaluate("""async () => {
            const bad = [];
            for (const f of document.fonts) {
                try { await f.load(); } catch (e) { bad.push(f.family + ' ' + f.weight + ' ' + f.style); }
            }
            return bad;
        }""")

        # Bắt lỗi tràn chữ (Overset Text Detection) - Học hỏi từ Adobe InDesign / DesignCraft
        oversets = page.evaluate("""() => {
            const bad = [];
            const containers = document.querySelectorAll('.panel, [data-dtp-frame="true"], .text-frame, .content-box, .sheet > div, .card');
            for (const el of containers) {
                const style = window.getComputedStyle(el);
                const isOverflowHidden = (style.overflow === 'hidden' || style.overflowY === 'hidden' || style.overflow === 'clip');
                const diffY = el.scrollHeight - el.clientHeight;
                // Dung sai 3px để tránh subpixel rendering sai số
                if (isOverflowHidden && diffY > 3) {
                    const idOrClass = el.id ? '#' + el.id : (el.className ? '.' + el.className.trim().split(/\\s+/).join('.') : el.tagName.toLowerCase());
                    const snippet = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 90);
                    bad.push({
                        selector: idOrClass,
                        overflow_px: Math.round(diffY),
                        snippet: snippet
                    });
                }
            }
            return bad;
        }""")

        page.wait_for_timeout(300)
        page.emulate_media(media="print")
        page.pdf(path=str(raw_pdf), print_background=True, prefer_css_page_size=True,
                 margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        browser.close()
    if blocked:
        print("⚠️  Đã CHẶN tài nguyên mạng (ấn phẩm in phải dùng file cục bộ):")
        for u in sorted(set(blocked))[:10]:
            print(f"     - {u}")
    if font_errors:
        print(f"⚠️  Font không tải được: {font_errors}")
    return blocked, oversets


def draw_crop_marks(page, fitz, trim, bleed_pt, mark_off_pt, mark_len_pt):
    """Vẽ 8 dấu cắt ở 4 góc, nằm NGOÀI vùng bleed."""
    shape = page.new_shape()
    x0, y0, x1, y1 = trim.x0, trim.y0, trim.x1, trim.y1
    o, L = mark_off_pt, mark_len_pt
    for x in (x0, x1):
        for y, sgn in ((y0, -1), (y1, 1)):
            shape.draw_line(fitz.Point(x, y + sgn * o), fitz.Point(x, y + sgn * (o + L)))   # dấu dọc
    for y in (y0, y1):
        for x, sgn in ((x0, -1), (x1, 1)):
            shape.draw_line(fitz.Point(x + sgn * o, y), fitz.Point(x + sgn * (o + L), y))   # dấu ngang
    shape.finish(color=(0, 0, 0), width=MARK_WIDTH_PT)
    shape.commit()


def main():
    ap = argparse.ArgumentParser(description="Xuất HTML thiết kế sang PDF in ấn có bleed / TrimBox / crop marks")
    ap.add_argument("--input", "-i", required=True, help="File HTML thiết kế")
    ap.add_argument("--output", "-o", required=True, help="File PDF đầu ra")
    ap.add_argument("--trim", help="Khổ thành phẩm mm, ví dụ 297x210 (mặc định: đọc <meta name=print:trim>)")
    ap.add_argument("--bleed", type=float, help="Bù xén mm mỗi cạnh (mặc định: <meta name=print:bleed> hoặc 3)")
    ap.add_argument("--marks", action="store_true", help="Thêm dấu cắt (crop marks) - khuyến nghị khi gửi nhà in")
    ap.add_argument("--allow-network", action="store_true", help="Cho phép tải tài nguyên http(s) (mặc định chặn)")
    ap.add_argument("--allow-overset", action="store_true", help="Bỏ qua khóa chặn lỗi tràn chữ (mặc định: chặn khi phát hiện tràn chữ)")
    ap.add_argument("--portrait", action="store_true", help="(Bỏ qua - giữ tương thích cũ; hướng giấy lấy từ CSS @page)")
    args = ap.parse_args()

    html = Path(args.input)
    out = Path(args.output)
    if not html.exists():
        print(f"❌ Không tìm thấy file đầu vào: {html}", file=sys.stderr)
        sys.exit(1)
    if html.suffix.lower() not in (".html", ".htm"):
        print("❌ Chỉ hỗ trợ HTML (SVG: nhúng vào HTML có @page).", file=sys.stderr)
        sys.exit(1)

    meta = read_print_meta(html)
    trim_txt = args.trim or meta.get("trim")
    if not trim_txt:
        print("❌ Chưa khai báo khổ thành phẩm: dùng --trim 297x210 hoặc <meta name=\"print:trim\" content=\"297x210\">",
              file=sys.stderr)
        sys.exit(1)
    trim_w, trim_h = parse_size(trim_txt)
    bleed = args.bleed if args.bleed is not None else float(meta.get("bleed", 3))

    fitz = require_fitz()
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"▶ Xuất {html.name}: thành phẩm {trim_w:g}x{trim_h:g}mm, bleed {bleed:g}mm, crop marks: {'có' if args.marks else 'không'}")

    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "raw.pdf"
        blocked, oversets = render_html(html, raw, args.allow_network)
        if oversets:
            print(f"❌ PHÁT HIỆN LỖI TRÀN CHỮ (OVERSET TEXT TRÊN {len(oversets)} KHUNG):", file=sys.stderr)
            for err in oversets:
                print(f"   - Khung [{err['selector']}] tràn {err['overflow_px']}px: \"{err['snippet']}...\"", file=sys.stderr)
            print("   -> BIỆN PHÁP KHẮC PHỤC (chuẩn DTP _shared/standards/layout_principles.md):", file=sys.stderr)
            print("      1. Rút gọn câu từ, tinh chỉnh nội dung ngắn gọn hơn.", file=sys.stderr)
            print("      2. Giảm cỡ chữ hoặc leading trong biên độ dung sai an toàn (≤ 10%).", file=sys.stderr)
            print("      3. Dùng --allow-overset nếu muốn xuất nháp xem xét.", file=sys.stderr)
            if not args.allow_overset:
                sys.exit(1)

        src = fitz.open(str(raw))

        exp_w, exp_h = mm2pt(trim_w + 2 * bleed), mm2pt(trim_h + 2 * bleed)
        bad = [i + 1 for i, pg in enumerate(src)
               if abs(pg.rect.width - exp_w) > 1.5 or abs(pg.rect.height - exp_h) > 1.5]
        if bad:
            pg = src[bad[0] - 1]
            print(f"❌ SAI KÍCH THƯỚC TRANG (trang {bad[:5]}): PDF {pt2mm(pg.rect.width):.1f}x{pt2mm(pg.rect.height):.1f}mm, "
                  f"cần {trim_w + 2 * bleed:g}x{trim_h + 2 * bleed:g}mm (= thành phẩm + 2 x bleed).", file=sys.stderr)
            print("   Sửa CSS: @page { size: <W+2*bleed>mm <H+2*bleed>mm; margin: 0 } và mỗi trang (.sheet) đúng kích thước đó,"
                  " nội dung không được tràn sang trang mới.", file=sys.stderr)
            sys.exit(1)

        b = mm2pt(bleed)
        result = fitz.open()
        if args.marks:
            mark_off = max(b, mm2pt(3.0))
            slug = mark_off + mm2pt(MARK_LEN_MM + MARK_GAP_MM) - b   # khoảng thêm ngoài vùng bleed
            for i, pg in enumerate(src):
                W, H = pg.rect.width, pg.rect.height
                np_ = result.new_page(width=W + 2 * slug, height=H + 2 * slug)
                bleed_rect = fitz.Rect(slug, slug, slug + W, slug + H)
                np_.show_pdf_page(bleed_rect, src, i)
                trim_rect = fitz.Rect(bleed_rect.x0 + b, bleed_rect.y0 + b, bleed_rect.x1 - b, bleed_rect.y1 - b)
                draw_crop_marks(np_, fitz, trim_rect, b, mark_off, mm2pt(MARK_LEN_MM))
                np_.set_bleedbox(bleed_rect)
                np_.set_trimbox(trim_rect)
        else:
            result.insert_pdf(src)
            for pg in result:
                r = pg.rect
                pg.set_bleedbox(r)
                pg.set_trimbox(fitz.Rect(r.x0 + b, r.y0 + b, r.x1 - b, r.y1 - b))

        result.set_metadata({"title": html.stem, "creator": "AIWF thiet-ke export_print_pdf.py",
                             "producer": "Chromium + PyMuPDF"})
        result.save(str(out), garbage=3, deflate=True)

    chk = fitz.open(str(out))
    p0 = chk[0]
    print(f"✅ Đã xuất PDF: {out}")
    print(f"   Trang: {len(chk)} | MediaBox {pt2mm(p0.rect.width):.1f}x{pt2mm(p0.rect.height):.1f}mm | "
          f"TrimBox {pt2mm(p0.trimbox.width):.1f}x{pt2mm(p0.trimbox.height):.1f}mm | "
          f"BleedBox {pt2mm(p0.bleedbox.width):.1f}x{pt2mm(p0.bleedbox.height):.1f}mm")
    print("   Màu: RGB (Chromium không xuất CMYK) -> ghi chú cho nhà in: [CẦN XÁC MINH: nhà in nhận PDF RGB hay yêu cầu CMYK]")
    print("   BƯỚC TIẾP THEO BẮT BUỘC: chạy preflight.py rồi XEM từng ảnh PNG xuất ra.")


if __name__ == "__main__":
    main()
