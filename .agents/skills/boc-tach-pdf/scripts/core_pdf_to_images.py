"""
core_pdf_to_images.py — Render PDF (hoặc ảnh chụp/scan) thành ảnh trang chất lượng cao.
Tự phát hiện DPI gốc của ảnh nhúng. Có memory protection cho file lớn.

Đầu vào nhận dạng theo magic bytes (không tin phần mở rộng):
  - PDF (scan hoặc có lớp chữ). PDF có mật khẩu → báo rõ, exit 2.
  - Ảnh JPG/PNG/TIFF (nhiều trang)/HEIC (cần pillow-heif)/WEBP/BMP/GIF → mỗi ảnh/khung = 1 trang, giữ đúng
    độ phân giải gốc; dựng 02.process/source.pdf cho các bước sau.
  - Tệp có lớp chữ (DOCX/XLSX/PPTX/ODF/EPUB/HTML/RTF/DOC/...) → TỪ CHỐI, exit 2 (đọc bằng scripts/doc_ingest.py).
    Riêng tệp Office muốn số hoá kiểu OCR: --office-to-pdf (LibreOffice chuyển sang PDF rồi render).

Usage:
    python3 core_pdf_to_images.py <file.pdf|ảnh> [--dpi N] [--output-dir <thư_mục_cha>] [--office-to-pdf]

Exit: 0 ok | 1 không tìm thấy/không render được | 2 tệp bị từ chối/mật khẩu/hỏng | 4 thiếu phụ thuộc.

Mặc định thư mục xử lý: ~/Downloads/AIWF_Output/_process/<tên>_processing
(KHÔNG BAO GIỜ tạo cạnh file PDF của người dùng; KHÔNG tạo trong repo).
"""
try:
    import pymupdf as fitz  # PyMuPDF >= 1.24
except ImportError:  # pragma: no cover
    import fitz
import sys
import os
import shutil
import argparse
import io
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
from doc_ingest_bridge import load_doc_ingest, sniff_kind  # noqa: E402

IMAGE_KINDS = {"png", "jpeg", "tiff", "heic", "webp", "bmp", "gif"}
# Tệp có lớp chữ: không OCR, đọc thẳng bằng doc_ingest. Nhóm OFFICE_KINDS có thể ép sang PDF bằng --office-to-pdf.
OFFICE_KINDS = {"docx", "doc", "odt", "rtf", "xlsx", "xls", "xlsb", "ods", "pptx", "ppt", "odp"}
TEXT_LAYER_KINDS = OFFICE_KINDS | {"epub", "html", "text", "markdown", "csv", "msg"}
MSG_TEXT_LAYER = ("[REFUSE] {name} là tệp {kind} — tệp có lớp chữ → dùng scripts/doc_ingest.py "
                  "(hoặc skill ejv-translate/xu-ly-van-phong), KHÔNG cần OCR:\n"
                  "    .venv/bin/python scripts/doc_ingest.py \"{path}\" --out <thư_mục>")
MSG_PASSWORD = ("[FAIL] {name} được bảo vệ bằng mật khẩu/mã hoá nên không render được (đây KHÔNG phải lỗi scan). "
                "Hãy hỏi người dùng gửi bản không đặt mật khẩu (mở bằng mật khẩu → In → Lưu thành PDF). KHÔNG đoán mật khẩu.")
MSG_HEIC = ("[FAIL] {name} là ảnh HEIC (iPhone) nhưng chưa cài pillow-heif. Cài: `pip3 install pillow-heif` "
            "(hoặc `.venv/bin/pip install pillow-heif`), hoặc xuất ảnh sang JPG (Ảnh/Photos → Xuất) rồi chạy lại.")


