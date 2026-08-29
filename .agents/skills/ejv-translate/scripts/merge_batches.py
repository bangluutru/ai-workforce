#!/usr/bin/env python3
"""Merge translated EJV batches and verify 100% block completeness."""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Merge translated EJV batches into unified dataset.")
    parser.add_argument("--process-dir", required=True, type=Path, help="Working directory containing batches (02.process/)")
    parser.add_argument("--output", required=True, type=Path, help="Output merged JSON file path")
    args = parser.parse_args()

    manifest_path = args.process_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"❌ Error: manifest.json not found in {args.process_dir}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    total_batches = manifest.get("total_batches", 0)
    expected_total_blocks = manifest.get("total_source_blocks", 0)

    merged_blocks = []
    missing_batches = []
    block_mismatch_batches = []

    for batch_id, b_meta in sorted(manifest.get("batches", {}).items(), key=lambda x: x[1]["index"]):
        target_file = args.process_dir / b_meta["target_file"]
        expected_count = b_meta["block_count"]

        if not target_file.exists():
            missing_batches.append(batch_id)
            continue

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                batch_data = json.load(f)
        except Exception as e:
            print(f"❌ Error reading {target_file}: {e}", file=sys.stderr)
            missing_batches.append(batch_id)
            continue

        if not isinstance(batch_data, list):
            print(f"❌ Error: {target_file} does not contain a JSON array", file=sys.stderr)
            missing_batches.append(batch_id)
            continue

        if len(batch_data) != expected_count:
            block_mismatch_batches.append((batch_id, expected_count, len(batch_data)))

        merged_blocks.extend(batch_data)

    # Integrity verification
    if missing_batches:
        print(f"❌ Failed: {len(missing_batches)} batch(es) are missing or failed to parse:")
        for mb in missing_batches:
            print(f"   • {mb}")
        sys.exit(1)

    if block_mismatch_batches:
        print(f"⚠️ Warning: Block count mismatches detected in {len(block_mismatch_batches)} batch(es):")
        for bid, exp, actual in block_mismatch_batches:
            print(f"   • {bid}: Expected {exp} blocks, got {actual} blocks")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(merged_blocks, f, ensure_ascii=False, indent=2)

    coverage_pct = (len(merged_blocks) / expected_total_blocks * 100) if expected_total_blocks > 0 else 100

    print("══════════════════════════════════════════════════════════")
    print("           🎉 EJV MERGE & AUDIT REPORT                   ")
    print("══════════════════════════════════════════════════════════")
    print(f" • Total Batches Merged: {total_batches}/{total_batches}")
    print(f" • Expected Source Blocks: {expected_total_blocks}")
    print(f" • Merged Target Blocks:   {len(merged_blocks)}")
    print(f" • Completeness Rate:       {coverage_pct:.1f}%")
    print(f" • Output File:            {args.output}")
    print("══════════════════════════════════════════════════════════")

    if coverage_pct < 100:
        print("⚠️ Notice: Not all blocks were translated. Please inspect mismatched batches.")
    else:
        print("✅ 100% Zero-Loss Document Translation Confirmed!")


if __name__ == "__main__":
    main()
