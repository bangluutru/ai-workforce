#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_kombu_landing.py
Sinh mã nguồn Landing Page chuẩn 100% Stitch cho dự án 12679839070991793857.
"""

import os, shutil
from pathlib import Path

TARGET_DIR = Path("/Users/tranhaibang/Downloads/landing-pages/rishiri-kombu")
SRC_DIR = TARGET_DIR / "src"
COMPONENTS_DIR = SRC_DIR / "components"
LIB_DIR = SRC_DIR / "lib"
TYPES_DIR = SRC_DIR / "types"

TARGET_DIR.mkdir(parents=True, exist_ok=True)
COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)
LIB_DIR.mkdir(parents=True, exist_ok=True)
TYPES_DIR.mkdir(parents=True, exist_ok=True)

# 1. Sao chép template cơ sở
skill_root = Path(__file__).resolve().parent.parent
template_dir = skill_root / "templates" / "react_vite_template"

for f in ["package.json", "vite.config.ts", "postcss.config.js", "tsconfig.json"]:
    src_f = template_dir / f
    if src_f.exists():
        shutil.copy(src_f, TARGET_DIR / f)

# Điều chỉnh port trong vite.config.ts thành 3002 để tránh xung đột với Rishiri Shampoo (3000) và Landing Hub (3001)
vite_cfg = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3002,
  }
});
"""
(TARGET_DIR / "vite.config.ts").write_text(vite_cfg, encoding="utf-8")

# Sao chép lib/lphub.ts và types/landing.ts
shutil.copy(template_dir / "src" / "lib" / "lphub.ts", LIB_DIR / "lphub.ts")
shutil.copy(template_dir / "src" / "types" / "landing.ts", TYPES_DIR / "landing.ts")

