"""Luật R7 — tái sử dụng engine dùng chung: registry hợp lệ, repo sạch, bộ kiểm tra bắt được vi phạm."""
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(ROOT / "scripts"))
checker = importlib.import_module("check_shared_reuse")


def test_registry_modules_exist_and_signatures_compile():
    import re
    reg = json.loads((SHARED / "engines.json").read_text(encoding="utf-8"))
    ids = [e["id"] for e in reg["engines"]]
    assert len(ids) == len(set(ids)), "id engine bị trùng"
    for e in reg["engines"]:
        assert (SHARED / e["module"]).exists(), f"{e['id']}: thiếu module {e['module']}"
        assert e.get("signatures"), f"{e['id']}: cần ít nhất một signature để phát hiện viết lại"
        for s in e["signatures"]:
            re.compile(s)
        for a in e.get("allow", []):
            assert (SHARED / a).exists(), f"{e['id']}: allow trỏ tới file không tồn tại {a}"
    assert any(b["id"] == "edge-tts" for b in reg["banned"])


def test_engines_md_lists_every_engine():
    reg = json.loads((SHARED / "engines.json").read_text(encoding="utf-8"))
    md = (SHARED / "ENGINES.md").read_text(encoding="utf-8")
    for e in reg["engines"]:
        assert f"`{e['id']}`" in md, f"ENGINES.md thiếu {e['id']}"


def test_repo_has_no_r7_fail():
    fails = [f for f in checker.scan() if f["level"] == "FAIL"]
    assert not fails, json.dumps(fails, ensure_ascii=False, indent=2)


@pytest.fixture
def fake_ws(tmp_path, monkeypatch):
    skills = tmp_path / ".agents" / "skills"
    shared = skills / "_shared"
    (shared / "media").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (shared / "media" / "tts.py").write_text("def synthesize_batch(items):\n    return items\n", encoding="utf-8")
    (shared / "engines.json").write_text(json.dumps({
        "banned": [{"id": "edge-tts", "patterns": ["\\bedge_tts\\b"], "reason": "x", "replacement": "y"}],
        "engines": [{"id": "media.tts", "module": "media/tts.py", "signatures": ["^\\s*def synthesize_batch\\("]}],
    }), encoding="utf-8")
    for name, val in (("WORKSPACE", tmp_path), ("SKILLS", skills), ("SHARED", shared),
                      ("REGISTRY", shared / "engines.json")):
        monkeypatch.setattr(checker, name, val)
    return skills


def _codes(findings):
    return sorted({f["code"] for f in findings if f["level"] == "FAIL"})


def test_detects_copy_rewrite_ban_and_asset(fake_ws):
    body = "# helper dùng chung\n" + "x = 1\n" * 60
    for sk in ("skill-a", "skill-b"):
        (fake_ws / sk / "scripts").mkdir(parents=True)
        (fake_ws / sk / "scripts" / "helper.py").write_text(body, encoding="utf-8")
    (fake_ws / "skill-a" / "scripts" / "voice.py").write_text(
        "import edge_tts\n\ndef synthesize_batch(items):\n    return []\n", encoding="utf-8")
    font = bytes(range(256)) * 4
    for sk in ("skill-a", "skill-b"):
        (fake_ws / sk / "fonts").mkdir()
        (fake_ws / sk / "fonts" / "F.ttf").write_bytes(font)
    assert _codes(checker.scan()) == ["R7-ASSET", "R7-BAN", "R7-DUP", "R7-SIG"]


def test_clean_skill_using_shared_engine_passes(fake_ws):
    (fake_ws / "skill-a" / "scripts").mkdir(parents=True)
    (fake_ws / "skill-a" / "scripts" / "run.py").write_text(
        "import bootstrap\nfrom tts import synthesize_batch\nprint(synthesize_batch([1]))\n", encoding="utf-8")
    assert _codes(checker.scan()) == []
