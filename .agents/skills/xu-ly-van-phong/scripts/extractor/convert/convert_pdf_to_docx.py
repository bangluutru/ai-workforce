"""Chuyển PDF số (có lớp chữ) → DOCX giữ bố cục bằng pdf2docx.

    .venv/bin/python scripts/extractor/convert/convert_pdf_to_docx.py input.pdf output.docx

Mã thoát: 0 = xong; 2 = không phải PDF / có mật khẩu / hỏng; 4 = thiếu pdf2docx (KHÔNG tự cài).
PDF scan (không có lớp chữ): vẫn chuyển nhưng DOCX chỉ chứa ảnh → tái tạo bằng Vision (resources/pdf.md).
"""
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parents[4] / "_shared"   # .agents/skills/_shared


def convert_pdf_to_docx(pdf_file, output_file):
    """Convert PDF file to DOCX using pdf2docx."""
    try:
        from pdf2docx import Converter
    except ImportError:
        print("❌ THIẾU pdf2docx (đã có trong requirements.txt). Cài: `.venv/bin/pip install pdf2docx` "
              "hoặc chạy `bash scripts/auto-setup.sh`, rồi chạy lại bằng `.venv/bin/python`.", file=sys.stderr)
        sys.exit(4)

    sys.path.insert(0, str(SHARED))
    from doc_ingest_bridge import pdf_preflight
    pre = pdf_preflight(pdf_file)
    if pre["code"] == 2:
        print(f"❌ {pre['message']}", file=sys.stderr)
        sys.exit(2)
    if pre["code"] == 3 or pre["scan_pages"]:
        print(f"⚠️  Trang scan (không có lớp chữ): {pre['scan_pages'][:30]} → DOCX chỉ chứa ảnh ở các trang này; "
              "cần chữ thì tái tạo bằng Vision (resources/pdf.md).", file=sys.stderr)
    for w in pre["warnings"]:
        print(w if w.startswith("⚠") else f"⚠️  {w}", file=sys.stderr)

    print(f"Converting {pdf_file} to {output_file}...")
    cv = Converter(pdf_file)
    cv.convert(output_file, start=0, end=None)
    cv.close()
    print(f"Created: {output_file}")


if __name__ == '__main__':
    if len(sys.argv) > 2:
        convert_pdf_to_docx(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python convert_pdf_to_docx.py <input.pdf> <output.docx>")
        sys.exit(2)
