#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

# Try to import required libraries
try:
    from markitdown import MarkItDown
    import pypandoc
except ImportError:
    print("Error: Missing required libraries. Please run: pip install markitdown pypandoc", file=sys.stderr)
    sys.exit(1)

_WHITESPACE = re.compile(r"\s+")

def _normalise(text: str) -> str:
    """Collapse whitespace and strip for fuzzy matching."""
    # Also strip some common markdown artifacts
    text = text.replace("*", "").replace("_", "").replace("#", "")
    return _WHITESPACE.sub(" ", text).strip()

def _similarity(a: str, b: str) -> float:
    """Simple token-overlap ratio for paragraph matching."""
    if not a or not b:
        return 0.0
    a_norm = _normalise(a).lower()
    b_norm = _normalise(b).lower()
    if a_norm == b_norm:
        return 1.0
    tokens_a = set(a_norm.split())
    tokens_b = set(b_norm.split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    return len(intersection) / max(len(tokens_a), len(tokens_b))

def _get_block_text(block: dict, lang: str) -> str:
    val = block.get(lang)
    if val is None:
        return ""
    if isinstance(val, list):
        return "\n".join(str(item) for item in val)
    return str(val)

def _get_table_cells_flat(block: dict, lang: str) -> list[str]:
    cells = []
    headers_raw = block.get("headers", {})
    rows_raw = block.get("rows", {})

    if isinstance(headers_raw, dict):
        headers = headers_raw.get(lang, headers_raw.get("vn", []))
    elif isinstance(headers_raw, list):
        headers = headers_raw
    else:
        headers = []

    if isinstance(rows_raw, dict):
        rows = rows_raw.get(lang, rows_raw.get("vn", []))
    elif isinstance(rows_raw, list):
        rows = rows_raw
    else:
        rows = []

    cells.extend(str(h) for h in headers)
    for row in rows:
        if isinstance(row, list):
            cells.extend(str(c) for c in row)
        else:
            cells.append(str(row))
    return cells

_ALL_LANGS = ("vn", "en", "ja")

def build_mapping(blocks: list[dict], lang: str) -> dict[str, str]:
    mapping = {}
    for block in blocks:
        btype = block.get("type", "")
        dst = _get_block_text(block, lang)
        if not dst:
            continue
            
        # Map whole block
        for src_lang in _ALL_LANGS:
            if src_lang == lang: continue
            src = _get_block_text(block, src_lang)
            if src:
                mapping[_normalise(src)] = dst

        # Map list items
        if btype in ("ul", "ol"):
            for src_lang in _ALL_LANGS:
                if src_lang == lang: continue
                src_items = block.get(src_lang, [])
                dst_items = block.get(lang, [])
                if isinstance(src_items, list) and isinstance(dst_items, list):
                    for si, di in zip(src_items, dst_items):
                        si_str, di_str = str(si).strip(), str(di).strip()
                        if si_str and di_str:
                            mapping[_normalise(si_str)] = di_str

        # Map table cells
        if btype == "meta_table":
            items = block.get("items", [])
            for item in items:
                for key in ("label", "value"):
                    raw = item.get(key, {})
                    if isinstance(raw, dict):
                        cell_dst = str(raw.get(lang, "")).strip()
                        if not cell_dst: continue
                        for src_lang in _ALL_LANGS:
                            if src_lang == lang: continue
                            cell_src = str(raw.get(src_lang, "")).strip()
                            if cell_src:
                                mapping[_normalise(cell_src)] = cell_dst
        elif btype == "table":
            dst_cells = _get_table_cells_flat(block, lang)
            for src_lang in _ALL_LANGS:
                if src_lang == lang: continue
                src_cells = _get_table_cells_flat(block, src_lang)
                for sc, dc in zip(src_cells, dst_cells):
                    sc_str, dc_str = sc.strip(), dc.strip()
                    if sc_str and dc_str:
                        mapping[_normalise(sc_str)] = dc_str
                        
    return mapping

def find_translation(text: str, mapping: dict[str, str], threshold: float = 0.70) -> str:
    norm = _normalise(text)
    if not norm:
        return text

    if norm in mapping:
        return mapping[norm]
        
    norm_lower = norm.lower()
    for key, val in mapping.items():
        if key.lower() == norm_lower:
            return val

    best_score = 0.0
    best_val = None
    for key, val in mapping.items():
        score = _similarity(norm, key)
        if score > best_score:
            best_score = score
            best_val = val

    if best_score >= threshold and best_val is not None:
        return best_val
        
    return text

def process_markdown(md_text: str, mapping: dict[str, str]) -> str:
    lines = md_text.split("\n")
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Handle Table Rows
        if stripped.startswith("|") and stripped.endswith("|"):
            # It's a table row
            parts = line.split("|")
            new_parts = []
            for i, cell in enumerate(parts):
                if i == 0 or i == len(parts) - 1:
                    new_parts.append(cell) # Keep the empty string before/after the border pipes
                else:
                    cell_stripped = cell.strip()
                    # Skip separator rows like |---|---|
                    if cell_stripped and all(c in '-: ' for c in cell_stripped):
                        new_parts.append(cell)
                    elif cell_stripped:
                        translated = find_translation(cell_stripped, mapping)
                        # Preserve original padding roughly if possible, or just space it
                        new_parts.append(f" {translated} ")
                    else:
                        new_parts.append(cell)
            new_lines.append("|".join(new_parts))
            
        # Handle Headings
        elif stripped.startswith("#"):
            prefix = ""
            content = stripped
            for i in range(len(stripped)):
                if stripped[i] == "#" or stripped[i] == " ":
                    prefix += stripped[i]
                else:
                    content = stripped[i:]
                    break
            translated = find_translation(content, mapping)
            new_lines.append(f"{prefix}{translated}")
            
        # Handle List Items
        elif stripped.startswith("- ") or stripped.startswith("* "):
            prefix = stripped[:2]
            content = stripped[2:]
            translated = find_translation(content, mapping)
            new_lines.append(f"{line[:len(line)-len(stripped)]}{prefix}{translated}")
            
        # Handle Normal Paragraphs
        elif stripped:
            translated = find_translation(stripped, mapping)
            new_lines.append(translated)
        else:
            new_lines.append(line)
            
    return "\n".join(new_lines)

def main():
    parser = argparse.ArgumentParser(description="Markdown-First Layout Preserving Translation")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--blocks", required=True, type=Path)
    parser.add_argument("--lang", required=True, choices=["vn", "en", "ja"])
    parser.add_argument("--output", required=True, type=Path)
    
    args = parser.parse_args()
    
    if not args.source.is_file():
        print(f"Error: Source file not found: {args.source}", file=sys.stderr)
        return 1
    if not args.blocks.is_file():
        print(f"Error: Blocks file not found: {args.blocks}", file=sys.stderr)
        return 1

    print(f"Extracting markdown from {args.source} using MarkItDown...")
    md = MarkItDown()
    result = md.convert(str(args.source))
    source_md = result.text_content
    
    # Save intermediate markdown for debugging
    md_path = args.output.with_suffix('.source.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(source_md)
    print(f"Saved source markdown to {md_path}")
        
    print(f"Loading translations from {args.blocks}...")
    with open(args.blocks, "r", encoding="utf-8") as f:
        blocks = json.load(f)
        
    mapping = build_mapping(blocks, args.lang)
    
    print("Replacing text in markdown...")
    translated_md = process_markdown(source_md, mapping)
    
    trans_md_path = args.output.with_suffix('.translated.md')
    with open(trans_md_path, 'w', encoding='utf-8') as f:
        f.write(translated_md)
    print(f"Saved translated markdown to {trans_md_path}")
        
    print(f"Reconstructing output file {args.output} via Pandoc...")
    
    ext = args.output.suffix.lower()
    try:
        if ext == '.pdf':
            # Pandoc needs a PDF engine. We can try wkhtmltopdf, weasyprint, or tectonic.
            # If none are installed, we'll fall back to saving as docx and telling the user.
            try:
                pypandoc.convert_text(translated_md, 'pdf', format='md', outputfile=str(args.output), extra_args=['--pdf-engine=xelatex'])
            except Exception as e:
                print(f"Warning: PDF conversion failed ({e}). Falling back to DOCX.")
                fallback_path = args.output.with_suffix('.docx')
                pypandoc.convert_text(translated_md, 'docx', format='md', outputfile=str(fallback_path))
                print(f"Saved as {fallback_path} instead.")
        elif ext == '.docx':
            pypandoc.convert_text(translated_md, 'docx', format='md', outputfile=str(args.output))
        else:
            print(f"Unsupported output format {ext}, saving as MD only.")
    except Exception as e:
        print(f"Pandoc error: {e}", file=sys.stderr)
        return 1
        
    print(f"✅ Success! Output saved to {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
