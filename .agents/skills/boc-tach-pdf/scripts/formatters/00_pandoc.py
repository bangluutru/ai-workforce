"""
00_pandoc.py — Layer 0: MERGED.md -> DOCX thô bằng Pandoc + reference.docx.

Tiền xử lý Markdown (ENRICHED.md) trước khi đưa vào Pandoc:
  1. Hình minh họa: thay placeholder bằng ảnh thật.
       [Hình minh họa: mô tả]                               -> ảnh nhúng kế tiếp của trang đó (image_map.json)
       [Hình minh họa: mô tả | file=img_p3_0.jpeg]          -> đúng file đó
       [Hình minh họa: mô tả | crop=0.10,0.42,0.90,0.71]    -> cắt từ ẢNH GỐC trang (toạ độ tỉ lệ 0-1: x0,y0,x1,y1)
     Placeholder không giải được -> giữ nguyên dạng chữ nghiêng và BÁO CÁO (không im lặng).
  2. <!-- page: N --> -> [PAGE_MARKER_N] (để Layer 1 xử lý trang ngang + xóa số trang).
  3. Khối header trang 1 (trước tên loại VB / "Kính gửi" / heading đầu): giữ NGẮT DÒNG CỨNG để Layer 2
     dựng lại header NĐ 30 đúng từng dòng (cơ quan chủ quản / cơ quan ban hành ...).
  4. <center>..</center> và <div style="text-align: right">..</div> -> custom-style "Center"/"Right"
     (Pandoc bỏ HTML thô khi xuất DOCX nên căn lề sẽ mất nếu không chuyển).
"""
import json
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt

PLACEHOLDER_RE = re.compile(r"\[Hình minh họa:\s*([^\]|]*?)\s*((?:\|\s*[a-z]+\s*=\s*[^\]|]+\s*)*)\]")
PAGE_RE = re.compile(r"<!--\s*page:\s*(\d+)\s*-->")
TITLE_RE = re.compile(
    r"^\W*(TỜ TRÌNH|QUYẾT ĐỊNH|NGHỊ QUYẾT|NGHỊ ĐỊNH|THÔNG TƯ|CHỈ THỊ|QUY CHẾ|QUY ĐỊNH|THÔNG CÁO|THÔNG BÁO|"
    r"HƯỚNG DẪN|CHƯƠNG TRÌNH|KẾ HOẠCH|PHƯƠNG ÁN|ĐỀ ÁN|DỰ ÁN|BÁO CÁO|BIÊN BẢN|HỢP ĐỒNG|CÔNG ĐIỆN|"
    r"BẢN GHI NHỚ|BẢN THỎA THUẬN|GIẤY|PHIẾU|THƯ CÔNG|LUẬT|PHÁP LỆNH|CÔNG VĂN)\b")


def parse_opts(raw):
    opts = {}
    for part in raw.split("|"):
        if "=" in part:
            k, v = part.split("=", 1)
            opts[k.strip()] = v.strip()
    return opts


def crop_figure(input_dir, out_dir, page, box, idx):
    from PIL import Image
    src = input_dir / f"page_{page:03d}.png"
    if not src.exists():
        return None
    try:
        x0, y0, x1, y1 = [float(v) for v in box.split(",")]
    except ValueError:
        return None
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        return None
    im = Image.open(src)
    W, H = im.size
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"fig_p{page:03d}_{idx}.png"
    im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))).save(out)
    return out


def header_hard_breaks(page_text):
    """Trong khối header trang 1, nối các dòng của cùng đoạn bằng ngắt dòng cứng (\\ cuối dòng)."""
    lines = page_text.split("\n")
    cut = len(lines)
    for i, ln in enumerate(lines[:40]):
        s = ln.strip().replace("*", "").replace("#", "").strip()
        # Hết vùng header: heading Markdown, câu thân bài (Căn cứ/Thực hiện/Xét/Theo đề nghị), hoặc dòng dài
        if (ln.lstrip().startswith("#") or re.match(r"^(Căn cứ|Thực hiện|Xét|Theo đề nghị)\b", s)
                or len(s) > 160):
            cut = i
            break
    head = [ln for ln in lines[:cut] if not re.match(r"^\s*<!--.*-->\s*$", ln)]
    out, para = [], []

    def flush():
        if para:
            out.append("\\\n".join(para))
            para.clear()

    for ln in head:
        if ln.strip():
            para.append(ln.rstrip())
        else:
            flush()
            out.append("")
    flush()
    return "\n".join(out + lines[cut:])


def html_to_custom_styles(text):
    text = re.sub(r"<center>\s*(.*?)\s*</center>",
                  lambda m: f'\n::: {{custom-style="Center"}}\n{m.group(1)}\n:::\n', text, flags=re.S)
    text = re.sub(r'<div\s+style="text-align:\s*right;?">\s*(.*?)\s*</div>',
                  lambda m: f'\n::: {{custom-style="Right"}}\n{m.group(1)}\n:::\n', text, flags=re.S)
    return text


