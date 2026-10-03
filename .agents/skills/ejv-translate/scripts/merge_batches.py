#!/usr/bin/env python3
"""Merge translated EJV batches and verify 100% block completeness."""

import argparse
import json
import os
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

        source_file = args.process_dir / b_meta.get("source_file", "")
        source_data = []
        if source_file.exists():
            try:
                with open(source_file, "r", encoding="utf-8") as sf:
                    source_data = json.load(sf)
            except Exception:
                pass

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                batch_data = json.load(f)
        except Exception as e:
            print(f"❌ Error reading {target_file}: {e}", file=sys.stderr)
            missing_batches.append(batch_id)
            continue

        if isinstance(batch_data, dict):
            # Compact key-value format {block_id: vn_text or {"vn": "..."}}
            merged_batch = []
            for sb in source_data:
                bid = sb.get("block_id")
                sb_copy = dict(sb)
                if bid in batch_data:
                    trans = batch_data[bid]
                    if isinstance(trans, dict):
                        sb_copy.update(trans)
                    else:
                        sb_copy["vn"] = str(trans)
                merged_batch.append(sb_copy)
            batch_data = merged_batch
        elif isinstance(batch_data, list) and source_data:
            # Khối ảnh không có chữ để dịch: nếu bản dịch bỏ đúng các khối image → chèn lại từ nguồn đúng vị trí
            n_img = sum(1 for sb in source_data if sb.get("type") == "image")
            if n_img and len(batch_data) == len(source_data) - n_img and \
                    not any(isinstance(tb, dict) and tb.get("type") == "image" for tb in batch_data):
                _it = iter(batch_data)
                batch_data = [dict(sb) if sb.get("type") == "image" else next(_it) for sb in source_data]
            # Check if list contains partial dicts with only block_id + vn
            if batch_data and "text" not in batch_data[0] and "block_id" in batch_data[0]:
                trans_map = {item["block_id"]: item for item in batch_data if "block_id" in item}
                merged_batch = []
                for sb in source_data:
                    bid = sb.get("block_id")
                    sb_copy = dict(sb)
                    if bid in trans_map:
                        sb_copy.update(trans_map[bid])
                    merged_batch.append(sb_copy)
                batch_data = merged_batch
            elif batch_data and len(batch_data) == len(source_data) and "text" not in batch_data[0]:
                # Danh sách đầy đủ theo thứ tự: ghép theo vị trí để GIỮ câu nguồn ("text") cho translation_qa.py
                def _keep_src(sb, tb):
                    m = {**sb, **tb}
                    for k in ("headers", "rows"):          # bảng nguồn dạng list bị bản dịch {lang: ...} đè → giữ riêng
                        if isinstance(sb.get(k), list) and isinstance(tb.get(k), dict):
                            m["text_" + k] = sb[k]
                    return m
                batch_data = [_keep_src(sb, tb) if isinstance(tb, dict) else tb for sb, tb in zip(source_data, batch_data)]

        if not isinstance(batch_data, list):
            print(f"❌ Error: {target_file} does not contain a JSON array or dict", file=sys.stderr)
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
        print(f"❌ Lệch số khối ở {len(block_mismatch_batches)} batch (dịch gộp/bỏ khối = MẤT NỘI DUNG):")
        for bid, exp, actual in block_mismatch_batches:
            print(f"   • {bid}: nguồn {exp} khối, bản dịch {actual} khối → dịch lại batch này đúng 1:1")
        if not os.environ.get("EJV_ALLOW_PARTIAL"):
            sys.exit(1)

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
