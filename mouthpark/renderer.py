"""Render a quantized mouth sequence to a PNG sequence and encode to WebM/VP9 alpha."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

from .mapping import MOUTH_NAMES


class MouthAssets:
    def __init__(self, mouths_dir: Path):
        self.dir = mouths_dir
        self.images: dict[str, Image.Image] = {}
        self.size: tuple[int, int] | None = None
        self._load()

    def _load(self) -> None:
        for name in MOUTH_NAMES:
            path = self.dir / f"{name}.png"
            if not path.exists():
                raise FileNotFoundError(f"Missing mouth asset: {path}")
            img = Image.open(path).convert("RGBA")
            if self.size is None:
                self.size = img.size
            elif img.size != self.size:
                raise ValueError(
                    f"Mouth asset {path} is {img.size}, expected {self.size}. "
                    "All mouth PNGs must share identical dimensions."
                )
            self.images[name] = img

    def transparent(self) -> Image.Image:
        assert self.size is not None
        return Image.new("RGBA", self.size, (0, 0, 0, 0))

    def get(self, mouth: str | None) -> Image.Image:
        if mouth is None:
            return self.images["closed"]
        return self.images[mouth]


FLESH_RGB = (241, 194, 165)  # neutral flesh tone for preview


def write_png_sequence(
    frames: list[str | None],
    assets: MouthAssets,
    out_dir: Path,
    background: tuple[int, int, int] | None = None,
) -> None:
    """Emit one PNG per frame.

    If background is given, composite each mouth over an opaque background
    of that color (useful for eyeballing the sync in non-alpha players).
    Otherwise frames keep their alpha channel.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    assert assets.size is not None
    for i, mouth in enumerate(frames):
        fg = assets.get(mouth)
        if background is not None:
            bg = Image.new("RGBA", assets.size, background + (255,))
            bg.alpha_composite(fg)
            bg.convert("RGB").save(out_dir / f"frame_{i:06d}.png")
        else:
            fg.save(out_dir / f"frame_{i:06d}.png")


def encode_webm(
    frames_dir: Path,
    output: Path,
    fps: int,
    *,
    alpha: bool = True,
    audio_path: Path | None = None,
) -> None:
    """PNG sequence → WebM/VP9. Alpha preserved when alpha=True."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ERROR: ffmpeg not found on PATH.", file=sys.stderr)
        sys.exit(3)

    cmd = [
        ffmpeg, "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%06d.png"),
    ]
    if audio_path is not None:
        cmd += ["-i", str(audio_path)]

    cmd += [
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p" if alpha else "yuv420p",
        "-b:v", "0",
        "-crf", "30",
        "-auto-alt-ref", "0",
    ]

    if audio_path is not None:
        cmd += [
            "-c:a", "libopus",
            "-b:a", "128k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
        ]

    cmd.append(str(output))
    subprocess.run(cmd, check=True)
