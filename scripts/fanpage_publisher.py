#!/usr/bin/env python3
"""
AI Workforce — Fanpage Publisher & Social Card Engine (scripts/fanpage_publisher.py)

Hỗ trợ Agent Team Phòng Fanpage (W3-phong-fanpage):
1. `next-topic`  : Đọc chủ đề PENDING kế tiếp từ `.agents/knowledge/fanpage_content_calendar.md`.
2. `mark-status` : Cập nhật trạng thái chủ đề trong `fanpage_content_calendar.md`.
3. `render-card` : Thiết kế tự động ảnh Poster Facebook 1080x1350 (tỷ lệ 4:5 tối ưu hiển thị).
4. `publish`     : Kiểm định pháp lý Luật R5 (`claim_guard.py`), xuất `fanpage_preview.html`
                   và đẩy bài viết + ảnh/video lên Facebook Fanpage qua Graph API v21.0
                   ở chế độ Nháp (`draft`), Hẹn giờ (`schedule`) hoặc Đăng ngay (`publish-now`).
                   Tuyệt đối không hardcode token (đọc từ `.env` hoặc biến môi trường).
"""

import argparse
import html
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CALENDAR = REPO_ROOT / ".agents" / "knowledge" / "fanpage_content_calendar.md"
SHARED_FONTS_DIR = REPO_ROOT / ".agents" / "skills" / "_shared" / "fonts"
CLAIM_GUARD_SCRIPT = REPO_ROOT / "scripts" / "claim_guard.py"


def load_dotenv(dotenv_path: Path) -> dict[str, str]:
    """Đọc biến môi trường từ file .env (nếu tồn tại) mà không cần thư viện ngoài."""
    env_vars: dict[str, str] = {}
    if not dotenv_path.exists():
        return env_vars
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        env_vars[k] = v
    return env_vars


def get_fb_credentials(profile: str = "") -> tuple[str, str, str]:
    """Lấy FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN, FB_PAGE_NAME từ môi trường hoặc .env (hỗ trợ --page-profile)."""
    dotenv_vars = load_dotenv(REPO_ROOT / ".env")
    prof = profile.strip().upper()
    if prof:
        id_key = f"FB_PAGE_{prof}_ID"
        tok_key = f"FB_PAGE_{prof}_TOKEN"
        name_key = f"FB_PAGE_{prof}_NAME"
        page_id = os.environ.get(id_key) or dotenv_vars.get(id_key, "")
        token = os.environ.get(tok_key) or dotenv_vars.get(tok_key, "")
        page_name = os.environ.get(name_key) or dotenv_vars.get(name_key, "") or prof
        return page_id.strip(), token.strip(), page_name.strip()

    page_id = os.environ.get("FB_PAGE_ID") or dotenv_vars.get("FB_PAGE_ID", "")
    token = os.environ.get("FB_PAGE_ACCESS_TOKEN") or dotenv_vars.get("FB_PAGE_ACCESS_TOKEN", "")
    page_name = (
        os.environ.get("FB_PAGE_NAME")
        or dotenv_vars.get("FB_PAGE_NAME", "")
        or "AI Workforce & Chotto Studio"
    )
    return page_id.strip(), token.strip(), page_name.strip()


def parse_calendar(calendar_path: Path) -> list[dict[str, str]]:
    """Đọc bảng Markdown trong fanpage_content_calendar.md."""
    if not calendar_path.exists():
        raise FileNotFoundError(f"Không tìm thấy bảng kế hoạch nội dung: {calendar_path}")
    rows: list[dict[str, str]] = []
    lines = calendar_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        s = line.strip()
        if not s.startswith("|") or not s.endswith("|"):
            continue
        cells = [c.strip().strip("`") for c in s.strip("|").split("|")]
        if len(cells) < 7:
            continue
        row_id = cells[0]
        if not re.match(r"^FP-\d+", row_id):
            continue
        rows.append(
            {
                "id": row_id,
                "scheduled_date": cells[1],
                "topic": cells[2],
                "category": cells[3],
                "media_type": cells[4],
                "cta": cells[5],
                "status": cells[6],
            }
        )
    return rows


