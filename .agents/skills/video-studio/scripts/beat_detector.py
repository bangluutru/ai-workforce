#!/usr/bin/env python3
"""
AIWF Video Studio — Beat Detector
Phát hiện nhịp (beat) tự động từ file audio/video bằng librosa.
"""
import json
import sys
import os
import subprocess
import tempfile

def extract_audio(video_path, output_path=None):
    """Trích xuất audio từ video thành WAV."""
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
        output_path
    ], capture_output=True, check=True)
    return output_path

def detect_beats(audio_path, hop_length=512):
    """Phát hiện beat timestamps từ file audio."""
    import librosa
    import numpy as np

    # Load audio
    y, sr = librosa.load(audio_path, sr=22050, mono=True)
    duration = len(y) / sr

    # Beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length).tolist()

    # Extract tempo value (librosa 1.0 returns ndarray)
    if isinstance(tempo, np.ndarray):
        tempo_val = float(tempo.flat[0]) if tempo.size > 0 else 120.0
    else:
        tempo_val = float(tempo)

    # Onset detection (cho chi tiết hơn)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length).tolist()

    return {
        "duration": round(duration, 3),
        "tempo": round(tempo_val, 1),
        "sample_rate": sr,
        "beats": [round(t, 3) for t in beat_times],
        "onsets": [round(t, 3) for t in onset_times],
        "beat_count": len(beat_times),
        "onset_count": len(onset_times)
    }

def get_waveform_peaks(audio_path, num_peaks=800):
    """Tạo waveform peaks cho hiển thị UI."""
    import librosa
    import numpy as np

    y, sr = librosa.load(audio_path, sr=22050, mono=True)
    # Chia thành num_peaks segments
    segment_size = max(1, len(y) // num_peaks)
    peaks = []
    for i in range(0, len(y), segment_size):
        segment = y[i:i + segment_size]
        if len(segment) > 0:
            peaks.append(round(float(np.max(np.abs(segment))), 4))
    return {
        "peaks": peaks[:num_peaks],
        "duration": round(len(y) / sr, 3),
        "sample_rate": sr
    }

def analyze_media(file_path):
    """Phân tích toàn diện file media — trả về beats + waveform + metadata."""
    # Nếu là video, trích xuất audio trước
    ext = os.path.splitext(file_path)[1].lower()
    audio_path = file_path
    is_video = ext in [".mp4", ".mkv", ".avi", ".mov", ".webm"]

    if is_video:
        audio_path = extract_audio(file_path)

    try:
        beats = detect_beats(audio_path)
        waveform = get_waveform_peaks(audio_path)

        # Get video metadata if applicable
        metadata = {"is_video": is_video, "file": file_path}
        if is_video:
            probe = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_streams", "-show_format", file_path
            ], capture_output=True, text=True)
            if probe.returncode == 0:
                info = json.loads(probe.stdout)
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "video":
                        metadata["width"] = stream.get("width")
                        metadata["height"] = stream.get("height")
                        metadata["fps"] = eval(stream.get("r_frame_rate", "30/1"))
                        break
                fmt = info.get("format", {})
                metadata["duration"] = float(fmt.get("duration", 0))
                metadata["size_mb"] = round(int(fmt.get("size", 0)) / 1048576, 1)

        return {**beats, "waveform": waveform["peaks"], "metadata": metadata}
    finally:
        if is_video and audio_path != file_path and os.path.exists(audio_path):
            os.unlink(audio_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python beat_detector.py <audio_or_video_file>")
        sys.exit(1)
    result = analyze_media(sys.argv[1])
    print(json.dumps(result, indent=2))
