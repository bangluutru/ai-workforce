#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""auditor_common.py - Hàm dùng chung cho các script App Auditor."""

import re
import sys
import urllib.parse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE = SKILL_DIR.parent.parent.parent
VENV_PY = WORKSPACE / ".venv" / "bin" / "python"


def require_playwright():
    """Trả về sync_playwright hoặc thoát mã 2 với hướng dẫn dùng .venv (không fallback âm thầm)."""
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        print(f"❌ LỖI: Python hiện tại ({sys.executable}) không có Playwright.", file=sys.stderr)
        print(f"   Chạy bằng Python của repo: {VENV_PY} .agents/skills/app-auditor/scripts/<script>.py ...", file=sys.stderr)
        print("   Nếu .venv chưa có: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt "
              "&& .venv/bin/python -m playwright install chromium", file=sys.stderr)
        sys.exit(2)


def is_local_url(url: str) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return host in ("localhost", "127.0.0.1", "::1", "0.0.0.0") or host.endswith(".localhost") or host.endswith(".test")


def sanitize_slug(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", text.strip("/").replace("/", "_"))
    return clean if clean else "root"


# Đo tràn ngang theo clientWidth (KHÔNG dùng window.innerWidth: với is_mobile, Chromium nới innerWidth theo nội dung
# nên tràn ngang bị che mất). Ngoài ra liệt kê phần tử vượt mép phải/trái = nội dung bị cắt dù không có thanh cuộn.
OVERFLOW_JS = """(configuredWidth) => {
  const de = document.documentElement;
  const cw = Math.min(de.clientWidth, configuredWidth || de.clientWidth);
  const sw = de.scrollWidth;
  const offenders = [], clipped = [];
  const seen = new Set();
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.position === 'fixed') continue;
    if (r.right > cw + 2 || r.left < -2) {
      // bỏ qua nếu cha đã được ghi nhận (chỉ báo phần tử ngoài cùng)
      let p = el.parentElement, dup = false;
      while (p) { if (seen.has(p)) { dup = true; break; } p = p.parentElement; }
      if (dup) continue;
      seen.add(el);
      let clipper = null, a = el.parentElement;
      while (a && a !== document.body) {
        const ox = getComputedStyle(a).overflowX;
        if (ox === 'hidden' || ox === 'clip') { clipper = a; break; }
        a = a.parentElement;
      }
      const item = {tag: el.tagName.toLowerCase(), id: el.id || '', className: String(el.className || '').slice(0, 50),
                    text: (el.innerText || '').trim().slice(0, 60), left: Math.round(r.left), right: Math.round(r.right),
                    width: Math.round(r.width), overflowAmount: Math.round(Math.max(r.right - cw, -r.left))};
      (clipper || sw <= cw + 1 ? clipped : offenders).push(item);
      if (offenders.length + clipped.length >= 10) break;
    }
  }
  return {scrollWidth: sw, clientWidth: cw, innerWidth: window.innerWidth, hasOverflow: sw > cw + 1,
          overflowAmount: Math.max(0, sw - cw), offenders, clipped};
}"""

BROKEN_IMG_JS = """() => [...document.images]
  .filter(i => i.complete && i.naturalWidth === 0 && (i.currentSrc || i.src))
  .map(i => ({src: i.currentSrc || i.src, alt: i.getAttribute('alt')}))"""
