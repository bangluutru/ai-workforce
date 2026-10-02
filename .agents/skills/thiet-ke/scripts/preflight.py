#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preflight.py - Kiểm tra PDF in ấn trước khi bàn giao (thiet-ke). Thoát mã 1 nếu có lỗi FAIL.

Kiểm tra:
  1. Hình học: TrimBox có và đúng khổ thành phẩm; BleedBox = TrimBox + bleed mỗi cạnh; MediaBox chứa BleedBox.
  2. Font: 100% nhúng; KHÔNG có font dự phòng (Times / Helvetica / Arial / Courier...) = dấu hiệu font thiết kế không tải được
     -> tiếng Việt vỡ dấu; chặn glyph Type3 (emoji bitmap / font biến thiên).
  3. Ảnh: độ phân giải hiệu dụng >= --min-ppi (mặc định 300) ở kích thước đặt trên trang.
  4. Chữ: không còn placeholder [[...]]; liệt kê [CẦN XÁC MINH ...]; chữ nằm ngoài vùng an toàn / ngoài mép xén.
  5. Màu: báo hệ màu ảnh (RGB/CMYK) để xác nhận với nhà in.
  6. Render từng trang ra PNG (bản đầy đủ + bản đã xén) để Agent BẮT BUỘC mở xem.

  .venv/bin/python .agents/skills/thiet-ke/scripts/preflight.py --pdf <file.pdf> --trim 297x210 --bleed 3 \
      --render-dir <process_dir>/preview
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from print_common import parse_size, pt2mm, require_fitz  # noqa: E402

FALLBACK_FONT_PAT = re.compile(r"(Times|Helvetica|Arial|Courier|LiberationS|DejaVu|Verdana|Georgia|Hiragino|"
                               r"PingFang|STHeiti|Menlo|Geneva|LucidaGrande|\.SF)", re.I)
BUNDLED_FONT_PAT = re.compile(r"(BeVietnamPro|Be ?Vietnam ?Pro|Spectral)", re.I)


