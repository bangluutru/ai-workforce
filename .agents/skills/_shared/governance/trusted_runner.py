#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trusted_runner.py — AIWF Local Execute-to-Verify Runner (Luật R7).

Mục đích: cung cấp verifier tin cậy CHO DUY NHẤT một việc: "một profile lệnh kiểm thử đã
được phê duyệt thực sự chạy và thoát với mã 0 tại một revision cụ thể của repo".

NGUYÊN TẮC
1. Runner TỰ chạy lệnh trong allowlist (`trusted_commands.json`). Kết quả đến từ chính
   subprocess (exit code, timeout, stdout/stderr) do runner bắt trực tiếp. KHÔNG đọc log,
   JSON, exit code, `verified=True` hay bất kỳ kết quả nào do caller/agent cung cấp.
2. Caller chỉ được nêu ID profile (`verification_method = "trusted_command:<id>"`). Không thể
   thay executable, đối số, cwd, timeout hay môi trường. Không shell, không pipe/redirect,
   không mở rộng biến, môi trường được lọc theo allowlist.
3. Kết quả gắn với (profile, revision git, fingerprint cây làm việc). Cây làm việc thay đổi
   trong khi chạy -> FAIL. Không lưu/replay kết quả giữa các tiến trình (chỉ memo trong cùng
   tiến trình khi fingerprint không đổi).
4. Fail-closed: cấu hình sai, profile lạ, timeout, lỗi git, lỗi ghi bản ghi, lồng nhau -> passed=False.
5. OPT-IN: import module này KHÔNG đăng ký verifier. Chỉ `install_local_runner_verifier()`
   (CLI: `review_router.py --verify-by-execution`) mới đăng ký, và CHỈ cho
   VERIFIER_AUTOMATED_TEST. Không bao giờ xác lập phê duyệt con người hay thẩm định độc lập.

GIỚI HẠN: chạy test thành công KHÔNG chứng minh repo an toàn để deploy; nó chỉ xác minh việc
thực thi profile đã nêu. Runner chạy cùng quyền người dùng nên KHÔNG chống được một agent đã
bị chiếm quyền sửa allowlist/runner (xem quality-governance.md §4; thay đổi allowlist = Tier 3).

CLI:
    python3 .agents/skills/_shared/governance/trusted_runner.py --list
    python3 .agents/skills/_shared/governance/trusted_runner.py --run <profile_id>
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

_HERE = Path(__file__).resolve().parent
_SHARED = _HERE.parent
for _p in (str(_HERE), str(_SHARED)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import evidence_gate as _eg  # noqa: E402

REPO_ROOT = _SHARED.parents[2]
DEFAULT_CONFIG = _HERE / "trusted_commands.json"

RUNNER_NAME = "aiwf-trusted-runner/1"
CLAIM_RE = re.compile(r"trusted_command:([a-z0-9][a-z0-9-]{0,48})")
PROFILE_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,48}")
STACK_ENV = "AIWF_TRUSTED_RUNNER_STACK"
FORBIDDEN_ARG_CHARS = set("|;&<>$`\\\n\r\t*?~!(){}[]\"' ")
MAX_TIMEOUT = 900
MAX_LOG_BYTES = 4_000_000
GIT_DIRS = ("/usr/bin", "/bin", "/opt/homebrew/bin", "/usr/local/bin")
_MEMO: Dict[Tuple[Any, ...], Dict[str, Any]] = {}


class TrustedRunnerError(Exception):
    """Cấu hình hoặc môi trường runner không hợp lệ (fail-closed)."""


# ---------------------------------------------------------------- config ----
def _inside(root: Path, p: Path) -> bool:
    try:
        p.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _check_arg(arg: Any, repo_root: Path, where: str) -> None:
    if not isinstance(arg, str) or not arg:
        raise TrustedRunnerError(f"{where}: đối số phải là chuỗi không rỗng.")
    if any(c in FORBIDDEN_ARG_CHARS for c in arg):
        raise TrustedRunnerError(f"{where}: đối số chứa ký tự shell/động bị cấm: {arg!r}")
    if arg == "-" or arg.startswith("-c"):
        raise TrustedRunnerError(f"{where}: cấm thực thi mã dòng lệnh (-c) hoặc stdin: {arg!r}")
    if arg.startswith("/") or ".." in arg.split("/"):
        raise TrustedRunnerError(f"{where}: đường dẫn tuyệt đối hoặc '..' bị cấm: {arg!r}")


