#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reconstruct_rishiri.py
Tái cấu trúc và đồng bộ 100% giao diện từ Stitch HTML vào dự án React Rishiri Shampoo.
"""

import os
from pathlib import Path

TARGET_DIR = Path("/Users/tranhaibang/Downloads/landing-pages/rishiri-shampoo")
SRC_DIR = TARGET_DIR / "src"
COMPONENTS_DIR = SRC_DIR / "components"

COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Cập nhật tailwind.config.js với toàn bộ design tokens từ Stitch
tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "surface-container-lowest": "#ffffff",
        "on-secondary": "#ffffff",
        "tertiary-fixed": "#ffdad8",
        "on-tertiary-fixed": "#3c070b",
        "on-primary-container": "#97e2bd",
        "tertiary": "#702e2f",
        "surface-white": "#FFFFFF",
        "surface-container": "#f0edec",
        "surface-tint": "#1c6b4d",
        "on-tertiary-container": "#ffc4c2",
        "on-primary": "#ffffff",
        "on-primary-fixed": "#002114",
        "primary-container": "#166749",
        "text-on-white": "#166749",
        "on-surface-variant": "#3f4943",
        "secondary-fixed-dim": "#c2c8c6",
        "on-secondary-container": "#606564",
        "on-error-container": "#93000a",
        "on-secondary-fixed": "#171d1c",
        "surface-container-low": "#f6f3f2",
        "secondary": "#5a5f5e",
        "border-muted": "#D1DED9",
        "surface-container-highest": "#e5e2e1",
        "inverse-on-surface": "#f3f0ef",
        "on-tertiary-fixed-variant": "#743232",
        "on-background": "#1c1b1b",
        "surface-bright": "#fcf9f8",
        "primary-fixed-dim": "#8bd6b1",
        "tertiary-fixed-dim": "#ffb3b1",
        "secondary-fixed": "#dee4e2",
        "surface-green": "#166749",
        "text-on-green": "#FFFFFF",
        "error": "#ba1a1a",
        "inverse-primary": "#8bd6b1",
        "on-primary-fixed-variant": "#005137",
        "on-error": "#ffffff",
        "surface": "#fcf9f8",
        "tertiary-container": "#8d4545",
        "background": "#fcf9f8",
        "primary": "#004e34",
        "on-secondary-fixed-variant": "#424847",
        "outline": "#6f7973",
        "surface-dim": "#dcd9d9",
        "surface-container-high": "#ebe7e7",
        "surface-variant": "#e5e2e1",
        "outline-variant": "#bfc9c1",
        "primary-fixed": "#a6f3cc",
        "on-tertiary": "#ffffff",
        "on-surface": "#1c1b1b",
        "error-container": "#ffdad6",
        "inverse-surface": "#313030",
        "secondary-container": "#dee4e2"
      },
      borderRadius: {
        "DEFAULT": "0.125rem",
        "lg": "0.25rem",
        "xl": "0.5rem",
        "full": "0.75rem"
      },
      spacing: {
        "max-width": "1280px",
        "base": "8px",
        "margin-mobile": "16px",
        "gutter": "24px",
        "margin-desktop": "64px"
      },
      fontFamily: {
        "title-md": ["Inter", "sans-serif"],
        "headline-lg-mobile": ["Inter", "sans-serif"],
        "display-lg": ["Inter", "sans-serif"],
        "label-sm": ["Inter", "sans-serif"],
        "headline-lg": ["Inter", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"]
      },
      fontSize: {
        "title-md": ["18px", { "lineHeight": "1.4", "letterSpacing": "0.02em", "fontWeight": "600" }],
        "headline-lg-mobile": ["24px", { "lineHeight": "1.2", "letterSpacing": "0.03em", "fontWeight": "600" }],
        "display-lg": ["48px", { "lineHeight": "1.1", "letterSpacing": "0.05em", "fontWeight": "700" }],
        "label-sm": ["12px", { "lineHeight": "1.4", "letterSpacing": "0.08em", "fontWeight": "600" }],
        "headline-lg": ["32px", { "lineHeight": "1.2", "letterSpacing": "0.03em", "fontWeight": "600" }],
        "body-md": ["16px", { "lineHeight": "1.6", "letterSpacing": "0", "fontWeight": "400" }],
        "body-lg": ["18px", { "lineHeight": "1.6", "letterSpacing": "0", "fontWeight": "400" }]
      }
    }
  },
  plugins: [],
}
"""
(TARGET_DIR / "tailwind.config.js").write_text(tailwind_config, encoding="utf-8")

# 2. Cập nhật index.html với Fonts Material Symbols và Inter
index_html = """<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Dầu Gội Phủ Màu Tóc Thảo Dược Rishiri Kombu | Nhật Bản</title>
    <meta name="description" content="Khám phá Dầu Gội Nhuộm Tóc Thảo Dược Rishiri Kombu Nhật Bản - Giải pháp phủ bạc an toàn, tự nhiên với 28 loại chiết xuất thảo mộc quý." />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet">
  </head>
  <body class="bg-surface-white font-body-md text-on-surface antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
(TARGET_DIR / "index.html").write_text(index_html, encoding="utf-8")

# 3. Cập nhật src/index.css
index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html, body {
    margin: 0;
    padding: 0;
    scroll-behavior: smooth;
  }
  body {
    overscroll-behavior: none;
  }
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
"""
(SRC_DIR / "index.css").write_text(index_css, encoding="utf-8")

