"""Flow Composer for Natural Document Composition via Typst.

Takes a reconstructed and translated LogicalDocument and composes a publication-grade,
naturally paginated PDF document without rigid bounding box constraints.

Conforms to AIWF Translation Upgrade #1.7:
- Part 16: Typography Reconstruction (Title > Heading > Body > Footnote)
- Part 17: Flow Composition from LogicalUnits
- Part 18: Natural Pagination (FREE constraint)
- Part 19: Keep-With-Next & Widow/Orphan Control
- Part 20: Layout Resolution Priority
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    from layout.logical_document import (
        ConfidenceLevel,
        InlineToken,
        LogicalDocument,
        LogicalTable,
        LogicalUnit,
        StructuralRole,
    )
except ImportError:
    from logical_document import (
        ConfidenceLevel,
        InlineToken,
        LogicalDocument,
        LogicalTable,
        LogicalUnit,
        StructuralRole,
    )


def _escape_typst(text: str) -> str:
    """Escapes special Typst markup characters for safe text insertion."""
    if not text:
        return ""
    # Typst special characters: \ # $ @ [ ] * _ < > and comment //
    t = text.replace("\\", "\\\\")
    t = t.replace("//", "\\/\\/")
    for ch in ("#", "$", "@", "[", "]", "*", "_", "<", ">"):
        t = t.replace(ch, f"\\{ch}")
    return t


def _format_inline_text(text: str, tokens: Optional[List[InlineToken]] = None) -> str:
    """Formats text, preserving superscripts and subscripts (e.g. Na+, HCO3-)."""
    if not text:
        return ""

    escaped = _escape_typst(text)

    # Convert common scientific ions to Typst super/subscripts if present in text
    # e.g. Na+ -> Na#super[+], K+ -> K#super[+], Cl- -> Cl#super[-]
    # HCO3- -> HCO#sub[3]#super[-]
    escaped = re.sub(r"\bHCO3([－\-\+])", r"HCO#sub[3]#super[\1]", escaped)
    escaped = re.sub(r"\b(Na|K|Cl|Ca|Mg|OH|H)([－\-\+])", r"\1#super[\2]", escaped)

    return escaped


class FlowComposer:
    """Composes a LogicalDocument into Typst source code and compiles it to PDF."""

    def __init__(
        self,
        log_doc: LogicalDocument,
        page_w_mm: float = 210.0,
        page_h_mm: float = 297.0,
        margin_x_mm: float = 20.0,
        margin_y_mm: float = 22.0,
        base_font_size: float = 9.8,
    ):
        self.doc = log_doc
        self.page_w_mm = page_w_mm
        self.page_h_mm = page_h_mm
        self.margin_x_mm = margin_x_mm
        self.margin_y_mm = margin_y_mm
        self.base_font_size = base_font_size

    def compose_typst(self) -> str:
        """Generates clean, publication-grade Typst document source."""
        lines = []

        # 1. Page & Layout Setup
        running_header = ""
        if self.doc.title and self.doc.title.translated_text:
            running_header = self.doc.title.translated_text.strip()
            if len(running_header) > 60:
                running_header = running_header[:57] + "..."

        lines.append(f"""
#set page(
  paper: "a4",
  margin: (x: {self.margin_x_mm}mm, top: {self.margin_y_mm}mm, bottom: {self.margin_y_mm}mm),
  header: align(right)[#text(size: 8pt, fill: rgb("666666"))[{_escape_typst(running_header)}]],
  footer: context align(center)[#text(size: 9pt, fill: rgb("666666"))[#counter(page).display("1")]],
)
#set text(
  font: ("Times New Roman", "Liberation Serif", "Arial"),
  size: {self.base_font_size}pt,
  lang: "vi",
)
#set par(
  justify: true,
  leading: 0.65em,
  spacing: 0.70em,
)
""")

        # 2. Document Title Header Block
        if self.doc.title:
            title_text = self.doc.title.translated_text or self.doc.title.text
            lines.append(f"""
#align(center)[
  #v(8pt)
  #text(size: 16pt, weight: "bold")[{_escape_typst(title_text)}]
