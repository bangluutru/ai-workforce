#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creative Studio 2.1, Phase 2: kiểm thử Audio Integration (kịch bản A-J của directive).

Các ca cần giọng nói dùng TTS offline THẬT (VieNeu/Kokoro) và đo âm thanh THẬT bằng ffmpeg.
Nếu engine không có trên máy → pytest.skip có lý do (hiển thị SKIPPED, KHÔNG tính là PASS).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SHARED = ROOT / ".agents" / "skills" / "_shared"
sys.path.insert(0, str(SHARED))
import bootstrap  # noqa: F401,E402

from creative.audio_track import parse_audio_spec, spoken_text, validate_audio_spec  # noqa: E402
from creative.storyboard_renderer import StoryboardRenderer  # noqa: E402
from creative.storyboard_validator import validate_storyboard  # noqa: E402
from ffmpeg_tools import ffmpeg_bin, ffprobe_bin, loudness  # noqa: E402

_ENGINE_OK = {}


def _need_engine(lang: str, tmp_path_factory):
    """Skip có lý do nếu engine TTS của ngôn ngữ này không chạy được trên máy."""
    if lang not in _ENGINE_OK:
        import dub_engine
        texts = {"vi": "Xin chào các bạn.", "en": "Hello everyone.", "ja": "こんにちは。"}
        try:
            res, _ = dub_engine.synthesize([{"key": "p", "text": texts[lang]}], lang, None, "female",
                                           str(tmp_path_factory.mktemp(f"probe_{lang}")), takes=1, verify=False,
                                           log=lambda *_: None)
            _ENGINE_OK[lang] = "p" in res
            if not _ENGINE_OK[lang]:
                _ENGINE_OK[lang] = "TTS không trả kết quả"
        except Exception as e:
            _ENGINE_OK[lang] = f"{type(e).__name__}: {e}"
    if _ENGINE_OK[lang] is not True:
        pytest.skip(f"Engine TTS '{lang}' không khả dụng trên máy này: {_ENGINE_OK[lang]}")


def _sb(scenes, audio=None, pid="audio_test"):
    sb = {
        "schema_version": "2.0", "project_id": pid, "fps": 30,
        "resolution": {"width": 720, "height": 720}, "brand_profile": "default",
        "scenes": [
            {
                "id": f"s{i + 1:02d}", "type": "motion_graphics", "duration_seconds": dur,
                "visual_goal": f"Cảnh {i + 1}", "motion": {"preset": "04_kinetic_title"},
                "props": {"title": f"Cảnh {i + 1}"},
                **({"narration": narr} if narr else {}),
            }
            for i, (dur, narr) in enumerate(scenes)
        ],
    }
    if audio is not None:
        sb["audio"] = audio
    return sb


def _render(sb, tmp_path, qa=True):
    return StoryboardRenderer().render_storyboard(sb, output_path=tmp_path / "out.mp4", work_dir=tmp_path / "work", run_qa=qa)


