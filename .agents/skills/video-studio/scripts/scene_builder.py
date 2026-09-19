#!/usr/bin/env python3
"""
AI WORKFORCE - Scene & Timeline Builder
Generates TTS narration for each scene, measures exact audio duration,
fetches matching stock video clips via StockFetcher, and builds an aligned timeline.
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from stock_fetcher import StockFetcher
from audio_mixer import AudioMixer


class SceneBuilder:
    """Builds TTS narration, timeline, and video segments aligned to speech."""

    def __init__(self, work_dir: str, tier: str = "free", primary_lang: str = "vi"):
        self.work_dir = Path(work_dir).resolve()
        self.clips_dir = self.work_dir / "clips"
        self.audio_dir = self.work_dir / "audio"
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        self.tier = tier
        self.primary_lang = primary_lang
        self.fetcher = StockFetcher(tier=self.tier)

        # TTS Voices
        self.voice_vi = "vi-VN-HoaiMyNeural"
        self.voice_ja = "ja-JP-NanamiNeural"

    async def _synth_edge_tts(self, text: str, voice: str, output_path: Path):
        """Synthesize TTS audio using edge_tts Python library or CLI fallback."""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
            return
        except ImportError:
            pass

        # CLI fallback (find edge-tts in venv if not in PATH)
        edge_bin = "edge-tts"
        candidate_bin = Path(__file__).resolve().parent.parent.parent.parent.parent / ".venv-tts" / "bin" / "edge-tts"
        if candidate_bin.exists():
            edge_bin = str(candidate_bin)

        cmd = [
            edge_bin,
            "--voice", voice,
            "--text", text,
            "--write-media", str(output_path)
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    def generate_narration_for_scenes(self, scenes: list[dict]) -> list[dict]:
        """
        Generate TTS narration for each scene and measure exact duration.
        primary_lang: 'vi' (default) -> speaks Vietnamese
                      'ja' -> speaks Japanese
        """
        print(f"\n📢 [SceneBuilder] Generating TTS narration (Primary: {self.primary_lang.upper()})...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        updated_scenes = []
        for s in scenes:
            sid = s["id"]
            vi_text = s.get("vi", "")
            jp_text = s.get("jp", "")
            
            # Select spoken text based on primary language
            if self.primary_lang == "vi":
                spoken_text = vi_text
                voice = self.voice_vi
                audio_file = self.audio_dir / f"{sid}_vi.mp3"
            else:
                spoken_text = jp_text
                voice = self.voice_ja
                audio_file = self.audio_dir / f"{sid}_ja.mp3"

            print(f"  🎙️ Synthesizing {sid}: '{spoken_text[:35]}...' ({voice})")
            loop.run_until_complete(self._synth_edge_tts(spoken_text, voice, audio_file))

            actual_dur = AudioMixer.get_duration(str(audio_file))
            # If duration is 0 or failed, default to 5.0
            if actual_dur <= 0.1:
                actual_dur = 5.0
            
            # Add 0.8s breath/pacing buffer
            scene_dur = round(actual_dur + 0.8, 2)
            s_copy = dict(s)
            s_copy["audio_path"] = str(audio_file)
            s_copy["audio_duration"] = actual_dur
            s_copy["duration"] = scene_dur
            updated_scenes.append(s_copy)
            print(f"     -> Actual duration: {actual_dur:.2f}s (Scene duration: {scene_dur:.2f}s)")

        return updated_scenes

    def fetch_clips_for_scenes(self, scenes: list[dict]) -> list[str]:
        """Fetch matching stock video clip for each scene based on keywords."""
        print(f"\n🎬 [SceneBuilder] Fetching stock footage for {len(scenes)} scenes (Tier: {self.tier.upper()})...")
        clip_paths = []
        for idx, s in enumerate(scenes):
            sid = s["id"]
            keywords = s.get("keywords", ["nature landscape"])
            dur_needed = s.get("duration", 5.0)
            target_clip = self.clips_dir / f"{sid}_clip.mp4"

            print(f"  [{idx+1}/{len(scenes)}] Scene {sid}: keywords={keywords}, needed={dur_needed}s")
            try:
                clip_path = self.fetcher.fetch_video_clip(
                    keywords=keywords,
                    min_duration=dur_needed,
                    output_path=str(target_clip)
                )
            except Exception as e:
                print(f"    ⚠️ Fetch error: {e}. Generating fallback visual...")
                clip_path = self._generate_fallback_clip(dur_needed, str(target_clip))
            
            clip_paths.append(clip_path)
        return clip_paths

    def _generate_fallback_clip(self, duration: float, output_path: str) -> str:
        """Generate a sleek animated color background as fallback."""
        out = Path(output_path)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x1a2436:s=1920x1080:d={duration:.2f}",
            "-vf", "noise=c1s=8:c0f=u",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(out)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return str(out)

    def normalize_and_trim_clips(self, scenes: list[dict], raw_clips: list[str]) -> list[str]:
        """Normalize all clips to 1920x1080 30fps and exact scene duration."""
        print("\n✂️ [SceneBuilder] Normalizing & trimming clips to 1080p 30fps...")
        trimmed_clips = []
        for s, raw_clip in zip(scenes, raw_clips):
            sid = s["id"]
            dur = s["duration"]
            out_clip = self.clips_dir / f"{sid}_trimmed.mp4"

            # Scale to 1920x1080, crop/pad to preserve aspect ratio, 30fps, mute audio
            vf = (
                "scale=1920:1080:force_original_aspect_ratio=increase,"
                "crop=1920:1080,"
                "fps=30"
            )
            cmd = [
                "ffmpeg", "-y",
                "-ss", "0",
                "-i", str(raw_clip),
                "-t", f"{dur:.2f}",
                "-vf", vf,
                "-c:v", "libx264",
                "-crf", "20",
                "-preset", "fast",
                "-an",
                str(out_clip)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            trimmed_clips.append(str(out_clip))
            print(f"  ✓ {sid}: {dur}s @ 1920x1080 -> {out_clip.name}")
        return trimmed_clips

    def build_video_track(self, trimmed_clips: list[str], output_path: str) -> str:
        """Concatenates trimmed clips into master video track."""
        print("\n🎞️ [SceneBuilder] Assembling master video track...")
        out_file = Path(output_path).resolve()
        concat_txt = self.work_dir / "_concat_clips.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in trimmed_clips:
                f.write(f"file '{Path(c).resolve()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c:v", "libx264",
            "-crf", "20",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-an",
            str(out_file)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if concat_txt.exists():
            concat_txt.unlink()
        print(f"  ✅ Master video track ready: {out_file.name}")
        return str(out_file)

    def render_karaoke_subtitles(
        self,
        video_path: str,
        audio_path: str,
        scenes: list[dict],
        output_path: str,
        title_top: str = "",
        title_sub: str = ""
    ) -> str:
        """
        Renders bilingual karaoke-style subtitles using PIL streaming directly to FFmpeg.
        Primary language on top (Golden highlight), Secondary language below.
        Uses CJK and Unicode fonts for flawless glyph rendering.
        """
        print(f"\n🎨 [SceneBuilder] Rendering karaoke subtitles (Primary: {self.primary_lang.upper()})...")
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        # Build timeline for subtitles
        subs = []
        cur_time = 0.0
        for s in scenes:
            dur = s["duration"]
            audio_dur = s.get("audio_duration", dur)
            # Primary vs secondary text
            if self.primary_lang == "vi":
                line_pri = s.get("vi", "")
                line_sec = s.get("jp", "")
            else:
                line_pri = s.get("jp", "")
                line_sec = s.get("vi", "")
            
            subs.append({
                "start": cur_time,
                "end": cur_time + audio_dur,
                "scene_end": cur_time + dur,
                "primary": line_pri,
                "secondary": line_sec
            })
            cur_time += dur

        # Probe video dimensions & fps
        probe_cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams", "-show_format",
            str(video_path)
        ]
        info = json.loads(subprocess.run(probe_cmd, capture_output=True, text=True, check=True).stdout)
        vs = next(s for s in info["streams"] if s["codec_type"] == "video")
        W = int(vs["width"])
        H = int(vs["height"])
        fps_parts = vs.get("r_frame_rate", "30/1").split("/")
        FPS = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0
        total_dur = float(info["format"]["duration"])
        total_frames = int(total_dur * FPS)

        print(f"  Frame resolution: {W}x{H} @ {FPS:.1f}fps, total: {total_frames} frames ({total_dur:.1f}s)")

        # Load Fonts based on primary language (Arial Unicode for Vietnamese, Hiragino for Japanese)
        font_cjk = "/System/Library/Fonts/Hiragino Sans GB.ttc"
        font_unicode = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
        if not Path(font_unicode).exists():
            font_unicode = "/System/Library/Fonts/Supplemental/Arial.ttf"

        try:
            if self.primary_lang == "vi":
                font_pri = ImageFont.truetype(font_unicode, 34)
                font_sec = ImageFont.truetype(font_cjk, 24)
                font_title = ImageFont.truetype(font_unicode, 48)
                font_subtitle = ImageFont.truetype(font_unicode, 28)
            else:
                font_pri = ImageFont.truetype(font_cjk, 34)
                font_sec = ImageFont.truetype(font_unicode, 24)
                font_title = ImageFont.truetype(font_cjk, 48)
                font_subtitle = ImageFont.truetype(font_unicode, 28)
        except Exception as e:
            print(f"⚠️ [SceneBuilder] Font load fallback: {e}")
            font_pri = font_sec = font_title = font_subtitle = ImageFont.load_default()

        def get_sub_info(t):
            for item in subs:
                if item["start"] <= t < item["scene_end"]:
                    dur_active = item["end"] - item["start"]
                    progress = (t - item["start"]) / dur_active if dur_active > 0 else 1.0
                    return item["primary"], item["secondary"], min(1.0, max(0.0, progress))
            return None, None, 0.0

        def process_frame(raw_bytes, t):
            img = Image.frombytes("RGB", (W, H), raw_bytes)
            draw = ImageDraw.Draw(img)

            # Subtitle background bar (semi-transparent dark gradient)
            bar_height = 110
            bar = Image.new("RGBA", (W, bar_height), (10, 15, 25, 175))
            base_layer = Image.new("RGBA", (W, bar_height), (0, 0, 0, 0))
            composite = Image.alpha_composite(base_layer, bar).convert("RGB")
            img.paste(composite, (0, H - bar_height))
            draw = ImageDraw.Draw(img)

            # Title card at beginning (0s - 4.5s)
            if t < 4.5 and title_top:
                alpha_factor = min(1.0, (4.5 - t) / 1.0) if t > 3.5 else 1.0
                bb1 = draw.textbbox((0, 0), title_top, font=font_title)
                tw1 = bb1[2] - bb1[0]
                draw.text(((W - tw1) // 2 + 2, H // 2 - 48 + 2), title_top, fill=(0, 0, 0), font=font_title)
                draw.text(((W - tw1) // 2, H // 2 - 48), title_top, fill=(255, 255, 255), font=font_title)
                if title_sub:
                    bb2 = draw.textbbox((0, 0), title_sub, font=font_subtitle)
                    tw2 = bb2[2] - bb2[0]
                    draw.text(((W - tw2) // 2 + 1, H // 2 + 20 + 1), title_sub, fill=(0, 0, 0), font=font_subtitle)
                    draw.text(((W - tw2) // 2, H // 2 + 20), title_sub, fill=(210, 235, 255), font=font_subtitle)

            # Karaoke subtitles
            pri_text, sec_text, prog = get_sub_info(t)
            if pri_text:
                chars = list(pri_text)
                cur_char_idx = int(prog * len(chars))
                bb_pri = draw.textbbox((0, 0), pri_text, font=font_pri)
                tw_pri = bb_pri[2] - bb_pri[0]
                x_pri = (W - tw_pri) // 2
                y_pri = H - 98

                # Shadow
                draw.text((x_pri + 2, y_pri + 2), pri_text, fill=(0, 0, 0), font=font_pri)
                
                # Karaoke letter-by-letter rendering
                curr_x = x_pri
                for i, ch in enumerate(chars):
                    cbox = draw.textbbox((0, 0), ch, font=font_pri)
                    cw = cbox[2] - cbox[0]
                    if i < cur_char_idx:
                        ch_color = (255, 225, 75)    # Golden active
                    elif i == cur_char_idx:
                        ch_color = (255, 255, 170)   # Highlight edge
                    else:
                        ch_color = (255, 255, 255)   # Inactive white
                    draw.text((curr_x, y_pri), ch, fill=ch_color, font=font_pri)
                    curr_x += cw

                # Secondary line (translation)
                if sec_text:
                    bb_sec = draw.textbbox((0, 0), sec_text, font=font_sec)
                    tw_sec = bb_sec[2] - bb_sec[0]
                    x_sec = (W - tw_sec) // 2
                    y_sec = H - 46
                    draw.text((x_sec + 1, y_sec + 1), sec_text, fill=(0, 0, 0), font=font_sec)
                    draw.text((x_sec, y_sec), sec_text, fill=(195, 230, 255), font=font_sec)

            return img.tobytes()

        # Stream decoder and encoder via FFmpeg
        decoder = subprocess.Popen(
            ["ffmpeg", "-i", str(video_path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-v", "quiet", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        encoder = subprocess.Popen(
            [
                "ffmpeg", "-y",
                "-f", "rawvideo", "-pix_fmt", "rgb24",
                "-s", f"{W}x{H}",
                "-r", str(FPS),
                "-i", "-",
                "-i", str(audio_path),
                "-c:v", "libx264", "-crf", "20", "-preset", "fast",
                "-c:a", "aac", "-b:a", "256k",
                "-movflags", "+faststart",
                "-shortest",
                str(out_file)
            ],
            stdin=subprocess.PIPE, stderr=subprocess.PIPE
        )

        frame_size = W * H * 3
        frame_idx = 0
        try:
            while True:
                raw_frame = decoder.stdout.read(frame_size)
                if not raw_frame or len(raw_frame) < frame_size:
                    break
                t = frame_idx / FPS
                processed = process_frame(raw_frame, t)
                try:
                    encoder.stdin.write(processed)
                except BrokenPipeError:
                    break
                frame_idx += 1
                if frame_idx % 90 == 0 or frame_idx == total_frames:
                    pct = min(100.0, (frame_idx / total_frames) * 100) if total_frames else 0
                    print(f"    Rendering progress: {pct:.1f}% ({frame_idx}/{total_frames} frames)", end="\r")
        finally:
            print()
            try:
                decoder.stdout.close()
                decoder.wait(timeout=5)
            except Exception:
                decoder.kill()
            try:
                encoder.stdin.close()
                encoder.wait(timeout=30)
            except Exception:
                encoder.kill()

        print(f"  ✅ Subtitle burn-in complete: {out_file.name}")
        return str(out_file)
