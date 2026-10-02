#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""export_leaflet_pdf.py - Tên cũ, giữ để tương thích. Dùng export_print_pdf.py (cùng tham số)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_print_pdf import main  # noqa: E402

if __name__ == "__main__":
    main()
