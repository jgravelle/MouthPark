"""Acoustic phoneme recognition via allosaurus.

Returns a list of (ipa_phoneme, start_sec, end_sec) tuples.
Allosaurus only accepts WAV, so non-wav inputs are transcoded via ffmpeg
to a temp 16kHz mono WAV first.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PhonemeEvent:
    phoneme: str
    start: float  # seconds
    end: float    # seconds


def _ensure_wav(audio_path: str) -> tuple[str, tempfile.TemporaryDirectory | None]:
    p = Path(audio_path)
    if p.suffix.lower() == ".wav":
        return str(p), None
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg required to transcode non-wav audio")
    tmp = tempfile.TemporaryDirectory(prefix="mouthpark_wav_")
    wav = Path(tmp.name) / "input.wav"
    subprocess.run(
        [ffmpeg, "-y", "-i", str(p), "-ac", "1", "-ar", "16000", str(wav)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return str(wav), tmp


def recognize(audio_path: str, lang: str = "eng") -> list[PhonemeEvent]:
    """Run allosaurus on an audio file and return timed IPA events."""
    from allosaurus.app import read_recognizer

    wav_path, tmp = _ensure_wav(audio_path)
    try:
        model = read_recognizer()
        raw = model.recognize(wav_path, lang, timestamp=True)
    finally:
        if tmp is not None:
            tmp.cleanup()

    events: list[PhonemeEvent] = []
    for line in raw.strip().splitlines():
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        start = float(parts[0])
        duration = float(parts[1])
        phoneme = parts[2]
        events.append(PhonemeEvent(phoneme, start, start + duration))
    return events
