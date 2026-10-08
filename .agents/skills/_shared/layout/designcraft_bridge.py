#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
designcraft_bridge.py — Cầu nối thực thi cỗ máy Desktop Publishing (DesignCraft DTP Engine).
Module dùng chung trong AIWF (_shared/layout/designcraft_bridge.py — Luật R7).

Cho phép các skill (thiet-ke, bao-cao-kt, dich-thuat) điều khiển cỗ máy dàn trang Pure Rust:
- Dàn trang ấn phẩm bằng kịch bản .dcs (chuỗi khung liên thông threaded frames, Knuth-Plass).
- Render trực tiếp trang tài liệu ra PNG (phục vụ visual inspection trong 40ms) hoặc PDF in ấn.
- Kiểm tra danh mục lệnh DTP (list_commands, describe).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE = Path(__file__).resolve().parents[3]
SHARED_BIN = Path(__file__).resolve().parent.parent / "bin"
DESIGNCRAFT_LOCAL_BIN = SHARED_BIN / "designcraft-cli"


def get_designcraft_bin() -> Optional[Path]:
    """Tìm binary designcraft-cli từ _shared/bin hoặc hệ thống PATH."""
    if DESIGNCRAFT_LOCAL_BIN.exists() and os.access(DESIGNCRAFT_LOCAL_BIN, os.X_OK):
        return DESIGNCRAFT_LOCAL_BIN
    sys_bin = shutil.which("designcraft-cli")
    if sys_bin:
        return Path(sys_bin)
    return None


def is_available() -> bool:
    """Kiểm tra DesignCraft CLI đã sẵn sàng hoạt động hay chưa."""
    b = get_designcraft_bin()
    if not b:
        return False
    try:
        res = subprocess.run([str(b), "--version"], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def run_script(
    script_text: str,
    export_path: Optional[str] = None,
    save_path: Optional[str] = None,
    in_file: Optional[str] = None,
    keep_going: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Thực thi kịch bản dàn trang DesignCraft Script (.dcs).
    Trả về: (thành_công: bool, kết_quả_json: dict)
    """
    bin_path = get_designcraft_bin()
    if not bin_path:
        return False, {"error": "Chưa cài đặt designcraft-cli. Hãy chạy: python3 scripts/setup_designcraft.py"}

    with tempfile.NamedTemporaryFile("w", suffix=".dcs", encoding="utf-8", delete=False) as tf:
        tf.write(script_text)
        script_file = Path(tf.name)

    try:
        cmd = [str(bin_path), "script", str(script_file)]
        if export_path:
            Path(export_path).parent.mkdir(parents=True, exist_ok=True)
            cmd.extend(["--export", str(export_path)])
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            cmd.extend(["--save", str(save_path)])
        if in_file:
            cmd.extend(["--in", str(in_file)])
        if keep_going:
            cmd.append("--keep-going")

        res = subprocess.run(cmd, capture_output=True, text=True)
        try:
            data = json.loads(res.stdout) if res.stdout.strip() else {}
        except Exception:
            data = {"raw_output": res.stdout, "stderr": res.stderr}

        ok = (res.returncode == 0)
        if not ok and "error" not in data:
            data["error"] = res.stderr.strip() or "Script thực thi thất bại."
        return ok, data
    finally:
        if script_file.exists():
            script_file.unlink()


def render_sample(page: int = 0, export_path: str = "sample.png") -> bool:
    """Render trang mẫu tạp chí có sẵn của DesignCraft ra PNG hoặc PDF."""
    bin_path = get_designcraft_bin()
    if not bin_path:
        print("❌ Chưa cài đặt designcraft-cli.", file=sys.stderr)
        return False

    out = Path(export_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(bin_path), "run", "--sample", "--page", str(page), "--export", str(out)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✅ Đã render trang mẫu {page} ra {out}")
        return True
    else:
        print(f"❌ Lỗi khi render: {res.stderr}", file=sys.stderr)
        return False


def list_commands(filter_kw: Optional[str] = None) -> List[Dict[str, Any]]:
    """Liệt kê danh sách lệnh DTP có sẵn của DesignCraft dưới dạng danh sách dict."""
    bin_path = get_designcraft_bin()
    if not bin_path:
        return []
    cmd = [str(bin_path), "commands"]
    if filter_kw:
        cmd.append(filter_kw)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            return json.loads(res.stdout)
        except Exception:
            return [{"id": line.strip()} for line in res.stdout.splitlines() if line.strip()]
    return []


def main():
    ap = argparse.ArgumentParser(description="AIWF DesignCraft DTP Bridge CLI")
    ap.add_argument("--check", action="store_true", help="Kiểm tra trạng thái sẵn sàng của DesignCraft CLI")
    ap.add_argument("--render-sample", action="store_true", help="Render trang mẫu magazine ra file")
    ap.add_argument("--page", type=int, default=0, help="Số trang cần render (mặc định 0)")
    ap.add_argument("--out", help="Đường dẫn file đầu ra (PNG hoặc PDF)")
    ap.add_argument("--run-script", help="Đường dẫn file kịch bản .dcs để thực thi")
    ap.add_argument("--list-commands", nargs="?", const="", help="Liệt kê danh mục lệnh DTP (kèm từ khóa lọc)")
    args = ap.parse_args()

    if args.check:
        avail = is_available()
        bin_p = get_designcraft_bin()
        if avail:
            res = subprocess.run([str(bin_p), "--version"], capture_output=True, text=True)
            print(f"✅ DesignCraft CLI sẵn sàng: {bin_p} ({res.stdout.strip()})")
            sys.exit(0)
        else:
            print("❌ DesignCraft CLI chưa sẵn sàng. Hãy chạy: python3 scripts/setup_designcraft.py")
            sys.exit(1)

    if args.render_sample:
        out_p = args.out or "sample.png"
        ok = render_sample(page=args.page, export_path=out_p)
        sys.exit(0 if ok else 1)

    if args.list_commands is not None:
        cmds = list_commands(args.list_commands or None)
        print(f"📋 Tìm thấy {len(cmds)} lệnh DTP:")
        for c in cmds[:25]:
            cmd_id = c.get("id", "")
            lbl = c.get("label", "")
            params = c.get("params", "")
            shortcut = f" [{c.get('shortcut')}]" if c.get("shortcut") else ""
            print(f"   • {cmd_id}: \"{lbl}\"{shortcut}")
            if params and len(params) > 10:
                short_p = params if len(params) <= 90 else params[:87] + "..."
                print(f"     └─ params: {short_p}")
        if len(cmds) > 25:
            print(f"   ... và {len(cmds) - 25} lệnh khác.")
        sys.exit(0)

    if args.run_script:
        p = Path(args.run_script)
        if not p.exists():
            print(f"❌ Không tìm thấy file: {p}", file=sys.stderr)
            sys.exit(1)
        ok, res = run_script(p.read_text(encoding="utf-8"), export_path=args.out)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        sys.exit(0 if ok else 1)

    ap.print_help()


if __name__ == "__main__":
    main()
