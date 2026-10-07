#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
soffice_tools.py — Engine dùng chung (Luật R7, id: office.soffice): tìm và chạy LibreOffice headless,
chuyển định dạng, tính lại công thức xlsx, render PDF/PNG. Chỉ tồn tại MỘT bản tại đây.

  from soffice_tools import find_soffice, run_soffice, convert, recalc_xlsx, render_png, SofficeMissing

- find_soffice(): $SOFFICE -> PATH -> vị trí cài chuẩn macOS/Windows/Linux; không có -> None.
- run_soffice(args): chạy soffice với môi trường phù hợp (VCL "svp"; shim socket trên Linux bị chặn AF_UNIX).
- convert(src, fmt, outdir): dùng profile riêng nên không đụng phiên LibreOffice của người dùng.
- Thiếu LibreOffice -> SofficeMissing (RuntimeError) kèm hướng dẫn cài.

CLI (giữ tương thích cách gọi cũ của xu-ly-van-phong): python3 soffice_tools.py --headless --convert-to pdf ... file
"""

import glob
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

_SOFFICE_CANDIDATES = [
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    os.path.expanduser("~/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    "/usr/bin/soffice", "/usr/bin/libreoffice", "/usr/local/bin/soffice",
    "/opt/homebrew/bin/soffice", "/snap/bin/libreoffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


class SofficeMissing(RuntimeError):
    """Không tìm thấy LibreOffice; thông báo có cách cài."""


def find_soffice():
    """Tìm LibreOffice: $SOFFICE -> PATH -> vị trí cài đặt chuẩn macOS/Windows/Linux. Không có -> None."""
    env = os.environ.get("SOFFICE")
    if env and Path(env).exists():
        return env
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    for c in _SOFFICE_CANDIDATES:
        if Path(c).exists():
            return c
    for c in glob.glob("/opt/libreoffice*/program/soffice"):
        return c
    return None


def require_soffice():
    p = find_soffice()
    if not p:
        raise SofficeMissing(
            "Không tìm thấy LibreOffice (soffice). Cài: macOS `brew install --cask libreoffice`, "
            "Ubuntu `sudo apt install libreoffice`, Windows tải tại libreoffice.org; "
            "hoặc đặt biến môi trường SOFFICE=<đường dẫn soffice>.")
    return p


def get_soffice_env() -> dict:
    env = os.environ.copy()
    env["SAL_USE_VCLPLUGIN"] = "svp"
    if sys.platform.startswith("linux") and _needs_shim():
        env["LD_PRELOAD"] = str(_ensure_shim())
    return env


def run_soffice(args, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run([require_soffice()] + list(args), env=get_soffice_env(), **kwargs)


def convert(src, fmt, outdir, timeout=180):
    """soffice --headless --convert-to <fmt>. Trả về đường dẫn file kết quả; lỗi -> RuntimeError."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    profile = Path(tempfile.mkdtemp(prefix="lo_profile_"))  # tránh đụng phiên LibreOffice đang mở
    try:
        res = run_soffice([f"-env:UserInstallation=file://{profile.as_posix()}", "--headless", "--convert-to", fmt,
                           "--outdir", str(outdir), str(src)], capture_output=True, text=True, timeout=timeout)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    out = outdir / (Path(src).stem + "." + fmt.split(":")[0])
    if not out.exists():
        raise RuntimeError(f"LibreOffice không tạo được {out.name}: {res.stderr.strip() or res.stdout.strip()}")
    return out


def recalc_xlsx(path):
    """Mở bằng LibreOffice và lưu lại để mọi công thức có giá trị (cached values). Trả về file tạm."""
    return convert(path, "xlsx", tempfile.mkdtemp(prefix="recalc_"))


def render_png(src, outdir, dpi=80):
    """Render file Office -> PDF -> PNG từng trang. Trả về (pdf, [png]).
    Mỗi file render vào thư mục con riêng <tên>_<đuôi>/ để xlsx và pptx cùng tên không ghi đè nhau."""
    outdir = Path(outdir) / f"{Path(src).stem}_{Path(src).suffix.lstrip('.')}"
    pdf = convert(src, "pdf", outdir)
    stem = outdir / Path(src).stem
    pngs = []
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(stem)], check=True)
        pngs = sorted(outdir.glob(Path(src).stem + "-*.png"))
    else:
        try:
            import pymupdf as fitz
        except ImportError:
            try:
                import fitz  # PyMuPDF bản cũ
            except ImportError:
                raise RuntimeError("Cần pdftoppm (poppler) hoặc PyMuPDF để render PNG.")
        doc = fitz.open(str(pdf))
        for i, page in enumerate(doc, 1):
            p = outdir / f"{Path(src).stem}-{i}.png"
            page.get_pixmap(dpi=dpi).save(str(p))
            pngs.append(p)
    return pdf, pngs


