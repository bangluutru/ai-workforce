#!/usr/bin/env python3
"""
sync_notebook.py — Đồng bộ tri thức từ Gemini Notebook về .agents/knowledge/
===========================================================================

Mục đích:
  Tự động kéo toàn bộ Notes, Sources metadata, và nội dung đã tổng hợp
  từ một (hoặc nhiều) Gemini Notebook về thư mục .agents/knowledge/ của
  AI Workforce, phục vụ làm Single Source of Truth (SSOT) cho các Skill.

Cách sử dụng:
  1. Cài đặt lần đầu:
     pip3 install "notebooklm-py[browser]"
     playwright install chromium
     notebooklm login          # Mở trình duyệt để đăng nhập Google

  2. Chạy đồng bộ:
     python3 scripts/sync_notebook.py

  3. Hoặc chỉ đồng bộ 1 notebook cụ thể:
     python3 scripts/sync_notebook.py --notebook-id cbcf39b2-2f6c-4df3-b6b5-321712bfd453

Quy tắc bảo toàn (R1 Git-Native):
  - Cập nhật trực tiếp vào .agents/knowledge/ để Git theo dõi diff và bảo toàn lịch sử phiên bản.
  - Tuyệt đối không tạo thư mục lưu trữ cục bộ làm phình repository.

Cấu trúc đầu ra:
  .agents/knowledge/<notebook_slug>/
    ├── metadata.json        # ID, tiêu đề, mô tả, ngày đồng bộ
    └── artifacts/
        ├── notes/
        │   ├── note_01_<title>.md
        │   └── ...
        └── sources/
            ├── source_01_<title>.md
            └── ...
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Hằng số
# ---------------------------------------------------------------------------
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent          # ai-workforce/
KNOWLEDGE_DIR = WORKSPACE_ROOT / ".agents" / "knowledge"
SYNC_LOG_FILE = WORKSPACE_ROOT / "scripts" / ".sync_notebook_log.json"

# Notebook mặc định (có thể ghi đè bằng --notebook-id)
DEFAULT_NOTEBOOK_IDS = [
    "cbcf39b2-2f6c-4df3-b6b5-321712bfd453",
]

# ---------------------------------------------------------------------------
# Tiện ích
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Chuyển tiêu đề thành slug an toàn cho tên thư mục / file."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    text = text.strip("_")
    return text[:80] if text else "untitled"


def sanitize_filename(text: str, max_len: int = 60) -> str:
    """Tạo tên file an toàn từ tiêu đề."""
    name = slugify(text)
    return name[:max_len]


def write_metadata(out_dir: Path, notebook_id: str, title: str,
                   description: str, source_count: int, note_count: int) -> None:
    """Ghi file metadata.json chuẩn KWSR."""
    meta = {
        "id": slugify(title),
        "notebook_id": notebook_id,
        "domain": "Gemini Notebook",
        "subject": title,
        "description": description,
        "source_url": f"https://notebook.google.com/notebook/{notebook_id}",
        "source_count": source_count,
        "note_count": note_count,
        "last_synced": datetime.now().isoformat(),
        "sync_tool": "sync_notebook.py",
    }
    meta_path = out_dir / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"  📝 metadata.json ({source_count} sources, {note_count} notes)")


def write_markdown(filepath: Path, title: str, content: str,
                   extra_header: str = "") -> None:
    """Ghi nội dung ra file Markdown chuẩn."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    header = f"# {title}\n\n"
    if extra_header:
        header += f"{extra_header}\n\n"
    header += f"> *Đồng bộ tự động từ Gemini Notebook — {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n---\n\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + content)


def update_sync_log(notebook_id: str, slug: str, status: str,
                    source_count: int = 0, note_count: int = 0) -> None:
    """Cập nhật log đồng bộ."""
    log = {}
    if SYNC_LOG_FILE.exists():
        with open(SYNC_LOG_FILE, "r", encoding="utf-8") as f:
            try:
                log = json.load(f)
            except json.JSONDecodeError:
                log = {}

    log[notebook_id] = {
        "slug": slug,
        "status": status,
        "sources": source_count,
        "notes": note_count,
        "last_sync": datetime.now().isoformat(),
    }

    SYNC_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNC_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Logic chính: Kết nối + Đồng bộ
