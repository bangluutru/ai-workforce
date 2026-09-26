#!/usr/bin/env python3
"""
scripts/run_phase4a.py — AIWF Phase 4A Real Agent Evaluation Runner

Executes controlled A/B Antigravity Agent evaluation tasks using ONE fixed model:
`gemini-3.8-flash-high`.

Results are stored strictly in `tests/agent_eval/results/phase4a/`.
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
OUTPUT_DIR = Path(WORKSPACE_DIR) / "tests/agent_eval/results/phase4a"
DOWNLOADS_DIR = Path.home() / "Downloads"


def parse_args():
    parser = argparse.ArgumentParser(description="Run Phase 4A real agent evaluation tasks")
    parser.add_argument("--task", help="Run a single task (e.g. T02, T06, T09, T10, T12)")
    parser.add_argument("--tasks", help="Comma-separated list of tasks (e.g. T02,T06,T09,T10,T12)")
    parser.add_argument("--suffix", default="phase4a", help="Suffix for result filenames (e.g. control, phase4a)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if task result JSON already exists")
    return parser.parse_args()


def run_single_task(task_id: str, suffix: str = "phase4a", skip_existing: bool = False):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_cli_path = OUTPUT_DIR / f"raw_cli_{task_id}_{suffix}.json"
    result_eval_path = OUTPUT_DIR / f"{task_id}_{suffix}_result.json"

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
    print(f"🚀 [PHASE 4A] Executing Task {task_id} ({suffix}) with model: {MODEL_ID}")
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
        with open(raw_cli_path, "w", encoding="utf-8") as f:
            json.dump({
                "conversation_id": None,
                "status": "TIMEOUT",
                "error": "Execution timed out after 600 seconds",
                "duration_seconds": 600.0,
                "num_turns": 1
            }, f, indent=2)
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

    cli_data = None
    try:
        cli_data = json.loads(raw_stdout)
    except json.JSONDecodeError:
        json_start = raw_stdout.find("{")
        json_end = raw_stdout.rfind("}")
        if json_start != -1 and json_end != -1:
            try:
                cli_data = json.loads(raw_stdout[json_start:json_end+1])
            except Exception:
                pass

    if not cli_data:
        print(f"❌ [{task_id}] Failed to parse valid JSON from agy CLI output!", file=sys.stderr)
        with open(raw_cli_path, "w", encoding="utf-8") as f:
            f.write(raw_stdout)
        return False

    with open(raw_cli_path, "w", encoding="utf-8") as f:
        json.dump(cli_data, f, indent=2, ensure_ascii=False)
    print(f"✅ [{task_id}] Saved raw CLI output to {raw_cli_path} (elapsed: {elapsed:.1f}s)")

    conv_id = cli_data.get("conversation_id")
    if not conv_id:
        print(f"❌ [{task_id}] No conversation_id found in CLI output!", file=sys.stderr)
        return False

    transcript_path = Path.home() / ".gemini/antigravity-cli/brain" / conv_id / ".system_generated/logs/transcript.jsonl"
    if not transcript_path.exists():
        transcript_path = Path.home() / ".gemini/antigravity-cli/brain" / conv_id / ".system_generated/logs/transcript_full.jsonl"

    if not transcript_path.exists():
        print(f"❌ [{task_id}] Transcript not found at {transcript_path}!", file=sys.stderr)
        return False

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
    default_tasks = ["T02", "T06", "T09", "T10", "T12"]

    if args.task:
        selected_tasks = [args.task.strip().upper()]
    elif args.tasks:
        selected_tasks = [t.strip().upper() for t in args.tasks.split(",") if t.strip()]
    else:
        selected_tasks = default_tasks

    print(f"Starting Phase 4A execution for {len(selected_tasks)} tasks: {', '.join(selected_tasks)}")
    results = {}
    for task_id in selected_tasks:
        ok = run_single_task(task_id, suffix=args.suffix, skip_existing=args.skip_existing)
        results[task_id] = "OK" if ok else "FAIL"

    print("\n================================================================================")
    print("🏁 Phase 4A Run Batch Complete")
    for t, status in results.items():
        print(f"  {t}: {status}")
    print("================================================================================")


if __name__ == "__main__":
    main()
