"""Speech text extraction — generates speakable prose for TTS from responses."""

import re

from .i18n import Language, tr

_RE_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_RE_MD_FORMAT = re.compile(r"[*_`]+")
_RE_WHITESPACE = re.compile(r"\s+")
_SPEECH_MIN_CHARS = 15  # don't speak trivially short responses
RE_SENTENCE_END = re.compile(r"(?<![A-Z0-9])[.!?]\s")  # sentence boundary for early TTS trigger
# Lines that start a structured markdown block — stop collecting intro before these
_RE_STRUCTURE_LINE = re.compile(r"^\s*(?:#{1,6}\s|[-*]\s|\d+\.\s)")
_SPEECH_MAX_CHARS = 200  # upper limit to avoid reading very long intros


def generate_speech_text(
    text: str, *, has_search_results: bool = False, lang: Language = "de"
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

    return " ".join(result).strip()
