# MouthPark — PRD

## Goal
A Python CLI that ingests an English-voice audio file and emits a South Park–style lip-synced mouth animation as a video clip with a transparent background. Output is mouth-only; the user composites it onto their own character.

## Non-goals
- Multilingual support
- Face/head animation, eyes, body
- Real-time streaming
- GUI

---

## Pipeline

```
audio file → acoustic phoneme recognition → phoneme→mouth mapping
          → frame quantization (12 FPS, min-hold) → PNG sequence → WebM/VP9 alpha
```

### 1. Phoneme recognition
- **Model:** `allosaurus` (or `wav2vec2-phoneme` as fallback). No transcript required.
- **Output:** list of `(phoneme, start_sec, end_sec)` tuples.
- **Silence:** gaps between phonemes → rest frames (fully transparent).

### 2. Phoneme → mouth mapping

| Mouth | Phonemes (ARPAbet / IPA) |
|---|---|
| `closed` | m, b, p |
| `clenched` | d, t, s, z, k, g, n, y, sh, ch, j, zh |
| `ah` | a (AA), i (AY), h (HH) |
| `ee` | e (EH), long a (EY), IY |
| `oh` | o, oh (OW), aw (AO) |
| `woo` | oo (UW), w, q (KW) |
| `bite` | f, v |
| `tongue` | l, th (TH, DH) |
| `uh` | schwa (AH0), ʌ (AH), ɜ (ER unstressed) |
| `rr` | r (R, ER stressed) |
| *(rest — no image)* | silence |

Unmapped phonemes → fall back to `clenched`.

### 3. Frame quantization (South Park feel)
- **Frame rate:** 12 FPS fixed.
- **Per frame:** choose the phoneme whose time span dominates that frame's window; if the window is mostly silence, rest.
- **Min hold:** 2 frames (~166ms). Runs shorter than that are merged into the neighbor with the greater overlap.
- **Hard cuts:** no tweening/blending between mouths.
- **Rest:** fully transparent frame.

### 4. Rendering
- **Canvas size:** native mouth PNG size (all mouth files assumed uniform dimensions; CLI validates and errors if mismatched).
- **Compositing:** each frame is either one mouth PNG copied verbatim, or a fully transparent PNG of the same dimensions.
- **Intermediate:** PNG sequence in a temp dir.
- **Final:** single-file **WebM / VP9 with alpha channel** (`-c:v libvpx-vp9 -pix_fmt yuva420p`). Alpha-preserving, widely supported by editors, far smaller than ProRes.
- **No audio** in the output; user re-muxes.

---

## CLI

```
mouthpark INPUT.wav [OUTPUT.webm]
  --fps 12              # default 12, cap enforced
  --min-hold 2          # frames
  --mouths-dir ./mouths # override mouth artwork
  --keep-frames DIR     # keep PNG sequence for debugging
  --verbose
```

Exit codes: 0 ok, 1 bad input, 2 missing mouth asset, 3 phoneme model failure.

---

## Stack
- Python 3.11+
- `allosaurus` for phoneme recognition
- `Pillow` for PNG handling / transparent canvas creation
- `ffmpeg` (system binary) for PNG-seq → WebM alpha encode
- `click` or `argparse` for CLI

---

## Assets (in `./mouths/`)
`closed, clenched, ah, ee, oh, woo, bite, tongue, uh, rr` — all present. All must share identical dimensions and transparent backgrounds.

---

## Open questions / v2
- Split `th` from `l` (currently share `tongue`).
- Optional dedicated `zh.png` (currently folds into `clenched`).
- `--size` / `--position` flags to pre-place the mouth on a larger canvas.
- Stress-based emphasis (e.g. hold wider mouth on stressed vowels).
