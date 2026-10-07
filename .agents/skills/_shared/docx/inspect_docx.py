#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inspect_docx.py — Đọc ngược DOCX thành JSON có cấu trúc để agent và test tự khẳng định (không cần nhìn ảnh).

Chỉ đọc, không sửa tệp. Lỗi từng phần ghi vào `warnings`, phần còn lại vẫn được trả về.
Thiết kế: docs/design/inspect_docx.md (lược đồ "aiwf.docx.inspect/1").

  python3 inspect_docx.py FILE.docx [--json OUT.json] [--text] [--rules RULES.json] [--pages]

Mã thoát: 0 = đọc được (và đạt luật nếu có --rules) · 1 = vi phạm luật · 2 = không xác minh được (đầu vào không
đọc được, luật không hợp lệ, hoặc luật 'pages' mà không render được vì thiếu LibreOffice) · 4 = thiếu python-docx.

--pages: render PDF bằng LibreOffice (engine office.soffice) để lấy số trang thật và chữ từng trang. Thiếu
LibreOffice hoặc render lỗi thì `pages` = null kèm cảnh báo (không đổi mã thoát, trừ khi luật có 'pages').
Dùng từ Python: `from inspect_docx import inspect_docx, InspectError`.
"""

import argparse
import hashlib
import json
import re
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "office"))

try:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph
except ImportError:  # pragma: no cover - phụ thuộc môi trường
    Document = None

SCHEMA = "aiwf.docx.inspect/1"
EMU_PER_MM = 36000
EMU_PER_INCH = 914400
TWIP_PER_MM = 1440 / 25.4
OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # Word cũ hoặc DOCX mã hóa bằng mật khẩu

PLACEHOLDER_RE = re.compile(
    r"\{\{.*?\}\}|<<.*?>>|\[TODO[^\]]*\]|\bTODO\b|\bXXX+\b|Lorem ipsum|#{3,}", re.IGNORECASE)
VERIFY_FLAG_RE = re.compile(r"\[(?:CẦN|CHƯA) XÁC MINH[^\]]*\]")
THEME_MAP = {"minorHAnsi": "minor", "minorAscii": "minor", "majorHAnsi": "major", "majorAscii": "major"}


class InspectError(Exception):
    """Đầu vào không đọc được; thông báo nói rõ cần làm gì tiếp."""


# ---------------------------------------------------------------- mở tệp

def _open(path):
    p = Path(path)
    if not p.is_file():
        raise InspectError(f"Không thấy tệp: {p}")
    with p.open("rb") as f:
        head = f.read(8)
    if head == OLE_MAGIC:
        raise InspectError("Tệp có mật khẩu hoặc là Word cũ (.doc): hỏi người dùng mật khẩu / bản .docx, không đoán.")
    if not zipfile.is_zipfile(p):
        raise InspectError("Không phải tệp DOCX (không phải gói zip).")
    with zipfile.ZipFile(p) as z:
        if "word/document.xml" not in z.namelist():
            raise InspectError("Gói zip không có word/document.xml, không phải DOCX hợp lệ.")
    if Document is None:
        raise ImportError("Thiếu python-docx: chạy `bash scripts/auto-setup.sh`.")
    try:
        return p, Document(str(p))
    except Exception as e:  # python-docx ném nhiều loại lỗi khác nhau
        raise InspectError(f"python-docx không mở được tệp: {e}")


def _theme_fonts(path):
    """Font latin của theme: {"minor": ..., "major": ...}. Rỗng nếu không có theme."""
    out = {}
    try:
        with zipfile.ZipFile(path) as z:
            name = next((n for n in z.namelist() if n.startswith("word/theme/") and n.endswith(".xml")), None)
            if name:
                xml = z.read(name).decode("utf-8", "ignore")
                for kind in ("minor", "major"):
                    m = re.search(rf"<a:{kind}Font>\s*<a:latin typeface=\"([^\"]*)\"", xml)
                    if m and m.group(1):
                        out[kind] = m.group(1)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------- phân giải định dạng

def _rfonts_name(rpr, theme):
    """Tên font latin từ w:rPr; (tên, "direct"|"theme") hoặc None."""
    if rpr is None:
        return None
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        return None
    for attr in ("w:ascii", "w:hAnsi"):
        if rf.get(qn(attr)):
            return rf.get(qn(attr)), "direct"
    for attr in ("w:asciiTheme", "w:hAnsiTheme"):
        kind = THEME_MAP.get(rf.get(qn(attr)) or "")
        if kind and theme.get(kind):
            return theme[kind], "theme"
    return None


def _half_points(rpr):
    if rpr is None:
        return None
    sz = rpr.find(qn("w:sz"))
    return int(sz.get(qn("w:val"))) / 2 if sz is not None and sz.get(qn("w:val")) else None


def _style_chain(style):
    while style is not None:
        yield style
        style = style.base_style


def _doc_defaults_rpr(doc):
    dd = doc.styles.element.find(qn("w:docDefaults"))
    if dd is None:
        return None
    rd = dd.find(qn("w:rPrDefault"))
    return rd.find(qn("w:rPr")) if rd is not None else None


def _resolve_run(run, para, doc, theme, defaults):
    """(font, nguồn font, cỡ pt) đã kế thừa: run → style ký tự → style đoạn → docDefaults."""
    rpr_chain = [("run", run._element.rPr)]
    if run.style is not None:
        rpr_chain += [("style", s.element.rPr) for s in _style_chain(run.style)]
    rpr_chain += [("style", s.element.rPr) for s in _style_chain(para.style)]
    rpr_chain.append(("docDefaults", defaults))
    font = src = size = None
    for origin, rpr in rpr_chain:
        if font is None:
            hit = _rfonts_name(rpr, theme)
            if hit:
                font, kind = hit
                src = "theme" if kind == "theme" else origin
        if size is None:
            size = _half_points(rpr)
    return font, src, size


def _flag(run, para, attr):
    """Đậm/nghiêng đã kế thừa qua style (None khi không ai đặt)."""
    v = getattr(run, attr)
    if v is not None:
        return bool(v)
    for s in _style_chain(para.style):
        sv = getattr(s.font, attr)
        if sv is not None:
            return bool(sv)
    return False


def _color(run):
    c = run.font.color
    try:
        return str(c.rgb) if c is not None and c.rgb is not None else None
    except Exception:
        return None


# ---------------------------------------------------------------- khối nội dung

def _iter_runs(p):
    for item in p.iter_inner_content():
        if hasattr(item, "runs"):  # Hyperlink
            yield from item.runs
        else:
            yield item


def _paragraph_block(i, p, doc, theme, defaults, fonts_used):
    runs = []
    for r in _iter_runs(p):
        if not r.text:
            continue
        font, src, size = _resolve_run(r, p, doc, theme, defaults)
        entry = {"text": r.text, "font": font, "font_src": src, "size_pt": size,
                 "bold": _flag(r, p, "bold"), "italic": _flag(r, p, "italic"), "color": _color(r)}
        fonts_used[font] = fonts_used.get(font, 0) + len(r.text)
        prev = runs[-1] if runs else None
        if prev and all(prev[k] == entry[k] for k in entry if k != "text"):
            prev["text"] += r.text
        else:
            runs.append(entry)
    ppr = p._element.pPr
    num = ppr.numPr if ppr is not None else None
    outline = None
    for s in _style_chain(p.style):
        m = re.fullmatch(r"(?:Heading|Tiêu đề)\s*(\d)", s.name or "")
        if m:
            outline = int(m.group(1))
            break
    if ppr is not None and ppr.find(qn("w:outlineLvl")) is not None:
        outline = int(ppr.find(qn("w:outlineLvl")).get(qn("w:val"))) + 1
    align = p.alignment
    return {
        "i": i, "kind": "paragraph", "style": p.style.name if p.style is not None else None,
        "outline": outline, "align": align.name.lower() if align is not None else None,
        "text": p.text,
        "list": ({"numId": int(num.numId.val), "ilvl": int(num.ilvl.val) if num.ilvl is not None else 0}
                 if num is not None and num.numId is not None else None),
        "page_break_before": bool(p.paragraph_format.page_break_before),
        "keep_next": bool(p.paragraph_format.keep_with_next),
        "runs": runs,
    }


def _cell_info(tc):
    span, vm = 1, None
    pr = tc.tcPr
    if pr is not None:
        gs = pr.find(qn("w:gridSpan"))
        if gs is not None:
            span = int(gs.get(qn("w:val")))
        v = pr.find(qn("w:vMerge"))
        if v is not None:
            vm = v.get(qn("w:val")) or "continue"
    return span, vm


def _table_block(i, tbl, doc, theme, defaults, fonts_used, cell_paragraphs):
    grid = tbl._tbl.find(qn("w:tblGrid"))
    widths = ([round(int(g.get(qn("w:w"))) / TWIP_PER_MM, 1) for g in grid.findall(qn("w:gridCol"))]
              if grid is not None else [])
    rows, merged = [], 0
    for tr in tbl._tbl.findall(qn("w:tr")):
        row = []
        for tc in tr.findall(qn("w:tc")):
            span, vm = _cell_info(tc)
            paras = [Paragraph(p, tbl) for p in tc.findall(qn("w:p"))]
            for p in paras:
                _paragraph_block(i, p, doc, theme, defaults, fonts_used)  # gom font; khối chi tiết không xuất
                cell_paragraphs.append((i, p))
            row.append({"text": "\n".join(p.text for p in paras), "span": span, "vmerge": vm})
            merged += (span > 1) + (vm is not None)
        rows.append(row)
    first = tbl._tbl.find(qn("w:tr"))
    header = False
    if first is not None and first.trPr is not None:
        header = first.trPr.find(qn("w:tblHeader")) is not None
    return {"i": i, "kind": "table", "rows": len(rows), "cols": len(widths) or max((len(r) for r in rows), default=0),
            "merged": merged, "header_row": header, "col_widths_mm": widths, "cells": rows}


# ---------------------------------------------------------------- ảnh, trường, sửa đổi

def _images(doc, i, p, warnings):
    out = []
    for dr in p._element.iter(qn("w:drawing")):
        ext = next(iter(dr.iter("{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent")), None)
        docpr = next(iter(dr.iter("{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr")), None)
        blip = next(iter(dr.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip")), None)
        if blip is None:
            continue
        rid = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
        px = None
        try:
            from PIL import Image
            import io
            with Image.open(io.BytesIO(p.part.related_parts[rid].blob)) as im:
                px = list(im.size)
        except Exception as e:
            warnings.append(f"Không đọc được kích thước ảnh ở khối {i}: {e}")
        placed = ([round(int(ext.get("cx")) / EMU_PER_MM, 1), round(int(ext.get("cy")) / EMU_PER_MM, 1)]
                  if ext is not None else None)
        dpi = round(px[0] / (int(ext.get("cx")) / EMU_PER_INCH)) if px and ext is not None and int(ext.get("cx")) else None
        alt = docpr.get("descr") if docpr is not None else None
        out.append({"block": i, "name": docpr.get("name") if docpr is not None else None,
                    "px": px, "placed_mm": placed, "effective_dpi": dpi, "alt": alt or None})
    return out


def _fields(root):
    toc = False
    names = []
    for it in root.iter(qn("w:instrText")):
        names.append((it.text or "").strip())
    for fs in root.iter(qn("w:fldSimple")):
        names.append((fs.get(qn("w:instr")) or "").strip())
    counts = {"page": 0, "numpages": 0, "other": []}
    for n in names:
        key = n.split(" ")[0].upper() if n else ""
        if key == "TOC":
            toc = True
        elif key == "PAGE":
            counts["page"] += 1
        elif key == "NUMPAGES":
            counts["numpages"] += 1
        elif key:
            counts["other"].append(key)
    counts["toc"] = toc
    counts["other"] = sorted(set(counts["other"]))
    return counts


def _review(path, root):
    ins = len(list(root.iter(qn("w:ins"))))
    dele = len(list(root.iter(qn("w:del"))))
    comments = footnotes = 0
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        if "word/comments.xml" in names:
            comments = len(re.findall(r"<w:comment\b", z.read("word/comments.xml").decode("utf-8", "ignore")))
        if "word/footnotes.xml" in names:
            xml = z.read("word/footnotes.xml").decode("utf-8", "ignore")
            footnotes = len([m for m in re.finditer(r"<w:footnote\b[^>]*>", xml) if "w:type=" not in m.group(0)])
    return {"tracked_insertions": ins, "tracked_deletions": dele, "comments": comments, "footnotes": footnotes}


def _hyperlinks(doc, root):
    out = []
    rid_attr = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    for h in root.iter(qn("w:hyperlink")):
        rid = h.get(rid_attr)
        target = None
        if rid:
            rel = doc.part.rels.get(rid)
            target = rel.target_ref if rel is not None else None
        else:
            target = "#" + h.get(qn("w:anchor"), "")
        out.append({"text": "".join(t.text or "" for t in h.iter(qn("w:t"))), "target": target})
    return out


def _sections(doc):
    out = []
    for s in doc.sections:
        cols = s._sectPr.find(qn("w:cols"))
        footer_xml = s.footer._element.xml if s.footer is not None else ""
        out.append({
            "page_mm": [round(s.page_width / EMU_PER_MM, 1), round(s.page_height / EMU_PER_MM, 1)],
            "orientation": "landscape" if s.page_width > s.page_height else "portrait",
            "margins_mm": {k: round((getattr(s, f"{k}_margin") or 0) / EMU_PER_MM, 1)
                           for k in ("top", "bottom", "left", "right")},
            "columns": int(cols.get(qn("w:num"))) if cols is not None and cols.get(qn("w:num")) else 1,
            "header_text": "\n".join(p.text for p in s.header.paragraphs).strip(),
            "footer_text": "\n".join(p.text for p in s.footer.paragraphs).strip(),
            "has_page_number_field": bool(re.search(r"PAGE\b", footer_xml)),
        })
    return out


# ---------------------------------------------------------------- phát hiện cơ học

def _findings(blocks, cell_paragraphs, images):
    f = {"placeholders": [], "verify_flags": [], "empty_paragraph_runs": [], "heading_gaps": [],
         "em_dash": [], "nfd_text": [], "missing_alt": [im["block"] for im in images if not im["alt"]]}
    units = [(b["i"], b["text"]) for b in blocks if b["kind"] == "paragraph"]
    units += [(i, p.text) for i, p in cell_paragraphs]
    for i, text in units:
        for m in PLACEHOLDER_RE.finditer(text):
            f["placeholders"].append({"block": i, "match": m.group(0)})
        for m in VERIFY_FLAG_RE.finditer(text):
            f["verify_flags"].append({"block": i, "match": m.group(0)})
        if "—" in text and i not in f["em_dash"]:
            f["em_dash"].append(i)
        if text and not unicodedata.is_normalized("NFC", text) and i not in f["nfd_text"]:
            f["nfd_text"].append(i)
    run_start = count = 0
    prev_level = None
    for b in blocks + [{"kind": "end"}]:
        empty = b["kind"] == "paragraph" and not b["text"].strip() and not b.get("page_break_before")
        if empty:
            if count == 0:
                run_start = b["i"]
            count += 1
        else:
            if count >= 2:
                f["empty_paragraph_runs"].append({"start": run_start, "count": count})
            count = 0
        if b["kind"] == "paragraph" and b["outline"]:
            if prev_level is not None and b["outline"] > prev_level + 1:
                f["heading_gaps"].append({"block": b["i"], "from": prev_level, "to": b["outline"]})
            prev_level = b["outline"]
    return f



# ---------------------------------------------------------------- số trang thật (--pages)

def _diacritic_split_warning(page_texts):
    """Font của tài liệu không có trên máy -> LibreOffice thay font, dấu tiếng Việt bị tách thành dòng lẻ khi trích chữ."""
    lone = sum(1 for t in page_texts for ln in t.splitlines()
               if len(ln.strip()) == 1 and ln.strip().isalpha() and not ln.strip().isascii())
    if lone < 3:
        return None
    return (f"--pages: {lone} dòng chỉ có một ký tự có dấu; nhiều khả năng máy thiếu font của tài liệu "
            "(LibreOffice thay font): chữ từng trang và số trang có thể lệch so với Word.")


def _render_pages(path, warnings):
    """{"count": n, "text": [chữ từng trang]} qua LibreOffice → PDF → PyMuPDF; None + cảnh báo nếu không được."""
    try:
        import soffice_tools
        if not soffice_tools.find_soffice():
            warnings.append("--pages: không có LibreOffice nên không biết số trang thật (cài hoặc đặt SOFFICE=...).")
            return None
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        with tempfile.TemporaryDirectory(prefix="inspect_docx_") as tmp:
            pdf = soffice_tools.convert(path, "pdf", tmp)
            with fitz.open(str(pdf)) as d:
                text = [unicodedata.normalize("NFC", pg.get_text()) for pg in d]
        warn = _diacritic_split_warning(text)
        if warn:
            warnings.append(warn)
        return {"engine": "libreoffice", "count": len(text), "text": text}
    except Exception as e:  # render hỏng không được làm mất phần đọc cấu trúc
        warnings.append(f"--pages: không render được ({type(e).__name__}: {e}).")
        return None


# ---------------------------------------------------------------- luật khai báo (--rules)

RULE_KEYS = {"fonts_allowed", "page_mm", "margins_mm", "no_placeholders", "max_consecutive_empty_paragraphs",
             "heading_no_skip", "min_image_dpi", "require_alt_text", "forbid", "pages"}
FORBIDDABLE = ("em_dash", "nfd_text", "verify_flags")
MM_TOL, MARGIN_TOL = 1.0, 0.5


def _rule_error(msg):
    raise InspectError(f"Luật không hợp lệ: {msg}")


def check_rules(report, rules):
    """Trả về danh sách vi phạm dạng "RULE <tên>: <vị trí>: <mô tả>". Ném InspectError nếu luật sai hoặc
    không xác minh được (khác với "xác minh và hỏng")."""
    if not isinstance(rules, dict):
        _rule_error("tệp luật phải là một đối tượng JSON")
    unknown = sorted(set(rules) - RULE_KEYS)
    if unknown:
        _rule_error(f"luật lạ {unknown}; hỗ trợ: {sorted(RULE_KEYS)}")
    if "pages" in rules and report.get("pages") is None:
        raise InspectError("Luật 'pages' cần số trang thật nhưng không render được (thiếu LibreOffice hoặc lỗi "
                           "render, xem warnings): không xác minh được.")
    v = []
    fi = report["findings"]
    if "fonts_allowed" in rules:
        allowed = rules["fonts_allowed"]
        if not isinstance(allowed, list):
            _rule_error("fonts_allowed phải là danh sách")
        for font, n in report["fonts_used"].items():
            if font is None:
                v.append(f"RULE fonts_allowed: toàn tài liệu: có {n} ký tự không phân giải được font")
            elif font not in allowed:
                v.append(f"RULE fonts_allowed: toàn tài liệu: font '{font}' ({n} ký tự), được phép {allowed}")
    for si, sec in enumerate(report["sections"], 1):
        if "page_mm" in rules:
            w, h = rules["page_mm"]
            if abs(sec["page_mm"][0] - w) > MM_TOL or abs(sec["page_mm"][1] - h) > MM_TOL:
                v.append(f"RULE page_mm: phần {si}: khổ {sec['page_mm']} mm, yêu cầu {[w, h]}")
        for side, rng in (rules.get("margins_mm") or {}).items():
            if side not in sec["margins_mm"]:
                _rule_error(f"margins_mm: cạnh lạ '{side}'")
            val = sec["margins_mm"][side]
            if not rng[0] - MARGIN_TOL <= val <= rng[1] + MARGIN_TOL:
                v.append(f"RULE margins_mm: phần {si}: lề {side} {val} mm, yêu cầu {rng[0]}-{rng[1]} mm")
    if "pages" in rules:
        pr, n = rules["pages"], report["pages"]["count"]
        if not isinstance(pr, dict) or not set(pr) <= {"min", "max"}:
            _rule_error("pages phải là {\"min\": n, \"max\": n}")
        if "max" in pr and n > pr["max"]:
            v.append(f"RULE pages: toàn tài liệu: {n} trang, tối đa {pr['max']}")
        if "min" in pr and n < pr["min"]:
            v.append(f"RULE pages: toàn tài liệu: {n} trang, tối thiểu {pr['min']}")
    if rules.get("no_placeholders"):
        v += [f"RULE no_placeholders: khối {m['block']}: '{m['match']}'" for m in fi["placeholders"]]
    if "max_consecutive_empty_paragraphs" in rules:
        mx = rules["max_consecutive_empty_paragraphs"]
        v += [f"RULE max_consecutive_empty_paragraphs: khối {r['start']}: {r['count']} đoạn trống liên tiếp (tối đa {mx})"
              for r in fi["empty_paragraph_runs"] if r["count"] > mx]
    if rules.get("heading_no_skip"):
        v += [f"RULE heading_no_skip: khối {g['block']}: nhảy từ cấp {g['from']} lên cấp {g['to']}" for g in fi["heading_gaps"]]
    if "min_image_dpi" in rules:
        v += [f"RULE min_image_dpi: khối {im['block']}: ảnh {im['effective_dpi']} dpi, yêu cầu >= {rules['min_image_dpi']}"
              for im in report["images"] if im["effective_dpi"] is not None and im["effective_dpi"] < rules["min_image_dpi"]]
    if rules.get("require_alt_text"):
        v += [f"RULE require_alt_text: khối {b}: ảnh thiếu văn bản thay thế" for b in fi["missing_alt"]]
    for name in rules.get("forbid", []):
        if name not in FORBIDDABLE:
            _rule_error(f"forbid: '{name}' không hỗ trợ; chọn trong {list(FORBIDDABLE)}")
        for item in fi[name]:
            loc = item["block"] if isinstance(item, dict) else item
            v.append(f"RULE forbid.{name}: khối {loc}: có {name}")
    return v


# ---------------------------------------------------------------- điểm vào

def inspect_docx(path, pages=False):
    """Trả về dict theo lược đồ aiwf.docx.inspect/1. Ném InspectError nếu không đọc được tệp.
    pages=True: thêm số trang thật qua LibreOffice (cần cài); không được thì "pages" là None + cảnh báo."""
    p, doc = _open(path)
    warnings, fonts_used, cell_paragraphs = [], {}, []
    theme = _theme_fonts(p)
    defaults = _doc_defaults_rpr(doc)
    root = doc.element.body

    blocks, images = [], []
    for child in root.iterchildren():
        i = len(blocks)
        try:
            if child.tag == qn("w:p"):
                para = Paragraph(child, doc)
                blocks.append(_paragraph_block(i, para, doc, theme, defaults, fonts_used))
                images += _images(doc, i, para, warnings)
            elif child.tag == qn("w:tbl"):
                blocks.append(_table_block(i, Table(child, doc), doc, theme, defaults, fonts_used, cell_paragraphs))
        except Exception as e:  # lỗi một khối không làm mất cả tài liệu
            warnings.append(f"Bỏ qua khối {i} do lỗi đọc: {e}")
            blocks.append({"i": i, "kind": "unreadable", "text": ""})

    core = doc.core_properties
    words = sum(len(b["text"].split()) for b in blocks if b["kind"] == "paragraph")
    return {
        "schema": SCHEMA,
        "file": {"path": str(p), "size": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                 "core": {"title": core.title, "author": core.author,
                          "created": core.created.isoformat() if core.created else None,
                          "modified": core.modified.isoformat() if core.modified else None}},
        "sections": _sections(doc),
        "blocks": blocks,
        "images": images,
        "fields": _fields(root),
        "review": _review(p, root),
        "hyperlinks": _hyperlinks(doc, root),
        "fonts_used": dict(sorted(fonts_used.items(), key=lambda kv: -kv[1])),
        "findings": _findings(blocks, cell_paragraphs, images),
        "stats": {"paragraphs": sum(b["kind"] == "paragraph" for b in blocks), "words": words,
                  "tables": sum(b["kind"] == "table" for b in blocks), "images": len(images)},
        "pages": _render_pages(p, warnings) if pages else None,
        "warnings": warnings,
    }


def plain_text(report):
    """Văn bản theo thứ tự đọc; bảng thành các dòng ô cách nhau bằng tab."""
    lines = []
    for b in report["blocks"]:
        if b["kind"] == "paragraph":
            lines.append(b["text"])
        elif b["kind"] == "table":
            lines += ["\t".join(c["text"].replace("\n", " ") for c in row) for row in b["cells"]]
    return "\n".join(lines)


def summary(r):
    f, s = r["findings"], r["stats"]
    sec = r["sections"][0] if r["sections"] else {}
    top_fonts = ", ".join(f"{k} ({v})" for k, v in list(r["fonts_used"].items())[:3]) or "-"
    return "\n".join([
        f"{Path(r['file']['path']).name}: {s['paragraphs']} đoạn, {s['words']} từ, {s['tables']} bảng, {s['images']} ảnh",
        f"Khổ giấy {sec.get('page_mm')} mm, lề {sec.get('margins_mm')}",
        f"Font chính: {top_fonts}",
        f"Placeholder: {len(f['placeholders'])} · cờ xác minh: {len(f['verify_flags'])} · "
        f"chuỗi đoạn trống: {len(f['empty_paragraph_runs'])} · nhảy cấp tiêu đề: {len(f['heading_gaps'])} · "
        f"em dash: {len(f['em_dash'])} · NFD: {len(f['nfd_text'])} · ảnh thiếu alt: {len(f['missing_alt'])}",
        *([f"Số trang thật: {r['pages']['count']}"] if r.get("pages") else []),
        f"Sửa đổi: +{r['review']['tracked_insertions']} / -{r['review']['tracked_deletions']}, "
        f"bình luận {r['review']['comments']}, chú thích cuối trang {r['review']['footnotes']}",
    ] + [f"Cảnh báo: {w}" for w in r["warnings"]])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Đọc ngược DOCX thành JSON cấu trúc (chỉ đọc).")
    ap.add_argument("file")
    ap.add_argument("--json", metavar="OUT", help="ghi JSON đầy đủ vào tệp này")
    ap.add_argument("--text", action="store_true", help="in văn bản thuần theo thứ tự đọc")
    ap.add_argument("--rules", metavar="RULES.json", help="kiểm theo luật khai báo; vi phạm thoát mã 1")
    ap.add_argument("--pages", action="store_true", help="thêm số trang thật (render bằng LibreOffice)")
    args = ap.parse_args(argv)
    violations = None
    try:
        rules = None
        if args.rules:
            try:
                rules = json.loads(Path(args.rules).expanduser().read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                raise InspectError(f"Không đọc được tệp luật {args.rules}: {e}")
        need_pages = args.pages or (isinstance(rules, dict) and "pages" in rules)
        report = inspect_docx(args.file, pages=need_pages)
        if args.rules:
            violations = check_rules(report, rules)
            report["rules"] = {"file": str(args.rules), "passed": not violations, "violations": violations}
    except InspectError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2
    except ImportError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 4
    if args.json:
        Path(args.json).expanduser().write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(plain_text(report) if args.text else summary(report))
    if violations is None:
        return 0
    for line in violations:
        print(line)
    if violations:
        print(f"❌ RULES FAIL ({len(violations)} vi phạm)")
        return 1
    print("✅ RULES PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
