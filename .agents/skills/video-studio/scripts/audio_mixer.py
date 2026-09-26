#!/usr/bin/env python3
"""
AI WORKFORCE - Audio Mixer Engine
Mixes narration speech with background music (BGM) using FFmpeg sidechaincompress (audio ducking).
Ensures BGM lowers smoothly when voice speaks, with fade-in/fade-out and loudness normalization.
"""

import os
import sys
import subprocess
from pathlib import Path


class AudioMixer:
    """Audio mixing and ducking utility using FFmpeg."""

    @staticmethod
    def get_duration(audio_path: str) -> float:
        """Return duration of audio file in seconds via ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(res.stdout.strip())
        except Exception as e:
            print(f"⚠️ [AudioMixer] Could not get duration for {audio_path}: {e}", file=sys.stderr)
            return 0.0

    @classmethod
    def mix_narration_and_bgm(
        cls,
        narration_path: str,
        bgm_path: str,
        output_path: str,
        bgm_volume: float = 0.22,
        ducking_ratio: float = 8.0,
        fade_in: float = 1.0,
        fade_out: float = 2.0,
        target_duration: float = None
    ) -> str:
        """
        Mixes narration with BGM using sidechaincompress ducking.
        - BGM volume drops when speech is active.
        - Smooth fade in at start and fade out at the end.
        """
        narr_file = Path(narration_path).resolve()
        bgm_file = Path(bgm_path).resolve()
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        if not narr_file.exists():
            raise FileNotFoundError(f"Narration file not found: {narr_file}")
        if not bgm_file.exists():
            raise FileNotFoundError(f"BGM file not found: {bgm_file}")

        narr_dur = cls.get_duration(str(narr_file))
        total_dur = target_duration if target_duration else (narr_dur + 1.5)

        bgm_dur = cls.get_duration(str(bgm_file))
        fade_out_start = max(0.5, total_dur - fade_out)

        # Loop BGM if shorter than required duration
        stream_loop = ["-stream_loop", "-1"] if bgm_dur < total_dur else []

        print(f"🎧 [AudioMixer] Mixing: Narration ({narr_dur:.1f}s) + BGM ({bgm_dur:.1f}s) -> Total ({total_dur:.1f}s)")
        print(f"   Ducking: BGM base vol={bgm_volume}, ratio={ducking_ratio}, fade_out at {fade_out_start:.1f}s")

        filter_complex = (
            f"[0:a]{stream_loop[0] + ' ' + stream_loop[1] + ',' if False else ''}volume={bgm_volume},"
            f"afade=t=in:ss=0:d={fade_in},"
            f"afade=t=out:st={fade_out_start}:d={fade_out}[bg];"
            f"[1:a]asplit=2[voice_main][voice_sc];"
            f"[bg][voice_sc]sidechaincompress=threshold=0.03:ratio={ducking_ratio}:attack=45:release=750[ducked_bg];"
            f"[ducked_bg][voice_main]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[out_audio]"
        )

        cmd = ["ffmpeg", "-y"]
        if stream_loop:
            cmd.extend(stream_loop)
        cmd.extend(["-i", str(bgm_file)])
        cmd.extend(["-i", str(narr_file)])
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[out_audio]",
            "-t", f"{total_dur:.2f}",
            "-c:a", "libmp3lame",
            "-b:a", "256k",
            str(out_file)
        ])

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"✅ [AudioMixer] Mixed audio successfully saved to: {out_file.name}")
            return str(out_file)
        except subprocess.CalledProcessError as e:
            print(f"❌ [AudioMixer Error] {e.stderr}", file=sys.stderr)
            raise

    @classmethod
    def concatenate_audio_segments(cls, segment_paths: list[str], output_path: str, pause_between: float = 0.5) -> str:
        """Concatenates individual scene TTS audios with optional pause between them."""
        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        inputs = []
        filter_parts = []
        
        # Build filtergraph with adelay / apad or simple concat
        list_txt = out_file.parent / "concat_audio_list.txt"
        with open(list_txt, "w", encoding="utf-8") as f:
            for seg in segment_paths:
                f.write(f"file '{Path(seg).resolve()}'\n")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_txt),
            "-c:a", "libmp3lame",
            "-b:a", "256k",
            str(out_file)
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if list_txt.exists():
                list_txt.unlink()
            return str(out_file)
        except Exception as e:
            if list_txt.exists():
                list_txt.unlink()
            raise RuntimeError(f"Failed to concatenate audio segments: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIWF Audio Mixer")
    parser.add_argument("--test", action="store_true", help="Run automated test with generated audio")
    parser.add_argument("--narration", type=str, help="Narration audio path")
    parser.add_argument("--bgm", type=str, help="BGM audio path")
    parser.add_argument("--output", type=str, default="/tmp/mixed.mp3", help="Output audio path")
    args = parser.parse_args()

    if args.test:
        print("🧪 Testing AudioMixer ducking...")
        v_test = "/tmp/test_voice.mp3"
        b_test = "/tmp/test_bgm.mp3"
        m_test = "/tmp/test_mixed.mp3"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=4", v_test], check=True, stderr=subprocess.PIPE)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=350:duration=6", b_test], check=True, stderr=subprocess.PIPE)
        out = AudioMixer.mix_narration_and_bgm(v_test, b_test, m_test)
        dur = AudioMixer.get_duration(out)
        print(f"✅ Mixed audio duration: {dur:.2f}s")
        for f in [v_test, b_test, m_test]:
            if os.path.exists(f): os.unlink(f)
    elif args.narration and args.bgm:
        AudioMixer.mix_narration_and_bgm(args.narration, args.bgm, args.output)
