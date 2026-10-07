#!/usr/bin/env python3
# R7-SHIM → .agents/skills/_shared/office/soffice_tools.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "_shared" / "office"))

from soffice_tools import (convert, find_soffice, get_soffice_env, main,  # noqa: F401,E402
                           recalc_xlsx, render_png, require_soffice, run_soffice)

if __name__ == "__main__":
    sys.exit(main())