def validate_config(cfg: Any, repo_root: Path) -> Dict[str, Dict[str, Any]]:
    """Kiểm tra nghiêm ngặt allowlist. Sai bất kỳ điều gì -> TrustedRunnerError."""
    if not isinstance(cfg, dict) or set(cfg) != {"version", "profiles"} or cfg.get("version") != 1:
        raise TrustedRunnerError("Cấu hình: chỉ chấp nhận khóa {version=1, profiles}.")
    profiles = cfg["profiles"]
    if not isinstance(profiles, dict) or not profiles:
        raise TrustedRunnerError("Cấu hình: profiles phải là dict không rỗng.")
    out: Dict[str, Dict[str, Any]] = {}
    for pid, prof in profiles.items():
        where = f"profile '{pid}'"
        if not isinstance(pid, str) or not PROFILE_ID_RE.fullmatch(pid):
            raise TrustedRunnerError(f"{where}: ID không hợp lệ.")
        required = {"executable", "args", "cwd", "timeout_seconds"}
        if not isinstance(prof, dict) or not required <= set(prof) or not set(prof) <= required | {"description"}:
            raise TrustedRunnerError(f"{where}: khóa phải là {sorted(required)} (+description).")
        if prof["executable"] != "python":
            raise TrustedRunnerError(f"{where}: executable chỉ được là 'python' (interpreter của runner).")
        args = prof["args"]
        if not isinstance(args, list) or not args:
            raise TrustedRunnerError(f"{where}: args phải là danh sách không rỗng.")
        for a in args:
            _check_arg(a, repo_root, where)
        if args[0] == "-m":
            if len(args) < 2 or args[1] != "pytest":
                raise TrustedRunnerError(f"{where}: chỉ cho phép '-m pytest'.")
        else:
            script = repo_root / args[0]
            if args[0].startswith("-") or not args[0].endswith(".py") or not script.is_file() or not _inside(repo_root, script):
                raise TrustedRunnerError(f"{where}: script '{args[0]}' phải là tệp .py nằm trong repo.")
        cwd = prof["cwd"]
        if not isinstance(cwd, str) or cwd.startswith("/") or ".." in cwd.split("/"):
            raise TrustedRunnerError(f"{where}: cwd phải là đường dẫn tương đối trong repo.")
        cwd_path = repo_root / cwd
        if not cwd_path.is_dir() or not _inside(repo_root, cwd_path):
            raise TrustedRunnerError(f"{where}: cwd '{cwd}' không tồn tại hoặc nằm ngoài repo.")
        t = prof["timeout_seconds"]
        if isinstance(t, bool) or not isinstance(t, int) or not 1 <= t <= MAX_TIMEOUT:
            raise TrustedRunnerError(f"{where}: timeout_seconds phải là số nguyên 1..{MAX_TIMEOUT}.")
        out[pid] = {"args": list(args), "cwd": cwd, "timeout_seconds": t}
    return out


def load_config(config_path: Path, repo_root: Path) -> Tuple[Dict[str, Dict[str, Any]], str]:
    try:
        raw = Path(config_path).read_bytes()
        cfg = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise TrustedRunnerError(f"Không đọc được cấu hình: {e}") from e
    return validate_config(cfg, repo_root), hashlib.sha256(raw).hexdigest()