# ---- shim AF_UNIX cho môi trường sandbox Linux (chỉ biên dịch khi thật sự bị chặn socket) ----

_SHIM_SO = Path(tempfile.gettempdir()) / "lo_socket_shim.so"


def _needs_shim() -> bool:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.close()
        return False
    except OSError:
        return True


def _ensure_shim() -> Path:
    if _SHIM_SO.exists():
        return _SHIM_SO
    src = Path(tempfile.gettempdir()) / "lo_socket_shim.c"
    src.write_text(_SHIM_SOURCE)
    subprocess.run(["gcc", "-shared", "-fPIC", "-o", str(_SHIM_SO), str(src), "-ldl"], check=True, capture_output=True)
    src.unlink()
    return _SHIM_SO


_SHIM_SOURCE = r"""
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>

static int (*real_socket)(int, int, int);
static int (*real_socketpair)(int, int, int, int[2]);
static int (*real_listen)(int, int);
static int (*real_accept)(int, struct sockaddr *, socklen_t *);
static int (*real_close)(int);
static int (*real_read)(int, void *, size_t);

/* Per-FD bookkeeping (FDs >= 1024 are passed through unshimmed). */
static int is_shimmed[1024];
static int peer_of[1024];
static int wake_r[1024];            /* accept() blocks reading this */
static int wake_w[1024];            /* close()  writes to this      */
static int listener_fd = -1;        /* FD that received listen()    */

__attribute__((constructor))
static void init(void) {
    real_socket     = dlsym(RTLD_NEXT, "socket");
    real_socketpair = dlsym(RTLD_NEXT, "socketpair");
    real_listen     = dlsym(RTLD_NEXT, "listen");
    real_accept     = dlsym(RTLD_NEXT, "accept");
    real_close      = dlsym(RTLD_NEXT, "close");
    real_read       = dlsym(RTLD_NEXT, "read");
    for (int i = 0; i < 1024; i++) {
        peer_of[i] = -1;
        wake_r[i]  = -1;
        wake_w[i]  = -1;
    }
}

/* ---- socket ---------------------------------------------------------- */
int socket(int domain, int type, int protocol) {
    if (domain == AF_UNIX) {
        int fd = real_socket(domain, type, protocol);
        if (fd >= 0) return fd;
        /* socket(AF_UNIX) blocked – fall back to socketpair(). */
        int sv[2];
        if (real_socketpair(domain, type, protocol, sv) == 0) {
            if (sv[0] >= 0 && sv[0] < 1024) {
                is_shimmed[sv[0]] = 1;
                peer_of[sv[0]]    = sv[1];
                int wp[2];
                if (pipe(wp) == 0) {
                    wake_r[sv[0]] = wp[0];
                    wake_w[sv[0]] = wp[1];
                }
            }
            return sv[0];
        }
        errno = EPERM;
        return -1;
    }
    return real_socket(domain, type, protocol);
}

/* ---- listen ---------------------------------------------------------- */
int listen(int sockfd, int backlog) {
    if (sockfd >= 0 && sockfd < 1024 && is_shimmed[sockfd]) {
        listener_fd = sockfd;
        return 0;
    }
    return real_listen(sockfd, backlog);
}

/* ---- accept ---------------------------------------------------------- */
int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen) {
    if (sockfd >= 0 && sockfd < 1024 && is_shimmed[sockfd]) {
        /* Block until close() writes to the wake pipe. */
        if (wake_r[sockfd] >= 0) {
            char buf;
            real_read(wake_r[sockfd], &buf, 1);
        }
        errno = ECONNABORTED;
        return -1;
    }
    return real_accept(sockfd, addr, addrlen);
}

/* ---- close ----------------------------------------------------------- */
int close(int fd) {
    if (fd >= 0 && fd < 1024 && is_shimmed[fd]) {
        int was_listener = (fd == listener_fd);
        is_shimmed[fd] = 0;

        if (wake_w[fd] >= 0) {              /* unblock accept() */
            char c = 0;
            write(wake_w[fd], &c, 1);
            real_close(wake_w[fd]);
            wake_w[fd] = -1;
        }
        if (wake_r[fd] >= 0) { real_close(wake_r[fd]); wake_r[fd]  = -1; }
        if (peer_of[fd] >= 0) { real_close(peer_of[fd]); peer_of[fd] = -1; }

        if (was_listener)
            _exit(0);                        /* conversion done – exit */
    }
    return real_close(fd);
}
"""


def main(argv=None) -> int:
    try:
        return run_soffice(sys.argv[1:] if argv is None else argv).returncode
    except SofficeMissing as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
