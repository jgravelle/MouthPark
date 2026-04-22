# MouthPark

South Park–style lip-synced mouth animation from an audio file.

Input: an English-voice audio file.
Output: a WebM video (VP9 with alpha) of the mouth only, on a transparent background, at 12 FPS. Composite it onto your own character.

## Install

Requires Python 3.11+ and `ffmpeg` on PATH.

```bash
pip install -r requirements.txt
```

## Use

```bash
python -m mouthpark path/to/voice.wav
# → writes path/to/voice.webm
```

Options:

```
--fps 12              frame rate (default 12)
--min-hold 2          minimum frames a shape must hold (default 2)
--mouths-dir mouths   mouth PNG directory
--keep-frames DIR     keep intermediate PNG sequence
-v / --verbose
```

## Mouth assets

PNG files in `mouths/` — all must share identical dimensions and have transparent backgrounds.

| File | Phonemes |
|---|---|
| `closed.png` | m, b, p |
| `clenched.png` | d, t, s, z, k, g, n, y, sh, ch, j, zh |
| `ah.png` | a, i, h |
| `ee.png` | e, long a |
| `oh.png` | o, oh, aw |
| `woo.png` | oo, w |
| `bite.png` | f, v |
| `tongue.png` | l, th |
| `uh.png` | schwa, cup-vowel |
| `rr.png` | r |

Silence → fully transparent frame (no mouth shown).