def _probe(path):
    out = subprocess.run([ffprobe_bin(), "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    return float(d["format"]["duration"]), [s["codec_type"] for s in d["streams"]]


@pytest.fixture(scope="module")
def bgm_file(tmp_path_factory):
    """BGM tổng hợp bằng ffmpeg (hợp âm sin) – là dữ liệu thử, không phải nhạc thật."""
    p = tmp_path_factory.mktemp("bgm") / "bgm.wav"
    subprocess.run([ffmpeg_bin(), "-y", "-v", "error", "-f", "lavfi", "-i",
                    "aevalsrc=0.3*sin(2*PI*220*t)+0.2*sin(2*PI*330*t)|0.3*sin(2*PI*220*t)+0.2*sin(2*PI*330*t):d=4",
                    "-c:a", "pcm_s16le", str(p)], check=True)
    return str(p)


# ------------------------------------------------------------------ validation (không cần TTS)
def test_validation_rejects_bad_audio_blocks():
    base = _sb([(3.0, "Xin chào")])
    bad = [
        ({"mode": "karaoke"}, "audio.mode"),
        ({"mode": "narration", "language": "fr"}, "audio.language"),
        ({"mode": "narration", "sync_policy": "magic"}, "sync_policy"),
        ({"mode": "narration", "target_lufs": 5}, "target_lufs"),
        ({"mode": "narration", "duck_level": 2}, "duck_level"),
        ({"mode": "narration_bgm"}, "bgm_path"),
        ({"mode": "bgm_only"}, "bgm_path"),
    ]
    for audio, needle in bad:
        ok, errs = validate_storyboard({**base, "audio": audio})
        assert not ok and any(needle in e for e in errs), (audio, errs)
    ok, errs = validate_storyboard({**_sb([(3.0, None)]), "audio": {"mode": "narration"}})
    assert not ok and any("narration" in e for e in errs)


def test_validation_accepts_legacy_and_valid_blocks():
    ok, errs = validate_storyboard(_sb([(3.0, "Xin chào")]))   # I: storyboard v2.0 cũ, không có audio
    assert ok, errs
    assert parse_audio_spec(_sb([(3.0, "x")])) is None
    ok, errs = validate_storyboard(_sb([(3.0, "Xin chào")], {"mode": "narration", "voice": "default"}))
    assert ok, errs
    s = parse_audio_spec(_sb([(3.0, "x")], {"narration_enabled": True, "bgm_enabled": True, "bgm_path": "a.wav"}))
    assert s.mode == "narration_bgm" and s.voice is None


def test_spoken_text_strips_subtitle_break():
    assert spoken_text("Xin chào | các bạn") == "Xin chào các bạn"
    assert validate_audio_spec({"scenes": []}) == []


# ------------------------------------------------------------------ I: tương thích ngược (render thật)
def test_I_legacy_storyboard_unchanged_behaviour(tmp_path):
    res = _render(_sb([(1.0, "Có narration nhưng không có khối audio")]), tmp_path)
    assert res.success, res.error_message
    assert res.audio_mode == "silent_default"
    assert any("không có khối 'audio'" in w for w in res.warnings)   # minh bạch, không giả vờ có tiếng
    dur, kinds = _probe(res.output_mp4)
    assert "audio" in kinds and abs(dur - 1.0) < 0.3


# ------------------------------------------------------------------ D: video không tiếng chủ đích
def test_D_silent_motion_graphics_is_intentional(tmp_path):
    res = _render(_sb([(1.0, None)], {"mode": "silent"}), tmp_path)
    assert res.success, res.error_message
    assert res.audio_mode == "silent"
    codes = {f["code"] for f in res.qa_report.technical["findings"]}
    assert "intentional_silence" in codes and "audio_too_quiet" not in codes
    assert not any("không có khối 'audio'" in w for w in res.warnings)


# ------------------------------------------------------------------ A, J: có giọng thật
def test_A_narration_only_real_voice(tmp_path, tmp_path_factory):
    _need_engine("vi", tmp_path_factory)
    res = _render(_sb([(4.0, "Chào mừng bạn đến với phòng media."), (4.0, "Tiếng Việt có dấu phát âm rõ ràng.")],
                      {"mode": "narration", "language": "vi"}), tmp_path)
    assert res.success, res.error_message
    lufs, peak = loudness(res.output_mp4)
    assert lufs is not None and -24 < lufs < -10, f"LUFS={lufs}: track không phải giọng nói đã chuẩn hóa"
    assert peak is not None and peak < -0.1
    assert res.audio_report["narration_scenes"] == 2 and res.audio_report["bgm"] is False
    assert res.qa_report.technical["verdict"] != "FAIL", res.qa_report.technical["findings"]


def test_B_narration_plus_bgm_with_ducking(tmp_path, tmp_path_factory, bgm_file):
    _need_engine("vi", tmp_path_factory)
    res = _render(_sb([(4.0, "Giọng đọc đè lên nhạc nền."), (4.0, "Nhạc nền tự hạ khi có lời.")],
                      {"mode": "narration_bgm", "bgm_path": bgm_file, "duck_level": 0.25}), tmp_path)
    assert res.success, res.error_message
    r = res.audio_report
    assert r["bgm"] is True and r["ducking"] is True and r["narration_scenes"] == 2
    lufs, _ = loudness(res.output_mp4)
    assert lufs is not None and -22 < lufs < -10


def test_C_bgm_only(tmp_path, bgm_file):
    res = _render(_sb([(2.0, None), (2.0, None)], {"mode": "bgm_only", "bgm_path": bgm_file}), tmp_path)
    assert res.success, res.error_message
    assert res.audio_report["narration_scenes"] == 0 and res.audio_report["bgm"] is True
    lufs, _ = loudness(res.output_mp4)
    assert lufs is not None and lufs > -50, "BGM-only không được im lặng"
    dur, kinds = _probe(res.output_mp4)
    assert abs(dur - 4.0) < 0.3 and "audio" in kinds


# ------------------------------------------------------------------ E, F: đồng bộ thời lượng
def test_E_long_narration_extends_scene_not_cut(tmp_path, tmp_path_factory):
    _need_engine("vi", tmp_path_factory)
    long_txt = "Đây là một câu thoại khá dài để chắc chắn rằng nó vượt quá thời lượng một giây của cảnh này."
    res = _render(_sb([(1.0, long_txt)], {"mode": "narration"}), tmp_path)
    assert res.success, res.error_message
    assert res.total_duration > 3.0, "cảnh phải được kéo dài, không cắt lời"
    ext = res.audio_report["extended_scenes"]
    assert ext and ext[0]["from"] == 1.0 and ext[0]["to"] > 3.0
    assert any("kéo dài" in w for w in res.warnings)
    dur, _ = _probe(res.output_mp4)
    assert abs(dur - res.total_duration) < 0.4


def test_E_strict_policy_returns_specific_blocker(tmp_path, tmp_path_factory):
    _need_engine("vi", tmp_path_factory)
    long_txt = "Đây là một câu thoại khá dài để chắc chắn rằng nó vượt quá thời lượng một giây của cảnh này."
    res = _render(_sb([(1.0, long_txt)], {"mode": "narration", "sync_policy": "strict"}), tmp_path)
    assert res.success is False
    assert "strict" in res.error_message and "s01" in res.error_message
    assert not (tmp_path / "out.mp4").exists()


def test_F_short_narration_keeps_scene_duration(tmp_path, tmp_path_factory):
    _need_engine("vi", tmp_path_factory)
    res = _render(_sb([(6.0, "Ngắn gọn.")], {"mode": "narration"}), tmp_path)
    assert res.success, res.error_message
    assert abs(res.total_duration - 6.0) < 1e-6 and res.audio_report["extended_scenes"] == []


# ------------------------------------------------------------------ G, H: lỗi phải lộ ra, không giả thành công
def test_G_tts_unavailable_is_blocker_not_silent_track(tmp_path, monkeypatch):
    import dub_engine

    def boom(*a, **k):
        raise RuntimeError("engine vieneu không khả dụng (giả lập)")
    monkeypatch.setattr(dub_engine, "synthesize", boom)
    res = _render(_sb([(2.0, "Xin chào")], {"mode": "narration"}), tmp_path)
    assert res.success is False
    assert "Không dùng track im lặng" in res.error_message and "giả lập" in res.error_message
    assert res.audio_mode == "narration"
    assert not (tmp_path / "out.mp4").exists()


def test_H_mux_failure_is_reported(tmp_path, tmp_path_factory, monkeypatch):
    _need_engine("vi", tmp_path_factory)
    import creative.storyboard_renderer as sr
    monkeypatch.setattr(sr, "mix_audio", lambda *a, **k: (str(tmp_path / "khong_ton_tai.wav"), {"mode": "narration"}))
    res = _render(_sb([(3.0, "Xin chào")], {"mode": "narration"}), tmp_path)
    assert res.success is False and "MP4 cuối cùng" in res.error_message


def test_missing_bgm_file_is_blocker(tmp_path, tmp_path_factory):
    res = _render(_sb([(2.0, None)], {"mode": "bgm_only", "bgm_path": str(tmp_path / "none.mp3")}), tmp_path)
    assert res.success is False and "BGM không tồn tại" in res.error_message


# ------------------------------------------------------------------ J: đa ngôn ngữ, đo âm thanh thật
@pytest.mark.parametrize("lang,text", [
    ("vi", "Quy định mới có hiệu lực từ tháng tư năm hai nghìn không trăm hai mươi bảy."),
    ("en", "The new rules take effect in April."),
    ("ja", "新しい制度は四月から始まります。"),
])
def test_J_multilingual_real_voice(tmp_path, tmp_path_factory, lang, text):
    _need_engine(lang, tmp_path_factory)
    res = _render(_sb([(5.0, text)], {"mode": "narration", "language": lang}), tmp_path, qa=False)
    assert res.success, res.error_message
    lufs, _ = loudness(res.output_mp4)
    assert lufs is not None and -24 < lufs < -10, f"{lang}: LUFS={lufs}"
    assert res.audio_report["narration_scenes"] == 1
