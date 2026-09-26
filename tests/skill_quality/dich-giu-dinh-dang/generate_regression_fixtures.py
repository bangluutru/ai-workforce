#!/usr/bin/env python3
"""Edge-Safety and Table Regression Fixtures.

Generates deterministic PDF test cases for:
1. Edge-safety: text blocks near page boundaries
2. Table cell alignment: various column types

Uses pymupdf to create reproducible synthetic PDFs.
"""

from pathlib import Path
import pymupdf

OUTPUT_DIR = Path(__file__).resolve().parent / "fixtures"


def generate_edge_safety_fixture():
    """Generate PDF with text blocks positioned near all page edges.

    Test values:
    - Footer near right edge: "Cat.No. ST-2026-04"
    - Long footer near right edge: "ABC-9999-X | Rev.3 2026-04-01"
    - Page number near bottom: "Page 12 / 12"
    - Header near top edge: "CONFIDENTIAL"
    - Left-aligned near left edge: "© 2026 Sakura Technology"
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / "EDGE_safety_regression.pdf"

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Title (normal position)
    page.insert_text(
        (50, 60),
        "エッジセーフティテスト文書",
        fontsize=16,
        fontname="japan",
    )

    # Body text (normal position)
    page.insert_text(
        (50, 120),
        "この文書はページ境界付近のテキストクリッピングをテストします。",
        fontsize=10,
        fontname="japan",
    )

    # RIGHT EDGE: Short footer near right edge
    # Position text so it ends very close to right margin
    page.insert_text(
        (440, 822),
        "Cat.No. ST-2026-04",
        fontsize=8,
        fontname="helv",
    )

    # RIGHT EDGE: Long footer
    page.insert_text(
        (350, 808),
        "ABC-9999-X | Rev.3 2026-04-01",
        fontsize=7,
        fontname="helv",
    )

    # BOTTOM EDGE: Page number near bottom
    page.insert_text(
        (270, 832),
        "Page 12 / 12",
        fontsize=8,
        fontname="helv",
    )

    # TOP EDGE: Header near top
    page.insert_text(
        (50, 18),
        "社外秘 — CONFIDENTIAL",
        fontsize=7,
        fontname="japan",
    )

    # LEFT EDGE: Copyright near left edge
    page.insert_text(
        (8, 822),
        "© 2026 Sakura Technology",
        fontsize=7,
        fontname="helv",
    )

    # Additional right-edge test: numeric value
    page.insert_text(
        (480, 795),
        "98.7%",
        fontsize=9,
        fontname="helv",
    )

    doc.save(str(output))
    doc.close()
    print(f"✅ Edge-safety fixture: {output}")
    return output


def generate_table_regression_fixture():
    """Generate PDF with a well-structured table for alignment testing.

    Table structure: 4 columns × 7 rows
    - Column 1: Japanese label (left-aligned)
    - Column 2: Technical value (center)
    - Column 3: Unit/range (center)
    - Column 4: Notes (left-aligned)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / "TABLE_alignment_regression.pdf"

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Title
    page.insert_text(
        (50, 50),
        "テーブルアライメント回帰テスト",
        fontsize=14,
        fontname="japan",
    )

    # Table dimensions
    table_x = 50
    table_y = 80
    col_widths = [140, 120, 130, 105]  # total = 495
    row_height = 22
    num_rows = 8  # header + 7 data

    # Draw table borders
    for row in range(num_rows + 1):
        y = table_y + row * row_height
        page.draw_line(
            pymupdf.Point(table_x, y),
            pymupdf.Point(table_x + sum(col_widths), y),
            width=0.5,
        )

    for col_idx in range(len(col_widths) + 1):
        x = table_x + sum(col_widths[:col_idx])
        page.draw_line(
            pymupdf.Point(x, table_y),
            pymupdf.Point(x, table_y + num_rows * row_height),
            width=0.5,
        )

    # Table data
    headers = ["項目", "仕様値", "範囲・単位", "備考"]
    data_rows = [
        ["製品番号", "TK-2026-MX500", "—", "—"],
        ["検出精度", "98.7%", "±0.2%", "常温環境"],
        ["動作温度範囲", "-20℃～+80℃", "—", "結露なきこと"],
        ["供給電圧", "DC 12V～24V", "—", "リップル≤100mV"],
        ["消費電力", "3.5W", "待機 0.2W", "最大値"],
        ["通信速度", "115200bps", "—", "RS-485"],
        ["筐体材質", "SUS304", "—", "ステンレス鋼"],
    ]

    # Insert header text
    for col_idx, header in enumerate(headers):
        x = table_x + sum(col_widths[:col_idx]) + 5
        y = table_y + 15
        page.insert_text(
            (x, y),
            header,
            fontsize=9,
            fontname="japan",
        )

    # Insert data rows
    for row_idx, row_data in enumerate(data_rows):
        for col_idx, cell_text in enumerate(row_data):
            x = table_x + sum(col_widths[:col_idx]) + 5
            y = table_y + (row_idx + 1) * row_height + 15
            font = "japan" if any(
                ord(c) > 127 and c not in "℃±≤" for c in cell_text
            ) else "helv"
            page.insert_text(
                (x, y),
                cell_text,
                fontsize=8,
                fontname=font,
            )

    # Footer with catalog number near right edge (edge-safety overlap test)
    page.insert_text(
        (430, 822),
        "Cat.No. ST-2026-04",
        fontsize=7,
        fontname="helv",
    )

    # Copyright near left edge
    page.insert_text(
        (50, 822),
        "© 2026 株式会社サクラテクノロジー",
        fontsize=7,
        fontname="japan",
    )

    doc.save(str(output))
    doc.close()
    print(f"✅ Table regression fixture: {output}")
    return output


if __name__ == "__main__":
    generate_edge_safety_fixture()
    generate_table_regression_fixture()
    print("\n✅ All regression fixtures generated.")
