#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_designcraft.py - Tự động tải và thiết lập cỗ máy DesignCraft CLI cho AI Workforce.
Được đặt tại: .agents/skills/_shared/bin/designcraft-cli (gitignored theo Luật R0 và R1).

Hỗ trợ macOS (Apple Silicon / Intel Universal) và Linux (x86_64 / aarch64).
Chạy: python3 scripts/setup_designcraft.py
"""

import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
SHARED_BIN = WORKSPACE / ".agents" / "skills" / "_shared" / "bin"
DESIGNCRAFT_BIN = SHARED_BIN / "designcraft-cli"

RELEASE_TAG = "v0.2.1"
BASE_URL = f"https://github.com/storytold/designcraft/releases/download/{RELEASE_TAG}"


def get_download_url() -> tuple[str, str]:
    """Trả về (url, kiểu_archive) phù hợp với OS và Architecture hiện tại."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        # macOS Universal (hỗ trợ cả Apple Silicon arm64 và Intel x86_64)
        return f"{BASE_URL}/designcraft-cli-{RELEASE_TAG.lstrip('v')}-macos-universal.zip", "zip"
    elif system == "linux":
        if "arm" in machine or "aarch64" in machine:
            return f"{BASE_URL}/designcraft-{RELEASE_TAG.lstrip('v')}-linux-aarch64.tar.gz", "tar.gz"
        else:
            return f"{BASE_URL}/designcraft-{RELEASE_TAG.lstrip('v')}-linux-x86_64.tar.gz", "tar.gz"
    else:
        raise OSError(f"Hệ điều hành {system} chưa được hỗ trợ tự động.")


def verify_binary(bin_path: Path) -> bool:
    """Kiểm tra binary có chạy được và in ra version hợp lệ không."""
    if not bin_path.exists():
        return False
    try:
        res = subprocess.run([str(bin_path), "--version"], capture_output=True, text=True, check=True)
        return "designcraft-cli" in res.stdout.lower() or "0." in res.stdout
    except Exception:
        return False


def install_designcraft() -> bool:
    if verify_binary(DESIGNCRAFT_BIN):
        print(f"✅ DesignCraft CLI đã sẵn sàng: {DESIGNCRAFT_BIN}")
        return True

    SHARED_BIN.mkdir(parents=True, exist_ok=True)
    url, archive_type = get_download_url()
    print(f"▶ Đang tải DesignCraft CLI {RELEASE_TAG} từ {url}...")

    with tempfile.TemporaryDirectory() as td:
        archive_path = Path(td) / ("archive." + ("zip" if archive_type == "zip" else "tar.gz"))
        
        req = urllib.request.Request(url, headers={"User-Agent": "AIWF-DesignCraft-Installer"})
        with urllib.request.urlopen(req) as resp, open(archive_path, "wb") as out_file:
            shutil.copyfileobj(resp, out_file)

        print("▶ Đang giải nén binary...")
        if archive_type == "zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(td)
                # Tìm file thực thi designcraft-cli trong thư mục giải nén
                found = list(Path(td).glob("**/designcraft-cli"))
                if not found:
                    print("❌ Không tìm thấy binary designcraft-cli trong file zip.", file=sys.stderr)
                    return False
                shutil.copy2(found[0], DESIGNCRAFT_BIN)
        else:
            import tarfile
            with tarfile.open(archive_path, "r:*") as tf:
                tf.extractall(td)
                found = list(Path(td).glob("**/designcraft-cli"))
                if not found:
                    print("❌ Không tìm thấy binary designcraft-cli trong archive.", file=sys.stderr)
                    return False
                shutil.copy2(found[0], DESIGNCRAFT_BIN)

    # Cấp quyền thực thi
    DESIGNCRAFT_BIN.chmod(DESIGNCRAFT_BIN.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    if verify_binary(DESIGNCRAFT_BIN):
        res = subprocess.run([str(DESIGNCRAFT_BIN), "--version"], capture_output=True, text=True)
        print(f"✅ Cài đặt thành công: {DESIGNCRAFT_BIN} ({res.stdout.strip()})")
        return True
    else:
        print("❌ Binary không thể thực thi sau khi cài đặt.", file=sys.stderr)
        return False


def main():
    success = install_designcraft()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