# 4. Component: Header.tsx
header_tsx = """import React from 'react';
import { LPHub } from '../lib/lphub';

export const Header: React.FC = () => {
  return (
    <header className="fixed top-0 w-full z-50 bg-surface-white border-b border-border-muted shadow-sm">
      <div className="h-20 max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop flex items-center justify-between">
        <div className="flex items-center gap-4">
          <img
            alt="logo rishiri.png"
            className="h-10 w-auto object-contain"
            src="https://lh3.googleusercontent.com/aida/AP1WRLuLreAejG1vjp6V9t5RlsWzNRztFisg5oW1gNI_st_6vA2C5D5Lcllel4koZVXwa0V7sFzQFmGJOeCDQli6YF4wzM4kGwtlFT_w8OD0gC8Xc0c6zxVfFCt4ptjt3QCZYemcxuW6OVoFlfXI7QktR_fxFoXvNeeoUPv3AH6pn7hzJmxbSzBbaK6A5UDm7qHfjro32gliolX7adiqM9sfD0-xWeh8r_43Lh1LDaVcsdBaec7yCgqI6-WAOHHxxyV5vojjR9Wxi-JQ"
          />
          <span className="font-title-md text-title-md text-text-on-white tracking-widest uppercase">
            RISHIRI
          </span>
        </div>
        <nav className="hidden lg:flex items-center gap-gutter">
          <a
            className="font-label-sm text-label-sm text-primary font-bold border-b-2 border-primary uppercase transition-colors py-2"
            href="#hero-slider"
          >
            TRANG CHỦ
          </a>
          <a
            className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary uppercase transition-colors py-2"
            href="#products"
            onClick={() => LPHub.track('cta_click', { buttonId: 'nav_mau_nhuom', section: 'header' })}
          >
            MÀU NHUỘM THIÊN NHIÊN
          </a>
          <a
            className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary uppercase transition-colors py-2"
            href="#products"
            onClick={() => LPHub.track('cta_click', { buttonId: 'nav_dau_goi', section: 'header' })}
          >
            DẦU GỘI NHUỘM TÓC
          </a>
          <a
            className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary uppercase transition-colors py-2"
            href="#products"
            onClick={() => LPHub.track('cta_click', { buttonId: 'nav_but_nhuom', section: 'header' })}
          >
            BÚT NHUỘM TỨC THỜI
          </a>
        </nav>
        <div className="flex items-center gap-4">
          <a
            href="#order-section"
            onClick={() => LPHub.track('cta_click', { buttonId: 'btn_header_order', section: 'header' })}
            className="px-5 py-2.5 bg-primary text-on-primary font-label-sm text-label-sm uppercase tracking-wider rounded-DEFAULT hover:bg-primary-container transition-colors shadow-sm"
          >
            Đặt Mua Ngay
          </a>
        </div>
      </div>
    </header>
  );
};
"""
(COMPONENTS_DIR / "Header.tsx").write_text(header_tsx, encoding="utf-8")

# 5. Component: HeroSlider.tsx
hero_slider_tsx = """import React, { useState, useEffect } from 'react';

const slides = [
  {
    id: 1,
    url: "https://lh3.googleusercontent.com/aida-public/AB6AXuClUbTYevHQQvIFnWAdyEDK68xl0oRXEmLyeQu929VicCPR4SU_wz4-9xZOlorKNI2GhgG-0AXL_Cqonm-MVpoUknbBYCwfrcjqX7BdRRNurChafvqlzmnb48JFs8COumQGBUYCoJzl2lxTL8F3hYfE3c9iYsLC2kzVI3lGfniALVSizfFU6z3Uh6mOBdwsBHzrflAPXM9xoSo0GjLB32jFHCtzqfVolnoXUnSrjeosxmkbLLoejtarzOm30ZfCf-kbxw"
  },
  {
    id: 2,
    url: "https://lh3.googleusercontent.com/aida-public/AB6AXuD_4kgfUAqc9iOuLED5nR5UWmONvz3T0hGr8eBVuBH1Rrr1UybIqNgXjRNOEJId-ZmpHKKc5mZOmzELFMVJJkwSPiodY1oemElYy1ExmRo3lgtDm1Oc5OS2NrhgRScSsnnX4uHEdAufCvWgHxASFK-Ufb7yGfubxwTTNZx5yYuEPtdNlnxQIvladwx_jKjw2898J6zk8FvZDdtlUEBNKGTFsGeZqJ2F1HDbZT55FlvkSvL1_xbcISu-yaa4M4sEVNwYtA"
  },
  {
    id: 3,
    url: "https://lh3.googleusercontent.com/aida-public/AB6AXuClTDdPoQLCXrqcaiWvrIWWlem-jFvsJ5Z9I-US7Tth-ljdcIlxKIgvgQgro1kDKyacZM33L1JstEFewmn2WnnpSbM9a9wVs2pMaVATh6sHlrp2CXg0iLjU7aPzzbBXAvs3icoocICvgx741qeGNCAu7LIv7nQcedx5GcR5NQJvDKv6iYQVZqy03OtnhrTKr_lm5DHAVI17ZMaHM2IA1qSnRvZn5YaXP0bhehcIDDIS4KCf7OSP8ZF-0muSW8wetKzWmw"
  }
];

export const HeroSlider: React.FC = () => {
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="relative w-full h-[600px] lg:h-[720px] overflow-hidden bg-surface-container" id="hero-slider">
      {slides.map((slide, index) => (
        <div
          key={slide.id}
          className={`absolute inset-0 transition-opacity duration-1000 ${
            index === currentSlide ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
          }`}
        >
          <div
            className="w-full h-full bg-cover bg-center"
            style={{ backgroundImage: `url('${slide.url}')` }}
          />
        </div>
      ))}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex gap-4">
        {slides.map((_, index) => (
          <button
            key={index}
            aria-label={`Slide ${index + 1}`}
            onClick={() => setCurrentSlide(index)}
            className={`w-3 h-3 rounded-full transition-all duration-300 ${
              index === currentSlide ? "bg-primary w-8" : "bg-surface-white/60 hover:bg-surface-white"
            }`}
          />
        ))}
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "HeroSlider.tsx").write_text(hero_slider_tsx, encoding="utf-8")

# 6. Component: BrandPhilosophy.tsx (Section 2)
brand_philosophy_tsx = """import React from 'react';

