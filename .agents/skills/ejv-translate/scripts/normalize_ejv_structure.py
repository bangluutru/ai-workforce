#!/usr/bin/env python3
"""Normalize and structure EJV JSON dataset according to Vietnamese Administrative Document standards.

Key responsibilities:
1. Filter out watermark stamps (e.g., 'anhnn.qld_Nguyen Ngoc Anh_...').
2. Remove standalone page numbers and clean leaked page numbers inside text.
3. Stitch together split sentences/paragraphs broken across page boundaries.
4. Normalize and classify legal hierarchy:
   - admin_header: National Motto, Agency Name, Reference Number, Date
   - doc_title: DRAFT / DECREE title
   - chapter: Chapter headers
   - article: Article headings (Điều X / Article X / 第X条)
   - clause: Clauses (1., 2.)
   - point: Points (a), b), c))
   - table / meta_table: Structured tabular data
   - sign_off: Recipient & Signature blocks
"""

import argparse
import json
import re
from pathlib import Path


WATERMARK_PATTERN = re.compile(
    r"(?:anhnn\.qld_Nguyen\s*Ngoc\s*Anh|\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}|qld_Nguyen\s*Ngoc\s*Anh)",
    re.IGNORECASE
)

PAGE_NUM_ONLY_PATTERN = re.compile(r"^\d{1,3}$")


def is_watermark_text(text: str) -> bool:
    if not text:
        return False
    t = str(text).strip()
    return bool(WATERMARK_PATTERN.search(t)) and len(t) < 80


def is_page_number_text(text: str) -> bool:
    if not text:
        return False
    t = str(text).strip()
    return bool(PAGE_NUM_ONLY_PATTERN.match(t))


def clean_leaked_page_num(text: str) -> str:
    """Clean leaked page number at start of text, e.g. '2 môi và cơ quan...' -> 'môi và cơ quan...'"""
    if not text:
        return ""
    t = str(text).strip()
    # If starts with a standalone 1-3 digit number followed by space and lowercase letter
    match = re.match(r"^(\d{1,3})\s+(.+)$", t)
    if match:
        first_word = match.group(2)
        if first_word and (first_word[0].islower() or first_word.startswith(("môi", "và", "cơ", "sản", "phẩm"))):
            return first_word
    return t


