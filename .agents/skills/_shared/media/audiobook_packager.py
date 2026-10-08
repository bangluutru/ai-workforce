#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audiobook_packager.py — Đóng gói sách nói M4B & MP3 tags chuẩn quốc tế (Luật R7).

Mục tiêu:
  Nhận danh sách các file audio từng chương/tiểu mục, tự động ghép nối âm thanh,
  chèn quãng nghỉ tự nhiên, nhúng ảnh bìa và tạo bảng phân chương (chapter markers)
  chuẩn FFMETADATA1.

Đầu ra tương thích 100%:
  • File .m4b (AAC mono 64k/96k, faststart) cho Apple Books, BookPlayer (hỗ trợ CarPlay/Android Auto),
    Audiobookshelf, Smart AudioBook Player.
  • Thư mục MP3 được đánh số và gắn đầy đủ thẻ ID3v2 (Title, Artist, Album, Track/Total, Attached Picture).

API:
  package_m4b_audiobook(chapters, output_m4b, book_title, author, ...)
  package_mp3_chapters(chapters, output_dir, book_title, author, ...)

CLI:
  python3 audiobook_packager.py --manifest chapters.json --output book.m4b --title "Tên Sách" --author "Tác Giả" [--cover cover.jpg] [--mp3-dir ./mp3s]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Nạp ffmpeg_tools từ cùng thư mục
try:
    from ffmpeg_tools import duration, ffmpeg_bin, ffprobe_bin
except ImportError:
    # Nếu chạy độc lập, thêm thư mục hiện tại vào sys.path
    _HERE = Path(__file__).resolve().parent
    if str(_HERE) not in sys.path:
        sys.path.insert(0, str(_HERE))
    from ffmpeg_tools import duration, ffmpeg_bin, ffprobe_bin


@dataclass
class ChapterItem:
    number: int
    title: str
    audio_path: Path
    duration_sec: float = 0.0


def check_ffmpeg_installed() -> bool:
    """Kiểm tra xem ffmpeg có sẵn trên hệ thống không."""
    ff = ffmpeg_bin()
    if os.path.isabs(ff) and os.path.isfile(ff) and os.access(ff, os.X_OK):
        return True
    return shutil.which(ff) is not None



def _esc_ffmeta(text: str) -> str:
    """Thoát các ký tự đặc biệt trong format FFMETADATA1 (=, ;, #, \\, newline)."""
    if not text:
        return ""
    s = str(text)
    s = s.replace("\\", "\\\\")
    s = s.replace("=", "\\=")
    s = s.replace(";", "\\;")
    s = s.replace("#", "\\#")
    s = s.replace("\n", " ")
    return s.strip()


def _safe_filename(name: str) -> str:
    """Tạo tên file an toàn trên mọi hệ điều hành."""
    s = re.sub(r'[\\/*?:"<>|]', "", name)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:80] or "untitled"


def create_silence_wav(output_path: Path, duration_sec: float, sample_rate: int = 44100) -> Path:
    """Tạo file WAV im lặng dùng làm khoảng nghỉ giữa các chương/tiểu mục."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_bin(),
        "-y",
        "-v", "error",
        "-f", "lavfi",
        "-i", f"anullsrc=r={sample_rate}:cl=mono",
        "-t", f"{duration_sec:.3f}",
        "-c:a", "pcm_s16le",
        str(output_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Lỗi tạo khoảng lặng ffmpeg: {res.stderr}")
    return output_path


def package_mp3_chapters(
    chapters: List[ChapterItem],
    output_dir: str | Path,
    book_title: str,
    author: str,
    cover_path: Optional[str | Path] = None,
    bitrate: str = "128k",
    sample_rate: int = 44100,
    narrator: Optional[str] = None,
) -> List[Path]:
    """
    Xuất danh sách MP3 từng chương gắn thẻ ID3v2 đầy đủ.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    ff = ffmpeg_bin()
    written_files: List[Path] = []
    total = len(chapters)

    cover = Path(cover_path) if cover_path and Path(cover_path).exists() else None
    artist_tag = narrator or author or "AI Workforce"

    for chapter in chapters:
        safe_title = _safe_filename(chapter.title)
        filename = f"{chapter.number:02d} - {safe_title}.mp3"
        target_file = out_path / filename

        cmd = [
            ff, "-y", "-v", "error",
            "-i", str(chapter.audio_path)
        ]

        maps = ["-map", "0:a"]
        if cover:
            cmd.extend(["-i", str(cover)])
            maps.extend(["-map", "1:v", "-c:v", "mjpeg", "-disposition:v", "attached_pic"])

        cmd.extend(maps)
        cmd.extend([
            "-c:a", "libmp3lame",
            "-b:a", bitrate,
            "-ar", str(sample_rate),
            "-ac", "1",
            "-metadata", f"title={chapter.title}",
            "-metadata", f"album={book_title}",
            "-metadata", f"artist={artist_tag}",
            "-metadata", f"album_artist={author}",
            "-metadata", "genre=Audiobook",
            "-metadata", f"track={chapter.number}/{total}",
            str(target_file)
        ])

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg lỗi khi tạo MP3 chương '{chapter.title}': {res.stderr}")
        written_files.append(target_file)

    return written_files