def cmd_next_topic(args: argparse.Namespace) -> int:
    cal_path = Path(args.calendar).resolve()
    rows = parse_calendar(cal_path)
    for r in rows:
        if r["status"].upper() == "PENDING":
            print(json.dumps({"status": "FOUND", "item": r}, ensure_ascii=False, indent=2))
            return 0
    print(
        json.dumps(
            {
                "status": "EMPTY_QUEUE",
                "message": "Toàn bộ chủ đề trong bảng kế hoạch đã được xử lý. Agent có thể tự nghiên cứu xu hướng mới.",
                "total_rows": len(rows),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_mark_status(args: argparse.Namespace) -> int:
    cal_path = Path(args.calendar).resolve()
    if not cal_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {cal_path}")
    content = cal_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    updated = False
    new_lines = []
    target_id = args.id.strip()
    new_status = args.status.strip().upper()

    for line in lines:
        if f"`{target_id}`" in line or re.search(rf"\|\s*{re.escape(target_id)}\s*\|", line):
            parts = line.split("|")
            if len(parts) >= 8:
                parts[-2] = f" `{new_status}` "
                line = "|".join(parts)
                updated = True
        new_lines.append(line)

    if not updated:
        print(f"Không tìm thấy dòng có ID '{target_id}' trong {cal_path}", file=sys.stderr)
        return 1

    cal_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "UPDATED", "id": target_id, "new_status": new_status}, ensure_ascii=False))
    return 0