export const BrandPhilosophy: React.FC = () => {
  return (
    <section className="w-full bg-primary pt-24 pb-0 text-on-primary">
      <div className="flex flex-col gap-16 w-full">
        <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop text-center flex flex-col gap-4 items-center">
          <span className="font-label-sm text-label-sm tracking-[0.2em] uppercase text-primary-fixed-dim">
            Triết lý sản phẩm
          </span>
          <h2 className="font-display-lg text-display-lg uppercase">
            Điểm khác biệt vượt trội của Rishiri
          </h2>
          <div className="w-16 h-1 bg-primary-fixed-dim mx-auto mt-4" />
        </div>
        <div className="w-full">
          <img
            alt="Điểm khác biệt vượt trội"
            className="w-full h-auto object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuAwzjkL1J4eGbgOooGVGJ3Woq8fob1D3-xMTx021J9Dxz9bPkG2pb78boDJTeqX4XqD9q-0roN0xVsUIFJsROoiWlpHtqBaG7UgGbUqdXiWRBK7qNuGYI7OSKSAZvUQ3-Errz6KUunKYl-74aqL9LySlRpTHWLJIX91_P-37Zd7LIqeGoXbJa9IVeKVAZf2xGBvGwYADRL7Dy_W_8jWm-CgXyCcNbZrDZcRWkpjl4Lewt7pc4atm60FbGm4kvG0c6WrxRNSYJhMU8Gfxg"
          />
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "BrandPhilosophy.tsx").write_text(brand_philosophy_tsx, encoding="utf-8")

# 7. Component: ColorMechanism.tsx (Section 3)
color_mechanism_tsx = """import React from 'react';

export const ColorMechanism: React.FC = () => {
  return (
    <section className="w-full bg-surface-white py-32">
      <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop">
        <div className="flex flex-col md:flex-row gap-16 items-center">
          <div className="w-full md:w-1/2 flex flex-col gap-8">
            <div className="flex flex-col gap-4">
              <span className="font-label-sm text-label-sm tracking-[0.2em] uppercase text-primary">
                Cơ chế tác động
              </span>
              <h2 className="font-headline-lg text-headline-lg text-on-surface uppercase">
                Cơ chế nhuộm an toàn từ biểu bì
              </h2>
            </div>
            <p className="font-body-lg text-body-lg text-on-surface-variant leading-relaxed">
              Không giống như thuốc nhuộm hóa học phá vỡ cấu trúc tóc để đưa hạt màu vào sâu bên trong, Rishiri sử dụng cơ chế bám màu ion, nhẹ nhàng bao phủ bên ngoài lớp biểu bì, giúp tóc không bị hư tổn, khô xơ.
            </p>
          </div>
          <div className="w-full md:w-1/2 flex flex-col gap-8">
            <div className="relative w-full aspect-[1.57] rounded-xl overflow-hidden border border-border-muted shadow-sm">
              <img
                alt="Cơ chế bám màu ion"
                className="w-full h-full object-cover"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuAcPLXHxdTPF_aLVA01OloTQKxqjh0sHMLYgeCVBNMGE3dmcAfCB8_8-ujQU8khVOZhhxutvBKYS-Mk8sxPrd0P6jxc4IwNbe1ghaA6UssRfH3dbZZoY7pdhaYxzzLFgE61cKiQvGH9JIsE2bmeM6JXpAbekbPUJYqlZt1AMm-hseiMM3ULOjE8LHjqCYYio0HImbKe9Cr98ZXOeBaWTOP65GCSubQ9eeXZfZV4pWrt1WQbzf_afMU5AKDjj2X5fvvKkw"
              />
            </div>
            <div className="relative w-full aspect-[1.57] rounded-xl overflow-hidden border border-border-muted shadow-sm">
              <img
                alt="Biểu bì tóc được bảo vệ"
                className="w-full h-full object-cover"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCw9o5Z6-Adeh4_4nqg3zR_hL6hxd3Xk4lJ_lKWyU5D1DtxsEgyLBS0teYM4EGJEgpLjgbRaquZovDuDUHMJ0NKbZRGvL3KPPqF3GklyT8Y9qwfvkXwlpCVUs91TdZhjEg10nTMAoiwVC-zzasmnbBPR-M_5nJV_VCBExYaVphSR2lo17RvN6BQNzjyfz1Q6LwFpqZ1CmocGFOiJGYPVnEzqDEsxQcl-o7d52WqKaRdSZv4W7p3iPyDwr1CkGHeek5nxw"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "ColorMechanism.tsx").write_text(color_mechanism_tsx, encoding="utf-8")

# 8. Component: HerbalIngredients.tsx (Section 4)
herbal_ingredients_tsx = """import React from 'react';
import { LPHub } from '../lib/lphub';

export const HerbalIngredients: React.FC = () => {
  return (
    <section className="w-full bg-surface-bright py-32 border-t border-border-muted">
      <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop">
        <div className="flex flex-col-reverse md:flex-row gap-24 items-center">
          <div className="w-full md:w-1/2 flex flex-col gap-8 pr-0 lg:pr-16">
            <span className="font-label-sm text-label-sm tracking-[0.2em] uppercase text-primary">
              Tinh túy tự nhiên
            </span>
            <h2 className="font-display-lg text-display-lg text-on-surface uppercase leading-tight">
              28 Loại Chiết Xuất<br />Thảo Dược
            </h2>
            <div className="w-12 h-1 bg-primary" />
            <p className="font-body-lg text-body-lg text-on-surface-variant leading-relaxed">
              Thành phần chính là tảo bẹ Kombu từ vùng biển sạch Rishiri (Nhật Bản), kết hợp cùng 28 loại chiết xuất thực vật khác. Các thành phần này không chỉ tạo màu tự nhiên mà còn cung cấp độ ẩm sâu, phục hồi tóc hư tổn từ bên trong.
            </p>
            <a
              href="#products"
              onClick={() => LPHub.track('cta_click', { buttonId: 'btn_learn_more', section: 'herbal_ingredients' })}
              className="self-start mt-4 px-8 py-4 bg-primary text-on-primary font-label-sm text-label-sm uppercase tracking-wider rounded-DEFAULT hover:bg-primary-container transition-colors inline-block"
            >
              Tìm hiểu thêm
            </a>
          </div>
          <div className="w-full md:w-1/2">
            <div className="relative w-full aspect-[0.72] max-w-md mx-auto rounded-2xl overflow-hidden shadow-2xl">
              <img
                alt="28 loại thảo dược quý"
                className="w-full h-full object-cover"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCOQbWBcg2dGbdzOglYtBqGmo7cV4tE0i8_7jFS-plZppUxZcuq2FheQ7JbWoctdGJlJS1pDk7uba0zIE-zkWSnrzh3dFB62jlQeUh37ClfQwx3C1xQHfzoMQnpOMAgoZmZavOFlBUJCvbo1fT_Obqy6cP60sxRimPvl0Zu7U-PNXvBzeBF1YvPl0P0qErCRrJkyi-chce8puhIZKgZKxiFFaWyb7o0yupNmdMp9xwtgL5qMjFMoBOULunED-b6QqBirw"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "HerbalIngredients.tsx").write_text(herbal_ingredients_tsx, encoding="utf-8")

# 9. Component: PpdWarning.tsx (Section 5)
ppd_warning_tsx = """import React from 'react';

export const PpdWarning: React.FC = () => {
  return (
    <section className="w-full bg-surface-container-low py-32">
      <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop">
        <div className="bg-surface-white p-12 lg:p-24 rounded-3xl border border-border-muted shadow-lg flex flex-col md:flex-row items-center gap-16">
          <div className="w-full md:w-1/3 flex justify-center">
            <div className="w-64 h-64 relative rounded-full border-4 border-error overflow-hidden shadow-md">
              <img
                alt="Cảnh báo PPD"
                className="w-full h-full object-cover"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuB91_3wTCI34Dg3n05pBFwLtwOca2Y8XKdJMjodQ9I7ghW3g-X4JkAXKVyQ38V-GVVn8ytEzkkgM2UjQMa6Q0ddNCsVd9Crff_OhXuchE1WMwXKpwwz9JGfH1ImdrA6sflhNYqMhaqN1NYTUkarhVP_Mr4YDH5TupeAi75JHlSH7Yi2FNyQfbRI_eDhSreaOdsil26XleMQXDiMCeYB7OaaMHegV4ffWzIV0Wx-xNI46vhvTkRN236cjbtPfLuaqH_X-Q"
              />
              <div className="absolute inset-0 bg-error/10" />
            </div>
          </div>
          <div className="w-full md:w-2/3 flex flex-col gap-6">
            <div className="inline-flex items-center gap-2 bg-error-container text-on-error-container px-4 py-2 rounded-full self-start">
              <span className="material-symbols-outlined text-[20px]">warning</span>
              <span className="font-label-sm text-label-sm uppercase tracking-wide">Cảnh báo sức khỏe</span>
            </div>
            <h2 className="font-headline-lg text-headline-lg text-on-surface uppercase">
              Nói không với PPD &amp; Hóa chất độc hại
            </h2>
            <p className="font-body-lg text-body-lg text-on-surface-variant leading-relaxed">
              PPD (Paraphenylenediamine) là hóa chất phổ biến trong thuốc nhuộm tóc, nguyên nhân chính gây dị ứng da đầu, rụng tóc và các vấn đề sức khỏe nghiêm trọng. Sản phẩm Rishiri cam kết 0% PPD, 0% Diamine, 0% Paraben, 0% Dầu khoáng.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "PpdWarning.tsx").write_text(ppd_warning_tsx, encoding="utf-8")

# 10. Component: ExpertQuote.tsx (Section 6)
expert_quote_tsx = """import React from 'react';

export const ExpertQuote: React.FC = () => {
  return (
    <section className="w-full bg-primary py-32 text-on-primary">
      <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop">
        <div className="flex flex-col md:flex-row gap-16 items-center">
          <div className="w-full md:w-5/12">
            <div className="relative aspect-[3/4] w-full rounded-2xl overflow-hidden shadow-2xl">
              <img
                alt="Dr. Yumi Harada"
                className="w-full h-full object-cover"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuBHQ4RADgpemGUv7ZeDe54bwMDCyO_t0LKxU_dbZvuxyKJnAiMqNjmxi4Ou069UJRbTJF-0ixc7b5qW3--zPP7ByIdFntYTbC3t-WOhswY6FIAG8fjFKxxoGD0wxFlQwM9_ad1h5goMMixxkG4iGSbe7IUYUNfgkOfPPTA9Jl-uBS2TyAwTvoNe8ZfTSu2xyqXIPzIgTr8yKLdCMbDKdS4B8Lm-dxZC9xSI1ZOpO8YvHe1pkfx94zUN"
              />
            </div>
          </div>
          <div className="w-full md:w-7/12 flex flex-col gap-8 lg:pl-12">
            <span className="material-symbols-outlined text-[48px] text-primary-fixed-dim opacity-50">
              format_quote
            </span>
            <h3 className="font-headline-lg text-headline-lg text-on-primary leading-relaxed font-light">
              "Sự cân bằng hoàn hảo giữa hiệu quả thẩm mỹ và sự an toàn tối ưu cho sức khỏe lâu dài của khách hàng."
            </h3>
            <div className="flex flex-col gap-1 mt-4">
              <span className="font-title-md text-title-md uppercase tracking-widest text-primary-fixed">
                Dr. Yumi Harada
              </span>
              <span className="font-label-sm text-label-sm uppercase text-primary-fixed-dim">
                Chuyên gia Da liễu &amp; Tóc - Viện Nghiên cứu Sastty Nhật Bản
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "ExpertQuote.tsx").write_text(expert_quote_tsx, encoding="utf-8")

# 11. Component: UsageSteps.tsx (Section 7)
usage_steps_tsx = """import React from 'react';

export const UsageSteps: React.FC = () => {
  return (
    <section className="w-full bg-surface-white py-32">
      <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop flex flex-col items-center gap-16">
        <div className="text-center flex flex-col gap-4">
          <span className="font-label-sm text-label-sm tracking-[0.2em] uppercase text-primary">
            Hướng dẫn sử dụng
          </span>
          <h2 className="font-display-lg text-display-lg text-on-surface uppercase">
            3 Bước Nhuộm Tóc Tại Nhà
          </h2>
        </div>
        <div className="w-full max-w-4xl border border-border-muted rounded-2xl overflow-hidden shadow-lg p-4 bg-surface-bright">
          <img
            alt="3 bước nhuộm tóc"
            className="w-full h-auto object-cover rounded-xl"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuC9GJ7Z94Dm153x9sGEgINWZ0QJDAYlhwHgtNUQb11Jy9moQgEPyfXuj75Yw0OY1sIajULmiw1KXtWT6oQTPsnSxkvRn5mEou6WAlkvchktvU32XzbA8rzba8GAgUoLsnUrQl5MyhPBTRi1MylD9hCG6u-wW_JYstgPH28HyJfB8F4UbP01mfvqIXolvOmox8s-o2YcejY3s62QmReStK6pJIIEFZ-yXZ_bg3qIb1uxje0oObl2M06ouotXiDvYcbn9FA"
          />
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "UsageSteps.tsx").write_text(usage_steps_tsx, encoding="utf-8")

# 12. Component: ProductCatalog.tsx (Section 8)
product_catalog_tsx = """import React from 'react';
import { LPHub } from '../lib/lphub';

interface ProductCatalogProps {
  onSelectProduct: (productName: string, price: number) => void;
}

export const ProductCatalog: React.FC<ProductCatalogProps> = ({ onSelectProduct }) => {
  const products = [
    {
      id: "product-1",
      name: "Màu Nhuộm Thiên Nhiên Rishiri",
      desc: "Giải pháp phủ bạc hoàn hảo với 28 loại thảo dược quý.",
      price: 850000,
      priceFormatted: "850.000đ",
      badge: "Best Seller",
      image: "https://lh3.googleusercontent.com/aida-public/AB6AXuCzNtT0bIFjIk_dQULG-hWyC280hp66hgc3XlEFyBgZ0rBLYxjjBm7a066ApwNj3BhMT_yHRmEPb8OsewvuoCBRbvVfeSFHcmr1uAsPyUVDIBBLFGDDvLd5ihslvX1tZjp3L2BVaDlGFQksX_S-iWpo1SFDQkW_9BUArWb86Bryg9YIdnSvZOuXVtXNQxl_SLtHehDs4VD7S1n-_UwMODpgKCU8yTAt1RUuteFTO7c9c9Y-91SHtY2cc2cS5Ssrk1kBQQ"
    },
    {
      id: "product-2",
      name: "Dầu Gội Nhuộm Tóc Rishiri",
      desc: "Lên màu dần dần qua mỗi lần gội, vô cùng tiện lợi.",
      price: 950000,
      priceFormatted: "950.000đ",
      badge: "Phổ Biến",
      image: "https://lh3.googleusercontent.com/aida-public/AB6AXuCadYZrG7E8q30zBlJaiNIFCuKpl9Dk8BmaMxroYwHliqNrm6iSVzj0jbEtozbb0sE-ijUkY9qQN9ejOoduO3i3UzvQX8YykKKf9Ta9EnD8A1ZpdqcAiMhl72O4IeJxYLfeHMCPVJAJrfRjr72TYTSz1Qv4d-4OvOFO9NayJ5IZIZolRevCXmHN4KF9kOMHEZ9__pJY6YYDr8AT0uJtanlMJKbgNISu-WmUnzqMq99MExa4T_XWShXYKMkaoHvKgK-s1w"
    },
    {
      id: "product-3",
      name: "Bút Nhuộm Tức Thời Rishiri",
      desc: "Che phủ chân tóc bạc nhanh chóng trước khi ra ngoài.",
      price: 750000,
      priceFormatted: "750.000đ",
      badge: "Tiện Lợi",
      image: "https://lh3.googleusercontent.com/aida-public/AB6AXuByMBR3NrLh16txZjGtCwBpjEPwiu0SAA8miTS5BGQjz9-DKjm8PjUMLduxlLwlWCvYHOZwWqoJgdM7zOH8Je6HFh602sfOa9l5pMmXPkfKWjTBij_MHoyFrERWt1F7SwgFtXdoRFWiFb4btguPEsfQxMt3GAAqonyRR26NLrglbD3hx45iqONAwjwXnQw5M0Nkrcmy-sUsGox0U0NHFQ6ZUfmygQiIbR-tA1M1FKmaAgYplRvueNa8G1_YDXGpICpF4Q"
    }
  ];

  return (
    <section className="w-full bg-surface-container py-32 border-t border-border-muted" id="products">
      <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop flex flex-col gap-20">
        <div className="flex flex-col md:flex-row justify-between items-end gap-8 border-b border-border-muted pb-8">
          <div className="flex flex-col gap-4">
            <span className="font-label-sm text-label-sm tracking-[0.2em] uppercase text-primary">
              Danh mục
            </span>
            <h2 className="font-display-lg text-display-lg text-on-surface uppercase">
              Bộ 3 Sản Phẩm Rishiri
            </h2>
          </div>
          <a
            href="#order-section"
            className="flex items-center gap-2 font-label-sm text-label-sm uppercase text-primary hover:text-primary-container transition-colors group cursor-pointer"
          >
            Đặt hàng ngay
            <span className="material-symbols-outlined transform group-hover:translate-x-1 transition-transform">
              arrow_forward
            </span>
          </a>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {products.map((p) => (
            <div
              key={p.id}
              onClick={() => {
                LPHub.track('cta_click', { buttonId: `card_${p.id}`, productName: p.name });
                onSelectProduct(p.name, p.price);
              }}
              className="flex flex-col bg-surface-white border border-border-muted rounded-xl overflow-hidden hover:shadow-xl transition-shadow group cursor-pointer"
            >
              <div className="relative w-full aspect-[0.72] bg-surface-bright p-8 flex items-center justify-center border-b border-border-muted">
                <img
                  alt={p.name}
                  className="h-full w-auto object-contain transform group-hover:scale-105 transition-transform duration-500"
                  src={p.image}
                />
                <div className="absolute top-4 left-4 bg-secondary-container text-on-secondary-container px-3 py-1 rounded-full font-label-sm text-label-sm uppercase tracking-wider">
                  {p.badge}
                </div>
              </div>
              <div className="p-8 flex flex-col gap-6 flex-grow">
                <div className="flex flex-col gap-2">
                  <h3 className="font-title-md text-title-md text-on-surface uppercase line-clamp-2">
                    {p.name}
                  </h3>
                  <p className="font-body-md text-body-md text-on-surface-variant">
                    {p.desc}
                  </p>
                </div>
                <div className="mt-auto pt-6 border-t border-border-muted flex items-center justify-between">
                  <span className="font-title-md text-title-md text-primary font-bold">
                    {p.priceFormatted}
                  </span>
                  <button
                    aria-label="Chọn mua sản phẩm"
                    className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center group-hover:bg-primary group-hover:text-on-primary transition-colors text-primary"
                  >
                    <span className="material-symbols-outlined text-[20px]">shopping_bag</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "ProductCatalog.tsx").write_text(product_catalog_tsx, encoding="utf-8")

# 13. Component: TiktokReviews.tsx (Section 9)
tiktok_reviews_tsx = """import React, { useEffect, useRef } from 'react';

const reviews = [
  { id: 0, user: "@lanhuong_review", quote: "Không hề rát da đầu, màu lên tự nhiên lắm!" },
  { id: 1, user: "@thuytien_spa", quote: "Gội 3 lần là phủ đều chân tóc bạc, cực kỳ tiện lợi." },
  { id: 2, user: "@minhanh_hair", quote: "Tóc mềm mượt hẳn, không bị khô xơ như thuốc nhuộm." },
  { id: 3, user: "@beauty_japan", quote: "Mùi hương thảo mộc rất dễ chịu, thích hợp dùng lâu dài." },
  { id: 4, user: "@chame_yeuthuong", quote: "Mua tặng mẹ, mẹ khen dùng không hề ngứa hay rát." },
  { id: 5, user: "@ngoclan_vlog", quote: "Thành phần 28 loại thảo mộc lành tính an tâm tuyệt đối." },
  { id: 6, user: "@duocsi_mai", quote: "Giải pháp phủ bạc ion an toàn cho người da đầu nhạy cảm." },
  { id: 7, user: "@thanhhang_40", quote: "Tiết kiệm thời gian ra tiệm, tự gội tại nhà rất nhanh." },
  { id: 8, user: "@haianh_organic", quote: "Chuẩn hàng nội địa Nhật, chất lượng vượt trội." }
];

export const TiktokReviews: React.FC = () => {
  const sliderRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const slider = sliderRef.current;
    if (!slider) return;

    let scrollAmount = 0;
    const interval = setInterval(() => {
      const maxScroll = slider.scrollWidth - slider.clientWidth;
      scrollAmount += 320;
      if (scrollAmount > maxScroll) scrollAmount = 0;
      slider.scrollTo({
        left: scrollAmount,
        behavior: 'smooth'
      });
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className="w-full bg-primary py-32 overflow-hidden text-on-primary relative" id="testimonials">
      <div
        className="absolute inset-0 opacity-5 pointer-events-none"
        style={{
          backgroundImage: `url('https://lh3.googleusercontent.com/aida-public/AB6AXuAexiMZ3NpNUKS7ho06uxZO1MUZzcwaQLk_xx0yIjZy5Em1xLzIWHtY5u9ksv753mjY1HYqY8z-0e2uzAhj3mV4BEzmRsgzvjuqATHLwdK5RWPWttFI_K7rMhdQFe9Wou7-HZ82PMB9BQv7MpBdScTE6_vlDpk4Xpdthi5v7eJmJKmtPnbhHqtJFg-1LeAspC9voPNheTQlsddVR8OLW9mrY_-Va05gTuY0_StTubD5OodECX-9NPja')`
        }}
      />
      <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop flex flex-col gap-16 relative z-10">
        <div className="text-center flex flex-col gap-4">
          <span className="font-label-sm text-label-sm tracking-[0.2em] uppercase text-primary-fixed-dim">
            Đánh giá thực tế
          </span>
          <h2 className="font-display-lg text-display-lg uppercase">
            Khách Hàng Nói Gì Về Rishiri
          </h2>
        </div>
        <div className="relative w-full">
          <div
            ref={sliderRef}
            className="flex gap-8 overflow-x-auto pb-8 snap-x snap-mandatory hide-scrollbar"
          >
            {reviews.map((r) => (
              <div
                key={r.id}
                className="flex-none w-[300px] md:w-[350px] aspect-[9/16] bg-surface-white rounded-2xl overflow-hidden relative shadow-xl snap-center group cursor-pointer"
              >
                <div className="absolute inset-0 bg-surface-variant">
                  <img
                    alt={r.user}
                    className="w-full h-full object-cover"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJKuEfow-HdeXcQugCDfMzE5FuKxWOiJuA_VzcGR99dq1_wdS0qd6lRuJGN9_h2d-PgHPgnCt2pX4YQ-wyOS0UJrtcESd-kK_zAhjE4vVou-vKGQ2aHh3n9IhHh89kv_5swHNa9Wibu8lxyrCqaWoTJ9BZAHTaig_M1hx5zlOKgT-epiIuIJ0Khy_cwa4c1WwOiTCvRhGUcQIfJwYhT8ZRbu9iFq1uasdps5rS2ybS7H0NAsiXO-f4"
                  />
                </div>
                <div className="absolute inset-0 bg-on-background/20 group-hover:bg-on-background/40 transition-colors" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full bg-surface-white/90 backdrop-blur flex items-center justify-center transform group-hover:scale-110 transition-transform shadow-md">
                    <span className="material-symbols-outlined text-primary text-[32px] ml-1">
                      play_arrow
                    </span>
                  </div>
                </div>
                <div className="absolute bottom-0 left-0 w-full p-6 bg-gradient-to-t from-on-background/90 via-on-background/50 to-transparent">
                  <p className="font-title-md text-title-md text-surface-white line-clamp-2 leading-snug">
                    "{r.quote}"
                  </p>
                  <p className="font-label-sm text-label-sm text-surface-white/80 mt-2 font-mono">
                    {r.user}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "TiktokReviews.tsx").write_text(tiktok_reviews_tsx, encoding="utf-8")

# 14. Component: OrderForm.tsx (Tích hợp Landing Hub SDK)
order_form_tsx = """import React, { useState } from 'react';
import { LPHub } from '../lib/lphub';

interface OrderFormProps {
  selectedProduct: string;
  unitPrice: number;
}

export const OrderForm: React.FC<OrderFormProps> = ({ selectedProduct, unitPrice }) => {
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    address: '',
    product: selectedProduct || 'Dầu Gội Nhuộm Tóc Rishiri',
    color: 'Đen Tự Nhiên (Natural Black)',
    quantity: 1,
    note: ''
  });

  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [orderCode, setOrderCode] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const currentPrice = unitPrice || 950000;
  const totalPrice = currentPrice * formData.quantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.phone.trim() || !formData.address.trim()) {
      alert("Vui lòng điền đầy đủ Họ tên, Số điện thoại và Địa chỉ nhận hàng.");
      return;
    }

    setStatus('loading');
    setErrorMessage('');

    try {
      const res = await LPHub.submitOrder({
        customer: {
          name: formData.name,
          phone: formData.phone,
          address: formData.address,
        },
        items: [
          {
            sku: formData.product,
            name: `${formData.product} - ${formData.color}`,
            qty: formData.quantity,
            price: currentPrice
          }
        ],
        totalAmount: totalPrice,
        currency: 'VND',
        paymentMethod: 'COD',
        shippingAddress: {
          address: formData.address
        },
        notes: formData.note
      });

      if (res.success) {
        setStatus('success');
        setOrderCode(res.orderId || 'ORD-' + Math.floor(100000 + Math.random() * 900000));
        LPHub.track('purchase', {
          orderId: res.orderId,
          amount: totalPrice,
          product: formData.product
        });
      } else {
        setStatus('error');
        setErrorMessage(res.error || 'Có lỗi xảy ra trong quá trình đặt hàng. Vui lòng thử lại.');
      }
    } catch (err: any) {
      setStatus('error');
      setErrorMessage(err.message || 'Lỗi mạng. Vui lòng thử lại sau ít phút.');
    }
  };

  return (
    <section className="w-full bg-surface-white py-32 border-t border-border-muted" id="order-section">
      <div className="max-w-[1000px] mx-auto px-margin-mobile lg:px-margin-desktop">
        <div className="bg-surface-bright rounded-3xl p-8 md:p-16 border border-border-muted shadow-2xl">
          <div className="text-center max-w-2xl mx-auto mb-12 flex flex-col gap-4">
            <span className="font-label-sm text-label-sm tracking-[0.2em] uppercase text-primary font-bold">
              ĐẶT MUA CHÍNH HÃNG
            </span>
            <h2 className="font-display-lg text-display-lg uppercase text-on-surface">
              Ưu Đãi Đặc Biệt Hôm Nay
            </h2>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Miễn phí giao hàng toàn quốc • Kiểm tra hàng trước khi thanh toán • Tặng kèm phụ kiện chuyên dụng
            </p>
          </div>

          {status === 'success' ? (
            <div className="p-8 rounded-2xl bg-surface-container border border-primary text-center flex flex-col items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-primary text-on-primary flex items-center justify-center">
                <span className="material-symbols-outlined text-[32px]">check</span>
              </div>
              <h3 className="font-headline-lg text-headline-lg text-primary uppercase">
                Đặt Hàng Thành Công!
              </h3>
              <p className="font-body-lg text-on-surface-variant">
                Mã đơn hàng của bạn: <strong className="text-primary font-mono">{orderCode}</strong>
              </p>
              <p className="font-body-md text-on-surface-variant max-w-md">
                Bộ phận chăm sóc khách hàng Rishiri Japan sẽ liên hệ xác nhận đơn hàng với bạn qua số điện thoại <strong>{formData.phone}</strong> trong vòng 15 phút.
              </p>
              <button
                onClick={() => setStatus('idle')}
                className="mt-4 px-8 py-3 bg-primary text-on-primary font-label-sm text-label-sm uppercase tracking-wider rounded-DEFAULT hover:bg-primary-container transition-colors"
              >
                Đặt Thêm Đơn Khác
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex flex-col gap-2">
                  <label className="font-label-sm text-label-sm uppercase text-on-surface-variant">
                    Họ và tên người nhận *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Ví dụ: Nguyễn Thị Mai"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-3.5 rounded-DEFAULT border border-border-muted bg-surface-white focus:outline-none focus:border-primary text-on-surface"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="font-label-sm text-label-sm uppercase text-on-surface-variant">
                    Số điện thoại nhận hàng *
                  </label>
                  <input
                    type="tel"
                    required
                    placeholder="Ví dụ: 0912345678"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-4 py-3.5 rounded-DEFAULT border border-border-muted bg-surface-white focus:outline-none focus:border-primary text-on-surface"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="font-label-sm text-label-sm uppercase text-on-surface-variant">
                  Địa chỉ nhận hàng chi tiết *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Số nhà, Tên đường, Phường/Xã, Quận/Huyện, Tỉnh/TP"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-4 py-3.5 rounded-DEFAULT border border-border-muted bg-surface-white focus:outline-none focus:border-primary text-on-surface"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex flex-col gap-2">
                  <label className="font-label-sm text-label-sm uppercase text-on-surface-variant">
                    Chọn dòng sản phẩm
                  </label>
                  <select
                    value={formData.product}
                    onChange={(e) => setFormData({ ...formData, product: e.target.value })}
                    className="w-full px-4 py-3.5 rounded-DEFAULT border border-border-muted bg-surface-white focus:outline-none focus:border-primary text-on-surface font-body-md"
                  >
                    <option value="Dầu Gội Nhuộm Tóc Rishiri">Dầu Gội Nhuộm Tóc (950.000đ)</option>
                    <option value="Màu Nhuộm Thiên Nhiên Rishiri">Màu Nhuộm Thiên Nhiên (850.000đ)</option>
                    <option value="Bút Nhuộm Tức Thời Rishiri">Bút Nhuộm Tức Thời (750.000đ)</option>
                  </select>
                </div>
                <div className="flex flex-col gap-2">
                  <label className="font-label-sm text-label-sm uppercase text-on-surface-variant">
                    Chọn tông màu tóc
                  </label>
                  <select
                    value={formData.color}
                    onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                    className="w-full px-4 py-3.5 rounded-DEFAULT border border-border-muted bg-surface-white focus:outline-none focus:border-primary text-on-surface font-body-md"
                  >
                    <option value="Đen Tự Nhiên (Natural Black)">Đen Tự Nhiên (Natural Black)</option>
                    <option value="Nâu Đậm (Dark Brown)">Nâu Đậm (Dark Brown)</option>
                    <option value="Nâu Sáng (Light Brown)">Nâu Sáng (Light Brown)</option>
                  </select>
                </div>
                <div className="flex flex-col gap-2">
                  <label className="font-label-sm text-label-sm uppercase text-on-surface-variant">
                    Số lượng
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
                    className="w-full px-4 py-3.5 rounded-DEFAULT border border-border-muted bg-surface-white focus:outline-none focus:border-primary text-on-surface text-center font-bold"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="font-label-sm text-label-sm uppercase text-on-surface-variant">
                  Ghi chú đơn hàng (nếu có)
                </label>
                <input
                  type="text"
                  placeholder="Ví dụ: Giao giờ hành chính, gọi trước khi giao"
                  value={formData.note}
                  onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                  className="w-full px-4 py-3.5 rounded-DEFAULT border border-border-muted bg-surface-white focus:outline-none focus:border-primary text-on-surface"
                />
              </div>

              <div className="p-6 rounded-2xl bg-surface-container flex flex-col md:flex-row justify-between items-center gap-4">
                <div>
                  <span className="font-label-sm text-label-sm uppercase text-on-surface-variant">
                    Tổng tiền thanh toán (COD khi nhận hàng):
                  </span>
                  <div className="font-display-lg text-[28px] text-primary font-bold">
                    {totalPrice.toLocaleString('vi-VN')} đ
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={status === 'loading'}
                  className="w-full md:w-auto px-10 py-4 bg-primary text-on-primary font-title-md text-title-md uppercase tracking-wider rounded-DEFAULT hover:bg-primary-container transition-colors shadow-lg disabled:opacity-50"
                >
                  {status === 'loading' ? 'Đang Xử Lý...' : 'Xác Nhận Đặt Mua'}
                </button>
              </div>

              {status === 'error' && (
                <div className="p-4 rounded-DEFAULT bg-error-container text-on-error-container font-label-sm text-center">
                  {errorMessage}
                </div>
              )}
            </form>
          )}
        </div>
      </div>
    </section>
  );
};
"""
(COMPONENTS_DIR / "OrderForm.tsx").write_text(order_form_tsx, encoding="utf-8")

# 15. Component: Footer.tsx (Section 10)
footer_tsx = """import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-surface-container-low border-t border-border-muted py-16 mt-20">
      <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop flex flex-col md:flex-row justify-between gap-12">
        <div className="flex flex-col gap-4 max-w-sm">
          <div className="flex items-center gap-2">
            <img
              alt="logo rishiri.png"
              className="h-8 w-auto grayscale opacity-70"
              src="https://lh3.googleusercontent.com/aida/AP1WRLuLreAejG1vjp6V9t5RlsWzNRztFisg5oW1gNI_st_6vA2C5D5Lcllel4koZVXwa0V7sFzQFmGJOeCDQli6YF4wzM4kGwtlFT_w8OD0gC8Xc0c6zxVfFCt4ptjt3QCZYemcxuW6OVoFlfXI7QktR_fxFoXvNeeoUPv3AH6pn7hzJmxbSzBbaK6A5UDm7qHfjro32gliolX7adiqM9sfD0-xWeh8r_43Lh1LDaVcsdBaec7yCgqI6-WAOHHxxyV5vojjR9Wxi-JQ"
            />
            <span className="font-title-md text-title-md text-on-surface-variant uppercase tracking-wider">
              RISHIRI
            </span>
          </div>
          <p className="font-body-md text-label-sm text-on-surface-variant leading-relaxed">
            Sản phẩm chăm sóc tóc thảo dược từ vùng biển Rishiri Nhật Bản, kết hợp khoa học hiện đại và tinh túy tự nhiên.
          </p>
          <div className="text-xs text-on-surface-variant/80 mt-2">
            <strong>Nhà sản xuất:</strong> Pyuru Co., Ltd. (Fukuoka, Japan)<br />
            <strong>Đơn vị phân phối:</strong> Genki Fami Vietnam
          </div>
        </div>
        <div className="grid grid-cols-2 gap-12">
          <div className="flex flex-col gap-4">
            <h4 className="font-label-sm text-label-sm text-primary uppercase font-bold">
              Sản phẩm
            </h4>
            <nav className="flex flex-col gap-2">
              <a className="font-body-md text-label-sm text-on-surface-variant hover:text-primary transition-colors" href="#products">
                Tất cả sản phẩm
              </a>
              <a className="font-body-md text-label-sm text-on-surface-variant hover:text-primary transition-colors" href="#order-section">
                Ưu đãi mới nhất
              </a>
            </nav>
          </div>
          <div className="flex flex-col gap-4">
            <h4 className="font-label-sm text-label-sm text-primary uppercase font-bold">
              Hỗ trợ
            </h4>
            <nav className="flex flex-col gap-2">
              <a className="font-body-md text-label-sm text-on-surface-variant hover:text-primary transition-colors" href="#order-section">
                Đặt hàng trực tuyến
              </a>
              <a className="font-body-md text-label-sm text-on-surface-variant hover:text-primary transition-colors" href="#">
                Chính sách vận chuyển
              </a>
            </nav>
          </div>
        </div>
      </div>
      <div className="max-w-[1280px] mx-auto px-margin-mobile lg:px-margin-desktop mt-12 pt-8 border-t border-border-muted/30 text-center font-label-sm text-label-sm text-on-surface-variant/60 uppercase tracking-widest">
        © 2024 RISHIRI JAPAN. ALL RIGHTS RESERVED.
      </div>
    </footer>
  );
};
"""
(COMPONENTS_DIR / "Footer.tsx").write_text(footer_tsx, encoding="utf-8")

# 16. App.tsx: Lắp ghép hoàn chỉnh theo đúng thứ tự 10 sections của Stitch
app_tsx = """import React, { useEffect, useState } from 'react';
import { LPHub } from './lib/lphub';
import { Header } from './components/Header';
import { HeroSlider } from './components/HeroSlider';
import { BrandPhilosophy } from './components/BrandPhilosophy';
import { ColorMechanism } from './components/ColorMechanism';
import { HerbalIngredients } from './components/HerbalIngredients';
import { PpdWarning } from './components/PpdWarning';
import { ExpertQuote } from './components/ExpertQuote';
import { UsageSteps } from './components/UsageSteps';
import { ProductCatalog } from './components/ProductCatalog';
import { TiktokReviews } from './components/TiktokReviews';
import { OrderForm } from './components/OrderForm';
import { Footer } from './components/Footer';

export const App: React.FC = () => {
  const [selectedProduct, setSelectedProduct] = useState('Dầu Gội Nhuộm Tóc Rishiri');
  const [unitPrice, setUnitPrice] = useState(950000);

  useEffect(() => {
    LPHub.init({
      apiUrl: 'http://localhost:3001',
      projectId: 'rishiri',
      landingPageId: 'd-u-g-i-nhu-m-t-c-th-o-d--c-rishiri-kombu-183o',
      formId: 'form-mtpsf9pw-8ur4'
    });
    LPHub.track('page_view', { title: 'Rishiri Kombu Hair Care Landing Page' });
  }, []);

  const handleSelectProduct = (productName: string, price: number) => {
    setSelectedProduct(productName);
    setUnitPrice(price);
    const orderElem = document.getElementById('order-section');
    if (orderElem) {
      orderElem.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="bg-surface-white font-body-md text-on-surface min-h-screen">
      <Header />
      <main className="w-full pt-20 bg-surface-white">
        <HeroSlider />
        <BrandPhilosophy />
        <ColorMechanism />
        <HerbalIngredients />
        <PpdWarning />
        <ExpertQuote />
        <UsageSteps />
        <ProductCatalog onSelectProduct={handleSelectProduct} />
        <TiktokReviews />
        <OrderForm selectedProduct={selectedProduct} unitPrice={unitPrice} />
      </main>
      <Footer />
    </div>
  );
};

export default App;
"""
(SRC_DIR / "App.tsx").write_text(app_tsx, encoding="utf-8")

print("SUCCESS: Hoàn thành tái cấu trúc 100% Landing Page Rishiri Shampoo từ Stitch HTML!")
