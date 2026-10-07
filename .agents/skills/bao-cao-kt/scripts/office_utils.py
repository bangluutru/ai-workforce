#!/usr/bin/env python3
# R7-SHIM → .agents/skills/_shared/office/soffice_tools.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared" / "office"))

from soffice_tools import convert, find_soffice, recalc_xlsx, render_png, require_soffice  # noqa: F401,E402
