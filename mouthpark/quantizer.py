"""Convert a timed phoneme stream into a fixed-FPS mouth-per-frame sequence.

Rules:
- Fixed FPS (default 12).
- For each frame window, pick the mouth shape whose phonemes dominate that
  window by total time. Silence gaps count toward REST.
- Apply min-hold: any run shorter than min_hold frames is merged into the
  adjacent run it overlaps most.
"""
from __future__ import annotations

from collections import defaultdict

from .mapping import REST, is_vowel, phoneme_to_mouth
from .recognizer import PhonemeEvent

# Allosaurus emits each phoneme as a short ~45ms pulse. Consonants are genuinely
# brief, but vowels are typically held (an elongated "ohhhh" still emits one
# pulse). So we extend each event to the next event's start, capped by:
#   VOWEL_HOLD  — how long a vowel mouth may hold across silence (elongation)
#   SILENCE_GAP — how long a consonant mouth may hold across silence
# Beyond the cap, the frame falls through to REST (rendered as closed.png).
VOWEL_HOLD = 2.0    # seconds
SILENCE_GAP = 0.25  # seconds


def _frame_dominant_mouth(
    frame_start: float,
    frame_end: float,
    events: list[PhonemeEvent],
) -> str | None:
    """Return the mouth shape with the most overlap in [frame_start, frame_end)."""
    totals: dict[str | None, float] = defaultdict(float)
    frame_len = frame_end - frame_start
    covered = 0.0

    for ev in events:
        if ev.end <= frame_start:
            continue
        if ev.start >= frame_end:
            break
        lo = max(ev.start, frame_start)
        hi = min(ev.end, frame_end)
        overlap = hi - lo
        if overlap <= 0:
            continue
        mouth = phoneme_to_mouth(ev.phoneme)
        totals[mouth] += overlap
        covered += overlap

    rest_time = max(0.0, frame_len - covered)
    totals[REST] += rest_time

    if not totals:
        return REST
    return max(totals.items(), key=lambda kv: kv[1])[0]


def _extend_events(events: list[PhonemeEvent]) -> list[PhonemeEvent]:
    """Hold each phoneme until the next; vowels hold longer than consonants."""
    out: list[PhonemeEvent] = []
    for i, ev in enumerate(events):
        next_start = events[i + 1].start if i + 1 < len(events) else float("inf")
        cap = VOWEL_HOLD if is_vowel(ev.phoneme) else SILENCE_GAP
        hold_until = min(next_start, ev.end + cap)
        new_end = max(ev.end, hold_until)
        out.append(PhonemeEvent(ev.phoneme, ev.start, new_end))
    return out


def quantize(
    events: list[PhonemeEvent],
    duration: float,
    fps: int = 12,
    min_hold: int = 2,
) -> list[str | None]:
    """Return a list of mouth shape names (or None for rest), one per frame."""
    events = sorted(events, key=lambda e: e.start)
    events = _extend_events(events)
    n_frames = max(1, int(round(duration * fps)))
    frame_len = 1.0 / fps

    frames: list[str | None] = []
    for i in range(n_frames):
        frames.append(_frame_dominant_mouth(i * frame_len, (i + 1) * frame_len, events))

    return _enforce_min_hold(frames, min_hold)


def _enforce_min_hold(frames: list[str | None], min_hold: int) -> list[str | None]:
    """Merge runs shorter than min_hold into their longer neighbor."""
    if min_hold <= 1 or not frames:
        return frames

    # Encode as runs
    runs: list[list] = []  # [mouth, length]
    for f in frames:
        if runs and runs[-1][0] == f:
            runs[-1][1] += 1
        else:
            runs.append([f, 1])

    changed = True
    while changed:
        changed = False
        for i, run in enumerate(runs):
            if run[1] >= min_hold:
                continue
            # Merge into the larger neighbor
            prev_run = runs[i - 1] if i > 0 else None
            next_run = runs[i + 1] if i + 1 < len(runs) else None
            target = None
            if prev_run and next_run:
                target = prev_run if prev_run[1] >= next_run[1] else next_run
            elif prev_run:
                target = prev_run
            elif next_run:
                target = next_run
            if target is None:
                break
            target[1] += run[1]
            runs.pop(i)
            changed = True
            break

        # Coalesce adjacent runs with same mouth after a merge
        if changed:
            coalesced: list[list] = []
            for r in runs:
                if coalesced and coalesced[-1][0] == r[0]:
                    coalesced[-1][1] += r[1]
                else:
                    coalesced.append(r)
            runs = coalesced

    out: list[str | None] = []
    for mouth, length in runs:
        out.extend([mouth] * length)
    return out
