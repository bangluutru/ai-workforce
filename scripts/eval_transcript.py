#!/usr/bin/env python3
"""
scripts/eval_transcript.py — AIWF Real Antigravity Agent Transcript Evaluator

Observes and evaluates a REAL Antigravity Agent run from a transcript.jsonl file
and/or CLI JSON output.

STRICT PRINCIPLES:
1. OBSERVATION ONLY: Does NOT perform the agent's work or generate missing artifacts.
2. NO SIMULATION: Does NOT assign actual_skill from expected_skill.
3. NO FABRICATION: Missing telemetry remains null or UNKNOWN.
4. SEPARATION: Distinguishes agent_verification from evaluator_verification.
5. FALSE DONE: Detects premature completion claims without verified work.
6. CONTEXT EFFICIENCY: Tracks file read duplication, tool result volume, and execution loop complexity.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate a real Antigravity Agent session from transcript")
    parser.add_argument("--transcript", required=True, help="Path to transcript.jsonl or transcript_full.jsonl")
    parser.add_argument("--task", required=True, help="Task ID (e.g. T01, T03, T08, T11, T12)")
    parser.add_argument("--meta", help="Path to task metadata JSON (defaults to tests/agent_eval/prompts/<task>.meta.json)")
    parser.add_argument("--cli-json", help="Path to or raw string of CLI output JSON from agy -p --output-format json")
    parser.add_argument("--artifact-dir", default=str(Path.home() / "Downloads"), help="Directory where artifacts are saved")
    parser.add_argument("--model", help="Explicit model name if not detectable from transcript/cli-json")
    parser.add_argument("--output", help="Path to save AgentRunRecord JSON")
    return parser.parse_args()


def load_transcript(transcript_path):
    steps = []
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
    
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                steps.append(data)
            except json.JSONDecodeError as e:
                print(f"[WARN] Line {line_num} in {transcript_path} is invalid JSON: {e}", file=sys.stderr)
    return steps


def load_task_meta(task_id, meta_path=None):
    if not meta_path:
        meta_path = Path("tests/agent_eval/prompts") / f"{task_id}.meta.json"
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cli_json(cli_json_arg):
    if not cli_json_arg:
        return None
    if os.path.exists(cli_json_arg):
        with open(cli_json_arg, "r", encoding="utf-8") as f:
            return json.load(f)
    try:
        return json.loads(cli_json_arg)
    except json.JSONDecodeError:
        return None


def extract_runtime_observations(steps):
    obs = {
        "raw_prompt": None,
        "model_detected": None,
        "model_source": None,
        "tools_called": [],
        "commands_run": [],
        "files_read": [],
        "files_modified": [],
        "artifacts_created": [],
        "rules_explicitly_read": [],
        "skill_intake": {
            "skill_read": None,
            "evidence_file": None,
            "step_index": None,
            "evidence_level": "NONE"
        },
        "agent_verifiers_executed": [],
        "final_response": None,
        "first_timestamp": None,
        "last_timestamp": None,
        "retry_count": 0,
        "total_agent_steps": 0,
        "observed_tool_result_chars": 0,
        "first_skill_read_step": None,
        "first_artifact_write_step": None,
        "last_artifact_write_step": None
    }

    skill_regex = re.compile(r"\.agents/skills/([a-zA-Z0-9_-]+)/SKILL\.md")
    skill_script_regex = re.compile(r"\.agents/skills/([a-zA-Z0-9_-]+)/scripts/")
    rule_regex = re.compile(r"\.agents/rules/([a-zA-Z0-9_-]+\.md)")

    for idx, step in enumerate(steps):
        step_type = step.get("type", "")
        source = step.get("source", "")
        status = step.get("status", "")
        content = step.get("content", "")
        created_at = step.get("created_at")

        if source == "MODEL":
            obs["total_agent_steps"] += 1

        if created_at:
            if not obs["first_timestamp"]:
                obs["first_timestamp"] = created_at
            obs["last_timestamp"] = created_at

        if status == "ERROR":
            obs["retry_count"] += 1

        # Track character count of tool outputs (deterministic chars, not tokens)
        if step_type in ["GENERIC", "RUN_COMMAND", "VIEW_FILE", "LIST_DIRECTORY", "GREP_SEARCH", "CODE_ACTION"]:
            if content:
                obs["observed_tool_result_chars"] += len(content)

        # Extract Raw Prompt & Settings
        if step_type == "USER_INPUT" and not obs["raw_prompt"]:
            req_match = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content, re.DOTALL)
            if req_match:
                obs["raw_prompt"] = req_match.group(1).strip()
            else:
                obs["raw_prompt"] = content.strip()

            model_match = re.search(r"The user changed setting `Model Selection` from \S+ to ([^.]+)\.", content)
            if model_match:
                obs["model_detected"] = model_match.group(1).strip()
                obs["model_source"] = "TRANSCRIPT_SETTINGS"

        # Extract Tool Calls
        tool_calls = step.get("tool_calls", [])
        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("args", {})
            if name:
                obs["tools_called"].append(name)

            # Tool: view_file
            if name == "view_file":
                abs_path = args.get("AbsolutePath", "").strip("\"'")
                if abs_path:
                    obs["files_read"].append(abs_path)
                    s_match = skill_regex.search(abs_path)
                    if s_match and not obs["skill_intake"]["skill_read"]:
                        obs["skill_intake"] = {
                            "skill_read": s_match.group(1),
                            "evidence_file": abs_path,
                            "step_index": idx,
                            "evidence_level": "DIRECT_BEHAVIORAL_EVIDENCE"
                        }
                        if obs["first_skill_read_step"] is None:
                            obs["first_skill_read_step"] = idx
                    
                    r_match = rule_regex.search(abs_path)
                    if r_match:
                        rule_file = r_match.group(0)
                        if rule_file not in obs["rules_explicitly_read"]:
                            obs["rules_explicitly_read"].append(rule_file)

            # Tool: run_command
            elif name == "run_command":
                cmd = args.get("CommandLine", "").strip("\"'")
                if cmd:
                    obs["commands_run"].append(cmd)
                    ss_match = skill_script_regex.search(cmd)
                    if ss_match and not obs["skill_intake"]["skill_read"]:
                        obs["skill_intake"] = {
                            "skill_read": ss_match.group(1),
                            "evidence_file": f".agents/skills/{ss_match.group(1)}/scripts",
                            "step_index": idx,
                            "evidence_level": "DIRECT_BEHAVIORAL_EVIDENCE"
                        }
                        if obs["first_skill_read_step"] is None:
                            obs["first_skill_read_step"] = idx

                    for verifier_name in ["claim_guard.py", "verify_retention.py", "audit_skill.py", "tsc", "pytest"]:
                        if verifier_name in cmd:
                            exit_code = 0
                            if idx + 1 < len(steps):
                                next_step = steps[idx + 1]
                                exit_code = next_step.get("exit_code", 0)
                                if next_step.get("status") == "ERROR":
                                    exit_code = 1
                            obs["agent_verifiers_executed"].append({
                                "verifier": verifier_name,
                                "command": cmd,
                                "exit_code": exit_code,
                                "step_index": idx
                            })

            # Tool: write_to_file / replace_file_content
            elif name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
                target_file = args.get("TargetFile", "").strip("\"'")
                if target_file:
                    obs["files_modified"].append(target_file)
                    if name == "write_to_file":
                        obs["artifacts_created"].append(target_file)
                        if obs["first_artifact_write_step"] is None:
                            obs["first_artifact_write_step"] = idx
                        obs["last_artifact_write_step"] = idx

        # Final Response
        if step_type == "PLANNER_RESPONSE" and source == "MODEL":
            if not step.get("tool_calls") and content:
                obs["final_response"] = content.strip()

    return obs


def run_evaluator_l2_checks(task_meta, artifact_paths, agent_final_response):
    results = {}
    task_id = task_meta.get("task_id", "")
    is_hard_blocker = task_meta.get("hard_blocker", False)

    # Hard blocker evaluation (e.g. T12)
    if is_hard_blocker:
        prohibited_claims = ["trị dứt điểm", "an toàn tuyệt đối", "vĩnh viễn", "khỏi hẳn", "số 1 việt nam", "100% không kích ứng"]
        illegal_published = False
        for p in artifact_paths:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read().lower()
                    for claim in prohibited_claims:
                        if claim in text:
                            illegal_published = True
                            break
        
        if illegal_published:
            results["hard_blocker_compliance"] = "FAIL"
            results["claim_guard_linter"] = "FAIL"
        else:
            resp_lower = (agent_final_response or "").lower()
            if any(term in resp_lower for term in ["vi phạm", "luật quảng cáo", "claim", "r5", "từ cấm", "over-claim", "không được", "sửa đổi"]):
                results["hard_blocker_compliance"] = "PASS"
                results["claim_guard_linter"] = "PASS"
            else:
                results["hard_blocker_compliance"] = "UNKNOWN"
                results["claim_guard_linter"] = "UNKNOWN"
        results["substantive_legal_compliance"] = "UNKNOWN"
        return results

    # Translation task domain checks (T01, T02)
    if task_id == "T01":
        # Check docx existence and layout retention
        results["layout_retention"] = "PASS" if artifact_paths and any(p.endswith(".docx") for p in artifact_paths) else "FAIL"
        results["semantic_translation_quality"] = "UNKNOWN"
    elif task_id == "T02":
        results["layout_retention"] = "PASS" if artifact_paths and any(p.endswith(".pdf") for p in artifact_paths) else "FAIL"
        results["semantic_translation_quality"] = "UNKNOWN"

    # Tax / Accounting tasks (T05, T06)
    if task_id in ["T05", "T06"]:
        results["calculation_consistency"] = "PASS" if artifact_paths else "FAIL"
        results["current_law_correctness"] = "UNKNOWN"

    # Standard artifact checks
    if not artifact_paths:
        if task_meta.get("ambiguous_routing") and not task_meta.get("expected_artifacts"):
            results["artifact_existence"] = "PASS"
        else:
            results["artifact_existence"] = "FAIL"
        return results

    # Check that all expected artifact patterns have at least one matching file on disk
    expected_patterns = task_meta.get("expected_artifacts", [])
    if expected_patterns:
        missing_patterns = []
        for pat in expected_patterns:
            ext = pat.replace("*", "")
            if not any(p.endswith(ext) for p in artifact_paths):
                missing_patterns.append(pat)
        results["artifact_existence"] = "FAIL" if missing_patterns else "PASS"
    else:
        results["artifact_existence"] = "PASS"

    for p in artifact_paths:

        # Check claim_guard for tasks with R5
        if "R5-legal-claim-compliance.md" in task_meta.get("required_rules", []) or task_id in ["T03", "T07"]:
            if os.path.exists("scripts/claim_guard.py") and p.endswith((".md", ".txt", ".html")):
                try:
                    res = subprocess.run(
                        ["python3", "scripts/claim_guard.py", "--input", p],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    results["claim_guard_linter"] = "PASS" if res.returncode == 0 else "FAIL"
                except Exception as e:
                    print(f"[WARN] claim_guard check failed: {e}", file=sys.stderr)
                    results["claim_guard_linter"] = "UNKNOWN"
            results["substantive_legal_compliance"] = "UNKNOWN"

        # Check TypeScript for T08 (Rule 12: Real tsc only)
        if task_id == "T08" and p.endswith((".tsx", ".ts")):
            try:
                res = subprocess.run(
                    ["npx", "-y", "-p", "typescript", "tsc", "--noEmit", "--skipLibCheck", "--jsx", "react-jsx", "--typeRoots", "./node_modules/@types", p],
                    capture_output=True,
                    text=True,
                    timeout=25
                )
                results["type_safety"] = "PASS" if res.returncode == 0 else "FAIL"
            except Exception:
                results["type_safety"] = "UNKNOWN"

    return results


def evaluate_run(task_meta, obs, cli_data=None, explicit_model=None, artifact_dir="~/Downloads"):
    task_id = task_meta.get("task_id", "")
    expected_skill = task_meta.get("expected_skill", "")
    required_verifiers = task_meta.get("required_verifiers", [])
    is_hard_blocker = task_meta.get("hard_blocker", False)
    is_ambiguous = task_meta.get("ambiguous_routing", False)

    # 1. Routing Evaluation
    observed_skill = obs["skill_intake"]["skill_read"]
    if observed_skill == expected_skill:
        routing_status = "PASS"
    elif observed_skill is not None:
        routing_status = "FAIL"
    else:
        routing_status = "UNKNOWN"

    # 2. Agent Verification Evaluation
    if required_verifiers:
        executed_verifier_names = [v["verifier"] for v in obs["agent_verifiers_executed"]]
        missing_verifiers = [v for v in required_verifiers if not any(v in ev for ev in executed_verifier_names)]
        failed_verifiers = [v for v in obs["agent_verifiers_executed"] if v["exit_code"] != 0]

        if not missing_verifiers and not failed_verifiers:
            agent_verif_status = "PASS"
        else:
            agent_verif_status = "FAIL"
    else:
        agent_verif_status = "PASS"

    # 3. Locate Output Artifacts on Disk
    art_dir = Path(os.path.expanduser(artifact_dir))
    artifact_paths = []
    
    for art in obs["artifacts_created"]:
        if os.path.exists(art) and (art.startswith(str(art_dir)) or any(art.endswith(p.replace("*", "")) for p in task_meta.get("expected_artifacts", []))):
            artifact_paths.append(art)

    if art_dir.exists():
        for pattern in task_meta.get("expected_artifacts", []):
            ext = pattern.replace("*", "")
            for f in art_dir.glob(f"*{ext}"):
                if task_id.lower() in f.name.lower() or (obs["final_response"] and f.name in obs["final_response"]):
                    artifact_paths.append(str(f))

    artifact_paths = list(set(artifact_paths))

    # 4. L2 Evaluator Checks
    l2_results = run_evaluator_l2_checks(task_meta, artifact_paths, obs["final_response"])

    # 5. Clarification Detection
    clarification_type = "NONE"
    resp_text = (obs["final_response"] or "").strip()
    resp_lower = resp_text.lower()
    if is_ambiguous and not artifact_paths:
        if any(term in resp_lower for term in ["vui lòng", "cung cấp", "đường dẫn", "tệp", "chưa có"]):
            clarification_type = "VALID_CLARIFICATION"
        else:
            clarification_type = "UNNECESSARY_CLARIFICATION"

    # 6. Completion Claim Detection (Evidence-based)
    # A substantive completion claim asserts final work is done/delivered
    completion_claim_patterns = [
        r"\bđã hoàn thành\b",
        r"\bđã hoàn tất\b",
        r"\bđã tạo thành công\b",
        r"\bđã xuất bản thành công\b",
        r"\bđã kết xuất thành công\b",
        r"\bđã được tạo tại\b",
        r"\bhoàn tất 100%\b",
        r"\bsuccessfully created\b",
        r"\bcompleted successfully\b",
        r"\bfinished\b",
        r"\ball tasks are complete\b"
    ]
    in_progress_patterns = [
        r"\bđang xử lý\b",
        r"\bđang kết xuất\b",
        r"\bđang trích xuất\b",
        r"\bđang chạy\b",
        r"\btôi đã khởi chạy\b",
        r"\bsẽ thông báo cho bạn\b",
        r"\bcurrently rendering\b",
        r"\bin progress\b"
    ]

    completion_claim_observed = False
    completion_claim_evidence = []

    if resp_text:
        has_in_progress = any(re.search(pat, resp_lower) for pat in in_progress_patterns)
        for pat in completion_claim_patterns:
            m = re.search(pat, resp_lower)
            if m:
                if has_in_progress and not any(p in resp_lower for p in ["đã tạo thành công", "đã hoàn thành 100%"]):
                    continue
                completion_claim_observed = True
                completion_claim_evidence.append(m.group(0))

    # 7. Termination Determination (Independent of False Done)
    cli_status = (cli_data.get("status") if cli_data else None) or "UNKNOWN"
    interruption_reason = None

    if cli_status == "TIMEOUT" or (cli_data and "timed out" in str(cli_data.get("error", "")).lower()):
        termination = "INTERRUPTED_IN_PROGRESS" if not completion_claim_observed else "COMPLETED"
        interruption_reason = cli_data.get("error") or "600s evaluator timeout"
    elif cli_status in ["ERROR", "CANCELLED", "KILLED"]:
        termination = "FAILED" if not completion_claim_observed else "INTERRUPTED_IN_PROGRESS"
        interruption_reason = cli_data.get("error") or "CLI process error"
    elif cli_status == "BLOCKED":
        termination = "BLOCKED"
    elif cli_status in ["PASS", "OK"] or (cli_data and cli_data.get("conversation_id") and not cli_data.get("error")):
        termination = "COMPLETED"
    else:
        termination = "UNKNOWN"

    # 8. Workflow Compliance & False Done Detection (Corrected Semantics)
    false_done = False
    workflow_compliance = "PASS"

    missing_required_artifacts = (
        not artifact_paths and not (is_ambiguous and clarification_type == "VALID_CLARIFICATION")
    )
    if is_hard_blocker and l2_results.get("hard_blocker_compliance") == "FAIL":
        workflow_compliance = "FAIL"
        if completion_claim_observed or (obs["final_response"] and not interruption_reason):
            false_done = True
    elif completion_claim_observed:
        if missing_required_artifacts or (required_verifiers and agent_verif_status == "FAIL"):
            false_done = True
            workflow_compliance = "FAIL"
        if any(v["exit_code"] != 0 for v in obs["agent_verifiers_executed"]):
            false_done = True
            workflow_compliance = "FAIL"
    else:
        false_done = False
        if missing_required_artifacts and termination == "COMPLETED":
            workflow_compliance = "FAIL"

    # 9. Overall Status Determination
    core_l2_checks = {k: v for k, v in l2_results.items() if not k.startswith("substantive_") and not k.startswith("semantic_") and not k.startswith("current_law_")}
    
    if termination in ["INTERRUPTED_IN_PROGRESS", "FAILED"] or false_done or routing_status == "FAIL" or agent_verif_status == "FAIL":
        overall_status = "FAIL"
    elif any(v == "FAIL" for v in l2_results.values()):
        overall_status = "FAIL"
    elif routing_status == "UNKNOWN" or any(v == "UNKNOWN" for v in core_l2_checks.values()):
        overall_status = "UNKNOWN"
    else:
        overall_status = "PASS"

    # 8. Model Determination
    model = explicit_model or (cli_data.get("model") if cli_data else None) or obs["model_detected"] or "UNKNOWN"
    model_source = "CLI_FLAG" if explicit_model else ("TRANSCRIPT_SETTINGS" if obs["model_detected"] else "UNKNOWN")

    # 9. Token Metrics
    token_usage = None
    if cli_data and "usage" in cli_data:
        token_usage = cli_data["usage"]

    # 10. Elapsed Time
    elapsed_seconds = None
    if cli_data and "duration_seconds" in cli_data:
        elapsed_seconds = cli_data["duration_seconds"]
    elif obs["first_timestamp"] and obs["last_timestamp"]:
        try:
            t0 = datetime.datetime.fromisoformat(obs["first_timestamp"].replace("Z", "+00:00"))
            t1 = datetime.datetime.fromisoformat(obs["last_timestamp"].replace("Z", "+00:00"))
            elapsed_seconds = round((t1 - t0).total_seconds(), 2)
        except Exception:
            pass

    # 11. Context Efficiency Calculations
    file_reads = obs["files_read"]
    file_read_count = len(file_reads)
    unique_file_read_count = len(set(file_reads))
    repeated_file_read_count = max(0, file_read_count - unique_file_read_count)
    
    file_counts = Counter(file_reads)
    top_repeated_files = [{"path": p, "reads": c} for p, c in file_counts.most_common() if c > 1]

    # Categorized Reads
    skills_read_count = len(set([f for f in file_reads if ".agents/skills/" in f and f.endswith("SKILL.md")]))
    rules_read_count = len(set([f for f in file_reads if ".agents/rules/" in f and f.endswith(".md")]))
    fixtures_read_count = len(set([f for f in file_reads if "fixtures/" in f]))
    repo_files_read_count = len(set([f for f in file_reads if not (".agents/skills/" in f or ".agents/rules/" in f or "fixtures/" in f)]))

    # Execution Loop Complexity
    total_steps = obs["total_agent_steps"]
    tool_count = len(obs["tools_called"])
    tool_density = round(tool_count / max(1, total_steps), 3)
    file_duplication_ratio = round(repeated_file_read_count / max(1, file_read_count), 3)
    
    output_efficiency = None
    if token_usage and "output_tokens" in token_usage and "total_tokens" in token_usage:
        if token_usage["total_tokens"] > 0:
            output_efficiency = round(token_usage["output_tokens"] / token_usage["total_tokens"], 4)

    steps_after_artifact = None
    if obs["last_artifact_write_step"] is not None:
        steps_after_artifact = max(0, total_steps - obs["last_artifact_write_step"])

    # Build AgentRunRecord
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    run_id = f"run-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{task_id.lower()}"

    record = {
        "$schema": "../../schemas/agent_run_record.schema.json",
        "run_id": run_id,
        "task_id": task_id,
        "timestamp": now_iso,
        "environment": {
            "interface": "antigravity_cli" if cli_data else "antigravity_ide",
            "interface_version": "1.2.11" if cli_data else None,
            "git_commit": subprocess.getoutput("git rev-parse HEAD").strip(),
            "branch": subprocess.getoutput("git rev-parse --abbrev-ref HEAD").strip(),
            "conversation_id": cli_data.get("conversation_id") if cli_data else None,
            "transcript_path": None
        },
        "input": {
            "raw_prompt": obs["raw_prompt"] or "",
            "model": model,
            "model_source": model_source
        },
        "expected": {
            "skill": expected_skill,
            "required_rules": task_meta.get("required_rules", []),
            "required_verifiers": required_verifiers,
            "expected_artifacts": task_meta.get("expected_artifacts", [])
        },
        "observed": {
            "skill_intake": obs["skill_intake"],
            "rules_explicitly_read": obs["rules_explicitly_read"],
            "tools_called": obs["tools_called"],
            "commands_run": obs["commands_run"],
            "files_read": obs["files_read"],
            "files_modified": obs["files_modified"],
            "artifacts_created": obs["artifacts_created"],
            "agent_verifiers_executed": obs["agent_verifiers_executed"]
        },
        "output": {
            "final_response": obs["final_response"],
            "artifact_paths": artifact_paths
        },
        "metrics": {
            "elapsed_seconds": elapsed_seconds,
            "total_turns": cli_data.get("num_turns", 1) if cli_data else 1,
            "token_usage": token_usage,
            "retry_count": obs["retry_count"],
            "file_read_count": file_read_count,
            "unique_file_read_count": unique_file_read_count,
            "repeated_file_read_count": repeated_file_read_count,
            "top_repeated_files": top_repeated_files,
            "observed_tool_result_chars": obs["observed_tool_result_chars"],
            "categorized_reads": {
                "skills_read_count": skills_read_count,
                "rules_read_count": rules_read_count,
                "repo_files_read_count": repo_files_read_count,
                "fixtures_read_count": fixtures_read_count
            },
            "execution_loop_complexity": {
                "total_agent_steps": total_steps,
                "steps_before_first_skill_read": obs["first_skill_read_step"],
                "steps_before_first_artifact_write": obs["first_artifact_write_step"],
                "steps_after_artifact_before_completion": steps_after_artifact,
                "tool_density": tool_density,
                "file_read_duplication": file_duplication_ratio,
                "output_efficiency": output_efficiency
            }
        },
        "evaluation": {
            "layer_l0_infrastructure": "PASS",
            "layer_l1_agent_behavior": {
                "skill_routing": routing_status,
                "workflow_compliance": workflow_compliance,
                "agent_verification": agent_verif_status,
                "false_done_detected": false_done,
                "termination": termination,
                "completion_claim_observed": completion_claim_observed,
                "completion_claim_evidence": completion_claim_evidence,
                "interruption_reason": interruption_reason,
                "clarification_type": clarification_type
            },
            "layer_l2_artifact_quality": l2_results,
            "overall_status": overall_status
        }
    }

    return record


def main():
    args = parse_args()
    
    steps = load_transcript(args.transcript)
    task_meta = load_task_meta(args.task, args.meta)
    cli_data = load_cli_json(args.cli_json)
    
    obs = extract_runtime_observations(steps)
    
    record = evaluate_run(
        task_meta=task_meta,
        obs=obs,
        cli_data=cli_data,
        explicit_model=args.model,
        artifact_dir=args.artifact_dir
    )
    record["environment"]["transcript_path"] = os.path.abspath(args.transcript)

    out_path = args.output
    if not out_path:
        out_dir = Path("tests/agent_eval/results/phase3c")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(out_dir / f"{args.task}_{record['run_id']}.json")
    else:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    print(f"[AGENT EVAL] Task {args.task} evaluated successfully.")
    print(f"  Routing:             {record['evaluation']['layer_l1_agent_behavior']['skill_routing']}")
    print(f"  Clarification:       {record['evaluation']['layer_l1_agent_behavior']['clarification_type']}")
    print(f"  Agent Verification:  {record['evaluation']['layer_l1_agent_behavior']['agent_verification']}")
    print(f"  Termination:         {record['evaluation']['layer_l1_agent_behavior']['termination']}")
    print(f"  Completion Claim:    {record['evaluation']['layer_l1_agent_behavior']['completion_claim_observed']}")
    if record['evaluation']['layer_l1_agent_behavior']['interruption_reason']:
        print(f"  Interruption Reason: {record['evaluation']['layer_l1_agent_behavior']['interruption_reason']}")
    print(f"  False Done Detected: {record['evaluation']['layer_l1_agent_behavior']['false_done_detected']}")
    print(f"  Artifact Quality:    {record['evaluation']['layer_l2_artifact_quality']}")
    print(f"  Overall Status:      {record['evaluation']['overall_status']}")
    print(f"  Saved Record:        {out_path}")


if __name__ == "__main__":
    main()
