#!/usr/bin/env python3
"""Generate a synthetic Japanese PDF for blind testing the document-reconstruction-translator.

Creates a 3-page document about environmental technology cooperation with:
- Title and headings (text-like objects)
- A structured table (table object)
- Paragraphs with technical terminology
- A numbered list
- Mixed CJK and Latin content (model numbers, percentages)

This document has NEVER been processed by any translation skill.
"""

import pymupdf
import hashlib
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "production-closure-validation" / "document-D-blind"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "source").mkdir(exist_ok=True)

pdf_path = OUTPUT_DIR / "source" / "環境技術協力報告書_BLIND_TEST.pdf"

# Create document
doc = pymupdf.Document()

# ── Page 1: Title + Overview Table + Summary ──
page1 = doc.new_page(width=595, height=842)  # A4

# Title
page1.insert_text((72, 60), "環境技術協力プロジェクト報告書", fontname="japan", fontsize=16)
page1.insert_text((72, 82), "Environmental Technology Cooperation Project Report", fontname="helv", fontsize=10)
page1.insert_text((72, 100), "2025年度 第2四半期 実績報告", fontname="japan", fontsize=12)

# Table (drawn as rectangles + text)
table_y = 130
col_widths = [140, 330]
col_x = [72, 212]
row_height = 22
headers = ["項目", "内容"]
rows = [
    ["プロジェクト名", "ASEAN地域における水質浄化技術の移転と普及"],
    ["実施機関", "環境技術研究所（ETRI）"],
    ["対象国", "ベトナム、カンボジア、ラオス"],
    ["実施期間", "2024年4月 ～ 2027年3月（3年間）"],
    ["予算総額", "約1.5億円（150,000千円）"],
    ["担当者", "山田太郎（主任研究員）"],
]

# Draw table
for row_idx, row_data in enumerate([headers] + rows):
    y = table_y + row_idx * row_height
    for col_idx, cell_text in enumerate(row_data):
        x = col_x[col_idx]
        w = col_widths[col_idx]
        rect = pymupdf.Rect(x, y, x + w, y + row_height)
        page1.draw_rect(rect, color=(0.6, 0.6, 0.6), width=0.5)
        if row_idx == 0:
            page1.draw_rect(rect, fill=(0.9, 0.92, 0.95), color=(0.6, 0.6, 0.6), width=0.5)
        page1.insert_text((x + 4, y + 15), cell_text, fontname="japan", fontsize=9)

# Body text
body_y = table_y + (len(rows) + 1) * row_height + 20
paragraphs_p1 = [
    "Ⅰ．プロジェクト概要",
    "",
    "本プロジェクトは、ASEAN地域（ベトナム、カンボジア、ラオス）における水質浄化技術の移転と普及を",
    "目的とした3年間の技術協力事業である。特に、農村地域における安全な飲料水の確保と、工業地帯からの",
    "排水処理技術の改善に重点を置いている。",
    "",
    "主な活動内容は以下のとおりである：",
    "①　現地調査および水質分析（BOD、COD、SS、pH等の測定）",
    "②　浄水処理装置（モデルWP-3000A）の設置と運転指導",
    "③　現地技術者への研修プログラムの実施（延べ120名参加）",
    "④　処理水の水質モニタリングシステムの構築",
    "",
    "第2四半期の実績として、ベトナム・ハノイ近郊において2基の浄水処理装置を設置完了し、処理能力は",
    "日量500m³/日を達成した。処理水のBOD除去率は95.3%に達し、ベトナム環境基準QCVN 14:2008/BTNMT",
    "の排水基準（BOD≤30mg/L）を十分に満たしている。",
]

for i, line in enumerate(paragraphs_p1):
    if line:
        fsize = 12 if line.startswith("Ⅰ") else 9.5
        page1.insert_text((72, body_y + i * 14), line, fontname="japan", fontsize=fsize)

# ── Page 2: Results + Technical Details ──
page2 = doc.new_page(width=595, height=842)

paragraphs_p2 = [
    "Ⅱ．四半期別実績",
    "",
    "1. ベトナム拠点の進捗",
    "ハノイ市から北西約40kmに位置するVinh Phuc省において、パイロットプラントの設置と試運転を実施",
    "した。本設備は、凝集沈殿法と生物処理法を組み合わせたハイブリッド型浄水システム（型番: WP-3000A）",
    "であり、以下の仕様を有する：",
    "",
    "・処理能力：500m³/日",
    "・BOD除去率：95.3%",
    "・COD除去率：89.7%",
    "・SS除去率：98.1%",
    "・消費電力：15.2kWh/m³",
    "・設置面積：約200m²（既存建屋内）",
    "",
    "2. カンボジア拠点の進捗",
    "プノンペン近郊のKandal州において、農村部の井戸水浄化プロジェクトを開始した。現地のヒ素汚染",
    "（最大0.15mg/L、WHO基準0.01mg/L超過）に対応するため、鉄共沈法によるヒ素除去装置を3基設置",
    "した。処理後のヒ素濃度は0.005mg/L以下に低減され、WHO飲料水水質ガイドラインを達成している。",
    "",
    "3. ラオス拠点の進捗",
    "ビエンチャン市内の2つの地区において、簡易浄水システムの運転訓練を実施した。現地技術者42名が",
    "参加し、水質分析の基礎（濁度、残留塩素、大腸菌群数の測定）について実習を行った。",
    "",
    "Ⅲ．研修実績",
    "",
    "本四半期中に実施した研修プログラムの概要は以下のとおりである。",
]

