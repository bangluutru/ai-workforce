#!/usr/bin/env python3
"""
Tự động lấy Page ID và Page Access Token vĩnh viễn (Expires: Never) cho các Fanpage thuộc Business Portfolio
và cập nhật vào file .env ở thư mục gốc của dự án.
Không bao giờ in raw access_token ra stdout.
"""
import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"

PAGES_TO_SYNC = [
    ("GENKIFAMI", "171721046035306", "Genki Fami"),
    ("NATTO", "466632146544306", "NATTO ICHOU"),
    ("TUYENDOITAC", "224650217395154", "Genki Fami - Tuyển Đối Tác"),
    ("DOTQUY", "601067016432327", "Tư vấn phòng ngừa đột quỵ, tai biến"),
    ("RISHIRI", "1343459025510588", "Rishiri - Dầu Gội Phủ Màu Không Chứa OXH"),
    ("FUKUSKE", "fukuske.vn", "Fukuske VN - Quần tất thế hệ mới"),
]


def get_user_token(cli_token: str = "") -> str:
    if cli_token:
        return cli_token.strip()
    env_tok = os.environ.get("FB_USER_ACCESS_TOKEN", "").strip()
    if env_tok:
        return env_tok
    if ENV_PATH.exists():
        m = re.search(r"^FB_USER_ACCESS_TOKEN=(.+)$", ENV_PATH.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    raise RuntimeError("Cần truyền --token hoặc thiết lập FB_USER_ACCESS_TOKEN trong .env / biến môi trường.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Đồng bộ Page ID và Page Access Token vào .env")
    parser.add_argument("--token", default="", help="Facebook User Access Token")
    args = parser.parse_args()

    user_tok = get_user_token(args.token)
    env_txt = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
    added = []

    for profile_key, lookup_id, fallback_name in PAGES_TO_SYNC:
        url = f"https://graph.facebook.com/v21.0/{lookup_id}?fields=id,name,access_token&access_token={user_tok}"
        try:
            with urllib.request.urlopen(url, timeout=8) as r:
                d = json.loads(r.read().decode())
                real_id = d.get("id", lookup_id)
                name = d.get("name", fallback_name)
                ptok = d.get("access_token", "")
                print(f"[OK] {profile_key}: id={real_id} | name={name} | token_present={bool(ptok)} (len={len(ptok)})")
                if ptok and f"FB_PAGE_{profile_key}_ID=" not in env_txt:
                    env_txt += (
                        f"\n# {name}\n"
                        f"FB_PAGE_{profile_key}_ID={real_id}\n"
                        f"FB_PAGE_{profile_key}_NAME=\"{name}\"\n"
                        f"FB_PAGE_{profile_key}_TOKEN={ptok}\n"
                    )
                    added.append((profile_key, real_id, name))
        except urllib.error.HTTPError as e:
            usage = e.headers.get("x-app-usage", "")
            print(f"[ERR] {profile_key} ({lookup_id}): HTTP {e.code} | x-app-usage={usage}")

    if added:
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write(env_txt)
        print(f"\n==> Đã lưu thêm {len(added)} Fanpage vào {ENV_PATH}: {[x[0] for x in added]}")
    else:
        print("\n==> Chưa có Fanpage mới nào được ghi thêm.")


if __name__ == "__main__":
    main()
