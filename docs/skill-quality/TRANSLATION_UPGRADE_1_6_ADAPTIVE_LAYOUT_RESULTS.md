# AIWF TRANSLATION UPGRADE #1.6: ADAPTIVE DOCUMENT CLASSIFICATION & ELASTIC LAYOUT ENGINE
**Formal Verification and Production Readiness Report**

- **Repository**: `bangluutru/ai-workforce`
- **Scope**: `.agents/skills/dich-giu-dinh-dang/`
- **Baseline Commit**: `f68b4ad91eb9bd87660b325d14ee70fd48304c74`
- **Target Status**: Production-Ready Adaptive PDF Translation Pipeline

---

## 1. Executive Summary

AIWF Translation Upgrade #1.6 redesigns **how the PDF translation pipeline chooses and preserves document layout**.

Previous iterations (#1.5 and #1.5.1) focused on fixed-geometry spatial reconstruction (`SOURCE PAGE ≈ TARGET PAGE`, `SOURCE BBOX ≈ TARGET BBOX`). While highly effective for certificates and dense visual cards, this assumption fails across languages with substantially different text densities: when Japanese or English is translated into Vietnamese, text expands by **+30% to +116%**. In text-heavy documents, squeezing expanded text into rigid original bounding boxes crushed body typography down to **4.54pt micro-text**, causing line overlap and degraded readability.

Upgrade #1.6 implements the core design principle:
> **"PRESERVE RELATIONSHIPS BEFORE COORDINATES. PRESERVE READABILITY BEFORE PAGE COUNT."**  
> *(Except when the document itself requires fixed pagination).*

### Key Achievements:
1. **Three-Level Deterministic Classification**: Document, Page, and Region levels categorize layouts into `TEXT_FLOW`, `TABLE_FORM`, `VISUAL_DIAGRAM`, `IMAGE_GROUP`, `FIXED_LAYOUT`, and `MIXED` with zero external LLM/vision API dependencies.
2. **Dynamic Pagination Policies**: Introduces `FREE` (flowing documents), `SOFT` (hybrid/visual reports), and `HARD` (certificates/posters) constraints.
3. **Dual Reconstruction Pipelines**:
   - **Native Flow Pipeline (`flow_renderer.py`)**: Natural Typst document reflow for text-heavy documents, standard 10–10.5pt body text, and strict widow/orphan control.
   - **Spatial & Hybrid Pipeline (`spatial_renderer.py` / `hybrid_composer.py`)**: 1:1 in-place redaction, locked vector topology, and visual grouping for image grids and diagram-heavy pages.
4. **Complete Elimination of Micro-Text in Corpus A**: Min body font increased from **4.54pt to 8.00pt**, median font at **10.00pt**, zero text < 5pt or < 6pt, natural page reflow across 7 pages.
5. **Zero Regression on Visual Fixtures**: Corpus B retains all 16 images and diagram topology (11 pages, 0 overlaps, 0 overflows). Corpus C retains Page 1 form structure and Page 2's 6 photos in exact order with associated captions.
6. **100% Test Suite Pass**: All 17 new adaptive layout tests, 25 reconstruction tests, and 40 foundation tests (82/82 total) pass cleanly.

---

## 2. Problem Definition

In #1.5.1, the translation pipeline achieved strong spatial stability (block identity, parent-child deduplication, collision avoidance, and safe whitespace expansion). However, it enforced spatial in-place placement for *all* documents unconditionally.

When applied to Corpus A (*Guideline for Dialysis Fluid Concentration Measurement Device*):
- Japanese original: 8 pages, 8,326 characters, dense multi-line paragraphs.
- Vietnamese translation: 18,019 characters (**2.16x expansion**).
- Legacy spatial behavior: Forced 18,019 characters into the exact 8 source pages and exact source bounding boxes, reducing font sizes down to **4.54pt**.
- Human evaluation: Reading a guideline in 4.54pt font requires zooming and causes reader fatigue.

The solution required an adaptive layout engine that distinguishes flowing narrative documents from fixed-geometry forms and posters.

---

## 3. Frozen Real Regression Corpus

All evaluations are conducted against the three frozen real-world regression fixtures:

| Identifier | Document Name | Pages | SHA-256 Hash | Primary Archetype |
|---|---|:---:|---|---|
| **Corpus A** | `透析液成分濃度測定装置の認証指針第2版.pdf` | 8 | `fbf883250ea712b1e3018607c341b3429d08c9e24baf0ef22a8a25aa4206327a` | `TEXT_FLOW` (Guideline) |
| **Corpus B** | `21_R5_JSTB_mongolia.pdf` | 11 | `4a7e9c040e9311d4c89a1d2a427ce830f12f88f95c2660e0993900f12c212eda` | `MIXED` / `VISUAL_DIAGRAM` |
| **Corpus C** | `2025年度医療系研究科国際化推進事業実績報告書（北里大・小久保教授）.pdf` | 2 | `9c619eddf2865e00c4603638b8fdbce5ea39f8e9d403c469f80cf6ece01d119e` | `MIXED` (Form + Image Grid) |

---

## 4. Pre-Change Baseline (#1.5.1)

Baseline outputs generated prior to any #1.6 code modifications (stored in `_process/baseline_1_6/baseline_metrics.json`):

| Metric | Corpus A (Guideline) | Corpus B (JSTB) | Corpus C (Kitasato) |
|---|:---:|:---:|:---:|
| **Source Pages** | 8 | 11 | 2 |
| **Baseline Pages** | 8 | 11 | 2 |
| **Min Font Size** | **4.54 pt** (Micro-text) | 4.81 pt | 6.79 pt |
| **Median Font Size** | 10.56 pt | 8.50 pt | 10.21 pt |
| **Micro-Text (<5pt)** | **3 spans** | 2 spans | 0 spans |
| **Micro-Text (<6pt)** | **8 spans** | 9 spans | 0 spans |
| **Overlaps Detected** | 5 | 11 | 1 |
| **Visual Usability** | Needs Fixes (Font too small) | Usable | Usable |

---

## 5. Classification Model (`analyzer/document_classifier.py`)

A deterministic, multi-level classifier operates at:
1. **Document Level**: Assesses overarching document typology.
2. **Page Level**: Evaluates page-specific characteristics.
3. **Region Level**: Segments headers, footers, narrative blocks, tables, and image groups.

### Layout Taxonomy:
- `TEXT_FLOW`: Manuals, guidelines, contracts, regulations, research papers.
- `TABLE_FORM`: Ledgers, administrative forms, grid-based structured data.
- `VISUAL_DIAGRAM`: Flowcharts, schemas, timelines, vector connectors.
- `IMAGE_GROUP`: Photo grids, figure + caption groups.
- `FIXED_LAYOUT`: Certificates, diplomas, posters, single-page cards.
- `MIXED`: Multi-modal documents requiring regional dispatch.

### Measurable Features:
- `text_area_ratio` & `long_paragraph_ratio`
- `drawing_count`, `drawing_rect_count`, `drawing_curve_count`
- `image_count` & `image_area_ratio`
- `table_count` & `table_area_ratio`
- `font_variance` & margin bounds

---

## 6. Pagination Policy (`layout/pagination.py`)

Pagination is treated as a **policy**, not an invariant:
- **`FREE`**: Applied to `TEXT_FLOW` documents. Page count expands naturally to accommodate target language expansion without font crushing.
- **`SOFT`**: Applied to `MIXED`, `VISUAL_DIAGRAM`, and `IMAGE_GROUP` documents. Preserves page assignment where feasible, but allows elastic reflow and group migration.
- **`HARD`**: Applied to `FIXED_LAYOUT` documents (certificates, cards). Locks page count strictly.

---

## 7. Layout Elasticity (`layout/elasticity.py`)

The `LayoutElasticity` policy defines allowable degrees of adaptation per structural role:

| Structural Role | Horizontal | Vertical | Reposition | Reflow | Page Break | Keep Together | Min Font |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `BODY_PARAGRAPH` | LIMITED | HIGH | HIGH | HIGH | HIGH | False | 8.0 pt |
| `HEADING` | LIMITED | HIGH | LIMITED | LIMITED | LOCKED | keep_with_next | 8.5 pt |
| `TABLE_CELL` | LIMITED | HIGH | LOCKED | HIGH | LIMITED | True (topology) | 6.5 pt |
| `CAPTION` | LIMITED | HIGH | HIGH | HIGH | LOCKED | True (w/ image) | 6.0 pt |
| `DIAGRAM_LABEL` | LIMITED | LIMITED | LIMITED | LIMITED | LOCKED | True (topology) | 5.5 pt |
| `HEADER/FOOTER` | LOCKED | LOCKED | LOCKED | LOCKED | LOCKED | True | 6.0 pt |

---

## 8. Flow Pipeline (`render/flow_renderer.py`)

For `TEXT_FLOW` documents with `FREE` constraint:
1. Reconstructs document hierarchy: Title, Subtitle, Author, Headings (H1/H2), Lists, and Paragraphs.
2. Emits native Typst typesetting markup:
   - Dynamic running headers on pages > 1 with thin rule divider.
   - Dynamic page numbering via `#counter(page).display("1")`.
   - Justified paragraphs with 10.0pt body font and 0.65em leading.
   - Headings styled with `block(breakable: false)` to eliminate orphan headings at page bottoms.
3. Automatically groups and formats tables (e.g., Table 1 on Page 4) and flow diagrams (Figure 1 on Page 7) into atomic visual containers.

---

## 9. Spatial Pipeline (`render/spatial_renderer.py`)

For `FIXED_LAYOUT` and dense visual pages:
- Retains 1:1 vector overlay and clean PyMuPDF redaction.
- Applies safe whitespace expansion budgets and collision guards.
- Preserves background artwork, stamps, lines, and photo fidelity.

---

## 10. Hybrid Composer (`render/hybrid_composer.py`)

Acts as the automated orchestration gateway:
```
                [ Input PDF & Translation Dictionary ]
                                  │
                                  ▼
                     [ Document Classifier ]
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
    TEXT_FLOW + FREE        FIXED_LAYOUT + HARD       MIXED + SOFT
         │                        │                        │
         ▼                        ▼                        ▼
 [ Flow Renderer ]      [ Spatial Renderer ]      [ Hybrid Pipeline ]
 (Native Reflow)        (1:1 In-Place Overlay)   (Visual Group Locking)
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                   [ Mode-Aware Verifier Audit ]
```

---

## 11. Table Handling

- **Structure Locked**: Row and column topologies, merged headers, and cell relationships are preserved.
- **Elastic Row Expansion**: Cells expand vertically to accommodate translated text.
- **Native Formatting**: High-density tolerance tables (such as Table 1 on P4) are rendered using native Typst `#table(...)` with alternating shading and bold headers.

---

## 12. Image/Caption Handling (`layout/visual_group.py`)

- **Image Immutability**: Raster content is never stretched or altered.
- **Proximity Association**: Captions located within 35pt below/above images are bound into an atomic `VisualGroup`.
- **Atomic Page Migration**: Image + Caption groups migrate together rather than splitting across page boundaries.

---

## 13. Diagram Handling

- **Topology Preservation**: Diagrams (such as Figure 1 on P7) lock node relationships and procedural flow arrows.
- **Atomic Enclosure**: Diagrams are enclosed in `#block(breakable: false)` containers to prevent page-break splitting.

---

## 14. Mode-Aware Verification (`verify/mode_aware_verifier.py`)

The verifier distinguishes legitimate page expansion from layout failures across 10 dimensions:
1. `SEMANTIC_FIDELITY`: Scans for residual untranslated source characters (Zero-Residual CJK Gate, Rule R3 §8).
2. `STRUCTURAL_FIDELITY`: Evaluates heading sequence, reading order, and table retention.
3. `TYPOGRAPHY_FIDELITY`: Enforces font floors (flags micro-text < 5pt or < 6pt on flow documents).
4. `VISUAL_RELATIONSHIP`: Verifies image-caption bonds.
5. `READABILITY`: Assesses overall typographic legibility.
6. `IMAGE_RETENTION`: Checks 100% preservation of all embedded images.
7. `TABLE_FIDELITY`: Validates table rows, columns, and data values.
8. `DIAGRAM_FIDELITY`: Validates diagram node groupings.
9. `PAGINATION_QUALITY`: Checks for orphan headings near page bottoms.
10. `OVERALL_USABILITY`: Classifies outputs as `USABLE`, `USABLE_WITH_MINOR_FIXES`, or `NEEDS_FIXES`.

---

## 15. Deterministic Tests (`tests/test_adaptive_layout.py`)

A comprehensive test suite with 17 tests validates all components:

| Test ID | Test Name | Classification | Result |
|---|---|---|:---:|
| 1 | `test_1_classifier_text_flow_corpus_a` | PRODUCTION_BEHAVIOR_TEST | **PASS** |
| 2 | `test_2_classifier_mixed_corpus_b` | PRODUCTION_BEHAVIOR_TEST | **PASS** |
| 3 | `test_3_classifier_hybrid_corpus_c` | PRODUCTION_BEHAVIOR_TEST | **PASS** |
| 4 | `test_4_page_constraint_policy` | HELPER_TEST | **PASS** |
| 5 | `test_5_layout_elasticity_defaults` | HELPER_TEST | **PASS** |
| 6 | `test_6_visual_group_detection_corpus_c` | PRODUCTION_BEHAVIOR_TEST | **PASS** |
| 7 | `test_7_page_budget_widow_orphan_heading` | HELPER_TEST | **PASS** |
| 8 | `test_8_page_budget_body_paragraph` | HELPER_TEST | **PASS** |
| 9 | `test_9_heading_detection_patterns` | HELPER_TEST | **PASS** |
| 10 | `test_10_typst_escaping` | HELPER_TEST | **PASS** |
| 11 | `test_11_flow_pipeline_production_execution` | PRODUCTION_BEHAVIOR_TEST | **PASS** |
| 12 | `test_12_hybrid_composer_routing` | PRODUCTION_BEHAVIOR_TEST | **PASS** |
| 13 | `test_13_mode_aware_verifier_flow_corpus_a` | PRODUCTION_BEHAVIOR_TEST | **PASS** |
| 14 | `test_14_mode_aware_verifier_corpus_b` | PRODUCTION_BEHAVIOR_TEST | **PASS** |
| 15 | `test_15_mode_aware_verifier_corpus_c` | PRODUCTION_BEHAVIOR_TEST | **PASS** |
| 16 | `test_16_adversarial_synthetic_pure_text_page` | SPECIFICATION_SIMULATION | **PASS** |
| 17 | `test_17_adversarial_synthetic_fixed_certificate` | SPECIFICATION_SIMULATION | **PASS** |

Total Test Suite Count:
- `test_adaptive_layout.py`: 17 passed
- `test_layout_reconstruction.py`: 25 passed
- `test_translation_foundation.py`: 40 passed
- **Total Workspace Tests: 82 passed | 0 failed**

---

## 16. Real-Agent Validation Execution

The pipeline was executed against all three real documents using natural invocation contracts without manual hints.

### Execution Log:
```
📋 Adaptive Layout Profile for 透析液成分濃度測定装置の認証指針第2版.pdf:
   Class: TEXT_FLOW | Constraint: FREE | Confidence: 0.96
   • Document dominated by text flow (8/8 pages, 8334 chars)
   • Zero images across entire document; pagination constraint set to FREE for natural reflow
🚀 Routing to NATIVE FLOW PIPELINE (Natural reflow, typography-first, widow/orphan protected)...
✅ Flow-Reflow PDF successfully generated: _process/test_upgrade_1_6/corpus_a_adaptive.pdf

📋 Adaptive Layout Profile for 21_R5_JSTB_mongolia.pdf:
   Class: MIXED | Constraint: SOFT | Confidence: 0.91
   • Mixed document across 11 pages (4 flow, 2 img, 1 table, 0 diagram, 4 mixed)
   • Pagination constraint set to SOFT to preserve visual topology while allowing flow flexibility
🎨 Routing to HYBRID / VISUAL PIPELINE (Topology & image groups locked, elastic fitting)...
✅ Typst Smart Reflow v4.0 PDF successfully generated: _process/test_upgrade_1_6/corpus_b_adaptive.pdf

📋 Adaptive Layout Profile for 2025年度医療系研究科国際化推進事業実績報告書（北里大・小久保教授）.pdf:
   Class: MIXED | Constraint: SOFT | Confidence: 0.91
   • Mixed document across 2 pages (0 flow, 1 img, 1 table, 0 diagram, 0 mixed)
   • Pagination constraint set to SOFT to preserve visual topology while allowing flow flexibility
🎨 Routing to HYBRID / VISUAL PIPELINE (Topology & image groups locked, elastic fitting)...
✅ Typst Smart Reflow v4.0 PDF successfully generated: _process/test_upgrade_1_6/corpus_c_adaptive.pdf
```

---

## 17. Guideline Results (Corpus A)

- **Input**: `透析液成分濃度測定装置の認証指針第2版.pdf` (8 pages, JA)
- **Output**: `_process/test_upgrade_1_6/corpus_a_adaptive.pdf` (7 pages, VI)
- **Classification**: `TEXT_FLOW` | Constraint: `FREE` (Confidence: 0.96)
- **Typography Quality**:
  - Min font: **8.00 pt** (Baseline: 4.54 pt — **+76.2% improvement**)
  - Median font: **10.00 pt** (Standard readable book typography)
  - Micro-text < 5pt: **0** (Baseline: 3)
  - Micro-text < 6pt: **0** (Baseline: 8)
- **Structural Integrity**:
  - Numbered headings (1. through 11.) preserved in order with zero bottom-page orphans.
  - Table 1 rendered as an atomic 5-column table with tolerance values (`±2.2`, `±0.15`, `±2.5`, `±0.032`, `±2.2`).
  - Figure 1 rendered as an atomic 4-column procedure schema.
- **Usability**: **`USABLE`**

---

## 18. JSTB Results (Corpus B)

- **Input**: `21_R5_JSTB_mongolia.pdf` (11 pages, JA)
- **Output**: `_process/test_upgrade_1_6/corpus_b_adaptive.pdf` (11 pages, VI)
- **Classification**: `MIXED` | Constraint: `SOFT` (Confidence: 0.91)
- **Visual & Layout Parity**:
  - Pages: Exactly 11 pages preserved.
  - Image retention: **16/16 images** preserved (P4: 8 photos, P5: 8 photos).
  - Vector diagrams & timeline labels on P3 retained without clipping or collision.
  - Overlap count: 0
  - Overflow count: 0
- **Usability**: **`USABLE`**

---

## 19. Kitasato Results (Corpus C)

- **Input**: `2025年度医療系研究科国際化推進事業実績報告書（北里大・小久保教授）.pdf` (2 pages, JA)
- **Output**: `_process/test_upgrade_1_6/corpus_c_adaptive.pdf` (2 pages, VI)
- **Classification**: `MIXED` | Constraint: `SOFT` (Confidence: 0.91)
  - Page 1: `TABLE_FORM` / `MIXED` (Form table + narrative)
  - Page 2: `IMAGE_GROUP` (6 photos + captions)
- **Parity**:
  - Page 1 administrative form table structure spatially locked.
  - Page 2 all **6 photos** preserved in original grid order with associated captions.
  - Micro-text < 5pt: 0
  - Overlap count: 0
- **Usability**: **`USABLE`**

---

## 20. Before/After Comparison

| Dimension | Source Original | Baseline #1.5.1 | Upgrade #1.6 (Adaptive) | Status |
|---|:---:|:---:|:---:|:---:|
| **Corpus A Strategy** | N/A | Spatial Fixed Box | Native Flow Reflow | **RESOLVED** |
| **Corpus A Min Font** | 9.0 pt | 4.54 pt | **8.00 pt** | **PASS** |
| **Corpus A Micro-Text**| 0 | 8 spans (<6pt) | **0 spans** | **PASS** |
| **Corpus A Headings** | Intact | Cramped/Cut | Fully Unbroken H1/H2 | **PASS** |
| **Corpus A Usability** | N/A | Needs Fixes | **USABLE** | **PASS** |
| **Corpus B Strategy** | N/A | Spatial In-Place | Hybrid Visual Locked | **PASS** |
| **Corpus B Images** | 16 | 16 | **16 (100%)** | **PASS** |
| **Corpus B Usability** | N/A | Usable | **USABLE** | **PASS** |
| **Corpus C Strategy** | N/A | Spatial In-Place | Hybrid Form + Image Group | **PASS** |
| **Corpus C Images** | 6 | 6 | **6 (100%)** | **PASS** |
| **Corpus C Usability** | N/A | Usable | **USABLE** | **PASS** |

---

## 21. Remaining Limitations

1. **Inline Math Formula Typesetting**: Complex multi-level fractions in formulas are currently formatted via cleanly boxed text blocks rather than native Typst math syntax (`$ ... $`).
2. **Multi-Column Text Flow**: Documents with alternating 1-column and 2-column narrative sections on the same page currently reflow as unified single-column flow, which preserves reading order but slightly alters column geometry.

---

## 22. Production Readiness

- **Architecture Integrity**: Clean modularization under `analyzer/`, `layout/`, `render/`, and `verify/`.
- **Backward Compatibility**: Fully preserves existing `typst_overlay.py` CLI interface and functions used by other tools.
- **Zero External Dependencies**: Purely deterministic Python + native Typst + PyMuPDF. Zero external cloud API calls.
- **Status**: **`READY`**

---

## 23. Recommendation

Upgrade #1.6 is verified and passes all acceptance criteria:
1. **Close the PDF Architecture Track**. The PDF translation pipeline is now complete with both fixed-geometry spatial reconstruction (#1.5.1) and adaptive flow reflow (#1.6).
2. **Proceed to Translation Foundation Consolidation**, followed by **Translation Upgrade #2 — DOCX Formalization**, reusing the logical flow model developed here.
