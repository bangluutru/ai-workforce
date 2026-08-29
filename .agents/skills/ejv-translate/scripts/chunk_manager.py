#!/usr/bin/env python3
"""Chunk Manager for EJV Translation — Split large documents into bounded batches with manifest tracking."""

import argparse
import json
import math
import sys
from pathlib import Path

DEFAULT_MAX_BLOCKS = 25
DEFAULT_MAX_WORDS = 1000


def count_words_in_block(block: dict) -> int:
    """Estimate word count of a block."""
    b_type = block.get("type", "")
    if b_type == "hr":
        return 1
    elif b_type in {"h1", "h2", "h3", "p", "blockquote", "caption"}:
        return len(str(block.get("text", "")).split())
    elif b_type in {"ul", "ol"}:
        items = block.get("items", [])
        return sum(len(str(x).split()) for x in items)
    elif b_type == "table":
        headers = block.get("headers", [])
        rows = block.get("rows", [])
        h_words = sum(len(str(x).split()) for x in headers)
        r_words = sum(sum(len(str(c).split()) for c in r) for r in rows)
        return h_words + r_words
    return len(str(block).split())


def create_chunks(blocks: list, max_blocks: int = DEFAULT_MAX_BLOCKS, max_words: int = DEFAULT_MAX_WORDS) -> list[list[dict]]:
    """Group blocks into bounded chunks."""
    chunks = []
    current_chunk = []
    current_words = 0

    for block in blocks:
        b_words = count_words_in_block(block)
        # Check boundary
        if current_chunk and (len(current_chunk) >= max_blocks or (current_words + b_words > max_words and len(current_chunk) >= 5)):
            chunks.append(current_chunk)
            current_chunk = [block]
            current_words = b_words
        else:
            current_chunk.append(block)
            current_words += b_words

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def main():
    parser = argparse.ArgumentParser(description="Split extracted blocks into bounded translation batches.")
    parser.add_argument("--input", required=True, type=Path, help="Input extracted blocks JSON file")
    parser.add_argument("--process-dir", required=True, type=Path, help="Working directory for batches (02.process/)")
    parser.add_argument("--max-blocks", type=int, default=DEFAULT_MAX_BLOCKS, help="Maximum blocks per batch")
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS, help="Maximum words per batch")
    args = parser.parse_args()

    args.process_dir.mkdir(parents=True, exist_ok=True)

    with open(args.input, "r", encoding="utf-8") as f:
        blocks = json.load(f)

    chunks = create_chunks(blocks, max_blocks=args.max_blocks, max_words=args.max_words)
    total_chunks = len(chunks)

    manifest = {
        "source_file": str(args.input),
        "total_source_blocks": len(blocks),
        "total_batches": total_chunks,
        "max_blocks_per_batch": args.max_blocks,
        "max_words_per_batch": args.max_words,
        "batches": {}
    }

    for idx, chunk in enumerate(chunks, 1):
        batch_id = f"batch_{idx:03d}"
        source_filename = f"{batch_id}_source.json"
        target_filename = f"{batch_id}_translated.json"
        source_path = args.process_dir / source_filename
        target_path = args.process_dir / target_filename

        with open(source_path, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)

        manifest["batches"][batch_id] = {
            "index": idx,
            "status": "completed" if target_path.exists() else "pending",
            "source_file": source_filename,
            "target_file": target_filename,
            "block_count": len(chunk),
            "word_count": sum(count_words_in_block(b) for b in chunk)
        }

    manifest_path = args.process_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ Chunking completed:")
    print(f"   • Total source blocks: {len(blocks)}")
    print(f"   • Total batches created: {total_chunks}")
    print(f"   • Manifest saved at: {manifest_path}")


if __name__ == "__main__":
    main()
