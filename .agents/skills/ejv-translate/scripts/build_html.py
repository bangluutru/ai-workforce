#!/usr/bin/env python3
# R7-SHIM → .agents/skills/_shared/html/responsive_html_builder.py
import sys
from pathlib import Path

# Add _shared/html to sys.path
_shared_html = Path(__file__).resolve().parents[2] / "_shared" / "html"
sys.path.insert(0, str(_shared_html))

from responsive_html_builder import main

if __name__ == "__main__":
    main()
