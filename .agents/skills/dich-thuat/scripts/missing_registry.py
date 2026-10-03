# -*- coding: utf-8 -*-
"""Sổ ghi các khối chữ nguồn mà bộ dựng PDF KHÔNG tìm được bản dịch (dùng chung giữa typst_overlay và flow_renderer).

Bản dịch được tra theo chuỗi nguồn; agent không thể đoán pipeline sẽ cắt đoạn thế nào → luôn chạy 2 lượt:
lượt 1 ghi <output>.missing.json (đúng những chuỗi pipeline cần), agent dịch chính xác các chuỗi đó, lượt 2 khớp 100%."""
MISSING = []


def record(text):
    t = (text or "").strip()
    if t and t not in MISSING:
        MISSING.append(t)
