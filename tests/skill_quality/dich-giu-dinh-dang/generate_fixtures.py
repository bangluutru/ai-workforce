#!/usr/bin/env python3
"""
generate_fixtures.py — Create realistic test corpus for dich-giu-dinh-dang quality audit.

Generates D01–D08 test fixtures using python-docx, pymupdf, openpyxl, python-pptx.
All content is synthetic/anonymized — no confidential data.
"""

import os, sys
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

# === D01: Simple Japanese DOCX ===
def create_d01():
    """Simple Japanese business DOCX with headings, paragraphs, bullets, bold."""
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Yu Gothic'
    style.font.size = Pt(11)

    # Title
    p = doc.add_heading('株式会社サクラテクノロジー 事業計画書', level=1)

    # Date
    p = doc.add_paragraph('2026年4月1日')
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Section 1
    doc.add_heading('1. 会社概要', level=2)
    doc.add_paragraph(
        '株式会社サクラテクノロジーは、2018年に東京都港区で設立された'
        'ソフトウェア開発企業です。主にクラウドサービスの設計・開発・運用を'
        '手がけており、従業員数は現在120名です。'
    )
    doc.add_paragraph(
        '当社の強みは、AIを活用した業務自動化ソリューションの提供にあります。'
        '特に製造業向けの品質管理システムは、国内シェア第3位の実績を誇ります。'
    )

    # Bullet list
    doc.add_heading('2. 事業内容', level=2)
    items = [
        'クラウドインフラ構築・運用サービス',
        'AI品質管理システムの開発・販売',
        'デジタルトランスフォーメーション（DX）コンサルティング',
        'セキュリティ監査・脆弱性診断',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    # Bold text section
    doc.add_heading('3. 財務目標', level=2)
    p = doc.add_paragraph()
    p.add_run('2026年度の売上目標は').bold = False
    run = p.add_run('35億円')
    run.bold = True
    run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    p.add_run('です。前年度比')
    run2 = p.add_run('15%増')
    run2.bold = True
    p.add_run('を見込んでいます。')

    doc.add_paragraph(
        '営業利益率は8.5%を目標とし、研究開発費は売上高の12%を維持します。'
        '新規顧客獲得には月間500万円のマーケティング予算を充てます。'
    )

    out = FIXTURE_DIR / "D01_simple_business_ja.docx"
    doc.save(str(out))
    print(f"✅ D01: {out}")
    return out


# === D02: Complex Japanese DOCX with tables, images, mixed formatting ===
def create_d02():
    """Complex DOCX: tables, placeholder images, captions, headers, mixed fonts."""
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor, Cm
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = Document()
    style = doc.styles['Normal']
    style.font.size = Pt(10.5)

    # Header/Footer
    section = doc.sections[0]
    header = section.header
    hp = header.paragraphs[0]
    hp.text = "株式会社サクラテクノロジー — 社内限定資料"
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = "Page "

    doc.add_heading('品質管理レポート 第4四半期', level=1)
    doc.add_heading('1. 製品検査結果一覧', level=2)

    # Table
    table = doc.add_table(rows=5, cols=5)
    table.style = 'Light Shading Accent 1'
    headers = ['製品コード', '製品名', '検査数量', '合格率', '不良内容']
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h

    data = [
        ['SP-2026-A1', 'センサーモジュール Type-A', '1,250個', '99.2%', '外観傷 0.8%'],
        ['SP-2026-B3', '制御基板 Rev.3', '800個', '98.5%', 'はんだ不良 1.5%'],
        ['SP-2026-C7', '防水コネクタ M12', '2,100個', '99.8%', '寸法NG 0.2%'],
        ['SP-2026-D2', '電源ユニット 24V', '650個', '97.3%', '動作不良 2.7%'],
    ]
    for r, row_data in enumerate(data):
        for c, val in enumerate(row_data):
            table.rows[r+1].cells[c].text = val

    doc.add_paragraph()

    # Numbered sections with mixed formatting
    doc.add_heading('2. 品質改善活動', level=2)

    doc.add_heading('2.1 不良品低減プログラム', level=3)
    doc.add_paragraph(
        '第4四半期において、制御基板 Rev.3 のはんだ不良率を 1.5% から '
        '0.8% 以下に低減するため、以下の改善策を実施しました。'
    )

    items = [
        'はんだペースト粘度管理の厳格化（管理値: 180±20 Pa·s）',
        'リフロー温度プロファイルの最適化（ピーク温度: 245±3℃）',
        '検査員の再教育プログラム実施（全14名、計42時間）',
    ]
    for i, item in enumerate(items, 1):
        doc.add_paragraph(f'{i}. {item}')

    doc.add_heading('3. 次期計画', level=2)
    p = doc.add_paragraph('次四半期の目標不良率は')
    run = p.add_run('0.5%以下')
    run.bold = True
    p.add_run('とし、全製品ラインにおいて')
    run2 = p.add_run('Six Sigma基準（3.4 DPMO）')
    run2.italic = True
    p.add_run('の達成を目指します。')

    out = FIXTURE_DIR / "D02_complex_report_ja.docx"
    doc.save(str(out))
    print(f"✅ D02: {out}")
    return out


# === D03: Native PDF (Japanese text, tables, simple layout) ===
def create_d03():
    """Create a multi-page text-native Japanese PDF using PyMuPDF."""
    import pymupdf

    doc = pymupdf.open()

    # Page 1
    page = doc.new_page(width=595, height=842)  # A4
    # Title
    page.insert_text((50, 60), "技術仕様書", fontsize=18, fontname="japan")
    page.insert_text((50, 85), "製品番号: TK-2026-MX500", fontsize=11, fontname="japan")
    page.insert_text((50, 100), "作成日: 2026年3月15日", fontsize=10, fontname="japan")

    # Paragraph
    text1 = (
        "本書は、TK-2026-MX500 産業用センサーの技術仕様を定めるものです。"
        "本製品は、温度範囲 -20℃～+80℃ で動作し、IP67 防水規格に準拠しています。"
    )
    rc = page.insert_textbox(
        pymupdf.Rect(50, 130, 545, 220),
        text1, fontsize=10, fontname="japan", align=0
    )

    # Table simulation using lines and text
    y_start = 240
    cols = [50, 200, 380, 545]
    rows_y = [y_start, y_start+25, y_start+50, y_start+75, y_start+100, y_start+125]

    # Draw table grid
    for y in rows_y:
        page.draw_line((cols[0], y), (cols[-1], y), width=0.5)
    for x in cols:
        page.draw_line((x, rows_y[0]), (x, rows_y[-1]), width=0.5)

    # Table headers
    headers = ["項目", "仕様値", "備考"]
    for i, h in enumerate(headers):
        page.insert_text((cols[i]+5, rows_y[0]+17), h, fontsize=9, fontname="japan")

    # Table data
    tdata = [
        ["動作温度範囲", "-20℃ ～ +80℃", "結露なきこと"],
        ["供給電圧", "DC 12V ～ 24V", "リップル ≤100mV"],
        ["消費電力", "最大 3.5W", "待機時 0.2W"],
        ["通信規格", "RS-485 / Modbus RTU", "最大 115200bps"],
    ]
    for r, row in enumerate(tdata):
        for c, val in enumerate(row):
            page.insert_text((cols[c]+5, rows_y[r+1]+17), val, fontsize=8.5, fontname="japan")

    # Page 2 — more specifications
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((50, 60), "2. 物理仕様", fontsize=14, fontname="japan")

    specs = [
        "外形寸法: 45mm × 32mm × 18mm (W×D×H)",
        "重量: 約 85g（ケーブル含まず）",
        "筐体材質: SUS304 ステンレス鋼",
        "ケーブル長: 標準 2m（最大 10m まで延長可）",
        "取付方法: M3 ネジ 4点固定",
    ]
    for i, s in enumerate(specs):
        page2.insert_text((70, 100 + i*25), f"• {s}", fontsize=10, fontname="japan")

    page2.insert_text((50, 280), "3. 認証・規格", fontsize=14, fontname="japan")
    certs = [
        "CE マーキング (EN 61326-1:2013)",
        "UL 認証 (UL 61010-1)",
        "RoHS 指令 (2011/65/EU) 適合",
        "JIS C 0920:2003 (IP67) 準拠",
    ]
    for i, c in enumerate(certs):
        page2.insert_text((70, 320 + i*25), f"• {c}", fontsize=10, fontname="japan")

    out = FIXTURE_DIR / "D03_native_pdf_spec_ja.pdf"
    doc.save(str(out))
    doc.close()
    print(f"✅ D03: {out}")
    return out


# === D04: Visually Complex PDF (multi-column, diagrams placeholder) ===
def create_d04():
    """Visually complex PDF with multi-column layout, tables, headers/footers."""
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    # Header bar
    page.draw_rect(pymupdf.Rect(0, 0, 595, 35), color=(0.1, 0.3, 0.6), fill=(0.1, 0.3, 0.6))
    page.insert_text((20, 24), "サクラテクノロジー 技術報告書 Vol.12", fontsize=12,
                     fontname="japan", color=(1, 1, 1))
    page.insert_text((420, 24), "2026年3月号", fontsize=10,
                     fontname="japan", color=(1, 1, 1))

    # Left column
    lx0, lx1 = 30, 280
    page.insert_text((lx0, 65), "AIベース品質検査の導入効果", fontsize=13, fontname="japan")

    left_text = (
        "当社が開発したAI画像検査システム「SAKURA-EYE v3.0」は、"
        "従来の目視検査と比較して検出精度を98.7%まで向上させました。"
        "特に微細なはんだクラック検出において、従来法の3.2倍の"
        "検出感度を実現しています。導入コストは月額45万円で、"
        "人件費削減効果は年間約1,200万円と試算されます。"
    )
    page.insert_textbox(pymupdf.Rect(lx0, 80, lx1, 220), left_text,
                       fontsize=9, fontname="japan", align=0)

    # Right column
    rx0, rx1 = 310, 565
    page.insert_text((rx0, 65), "導入事例：XX電子工業", fontsize=13, fontname="japan")
    right_text = (
        "XX電子工業株式会社（従業員350名）は、2025年10月に"
        "SAKURA-EYE v3.0を本格導入しました。導入後6ヶ月で、"
        "不良品流出率を0.12%から0.03%に低減。"
        "年間の品質コスト削減額は約800万円に達しました。"
        "同社の品質管理部長は「AIの導入により、検査員の負担が"
        "大幅に軽減された」と評価しています。"
    )
    page.insert_textbox(pymupdf.Rect(rx0, 80, rx1, 220), right_text,
                       fontsize=9, fontname="japan", align=0)

    # Divider line between columns
    page.draw_line((295, 55), (295, 220), width=0.5, color=(0.5, 0.5, 0.5))

    # Table section spanning full width
    page.insert_text((30, 250), "検査精度比較表", fontsize=12, fontname="japan")

    # Draw comparison table
    y0 = 270
    col_x = [30, 170, 310, 450, 565]
    row_h = 22
    n_rows = 5
    for i in range(n_rows + 1):
        y = y0 + i * row_h
        page.draw_line((col_x[0], y), (col_x[-1], y), width=0.5)
    for x in col_x:
        page.draw_line((x, y0), (x, y0 + n_rows * row_h), width=0.5)

    # Header row
    thead = ["検査方式", "検出精度", "処理速度", "コスト/月"]
    for j, h in enumerate(thead):
        page.insert_text((col_x[j]+5, y0+15), h, fontsize=8, fontname="japan")

    trows = [
        ["目視検査", "92.3%", "120個/時間", "85万円"],
        ["従来型カメラ", "95.8%", "300個/時間", "55万円"],
        ["SAKURA-EYE v2", "97.4%", "500個/時間", "45万円"],
        ["SAKURA-EYE v3", "98.7%", "800個/時間", "45万円"],
    ]
    for i, row in enumerate(trows):
        for j, val in enumerate(row):
            page.insert_text((col_x[j]+5, y0+(i+1)*row_h+15), val, fontsize=8, fontname="japan")

    # Footer
    page.draw_line((30, 800), (565, 800), width=0.3, color=(0.5, 0.5, 0.5))
    page.insert_text((30, 820), "© 2026 サクラテクノロジー株式会社 — 社外秘",
                    fontsize=7, fontname="japan", color=(0.5, 0.5, 0.5))
    page.insert_text((500, 820), "Page 1/1",
                    fontsize=7, fontname="japan", color=(0.5, 0.5, 0.5))

    out = FIXTURE_DIR / "D04_complex_layout_ja.pdf"
    doc.save(str(out))
    doc.close()
    print(f"✅ D04: {out}")
    return out


# === D05: Scanned PDF simulation ===
def create_d05():
    """Create a simulated scanned PDF (rasterized text page)."""
    import pymupdf

    # Create a text page, render to image, then save as image-only PDF
    tmp_doc = pymupdf.open()
    page = tmp_doc.new_page(width=595, height=842)

    page.insert_text((50, 60), "請求書", fontsize=20, fontname="japan")
    page.insert_text((50, 90), "請求番号: INV-2026-0042", fontsize=11, fontname="japan")
    page.insert_text((50, 110), "発行日: 2026年3月20日", fontsize=10, fontname="japan")
    page.insert_text((50, 130), "支払期限: 2026年4月20日", fontsize=10, fontname="japan")

    page.insert_text((50, 170), "請求先: XX商事株式会社 御中", fontsize=11, fontname="japan")
    page.insert_text((350, 170), "発行元: サクラテクノロジー(株)", fontsize=10, fontname="japan")

    # Items table
    y0 = 210
    cols = [50, 280, 380, 470, 545]
    row_h = 20
    n_rows = 5
    for i in range(n_rows + 1):
        y = y0 + i * row_h
        page.draw_line((cols[0], y), (cols[-1], y), width=0.5)
    for x in cols:
        page.draw_line((x, y0), (x, y0 + n_rows * row_h), width=0.5)

    thead = ["品名", "数量", "単価(円)", "金額(円)"]
    for j, h in enumerate(thead):
        page.insert_text((cols[j]+3, y0+14), h, fontsize=8, fontname="japan")

    inv_data = [
        ["AI検査システム SAKURA-EYE v3 ライセンス", "1式", "5,400,000", "5,400,000"],
        ["設置・調整費用", "1式", "350,000", "350,000"],
        ["操作研修（2日間）", "1式", "180,000", "180,000"],
        ["年間保守サポート（初年度）", "1式", "648,000", "648,000"],
    ]
    for i, row in enumerate(inv_data):
        for j, val in enumerate(row):
            page.insert_text((cols[j]+3, y0+(i+1)*row_h+14), val, fontsize=7.5, fontname="japan")

    # Total
    page.insert_text((380, y0+n_rows*row_h+25), "小計: ¥6,578,000", fontsize=10, fontname="japan")
    page.insert_text((380, y0+n_rows*row_h+45), "消費税(10%): ¥657,800", fontsize=10, fontname="japan")
    page.insert_text((380, y0+n_rows*row_h+70), "合計: ¥7,235,800", fontsize=12, fontname="japan")

    # Render to image and create image-only PDF
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")
    tmp_doc.close()

    # Create image-only PDF
    scan_doc = pymupdf.open()
    scan_page = scan_doc.new_page(width=595, height=842)
    scan_page.insert_image(scan_page.rect, stream=img_bytes)

    out = FIXTURE_DIR / "D05_scanned_invoice_ja.pdf"
    scan_doc.save(str(out))
    scan_doc.close()
    print(f"✅ D05: {out}")
    return out


# === D06: PPTX ===
def create_d06():
    """Business presentation with titles, text boxes, shapes."""
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        print("⚠️  D06: python-pptx not installed. Skipping.")
        return None

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Slide 1 — Title
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "サクラテクノロジー 新製品紹介"
    slide.placeholders[1].text = "2026年度 第1四半期 戦略会議資料"

    # Slide 2 — Content with bullets
    slide2 = prs.slides.add_slide(prs.slide_layouts[1])
    slide2.shapes.title.text = "市場動向分析"
    tf = slide2.placeholders[1].text_frame
    tf.text = "国内IoTセンサー市場は年率12.5%で成長中"
    p2 = tf.add_paragraph()
    p2.text = "競合他社の主力製品との差別化ポイント"
    p3 = tf.add_paragraph()
    p3.text = "2026年度の市場規模予測: 約4,500億円"
    p4 = tf.add_paragraph()
    p4.text = "当社のシェア目標: 8.2% → 12.0%"

    # Slide 3 — Table
    slide3 = prs.slides.add_slide(prs.slide_layouts[5])  # blank
    slide3.shapes.title.text = "売上計画"

    from pptx.util import Emu
    rows, cols = 4, 4
    tbl = slide3.shapes.add_table(rows, cols, Inches(1), Inches(2), Inches(10), Inches(3)).table
    tbl.cell(0, 0).text = "四半期"
    tbl.cell(0, 1).text = "売上目標(億円)"
    tbl.cell(0, 2).text = "営業利益(億円)"
    tbl.cell(0, 3).text = "利益率"
    data = [
        ["Q1", "8.2", "0.65", "7.9%"],
        ["Q2", "9.5", "0.82", "8.6%"],
        ["Q3", "10.1", "0.91", "9.0%"],
    ]
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            tbl.cell(r+1, c).text = val

    out = FIXTURE_DIR / "D06_presentation_ja.pptx"
    prs.save(str(out))
    print(f"✅ D06: {out}")
    return out


# === D07: XLSX ===
def create_d07():
    """Spreadsheet with Japanese text, formulas, formatting, merged cells."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, numbers
    except ImportError:
        print("⚠️  D07: openpyxl not installed. Skipping.")
        return None

    wb = Workbook()
    ws = wb.active
    ws.title = "売上報告"

    # Merged header
    ws.merge_cells('A1:F1')
    ws['A1'] = "株式会社サクラテクノロジー 2026年度 月次売上報告書"
    ws['A1'].font = Font(name='Yu Gothic', size=14, bold=True)
    ws['A1'].alignment = Alignment(horizontal='center')

    # Column headers
    headers = ['月', '製品A売上(千円)', '製品B売上(千円)', '製品C売上(千円)', '合計(千円)', '前月比(%)']
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.font = Font(bold=True, size=10)
        cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        cell.font = Font(bold=True, size=10, color='FFFFFF')
        cell.alignment = Alignment(horizontal='center')

    # Data with formulas
    months = ['1月', '2月', '3月', '4月', '5月', '6月']
    prod_a = [12500, 13200, 14100, 13800, 15200, 16500]
    prod_b = [8900, 9100, 9500, 10200, 10800, 11300]
    prod_c = [5600, 5800, 6200, 6500, 6900, 7100]

    for i, (m, a, b, c) in enumerate(zip(months, prod_a, prod_b, prod_c)):
        row = 4 + i
        ws.cell(row=row, column=1, value=m)
        ws.cell(row=row, column=2, value=a)
        ws.cell(row=row, column=3, value=b)
        ws.cell(row=row, column=4, value=c)
        ws.cell(row=row, column=5).value = f'=SUM(B{row}:D{row})'
        if i > 0:
            ws.cell(row=row, column=6).value = f'=E{row}/E{row-1}*100'
            ws.cell(row=row, column=6).number_format = '0.0'

    # Summary row
    row_sum = 10
    ws.merge_cells(f'A{row_sum}:A{row_sum}')
    ws.cell(row=row_sum, column=1, value='合計')
    ws.cell(row=row_sum, column=1).font = Font(bold=True)
    for col in range(2, 5):
        ws.cell(row=row_sum, column=col).value = f'=SUM({chr(64+col)}4:{chr(64+col)}9)'
        ws.cell(row=row_sum, column=col).font = Font(bold=True)
    ws.cell(row=row_sum, column=5).value = f'=SUM(E4:E9)'
    ws.cell(row=row_sum, column=5).font = Font(bold=True)

    # Notes section
    ws.cell(row=12, column=1, value='備考:')
    ws.cell(row=12, column=1).font = Font(bold=True)
    ws.cell(row=13, column=1, value='• 製品Aは新規顧客向けセンサーモジュール')
    ws.cell(row=14, column=1, value='• 製品Bは既存顧客向け保守サービス')
    ws.cell(row=15, column=1, value='• 製品Cはソフトウェアライセンス収入')

    # Column widths
    ws.column_dimensions['A'].width = 8
    for c in ['B', 'C', 'D', 'E']:
        ws.column_dimensions[c].width = 18
    ws.column_dimensions['F'].width = 14

    out = FIXTURE_DIR / "D07_sales_report_ja.xlsx"
    wb.save(str(out))
    print(f"✅ D07: {out}")
    return out


# === D08: Reverse translation (VI → JA) ===
def create_d08():
    """Vietnamese DOCX for reverse translation to Japanese."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    style = doc.styles['Normal']
    style.font.size = Pt(11)

    doc.add_heading('BÁO CÁO HOẠT ĐỘNG KINH DOANH', level=1)
    doc.add_heading('Quý 1 năm 2026 — Công ty TNHH Sakura Technology Việt Nam', level=2)

    doc.add_heading('1. Tổng quan tình hình', level=2)
    doc.add_paragraph(
        'Trong quý 1 năm 2026, Công ty TNHH Sakura Technology Việt Nam đã đạt '
        'doanh thu 12,5 tỷ đồng, tăng 18% so với cùng kỳ năm trước. Lợi nhuận '
        'ròng đạt 1,8 tỷ đồng, tương đương biên lợi nhuận 14,4%.'
    )
    doc.add_paragraph(
        'Thị trường cảm biến công nghiệp tại Việt Nam tiếp tục tăng trưởng mạnh '
        'nhờ làn sóng chuyển đổi số trong ngành sản xuất. Số lượng khách hàng mới '
        'trong quý đạt 15 đơn vị, nâng tổng số khách hàng lên 87 đơn vị.'
    )

    doc.add_heading('2. Kết quả theo sản phẩm', level=2)

    # Table
    table = doc.add_table(rows=4, cols=4)
    table.style = 'Light Shading Accent 1'
    headers = ['Sản phẩm', 'Doanh thu (tỷ đồng)', 'Tỷ trọng (%)', 'Tăng trưởng YoY']
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    data = [
        ['Cảm biến SAKURA-EYE', '6,2', '49,6%', '+22%'],
        ['Dịch vụ bảo trì', '3,8', '30,4%', '+12%'],
        ['Phần mềm & Giấy phép', '2,5', '20,0%', '+25%'],
    ]
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            table.rows[r+1].cells[c].text = val

    doc.add_heading('3. Kế hoạch quý 2', level=2)
    items = [
        'Triển khai hệ thống SAKURA-EYE v3.0 tại 5 nhà máy mới',
        'Đào tạo 30 kỹ sư vận hành hệ thống AI kiểm tra',
        'Mở rộng đội ngũ kinh doanh thêm 8 nhân sự',
        'Mục tiêu doanh thu quý 2: 15 tỷ đồng (+20%)',
    ]
    for item in items:
        doc.add_paragraph(item, style='List Bullet')

    out = FIXTURE_DIR / "D08_business_report_vi.docx"
    doc.save(str(out))
    print(f"✅ D08: {out}")
    return out


if __name__ == "__main__":
    print("=" * 60)
    print("GENERATING TEST FIXTURES FOR dich-giu-dinh-dang AUDIT")
    print("=" * 60)

    create_d01()
    create_d02()
    create_d03()
    create_d04()
    create_d05()
    create_d06()
    create_d07()
    create_d08()

    print("\n" + "=" * 60)
    print("FIXTURE GENERATION COMPLETE")
    print(f"Location: {FIXTURE_DIR}")
    print("=" * 60)
