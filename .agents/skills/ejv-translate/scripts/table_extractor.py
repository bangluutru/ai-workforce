#!/usr/bin/env python3
"""Hybrid Table Extraction: PyMuPDF (fast) + img2table (accurate, lightweight).

This module provides a unified interface for extracting tables from PDF and DOCX
documents. Designed for AI Workforce portability (git-based sharing across machines):

  Tier 1 (default): PyMuPDF find_tables() — zero extra dependency
  Tier 2 (optional): img2table — lightweight (~10MB), OpenCV-based, no PyTorch
  Tier 3 (optional): Docling TableFormer — heavy (~1GB), highest accuracy

Usage:
    from table_extractor import TableExtractor
    
    extractor = TableExtractor(mode="auto")  # PyMuPDF + img2table fallback
    tables = extractor.extract_tables_from_pdf("document.pdf")
    for table in tables:
        print(table.headers, table.rows, table.merges)
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class MergeInfo:
    """Metadata for a merged cell region (rowspan/colspan)."""
    row: int
    col: int
    rowspan: int
    colspan: int
    value: str = ""


@dataclass
class ExtractedTable:
    """Standardized table structure from any extraction engine."""
    page: int
    headers: list[str]
    rows: list[list[str]]
    merges: list[MergeInfo] = field(default_factory=list)
    bbox: tuple = ()  # (x0, y0, x1, y1) bounding box on page
    confidence: float = 1.0
    source: str = "pymupdf"  # "pymupdf" | "img2table" | "docling"


# ──────────────────────────────────────────────────────────────────────
# Complexity Scoring
# ──────────────────────────────────────────────────────────────────────

def _compute_complexity_score(normalized: list[list[str]], merges: list[MergeInfo]) -> float:
    """Score table complexity (0.0 = trivial, 1.0 = very complex).
    
    High complexity indicators:
    - Many merged cells (rowspan/colspan)
    - High column count (>6)
    - Empty cells in irregular patterns
    - Inconsistent row lengths
    """
    if not normalized or len(normalized) < 2:
        return 0.0
    
    score = 0.0
    num_rows = len(normalized)
    num_cols = max(len(row) for row in normalized)
    
    # Factor 1: Merge complexity (0-0.4)
    if merges:
        merge_ratio = len(merges) / max(num_rows * num_cols, 1)
        multi_span_merges = sum(1 for m in merges if m.rowspan > 1 or m.colspan > 2)
        score += min(0.4, merge_ratio * 2 + multi_span_merges * 0.1)
    
    # Factor 2: Column count (0-0.2)
    if num_cols > 8:
        score += 0.2
    elif num_cols > 5:
        score += 0.1
    
    # Factor 3: Empty cell irregularity (0-0.2)
    empty_counts = [sum(1 for c in row if not c.strip()) for row in normalized]
    if empty_counts:
        mean_empty = sum(empty_counts) / len(empty_counts)
        variance = sum((e - mean_empty) ** 2 for e in empty_counts) / len(empty_counts)
        if variance > 2.0:
            score += 0.2
        elif variance > 0.5:
            score += 0.1
    
    # Factor 4: Row length inconsistency (0-0.2)
    row_lengths = [len(row) for row in normalized]
    if len(set(row_lengths)) > 1:
        score += 0.2
    
    return min(1.0, score)


# ──────────────────────────────────────────────────────────────────────
# PyMuPDF Table Helpers
# ──────────────────────────────────────────────────────────────────────

def _normalize_table_cells(extracted_tab: list[list]) -> list[list[str]]:
    """Normalize table cells: None → '', strip whitespace, join multi-line cells."""
    result = []
    for row in extracted_tab:
        normalized_row = []
        for cell in row:
            if cell is None:
                normalized_row.append("")
            else:
                cell_str = str(cell).strip()
                cell_str = re.sub(r'\n+', ' ', cell_str)
                normalized_row.append(cell_str)
        result.append(normalized_row)
    return result


def _detect_merged_cells_pymupdf(normalized: list[list[str]]) -> list[MergeInfo]:
    """Detect merged cells by finding adjacent cells with identical content.
    
    PyMuPDF's table.extract() duplicates content for merged cells.
    This heuristic detects adjacent identical cells to infer merges.
    """
    if not normalized or len(normalized) < 1:
        return []
    
    num_rows = len(normalized)
    num_cols = max(len(row) for row in normalized) if normalized else 0
    if num_cols == 0:
        return []
    
    # Pad rows to same length
    for row in normalized:
        while len(row) < num_cols:
            row.append("")
    
    consumed = [[False] * num_cols for _ in range(num_rows)]
    merges = []
    
    for r in range(num_rows):
        for c in range(num_cols):
            if consumed[r][c]:
                continue
            
            cell_val = normalized[r][c]
            
            # Detect colspan
            colspan = 1
            while c + colspan < num_cols and normalized[r][c + colspan] == cell_val and cell_val != "":
                colspan += 1
            
            # Detect rowspan
            rowspan = 1
            if cell_val != "":
                while r + rowspan < num_rows:
                    match = True
                    for dc in range(colspan):
                        if c + dc >= num_cols or normalized[r + rowspan][c + dc] != cell_val:
                            match = False
                            break
                    if match:
                        rowspan += 1
                    else:
                        break
            
            if colspan > 1 or rowspan > 1:
                merges.append(MergeInfo(
                    row=r, col=c,
                    rowspan=rowspan, colspan=colspan,
                    value=cell_val
                ))
                for dr in range(rowspan):
                    for dc in range(colspan):
                        if dr == 0 and dc == 0:
                            continue
                        consumed[r + dr][c + dc] = True
    
    return merges


# ──────────────────────────────────────────────────────────────────────
# img2table Integration (Lightweight, ~10MB, OpenCV-based)
# ──────────────────────────────────────────────────────────────────────

def _check_img2table_available() -> bool:
    """Check if img2table is installed."""
    try:
        import img2table  # noqa: F401
        return True
    except ImportError:
        return False


def _img2table_extract_tables(pdf_path: Path) -> list[ExtractedTable]:
    """Extract tables using img2table (lightweight OpenCV-based).
    
    img2table detects table structures via image processing,
    supporting borderless tables and implicit rows/columns.
    Does NOT require PyTorch or heavy ML frameworks.
    
    Install: pip install img2table
    """
    from img2table.document import PDF as Img2TablePDF
    
    log.info(f"img2table: Processing {pdf_path}...")
    pdf_doc = Img2TablePDF(str(pdf_path))
    
    # Extract tables without OCR (uses native PDF text)
    # For scanned PDFs, OCR engine would be needed
    try:
        extracted = pdf_doc.extract_tables()
    except Exception as e:
        log.warning(f"img2table extraction failed: {e}")
        return []
    
    tables = []
    for page_num, page_tables in extracted.items():
        for tbl in page_tables:
            df = tbl.df
            if df is None or df.empty:
                continue
            
            headers = [str(c) for c in df.columns.tolist()]
            rows = []
            for _, row in df.iterrows():
                rows.append([str(v) if v is not None else "" for v in row.tolist()])
            
            tables.append(ExtractedTable(
                page=page_num + 1,
                headers=headers,
                rows=rows,
                merges=[],  # img2table flattens merges into DataFrame
                confidence=0.85,
                source="img2table"
            ))
    
    log.info(f"  img2table: found {len(tables)} table(s)")
    return tables


# ──────────────────────────────────────────────────────────────────────
# Docling Integration (Heavy, ~1GB, highest accuracy)
# ──────────────────────────────────────────────────────────────────────

def _check_docling_available() -> bool:
    """Check if docling is installed and importable."""
    try:
        import docling  # noqa: F401
        return True
    except ImportError:
        return False


def _docling_extract_tables(pdf_path: Path) -> list[ExtractedTable]:
    """Extract tables using Docling's TableFormer model (ACCURATE mode).
    
    Returns list of ExtractedTable with precise merge information.
    Raises ImportError if docling is not installed.
    
    Install: pip install docling pandas
    WARNING: ~1GB install due to PyTorch dependency.
    """
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    log.info(f"Docling: Converting {pdf_path} with TableFormer ACCURATE mode...")
    result = converter.convert(str(pdf_path))
    
    tables = []
    for table_ix, table in enumerate(result.document.tables):
        html_output = table.export_to_html()
        merges, headers, rows = _parse_html_table(html_output)
        
        page_num = 0
        if hasattr(table, 'prov') and table.prov:
            for prov in table.prov:
                if hasattr(prov, 'page_no'):
                    page_num = prov.page_no
                    break
        
        tables.append(ExtractedTable(
            page=page_num,
            headers=headers,
            rows=rows,
            merges=merges,
            confidence=0.95,
            source="docling"
        ))
        log.info(f"  Table {table_ix}: {len(headers)} cols, {len(rows)} rows, "
                 f"{len(merges)} merges")
    
    return tables


def _parse_html_table(html: str) -> tuple[list[MergeInfo], list[str], list[list[str]]]:
    """Parse HTML table string to extract headers, rows, and merge metadata.
    
    Handles <th>/<td> with rowspan/colspan attributes.
    Returns (merges, headers, rows).
    """
    merges = []
    headers = []
    rows = []
    
    tr_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
    cell_pattern = re.compile(
        r'<(th|td)([^>]*)>(.*?)</\1>',
        re.DOTALL | re.IGNORECASE
    )
    rowspan_pattern = re.compile(r'rowspan\s*=\s*["\']?(\d+)', re.IGNORECASE)
    colspan_pattern = re.compile(r'colspan\s*=\s*["\']?(\d+)', re.IGNORECASE)
    
    all_rows = tr_pattern.findall(html)
    
    for row_idx, row_html in enumerate(all_rows):
        cells = cell_pattern.findall(row_html)
        row_data = []
        
        col_offset = 0
        for tag_type, attrs, content in cells:
            clean_text = re.sub(r'<[^>]+>', '', content).strip()
            
            rs_match = rowspan_pattern.search(attrs)
            cs_match = colspan_pattern.search(attrs)
            rowspan = int(rs_match.group(1)) if rs_match else 1
            colspan = int(cs_match.group(1)) if cs_match else 1
            
            row_data.append(clean_text)
            
            if rowspan > 1 or colspan > 1:
                merges.append(MergeInfo(
                    row=row_idx,
                    col=col_offset,
                    rowspan=rowspan,
                    colspan=colspan,
                    value=clean_text
                ))
            
            col_offset += colspan
        
        if row_idx == 0 and any(tag == 'th' for tag, _, _ in cells):
            headers = row_data
        elif row_idx == 0:
            headers = row_data
        else:
            rows.append(row_data)
    
    return merges, headers, rows


# ──────────────────────────────────────────────────────────────────────
# Main TableExtractor Class
# ──────────────────────────────────────────────────────────────────────

class TableExtractor:
    """Hybrid table extraction with tiered engines for portability.
    
    Designed for AI Workforce git-based distribution:
    
    Modes:
        - "fast": PyMuPDF only (zero extra dependency, always available)
        - "enhanced": PyMuPDF + img2table fallback (~10MB, lightweight)
        - "accurate": Docling TableFormer (heavy ~1GB, best accuracy)
        - "auto": PyMuPDF → img2table fallback (recommended default)
    
    Engine Priority (auto mode):
        1. PyMuPDF find_tables() — instant, always available
        2. img2table — if installed and table complexity > threshold
        3. Docling — only if explicitly installed by power users
    
    Usage:
        extractor = TableExtractor(mode="auto")
        tables = extractor.extract_tables_from_pdf("document.pdf")
    """
    
    COMPLEXITY_THRESHOLD = 0.35
    
    def __init__(self, mode: str = "auto"):
        if mode not in ("fast", "enhanced", "accurate", "auto"):
            raise ValueError(f"Invalid mode: {mode}. Choose 'fast', 'enhanced', 'accurate', or 'auto'.")
        self.mode = mode
        self._img2table_available = None
        self._docling_available = None
    
    @property
    def img2table_available(self) -> bool:
        if self._img2table_available is None:
            self._img2table_available = _check_img2table_available()
        return self._img2table_available
    
    @property
    def docling_available(self) -> bool:
        if self._docling_available is None:
            self._docling_available = _check_docling_available()
        return self._docling_available
    
    def extract_tables_from_pdf(self, pdf_path: Path | str) -> list[ExtractedTable]:
        """Extract all tables from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file.
        
        Returns:
            List of ExtractedTable objects with headers, rows, and merge metadata.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        if self.mode == "accurate":
            return self._extract_accurate(pdf_path)
        
        if self.mode == "fast":
            return self._extract_with_pymupdf(pdf_path)
        
        if self.mode == "enhanced":
            return self._extract_enhanced(pdf_path)
        
        # Auto mode: PyMuPDF first → img2table fallback for complex tables
        return self._extract_auto(pdf_path)
    
    def _extract_auto(self, pdf_path: Path) -> list[ExtractedTable]:
        """Auto mode: PyMuPDF primary, img2table for complex tables."""
        pymupdf_tables = self._extract_with_pymupdf(pdf_path)
        
        # Check if any table is complex enough for enhanced extraction
        complex_tables_exist = any(
            _compute_complexity_score(
                [t.headers] + t.rows if t.headers else t.rows,
                t.merges
            ) > self.COMPLEXITY_THRESHOLD
            for t in pymupdf_tables
        )
        
        if complex_tables_exist:
            # Try img2table first (lightweight)
            if self.img2table_available:
                log.info("Complex tables detected — using img2table for enhanced extraction...")
                try:
                    enhanced = _img2table_extract_tables(pdf_path)
                    if enhanced:
                        return enhanced
                    log.warning("img2table returned no tables — using PyMuPDF results.")
                except Exception as e:
                    log.warning(f"img2table failed: {e} — using PyMuPDF results.")
            
            # Try Docling as last resort (only if someone installed it)
            elif self.docling_available:
                log.info("Complex tables detected — using Docling for highest accuracy...")
                try:
                    docling_tables = _docling_extract_tables(pdf_path)
                    if docling_tables:
                        return docling_tables
                except Exception as e:
                    log.warning(f"Docling failed: {e} — using PyMuPDF results.")
            
            else:
                log.info("Complex tables detected but no enhanced extractor installed. "
                         "For better results: pip install img2table")
        
        return pymupdf_tables
    
    def _extract_enhanced(self, pdf_path: Path) -> list[ExtractedTable]:
        """Enhanced mode: prefer img2table, fallback to PyMuPDF."""
        if self.img2table_available:
            try:
                tables = _img2table_extract_tables(pdf_path)
                if tables:
                    return tables
            except Exception as e:
                log.warning(f"img2table failed: {e}")
        
        log.info("Falling back to PyMuPDF...")
        return self._extract_with_pymupdf(pdf_path)
    
    def _extract_accurate(self, pdf_path: Path) -> list[ExtractedTable]:
        """Accurate mode: prefer Docling, fallback chain."""
        if self.docling_available:
            try:
                return _docling_extract_tables(pdf_path)
            except Exception as e:
                log.warning(f"Docling failed: {e}")
        
        if self.img2table_available:
            log.info("Docling not available, trying img2table...")
            try:
                tables = _img2table_extract_tables(pdf_path)
                if tables:
                    return tables
            except Exception as e:
                log.warning(f"img2table failed: {e}")
        
        log.info("No enhanced extractor available, using PyMuPDF...")
        return self._extract_with_pymupdf(pdf_path)
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> list[ExtractedTable]:
        """Extract tables using PyMuPDF's built-in find_tables()."""
        import pymupdf
        
        doc = pymupdf.open(pdf_path)
        tables = []
        
        for page_idx, page in enumerate(doc):
            try:
                page_tables = page.find_tables()
            except Exception as e:
                log.warning(f"Page {page_idx + 1}: find_tables() failed: {e}")
                continue
            
            for t in page_tables:
                extracted = t.extract()
                if not extracted or len(extracted) < 1:
                    continue
                
                normalized = _normalize_table_cells(extracted)
                merges = _detect_merged_cells_pymupdf(normalized)
                
                headers = normalized[0] if normalized else []
                rows = normalized[1:] if len(normalized) > 1 else []
                
                tables.append(ExtractedTable(
                    page=page_idx + 1,
                    headers=headers,
                    rows=rows,
                    merges=merges,
                    bbox=t.bbox if hasattr(t, 'bbox') else (),
                    confidence=0.8,
                    source="pymupdf"
                ))
        
        doc.close()
        return tables
    
    def extract_tables_from_docx(self, docx_path: Path | str) -> list[ExtractedTable]:
        """Extract tables from a DOCX file using python-docx (native OOXML).
        
        python-docx provides direct access to table structure including
        merged cells via OOXML, so no ML model is needed.
        """
        from docx import Document
        from docx.oxml.ns import qn
        
        docx_path = Path(docx_path)
        if not docx_path.exists():
            raise FileNotFoundError(f"DOCX not found: {docx_path}")
        
        doc = Document(docx_path)
        tables = []
        
        for tbl_idx, tbl in enumerate(doc.tables):
            num_rows = len(tbl.rows)
            num_cols = len(tbl.columns)
            
            if num_rows == 0 or num_cols == 0:
                continue
            
            # Build grid and detect merges from OOXML
            grid = [["" for _ in range(num_cols)] for _ in range(num_rows)]
            merges = []
            consumed = [[False] * num_cols for _ in range(num_rows)]
            
            for r_idx, row in enumerate(tbl.rows):
                c_idx = 0
                for cell in row.cells:
                    while c_idx < num_cols and consumed[r_idx][c_idx]:
                        c_idx += 1
                    if c_idx >= num_cols:
                        break
                    
                    text = cell.text.strip()
                    text = re.sub(r'\n+', ' ', text)
                    
                    # Detect merge via OOXML gridSpan (colspan)
                    tc = cell._tc
                    tc_pr = tc.find(qn('w:tcPr'))
                    colspan = 1
                    if tc_pr is not None:
                        gs = tc_pr.find(qn('w:gridSpan'))
                        if gs is not None:
                            colspan = int(gs.get(qn('w:val'), '1'))
                    
                    # Detect vertical merge (rowspan)
                    rowspan = 1
                    if tc_pr is not None:
                        vmerge = tc_pr.find(qn('w:vMerge'))
                        if vmerge is not None:
                            val = vmerge.get(qn('w:val'), '')
                            if val == 'restart':
                                for scan_r in range(r_idx + 1, num_rows):
                                    scan_cell = tbl.cell(scan_r, c_idx)
                                    scan_tc = scan_cell._tc
                                    scan_tcPr = scan_tc.find(qn('w:tcPr'))
                                    if scan_tcPr is not None:
                                        scan_vm = scan_tcPr.find(qn('w:vMerge'))
                                        if scan_vm is not None and scan_vm.get(qn('w:val'), '') != 'restart':
                                            rowspan += 1
                                        else:
                                            break
                                    else:
                                        break
                            elif val == '' or val is None:
                                consumed[r_idx][c_idx] = True
                                c_idx += 1
                                continue
                    
                    grid[r_idx][c_idx] = text
                    
                    if colspan > 1 or rowspan > 1:
                        merges.append(MergeInfo(
                            row=r_idx, col=c_idx,
                            rowspan=rowspan, colspan=colspan,
                            value=text
                        ))
                        for dr in range(rowspan):
                            for dc in range(colspan):
                                if dr == 0 and dc == 0:
                                    continue
                                if r_idx + dr < num_rows and c_idx + dc < num_cols:
                                    consumed[r_idx + dr][c_idx + dc] = True
                    
                    c_idx += colspan
            
            headers = grid[0] if grid else []
            rows = grid[1:] if len(grid) > 1 else []
            
            tables.append(ExtractedTable(
                page=0,
                headers=headers,
                rows=rows,
                merges=merges,
                confidence=1.0,
                source="docx-native"
            ))
        
        return tables


