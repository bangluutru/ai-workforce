#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
open_media.py — Ảnh có GIẤY PHÉP RÕ RÀNG, không cần API key: Wikimedia Commons → Openverse.

Dùng khi không có PEXELS_API_KEY / PIXABAY_API_KEY. Mỗi ảnh trả kèm license + tác giả + link nguồn
để ghi vào credits.txt (CC BY / BY-SA bắt buộc ghi công). Bỏ qua NC/ND (không dùng thương mại/không phái sinh).
Ảnh tĩnh được scene_builder biến thành chuyển động Ken Burns.

    python3 open_media.py --query "espresso pouring" --out /tmp/x.jpg
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

UA = "AIWF-video-studio/2.0 (https://github.com/bangluutru; offline video tool)"
BAD_TITLE = re.compile(r"\b(map|logo|diagram|chart|flag|coat of arms|icon|plan|graph|seal|signature|svg|scan|document|page)\b", re.I)
OK_LICENSE = re.compile(r"^(cc0|public domain|pd|cc[ -]?by(?:[ -]sa)?(?:[ -][\d.]+)?)", re.I)


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def search_wikimedia(query, min_width=1600, landscape=True, limit=12):
    q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {query}",
                                "gsrnamespace": 6, "gsrlimit": limit, "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 2560})
    try:
        d = json.loads(_get("https://commons.wikimedia.org/w/api.php?" + q))
    except Exception:
        return []
    out = []
    for p in sorted((d.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = _clean(md.get("LicenseShortName", {}).get("value", ""))
        w, h = ii.get("width", 0), ii.get("height", 0)
        if not OK_LICENSE.match(lic) or w < min_width or ii.get("mime") not in ("image/jpeg", "image/png") or BAD_TITLE.search(p.get("title", "")):
            continue
        if landscape and w < h * 1.15:
            continue
        out.append({"url": ii.get("thumburl") or ii["url"], "width": w, "height": h, "license": lic, "author": _clean(md.get("Artist", {}).get("value", ""))[:80],
                    "title": p.get("title", "").replace("File:", ""), "page": ii.get("descriptionurl", ""), "source": "Wikimedia Commons"})
    return out


def search_openverse(query, min_width=1200, landscape=True, limit=20):
    q = urllib.parse.urlencode({"q": query, "license_type": "commercial,modification", "page_size": limit, "size": "large"})
    try:
        d = json.loads(_get("https://api.openverse.org/v1/images/?" + q))
    except Exception:
        return []
    out = []
    for r in d.get("results", []):
        w, h = r.get("width") or 0, r.get("height") or 0
        if w < min_width or (landscape and w < h * 1.15) or BAD_TITLE.search(r.get("title") or ""):
            continue
        lic = f"CC {r.get('license', '').upper()} {r.get('license_version', '')}".strip()
        out.append({"url": r["url"], "width": w, "height": h, "license": lic, "author": (r.get("creator") or "")[:80], "title": r.get("title") or "",
                    "page": r.get("foreign_landing_url", ""), "source": f"Openverse/{r.get('source', '')}"})
    return out


def find_image(query, out_path, landscape=True, skip_urls=()):
    """Tải ảnh tốt nhất cho `query` vào out_path. Trả về dict credit hoặc None."""
    for cands in (search_wikimedia(query, landscape=landscape), search_openverse(query, landscape=landscape)):
        for c in cands:
            if c["url"] in skip_urls:
                continue
            try:
                data = _get(c["url"], timeout=60)
                if len(data) < 20000:
                    continue
                os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
                open(out_path, "wb").write(data)
                return {**c, "path": out_path, "query": query}
            except Exception:
                continue
    return None


def credit_line(c):
    who = f" — {c['author']}" if c.get("author") else ""
    return f"\"{c.get('title', '')}\"{who} · {c.get('license', '')} · {c.get('source', '')} · {c.get('page', '')}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True); ap.add_argument("--out", required=True); ap.add_argument("--portrait", action="store_true")
    a = ap.parse_args()
    r = find_image(a.query, a.out, landscape=not a.portrait)
    print(json.dumps(r, ensure_ascii=False, indent=2) if r else "null")
    sys.exit(0 if r else 1)
