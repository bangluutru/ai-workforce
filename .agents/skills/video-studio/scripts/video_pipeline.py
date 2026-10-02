#!/usr/bin/env python3
"""
AI WORKFORCE — Video Studio v2: kịch bản JSON (AGENT viết) → MP4 hoàn chỉnh.

  1. Giọng đọc: VieNeu-TTS 48 kHz offline cho tiếng Việt (long-tieng/dub_engine), Whisper nghe lại từng câu,
     đọc lại câu sai. Dòng thời gian được dựng theo độ dài lời đọc thật.
  2. Hình: file người dùng → Pexels/Pixabay (nếu có key) → ảnh CÓ GIẤY PHÉP từ Wikimedia Commons/Openverse
     (không cần key) + chuyển động Ken Burns. YouTube chỉ khi --allow-youtube (giấy phép không xác minh được).
  3. Nhạc: thư viện CC BY 4.0 (Kevin MacLeod) theo mood, hạ còn 25% khi có lời, chuẩn hoá −16 LUFS.
  4. Phụ đề: ngắt câu + ASS của phu-de (Be Vietnam Pro, hộp bo góc, 9:16 tự chỉnh), tiêu đề + caption cảnh.
  5. Bằng chứng: <tên>_review.jpg (1 khung/cảnh để NHÌN), <tên>_credits.txt (ghi công bắt buộc), <tên>_report.json.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILLS = SCRIPT_DIR.parent.parent
PHUDE = SKILLS / "phu-de" / "scripts"
for p in (SCRIPT_DIR, SKILLS / "long-tieng" / "scripts", PHUDE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Kịch bản MẪU cố định — chỉ dùng với --allow-template để thử máy. Video thật: agent viết --script.
PRESET_SCRIPTS = {
    "nhat_ban": {
        "title_top": "Cuộc Sống Tươi Đẹp Ở Nhật Bản",
        "title_sub": "日本の美しい暮らし",
        "mood": "traditional",
        "scenes": [
            {
                "id": "s01",
                "vi": "Hoa anh đào bay nhẹ trong gió, mùa xuân dịu dàng ghé thăm từng góc phố.",
                "jp": "桜の花が風に舞い、春が静かに訪れる。",
                "keywords": ["cherry blossom japan", "sakura spring tokyo", "japanese garden spring"],
            },
            {
                "id": "s02",
                "vi": "Ánh nắng ban mai tinh khôi ôm trọn những ngôi chùa cổ kính trầm mặc tại Kyoto.",
                "jp": "朝の光が京都の寺院を優しく包む。",
                "keywords": ["kyoto temple morning", "pagoda japan sunrise", "kyoto bamboo forest"],
            },
            {
                "id": "s03",
                "vi": "Đoàn tàu Shinkansen hiện đại lướt êm ái trước đỉnh núi Phú Sĩ hùng vĩ.",
                "jp": "新幹線が富士山の前を颯爽と駆け抜ける。",
                "keywords": ["shinkansen mount fuji", "bullet train fuji", "mount fuji japan"],
            },
            {
                "id": "s04",
                "vi": "Phố phường Tokyo lung linh ánh đèn neon, luôn tràn đầy năng lượng ngày và đêm.",
                "jp": "東京の街は昼も夜も活気に満ちている。",
                "keywords": ["tokyo shibuya crossing night", "tokyo street neon", "shinjuku city lights"],
            },
            {
                "id": "s05",
                "vi": "Từng bát mì ramen nóng hổi và nghệ thuật ẩm thực tinh tế làm say lòng du khách.",
                "jp": "職人が作る温かいラーメンと繊細な日本料理。",
                "keywords": ["ramen cooking japan", "japanese food preparation", "sushi chef craft"],
            },
            {
                "id": "s06",
                "vi": "Hơi nước ấm áp từ suối nước nóng onsen giữa thung lũng tuyết thanh bình.",
                "jp": "温泉の湯気が山の澄んだ空気と交わる。",
                "keywords": ["onsen hot spring japan", "snow onsen winter", "japan mountain steam"],
            },
            {
                "id": "s07",
                "vi": "Những chú nai thân thiện tự do dạo bước dưới bóng cây xanh mát tại Nara.",
                "jp": "鹿が奈良の公園を自由に歩き回る。",
                "keywords": ["nara deer park", "japan deer bowing", "nara temple park"],
            },
            {
                "id": "s08",
                "vi": "Vẻ đẹp bốn mùa của xứ sở mặt trời mọc luôn đọng lại sâu sắc trong lòng mỗi người.",
                "jp": "日本の四季の美しさは、いつまでも心に残り続ける。",
                "keywords": ["japan torii gate sunset", "japan landscape autumn", "fuji sunset aerial"],
            }
        ]
    },
    "viet_nam": {
        "title_top": "Việt Nam — Vẻ Đẹp Bất Tận",
        "title_sub": "Hello Vietnam • Đất Nước & Con Người",
        "mood": "peaceful",
        "scenes": [
            {
                "id": "s01",
                "vi": "Chào mừng bạn đến với Việt Nam, dải đất hình chữ S tươi đẹp bên bờ Biển Đông.",
                "jp": "東海のほとりに広がる美しい国、ベトナムへようこそ。",
                "keywords": ["vietnam coastline aerial", "vietnam aerial landscape", "vietnam scenic mountains"],
            },
            {
                "id": "s02",
                "vi": "Vịnh Hạ Long kỳ vĩ với hàng nghìn hòn đảo đá vôi xanh biếc nhấp nhô giữa làn sương sớm.",
                "jp": "朝霧の中に無数の島々が浮かぶ、雄大なハロン湾。",
                "keywords": ["halong bay aerial", "vietnam limestone islands", "halong bay cruise"],
            },
            {
                "id": "s03",
                "vi": "Những thửa ruộng bậc thang Mù Cang Chải uốn lượn như dải lụa vàng giữa mây ngàn Tây Bắc.",
                "jp": "黄金色の絹のように山々を彩る、ムーカンチャイの棚田。",
                "keywords": ["sapa rice fields", "mu cang chai rice terraces", "vietnam terraced fields"],
            },
            {
                "id": "s04",
                "vi": "Thủ đô Hà Nội nghìn năm văn hiến, bình yên bên Hồ Gươm và từng góc phố cổ rêu phong.",
                "jp": "ホアンキエム湖の静けさと千年の歴史が息づく首都ハノイ。",
                "keywords": ["hanoi old quarter", "hanoi lake tower", "vietnam hanoi street"],
            },
            {
                "id": "s05",
                "vi": "Phố cổ Hội An lung linh sắc màu đèn lồng soi bóng dòng sông Hoài thơ mộng.",
                "jp": "ランタンの灯りが川面に優しく揺れる古都ホイアン。",
                "keywords": ["hoi an ancient town", "hoi an lanterns", "hoi an night river"],
            },
            {
                "id": "s06",
                "vi": "Sông nước miền Tây hiền hòa với những khu chợ nổi rộn rã và miệt vườn cây trái sum suê.",
                "jp": "水上マーケットの活気と豊かな果樹園が広がるメコンデルタ。",
                "keywords": ["mekong delta boat", "vietnam river floating market", "vietnam delta boat"],
            },
            {
                "id": "s07",
                "vi": "Nụ cười hồn hậu và tà áo dài truyền thống thướt tha mang đậm tâm hồn con người Việt Nam.",
                "jp": "温かい笑顔と優雅なアオザイに宿る、ベトナム人の心。",
                "keywords": ["vietnamese woman ao dai", "vietnam smiling girl", "vietnam conical hat"],
            },
            {
                "id": "s08",
                "vi": "Một Việt Nam vươn mình mạnh mẽ, hiện đại nhưng luôn gìn giữ trọn vẹn bản sắc tự hào.",
                "jp": "伝統を守りながら力強く未来へ歩み続けるベトナム。",
                "keywords": ["ho chi minh city skyline", "saigon sunset bridge", "vietnam modern city skyline"],
            }
        ]
    }
}




def slugify(text: str) -> str:
    """Convert text to safe folder/file name."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "_", text).strip("_")


