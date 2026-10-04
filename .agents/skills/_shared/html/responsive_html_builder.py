#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
responsive_html_builder.py — Engine dùng chung xuất bản HTML Responsive cao cấp (Luật R7).
ID: html.responsive_builder

Hỗ trợ xuất bản tài liệu độc lập (Single-file Standalone HTML), thích ứng hoàn hảo trên:
- Mobile: iOS Safari & Android Chrome (drawer TOC, tabbed switcher, stacked view, touch targets >= 44px, zero horizontal overflow)
- Desktop: Chrome, Safari, Edge, Firefox (sticky TOC scrollspy, multi-column parallel comparison, synchronized hover, dark/light toggle)
- Print: Chế độ in ấn sạch (@media print) A4, ẩn thanh công cụ.

Tuân thủ:
- Zero External Dependency: Chạy 100% bằng Python Standard Library (không cần jinja2, markdown, nodejs).
- Zero External CDN: Toàn bộ CSS, SVG icons và vanilla JS nhúng trực tiếp vào file HTML, mở offline 100% qua file://.
- Anti-Repo Bloat: Xuất file thành phẩm vào <output_dir> (mặc định ~/Downloads/AIWF_Output/).
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import output manager từ _shared (Luật R7)
SHARED_DIR = Path(__file__).resolve().parent.parent
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
from output_manager import resolve_output_dir


# ==============================================================================
# 1. DESIGN TOKENS & EMBEDDED STYLES (DARK/LIGHT + RESPONSIVE + PRINT)
# ==============================================================================

