# AIWF MEDIA ISOLATION & COMPUTE COST REPORT (PHASE 4A.1)

> **Repository:** `bangluutru/ai-workforce`  
> **Commit Baseline:** `cf3162d`  
> **Objective:** Isolate physical media pipeline and render engine compute costs from Antigravity Agent/AIWF reasoning overhead for tasks T09 (`video-studio`) and T10 (`hand-drawn-animation`).  
> **Date:** September 26, 2026  
> **Hardware:** Apple Silicon (macOS)  

---

## 1. EXECUTIVE SUMMARY & CORE FINDINGS

In Phase 3C and Phase 4A, both T09 and T10 exhibited extended runtimes reaching or exceeding the 600-second execution envelope. A central hypothesis was that media rendering compute (ffmpeg encoding, canvas frame capture in headless browser) was inherently so slow that it exceeded the benchmark envelope.

**The Phase 4A.1 controlled experiments disprove that hypothesis with direct measurement:**
1. **T09 Direct Pipeline Compute:** Running `video_pipeline.py` directly without Agent reasoning takes only **76.63 seconds** (outputting a 1080p, 30fps MP4 with smart ducking and burned-in subtitles).
2. **T10 Direct Render Compute:** Running `render.mjs` directly on the exact generated Canvas 2D HTML film takes only **52.98 seconds** for 360 frames (24fps 1080p) and only **29.21 seconds** for 180 frames (12fps 1080p).
3. **Bottleneck Reality:** In both media tasks, the rendering engines are fast and consume only **8.8% to 12.8%** of the 600s budget. The remaining **87.2% to 91.2%** of the time is consumed by **Agent tool-loop overhead** (authoring generation code from scratch, reading source files repeatedly, running multiple debugging commands, and re-checking intermediate files).

---

## 2. TASK T09 MEDIA ISOLATION (`video-studio`)

### 2.1 Direct Pipeline Execution vs Real Agent Run

| Metric | Direct Pipeline Run (`video_pipeline.py`) | Real Agent Run (Phase 4A) | Variance / Overhead |
|---|:---:|:---:|:---:|
| **Execution Mode** | Direct CLI invocation (No Agent) | Antigravity Agent (`gemini-3.8-flash-high`) | - |
| **Wall-Clock Runtime** | **76.63 seconds** | **600.00 seconds** (Timeout) | **+523.37 seconds (Agent overhead)** |
| **Core Compute Share** | **12.8%** of 600s envelope | - | - |
| **Exit Status** | Exit code 0 (PASS) | Process Timed Out | - |
| **Termination Semantics** | `COMPLETED` | `INTERRUPTED_IN_PROGRESS` | Evaluator correction |
| **Output Artifact** | `/Users/tranhaibang/Downloads/direct_test_caphe_30s.mp4` | Generated, not delivered before timeout | - |
| **Artifact Resolution** | 1920x1080 @ 30fps | 1920x1080 @ 30fps | Identical |
| **Audio & Ducking** | AAC @ 256k, Smart Ducking -14dB | AAC @ 256k, Smart Ducking -14dB | Identical |
| **Subtitles Burn-in** | 456 frames (PASS) | 456 frames (PASS) | Identical |
| **Output Size** | 20.63 MB | ~20 MB | Identical |
| **Stdout/Stderr Chars** | 3,507 chars stdout / 0 stderr | 119,786 chars | -97.1% chars |
| **Agent Steps** | 0 | 172 | - |
| **Tool Calls** | 0 | 86 | - |
| **File Reads** | 0 | 28 (11 unique, 17 repeated) | - |
| **Top Repeated Reads** | None | `scene_builder.py` (12), `video_pipeline.py` (6) | - |

### 2.2 T09 Change Decomposition

Phase 4A introduced changes into the video pipeline. Their explicit functional classifications are:

