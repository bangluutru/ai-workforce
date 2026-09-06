#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
landing_builder.py — Bộ Sinh Mã Nguồn Landing Page (React + Vite + TS + Tailwind)
Xây dựng dự án landing page thực tế, chạy được, tích hợp sẵn LPHub SDK.
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

def generate_landing_project(design_spec: dict, hub_config: dict, target_dir: str) -> dict:
    """
    Sinh mã nguồn landing page hoàn chỉnh từ đặc tả thiết kế và cấu hình Landing Hub.
    """
    out_path = Path(target_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    # Thư mục template gốc
    skill_root = Path(__file__).resolve().parent.parent
    template_dir = skill_root / "templates" / "react_vite_template"

    # 1. Sao chép cấu hình nền tảng (package.json, vite.config.ts, tsconfig.json, etc.)
    for base_file in ["package.json", "vite.config.ts", "tailwind.config.js", "postcss.config.js", "tsconfig.json"]:
        src_file = template_dir / base_file
        if src_file.exists():
            shutil.copy(src_file, out_path / base_file)

    # Tạo cấu trúc thư mục src
    src_dir = out_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "lib").mkdir(parents=True, exist_ok=True)
    (src_dir / "types").mkdir(parents=True, exist_ok=True)
    (src_dir / "components").mkdir(parents=True, exist_ok=True)

    # 2. Sao chép lib/lphub.ts và types/landing.ts
    shutil.copy(template_dir / "src" / "lib" / "lphub.ts", src_dir / "lib" / "lphub.ts")
    shutil.copy(template_dir / "src" / "types" / "landing.ts", src_dir / "types" / "landing.ts")

    # 3. Chuẩn hóa token và màu sắc
    tokens = design_spec.get("tokens") or design_spec.get("variables") or {}
    colors = tokens.get("colors", {})
    primary = colors.get("primary", "#006964")
    secondary = colors.get("secondary", "#51BF9D")
    accent = colors.get("accent", "#E11D48")
    bg = colors.get("background", "#0B1320")
    surface = colors.get("surface", "#162235")
    text_color = colors.get("text", "#F8FAFC")
    muted_color = colors.get("muted", "#94A3B8")

    # 4. Sinh index.css với CSS Variables tùy biến theo thương hiệu
    index_css_content = f"""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {{
  --color-primary: {primary};
  --color-secondary: {secondary};
  --color-accent: {accent};
  --color-background: {bg};
  --color-surface: {surface};
  --color-text: {text_color};
  --color-muted: {muted_color};
  --radius-brand: 1.25rem;
}}

html {{
  scroll-behavior: smooth;
}}

body {{
  margin: 0;
  padding: 0;
  background-color: var(--color-background);
  color: var(--color-text);
  overflow-x: hidden;
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}}
"""
    (src_dir / "index.css").write_text(index_css_content, encoding="utf-8")

    # 5. Sinh index.html
    title = design_spec.get("title", "Landing Page")
    index_html_src = (template_dir / "index.html").read_text(encoding="utf-8")
    index_html_rendered = index_html_src.replace("{{TITLE}}", title).replace("{{DESCRIPTION}}", f"Khám phá {title}")
    (out_path / "index.html").write_text(index_html_rendered, encoding="utf-8")

    # 6. Trích xuất thông tin các section
    sections = design_spec.get("sections", [])
    header_data = next((s["content"] for s in sections if s.get("role") == "header"), {})
    hero_data = next((s["content"] for s in sections if s.get("role") == "hero"), {})
    benefits_data = next((s["content"] for s in sections if s.get("role") == "benefits"), {})
    form_section = next((s for s in sections if "form" in s.get("role", "")), None)
    order_data = form_section.get("content", {}) if form_section else {}
    footer_data = next((s["content"] for s in sections if s.get("role") == "footer"), {})

    # Hỗ trợ cả cấu trúc phẳng hoặc lồng trong { config: { ... } }
    cfg = hub_config.get("config", hub_config)
    form_type = cfg.get("formType", "lead")
    project_id = cfg.get("projectId", "genki-fami")
    lp_id = cfg.get("landingPageId", "genki-lp-01")
    form_id = cfg.get("formId", "form-01")
    api_url = cfg.get("apiUrl", "http://localhost:3001")

    # 7. Sinh Component Header.tsx
    header_code = f"""import React from 'react';
import {{ LPHub }} from '../lib/lphub';

export const Header: React.FC = () => {{
  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-900/80 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-xl font-extrabold tracking-tight text-white bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent">
            {header_data.get("brand", "Genki Fami Japan")}
          </span>
          <span className="hidden sm:inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20">
            {header_data.get("badge", "Chính Hãng")}
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <a
            href="tel:{header_data.get('hotline', '1800-6868')}"
            className="hidden md:inline-flex text-sm text-slate-300 hover:text-white transition"
          >
            Hotline: <strong className="ml-1 text-teal-400">{header_data.get("hotline", "1800-6868")}</strong>
          </a>
          <a
            href="#order-section"
            onClick={{() => LPHub.track('cta_click', {{ buttonId: 'btn_header_cta', section: 'header' }})}}
            className="px-4 py-2 text-sm font-semibold rounded-full text-white bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 shadow-md shadow-teal-500/20 transition transform hover:-translate-y-0.5"
          >
            {header_data.get("ctaLabel", "Đặt Ngay")}
          </a>
        </div>
      </div>
    </header>
  );
}};
"""
    (src_dir / "components" / "Header.tsx").write_text(header_code, encoding="utf-8")

    # 8. Sinh Component Hero.tsx
    stats_items = hero_data.get("stats", [
        {"value": "96.8%", "label": "Khách hàng hài lòng"},
        {"value": "15 Phút", "label": "Hấp thu nhanh chóng"},
        {"value": "Top 1", "label": "Thương hiệu khuyên dùng"}
    ])
    stats_markup = "\n".join([
        f"""          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 backdrop-blur">
            <div className="text-2xl sm:text-3xl font-black text-teal-400">{s.get('value')}</div>
            <div className="text-xs sm:text-sm text-slate-400 mt-1">{s.get('label')}</div>
          </div>""" for s in stats_items
    ])

    hero_code = f"""import React from 'react';
import {{ LPHub }} from '../lib/lphub';

export const Hero: React.FC = () => {{
  return (
    <section className="relative overflow-hidden py-16 sm:py-24 bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-950">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-teal-500/10 via-transparent to-transparent pointer-events-none" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-300 text-xs sm:text-sm font-medium">
              <span className="flex h-2 w-2 rounded-full bg-teal-400 animate-pulse" />
              <span>Tiêu chuẩn nội địa Nhật Bản</span>
            </div>
            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-tight">
              {hero_data.get("headline", "Giải Pháp Trẻ Hóa Tự Nhiên")}
            </h1>
            <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
              {hero_data.get("subheadline", "Chăm sóc làn da và sức khỏe với chiết xuất vi hạt sinh học cao cấp.")}
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-2">
              <a
                href="#order-section"
                onClick={{() => LPHub.track('cta_click', {{ buttonId: 'btn_hero_primary', section: 'hero' }})}}
                className="w-full sm:w-auto px-8 py-4 rounded-full text-base font-bold text-white bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 shadow-xl shadow-teal-500/25 transition transform hover:-translate-y-0.5 text-center"
              >
                {hero_data.get("primaryCta", "Đặt Hàng Nhận Ưu Đãi")}
              </a>
              <a
                href="#benefits-section"
                onClick={{() => LPHub.track('cta_click', {{ buttonId: 'btn_hero_secondary', section: 'hero' }})}}
                className="w-full sm:w-auto px-6 py-4 rounded-full text-base font-semibold text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-800 border border-slate-700 transition text-center"
              >
                {hero_data.get("secondaryCta", "Tìm Hiểu Thêm")}
              </a>
            </div>
            <div className="grid grid-cols-3 gap-3 pt-6">
{stats_markup}
            </div>
          </div>
          <div className="lg:col-span-5 flex justify-center">
            <div className="relative w-full max-w-md">
              <div className="absolute -inset-1 rounded-3xl bg-gradient-to-tr from-teal-500 to-emerald-500 opacity-30 blur-2xl animate-pulse" />
              <div className="relative rounded-2xl overflow-hidden border border-slate-700/80 shadow-2xl bg-slate-800">
                <img
                  src="{hero_data.get('productImage', 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=800&auto=format&fit=crop&q=80')}"
                  alt="Sản phẩm chính"
                  className="w-full h-80 sm:h-96 object-cover hover:scale-105 transition duration-500"
                  loading="lazy"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}};
"""
    (src_dir / "components" / "Hero.tsx").write_text(hero_code, encoding="utf-8")

    # 9. Sinh Component Benefits.tsx
    benefit_items = benefits_data.get("items", [
        {"title": "Công Nghệ Độc Quyền", "desc": "Hấp thu đa tầng nhanh hơn gấp nhiều lần."},
        {"title": "Dưỡng Ẩm Chuyên Sâu", "desc": "Cung cấp dưỡng chất thiết yếu cho cấu trúc tế bào."},
        {"title": "Lành Tính An Toàn", "desc": "Kiểm nghiệm da liễu nghiêm ngặt, không kích ứng."}
    ])
    benefits_markup = "\n".join([
        f"""          <div className="p-8 rounded-2xl bg-slate-800/60 border border-slate-700/60 hover:border-teal-500/40 transition hover:shadow-xl hover:shadow-teal-500/5 group">
            <div className="w-12 h-12 rounded-xl bg-teal-500/10 border border-teal-500/20 text-teal-400 flex items-center justify-center font-bold text-xl mb-6 group-hover:scale-110 transition">
              0{i}
            </div>
            <h3 className="text-xl font-bold text-white mb-3">{item.get('title')}</h3>
            <p className="text-slate-300 leading-relaxed text-sm sm:text-base">{item.get('desc')}</p>
          </div>""" for i, item in enumerate(benefit_items, start=1)
    ])

    benefits_code = f"""import React from 'react';

export const Benefits: React.FC = () => {{
  return (
    <section id="benefits-section" className="py-20 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-teal-400 text-sm font-bold tracking-wider uppercase">Giá Trị Cốt Lõi</span>
          <h2 className="text-3xl sm:text-4xl font-black text-white mt-2">
            Tại Sao Hơn 50,000 Khách Hàng Tin Dùng?
          </h2>
          <p className="text-slate-400 mt-4 text-base sm:text-lg">
            Sản phẩm được nghiên cứu bài bản, mang lại kết quả bền vững và an toàn cho người dùng.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
{benefits_markup}
        </div>
      </div>
    </section>
  );
}};
"""
    (src_dir / "components" / "Benefits.tsx").write_text(benefits_code, encoding="utf-8")

    # 10. Sinh Form Component (OrderForm.tsx hoặc LeadForm.tsx)
    if form_type == "order":
        prod_name = order_data.get("productName", "Dầu Gội Nhuộm Tóc Thảo Dược Rishiri Kombu (200ml)")
        sale_price = int(order_data.get("salePrice", 890000))
        reg_price = int(order_data.get("regularPrice", 1200000))
        gift_text = order_data.get("giftNote", "Tặng kèm 01 Lược gội tạo bọt & 01 Đôi găng tay chuyên dụng")
        promo_badge = order_data.get("promoBadge", "Ưu Đãi Đặc Biệt — Giảm 25%")

        form_code = f"""import React, {{ useState }} from 'react';
import {{ LPHub }} from '../lib/lphub';

export const OrderForm: React.FC = () => {{
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [note, setNote] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [selectedColor, setSelectedColor] = useState('Đen Tự Nhiên (Natural Black)');
  const [submitting, setSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [orderId, setOrderId] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const unitPrice = {sale_price};
  const regularPrice = {reg_price};
  const totalPrice = unitPrice * quantity;

  const handleSubmit = async (e: React.FormEvent) => {{
    e.preventDefault();
    if (!name || !phone || !address) {{
      setErrorMessage('Vui lòng điền đầy đủ Họ tên, Số điện thoại và Địa chỉ nhận hàng.');
      return;
    }}

    setSubmitting(true);
    setErrorMessage('');

    try {{
      const res = await LPHub.submitOrder({{
        formId: '{form_id}',
        customer: {{ name, phone, address, note }},
        items: [
          {{
            id: 'item-1',
            name: '{prod_name}',
            quantity: quantity,
            price: unitPrice,
            variant: selectedColor
          }}
        ],
        subtotal: totalPrice,
        total: totalPrice,
        currency: 'VND',
        paymentMethod: 'cod'
      }});

      if (res.success) {{
        setIsSuccess(true);
        setOrderId(res.id || res.data?.orderId || 'ORD-SUCCESS');
      }} else {{
        setErrorMessage(res.error?.message || 'Không thể tạo đơn hàng. Vui lòng kiểm tra và thử lại.');
      }}
    }} catch (err: any) {{
      setErrorMessage(err.message || 'Lỗi kết nối. Vui lòng bấm thử lại.');
    }} finally {{
      setSubmitting(false);
    }}
  }};

  if (isSuccess) {{
    return (
      <section id="order-section" className="py-20 bg-slate-900">
        <div className="max-w-2xl mx-auto px-4 text-center">
          <div className="p-10 rounded-3xl bg-slate-800/90 border border-teal-500/40 shadow-2xl space-y-4">
            <div className="w-16 h-16 bg-teal-500/20 text-teal-400 rounded-full flex items-center justify-center mx-auto text-3xl font-bold">
              ✓
            </div>
            <h3 className="text-2xl sm:text-3xl font-black text-white">ĐẶT HÀNG THÀNH CÔNG!</h3>
            <p className="text-slate-300">
              Cảm ơn <strong>{{name}}</strong>! Mã đơn hàng của bạn là: <span className="font-mono text-teal-400 font-bold">{{orderId}}</span>.
            </p>
            <p className="text-sm text-slate-400">
              Tông màu đã chọn: <strong className="text-teal-300">{{selectedColor}}</strong> ({{quantity}} chai).
            </p>
            <p className="text-sm text-slate-400">
              Chuyên viên tư vấn sẽ liên hệ qua số điện thoại <strong>{{phone}}</strong> để xác nhận và giao hàng tận nơi.
            </p>
            <button
              type="button"
              onClick={{() => setIsSuccess(false)}}
              className="mt-4 px-6 py-2.5 rounded-full text-sm font-semibold bg-slate-700 text-white hover:bg-slate-600 transition"
            >
              Đặt thêm đơn khác
            </button>
          </div>
        </div>
      </section>
    );
  }}

  return (
    <section id="order-section" className="py-20 bg-gradient-to-b from-slate-950 to-slate-900 relative">
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="p-8 sm:p-12 rounded-3xl bg-slate-800/80 border border-slate-700 shadow-2xl backdrop-blur">
          <div className="text-center max-w-xl mx-auto mb-8">
            <span className="px-3 py-1 text-xs font-bold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-wider">
              {promo_badge}
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-white mt-3">Đăng Ký Đặt Mua Chính Hãng</h2>
            <p className="text-slate-300 text-sm sm:text-base mt-2">
              Miễn phí vận chuyển toàn quốc — Kiểm tra hàng trước khi thanh toán (COD).
            </p>
          </div>

          <form onSubmit={{handleSubmit}} className="space-y-6">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60 flex flex-col sm:flex-row justify-between items-center gap-4">
              <div>
                <div className="font-bold text-white">{prod_name}</div>
                <div className="text-xs text-emerald-400">{gift_text}</div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center border border-slate-700 rounded-lg overflow-hidden">
                  <button
                    type="button"
                    onClick={{() => setQuantity(Math.max(1, quantity - 1))}}
                    className="px-3 py-1 bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >-</button>
                  <span className="px-4 py-1 font-bold text-white">{{quantity}}</span>
                  <button
                    type="button"
                    onClick={{() => setQuantity(quantity + 1)}}
                    className="px-3 py-1 bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >+</button>
                </div>
                <div className="text-right">
                  <div className="text-lg font-black text-emerald-400">{{totalPrice.toLocaleString('vi-VN')}} đ</div>
                  <div className="text-xs line-through text-slate-500">{{({reg_price} * quantity).toLocaleString('vi-VN')}} đ</div>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-2">Lựa chọn tông màu tóc *</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {{[
                  {{ name: 'Đen Tự Nhiên (Natural Black)', badge: 'Phù hợp tóc đen truyền thống' }},
                  {{ name: 'Nâu Đậm (Dark Brown)', badge: 'Thanh lịch, trẻ trung' }},
                  {{ name: 'Nâu Sáng (Light Brown)', badge: 'Sáng da, hiện đại' }}
                ].map((item) => (
                  <button
                    key={{item.name}}
                    type="button"
                    onClick={{() => setSelectedColor(item.name)}}
                    className={{`p-3.5 rounded-xl border text-left transition ${{
                      selectedColor === item.name
                        ? 'border-emerald-500 bg-emerald-500/10 text-white'
                        : 'border-slate-700 bg-slate-900/60 text-slate-300 hover:border-slate-600'
                    }}`}}
                  >
                    <div className="font-bold text-sm">{{item.name.split(' (')[0]}}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{{item.badge}}</div>
                  </button>
                ))}}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Họ và tên *</label>
                <input
                  type="text"
                  required
                  value={{name}}
                  onChange={{(e) => setName(e.target.value)}}
                  placeholder="Nguyễn Văn A"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-teal-400 transition"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Số điện thoại *</label>
                <input
                  type="tel"
                  required
                  value={{phone}}
                  onChange={{(e) => setPhone(e.target.value)}}
                  placeholder="0912345678"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-teal-400 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Địa chỉ giao hàng chi tiết *</label>
              <input
                type="text"
                required
                value={{address}}
                onChange={{(e) => setAddress(e.target.value)}}
                placeholder="Số nhà, tên đường, phường/xã, quận/huyện, tỉnh/thành"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-teal-400 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Ghi chú giao hàng (Tùy chọn)</label>
              <input
                type="text"
                value={{note}}
                onChange={{(e) => setNote(e.target.value)}}
                placeholder="Ví dụ: Giao giờ hành chính, gọi trước khi đến"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-teal-400 transition"
              />
            </div>

            {{errorMessage && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm font-medium">
                ⚠️ {{errorMessage}}
              </div>
            )}}

            <button
              type="submit"
              disabled={{submitting}}
              className="w-full py-4 rounded-xl text-lg font-bold text-white bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 shadow-xl shadow-teal-500/25 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {{submitting ? (
                <>
                  <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Đang xử lý đơn hàng...</span>
                </>
              ) : (
                <span>XÁC NHẬN ĐẶT HÀNG NGAY — {{totalPrice.toLocaleString('vi-VN')}} đ</span>
              )}}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}};
"""
        (src_dir / "components" / "OrderForm.tsx").write_text(form_code, encoding="utf-8")
    else:
        # LeadForm.tsx
        form_code = f"""import React, {{ useState }} from 'react';
import {{ LPHub }} from '../lib/lphub';

export const LeadForm: React.FC = () => {{
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [skinType, setSkinType] = useState('Da nhạy cảm');
  const [submitting, setSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {{
    e.preventDefault();
    if (!name || !phone) {{
      setErrorMessage('Vui lòng nhập Họ tên và Số điện thoại.');
      return;
    }}

    setSubmitting(true);
    setErrorMessage('');

    try {{
      const res = await LPHub.submitLead({{
        formId: '{form_id}',
        name,
        phone,
        email,
        data: {{ skinType }}
      }});

      if (res.success) {{
        setIsSuccess(true);
      }} else {{
        setErrorMessage(res.error?.message || 'Gửi thông tin thất bại. Vui lòng thử lại.');
      }}
    }} catch (err: any) {{
      setErrorMessage(err.message || 'Lỗi kết nối mạng. Vui lòng bấm thử lại.');
    }} finally {{
      setSubmitting(false);
    }}
  }};

  if (isSuccess) {{
    return (
      <section id="order-section" className="py-20 bg-slate-900">
        <div className="max-w-xl mx-auto px-4 text-center">
          <div className="p-8 rounded-3xl bg-slate-800 border border-purple-500/40 shadow-2xl space-y-4">
            <div className="w-14 h-14 bg-purple-500/20 text-purple-400 rounded-full flex items-center justify-center mx-auto text-2xl font-bold">
              ✓
            </div>
            <h3 className="text-2xl font-black text-white">ĐĂNG KÝ THÀNH CÔNG!</h3>
            <p className="text-slate-300">
              Cảm ơn <strong>{{name}}</strong>. Chuyên gia tư vấn sẽ liên hệ lại với bạn qua số <strong>{{phone}}</strong> trong ít phút.
            </p>
            <button
              type="button"
              onClick={{() => setIsSuccess(false)}}
              className="mt-4 px-6 py-2 rounded-full text-sm font-semibold bg-slate-700 text-white hover:bg-slate-600 transition"
            >
              Gửi thêm yêu cầu
            </button>
          </div>
        </div>
      </section>
    );
  }}

  return (
    <section id="order-section" className="py-20 bg-slate-950">
      <div className="max-w-2xl mx-auto px-4">
        <div className="p-8 sm:p-10 rounded-3xl bg-slate-800/80 border border-slate-700 shadow-2xl backdrop-blur">
          <div className="text-center mb-8">
            <h2 className="text-2xl sm:text-3xl font-black text-white">Đăng Ký Nhận Tư Vấn & Mẫu Thử</h2>
            <p className="text-slate-300 text-sm mt-2">Dành riêng cho 500 khách hàng đăng ký sớm nhất hôm nay.</p>
          </div>

          <form onSubmit={{handleSubmit}} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Họ và tên *</label>
              <input
                type="text"
                required
                value={{name}}
                onChange={{(e) => setName(e.target.value)}}
                placeholder="Nguyễn Thị Mai"
                className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-400"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Số điện thoại *</label>
              <input
                type="tel"
                required
                value={{phone}}
                onChange={{(e) => setPhone(e.target.value)}}
                placeholder="0912345678"
                className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-400"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Email (Tùy chọn)</label>
              <input
                type="email"
                value={{email}}
                onChange={{(e) => setEmail(e.target.value)}}
                placeholder="mai@gmail.com"
                className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-purple-400"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Tình trạng da hiện tại</label>
              <select
                value={{skinType}}
                onChange={{(e) => setSkinType(e.target.value)}}
                className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-purple-400"
              >
                <option value="Da nhạy cảm / Dễ kích ứng">Da nhạy cảm / Dễ kích ứng</option>
                <option value="Da mụn / Thâm sạm">Da mụn / Thâm sạm</option>
                <option value="Da khô / Mất nước">Da khô / Mất nước</option>
                <option value="Da lão hóa / Có nếp nhăn">Da lão hóa / Có nếp nhăn</option>
              </select>
            </div>

            {{errorMessage && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
                ⚠️ {{errorMessage}}
              </div>
            )}}

            <button
              type="submit"
              disabled={{submitting}}
              className="w-full py-3.5 rounded-xl text-base font-bold text-white bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 shadow-xl shadow-purple-500/25 transition disabled:opacity-50"
            >
              {{submitting ? 'Đang gửi...' : 'ĐĂNG KÝ NHẬN TƯ VẤN MIỄN PHÍ'}}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}};
"""
        (src_dir / "components" / "LeadForm.tsx").write_text(form_code, encoding="utf-8")

    # 11. Sinh Component Footer.tsx
    footer_code = f"""import React from 'react';

export const Footer: React.FC = () => {{
  return (
    <footer className="py-12 bg-slate-950 border-t border-slate-800 text-slate-400 text-xs sm:text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4 text-center sm:text-left sm:flex sm:justify-between sm:items-center sm:space-y-0">
        <div className="space-y-1">
          <div className="font-bold text-white">{footer_data.get("company", "Genki Fami Vietnam")}</div>
          <div>{footer_data.get("address", "Số 1 Sakura Center, Q. 1, TP.HCM")}</div>
          <div className="text-slate-500">{footer_data.get("license", "GPKD: 0314892182")}</div>
        </div>
        <div className="max-w-md text-slate-500 text-xs">
          {footer_data.get("disclaimer", "Sản phẩm này là thực phẩm bảo vệ sức khỏe, không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh.")}
        </div>
      </div>
    </footer>
  );
}};
"""
    (src_dir / "components" / "Footer.tsx").write_text(footer_code, encoding="utf-8")

    # 12. Sinh App.tsx và main.tsx
    form_component_name = "OrderForm" if form_type == "order" else "LeadForm"
    app_code = f"""import React, {{ useEffect }} from 'react';
import {{ Header }} from './components/Header';
import {{ Hero }} from './components/Hero';
import {{ Benefits }} from './components/Benefits';
import {{ {form_component_name} }} from './components/{form_component_name}';
import {{ Footer }} from './components/Footer';
import {{ LPHub }} from './lib/lphub';

export function App() {{
  useEffect(() => {{
    // Khởi tạo Landing Hub Client SDK v1.1.0
    LPHub.init({{
      projectId: '{project_id}',
      landingPageId: '{lp_id}',
      apiUrl: '{api_url}',
      autoPageView: true,
      debug: false
    }});
  }}, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-50 flex flex-col selection:bg-teal-500 selection:text-white">
      <Header />
      <main className="flex-grow">
        <Hero />
        <Benefits />
        <{form_component_name} />
      </main>
      <Footer />
    </div>
  );
}}

export default App;
"""
    (src_dir / "App.tsx").write_text(app_code, encoding="utf-8")

    main_tsx_code = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
    (src_dir / "main.tsx").write_text(main_tsx_code, encoding="utf-8")

    return {
        "success": True,
        "output_dir": str(out_path),
        "form_type": form_type,
        "files_created": [
            "package.json", "vite.config.ts", "tailwind.config.js", "postcss.config.js",
            "tsconfig.json", "index.html", "src/main.tsx", "src/App.tsx", "src/index.css",
            "src/lib/lphub.ts", "src/types/landing.ts", "src/components/Header.tsx",
            "src/components/Hero.tsx", "src/components/Benefits.tsx",
            f"src/components/{form_component_name}.tsx", "src/components/Footer.tsx"
        ]
    }

def main():
    parser = argparse.ArgumentParser(description="Landing Builder cho tao-landing-page")
    parser.add_argument("--design-json", required=True, help="File JSON chứa design data")
    parser.add_argument("--hub-config-json", required=True, help="File JSON chứa cấu hình Landing Hub")
    parser.add_argument("--target-dir", required=True, help="Thư mục xuất mã nguồn landing page")
    args = parser.parse_args()

    with open(args.design_json, "r", encoding="utf-8") as f:
        design_data = json.load(f)
    with open(args.hub_config_json, "r", encoding="utf-8") as f:
        hub_config = json.load(f)

    res = generate_landing_project(design_data, hub_config, args.target_dir)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