EMBEDDED_CSS = """
/* AI Workforce Responsive Document Engine v1.0 */
:root {
  --bg-page: #f8fafc;
  --bg-card: #ffffff;
  --bg-card-alt: #f1f5f9;
  --bg-sidebar: #ffffff;
  --text-primary: #0f172a;
  --text-secondary: #334155;
  --text-muted: #64748b;
  --border-color: #e2e8f0;
  --border-subtle: #f1f5f9;
  --accent-primary: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-soft: rgba(37, 99, 235, 0.08);
  --accent-border: #bfdbfe;
  --code-bg: #f1f5f9;
  --code-text: #0f172a;
  --table-header: #f8fafc;
  --table-zebra: #f8fafc;
  --quote-bg: #f8fafc;
  --quote-border: #3b82f6;
  --badge-bg: #e2e8f0;
  --badge-text: #1e293b;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.04);
  --card-shadow-hover: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-serif: "Times New Roman", "Yu Mincho", "Noto Serif", Georgia, serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  --sidebar-width: 290px;
  --content-max-width: 900px;
  --parallel-max-width: 1480px;
  --header-height: 56px;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
}

[data-theme="dark"] {
  --bg-page: #0b0f19;
  --bg-card: #151c2c;
  --bg-card-alt: #1e293b;
  --bg-sidebar: #111726;
  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --border-color: #243048;
  --border-subtle: #192233;
  --accent-primary: #38bdf8;
  --accent-hover: #60a5fa;
  --accent-soft: rgba(56, 189, 248, 0.12);
  --accent-border: #0369a1;
  --code-bg: #1e293b;
  --code-text: #f1f5f9;
  --table-header: #151c2c;
  --table-zebra: #101624;
  --quote-bg: #111827;
  --quote-border: #38bdf8;
  --badge-bg: #1e293b;
  --badge-text: #93c5fd;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
  --card-shadow-hover: 0 6px 12px rgba(0, 0, 0, 0.5);
}

/* Base Reset */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.65;
  background-color: var(--bg-page);
  color: var(--text-primary);
  scroll-behavior: smooth;
  -webkit-text-size-adjust: 100%;
}

body {
  min-height: 100vh;
  overflow-x: hidden;
  background-color: var(--bg-page);
  color: var(--text-primary);
}

/* Reading Progress Bar */
#reading-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  width: 0%;
  background: linear-gradient(90deg, #2563eb, #38bdf8, #10b981);
  z-index: 1000;
  transition: width 0.1s linear;
}

/* Top App Header */
.app-header {
  position: sticky;
  top: 0;
  z-index: 900;
  height: var(--header-height);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.25rem;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  overflow: hidden;
}

.header-brand {
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--accent-primary);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  white-space: nowrap;
}

.header-title-cut {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 480px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-icon {
  background: var(--bg-card-alt);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-icon:hover {
  background: var(--accent-soft);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.btn-pill {
  background: var(--bg-card-alt);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: all 0.2s ease;
}

.btn-pill:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

/* Layout Container */
.app-container {
  display: flex;
  max-width: 100%;
  margin: 0 auto;
}

/* Sidebar TOC (Desktop) */
.app-sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  height: calc(100vh - var(--header-height));
  position: sticky;
  top: var(--header-height);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
  padding: 1.25rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.sidebar-title {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toc-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.toc-link {
  display: block;
  font-size: 0.825rem;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 0.35rem 0.6rem;
  border-radius: var(--radius-sm);
  line-height: 1.4;
  transition: all 0.15s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-left: 2px solid transparent;
}

.toc-link:hover {
  background: var(--accent-soft);
  color: var(--accent-primary);
}

.toc-link.active {
  background: var(--accent-soft);
  color: var(--accent-primary);
  font-weight: 600;
  border-left-color: var(--accent-primary);
}

.toc-link.toc-h2 { padding-left: 0.6rem; }
.toc-link.toc-h3 { padding-left: 1.4rem; font-size: 0.775rem; opacity: 0.9; }

/* Main Content Area */
.app-main {
  flex: 1;
  min-width: 0;
  padding: 2rem 2.5rem 6rem;
  display: flex;
  justify-content: center;
}

.content-wrapper {
  width: 100%;
  max-width: var(--content-max-width);
}

.content-wrapper.parallel-mode {
  max-width: var(--parallel-max-width);
}

/* Document Hero Header */
.doc-hero {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: var(--card-shadow);
}

.doc-hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--accent-soft);
  color: var(--accent-primary);
  border: 1px solid var(--accent-border);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.85rem;
}

.doc-hero-title {
  font-size: 1.85rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.3;
  margin-bottom: 0.75rem;
}

.doc-hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1.25rem;
  font-size: 0.825rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border-subtle);
  padding-top: 1rem;
  margin-top: 1rem;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

/* Article Typography */
article h1, article h2, article h3, article h4, article h5, article h6 {
  color: var(--text-primary);
  font-weight: 700;
  line-height: 1.35;
  margin-top: 2.2rem;
  margin-bottom: 0.85rem;
  scroll-margin-top: calc(var(--header-height) + 1.5rem);
}

article h1 { font-size: 1.65rem; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem; }
article h2 { font-size: 1.35rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.4rem; }
article h3 { font-size: 1.15rem; }
article h4 { font-size: 1.0rem; }

article p {
  margin-bottom: 1.15rem;
  color: var(--text-secondary);
  font-size: 1.0rem;
  line-height: 1.7;
}

article ul, article ol {
  margin-bottom: 1.25rem;
  padding-left: 1.75rem;
  color: var(--text-secondary);
}

article li {
  margin-bottom: 0.4rem;
  line-height: 1.65;
}

article li::marker {
  color: var(--accent-primary);
}

/* Task Checklists */
ul.task-list {
  list-style: none;
  padding-left: 0.25rem;
}

ul.task-list li {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  margin-bottom: 0.6rem;
}

input[type="checkbox"].task-checkbox {
  appearance: none;
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  min-width: 18px;
  margin-top: 0.2rem;
  border: 2px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-card);
  cursor: pointer;
  position: relative;
  transition: all 0.15s ease;
}

input[type="checkbox"].task-checkbox:checked {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
}

input[type="checkbox"].task-checkbox:checked::after {
  content: "";
  position: absolute;
  left: 5px;
  top: 1px;
  width: 4px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

/* Code Blocks & Inline Code */
code {
  font-family: var(--font-mono);
  font-size: 0.875em;
  background: var(--code-bg);
  color: var(--code-text);
  padding: 0.15em 0.4em;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

pre {
  background: var(--bg-card-alt);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
  overflow-x: auto;
  margin-bottom: 1.5rem;
  position: relative;
}

pre code {
  background: transparent;
  border: none;
  padding: 0;
  font-size: 0.875rem;
  line-height: 1.6;
}

/* Callout Cards & Alerts */
.callout {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-left: 4px solid var(--accent-primary);
  border-radius: var(--radius-md);
  padding: 1.25rem 1.5rem;
  margin: 1.5rem 0;
  box-shadow: var(--card-shadow);
}

.callout.callout-note { border-left-color: #3b82f6; }
.callout.callout-tip { border-left-color: #10b981; }
.callout.callout-important { border-left-color: #8b5cf6; }
.callout.callout-warning { border-left-color: #f59e0b; background: rgba(245, 158, 11, 0.04); }
.callout.callout-caution { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.04); }

.callout-header {
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.callout-note .callout-header { color: #3b82f6; }
.callout-tip .callout-header { color: #10b981; }
.callout-important .callout-header { color: #8b5cf6; }
.callout-warning .callout-header { color: #f59e0b; }
.callout-caution .callout-header { color: #ef4444; }

/* Evidence Citations (Đọc Sâu) */
blockquote.evidence-quote {
  background: var(--quote-bg);
  border: 1px solid var(--border-color);
  border-left: 4px solid var(--quote-border);
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
  margin: 1.25rem 0;
  font-style: normal;
  position: relative;
}

blockquote.evidence-quote .quote-text {
  font-family: var(--font-serif);
  font-size: 1.05rem;
  color: var(--text-primary);
  line-height: 1.6;
}

blockquote.evidence-quote .quote-badge {
  display: inline-block;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent-primary);
  background: var(--accent-soft);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-sm);
}

/* Quick Win 24h Action Card */
.quick-win-card {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.06), rgba(16, 185, 129, 0.08));
  border: 2px solid var(--accent-primary);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin: 2rem 0;
  box-shadow: var(--card-shadow);
}

.quick-win-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--accent-primary);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 0.3rem 0.75rem;
  border-radius: 9999px;
  margin-bottom: 0.75rem;
}

/* Data Tables */
.table-responsive {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 1.5rem 0;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--card-shadow);
  background: var(--bg-card);
}

table.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.925rem;
  text-align: left;
}

table.data-table th {
  background: var(--table-header);
  color: var(--text-primary);
  font-weight: 600;
  padding: 0.85rem 1rem;
  border-bottom: 2px solid var(--border-color);
  white-space: nowrap;
}

table.data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
  line-height: 1.55;
  vertical-align: top;
}

table.data-table tbody tr:nth-child(even) {
  background: var(--table-zebra);
}

table.data-table tbody tr:hover {
  background: var(--accent-soft);
}

/* Parallel View for EJV Multilingual Translations */
.parallel-table-wrapper {
  margin: 1.5rem 0;
}

.lang-selector-mobile {
  display: none;
  position: sticky;
  top: var(--header-height);
  z-index: 850;
  background: var(--bg-card);
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--border-color);
  gap: 0.4rem;
}

.lang-tab {
  flex: 1;
  padding: 0.5rem 0.25rem;
  font-size: 0.8rem;
  font-weight: 600;
  text-align: center;
  border-radius: var(--radius-sm);
  background: var(--bg-card-alt);
  color: var(--text-muted);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.lang-tab.active {
  background: var(--accent-primary);
  color: white;
  border-color: var(--accent-primary);
}

.parallel-row {
  display: grid;
  grid-template-columns: repeat(var(--lang-cols, 3), 1fr);
  gap: 1.25rem;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  margin-bottom: 0.5rem;
  background: var(--bg-card);
  transition: box-shadow 0.15s ease;
}

.parallel-row:hover {
  background: var(--accent-soft);
  box-shadow: var(--card-shadow);
}

.parallel-col {
  min-width: 0;
  font-size: 0.95rem;
  line-height: 1.65;
  color: var(--text-secondary);
}

.parallel-col-label {
  display: none;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--accent-primary);
  margin-bottom: 0.25rem;
}

.parallel-col.primary-lang {
  color: var(--text-primary);
  font-weight: 500;
}

/* Floating Action Button (Mobile Drawer Toggle) */
.btn-fab {
  display: none;
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 950;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: var(--accent-primary);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.mobile-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 980;
}

/* Toast Notification */
#toast-box {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%) translateY(100px);
  background: var(--text-primary);
  color: var(--bg-page);
  padding: 0.5rem 1.25rem;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 500;
  box-shadow: var(--shadow-lg);
  opacity: 0;
  pointer-events: none;
  z-index: 1100;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
}

#toast-box.show {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
}

/* Back to Top */
#back-to-top {
  position: fixed;
  bottom: 1.5rem;
  left: 1.5rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--card-shadow);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s ease, transform 0.25s ease;
  z-index: 800;
}

#back-to-top.visible {
  opacity: 1;
  pointer-events: auto;
}

#back-to-top:hover {
  color: var(--accent-primary);
  border-color: var(--accent-primary);
  transform: translateY(-2px);
}

/* ==========================================================================
   RESPONSIVE BREAKPOINTS (MOBILE & TABLET OPTIMIZATIONS)
   ========================================================================== */

@media screen and (max-width: 1023px) {
  .app-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    height: 100vh;
    z-index: 990;
    transform: translateX(-100%);
    box-shadow: var(--shadow-lg);
  }

  .app-sidebar.open {
    transform: translateX(0);
  }

  .btn-fab {
    display: flex;
  }

  .mobile-overlay.open {
    display: block;
  }

  .app-main {
    padding: 1.5rem 1.25rem 5rem;
  }

  .header-title-cut {
    max-width: 240px;
  }
}

@media screen and (max-width: 767px) {
  :root {
    --header-height: 52px;
  }

  html {
    font-size: 15px;
  }

  .app-main {
    padding: 1rem 0.85rem 5rem;
  }

  .doc-hero {
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    border-radius: var(--radius-md);
  }

  .doc-hero-title {
    font-size: 1.45rem;
  }

  /* Parallel table collapse on mobile */
  .lang-selector-mobile {
    display: flex;
  }

  .parallel-row {
    grid-template-columns: 1fr;
    gap: 0.75rem;
    padding: 0.85rem;
  }

  .parallel-col {
    display: none;
  }

  .parallel-col.mobile-active-lang {
    display: block;
  }

  .parallel-col-label {
    display: block;
  }

  /* Compact tables */
  table.data-table th, table.data-table td {
    padding: 0.6rem 0.75rem;
    font-size: 0.85rem;
  }
}

/* ==========================================================================
   CLEAN PRINT STYLESHEET (@media print)
   ========================================================================== */
@media print {
  body {
    background: #ffffff !important;
    color: #000000 !important;
  }

  .app-header,
  .app-sidebar,
  .btn-fab,
  #back-to-top,
  #reading-progress,
  #toast-box,
  .mobile-overlay,
  .lang-selector-mobile {
    display: none !important;
  }

  .app-main {
    padding: 0 !important;
    max-width: 100% !important;
  }

  .content-wrapper {
    max-width: 100% !important;
  }

  .doc-hero {
    border: none !important;
    box-shadow: none !important;
    padding: 0 0 1rem 0 !important;
    border-bottom: 2px solid #000000 !important;
    margin-bottom: 1.5rem !important;
  }

  .callout, blockquote.evidence-quote, .quick-win-card, .table-responsive {
    box-shadow: none !important;
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .parallel-row {
    break-inside: avoid;
    page-break-inside: avoid;
    border: 1px solid #cccccc !important;
  }

  article a {
    color: #000000 !important;
    text-decoration: underline;
  }
}
"""

