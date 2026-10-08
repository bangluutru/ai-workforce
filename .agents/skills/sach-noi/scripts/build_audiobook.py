#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_audiobook.py — Điều phối toàn bộ quy trình tạo sách nói M4B & MP3 (Luật R7).

Quy trình tự động:
  1. Phân tích tài liệu nguồn (hoặc thư mục chương) thành các chương/mục độc lập.
  2. Chuẩn hóa phát thanh tiếng Việt qua `spoken_normalizer.py`.
  3. Sinh giọng đọc AI offline qua `_shared/media/tts.py` (VieNeu-TTS / Kokoro).
  4. Đóng gói file .m4b kèm mục lục chương, ảnh bìa và thư mục MP3 ID3 tags qua `audiobook_packager.py`.
  5. Thực hiện thẩm định kép (Technical & User Experience) và xuất `audit_report.json`.

CLI:
  python3 build_audiobook.py --input book.md --title "Tên Sách" --author "Tác Giả" [--voice "Thái Sơn"] [--output-dir ~/Downloads/AIWF_Output]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Thêm _shared vào sys.path theo chuẩn R7
_HERE = Path(__file__).resolve().parent
_SKILL_DIR = _HERE.parent
_SHARED = _SKILL_DIR.parent / "_shared"
sys.path.insert(0, str(_SHARED))
import bootstrap  # noqa: F401,E402

from audiobook_packager import check_ffmpeg_installed, package_m4b_audiobook
from spoken_normalizer import normalize_spoken_vietnamese
from tts import default_voice, get_voice_catalog, synthesize_line


def extract_chapters_from_markdown(text: str) -> List[Dict[str, str]]:
    """
    Tự động phân tách các chương từ văn bản Markdown dựa trên tiêu đề #, ## hoặc 'Chương N'.
    """
    lines = text.split("\n")
    chapters: List[Dict[str, str]] = []
    current_title = "Mở đầu"
    current_lines: List[str] = []

    heading_re = re.compile(r"^(?:#{1,3}\s+|Chương\s+\d+[\.:\s]+)(.+)$", re.IGNORECASE)

    for line in lines:
        m = heading_re.match(line.strip())
        if m:
            if current_lines:
                ch_content = "\n".join(current_lines).strip()
                if ch_content:
                    chapters.append({"title": current_title, "content": ch_content})
                current_lines = []
            current_title = line.strip().lstrip("#").strip()
        else:
            current_lines.append(line)

    if current_lines:
        ch_content = "\n".join(current_lines).strip()
        if ch_content:
            chapters.append({"title": current_title, "content": ch_content})

    # Nếu không tìm thấy heading nào, coi toàn bộ là 1 chương
    if not chapters and text.strip():
        chapters.append({"title": "Toàn bộ nội dung", "content": text.strip()})

    return chapters


