from __future__ import annotations

import io

from pydub import AudioSegment
from pydub.effects import compress_dynamic_range


def merge_segments(
    segments: list[bytes],
    pause_ms: int = 500,
) -> AudioSegment:
    """Concatenate audio byte-blobs with a silence gap between each."""
    silence = AudioSegment.silent(duration=pause_ms)
    combined = AudioSegment.empty()

    for i, raw in enumerate(segments):
        audio = AudioSegment.from_file(io.BytesIO(raw), format="mp3")
        combined = combined + audio
        if i < len(segments) - 1:
            combined = combined + silence

    return combined


def insert_silence(audio: AudioSegment, duration_ms: int) -> AudioSegment:
    return audio + AudioSegment.silent(duration=duration_ms)


def normalize_volume(
    audio: AudioSegment,
    target_lufs: float = -16.0,
) -> AudioSegment:
    """Normalize loudness toward target LUFS, falling back to dBFS if needed."""
    try:
        import numpy as np
        import pyloudnorm as pyln

        samples = np.array(audio.get_array_of_samples()).astype(float)
        if audio.channels > 1:
            samples = samples.reshape((-1, audio.channels))
        samples /= float(1 << (8 * audio.sample_width - 1))
        meter = pyln.Meter(audio.frame_rate)
        loudness = meter.integrated_loudness(samples)
        if loudness == float("-inf"):
            return audio
        return audio.apply_gain(target_lufs - loudness)
    except Exception:
        pass

    current_loudness = audio.dBFS
    if current_loudness == float("-inf"):
        return audio
    gain_db = target_lufs - current_loudness
    return audio.apply_gain(gain_db)


def limit_peaks(audio: AudioSegment, threshold_dbfs: float = -1.0) -> AudioSegment:
    """Apply light compression and peak gain trim to avoid clipping."""
    limited = compress_dynamic_range(audio, threshold=-12.0, ratio=4.0, attack=5.0, release=50.0)
    if limited.max_dBFS > threshold_dbfs:
        limited = limited.apply_gain(threshold_dbfs - limited.max_dBFS)
    return limited


def fade_edges(
    audio: AudioSegment,
    fade_in_ms: int = 500,
    fade_out_ms: int = 500,
) -> AudioSegment:
    return audio.fade_in(fade_in_ms).fade_out(fade_out_ms)


def mix_bgm(
    speech: AudioSegment,
    bgm_path: str,
    bgm_volume_db: float = -20.0,
    fade_ms: int = 1500,
) -> AudioSegment:
    """Overlay background music under speech.

    BGM is looped/trimmed to match speech duration and ducked by bgm_volume_db.
    """
    bgm_raw = AudioSegment.from_file(bgm_path)
    speech_len = len(speech)

    # Loop BGM if shorter than speech
    if len(bgm_raw) < speech_len:
        loops_needed = (speech_len // len(bgm_raw)) + 1
        bgm_raw = bgm_raw * loops_needed

    bgm_trimmed = bgm_raw[:speech_len]
    if fade_ms > 0:
        bgm_trimmed = bgm_trimmed.fade_in(fade_ms).fade_out(fade_ms)
    bgm_ducked = bgm_trimmed + bgm_volume_db

    return speech.overlay(bgm_ducked)
