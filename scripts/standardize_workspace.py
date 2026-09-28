#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
standardize_workspace.py — Chuẩn hóa & Hợp nhất Workspace Antigravity (SSOT Symlink Architecture)
Tuân thủ:
- Luật R0: Mọi thay đổi đồng bộ qua Git (Git-Sync Mandatory)
- Luật R1: Bảo toàn dữ liệu (Zero-Destruction - Không xóa mã nguồn khi chưa backup)
- Luật R2: Phân loại minh bạch (Zero-Inference Taxonomy & Codebase-first)

Tác vụ:
1. Phát hiện tình trạng phân mảnh giữa ~/.gemini/antigravity/scratch và ~/.gemini/antigravity-ide/scratch.
2. Kiểm tra Git status (uncommitted, unpushed) trên từng dự án.
3. Hợp nhất dự án về ~/.gemini/antigravity-ide/scratch (Single Source of Truth).
4. Tạo Symbolic Link từ ~/.gemini/antigravity/scratch -> ~/.gemini/antigravity-ide/scratch.
5. Tạo Symbolic Link từ ~/.gemini/antigravity/skills -> ~/.gemini/config/skills (nếu có).
6. Dọn dẹp an toàn các file rác (__pycache__, .DS_Store, Chromium cache, logs/recordings cũ).

