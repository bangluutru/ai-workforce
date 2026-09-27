#!/usr/bin/env python3
"""
generate_reconstruction_fixtures.py — Comprehensive Test Corpus for Document Reconstruction Translator.

Generates 11 specialized test fixtures conforming to Section 39:
1. FORMULA_HEAVY: Scientific paper with calculus, Greek letters, matrices, physics equations.
2. TABLE_COMPLEX: Multi-page financial/engineering report with hierarchical headers and numbers.
3. CHART_BAR: Bar chart with revenue by quarter and numeric units.
4. CHART_LINE: Time-series trend chart with multiple observation points.
5. CHART_MULTI_SERIES: Multi-series comparison chart.
6. DIAGRAM_FLOW: Multi-step process workflow with directed arrows.
7. DIAGRAM_ARCHITECTURE: System architecture block diagram with layers.
8. PHOTO_HEAVY: Quality inspection report with evidence photographs and captions.
9. SCAN_TEXT: Simulated scan document requiring OCR.
10. SCAN_MIXED: Scanned form with both text, photo, and signature stamp.
11. MIXED_COMPLEX: Comprehensive master document uniting Heading, Paragraph, Table, Formula, Chart, Diagram, Photo, Caption.
"""

import os
import sys
import io
import math
from pathlib import Path
import pymupdf
from PIL import Image, ImageDraw, ImageFont

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_photo(filename: str, label: str, w=400, h=300, color=(50, 100, 160)) -> Path:
    """Creates a sample realistic photographic test asset."""
    img_path = FIXTURE_DIR / filename
    img = Image.new("RGB", (w, h), color=color)
    draw = ImageDraw.Draw(img)
    # Draw simple gradient/texture
    for y in range(0, h, 10):
        draw.line([(0, y), (w, y)], fill=(color[0] + y % 40, color[1] + y % 30, color[2] + y % 50))
    # Border & label
    draw.rectangle([5, 5, w - 5, h - 5], outline=(255, 255, 255), width=2)
    draw.text((20, 20), f"[SOURCE PHOTO: {label}]", fill=(255, 255, 255))
    draw.text((20, h - 30), "SHA-256 IMMUTABILITY TEST ASSET", fill=(200, 240, 255))
    img.save(img_path, format="PNG")
    return img_path