def package_m4b_audiobook(
    chapters: List[Dict[str, Any]],
    output_m4b: str | Path,
    book_title: str,
    author: str,
    cover_path: Optional[str | Path] = None,
    bitrate: str = "64k",
    sample_rate: int = 44100,
    chapter_gap_sec: float = 2.0,
    narrator: Optional[str] = None,
    mp3_dir: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """
    Đóng gói sách nói M4B có mục lục chương và ảnh bìa.

    Args:
        chapters: Danh sách dict [{'title': str, 'audio_path': str|Path}, ...]
        output_m4b: Đường dẫn file xuất .m4b
        book_title: Tên cuốn sách
        author: Tên tác giả
        cover_path: Đường dẫn ảnh bìa (JPEG/PNG)
        bitrate: Bitrate AAC (mặc định '64k' mono chuẩn sách nói)
        sample_rate: Tần số lấy mẫu (44100 Hz)
        chapter_gap_sec: Khoảng lặng chèn giữa 2 chương (mặc định 2.0s)
        narrator: Tên người đọc / giọng AI
        mp3_dir: Nếu cung cấp, xuất thêm thư mục MP3 có ID3 tags

    Returns:
        Dict thông tin nghiệm thu sách nói: {
            'm4b_path': str,
            'total_duration_sec': float,
            'chapter_count': int,
            'mp3_files': List[str],
            'chapters': List[dict]
        }
    """
    if not chapters:
        raise ValueError("Danh sách chương sách nói (chapters) không được rỗng.")

    if not check_ffmpeg_installed():
        raise RuntimeError(
            "Không tìm thấy ffmpeg trên hệ thống (cần để xử lý và đóng gói âm thanh AAC/M4B/MP3).\n"
            "Vui lòng cài đặt:\n"
            "  • macOS: brew install ffmpeg\n"
            "  • Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  • Windows: winget install Gyan.FFmpeg"
        )

    out_file = Path(output_m4b)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    cover = Path(cover_path) if cover_path and Path(cover_path).exists() else None
    ff = ffmpeg_bin()

    # 1. Đo đạc chính xác thời lượng từng chương
    parsed_chapters: List[ChapterItem] = []
    for idx, c in enumerate(chapters, start=1):
        c_title = c.get("title", f"Chương {idx}")
        c_path = Path(c.get("audio_path", ""))
        if not c_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file âm thanh cho chương {idx}: {c_path}")
        
        dur = float(c.get("duration_sec", 0.0))
        if dur <= 0:
            dur = duration(str(c_path))
        
        parsed_chapters.append(ChapterItem(
            number=idx,
            title=c_title,
            audio_path=c_path,
            duration_sec=dur
        ))

    # 2. Tạo không gian làm việc tạm
    with tempfile.TemporaryDirectory(prefix="aiwf_audiobook_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Tạo file khoảng lặng nếu có gap > 0
        silence_file = None
        if chapter_gap_sec > 0:
            silence_file = tmp_path / "silence.wav"
            create_silence_wav(silence_file, chapter_gap_sec, sample_rate=sample_rate)

        # Tạo file concat list và bảng metadata phân chương
        concat_lines: List[str] = []
        meta_lines: List[str] = [
            ";FFMETADATA1",
            f"title={_esc_ffmeta(book_title)}",
            f"artist={_esc_ffmeta(author)}",
            f"album={_esc_ffmeta(book_title)}",
            f"album_artist={_esc_ffmeta(author)}",
            f"genre=Audiobook",
            f"comment=Created by AI Workforce Audiobook Engine",
        ]
        if narrator:
            meta_lines.append(f"composer={_esc_ffmeta(narrator)}")

        cursor_ms = 0
        chapter_timings = []

        for i, ch in enumerate(parsed_chapters):
            start_ms = cursor_ms
            duration_ms = int(ch.duration_sec * 1000)
            end_ms = start_ms + duration_ms

            meta_lines.extend([
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={start_ms}",
                f"END={end_ms}",
                f"title={_esc_ffmeta(ch.title)}"
            ])

            chapter_timings.append({
                "number": ch.number,
                "title": ch.title,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_sec": ch.duration_sec
            })

            # Dòng file cho concat demuxer
            concat_lines.append(f"file '{ch.audio_path.resolve().as_posix()}'")

            cursor_ms = end_ms
            # Chèn khoảng lặng giữa các chương (trừ chương cuối cùng)
            if silence_file and i < len(parsed_chapters) - 1:
                concat_lines.append(f"file '{silence_file.resolve().as_posix()}'")
                cursor_ms += int(chapter_gap_sec * 1000)

        concat_list_file = tmp_path / "concat.txt"
        concat_list_file.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

        metadata_file = tmp_path / "ffmetadata.txt"
        metadata_file.write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

        # 3. Chạy ffmpeg ghép và đóng gói container M4B
        cmd = [
            ff, "-y", "-v", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_list_file),
            "-i", str(metadata_file)
        ]

        maps = ["-map", "0:a"]
        if cover:
            cmd.extend(["-i", str(cover)])
            # Input 0: audio, Input 1: metadata, Input 2: cover
            maps.extend(["-map", "2:v", "-c:v", "mjpeg", "-disposition:v", "attached_pic"])

        cmd.extend(maps)
        cmd.extend([
            "-map_metadata", "1",
            "-map_chapters", "1",
            "-c:a", "aac",
            "-b:a", bitrate,
            "-ar", str(sample_rate),
            "-ac", "1",
            "-movflags", "+faststart",
            "-f", "mp4",
            str(out_file)
        ])

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg lỗi khi đóng gói M4B: {res.stderr}")

    # 4. Xuất thư mục MP3 nếu được yêu cầu
    written_mp3s: List[str] = []
    if mp3_dir:
        mp3_paths = package_mp3_chapters(
            parsed_chapters,
            output_dir=mp3_dir,
            book_title=book_title,
            author=author,
            cover_path=cover_path,
            narrator=narrator,
            sample_rate=sample_rate
        )
        written_mp3s = [str(p) for p in mp3_paths]

    total_sec = cursor_ms / 1000.0

    return {
        "m4b_path": str(out_file),
        "total_duration_sec": total_sec,
        "chapter_count": len(parsed_chapters),
        "mp3_files": written_mp3s,
        "chapters": chapter_timings
    }


def main():
    parser = argparse.ArgumentParser(description="Đóng gói sách nói M4B & MP3 tags (Luật R7).")
    parser.add_argument("--manifest", "-m", type=str, required=True, help="File JSON manifest mô tả các chương")
    parser.add_argument("--output", "-o", type=str, required=True, help="Đường dẫn file .m4b đầu ra")
    parser.add_argument("--title", "-t", type=str, required=True, help="Tên sách")
    parser.add_argument("--author", "-a", type=str, required=True, help="Tên tác giả")
    parser.add_argument("--narrator", type=str, default="AI Workforce", help="Tên người đọc / giọng AI")
    parser.add_argument("--cover", "-c", type=str, help="Đường dẫn ảnh bìa (JPEG/PNG)")
    parser.add_argument("--bitrate", "-b", type=str, default="64k", help="Bitrate AAC (mặc định 64k)")
    parser.add_argument("--gap", type=float, default=2.0, help="Khoảng lặng giữa các chương (giây)")
    parser.add_argument("--mp3-dir", type=str, help="Thư mục xuất các file MP3 từng chương")

    args = parser.parse_args()

    manifest_p = Path(args.manifest)
    if not manifest_p.exists():
        print(f"❌ Không tìm thấy manifest: {args.manifest}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(manifest_p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Lỗi đọc manifest JSON: {e}", file=sys.stderr)
        sys.exit(1)

    chapters = data if isinstance(data, list) else data.get("chapters", [])
    if not chapters:
        print("❌ Không có danh sách chương trong manifest.", file=sys.stderr)
        sys.exit(1)

    try:
        report = package_m4b_audiobook(
            chapters=chapters,
            output_m4b=args.output,
            book_title=args.title,
            author=args.author,
            cover_path=args.cover,
            bitrate=args.bitrate,
            chapter_gap_sec=args.gap,
            narrator=args.narrator,
            mp3_dir=args.mp3_dir
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"\n✅ Đã đóng gói thành công sách nói: {args.output}")
    except Exception as e:
        print(f"❌ Thất bại: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