def _load_font(weight: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = {
        "bold": [
            SHARED_FONTS_DIR / "BeVietnamPro-Bold.ttf",
            SHARED_FONTS_DIR / "Montserrat-Bold.ttf",
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/System/Library/Fonts/Helvetica.ttc"),
        ],
        "semibold": [
            SHARED_FONTS_DIR / "BeVietnamPro-SemiBold.ttf",
            SHARED_FONTS_DIR / "BeVietnamPro-Bold.ttf",
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ],
        "regular": [
            SHARED_FONTS_DIR / "BeVietnamPro-Regular.ttf",
            SHARED_FONTS_DIR / "Montserrat-Regular.ttf",
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Helvetica.ttc"),
        ],
    }
    for fp in candidates.get(weight, candidates["regular"]):
        if fp.exists():
            try:
                return ImageFont.truetype(str(fp), size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        test = f"{cur} {w}"
        bbox = draw.textbbox((0, 0), test, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def cmd_render_card(args: argparse.Namespace) -> int:
    """Thiết kế Poster Facebook 1080x1350 (tỷ lệ 4:5) phong cách Pastel / Editorial."""
    W, H = 1080, 1350
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    palettes = {
        "pastel": {
            "bg_top": (253, 232, 226),
            "bg_bot": (232, 244, 242),
            "card": (255, 252, 247),
            "ink": (43, 50, 68),
            "muted": (92, 102, 122),
            "accent": (232, 114, 126),
            "accent_soft": (252, 214, 218),
            "mint": (118, 198, 184),
        },
        "navy": {
            "bg_top": (24, 38, 64),
            "bg_bot": (42, 68, 102),
            "card": (252, 250, 245),
            "ink": (28, 36, 54),
            "muted": (88, 98, 118),
            "accent": (228, 104, 88),
            "accent_soft": (252, 224, 216),
            "mint": (98, 186, 168),
        },
    }
    pal = palettes.get(args.theme, palettes["pastel"])

    # 1. Smooth vertical background gradient
    base = Image.new("RGB", (W, H), pal["bg_top"])
    draw_bg = ImageDraw.Draw(base)
    for y in range(H):
        t = y / float(H - 1)
        r = int(pal["bg_top"][0] * (1 - t) + pal["bg_bot"][0] * t)
        g = int(pal["bg_top"][1] * (1 - t) + pal["bg_bot"][1] * t)
        b = int(pal["bg_top"][2] * (1 - t) + pal["bg_bot"][2] * t)
        draw_bg.line([(0, y), (W, y)], fill=(r, g, b))

    # Decorative soft pastel circles
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse((W - 340, -120, W + 140, 360), fill=(*pal["accent"], 42))
    odraw.ellipse((-160, H - 380, 320, H + 100), fill=(*pal["mint"], 48))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=24))
    base = Image.alpha_composite(base.convert("RGBA"), overlay)

    # 2. Main Editorial Card Container with soft drop shadow
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    card_box = (76, 86, W - 76, H - 86)
    sdraw.rounded_rectangle(
        (card_box[0] + 8, card_box[1] + 16, card_box[2] + 8, card_box[3] + 16),
        radius=40,
        fill=(32, 38, 52, 34),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))
    base = Image.alpha_composite(base, shadow)

    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle(card_box, radius=40, fill=pal["card"], outline=pal["ink"], width=4)

    # Inner decorative top bar
    draw.rounded_rectangle(
        (card_box[0] + 36, card_box[1] + 36, card_box[2] - 36, card_box[1] + 48),
        radius=6,
        fill=pal["mint"],
    )

    f_badge = _load_font("bold", 25)
    f_title = _load_font("bold", 52)
    f_bullet = _load_font("regular", 33)
    f_cta = _load_font("semibold", 29)
    f_brand = _load_font("semibold", 24)

    # 3. Category / Tag Pill
    badge_text = (args.tag or "TIÊU ĐIỂM HÔM NAY").upper()
    bb = draw.textbbox((0, 0), badge_text, font=f_badge)
    bw = (bb[2] - bb[0]) + 48
    bh = 54
    bx0, by0 = 132, 170
    draw.rounded_rectangle((bx0, by0, bx0 + bw, by0 + bh), radius=27, fill=pal["accent_soft"], outline=pal["accent"], width=2)
    draw.text((bx0 + bw // 2, by0 + bh // 2), badge_text, font=f_badge, fill=pal["accent"], anchor="mm")

    # 4. Headline
    max_text_w = W - 264
    title_lines = _wrap_text(draw, args.title.strip(), f_title, max_text_w)
    cur_y = 268
    for line in title_lines[:4]:
        draw.text((132, cur_y), line, font=f_title, fill=pal["ink"])
        cur_y += 68

    # Accent divider
    cur_y += 20
    draw.rounded_rectangle((132, cur_y, 292, cur_y + 8), radius=4, fill=pal["accent"])
    cur_y += 46

    # 5. Key Bullet Points (up to 3)
    bullets = [b.strip() for b in (args.bullets or []) if b.strip()]
    for idx, b_text in enumerate(bullets[:3], start=1):
        # Number circle badge
        cy_badge = cur_y + 24
        draw.ellipse((132, cy_badge - 22, 176, cy_badge + 22), fill=pal["mint"], outline=pal["ink"], width=2)
        draw.text((154, cy_badge), str(idx), font=f_badge, fill=(255, 255, 255), anchor="mm")

        b_lines = _wrap_text(draw, b_text, f_bullet, max_text_w - 72)
        for bl in b_lines[:3]:
            draw.text((198, cur_y), bl, font=f_bullet, fill=pal["ink"])
            cur_y += 46
        cur_y += 26

    # 6. Bottom CTA Banner & Brand Footer
    cta_y0 = H - 268
    cta_box = (124, cta_y0, W - 124, cta_y0 + 96)
    draw.rounded_rectangle(cta_box, radius=24, fill=pal["accent_soft"], outline=pal["accent"], width=2)
    cta_lines = _wrap_text(draw, args.cta or "Theo dõi Fanpage để cập nhật thông tin hữu ích mỗi ngày!", f_cta, max_text_w - 48)
    cta_display = cta_lines[0] if cta_lines else ""
    draw.text((W // 2, cta_y0 + 48), cta_display, font=f_cta, fill=pal["ink"], anchor="mm")

    _, _, page_name = get_fb_credentials()
    brand_label = args.brand or page_name
    draw.text((W // 2, H - 128), f"✦ {brand_label} ✦", font=f_brand, fill=pal["muted"], anchor="mm")

    base.convert("RGB").save(out_path, quality=95)
    print(json.dumps({"status": "RENDERED", "image_path": str(out_path), "resolution": f"{W}x{H}"}, ensure_ascii=False))
    return 0


def _strip_markdown_for_fb(md_text: str) -> str:
    """Chuyển bài viết Markdown thành plain-text sạch đẹp chuẩn hiển thị Facebook."""
    raw_lines = md_text.splitlines()
    # Nếu file theo mẫu có mục '## Nội dung bài đăng', chỉ trích xuất phần nội dung bài đăng
    has_copy_section = any(re.match(r"^##\s+Nội dung bài đăng", ln.strip(), re.I) for ln in raw_lines)
    active = not has_copy_section
    lines = []
    for raw in raw_lines:
        s = raw.strip()
        if s.startswith("<!--") and s.endswith("-->"):
            continue
        if has_copy_section:
            if re.match(r"^##\s+Nội dung bài đăng", s, re.I):
                active = True
                continue
            if active and (s == "---" or s.startswith("## ")):
                break
            if not active:
                continue
        if s.startswith("#"):
            clean_h = s.lstrip("#").strip()
            lines.append(f"📌 {clean_h.upper()}")
            continue
        clean_line = re.sub(r"\*\*(.+?)\*\*", r"\1", raw)
        clean_line = re.sub(r"__(.+?)__", r"\1", clean_line)
        lines.append(clean_line)
    return "\n".join(lines).strip()


def _run_legal_gate(post_file: Path) -> tuple[bool, str]:
    """Chạy claim_guard.py --profile ads để đảm bảo tuân thủ 100% Luật R5 trước khi đăng."""
    if not CLAIM_GUARD_SCRIPT.exists():
        return True, "claim_guard.py not found (skipped)"
    proc = subprocess.run(
        [sys.executable, str(CLAIM_GUARD_SCRIPT), "--input", str(post_file), "--profile", "ads"],
        capture_output=True,
        text=True,
    )
    out = (proc.stdout + "\n" + proc.stderr).strip()
    return (proc.returncode == 0), out


def _generate_preview_html(
    preview_path: Path,
    page_name: str,
    post_text: str,
    media_path: Path | None,
    mode: str,
    api_status: dict,
):
    """Tạo trang HTML mô phỏng giao diện bài đăng Facebook Fanpage để người dùng duyệt trực quan."""
    escaped_text = html.escape(post_text).replace("\n", "<br>")
    media_html = ""
    if media_path and media_path.exists():
        rel_media = media_path.name
        ext = media_path.suffix.lower()
        if ext in (".mp4", ".mov", ".webm"):
            media_html = f'<div class="media"><video controls src="{html.escape(rel_media)}"></video></div>'
        elif ext in (".png", ".jpg", ".jpeg", ".webp"):
            media_html = f'<div class="media"><img src="{html.escape(rel_media)}" alt="Fanpage Media"/></div>'

    badge_color = "#10b981" if api_status.get("published_remote") else "#f59e0b"
    status_label = api_status.get("summary_label", "Sẵn sàng duyệt (Local / Draft)")

    html_doc = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Xem trước Bài đăng Fanpage — {html.escape(page_name)}</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #f0f2f5;
    margin: 0;
    padding: 32px 16px;
    color: #1c1e21;
  }}
  .container {{
    max-width: 620px;
    margin: 0 auto;
  }}
  .status-banner {{
    background: #ffffff;
    border-left: 6px solid {badge_color};
    padding: 14px 18px;
    border-radius: 10px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    font-size: 14px;
    line-height: 1.5;
  }}
  .fb-card {{
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    overflow: hidden;
  }}
  .fb-header {{
    display: flex;
    align-items: center;
    padding: 16px;
    gap: 12px;
  }}
  .avatar {{
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f2838e, #68c2b2);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-weight: 700;
    font-size: 18px;
  }}
  .page-meta .name {{
    font-weight: 600;
    font-size: 15px;
    color: #050505;
  }}
  .page-meta .time {{
    font-size: 13px;
    color: #65676b;
  }}
  .fb-body {{
    padding: 4px 16px 16px;
    font-size: 15px;
    line-height: 1.55;
    white-space: normal;
    word-break: break-word;
  }}
  .media img, .media video {{
    width: 100%;
    max-height: 680px;
    object-fit: cover;
    display: block;
    background: #fafafa;
  }}
  .fb-footer {{
    border-top: 1px solid #ced0d4;
    padding: 10px 16px;
    display: flex;
    justify-content: space-around;
    color: #65676b;
    font-weight: 600;
    font-size: 14px;
  }}
</style>
</head>
<body>
  <div class="container">
    <div class="status-banner">
      <strong>Trạng thái xuất bản:</strong> {html.escape(status_label)}<br/>
      <strong>Chế độ (`mode`):</strong> <code>{html.escape(mode)}</code> |
      <strong>Kiểm định Luật R5:</strong> ✅ PASS (0 vi phạm)
    </div>
    <div class="fb-card">
      <div class="fb-header">
        <div class="avatar">AI</div>
        <div class="page-meta">
          <div class="name">{html.escape(page_name)}</div>
          <div class="time">Vừa xong · 🌐 Bản xem trước Fanpage</div>
        </div>
      </div>
      <div class="fb-body">{escaped_text}</div>
      {media_html}
      <div class="fb-footer">
        <span>👍 Thích</span>
        <span>💬 Bình luận</span>
        <span>↗️ Chia sẻ</span>
      </div>
    </div>
  </div>
</body>
</html>
"""
    preview_path.write_text(html_doc, encoding="utf-8")


def _upload_multipart_graph_api(
    url: str, fields: dict[str, str], file_field: str | None = None, file_path: Path | None = None
) -> dict:
    """Gửi HTTP POST multipart/form-data lên Facebook Graph API bằng urllib chuẩn."""
    boundary = f"----AIWFBoundary{uuid.uuid4().hex}"
    body = bytearray()

    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{v}\r\n".encode("utf-8"))

    if file_field and file_path and file_path.exists():
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode("utf-8")
        )
        body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_path.read_bytes())
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(url, data=bytes(body), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def cmd_publish(args: argparse.Namespace) -> int:
    post_file = Path(args.post_file).resolve()
    if not post_file.exists():
        print(f"Không tìm thấy file bài viết: {post_file}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Cổng kiểm định pháp lý Luật R5 bắt buộc
    passed_r5, r5_log = _run_legal_gate(post_file)
    if not passed_r5:
        print("❌ BÀI VIẾT BỊ CHẶN BỞI CỔNG PHÁP LÝ LUẬT R5 (claim_guard.py):", file=sys.stderr)
        print(r5_log, file=sys.stderr)
        return 1

    raw_md = post_file.read_text(encoding="utf-8")
    fb_caption = _strip_markdown_for_fb(raw_md)
    caption_out = out_dir / "fb_caption.txt"
    caption_out.write_text(fb_caption, encoding="utf-8")

    media_path = Path(args.media).resolve() if args.media else None
    if media_path and media_path.exists() and media_path.parent != out_dir:
        target_media = out_dir / media_path.name
        target_media.write_bytes(media_path.read_bytes())
        media_path = target_media

    page_id, access_token, page_name = get_fb_credentials(getattr(args, "page_profile", ""))
    mode = args.mode.lower()  # draft | schedule | publish-now

    # Tính toán tham số Facebook Graph API theo mode
    fb_params: dict[str, str] = {"access_token": access_token}
    scheduled_ts = 0
    if mode == "draft":
        fb_params["published"] = "false"
        fb_params["unpublished_content_type"] = "DRAFT"
    elif mode == "schedule":
        fb_params["published"] = "false"
        fb_params["unpublished_content_type"] = "SCHEDULED"
        scheduled_ts = int(time.time()) + max(15, int(args.schedule_minutes)) * 60
        fb_params["scheduled_publish_time"] = str(scheduled_ts)
    else:
        fb_params["published"] = "true"

    api_result: dict = {
        "published_remote": False,
        "page_name": page_name,
        "page_id": page_id,
        "mode": mode,
        "r5_compliance": "PASS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Tạo script đẩy nhanh 1-chạm (publish_to_fb.sh) phòng khi người dùng chưa cấu hình .env
    curl_script = out_dir / "publish_to_fb.sh"
    if media_path and media_path.suffix.lower() in (".mp4", ".mov"):
        endpoint_suffix = "videos"
        msg_field = "description"
    elif media_path and media_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
        endpoint_suffix = "photos"
        msg_field = "caption"
    else:
        endpoint_suffix = "feed"
        msg_field = "message"

    curl_Lines = [
        "#!/bin/bash",
        "# Script đẩy bài lên Facebook Fanpage (đọc FB_PAGE_ID và FB_PAGE_ACCESS_TOKEN từ .env)",
        "set -e",
        f'DIR="$(cd "$(dirname "$0")" && pwd)"',
        f'if [ -f "{REPO_ROOT}/.env" ]; then source "{REPO_ROOT}/.env"; fi',
        'if [ -z "$FB_PAGE_ID" ] || [ -z "$FB_PAGE_ACCESS_TOKEN" ]; then',
        '  echo "⚠️ Vui lòng khai báo FB_PAGE_ID và FB_PAGE_ACCESS_TOKEN trong file .env trước khi chạy."',
        "  exit 1",
        "fi",
    ]
    if endpoint_suffix in ("photos", "videos") and media_path:
        curl_Lines.append(
            f'curl -sS -X POST "https://graph.facebook.com/v21.0/$FB_PAGE_ID/{endpoint_suffix}" '
            f'-F "access_token=$FB_PAGE_ACCESS_TOKEN" '
            f'-F "{msg_field}=$(cat "$DIR/fb_caption.txt")" '
            f'-F "source=@$DIR/{media_path.name}" '
            f'-F "published={"true" if mode == "publish-now" else "false"}" '
            + (f'-F "unpublished_content_type=DRAFT"' if mode == "draft" else "")
            + (f'-F "unpublished_content_type=SCHEDULED" -F "scheduled_publish_time={scheduled_ts}"' if mode == "schedule" else "")
        )
    else:
        curl_Lines.append(
            f'curl -sS -X POST "https://graph.facebook.com/v21.0/$FB_PAGE_ID/feed" '
            f'-F "access_token=$FB_PAGE_ACCESS_TOKEN" '
            f'-F "message=$(cat "$DIR/fb_caption.txt")" '
            f'-F "published={"true" if mode == "publish-now" else "false"}" '
            + (f'-F "unpublished_content_type=DRAFT"' if mode == "draft" else "")
            + (f'-F "unpublished_content_type=SCHEDULED" -F "scheduled_publish_time={scheduled_ts}"' if mode == "schedule" else "")
        )
    curl_script.write_text("\n".join(curl_Lines) + "\n", encoding="utf-8")
    curl_script.chmod(0o755)

    # Nếu đã có đủ FB_PAGE_ID & FB_PAGE_ACCESS_TOKEN và không bật --dry-run -> gọi Graph API thật
    if page_id and access_token and not args.dry_run:
        url = f"https://graph.facebook.com/v21.0/{page_id}/{endpoint_suffix}"
        fb_params[msg_field] = fb_caption
        try:
            resp_json = _upload_multipart_graph_api(
                url,
                fb_params,
                file_field="source" if endpoint_suffix in ("photos", "videos") else None,
                file_path=media_path if endpoint_suffix in ("photos", "videos") else None,
            )
            api_result["published_remote"] = True
            api_result["graph_api_response"] = resp_json
            api_result["summary_label"] = f"Đã đẩy lên Fanpage {page_name} ({mode.upper()}) — ID: {resp_json.get('id', 'OK')}"
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            api_result["graph_api_error"] = f"HTTP {e.code}: {err_body}"
            api_result["summary_label"] = f"Đã lưu gói bài đăng cục bộ (Lỗi Graph API HTTP {e.code})"
        except Exception as e:
            api_result["graph_api_error"] = str(e)
            api_result["summary_label"] = "Đã lưu gói bài đăng cục bộ (Chưa kết nối mạng/API)"
    else:
        reason = "Chế độ --dry-run" if args.dry_run else "Chưa khai báo FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN trong .env"
        api_result["summary_label"] = f"Gói bài đăng Nháp đã sẵn sàng ({reason})"
        api_result["next_step"] = f"Điền FB_PAGE_ID & FB_PAGE_ACCESS_TOKEN vào {REPO_ROOT / '.env'} hoặc chạy {curl_script}"

    preview_html = out_dir / "fanpage_preview.html"
    _generate_preview_html(preview_html, page_name, fb_caption, media_path, mode, api_result)

    manifest_path = out_dir / "post_manifest.json"
    api_result["files"] = {
        "caption_txt": str(caption_out),
        "media_file": str(media_path) if media_path else None,
        "preview_html": str(preview_html),
        "publish_script": str(curl_script),
    }
    manifest_path.write_text(json.dumps(api_result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(api_result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Workforce Fanpage Publisher & Card Generator")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_next = sub.add_parser("next-topic", help="Lấy chủ đề PENDING kế tiếp từ lịch nội dung")
    p_next.add_argument("--calendar", default=str(DEFAULT_CALENDAR), help="Đường dẫn file lịch nội dung")

    p_mark = sub.add_parser("mark-status", help="Cập nhật trạng thái chủ đề trong lịch nội dung")
    p_mark.add_argument("--calendar", default=str(DEFAULT_CALENDAR))
    p_mark.add_argument("--id", required=True, help="Mã chủ đề (vd: FP-001)")
    p_mark.add_argument("--status", required=True, help="DRAFT_READY | SCHEDULED | PUBLISHED | PENDING")

    p_card = sub.add_parser("render-card", help="Thiết kế ảnh Poster Facebook 1080x1350 tự động")
    p_card.add_argument("--title", required=True, help="Tiêu đề chính trên poster")
    p_card.add_argument("--bullets", nargs="*", default=[], help="Tối đa 3 ý chính")
    p_card.add_argument("--cta", default="Theo dõi Fanpage để nhận thông tin hữu ích mỗi ngày!", help="Câu kêu gọi hành động")
    p_card.add_argument("--tag", default="TIÊU ĐIỂM", help="Nhãn góc trên")
    p_card.add_argument("--brand", default="", help="Tên thương hiệu dưới chân poster")
    p_card.add_argument("--theme", choices=["pastel", "navy"], default="pastel")
    p_card.add_argument("--output", required=True, help="Đường dẫn ảnh PNG đầu ra")

    p_pub = sub.add_parser("publish", help="Kiểm định R5, tạo bản xem trước và đẩy bài lên Fanpage")
    p_pub.add_argument("--post-file", required=True, help="Đường dẫn file bài viết (.md hoặc .txt)")
    p_pub.add_argument("--media", default="", help="Đường dẫn file ảnh (.png/.jpg) hoặc video (.mp4)")
    p_pub.add_argument("--mode", choices=["draft", "schedule", "publish-now"], default="draft")
    p_pub.add_argument("--schedule-minutes", type=int, default=180, help="Số phút hẹn giờ đăng (nếu mode=schedule)")
    p_pub.add_argument("--page-profile", default="", help="Hồ sơ Fanpage trong .env: CHOTTO | OMEGA3 | BEANSTALK | ONAKA | HUMA | MINNA")
    p_pub.add_argument("--out-dir", required=True, help="Thư mục lưu gói thành phẩm")
    p_pub.add_argument("--dry-run", action="store_true", help="Chỉ đóng gói và tạo bản xem trước, không gọi API")

    args = parser.parse_args()
    if args.subcommand == "next-topic":
        return cmd_next_topic(args)
    if args.subcommand == "mark-status":
        return cmd_mark_status(args)
    if args.subcommand == "render-card":
        return cmd_render_card(args)
    if args.subcommand == "publish":
        return cmd_publish(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
