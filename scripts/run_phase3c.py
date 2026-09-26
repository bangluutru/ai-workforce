#!/usr/bin/env python3
"""
scripts/run_phase3c.py — AIWF Phase 3C Real Agent Evaluation Runner

Executes canonical Antigravity Agent evaluation tasks (T01–T12) using ONE fixed model:
`gemini-3.8-flash-high`.

Strict constraints:
- Real Antigravity Agent execution via CLI (agy -p)
- Direct observation from transcripts and CLI JSON
- Separation of L0, L1, L2
- No simulation, no retries to force PASS
- Context efficiency telemetry collection
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

MODEL_ID = "gemini-3.8-flash-high"
CLI_PATH = "/Users/tranhaibang/.local/bin/agy"
WORKSPACE_DIR = "/Users/tranhaibang/.gemini/antigravity-ide/scratch/ai-workforce"
OUTPUT_DIR = Path(WORKSPACE_DIR) / "tests/agent_eval/results/phase3c"
DOWNLOADS_DIR = Path.home() / "Downloads"


def parse_args():
    parser = argparse.ArgumentParser(description="Run Phase 3C real agent evaluation tasks")
    parser.add_argument("--task", help="Run a single task (e.g. T01, T02)")
    parser.add_argument("--tasks", help="Comma-separated list of tasks (e.g. T01,T02,T03)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if task result JSON already exists")
    return parser.parse_args()


def run_single_task(task_id: str, skip_existing: bool = False):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_cli_path = OUTPUT_DIR / f"raw_cli_{task_id}_flash.json"
    result_eval_path = OUTPUT_DIR / f"{task_id}_flash_result.json"

    if skip_existing and result_eval_path.exists():
        print(f"[{task_id}] Result already exists at {result_eval_path}, skipping.")
        return True

    prompt_path = Path(WORKSPACE_DIR) / "tests/agent_eval/prompts" / f"{task_id}.prompt.txt"
    meta_path = Path(WORKSPACE_DIR) / "tests/agent_eval/prompts" / f"{task_id}.meta.json"

    if not prompt_path.exists():
        print(f"[{task_id}] Prompt file not found: {prompt_path}", file=sys.stderr)
        return False
    if not meta_path.exists():
        print(f"[{task_id}] Metadata file not found: {meta_path}", file=sys.stderr)
        return False

    with open(prompt_path, "r", encoding="utf-8") as f:
        raw_prompt = f.read().strip()

    print(f"\n================================================================================")
    print(f"🚀 [PHASE 3C] Executing Task {task_id} with model: {MODEL_ID}")
    print(f"   Prompt: {raw_prompt[:120]}...")
    print(f"================================================================================")

    start_time = time.time()

    cmd = [
        CLI_PATH,
        "-p", raw_prompt,
        "--model", MODEL_ID,
        "--output-format", "json",
        "--dangerously-skip-permissions"
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout per task
        )
        elapsed = time.time() - start_time
    except subprocess.TimeoutExpired:
        print(f"❌ [{task_id}] Execution timed out after 600 seconds!", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ [{task_id}] Execution failed: {e}", file=sys.stderr)
        return False

    raw_stdout = proc.stdout.strip()
    raw_stderr = proc.stderr.strip()

    if proc.returncode != 0:
        print(f"⚠️ [{task_id}] agy exited with code {proc.returncode}")
        if raw_stderr:
            print(f"   Stderr: {raw_stderr[:300]}")

    # Parse CLI JSON output
    cli_data = None
    try:
        cli_data = json.loads(raw_stdout)
    except json.JSONDecodeError:
        # CLI might print extra non-JSON lines; attempt to extract outermost JSON
        json_start = raw_stdout.find("{")
        json_end = raw_stdout.rfind("}")
        if json_start != -1 and json_end != -1:
            try:
                cli_data = json.loads(raw_stdout[json_start:json_end+1])
            except Exception:
                pass

    if not cli_data:
        print(f"❌ [{task_id}] Failed to parse valid JSON from agy CLI output!", file=sys.stderr)
        print(f"Raw stdout preview:\n{raw_stdout[:500]}\n")
        # Save raw stdout anyway for debugging
        with open(raw_cli_path, "w", encoding="utf-8") as f:
            f.write(raw_stdout)
        return False

    # Save raw CLI JSON
    with open(raw_cli_path, "w", encoding="utf-8") as f:
        json.dump(cli_data, f, indent=2, ensure_ascii=False)
    print(f"✅ [{task_id}] Saved raw CLI output to {raw_cli_path} (elapsed: {elapsed:.1f}s)")

    conv_id = cli_data.get("conversation_id")
    if not conv_id:
        print(f"❌ [{task_id}] No conversation_id found in CLI output!", file=sys.stderr)
        return False

    transcript_path = Path.home() / ".gemini/antigravity-cli/brain" / conv_id / ".system_generated/logs/transcript.jsonl"
    if not transcript_path.exists():
        # Fallback to full transcript if compact is missing
        transcript_path = Path.home() / ".gemini/antigravity-cli/brain" / conv_id / ".system_generated/logs/transcript_full.jsonl"

    if not transcript_path.exists():
        print(f"❌ [{task_id}] Transcript not found at {transcript_path}!", file=sys.stderr)
        return False

    # Run eval_transcript.py
    eval_cmd = [
        sys.executable,
        str(Path(WORKSPACE_DIR) / "scripts/eval_transcript.py"),
        "--transcript", str(transcript_path),
        "--task", task_id,
        "--meta", str(meta_path),
        "--cli-json", str(raw_cli_path),
        "--model", MODEL_ID,
        "--output", str(result_eval_path)
    ]

    eval_proc = subprocess.run(eval_cmd, cwd=WORKSPACE_DIR, capture_output=True, text=True)
    if eval_proc.returncode != 0:
        print(f"❌ [{task_id}] Evaluator failed with code {eval_proc.returncode}:", file=sys.stderr)
        print(eval_proc.stderr)
        return False

    print(eval_proc.stdout)
    return True


def main():
    args = parse_args()
    all_tasks = [f"T{i:02d}" for i in range(1, 13)]

    if args.task:
        selected_tasks = [args.task.strip().upper()]
    elif args.tasks:
        selected_tasks = [t.strip().upper() for t in args.tasks.split(",") if t.strip()]
    else:
        selected_tasks = all_tasks

    print(f"Starting Phase 3C execution for {len(selected_tasks)} tasks: {', '.join(selected_tasks)}")
    results = {}
    for task_id in selected_tasks:
        ok = run_single_task(task_id, skip_existing=args.skip_existing)
        results[task_id] = "OK" if ok else "FAIL"

    print("\n================================================================================")
    print("🏁 Phase 3C Run Batch Complete")
    for t, status in results.items():
        print(f"  {t}: {status}")
    print("================================================================================")


if __name__ == "__main__":
    main()