ASPECTS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
FPS = 30
LEAD_IN, PAUSE, TAIL = 0.5, 0.55, 1.6
MUSIC_LIB = SCRIPT_DIR.parent / "config" / "music_library.json"
MUSIC_CACHE = Path.home() / ".cache" / "aiwf" / "music"


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise RuntimeError(f"{' '.join(map(str, cmd[:3]))}…: {r.stderr[-600:]}")
    return r


class VideoPipeline:
    """Kịch bản (do AGENT viết) → giọng đọc có kiểm tra → hình có giấy phép → nhạc CC BY → phụ đề chuẩn → MP4 + bằng chứng."""

    def __init__(self, topic: str, tier: str = "free", lang: str = "vi", mood: str = None, output: str = None, bgm: str = None,
                 script_file: str = None, ducking_ratio: float = 14.0, json_output: bool = False, voice: str = None,
                 aspect: str = None, allow_template: bool = False, allow_youtube: bool = False, gender: str = "female",
                 music_level: float = 0.6, subtitles: bool = True, verify_voice: bool = True):
        self.topic, self.tier, self.lang = topic, tier.lower(), lang.lower()
        self.user_mood, self.custom_bgm, self.script_file = mood, bgm, script_file
        self.ducking_ratio, self.json_output, self.voice, self.gender = ducking_ratio, json_output, voice, gender
        self.aspect, self.allow_template, self.allow_youtube = aspect, allow_template, allow_youtube
        self.music_level, self.subtitles, self.verify_voice = music_level, subtitles, verify_voice
        self.topic_slug = slugify(topic) or "video_project"
        out_root = Path.home() / "Downloads" / "AIWF_Output"
        self.final_output = Path(output).expanduser().resolve() if output else out_root / self.topic_slug / f"{self.topic_slug}.mp4"
        self.out_dir = self.final_output.parent
        self.work_dir = self.out_dir / f"_{self.final_output.stem}_work"     # cache: render lại chỉ làm phần thay đổi
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.credits, self.warnings = [], []
        print("\n" + "=" * 65 + f"\n🎬 AIWF VIDEO STUDIO v2 — {self.topic}\n" + "=" * 65)

    def log(self, m):
        if not self.json_output or not m.startswith("   "):
            print(m, flush=True)

    # ------------------------------------------------------------------ script
    def resolve_script(self) -> dict:
        if self.script_file and Path(self.script_file).exists():
            return json.load(open(self.script_file, encoding="utf-8"))
        if not self.allow_template:
            raise SystemExit("❌ Thiếu --script. Agent PHẢI tự viết kịch bản JSON cho chủ đề (xem SKILL.md §3 và "
                             "references/script-guide.md). Mẫu cố định chỉ dùng để thử máy: thêm --allow-template.")
        t = self.topic.lower()
        key = "nhat_ban" if any(k in t for k in ["nhật", "japan", "tokyo", "kyoto"]) else "viet_nam"
        self.warnings.append("Dùng kịch bản MẪU cố định (--allow-template), không phải kịch bản viết cho chủ đề.")
        return PRESET_SCRIPTS[key]

    def scene_text(self, s):
        alias = {"vi": ["narration", "vi"], "ja": ["narration", "jp", "ja"], "en": ["narration", "en"]}[self.lang]
        return next((s[k].strip() for k in alias if s.get(k)), "")

    def spoken(self, s):
        """Lời đọc cho TTS: bỏ dấu '|' (dấu '|' chỉ là chỗ agent muốn ngắt phụ đề)."""
        return re.sub(r"\s*\|\s*", " ", self.scene_text(s)).strip()

    # ------------------------------------------------------------------ voice
    def narrate(self, scenes):
        import dub_engine
        lines = [{"key": s["id"], "text": self.spoken(s)} for s in scenes]
        empty = [l["key"] for l in lines if not l["text"]]
        if empty:
            raise SystemExit(f"❌ Cảnh không có lời đọc: {empty}")
        voice = self.voice or {"vi": None, "ja": "ja-JP-NanamiNeural", "en": None}[self.lang]
        res, used = dub_engine.synthesize(lines, self.lang, voice, self.gender, str(self.work_dir / "voice"),
                                          takes=3, verify=self.verify_voice, log=self.log)
        missing = [l["key"] for l in lines if l["key"] not in res]
        if missing:
            raise RuntimeError(f"Không tổng hợp được giọng cho cảnh: {missing}")
        self.voice_used = used
        return res

    # ------------------------------------------------------------------ visuals
    def visuals_of(self, s):
        vis = s.get("visuals") or [{"query": k} for k in s.get("keywords", [])]
        return [v if isinstance(v, dict) else {"query": str(v)} for v in vis] or [{"query": self.topic}]

    def make_shot(self, v, dur, idx, W, H, out):
        """Một shot: video thật (file của người dùng / Pexels / Pixabay) hoặc ảnh có giấy phép + Ken Burns."""
        from stock_fetcher import StockFetcher
        src, kind, credit = None, None, None
        media = v.get("media")
        if media:
            p = Path(media).expanduser()
            if not p.exists():
                self.warnings.append(f"Không thấy file media: {media}")
            else:
                src, kind = str(p), ("video" if p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm", ".m4v") else "image")
                credit = {"source": "Người dùng cung cấp", "title": p.name, "license": "—"}
        q = v.get("query")
        if not src and q:
            f = StockFetcher(tier=self.tier)
            for search in (f.search_pexels_video, f.search_pixabay_video):
                try:
                    items = search(q, min_duration=min(dur, 6))
                except Exception:
                    items = []
                if items:
                    tgt = self.work_dir / "media" / f"{slugify(q)[:40]}_{search.__name__[7:13]}.mp4"
                    tgt.parent.mkdir(parents=True, exist_ok=True)
                    if tgt.exists() or f.download_url_file(items[0]["url"], tgt):
                        src, kind = str(tgt), "video"
                        credit = {"source": items[0]["source"].title(), "title": items[0]["title"], "license": f"{items[0]['source'].title()} License"}
                        break
            if not src:
                from open_media import find_image
                tgt = self.work_dir / "media" / f"{slugify(q)[:50]}.jpg"
                if tgt.exists() and (tgt.with_suffix(".json")).exists():
                    credit = json.load(open(tgt.with_suffix(".json"), encoding="utf-8")); src, kind = str(tgt), "image"
                else:
                    c = find_image(q, str(tgt), landscape=W >= H)
                    if c:
                        json.dump(c, open(tgt.with_suffix(".json"), "w", encoding="utf-8"), ensure_ascii=False)
                        src, kind, credit = str(tgt), "image", c
            if not src and self.allow_youtube:
                try:
                    tgt = self.work_dir / "media" / f"{slugify(q)[:40]}_yt.mp4"
                    src = StockFetcher(tier=self.tier).fetch_video_clip([q], dur, str(tgt)); kind = "video"
                    credit = {"source": "YouTube (KHÔNG xác minh giấy phép)", "title": q, "license": "?"}
                    self.warnings.append(f"Shot '{q}' lấy từ YouTube — giấy phép chưa được xác minh.")
                except Exception:
                    src = None
        n = int(round(dur * FPS))
        cache_key = f"{src}|{kind}|{n}|{idx % 4}|{W}x{H}"
        keyf = Path(str(out) + ".key")
        if src and out.exists() and keyf.exists() and keyf.read_text() == cache_key:
            return credit                                   # shot không đổi: dùng lại, khỏi mã hoá lại
        common = ["-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-an", "-frames:v", str(n), str(out)]
        if kind == "video":
            vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p"
            run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-ss", "0.4", "-i", src, "-vf", vf] + common)
        elif kind == "image":
            # Ken Burns: ảnh phóng 2× rồi zoompan (mượt, không rung); luân phiên 4 chuyển động
            z, x, y = [("1+0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
                       ("1.12-0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
                       ("1.12", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
                       ("1.12", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)")][idx % 4]
            z, x, y = (e.format(n=n) for e in (z, x, y))
            vf = (f"scale={2 * W}:{2 * H}:force_original_aspect_ratio=increase,crop={2 * W}:{2 * H},"
                  f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS},format=yuv420p")
            run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", src, "-vf", vf] + common)
        if src:
            keyf.write_text(cache_key)
        else:
            self.warnings.append(f"Không tìm được hình cho '{q or media}' — dùng nền màu. Đổi query cụ thể hơn hoặc thêm 'media'.")
            run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"gradients=s={W}x{H}:c0=0x1d2b45:c1=0x3b5f8a:duration={dur:.2f}:speed=0.02"] + common)
            credit = {"source": "nền màu (thiếu hình)", "title": q or media, "license": "—"}
        return credit

    # ------------------------------------------------------------------ music
    def music(self, mood, total):
        out = self.work_dir / "music_bed.wav"
        src, credit = None, None
        if self.custom_bgm and Path(self.custom_bgm).expanduser().exists():
            src = str(Path(self.custom_bgm).expanduser()); credit = f"Music: {Path(src).name} (người dùng cung cấp)"
        else:
            lib = json.load(open(MUSIC_LIB, encoding="utf-8"))
            titles = lib["moods"].get(mood) or lib["moods"]["corporate"]
            title = titles[sum(map(ord, self.topic)) % len(titles)]
            MUSIC_CACHE.mkdir(parents=True, exist_ok=True)
            cached = MUSIC_CACHE / f"{title}.mp3"
            if not cached.exists():
                try:
                    import urllib.parse, urllib.request
                    req = urllib.request.Request(lib["base_url"] + urllib.parse.quote(title) + ".mp3", headers={"User-Agent": "AIWF-video-studio/2.0"})
                    cached.write_bytes(urllib.request.urlopen(req, timeout=60).read())
                except Exception as e:
                    self.warnings.append(f"Không tải được nhạc '{title}': {e}. Video không có nhạc nền.")
                    return None, None
            src, credit = str(cached), lib["credit_template"].format(title=title)
        # lặp/cắt đúng độ dài, fade, chuẩn hoá −20 LUFS (≈ ngang giọng) để mức trộn dễ đoán
        run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", src, "-t", f"{total:.2f}",
             "-af", f"afade=t=in:d=1.2,afade=t=out:st={max(0, total - 3):.2f}:d=3,loudnorm=I=-20:TP=-2", "-ar", "48000", "-ac", "2", str(out)])
        return str(out), credit

    # ------------------------------------------------------------------ subtitles
    def subtitle_segments(self, scenes, timeline):
        from semantic_segmenter import semantic_chunk_words
        segs = []
        for s, (start, speech, end) in zip(scenes, timeline):
            text = self.scene_text(s); cjk = self.lang == "ja"
            toks = [t for t in (list(text.replace(" ", "")) if cjk else text.split()) if t != "|"]
            weights = [len(t) + (0 if cjk else 1) for t in toks]; tot = sum(weights) or 1
            t, words = start, []
            for tok, w in zip(toks, weights):
                d = speech * w / tot; words.append({"word": tok, "start": round(t, 3), "end": round(t + d, 3), "probability": 1.0}); t += d
            if "|" in text:      # agent đã chỉ định chỗ ngắt phụ đề: mỗi đoạn giữa hai '|' là một phụ đề
                parts, wi = [], 0
                for chunk in [c.strip() for c in text.split("|") if c.strip()]:
                    n = len(list(chunk.replace(" ", "")) if cjk else chunk.split())
                    ws = [w for w in words[wi:wi + n] if w["word"] != "|"]; wi += n
                    if ws:
                        parts.append({"start": ws[0]["start"], "end": ws[-1]["end"] + 0.35, "source_text": chunk})
                for p0, p1 in zip(parts, parts[1:]):
                    p0["end"] = min(p0["end"], p1["start"] - 0.05)
            else:
                parts = semantic_chunk_words([{"words": words}], max_lines=2, lang=self.lang)
            sec = (s.get("secondary") or "").strip()
            for k, p in enumerate(parts):
                p["end"] = min(p["end"], end - 0.05)
                seg = {"start": p["start"], "end": p["end"], "source_text": p["source_text"], "translated_text": p["source_text"]}
                if sec:      # song ngữ: chia câu phụ theo tỉ lệ ký tự
                    n = len(parts); L = len(sec)
                    a, b = round(L * k / n), round(L * (k + 1) / n)
                    a = sec.rfind(" ", 0, a) + 1 if k else 0; b = L if k == n - 1 else max(a + 1, sec.rfind(" ", 0, b))
                    seg["source_text"] = sec[a:b].strip()
                segs.append(seg)
        return segs

    def write_ass(self, segs, scenes, timeline, title, subtitle, W, H, path):
        from ass_generator import generate_ass
        presets = json.load(open(PHUDE / ".." / "templates" / "default_styles.json", encoding="utf-8"))["presets"]
        style = dict(presets["tiktok_box" if H > W else "modern_bottom"])
        bilingual = any(s.get("secondary") for s in scenes)
        style["mode"] = "bilingual" if bilingual else "monolingual"
        if H > W:
            style.update({"max_cpl": 30, "margin_v": 260})
        proj = {"video": {"width": W, "height": H}, "style": style, "segments": segs if self.subtitles else []}
        generate_ass(proj, path)
        # Tiêu đề mở đầu + caption từng cảnh (chữ lớn, fade) — thêm style riêng vào cùng file ASS
        fs = int(min(W, H) * 0.1)
        lines = open(path, encoding="utf-8").read().split("\n")
        k = next(i for i, l in enumerate(lines) if l.startswith("Style:")) + 1
        lines.insert(k, f"Style: Title,Be Vietnam Pro,{fs},&H00FFFFFF,&H00FFFFFF,&H00141414,&H64000000,1,0,0,0,100,100,0,0,1,{fs / 18:.1f},{fs / 30:.1f},5,60,60,0,1")
        lines.insert(k + 1, f"Style: Caption,Be Vietnam Pro,{int(fs * 0.62)},&H00FFFFFF,&H00FFFFFF,&H00141414,&H64000000,1,0,0,0,100,100,0,0,1,{fs / 22:.1f},{fs / 36:.1f},8,60,60,{int(H * 0.08)},1")
        fmt = lambda t: f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
        if title:
            sub = f"\\N{{\\fs{int(fs * 0.5)}\\b0}}{subtitle}" if subtitle else ""
            lines.append(f"Dialogue: 2,{fmt(0.2)},{fmt(min(3.6, timeline[0][2]))},Title,,0,0,0,,{{\\fad(450,450)}}{title}{sub}")
        for s, (start, _, end) in zip(scenes, timeline):
            if s.get("caption"):
                lines.append(f"Dialogue: 2,{fmt(start + 0.15)},{fmt(end - 0.1)},Caption,,0,0,0,,{{\\fad(300,300)}}{s['caption']}")
        open(path, "w", encoding="utf-8").write("\n".join(lines))

    # ------------------------------------------------------------------ run
    def run(self) -> str:
        import dub_engine
        sd = self.resolve_script()
        scenes = sd["scenes"]
        for i, s in enumerate(scenes):
            s.setdefault("id", f"s{i + 1:02d}")
        aspect = self.aspect or sd.get("aspect", "16:9")
        W, H = ASPECTS.get(aspect, ASPECTS["16:9"])
        mood = self.user_mood or sd.get("mood", "corporate")
        self.lang = sd.get("lang", self.lang)
        self.voice = self.voice or sd.get("voice")

        # 1) giọng đọc (VieNeu + Whisper kiểm tra) → dòng thời gian theo lời
        self.log(f"🗣  [1/5] Giọng đọc {len(scenes)} cảnh ({self.lang}, {self.voice or self.gender})")
        vo = self.narrate(scenes)
        timeline, t = [], LEAD_IN
        for s in scenes:
            speech = vo[s["id"]]["dur"]
            dur = max(float(s.get("min_duration", 0)), speech + PAUSE)
            timeline.append((t, speech, t + dur)); t += dur
        total = t + TAIL
        timeline[-1] = (timeline[-1][0], timeline[-1][1], total)

        # 2) hình: mỗi cảnh 1–3 shot (≈ 4.5 s/shot), ảnh/clip có giấy phép
        self.log(f"🎞  [2/5] Hình ảnh ({aspect} {W}x{H})")
        shots_dir = self.work_dir / "shots"; shots_dir.mkdir(exist_ok=True)
        shot_files, scene_credits, idx = [], [], 0
        for s, (start, _, end) in zip(scenes, timeline):
            vis = self.visuals_of(s); dur = end - start
            n = max(1, min(len(vis), 3, int(round(dur / 4.5))))
            sc = []
            for k in range(n):
                part = dur / n
                out = shots_dir / f"{s['id']}_{k}.mp4"
                c = self.make_shot(vis[k], part, idx, W, H, out); idx += 1
                shot_files.append(out); sc.append({**(c or {}), "query": vis[k].get("query") or vis[k].get("media")})
            scene_credits.append(sc)
            self.log(f"   {s['id']}: {n} shot · " + " | ".join(f"{c.get('source')}: {str(c.get('title'))[:40]}" for c in sc))
        concat = self.work_dir / "shots.txt"
        concat.write_text("".join(f"file '{p}'\n" for p in shot_files))
        master = self.work_dir / "master_video.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(master)])

        # 3) âm thanh: giọng đặt đúng mốc + nhạc CC BY hạ khi có lời, chuẩn −16 LUFS
        self.log(f"🎵  [3/5] Nhạc nền ({mood}) + hòa âm")
        bed, music_credit = self.music(mood, total)
        mix_wav = str(self.work_dir / "final_mix.wav")
        dub_engine.mix(bed, [(start, vo[s["id"]]["path"]) for s, (start, _, _) in zip(scenes, timeline)], mix_wav, total,
                       bg_volume=self.music_level if bed else 0.0, duck_level=0.25, voice_volume=1.0)
        lufs, peak = dub_engine.loudness(mix_wav)

        # 4) phụ đề + tiêu đề (bộ sinh của phu-de) → render cuối
        self.log("🔤  [4/5] Phụ đề + render")
        ass = str(self.work_dir / "subs.ass")
        segs = self.subtitle_segments(scenes, timeline)
        self.write_ass(segs, scenes, timeline, sd.get("title_top") or sd.get("title", ""), sd.get("title_sub") or sd.get("subtitle", ""), W, H, ass)
        fonts = str((PHUDE / ".." / "templates" / "fonts").resolve())
        esc = lambda p: p.replace("\\", "/").replace(":", "\\:")
        ff = dub_engine.ffmpeg_bin()
        vf = f"ass='{esc(ass)}':fontsdir='{esc(fonts)}',fade=t=in:st=0:d=0.5,fade=t=out:st={total - 0.8:.2f}:d=0.8"
        self.final_output.parent.mkdir(parents=True, exist_ok=True)
        run([ff, "-v", "error", "-y", "-i", str(master), "-i", mix_wav, "-vf", vf, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
             "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.2f}", str(self.final_output)])

        # 5) bằng chứng: ảnh duyệt (1 khung/cảnh), credits, báo cáo
        self.log("🔍  [5/5] Ảnh duyệt + credits + báo cáo")
        review = self.final_output.with_name(self.final_output.stem + "_review.jpg")
        tiles = []
        for k, (s, (start, speech, end)) in enumerate(zip(scenes, timeline)):
            fp = self.work_dir / f"rv_{k:02d}.jpg"
            run([ff, "-v", "error", "-y", "-ss", f"{start + min(speech, end - start) * 0.6:.2f}", "-i", str(self.final_output), "-frames:v", "1", "-vf", "scale=640:-2", str(fp)])
            tiles.append((s["id"], fp))
        from PIL import Image, ImageDraw
        ims = [Image.open(p) for _, p in tiles]; tw, th = ims[0].size; cols = 3 if W >= H else 4; rows = -(-len(ims) // cols)
        sheet = Image.new("RGB", (cols * tw, rows * (th + 24)), "#111"); dr = ImageDraw.Draw(sheet)
        for k, ((sid, _), im) in enumerate(zip(tiles, ims)):
            x, y = k % cols * tw, k // cols * (th + 24); sheet.paste(im, (x, y)); dr.text((x + 6, y + th + 5), f"{sid}  {timeline[k][0]:.1f}s", fill="#ddd")
        sheet.save(review, quality=88)
        credit_lines = [f"Voice: {self.voice_used or 'TTS'} ({'VieNeu-TTS' if self.lang == 'vi' else 'TTS'})"]
        if music_credit:
            credit_lines.append(music_credit)
        from open_media import credit_line
        for s, sc in zip(scenes, scene_credits):
            for c in sc:
                if c.get("license") not in (None, "—"):
                    credit_lines.append(f"{s['id']}: {credit_line(c)}")
        credits_path = self.final_output.with_name(self.final_output.stem + "_credits.txt")
        credits_path.write_text("\n".join(credit_lines) + "\n", encoding="utf-8")
        report = {"status": "PASS" if not self.warnings else "PASS_WITH_WARNINGS", "output": str(self.final_output), "review_image": str(review),
                  "credits": str(credits_path), "duration_seconds": round(total, 2), "aspect": aspect, "scenes": len(scenes), "lang": self.lang,
                  "voice": self.voice_used, "loudness_lufs": lufs, "true_peak_dbfs": peak, "warnings": self.warnings,
                  "voice_check": [{"scene": s["id"], "cer": vo[s["id"]].get("cer"), "heard": vo[s["id"]].get("heard")} for s in scenes if (vo[s["id"]].get("cer") or 0) > 0.08],
                  "visuals": [{"scene": s["id"], "shots": sc} for s, sc in zip(scenes, scene_credits)]}
        json.dump(report, open(self.final_output.with_name(self.final_output.stem + "_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        if self.json_output:
            print(json.dumps({k: v for k, v in report.items() if k != "visuals"}, ensure_ascii=False, indent=2))
        else:
            print(f"\n🎉 {self.final_output} · {total:.1f}s · {len(scenes)} cảnh · {lufs} LUFS\n   Duyệt: {review}\n   Credits: {credits_path}")
            for w in self.warnings:
                print(f"   ⚠️ {w}")
        return str(self.final_output)


def main():
    ap = argparse.ArgumentParser(description="AIWF Video Studio v2 — kịch bản JSON (agent viết) → MP4 có giọng, hình, nhạc, phụ đề")
    ap.add_argument("--topic", required=True, help="Tên/chủ đề video (đặt tên file đầu ra)")
    ap.add_argument("--script", default=None, help="Kịch bản JSON do agent viết (BẮT BUỘC, xem references/script-guide.md)")
    ap.add_argument("--allow-template", action="store_true", help="Cho phép chạy bằng kịch bản mẫu cố định (chỉ để thử máy)")
    ap.add_argument("--tier", choices=["free", "premium"], default="free")
    ap.add_argument("--lang", choices=["vi", "ja", "en"], default="vi")
    ap.add_argument("--mood", choices=["peaceful", "traditional", "energetic", "emotional", "urban", "corporate", "playful", "epic"], default=None)
    ap.add_argument("--aspect", choices=list(ASPECTS), default=None, help="16:9 (YouTube), 9:16 (TikTok/Reels/Shorts), 1:1, 4:5")
    ap.add_argument("--bgm", default=None, help="File nhạc nền riêng")
    ap.add_argument("--music-level", type=float, default=0.6, help="Mức nhạc nền khi không có lời (0–1); khi có lời tự hạ còn 25%%")
    ap.add_argument("--output", default=None, help="MP4 đầu ra (mặc định ~/Downloads/AIWF_Output/<topic>/<topic>.mp4)")
    ap.add_argument("--voice", default=None, help="Giọng: VieNeu (Thùy Dung, Trúc Ly, Minh Quân Pro…) hoặc Edge (vi-VN-NamMinhNeural…)")
    ap.add_argument("--gender", choices=["female", "male"], default="female")
    ap.add_argument("--no-subtitles", action="store_true")
    ap.add_argument("--no-verify-voice", action="store_true", help="Bỏ kiểm tra phát âm bằng Whisper (nhanh hơn, kém an toàn)")
    ap.add_argument("--allow-youtube", action="store_true", help="Cho phép lấy clip YouTube khi thiếu hình (giấy phép KHÔNG được xác minh)")
    ap.add_argument("--ducking", type=float, default=14.0, help="(giữ tương thích, không còn dùng)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    VideoPipeline(topic=a.topic, tier=a.tier, lang=a.lang, mood=a.mood, output=a.output, bgm=a.bgm, script_file=a.script,
                  ducking_ratio=a.ducking, json_output=a.json, voice=a.voice, aspect=a.aspect, allow_template=a.allow_template,
                  allow_youtube=a.allow_youtube, gender=a.gender, music_level=a.music_level, subtitles=not a.no_subtitles,
                  verify_voice=not a.no_verify_voice).run()


if __name__ == "__main__":
    main()