def build_audiobook_pipeline(
    input_file: Optional[str | Path] = None,
    text_content: Optional[str] = None,
    chapters_dir: Optional[str | Path] = None,
    book_title: str = "Sách Nói AI",
    author: str = "Tác Giả",
    voice: Optional[str] = None,
    lang: str = "vi",
    gender: str = "male",
    cover_path: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
    process_dir: Optional[str | Path] = None,
    export_mp3: bool = True,
    bitrate: str = "64k",
) -> Dict[str, Any]:
    """
    Thực thi trọn gói pipeline tạo sách nói và trả về báo cáo nghiệm thu 2 góc nhìn.
    """
    # 1. Khởi tạo đường dẫn
    home_downloads = Path.home() / "Downloads" / "AIWF_Output"
    base_out = Path(output_dir) if output_dir else home_downloads
    safe_title = re.sub(r'[\\/*?:"<>|]', "", book_title).strip() or "audiobook"
    book_out_dir = base_out / safe_title
    book_out_dir.mkdir(parents=True, exist_ok=True)

    proc_dir = Path(process_dir) if process_dir else (book_out_dir / ".process")
    proc_dir.mkdir(parents=True, exist_ok=True)

    # 2. Thu nạp nội dung các chương
    raw_chapters: List[Dict[str, str]] = []
    if chapters_dir and Path(chapters_dir).exists():
        for f in sorted(Path(chapters_dir).glob("*.txt")):
            t = f.stem
            c = f.read_text(encoding="utf-8")
            raw_chapters.append({"title": t, "content": c})
    elif input_file and Path(input_file).exists():
        content = Path(input_file).read_text(encoding="utf-8")
        raw_chapters = extract_chapters_from_markdown(content)
    elif text_content:
        raw_chapters = extract_chapters_from_markdown(text_content)
    else:
        raise ValueError("Phải cung cấp input_file, chapters_dir hoặc text_content.")

    if not raw_chapters:
        raise ValueError("Không tìm thấy nội dung chương nào để sản xuất sách nói.")

    # 3. Chuẩn hóa phát thanh tiếng Việt từng chương
    spoken_chapters_dir = proc_dir / "spoken"
    spoken_chapters_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = proc_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    selected_voice = voice or default_voice(lang, gender)
    rendered_chapters: List[Dict[str, Any]] = []

    for idx, ch in enumerate(raw_chapters, start=1):
        ch_title = ch.get("title", f"Chương {idx}")
        normalized_text = normalize_spoken_vietnamese(ch.get("content", ""))
        
        spoken_file = spoken_chapters_dir / f"chapter_{idx:02d}.txt"
        spoken_file.write_text(normalized_text, encoding="utf-8")

        wav_file = audio_dir / f"chapter_{idx:02d}.wav"
        
        # Nếu đã có file âm thanh sẵn (resume checkpoint) thì bỏ qua
        if not wav_file.exists() or wav_file.stat().st_size == 0:
            synth_res = synthesize_line(
                text=normalized_text,
                output_path=wav_file,
                lang=lang,
                gender=gender,
                voice=selected_voice,
                speed=1.0
            )
            if not synth_res.get("success"):
                raise RuntimeError(f"Lỗi tạo giọng đọc cho chương {idx} ('{ch_title}'): {synth_res.get('error')}")

        rendered_chapters.append({
            "number": idx,
            "title": ch_title,
            "audio_path": str(wav_file)
        })

    # 4. Đóng gói M4B và xuất MP3
    out_m4b = book_out_dir / f"{safe_title}.m4b"
    mp3_target_dir = (book_out_dir / "MP3") if export_mp3 else None

    pack_report = package_m4b_audiobook(
        chapters=rendered_chapters,
        output_m4b=out_m4b,
        book_title=book_title,
        author=author,
        cover_path=cover_path,
        bitrate=bitrate,
        chapter_gap_sec=2.0,
        narrator=selected_voice,
        mp3_dir=mp3_target_dir
    )

    # 5. GIAO THỨC KIỂM ĐỊNH KÉP (DUAL-PERSPECTIVE AUDIT)
    tech_checks = {
        "m4b_file_exists": out_m4b.exists(),
        "m4b_file_size_bytes": out_m4b.stat().st_size if out_m4b.exists() else 0,
        "total_duration_sec": pack_report.get("total_duration_sec", 0.0),
        "chapter_count": pack_report.get("chapter_count", 0),
        "aac_bitrate": bitrate,
        "has_cover_art": bool(cover_path and Path(cover_path).exists()),
        "mp3_files_count": len(pack_report.get("mp3_files", []))
    }

    user_checks = {
        "output_directory": str(book_out_dir),
        "clean_delivery_no_repo_bloat": not str(book_out_dir).startswith(str(Path.cwd() / ".agents")),
        "voice_used": selected_voice,
        "natural_pacing_2s_chapter_gap": True,
        "mobile_app_compatibility": ["Apple Books", "BookPlayer", "CarPlay", "Android Auto"],
        "spoken_normalization_applied": True
    }

    audit_summary = {
        "status": "PASS" if tech_checks["m4b_file_exists"] and tech_checks["chapter_count"] > 0 else "FAIL",
        "book_title": book_title,
        "author": author,
        "technical_perspective": tech_checks,
        "user_experience_perspective": user_checks,
        "chapters": pack_report.get("chapters", [])
    }

    audit_file = book_out_dir / "audit_report.json"
    audit_file.write_text(json.dumps(audit_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return audit_summary


def main():
    parser = argparse.ArgumentParser(description="Điều phối sản xuất sách nói hoàn chỉnh M4B & MP3 (Luật R7).")
    parser.add_argument("--input", "-i", type=str, help="File tài liệu nguồn (.md, .txt, .docx)")
    parser.add_argument("--chapters-dir", type=str, help="Thư mục chứa các file text từng chương")
    parser.add_argument("--title", "-t", type=str, default="Sách Nói AI", help="Tên sách")
    parser.add_argument("--author", "-a", type=str, default="AI Workforce", help="Tên tác giả")
    parser.add_argument("--voice", "-v", type=str, help="Tên giọng đọc (vd: Thái Sơn, Trúc Ly, af_heart)")
    parser.add_argument("--cover", "-c", type=str, help="Đường dẫn file ảnh bìa (JPEG/PNG)")
    parser.add_argument("--output-dir", "-o", type=str, help="Thư mục xuất thành phẩm (mặc định ~/Downloads/AIWF_Output)")
    parser.add_argument("--bitrate", "-b", type=str, default="64k", help="Bitrate AAC (mặc định 64k)")
    parser.add_argument("--no-mp3", action="store_true", help="Không xuất thư mục MP3 phụ")

    args = parser.parse_args()

    if not args.input and not args.chapters_dir:
        parser.print_help()
        sys.exit(1)

    try:
        res = build_audiobook_pipeline(
            input_file=args.input,
            chapters_dir=args.chapters_dir,
            book_title=args.title,
            author=args.author,
            voice=args.voice,
            cover_path=args.cover,
            output_dir=args.output_dir,
            export_mp3=not args.no_mp3,
            bitrate=args.bitrate
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        print("\n🎉 Hoàn thành sản xuất sách nói chuẩn studio!")
    except Exception as e:
        print(f"❌ Thất bại: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
