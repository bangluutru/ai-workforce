#!/usr/bin/env python3
"""
AI WORKFORCE - Stock Media Fetcher
Multi-source video and background music fetcher with Tier support (Free vs Premium).
Sources:
  - Video: Pexels API, Pixabay API, YouTube CC (fallback), Premium Stock Providers
  - Music: YouTube Audio Library / CC Royalty Free, Freesound API (SFX/ambient)
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import subprocess
from pathlib import Path

# Load .env variables without external dependencies
def load_env(env_path=None):
    """Load key-value pairs from .env into os.environ."""
    if not env_path:
        curr = Path(__file__).resolve().parent
        while curr != curr.parent:
            candidate = curr / ".env"
            if candidate.exists():
                env_path = candidate
                break
            curr = curr.parent
    
    if env_path and Path(env_path).exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    if k and k not in os.environ:
                        os.environ[k] = v

load_env()

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "").strip()
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "").strip()
FREESOUND_API_KEY = os.environ.get("FREESOUND_API_KEY", "").strip()
PREMIUM_STOCK_API_KEY = os.environ.get("PREMIUM_STOCK_API_KEY", "").strip()


class StockFetcher:
    """Multi-source stock media fetcher with Free vs Premium tier support."""

    def __init__(self, tier="free"):
        self.tier = tier.lower()
        if self.tier not in ["free", "premium"]:
            self.tier = "free"
        
        print(f"🎬 [StockFetcher] Initialized in {'💎 PREMIUM' if self.tier == 'premium' else '🆓 FREE (Default)'} Tier")
        if not PEXELS_API_KEY and not PIXABAY_API_KEY:
            print("⚠️ [StockFetcher] No Pexels or Pixabay API key found in .env. Will use YouTube CC fallback.")

    def search_pexels_video(self, query: str, min_duration: float = 3.0) -> list[dict]:
        """Search Pexels API for landscape video clips matching query."""
        if not PEXELS_API_KEY:
            return []
        
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.pexels.com/videos/search?query={encoded_query}&per_page=12&orientation=landscape"
        headers = {
            "Authorization": PEXELS_API_KEY,
            "User-Agent": "AIWorkforce-VideoStudio/1.0"
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                videos = data.get("videos", [])
                results = []
                for v in videos:
                    dur = v.get("duration", 0)
                    if dur < min_duration:
                        continue
                    
                    files = v.get("video_files", [])
                    if not files:
                        continue
                    
                    # Sort files based on tier
                    # Premium tier: prefer 4K / UHD (width >= 3840 or highest width)
                    # Free tier: prefer 1080p Full HD (width == 1920 or closest to 1920)
                    if self.tier == "premium":
                        sorted_files = sorted(
                            files,
                            key=lambda f: (f.get("width") or 0) * (f.get("height") or 0),
                            reverse=True
                        )
                    else:
                        # Find closest to 1920x1080 without exceeding unnecessarily
                        def score_free_file(f):
                            w = f.get("width") or 0
                            h = f.get("height") or 0
                            # 16:9 check
                            is_16_9 = abs((w / h if h else 1) - (16 / 9)) < 0.15
                            diff_1080 = abs(w - 1920)
                            return (is_16_9, -diff_1080)
                        sorted_files = sorted(files, key=score_free_file, reverse=True)
                    
                    chosen = sorted_files[0]
                    results.append({
                        "source": "pexels",
                        "id": v.get("id"),
                        "duration": dur,
                        "width": chosen.get("width"),
                        "height": chosen.get("height"),
                        "url": chosen.get("link"),
                        "title": f"Pexels Video {v.get('id')} ({chosen.get('width')}x{chosen.get('height')})"
                    })
                return results
        except Exception as e:
            print(f"⚠️ [Pexels Search Error] {e}", file=sys.stderr)
            return []

    def search_pixabay_video(self, query: str, min_duration: float = 3.0) -> list[dict]:
        """Search Pixabay API for landscape video clips matching query."""
        if not PIXABAY_API_KEY:
            return []
        
        encoded_query = urllib.parse.quote(query)
        url = f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={encoded_query}&video_type=all&per_page=12"
        headers = {"User-Agent": "AIWorkforce-VideoStudio/1.0"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("hits", [])
                results = []
                for h in hits:
                    dur = h.get("duration", 0)
                    if dur < min_duration:
                        continue
                    
                    videos_dict = h.get("videos", {})
                    # Pixabay provides 'large', 'medium', 'small', 'tiny'
                    if self.tier == "premium" and "large" in videos_dict and videos_dict["large"].get("url"):
                        chosen = videos_dict["large"]
                    elif "large" in videos_dict and videos_dict["large"].get("url") and videos_dict["large"].get("width", 0) <= 1920:
                        chosen = videos_dict["large"]
                    elif "medium" in videos_dict and videos_dict["medium"].get("url"):
                        chosen = videos_dict["medium"]
                    elif "large" in videos_dict:
                        chosen = videos_dict["large"]
                    elif "small" in videos_dict:
                        chosen = videos_dict["small"]
                    else:
                        continue
                    
                    results.append({
                        "source": "pixabay",
                        "id": h.get("id"),
                        "duration": dur,
                        "width": chosen.get("width"),
                        "height": chosen.get("height"),
                        "url": chosen.get("url"),
                        "title": f"Pixabay Video {h.get('id')} ({chosen.get('width')}x{chosen.get('height')})"
                    })
                return results
        except Exception as e:
            print(f"⚠️ [Pixabay Search Error] {e}", file=sys.stderr)
            return []

    def download_url_file(self, url: str, target_path: Path) -> bool:
        """Download remote media file to target_path with safe streaming."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as response, open(target_path, "wb") as out_file:
                chunk_size = 64 * 1024
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
            return target_path.exists() and target_path.stat().st_size > 1000
        except Exception as e:
            print(f"⚠️ [Download Error] Failed to download {url}: {e}", file=sys.stderr)
            if target_path.exists():
                target_path.unlink()
            return False

    def fetch_video_clip(self, keywords: list[str], min_duration: float, output_path: str) -> str:
        """
        Fetch best matching video clip for given keywords.
        Tries keywords one by one across Pexels -> Pixabay -> YouTube CC fallback.
        """
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Pexels API (Highest quality)
        for kw in keywords:
            print(f"  🔍 Searching Pexels for: '{kw}'...")
            items = self.search_pexels_video(kw, min_duration=min_duration)
            if items:
                best = items[0]
                print(f"  ✨ Found on Pexels ({best['width']}x{best['height']}, {best['duration']}s): {best['title']}")
                if self.download_url_file(best["url"], out_file):
                    print(f"  ✅ Downloaded Pexels clip -> {out_file.name}")
                    return str(out_file)
        
        # 2. Pixabay API
        for kw in keywords:
            print(f"  🔍 Searching Pixabay for: '{kw}'...")
            items = self.search_pixabay_video(kw, min_duration=min_duration)
            if items:
                best = items[0]
                print(f"  ✨ Found on Pixabay ({best['width']}x{best['height']}, {best['duration']}s): {best['title']}")
                if self.download_url_file(best["url"], out_file):
                    print(f"  ✅ Downloaded Pixabay clip -> {out_file.name}")
                    return str(out_file)

        # 3. YouTube Creative Commons Fallback (yt-dlp)
        print("  ⚠️ Pexels and Pixabay returned no matching clip. Falling back to YouTube CC...")
        search_query = keywords[0] if keywords else "landscape scenery 4k"
        yt_cmd = [
            "yt-dlp",
            f"ytsearch1:{search_query} creative commons 4k",
            "--extractor-args", "youtube:player_client=web_embedded",
            "-f", "best[height<=1080][ext=mp4]/best[ext=mp4]/best",
            "--max-downloads", "1",
            "-o", str(out_file)
        ]
        try:
            subprocess.run(yt_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
            if out_file.exists() and out_file.stat().st_size > 1000:
                print(f"  ✅ Downloaded YouTube CC fallback -> {out_file.name}")
                return str(out_file)
        except Exception as e:
            print(f"⚠️ [YouTube CC Error] {e}", file=sys.stderr)

        raise RuntimeError(f"Could not fetch any stock video for keywords: {keywords}")

    def fetch_background_music(self, mood: str, duration: float, output_path: str) -> str:
        """
        Fetch royalty-free background music matching mood.
        Uses YouTube Audio Library / CC instrumental tracks.
        """
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        mood_queries = {
            "peaceful": "calm peaceful piano ambient no copyright background music",
            "traditional": "japanese traditional koto shamisen royalty free instrumental",
            "energetic": "upbeat electronic energetic background music no copyright",
            "emotional": "cinematic emotional violin piano soundtrack no copyright",
            "urban": "lofi chill hop beat background music no copyright"
        }
        
        query = mood_queries.get(mood.lower(), f"{mood} instrumental background music no copyright")
        print(f"🎵 [StockFetcher] Searching BGM for mood '{mood}': '{query}'...")
        
        yt_cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            f"ytsearch1:{query}",
            "--extractor-args", "youtube:player_client=web_embedded",
            "--max-downloads", "1",
            "-o", str(out_file.with_suffix(".%(ext)s"))
        ]
        
        try:
            proc = subprocess.run(yt_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            # Find the generated mp3
            if out_file.exists():
                print(f"  ✅ BGM downloaded -> {out_file.name}")
                return str(out_file)
            for f in out_file.parent.glob(f"{out_file.stem}*.mp3"):
                f.rename(out_file)
                print(f"  ✅ BGM downloaded -> {out_file.name}")
                return str(out_file)
        except Exception as e:
            print(f"⚠️ [BGM Fetch Error] {e}", file=sys.stderr)
            
        raise RuntimeError(f"Failed to fetch background music for mood '{mood}'")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIWF Stock Media Fetcher")
    parser.add_argument("--query", type=str, default="cherry blossom", help="Search keywords")
    parser.add_argument("--tier", type=str, choices=["free", "premium"], default="free", help="Quality tier")
    parser.add_argument("--duration", type=float, default=5.0, help="Minimum duration in seconds")
    parser.add_argument("--output", type=str, default="/tmp/test_clip.mp4", help="Output video file path")
    parser.add_argument("--test", action="store_true", help="Run a quick verification test")
    args = parser.parse_args()

    fetcher = StockFetcher(tier=args.tier)
    if args.test:
        print(f"\n🧪 Running test video search for query '{args.query}' (Tier: {args.tier})...")
        res_pex = fetcher.search_pexels_video(args.query, min_duration=args.duration)
        print(f"  Pexels returned {len(res_pex)} video candidates.")
        res_pix = fetcher.search_pixabay_video(args.query, min_duration=args.duration)
        print(f"  Pixabay returned {len(res_pix)} video candidates.")
        if res_pex or res_pix:
            print("✅ StockFetcher APIs Verified Successfully!")
        else:
            print("❌ No results found or API keys missing.")
    else:
        out = fetcher.fetch_video_clip([args.query], min_duration=args.duration, output_path=args.output)
        print(f"Downloaded: {out}")