class InputError(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


def classify_input(path, office_to_pdf=False):
    """Nhận dạng tệp theo magic bytes → 'pdf' | 'image:<kind>' | 'office:<kind>'. Ném InputError nếu từ chối."""
    p = Path(path)
    kind = sniff_kind(p)
    if kind == "missing":
        raise InputError(f"[FAIL] Không tìm thấy file: {p}", 1)
    if kind == "pdf":
        try:
            doc = fitz.open(str(p))
        except Exception as e:  # noqa: BLE001
            raise InputError(f"[FAIL] PDF hỏng, không mở được ({e}). Hãy hỏi người dùng gửi lại bản gốc.")
        locked = doc.needs_pass or doc.is_encrypted
        n = doc.page_count if not locked else 1
        doc.close()
        if locked:
            raise InputError(MSG_PASSWORD.format(name=p.name))
        if n == 0:
            raise InputError(f"[FAIL] {p.name}: PDF 0 trang.")
        return "pdf"
    if kind in IMAGE_KINDS:
        if kind == "heic":
            try:
                import pillow_heif  # noqa: F401
            except ImportError:
                raise InputError(MSG_HEIC.format(name=p.name), 4)
        return f"image:{kind}"
    if kind == "ooxml_encrypted":
        raise InputError(MSG_PASSWORD.format(name=p.name))
    if kind in OFFICE_KINDS:
        try:
            _, info = load_doc_ingest().detect_format(p)
        except Exception:  # noqa: BLE001
            info = {}
        if info.get("encrypted"):
            raise InputError(MSG_PASSWORD.format(name=p.name))
        if office_to_pdf:
            return f"office:{kind}"
    if kind in TEXT_LAYER_KINDS:
        msg = MSG_TEXT_LAYER.format(name=p.name, kind=kind.upper(), path=p)
        if kind in OFFICE_KINDS:
            msg += ("\n    (Chỉ khi người dùng thật sự muốn số hoá kiểu OCR từ bản in: thêm --office-to-pdf "
                    "để LibreOffice chuyển sang PDF rồi render.)")
        raise InputError(msg)
    raise InputError(f"[FAIL] {p.name} không phải PDF hay ảnh (nhận dạng: {kind}). "
                     "Hãy hỏi người dùng tệp PDF/ảnh scan gốc; tệp khác đọc bằng scripts/doc_ingest.py.")


def images_to_pdf(img_path, out_pdf):
    """Ảnh (mọi khung của TIFF nhiều trang) → PDF; kích thước trang theo DPI ảnh (mặc định 300) để render 1:1."""
    from PIL import Image, ImageOps, ImageSequence
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    raw = Path(img_path).read_bytes()
    out = fitz.open()
    dpis = []
    with Image.open(io.BytesIO(raw)) as im:
        fmt = im.format
        frames = [f.copy() for f in ImageSequence.Iterator(im)]
        dpi = im.info.get("dpi", (0, 0))[0] or 0
    dpi = int(round(dpi)) if dpi and dpi >= 150 else 300
    for fr in frames:
        rotated = fr.getexif().get(0x0112, 1) not in (0, 1)
        upright = ImageOps.exif_transpose(fr) if rotated else fr
        if fmt == "JPEG" and len(frames) == 1 and not rotated:
            data = raw  # giữ nguyên JPEG gốc, không nén lại
        else:
            if upright.mode not in ("RGB", "L", "RGBA", "LA"):
                upright = upright.convert("RGB")
            buf = io.BytesIO()
            upright.save(buf, format="PNG")
            data = buf.getvalue()
        w, h = upright.size
        page = out.new_page(width=w * 72 / dpi, height=h * 72 / dpi)
        page.insert_image(page.rect, stream=data)
        dpis.append(dpi)
    out.save(str(out_pdf))
    out.close()
    return dpis[0] if dpis else 300


def office_to_pdf(src, out_pdf):
    exe = load_doc_ingest().find_soffice()
    if not exe:
        raise InputError("[FAIL] --office-to-pdf cần LibreOffice (soffice): `brew install --cask libreoffice`.", 4)
    shared = Path(tempfile.gettempdir()) / f"aiwf_lo_profile_{os.getuid() if hasattr(os, 'getuid') else 'user'}"
    with tempfile.TemporaryDirectory() as td:
        res, last = Path(td) / (Path(src).stem + ".pdf"), ""
        # Hồ sơ LibreOffice dùng chung có thể đang bị tiến trình khác khoá → thử lại với hồ sơ riêng.
        for profile in (shared, Path(td) / "profile"):
            r = subprocess.run([exe, f"-env:UserInstallation={profile.as_uri()}", "--headless", "--norestore",
                                "--nolockcheck", "--convert-to", "pdf", "--outdir", td, str(src)],
                               capture_output=True, text=True, timeout=240, stdin=subprocess.DEVNULL)
            last = (r.stderr or r.stdout or "").strip()[-300:]
            if res.exists():
                break
        if not res.exists():
            raise InputError(f"[FAIL] LibreOffice không chuyển được {Path(src).name} sang PDF: {last}")
        shutil.move(str(res), str(out_pdf))


def detect_native_dpi(doc, max_pages_to_scan=3):
    """Tính DPI gốc của ảnh nhúng trong PDF scan.
    Quét vài trang đầu, lấy DPI cao nhất tìm thấy.
    """
    detected_dpi = 0
    for page_idx in range(min(max_pages_to_scan, len(doc))):
        page = doc[page_idx]
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            try:
                bbox = page.get_image_bbox(img)
                if bbox.is_empty or bbox.width <= 0 or bbox.height <= 0:
                    continue
                img_info = doc.extract_image(xref)
                w = img_info["width"]
                h = img_info["height"]
                dpi_x = (w / bbox.width) * 72
                dpi_y = (h / bbox.height) * 72
                detected_dpi = max(detected_dpi, dpi_x, dpi_y)
            except Exception:
                continue
    return detected_dpi


def setup_and_render(pdf_path, forced_dpi=None, output_dir=None, office_pdf=False):
    pdf_path = Path(pdf_path).resolve()
    try:
        input_kind = classify_input(pdf_path, office_to_pdf=office_pdf)
    except InputError as e:
        print(str(e))
        setup_and_render.last_code = e.code
        return None

    # Khởi tạo cây thư mục
    default_parent = Path(os.environ.get("AIWF_OUTPUT_DIR", "~/Downloads/AIWF_Output")).expanduser() / "_process"
    parent_dir = Path(output_dir).expanduser().resolve() if output_dir else default_parent
    base_dir = parent_dir / f"{pdf_path.stem}_processing"
    input_dir = base_dir / "01.input"
    process_dir = base_dir / "02.process"
    final_output_dir = base_dir / "03.output"

    for d in [input_dir, process_dir, final_output_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Lưu đường dẫn PDF gốc để các script khác tham chiếu
    # source.txt = PDF mà analyze_format/extract_images mở; với ảnh/Office là bản PDF dựng lại trong 02.process,
    # còn source_original.txt giữ tệp gốc của người dùng.
    source_txt = process_dir / "source.txt"
    orig_txt = process_dir / "source_original.txt"
    prev = orig_txt if orig_txt.exists() else source_txt
    if prev.exists() and prev.read_text(encoding="utf-8").strip() != str(pdf_path):
        print(f"[WARN] {base_dir} đang chứa dữ liệu của file khác ({prev.read_text(encoding='utf-8').strip()}). "
              f"Dùng --output-dir khác hoặc xoá thư mục cũ.")
        return None

    print(f"[INFO] Cây thư mục: {base_dir}")
    image_dpi = None
    render_src = pdf_path
    if input_kind != "pdf":
        render_src = process_dir / "source.pdf"
        try:
            if input_kind.startswith("image:"):
                image_dpi = images_to_pdf(pdf_path, render_src)
                print(f"[INFO] Đầu vào là ảnh ({input_kind[6:]}) → dựng {render_src.name}, giữ độ phân giải gốc")
            else:
                office_to_pdf(pdf_path, render_src)
                print(f"[INFO] --office-to-pdf: LibreOffice đã chuyển {pdf_path.name} → {render_src.name}")
        except InputError as e:
            print(str(e))
            setup_and_render.last_code = e.code
            return None
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] Không đọc được ảnh {pdf_path.name}: {e}")
            return None
        orig_txt.write_text(str(pdf_path), encoding="utf-8")
    source_txt.write_text(str(render_src), encoding="utf-8")
    pdf_path = render_src

    # Mở PDF
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        print(f"[FAIL] Không mở được PDF: {e}")
        return None

    total_pages = len(doc)
    page_size = doc[0].rect if total_pages > 0 else None

    # Xác định DPI
    if forced_dpi:
        render_dpi = min(forced_dpi, 600)
        dpi_source = f"override ({forced_dpi} → cap {render_dpi})"
    elif image_dpi:
        render_dpi = image_dpi
        dpi_source = "ảnh gốc (1:1 điểm ảnh)"
    else:
        native_dpi = detect_native_dpi(doc)
        if native_dpi > 100:
            render_dpi = min(int(native_dpi), 600)
            dpi_source = f"native ({int(native_dpi)} → cap {render_dpi})"
        else:
            render_dpi = 300
            dpi_source = "fallback (300 — không phát hiện ảnh nhúng)"

    # Metadata
    print(f"[INFO] Số trang: {total_pages}")
    if page_size:
        print(f"[INFO] Kích thước trang: {page_size.width:.0f} x {page_size.height:.0f} pt")
    print(f"[INFO] DPI render: {render_dpi} ({dpi_source})")

    # Render từng trang
    zoom = render_dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    batch_size = 50  # Memory protection: shrink cache mỗi batch

    image_paths = []
    for i in range(total_pages):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        output_file = input_dir / f"page_{i+1:03d}.png"
        pix.save(str(output_file))
        image_paths.append(str(output_file))

        # Memory protection: shrink cache mỗi batch
        if (i + 1) % batch_size == 0:
            fitz.TOOLS.store_shrink(100)
            print(f"  ... đã render {i+1}/{total_pages} trang")

    doc.close()
    fitz.TOOLS.store_shrink(100)  # Clean up cuối

    print(f"\n[OK] Đã render {len(image_paths)} ảnh tại: {input_dir}")
    print(f"[OK] Thư mục process (lưu MD): {process_dir}")
    print(f"[OK] Thư mục output: {final_output_dir}")
    print(f"[OK] DPI: {render_dpi}")
    return str(base_dir)


def main():
    parser = argparse.ArgumentParser(description="Render PDF/ảnh scan thành ảnh trang chất lượng cao")
    parser.add_argument("pdf_path", help="Đường dẫn file PDF hoặc ảnh (JPG/PNG/TIFF/HEIC)")
    parser.add_argument("--dpi", type=int, default=None,
                        help="Override DPI (mặc định: tự phát hiện, cap 600)")
    parser.add_argument("--output-dir", "-o", type=str, default=None,
                        help="Thư mục cha chứa <tên>_processing (mặc định: ~/Downloads/AIWF_Output/_process)")
    parser.add_argument("--office-to-pdf", action="store_true",
                        help="Tệp Office (DOCX/XLSX/PPTX/ODF/RTF/DOC): chuyển sang PDF bằng LibreOffice rồi render "
                             "(chỉ khi người dùng muốn số hoá kiểu OCR; bình thường đọc bằng scripts/doc_ingest.py)")
    args = parser.parse_args()

    setup_and_render.last_code = 1
    result = setup_and_render(args.pdf_path, forced_dpi=args.dpi, output_dir=args.output_dir,
                              office_pdf=args.office_to_pdf)
    if result is None:
        sys.exit(setup_and_render.last_code)


if __name__ == "__main__":
    main()