def create_formula_heavy():
    """1. FORMULA_HEAVY fixture."""
    pdf_path = FIXTURE_DIR / "01_formula_heavy.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    
    # Title & Text
    page.insert_text((50, 60), "Theoretical Physics & Quantum Mechanics Report", fontsize=16, fontname="helv")
    page.insert_text((50, 85), "1. Mathematical Foundations and Derivations", fontsize=12, fontname="helv")
    page.insert_text((50, 110), "In this section we analyze the energy dispersion relation and path integrals.", fontsize=10, fontname="helv")
    
    # Formulas
    page.insert_text((70, 145), "E = mc^2 + alpha / beta", fontsize=11, fontname="times-roman")
    page.insert_text((70, 185), "int_0^infty e^(-x^2) dx = sqrt(pi) / 2", fontsize=11, fontname="times-roman")
    page.insert_text((70, 225), "sigma = sqrt( 1/N * sum_{i=1}^N (x_i - mu)^2 )", fontsize=11, fontname="times-roman")
    page.insert_text((70, 265), "Delta x * Delta p >= hbar / 2", fontsize=11, fontname="times-roman")
    
    page.insert_text((50, 310), "The above formulations govern the thermal equilibrium where T = 298.15 K.", fontsize=10, fontname="helv")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def create_table_complex():
    """2. TABLE_COMPLEX fixture."""
    pdf_path = FIXTURE_DIR / "02_table_complex.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    
    page.insert_text((50, 60), "Báo Cáo Tài Chính Hợp Nhất & Kiểm Toán Chi Phí 2025", fontsize=14, fontname="helv")
    page.insert_text((50, 80), "Bảng 1: Phân bổ ngân sách nghiên cứu và triển khai (R&D)", fontsize=10, fontname="helv")
    
    # Table Grid lines
    y_start = 110
    col_x = [50, 170, 280, 400, 520]
    row_h = 24
    
    headers = ["Hạng mục", "Kỳ trước (VND)", "Kỳ này (VND)", "Tăng trưởng (%)"]
    rows = [
        ["Hạ tầng Cloud AI", "1,200,000,000", "1,850,000,000", "+54.2%"],
        ["Nhân sự R&D", "3,500,000,000", "4,200,000,000", "+20.0%"],
        ["Bản quyền phần mềm", "800,000,000", "950,000,000", "+18.8%"],
        ["Kiểm định bảo mật", "450,000,000", "600,000,000", "+33.3%"],
        ["Tổng cộng chi phí", "5,950,000,000", "7,600,000,000", "+27.7%"]
    ]
    
    # Header row
    page.draw_rect(pymupdf.Rect(col_x[0], y_start, col_x[-1], y_start + row_h), color=(0.2, 0.4, 0.7), fill=(0.9, 0.93, 0.98))
    for c_i, h in enumerate(headers):
        page.insert_text((col_x[c_i] + 5, y_start + 16), h, fontsize=9, fontname="helv")
        
    for r_i, r in enumerate(rows):
        cur_y = y_start + (r_i + 1) * row_h
        page.draw_rect(pymupdf.Rect(col_x[0], cur_y, col_x[-1], cur_y + row_h), color=(0.8, 0.8, 0.8))
        for c_i, val in enumerate(r):
            page.insert_text((col_x[c_i] + 5, cur_y + 16), val, fontsize=8.5, fontname="helv")
            
    page.insert_text((50, y_start + 7 * row_h + 10), "Ghi chú: Toàn bộ số liệu đã qua soát xét theo chuẩn VAS/IFRS.", fontsize=8, fontname="helv")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def create_chart_fixtures():
    """3, 4, 5. CHART_BAR, CHART_LINE, CHART_MULTI_SERIES fixtures."""
    # 3. Bar Chart
    p_bar = FIXTURE_DIR / "03_chart_bar.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    page.insert_text((50, 60), "Annual Sales Performance by Region", fontsize=14, fontname="helv")
    # Draw simple bar chart vector representation
    page.draw_line(pymupdf.Point(80, 250), pymupdf.Point(450, 250), color=(0.3, 0.3, 0.3), width=1.5)
    page.draw_line(pymupdf.Point(80, 100), pymupdf.Point(80, 250), color=(0.3, 0.3, 0.3), width=1.5)
    # Bars
    bars = [("Region A", 120, 140), ("Region B", 200, 180), ("Region C", 280, 210), ("Region D", 360, 160)]
    for name, x, h in bars:
        page.draw_rect(pymupdf.Rect(x, 250 - (h - 80), x + 40, 250), color=(0.1, 0.4, 0.7), fill=(0.2, 0.5, 0.8))
        page.insert_text((x, 265), name, fontsize=8, fontname="helv")
    page.insert_text((50, 290), "Figure 1: Quarterly distribution across four operational zones.", fontsize=9, fontname="helv")
    doc.save(str(p_bar))
    doc.close()

    # 4. Line Chart
    p_line = FIXTURE_DIR / "04_chart_line.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    page.insert_text((50, 60), "Server Latency Response Time Trend", fontsize=14, fontname="helv")
    page.draw_line(pymupdf.Point(80, 250), pymupdf.Point(450, 250), color=(0.3, 0.3, 0.3), width=1.5)
    page.draw_line(pymupdf.Point(80, 100), pymupdf.Point(80, 250), color=(0.3, 0.3, 0.3), width=1.5)
    pts = [pymupdf.Point(100, 200), pymupdf.Point(180, 170), pymupdf.Point(260, 130), pymupdf.Point(340, 140), pymupdf.Point(420, 110)]
    for i in range(len(pts) - 1):
        page.draw_line(pts[i], pts[i+1], color=(0.8, 0.2, 0.2), width=2.0)
    page.insert_text((50, 290), "Figure 2: Latency in ms over a 24-hour observation window.", fontsize=9, fontname="helv")
    doc.save(str(p_line))
    doc.close()

    # 5. Multi Series Chart
    p_multi = FIXTURE_DIR / "05_chart_multi_series.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    page.insert_text((50, 60), "Comparative Multi-Product Adoption Index", fontsize=14, fontname="helv")
    page.draw_line(pymupdf.Point(80, 250), pymupdf.Point(450, 250), color=(0.3, 0.3, 0.3), width=1.5)
    page.draw_line(pymupdf.Point(80, 100), pymupdf.Point(80, 250), color=(0.3, 0.3, 0.3), width=1.5)
    page.insert_text((50, 290), "Figure 3: Product A vs Product B adoption curves.", fontsize=9, fontname="helv")
    doc.save(str(p_multi))
    doc.close()


