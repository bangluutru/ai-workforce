#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPUB Document Parser for EJV Translate.

Extracts structured document blocks (headings, paragraphs, lists, quotes) from EPUB e-books
while preserving structural metadata (spine order, HTML file paths, CSS classes, element indices,
and Table of Contents) for 100% faithful layout reconstruction.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


import re as _re_txt


def _text(el):
    """Chữ của một phần tử HTML, GIỮ khoảng trắng giữa các thẻ con.
    get_text(strip=True) nối "<i>Farnam Street</i> is" thành "Farnam Streetis" (43 lỗi trong bản dịch thật)."""
    t = el.get_text(" ", strip=True)
    t = _re_txt.sub(r"\s+", " ", t)
    return _re_txt.sub(r"\s+([,.;:!?…)\]’”%])", r"\1", t).replace("( ", "(").replace("“ ", "“").strip()

def table_grid(table) -> List[List[str]]:
    """Ô của một <table> (bỏ hàng của bảng lồng), đệm cho đủ số cột."""
    rows = []
    for tr in table.find_all("tr"):
        if tr.find_parent("table") is not table:
            continue
        rows.append([_text(c) for c in tr.find_all(["td", "th"], recursive=False)])
    width = max((len(r) for r in rows), default=0)
    return [r + [""] * (width - len(r)) for r in rows if r]


def epub_drm_reason(z: zipfile.ZipFile) -> Optional[str]:
    """EPUB có DRM? (rights.xml, hoặc encryption.xml mã hoá nội dung — bỏ qua làm rối font IDPF/Adobe)."""
    names = set(z.namelist())
    if "META-INF/rights.xml" in names:
        return "META-INF/rights.xml"
    if "META-INF/encryption.xml" not in names:
        return None
    try:
        root = ElementTree.fromstring(z.read("META-INF/encryption.xml"))
    except ElementTree.ParseError:
        return "META-INF/encryption.xml (không đọc được)"
    ns = "{http://www.w3.org/2001/04/xmlenc#}"
    for ed in root.iter(f"{ns}EncryptedData"):
        m = ed.find(f"{ns}EncryptionMethod")
        alg = m.get("Algorithm", "") if m is not None else ""
        ref = ed.find(f".//{ns}CipherReference")
        uri = (ref.get("URI", "") if ref is not None else "").lower()
        if alg in ("http://www.idpf.org/2008/embedding", "http://ns.adobe.com/pdf/enc#RC") or \
                uri.endswith((".ttf", ".otf", ".woff", ".woff2")):
            continue
        return f"META-INF/encryption.xml ({uri or 'nội dung'})"
    return None


class EpubDRMError(RuntimeError):
    pass


def extract_epub_metadata_and_spine(z: zipfile.ZipFile) -> Tuple[str, str, Dict[str, str], List[str], List[Dict[str, str]]]:
    """Extract container info, OPF path, manifest, spine items, and TOC entries from EPUB."""
    # 1. Locate rootfile from META-INF/container.xml
    try:
        container_xml = z.read("META-INF/container.xml")
        container = ElementTree.fromstring(container_xml)
        rootfile_elem = container.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
        if rootfile_elem is None or "full-path" not in rootfile_elem.attrib:
            raise ValueError("Invalid META-INF/container.xml: rootfile full-path not found")
        opf_path = rootfile_elem.attrib["full-path"]
    except Exception as e:
        log.warning(f"Failed to parse container.xml: {e}. Falling back to search for .opf")
        opf_candidates = [n for n in z.namelist() if n.endswith(".opf")]
        if not opf_candidates:
            raise FileNotFoundError("No .opf file found in EPUB archive")
        opf_path = opf_candidates[0]

    opf_dir = str(Path(opf_path).parent)
    if opf_dir == ".":
        opf_dir = ""

    # 2. Parse OPF
    opf_content = z.read(opf_path)
    opf_soup = BeautifulSoup(opf_content, "xml")

    # Manifest map: id -> href
    manifest: Dict[str, str] = {}
    toc_href: Optional[str] = None
    for item in opf_soup.find_all("item"):
        item_id = item.get("id")
        href = item.get("href")
        media_type = item.get("media-type", "")
        if not item_id or not href:
            continue
        
        full_href = f"{opf_dir}/{href}".lstrip("/") if opf_dir else href
        manifest[item_id] = full_href
        if media_type == "application/x-dtbncx+xml" or href.endswith(".ncx"):
            toc_href = full_href

    # Spine itemrefs
    spine: List[str] = [item["idref"] for item in opf_soup.find_all("itemref") if item.get("idref")]

    # 3. Parse TOC (toc.ncx)
    toc_items: List[Dict[str, str]] = []
    if toc_href and toc_href in z.namelist():
        try:
            toc_soup = BeautifulSoup(z.read(toc_href), "xml")
            for navpoint in toc_soup.find_all("navPoint"):
                text_elem = navpoint.find("text")
                content_elem = navpoint.find("content")
                t_label = _text(text_elem) if text_elem else ""
                t_src = content_elem.get("src", "") if content_elem else ""
                n_id = navpoint.get("id", "")
                if t_label:
                    toc_items.append({
                        "id": n_id,
                        "label": t_label,
                        "src": t_src
                    })
        except Exception as err:
            log.warning(f"Could not parse TOC NCX: {err}")

    return opf_path, opf_dir, manifest, spine, toc_items