def enrich_md_with_images(merged_md_path, image_map_path, input_dir, process_dir=None):
    """Trả về (đường dẫn ENRICHED.md, báo cáo dict)."""
    merged_md_path = Path(merged_md_path)
    input_dir = Path(input_dir)
    process_dir = Path(process_dir) if process_dir else merged_md_path.parent
    md_text = merged_md_path.read_text(encoding="utf-8")

    image_map = []
    if Path(image_map_path).exists():
        image_map = json.loads(Path(image_map_path).read_text(encoding="utf-8"))
    by_file = {e["filename"]: e for e in image_map}
    by_page = {}
    for e in sorted(image_map, key=lambda e: (e.get("page", 0), (e.get("bbox") or [0, 0])[1])):
        by_page.setdefault(e.get("page"), []).append(e)
    used = set()
    report = {"placeholders": 0, "resolved": 0, "unresolved": []}

    # Tách theo trang để biết placeholder thuộc trang nào
    parts = PAGE_RE.split(md_text)
    pieces = [(None, parts[0])] + [(int(parts[i]), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
    out = []
    first_page_seen = False
    for page, body in pieces:
        fig_idx = 0

        def replacer(m):
            nonlocal fig_idx
            report["placeholders"] += 1
            desc, opts = m.group(1).strip(), parse_opts(m.group(2) or "")
            path = None
            if opts.get("file") in by_file:
                path = input_dir / opts["file"]
                used.add(opts["file"])
            elif "crop" in opts and page:
                fig_idx += 1
                path = crop_figure(input_dir, process_dir / "figures", page, opts["crop"], fig_idx)
            elif page in by_page:
                nxt = next((e for e in by_page[page] if e["filename"] not in used), None)
                if nxt:
                    used.add(nxt["filename"])
                    path = input_dir / nxt["filename"]
            if path and Path(path).exists():
                report["resolved"] += 1
                return f"![{desc}]({Path(path).resolve().as_posix()})"
            report["unresolved"].append({"page": page, "placeholder": m.group(0)})
            return f"*[Hình minh họa: {desc}]*"

        body = PLACEHOLDER_RE.sub(replacer, body)
        if page is not None and not first_page_seen:
            body = header_hard_breaks(body)
            first_page_seen = True
        body = html_to_custom_styles(body)
        out.append(body if page is None else f"\n[PAGE_MARKER_{page}]\n\n{body.strip()}\n")

    enriched_path = process_dir / "ENRICHED.md"
    enriched_path.write_text("".join(out), encoding="utf-8")
    unused = [e["filename"] for e in image_map if e["filename"] not in used]
    report["unused_images"] = unused
    return enriched_path, report


def export_with_pandoc(enriched_md, reference_docx, output_docx, resource_dirs):
    """Sử dụng pypandoc-binary để chuyển đổi sang DOCX."""
    try:
        import pypandoc
        args = [
            f"--reference-doc={reference_docx}",
            "--wrap=none",
            "--resource-path=" + ":".join(str(d) for d in resource_dirs),
            "+RTS", "-V0", "-RTS",
        ]
        pypandoc.convert_file(str(enriched_md), "docx", format="markdown",
                              outputfile=str(output_docx), extra_args=args)
        return True
    except ImportError:
        print("[WARN] Chưa cài đặt pypandoc-binary (pip3 install pypandoc-binary).")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] Pandoc lỗi: {e}")
        return False


def export_fallback_docx(enriched_md, format_spec, output_docx):
    """Fallback xuất DOCX bằng python-docx (không dùng reference.docx). CHẤT LƯỢNG THẤP: bảng/ảnh không giữ."""
    print("[WARN] Đang dùng fallback python-docx: bảng và ảnh sẽ KHÔNG được dựng. Hãy cài pypandoc-binary.")
    doc = Document()
    with open(enriched_md, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            p = doc.add_paragraph()
            if line.startswith("## "):
                run = p.add_run(line[3:]); run.font.size = Pt(16); run.font.bold = True
            elif line.startswith("### "):
                run = p.add_run(line[4:]); run.font.size = Pt(14); run.font.bold = True
            else:
                p.add_run(line)
    doc.save(str(output_docx))
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 00_pandoc.py <processing_dir> <output_docx>")
        sys.exit(1)

    processing_dir = Path(sys.argv[1]).resolve()
    output_docx = Path(sys.argv[2])
    process_dir = processing_dir / "02.process"
    input_dir = processing_dir / "01.input"
    merged_md = process_dir / "MERGED.md"
    reference_docx = process_dir / "reference.docx"
    image_map_path = process_dir / "image_map.json"
    format_spec_path = process_dir / "format_spec.json"

    if not merged_md.exists():
        print("[FAIL] Không tìm thấy 02.process/MERGED.md (chạy core_merge_md.py trước)")
        sys.exit(1)
    format_spec = json.loads(format_spec_path.read_text(encoding="utf-8"))

    print("[INFO] Bước 0: Chèn hình minh họa + chuẩn hóa Markdown...")
    enriched, rep = enrich_md_with_images(merged_md, image_map_path, input_dir, process_dir)
    print(f"[INFO] Hình minh họa: {rep['resolved']}/{rep['placeholders']} placeholder đã gắn ảnh.")
    for u in rep["unresolved"]:
        print(f"  [WARN] Trang {u['page']}: chưa có ảnh cho {u['placeholder']} -> thêm '| crop=x0,y0,x1,y1'")
    if rep["unused_images"]:
        print(f"  [WARN] Ảnh trích xuất chưa được dùng: {rep['unused_images']}")
    (process_dir / "figures_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[INFO] Bước 0: Xuất DOCX bằng Pandoc + reference template...")
    success = False
    if reference_docx.exists():
        success = export_with_pandoc(enriched, reference_docx, output_docx, [process_dir, input_dir])
    else:
        print("[WARN] Thiếu reference.docx (chạy generate_reference.py).")
    if not success:
        success = export_fallback_docx(enriched, format_spec, output_docx)
    if success:
        print(f"[OK] Đã xuất DOCX thô thành công: {output_docx.name}")
    else:
        print("[FAIL] Xuất DOCX thất bại")
        sys.exit(1)
