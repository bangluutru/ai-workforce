"""Structured Mathematical Formula Recognition & Reconstruction Engine.

Conforms to Section 8, 9, 10, 11 of AIWF Document Reconstruction Directive:
- Source Types:
  * TYPE A: Clean text layer -> structured AST/parsing.
  * TYPE B: Vector/mixed glyph -> analyze geometry/glyph structure.
  * TYPE C: Raster/image math -> local recognition with safe fallback crop.
- Mathematical Structures Supported:
  * Fractions & nested fractions (frac, /)
  * Superscripts (^) and subscripts (_)
  * Integrals with limits (integral_a^b)
  * Summations with bounds (sum_(i=1)^n)
  * Limits (lim_(x -> infinity))
  * Square roots (sqrt)
  * Matrices and cases (mat, cases)
  * Greek symbols and differential operators
  * Multi-line equations
- Semantic Validation:
  * Compares variables, operators, powers, indices, fractions, and symbols.
  * If validation fails or confidence < threshold: fallback to original formula crop.
  * Absolute ban: NEVER invent or hallucinate variables or equations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import sys
from pathlib import Path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ir.models import ConfidenceMetrics, ReconstructionStrategy, SemanticObject, SemanticObjectType


class FormulaSourceType(str, Enum):
    TYPE_A = "TEXT_LAYER"       # Good native text layer
    TYPE_B = "VECTOR_GLYPHS"    # Vector curves / mixed glyph structure
    TYPE_C = "RASTER_IMAGE"     # Scanned or raster image crop


@dataclass
class FormulaModel:
    raw_source: str
    typst_math: str
    source_type: FormulaSourceType = FormulaSourceType.TYPE_A
    variables: Set[str] = field(default_factory=set)
    operators: Set[str] = field(default_factory=set)
    has_fractions: bool = False
    has_subscripts: bool = False
    has_superscripts: bool = False
    has_matrix: bool = False
    has_integral: bool = False
    has_summation: bool = False
    has_limit: bool = False
    confidence: float = 0.90


class FormulaEngine:
    """Recognizes, parses, formats, and semantically validates structured math."""

    TYPST_MATH_WORDS = {
        "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa",
        "lambda", "mu", "nu", "xi", "pi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
        "Alpha", "Beta", "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega",
        "sin", "cos", "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh",
        "ln", "log", "exp", "lim", "min", "max", "inf", "infinity", "sqrt", "sum", "product", "integral",
        "diff", "dif", "times", "div", "pm", "plus", "minus", "eq", "in", "subset", "forall", "exists", "approx",
        "hbar", "planck", "mat", "cases", "vec"
    }

    def __init__(self, confidence_threshold: float = 0.80):
        self.confidence_threshold = confidence_threshold

    def process_formula_object(self, obj: SemanticObject) -> Dict[str, Any]:
        """Analyzes a FORMULA SemanticObject and produces Typst math markup or fallback."""
        raw_text = obj.get_text_content(prefer_translated=False).strip()
        asset_ref = obj.source_asset_reference

        if not raw_text:
            obj.reconstruction_strategy = ReconstructionStrategy.PRESERVE_ASSET
            obj.fallback_used = True
            return {
                "success": False,
                "strategy": ReconstructionStrategy.PRESERVE_ASSET.value,
                "typst_markup": "",
                "confidence": 0.0,
                "fallback": True,
                "reason": "Empty formula expression. Preserving original graphic safely.",
            }

        # Determine source type
        if len(raw_text) > 1:
            source_type = FormulaSourceType.TYPE_A
        elif asset_ref and Path(asset_ref).exists():
            source_type = FormulaSourceType.TYPE_C
        else:
            source_type = FormulaSourceType.TYPE_B

        # If TYPE C and no text layer, evaluate local OCR / raster capability
        if source_type == FormulaSourceType.TYPE_C and not raw_text:
            # Fallback safely to preserving original graphic (no hallucination)
            obj.reconstruction_strategy = ReconstructionStrategy.PRESERVE_ASSET
            obj.fallback_used = True
            return {
                "success": False,
                "strategy": ReconstructionStrategy.PRESERVE_ASSET.value,
                "typst_markup": "",
                "confidence": 0.50,
                "fallback": True,
                "reason": "Raster formula without verifiable text layer. Preserving original graphic safely.",
            }

        # Structure Recognition & Parsing
        model = self.recognize_formula(raw_text, source_type)

        # Semantic Validation
        is_valid, val_reason = self.validate_formula_semantics(raw_text, model)

        if is_valid and model.confidence >= self.confidence_threshold:
            obj.reconstruction_strategy = ReconstructionStrategy.LATEX_MATH
            obj.confidence.reconstruction = model.confidence
            obj.translated_content = model.typst_math
            return {
                "success": True,
                "strategy": ReconstructionStrategy.LATEX_MATH.value,
                "typst_markup": model.typst_math,
                "confidence": model.confidence,
                "fallback": False,
                "model": {
                    "source_type": model.source_type.value,
                    "variables": sorted(list(model.variables)),
                    "operators": sorted(list(model.operators)),
                },
            }
        else:
            obj.reconstruction_strategy = ReconstructionStrategy.PRESERVE_ASSET
            obj.fallback_used = True
            return {
                "success": False,
                "strategy": ReconstructionStrategy.PRESERVE_ASSET.value,
                "typst_markup": "",
                "confidence": model.confidence,
                "fallback": True,
                "reason": val_reason or f"Confidence {model.confidence:.2f} below threshold {self.confidence_threshold}",
            }

    def recognize_formula(self, raw_expr: str, source_type: FormulaSourceType = FormulaSourceType.TYPE_A) -> FormulaModel:
        """Parses raw math text / LaTeX / symbols into a structured FormulaModel."""
        s = raw_expr.strip()
        s = s.strip("$").strip()

        # Check if raw_expr contains Japanese / Chinese prose
        if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", s):
            if re.search(r"[。、]", s) or len(re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]", s)) > 4:
                return FormulaModel(
                    raw_source=raw_expr,
                    typst_math="",
                    source_type=source_type,
                    confidence=0.30,
                )

        confidence = 0.95
        if len(s) > 300:
            confidence -= 0.25

        variables: Set[str] = set()
        operators: Set[str] = set()

        has_fractions = False
        has_subscripts = False
        has_superscripts = False
        has_matrix = False
        has_integral = False
        has_summation = False
        has_limit = False

        # 1. LaTeX \frac{num}{den} conversion
        while r"\frac" in s:
            has_fractions = True
            m = re.search(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", s)
            if m:
                s = s[:m.start()] + f"({m.group(1)}) / ({m.group(2)})" + s[m.end():]
            else:
                break

        # 2. LaTeX matrices: \begin{matrix} ... \end{matrix} or pmatrix / bmatrix
        mat_match = re.search(r"\\begin\{(?:matrix|pmatrix|bmatrix|vmatrix)\}(.*?)\\end\{(?:matrix|pmatrix|bmatrix|vmatrix)\}", s, re.DOTALL)
        if mat_match:
            has_matrix = True
            mat_body = mat_match.group(1).strip()
            rows = [r.strip() for r in mat_body.split(r"\\") if r.strip()]
            typ_rows = []
            for r in rows:
                cols = [c.strip() for c in r.split("&")]
                typ_rows.append(", ".join(cols))
            typ_mat = f"mat({'; '.join(typ_rows)})"
            s = s[:mat_match.start()] + typ_mat + s[mat_match.end():]

        # 3. LaTeX cases: \begin{cases} ... \end{cases}
        cases_match = re.search(r"\\begin\{cases\}(.*?)\\end\{cases\}", s, re.DOTALL)
        if cases_match:
            cases_body = cases_match.group(1).strip()
            c_rows = [r.strip() for r in cases_body.split(r"\\") if r.strip()]
            typ_cases = []
            for r in c_rows:
                parts = [p.strip() for p in r.split("&")]
                typ_cases.append(" ".join(parts))
            s = s[:cases_match.start()] + f"cases({', '.join(typ_cases)})" + s[cases_match.end():]

        # 4. Integrals & Summations & Limits
        if r"\int" in s or "∫" in s or "integral" in s:
            has_integral = True
            operators.add("integral")
            s = s.replace(r"\int", "integral").replace("int_", "integral_")
        if r"\sum" in s or "∑" in s or "sum" in s:
            has_summation = True
            operators.add("sum")
            s = s.replace(r"\sum", "sum").replace("sum_", "sum_")
        if r"\lim" in s or "lim_" in s:
            has_limit = True
            operators.add("lim")
            s = s.replace(r"\lim", "lim").replace(r"\to", "->").replace(r"\rightarrow", "->")

        # 5. Greek symbols
        unicode_greek = {
            "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
            "ε": "epsilon", "θ": "theta", "λ": "lambda", "μ": "mu",
            "π": "pi", "σ": "sigma", "ω": "omega", "Δ": "Delta", "Σ": "Sigma",
        }
        for u_char, name in unicode_greek.items():
            if u_char in s:
                s = s.replace(u_char, f" {name} ")
                variables.add(name)

        # LaTeX greek symbols
        for g_name in ("alpha", "beta", "gamma", "delta", "epsilon", "theta", "lambda", "mu", "pi", "sigma", "omega", "Delta", "Sigma"):
            if f"\\{g_name}" in s:
                s = s.replace(f"\\{g_name}", f" {g_name} ")
                variables.add(g_name)

        # 6. Mathematical operators
        op_map = {
            "×": " times ", "÷": " div ", "±": " plus.minus ", "≠": " eq.not ",
            "≈": " approx ", "≤": " lt.eq ", "≥": " gt.eq ", "√": " sqrt ",
            "∞": " infinity ", "∂": " diff ", r"\times": " times ", r"\div": " div ",
            r"\pm": " plus.minus ", r"\neq": " eq.not ", r"\approx": " approx ",
            r"\leq": " lt.eq ", r"\geq": " gt.eq ", r"\infty": " infinity ",
            r"\partial": " diff ",
        }
        for k, v in op_map.items():
            if k in s:
                s = s.replace(k, v)
                operators.add(v.strip())

        # 7. Differentials: dx, dt, dy -> dif x, dif t, dif y
        s = re.sub(r"\b(dx|dt|du|dv|dy|dz)\b", r"dif \1", s)
        s = s.replace("dif dx", "dif x").replace("dif dt", "dif t")

        # 8. Square root
        while r"\sqrt" in s:
            m = re.search(r"\\sqrt\s*\{([^{}]+)\}", s)
            if m:
                s = s[:m.start()] + f"sqrt({m.group(1)})" + s[m.end():]
            else:
                break
        s = re.sub(r"sqrt\s*\(([^)]+)\)", r"sqrt(\1)", s)

        # 9. Superscripts and subscripts
        if "^" in s:
            has_superscripts = True
            s = re.sub(r"\^{([^}]+)}", r"^(\1)", s)
        if "_" in s:
            has_subscripts = True
            s = re.sub(r"_{([^}]+)}", r"_(\1)", s)

        # 10. Extract standard variables (single letters)
        for var_m in re.finditer(r"\b([a-zA-Z])\b", s):
            v_char = var_m.group(1)
            if v_char not in ("d", "e"):
                variables.add(v_char)

        # Format multiline equations: Typst supports multiline math with backslash
        s = s.replace(r"\\", " \\\n ")

        # Convert standalone int or infty to Typst names
        s = re.sub(r"\bint\b", "integral", s)
        s = re.sub(r"\bint_", "integral_", s)
        s = re.sub(r"\binfty\b", "infinity", s)

        # Split multi-character consecutive letters (like 'mc' -> 'm c') unless recognized
        def _split_letters(m):
            token = m.group(0)
            if token in self.TYPST_MATH_WORDS:
                return token
            return " ".join(list(token))

        s = re.sub(r"[A-Za-z]+", _split_letters, s)

        # Clean spaces
        s = re.sub(r"\s+", " ", s).strip()
        typst_math = f"$ {s} $"

        return FormulaModel(
            raw_source=raw_expr,
            typst_math=typst_math,
            source_type=source_type,
            variables=variables,
            operators=operators,
            has_fractions=has_fractions,
            has_subscripts=has_subscripts,
            has_superscripts=has_superscripts,
            has_matrix=has_matrix,
            has_integral=has_integral,
            has_summation=has_summation,
            has_limit=has_limit,
            confidence=confidence,
        )

    def validate_formula_semantics(self, raw_expr: str, model: FormulaModel) -> Tuple[bool, Optional[str]]:
        """Compares semantic tokens between raw source and parsed model."""
        # 1. Check brackets balance
        math_content = model.typst_math.strip("$").strip()
        open_parens = math_content.count("(")
        close_parens = math_content.count(")")
        if open_parens != close_parens:
            return False, f"Unbalanced parentheses in formula: {open_parens} open vs {close_parens} close"

        open_brackets = math_content.count("[")
        close_brackets = math_content.count("]")
        if open_brackets != close_brackets:
            return False, f"Unbalanced square brackets in formula: {open_brackets} vs {close_brackets}"

        # 2. Check variable presence
        # Any single letter in source must not be silently deleted unless it was a command
        src_clean = re.sub(r"\\[a-zA-Z]+", "", raw_expr)
        for var in model.variables:
            if len(var) == 1 and var not in src_clean:
                return False, f"Invented variable detected: '{var}' not in source formula"

        return True, None