def main():
    ap = argparse.ArgumentParser(description="Preflight PDF in ấn (thiet-ke)")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--trim", help="Khổ thành phẩm mm (vd 297x210). Bỏ trống = chỉ kiểm tra nhất quán các box")
    ap.add_argument("--bleed", type=float, default=3.0, help="Bleed mm mỗi cạnh (0 cho slide)")
    ap.add_argument("--safe", type=float, default=5.0, help="Lề an toàn mm tính từ mép xén")
    ap.add_argument("--min-ppi", type=float, default=300.0)
    ap.add_argument("--render-dir", required=True, help="Thư mục lưu PNG xem trước + báo cáo")
    ap.add_argument("--dpi", type=int, default=110, help="DPI ảnh xem trước")
    ap.add_argument("--allow-font", action="append", default=[], help="Tên font được phép thêm (có giấy phép, đủ dấu)")
    args = ap.parse_args()

    fitz = require_fitz()
    pdf = Path(args.pdf)
    if not pdf.exists():
        print(f"❌ Không thấy file {pdf}", file=sys.stderr)
        sys.exit(1)
    doc = fitz.open(str(pdf))
    out_dir = Path(args.render_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fails, warns, infos = [], [], []
    tol = 0.6  # mm
    trim_exp = parse_size(args.trim) if args.trim else None
    verify_flags, placeholders = [], []
    fonts_seen = {}
    colorspaces = set()
    pngs = []

    for pno, page in enumerate(doc, start=1):
        media, trim, bleed = page.rect, page.trimbox, page.bleedbox
        tw, th = pt2mm(trim.width), pt2mm(trim.height)
        # ---- 1. Hình học
        if args.bleed > 0 and abs(trim.width - media.width) < 0.5 and abs(trim.height - media.height) < 0.5:
            fails.append(f"Trang {pno}: TrimBox = MediaBox ({tw:.1f}x{th:.1f}mm) -> KHÔNG có bleed. Xuất lại bằng export_print_pdf.py.")
        if trim_exp and (abs(tw - trim_exp[0]) > tol or abs(th - trim_exp[1]) > tol):
            fails.append(f"Trang {pno}: TrimBox {tw:.1f}x{th:.1f}mm khác khổ thành phẩm yêu cầu {trim_exp[0]:g}x{trim_exp[1]:g}mm.")
        bw, bh = pt2mm(bleed.width), pt2mm(bleed.height)
        if abs(bw - (tw + 2 * args.bleed)) > tol or abs(bh - (th + 2 * args.bleed)) > tol:
            fails.append(f"Trang {pno}: BleedBox {bw:.1f}x{bh:.1f}mm != TrimBox + 2x{args.bleed:g}mm.")
        if not media.contains(bleed):
            fails.append(f"Trang {pno}: BleedBox nằm ngoài MediaBox.")

        # ---- 2. Font
        for f in page.get_fonts(full=True):
            xref, ext, ftype, basefont = f[0], f[1], f[2], f[3]
            name = basefont.split("+", 1)[-1] or f"(Type3 không tên, xref {xref})"
            if ftype == "Type3":
                name = "Type3-glyphs"  # gom chung: emoji bitmap hoặc font biến thiên bị chuyển Type3
            fonts_seen.setdefault(name, {"embedded": ext != "n/a" or ftype == "Type3", "type": ftype,
                                         "pages": set()})["pages"].add(pno)

        # ---- 3. Ảnh
        for info in page.get_image_info(xrefs=True):
            bb = fitz.Rect(info["bbox"])
            if bb.is_empty or bb.width < 2 or bb.height < 2:
                continue
            vis = bb & trim if args.bleed >= 0 else bb
            if vis.is_empty:
                continue
            ppi_x = info["width"] / (bb.width / 72.0)
            ppi_y = info["height"] / (bb.height / 72.0)
            ppi = min(ppi_x, ppi_y)
            cs = info.get("cs-name") or str(info.get("colorspace"))
            colorspaces.add(cs)
            need_w = int(round(bb.width / 72.0 * args.min_ppi))
            msg = (f"Trang {pno}: ảnh {info['width']}x{info['height']}px đặt ở {pt2mm(bb.width):.0f}x{pt2mm(bb.height):.0f}mm "
                   f"= {ppi:.0f}ppi (cần >= {args.min_ppi:.0f}ppi, tức >= {need_w}px chiều ngang)")
            if ppi >= args.min_ppi:
                infos.append(msg)
            elif info.get("xref", 0) == 0:
                # Ảnh inline do Chromium raster hóa hiệu ứng CSS (gradient trong suốt, bóng đổ, blur), không phải ảnh chụp
                warns.append(msg + " - hiệu ứng CSS (gradient/bóng) bị raster hóa: soi dải màu trên ảnh xem trước")
            else:
                fails.append(msg)

        # ---- 4. Chữ
        safe = fitz.Rect(trim.x0, trim.y0, trim.x1, trim.y1)
        s = args.safe * 72 / 25.4
        safe = fitz.Rect(safe.x0 + s, safe.y0 + s, safe.x1 - s, safe.y1 - s)
        text = page.get_text()
        placeholders += [f"Trang {pno}: {m}" for m in re.findall(r"\[\[[^\]]{0,60}\]\]", text)]
        verify_flags += [f"Trang {pno}: {m}" for m in re.findall(r"\[CẦN XÁC MINH[^\]]{0,80}\]", text)]
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    t = span["text"].strip()
                    if not t:
                        continue
                    r = fitz.Rect(span["bbox"])
                    if not trim.contains(r) and not (r & trim).is_empty:
                        fails.append(f"Trang {pno}: chữ bị CẮT ở mép xén: \"{t[:40]}\"")
                    elif trim.contains(r) and not safe.contains(r):
                        warns.append(f"Trang {pno}: chữ nằm ngoài vùng an toàn {args.safe:g}mm: \"{t[:40]}\"")

        # ---- 6. Render
        full_png = out_dir / f"page-{pno:02d}_full.png"
        page.get_pixmap(dpi=args.dpi).save(str(full_png))
        trim_png = out_dir / f"page-{pno:02d}_trimmed.png"
        page.get_pixmap(dpi=args.dpi, clip=trim).save(str(trim_png))
        pngs += [str(trim_png), str(full_png)]

    # Tổng hợp font
    for name, meta in sorted(fonts_seen.items()):
        pages = sorted(meta["pages"])
        allowed = BUNDLED_FONT_PAT.search(name) or any(a.lower() in name.lower() for a in args.allow_font)
        if not meta["embedded"]:
            fails.append(f"Font KHÔNG nhúng: {name} (trang {pages})")
        elif meta["type"] == "Type3":
            fails.append(f"Có glyph Type3 ở trang {pages}: thường do emoji (bitmap, in bị răng cưa) hoặc font biến thiên. "
                         f"Thay emoji bằng icon SVG, chỉ dùng font tĩnh trong fonts/fonts.css.")
        elif FALLBACK_FONT_PAT.search(name) and not allowed:
            fails.append(f"Font DỰ PHÒNG '{name}' (trang {pages}): font thiết kế không tải được -> nguy cơ vỡ dấu tiếng Việt. "
                         f"Dùng font đóng gói (Be Vietnam Pro / Spectral) qua fonts/fonts.css.")
        elif not allowed:
            warns.append(f"Font ngoài bộ đóng gói: {name} (trang {pages}) - xác nhận giấy phép và đủ dấu tiếng Việt")
    if placeholders:
        fails.append(f"Còn {len(placeholders)} placeholder chưa thay: " + "; ".join(placeholders[:8]))
    if verify_flags:
        warns.append(f"{len(verify_flags)} mục [CẦN XÁC MINH] phải liệt kê cho người dùng: " + "; ".join(verify_flags[:10]))
    rgb = [c for c in colorspaces if "RGB" in c.upper()]
    if rgb or not colorspaces:
        warns.append("Hệ màu RGB (Chromium không xuất CMYK). Ghi rõ khi bàn giao: [CẦN XÁC MINH: nhà in chấp nhận PDF RGB?]")

    report = {"pdf": str(pdf), "pages": len(doc), "fails": fails, "warnings": warns, "info": infos,
              "fonts": {k: {"embedded": v["embedded"], "type": v["type"], "pages": sorted(v["pages"])} for k, v in fonts_seen.items()},
              "verify_flags": verify_flags, "preview_pngs": pngs,
              "status": "FAIL" if fails else "PASS_PENDING_VISUAL_REVIEW"}
    (out_dir / "preflight_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 70)
    print(f"PREFLIGHT {pdf.name}: {len(doc)} trang")
    for f_ in fails:
        print(f"  ❌ {f_}")
    for w in warns:
        print(f"  ⚠️  {w}")
    for i in infos:
        print(f"  ✓ {i}")
    print("-" * 70)
    print("BẮT BUỘC - KIỂM TRA THỊ GIÁC: mở (view_file) TỪNG ảnh dưới đây, ưu tiên bản *_trimmed.png:")
    for p in pngs:
        print(f"   {p}")
    print("   Soát: dấu tiếng Việt đúng; chữ đủ tương phản; không chữ nào sát mép/nếp gấp; ảnh không vỡ;")
    print("   phân cấp tiêu đề rõ; không còn khoảng trống chết; nội dung khớp facts.md.")
    print("=" * 70)
    if fails:
        print(f"❌ PREFLIGHT FAIL ({len(fails)} lỗi). Sửa design.html -> xuất lại -> chạy lại preflight.")
        sys.exit(1)
    print("✅ PREFLIGHT KỸ THUẬT ĐẠT - chưa được bàn giao cho tới khi đã xem hết ảnh xem trước.")


if __name__ == "__main__":
    main()
