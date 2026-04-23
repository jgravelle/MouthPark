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
    # ah: A-vowels, I-diphthong, h
    "a": "ah", "ɑ": "ah", "æ": "ah", "aɪ": "ah", "aʊ": "ah", "h": "ah",
    # ee: E-vowels, long A, high-front I
    "i": "ee", "iː": "ee", "ɪ": "ee", "ɛ": "ee", "eɪ": "ee",
    # bare "e" — allosaurus emits this for letter-name "A" → render as tongue
    "e": "tongue",
    # oh: O-vowels, aw
    "o": "oh", "oʊ": "oh", "ɔ": "oh", "ɔː": "oh", "ɔɪ": "oh",
    # woo: U-vowels, w
    "u": "woo", "uː": "woo", "ʊ": "woo", "w": "woo",
    # bite: f, v
    "f": "bite", "v": "bite",
    # tongue: l, th
    "l": "tongue", "θ": "tongue", "ð": "tongue",
    # uh: cup vowel only (genuine stressed "uh" as in "cup").
    # Schwa (ə) and r-colored schwa (ɚ) are reduction vowels — mapping them to
    # uh made uh.png appear everywhere. They now fall through to FALLBACK and
    # are filtered in phoneme_to_mouth below → render as REST (closed).
    "ʌ": "uh", "ɜ": "uh",
    # rr: r, stressed ER, retroflex approximant
    "r": "rr", "ɹ": "rr", "ɻ": "rr", "ɝ": "rr",
    # open back round (British "lot") → ah family
    "ɒ": "ah",
    # glottal stop → brief closure
    "ʔ": "closed",
}

VOWEL_SHAPES = {"ah", "ee", "oh", "woo", "uh"}

# IPA phonemes that should hold across silence (elongation), regardless of
# which mouth shape they render as. Used by the quantizer's hold cap so the
# letter-name "A" (emitted as `e`, rendered as tongue) holds like a real vowel.
VOWEL_PHONEMES = {
    "a", "ɑ", "æ", "aɪ", "aʊ", "ɒ",
    "e", "ɛ", "eɪ", "i", "iː", "ɪ",
    "o", "oʊ", "ɔ", "ɔː", "ɔɪ",
    "u", "uː", "ʊ",
    "ʌ", "ɜ", "ɝ",
}


def is_vowel(ipa: str) -> bool:
    if not ipa:
        return False
    cleaned = ipa.replace("ː", "").replace("ˈ", "").replace("ˌ", "").strip()
    return cleaned in VOWEL_PHONEMES or (len(cleaned) > 1 and cleaned[0] in VOWEL_PHONEMES)

FALLBACK = "clenched"

MOUTH_NAMES = {
    "closed", "clenched", "ah", "ee", "oh", "woo",
    "bite", "tongue", "uh", "rr",
}


SILENT_PHONEMES = {"ə", "ɚ"}  # reduction vowels → no mouth (render as closed)


def phoneme_to_mouth(ipa: str):
    """Map an IPA phoneme to a mouth name, or None for rest.

    Strips length/stress markers before lookup. Schwa-class reduction vowels
    are treated as rest. Unmapped phonemes → FALLBACK.
    """
    if not ipa:
        return FALLBACK
    cleaned = ipa.replace("ː", "").replace("ˈ", "").replace("ˌ", "").strip()
    if cleaned in SILENT_PHONEMES:
        return REST
    if cleaned in IPA_TO_MOUTH:
        return IPA_TO_MOUTH[cleaned]
    if len(cleaned) > 1 and cleaned[0] in IPA_TO_MOUTH:
        return IPA_TO_MOUTH[cleaned[0]]
    return FALLBACK
