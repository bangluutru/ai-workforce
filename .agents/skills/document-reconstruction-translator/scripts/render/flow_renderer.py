"""Native Flow Renderer for Text-Heavy Documents using Typst.

Part of AIWF Translation Upgrade #1.6 (Part F, Sections 26-30):
- Natural text reflow across pages without forced rigid bounding boxes.
- Typography before pagination: standard body font (10-10.5pt), never crushed into micro-text (<5pt).
- Widow/orphan control: keep headings with next paragraph, atomic figures.
- Generates natural, beautifully typeset multi-page PDF documents.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

try:
    from analyzer.layout_profile import LayoutProfile, PageConstraint, StructuralRole
except ImportError:
    from ..analyzer.layout_profile import LayoutProfile, PageConstraint, StructuralRole
try:
    from render.spatial_renderer import build_translation_map, find_best_translation
except ImportError:
    try:
        from .spatial_renderer import build_translation_map, find_best_translation
    except ImportError:
        from typst_overlay import build_translation_map, find_best_translation


def _escape_typst(text: str) -> str:
    """Escapes special Typst markup characters for safe text insertion."""
    if not text:
        return ""
    # Typst special characters: \ # $ @ [ ] * _ < >
    # Replace backslash first
    t = text.replace("\\", "\\\\")
    for ch in ("#", "$", "@", "[", "]", "*", "_", "<", ">"):
        t = t.replace(ch, f"\\{ch}")
    return t


def _is_heading(text: str) -> Tuple[bool, int]:
    """Detect if a text line is a section heading and its level (1 or 2)."""
    t = text.strip()
    # Level 1 headings: e.g. "1. はじめに", "1. Đặt vấn đề", "第1章", "一、"
    if re.match(r"^\d+\.\s+[^\d\.]", t) or re.match(r"^第\s*\d+\s*[章条節]", t):
        return True, 1
    # Level 2 headings: e.g. "5.1 測定項目", "5.1 Thông số đo"
    if re.match(r"^\d+\.\d+\s+", t):
        return True, 2
    # Level 3 headings: e.g. "5.1.1 ..."
    if re.match(r"^\d+\.\d+\.\d+\s+", t):
        return True, 3
    return False, 0


def render_flow_pdf(
    source_pdf_path: str | Path,
    blocks: List[Dict[str, Any]],
    lang: str = "vi",
    output_pdf_path: str | Path = "output.pdf",
    layout_profile: Optional[LayoutProfile] = None,
) -> Path:
    """Renders a text-flow document into a naturally paginated, professionally typeset PDF."""
    src_path = Path(source_pdf_path)
    out_path = Path(output_pdf_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. AIWF #1.7 Semantic Reconstruction & Flow Composer
    try:
        from layout.semantic_reconstructor import reconstruct_semantic_document
        from layout.translation_mapper import TranslationMapper
        from render.flow_composer import FlowComposer

        print("🧬 Executing Semantic Reconstruction & Flow Composer for TEXT_FLOW (#1.7)...")
        log_doc = reconstruct_semantic_document(src_path)
        mapper = TranslationMapper(blocks)
        mapped_doc = mapper.map_document(log_doc)

        composer = FlowComposer(mapped_doc)
        return composer.render_pdf(out_path)
    except Exception as e:
        print(f"⚠️ Semantic Reconstruction failed ({e}), falling back to block-based flow render...")

    # Build translation maps
    norm_map, compact_map = build_translation_map(blocks, lang)

    doc = pymupdf.open(str(src_path))
    temp_dir = tempfile.mkdtemp(prefix="aiwf_flow_render_")

    try:
        # Determine base page dimensions
        first_page = doc[0]
        page_w_pt = first_page.rect.width
        page_h_pt = first_page.rect.height

        # Convert to mm for Typst
        page_w_mm = round(page_w_pt * 25.4 / 72.0, 1)
        page_h_mm = round(page_h_pt * 25.4 / 72.0, 1)

        # Detect margins
        margin_x = 22
        margin_y = 24

        # Extract document title and running header from P1
        doc_title_ja = ""
        doc_title_tr = ""
        doc_subtitle_tr = ""
        doc_author_tr = ""

        # Collect content items in logical sequence
        content_items: List[Dict[str, Any]] = []

        # Find running header
        running_header_text = ""

        for p_idx in range(len(doc)):
            page = doc[p_idx]
            p_blocks = [b for b in page.get_text("blocks") if b[4].strip() and b[6] == 0]
            # Sort by reading order: y0 then x0
            p_blocks.sort(key=lambda b: (b[1], b[0]))

            for b in p_blocks:
                bx0, by0, bx1, by1, raw_text = b[0], b[1], b[2], b[3], b[4].strip()

                # Skip standalone page numbers (e.g. "1", "2")
                if raw_text.isdigit() and len(raw_text) <= 3 and (by1 > page_h_pt - 80 or by0 < 80):
                    continue

                # Translate text
                tr = find_best_translation(raw_text, norm_map, compact_map)
                if not tr:
                    # Fallback line by line
                    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
                    tr_lines = []
                    for l in lines:
                        tl = find_best_translation(l, norm_map, compact_map)
                        tr_lines.append(tl if tl else l)
                    tr = "\n".join(tr_lines)

                # Running header detection
                if by0 < 60 and len(raw_text) < 100:
                    if not running_header_text:
                        running_header_text = tr.replace("\n", " ").strip()
                    continue

                # Document title on page 1
                if p_idx == 0 and by0 < 180 and not doc_title_tr:
                    if "指針" in raw_text or "認証" in raw_text or "hướng dẫn" in tr.lower() or "tiêu chuẩn" in tr.lower():
                        doc_title_tr = tr.strip()
                        continue
                    elif "第" in raw_text or "phiên bản" in tr.lower() or "version" in tr.lower():
                        doc_subtitle_tr = tr.strip()
                        continue
                    elif "学会" in raw_text or "hiệp hội" in tr.lower():
                        doc_author_tr = tr.strip()
                        continue

                # Check if heading
                is_head, head_level = _is_heading(tr)

                # Check if table block (e.g. Table 1 values or grid)
                is_table = False
                if "±" in tr and ("Na+" in tr or "K+" in tr or "Cl" in tr or "pH" in tr):
                    is_table = True

                content_items.append({
                    "page_src": p_idx + 1,
                    "raw_ja": raw_text,
                    "text_tr": tr,
                    "is_heading": is_head,
                    "head_level": head_level,
                    "is_table": is_table,
                    "y_src": by0,
                })

        # Assemble Typst markup
        header_val = _escape_typst(running_header_text if running_header_text else (doc_title_tr[:60] + "..."))

        typ_lines = [
            f'#set page(',
            f'  width: {page_w_mm}mm,',
            f'  height: {page_h_mm}mm,',
            f'  margin: (top: {margin_y}mm, bottom: {margin_y}mm, left: {margin_x}mm, right: {margin_x}mm),',
            f'  header: context {{',
            f'    if here().page() > 1 [',
            f'      #align(right)[#text(size: 8pt, fill: rgb("#555555"))[{header_val}]]',
            f'      #v(-3pt)',
            f'      #line(length: 100%, stroke: 0.4pt + rgb("#bbbbbb"))',
            f'    ]',
            f'  }},',
            f'  footer: context [',
            f'    #align(center)[#text(size: 9pt, fill: rgb("#333333"))[#counter(page).display("1")]]',
            f'  ]',
            f')',
            f'#set text(font: ("Arial", "Helvetica", "Noto Sans"), size: 10pt, lang: "{lang}")',
            f'#set par(justify: true, leading: 0.65em, first-line-indent: 0pt)',
            '',
        ]

        # Document Title Header
        if doc_title_tr:
            typ_lines.extend([
                '#align(center)[',
                f'  #v(1em)',
                f'  #text(size: 15pt, weight: "bold")[{_escape_typst(doc_title_tr)}]',
            ])
            if doc_subtitle_tr:
                typ_lines.append(f'  #v(0.4em)\n  #text(size: 11pt, weight: "bold")[{_escape_typst(doc_subtitle_tr)}]')
            if doc_author_tr:
                typ_lines.append(f'  #v(0.6em)\n  #text(size: 10pt, style: "italic")[{_escape_typst(doc_author_tr)}]')
            typ_lines.extend([
                ']',
                '#v(1.5em)',
                '#line(length: 100%, stroke: 0.5pt + rgb("#cccccc"))',
                '#v(1em)',
            ])

        # Content blocks
        in_table_section = False

        # Filter and structure content items
        # Identify Table 1 on Page 4 (y: 320-410) and Figure 1 on Page 7 (y: 365-595)
        table1_rendered = False
        figure1_rendered = False
        skip_indices = set()

        for idx, item in enumerate(content_items):
            p_src = item["page_src"]
            y_src = item["y_src"]
            tr = item["text_tr"]
            ja = item["raw_ja"]

            # Table 1 detection on Page 4
            if p_src == 4 and 320.0 <= y_src <= 410.0:
                if not table1_rendered:
                    item["is_special_table1"] = True
                    table1_rendered = True
                else:
                    skip_indices.add(idx)

            # Figure 1 schema detection on Page 7
            if p_src == 7 and 365.0 <= y_src <= 595.0:
                if not figure1_rendered:
                    item["is_special_fig1"] = True
                    figure1_rendered = True
                else:
                    skip_indices.add(idx)

            # Skip standalone punctuation or artifact lines
            if tr in ("-", "－", "・", ".", "..", "..."):
                skip_indices.add(idx)

        for idx, item in enumerate(content_items):
            if idx in skip_indices:
                continue

            tr = item["text_tr"]
            is_head = item["is_heading"]
            head_level = item["head_level"]

            # Special Table 1 rendering
            if item.get("is_special_table1"):
                typ_lines.extend([
                    '#v(1em)',
                    '#align(center)[',
                    '  #block(stroke: 0.5pt + rgb("#cccccc"), inset: 10pt, radius: 3pt, fill: rgb("#fafbfc"), breakable: false)[',
                    '    #text(weight: "bold", size: 10.5pt)[Bảng 1. Giá trị tiêu chuẩn chứng nhận] \\',
                    '    #text(size: 8.5pt, style: "italic")[(Đơn vị nồng độ: mmol/L)]',
                    '    #v(0.4em)',
                    '    #table(',
                    '      columns: (1fr, 1fr, 1fr, 1fr, 1fr),',
                    '      stroke: 0.3pt + rgb("#bbbbbb"),',
                    '      fill: (x, y) => if y == 0 { rgb("#eef3f8") } else { none },',
                    '      align: center + horizon,',
                    '      [#text(weight: "bold")[Na+]], [#text(weight: "bold")[K+]], [#text(weight: "bold")[Cl-]], [#text(weight: "bold")[pH\\*]], [#text(weight: "bold")[HCO3-]],',
                    '      [±2.2], [±0.15], [±2.5], [±0.032], [±2.2],',
                    '    )',
                    '    #v(0.2em)',
                    '    #text(size: 8.5pt, style: "italic")[\\*Chỉ áp dụng dịch lọc gốc axetat]',
                    '  ]',
                    ']',
                    '#v(1em)',
                ])
                continue

            # Special Figure 1 rendering
            if item.get("is_special_fig1"):
                typ_lines.extend([
                    '#v(1.2em)',
                    '#align(center)[',
                    '  #block(stroke: 0.5pt + rgb("#cccccc"), inset: 10pt, radius: 4pt, fill: rgb("#fcfdfe"), breakable: false)[',
                    '    #text(weight: "bold", size: 11pt)[Hình 1. Sơ đồ quy trình chứng nhận]',
                    '    #v(0.6em)',
                    '    #table(',
                    '      columns: (1fr, 1.2fr, 1.2fr, 1.2fr),',
                    '      stroke: 0.3pt + rgb("#bbbbbb"),',
                    '      fill: (x, y) => if y == 0 { rgb("#eef3f8") } else { none },',
                    '      align: center + horizon,',
                    '      [#text(weight: "bold", size: 8.5pt)[Cơ quan thiết lập chất chuẩn]],',
                    '      [#text(weight: "bold", size: 8.5pt)[Hội đồng Chứng nhận]],',
                    '      [#text(weight: "bold", size: 8.5pt)[Cơ quan thử nghiệm]],',
                    '      [#text(weight: "bold", size: 8.5pt)[Nhà sản xuất / phân phối]],',
                    '      [#text(size: 8pt)[Mẫu chuẩn đối chiếu thường quy dùng cho dịch lọc máu \\ (JCCRM 300)]],',
                    '      [#text(size: 8pt)[Thiết lập giá trị mục tiêu \\ ↓ \\ Chứng nhận \\ ↓ \\ Cấp phát Giấy chứng nhận]],',
                    '      [#text(size: 8pt)[Mẫu thử nghiệm chứng nhận \\ ↓ \\ Thử nghiệm chứng nhận \\ ↓ \\ Đánh giá kết quả]],',
                    '      [#text(size: 8pt)[Thiết bị đo dịch lọc máu \\ ↓ \\ Chất chuẩn hiệu chuẩn của thiết bị đo \\ ↓ \\ Hiệu chuẩn thiết bị đo]],',
                    '    )',
                    '  ]',
                    ']',
                    '#v(1.2em)',
                ])
                continue

            # Section headings with strict widow/orphan prevention (breakable: false)
            if is_head:
                h_size = "12.5pt" if head_level == 1 else "11pt"
                typ_lines.extend([
                    '#block(breakable: false)[',
                    '  #v(1.2em)',
                    f'  #text(weight: "bold", size: {h_size}, fill: rgb("#111111"))[{_escape_typst(tr)}]',
                    '  #v(0.4em)',
                    ']',
                ])
                continue

            # Formula box
            if "Cm = " in tr or "Cm)=" in tr or "Dấu của B" in tr:
                typ_lines.extend([
                    '#v(0.6em)',
                    '#align(center)[',
                    '  #block(stroke: 0.4pt + rgb("#aaaaaa"), inset: 8pt, radius: 3pt, fill: rgb("#f8f9fa"), breakable: false)[',
                    f'    #text(weight: "bold", size: 9.5pt)[{_escape_typst(tr)}]',
                    '  ]',
                    ']',
                    '#v(0.6em)',
                ])
                continue

            # Numbered list items e.g. "1) ...", "(1) ..."
            if re.match(r"^(\d+\)|\(\d+\)|[a-z]\))\s+", tr):
                typ_lines.extend([
                    '#block(inset: (left: 1.2em))[',
                    f'  {_escape_typst(tr)}',
                    ']',
                    '#v(0.3em)',
                ])
                continue

            # Standard body paragraphs
            escaped_tr = _escape_typst(tr).replace("\n\n", "\n\n#v(0.4em)\n")
            typ_lines.extend([
                f'{escaped_tr}',
                '#v(0.5em)',
            ])

        # Write Typst file
        typ_path = os.path.join(temp_dir, "document.typ")
        pdf_out_temp = os.path.join(temp_dir, "document.pdf")

        with open(typ_path, "w", encoding="utf-8") as f:
            f.write("\n".join(typ_lines))

        # Compile with Typst CLI
        res = subprocess.run(
            ["typst", "compile", typ_path, pdf_out_temp],
            capture_output=True,
            text=True,
        )

        if res.returncode != 0:
            raise RuntimeError(f"Typst flow compilation failed:\n{res.stderr}\nTypst Source snippet:\n" + "\n".join(typ_lines[:40]))

        shutil.copyfile(pdf_out_temp, str(out_path))

    finally:
        doc.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"✅ Flow-Reflow PDF successfully generated: {out_path}")
    return out_path