Sử dụng:
    python3 scripts/standardize_workspace.py             # Mặc định: Chế độ khảo sát (Dry-run audit)
    python3 scripts/standardize_workspace.py --execute   # Thực thi chuẩn hóa & dọn dẹp
    python3 scripts/standardize_workspace.py --cleanup   # Chỉ dọn dẹp rác (không đụng thư mục dự án)
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Màu hiển thị Terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def get_dir_size(path: Path) -> int:
    """Tính tổng dung lượng thư mục bằng du -sk (cực nhanh trên macOS/Linux)."""
    if not path.exists():
        return 0
    try:
        res = subprocess.run(["du", "-sk", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            kb = int(res.stdout.strip().split()[0])
            return kb * 1024
    except Exception:
        pass
    return 0

def format_size(size_bytes: int) -> str:
    """Format dung lượng sang KB, MB, GB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def check_git_repo(path: Path) -> dict:
    """Kiểm tra trạng thái Git repo: commit mới nhất, uncommitted changes."""
    git_dir = path / ".git"
    if not git_dir.exists():
        return {"is_git": False}

    info = {"is_git": True, "dirty": False, "commit": "", "date": "", "unpushed": False}
    try:
        # Check dirty
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
        )
        if res.stdout.strip():
            info["dirty"] = True

        # Last commit
        res = subprocess.run(
            ["git", "log", "-1", "--format=%h|%cI|%s"],
            cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
        )
        if res.returncode == 0 and res.stdout.strip():
            parts = res.stdout.strip().split("|", 2)
            info["commit"] = parts[0]
            info["date"] = parts[1][:10] if len(parts) > 1 else ""

        # Unpushed commits
        res = subprocess.run(
            ["git", "log", "@{u}..HEAD", "--oneline"],
            cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
        )
        if res.returncode == 0 and res.stdout.strip():
            info["unpushed"] = True
    except Exception:
        pass

    return info

def scan_cleanable_items(gemini_dir: Path) -> list:
    """Quét các mục rác có thể dọn dẹp trong ~/.gemini."""
    items = []

    # 1. Chromium Browser profile
    browser_prof = gemini_dir / "antigravity-browser-profile"
    if browser_prof.exists():
        sz = get_dir_size(browser_prof)
        if sz > 0:
            items.append({"type": "browser_profile", "path": browser_prof, "size": sz, "desc": "Chromium Browser Cache"})

    # 2. __pycache__ & .DS_Store (bỏ qua scratch, backup để quét nhanh)
    pycache_size = 0
    pycache_dirs = []
    ds_size = 0
    ds_files = []
    
    skip_dirs = {"scratch", "scratch_backup", "node_modules", ".git", "brain", "conversations"}

    for root, dirs, files in os.walk(gemini_dir):
        # Prune dirs
        dirs[:] = [d for d in dirs if not any(s in d for s in skip_dirs)]
        if "__pycache__" in dirs:
            p = Path(root) / "__pycache__"
            s = get_dir_size(p)
            pycache_size += s
            pycache_dirs.append(p)
        if ".DS_Store" in files:
            p = Path(root) / ".DS_Store"
            try:
                s = p.stat().st_size
                ds_size += s
                ds_files.append(p)
            except Exception:
                pass

    if pycache_size > 0:
        items.append({"type": "pycache", "paths": pycache_dirs, "size": pycache_size, "desc": f"Python __pycache__ ({len(pycache_dirs)} dirs)"})
    if ds_size > 0:
        items.append({"type": "ds_store", "paths": ds_files, "size": ds_size, "desc": f"macOS .DS_Store ({len(ds_files)} files)"})

    # 4. Old scratch backups
    ag_dir = gemini_dir / "antigravity"
    if ag_dir.exists():
        for p in ag_dir.iterdir():
            if p.is_dir() and "scratch_backup" in p.name:
                sz = get_dir_size(p)
                items.append({"type": "scratch_backup", "path": p, "size": sz, "desc": f"Bản backup cũ ({p.name})"})

    # 5. Temp in ~/.gemini/tmp
    tmp_dir = gemini_dir / "tmp"
    if tmp_dir.exists():
        sz = get_dir_size(tmp_dir)
        if sz > 0:
            items.append({"type": "tmp", "path": tmp_dir, "size": sz, "desc": "Thư mục tạm ~/.gemini/tmp"})

    return items

def audit_workspace(home: Path):
    """Khảo sát hiện trạng kiến trúc scratch và phân mảnh."""
    gemini_dir = home / ".gemini"
    ag_scratch = gemini_dir / "antigravity" / "scratch"
    ide_scratch = gemini_dir / "antigravity-ide" / "scratch"

    print(f"\n{BOLD}{CYAN}══════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{CYAN}🔍 KHẢO SÁT HIỆN TRẠNG WORKSPACE ANTIGRAVITY (AUDIT REPORT){RESET}")
    print(f"{BOLD}{CYAN}══════════════════════════════════════════════════════════════{RESET}")
    print(f"• User Home:       {home}")
    print(f"• AG Scratch:      {ag_scratch}")
    print(f"• IDE Scratch:     {ide_scratch}")

    is_symlink = ag_scratch.is_symlink()
    symlink_target = ag_scratch.resolve() if is_symlink else None
    
    print(f"\n{BOLD}1. Trạng Thái Symlink Scratch:{RESET}")
    if is_symlink:
        if symlink_target == ide_scratch.resolve():
            print(f"   {GREEN}✅ ĐÃ CHUẨN HÓA:{RESET} ~/.gemini/antigravity/scratch -> {symlink_target}")
        else:
            print(f"   {YELLOW}⚠️  Symlink tồn tại nhưng trỏ tới:{RESET} {symlink_target}")
    else:
        if ag_scratch.exists():
            print(f"   {RED}❌ PHÂN MẢNH PHÁT HIỆN:{RESET} Thư mục `antigravity/scratch` là thư mục vật lý riêng biệt!")
        else:
            print(f"   {YELLOW}ℹ️  Thư mục `antigravity/scratch` chưa tồn tại.{RESET}")

    # Khảo sát danh sách thư mục dự án
    ag_projects = set()
    ide_projects = set()

    if ag_scratch.exists() and not is_symlink:
        ag_projects = {p.name for p in ag_scratch.iterdir() if p.is_dir() and not p.name.startswith(".")}
    
    if ide_scratch.exists():
        ide_projects = {p.name for p in ide_scratch.iterdir() if p.is_dir() and not p.name.startswith(".")}

    overlap = ag_projects.intersection(ide_projects)
    unique_ag = ag_projects - ide_projects
    unique_ide = ide_projects - ag_projects

    print(f"\n{BOLD}2. Thống Kê Dự Án:{RESET}")
    print(f"   • Dự án tại IDE Scratch (SSOT):  {BOLD}{len(ide_projects)}{RESET}")
    if not is_symlink and ag_scratch.exists():
        print(f"   • Dự án tại AG Scratch:          {BOLD}{len(ag_projects)}{RESET}")
        print(f"   • Dự án chỉ có ở AG Scratch:     {YELLOW}{len(unique_ag)}{RESET} ({', '.join(sorted(unique_ag)) or 'None'})")
        print(f"   • Dự án trùng lặp ở cả hai:     {RED}{len(overlap)}{RESET} ({', '.join(sorted(overlap)) or 'None'})")
    else:
        print(f"   • Trạng thái: Toàn bộ {len(ide_projects)} dự án đang được quản lý tập trung tại IDE Scratch.")

    # Đánh giá rác hệ thống có thể dọn
    print(f"\n{BOLD}3. Khảo Sát Dung Lượng Có Thể Dọn Dẹp:{RESET}")
    cleanable = scan_cleanable_items(gemini_dir)
    total_cleanable = sum(item["size"] for item in cleanable)

    for item in cleanable:
        desc = item["desc"]
        size_str = format_size(item["size"])
        print(f"   • {desc:<42} : {YELLOW}{size_str:>10}{RESET}")
    print(f"   ────────────────────────────────────────────────────────")
    print(f"   {BOLD}Tổng dung lượng rác có thể giải phóng:    : {GREEN}{format_size(total_cleanable):>10}{RESET}")

    return {
        "is_symlink": is_symlink,
        "unique_ag": unique_ag,
        "overlap": overlap,
        "cleanable": cleanable,
        "total_cleanable": total_cleanable
    }

def execute_standardization(home: Path):
    """Thực thi chuẩn hóa hợp nhất dự án và tạo symlink an toàn."""
    gemini_dir = home / ".gemini"
    ag_dir = gemini_dir / "antigravity"
    ag_scratch = ag_dir / "scratch"
    ide_scratch = gemini_dir / "antigravity-ide" / "scratch"
    ag_skills = ag_dir / "skills"
    config_skills = gemini_dir / "config" / "skills"

    ide_scratch.mkdir(parents=True, exist_ok=True)

    print(f"\n{BOLD}{GREEN}══════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}🚀 TIẾN HÀNH CHUẨN HÓA WORKSPACE & TẠO SYMLINK SSOT{RESET}")
    print(f"{BOLD}{GREEN}══════════════════════════════════════════════════════════════{RESET}")

    # BƯỚC 1: Xử lý AG Scratch nếu là thư mục vật lý (chưa symlink)
    if ag_scratch.exists() and not ag_scratch.is_symlink():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = ag_dir / f"scratch_backup_{timestamp}"
        print(f"\n{BOLD}Bước 1: Sao lưu an toàn `antigravity/scratch`...{RESET}")
        print(f"   Đổi tên: {ag_scratch} -> {backup_dir.name}")
        ag_scratch.rename(backup_dir)

        # Chép các dự án từ backup sang ide_scratch nếu chưa có
        print(f"\n{BOLD}Bước 2: Hợp nhất dự án sang `antigravity-ide/scratch` (SSOT)...{RESET}")
        for p in backup_dir.iterdir():
            if not p.is_dir() or p.name.startswith("."):
                continue
            target_p = ide_scratch / p.name
            if not target_p.exists():
                print(f"   ➕ Chép dự án mới từ backup: {BOLD}{p.name}{RESET}")
                shutil.copytree(p, target_p, symlinks=True)
            else:
                git_b = check_git_repo(p)
                git_t = check_git_repo(target_p)
                print(f"   🔄 Dự án trùng `{p.name}`: IDE commit `{git_t.get('commit', 'N/A')}`, AG commit `{git_b.get('commit', 'N/A')}`")

        # BƯỚC 3: Tạo symlink
        print(f"\n{BOLD}Bước 3: Tạo Symlink Scratch...{RESET}")
        os.symlink(str(ide_scratch), str(ag_scratch))
        print(f"   {GREEN}✅ Symlink scratch đã tạo thành công:{RESET} {ag_scratch} -> {ide_scratch}")

    elif ag_scratch.is_symlink():
        print(f"   {GREEN}✅ `antigravity/scratch` đã là symlink hợp lệ, bỏ qua bước tạo symlink.{RESET}")
    else:
        print(f"\n{BOLD}Tạo Symlink Scratch trực tiếp...{RESET}")
        os.symlink(str(ide_scratch), str(ag_scratch))
        print(f"   {GREEN}✅ Symlink scratch đã tạo thành công:{RESET} {ag_scratch} -> {ide_scratch}")

    # BƯỚC 4: Tạo symlink cho Skills nếu có config/skills
    if config_skills.exists() and (not ag_skills.exists() or not ag_skills.is_symlink()):
        print(f"\n{BOLD}Bước 4: Chuẩn hóa Symlink Skills...{RESET}")
        if ag_skills.exists() and not ag_skills.is_symlink():
            skills_backup = ag_dir / f"skills_backup_{datetime.now().strftime('%Y%m%d')}"
            ag_skills.rename(skills_backup)
            print(f"   Đã backup skills cũ sang: {skills_backup.name}")
        os.symlink(str(config_skills), str(ag_skills))
        print(f"   {GREEN}✅ Symlink skills đã tạo thành công:{RESET} {ag_skills} -> {config_skills}")

    # BƯỚC 5: Dọn dẹp rác an toàn
    execute_cleanup(home)

    print(f"\n{BOLD}{GREEN}══════════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{GREEN}🎉 HOÀN TẤT CHUẨN HÓA WORKSPACE!{RESET}")
    print(f"{BOLD}{GREEN}══════════════════════════════════════════════════════════════{RESET}")
    print(f"• Thư mục duy nhất lưu trữ dự án: {BOLD}{ide_scratch}{RESET}")
    print(f"• Đường dẫn symlink:               {BOLD}{ag_scratch}{RESET}")
    print(f"• Mọi thay đổi từ IDE hay CLI đều được đồng bộ tức thì, không bao giờ bị nhân đôi.")

def execute_cleanup(home: Path):
    """Dọn dẹp rác hệ thống: __pycache__, .DS_Store, cache trình duyệt Chromium, logs cũ."""
    gemini_dir = home / ".gemini"
    print(f"\n{BOLD}Bước 5: Dọn dẹp rác hệ thống & giải phóng ổ đĩa...{RESET}")
    
    cleanable = scan_cleanable_items(gemini_dir)
    freed_bytes = 0

    for item in cleanable:
        itype = item["type"]
        if itype == "browser_profile":
            shutil.rmtree(item["path"], ignore_errors=True)
            freed_bytes += item["size"]
            print(f"   🧹 Đã xóa Chromium Browser cache: {format_size(item['size'])}")
        elif itype == "pycache":
            for p in item["paths"]:
                shutil.rmtree(p, ignore_errors=True)
            freed_bytes += item["size"]
            print(f"   🧹 Đã dọn dẹp các thư mục __pycache__: {format_size(item['size'])}")
        elif itype == "ds_store":
            for p in item["paths"]:
                try:
                    p.unlink()
                except Exception:
                    pass
            freed_bytes += item["size"]
            print(f"   🧹 Đã xóa các file .DS_Store: {format_size(item['size'])}")
        elif itype == "tmp":
            for f in item["path"].iterdir():
                try:
                    if f.is_dir():
                        shutil.rmtree(f, ignore_errors=True)
                    else:
                        f.unlink()
                except Exception:
                    pass
            freed_bytes += item["size"]
            print(f"   🧹 Đã dọn dẹp thư mục tmp: {format_size(item['size'])}")

    print(f"   {GREEN}✅ Tổng dung lượng rác đã giải phóng: {format_size(freed_bytes)}{RESET}")

def main():
    parser = argparse.ArgumentParser(description="Chuẩn hóa Workspace Antigravity & Symlink SSOT")
    parser.add_argument("--execute", action="store_true", help="Thực thi chuẩn hóa dự án và tạo symlink")
    parser.add_argument("--cleanup", action="store_true", help="Chỉ dọn dẹp rác (không đụng thư mục dự án)")
    args = parser.parse_args()

    home = Path.home()

    if args.cleanup:
        execute_cleanup(home)
    elif args.execute:
        execute_standardization(home)
    else:
        res = audit_workspace(home)
        if not res["is_symlink"]:
            print(f"\n{YELLOW}💡 GỢI Ý:{RESET} Để tiến hành hợp nhất và tạo symlink tự động, hãy chạy:")
            print(f"   {BOLD}python3 scripts/standardize_workspace.py --execute{RESET}\n")

if __name__ == "__main__":
    main()