""")
            if self.doc.subtitle:
                sub_text = self.doc.subtitle.translated_text or self.doc.subtitle.text
                lines.append(f"""  #v(4pt)\n  #text(size: 12pt, weight: "bold")[{_escape_typst(sub_text)}]\n""")

            if self.doc.authors:
                author_names = ", ".join(
                    a.translated_text or a.text for a in self.doc.authors
                )
                lines.append(f"""  #v(4pt)\n  #text(size: 10.5pt, style: "italic")[{_escape_typst(author_names)}]\n""")

            lines.append("  #v(12pt)\n]\n")

        # 3. Process Content Units
        for unit in self.doc.units:
            if isinstance(unit, LogicalTable):
                lines.append(self._compose_table(unit))
            elif isinstance(unit, LogicalUnit):
                lines.append(self._compose_unit(unit))

        return "\n".join(lines)

    def _compose_unit(self, unit: LogicalUnit) -> str:
        """Composes a single LogicalUnit into Typst markup."""
        text = unit.translated_text or unit.text
        if not text.strip():
            return ""

        formatted_text = _format_inline_text(text, unit.tokens)

        # A. Headings (Keep-with-next invariant)
        if unit.role == StructuralRole.HEADING_1:
            return f"""
#v(12pt)
#block(breakable: false)[
  #text(size: 13pt, weight: "bold", fill: rgb("0f172a"))[{formatted_text}]
]
#v(3pt)
"""
        elif unit.role == StructuralRole.HEADING_2:
            return f"""
#v(9pt)
#block(breakable: false)[
  #text(size: 11pt, weight: "bold", fill: rgb("1e293b"))[{formatted_text}]
]
#v(2pt)
"""
        elif unit.role == StructuralRole.HEADING_3:
            return f"""
#v(6pt)
#block(breakable: false)[
  #text(size: 10.5pt, weight: "bold", fill: rgb("334155"))[{formatted_text}]
]
#v(2pt)
"""

        # B. Formula Block
        elif unit.role == StructuralRole.FORMULA_BLOCK:
            return f"""
#v(4pt)
#align(center)[
  #block(
    fill: rgb("f8fafc"),
    stroke: 0.5pt + rgb("cbd5e1"),
    inset: (x: 12pt, y: 7pt),
    radius: 4pt,
  )[
    #text(size: 9.5pt, weight: "medium")[{formatted_text}]
  ]
]
#v(4pt)
"""

        # C. Definition Item / Key-Value Item
        elif unit.role == StructuralRole.DEFINITION_ITEM:
            delim = None
            if ":" in formatted_text:
                delim = ":"
            elif "：" in formatted_text:
                delim = "："

            if delim:
                parts = formatted_text.split(delim, 1)
                lbl = parts[0].strip()
                val = parts[1].strip() if len(parts) > 1 else ""
                # Avoid breaking on URL protocols (http, https)
                if lbl.lower() in ("http", "https"):
                    return f"""#block(inset: (left: 12pt))[{formatted_text}]\n"""
                return f"""#block(inset: (left: 12pt))[#text(weight: "bold")[{lbl}:] {val}]\n"""
            else:
                return f"""#block(inset: (left: 12pt))[{formatted_text}]\n"""

        # D. List Item
        elif unit.role == StructuralRole.LIST_ITEM:
            clean_txt = formatted_text
            clean_txt = re.sub(r"^([•・\-\*○■◆▶]|\\[\*\-])\s*", "", clean_txt)
            return f"""#block(inset: (left: 14pt))[• #h(4pt) {clean_txt}]\n"""

        # E. Body Paragraph
        else:
            return f"""#par[{formatted_text}]\n"""

    def _compose_table(self, tbl: LogicalTable) -> str:
        """Composes a LogicalTable into a Typst #table with proper formatting."""
        headers = tbl.translated_headers if tbl.translated_headers else tbl.headers
        rows = tbl.translated_rows if tbl.translated_rows else tbl.rows

        if not headers and not rows:
            return ""

        num_cols = len(headers[0]) if headers else (len(rows[0]) if rows else 1)
        if num_cols == 0:
            num_cols = 1

        lines = ["\n#v(6pt)"]

        # Table caption
        caption = tbl.translated_caption or tbl.caption
        if caption:
            lines.append(f"""#align(center)[#text(size: 10pt, weight: "bold")[{_escape_typst(caption)}]]\n#v(2pt)""")

        # Table block
        lines.append(f"""
#align(center)[
  #table(
    columns: {num_cols},
    stroke: 0.5pt + rgb("94a3b8"),
    fill: (col, row) => if row == 0 {{ rgb("f1f5f9") }} else {{ none }},
    align: (col, row) => if row == 0 {{ center + horizon }} else {{ center + horizon }},
    inset: 6pt,
""")

        # Headers
        for h_row in headers:
            for cell in h_row:
                cell_fmt = _format_inline_text(cell)
                lines.append(f"""    [#text(weight: "bold", size: 9pt)[{cell_fmt}]],""")

        # Body Rows
        for b_row in rows:
            for cell in b_row:
                cell_fmt = _format_inline_text(cell)
                lines.append(f"""    [#text(size: 8.8pt)[{cell_fmt}]],""")

        lines.append("  )\n]")

        # Table footnote
        footnote = tbl.translated_footnote or tbl.footnote
        if footnote:
            lines.append(f"""#v(2pt)\n#align(left)[#text(size: 8pt, style: "italic", fill: rgb("475569"))[{_escape_typst(footnote)}]]""")

        lines.append("#v(6pt)\n")
        return "\n".join(lines)

    def render_pdf(self, output_pdf_path: Union[str, Path]) -> Path:
        """Compiles Typst code to the target PDF file."""
        out_path = Path(output_pdf_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        typst_src = self.compose_typst()

        temp_dir = tempfile.mkdtemp(prefix="aiwf_typst_flow_")
        typ_file = Path(temp_dir) / "document.typ"

        try:
            with open(typ_file, "w", encoding="utf-8") as f:
                f.write(typst_src)

            # Compile with Typst
            cmd = ["typst", "compile", str(typ_file), str(out_path)]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if res.returncode != 0:
                raise RuntimeError(f"Typst compilation failed (code {res.returncode}):\n{res.stderr}")

            return out_path
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