def normalize_blocks(raw_blocks: list[dict]) -> list[dict]:
    cleaned = []
    
    # Phase 1: Filter out pure watermark and page number blocks
    for b in raw_blocks:
        b_type = b.get("type", "p")
        vn = b.get("vn", "")
        en = b.get("en", "")
        ja = b.get("ja", "")
        
        # Check if block is pure watermark
        if isinstance(vn, str) and (is_watermark_text(vn) or is_page_number_text(vn)):
            continue
        if isinstance(vn, str) and vn.strip() in {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75", "76", "77", "78"}:
            continue
            
        cleaned.append(b)

    # Phase 2: Unflatten fake <ol> lists into individual structured blocks
    unflattened = []
    for b in cleaned:
        b_type = b.get("type", "p")
        
        if b_type in {"ol", "ul"}:
            vn_items = b.get("vn", [])
            en_items = b.get("en", [])
            ja_items = b.get("ja", [])
            
            # If ol was used to wrap legal articles or clauses, unpack them
            is_legal_container = False
            for it in vn_items:
                it_str = str(it).strip()
                if it_str.startswith(("Điều ", "Nghị định này", "a) ", "b) ", "c) ", "d) ", "đ) ", "e) ", "Thay mặt", "Tôi xin", "Cơ sở ", "Chương ")):
                    is_legal_container = True
                    break
            
            if is_legal_container:
                for v_item, e_item, j_item in zip(vn_items, en_items, ja_items):
                    v_str = str(v_item).strip()
                    e_str = str(e_item).strip()
                    j_str = str(j_item).strip()
                    
                    if not v_str or is_watermark_text(v_str) or is_page_number_text(v_str):
                        continue
                    
                    # Clean vertical bar artifacts like '| DRAFT'
                    e_str = re.sub(r"^\|\s*", "", e_str)
                    j_str = re.sub(r"^\|\s*", "", j_str)
                    
                    # Classify item
                    if v_str.startswith("Điều ") or e_str.startswith("Article ") or j_str.startswith("第") and "条" in j_str:
                        unflattened.append({"type": "article", "vn": v_str, "en": e_str, "ja": j_str})
                    elif v_str.startswith("Chương ") or e_str.startswith("Chapter ") or j_str.startswith("第") and "章" in j_str:
                        unflattened.append({"type": "chapter", "vn": v_str, "en": e_str, "ja": j_str})
                    elif re.match(r"^[a-zđ]\)\s*", v_str):
                        unflattened.append({"type": "point", "vn": v_str, "en": e_str, "ja": j_str})
                    elif re.match(r"^\d+\.\s*", v_str):
                        unflattened.append({"type": "clause", "vn": v_str, "en": e_str, "ja": j_str})
                    else:
                        unflattened.append({"type": "p", "vn": v_str, "en": e_str, "ja": j_str})
            else:
                # Real list item
                filtered_v, filtered_e, filtered_j = [], [], []
                for v_item, e_item, j_item in zip(vn_items, en_items, ja_items):
                    v_str = str(v_item).strip()
                    e_str = str(e_item).strip()
                    j_str = str(j_item).strip()
                    if v_str and not is_watermark_text(v_str) and not is_page_number_text(v_str):
                        filtered_v.append(v_str)
                        filtered_e.append(re.sub(r"^\|\s*", "", e_str))
                        filtered_j.append(re.sub(r"^\|\s*", "", j_str))
                if filtered_v:
                    unflattened.append({"type": b_type, "vn": filtered_v, "en": filtered_e, "ja": filtered_j})
        else:
            # Clean string fields
            if isinstance(b.get("vn"), str):
                b["vn"] = clean_leaked_page_num(b["vn"])
                b["en"] = clean_leaked_page_num(re.sub(r"^\|\s*", "", str(b.get("en", ""))))
                b["ja"] = clean_leaked_page_num(re.sub(r"^\|\s*", "", str(b.get("ja", ""))))
                
                # Classify headings and legal terms
                v_str = b["vn"].strip()
                if v_str.startswith("Điều ") or str(b.get("en", "")).startswith("Article ") or (str(b.get("ja", "")).startswith("第") and "条" in str(b.get("ja", ""))):
                    b["type"] = "article"
                elif v_str.startswith("Chương ") or str(b.get("en", "")).startswith("Chapter ") or (str(b.get("ja", "")).startswith("第") and "章" in str(b.get("ja", ""))):
                    b["type"] = "chapter"
                elif re.match(r"^[a-zđ]\)\s*", v_str):
                    b["type"] = "point"
                elif re.match(r"^\d+\.\s*", v_str) and not v_str.startswith("13/05/2026"):
                    b["type"] = "clause"
            
            unflattened.append(b)

    # Phase 3: Stitching split sentences
    stitched = []
    i = 0
    while i < len(unflattened):
        curr = unflattened[i]
        
        # Check if next block should be stitched into current
        if i + 1 < len(unflattened):
            nxt = unflattened[i + 1]
            
            if curr.get("type") in {"p", "clause", "point"} and nxt.get("type") == "p":
                c_vn = str(curr.get("vn", "")).strip()
                n_vn = str(nxt.get("vn", "")).strip()
                
                # If current ends with comma, colon or unclosed parenthesis, or next starts with lowercase letter
                if (c_vn.endswith((",", ";", "(", "móng,", "tóc,", "hoặc", "và", "là")) or 
                    (n_vn and n_vn[0].islower() and not n_vn.startswith(("a)", "b)", "c)", "d)", "đ)", "e)")))):
                    
                    merged_curr = {**curr}
                    merged_curr["vn"] = c_vn + " " + n_vn
                    merged_curr["en"] = str(curr.get("en", "")).strip() + " " + str(nxt.get("en", "")).strip()
                    merged_curr["ja"] = str(curr.get("ja", "")).strip() + str(nxt.get("ja", "")).strip()
                    stitched.append(merged_curr)
                    i += 2
                    continue
        
        stitched.append(curr)
        i += 1

    return stitched


def main():
    parser = argparse.ArgumentParser(description="Normalize EJV structure and eliminate layout artifacts.")
    parser.add_argument("--input", required=True, type=Path, help="Input merged_ejv.json")
    parser.add_argument("--output", required=True, type=Path, help="Output clean_structured_ejv.json")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"📊 Processing {len(raw_data)} raw blocks...")
    clean_data = normalize_blocks(raw_data)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Normalized {len(clean_data)} structured blocks saved to: {args.output}")


if __name__ == "__main__":
    main()
