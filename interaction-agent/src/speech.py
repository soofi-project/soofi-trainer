"""Speech text extraction — generates speakable prose for TTS from responses."""

import re

from .i18n import Language, tr

_RE_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_RE_MD_FORMAT = re.compile(r"[*_`]+")
_RE_WHITESPACE = re.compile(r"\s+")
_SPEECH_MIN_CHARS = 15  # don't speak trivially short responses
_SPEECH_MIN_RESULT_CHARS = 25  # don't emit speech for filler-only first sentences
RE_SENTENCE_END = re.compile(r"(?<![A-Z0-9])[.!?]\s")  # sentence boundary for early TTS trigger
# Lines that start a structured markdown block — stop collecting intro before these
_RE_STRUCTURE_LINE = re.compile(r"^\s*(?:#{1,6}\s|[-*]\s|\d+\.\s)")
_SPEECH_MAX_CHARS = 200  # upper limit to avoid reading very long intros
# Filler opener sentences — stripped before speaking so TTS never plays "Perfekt!" alone.
# Matches a whole short opener sentence (up to ~4 words) ending in .!? — case insensitive.
_RE_FILLER_OPENER = re.compile(
    r"^(?:"
    r"perfekt|gerne|gut|sehr gut|super|okay|ok|klar|alles klar|verstanden|"
    r"perfect|great|sure|alright|all right|got it|understood|awesome|nice"
    r")[!.?]+\s*",
    re.IGNORECASE,
)
# Abbreviations whose internal periods must not be treated as sentence endings —
# otherwise TTS stops mid-sentence at "bzw.", "z.B." etc. Mask period with \x00
# before splitting, unmask before speaking.
_ABBREV_PLACEHOLDER = "\x00"
_ABBREVIATIONS = (
    "bzw.", "z.B.", "z. B.", "u.a.", "u. a.", "d.h.", "d. h.",
    "i.d.R.", "ca.", "ggf.", "etc.", "bzgl.", "sog.", "z.T.", "evtl.",
    "Dr.", "Prof.", "St.", "Jr.", "Sr.", "usw.", "u.v.m.",
    "Abb.", "Tab.", "Nr.", "Mr.", "Mrs.", "Ms.", "vs.", "e.g.", "i.e.",
)


def _mask_abbreviations(text: str) -> str:
    for abbr in _ABBREVIATIONS:
        text = text.replace(abbr, abbr.replace(".", _ABBREV_PLACEHOLDER))
    return text


def _unmask_abbreviations(text: str) -> str:
    return text.replace(_ABBREV_PLACEHOLDER, ".")


# Insert a space after .!? when the model glued two sentences together
# (e.g. "Satz eins.Satz zwei."). Runs AFTER masking, so abbreviation periods
# (now \x00) are untouched.
_RE_MISSING_SENTENCE_SPACE = re.compile(r"([.!?])(?=[^\s.!?])")


def _normalize_sentence_spacing(text: str) -> str:
    return _RE_MISSING_SENTENCE_SPACE.sub(r"\1 ", text)


def generate_speech_text(
    text: str,
    *,
    has_search_results: bool = False,
    lang: Language = "de",
    is_final: bool = False,
) -> str:
    """Extract speakable intro prose from a Markdown response for TTS.

    - Collects lines up to the first structural element (header, bullet, list)
    - If the whole response is structural, returns a static fallback phrase
    - Reads all intro sentences; stops and converts a colon-ending sentence
      (which would introduce a list) to a period so it sounds natural
    """
    # Collect only the intro lines before any structural markdown
    intro_lines: list[str] = []
    for line in text.splitlines():
        if _RE_STRUCTURE_LINE.match(line):
            break
        intro_lines.append(line)

    intro = "\n".join(intro_lines).strip()

    # Whole response starts with structure — give a short spoken acknowledgement
    # Only use the search fallback when there were actual search results
    if not intro:
        return tr("speech_fallback", lang) if has_search_results else ""

    # Too short to speak — return empty so caller can retry after more text arrives
    if len(intro) < _SPEECH_MIN_CHARS:
        return ""

    # Strip inline markdown
    intro = _RE_MD_LINK.sub(r"\1", intro)
    intro = _RE_MD_FORMAT.sub("", intro)
    intro = _RE_WHITESPACE.sub(" ", intro).strip()

    # Strip filler opener ("Perfekt!", "Gerne!", "Perfect!" ...) so TTS never
    # plays only the filler while the real content is still streaming in.
    stripped = _RE_FILLER_OPENER.sub("", intro, count=1)
    if stripped:
        intro = stripped

    # Protect abbreviations like "bzw." from being treated as sentence endings
    intro = _mask_abbreviations(intro)
    # Split glued sentences like "eins.zwei" — abbreviations are already masked
    intro = _normalize_sentence_spacing(intro)

    # Collect sentences; rules:
    # - Only include sentences that end with proper punctuation (.!?) — trailing
    #   fragments without punctuation are incomplete (early-emission artifact)
    # - When a sentence ends with ":" it introduces a list: replace colon with
    #   "." and stop so list items are not read out
    sentences = re.split(r"(?<=[.!?])\s+", intro)
    result: list[str] = []
    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue
        if s.endswith(":"):
            result.append(s[:-1] + ".")
            break
        if not re.search(r"[.!?]$", s):
            break  # incomplete fragment — stop here
        result.append(s)
        if sum(len(x) for x in result) >= _SPEECH_MAX_CHARS:
            break

    joined = _unmask_abbreviations(" ".join(result).strip())
    # Hold back speech until we have enough content — avoids emitting single
    # short openers while longer sentences are still streaming.
    if len(joined) < _SPEECH_MIN_RESULT_CHARS:
        return ""
    # During streaming (not final), also require ≥ 2 complete sentences so we
    # don't speak just the first short sentence while the informative follow-up
    # is still streaming in. At end-of-stream a single sentence is fine.
    if not is_final and len(result) < 2:
        return ""
    return joined
