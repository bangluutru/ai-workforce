---
name: pdf-translate
description: Translate local text-based PDFs, scanned PDFs (with OCR), and standalone images (.png, .jpg, .jpeg, .webp, .bmp, .tiff) into Vietnamese, English, Japanese, Chinese, Korean, or any other supported language with full Unicode font fidelity while preserving the original layout, formulas, tables, and figures. Use for PDF translation, scanned document translation, batch translation, terminology-sensitive handoff translation, or diagnosing incomplete translated output.
license: AGPL-3.0-only
---

# PDF Translate

Translate a PDF or image document with the bundled Code4Life engine + OCR. Keep the source file unchanged and produce a separate PDF with the same structure.

## Resolve the skill root

This skill may be installed globally while the user's files live elsewhere. Resolve the absolute directory containing this `SKILL.md` before running anything. Call its scripts and dependency files by absolute path; do not assume the current working directory is the skill directory.

Use the interpreter inside `<skill-root>/.venv`:

- Windows: `<skill-root>\.venv\Scripts\python.exe`
- macOS/Linux: `<skill-root>/.venv/bin/python`

## Choose a mode

| Mode | Translator | Speed | Layout Quality | Use when |
| --- | --- | --- | --- | --- |
| Google (**default, recommended**) | `translate.google.com/m` (free web scraping, no API key) | ~1 page/sec | ★★★★★ | All normal cases — books, batches, legal docs, tables, scans |
| Handoff (**experimental** ⚠️) | The active agent | ~2× slower | ★★★☆☆ | Only when Google is blocked or manual segment control needed |

**Always default to Google mode.** It is free (web scraping, no API key), fast, and produces perfect layout because it translates in real-time as the PDF engine processes each segment — there is zero segment boundary mismatch.

> ⚠️ **Known Handoff limitation**: The extraction pass and rendering pass split text at different boundaries, causing dictionary lookup misses. This results in untranslated fragments, especially in tables and appendices. Do not use Handoff for documents with complex table structures unless the user explicitly requests it and accepts the quality trade-off.

## Capabilities & Boundaries