# ------------------------------------------------------------------- git ----
def _clean_env() -> Dict[str, str]:
    """Môi trường tối thiểu theo allowlist; không kế thừa phần còn lại của caller."""
    env = {
        "PATH": os.pathsep.join([str(Path(sys.executable).parent), *GIT_DIRS]),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    for k in ("HOME", "TMPDIR"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def _git(repo_root: Path, *args: str) -> bytes:
    git = shutil.which("git", path=os.pathsep.join(GIT_DIRS))
    if not git:
        raise TrustedRunnerError("Không tìm thấy git.")
    env = {"PATH": os.pathsep.join(GIT_DIRS), "GIT_CONFIG_NOSYSTEM": "1"}
    if "HOME" in os.environ:
        env["HOME"] = os.environ["HOME"]
    p = subprocess.run([git, *args], cwd=str(repo_root), env=env, capture_output=True, timeout=120)
    if p.returncode != 0:
        raise TrustedRunnerError(f"git {args[0]} lỗi: {p.stderr.decode('utf-8', 'ignore').strip()[:200]}")
    return p.stdout


def tree_fingerprint(repo_root: Path) -> Tuple[str, str]:
    """(HEAD sha, sha256 của diff so với HEAD + danh sách/hash tệp chưa theo dõi)."""
    head = _git(repo_root, "rev-parse", "HEAD").decode().strip()
    h = hashlib.sha256()
    h.update(_git(repo_root, "diff", "HEAD", "--binary", "--no-ext-diff"))
    untracked = _git(repo_root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    for rel in sorted(x for x in untracked if x):
        h.update(b"\0U\0" + rel)
        fp = repo_root / rel.decode("utf-8", "surrogateescape")
        h.update(hashlib.sha256(fp.read_bytes()).digest() if fp.is_file() else b"-")
    return head, h.hexdigest()


# ------------------------------------------------------------------- run ----
def _fail(profile_id: str, error: str, **extra: Any) -> Dict[str, Any]:
    r = {"runner": RUNNER_NAME, "profile_id": profile_id, "passed": False, "error": error}
    r.update(extra)
    return r


def _write_record(record_base: Optional[Path], profile_id: str, result: Dict[str, Any], out: bytes, err: bytes) -> Path:
    from output_manager import resolve_output_dir  # reuse engine dùng chung (R7)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    d = resolve_output_dir(
        "trusted-runs", user_path=str(record_base) if record_base else None, project_name=f"{profile_id}_{stamp}"
    )
    (d / "stdout.log").write_bytes(out)
    (d / "stderr.log").write_bytes(err)
    result["stdout_sha256"] = hashlib.sha256(out).hexdigest()
    result["stderr_sha256"] = hashlib.sha256(err).hexdigest()
    result["record_dir"] = str(d)
    (d / "record.json").write_text(
        json.dumps({**result, "note": "AUDIT ONLY. Verification never reads this file."}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return d


def run_profile(
    profile_id: str,
    config_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    record_base: Optional[Path] = None,
) -> Dict[str, Any]:
    """Chạy profile allowlist và trả kết quả thực thi thật. KHÔNG BAO GIỜ raise: lỗi -> passed=False."""
    root = Path(repo_root) if repo_root else REPO_ROOT
    cfg_path = Path(config_path) if config_path else DEFAULT_CONFIG
    try:
        if not isinstance(profile_id, str) or not PROFILE_ID_RE.fullmatch(profile_id):
            return _fail(str(profile_id)[:60], "profile_id không hợp lệ")
        stack = [s for s in os.environ.get(STACK_ENV, "").split(",") if s]
        if profile_id in stack:
            return _fail(profile_id, "chạy lồng nhau cùng profile bị chặn (chống đệ quy)")
        profiles, cfg_sha = load_config(cfg_path, root)
        prof = profiles.get(profile_id)
        if prof is None:
            return _fail(profile_id, "profile không có trong allowlist")

        head, fp_before = tree_fingerprint(root)
        argv = [sys.executable, *prof["args"]]
        memo_key = (str(root.resolve()), profile_id, tuple(argv), prof["cwd"], cfg_sha, head, fp_before)
        if memo_key in _MEMO:
            return {**_MEMO[memo_key], "memoized": True}

        env = _clean_env()
        env[STACK_ENV] = ",".join([*stack, profile_id])
        started = datetime.datetime.now(datetime.timezone.utc)
        t0 = time.monotonic()
        timed_out = False
        proc = subprocess.Popen(
            argv, cwd=str(root / prof["cwd"]), env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        )
        try:
            out, err = proc.communicate(timeout=prof["timeout_seconds"])
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            out, err = proc.communicate()
        duration = round(time.monotonic() - t0, 3)
        _, fp_after = tree_fingerprint(root)

        exit_code = proc.returncode
        tree_stable = fp_before == fp_after
        result: Dict[str, Any] = {
            "runner": RUNNER_NAME,
            "profile_id": profile_id,
            "argv": argv,
            "cwd": prof["cwd"],
            "timeout_seconds": prof["timeout_seconds"],
            "config_sha256": cfg_sha,
            "revision": head,
            "tree_fingerprint_before": fp_before,
            "tree_fingerprint_after": fp_after,
            "tree_stable": tree_stable,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "started_at": started.isoformat(),
            "duration_seconds": duration,
            "python": sys.version.split()[0],
            "memoized": False,
        }
        result["passed"] = bool(exit_code == 0 and not timed_out and tree_stable)
        if not tree_stable:
            result["error"] = "cây làm việc thay đổi trong khi chạy"
        _write_record(record_base, profile_id, result, out[:MAX_LOG_BYTES], err[:MAX_LOG_BYTES])
        if result["passed"]:
            _MEMO[memo_key] = dict(result)
        return result
    except Exception as e:  # fail-closed, không nuốt lặng: lỗi được trả về trong kết quả
        return _fail(profile_id if isinstance(profile_id, str) else "?", f"{type(e).__name__}: {e}")


# -------------------------------------------------------------- verifier ----
def make_verifier(
    config_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    record_base: Optional[Path] = None,
) -> Callable[[Dict[str, Any]], bool]:
    def verify(claim: Dict[str, Any]) -> bool:
        # Chỉ lấy ID profile từ verification_method; MỌI trường khác của claim bị bỏ qua.
        step = claim.get("step") if isinstance(claim, dict) else None
        vm = step.get("verification_method") if isinstance(step, dict) else None
        m = CLAIM_RE.fullmatch(vm) if isinstance(vm, str) else None
        if not m:
            return False
        return run_profile(m.group(1), config_path, repo_root, record_base).get("passed") is True

    return verify


def install_local_runner_verifier(
    config_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    record_base: Optional[Path] = None,
) -> None:
    """Đăng ký verifier thực thi cục bộ CHO DUY NHẤT automated_test. Gọi tường minh (opt-in)."""
    _eg._TRUSTED_VERIFIERS[_eg.VERIFIER_AUTOMATED_TEST] = make_verifier(config_path, repo_root, record_base)


def uninstall_local_runner_verifier() -> None:
    _eg._TRUSTED_VERIFIERS.pop(_eg.VERIFIER_AUTOMATED_TEST, None)


def main() -> None:
    ap = argparse.ArgumentParser(description="AIWF Trusted Local Runner (execute-to-verify)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="Liệt kê profile trong allowlist")
    g.add_argument("--run", metavar="PROFILE_ID", help="Chạy một profile và in kết quả thực thi")
    args = ap.parse_args()
    if args.list:
        try:
            profiles, sha = load_config(DEFAULT_CONFIG, REPO_ROOT)
        except TrustedRunnerError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(2)
        print(f"allowlist sha256={sha}")
        for pid, p in profiles.items():
            print(f"- {pid}: python {' '.join(p['args'])} (cwd={p['cwd']}, timeout={p['timeout_seconds']}s)")
        sys.exit(0)
    r = run_profile(args.run)
    print(json.dumps({k: r.get(k) for k in (
        "profile_id", "passed", "exit_code", "timed_out", "tree_stable", "revision", "record_dir", "error")},
        indent=2, ensure_ascii=False))
    sys.exit(0 if r.get("passed") else 1)


if __name__ == "__main__":
    main()