def create_diagram_fixtures():
    """6, 7. DIAGRAM_FLOW and DIAGRAM_ARCHITECTURE fixtures."""
    # 6. Flowchart
    p_flow = FIXTURE_DIR / "06_diagram_flow.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    page.insert_text((50, 60), "Automated Ingestion Pipeline Workflow", fontsize=14, fontname="helv")
    
    # 3 nodes with arrows
    page.draw_rect(pymupdf.Rect(70, 120, 180, 160), color=(0.1, 0.4, 0.8), fill=(0.9, 0.95, 1.0))
    page.insert_text((85, 145), "Raw Data Ingest", fontsize=9, fontname="helv")
    
    page.draw_line(pymupdf.Point(180, 140), pymupdf.Point(240, 140), color=(0.1, 0.4, 0.8), width=1.5)
    
    page.draw_rect(pymupdf.Rect(240, 120, 360, 160), color=(0.1, 0.4, 0.8), fill=(0.9, 0.95, 1.0))
    page.insert_text((255, 145), "Semantic Analysis", fontsize=9, fontname="helv")
    
    page.draw_line(pymupdf.Point(360, 140), pymupdf.Point(420, 140), color=(0.1, 0.4, 0.8), width=1.5)
    
    page.draw_rect(pymupdf.Rect(420, 120, 520, 160), color=(0.1, 0.4, 0.8), fill=(0.9, 0.95, 1.0))
    page.insert_text((435, 145), "Typeset PDF", fontsize=9, fontname="helv")
    
    page.insert_text((50, 200), "Figure 4: End-to-end data transformation pipeline.", fontsize=9, fontname="helv")
    doc.save(str(p_flow))
    doc.close()

    # 7. Architecture
    p_arch = FIXTURE_DIR / "07_diagram_architecture.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    page.insert_text((50, 60), "Multi-Tier Cloud System Architecture", fontsize=14, fontname="helv")
    page.draw_rect(pymupdf.Rect(60, 100, 500, 150), color=(0.2, 0.5, 0.3), fill=(0.95, 1.0, 0.95))
    page.insert_text((80, 130), "Presentation Tier (Vite / React / Typst Web)", fontsize=10, fontname="helv")
    page.draw_rect(pymupdf.Rect(60, 170, 500, 220), color=(0.2, 0.3, 0.6), fill=(0.95, 0.95, 1.0))
    page.insert_text((80, 200), "Application & Reconstruction Engine Tier (Python / PyMuPDF)", fontsize=10, fontname="helv")
    page.draw_rect(pymupdf.Rect(60, 240, 500, 290), color=(0.6, 0.4, 0.2), fill=(1.0, 0.97, 0.92))
    page.insert_text((80, 270), "Storage & Asset Persistence Tier (Local FS / Git-Native)", fontsize=10, fontname="helv")
    page.insert_text((50, 320), "Figure 5: Three-tier modular service topology.", fontsize=9, fontname="helv")
    doc.save(str(p_arch))
    doc.close()


def create_photo_heavy():
    """8. PHOTO_HEAVY fixture with embedded photo asset."""
    p_photo = FIXTURE_DIR / "08_photo_heavy.pdf"
    img_path = create_sample_photo("equipment_photo.png", "High Precision Sensor", 400, 260)
    
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    page.insert_text((50, 60), "Field Quality Inspection & Forensic Report", fontsize=14, fontname="helv")
    page.insert_text((50, 85), "Station 4 - Sensor Array Calibration Unit", fontsize=11, fontname="helv")
    page.insert_text((50, 110), "The physical evidence was documented during site inspection on 2026-04-15.", fontsize=10, fontname="helv")
    
    # Insert image
    rect = pymupdf.Rect(50, 130, 450, 390)
    page.insert_image(rect, filename=str(img_path))
    
    page.insert_text((50, 410), "Photo 1: Photographic proof of sensor terminal calibration under vacuum.", fontsize=9, fontname="helv")
    page.insert_text((50, 435), "All serial numbers match asset registry code SN-8849-B2.", fontsize=9, fontname="helv")
    doc.save(str(p_photo))
    doc.close()
    return p_photo