# ──────────────────────────────────────────────────────────────────────
# CLI for standalone testing
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json
    
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Extract tables from PDF/DOCX")
    parser.add_argument("--input", required=True, type=Path, help="Input PDF or DOCX")
    parser.add_argument("--mode", default="auto", choices=["fast", "enhanced", "accurate", "auto"])
    parser.add_argument("--output", type=Path, help="Output JSON (optional)")
    args = parser.parse_args()
    
    extractor = TableExtractor(mode=args.mode)
    
    # Report available engines
    print(f"🔧 Engines: PyMuPDF=✅  img2table={'✅' if extractor.img2table_available else '❌'}  "
          f"Docling={'✅' if extractor.docling_available else '❌'}")
    
    ext = args.input.suffix.lower()
    if ext == ".pdf":
        tables = extractor.extract_tables_from_pdf(args.input)
    elif ext == ".docx":
        tables = extractor.extract_tables_from_docx(args.input)
    else:
        print(f"Unsupported format: {ext}")
        exit(1)
    
    print(f"\n✅ Extracted {len(tables)} table(s)")
    for i, t in enumerate(tables):
        print(f"\n--- Table {i + 1} (page {t.page}, source: {t.source}, "
              f"confidence: {t.confidence:.0%}) ---")
        print(f"  Headers: {t.headers}")
        print(f"  Rows: {len(t.rows)}")
        print(f"  Merges: {len(t.merges)}")
        for m in t.merges:
            print(f"    merge at ({m.row},{m.col}): {m.rowspan}x{m.colspan} = '{m.value[:30]}'")
    
    if args.output:
        output_data = []
        for t in tables:
            output_data.append({
                "page": t.page,
                "headers": t.headers,
                "rows": t.rows,
                "merges": [{"row": m.row, "col": m.col, "rowspan": m.rowspan,
                            "colspan": m.colspan, "value": m.value} for m in t.merges],
                "source": t.source,
                "confidence": t.confidence
            })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Saved to {args.output}")
