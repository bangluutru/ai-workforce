# ANTIGRAVITY AGENT EVALUATION CAPABILITIES AUDIT

> **Status:** Completed Feasibility Audit (AIWF Phase 3A)  
> **Baseline Commit:** `d820d8d`  
> **Date:** September 2026  
> **Primary Question:** *Can Antigravity currently execute a real Agent session from a raw user prompt and expose enough runtime evidence to evaluate AIWF behavior?*

---

## 1. Executive Summary

This audit evaluates the real-world, native runtime observability and execution mechanisms provided by the Google Antigravity platform (version 2.11.0 / CLI 1.2.11). 

The goal of AIWF Phase 3A is strictly factual: **determine what can be observed directly from an actual Antigravity Agent run versus what is inferred, simulated, or unavailable**.

### Key Findings:
1. **Two Distinct Native Interfaces Exist:**
   - **Antigravity IDE (GUI):** Built on VS Code architecture with `language_server_macos_arm`. User-interactive, session-managed. Transcripts are written to `~/.gemini/antigravity-ide/brain/<conv_id>/.system_generated/logs/transcript.jsonl`.
   - **Antigravity CLI (`agy` v1.2.11):** Standalone terminal agent binary located at `/Users/tranhaibang/.local/bin/agy`. Supports headless print mode (`agy -p "<prompt>" --output-format json`) with real multi-step execution, token telemetry, and transcript storage in `~/.gemini/antigravity-cli/brain/<conv_id>/`.
2. **Programmatic Headless Execution:**
   - **Antigravity IDE companion CLI (`agentapi new-conversation`):** **FAILS headlessly** with `rpc error: code = Unknown desc = project_id is required when providing project_env_config`. The IDE internal RPC daemon requires GUI session context.
   - **Antigravity CLI (`agy -p`):** **SUCCEEDS headlessly**. It can receive raw prompts programmatically, execute tools, respect workspace boundaries, and output structured execution JSON.
3. **Runtime Observability:**
   - Tool calls (`view_file`, `run_command`, `replace_file_content`, `write_to_file`, `call_mcp_tool`) and their parameters are **directly observable and 100% reliable** via `transcript.jsonl`.
   - Skill activation is **NOT a native telemetry event**, but is **observably evidenced** when the agent reads `.agents/skills/<skill>/SKILL.md` or executes scripts in `.agents/skills/<skill>/scripts/`.
   - Automatic Rule injection (`GEMINI.md`, `.agents/rules/*.md`) is baked into the initial prompt context (~85,000 input tokens) but individual injected rule boundaries are **not logged as distinct events** in `transcript.jsonl`.
   - Token and context usage metrics are **unavailable in IDE transcripts**, but are **natively exposed in `agy` CLI JSON outputs**.

---

## 2. Antigravity Native Capability Matrix