- **Digital PDFs & Scanned PDFs & Images:** Supports text-based PDFs, scanned PDFs, and image files (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`, `.tif`).
- **Built-in OCR (`--ocr auto` by default):** Automatically detects scanned/image-only pages, extracts text bounding boxes with ONNX-powered `RapidOCR`, corrects orientation (0°, 90°, 270°), and generates a clean background canvas with an embedded text layer for layout-preserving translation.
- **OCR Options:**
  - `--ocr {auto, force, none}` (Default: `auto` — runs OCR only when needed).
  - `--ocr-dpi {150, 200, 300}` (Default: `200` — balance between speed and precision).
- Use the bundled `pdf2zh/` core. Never substitute the PyPI `pdf2zh` package; the runner checks version `1.9.11` and preservation ruleset `code4life-preservation-v1` and refuses an external core.
- Google mode sends extracted document text to Google. Tell the user before processing sensitive material and obtain explicit confirmation unless their request already authorizes that disclosure. Handoff mode does not contact Google.
- Supported targets include Vietnamese (`vi`), CJK languages (Japanese `ja`, Chinese `zh`/`zh-cn`/`zh-tw`, Korean `ko`), Latin/European scripts (`en`, `fr`, `de`, `es`, `it`, `pt`, `ru`, `uk`, etc.), and other Unicode world scripts.
- Text inside detected vector figures, contents pages, indexes, symbol lists, or references may intentionally remain in the source language.
- Preserve the source. Write results to a separate output directory. Do not pass `--overwrite` without explicit replacement authorization.

Read [the preservation contract](references/preservation-rules.md) before changing layout behavior, diagnosing preserved pages, or investigating untranslated regions.

## Set up the runtime

Use Python 3.11 or 3.12. Create `<skill-root>/.venv` and install `<skill-root>/requirements.txt` if the environment is absent or stale. Keep this environment separate from the user's project.

The source distribution downloads layout and font assets on its first translation, so the first run needs network access and takes longer. The packaged Windows app already contains these assets.

Windows:

```powershell
python -m venv "<skill-root>\.venv"
& "<skill-root>\.venv\Scripts\python.exe" -m pip install -r "<skill-root>\requirements.txt"
```

macOS/Linux:

```bash
python3 -m venv "<skill-root>/.venv"
"<skill-root>/.venv/bin/python" -m pip install -r "<skill-root>/requirements.txt"
```

Shared runner options include `--target-language` (default `vi`), `--source-language auto`, one-based `--pages 1,3-5`, `--threads 1..8` (default `4`), `--ignore-cache`, and `--overwrite`.

## Google mode

Run one command per file. Use absolute paths for the input and output directory.

Windows:

```powershell
& "<skill-root>\.venv\Scripts\python.exe" "<skill-root>\scripts\translate_pdf.py" "<input.pdf>" --output-dir "<output-dir>"
```

macOS/Linux:

```bash
"<skill-root>/.venv/bin/python" "<skill-root>/scripts/translate_pdf.py" "<input.pdf>" --output-dir "<output-dir>"
```

For a batch, process files individually and report progress. A failure on one file must not stop the remaining files; collect and report all failures at the end.

## Handoff mode

Handoff extracts translatable segments to JSONL, lets the active agent translate them, then rebuilds the PDF. Warn about token and time cost before starting a large document. For long documents, suggest a representative sample such as `--pages 1-5` first.

### 1. Extract

An output directory is not required during extraction because the pass-one PDF is discarded.

```text
<python> <skill-root>/scripts/translate_pdf.py <input.pdf> --engine handoff --emit-segments <segments.jsonl>
```

### 2. Translate

Read `segments.jsonl` in manageable batches. Write one JSON object per line to `translations.jsonl`:

```json
{"src":"exact source text","dst":"translated text"}
```

Copy each `src` value exactly. Preserve URLs, paths, identifiers, citation markers, and numbers.

Formula and code placeholders such as `<b0></b0>` are immutable. Every opening and closing tag must retain the same identifier, count, and order as the source. The loader rejects a record whose placeholders differ, leaving that segment untranslated.

Inline emphasis markers are immutable as balanced pairs: `<s1>...</s1>` is
bold, `<s2>...</s2>` is italic, and `<s3>...</s3>` is bold italic. Complete
style pairs may move with the translated phrase, but none may be dropped,
duplicated, or cross-nested. Invalid style markup leaves the segment
untranslated instead of silently losing emphasis.

**Table-aware translation rules:**
- Segments extracted from table cells retain their row/column position. Do not merge multiple cell segments into a single translation.
- Table headers and data cells are separate segments — translate each independently while maintaining consistent terminology across the entire table.
- Numeric values, units, formulas, and identifiers in table cells must be preserved exactly.
- Empty cells produce no segments. Do not insert extra content for gaps in the source table.

### 3. Rebuild

```text
<python> <skill-root>/scripts/translate_pdf.py <input.pdf> --engine handoff --segments <translations.jsonl> --output-dir <output-dir> --emit-segments <still-missing.jsonl>
```

The command prints the remaining untranslated segment count. If it is nonzero, translate `still-missing.jsonl`, append valid records to `translations.jsonl`, and rebuild again. Stop only at zero or when a segment cannot be translated safely; then report the exact remaining limitation.

Extraction and rebuild each run the layout pass, so handoff uses roughly twice the local PDF processing of Google mode in addition to the agent's translation work.

## Verify before delivery

1. Confirm the output exists and the source still exists unchanged.
2. Confirm source and output page counts match.
3. Extract text page by page and check for substantial untranslated passages, missing formulas, damaged URLs, or lost identifiers.
4. When page rendering or image inspection is available, render every output page and inspect for blank pages, missing glyphs, clipping, overlap, and displaced tables or figures.
5. If full visual inspection is unavailable, say which checks were completed. Do not present a partially verified or partially translated file as fully complete.