for i, line in enumerate(paragraphs_p2):
    fsize = 12 if line.startswith("Ⅱ") or line.startswith("Ⅲ") else (10.5 if line.startswith(("1.", "2.", "3.")) else 9.5)
    if line:
        page2.insert_text((72, 55 + i * 14), line, fontname="japan", fontsize=fsize)

# Training results table
train_y = 55 + len(paragraphs_p2) * 14 + 10
train_headers = ["研修名", "実施場所", "参加者数", "期間"]
train_rows = [
    ["水質分析基礎研修", "ベトナム・ハノイ", "35名", "5日間"],
    ["浄水装置運転管理研修", "ベトナム・ハノイ", "28名", "3日間"],
    ["ヒ素除去技術研修", "カンボジア・プノンペン", "15名", "4日間"],
    ["簡易水質検査研修", "ラオス・ビエンチャン", "42名", "2日間"],
]

t_col_w = [150, 130, 60, 60]
t_col_x = [72]
for w in t_col_w[:-1]:
    t_col_x.append(t_col_x[-1] + w)

for row_idx, row_data in enumerate([train_headers] + train_rows):
    y = train_y + row_idx * 20
    for col_idx, cell_text in enumerate(row_data):
        x = t_col_x[col_idx]
        w = t_col_w[col_idx]
        rect = pymupdf.Rect(x, y, x + w, y + 20)
        page2.draw_rect(rect, color=(0.6, 0.6, 0.6), width=0.5)
        if row_idx == 0:
            page2.draw_rect(rect, fill=(0.9, 0.92, 0.95), color=(0.6, 0.6, 0.6), width=0.5)
        page2.insert_text((x + 4, y + 14), cell_text, fontname="japan", fontsize=8.5)

# ── Page 3: Future Plans + Conclusion ──
page3 = doc.new_page(width=595, height=842)

paragraphs_p3 = [
    "Ⅳ．今後の計画",
    "",
    "次四半期（第3四半期）の計画は以下のとおりである。",
    "",
    "1. ベトナム：処理能力の拡大（500m³/日→1,000m³/日）に向けた追加設備の設計・調達を実施する。",
    "   また、地元の環境局（DoNRE）との共同モニタリング体制を構築する。",
    "2. カンボジア：ヒ素除去装置の追加5基の設置を完了し、対象地域の飲料水供給人口を約5,000人に",
    "   拡大する計画である。",
    "3. ラオス：第3次研修プログラムを実施し、水処理施設のO&M（Operation & Maintenance）マニュアル",
    "   の現地語翻訳版を完成させる。",
    "",
    "Ⅴ．課題と対策",
    "",
    "現在の主な課題として、以下の3点が挙げられる。",
    "",
    "（1）電力供給の不安定性：農村部では停電が頻繁に発生するため、蓄電池（Liイオン電池、容量50kWh）",
    "     の設置を検討している。推定コストは約350万円/基である。",
    "（2）スペア部品の現地調達：フィルター膜（MF膜、孔径0.1μm）の現地調達が困難であり、日本からの",
    "     定期供給体制の確立が必要である。",
    "（3）現地人材の定着：研修修了者の約30%が他の機関に転職しており、継続的な人材育成プログラムの",
    "     構築が急務である。",
    "",
    "Ⅵ．結論",
    "",
    "本プロジェクトは、第2四半期において当初計画どおりの進捗を達成した。特に、ベトナムにおける浄水",
    "処理装置の設置・稼働、およびカンボジアにおけるヒ素除去技術の実装は、目標値を上回る成果を得て",
    "いる。今後は、処理能力のスケールアップと現地運営体制の強化を重点課題として取り組む。",
    "",
    "以上",
    "",
    "                                    環境技術研究所",
    "                                    主任研究員　山田太郎",
    "                                    2025年9月30日",
]

for i, line in enumerate(paragraphs_p3):
    if line:
        fsize = 12 if line.startswith("Ⅳ") or line.startswith("Ⅴ") or line.startswith("Ⅵ") else 9.5
        page3.insert_text((72, 55 + i * 14), line, fontname="japan", fontsize=fsize)

# Save
doc.save(str(pdf_path))
doc.close()

# Calculate SHA-256
sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

print(f"✅ Blind test PDF created: {pdf_path}")
print(f"   Pages: 3")
print(f"   SHA-256: {sha256}")
print(f"   Content: Environmental technology cooperation report (JA→VI)")
print(f"   Features: 2 tables, headings, numbered lists, technical specs, model numbers")
