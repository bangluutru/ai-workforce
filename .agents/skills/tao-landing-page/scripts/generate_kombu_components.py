#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_kombu_components.py
Sinh 11 components React chuẩn 100% Stitch cho Rishiri Kombu Landing Page.
"""

from pathlib import Path

TARGET_DIR = Path("/Users/tranhaibang/Downloads/landing-pages/rishiri-kombu")
COMPONENTS_DIR = TARGET_DIR / "src" / "components"
SRC_DIR = TARGET_DIR / "src"

# 1. Header.tsx
header_code = """import React from 'react';
import { LPHub } from '../lib/lphub';

export const Header: React.FC = () => {
  return (
    <header className="fixed top-0 w-full z-50 shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      {/* Top Announcement Bar */}
      <div className="bg-primary text-on-primary py-space-2xs px-space-md text-center text-label-caps font-label-caps tracking-wider flex items-center justify-center gap-space-xs">
        <span className="text-secondary-fixed text-label-badge font-label-badge">🏆</span>
        <span>GIẢI PHÁP CHĂM SÓC TÓC BẠC SỐ 1 NHẬT BẢN 14 NĂM LIÊN TIẾP | NHẬP KHẨU CHÍNH NGẠCH BỞI GENKI FAMI VIỆT NAM</span>
      </div>

      {/* Main Nav */}
      <div className="h-20 bg-surface/90 backdrop-blur-xl">
        <div className="max-w-container-max mx-auto h-full px-space-md lg:px-space-xl flex items-center justify-between gap-space-md">
          {/* Brand Logo */}
          <a href="#" className="flex items-center gap-space-sm shrink-0">
            <img
              alt="Rishiri Kombu Logo"
              className="h-8 w-auto object-contain"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBhlYbyEoq5wHYYOig3Uh29mNu8_7I1Bd8F1Ix4JO8KJu4z15fwnmDo1cHI2G6l8dsClJupsgWyVx-PTjMqRFKqDvx0Mvot--uFgtlGTVUU7f0gDiaWPjhDEdUXscuRC1QjTv1z5t9S7NoYsJ7yEWaloA3qukmH_U0Fe1RV7oU4Yz8DcKQNQ8swBm4iGGRAMD3FyIeMBzvB16qA95p59H9u_6lrADJ8l0x1_dl7vt_PARusQJLysPYAwQ"
            />
            <div className="flex flex-col">
              <span className="font-headline-sm text-headline-sm text-primary tracking-tight font-bold leading-tight">利尻昆布</span>
              <span className="font-label-caps text-label-caps text-on-surface-variant uppercase">Pyuru Japan</span>
            </div>
          </a>

          {/* Nav Links */}
          <nav className="hidden xl:flex items-center gap-space-xs">
            <a className="px-space-xs py-space-2xs text-on-surface-variant font-label-badge text-label-badge hover:text-on-surface transition-colors" href="#van-de">Vấn Đề</a>
            <a className="px-space-xs py-space-2xs text-on-surface-variant font-label-badge text-label-badge hover:text-on-surface transition-colors" href="#giai-phap-kombu">Giải Pháp Kombu</a>
            <a className="px-space-xs py-space-2xs text-on-surface-variant font-label-badge text-label-badge hover:text-on-surface transition-colors" href="#co-che-khoa-hoc">Cơ Chế Khoa Học</a>
            <a className="px-space-xs py-space-2xs text-on-surface-variant font-label-badge text-label-badge hover:text-on-surface transition-colors" href="#quy-trinh-4-buoc">Quy Trình 4 Bước</a>
            <a className="px-space-xs py-space-2xs text-on-surface-variant font-label-badge text-label-badge hover:text-on-surface transition-colors" href="#bang-mau">Bảng Màu</a>
            <a className="px-space-xs py-space-2xs text-on-surface-variant font-label-badge text-label-badge hover:text-on-surface transition-colors" href="#chung-nhan-uy-tin">Chứng Nhận &amp; Uy Tín</a>
            <a className="px-space-xs py-space-2xs text-on-surface-variant font-label-badge text-label-badge hover:text-on-surface transition-colors" href="#faq">FAQ</a>
          </nav>

          {/* Right Action */}
          <div className="flex items-center gap-space-sm shrink-0">
            <a
              className="hidden sm:inline-flex items-center justify-center px-space-md py-space-xs bg-primary-container text-on-primary font-label-badge text-label-badge rounded-lg border border-secondary/40 shadow-[0_4px_16px_rgba(26,56,43,0.15)] hover:bg-primary transition-all duration-300"
              href="#dat-mua"
              onClick={() => LPHub.track('cta_click', { buttonId: 'btn_header_order', section: 'header' })}
            >
              Đặt Mua Chính Hãng
            </a>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
              <span className="material-symbols-outlined text-[18px]">person</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
"""
(COMPONENTS_DIR / "Header.tsx").write_text(header_code, encoding="utf-8")

# 2. HeroSection.tsx
hero_code = """import React from 'react';
import { LPHub } from '../lib/lphub';

export const HeroSection: React.FC = () => {
  return (
    <section className="relative overflow-hidden bg-surface pt-space-xl pb-space-3xl lg:py-space-4xl">
      <div className="absolute inset-0 pointer-events-none opacity-40 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary-fixed/30 via-surface-container/20 to-transparent" />
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl relative">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-2xl items-center">
          {/* Left Text Column */}
          <div className="lg:col-span-7 flex flex-col items-start text-left space-y-space-md">
            <div className="inline-flex items-center gap-space-xs px-space-sm py-space-2xs bg-primary-container text-on-primary rounded-full shadow-sm">
              <span className="text-secondary-fixed text-label-badge font-label-badge">🏆</span>
              <span className="font-label-caps text-label-caps uppercase tracking-wider">
                GIẢI PHÁP CHĂM SÓC TÓC BẠC SỐ 1 NHẬT BẢN 14 NĂM LIÊN TIẾP
              </span>
            </div>

            <h1 className="font-display-hero text-headline-lg lg:text-display-hero text-primary tracking-tight font-display-hero leading-tight">
              Chăm Sóc Tóc Bạc Dịu Dàng Trong Từng Lần Gội, Tạm Biệt Hóa Chất Nhuộm Độc Hại
            </h1>

            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl leading-relaxed">
              Dầu gội phủ màu tóc bạc Rishiri Color Shampoo ứng dụng chiết xuất tảo bẹ Rishiri từ vùng biển lạnh Hokkaido. Màu được bồi đắp tự nhiên trên bề mặt sợi tóc qua mỗi lần gội, không dùng phản ứng oxy hóa, an toàn tuyệt đối cho da đầu nhạy cảm.
            </p>

            {/* Social Proof Snippet Pill */}
            <div className="flex flex-wrap items-center gap-space-sm p-space-sm bg-surface-container-high/70 rounded-xl">
              <span className="material-symbols-outlined text-secondary font-bold text-[22px]">verified</span>
              <p className="font-body-sm text-body-sm text-on-surface font-medium">
                <strong className="text-primary font-bold">Hơn 37 triệu sản phẩm</strong> bán ra tại Nhật Bản. Công thức mới 2026 tăng <span className="text-secondary font-bold">149%</span> khả năng giữ màu.
              </p>
            </div>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-space-sm pt-space-xs w-full sm:w-auto">
              <a
                className="w-full sm:w-auto inline-flex items-center justify-center gap-space-xs px-space-xl py-space-md bg-primary-container text-on-primary font-headline-sm text-headline-sm rounded-lg shadow-xl hover:bg-primary transition-all duration-300"
                href="#dat-mua"
                onClick={() => LPHub.track('cta_click', { buttonId: 'btn_hero_primary', section: 'hero' })}
              >
                <span className="material-symbols-outlined text-[20px]">shopping_bag</span>
                <span>Khám Phá Điểm Bán Chính Hãng</span>
              </a>
              <a
                className="w-full sm:w-auto inline-flex items-center justify-center gap-space-xs px-space-lg py-space-md bg-surface-container text-on-surface font-headline-sm text-headline-sm rounded-lg hover:bg-surface-container-high transition-all duration-300"
                href="#co-che-khoa-hoc"
                onClick={() => LPHub.track('cta_click', { buttonId: 'btn_hero_secondary', section: 'hero' })}
              >
                <span>Tìm Hiểu Cơ Chế Kombu Care</span>
                <span className="material-symbols-outlined text-[18px]">arrow_downward</span>
              </a>
            </div>

            {/* Trust Badges */}
            <div className="grid grid-cols-3 gap-space-sm pt-space-sm w-full max-w-lg">
              <div className="flex items-center gap-space-2xs">
                <span className="material-symbols-outlined text-primary text-[20px]">eco</span>
                <span className="font-label-badge text-label-badge text-on-surface-variant">0% Diamine / PPD</span>
              </div>
              <div className="flex items-center gap-space-2xs">
                <span className="material-symbols-outlined text-primary text-[20px]">spa</span>
                <span className="font-label-badge text-label-badge text-on-surface-variant">0% Amoniac độc hại</span>
              </div>
              <div className="flex items-center gap-space-2xs">
                <span className="material-symbols-outlined text-primary text-[20px]">public</span>
                <span className="font-label-badge text-label-badge text-on-surface-variant">100% Nhập khẩu Nhật</span>
              </div>
            </div>
          </div>

          {/* Right Hero Media Column */}
          <div className="lg:col-span-5 relative flex justify-center items-center">
            <div className="relative w-full max-w-md aspect-square rounded-full bg-gradient-to-tr from-surface-container-high via-surface-container-low to-primary-fixed/20 p-space-sm flex items-center justify-center shadow-2xl">
              <img
                alt="Rishiri Color Shampoo Chai Dầu Gội Phủ Bạc Tảo Bẹ Hokkaido"
                className="w-full h-full object-contain rounded-full transition-transform duration-500 hover:scale-105"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCKFVpYRHLaJ4Ps5wPS7RiRWbJ2_D7R_nw058R5hPVLG_by-Bj7hLEG8YQVTQY7ISci026nxrRqh9dqKt6ycb4VwqhyHbDKrKoKssTS67e8h6gYHSLgAl5V2pVlKn2WpHj77Uf0B-2sHovOB1bfX7qWYdszB47caaXlE2Bn6y2kVG2ZZIfmi2Pp0krXFQuqddIjtzQ4ZgoKag8dKBXj_HMybjWeELNqlKi0hECQ1XdcsTdKdbMM50jF_w"
              />
              <div className="absolute -bottom-4 -left-4 bg-surface-container-lowest p-space-sm rounded-2xl shadow-xl flex items-center gap-space-sm max-w-[200px]">
                <div className="w-10 h-10 rounded-full bg-secondary/15 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-secondary text-[24px]">workspace_premium</span>
                </div>
                <div className="flex flex-col">
                  <span className="font-headline-sm text-[13px] text-primary font-bold leading-tight">PYURU JAPAN</span>
                  <span className="font-label-caps text-[10px] text-on-surface-variant">Chiết xuất Kombu Tự Nhiên</span>
                </div>
              </div>
              <div className="absolute -top-3 -right-3 bg-primary-container text-on-primary px-space-md py-space-xs rounded-full shadow-lg flex items-center gap-space-2xs">
                <span className="material-symbols-outlined text-secondary-fixed text-[18px]">verified</span>
                <span className="font-label-badge text-label-badge">Formula 2026 Boost</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "HeroSection.tsx").write_text(hero_code, encoding="utf-8")

# 3. ProblemSection.tsx
problem_code = """import React from 'react';

export const ProblemSection: React.FC = () => {
  return (
    <section className="py-space-3xl lg:py-space-4xl bg-surface-container-low" id="van-de">
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl">
        <div className="max-w-3xl mx-auto text-center space-y-space-xs mb-space-2xl">
          <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
            Thực Trạng Đáng Lo Ngại
          </span>
          <h2 className="font-headline-lg text-headline-lg-mobile lg:text-headline-lg text-primary font-headline-lg">
            Nỗi Ám Ảnh Khi Nhuộm Tóc Bạc Truyền Thống
          </h2>
          <p className="font-body-md text-body-md text-on-surface-variant">
            Nhuộm tóc bạc định kỳ tại tiệm hoặc tự nhuộm tại nhà bằng thuốc nhuộm hóa chất đang khiến hàng triệu người gặp phải 3 rắc rối nan giải:
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-space-lg">
          {/* Card 1 */}
          <div className="bg-surface-container-lowest p-space-xl rounded-2xl shadow-sm flex flex-col justify-between transition-all duration-300 hover:shadow-md">
            <div className="space-y-space-md">
              <div className="w-12 h-12 rounded-xl bg-error-container text-on-error-container flex items-center justify-center">
                <span className="font-headline-md text-[24px]">❌</span>
              </div>
              <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                Châm chích, ngứa rát và rủi ro dị ứng
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Thuốc nhuộm vĩnh viễn chứa hợp chất Diamine (PPD) và amoniac nồng nặc mùi hăng hắc. Da đầu bạn liên tục bị bỏng rát, đỏ ửng và đối mặt với nguy cơ viêm da tiếp xúc sau mỗi lần chấm chân tóc.
              </p>
            </div>
            <div className="mt-space-lg pt-space-sm border-t-0 bg-surface-container-high/40 p-space-xs rounded-lg">
              <span className="font-label-badge text-label-badge text-error font-semibold flex items-center gap-space-2xs">
                <span className="material-symbols-outlined text-[16px]">warning</span> Nguy cơ tổn hại da đầu lâu dài
              </span>
            </div>
          </div>
          {/* Card 2 */}
          <div className="bg-surface-container-lowest p-space-xl rounded-2xl shadow-sm flex flex-col justify-between transition-all duration-300 hover:shadow-md">
            <div className="space-y-space-md">
              <div className="w-12 h-12 rounded-xl bg-error-container text-on-error-container flex items-center justify-center">
                <span className="font-headline-md text-[24px]">❌</span>
              </div>
              <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                Tóc ngày càng khô xơ, chẻ ngọn và gãy rụng
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Phản ứng oxy hóa mở toang lớp biểu bì để tẩy sắc tố melanin tự nhiên. Quá trình này hút cạn độ ẩm, khiến sợi tóc mất đi lớp dầu bảo vệ, trở nên xơ xác như rơm sau vài lần nhuộm.
              </p>
            </div>
            <div className="mt-space-lg pt-space-sm border-t-0 bg-surface-container-high/40 p-space-xs rounded-lg">
              <span className="font-label-badge text-label-badge text-error font-semibold flex items-center gap-space-2xs">
                <span className="material-symbols-outlined text-[16px]">warning</span> Hỏng hoàn toàn lớp biểu bì tóc
              </span>
            </div>
          </div>
          {/* Card 3 */}
          <div className="bg-surface-container-lowest p-space-xl rounded-2xl shadow-sm flex flex-col justify-between transition-all duration-300 hover:shadow-md">
            <div className="space-y-space-md">
              <div className="w-12 h-12 rounded-xl bg-error-container text-on-error-container flex items-center justify-center">
                <span className="font-headline-md text-[24px]">❌</span>
              </div>
              <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                Ranh giới chân tóc trắng mọc lại chỉ sau 2 đến 3 tuần
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Tóc mới nhú ra tạo thành hai mảng màu đối lập rõ rệt. Bạn buộc phải tiếp tục nhuộm dặm liên tục, vừa tốn kém tiền bạc, vừa mất cả buổi ngồi chờ ngoài tiệm.
              </p>
            </div>
            <div className="mt-space-lg pt-space-sm border-t-0 bg-surface-container-high/40 p-space-xs rounded-lg">
              <span className="font-label-badge text-label-badge text-error font-semibold flex items-center gap-space-2xs">
                <span className="material-symbols-outlined text-[16px]">warning</span> Vòng lặp tốn kém và mệt mỏi
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "ProblemSection.tsx").write_text(problem_code, encoding="utf-8")

# 4. SolutionSection.tsx
solution_code = """import React from 'react';

export const SolutionSection: React.FC = () => {
  return (
    <section className="py-space-3xl lg:py-space-4xl bg-surface" id="giai-phap-kombu">
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl">
        <div className="max-w-3xl mx-auto text-center space-y-space-xs mb-space-2xl">
          <span className="font-label-caps text-label-caps text-surface-tint font-bold tracking-widest uppercase">
            Liệu Pháp Phủ Bạc Hữu Cơ
          </span>
          <h2 className="font-headline-lg text-headline-lg-mobile lg:text-headline-lg text-primary font-headline-lg">
            Dầu Gội Phủ Bạc Rishiri Kombu: Đổi Mới Thói Quen Mỗi Sáng
          </h2>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Rishiri Color Shampoo mở ra cách tiếp cận hoàn toàn khác biệt. Không cần thêm bất kỳ công đoạn phức tạp nào, bước phủ màu tóc bạc được tích hợp ngay vào chính thói quen gội đầu hằng ngày của bạn.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-space-lg">
          {/* Benefit Card 1 */}
          <div className="bg-surface-container p-space-xl rounded-2xl flex items-start gap-space-md transition-all duration-300 hover:bg-surface-container-high">
            <div className="w-10 h-10 rounded-full bg-primary-fixed text-on-primary-fixed flex items-center justify-center shrink-0 mt-1">
              <span className="material-symbols-outlined text-[20px] font-bold">check</span>
            </div>
            <div className="space-y-space-xs">
              <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                Phủ màu bề mặt sợi tóc, không xâm lấn lõi tóc
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Các hạt màu ion hữu cơ tự nhiên liên kết nhẹ nhàng bên ngoài biểu bì sợi tóc. Màu tóc sẫm dần tự nhiên theo từng lần gội, không phá vỡ cấu trúc tóc và không để lại ranh giới chân tóc trắng lộ liễu.
              </p>
            </div>
          </div>
          {/* Benefit Card 2 */}
          <div className="bg-surface-container p-space-xl rounded-2xl flex items-start gap-space-md transition-all duration-300 hover:bg-surface-container-high">
            <div className="w-10 h-10 rounded-full bg-primary-fixed text-on-primary-fixed flex items-center justify-center shrink-0 mt-1">
              <span className="material-symbols-outlined text-[20px] font-bold">check</span>
            </div>
            <div className="space-y-space-xs">
              <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                Dưỡng ẩm sâu từ tảo bẹ Rishiri đảo Hokkaido
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Chiết xuất tảo bẹ Rishiri giàu khoáng chất, axit alginic và fucoidan đậm đặc. Đây là nguồn dưỡng ẩm tự nhiên giúp nuôi dưỡng da đầu khỏe mạnh, làm mượt tóc từ gốc đến ngọn.
              </p>
            </div>
          </div>
          {/* Benefit Card 3 */}
          <div className="bg-surface-container p-space-xl rounded-2xl flex items-start gap-space-md transition-all duration-300 hover:bg-surface-container-high">
            <div className="w-10 h-10 rounded-full bg-primary-fixed text-on-primary-fixed flex items-center justify-center shrink-0 mt-1">
              <span className="material-symbols-outlined text-[20px] font-bold">check</span>
            </div>
            <div className="space-y-space-xs">
              <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                Công thức sạch đạt chuẩn Effective Clean Beauty
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                100% không chứa chất oxy hóa (oxy già), không amoniac, không diamine (PPD), không silicone, không paraben và không dầu khoáng.
              </p>
            </div>
          </div>
          {/* Benefit Card 4 */}
          <div className="bg-surface-container p-space-xl rounded-2xl flex items-start gap-space-md transition-all duration-300 hover:bg-surface-container-high">
            <div className="w-10 h-10 rounded-full bg-primary-fixed text-on-primary-fixed flex items-center justify-center shrink-0 mt-1">
              <span className="material-symbols-outlined text-[20px] font-bold">check</span>
            </div>
            <div className="space-y-space-xs">
              <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                Chất làm sạch dịu nhẹ gốc amino acid
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Tạo lớp bọt mịn màng, làm sạch bã nhờn nhẹ nhàng mà không bào mòn hàng rào bảo vệ tự nhiên của da đầu.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "SolutionSection.tsx").write_text(solution_code, encoding="utf-8")

# 5. ScienceSection.tsx
science_code = """import React from 'react';

export const ScienceSection: React.FC = () => {
  return (
    <section className="py-space-3xl lg:py-space-4xl bg-surface-container-low" id="co-che-khoa-hoc">
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl">
        <div className="max-w-3xl mx-auto text-center space-y-space-xs mb-space-2xl">
          <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
            Nền Tảng Sinh Học Biển
          </span>
          <h2 className="font-headline-lg text-headline-lg-mobile lg:text-headline-lg text-primary font-headline-lg">
            Cơ Chế Hoạt Động Của Hệ Dưỡng Chất Kombu Care
          </h2>
        </div>

        {/* Scientific Insight Banner */}
        <div className="bg-surface-container-lowest p-space-xl rounded-2xl shadow-sm mb-space-2xl border-l-4 border-primary">
          <div className="flex items-start gap-space-md">
            <span className="material-symbols-outlined text-secondary text-[32px] shrink-0">lightbulb</span>
            <p className="font-body-lg text-body-lg text-on-surface italic leading-relaxed">
              “Hiểu đúng về sản phẩm là chìa khóa để chăm sóc mái tóc hiệu quả: Tảo bẹ Kombu là chất cấp ẩm, không phải chất tạo màu. Nguồn tảo bẹ thu hoạch từ vùng biển lạnh đảo Rishiri phía bắc Hokkaido cung cấp độ ẩm dồi dào. Tảo bẹ hỗ trợ khép mịn các vảy biểu bì tóc, giúp tóc giữ nước và phản chiếu ánh sáng óng ả.”
            </p>
          </div>
        </div>

        {/* 3 Tier Kombu Extract Breakdown & Ion Mechanism */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl">
          {/* 3-Tier Kombu Extract Column */}
          <div className="lg:col-span-6 space-y-space-md">
            <h3 className="font-headline-md text-headline-md text-primary font-semibold flex items-center gap-space-xs">
              <span className="material-symbols-outlined text-surface-tint text-[24px]">layers</span>
              Hệ 3 Tầng Chiết Xuất Kombu Độc Quyền
            </h3>
            <div className="space-y-space-sm">
              <div className="bg-surface-container-lowest p-space-md rounded-xl shadow-xs">
                <span className="font-label-caps text-label-caps text-secondary uppercase font-bold">Tầng 1 - Nền tảng tự nhiên</span>
                <h4 className="font-headline-sm text-headline-sm text-primary font-bold mt-1">Chiết xuất tự nhiên nền tảng</h4>
                <p className="font-body-md text-body-md text-on-surface-variant mt-1">
                  Cung cấp khoáng chất biển nuôi dưỡng chân tóc, tạo tiền đề cho sợi tóc chắc khỏe từ gốc.
                </p>
              </div>
              <div className="bg-surface-container-lowest p-space-md rounded-xl shadow-xs">
                <span className="font-label-caps text-label-caps text-secondary uppercase font-bold">Tầng 2 - Dưỡng ẩm cô đặc</span>
                <h4 className="font-headline-sm text-headline-sm text-primary font-bold mt-1">Chiết xuất Kombu cô đặc</h4>
                <p className="font-body-md text-body-md text-on-surface-variant mt-1">
                  Củng cố hàng rào giữ ẩm của da đầu, ngăn chặn tình trạng thất thoát nước do tác nhân môi trường.
                </p>
              </div>
              <div className="bg-surface-container-lowest p-space-md rounded-xl shadow-xs">
                <span className="font-label-caps text-label-caps text-secondary uppercase font-bold">Tầng 3 - Lên men sinh học</span>
                <h4 className="font-headline-sm text-headline-sm text-primary font-bold mt-1">Dịch lên men Rishiri Kombu</h4>
                <p className="font-body-md text-body-md text-on-surface-variant mt-1">
                  Tăng cường độ đàn hồi, giúp sợi tóc mềm mại và dễ vào nếp mà không cần đến hóa chất silicone.
                </p>
              </div>
            </div>
          </div>

          {/* Mechanism Infographic Card */}
          <div className="lg:col-span-6 bg-surface-container p-space-xl rounded-2xl flex flex-col justify-between">
            <div className="space-y-space-md">
              <div className="inline-flex items-center gap-space-2xs px-space-sm py-space-2xs bg-primary-fixed text-on-primary-fixed rounded-full">
                <span className="material-symbols-outlined text-[16px]">science</span>
                <span className="font-label-badge text-label-badge">Non-Oxidative Surface Coloring</span>
              </div>
              <h3 className="font-headline-md text-headline-md text-primary font-semibold">
                Cơ chế bám màu ion tự nhiên
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Các hạt màu mang điện tích liên kết với điện tích bề mặt của sợi tóc. Màu được bồi đắp từng lớp mỏng qua mỗi lần gội, tạo sắc màu chuyển đổi mượt mà và bóng khỏe.
              </p>

              {/* Visual SVG Diagram showing Ion Bonding */}
              <div className="bg-surface-container-lowest p-space-md rounded-xl">
                <svg className="w-full h-auto text-primary" fill="none" stroke="currentColor" viewBox="0 0 400 160">
                  <rect fill="#ece8df" height="90" rx="12" stroke="#727974" strokeWidth="1.5" width="360" x="20" y="35" />
                  <text className="text-[12px] font-medium" fill="#424844" stroke="none" x="35" y="60">
                    Biểu bì sợi tóc (Cuticle Layer - Điện tích Âm [-])
                  </text>
                  <path d="M40 75 Q60 65 80 75" fill="none" stroke="#727974" strokeWidth="2" />
                  <path d="M100 75 Q120 65 140 75" fill="none" stroke="#727974" strokeWidth="2" />
                  <path d="M160 75 Q180 65 200 75" fill="none" stroke="#727974" strokeWidth="2" />
                  <path d="M220 75 Q240 65 260 75" fill="none" stroke="#727974" strokeWidth="2" />
                  <path d="M280 75 Q300 65 320 75" fill="none" stroke="#727974" strokeWidth="2" />
                  <g fill="#904d00" stroke="#ffdcc3" strokeWidth="1">
                    <circle cx="60" cy="100" r="10" />
                    <circle cx="120" cy="100" r="10" />
                    <circle cx="180" cy="100" r="10" />
                    <circle cx="240" cy="100" r="10" />
                    <circle cx="300" cy="100" r="10" />
                    <circle cx="350" cy="100" r="10" />
                  </g>
                  <g className="text-[11px] font-bold text-center" fill="#ffffff" stroke="none">
                    <text x="57" y="104">+</text>
                    <text x="117" y="104">+</text>
                    <text x="177" y="104">+</text>
                    <text x="237" y="104">+</text>
                    <text x="297" y="104">+</text>
                    <text x="347" y="104">+</text>
                  </g>
                  <text className="text-[11px] font-semibold" fill="#904d00" stroke="none" x="60" y="128">
                    Lớp màu khoáng thực vật bám kết chặt chẽ
                  </text>
                </svg>
              </div>
            </div>
            <div className="mt-space-md flex items-center gap-space-sm bg-primary-fixed/30 p-space-sm rounded-xl">
              <span className="material-symbols-outlined text-primary text-[20px]">shield_with_heart</span>
              <span className="font-body-sm text-body-sm text-primary font-medium">
                Bảo vệ cấu trúc lõi tóc vĩnh viễn - Không lo gãy rụng
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "ScienceSection.tsx").write_text(science_code, encoding="utf-8")

# 6. RoutineSection.tsx
routine_code = """import React from 'react';

export const RoutineSection: React.FC = () => {
  return (
    <section className="py-space-3xl lg:py-space-4xl bg-surface" id="quy-trinh-4-buoc">
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl">
        <div className="max-w-3xl mx-auto text-center space-y-space-xs mb-space-2xl">
          <span className="font-label-caps text-label-caps text-surface-tint font-bold tracking-widest uppercase">
            Liệu Trình Tại Gia
          </span>
          <h2 className="font-headline-lg text-headline-lg-mobile lg:text-headline-lg text-primary font-headline-lg">
            Quy Trình 4 Bước Gội Đầu Đơn Giản Tại Nhà
          </h2>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Bạn không cần pha trộn hóa chất, không cần đeo mặt nạ chống mùi hôi
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-space-md relative">
          {/* Step 1 */}
          <div className="bg-surface-container p-space-lg rounded-2xl relative flex flex-col justify-between transition-all duration-300 hover:bg-surface-container-high">
            <div className="space-y-space-sm">
              <div className="w-12 h-12 rounded-full bg-primary-container text-on-primary flex items-center justify-center font-headline-md text-headline-md font-bold">
                01
              </div>
              <div className="flex items-center gap-space-xs text-primary">
                <span className="material-symbols-outlined text-[24px]">water_drop</span>
                <h3 className="font-headline-sm text-headline-sm font-bold">Làm ướt tóc</h3>
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Xả sạch bụi bẩn trên tóc và da đầu bằng nước ấm như khi gội đầu bình thường.
              </p>
            </div>
            <div className="mt-space-md pt-space-xs">
              <span className="font-label-caps text-label-caps text-outline uppercase font-semibold">Thời gian: 1 phút</span>
            </div>
          </div>
          {/* Step 2 */}
          <div className="bg-surface-container p-space-lg rounded-2xl relative flex flex-col justify-between transition-all duration-300 hover:bg-surface-container-high">
            <div className="space-y-space-sm">
              <div className="w-12 h-12 rounded-full bg-primary-container text-on-primary flex items-center justify-center font-headline-md text-headline-md font-bold">
                02
              </div>
              <div className="flex items-center gap-space-xs text-primary">
                <span className="material-symbols-outlined text-[24px]">bubble_chart</span>
                <h3 className="font-headline-sm text-headline-sm font-bold">Tạo bọt &amp; xoa đều</h3>
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Lấy một lượng dầu gội vừa đủ ra lòng bàn tay ẩm, tạo bọt mịn rồi thoa đều từ chân tóc đến ngọn tóc.
              </p>
            </div>
            <div className="mt-space-md pt-space-xs">
              <span className="font-label-caps text-label-caps text-outline uppercase font-semibold">Tạo bọt mịn màng</span>
            </div>
          </div>
          {/* Step 3 */}
          <div className="bg-surface-container p-space-lg rounded-2xl relative flex flex-col justify-between transition-all duration-300 hover:bg-surface-container-high">
            <div className="space-y-space-sm">
              <div className="w-12 h-12 rounded-full bg-secondary text-on-secondary flex items-center justify-center font-headline-md text-headline-md font-bold">
                03
              </div>
              <div className="flex items-center gap-space-xs text-secondary">
                <span className="material-symbols-outlined text-[24px]">timer</span>
                <h3 className="font-headline-sm text-headline-sm font-bold">Thư giãn vài phút</h3>
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Giữ lớp bọt trên tóc trong 3 đến 5 phút để các hạt màu có thời gian bám đều lên bề mặt sợi tóc.
              </p>
            </div>
            <div className="mt-space-md pt-space-xs">
              <span className="font-label-caps text-label-caps text-secondary font-bold uppercase">Ủ màu: 3 - 5 phút</span>
            </div>
          </div>
          {/* Step 4 */}
          <div className="bg-surface-container p-space-lg rounded-2xl relative flex flex-col justify-between transition-all duration-300 hover:bg-surface-container-high">
            <div className="space-y-space-sm">
              <div className="w-12 h-12 rounded-full bg-primary-container text-on-primary flex items-center justify-center font-headline-md text-headline-md font-bold">
                04
              </div>
              <div className="flex items-center gap-space-xs text-primary">
                <span className="material-symbols-outlined text-[24px]">shower</span>
                <h3 className="font-headline-sm text-headline-sm font-bold">Xả sạch với nước</h3>
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Xả kỹ lại bằng nước ấm cho đến khi nước chảy ra hoàn toàn trong veo. Sấy khô tóc nhẹ nhàng để cảm nhận mái tóc mềm mượt.
              </p>
            </div>
            <div className="mt-space-md pt-space-xs">
              <span className="font-label-caps text-label-caps text-outline uppercase font-semibold">Tóc bóng mượt ngay</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "RoutineSection.tsx").write_text(routine_code, encoding="utf-8")

# 7. ColorSelectionSection.tsx
color_code = """import React from 'react';
import { LPHub } from '../lib/lphub';

interface ColorSelectionProps {
  onSelectColor: (colorName: string) => void;
}

export const ColorSelectionSection: React.FC<ColorSelectionProps> = ({ onSelectColor }) => {
  return (
    <section className="py-space-3xl lg:py-space-4xl bg-surface-container-low" id="bang-mau">
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl">
        <div className="max-w-3xl mx-auto text-center space-y-space-xs mb-space-2xl">
          <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
            Bảng Màu Tinh Tế
          </span>
          <h2 className="font-headline-lg text-headline-lg-mobile lg:text-headline-lg text-primary font-headline-lg">
            3 Lựa Chọn Tông Màu Phù Hợp Người Việt
          </h2>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            Rishiri Color Shampoo được nghiên cứu với 3 tông màu trang nhã, tương thích hoàn hảo với làn da và màu tóc tự nhiên của người châu Á
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-space-lg">
          {/* Color Card 1: Black */}
          <div
            onClick={() => {
              LPHub.track('cta_click', { buttonId: 'select_color_black', color: 'Black' });
              onSelectColor('Black (Đen tự nhiên)');
            }}
            className="bg-surface-container-lowest p-space-xl rounded-2xl shadow-sm flex flex-col justify-between transition-all duration-300 hover:shadow-md cursor-pointer border border-transparent hover:border-primary/30"
          >
            <div className="space-y-space-md">
              <div className="flex items-center justify-between">
                <span className="font-label-badge text-label-badge px-space-xs py-space-2xs bg-surface-container-high rounded text-on-surface">
                  Tự Nhiên &amp; Truyền Thống
                </span>
                <div className="w-8 h-8 rounded-full bg-[#1c1c1c] shadow-inner" />
              </div>
              <h3 className="font-headline-md text-headline-md text-primary font-bold">
                Black (Đen tự nhiên)
              </h3>
              <div className="h-16 w-full rounded-xl bg-gradient-to-r from-[#111111] via-[#222222] to-[#333333] flex items-center justify-center text-on-primary font-label-badge text-label-badge shadow-sm">
                Sắc đen thuần Á Đông
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Phù hợp cho những ai muốn mái tóc đen tuyền truyền thống, che phủ hoàn hảo các sợi bạc rải rác hoặc tóc bạc diện rộng.
              </p>
            </div>
            <div className="mt-space-lg pt-space-md bg-surface-container-low/50 p-space-sm rounded-xl">
              <span className="font-label-caps text-label-caps text-outline uppercase font-semibold">Tỷ lệ che bạc khuyên dùng:</span>
              <p className="font-body-sm text-body-sm text-primary font-bold mt-1">Từ 30% đến trên 80% sợi bạc</p>
            </div>
          </div>

          {/* Color Card 2: Dark Brown */}
          <div
            onClick={() => {
              LPHub.track('cta_click', { buttonId: 'select_color_dark_brown', color: 'Dark Brown' });
              onSelectColor('Dark Brown (Nâu đậm thanh lịch)');
            }}
            className="bg-surface-container-lowest p-space-xl rounded-2xl shadow-md flex flex-col justify-between relative transition-all duration-300 hover:shadow-lg cursor-pointer border-2 border-secondary/40"
          >
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-secondary text-on-secondary px-space-md py-space-2xs rounded-full font-label-badge text-label-badge shadow-sm">
              Best Seller ⭐️
            </div>
            <div className="space-y-space-md pt-space-xs">
              <div className="flex items-center justify-between">
                <span className="font-label-badge text-label-badge px-space-xs py-space-2xs bg-secondary-fixed text-on-secondary-fixed rounded font-semibold">
                  Bán Chạy Nhất
                </span>
                <div className="w-8 h-8 rounded-full bg-[#3d2817] shadow-inner" />
              </div>
              <h3 className="font-headline-md text-headline-md text-primary font-bold">
                Dark Brown (Nâu đậm thanh lịch)
              </h3>
              <div className="h-16 w-full rounded-xl bg-gradient-to-r from-[#2c1c11] via-[#3d2817] to-[#4e341f] flex items-center justify-center text-on-primary font-label-badge text-label-badge shadow-sm">
                Sắc nâu hạt dẻ trầm ấm
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Tông màu được ưa chuộng nhất, mang lại cảm giác trẻ trung, hiện đại và vô cùng tự nhiên dưới ánh sáng ban ngày.
              </p>
            </div>
            <div className="mt-space-lg pt-space-md bg-secondary-fixed/30 p-space-sm rounded-xl">
              <span className="font-label-caps text-label-caps text-secondary font-semibold uppercase">Tỷ lệ che bạc khuyên dùng:</span>
              <p className="font-body-sm text-body-sm text-secondary font-bold mt-1">Lý tưởng nhất cho mọi tỷ lệ tóc bạc</p>
            </div>
          </div>

          {/* Color Card 3: Light Brown */}
          <div
            onClick={() => {
              LPHub.track('cta_click', { buttonId: 'select_color_light_brown', color: 'Light Brown' });
              onSelectColor('Light Brown (Nâu sáng nhẹ nhàng)');
            }}
            className="bg-surface-container-lowest p-space-xl rounded-2xl shadow-sm flex flex-col justify-between transition-all duration-300 hover:shadow-md cursor-pointer border border-transparent hover:border-primary/30"
          >
            <div className="space-y-space-md">
              <div className="flex items-center justify-between">
                <span className="font-label-badge text-label-badge px-space-xs py-space-2xs bg-surface-container-high rounded text-on-surface">
                  Tươi Sáng &amp; Trẻ Trung
                </span>
                <div className="w-8 h-8 rounded-full bg-[#6f432a] shadow-inner" />
              </div>
              <h3 className="font-headline-md text-headline-md text-primary font-bold">
                Light Brown (Nâu sáng nhẹ nhàng)
              </h3>
              <div className="h-16 w-full rounded-xl bg-gradient-to-r from-[#59351e] via-[#6f432a] to-[#865337] flex items-center justify-center text-on-primary font-label-badge text-label-badge shadow-sm">
                Sắc nâu sáng rạng ngời
              </div>
              <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                Lựa chọn lý tưởng cho người thích phong cách thời trang, tạo độ sáng hài hòa cho gương mặt.
              </p>
            </div>
            <div className="mt-space-lg pt-space-md bg-surface-container-low/50 p-space-sm rounded-xl">
              <span className="font-label-caps text-label-caps text-outline uppercase font-semibold">Tỷ lệ che bạc khuyên dùng:</span>
              <p className="font-body-sm text-body-sm text-primary font-bold mt-1">Dưới 50% tóc bạc, thích sự trẻ trung</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "ColorSelectionSection.tsx").write_text(color_code, encoding="utf-8")

# 8. SocialProofSection.tsx
social_proof_code = """import React from 'react';

export const SocialProofSection: React.FC = () => {
  return (
    <section className="py-space-3xl lg:py-space-4xl bg-surface" id="chung-nhan-uy-tin">
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl">
        <div className="max-w-3xl mx-auto text-center space-y-space-xs mb-space-2xl">
          <span className="font-label-caps text-label-caps text-surface-tint font-bold tracking-widest uppercase">
            Uy Tín Quốc Tế
          </span>
          <h2 className="font-headline-lg text-headline-lg-mobile lg:text-headline-lg text-primary font-headline-lg">
            Bảo Chứng Chất Lượng Từ Nhật Bản
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-space-lg">
          {/* Stat 1 */}
          <div className="bg-surface-container p-space-xl rounded-2xl space-y-space-xs">
            <div className="font-data-metric text-data-metric text-primary font-bold">
              37.000.000+
            </div>
            <h3 className="font-headline-sm text-headline-sm text-primary font-semibold">sản phẩm bán ra</h3>
            <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
              Hơn 37 triệu chai chăm sóc tóc bạc Rishiri đã đồng hành cùng người tiêu dùng Nhật Bản suốt hơn một thập kỷ.
            </p>
          </div>
          {/* Stat 2 */}
          <div className="bg-surface-container p-space-xl rounded-2xl space-y-space-xs">
            <div className="font-data-metric text-data-metric text-secondary font-bold">
              14 Năm
            </div>
            <h3 className="font-headline-sm text-headline-sm text-primary font-semibold">liên tiếp dẫn đầu thị phần</h3>
            <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
              Giữ vững vị trí dẫn đầu thị phần sản phẩm chăm sóc tóc bạc tại thị trường nội địa Nhật Bản từ năm 2011 đến nay.
            </p>
          </div>
          {/* Stat 3 */}
          <div className="bg-surface-container p-space-xl rounded-2xl space-y-space-xs">
            <div className="font-data-metric text-data-metric text-primary font-bold">
              +149%
            </div>
            <h3 className="font-headline-sm text-headline-sm text-primary font-semibold">Cải tiến công nghệ 2026</h3>
            <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
              Công thức mới nhất ứng dụng Color Boost tăng 149% hiệu quả bám màu, cho sắc tóc đậm đà và bền màu hơn sau mỗi lần gội.
            </p>
          </div>
          {/* Accreditation 4 */}
          <div className="bg-surface-container p-space-xl rounded-2xl space-y-space-xs lg:col-span-2">
            <div className="flex items-center gap-space-xs text-primary">
              <span className="material-symbols-outlined text-[28px]">domain_verification</span>
              <h3 className="font-headline-sm text-headline-sm font-bold">Nhà máy Itoshima đạt chuẩn ISO 22716</h3>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
              Toàn bộ sản phẩm được nghiên cứu, phát triển và đóng gói tại Itoshima (Fukuoka), tuân thủ tiêu chuẩn thực hành sản xuất mỹ phẩm tốt quốc tế ISO 22716 và tiêu chuẩn chất lượng nghiêm ngặt của Bộ Y tế Lao động Nhật Bản (MHLW).
            </p>
          </div>
          {/* Accreditation 5 */}
          <div className="bg-surface-container p-space-xl rounded-2xl space-y-space-xs">
            <div className="flex items-center gap-space-xs text-primary">
              <span className="material-symbols-outlined text-[28px]">verified_user</span>
              <h3 className="font-headline-sm text-headline-sm font-bold">Nhập khẩu chính hãng</h3>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
              Phân phối chính ngạch bởi Công ty TNHH Genki Fami Việt Nam, đầy đủ tem phụ tiếng Việt và chứng từ hải quan.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "SocialProofSection.tsx").write_text(social_proof_code, encoding="utf-8")

# 9. FaqSection.tsx
faq_code = """import React from 'react';

export const FaqSection: React.FC = () => {
  return (
    <section className="py-space-3xl lg:py-space-4xl bg-surface-container-low" id="faq">
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl">
        <div className="max-w-3xl mx-auto text-center space-y-space-xs mb-space-2xl">
          <span className="font-label-caps text-label-caps text-secondary font-bold tracking-widest uppercase">
            Giải Đáp Mọi Băn Khoăn
          </span>
          <h2 className="font-headline-lg text-headline-lg-mobile lg:text-headline-lg text-primary font-headline-lg">
            Giải Đáp Thắc Mắc Thường Gặp
          </h2>
        </div>
        <div className="max-w-3xl mx-auto space-y-space-md">
          {/* Q1 */}
          <div className="bg-surface-container-lowest p-space-lg rounded-2xl shadow-sm">
            <div className="flex items-start gap-space-sm">
              <span className="font-headline-md text-headline-md text-secondary font-bold">Q1.</span>
              <div className="space-y-space-xs">
                <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                  Dầu gội có làm dính đen da đầu hoặc bàn tay không?
                </h3>
                <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed pt-space-xs">
                  Dầu gội Rishiri hoạt động theo cơ chế phủ màu bề mặt và được rửa trôi dễ dàng bằng xà phòng. Để tiện lợi nhất, bạn có thể làm ướt tay trước khi lấy dầu gội hoặc đeo găng tay mỏng khi thao tác.
                </p>
              </div>
            </div>
          </div>
          {/* Q2 */}
          <div className="bg-surface-container-lowest p-space-lg rounded-2xl shadow-sm">
            <div className="flex items-start gap-space-sm">
              <span className="font-headline-md text-headline-md text-secondary font-bold">Q2.</span>
              <div className="space-y-space-xs">
                <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                  Bao nhiêu lần gội thì tóc bạc lên màu rõ?
                </h3>
                <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed pt-space-xs">
                  Do không dùng hóa chất tẩy mở biểu bì, màu sắc sẽ bồi đắp đậm dần sau 3 đến 5 lần gội đầu tiên. Sau khi đạt màu sắc ưng ý, bạn chỉ cần duy trì gội đều đặn để giữ chân tóc luôn đều màu.
                </p>
              </div>
            </div>
          </div>
          {/* Q3 */}
          <div className="bg-surface-container-lowest p-space-lg rounded-2xl shadow-sm">
            <div className="flex items-start gap-space-sm">
              <span className="font-headline-md text-headline-md text-secondary font-bold">Q3.</span>
              <div className="space-y-space-xs">
                <h3 className="font-headline-sm text-headline-sm text-primary font-bold">
                  Sản phẩm có mùi hôi hắc giống thuốc nhuộm ngoài tiệm không?
                </h3>
                <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed pt-space-xs">
                  Hoàn toàn không. Sản phẩm không chứa amoniac nên không có mùi hăng nồng khó chịu, chỉ mang hương thơm dịu nhẹ và cảm giác tươi mát tự nhiên.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "FaqSection.tsx").write_text(faq_code, encoding="utf-8")

# 10. OrderCtaSection.tsx
order_cta_code = """import React, { useState } from 'react';
import { LPHub } from '../lib/lphub';

interface OrderCtaProps {
  selectedColor: string;
}

export const OrderCtaSection: React.FC<OrderCtaProps> = ({ selectedColor }) => {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    address: '',
    color: selectedColor || 'Dark Brown (Nâu đậm thanh lịch)',
    quantity: 1,
    note: ''
  });

  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [orderCode, setOrderCode] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const unitPrice = 950000;
  const totalPrice = unitPrice * formData.quantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.phone.trim() || !formData.address.trim()) {
      alert("Vui lòng nhập đầy đủ Họ tên, Số điện thoại và Địa chỉ nhận hàng.");
      return;
    }

    setStatus('loading');
    setErrorMessage('');

    try {
      const res = await LPHub.submitOrder({
        formId: 'form-mtqdjmpr-m5et',
        customer: {
          name: formData.name,
          phone: formData.phone,
          address: formData.address,
          note: formData.note
        },
        items: [
          {
            name: `Dầu Gội Phủ Bạc Rishiri Kombu (200ml) - ${formData.color}`,
            quantity: formData.quantity,
            price: unitPrice,
            variant: formData.color
          }
        ],
        total: totalPrice,
        currency: 'VND',
        paymentMethod: 'COD'
      });

      if (res.success) {
        setStatus('success');
        const generatedId = res.id || (res.data && res.data.id) || ('ORD-' + Math.floor(100000 + Math.random() * 900000));
        setOrderCode(generatedId);
        LPHub.track('purchase', {
          orderId: generatedId,
          amount: totalPrice,
          color: formData.color
        });
      } else {
        setStatus('error');
        setErrorMessage(res.error?.message || res.message || 'Có lỗi xảy ra khi đặt hàng. Vui lòng thử lại.');
      }
    } catch (err: any) {
      setStatus('error');
      setErrorMessage(err.message || 'Lỗi mạng khi kết nối đến hệ thống.');
    }
  };

  return (
    <section className="py-space-3xl lg:py-space-4xl bg-primary text-on-primary relative overflow-hidden" id="dat-mua">
      <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(#adcebc_1px,transparent_1px)] [background-size:16px_16px]" />
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl relative z-10">
        <div className="max-w-3xl mx-auto text-center space-y-space-lg mb-space-2xl">
          <div className="inline-flex items-center gap-space-xs px-space-md py-space-2xs bg-primary-container text-on-primary rounded-full">
            <span className="material-symbols-outlined text-secondary-fixed text-[18px]">verified</span>
            <span className="font-label-caps text-label-caps tracking-wider uppercase">Chính Hãng Phân Phối Tại Việt Nam</span>
          </div>
          <h2 className="font-display-hero text-headline-lg lg:text-display-hero font-display-hero text-on-primary leading-tight">
            Sẵn Sàng Trả Lại Sức Sống Cho Mái Tóc Bạc Của Bạn?
          </h2>
          <p className="font-body-lg text-body-lg text-on-primary-container max-w-2xl mx-auto leading-relaxed">
            Không còn nỗi sợ châm chích da đầu. Hãy trải nghiệm liệu pháp phủ bạc dưỡng tóc chuẩn Nhật Bản ngay hôm nay.
          </p>
          <div className="bg-primary-container/80 p-space-md rounded-2xl max-w-xl mx-auto flex items-center justify-center gap-space-sm">
            <span className="material-symbols-outlined text-secondary-fixed text-[26px]">gpp_good</span>
            <p className="font-body-sm text-body-sm text-on-primary text-left">
              100% nhập khẩu chính hãng từ Pyuru Nhật Bản. Đầy đủ tem chống hàng giả và hóa đơn chứng từ.
            </p>
          </div>
        </div>

        {/* Order Form Card */}
        <div className="max-w-2xl mx-auto bg-surface text-on-surface p-space-xl rounded-3xl shadow-2xl">
          {status === 'success' ? (
            <div className="text-center py-space-xl space-y-space-md">
              <div className="w-16 h-16 rounded-full bg-primary text-on-primary mx-auto flex items-center justify-center">
                <span className="material-symbols-outlined text-[32px]">check</span>
              </div>
              <h3 className="font-headline-lg text-headline-lg text-primary">
                ĐẶT HÀNG THÀNH CÔNG!
              </h3>
              <p className="font-body-lg text-on-surface-variant">
                Mã đơn hàng: <strong className="text-secondary font-mono">{orderCode}</strong>
              </p>
              <p className="font-body-md text-on-surface-variant max-w-md mx-auto">
                Chuyên viên tư vấn Rishiri Kombu sẽ liên hệ xác nhận đơn hàng với bạn qua số <strong>{formData.phone}</strong> trong ít phút.
              </p>
              <button
                onClick={() => setStatus('idle')}
                className="mt-space-md px-space-xl py-space-sm bg-primary text-on-primary font-headline-sm rounded-lg hover:bg-primary-container transition-colors"
              >
                Đặt Thêm Đơn Hàng Mới
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-space-md">
              <div className="text-center border-b border-surface-container-high pb-space-sm">
                <h3 className="font-headline-md text-headline-md text-primary font-bold">
                  Đặt Mua Dầu Gội Rishiri Kombu 200ml
                </h3>
                <p className="font-body-sm text-body-sm text-secondary font-semibold mt-1">
                  Giá ưu đãi chính hãng: 950.000 đ / chai (Miễn phí vận chuyển COD toàn quốc)
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
                <div className="space-y-space-2xs">
                  <label className="font-label-caps text-label-caps text-on-surface-variant block uppercase">
                    Họ và tên người nhận *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Ví dụ: Hoàng Thị Ánh Tuyết"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-space-sm py-space-xs rounded-lg border border-outline-variant bg-surface-container-lowest text-on-surface focus:outline-none focus:border-primary text-body-md"
                  />
                </div>
                <div className="space-y-space-2xs">
                  <label className="font-label-caps text-label-caps text-on-surface-variant block uppercase">
                    Số điện thoại nhận hàng *
                  </label>
                  <input
                    type="tel"
                    required
                    placeholder="Ví dụ: 0987654321"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-space-sm py-space-xs rounded-lg border border-outline-variant bg-surface-container-lowest text-on-surface focus:outline-none focus:border-primary text-body-md"
                  />
                </div>
              </div>

              <div className="space-y-space-2xs">
                <label className="font-label-caps text-label-caps text-on-surface-variant block uppercase">
                  Địa chỉ nhận hàng chi tiết *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Số nhà, Tên đường, Phường/Xã, Quận/Huyện, Tỉnh/Thành phố"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-space-sm py-space-xs rounded-lg border border-outline-variant bg-surface-container-lowest text-on-surface focus:outline-none focus:border-primary text-body-md"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
                <div className="space-y-space-2xs">
                  <label className="font-label-caps text-label-caps text-on-surface-variant block uppercase">
                    Chọn tông màu tóc
                  </label>
                  <select
                    value={formData.color}
                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                    className="w-full px-space-sm py-space-xs rounded-lg border border-outline-variant bg-surface-container-lowest text-on-surface focus:outline-none focus:border-primary text-body-md font-medium"
                  >
                    <option value="Dark Brown (Nâu đậm thanh lịch)">Dark Brown (Nâu đậm - Bán chạy nhất)</option>
                    <option value="Black (Đen tự nhiên)">Black (Đen tự nhiên Á Đông)</option>
                    <option value="Light Brown (Nâu sáng nhẹ nhàng)">Light Brown (Nâu sáng trẻ trung)</option>
                  </select>
                </div>
                <div className="space-y-space-2xs">
                  <label className="font-label-caps text-label-caps text-on-surface-variant block uppercase">
                    Số lượng chai
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
                    className="w-full px-space-sm py-space-xs rounded-lg border border-outline-variant bg-surface-container-lowest text-on-surface focus:outline-none focus:border-primary text-body-md text-center font-bold"
                  />
                </div>
              </div>

              <div className="space-y-space-2xs">
                <label className="font-label-caps text-label-caps text-on-surface-variant block uppercase">
                  Ghi chú đơn hàng (nếu có)
                </label>
                <input
                  type="text"
                  placeholder="Ví dụ: Giao vào giờ hành chính, gọi trước 15 phút"
                  value={formData.note}
                  onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                  className="w-full px-space-sm py-space-xs rounded-lg border border-outline-variant bg-surface-container-lowest text-on-surface focus:outline-none focus:border-primary text-body-md"
                />
              </div>

              <div className="p-space-md rounded-xl bg-surface-container flex flex-col sm:flex-row justify-between items-center gap-space-sm">
                <div>
                  <span className="font-label-caps text-label-caps text-on-surface-variant block uppercase">
                    Tổng thanh toán (COD khi nhận):
                  </span>
                  <div className="font-headline-lg text-headline-lg text-primary font-bold">
                    {totalPrice.toLocaleString('vi-VN')} đ
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={status === 'loading'}
                  className="w-full sm:w-auto px-space-xl py-space-sm bg-primary text-on-primary font-headline-sm rounded-lg hover:bg-primary-container transition-all duration-300 shadow-lg disabled:opacity-50"
                >
                  {status === 'loading' ? 'Đang Xử Lý...' : 'Xác Nhận Đặt Hàng'}
                </button>
              </div>

              {status === 'error' && (
                <div className="p-space-sm rounded-lg bg-error-container text-on-error-container font-label-badge text-center">
                  {errorMessage}
                </div>
              )}
            </form>
          )}

          {/* Social Platforms Links */}
          <div className="mt-space-lg pt-space-md border-t border-surface-container-high text-center">
            <span className="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-space-xs">
              Hoặc mua hàng tại sàn thương mại điện tử:
            </span>
            <div className="flex flex-wrap justify-center gap-space-sm">
              <a
                href="https://shopee.vn"
                target="_blank"
                rel="noreferrer"
                className="px-space-md py-space-2xs rounded-lg bg-secondary text-on-secondary font-label-badge text-label-badge hover:bg-secondary/90 transition-colors inline-flex items-center gap-space-2xs"
              >
                <span className="material-symbols-outlined text-[16px]">shopping_cart</span> Shopee Mall
              </a>
              <a
                href="https://lazada.vn"
                target="_blank"
                rel="noreferrer"
                className="px-space-md py-space-2xs rounded-lg bg-surface-container text-on-surface font-label-badge text-label-badge hover:bg-surface-container-high transition-colors inline-flex items-center gap-space-2xs"
              >
                <span className="material-symbols-outlined text-[16px]">storefront</span> Lazada Mall / TikTok Shop
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "OrderCtaSection.tsx").write_text(order_cta_code, encoding="utf-8")

# 11. Footer.tsx
footer_code = """import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-surface-container-low">
      <div className="max-w-container-max mx-auto px-space-md lg:px-space-xl py-space-3xl">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-space-xl">
          {/* Col 1 */}
          <div className="space-y-space-sm">
            <div className="flex items-center gap-space-sm">
              <span className="font-headline-md text-headline-md text-primary font-bold">利尻昆布</span>
              <span className="font-label-caps text-label-caps bg-primary-fixed text-on-primary-fixed px-space-xs py-space-2xs rounded font-bold">
                ISO 22716
              </span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
              Dầu gội phủ bạc hữu cơ Rishiri Kombu chiết xuất tảo bẹ vùng biển lạnh Hokkaido. Liệu pháp chăm sóc tóc bạc tự nhiên, an toàn tuyệt đối cho da đầu nhạy cảm.
            </p>
            <div className="pt-space-xs">
              <span className="font-label-caps text-label-caps text-secondary font-bold block mb-space-2xs">
                CHỨNG NHẬN CHẤT LƯỢNG NHẬT BẢN
              </span>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Nhà máy Pyuru đạt chuẩn Thực hành sản xuất tốt Mỹ phẩm Quốc tế ISO 22716 &amp; GMP Nhật Bản.
              </p>
            </div>
          </div>

          {/* Col 2 */}
          <div className="space-y-space-sm">
            <h4 className="font-headline-sm text-headline-sm text-primary font-semibold">Nhà Sản Xuất Pyuru Co., Ltd.</h4>
            <p className="font-body-sm text-body-sm text-on-surface-variant">Địa chỉ: 723-1 Tomari, Itoshima-shi, Fukuoka 819-1111, Japan</p>
            <p className="font-body-sm text-body-sm text-on-surface-variant">Tiêu chuẩn: 100% Sản xuất và đóng gói nội địa Nhật Bản (Made in Japan)</p>
            <p className="font-body-sm text-body-sm text-on-surface-variant">Cam kết: Không Paraben, Không Silicon, Không Amoniac, Không Hoá Chất Tẩy Nhuộm.</p>
          </div>

          {/* Col 3 */}
          <div className="space-y-space-sm">
            <h4 className="font-headline-sm text-headline-sm text-primary font-semibold">Phân Phối Chính Ngạch</h4>
            <p className="font-body-sm text-body-sm text-on-surface-variant font-medium text-on-surface">Công Ty TNHH Genki Fami Việt Nam</p>
            <p className="font-body-sm text-body-sm text-on-surface-variant">Đại diện phân phối độc quyền và hợp pháp các dòng sản phẩm phủ bạc Rishiri tại Việt Nam.</p>
            <p className="font-body-sm text-body-sm text-on-surface-variant">Hotline Tư Vấn: 1800-xxxx (Miễn cước toàn quốc)</p>
            <p className="font-body-sm text-body-sm text-on-surface-variant">Email: info@genkifami.vn</p>
          </div>

          {/* Col 4 */}
          <div className="space-y-space-sm">
            <h4 className="font-headline-sm text-headline-sm text-primary font-semibold">Liên Kết Nhanh</h4>
            <ul className="space-y-space-2xs font-body-sm text-body-sm text-on-surface-variant">
              <li className="hover:text-on-surface transition-colors cursor-pointer">Hướng dẫn kiểm tra tem chống hàng giả</li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">Chính sách đổi trả &amp; Hoàn tiền</li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">Phương thức giao hàng &amp; Thanh toán</li>
              <li className="hover:text-on-surface transition-colors cursor-pointer">Hồ sơ công bố mỹ phẩm Bộ Y Tế</li>
            </ul>
          </div>
        </div>

        {/* Legal Disclaimer */}
        <div className="mt-space-2xl pt-space-lg bg-surface-container-high/40 p-space-md rounded-xl">
          <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed text-center">
            *Lưu ý: Rishiri Kombu Color Shampoo là dầu gội hỗ trợ phủ màu tóc bạc bằng cơ chế tích tụ hạt màu khoáng thực vật tự nhiên theo từng lần gội, không phải là thuốc nhuộm hóa học tẩy tóc. Mức độ lên màu có thể khác nhau tùy thuộc vào cấu trúc tóc ban đầu và tần suất sử dụng.
          </p>
        </div>

        <div className="mt-space-lg text-center font-body-sm text-body-sm text-on-surface-variant">
          © 2024 Pyuru Co., Ltd. &amp; Genki Fami Vietnam. All rights reserved. Rishiri Kombu Hair Color Series.
        </div>
      </div>
    </footer>
  );
};
"""
(COMPONENTS_DIR / "Footer.tsx").write_text(footer_code, encoding="utf-8")

# 12. App.tsx
app_code = """import React, { useEffect, useState } from 'react';
import { LPHub } from './lib/lphub';
import { Header } from './components/Header';
import { HeroSection } from './components/HeroSection';
import { ProblemSection } from './components/ProblemSection';
import { SolutionSection } from './components/SolutionSection';
import { ScienceSection } from './components/ScienceSection';
import { RoutineSection } from './components/RoutineSection';
import { ColorSelectionSection } from './components/ColorSelectionSection';
import { SocialProofSection } from './components/SocialProofSection';
import { FaqSection } from './components/FaqSection';
import { OrderCtaSection } from './components/OrderCtaSection';
import { Footer } from './components/Footer';

export const App: React.FC = () => {
  const [selectedColor, setSelectedColor] = useState('Dark Brown (Nâu đậm thanh lịch)');

  useEffect(() => {
    LPHub.init({
      apiUrl: 'http://localhost:3001',
      projectId: 'rishiri-kombu',
      landingPageId: 'd-u-g-i-ph--b-c-t-o-b--rishiri-kombu--pyuru-nh-t-b-n--upr2'
    });
    LPHub.track('page_view', { title: 'Rishiri Kombu Color Shampoo Landing Page' });
  }, []);

  const handleSelectColor = (colorName: string) => {
    setSelectedColor(colorName);
    const orderElem = document.getElementById('dat-mua');
    if (orderElem) {
      orderElem.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface antialiased min-h-screen">
      <Header />
      <main className="w-full pt-20 bg-surface">
        <HeroSection />
        <ProblemSection />
        <SolutionSection />
        <ScienceSection />
        <RoutineSection />
        <ColorSelectionSection onSelectColor={handleSelectColor} />
        <SocialProofSection />
        <FaqSection />
        <OrderCtaSection selectedColor={selectedColor} />
      </main>
      <Footer />
    </div>
  );
};

export default App;
"""
(SRC_DIR / "App.tsx").write_text(app_code, encoding="utf-8")

print("Đã sinh toàn bộ 11 components React cho Rishiri Kombu!")
