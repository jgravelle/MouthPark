# MouthPark

South Park-style lip-synced mouth animation from an audio file. 

**Input:** an English-voice audio file (`.wav`, `.mp3`, anything ffmpeg can read).
**Output:** a WebM video (VP9 + alpha) of the mouth only, on a transparent background, ready to composite onto your own character.

```
audio  →  phoneme recognition (allosaurus)
       →  phoneme → mouth mapping (10 shapes)
       →  frame quantization (18 FPS, min-hold)
       →  PNG sequence
       →  WebM / VP9 with alpha
```

---

## Quick start

Requires **Python 3.11+** and **ffmpeg** on PATH.

```bash
git clone https://github.com/jgravelle/MouthPark.git
cd MouthPark
pip install .
mouthpark path/to/voice.mp3
# → writes path/to/voice.webm
```

The first run downloads the `allosaurus` phoneme model (~30 MB) and caches it. Subsequent runs are fast.

### Without installing

```bash
pip install -r requirements.txt
python -m mouthpark path/to/voice.mp3
```

### Installing ffmpeg

| OS | Command |
|---|---|
| macOS | `brew install ffmpeg` |
| Ubuntu/Debian | `sudo apt install ffmpeg` |
| Windows (winget) | `winget install ffmpeg` |
| Windows (choco) | `choco install ffmpeg` |

Verify: `ffmpeg -version`.

---

## Usage

```bash
mouthpark INPUT [OUTPUT] [OPTIONS]
```

If `OUTPUT` is omitted, writes `INPUT` with a `.webm` extension next to the input.

### Options

| Flag | Default | Description |
|---|---|---|
| `--fps N` | `18` | Output frame rate. |
| `--min-hold N` | `2` | Minimum frames a mouth shape must hold. Short runs merge into a neighbor. |
| `--mouths-dir DIR` | `mouths` | Directory of mouth PNGs. |
| `--keep-frames DIR` | — | Save the intermediate PNG sequence for debugging. |
| `--background` | off | Render over a flesh-toned opaque background (alpha disabled — handy for previewing in players that don't handle alpha WebM). |
| `--bg-color #RRGGBB` | — | Custom background hex color; implies `--background`. |
| `--with-audio` | off | Mux the input audio into the output WebM (Opus, 128kbps). |
| `-v, --verbose` | off | Log duration, event count, and frame count. |

### Examples

```bash
# Alpha WebM for compositing
mouthpark voice.mp3

# Preview with audio + flesh-toned background
mouthpark voice.mp3 --background --with-audio

# Custom background color
mouthpark voice.mp3 --bg-color "#80c080"

# Keep the PNG sequence to inspect frames
mouthpark voice.mp3 --keep-frames ./frames -v
```

### Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | Bad input |
| 2 | Missing / mismatched mouth asset |
| 3 | Phoneme recognition failure |

---

## Mouth assets

10 PNG files in `mouths/`. **All must share identical dimensions and have transparent backgrounds.**

| File | Phoneme bucket |
|---|---|
| `closed.png` | m, b, p, glottal stop, **silence** |
| `clenched.png` | d, t, s, z, k, g, n, y, sh, ch, j, zh |
| `ah.png` | a, æ, ɑ, aɪ, aʊ, ɒ, h |
| `ee.png` | e (short), ɛ, eɪ, i, iː, ɪ |
| `oh.png` | o, oʊ, ɔ, ɔː, ɔɪ |
| `woo.png` | u, uː, ʊ, w |
| `bite.png` | f, v |
| `tongue.png` | l, θ, ð, **plus bare `e`** (allosaurus emits this for letter-name "A") |
| `uh.png` | ʌ, ɜ (the stressed "cup" vowel only) |
| `rr.png` | r, ɹ, ɻ, ɝ |

**Silence** (and reduction schwa `ə`, `ɚ`) → `closed.png`.

The full mapping lives in [`mouthpark/mapping.py`](mouthpark/mapping.py); tweak it freely for your voice / style.

### Replacing the art

Drop-in replacement is supported — ship your own 10 PNGs (same filenames, same size, transparent background) and pass `--mouths-dir path/to/your/mouths`.

---

## How the timing works

- Allosaurus emits each phoneme as a short ~45 ms pulse.
- Each pulse is extended forward until the next pulse starts, capped by:
  - `VOWEL_HOLD = 2.0s` for vowel phonemes (lets "ohhhh" hold `oh.png` through the elongation).
  - `SILENCE_GAP = 0.25s` for consonants.
- Beyond the cap, frames fall through to **rest** (rendered as `closed.png`).
- A `min-hold` pass merges any run shorter than `--min-hold` frames into its larger neighbor, so individual frames don't flicker.

Knobs live in [`mouthpark/quantizer.py`](mouthpark/quantizer.py).

---

## Project layout

```
MouthPark/
├── mouthpark/
│   ├── cli.py          # Click entrypoint
│   ├── recognizer.py   # allosaurus wrapper → PhonemeEvent list
│   ├── mapping.py      # IPA → mouth shape table
│   ├── quantizer.py    # events → per-frame mouth sequence
│   └── renderer.py     # PNGs → WebM/VP9 (alpha or background)
├── mouths/             # the 10 reference mouth PNGs
├── characters/         # sample characters to composite mouths onto
├── test.mp3, test02.mp3, test03.mp3   # regression samples
├── pyproject.toml
└── requirements.txt
```

---

## Troubleshooting

**`No module named 'allosaurus'`** — the Python interpreter you're invoking isn't the one `pip install` targeted. Run `pip install .` with the same Python (`python -m pip install .`), or use a virtualenv.

**`ffmpeg not found on PATH`** — install ffmpeg (see table above) and restart your shell.

**UTF-8 / `UnicodeEncodeError` on Windows** — set `PYTHONIOENCODING=utf-8` before running (IPA symbols don't fit in cp1252).

**Mouth looks wrong on a specific vowel** — allosaurus's perception may differ from your ear. Run with `-v` and dump events:

```python
from mouthpark.recognizer import recognize
from mouthpark.mapping import phoneme_to_mouth
for e in recognize("voice.mp3"):
    print(e.start, e.phoneme, phoneme_to_mouth(e.phoneme))
```

Then adjust `IPA_TO_MOUTH` in `mapping.py`.

---

## Non-goals

- Multilingual support (English voice model only)
- Face/head/body animation, eye blinks
- Real-time streaming
- GUI

---

## License

MIT.
