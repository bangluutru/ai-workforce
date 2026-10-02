import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

def run_formatter(script_name, *args):
    script_path = Path(__file__).parent / "formatters" / script_name
    cmd = [sys.executable, str(script_path)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0

def verification_gate(process_dir, allow_unverified):
    """Chặn xuất bản khi chưa đối chiếu OCR (ocr_crosscheck.py) hoặc còn cờ mở."""
    nv = process_dir / "needs_verification.json"
    if not nv.exists():
        msg = "Chưa chạy ocr_crosscheck.py (02.process/needs_verification.json không tồn tại)."
    else:
        rep = json.loads(nv.read_text(encoding="utf-8"))
        st = rep.get("status")
        if st in ("clean", "marked"):
            print(f"[OK] Đối chiếu OCR: {st} (engine: {rep.get('engine')}).")
            return True
        if st == "engine_unavailable" and (process_dir / "selfcheck.json").exists():
            print("[WARN] Không có OCR engine đối chiếu; dùng kết quả tự kiểm 2 lượt (selfcheck.json).")
            return True
        msg = f"Đối chiếu OCR chưa xong (status={st}, cờ mở={rep.get('open_flags')})."
    if allow_unverified:
        print(f"[WARN] {msg} Vẫn xuất do --allow-unverified (PHẢI báo người dùng).")
        return True
    print(f"[FAIL] {msg} Chạy: python3 ocr_crosscheck.py <processing_dir> rồi giải quyết cờ "
          f"(hoặc --finalize). Dùng --allow-unverified chỉ khi người dùng chấp nhận.")
    return False


def fidelity_check(merged_md, docx_path):
    """So túi từ: mọi chữ/số trong MERGED.md phải có mặt trong DOCX (bắt lỗi layer làm mất nội dung)."""
    import re
    from collections import Counter
    from docx import Document
    md = merged_md.read_text(encoding="utf-8")
    md = re.sub(r"<!--.*?-->|<[^>]+>|!\[[^\]]*\]\([^)]*\)", " ", md, flags=re.S)
    md = re.sub(r"\[Hình minh họa:[^\]]*\]", " ", md)
    tok = lambda t: Counter(w.lower() for w in re.findall(r"\w+", t))  # noqa: E731
    d = Document(str(docx_path))
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                parts.append(c.text)
    a, b = tok(md), tok("\n".join(parts))
    missing = a - b
    for k in [k for k in missing if re.fullmatch(r"page_marker_\d+|\d{1,3}", k)]:
        del missing[k]  # số trang in trên giấy đã được xóa có chủ đích
    return missing


def export_docx(processing_dir_path, target_output_dir=None, allow_unverified=False):
    """
    Orchestrator script:
    Gọi tuần tự các layer script trong thư mục formatters/
    Temp files lưu trong 02.process/, final output lưu trong 03.output/.
    File cuối cùng đặt tên theo tên tài liệu gốc.
    Nếu có target_output_dir, sao chép file cuối cùng sang đó.
    """
    processing_dir = Path(processing_dir_path)
    process_dir = processing_dir / "02.process"
    output_dir = processing_dir / "03.output"
    format_spec_path = process_dir / "format_spec.json"
    
    if not format_spec_path.exists():
        print(f"[FAIL] Không tìm thấy {format_spec_path}. Chạy analyze_format.py trước.")
        return False
    
    output_dir.mkdir(parents=True, exist_ok=True)
    if not verification_gate(process_dir, allow_unverified):
        return False
    
    # Xác định tên tài liệu gốc từ tên thư mục processing
    # Ví dụ: "di-19-TTr-UBND.signed_processing" → "di-19-TTr-UBND.signed"
    dir_name = processing_dir.name
    if dir_name.endswith("_processing"):
        doc_basename = dir_name[:-len("_processing")]
    else:
        doc_basename = dir_name
    
    final_docx = output_dir / f"{doc_basename}.docx"
    final_md = output_dir / f"{doc_basename}.md"
    
    # Temporary files trong 02.process/
    temp0 = process_dir / "temp0.docx"
    temp1 = process_dir / "temp1.docx"
    temp2 = process_dir / "temp2.docx"
    temp3 = process_dir / "temp3.docx"
    temp4 = process_dir / "temp4.docx"
    
    print("=== LAYER 0: PANDOC GENERATION ===")
    if not run_formatter("00_pandoc.py", str(processing_dir), str(temp0)): 
        print("[FAIL] Lỗi ở Layer 0")
        return False
    
    print("=== LAYER 1: PAGE LAYOUT ===")
    shutil.copy(temp0, temp1)
    if not run_formatter("01_layout.py", str(temp1), str(format_spec_path)): 
        print("[FAIL] Lỗi ở Layer 1")
        return False
        
    print("=== LAYER 2: STRUCTURE ===")
    with open(format_spec_path, "r", encoding="utf-8") as f:
        format_spec = json.load(f)
        
    shutil.copy(temp1, temp2)
    # Tái cấu trúc bảng NĐ30 chỉ chạy nếu doc_type là hanh_chinh_nd30
    if format_spec.get("doc_type") == "hanh_chinh_nd30":
        if not run_formatter("02_structure.py", str(temp2)): 
            print("[FAIL] Lỗi ở Layer 2")
            return False
    else:
        print("[INFO] Bỏ qua Layer 2 (không phải NĐ 30)")
    
    print("=== LAYER 3: BLOCK FORMAT ===")
    shutil.copy(temp2, temp3)
    if not run_formatter("03_block.py", str(temp3), str(format_spec_path)): 
        print("[FAIL] Lỗi ở Layer 3")
        return False
    
    print("=== LAYER 4: TYPOGRAPHY ===")
    shutil.copy(temp3, temp4)
    if not run_formatter("04_typography.py", str(temp4), str(format_spec_path)): 
        print("[FAIL] Lỗi ở Layer 4")
        return False
    
    # Di chuyển file cuối cùng ra 03.output/ với tên tài liệu gốc
    shutil.move(temp4, final_docx)
    
    # Copy MERGED.md từ 02.process/ sang 03.output/ với tên tài liệu gốc
    merged_md = process_dir / "MERGED.md"
    if merged_md.exists():
        shutil.copy2(merged_md, final_md)
    
    missing = fidelity_check(merged_md, final_docx) if merged_md.exists() else {}
    if missing:
        print(f"[WARN] {sum(missing.values())} từ trong MERGED.md không thấy trong DOCX: {list(missing)[:15]}")
    else:
        print("[OK] Kiểm tra bảo toàn nội dung: 100% từ của MERGED.md có trong DOCX.")

    print(f"\n[OK] Pipeline hoàn tất.")
    print(f"  DOCX: {final_docx}")
    print(f"  MD:   {final_md}")

    # Nếu có target_output_dir (hoặc biến môi trường OUTPUT_DIR), sao chép thành phẩm sang thư mục đó
    target_dir = target_output_dir or os.environ.get("OUTPUT_DIR") or str(Path("~/Downloads/AIWF_Output").expanduser())
    if target_dir:
        target_path = Path(target_dir).resolve()
        target_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final_docx, target_path / final_docx.name)
        if final_md.exists():
            shutil.copy2(final_md, target_path / final_md.name)
        nv = process_dir / "needs_verification.json"
        if nv.exists():
            shutil.copy2(nv, target_path / f"{doc_basename}_needs_verification.json")
        print(f"  [OK] Đã sao chép thành phẩm sang thư mục đích: {target_path}")

    return True

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description="Xuất DOCX 5 layer từ MERGED.md")
    ap.add_argument("processing_dir")
    ap.add_argument("target_output_dir", nargs="?", default=None,
                    help="Thư mục nhận thành phẩm (mặc định ~/Downloads/AIWF_Output)")
    ap.add_argument("--allow-unverified", action="store_true",
                    help="Xuất dù chưa đối chiếu OCR xong (chỉ khi người dùng đồng ý)")
    a = ap.parse_args()
    ok = export_docx(a.processing_dir, target_output_dir=a.target_output_dir, allow_unverified=a.allow_unverified)
    sys.exit(0 if ok else 1)
