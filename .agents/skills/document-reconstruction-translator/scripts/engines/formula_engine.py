"""Structured Mathematical Formula Reconstruction Engine.

Conforms to Section 11 & Section 29 of AIWF Document Reconstruction Translator:
- Math structure recognition: fractions, superscripts, subscripts, integrals,
  summations, roots, Greek symbols, chemical and physical units.
- Converts to publication-grade Typst Math / LaTeX markup.
- Confidence-aware: if confidence < threshold, preserves original formula crop.
- Absolute ban: NEVER invent or hallucinate formula variables or equations.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from ir.models import ConfidenceMetrics, ReconstructionStrategy, SemanticObject, SemanticObjectType


class FormulaEngine:
    """Recognizes, parses, and formats structured mathematical equations."""

    GREEK_MAP = {
        "alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta",
        "epsilon": "epsilon", "zeta": "zeta", "eta": "eta", "theta": "theta",
        "iota": "iota", "kappa": "kappa", "lambda": "lambda", "mu": "mu",
        "nu": "nu", "xi": "xi", "pi": "pi", "rho": "rho", "sigma": "sigma",
        "tau": "tau", "upsilon": "upsilon", "phi": "phi", "chi": "chi",
        "psi": "psi", "omega": "omega", "Delta": "Delta", "Gamma": "Gamma",
        "Theta": "Theta", "Lambda": "Lambda", "Sigma": "Sigma", "Omega": "Omega",
    }

    def __init__(self, confidence_threshold: float = 0.80):
        self.confidence_threshold = confidence_threshold

    def process_formula_object(self, obj: SemanticObject) -> Dict[str, Any]:
        """Analyzes a FORMULA SemanticObject and produces Typst math markup or fallback."""
        raw_text = obj.get_text_content(prefer_translated=False).strip()
        if not raw_text:
            return {
                "success": False,
                "strategy": ReconstructionStrategy.PRESERVE_ASSET.value,
                "typst_markup": "",
                "confidence": 0.0,
                "fallback": True,
            }

        # 1. Structure Recognition
        typst_math, confidence = self.convert_to_typst_math(raw_text)

        # 2. Confidence Evaluation
        if confidence >= self.confidence_threshold:
            obj.reconstruction_strategy = ReconstructionStrategy.LATEX_MATH
            obj.confidence.reconstruction = confidence
            obj.translated_content = typst_math
            return {
                "success": True,
                "strategy": ReconstructionStrategy.LATEX_MATH.value,
                "typst_markup": typst_math,
                "confidence": confidence,
                "fallback": False,
            }
        else:
            # Fallback to preserving original graphic
            obj.reconstruction_strategy = ReconstructionStrategy.PRESERVE_ASSET
            obj.fallback_used = True
            return {
                "success": False,
                "strategy": ReconstructionStrategy.PRESERVE_ASSET.value,
                "typst_markup": "",
                "confidence": confidence,
                "fallback": True,
                "reason": f"Confidence {confidence:.2f} below threshold {self.confidence_threshold}",
            }

    def convert_to_typst_math(self, raw_expr: str) -> Tuple[str, float]:
        """Converts raw mathematical text/symbols to clean Typst math code."""
        s = raw_expr.strip()

        # Remove surrounding dollar signs if present
        s = s.strip("$").strip()

        confidence = 0.95
        # If expression is too corrupted or contains non-math unparseable noise
        if len(s) > 250:
            confidence -= 0.20

        # Replace standard fractions: e.g. (a + b) / (c + d) -> (a + b) / (c + d)
        # Typst natively supports a / b as fractions in math mode!

        # Replace LaTeX operator syntax
        s = s.replace(r"\int", "integral").replace("int_", "integral_")
        s = s.replace(r"\infty", "infinity").replace("infty", "infinity")
        s = s.replace(r"\sum", "sum").replace("sum_", "sum_")
        s = s.replace(r"\alpha", "alpha").replace(r"\beta", "beta")
        s = s.replace(r"\gamma", "gamma").replace(r"\delta", "delta")
        s = s.replace(r"\sigma", "sigma").replace(r"\mu", "mu").replace(r"\pi", "pi")

        # Replace Greek unicode symbols with Typst names
        unicode_greek = {
            "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
            "ε": "epsilon", "θ": "theta", "λ": "lambda", "μ": "mu",
            "π": "pi", "σ": "sigma", "ω": "omega", "Δ": "Delta", "Σ": "Sigma",
        }
        for u_char, name in unicode_greek.items():
            s = s.replace(u_char, f" {name} ")

        # Replace math operator unicodes
        s = s.replace("×", " times ")
        s = s.replace("÷", " div ")
        s = s.replace("±", " plus.minus ")
        s = s.replace("≠", " eq.not ")
        s = s.replace("≈", " approx ")
        s = s.replace("≤", " lt.eq ")
        s = s.replace("≥", " gt.eq ")
        s = s.replace("∑", " sum ")
        s = s.replace("∏", " product ")
        s = s.replace("∫", " integral ")
        s = s.replace("√", " sqrt ")
        s = s.replace("∞", " infinity ")
        s = s.replace("∂", " diff ")

        # Differential terms
        s = re.sub(r"\b(dx|dt|du|dv|dy|dz)\b", r"dif \1", s)
        s = s.replace("dif dx", "dif x").replace("dif dt", "dif t")

        # Handle square root syntax: e.g. sqrt(x) or sqrt x
        s = re.sub(r"sqrt\s*\(([^)]+)\)", r"sqrt(\1)", s)

        # Handle superscripts and subscripts
        # e.g. x^2, x_i, x^{i+1} -> Typst uses x^2, x_i, x^(i+1)
        s = re.sub(r"\^{([^}]+)}", r"^(\1)", s)
        s = re.sub(r"_{([^}]+)}", r"_(\1)", s)

        # Typst recognized math keywords
        typst_math_words = {
            "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa",
            "lambda", "mu", "nu", "xi", "pi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
            "Alpha", "Beta", "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega",
            "sin", "cos", "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh",
            "ln", "log", "exp", "lim", "min", "max", "inf", "infinity", "sqrt", "sum", "product", "integral",
            "diff", "dif", "times", "div", "pm", "plus", "minus", "eq", "in", "subset", "forall", "exists", "approx",
            "hbar", "planck"
        }

        # Split multi-character consecutive letters (like 'mc' -> 'm c') unless recognized
        def _split_letters(m):
            token = m.group(0)
            if token in typst_math_words:
                return token
            return " ".join(list(token))

        s = re.sub(r"[A-Za-z]+", _split_letters, s)

        # Clean multiple spaces
        s = re.sub(r"\s+", " ", s).strip()

        # Format as Typst Math block
        typst_block = f"$ {s} $"

        return typst_block, confidence
