#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_manager.py — Quản lý trạng thái dự án (project.json).
Single Source of Truth (SSOT) giữa Antigravity, Temporary UI và Final Renderer.
Quản lý snapshots, revision history, Undo/Redo an toàn và thao tác sửa phụ đề.
"""

import argparse
import datetime
import json
import os
import shutil
import sys


DEFAULT_STYLE = {
    "preset": "modern_bottom",
    "font_family": "Be Vietnam Pro",
    "font_size": 24,
    "primary_color": "#FFFFFF",
    "secondary_color": "#FFD700",
    "outline_color": "#000000",
    "outline_width": 2.2,
    "shadow_width": 1.0,
    "background_color": "#000000",
    "background_opacity": 0.35,
    "alignment": 2,  # 2: Bottom-Center (ASS convention)
    "margin_v": 45,
    "margin_l": 40,
    "margin_r": 40,
    "line_spacing": 6,
    "border_radius": 8,
    "box_padding": 16,
    "bilingual_order": "target_top",  # target_top | source_top
    "mode": "bilingual",  # monolingual | bilingual
}

DEFAULT_RENDER = {
    "burn_in": True,
    "video_codec": "libx264",
    "crf": 20,
    "preset": "fast",
    "audio_copy": True,
}


def create_project(video_meta, segments, source_lang="auto", target_lang="vi", mode="bilingual", project_dir=None):
    """
    Khởi tạo project dict và cấu trúc thư mục lưu trữ.
    """
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    project_id = f"sub_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    style = dict(DEFAULT_STYLE)
    style["mode"] = mode

    project = {
        "version": "1.0",
        "project_id": project_id,
        "created_at": now_str,
        "updated_at": now_str,
        "video": video_meta,
        "languages": {
            "source_lang": source_lang,
            "target_lang": target_lang,
            "mode": mode,
        },
        "style": style,
        "render_settings": dict(DEFAULT_RENDER),
        "segments": segments,
        "history": {
            "current_revision": 1,
            "snapshots": [
                {
                    "revision": 1,
                    "timestamp": now_str,
                    "description": "Khởi tạo dự án và bóc tách ban đầu",
                }
            ],
        },
    }

    if project_dir:
        os.makedirs(project_dir, exist_ok=True)
        proj_file = os.path.join(project_dir, "project.json")
        snap_dir = os.path.join(project_dir, "snapshots")
        os.makedirs(snap_dir, exist_ok=True)

        # Lưu bản nháp ban đầu
        with open(proj_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)

        rev_1_file = os.path.join(snap_dir, "rev_001.json")
        with open(rev_1_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)

    return project


def save_project(project, proj_file, description="Cập nhật dự án", make_snapshot=True):
    """
    Lưu project.json và tự động tạo snapshot an toàn.
    """
    project_dir = os.path.dirname(os.path.abspath(proj_file))
    snap_dir = os.path.join(project_dir, "snapshots")
    os.makedirs(snap_dir, exist_ok=True)

    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    project["updated_at"] = now_str

    if make_snapshot:
        cur_rev = project.get("history", {}).get("current_revision", 1)
        next_rev = cur_rev + 1
        project.setdefault("history", {})["current_revision"] = next_rev
        snap_file = os.path.join(snap_dir, f"rev_{next_rev:03d}.json")

        with open(snap_file, "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)

        project["history"].setdefault("snapshots", []).append({
            "revision": next_rev,
            "timestamp": now_str,
            "description": description,
        })

    # Ghi file nguyên tử (atomic write)
    tmp_file = f"{proj_file}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, proj_file)

    return project


def load_project(proj_file):
    if not os.path.isfile(proj_file):
        raise FileNotFoundError(f"Không tìm thấy file project: {proj_file}")
    with open(proj_file, "r", encoding="utf-8") as f:
        return json.load(f)


def undo(proj_file):
    """Phục hồi snapshot liền trước."""
    project = load_project(proj_file)
    cur_rev = project.get("history", {}).get("current_revision", 1)
    if cur_rev <= 1:
        return False, "Đã ở bản sửa đổi đầu tiên, không thể Undo thêm."

    target_rev = cur_rev - 1
    project_dir = os.path.dirname(os.path.abspath(proj_file))
    snap_file = os.path.join(project_dir, "snapshots", f"rev_{target_rev:03d}.json")

    if not os.path.isfile(snap_file):
        return False, f"Không tìm thấy snapshot rev_{target_rev:03d}.json"

    with open(snap_file, "r", encoding="utf-8") as f:
        target_data = json.load(f)

    # Cập nhật lại segments và style từ snapshot cũ, nhưng giữ nguyên con trỏ revision
    project["segments"] = target_data.get("segments", [])
    project["style"] = target_data.get("style", project.get("style", {}))
    project["history"]["current_revision"] = target_rev
    project["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with open(proj_file, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)

    return True, f"Đã Undo về revision {target_rev}"


def redo(proj_file):
    """Tiến tới snapshot kế tiếp (nếu có)."""
    project = load_project(proj_file)
    cur_rev = project.get("history", {}).get("current_revision", 1)
    total_snaps = len(project.get("history", {}).get("snapshots", []))

    if cur_rev >= total_snaps:
        return False, "Đã ở bản sửa đổi mới nhất, không thể Redo."

    target_rev = cur_rev + 1
    project_dir = os.path.dirname(os.path.abspath(proj_file))
    snap_file = os.path.join(project_dir, "snapshots", f"rev_{target_rev:03d}.json")

    if not os.path.isfile(snap_file):
        return False, f"Không tìm thấy snapshot rev_{target_rev:03d}.json"

    with open(snap_file, "r", encoding="utf-8") as f:
        target_data = json.load(f)

    project["segments"] = target_data.get("segments", [])
    project["style"] = target_data.get("style", project.get("style", {}))
    project["history"]["current_revision"] = target_rev
    project["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with open(proj_file, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)

    return True, f"Đã Redo tới revision {target_rev}"


def split_segment(project, segment_id, split_time, text_split_idx=None):
    """
    Chia 1 segment thành 2 segments tại thời điểm split_time.
    """
    segments = project.get("segments", [])
    target_idx = None
    for idx, s in enumerate(segments):
        if s.get("id") == segment_id:
            target_idx = idx
            break

    if target_idx is None:
        raise ValueError(f"Không tìm thấy segment ID: {segment_id}")

    target_seg = segments[target_idx]
    orig_start = target_seg["start"]
    orig_end = target_seg["end"]

    if not (orig_start < split_time < orig_end):
        raise ValueError(f"Thời gian chia ({split_time}s) phải nằm giữa {orig_start}s và {orig_end}s.")

    src_text = target_seg.get("source_text", "")
    trans_text = target_seg.get("translated_text", "")

    # Cắt text
    if text_split_idx is not None and 0 < text_split_idx < len(src_text):
        src_1 = src_text[:text_split_idx].strip()
        src_2 = src_text[text_split_idx:].strip()
    else:
        words = src_text.split()
        half = max(1, len(words) // 2)
        src_1 = " ".join(words[:half])
        src_2 = " ".join(words[half:])

    t_words = trans_text.split()
    t_half = max(1, len(t_words) // 2)
    trans_1 = " ".join(t_words[:t_half])
    trans_2 = " ".join(t_words[t_half:])

    seg_1 = dict(target_seg)
    seg_1["end"] = round(split_time, 2)
    seg_1["source_text"] = src_1
    seg_1["translated_text"] = trans_1
    seg_1["duration"] = round(split_time - orig_start, 2)

    seg_2 = dict(target_seg)
    seg_2["id"] = f"{segment_id}_b"
    seg_2["start"] = round(split_time, 2)
    seg_2["end"] = orig_end
    seg_2["source_text"] = src_2
    seg_2["translated_text"] = trans_2
    seg_2["duration"] = round(orig_end - split_time, 2)

    # Thay thế và re-index
    segments.pop(target_idx)
    segments.insert(target_idx, seg_2)
    segments.insert(target_idx, seg_1)

    for i, s in enumerate(segments, 1):
        s["id"] = f"seg_{i:03d}"

    project["segments"] = segments
    return project


def merge_segment(project, segment_id):
    """
    Gộp segment được chỉ định với segment liền sau nó.
    """
    segments = project.get("segments", [])
    target_idx = None
    for idx, s in enumerate(segments):
        if s.get("id") == segment_id:
            target_idx = idx
            break

    if target_idx is None:
        raise ValueError(f"Không tìm thấy segment ID: {segment_id}")

    if target_idx >= len(segments) - 1:
        raise ValueError("Đây là segment cuối cùng, không thể gộp với câu tiếp theo.")

    seg1 = segments[target_idx]
    seg2 = segments[target_idx + 1]

    merged_seg = {
        "id": seg1["id"],
        "start": seg1["start"],
        "end": seg2["end"],
        "source_text": f"{seg1.get('source_text', '')} {seg2.get('source_text', '')}".strip(),
        "translated_text": f"{seg1.get('translated_text', '')} {seg2.get('translated_text', '')}".strip(),
        "words": seg1.get("words", []) + seg2.get("words", []),
        "duration": round(seg2["end"] - seg1["start"], 2),
        "confidence": round((seg1.get("confidence", 1.0) + seg2.get("confidence", 1.0)) / 2, 2),
    }

    segments.pop(target_idx + 1)
    segments[target_idx] = merged_seg

    for i, s in enumerate(segments, 1):
        s["id"] = f"seg_{i:03d}"

    project["segments"] = segments
    return project


def main():
    parser = argparse.ArgumentParser(description="Quản trị project.json cho kỹ năng phu-de.")
    parser.add_argument("--project", "-p", required=True, help="Đường dẫn file project.json")
    parser.add_argument("--action", "-a", choices=["info", "undo", "redo", "save"], default="info")
    parser.add_argument("--desc", default="Manual update", help="Mô tả khi save snapshot")

    args = parser.parse_args()

    if args.action == "info":
        p = load_project(args.project)
        print(f"Project ID : {p.get('project_id')}")
        print(f"Video      : {p.get('video', {}).get('filename')} ({p.get('video', {}).get('duration')}s)")
        print(f"Segments   : {len(p.get('segments', []))} phân đoạn")
        print(f"Revision   : {p.get('history', {}).get('current_revision')}")
        print(f"Mode       : {p.get('style', {}).get('mode')}")
    elif args.action == "undo":
        ok, msg = undo(args.project)
        print(f"{'✅' if ok else '❌'} {msg}")
    elif args.action == "redo":
        ok, msg = redo(args.project)
        print(f"{'✅' if ok else '❌'} {msg}")


if __name__ == "__main__":
    sys.exit(main())