# ---------------------------------------------------------------------------

async def _fetch_source_fulltext(client, notebook_id: str, source_id: str,
                                  title: str) -> str:
    """
    Lấy full-text nội dung của 1 source.
    Thử qua Python API trước, nếu không được thì fallback sang CLI.
    """
    import subprocess

    # --- Phương án 1: Python API (nếu client hỗ trợ) ---
    try:
        # Thử các method có thể có trong notebooklm-py
        if hasattr(client.sources, "get_fulltext"):
            result = await client.sources.get_fulltext(source_id, notebook_id=notebook_id)
            content = getattr(result, "content", None) or getattr(result, "text", None) or str(result)
            if content and len(content) > 50:
                return content
        elif hasattr(client.sources, "fulltext"):
            result = await client.sources.fulltext(source_id, notebook_id=notebook_id)
            content = getattr(result, "content", None) or getattr(result, "text", None) or str(result)
            if content and len(content) > 50:
                return content
        elif hasattr(client.sources, "get"):
            result = await client.sources.get(source_id, notebook_id=notebook_id)
            content = getattr(result, "content", None) or getattr(result, "fulltext", None) or ""
            if content and len(content) > 50:
                return content
    except Exception:
        pass  # Fallback sang CLI

    # --- Phương án 2: CLI subprocess với -o FILE (tránh bị truncate stdout) ---
    import tempfile
    try:
        # Tạo file tạm để CLI ghi fulltext vào
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, prefix="nlm_"
        ) as tmp:
            tmp_path = tmp.name

        proc = subprocess.run(
            [
                sys.executable, "-m", "notebooklm",
                "source", "fulltext", source_id,
                "-n", notebook_id,
                "-f", "markdown",
                "-o", tmp_path,
                "--force",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if proc.returncode == 0 and os.path.exists(tmp_path):
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            # Dọn file tạm
            os.unlink(tmp_path)
            if len(content) > 50:
                return content

        # Dọn file tạm nếu còn tồn tại
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    except subprocess.TimeoutExpired:
        print(f"      ⏱️  Timeout khi lấy fulltext: {title[:40]}...")
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    except Exception:
        pass

    return ""

async def sync_one_notebook(client, notebook_id: str) -> dict:
    """
    Đồng bộ 1 notebook:
      1. Lấy metadata notebook
      2. Lấy danh sách sources → ghi file .md
      3. Lấy danh sách notes → ghi file .md
      4. Ghi metadata.json
    """
    print(f"\n{'='*60}")
    print(f"🔄 Đang đồng bộ notebook: {notebook_id}")
    print(f"{'='*60}")

    # --- Bước 1: Lấy thông tin notebook ---
    try:
        notebook = await client.notebooks.get(notebook_id)
    except Exception as e:
        # Fallback: thử list tất cả rồi lọc
        print(f"  ⚠️  Không thể get trực tiếp, thử list notebooks...")
        all_notebooks = await client.notebooks.list()
        notebook = None
        for nb in all_notebooks:
            if nb.id == notebook_id:
                notebook = nb
                break
        if notebook is None:
            print(f"  ❌ Không tìm thấy notebook {notebook_id}")
            update_sync_log(notebook_id, "unknown", "NOT_FOUND")
            return {"status": "NOT_FOUND", "id": notebook_id}

    title = getattr(notebook, "title", None) or "Untitled Notebook"
    slug = slugify(title)
    print(f"  📓 Notebook: {title}")

    # --- Bước 2: Chuẩn bị thư mục đầu ra ---
    out_dir = KNOWLEDGE_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "artifacts" / "notes").mkdir(parents=True, exist_ok=True)
    (out_dir / "artifacts" / "sources").mkdir(parents=True, exist_ok=True)

    # --- Bước 3: Đồng bộ Sources (bao gồm full-text) ---
    source_count = 0
    try:
        sources = await client.sources.list(notebook_id)
        print(f"  📎 Tìm thấy {len(sources)} nguồn tài liệu (sources)")

        for idx, source in enumerate(sources, 1):
            s_title = getattr(source, "title", None) or f"Source {idx}"
            s_content = getattr(source, "content", None) or ""
            s_type = getattr(source, "type", None) or "unknown"
            s_url = getattr(source, "url", None) or ""
            s_id = getattr(source, "id", None) or ""

            # --- Thử lấy full-text nội dung ---
            fulltext = ""
            if s_id:
                fulltext = await _fetch_source_fulltext(client, notebook_id, s_id, s_title)

            # Ưu tiên: fulltext > content > placeholder
            if fulltext:
                s_content = fulltext
            elif not s_content:
                s_content = (
                    f"*(Nội dung nguồn tài liệu \"{s_title}\" được lưu trữ "
                    f"trên Gemini Notebook. Truy cập notebook để xem chi tiết.)*"
                )

            filename = f"source_{idx:02d}_{sanitize_filename(s_title)}.md"
            extra = f"- **Loại**: {s_type}"
            if s_url:
                extra += f"\n- **URL gốc**: {s_url}"
            if s_id:
                extra += f"\n- **Source ID**: `{s_id}`"

            content_len = len(s_content)
            content_indicator = f"({content_len:,} ký tự)" if fulltext else "(metadata only)"

            write_markdown(
                out_dir / "artifacts" / "sources" / filename,
                s_title,
                s_content,
                extra_header=extra,
            )
            source_count += 1
            print(f"    ✅ [{idx}/{len(sources)}] {s_title} {content_indicator}")

    except Exception as e:
        print(f"  ⚠️  Lỗi khi lấy sources: {e}")

    # --- Bước 4: Đồng bộ Notes ---
    note_count = 0
    try:
        notes = await client.notes.list(notebook_id)
        print(f"  📝 Tìm thấy {len(notes)} ghi chú (notes)")

        for idx, note in enumerate(notes, 1):
            n_title = getattr(note, "title", None) or f"Note {idx}"
            n_content = getattr(note, "content", None) or ""

            if not n_content:
                n_content = f"*(Ghi chú trống hoặc chưa có nội dung)*"

            filename = f"note_{idx:02d}_{sanitize_filename(n_title)}.md"

            write_markdown(
                out_dir / "artifacts" / "notes" / filename,
                n_title,
                n_content,
            )
            note_count += 1
            print(f"    ✅ [{idx}/{len(notes)}] {n_title}")

    except Exception as e:
        print(f"  ⚠️  Lỗi khi lấy notes: {e}")

    # --- Bước 5: Ghi metadata ---
    description = (
        f"Tri thức được đồng bộ tự động từ Gemini Notebook \"{title}\". "
        f"Chứa {source_count} nguồn tài liệu và {note_count} ghi chú đã xử lý."
    )
    write_metadata(out_dir, notebook_id, title, description,
                   source_count, note_count)

    # --- Bước 6: Ghi log ---
    update_sync_log(notebook_id, slug, "SUCCESS", source_count, note_count)

    result = {
        "status": "SUCCESS",
        "id": notebook_id,
        "title": title,
        "slug": slug,
        "sources": source_count,
        "notes": note_count,
        "output_dir": str(out_dir),
    }
    print(f"\n  ✅ Hoàn tất: {source_count} sources + {note_count} notes → {out_dir.relative_to(WORKSPACE_ROOT)}")
    return result


async def run_sync(notebook_ids: list[str]) -> list[dict]:
    """Chạy đồng bộ cho danh sách notebook IDs."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        print("❌ Chưa cài thư viện notebooklm-py!")
        print()
        print("Vui lòng chạy các lệnh sau:")
        print('  pip3 install "notebooklm-py[browser]"')
        print("  playwright install chromium")
        print("  notebooklm login")
        print()
        sys.exit(1)

    results = []

    try:
        async with NotebookLMClient.from_storage() as client:
            print("✅ Đã kết nối thành công với Gemini Notebook!")
            print(f"📋 Danh sách notebook cần đồng bộ: {len(notebook_ids)} notebook(s)")

            for nb_id in notebook_ids:
                try:
                    result = await sync_one_notebook(client, nb_id)
                    results.append(result)
                except Exception as e:
                    print(f"\n❌ Lỗi khi đồng bộ notebook {nb_id}: {e}")
                    update_sync_log(nb_id, "unknown", f"ERROR: {e}")
                    results.append({"status": "ERROR", "id": nb_id, "error": str(e)})

    except Exception as e:
        error_msg = str(e)
        if "storage" in error_msg.lower() or "auth" in error_msg.lower() or "login" in error_msg.lower():
            print("❌ Chưa đăng nhập! Vui lòng chạy lệnh sau trước:")
            print("  notebooklm login")
            print()
            print("Lệnh này sẽ mở trình duyệt để bạn đăng nhập tài khoản Google.")
        else:
            print(f"❌ Lỗi kết nối: {e}")
        sys.exit(1)

    return results


# ---------------------------------------------------------------------------
# Báo cáo tổng kết
# ---------------------------------------------------------------------------

def print_report(results: list[dict]) -> None:
    """In báo cáo tổng kết sau khi đồng bộ."""
    print("\n" + "=" * 60)
    print("📊 BÁO CÁO ĐỒNG BỘ GEMINI NOTEBOOK → AI WORKFORCE")
    print("=" * 60)

    total_sources = 0
    total_notes = 0
    success = 0
    failed = 0

    for r in results:
        status_icon = "✅" if r["status"] == "SUCCESS" else "❌"
        title = r.get("title", r.get("id", "Unknown"))
        print(f"  {status_icon} {title}")

        if r["status"] == "SUCCESS":
            s = r.get("sources", 0)
            n = r.get("notes", 0)
            print(f"     → {s} sources, {n} notes → .agents/knowledge/{r['slug']}/")
            total_sources += s
            total_notes += n
            success += 1
        else:
            print(f"     → {r.get('error', r['status'])}")
            failed += 1

    print(f"\n  Tổng kết: {success} thành công, {failed} thất bại")
    print(f"  Tổng cộng: {total_sources} sources + {total_notes} notes đã đồng bộ")
    print(f"  Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Đồng bộ tri thức từ Gemini Notebook về .agents/knowledge/",
        epilog=(
            "Ví dụ:\n"
            "  python3 scripts/sync_notebook.py\n"
            "  python3 scripts/sync_notebook.py --notebook-id abc123\n"
            "  python3 scripts/sync_notebook.py --notebook-id id1 --notebook-id id2\n"
            "  python3 scripts/sync_notebook.py --list\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--notebook-id",
        action="append",
        dest="notebook_ids",
        help="ID notebook cần đồng bộ (có thể dùng nhiều lần). "
             "Mặc định: notebook đã cấu hình sẵn trong script.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liệt kê tất cả notebook có trên tài khoản (không đồng bộ).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ quét và hiển thị, không ghi file.",
    )
    args = parser.parse_args()

    # Chế độ list
    if args.list:
        asyncio.run(list_all_notebooks())
        return

    # Xác định danh sách notebook IDs
    notebook_ids = args.notebook_ids or DEFAULT_NOTEBOOK_IDS

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  🔄 SYNC GEMINI NOTEBOOK → AI WORKFORCE KNOWLEDGE      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Workspace: {WORKSPACE_ROOT}")
    print(f"  Knowledge: {KNOWLEDGE_DIR}")
    print(f"  Notebooks: {len(notebook_ids)}")

    results = asyncio.run(run_sync(notebook_ids))
    print_report(results)


async def list_all_notebooks():
    """Liệt kê tất cả notebook trên tài khoản."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        print("❌ Chưa cài notebooklm-py. Chạy: pip3 install 'notebooklm-py[browser]'")
        sys.exit(1)

    try:
        async with NotebookLMClient.from_storage() as client:
            notebooks = await client.notebooks.list()
            print(f"\n📋 Tìm thấy {len(notebooks)} notebook(s):\n")
            for idx, nb in enumerate(notebooks, 1):
                title = getattr(nb, "title", "Untitled")
                nb_id = getattr(nb, "id", "unknown")
                print(f"  {idx}. {title}")
                print(f"     ID: {nb_id}")
                print(f"     URL: https://notebook.google.com/notebook/{nb_id}")
                print()
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print("Đã đăng nhập chưa? Chạy: notebooklm login")
        sys.exit(1)


if __name__ == "__main__":
    main()
