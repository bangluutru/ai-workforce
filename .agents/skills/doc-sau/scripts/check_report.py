#!/usr/bin/env python3
"""
check_report.py — Cổng chất lượng cho báo cáo Đọc Sâu.

Kiểm tra:
  1. Đủ các mục bắt buộc theo Level (theo templates/bao_cao_doc_sau.md).
  2. Đủ số trích dẫn nguyên văn theo Level; mọi trích dẫn được KIỂM CHỨNG bằng
     scripts/harness/evidence_verifier.py (khớp 100% với file nguồn cục bộ, ≥ 30 ký tự; chữ Hán/kana tính 2).
  3. Bảng độ phủ: mọi chunk trong manifest.json có trạng thái; Level ≥ 2 phải "Đã đọc" 100%.
  4. Kích hoạt tri thức: đúng 3 bài học, đúng 1 Quick Win 24h; Level 3 dùng ≥ 3 mô hình từ ≥ 2 tập.

Cú pháp trích dẫn trong báo cáo (để trích xuất tự động):
  > "nguyên văn từ tài liệu, tối thiểu 30 ký tự" (vị trí: tr.12)
  > "nguyên văn từ nguồn đối chiếu" (nguồn: ten_file_trong_sources.txt, vị trí: ...)
  Mọi đoạn trong ngoặc kép “...” hoặc "..." dài ≥ 30 ký tự ở bất kỳ đâu cũng bị kiểm chứng.

Usage:
  python3 check_report.py --report <báo_cáo.md> --process-dir <process_dir> --level 2
Exit: 0 = đạt; 1 = chưa đạt (xem danh sách); 2 = lỗi chạy (thiếu source.txt / verifier).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
VERIFIER = ROOT / "scripts" / "harness" / "evidence_verifier.py"

SECTIONS = {  # mục -> level tối thiểu
    "0. Thông tin tài liệu & độ phủ đọc": 1,
    "1. Luận điểm cốt lõi & cấu trúc lập luận": 1,
    "2. SCQA": 1,
    "3. Kiểm tra 5W2H & khoảng trống thông tin": 1,
    "4. Khung định hình & ẩn ý": 1,
    "5. Phản biện lập luận": 2,
    "6. Tư duy đảo ngược & tiền khám nghiệm": 2,
    "7. Mạng lưới mô hình tư duy": 3,
    "8. Nguyên lý đệ nhất, tư duy hệ thống & sáu chiếc nón": 3,
    "9. Ma trận đối chiếu đa nguồn": 4,
    "10. Kích hoạt tri thức": 1,
    "11. Giới hạn phạm vi & cờ xác minh": 1,
}
MIN_QUOTES = {1: 3, 2: 6, 3: 10, 4: 14}
QUOTE_RE = re.compile(r"[\"“]([^\"“”\n]{8,}?)[\"”]")


def weight_len(s: str) -> int:
    s = re.sub(r"[\s\W_]+", "", unicodedata.normalize("NFKC", s))
    return sum(2 if re.match(r"[\u3040-\u30ff\u3400-\u9fff]", c) else 1 for c in s)


def section_text(md: str, title: str) -> str:
    m = re.search(r"^##\s+" + re.escape(title) + r".*?$(.*?)(?=^##\s+\d+\.|\Z)", md, re.M | re.S)
    return m.group(1) if m else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Cổng chất lượng báo cáo Đọc Sâu")
    ap.add_argument("--report", required=True)
    ap.add_argument("--process-dir", required=True)
    ap.add_argument("--level", type=int, choices=[1, 2, 3, 4], required=True)
    a = ap.parse_args()
    rep, pdir = Path(a.report), Path(a.process_dir)
    src = pdir / "source.txt"
    if not rep.is_file() or not src.is_file():
        print(f"[FAIL] Thiếu báo cáo hoặc {src} (chạy ingest.py trước).")
        return 2
    if not VERIFIER.is_file():
        print(f"[FAIL] Không thấy {VERIFIER}")
        return 2
    md = rep.read_text(encoding="utf-8")
    problems, notes = [], []

    # 1) Mục bắt buộc
    for title, lv in SECTIONS.items():
        if lv <= a.level and not re.search(r"^##\s+" + re.escape(title), md, re.M):
            problems.append(f"Thiếu mục '## {title}' (bắt buộc từ Level {lv})")
        elif lv <= a.level and len(section_text(md, title).strip()) < 80:
            problems.append(f"Mục '{title}' gần như trống")

    # 2) Độ phủ
    manifest = json.loads((pdir / "manifest.json").read_text(encoding="utf-8")) if (pdir / "manifest.json").exists() else None
    cov = section_text(md, "0. Thông tin tài liệu & độ phủ đọc")
    if manifest:
        n = len(manifest["chunks"])
        rows = [r for r in cov.splitlines() if re.match(r"^\|\s*\d+\s*\|", r)]
        read = [r for r in rows if "đã đọc" in r.lower()]
        if len(rows) < n:
            problems.append(f"Bảng độ phủ có {len(rows)}/{n} chunk")
        if a.level >= 2 and len(read) < n:
            problems.append(f"Level {a.level} yêu cầu đọc 100% chunk: mới 'Đã đọc' {len(read)}/{n}")
        elif len(read) < n and "giới hạn" not in section_text(md, "11. Giới hạn phạm vi & cờ xác minh").lower():
            problems.append("Chưa đọc hết chunk nhưng mục 11 không nêu giới hạn phạm vi")
        notes.append(f"Độ phủ: {len(read)}/{n} chunk")

    # 3) Kích hoạt tri thức
    act = section_text(md, "10. Kích hoạt tri thức")
    lessons = re.findall(r"^\s*(?:###\s*)?(?:Bài học|Lesson)\s*\d", act, re.M | re.I)
    if len(lessons) != 3:
        problems.append(f"Mục 10 cần đúng 3 bài học ('Bài học 1..3'), đang có {len(lessons)}")
    qw = re.findall(r"quick win", act, re.I)
    if len(qw) < 1:
        problems.append("Mục 10 thiếu 'Quick Win 24h'")
    if a.level >= 3:
        mm = section_text(md, "7. Mạng lưới mô hình tư duy")
        models = re.findall(r"^###\s+", mm, re.M)
        vols = set(re.findall(r"Vol\s*([1-4])", mm))
        if len(models) < 3 or len(vols) < 2:
            problems.append(f"Mục 7 cần ≥ 3 mô hình (### mỗi mô hình) từ ≥ 2 tập: có {len(models)} mô hình, tập {sorted(vols)}")

    # 4) Trích dẫn + kiểm chứng
    quotes = []
    for line in md.splitlines():
        for m in QUOTE_RE.finditer(line):
            q = m.group(1).strip()
            sm = re.search(r"nguồn:\s*([\w.\-]+\.(?:txt|md))", line)
            source = str(pdir / "sources" / sm.group(1)) if sm else str(src)
            quotes.append({"q": q, "source": source, "line": line.strip()[:120]})
    short = [x for x in quotes if weight_len(x["q"]) < 30]
    for x in short:
        problems.append(f"Trích dẫn quá ngắn để kiểm chứng (< 30 ký tự): \"{x['q']}\" -> mở rộng nguyên văn hoặc bỏ ngoặc kép (diễn giải)")
    verifiable = [x for x in quotes if weight_len(x["q"]) >= 30]
    if len(verifiable) < MIN_QUOTES[a.level]:
        problems.append(f"Level {a.level} cần ≥ {MIN_QUOTES[a.level]} trích dẫn nguyên văn, có {len(verifiable)}")
    claims = [{"claim": f"doc-sau quote {i + 1}", "verbatim_quote": x["q"], "source": x["source"]}
              for i, x in enumerate(verifiable)]
    claims_path = pdir / "claims.json"
    claims_path.write_text(json.dumps(claims, ensure_ascii=False, indent=2), encoding="utf-8")
    if claims:
        res = subprocess.run([sys.executable, str(VERIFIER), "--claims", str(claims_path)], capture_output=True, text=True)
        try:
            out = json.loads(res.stdout)
        except json.JSONDecodeError:
            print(f"[FAIL] evidence_verifier không trả JSON: {res.stdout[:300]} {res.stderr[:300]}")
            return 2
        (pdir / "evidence_result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        bad = [d for d in out.get("details", []) if d.get("status") != "VERIFIED"]
        for d in bad:
            problems.append(f"Trích dẫn KHÔNG khớp nguồn ({d.get('status')}: {d.get('reason', '')}): \"{d.get('quote', '')[:90]}\"")
        notes.append(f"Trích dẫn đã kiểm chứng: {out.get('verified_count', 0)}/{out.get('total_claims', 0)}")
        if a.level == 4:
            ext = {Path(x["source"]).name for x in verifiable if Path(x["source"]).parent.name == "sources"}
            if len(ext) < 2:
                problems.append(f"Level 4 cần trích dẫn từ ≥ 2 nguồn đối chiếu trong sources/, có {len(ext)}")

    print(f"=== KIỂM TRA BÁO CÁO ĐỌC SÂU (Level {a.level}): {rep.name} ===")
    for n_ in notes:
        print(f"  ℹ️  {n_}")
    if problems:
        print(f"❌ {len(problems)} vấn đề:")
        for p in problems:
            print(f"  • {p}")
        return 1
    print("✅ ĐẠT: đủ mục, đủ độ phủ, mọi trích dẫn khớp nguyên văn nguồn.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"[CRASH] check_report.py: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(2)