EMBEDDED_JS = """
// AI Workforce Responsive Document Engine Interactions
(function() {
  const STORAGE_KEY_THEME = 'aiwf-document-theme';
  const STORAGE_KEY_FONT = 'aiwf-font-size';
  const STORAGE_KEY_TASKS = 'aiwf-tasks-state';

  // 1. Theme Management (Dark / Light)
  function initTheme() {
    const saved = localStorage.getItem(STORAGE_KEY_THEME);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
  }

  window.toggleTheme = function() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem(STORAGE_KEY_THEME, next);
    showToast(next === 'dark' ? '🌙 Chế độ tối' : '☀️ Chế độ sáng');
  };

  // 2. Font Size Scaling
  let currentZoom = 0;
  window.changeFontSize = function(delta) {
    currentZoom = Math.max(-2, Math.min(3, currentZoom + delta));
    const sizes = ['14px', '15px', '16px', '17.5px', '19px', '21px'];
    const targetSize = sizes[currentZoom + 2];
    document.documentElement.style.fontSize = targetSize;
    localStorage.setItem(STORAGE_KEY_FONT, currentZoom);
    showToast('Cỡ chữ: ' + targetSize);
  };

  // 3. Mobile Sidebar Drawer
  window.toggleMobileSidebar = function() {
    const sb = document.querySelector('.app-sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    if (!sb || !overlay) return;
    const isOpen = sb.classList.contains('open');
    if (isOpen) {
      sb.classList.remove('open');
      overlay.classList.remove('open');
      document.body.style.overflow = '';
    } else {
      sb.classList.add('open');
      overlay.classList.add('open');
      document.body.style.overflow = 'hidden';
    }
  };

  // 4. ScrollSpy & Reading Progress
  function initScrollSpy() {
    const progressEl = document.getElementById('reading-progress');
    const bttEl = document.getElementById('back-to-top');
    const headings = Array.from(document.querySelectorAll('article h1, article h2, article h3'));
    const tocLinks = Array.from(document.querySelectorAll('.toc-link'));

    window.addEventListener('scroll', () => {
      // Progress bar
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      if (progressEl) progressEl.style.width = Math.min(100, Math.max(0, progress)) + '%';

      // Back to top button
      if (bttEl) {
        if (scrollTop > 350) bttEl.classList.add('visible');
        else bttEl.classList.remove('visible');
      }

      // Heading highlight
      let currentActiveId = '';
      for (const h of headings) {
        const top = h.getBoundingClientRect().top;
        if (top <= 120) {
          currentActiveId = h.getAttribute('id');
        } else {
          break;
        }
      }

      if (currentActiveId) {
        tocLinks.forEach(link => {
          if (link.getAttribute('href') === '#' + currentActiveId) {
            link.classList.add('active');
          } else {
            link.classList.remove('active');
          }
        });
      }
    }, { passive: true });
  }

  // 5. Mobile Language Tab Switcher (For Parallel Multilingual Translations)
  window.switchMobileLang = function(langKey) {
    const tabs = document.querySelectorAll('.lang-tab');
    tabs.forEach(t => {
      if (t.getAttribute('data-lang') === langKey) t.classList.add('active');
      else t.classList.remove('active');
    });

    const cols = document.querySelectorAll('.parallel-col');
    cols.forEach(c => {
      if (c.getAttribute('data-lang') === langKey) {
        c.classList.add('mobile-active-lang');
      } else {
        c.classList.remove('mobile-active-lang');
      }
    });

    showToast('Ngôn ngữ: ' + langKey.toUpperCase());
  };

  // 6. Interactive Task Checkboxes Persistence
  function initCheckboxes() {
    const boxes = document.querySelectorAll('input.task-checkbox');
    const savedStates = JSON.parse(localStorage.getItem(STORAGE_KEY_TASKS) || '{}');

    boxes.forEach((box, idx) => {
      const key = box.getAttribute('id') || ('task_' + idx);
      if (savedStates[key]) box.checked = true;

      box.addEventListener('change', () => {
        savedStates[key] = box.checked;
        localStorage.setItem(STORAGE_KEY_TASKS, JSON.stringify(savedStates));
        if (box.checked) showToast('✅ Đã đánh dấu hoàn tất!');
      });
    });
  }

  // 7. Toast Notification Helper
  window.showToast = function(msg) {
    const toast = document.getElementById('toast-box');
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => {
      toast.classList.remove('show');
    }, 2200);
  };

  // 8. Close drawer on TOC link click (Mobile)
  function initTocClick() {
    document.querySelectorAll('.toc-link').forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth < 1024) {
          toggleMobileSidebar();
        }
      });
    });
  }

  // DOM Ready Initializer
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initScrollSpy();
    initCheckboxes();
    initTocClick();

    // Khởi tạo tab đầu tiên trên mobile nếu có
    const firstTab = document.querySelector('.lang-tab');
    if (firstTab) {
      switchMobileLang(firstTab.getAttribute('data-lang'));
    }
  });
})();
"""


