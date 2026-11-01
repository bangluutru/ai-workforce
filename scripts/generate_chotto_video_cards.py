#!/usr/bin/env python3
"""
AI Workforce — Chotto 60s Video Graphic Cards Engine (1080x1080, Aspect 1:1)
Tuân thủ Luật R6 (bố cục & đồ họa), R7 (tái sử dụng font dùng chung).
Vùng an toàn phụ đề: Y=665..1080 TUYỆT ĐỐI KHÔNG chứa nội dung/chữ để nhường chỗ cho phụ đề ASS.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED_FONTS = REPO_ROOT / ".agents" / "skills" / "_shared" / "fonts"

W, H = 1080, 1080
MAX_CONTENT_Y = 635  # Giới hạn cứng Y <= 635 để chừa trống hoàn toàn Y=665..1080

def get_fonts():
    return {
        "jp_bold_large": ImageFont.truetype(str(SHARED_FONTS / "NotoSansJP-Bold.otf"), 52),
        "jp_bold_brand": ImageFont.truetype(str(SHARED_FONTS / "NotoSansJP-Bold.otf"), 68),
        "jp_bold_mid": ImageFont.truetype(str(SHARED_FONTS / "NotoSansJP-Bold.otf"), 40),
        "jp_regular_mid": ImageFont.truetype(str(SHARED_FONTS / "NotoSansJP-Regular.otf"), 26),
        "vi_bold_xl": ImageFont.truetype(str(SHARED_FONTS / "BeVietnamPro-Bold.ttf"), 38),
        "vi_bold_lg": ImageFont.truetype(str(SHARED_FONTS / "BeVietnamPro-Bold.ttf"), 30),
        "vi_bold_md": ImageFont.truetype(str(SHARED_FONTS / "BeVietnamPro-Bold.ttf"), 24),
        "vi_semi_md": ImageFont.truetype(str(SHARED_FONTS / "BeVietnamPro-SemiBold.ttf"), 22),
        "vi_reg_md": ImageFont.truetype(str(SHARED_FONTS / "BeVietnamPro-Regular.ttf"), 21),
        "vi_reg_sm": ImageFont.truetype(str(SHARED_FONTS / "BeVietnamPro-Regular.ttf"), 18),
        "badge": ImageFont.truetype(str(SHARED_FONTS / "BeVietnamPro-Bold.ttf"), 17),
    }

def create_base_canvas(accent_color=(56, 189, 248)):
    # Gradient nền xanh đen sang trọng (Dark Slate / Deep Indigo)
    base = Image.new("RGB", (W, H), (15, 23, 42))
    draw = ImageDraw.Draw(base)
    top_c = (15, 23, 42)
    bot_c = (10, 15, 30)
    for y in range(H):
        t = y / (H - 1)
        r = int(top_c[0] * (1 - t) + bot_c[0] * t)
        g = int(top_c[1] * (1 - t) + bot_c[1] * t)
        b = int(top_c[2] * (1 - t) + bot_c[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Glow ánh sáng mềm ở góc trên
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse((-120, -120, 360, 360), fill=(*accent_color, 45))
    odraw.ellipse((W - 320, -100, W + 120, 340), fill=(244, 63, 94, 30))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=50))
    base.paste(overlay, (0, 0), overlay)

    return base

def draw_header(draw, fonts, category="CHOTTO • ĐỜI SỐNG & THUẾ TẠI NHẬT", title_1="", title_2="", color_1=(56, 189, 248), color_2=(255, 255, 255)):
    # Category Pill
    pill_w = 460
    draw.rounded_rectangle([70, 45, 70 + pill_w, 82], radius=18, fill=(30, 41, 59, 220), outline=(56, 189, 248), width=1)
    draw.text((90, 52), f"🇯🇵 {category}", font=fonts["badge"], fill=(224, 242, 254))

    # Time badge
    draw.rounded_rectangle([W - 270, 45, W - 70, 82], radius=18, fill=(244, 63, 94, 40), outline=(244, 63, 94), width=1)
    draw.text((W - 250, 52), "⏱️ VIDEO 60 GIÂY", font=fonts["badge"], fill=(254, 205, 211))

    # Titles
    y_pos = 105
    if title_1:
        draw.text((70, y_pos), title_1, font=fonts["vi_bold_md"], fill=color_1)
        y_pos += 38
    if title_2:
        draw.text((70, y_pos), title_2, font=fonts["vi_bold_xl"], fill=color_2)

def generate_scene_1(out_path: Path):
    """Scene 1: Hook — Thư gửi cuối tháng 10: Đừng vội vứt vào thùng rác!"""
    fonts = get_fonts()
    im = create_base_canvas(accent_color=(239, 68, 68))
    draw = ImageDraw.Draw(im)
    draw_header(draw, fonts, "CẢNH BÁO CUỐI THÁNG 10", "PHONG BÌ BƯU ĐIỆN VỪA GỬI VỀ NHÀ?", "ĐỪNG VỘI VỨT VÀO THÙNG RÁC!", color_1=(251, 146, 60), color_2=(255, 255, 255))

    # Content Container Y=200..630
    box = [70, 200, W - 70, 625]
    draw.rounded_rectangle(box, radius=24, fill=(24, 34, 53), outline=(249, 115, 22), width=2)

    # Nội dung bên trong thẻ
    # Mô phỏng bì thư chính thức
    env = [110, 230, W - 110, 360]
    draw.rounded_rectangle(env, radius=16, fill=(248, 250, 252), outline=(203, 213, 225), width=2)
    # Tem bưu điện & dấu đỏ
    draw.rectangle([env[0] + 25, env[1] + 20, env[0] + 85, env[1] + 95], fill=(224, 231, 255), outline=(99, 102, 241), width=1)
    draw.text((env[0] + 35, env[1] + 45), "〒", font=fonts["jp_bold_mid"], fill=(79, 70, 229))
    draw.rounded_rectangle([env[2] - 120, env[1] + 20, env[2] - 25, env[1] + 65], radius=8, fill=(254, 226, 226), outline=(239, 68, 68), width=2)
    draw.text((env[2] - 105, env[1] + 28), "重要", font=fonts["jp_bold_mid"], fill=(220, 38, 38))

    # Tên thư trên phong bì
    draw.text((env[0] + 115, env[1] + 45), "保険料控除証明書 在中", font=fonts["jp_bold_mid"], fill=(30, 41, 59))
    draw.text((env[0] + 115, env[1] + 90), "(Thư gửi từ Hãng Bảo hiểm hoặc Cơ quan Nenkin)", font=fonts["vi_reg_sm"], fill=(100, 116, 139))

    # Lời giải thích cảnh báo
    warn_box = [110, 385, W - 110, 490]
    draw.rounded_rectangle(warn_box, radius=16, fill=(239, 68, 68, 40), outline=(239, 68, 68), width=1)
    draw.text((135, 405), "⚠️ KHÔNG PHẢI THƯ RÁC HAY QUẢNG CÁO!", font=fonts["vi_bold_md"], fill=(254, 205, 211))
    draw.text((135, 445), "Nhiều bạn tưởng nhầm hóa đơn đòi nợ nên lỡ tay vứt bỏ.", font=fonts["vi_reg_md"], fill=(241, 245, 249))

    # Hướng dẫn hành động nhanh
    draw.rounded_rectangle([110, 515, W - 110, 595], radius=16, fill=(16, 185, 129, 30), outline=(16, 185, 129), width=1)
    draw.text((135, 535), "👉 BẬT MÍ: Giấy này giúp bạn NHẬN LẠI TIỀN HOÀN THUẾ!", font=fonts["vi_bold_md"], fill=(110, 231, 183))
    draw.text((135, 568), "Hãy theo dõi 3 nhịp giải mã dưới đây để không mất tiền oan.", font=fonts["vi_reg_sm"], fill=(209, 250, 229))

    im.save(out_path, quality=95)

def generate_scene_2(out_path: Path):
    """Scene 2: Vấn đề của Chobi — Chữ Hán dài ngoằng, tưởng giấy đòi tiền."""
    fonts = get_fonts()
    im = create_base_canvas(accent_color=(234, 179, 8))
    draw = ImageDraw.Draw(im)
    draw_header(draw, fonts, "TÌNH HUỐNG THỰC TẾ", "VẤN ĐỀ CỦA BẠN CHOBI", "HIỂU NHẦM TƯỞNG ĐÒI TIỀN BẢO HIỂM", color_1=(250, 204, 21), color_2=(255, 255, 255))

    box = [70, 200, W - 70, 625]
    draw.rounded_rectangle(box, radius=24, fill=(24, 34, 53), outline=(234, 179, 8), width=2)

    # Khung suy nghĩ của Chobi
    thought_box = [110, 230, W - 110, 375]
    draw.rounded_rectangle(thought_box, radius=16, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
    draw.text((135, 250), "💭 CHOBI SUY NGHĨ:", font=fonts["vi_bold_md"], fill=(250, 204, 21))
    draw.text((135, 290), '"Thư gì chữ Hán dài ngoằng, chắc lại bắt đóng thêm tiền', font=fonts["vi_reg_md"], fill=(241, 245, 249))
    draw.text((135, 325), 'hoặc quảng cáo linh tinh... Thôi ném thùng rác cho đỡ chật!"', font=fonts["vi_reg_md"], fill=(241, 245, 249))

    # Dấu nhân to cảnh báo sai lầm
    alert_box = [110, 400, W - 110, 595]
    draw.rounded_rectangle(alert_box, radius=16, fill=(225, 29, 72, 30), outline=(225, 29, 72), width=2)
    draw.text((135, 425), "❌ SAI LẦM TAI HẠI NẾU VỨT ĐI:", font=fonts["vi_bold_md"], fill=(251, 113, 133))

    reasons = [
        "1. Đây là giấy chứng nhận số tiền bạn ĐÃ TỰ ĐÓNG trong năm.",
        "2. Không có giấy này -> Tháng 11 không kê khai giảm trừ được.",
        "3. Hậu quả: Bị trừ nhiều thuế hơn, mất quyền hoàn tiền hàng vạn yên!",
    ]
    y_r = 468
    for r in reasons:
        draw.text((140, y_r), r, font=fonts["vi_reg_md"], fill=(255, 241, 242))
        y_r += 38

    im.save(out_path, quality=95)

def generate_scene_3(out_path: Path):
    """Scene 3: Nhịp 1 — Giải mã 7 chữ Hán 保険料控除証明書."""
    fonts = get_fonts()
    im = create_base_canvas(accent_color=(52, 211, 153))
    draw = ImageDraw.Draw(im)
    draw_header(draw, fonts, "NHỊP 1 • NHẬN DIỆN TIÊU ĐỀ", "GIẢI MÃ BẢY CHỮ HÁN TRÊN THƯ", "XÁC NHẬN BẠN ĐÃ ĐÓNG TIỀN ĐẦY ĐỦ", color_1=(52, 211, 153), color_2=(255, 255, 255))

    box = [70, 200, W - 70, 625]
    draw.rounded_rectangle(box, radius=24, fill=(24, 34, 53), outline=(52, 211, 153), width=2)

    # Hộp chữ Hán nổi bật
    kanji_box = [110, 225, W - 110, 360]
    draw.rounded_rectangle(kanji_box, radius=18, fill=(15, 23, 42), outline=(52, 211, 153), width=2)
    draw.text((140, 240), "保険料控除証明書", font=fonts["jp_bold_large"], fill=(253, 224, 71))
    draw.text((145, 310), "Furigana: ほけんりょう こうじょ しょうめいしょ", font=fonts["jp_regular_mid"], fill=(148, 163, 184))

    # Tách nghĩa 3 cụm
    mean_box = [110, 380, W - 110, 520]
    draw.rounded_rectangle(mean_box, radius=16, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
    draw.text((135, 395), "📖 TÁCH NGHĨA DỄ HIỂU:", font=fonts["vi_bold_md"], fill=(56, 189, 248))

    breakdown = [
        ("• 保険料 (Hoken-ryō):", "Tiền bảo hiểm (nhân thọ, Nenkin tư nhân)"),
        ("• 控除 (Kōjo):", "Khấu trừ (giảm trừ thu nhập tính thuế)"),
        ("• 証明書 (Shōmeisho):", "Giấy chứng nhận chính thức"),
    ]
    y_b = 430
    for term, mean in breakdown:
        draw.text((140, y_b), term, font=fonts["vi_bold_md"], fill=(254, 240, 138))
        draw.text((360, y_b), mean, font=fonts["vi_reg_md"], fill=(241, 245, 249))
        y_b += 28

    # Badge kết luận xanh lá
    draw.rounded_rectangle([110, 540, W - 110, 605], radius=14, fill=(16, 185, 129, 40), outline=(16, 185, 129), width=2)
    draw.text((145, 555), "✅ BẢN CHẤT: Giấy chứng nhận ĐÃ ĐÓNG TIỀN — KHÔNG PHẢI GIẤY NỢ!", font=fonts["vi_bold_md"], fill=(110, 231, 183))

    im.save(out_path, quality=95)

def generate_scene_4(out_path: Path):
    """Scene 4: Nhịp 2 — Giải mã giá trị: Nộp cho 年末調整 để nhận hoàn thuế."""
    fonts = get_fonts()
    im = create_base_canvas(accent_color=(56, 189, 248))
    draw = ImageDraw.Draw(im)
    draw_header(draw, fonts, "NHỊP 2 • GIẢI MÃ GIÁ TRỊ", "MỤC ĐÍCH SỬ DỤNG LÀ GÌ?", "NỘP ĐỂ ĐƯỢC NHẬN TIỀN HOÀN THUẾ", color_1=(56, 189, 248), color_2=(255, 255, 255))

    box = [70, 200, W - 70, 625]
    draw.rounded_rectangle(box, radius=24, fill=(24, 34, 53), outline=(56, 189, 248), width=2)

    # Khái niệm Nenmatsu Chosei
    term_box = [110, 225, W - 110, 335]
    draw.rounded_rectangle(term_box, radius=16, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
    draw.text((140, 240), "年末調整", font=fonts["jp_bold_large"], fill=(56, 189, 248))
    draw.text((400, 248), "(Nen-mát-sư Chô-xây)", font=fonts["vi_bold_lg"], fill=(224, 242, 254))
    draw.text((140, 298), "Thủ tục Điều Chỉnh Thuế Cuối Năm tại công ty vào tháng 11", font=fonts["vi_semi_md"], fill=(203, 213, 225))

    # Quy trình 2 bước nhận tiền
    flow_box = [110, 355, W - 110, 520]
    draw.rounded_rectangle(flow_box, radius=16, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
    draw.text((135, 370), "💰 QUY TRÌNH HƯỞNG LỢI ÍCH:", font=fonts["vi_bold_md"], fill=(250, 204, 21))

    draw.text((140, 410), "• THÁNG 11:", font=fonts["vi_bold_md"], fill=(56, 189, 248))
    draw.text((275, 410), "Nộp giấy này kẹp cùng tờ khai thuế nộp cho phòng nhân sự.", font=fonts["vi_reg_md"], fill=(241, 245, 249))

    draw.text((140, 455), "• THÁNG 12:", font=fonts["vi_bold_md"], fill=(52, 211, 153))
    draw.text((275, 455), "Công ty tính lại thuế -> Nhận lại tiền hoàn thuế trong lương!", font=fonts["vi_reg_md"], fill=(241, 245, 249))

    # Lợi ích đôi
    draw.rounded_rectangle([110, 540, W - 110, 605], radius=14, fill=(59, 130, 246, 30), outline=(59, 130, 246), width=1)
    draw.text((135, 558), "✨ Giúp bạn giảm cả Thuế Thu Nhập (所得税) và Thuế Thị Dân (住民税)!", font=fonts["vi_bold_md"], fill=(191, 219, 254))

    im.save(out_path, quality=95)

def generate_scene_5(out_path: Path):
    """Scene 5: Nhịp 3 — Hành động an toàn & Nơi xác minh chính thức."""
    fonts = get_fonts()
    im = create_base_canvas(accent_color=(168, 85, 247))
    draw = ImageDraw.Draw(im)
    draw_header(draw, fonts, "NHỊP 3 • HÀNH ĐỘNG AN TOÀN", "CÁCH XỬ LÝ AN TOÀN KHI NHẬN THƯ", "BƯỚC LÀM ĐÚNG VÀ NƠI XÁC MINH CHUẨN", color_1=(192, 132, 252), color_2=(255, 255, 255))

    box = [70, 200, W - 70, 625]
    draw.rounded_rectangle(box, radius=24, fill=(24, 34, 53), outline=(168, 85, 247), width=2)

    # Bước 1
    step1_box = [110, 225, W - 110, 335]
    draw.rounded_rectangle(step1_box, radius=16, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
    draw.text((135, 240), "📁 BƯỚC 1: CẤT NGAY VÀO BÌA HỒ SƠ", font=fonts["vi_bold_md"], fill=(52, 211, 153))
    draw.text((135, 275), "Giữ nguyên bản gốc sạch sẽ. Khi công ty phát tờ khai 年末調整,", font=fonts["vi_reg_md"], fill=(241, 245, 249))
    draw.text((135, 302), "kẹp giấy này vào mặt sau để nộp cùng.", font=fonts["vi_reg_md"], fill=(241, 245, 249))

    # Bước 2
    step2_box = [110, 350, W - 110, 475]
    draw.rounded_rectangle(step2_box, radius=16, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
    draw.text((135, 365), "🔄 BƯỚC 2: NẾU LỠ LÀM MẤT? XIN CẤP LẠI (再発行)", font=fonts["vi_bold_md"], fill=(251, 146, 60))
    draw.text((135, 400), "Liên hệ ngay tổng đài hãng bảo hiểm yêu cầu Sai-hắc-kô (再発行).", font=fonts["vi_reg_md"], fill=(241, 245, 249))
    draw.text((135, 430), "Nên xin sớm vì thư gửi lại thường mất từ 3 đến 7 ngày.", font=fonts["vi_reg_md"], fill=(241, 245, 249))

    # Nơi xác minh chính thức
    auth_box = [110, 495, W - 110, 600]
    draw.rounded_rectangle(auth_box, radius=16, fill=(15, 23, 42), outline=(168, 85, 247), width=1)
    draw.text((135, 515), "🏛️ NƠI XÁC MINH CHÍNH THỨC:", font=fonts["vi_bold_md"], fill=(233, 213, 255))
    draw.text((135, 550), "• Cơ quan Thuế Quốc gia Nhật Bản (国税庁 - NTA): nta.go.jp", font=fonts["vi_reg_md"], fill=(224, 231, 255))
    draw.text((135, 575), "• Hoặc hỏi trực tiếp Phòng Nhân sự (Somu/Jinji) tại công ty bạn.", font=fonts["vi_reg_sm"], fill=(148, 163, 184))

    im.save(out_path, quality=95)

def generate_scene_6(out_path: Path):
    """Scene 6: Kết — Thương hiệu Chotto: Một chút hữu ích, mỗi ngày."""
    fonts = get_fonts()
    im = create_base_canvas(accent_color=(244, 63, 94))
    draw = ImageDraw.Draw(im)
    draw_header(draw, fonts, "MỖI NGÀY MỘT CHÚT HỮU ÍCH", "ĐỒNG HÀNH CÙNG NGƯỜI VIỆT TẠI NHẬT", "THEO DÕI ĐỂ CẬP NHẬT KIẾN THỨC MỖI NGÀY", color_1=(244, 63, 94), color_2=(255, 255, 255))

    box = [70, 200, W - 70, 625]
    draw.rounded_rectangle(box, radius=24, fill=(24, 34, 53), outline=(244, 63, 94), width=2)

    # Logo Chotto lớn
    logo_box = [110, 225, W - 110, 365]
    draw.rounded_rectangle(logo_box, radius=18, fill=(15, 23, 42), outline=(244, 63, 94), width=2)
    draw.text((150, 245), "ちょっと", font=fonts["jp_bold_brand"], fill=(244, 63, 94))
    draw.text((440, 260), "CHOTTO", font=fonts["vi_bold_xl"], fill=(255, 255, 255))
    draw.text((150, 325), "« Một chút hữu ích, mỗi ngày. »", font=fonts["vi_bold_lg"], fill=(254, 205, 211))

    # Tóm tắt sứ mệnh
    info_box = [110, 385, W - 110, 495]
    draw.rounded_rectangle(info_box, radius=16, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
    draw.text((135, 405), "🌟 NỘI DUNG CHUYÊN BIỆT CHO BẠN:", font=fonts["vi_bold_md"], fill=(250, 204, 21))
    draw.text((135, 440), "• Giao thông nhà ga • Thủ tục cư trú & visa • Thuế & Nenkin", font=fonts["vi_reg_md"], fill=(241, 245, 249))
    draw.text((135, 465), "• Y tế, thuốc men • Phân loại rác • Phòng chống thiên tai", font=fonts["vi_reg_md"], fill=(241, 245, 249))

    # Nút kêu gọi hành động
    cta_box = [110, 520, W - 110, 605]
    draw.rounded_rectangle(cta_box, radius=16, fill=(244, 63, 94), outline=(251, 113, 133), width=2)
    draw.text((150, 545), "👉 BẤM THEO DÕI FANPAGE ちょっと ĐỂ NHẬN HỮU ÍCH MỖI NGÀY!", font=fonts["vi_bold_md"], fill=(255, 255, 255))

    im.save(out_path, quality=95)

def generate_all_cards(target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    cards = [
        target_dir / "scene_1_hook.png",
        target_dir / "scene_2_chobi.png",
        target_dir / "scene_3_nhip1.png",
        target_dir / "scene_4_nhip2.png",
        target_dir / "scene_5_nhip3.png",
        target_dir / "scene_6_outro.png",
    ]
    generate_scene_1(cards[0])
    generate_scene_2(cards[1])
    generate_scene_3(cards[2])
    generate_scene_4(cards[3])
    generate_scene_5(cards[4])
    generate_scene_6(cards[5])
    return cards

if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/chotto_cards")
    generated = generate_all_cards(out)
    print(f"Đã tạo thành công {len(generated)} thẻ đồ họa 1080x1080 tại {out}")