def extract_from_epub(epub_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]], Dict[str, Any]]:
    """Extract structured blocks and TOC from EPUB document."""
    with zipfile.ZipFile(epub_path, "r") as z:
        drm = epub_drm_reason(z)
        if drm:
            raise EpubDRMError(f"EPUB có DRM ({drm}) → không trích được nội dung. Hỏi người dùng bản không DRM.")
        opf_path, opf_dir, manifest, spine, toc_items = extract_epub_metadata_and_spine(z)

        blocks: List[Dict[str, Any]] = []
        seq = 0
        seen_files = set()

        for item_id in spine:
            file_path = manifest.get(item_id)
            if not file_path or file_path in seen_files:
                continue
            if file_path not in z.namelist():
                continue
            seen_files.add(file_path)

            raw_html = z.read(file_path).decode("utf-8", errors="replace")
            soup = BeautifulSoup(raw_html, "html.parser")

            # Extract translatable tags in reading order. Tables become ONE table block (headers/rows) placed where
            # the table starts; elements inside a table are still counted in elem_index (epub_builder enumerates
            # them the same way) but not emitted twice.
            elements = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "li", "table"])
            elem_idx = 0
            table_idx = -1

            for el in elements:
                if el.name == "table":
                    table_idx += 1
                    if el.find_parent("table") is not None:
                        continue  # bảng lồng: chữ đã nằm trong ô của bảng ngoài
                    grid = table_grid(el)
                    if grid and any(c for r in grid for c in r):
                        seq += 1
                        blocks.append({"block_id": f"b_{seq:04d}", "file": file_path, "table_index": table_idx,
                                       "type": "table", "headers": grid[0], "rows": grid[1:]})
                    continue
                txt = _text(el)
                if not txt:
                    continue
                if el.find_parent("table") is not None:
                    elem_idx += 1  # giữ khớp chỉ số với epub_builder
                    continue

                inner_html = "".join(str(c) for c in el.contents)
                has_inline = any(c.name for c in el.contents if hasattr(c, "name"))

                b_type = el.name
                classes = el.get("class", [])
                if isinstance(classes, str):
                    classes = [classes]

                # Map semantic types
                if "headings" in classes and b_type == "p":
                    b_type = "h2"
                elif b_type in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                    pass
                elif b_type == "blockquote" or "center_quote" in classes:
                    b_type = "blockquote"
                elif b_type == "li":
                    b_type = "li"
                else:
                    b_type = "p"

                seq += 1
                block = {
                    "block_id": f"b_{seq:04d}",
                    "file": file_path,
                    "elem_index": elem_idx,
                    "tag": el.name,
                    "type": b_type,
                    "classes": classes,
                    "text": txt,
                    "en": txt,
                    "has_inline_html": has_inline,
                    "inner_html": inner_html
                }
                blocks.append(block)
                elem_idx += 1

        epub_meta = {
            "opf_path": opf_path,
            "opf_dir": opf_dir,
            "total_blocks": len(blocks),
            "total_files": len(seen_files),
            "toc_items": toc_items
        }

    return blocks, toc_items, epub_meta


def main():
    parser = argparse.ArgumentParser(description="Extract structured text blocks from EPUB file.")
    parser.add_argument("--input", required=True, type=Path, help="Input EPUB file")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON blocks file")
    parser.add_argument("--toc-output", type=Path, default=None, help="Optional output JSON for TOC items")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        blocks, toc_items, meta = extract_from_epub(args.input)
    except EpubDRMError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(2)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(blocks, f, ensure_ascii=False, indent=2)

    if args.toc_output:
        args.toc_output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.toc_output, "w", encoding="utf-8") as f:
            json.dump(toc_items, f, ensure_ascii=False, indent=2)

    print(f"✅ Extracted {len(blocks)} blocks from EPUB to: {args.output}")
    print(f"   📑 Total TOC navigation items: {len(toc_items)}")


if __name__ == "__main__":
    main()
