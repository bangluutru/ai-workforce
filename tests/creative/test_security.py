"""
Security regression tests for Video Studio 2.0 hardening.
Tests:
- Safe frame rate parsing (preventing eval() RCE vulnerabilities)
- Path traversal prevention (LFI / arbitrary file access)
- Null byte rejection
- Extension whitelisting
- Allowed root directory boundaries
"""
import os
import sys
import tempfile
import pytest

# Ensure video-studio scripts are importable
SKILL_SCRIPTS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".agents", "skills", "video-studio", "scripts")
)
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

from beat_detector import parse_frame_rate
from video_studio_server import is_safe_path, get_allowed_roots, ALLOWED_MEDIA_EXTENSIONS, WORKSPACE_ROOT


class TestFrameRateSecurity:
    """Kiểm tra độ an toàn tuyệt đối của parse_frame_rate, triệt tiêu nguy cơ eval() RCE."""

    def test_standard_fps_fractions(self):
        assert parse_frame_rate("30/1") == 30.0
        assert parse_frame_rate("24/1") == 24.0
        assert parse_frame_rate("60000/1001") == 59.94
        assert parse_frame_rate("24000/1001") == 23.976

    def test_numeric_inputs(self):
        assert parse_frame_rate(30) == 30.0
        assert parse_frame_rate(29.97) == 29.97
        assert parse_frame_rate(60.0) == 60.0

    def test_malicious_code_injection(self):
        # Payloads that would execute code if eval() were used
        malicious_payloads = [
            '__import__("os").system("id")',
            'eval("1+1")',
            '[x for x in ().__class__.__bases__[0].__subclasses__() if x.__name__ == "BuiltinImporter"]',
            'open("/etc/passwd").read()',
            '__builtins__.__import__("sys").exit(1)'
        ]
        for payload in malicious_payloads:
            # Must safely return default (30.0) without raising exception or executing code
            result = parse_frame_rate(payload, default=30.0)
            assert result == 30.0

    def test_invalid_edge_cases(self):
        assert parse_frame_rate(None, default=24.0) == 24.0
        assert parse_frame_rate("", default=30.0) == 30.0
        assert parse_frame_rate("   ", default=30.0) == 30.0
        assert parse_frame_rate("0/0", default=30.0) == 30.0
        assert parse_frame_rate("30/0", default=30.0) == 30.0
        assert parse_frame_rate("not_a_number", default=25.0) == 25.0
        assert parse_frame_rate({}, default=30.0) == 30.0


class TestPathTraversalSecurity:
    """Kiểm tra cơ chế phòng vệ chống tấn công đọc file bất kỳ (Arbitrary File Read / LFI)."""

    def test_path_traversal_rejection(self):
        attack_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "../../../../etc/passwd",
            os.path.expanduser("~/.ssh/id_rsa"),
            os.path.expanduser("~/.bashrc"),
            "/var/log/system.log",
            "../../../Applications",
        ]
        for bad_path in attack_paths:
            ok, msg = is_safe_path(bad_path)
            assert ok is False, f"Lỗ hổng: {bad_path} không bị chặn!"
            assert "Truy cập bị từ chối" in msg or "không hợp lệ" in msg

    def test_null_byte_injection(self):
        null_byte_paths = [
            os.path.join(tempfile.gettempdir(), "test.mp4\x00.exe"),
            "~/Downloads/video.mp4\x00/../../etc/passwd"
        ]
        for bad_path in null_byte_paths:
            ok, msg = is_safe_path(bad_path)
            assert ok is False
            assert "null byte" in msg

    def test_disallowed_extension_rejection(self):
        # File located inside allowed root (temp dir), but with dangerous extension
        bad_ext_file = os.path.join(tempfile.gettempdir(), "exploit.sh")
        ok, msg = is_safe_path(bad_ext_file, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS)
        assert ok is False
        assert "Định dạng tệp không được phép" in msg

        bad_py_file = os.path.join(tempfile.gettempdir(), "script.py")
        ok, msg = is_safe_path(bad_py_file, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS)
        assert ok is False

    def test_allowed_roots_contain_expected_dirs(self):
        roots = get_allowed_roots()
        downloads = os.path.realpath(os.path.expanduser("~/Downloads"))
        temp_dir = os.path.realpath(tempfile.gettempdir())
        workspace = os.path.realpath(WORKSPACE_ROOT)

        assert downloads in roots
        assert temp_dir in roots
        assert workspace in roots

    def test_safe_paths_accepted(self):
        # Safe temp file
        safe_temp_video = os.path.join(tempfile.gettempdir(), "safe_preview.mp4")
        ok, resolved = is_safe_path(safe_temp_video, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS)
        assert ok is True
        assert resolved.startswith(os.path.realpath(tempfile.gettempdir()))

        # Safe workspace file
        safe_ws_file = os.path.join(WORKSPACE_ROOT, "README.md")
        ok, resolved = is_safe_path(safe_ws_file)
        assert ok is True
        assert resolved.startswith(os.path.realpath(WORKSPACE_ROOT))

    def test_must_exist_validation(self):
        non_existent = os.path.join(tempfile.gettempdir(), "this_file_does_not_exist_987654.mp4")
        ok, msg = is_safe_path(non_existent, allowed_extensions=ALLOWED_MEDIA_EXTENSIONS, must_exist=True)
        assert ok is False
        assert "Tệp không tồn tại" in msg