| File Modified | Exact Change | Category | Impact on Pipeline |
|---|---|:---:|---|
| `SKILL.md` | Documented canonical `video_pipeline.py` syntax | `CONTEXT_INTERFACE` | Provided Agent with clear flags (`--topic`, `--output`, `--mood`, `--ducking`, `--json`). |
| `video_pipeline.py` | Added `--json` machine-readable output summary | `OUTPUT_VERBOSITY` | Emits concise JSON block; reduces token bloat in Agent context. |
| `video_pipeline.py` | Added `--script <path>`, `--ducking <dB>`, `--voice <name>` | `CONTEXT_INTERFACE` | Allows passing custom parameters without editing Python files. |
| `video_pipeline.py` | Relocated temp cache to `_<slug>_cache` | `FUNCTIONAL_FIX` | Prevents workspace bloat (Rule R1 compliance). |
| `scene_builder.py` | Quiet FFmpeg invocation (`-v error`, stderr to DEVNULL) | `OUTPUT_VERBOSITY` | Suppresses hundreds of routine progress lines. |
| `scene_builder.py` | Added `-pix_fmt yuv420p` | `BUG_FIX` | Ensures QuickTime / Apple Silicon compatibility for MP4 playback. |
| `scene_builder.py` | Replaced `encoder.wait` with `encoder.communicate(timeout=60)` | `BUG_FIX` | Prevents FFmpeg stdin/stdout pipe deadlock on long renders. |
| `audio_mixer.py` | Tuned normalization parameters | `FUNCTIONAL_FIX` | Prevents clipping when ducking music under narration. |

### 2.3 T09 Bottleneck Classification
* **Classification:** **HARNESS_DOMINANT** (Specifically: Agent tool-loop iteration & autonomous debugging behavior).
* **Rationale:** The video pipeline executes end-to-end in 76.6s. The reason T09 timed out at 600s was that the Agent spent over 520s inspecting `scene_builder.py` (12 times) and `video_pipeline.py` (6 times), writing custom JSON scripts, and running ancillary audit scripts (`audit_skill.py`) instead of simply executing the pipeline once and stopping.

---

## 3. TASK T10 MEDIA ISOLATION (`hand-drawn-animation`)

### 3.1 Direct Render Compute Benchmark (`render.mjs`)

Using the exact HTML Canvas 2D artifact generated during Phase 4A (`/Users/tranhaibang/Downloads/canh-chim-phuong-hoang-tai-sinh.html`), we executed `render.mjs` directly in Headless Chrome:

| Render Configuration | Frame Count | Requested FPS | Resolution | Frame Render Time | FFmpeg Mux Time | Total Wall-Clock | MP4 Size | Exit Code |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **12 FPS (Archival Standard)** | **180 frames** | 12 fps | 1920x1080 | ~26.5s | ~2.7s | **29.21s** | 16.90 MB | 0 (PASS) |
| **24 FPS (Default Standard)** | **360 frames** | 24 fps | 1920x1080 | ~48.2s | ~4.8s | **52.98s** | 24.24 MB | 0 (PASS) |
| **Spot Preview (`--only 0`)** | **1 frame** | - | 1920x1080 | ~1.8s | 0s | **2.10s** | - | 0 (PASS) |

### 3.2 Comparison with Real Agent Run

| Metric | Direct 24fps Render | Real Agent Run (Phase 4A) | Real Agent Run (Phase 3C) |
|---|:---:|:---:|:---:|
| **Runtime** | **52.98 seconds** | **600.00 seconds** (Timeout) | **600.00 seconds** (Timeout) |
| **Render Compute Share** | **8.8%** of 600s envelope | - | - |
| **Agent Overhead Time** | 0s | **>547.02 seconds (~91.2%)** | **>540.00 seconds (~90%)** |
| **Agent Steps** | 0 | 133 | 107 |
| **Tool Calls** | 0 | 66 | 53 |
| **File Reads** | 0 | 34 (20 unique, 14 repeated) | 26 (16 unique, 10 repeated) |
| **Preview Loop Behavior** | None | Spot preview (1 pass) | Grid loop (6 repeated reads) |
| **Steps to First Write** | 0 | 59 steps | 57 steps |
| **Steps After First Write** | 0 | 74 steps | 6 steps |
| **Termination Semantics** | `COMPLETED` | `INTERRUPTED_IN_PROGRESS` | `INTERRUPTED_IN_PROGRESS` |

