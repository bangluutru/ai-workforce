"""Tests cho mixed_lang: lời Việt chèn từ Anh (R7: engine _shared/media/mixed_lang.py)."""
import sys
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parent.parent.parent / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED))
import bootstrap  # noqa: F401,E402
import mixed_lang  # noqa: E402
from creative.storyboard_validator import validate_storyboard  # noqa: E402


def langs(t, **kw):
    return [(l, s) for l, s in mixed_lang.split_mixed(t, **kw)]


def test_pure_vietnamese_has_no_english():
    for t in ["Chúng tôi giúp bạn bán hàng tốt hơn.", "Ban đầu hơi khó, con cần thời gian.", "Gói 15 ngày."]:
        assert not mixed_lang.has_english(t), t


def test_english_words_detected_and_split():
    segs = langs("Chúng tôi dùng Facebook và YouTube cho marketing.")
    assert segs == [("vi", "Chúng tôi dùng"), ("en", "Facebook"), ("vi", "và"), ("en", "YouTube"),
                    ("vi", "cho"), ("en", "marketing.")]


def test_adjacent_english_merge_and_acronym_and_alnum():
    segs = langs("Hãy download file SEO trên iPhone 4K.")
    assert ("en", "download file SEO") in segs or ("en", "download file") in segs
    assert any(l == "en" and "iPhone" in s for l, s in segs)
    assert mixed_lang._spell_acronyms("SEO") == "S. E. O."


def test_overrides():
    assert mixed_lang.has_english("Xin chào Zalo", english_words=["Zalo"])
    assert not mixed_lang.has_english("Công ty Chotto", vietnamese_words=["Chotto"])


def test_collision_words_are_english():
    assert mixed_lang.has_english("Mở chat với khách")


def test_validation_of_new_audio_keys():
    base = {"schema_version": "2.0", "project_id": "x", "fps": 30, "resolution": {"width": 720, "height": 720},
            "scenes": [{"id": "s1", "type": "motion_graphics", "duration_seconds": 3, "visual_goal": "g",
                        "narration": "Xin chào Facebook"}]}
    ok, errs = validate_storyboard({**base, "audio": {"mode": "narration", "mixed_english": "auto", "english_words": ["Zalo"]}})
    assert ok, errs
    for bad in ({"mixed_english": "maybe"}, {"pronunciations": ["a"]}, {"english_words": "Zalo"}, {"vietnamese_words": [1]}):
        ok, errs = validate_storyboard({**base, "audio": {"mode": "narration", **bad}})
        assert not ok and errs


def test_synthesize_mixed_real(tmp_path):
    import dub_engine
    try:
        r, _ = dub_engine.synthesize([{"key": "p", "text": "Hello."}], "en", None, "female", str(tmp_path / "p_en"),
                                     takes=1, verify=False, log=lambda *_: None)
        r2, _ = dub_engine.synthesize([{"key": "p", "text": "Xin chào."}], "vi", None, "female", str(tmp_path / "p_vi"),
                                      takes=1, verify=False, log=lambda *_: None)
        if "p" not in r or "p" not in r2:
            pytest.skip("Engine TTS vi/en không trả kết quả")
    except Exception as e:
        pytest.skip(f"Engine TTS không khả dụng: {e}")
    res, _ = mixed_lang.synthesize_mixed([{"key": "a", "text": "Chúng tôi dùng Facebook cho marketing."}],
                                         work=str(tmp_path / "w"), takes=1, verify=False, log=lambda *_: None)
    a = res["a"]
    assert Path(a["path"]).is_file() and a["dur"] > 1.5
    assert [s["lang"] for s in a["segments"]] == ["vi", "en", "vi", "en"]


def test_phonetic_respell_and_unknown():
    out, unk = mixed_lang.phonetic_respell("Dùng Facebook và YouTube cho marketing, SEO.")
    assert out == "Dùng phây búc và diu túp cho ma két ting, ét i âu." and unk == []
    out, unk = mixed_lang.phonetic_respell("Dùng blockchain nhé", {"blockchain": "bờ lốc chên"})
    assert "bờ lốc chên" in out and unk == []
    out, unk = mixed_lang.phonetic_respell("Dùng blockchain nhé")
    assert unk == ["blockchain"]
    assert mixed_lang.phonetic_respell("Hoàn toàn tiếng Việt.")[0] == "Hoàn toàn tiếng Việt."


def test_default_is_native_vieneu_no_rewrite():
    from creative.audio_track import parse_audio_spec
    sb = {"audio": {"mode": "narration"}}
    assert parse_audio_spec(sb).mixed_english == "off"
    assert parse_audio_spec({"audio": {"mode": "narration", "mixed_english": "phonetic"}}).mixed_english == "phonetic"
