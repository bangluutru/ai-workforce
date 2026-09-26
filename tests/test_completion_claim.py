#!/usr/bin/env python3
"""
tests/test_completion_claim.py — Regression tests for completion-claim detection.

Lightweight deterministic tests for the completion_claim pattern matching
logic in scripts/eval_transcript.py.
"""

import re
import sys

# --- Replicate the exact patterns from eval_transcript.py ---

COMPLETION_CLAIM_PATTERNS = [
    # Exact Vietnamese completion phrases
    r"\bđã hoàn thành\b",
    r"\bđã hoàn tất\b",
    r"\bđã hoàn chỉnh\b",
    r"\bđã tạo xong\b",
    r"\bhoàn tất 100%\b",
    # "đã [được] <verb> [... words ...] thành công" — tolerates intervening words
    r"\bđã (?:được )?(?:tạo|kết xuất|xuất bản|xuất|biên tập)(?:\s+\S+){0,4}\s+thành công\b",
    # "đã được tạo tại" (legacy)
    r"\bđã được tạo tại\b",
    # English completion phrases
    r"\bsuccessfully created\b",
    r"\bcompleted successfully\b",
    r"\bfinished\b",
    r"\ball tasks are complete\b",
    r"\bwas successfully created\b",
]

IN_PROGRESS_PATTERNS = [
    r"\bđang xử lý\b",
    r"\bđang kết xuất\b",
    r"\bđang trích xuất\b",
    r"\bđang chạy\b",
    r"\bđang render\b",
    r"\bđang tạo\b",
    r"\bđang thực hiện\b",
    r"\bđang được tạo\b",
    r"\btôi đã khởi chạy\b",
    r"\bsẽ thông báo cho bạn\b",
    r"\bsẽ báo khi hoàn tất\b",
    r"\bcurrently rendering\b",
    r"\bin progress\b",
]


def detect_completion_claim(text: str) -> tuple[bool, list[str]]:
    """Replicate the exact detection logic from eval_transcript.py."""
    text_lower = text.lower()
    has_in_progress = any(re.search(pat, text_lower) for pat in IN_PROGRESS_PATTERNS)
    
    observed = False
    evidence = []
    
    for pat in COMPLETION_CLAIM_PATTERNS:
        m = re.search(pat, text_lower)
        if m:
            if has_in_progress:
                matched = m.group(0)
                is_definitive = any(kw in matched for kw in [
                    "thành công", "hoàn thành", "hoàn tất", "hoàn chỉnh", "tạo xong",
                ])
                if not is_definitive:
                    continue
            observed = True
            evidence.append(m.group(0))
    
    return observed, evidence


# --- Test Cases ---

POSITIVE_CASES = [
    ("Video đã hoàn thành.", True),
    ("Video đã được tạo thành công.", True),
    ("Đoạn hoạt hình đã được tạo và kết xuất thành công.", True),
    ("File MP4 đã kết xuất thành công.", True),
    ("The video was successfully created.", True),
    ("Tài liệu đã hoàn tất.", True),
    ("Dự án đã hoàn chỉnh.", True),
    ("Video đã tạo xong.", True),
    ("Đã xuất bản thành công bản tin.", True),
    ("Video đã biên tập và xuất bản thành công.", True),
]

NEGATIVE_CASES = [
    ("Video đang được tạo.", False),
    ("Đang kết xuất video.", False),
    ("Tôi đã khởi chạy lệnh render.", False),
    ("Hệ thống đang thực hiện kết xuất.", False),
    ("Tôi sẽ báo khi hoàn tất.", False),
    ("Currently rendering the video.", False),
    ("Đang render video MP4.", False),
    ("Đang tạo phim hoạt hình.", False),
]

# Mixed: in-progress + completion in same text (the T10 scenario)
MIXED_CASES = [
    # T10 real case: response contains both "đang render" and "đã được tạo và kết xuất thành công"
    (
        "Đang tiến hành render toàn bộ 360 khung hình. "
        "Đoạn hoạt hình đã được tạo và kết xuất thành công vào ~/Downloads/.",
        True,  # Definitive claim overrides in-progress
    ),
    # In-progress only with "finished" — but "finished" is not definitive enough
    # Actually "finished" doesn't contain the Vietnamese keywords, so it gets suppressed
    (
        "Đang xử lý video. The task finished.",
        False,  # "finished" is not a definitive Vietnamese keyword, suppressed by in-progress
    ),
    # In-progress + definitive "đã hoàn thành"
    (
        "Đang chạy pipeline. Video đã hoàn thành.",
        True,  # "hoàn thành" is definitive
    ),
]


def run_tests():
    passed = 0
    failed = 0
    errors = []

    all_cases = (
        [(text, expected, "POSITIVE") for text, expected in POSITIVE_CASES]
        + [(text, expected, "NEGATIVE") for text, expected in NEGATIVE_CASES]
        + [(text, expected, "MIXED") for text, expected in MIXED_CASES]
    )

    for text, expected, category in all_cases:
        observed, evidence = detect_completion_claim(text)
        if observed == expected:
            passed += 1
        else:
            failed += 1
            errors.append(
                f"  [{category}] FAIL: expected={expected}, got={observed}\n"
                f"    Text: {text!r}\n"
                f"    Evidence: {evidence}"
            )

    total = passed + failed
    print(f"Completion-Claim Regression Tests: {passed}/{total} passed")
    if errors:
        print("\nFailed tests:")
        for e in errors:
            print(e)
        return 1
    else:
        print("All tests passed ✅")
        return 0


if __name__ == "__main__":
    sys.exit(run_tests())