### 3.3 FPS & Frame Count Discrepancy Resolution (Section 19)
* **Discrepancy:** Phase 4A documentation suggested that traditional hand-drawn animation should run at 12fps (animating on twos), yet the agent rendered 360 frames at 24fps.
* **Root Cause Found in Source Code:** In `hand-drawn-animation/assets/core.js` (line 523), `defineFilm` defaults to `fps: 24` unless explicitly overridden:
  ```javascript
  function defineFilm({ palette, timeline, score, format = {}, fps = 24 })
  ```
  In `_process/make_phoenix_film.mjs` (line 950), the Agent explicitly coded `fps: 24`, creating 360 frames.
* **Compute Comparison (Section 20):**
  - At 24fps: 360 frames take **52.98s**.
  - At 12fps: 180 frames take **29.21s** (-44.9% render time savings).
  - Both complete in well under 1 minute.
* **Critical Conclusion:** Even at 24fps, the pure render time is only **52.98s**. Therefore, the choice of 24fps vs 12fps is NOT what caused the 600s timeout!

### 3.4 T10 Bottleneck Classification
* **Classification:** **HARNESS_DOMINANT** (Specifically: Agent authoring & iterative scripting loop).
* **Rationale:** Direct rendering of all 360 1080p canvas frames takes under 53 seconds. The Agent timed out because it took 59 steps to explore and write the initial script, then spent another 74 steps re-reading assets (`assets/core.js` read 5 times), editing `make_phoenix_film.mjs` 4 times, generating spot frames in `/tmp/preview-phoenix/`, and only launched the final render command with less than 30 seconds remaining in the 600-second window.

---

## 4. CONSOLIDATED SUMMARY & CLASSIFICATION TABLE

| Task ID | Skill | Direct Pipeline Compute | Agent Benchmark Runtime | Compute Share | Agent Overhead Share | Bottleneck Classification | Primary Mechanism |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **T09** | `video-studio` | **76.63s** | 600.00s (TO) | 12.8% | **87.2%** | **HARNESS_DOMINANT** | Agent inspected media scripts 18 times & ran extra verifiers instead of calling pipeline once. |
| **T10** | `hand-drawn-animation` | **52.98s** | 600.00s (TO) | 8.8% | **91.2%** | **HARNESS_DOMINANT** | Agent spent 133 steps authoring procedural canvas code & inspecting assets before rendering. |
| **T02** | `dich-giu-dinh-dang` | ~35.00s | 153.30s | 22.8% | **77.2%** | **BALANCED / KEEP** | Optimized in Phase 4A: CLI Contract cut tool calls from 53 to 30 (-43.4%). |
| **T06** | `tu-van-thue-tncn` | ~1.50s | 188.70s | 0.8% | **99.2%** | **BALANCED / KEEP** | Tax calculation & Excel formulas verified 100% PASS with 18k token savings. |
| **T12** | `viet-bai` | ~1.00s | 175.80s | 0.6% | **99.4%** | **CONTROL / PASS** | Clean 100% legal compliance under Rule R5 with zero regressions. |

---

## 5. STRATEGIC IMPLICATIONS

1. **The Rendering Engines are Production-Ready:** Neither `video_pipeline.py` nor `render.mjs` has a performance defect. Both generate production-quality 1080p media in under 80 seconds.
2. **Harness Layers Will Not Fix Creative Scripting:** Adding Subagent forks, Router models, or Reviewer agents will not speed up T09 or T10; it would only add more steps, prompts, and context latency.
3. **The True Path Forward:** If T09 and T10 are to complete within standard benchmark limits, domain skill instructions should provide ready-to-use boilerplate templates or direct CLI generation wrappers, reducing the need for the Agent to write hundreds of lines of JavaScript/Python from scratch.
