"""Nối inspect_docx --rules vào các skill: luật khớp đầu ra thật của engine, SKILL.md trỏ đúng tệp luật.

Chạy: .venv/bin/python -m pytest tests/test_docx_rules_wiring.py -q
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
SHARED_DOCX = SKILLS / "_shared" / "docx"
INSPECT = SHARED_DOCX / "inspect_docx.py"
LEGAL = SHARED_DOCX / "legal_report.py"
RULES_DIR = SHARED_DOCX / "rules"

REPORT_MD = """# Báo cáo tư vấn thử nghiệm

## 1. Kết luận
Doanh nghiệp được phép thực hiện theo Luật số 122/2025/QH15 [XÁC ĐỊNH].

> [!WARNING]
> Cần đối chiếu nguyên văn [CẦN XÁC MINH: chưa có bản chính thức].

## 2. Phân tích
- Ý một
- Ý hai

| Văn bản | Điều |
|---|---|
| Luật A | 5 |

### 2.1 Chi tiết
Đoạn văn có **đậm** và *nghiêng*.
"""


def run(args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def build_legal(tmp_path, md=REPORT_MD, name="r"):
    src = tmp_path / f"{name}.md"
    src.write_text(md, encoding="utf-8")
    out = tmp_path / f"{name}.docx"
    res = run([LEGAL, "--input", src, "--output", out])
    assert res.returncode == 0, res.stderr
    return out


@pytest.mark.parametrize("rules", ["legal_report_vn.rules.json", "legal_report_jp.rules.json"])
def test_rules_pass_on_real_legal_report_output(tmp_path, rules):
    docx = build_legal(tmp_path)
    res = run([INSPECT, docx, "--rules", RULES_DIR / rules])
    assert res.returncode == 0, res.stdout + res.stderr
    assert "RULES PASS" in res.stdout


def test_vn_rules_catch_em_dash_and_placeholder_jp_allows_em_dash(tmp_path):
    docx = build_legal(tmp_path, REPORT_MD + "\nChưa điền {{ten_khach}} — xem lại.\n", name="bad")
    vn = run([INSPECT, docx, "--rules", RULES_DIR / "legal_report_vn.rules.json"])
    assert vn.returncode == 1
    assert "RULE no_placeholders:" in vn.stdout and "RULE forbid.em_dash:" in vn.stdout
    jp = run([INSPECT, docx, "--rules", RULES_DIR / "legal_report_jp.rules.json"])
    assert jp.returncode == 1 and "forbid.em_dash" not in jp.stdout  # JP chỉ còn bắt placeholder


def test_rule_files_are_valid_known_rules():
    sys.path.insert(0, str(SHARED_DOCX))
    from inspect_docx import RULE_KEYS
    files = sorted(RULES_DIR.glob("*.rules.json"))
    assert files
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        assert set(data) <= RULE_KEYS, f"{f.name}: luật lạ {set(data) - RULE_KEYS}"


def test_skill_md_references_existing_rule_files():
    """Mọi `--rules <đường dẫn>` trong SKILL.md phải trỏ tới tệp tồn tại, và mọi skill gọi inspect_docx phải khai báo engine."""
    pat = re.compile(r"inspect_docx\.py[^\n]*?--rules\s+(\S+)")
    seen = 0
    for md in SKILLS.glob("*/SKILL.md"):
        text = md.read_text(encoding="utf-8")
        for m in pat.finditer(text):
            ref = m.group(1).strip("`'\"")
            if "<" in ref:
                continue
            seen += 1
            target = (ROOT / ref) if "/" in ref else (RULES_DIR / ref)  # tên trần = tệp trong _shared/docx/rules/
            assert target.is_file(), f"{md.parent.name}: --rules trỏ tới tệp không có: {ref}"
        if "inspect_docx.py" in text:
            assert "`docx.inspect`" in text, f"{md.parent.name}: dùng inspect_docx nhưng thiếu dòng docx.inspect trong mục Engine dùng chung"
    assert seen >= 2
