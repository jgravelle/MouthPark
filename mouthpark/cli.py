"""MouthPark CLI entrypoint."""
from __future__ import annotations

import shutil
import sys
import tempfile
import wave
from pathlib import Path

import click

from .quantizer import quantize
from .recognizer import recognize
from .renderer import FLESH_RGB, MouthAssets, encode_webm, write_png_sequence


def _parse_color(spec: str) -> tuple[int, int, int]:
    s = spec.strip().lstrip("#")
    if len(s) == 6:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    raise click.BadParameter(f"Expected #RRGGBB hex, got {spec!r}")


def _audio_duration(path: Path) -> float:
    """Best-effort duration detection. Falls back to ffprobe for non-wav."""
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as wf:
                return wf.getnframes() / float(wf.getframerate())
        except wave.Error:
            pass
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise click.ClickException("ffprobe not found; install ffmpeg or use a .wav file")
    import subprocess
    out = subprocess.check_output([
        ffprobe, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ])
    return float(out.strip())


@click.command()
@click.argument("input_audio", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("output", type=click.Path(dir_okay=False, path_type=Path), required=False)
@click.option("--fps", default=18, show_default=True, type=int, help="Output frame rate (cap).")
@click.option("--min-hold", default=2, show_default=True, type=int, help="Minimum frames a mouth shape must hold.")
@click.option("--mouths-dir", default="mouths", show_default=True, type=click.Path(path_type=Path), help="Directory containing mouth PNGs.")
@click.option("--keep-frames", default=None, type=click.Path(path_type=Path), help="Keep intermediate PNG sequence in this directory.")
@click.option("--background", "background", flag_value="flesh", default=None, help="Render over a flesh-toned opaque background for evaluation (disables alpha).")
@click.option("--bg-color", default=None, help="Custom background color as #RRGGBB (implies --background).")
@click.option("--with-audio", is_flag=True, help="Mux the input audio into the output video.")
@click.option("-v", "--verbose", is_flag=True)
def main(input_audio, output, fps, min_hold, mouths_dir, keep_frames, background, bg_color, with_audio, verbose):
    """Generate a South Park-style lip-synced mouth animation from an audio file."""
    if output is None:
        output = input_audio.with_suffix(".webm")

    if bg_color is not None:
        bg_rgb = _parse_color(bg_color)
    elif background == "flesh":
        bg_rgb = FLESH_RGB
    else:
        bg_rgb = None
    use_alpha = bg_rgb is None

    if not mouths_dir.exists():
        raise click.ClickException(f"Mouths directory not found: {mouths_dir}")

    if verbose:
        click.echo(f"Loading mouth assets from {mouths_dir}")
    try:
        assets = MouthAssets(mouths_dir)
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(2)

    if verbose:
        click.echo(f"Analyzing audio: {input_audio}")
    try:
        events = recognize(str(input_audio))
    except Exception as e:
        click.echo(f"ERROR: phoneme recognition failed: {e}", err=True)
        sys.exit(3)

    duration = _audio_duration(input_audio)
    if verbose:
        click.echo(f"Duration: {duration:.2f}s, {len(events)} phoneme events")

    frames = quantize(events, duration, fps=fps, min_hold=min_hold)
    if verbose:
        click.echo(f"Quantized to {len(frames)} frames @ {fps} FPS")

    audio_path = input_audio if with_audio else None

    if keep_frames:
        frames_dir = Path(keep_frames)
        frames_dir.mkdir(parents=True, exist_ok=True)
        write_png_sequence(frames, assets, frames_dir, background=bg_rgb)
        encode_webm(frames_dir, output, fps, alpha=use_alpha, audio_path=audio_path)
    else:
        with tempfile.TemporaryDirectory(prefix="mouthpark_") as tmp:
            frames_dir = Path(tmp)
            write_png_sequence(frames, assets, frames_dir, background=bg_rgb)
            encode_webm(frames_dir, output, fps, alpha=use_alpha, audio_path=audio_path)

    click.echo(f"Wrote {output}")


if __name__ == "__main__":
    main()
