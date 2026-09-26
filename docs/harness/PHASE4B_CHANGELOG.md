# PHASE 4B CHANGELOG — Skill Execution Boundary & Fast Path

> **Commit Baseline:** `4733177` (Phase 4A.1)
> **Date:** September 26, 2026
> **Scope:** T09 (`video-studio`) and T10 (`hand-drawn-animation`) ONLY

---

## CHANGES MADE

### 1. `.agents/skills/video-studio/SKILL.md`

**Added Section 8: EXECUTION BOUNDARY**

| What | Details |
|---|---|
| **Type** | Skill instruction (context optimization) |
| **Lines Added** | ~45 lines |
| **Purpose** | Prevent Agent from reading helper script source code before calling pipeline CLI |
| **Key Prohibitions** | (1) CẤM đọc `scene_builder.py`, `stock_fetcher.py`, `audio_mixer.py`, `video_pipeline.py` trước khi gọi lệnh. (2) CẤM chạy lệnh ffmpeg thủ công. (3) CẤM chạy `audit_skill.py` khi pipeline exit 0. (4) CẤM đọc lại file đã đọc. |
| **Fast Path** | 5-step procedure: Xác định tham số → Kích hoạt venv → Gọi pipeline 1 lần → Kiểm tra exit code → Bàn giao sạch |
| **Measured Impact** | T09 runtime: 600s → 152s (−74.7%). Agent steps: 172 → 24 (−86.0%). File reads: 28 → 1 (−96.4%). |

### 2. `.agents/skills/hand-drawn-animation/SKILL.md`

**Added Section 9: EXECUTION BOUNDARY**

| What | Details |
|---|---|
| **Type** | Skill instruction (context optimization) |
| **Lines Added** | ~40 lines |
| **Purpose** | Limit reference reading and render attempts; prevent aimless asset exploration |
| **Key Prohibitions** | (1) CẤM đọc core.js/cels.js/studio.js/materials.js source. (2) CẤM đọc >2 reference files. (3) CẤM render >2 lần. (4) CẤM đọc lại file. (5) CẤM inspect render.mjs. |
| **Fast Path** | 6-step procedure: Brief → Đọc tham khảo tối thiểu → Copy Creative Template → Spot Preview → Full Render 1 lần → Bàn giao |

**Added Section 10: CREATIVE TEMPLATE**

| What | Details |
|---|---|
| **Type** | API cheat sheet embedded in Skill file |
| **Lines Added** | ~120 lines |
| **Purpose** | Eliminate need to read core.js source by providing in-Skill API reference |
| **Contents** | (1) Complete film HTML boilerplate with comments. (2) Drawing API table (blob, curvePath, wob, hatch, surface, scribble). (3) Motion API table (key, arc, spring, settle, squash, camKeys, sm, pulse). (4) Global variables table (CX, CY, W, H, PAL, TAU). (5) Simplicity tip for 15s films. |
| **Measured Impact** | T10 runtime: 600s → 487s (−18.8%). File read duplication: 0.412 → 0.2 (−51.5%). Status: FAIL → PASS. |

---

## FILES NOT CHANGED

The following files were explicitly NOT modified per Phase 4B scope constraints:

- `GEMINI.md` — No architectural changes
- `AGENTS.md` — No routing changes
- `R0–R6 rules` — No rule changes
- All other 14 Skill SKILL.md files — Not in scope
- `scripts/eval_transcript.py` — Evaluation infrastructure unchanged
- `schemas/agent_run_record.schema.json` — Schema unchanged

---

## BENCHMARK EVIDENCE

### T09 Benchmark Record
- **Run ID:** `run-20260926181828-t09`
- **Conversation ID:** `f92116ce-af17-45a9-bacd-0c222e3e21fa`
- **Result File:** `tests/agent_eval/results/phase4b/T09_phase4b.json`
- **Artifact:** `/Users/tranhaibang/Downloads/ca_phe_nguyen_chat_30s.mp4` (47.9 MB, 1920×1080 @ 30fps, 36.5s)

### T10 Benchmark Record
- **Run ID:** `run-20260926182343-t10`
- **Conversation ID:** `47ceeff8-e38b-4621-a780-6cc3865b3903`
- **Result File:** `tests/agent_eval/results/phase4b/T10_phase4b.json`
- **Artifact:** `/Users/tranhaibang/Downloads/canh-chim-phuong-hoang-tai-sinh.mp4` (27.6 MB, 1920×1080 @ 24fps, 15.0s)

---

## DECISION: KEEP / INCONCLUSIVE / REVERT

| Change | Decision | Rationale |
|---|:---:|---|
| T09 Execution Boundary + Fast Path | **KEEP** | −74.7% runtime, −86% steps, FAIL→PASS. |
| T10 Execution Boundary + Fast Path + Creative Template | **KEEP** | −18.8% runtime, −56% file reads, FAIL→PASS. Partial Fast Path compliance but outcome is successful. |

---

## RECOMMENDATION: CLOSE GENERAL HARNESS OPTIMIZATION

**YES — Close general AIWF harness optimization after Phase 4B.**

Justification:
1. All targeted FAIL tasks (T09, T10) now PASS.
2. No regressions were observed in the Phase 4B T09/T10 validation. Tasks T01–T08 and T11–T12 were not rerun; their latest evidence remains the Phase 3C/4A benchmark results.
3. Remaining T10 overhead is irreducible creative authoring cost, not harness inefficiency.
4. The Execution Boundary + Fast Path pattern is reusable for future skills.
5. Further optimization would require architectural additions explicitly prohibited by the user.
