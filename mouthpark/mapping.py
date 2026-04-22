"""Phoneme → mouth shape mapping.

Allosaurus emits IPA. We normalize IPA symbols into our 10 mouth shapes.
"""

REST = None  # transparent frame

IPA_TO_MOUTH = {
    # closed: m, b, p
    "m": "closed", "b": "closed", "p": "closed",
    # clenched: d, t, s, z, k, g, n, y, sh, ch, j, zh
    "d": "clenched", "t": "clenched", "s": "clenched", "z": "clenched",
    "k": "clenched", "ɡ": "clenched", "g": "clenched", "n": "clenched",
    "ŋ": "clenched", "j": "clenched",  # j in IPA = English "y"
    "ʃ": "clenched", "tʃ": "clenched", "dʒ": "clenched", "ʒ": "clenched",
    # ah: a, i (AY), h
    "a": "ah", "ɑ": "ah", "æ": "ah", "aɪ": "ah", "aʊ": "ah", "h": "ah",
    # ee: e, long a (EY), IY
    "i": "ee", "iː": "ee", "ɪ": "ee", "e": "ee", "ɛ": "ee", "eɪ": "ee",
    # oh: o, oh, aw
    "o": "oh", "oʊ": "oh", "ɔ": "oh", "ɔː": "oh", "ɔɪ": "oh",
    # woo: oo, w
    "u": "woo", "uː": "woo", "ʊ": "woo", "w": "woo",
    # bite: f, v
    "f": "bite", "v": "bite",
    # tongue: l, th
    "l": "tongue", "θ": "tongue", "ð": "tongue",
    # uh: schwa, cup vowel, unstressed ER
    "ə": "uh", "ʌ": "uh", "ɜ": "uh", "ɚ": "uh",
    # rr: r, stressed ER
    "r": "rr", "ɹ": "rr", "ɝ": "rr",
}

FALLBACK = "clenched"

MOUTH_NAMES = {
    "closed", "clenched", "ah", "ee", "oh", "woo",
    "bite", "tongue", "uh", "rr",
}


def phoneme_to_mouth(ipa: str) -> str:
    """Map an IPA phoneme to one of the mouth shape names.

    Strips length/stress markers before lookup. Unmapped phonemes → FALLBACK.
    """
    if not ipa:
        return FALLBACK
    cleaned = ipa.replace("ː", "").replace("ˈ", "").replace("ˌ", "").strip()
    if cleaned in IPA_TO_MOUTH:
        return IPA_TO_MOUTH[cleaned]
    if len(cleaned) > 1 and cleaned[0] in IPA_TO_MOUTH:
        return IPA_TO_MOUTH[cleaned[0]]
    return FALLBACK