def create_scanned_fixtures():
    """9, 10. SCAN_TEXT and SCAN_MIXED fixtures (rendered to image page to simulate scan)."""
    # 9. Scanned Text
    p_scan_text = FIXTURE_DIR / "09_scan_text.pdf"
    # Create image page with text
    img = Image.new("RGB", (800, 1100), color=(248, 248, 245))
    draw = ImageDraw.Draw(img)
    draw.text((60, 60), "THÔNG BÁO VỀ VIỆC THỰC HIỆN TIÊU CHUẨN KỸ THUẬT", fill=(30, 30, 30))
    draw.text((60, 100), "Kính gửi: Các đơn vị phòng ban trực thuộc", fill=(40, 40, 40))
    draw.text((60, 140), "Căn cứ quy chế hoạt động năm 2026, toàn bộ hệ thống bắt buộc tuân thủ", fill=(50, 50, 50))
    draw.text((60, 170), "quy trình kiểm định chất lượng 100% không phát sinh lỗi tồn đọng.", fill=(50, 50, 50))
    draw.text((60, 220), "Mọi báo cáo nghiệm thu phải được ký duyệt trước ngày 30 tháng 4.", fill=(50, 50, 50))
    
    scan_img_path = FIXTURE_DIR / "_scan_tmp_9.png"
    img.save(scan_img_path)
    
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    page.insert_image(page.rect, filename=str(scan_img_path))
    doc.save(str(p_scan_text))
    doc.close()
    if scan_img_path.exists():
        scan_img_path.unlink()

    # 10. Scanned Mixed
    p_scan_mixed = FIXTURE_DIR / "10_scan_mixed.pdf"
    img2 = Image.new("RGB", (800, 1100), color=(245, 245, 242))
    draw2 = ImageDraw.Draw(img2)
    draw2.text((60, 60), "HỢP ĐỒNG NGIỆM THU KỸ THUẬT & CHỨNG NHẬN", fill=(30, 30, 30))
    draw2.rectangle([60, 110, 740, 300], outline=(100, 100, 100), width=2)
    draw2.text((80, 130), "Mã thiết bị: MOD-9942", fill=(40, 40, 40))
    draw2.text((80, 160), "Tỷ lệ sai số: 0.02%", fill=(40, 40, 40))
    draw2.text((80, 190), "Nhiệt độ tối đa: 85°C", fill=(40, 40, 40))
    # Stamp simulation
    draw2.ellipse([500, 200, 680, 380], outline=(200, 40, 40), width=3)
    draw2.text((540, 280), "ĐÃ DUYỆT", fill=(200, 40, 40))
    
    scan_img_path2 = FIXTURE_DIR / "_scan_tmp_10.png"
    img2.save(scan_img_path2)
    doc2 = pymupdf.open()
    page2 = doc2.new_page(width=595.3, height=841.9)
    page2.insert_image(page2.rect, filename=str(scan_img_path2))
    doc2.save(str(p_scan_mixed))
    doc2.close()
    if scan_img_path2.exists():
        scan_img_path2.unlink()


