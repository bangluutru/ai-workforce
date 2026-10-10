"""Phase 6: hồi quy cho lỗi bố cục hf-root và prop logo_url của preset 06."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".agents" / "skills" / "_shared"))
import bootstrap  # noqa: F401,E402
from creative.presets.registry import render_preset_html  # noqa: E402


def test_hf_root_is_flex_centered_for_body_centered_presets():
    for name in ("01_fade_in", "06_logo_reveal", "07_product_spotlight", "10_cta_reveal"):
        html = render_preset_html(name, props={}, width=1080, height=1080, duration=5)
        root = html.split('id="hf-root"', 1)[1].split(">", 1)[0]
        assert "display:flex" in root and "align-items:center" in root and "justify-content:center" in root, name


def test_logo_reveal_supports_logo_url_and_keeps_default():
    with_logo = render_preset_html("06_logo_reveal", props={"logo_url": "data:image/png;base64,AAAA"}, width=1920, height=1080, duration=5)
    assert "data:image/png;base64,AAAA" in with_logo
    assert "props.logo_url" in with_logo and "props.logo_char" in with_logo


def test_fade_in_title_uses_text_color_not_hardcoded_white():
    html = render_preset_html("01_fade_in", props={}, width=1280, height=720, duration=5)
    assert "linear-gradient(180deg, #FFFFFF 40%" not in html