| Capability | Native Support | Mechanism | Programmatic? | Observable? | Reliable? | Observed Evidence & Limitations |
|:---|:---:|:---|:---:|:---:|:---:|:---|
| **Start Agent session** | **YES** (CLI) / **NO** (IDE RPC) | `agy -p "<prompt>"` (CLI) vs `agentapi new-conversation` (IDE) | **YES** via `agy` / **NO** via `agentapi` | **YES** | **YES** (CLI) / **NO** (IDE) | **Observed:** `agy -p` starts a real agent turn with exit code 0. `agentapi new-conversation` fails with RPC error (`project_id is required`). |
| **Submit raw prompt** | **YES** | Command-line argument, stdin stream (`--input-format stream-json`), or IDE chat input | **YES** | **YES** | **YES** | **Observed:** Prompt appears as `step_index: 0`, `source: "USER_EXPLICIT"`, `type: "USER_INPUT"` in `transcript.jsonl`. |
| **Select model** | **YES** | CLI flag `--model=<name>` (e.g. `gemini-3.8-flash-high`, `claude-sonnet-4-6`) or IDE GUI dropdown | **YES** (CLI) / **NO** (IDE) | **YES** (CLI) / **PARTIAL** (IDE) | **YES** (CLI) / **NO** (IDE) | **Observed:** `agy models` lists 14 available models. IDE metadata (`get-conversation-metadata`) leaves `modelName` blank. |
| **Observe Skill selected** | **INFERRED** | Agent calling `view_file` on `.agents/skills/<skill>/SKILL.md` or running skill scripts | **YES** (via transcript parser) | **INFERRED** (File read) | **HIGH** (Behavioral) | **Limitation:** No native `skill_activated` telemetry event exists. Skill intake is evidenced by the agent reading the skill's `SKILL.md`. |
| **Observe Rules loaded** | **PARTIAL** | System prompt compilation + explicit `view_file` calls | **NO** (Injection) / **YES** (Explicit read) | **PROXY** (Token count) / **DIRECT** (File read) | **LOW** (Injection) / **HIGH** (Explicit) | **Observed:** Baseline prompt has ~85,000 tokens due to injected rules, but transcript does not emit rule ingestion events. |
| **Observe tool calls** | **YES** | `transcript.jsonl` logged by Antigravity runtime | **YES** | **YES** | **YES** | **Observed:** Every tool call is captured with exact tool name, arguments, and step index under `tool_calls: [...]`. |
| **Observe shell commands** | **YES** | `transcript.jsonl` under `tool_calls` where `name == "run_command"` + step `type == "GENERIC"` for stdout/stderr | **YES** | **YES** | **YES** | **Observed:** Exact `CommandLine`, `Cwd`, output content, and `exit_code` are logged. |
| **Observe file reads** | **YES** | `transcript.jsonl` under `tool_calls` where `name == "view_file"` | **YES** | **YES** | **YES** | **Observed:** `AbsolutePath`, `StartLine`, `EndLine`, and returned lines are captured in full. |
| **Observe file edits** | **YES** | `transcript.jsonl` (`replace_file_content`, `write_to_file`) + Git status/diff | **YES** | **YES** | **YES** | **Observed:** Target file, instructions, replacement text, and diffs are captured. |
| **Observe verification** | **INFERRED** | Tool call invoking verifier (`claim_guard.py`, `verify_retention.py`, `audit_skill.py`, test runners) | **YES** | **YES** (Tool call) | **HIGH** (Behavioral) | **Limitation:** No special "Verification" event type. Verification is detected by auditing commands run and their exit codes. |
| **Capture final response** | **YES** | `PLANNER_RESPONSE` in `transcript.jsonl` or `"response"` key in `agy` CLI JSON | **YES** | **YES** | **YES** | **Observed:** Final assistant text is recorded verbatim in both transcript and CLI stdout. |
| **Capture artifact** | **YES** | File written to `<output_dir>` or `<appDataDir>/brain/<id>/` | **YES** | **YES** | **YES** | **Observed:** Output artifacts are tangible files on disk; their creation is logged in transcript via `write_to_file`. |
| **Token/context metrics** | **YES** (CLI) / **NO** (IDE) | `agy --output-format json` exposes `usage` object; IDE `transcript.jsonl` does not | **YES** (CLI) / **NO** (IDE) | **YES** (CLI) / **NO** (IDE) | **YES** (CLI) / **UNAVAILABLE** (IDE) | **Observed:** `agy` reports `input_tokens`, `output_tokens`, `thinking_tokens`, `cache_read_tokens`, `total_tokens`. IDE omits all token data. |
| **Elapsed time** | **YES** | `agy` `"duration_seconds"` or timestamp delta in `transcript.jsonl` (`created_at`) | **YES** | **YES** | **YES** | **Observed:** Precision down to microseconds in CLI, millisecond ISO-8601 timestamps in transcript. |
| **Subagent trace** | **PARTIAL** | `invoke_subagent` or `browser_subagent` tool calls in parent transcript | **YES** | **YES** | **MEDIUM** | **Observed:** Parent logs the subagent invocation and returned report. Child transcript resides in a separate conversation ID. |
| **Observe MCP calls** | **YES** | `transcript.jsonl` under `call_mcp_tool` or `mcp_<server>_<tool>` | **YES** | **YES** | **YES** | **Observed:** Server name, tool name, and arguments are recorded in step `tool_calls`. |
| **Lifecycle Hooks** | **YES** | Native `hooks.json` in `.agents/hooks.json` or `~/.gemini/config/hooks.json` | **YES** | **YES** | **YES** | **Observed:** `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, and `Stop` hooks pass JSON payload via stdin. |

---

## 3. Deep-Dive: Skill Activation Observability

### Direct Observation vs. Behavioral Inference
A critical requirement of Phase 3A is establishing whether Skill selection can be directly observed or must be behaviorally inferred.

1. **Native Telemetry Event:**
   - **Result:** **NO.** Antigravity has no `SkillActivated` or `SkillLoaded` step type in `transcript.jsonl`.
   - The step types observed in actual execution are:
     `['CHECKPOINT', 'CODE_ACTION', 'CONVERSATION_HISTORY', 'ERROR_MESSAGE', 'GENERIC', 'GREP_SEARCH', 'KNOWLEDGE_ARTIFACTS', 'LIST_DIRECTORY', 'PLANNER_RESPONSE', 'RUN_COMMAND', 'SEARCH_WEB', 'SYSTEM_MESSAGE', 'USER_INPUT', 'VIEW_FILE']`.
2. **Behavioral Inference (High Fidelity):**
   - When an Antigravity Agent routes a task to a skill, it follows the system instructions in `GEMINI.md` and reads the skill's instructions.
   - **Observable Signal 1:** A `view_file` tool call with `AbsolutePath` ending in `.agents/skills/<skill-name>/SKILL.md`.
   - **Observable Signal 2:** A `run_command` tool call executing a script inside `.agents/skills/<skill-name>/scripts/`.
3. **The Anti-Hallucination Routing Boundary:**
   - If an Agent produces an output artifact (e.g., an HTML leaflet) but the transcript shows **NO** read of `.agents/skills/thiet-ke/SKILL.md` and **NO** execution of `thiet-ke` scripts:
     - The benchmark **MUST NOT** score this as `actual_skill = "thiet-ke"`.
     - It must be recorded as `observed.skill = null` (or `routing = UNVERIFIED`).
   - Merely producing an artifact does not prove that the Skill was loaded.

---

## 4. Deep-Dive: Rule Ingestion & Observability

How does Antigravity expose rules (`GEMINI.md`, `R0`–`R6`)?

1. **System Prompt Injection (Implicit):**
   - Antigravity's core engine scans the workspace root and `.agents/rules/` and injects their contents directly into the system instructions before the first user turn.
   - **Evidence:** An initial prompt to `agy` consumed **84,894 input tokens** before reading any files. This confirms that all repository rules and skill summaries were compiled into the initial model context.
   - **Limitation:** The transcript does NOT emit an event showing which individual rule files were injected.
2. **Explicit Reading (Observable):**
   - If the Agent calls `view_file` on `.agents/rules/R5-legal-claim-compliance.md` or `.agents/rules/R6-document-layout-preservation.md`, this is recorded verbatim as a `VIEW_FILE` step.
3. **Rule Enforcement Observability:**
   - We cannot measure "did the agent read the injected rule in its mind".
   - We CAN measure "did the agent violate the rule's deterministic invariant":
     - For `R0` (Git Sync): Did the agent write files outside the workspace or untracked paths?
     - For `R1` (Zero Destruction): Did the agent create `_Delete` or `_Archive` folders?
     - For `R4` (Skill Standards): Did the agent pass `audit_skill.py`?
     - For `R5` (Legal Claim Compliance): Did the generated text pass `claim_guard.py`?
     - For `R6` (Retain PDF): Did the output pass `verify_retention.py`?

---

## 5. Deep-Dive: Model Identification

Can the benchmark reliably record which model executed the task?

1. **In Antigravity CLI (`agy`):**
   - **YES (100% Reliable).**
   - The CLI accepts an explicit `--model` argument:
     - `gemini-3.8-flash-high`
     - `gemini-3.8-flash-medium`
     - `gemini-3.8-flash-low`
     - `gemini-3.7-flash-high`
     - `gemini-3.1-pro-high`
     - `claude-sonnet-4-6`
     - `claude-opus-4-6-thinking`
     - `gpt-oss-120b-medium`
   - In addition, the transcript explicitly records the model change in the user turn:
     `<USER_SETTINGS_CHANGE> The user changed setting \`Model Selection\` from None to Gemini 3.8 Flash (High). ... </USER_SETTINGS_CHANGE>`.