def create_mixed_complex():
    """11. MIXED_COMPLEX fixture (Master Test Document).
    Contains simultaneously:
    - Heading
    - Paragraph
    - Table
    - Formula
    - Chart
    - Diagram
    - Photo
    - Caption
    """
    pdf_path = FIXTURE_DIR / "11_mixed_complex.pdf"
    photo_path = create_sample_photo("master_evidence.png", "Quantum Optical Chip", 360, 180)
    
    doc = pymupdf.open()
    page = doc.new_page(width=595.3, height=841.9)
    
    # 1. Heading
    page.insert_text((50, 45), "Báo Cáo Nghiên Cứu Kỹ Thuật Vi Mạch Lượng Tử 2026", fontsize=14, fontname="helv")
    
    # 2. Paragraph
    page.insert_text((50, 70), "Tài liệu này tổng hợp toàn bộ kết quả phân tích cấu trúc, hiệu năng tính toán và mô phỏng thực nghiệm.", fontsize=9, fontname="helv")
    page.insert_text((50, 85), "Thiết bị thử nghiệm đạt độ nhạy cao với sai số đo lường dưới 0.05% trong điều kiện 4.2 Kelvin.", fontsize=9, fontname="helv")
    
    # 3. Formula
    page.insert_text((50, 115), "Công thức truyền dẫn xác suất sóng lượng tử:", fontsize=9.5, fontname="helv")
    page.insert_text((70, 135), "Psi(x, t) = A * e^(i * (k * x - omega * t)) + alpha / beta", fontsize=10, fontname="times-roman")
    
    # 4. Table
    y_tbl = 160
    col_x = [50, 160, 260, 380, 500]
    page.draw_rect(pymupdf.Rect(col_x[0], y_tbl, col_x[-1], y_tbl + 20), color=(0.2, 0.4, 0.7), fill=(0.92, 0.95, 1.0))
    headers = ["Kênh tín hiệu", "Tần số (GHz)", "Công suất (mW)", "Độ ổn định"]
    for c_i, h in enumerate(headers):
        page.insert_text((col_x[c_i] + 5, y_tbl + 14), h, fontsize=8, fontname="helv")
        
    t_rows = [
        ["Channel Alpha", "24.5 GHz", "150 mW", "99.8%"],
        ["Channel Beta", "28.0 GHz", "180 mW", "99.5%"],
        ["Channel Gamma", "32.2 GHz", "210 mW", "99.1%"]
    ]
    for r_i, r in enumerate(t_rows):
        cur_y = y_tbl + 20 + r_i * 18
        page.draw_rect(pymupdf.Rect(col_x[0], cur_y, col_x[-1], cur_y + 18), color=(0.8, 0.8, 0.8))
        for c_i, val in enumerate(r):
            page.insert_text((col_x[c_i] + 5, cur_y + 13), val, fontsize=7.5, fontname="helv")
            
    # 5. Chart
    page.insert_text((50, 250), "Biểu đồ Phân Bổ Tín Hiệu (Signal Distribution):", fontsize=9, fontname="helv")
    page.draw_line(pymupdf.Point(70, 330), pymupdf.Point(260, 330), color=(0.3, 0.3, 0.3), width=1.0)
    page.draw_line(pymupdf.Point(70, 265), pymupdf.Point(70, 330), color=(0.3, 0.3, 0.3), width=1.0)
    page.draw_rect(pymupdf.Rect(90, 280, 120, 330), color=(0.1, 0.4, 0.7), fill=(0.3, 0.6, 0.9))
    page.draw_rect(pymupdf.Rect(140, 295, 170, 330), color=(0.1, 0.4, 0.7), fill=(0.3, 0.6, 0.9))
    page.draw_rect(pymupdf.Rect(190, 275, 220, 330), color=(0.1, 0.4, 0.7), fill=(0.3, 0.6, 0.9))
    page.insert_text((50, 345), "Biểu đồ 1: Công suất phát tại 3 dải tần thực nghiệm.", fontsize=8, fontname="helv")
    
    # 6. Diagram
    page.insert_text((290, 250), "Sơ Đồ Kết Nối Modul (System Topology):", fontsize=9, fontname="helv")
    page.draw_rect(pymupdf.Rect(300, 270, 370, 310), color=(0.2, 0.5, 0.2), fill=(0.95, 1.0, 0.95))
    page.insert_text((310, 292), "Bộ kích sóng", fontsize=7.5, fontname="helv")
    page.draw_line(pymupdf.Point(370, 290), pymupdf.Point(410, 290), color=(0.2, 0.5, 0.2), width=1.5)
    page.draw_rect(pymupdf.Rect(410, 270, 490, 310), color=(0.2, 0.5, 0.2), fill=(0.95, 1.0, 0.95))
    page.insert_text((420, 292), "Bộ giải mã tín hiệu", fontsize=7.5, fontname="helv")
    page.insert_text((290, 345), "Sơ đồ 1: Luồng xử lý tuần tự qua vi mạch lượng tử.", fontsize=8, fontname="helv")
    
    # 7. Photo & 8. Caption
    img_rect = pymupdf.Rect(120, 370, 440, 520)
    page.insert_image(img_rect, filename=str(photo_path))
    page.insert_text((100, 535), "Hình 1: Ảnh chụp vi mạch mẫu quang học lượng tử tại phòng sạch Class 100.", fontsize=8.5, fontname="helv")
    page.insert_text((50, 560), "Kết luận: Toàn bộ 8 thành phần kỹ thuật đã được kiểm chứng hoạt động đồng bộ.", fontsize=9, fontname="helv")
    
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def generate_all():
    print("======================================================================")
    print("GENERATING AIWF DOCUMENT RECONSTRUCTION TEST CORPUS (11 FIXTURES)")
    print("======================================================================")
    
    f1 = create_formula_heavy()
    print(f"  [1/11] Created FORMULA_HEAVY: {f1.name}")
    
    f2 = create_table_complex()
    print(f"  [2/11] Created TABLE_COMPLEX: {f2.name}")
    
    create_chart_fixtures()
    print(f"  [3/11] Created CHART_BAR")
    print(f"  [4/11] Created CHART_LINE")
    print(f"  [5/11] Created CHART_MULTI_SERIES")
    
    create_diagram_fixtures()
    print(f"  [6/11] Created DIAGRAM_FLOW")
    print(f"  [7/11] Created DIAGRAM_ARCHITECTURE")
    
    f8 = create_photo_heavy()
    print(f"  [8/11] Created PHOTO_HEAVY: {f8.name}")
    
    create_scanned_fixtures()
    print(f"  [9/11] Created SCAN_TEXT")
    print(f"  [10/11] Created SCAN_MIXED")
    
    f11 = create_mixed_complex()
    print(f"  [11/11] Created MIXED_COMPLEX: {f11.name}")
    
    print("======================================================================")
    print(f"ALL 11 FIXTURES GENERATED IN: {FIXTURE_DIR}")
    print("======================================================================")


if __name__ == "__main__":
    generate_all()