# 2. tailwind.config.js
tw_config = """/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "tertiary-fixed": "#ffdbd0",
        "secondary-fixed": "#ffdcc3",
        "surface-tint": "#466556",
        "outline": "#727974",
        "surface-container-low": "#f8f3ea",
        "on-tertiary": "#ffffff",
        "tertiary": "#351308",
        "secondary": "#904d00",
        "inverse-primary": "#adcebc",
        "on-secondary": "#ffffff",
        "on-background": "#1d1c16",
        "primary-fixed-dim": "#adcebc",
        "primary-fixed": "#c8ead7",
        "surface-bright": "#fef9f0",
        "inverse-surface": "#32302a",
        "on-tertiary-fixed-variant": "#673b2e",
        "on-secondary-container": "#663500",
        "error-container": "#ffdad6",
        "on-surface-variant": "#424844",
        "on-tertiary-fixed": "#331107",
        "inverse-on-surface": "#f5f0e7",
        "surface-container-lowest": "#ffffff",
        "surface-container-high": "#ece8df",
        "surface-dim": "#ded9d1",
        "outline-variant": "#c1c8c2",
        "on-error": "#ffffff",
        "on-secondary-fixed": "#2f1500",
        "surface": "#fef9f0",
        "on-tertiary-container": "#c68c7b",
        "surface-variant": "#e7e2d9",
        "on-secondary-fixed-variant": "#6e3900",
        "background": "#fef9f0",
        "tertiary-container": "#4f271b",
        "primary": "#032217",
        "secondary-fixed-dim": "#ffb77d",
        "on-primary": "#ffffff",
        "primary-container": "#1a382b",
        "error": "#ba1a1a",
        "surface-container-highest": "#e7e2d9",
        "on-primary-fixed": "#022115",
        "tertiary-fixed-dim": "#f7b8a5",
        "on-error-container": "#93000a",
        "on-primary-container": "#81a291",
        "on-surface": "#1d1c16",
        "on-primary-fixed-variant": "#2f4d3f",
        "surface-container": "#f2ede4",
        "secondary-container": "#fe932c"
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "0.5rem",
        "xl": "0.75rem",
        "full": "9999px"
      },
      spacing: {
        "space-lg": "1.5rem",
        "space-xl": "2rem",
        "space-sm": "0.75rem",
        "space-2xl": "3rem",
        "container-max": "75rem",
        "space-2xs": "0.25rem",
        "gutter-desktop": "2rem",
        "gutter-mobile": "1rem",
        "space-4xl": "6.5rem",
        "space-3xl": "4.5rem",
        "space-xs": "0.5rem",
        "space-md": "1rem"
      },
      fontFamily: {
        "label-badge": ["Noto Sans", "sans-serif"],
        "headline-md": ["Noto Serif", "serif"],
        "label-caps": ["Noto Sans", "sans-serif"],
        "display-hero": ["Noto Serif", "serif"],
        "body-sm": ["Noto Sans", "sans-serif"],
        "headline-sm": ["Noto Sans", "sans-serif"],
        "headline-lg-mobile": ["Noto Serif", "serif"],
        "body-md": ["Noto Sans", "sans-serif"],
        "display-hero-mobile": ["Noto Serif", "serif"],
        "headline-lg": ["Noto Serif", "serif"],
        "body-lg": ["Noto Sans", "sans-serif"],
        "data-metric": ["Noto Serif", "serif"]
      },
      fontSize: {
        "label-badge": ["12px", { "lineHeight": "16px", "letterSpacing": "0.04em", "fontWeight": "600" }],
        "headline-md": ["24px", { "lineHeight": "32px", "letterSpacing": "0em", "fontWeight": "500" }],
        "label-caps": ["11px", { "lineHeight": "16px", "letterSpacing": "0.14em", "fontWeight": "700" }],
        "display-hero": ["56px", { "lineHeight": "68px", "letterSpacing": "-0.02em", "fontWeight": "600" }],
        "body-sm": ["13px", { "lineHeight": "20px", "letterSpacing": "0.02em", "fontWeight": "400" }],
        "headline-sm": ["18px", { "lineHeight": "26px", "letterSpacing": "0.01em", "fontWeight": "600" }],
        "headline-lg-mobile": ["26px", { "lineHeight": "36px", "letterSpacing": "-0.01em", "fontWeight": "600" }],
        "body-md": ["15px", { "lineHeight": "26px", "letterSpacing": "0.01em", "fontWeight": "400" }],
        "display-hero-mobile": ["34px", { "lineHeight": "44px", "letterSpacing": "-0.01em", "fontWeight": "600" }],
        "headline-lg": ["38px", { "lineHeight": "48px", "letterSpacing": "-0.015em", "fontWeight": "600" }],
        "body-lg": ["18px", { "lineHeight": "30px", "letterSpacing": "0.01em", "fontWeight": "400" }],
        "data-metric": ["44px", { "lineHeight": "48px", "letterSpacing": "-0.02em", "fontWeight": "700" }]
      }
    }
  },
  plugins: [],
}
"""
(TARGET_DIR / "tailwind.config.js").write_text(tw_config, encoding="utf-8")

# 3. index.html
index_html = """<!doctype html>
<html class="scroll-smooth" lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Rishiri Kombu Color Shampoo - Pyuru Japan x Genki Fami</title>
    <meta name="description" content="Dầu gội phủ màu tóc bạc Rishiri Color Shampoo chiết xuất tảo bẹ Rishiri Hokkaido Nhật Bản. Liệu pháp phủ bạc tự nhiên dịu nhẹ 100% không hóa chất tẩy nhuộm độc hại." />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&family=Noto+Serif:wght@500;600;700&display=swap" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
  </head>
  <body class="bg-surface font-body-md text-body-md text-on-surface antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
(TARGET_DIR / "index.html").write_text(index_html, encoding="utf-8")

# 4. src/index.css
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

::-webkit-scrollbar {
  display: none;
}
"""
(SRC_DIR / "index.css").write_text(index_css, encoding="utf-8")

print("Đã khởi tạo cấu hình dự án Rishiri Kombu!")