2. **In Antigravity IDE (GUI):**
   - **PARTIAL / UNRELIABLE.**
   - `agentapi get-conversation-metadata <id>` returns `modelName: ""` (empty string).
   - If the user switches models in the GUI dropdown, a `<USER_SETTINGS_CHANGE>` message may be injected into the transcript, but on initial sessions starting with the default model, the model name is omitted from the transcript schema.
3. **Conclusion for Evaluation:**
   - Any automated benchmark running via `agy` can explicitly record and enforce the model identifier.
   - Interactive IDE evaluations must record the model via human attestation or manual run metadata.

---

## 6. Deep-Dive: Token & Context Telemetry

| Telemetry Metric | In Antigravity IDE (`transcript.jsonl`) | In Antigravity CLI (`agy --output-format json`) |
|:---|:---:|:---:|
| `input_tokens` | ❌ UNAVAILABLE | ✅ EXACT (`47746`) |
| `output_tokens` | ❌ UNAVAILABLE | ✅ EXACT (`521`) |
| `thinking_tokens` | ❌ UNAVAILABLE | ✅ EXACT (`333`) |
| `cache_read_tokens` | ❌ UNAVAILABLE | ✅ EXACT (`36765`) |
| `total_tokens` | ❌ UNAVAILABLE | ✅ EXACT (`48267`) |
| Context size limit | ❌ UNAVAILABLE | ❌ UNAVAILABLE |