# ==============================================================================
# 2. MARKDOWN PARSER TO CLEAN HTML
# ==============================================================================

class MarkdownHtmlConverter:
    """Chuyển đổi cú pháp Markdown chuẩn và các thành phần báo cáo AIWF sang HTML."""

    def __init__(self, doc_type: str = "generic"):
        self.doc_type = doc_type
        self.toc_items: List[Dict[str, Any]] = []
        self._heading_counts: Dict[str, int] = {}

    def _slugify(self, text: str) -> str:
        s = text.lower().strip()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s_]+", "-", s)
        if not s:
            s = "section"
        self._heading_counts[s] = self._heading_counts.get(s, 0) + 1
        if self._heading_counts[s] > 1:
            return f"{s}-{self._heading_counts[s]}"
        return s

    def _format_inline(self, text: str) -> str:
        """Định dạng các cú pháp inline: bold, italic, code, link, confidence tags."""
        if not text:
            return ""

        t = html.escape(text)

        # Confidence Badges
        t = re.sub(r'\[(XÁC ĐỊNH|SUY LUẬN ÁP DỤNG|PRIMARY_VERIFIED|Web)\]',
                   r'<span class="badge badge-success" style="background:#10b981;color:#fff;font-size:0.75rem;padding:0.15rem 0.45rem;border-radius:4px;font-weight:600;">[\1]</span>', t)
        t = re.sub(r'\[(CẦN XÁC MINH|CHƯA XÁC MINH|GIẢ ĐỊNH[^\]]*)\]',
                   r'<span class="badge badge-warning" style="background:#f59e0b;color:#fff;font-size:0.75rem;padding:0.15rem 0.45rem;border-radius:4px;font-weight:600;">[\1]</span>', t)
        t = re.sub(r'\[(CẢNH BÁO|FAIL[^\]]*)\]',
                   r'<span class="badge badge-danger" style="background:#ef4444;color:#fff;font-size:0.75rem;padding:0.15rem 0.45rem;border-radius:4px;font-weight:600;">[\1]</span>', t)

        # Inline Code: `code`
        t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)

        # Bold: **bold** or __bold__
        t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', t)

        # Italic: *italic* (chỉ khi sát chữ)
        t = re.sub(r'(?<!\w)\*([^*]+)\*(?!\w)', r'<em>\1</em>', t)

        # Links: [text](url)
        t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', t)

        return t

    def convert(self, md_content: str) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """Phân tích toàn bộ Markdown thành khối HTML + Danh mục TOC + Meta."""
        lines = md_content.splitlines()
        html_parts = []
        meta = {
            "title": "",
            "author": "",
            "year": "",
            "genre": "",
            "level": "",
            "purpose": ""
        }

        in_code_block = False
        code_lines = []
        code_lang = ""

        in_table = False
        table_rows = []

        in_list = False
        list_type = "ul"
        task_id = 0

        i = 0
        n = len(lines)

        while i < n:
            raw_line = lines[i]
            line = raw_line.rstrip()

            # 1. Code Block ```
            if line.startswith("```"):
                if in_code_block:
                    code_html = html.escape("\n".join(code_lines))
                    html_parts.append(f'<pre><code class="language-{code_lang}">{code_html}</code></pre>')
                    in_code_block = False
                    code_lines = []
                else:
                    if in_table:
                        html_parts.append(self._flush_table(table_rows))
                        in_table = False
                        table_rows = []
                    if in_list:
                        html_parts.append(f"</{list_type}>")
                        in_list = False
                    in_code_block = True
                    code_lang = line[3:].strip()
                i += 1
                continue

            if in_code_block:
                code_lines.append(raw_line)
                i += 1
                continue

            # 2. Tables: | col1 | col2 |
            if line.startswith("|") and line.endswith("|"):
                if in_list:
                    html_parts.append(f"</{list_type}>")
                    in_list = False
                in_table = True
                table_rows.append(line)
                i += 1
                continue
            elif in_table:
                html_parts.append(self._flush_table(table_rows))
                in_table = False
                table_rows = []

            # 3. Lists: - item, * item, 1. item, - [ ] task
            list_match = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
            if list_match:
                marker = list_match.group(2)
                item_content = list_match.group(3)
                is_ordered = marker[0].isdigit()
                cur_list_type = "ol" if is_ordered else "ul"

                # Check task list checkbox
                is_task = False
                task_checked = False
                if item_content.startswith("[ ] "):
                    is_task = True
                    task_checked = False
                    item_content = item_content[4:]
                elif item_content.startswith("[x] ") or item_content.startswith("[X] "):
                    is_task = True
                    task_checked = True
                    item_content = item_content[4:]

                if not in_list or list_type != cur_list_type:
                    if in_list:
                        html_parts.append(f"</{list_type}>")
                    list_type = cur_list_type
                    in_list = True
                    list_class = "task-list" if is_task else ""
                    html_parts.append(f'<{list_type} class="{list_class}">')

                formatted_item = self._format_inline(item_content)
                if is_task:
                    task_id += 1
                    chk_str = 'checked' if task_checked else ''
                    html_parts.append(
                        f'<li><input type="checkbox" id="task_chk_{task_id}" class="task-checkbox" {chk_str}>'
                        f'<span>{formatted_item}</span></li>'
                    )
                else:
                    html_parts.append(f"<li>{formatted_item}</li>")

                i += 1
                continue
            elif in_list:
                html_parts.append(f"</{list_type}>")
                in_list = False

            # Empty lines
            if not line.strip():
                i += 1
                continue

            # 4. Headings: # H1, ## H2, ### H3 ...
            heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                h_text = heading_match.group(2).strip()
                h_slug = self._slugify(h_text)

                if level == 1 and not meta["title"]:
                    meta["title"] = h_text
                    i += 1
                    continue

                # Ghi vào TOC
                self.toc_items.append({
                    "level": level,
                    "text": h_text,
                    "slug": h_slug
                })

                formatted_h = self._format_inline(h_text)
                html_parts.append(f'<h{level} id="{h_slug}">{formatted_h}</h{level}>')
                i += 1
                continue

            # 5. Metadata lines: **Tác giả / Đơn vị:** ...
            is_meta = False
            meta_match = re.search(r"\*\*Tác giả[^:]*:\*\*\s*([^|]+)", line)
            if meta_match:
                meta["author"] = meta_match.group(1).strip()
                is_meta = True
            level_match = re.search(r"\*\*Level:\*\*\s*\[?([1-4])\]?", line)
            if level_match:
                meta["level"] = f"Level {level_match.group(1)}"
                is_meta = True
            purpose_match = re.search(r"\*\*Mục đích[^:]*:\*\*\s*\[?([^|\]]+)\]?", line)
            if purpose_match:
                meta["purpose"] = purpose_match.group(1).strip()
                is_meta = True

            if is_meta:
                i += 1
                continue

            # 6. Blockquote & Evidence Quotes: > ...
            if line.startswith(">"):
                quote_lines = []
                while i < n and lines[i].startswith(">"):
                    q_text = lines[i][1:].strip()
                    if q_text:
                        quote_lines.append(q_text)
                    i += 1
                full_quote = " ".join(quote_lines)

                # Check evidence cite: > "..." (vị trí: ...)
                evidence_match = re.search(r'^["“](.+)["”]\s*\((vị trí:[^)]+)\)', full_quote)
                if evidence_match:
                    q_core = self._format_inline(evidence_match.group(1))
                    q_loc = html.escape(evidence_match.group(2))
                    html_parts.append(
                        f'<blockquote class="evidence-quote">'
                        f'<div class="quote-text">“{q_core}”</div>'
                        f'<div class="quote-badge">📍 {q_loc} · [BẰNG CHỨNG XÁC THỰC]</div>'
                        f'</blockquote>'
                    )
                else:
                    formatted_q = self._format_inline(full_quote)
                    html_parts.append(f'<blockquote><p>{formatted_q}</p></blockquote>')
                continue

            # 7. Callouts: [!NOTE], [!TIP], [!WARNING], [!CAUTION], [!IMPORTANT]
            callout_match = re.match(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$", line, re.IGNORECASE)
            if callout_match:
                c_type = callout_match.group(1).lower()
                c_body = callout_match.group(2).strip()
                html_parts.append(
                    f'<div class="callout callout-{c_type}">'
                    f'<div class="callout-header">⚡ {c_type.upper()}</div>'
                    f'<p>{self._format_inline(c_body)}</p>'
                    f'</div>'
                )
                i += 1
                continue

            # 8. Quick Win 24h Card Check
            if "Kế hoạch hành động 24h" in line or "Quick Win 24h" in line:
                html_parts.append('<div class="quick-win-card">')
                html_parts.append('<div class="quick-win-badge">🚀 QUICK WIN 24H · HÀNH ĐỘNG NGAY</div>')
                html_parts.append(f'<p>{self._format_inline(line)}</p>')
                html_parts.append('</div>')
                i += 1
                continue

            # 9. Standard Paragraph
            formatted_p = self._format_inline(line)
            html_parts.append(f"<p>{formatted_p}</p>")
            i += 1

        # Flush any trailing structures
        if in_table:
            html_parts.append(self._flush_table(table_rows))
        if in_list:
            html_parts.append(f"</{list_type}>")

        return "\n".join(html_parts), self.toc_items, meta

    def _flush_table(self, rows: List[str]) -> str:
        """Render mảng dòng markdown table thành HTML table responsive."""
        if not rows:
            return ""

        out = ['<div class="table-responsive"><table class="data-table">']
        has_header = False
        in_tbody = False

        for row_idx, r in enumerate(rows):
            clean_r = r.strip()
            if not clean_r:
                continue

            # Bỏ qua dòng phân cách: |---|---|
            if re.match(r"^\|(\s*:?-+:?\s*\|)+$", clean_r):
                continue

            cells = [c.strip() for c in clean_r.split("|")[1:-1]]

            if row_idx == 0:
                has_header = True
                out.append("<thead><tr>")
                for cell in cells:
                    out.append(f"<th>{self._format_inline(cell)}</th>")
                out.append("</tr></thead>")
            else:
                if not in_tbody:
                    out.append("<tbody>")
                    in_tbody = True
                out.append("<tr>")
                for cell in cells:
                    out.append(f"<td>{self._format_inline(cell)}</td>")
                out.append("</tr>")

        if in_tbody:
            out.append("</tbody>")
        out.append("</table></div>")
        return "\n".join(out)


# ==============================================================================
# 3. EJV TRILINGUAL PARALLEL BUILDER (MULTILINGUAL DUAL-VIEW)
# ==============================================================================

class EjvHtmlConverter:
    """Chuyển đổi dữ liệu EJV Multilingual JSON sang giao diện Responsive Dual-View."""

    def __init__(self, langs: Optional[List[str]] = None):
        self.langs = langs or ["vn", "en", "ja"]
        self.toc_items: List[Dict[str, Any]] = []

    def convert(self, blocks: List[Dict[str, Any]], title: str = "Tài Liệu Dịch Thuật EJV") -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        html_parts = []
        meta = {
            "title": title,
            "languages": ", ".join([l.upper() for l in self.langs]),
            "blocks_count": len(blocks)
        }

        # Mobile Language Selector Bar
        html_parts.append('<div class="lang-selector-mobile">')
        lang_names = {"vn": "Tiếng Việt (VN)", "en": "English (EN)", "ja": "日本語 (JA)", "zh": "中文 (ZH)"}
        for idx, lang in enumerate(self.langs):
            active_cls = "active" if idx == 0 else ""
            label = lang_names.get(lang, lang.upper())
            html_parts.append(
                f'<button class="lang-tab {active_cls}" data-lang="{lang}" onclick="switchMobileLang(\'{lang}\')">'
                f'{label}</button>'
            )
        html_parts.append('</div>')

        html_parts.append(f'<div class="parallel-table-wrapper" style="--lang-cols: {len(self.langs)};">')

        for b_idx, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue

            b_type = block.get("type", "p")
            b_id = f"block_{b_idx + 1}"

            # TOC capture if heading
            if b_type in ("h1", "h2", "h3"):
                h_text = block.get(self.langs[0]) or block.get("vn") or block.get("en") or ""
                if h_text:
                    level = int(b_type[1])
                    self.toc_items.append({
                        "level": level,
                        "text": h_text,
                        "slug": b_id
                    })

            html_parts.append(f'<div class="parallel-row" id="{b_id}">')

            for l_idx, lang in enumerate(self.langs):
                text_content = block.get(lang, "")
                if text_content is None:
                    text_content = ""
                text_content = str(text_content).strip()

                is_primary = "primary-lang" if l_idx == 0 else ""
                mobile_active = "mobile-active-lang" if l_idx == 0 else ""
                lang_label = lang_names.get(lang, lang.upper())

                formatted_text = html.escape(text_content).replace("\n", "<br/>")

                # If heading, render bold
                if b_type.startswith("h") or b_type in ("chapter", "article"):
                    formatted_text = f"<strong>{formatted_text}</strong>"

                html_parts.append(
                    f'<div class="parallel-col {is_primary} {mobile_active}" data-lang="{lang}">'
                    f'<div class="parallel-col-label">{lang_label}</div>'
                    f'{formatted_text}'
                    f'</div>'
                )

            html_parts.append('</div>')

        html_parts.append('</div>')

        return "\n".join(html_parts), self.toc_items, meta


# ==============================================================================
# 4. MASTER HTML TEMPLATE COMPOSITOR
# ==============================================================================

def build_standalone_html(
    content_html: str,
    toc_items: List[Dict[str, Any]],
    meta: Dict[str, Any],
    doc_type: str = "generic",
    parallel_mode: bool = False
) -> str:
    """Tạo file HTML hoàn chỉnh độc lập (Standalone Single File), nhúng toàn bộ CSS + JS."""

    title = meta.get("title") or "Báo Cáo AI Workforce"
    title_escaped = html.escape(title)

    # Render TOC links
    toc_html_parts = []
    if toc_items:
        for item in toc_items:
            h_cls = f"toc-h{item['level']}"
            t_esc = html.escape(item['text'])
            toc_html_parts.append(
                f'<a href="#{item["slug"]}" class="toc-link {h_cls}">{t_esc}</a>'
            )
    else:
        toc_html_parts.append('<div style="font-size:0.8rem;color:var(--text-muted);">Mục lục tài liệu</div>')
    toc_html = "\n".join(toc_html_parts)

    # Render Hero Meta Badges
    meta_badges = []
    if meta.get("level"):
        meta_badges.append(f'<span class="meta-item">🏆 {html.escape(meta["level"])}</span>')
    if meta.get("purpose"):
        meta_badges.append(f'<span class="meta-item">🎯 {html.escape(meta["purpose"])}</span>')
    if meta.get("author"):
        meta_badges.append(f'<span class="meta-item">✍️ {html.escape(meta["author"])}</span>')
    if meta.get("languages"):
        meta_badges.append(f'<span class="meta-item">🌐 {html.escape(meta["languages"])}</span>')
    if meta.get("blocks_count"):
        meta_badges.append(f'<span class="meta-item">📑 {meta["blocks_count"]} khối</span>')

    meta_bar_html = f'<div class="doc-hero-meta">{"".join(meta_badges)}</div>' if meta_badges else ""

    hero_badge_text = "BÁO CÁO PHÂN TÍCH CHUYÊN SÂU" if doc_type == "deep-reading" else "TÀI LIỆU XUẤT BẢN AIWF"
    parallel_class = "parallel-mode" if parallel_mode else ""

    full_html = f"""<!DOCTYPE html>
<html lang="vi" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>{title_escaped}</title>
  <meta name="description" content="Tài liệu xuất bản định dạng HTML Responsive từ AI Workforce">
  <meta name="generator" content="AI Workforce Responsive Document Studio v1.0">
  <style>
{EMBEDDED_CSS}
  </style>
</head>
<body>
  <!-- Reading Progress Bar -->
  <div id="reading-progress"></div>

  <!-- Mobile Drawer Overlay -->
  <div class="mobile-overlay" onclick="toggleMobileSidebar()"></div>

  <!-- Top Navigation Header -->
  <header class="app-header">
    <div class="header-left">
      <button class="btn-icon" onclick="toggleMobileSidebar()" title="Mở danh mục (TOC)" aria-label="Menu">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>
      <div class="header-brand">
        <span>⚡ AIWF</span>
      </div>
      <div class="header-title-cut" title="{title_escaped}">{title_escaped}</div>
    </div>
    <div class="header-right">
      <button class="btn-icon" onclick="changeFontSize(-1)" title="Giảm cỡ chữ (A-)">A-</button>
      <button class="btn-icon" onclick="changeFontSize(1)" title="Tăng cỡ chữ (A+)">A+</button>
      <button class="btn-icon" onclick="toggleTheme()" title="Chuyển đổi giao diện Sáng / Tối" aria-label="Theme">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5"></circle>
          <line x1="12" y1="1" x2="12" y2="3"></line>
          <line x1="12" y1="21" x2="12" y2="23"></line>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
          <line x1="1" y1="12" x2="3" y2="12"></line>
          <line x1="21" y1="12" x2="23" y2="12"></line>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>
      </button>
      <button class="btn-pill" onclick="window.print()" title="In ấn hoặc lưu PDF sạch (A4)">
        <span>🖨️ In A4</span>
      </button>
    </div>
  </header>

  <!-- App Layout -->
  <div class="app-container">
    <!-- Sticky / Drawer Sidebar -->
    <aside class="app-sidebar">
      <div class="sidebar-title">
        <span>Mục lục tài liệu</span>
        <button class="btn-icon" onclick="toggleMobileSidebar()" style="width:28px;height:28px;" title="Đóng">✕</button>
      </div>
      <nav class="toc-nav">
{toc_html}
      </nav>
    </aside>

    <!-- Main Reading Article -->
    <main class="app-main">
      <div class="content-wrapper {parallel_class}">
        <div class="doc-hero">
          <div class="doc-hero-badge">{hero_badge_text}</div>
          <h1 class="doc-hero-title">{title_escaped}</h1>
          {meta_bar_html}
        </div>

        <article>
{content_html}
        </article>
      </div>
    </main>
  </div>

  <!-- Mobile Floating Action Button (TOC) -->
  <button class="btn-fab" onclick="toggleMobileSidebar()" title="Mục lục" aria-label="Mục lục">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <line x1="3" y1="12" x2="21" y2="12"></line>
      <line x1="3" y1="6" x2="21" y2="6"></line>
      <line x1="3" y1="18" x2="21" y2="18"></line>
    </svg>
  </button>

  <!-- Back to Top Button -->
  <button id="back-to-top" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})" title="Lên đầu trang" aria-label="Lên đầu trang">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="18 15 12 9 6 15"></polyline>
    </svg>
  </button>

  <!-- Interactive Toast Notification -->
  <div id="toast-box">Thông báo</div>

  <script>
{EMBEDDED_JS}
  </script>
</body>
</html>
"""
    return full_html


# ==============================================================================
# 5. CORE EXPORT API FUNCTION & CLI INTERFACE
# ==============================================================================

def build_responsive_html(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    doc_type: str = "generic",
    title: Optional[str] = None,
    langs: Optional[List[str]] = None
) -> Path:
    """Hàm lõi chuyển đổi file đầu vào (Markdown hoặc EJV JSON) sang file HTML Responsive hoàn chỉnh."""
    in_path = Path(input_file).resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path}")

    # Xác định đường dẫn output
    if output_file:
        out_path = Path(output_file).resolve()
    else:
        out_dir = resolve_output_dir(skill_name=doc_type)
        out_path = out_dir / f"{in_path.stem}.html"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Đọc dữ liệu đầu vào
    text_content = in_path.read_text(encoding="utf-8")

    # Phân loại đầu vào
    if in_path.suffix.lower() == ".json":
        try:
            data = json.loads(text_content)
        except Exception as e:
            raise ValueError(f"Invalid JSON file: {e}")

        # EJV blocks list
        if isinstance(data, list):
            converter = EjvHtmlConverter(langs=langs)
            doc_title = title or in_path.stem.replace("_", " ").title()
            content_html, toc_items, meta = converter.convert(data, title=doc_title)
            final_html = build_standalone_html(content_html, toc_items, meta, doc_type="parallel", parallel_mode=True)
        elif isinstance(data, dict) and "blocks" in data:
            converter = EjvHtmlConverter(langs=langs)
            doc_title = title or data.get("title") or in_path.stem.replace("_", " ").title()
            content_html, toc_items, meta = converter.convert(data["blocks"], title=doc_title)
            final_html = build_standalone_html(content_html, toc_items, meta, doc_type="parallel", parallel_mode=True)
        else:
            # Generic JSON display
            md_text = f"# {in_path.stem}\n\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
            conv = MarkdownHtmlConverter(doc_type=doc_type)
            content_html, toc_items, meta = conv.convert(md_text)
            if title:
                meta["title"] = title
            final_html = build_standalone_html(content_html, toc_items, meta, doc_type=doc_type, parallel_mode=False)

    else:
        # Markdown file (.md / .txt)
        conv = MarkdownHtmlConverter(doc_type=doc_type)
        content_html, toc_items, meta = conv.convert(text_content)
        if title:
            meta["title"] = title
        elif not meta.get("title"):
            meta["title"] = in_path.stem.replace("_", " ").title()

        final_html = build_standalone_html(
            content_html,
            toc_items,
            meta,
            doc_type=doc_type,
            parallel_mode=False
        )

    out_path.write_text(final_html, encoding="utf-8")
    print(f"✅ Đã xuất bản HTML Responsive thành công: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="AIWF Responsive Document HTML Exporter (Luật R7)")
    parser.add_argument("--input", "-i", required=True, help="Đường dẫn file đầu vào (.md hoặc .json)")
    parser.add_argument("--output", "-o", help="Đường dẫn file đầu ra .html (mặc định tại <output_dir>)")
    parser.add_argument("--type", "-t", default="generic", choices=["generic", "deep-reading", "parallel"],
                        help="Loại văn bản (deep-reading, parallel, generic)")
    parser.add_argument("--title", help="Tiêu đề hiển thị cho tài liệu")
    parser.add_argument("--langs", help="Danh sách ngôn ngữ xuất đối chiếu (ví dụ: vn,en,ja)")

    args = parser.parse_args()

    langs_list = [l.strip() for l in args.langs.split(",")] if args.langs else None

    try:
        build_responsive_html(
            input_file=args.input,
            output_file=args.output,
            doc_type=args.type,
            title=args.title,
            langs=langs_list
        )
    except Exception as e:
        print(f"❌ Lỗi khi xuất bản HTML: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
