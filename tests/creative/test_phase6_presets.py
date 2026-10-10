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


# ---------------------------------------------------------------------------
# P3: prop rỗng / thiếu không được rò chữ demo của preset vào video thật
# ---------------------------------------------------------------------------
import re  # noqa: E402

import pytest  # noqa: E402
from creative.presets.registry import PRESET_REGISTRY, missing_demo_props  # noqa: E402

_PRESET_DIR = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "_shared" / "creative" / "presets"


def test_p3_no_template_falls_back_to_hardcoded_text_on_empty_prop():
    """Moi dong gan chu phai dung pv(); khong con textContent = props.x || chu mau."""
    for f in sorted(_PRESET_DIR.glob("*.html")):
        t = f.read_text(encoding="utf-8")
        assert "function pv(" in t or "const pv" in t, f.name
        assert not re.search(r"textContent\s*=\s*props\.\w+\s*\|\|", t), f.name
    logo = (_PRESET_DIR / "06_logo_reveal.html").read_text(encoding="utf-8")
    assert "pv('brand_name')" in logo


def test_p3_explicit_empty_prop_is_kept_in_merged_props_not_default():
    html = render_preset_html("10_cta_reveal", props={"domain": ""}, width=1280, height=720, duration=5)
    assert "aiworkforce.vn" not in html


def test_p3_missing_demo_props_reports_text_and_data_separately():
    r = missing_demo_props("10_cta_reveal", {"domain": ""})
    assert "domain" not in r["text"] and "domain" not in r["data"]
    r2 = missing_demo_props("10_cta_reveal", {})
    assert "domain" in r2["text"]
    assert set(r2) == {"text", "data"}


def test_p3_browser_empty_prop_renders_empty_and_missing_uses_merged_default():
    pw = pytest.importorskip("playwright.sync_api")
    try:
        with pw.sync_playwright() as p:
            b = p.chromium.launch()
            out = {}
            for tag, props in (("empty", {"domain": ""}), ("missing", {})):
                html = render_preset_html("10_cta_reveal", props=props, width=1280, height=720, duration=5)
                page = b.new_page()
                page.set_content(html)
                page.wait_for_timeout(300)
                out[tag] = page.evaluate("document.getElementById(\"domain\").textContent")
            b.close()
    except Exception as e:  # chromium chua cai
        pytest.skip("khong chay duoc chromium: %s" % e)
    assert "aiworkforce.vn" not in out["empty"]
    assert "aiworkforce.vn" in out["missing"]