**Strict Audit Finding:**  
Token counts must NEVER be estimated or calculated via heuristics (e.g., character count / 4). When evaluating IDE runs, `token_usage` must be recorded as `null` or `UNKNOWN`. When evaluating `agy` CLI runs, exact token metrics from the native output JSON can be recorded.

---

## 7. Deep-Dive: Native Lifecycle Hooks (`hooks.json`)

Antigravity natively implements lifecycle hooks defined in `hooks.json` (supported locations: `.agents/hooks.json` or `~/.gemini/config/hooks.json`).

Supported Event Types:
- `PreToolUse`: Fires before any tool step. Input JSON includes `toolCall`, `stepIdx`, `conversationId`, `workspacePaths`, `transcriptPath`, `artifactDirectoryPath`, `modelName`. Returns `{"decision": "allow" | "deny" | "ask"}`.
- `PostToolUse`: Fires after a tool completes. Receives `stepIdx`, `error` (if failed), and system metadata.
- `PreInvocation`: Fires before the model is called. Can inject steps (`userMessage`, `ephemeralMessage`).
- `PostInvocation`: Fires after model generation. Can set `terminationBehavior: "force_continue" | "terminate"`.
- `Stop`: Fires when the agent loop is about to terminate. Receives `executionNum`, `terminationReason: "model_stop" | "error"`, `fullyIdle`. Can return `{"decision": "continue", "reason": "..."}` to block premature completion.

**Feasibility Significance:**  
While Phase 3A prohibits installing a new quality harness or Stop Hook yet, this capability proves that Antigravity provides the native architecture for non-intrusive runtime auditing and completion gating in future phases.

---

## 8. Summary of What Can and Cannot Be Observed Today

### What CAN Be Directly Observed:
1. Exact tool calls with all input arguments (`transcript.jsonl`).
2. Exact shell commands executed and their exit codes/outputs (`run_command`).
3. Exact files read (`view_file`) and written (`write_to_file`, `replace_file_content`).
4. Exact elapsed execution time (`duration_seconds` or timestamp deltas).
5. Exact final text response from the agent.
6. Resulting output artifacts on disk.
7. Token usage breakdown (in `agy` CLI).
8. Model selected (in `agy` CLI).

### What CANNOT Be Directly Observed (Must be Inferred or Handled Manually):
1. Native `skill_selected` event (must be inferred from reading `SKILL.md` or running skill scripts).
2. Rule injection breakdown (rules are silently compiled into the initial system context).
3. Token usage in the IDE GUI (must be marked `null`/`UNKNOWN`).
4. Model name in initial IDE GUI sessions (must be recorded manually).
5. "Mind state" / reasoning validity without inspecting `thinking` blocks or tool evidence.
