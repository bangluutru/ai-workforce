#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPUB Document Builder for EJV Translate.

Reconstructs publication-grade EPUB e-books in target language (Vietnamese) from the original
EPUB layout and translated blocks, preserving 100% of:
- CSS stylesheets and layout formatting
- Chapter structure, page breaks, and cover artwork
- Image illustrations and diagrams
- Table of Contents navigation hierarchy (NCX / Nav)
- OPF metadata and language tagging
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def update_html_file(file_path: Path, rel_key: str, file_blocks: Dict[int, Dict[str, Any]], lang: str):
    """Update HTML file elements with translated text while preserving markup."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")
    elements = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "li"])
    non_empty = [el for el in elements if el.get_text(strip=True)]

    for idx, el in enumerate(non_empty):
        if idx not in file_blocks:
            continue

        b = file_blocks[idx]
        trans_text = b.get(lang) or b.get("vn") or b.get("text_vn") or b.get("text")
        if not trans_text:
            continue

        # 1. If block has explicit translated inner HTML
        if b.get("vn_html"):
            try:
                new_soup = BeautifulSoup(b["vn_html"], "html.parser")
                el.clear()
                for child in list(new_soup.contents):
                    el.append(child)
                continue
            except Exception as err:
                log.warning(f"Error parsing vn_html for block {b.get('block_id')}: {err}")

        # 2. Check if element has special child spans (footnotes or attributions)
        special_spans = el.find_all("span", class_=lambda c: c and any("attribution" in c or "footnote" in c for c in (c if isinstance(c, list) else [c])))
        if special_spans and not b.get("vn_html"):
            # Preserve special spans by extracting them, updating text, then appending spans
            preserved_spans = [s.extract() for s in special_spans]
            el.string = str(trans_text).strip()
            for s in preserved_spans:
                el.append(s)
        else:
            el.string = str(trans_text).strip()

    # Bảng: khối table (table_index) → thay chữ từng ô theo ngôn ngữ đích
    tables = soup.find_all("table")
    for b in file_blocks.values():
        if b.get("type") != "table" or b.get("table_index") is None:
            continue
        ti = int(b["table_index"])
        if ti >= len(tables):
            continue
        H, R = b.get("headers"), b.get("rows")
        h = H.get(lang) if isinstance(H, dict) else None
        r = R.get(lang) if isinstance(R, dict) else None
        if h is None and r is None:
            continue  # bảng chưa dịch sang ngôn ngữ này: giữ nguyên
        grid = [h or []] + list(r or [])
        trs = [tr for tr in tables[ti].find_all("tr") if tr.find_parent("table") is tables[ti]]
        for tr, vals in zip(trs, grid):
            for cell, val in zip(tr.find_all(["td", "th"], recursive=False), vals):
                if str(val).strip():
                    cell.clear()
                    cell.string = str(val).strip()

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


def rebuild_epub(
    source_epub: Path,
    translated_blocks: List[Dict[str, Any]],
    output_epub: Path,
    lang: str = "vn",
    toc_translations: Optional[Dict[str, str]] = None,
    book_title: Optional[str] = None
) -> Path:
    """Rebuild EPUB document with translated text and updated metadata."""
    output_epub.parent.mkdir(parents=True, exist_ok=True)

    # Index blocks by (file_href, elem_index)
    blocks_by_file: Dict[str, Dict[int, Dict[str, Any]]] = {}
    for b in translated_blocks:
        f_href = b.get("file", "")
        e_idx = b.get("elem_index")
        if f_href and e_idx is not None:
            if f_href not in blocks_by_file:
                blocks_by_file[f_href] = {}
            blocks_by_file[f_href][int(e_idx)] = b
        elif f_href and b.get("type") == "table" and b.get("table_index") is not None:
            # khoá âm để không trùng elem_index của phần tử chữ
            blocks_by_file.setdefault(f_href, {})[-1 - int(b["table_index"])] = b

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Unpack source EPUB
        with zipfile.ZipFile(source_epub, "r") as zin:
            zin.extractall(tmp_path)

        # 2. Update each HTML content file
        for rel_href, file_blocks in blocks_by_file.items():
            target_html = tmp_path / rel_href
            if target_html.exists():
                update_html_file(target_html, rel_href, file_blocks, lang)

        # 3. Update OPF metadata (Language & Title)
        opf_candidates = list(tmp_path.glob("**/*.opf"))
        if opf_candidates:
            opf_file = opf_candidates[0]
            with open(opf_file, "r", encoding="utf-8") as f:
                opf_soup = BeautifulSoup(f.read(), "xml")

            # Update language tag
            lang_elem = opf_soup.find("dc:language") or opf_soup.find("language")
            if lang_elem:
                lang_elem.string = "vi" if lang in ("vi", "vn") else lang
            else:
                meta_elem = opf_soup.find("metadata")
                if meta_elem:
                    new_lang = opf_soup.new_tag("dc:language")
                    new_lang.string = "vi" if lang in ("vi", "vn") else lang
                    meta_elem.append(new_lang)

            # Update title
            if book_title:
                title_elem = opf_soup.find("dc:title") or opf_soup.find("title")
                if title_elem:
                    title_elem.string = book_title

            with open(opf_file, "w", encoding="utf-8") as f:
                f.write(str(opf_soup))

        # 4. Update Table of Contents (toc.ncx)
        if toc_translations:
            ncx_candidates = list(tmp_path.glob("**/*.ncx"))
            if ncx_candidates:
                ncx_file = ncx_candidates[0]
                with open(ncx_file, "r", encoding="utf-8") as f:
                    ncx_soup = BeautifulSoup(f.read(), "xml")

                for navpoint in ncx_soup.find_all("navPoint"):
                    text_elem = navpoint.find("text")
                    if text_elem:
                        old_txt = text_elem.get_text(strip=True)
                        n_id = navpoint.get("id", "")
                        # Match by ID or exact old text
                        trans_val = toc_translations.get(n_id) or toc_translations.get(old_txt)
                        if trans_val:
                            text_elem.string = trans_val

                with open(ncx_file, "w", encoding="utf-8") as f:
                    f.write(str(ncx_soup))

        # 5. Pack into output EPUB archive
        # Rule: mimetype must be first file stored with zero compression
        if output_epub.exists():
            output_epub.unlink()

        with zipfile.ZipFile(output_epub, "w") as zout:
            mimetype_file = tmp_path / "mimetype"
            if mimetype_file.exists():
                zout.write(mimetype_file, "mimetype", compress_type=zipfile.ZIP_STORED)

            for root, dirs, files in os.walk(tmp_path):
                for fname in sorted(files):
                    if fname == "mimetype" and root == str(tmp_path):
                        continue
                    full_p = Path(root) / fname
                    rel_p = full_p.relative_to(tmp_path)
                    zout.write(full_p, str(rel_p), compress_type=zipfile.ZIP_DEFLATED)

    log.info(f"✅ Rebuilt translated EPUB ({output_epub.stat().st_size} bytes) -> {output_epub}")
    return output_epub


def main():
    parser = argparse.ArgumentParser(description="Rebuild EPUB document from translated blocks.")
    parser.add_argument("--source", required=True, type=Path, help="Original EPUB document")
    parser.add_argument("--blocks", required=True, type=Path, help="JSON file containing translated blocks")
    parser.add_argument("--output", required=True, type=Path, help="Output translated EPUB path")
    parser.add_argument("--lang", default="vn", choices=["vn", "vi", "en", "ja"], help="Target language key")
    parser.add_argument("--toc", type=Path, default=None, help="Optional JSON file for TOC translations")
    parser.add_argument("--title", type=str, default=None, help="Optional translated book title")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    with open(args.blocks, "r", encoding="utf-8") as f:
        blocks = json.load(f)

    toc_trans = None
    if args.toc and args.toc.exists():
        with open(args.toc, "r", encoding="utf-8") as f:
            toc_trans = json.load(f)

    rebuild_epub(
        source_epub=args.source,
        translated_blocks=blocks,
        output_epub=args.output,
        lang=args.lang,
        toc_translations=toc_trans,
        book_title=args.title
    )
    print(f"🎉 Successfully built translated EPUB: {args.output}")


if __name__ == "__main__":
    main()
