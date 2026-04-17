"""Speech text extraction — generates speakable prose for TTS from responses."""

import re

from .i18n import Language, tr

_RE_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
# Bare URLs in parentheses like "(https://hf.co/...)" — strip parens + URL entirely
_RE_URL_PARENS = re.compile(r"\(\s*https?://[^\s)]+\s*\)")
# Remaining bare URLs not in parentheses — stop at whitespace
_RE_URL_BARE = re.compile(r"https?://\S+")
_RE_MD_FORMAT = re.compile(r"[*_`]+")
_RE_WHITESPACE = re.compile(r"\s+")
_SPEECH_MIN_CHARS = 15  # don't speak trivially short responses
_SPEECH_MIN_RESULT_CHARS = 25  # don't emit speech for filler-only first sentences
# Lines that start a structured markdown block — stop collecting intro before these
_RE_STRUCTURE_LINE = re.compile(r"^\s*(?:#{1,6}\s|[-*]\s|\d+\.\s)")
# Filler opener sentences — stripped before speaking so TTS never plays "Perfekt!" alone.
# Matches a whole short opener sentence (up to ~4 words) ending in .!? — case insensitive.
_RE_FILLER_OPENER = re.compile(
    r"^(?:"
    r"perfekt|gerne|gut|sehr gut|super|okay|ok|klar|alles klar|verstanden|"
    r"hallo|hi|hey|hallöchen|guten tag|guten morgen|guten abend|grüß dich|servus|"
    r"perfect|great|sure|alright|all right|got it|understood|awesome|nice|"
    r"hello|good morning|good afternoon|good evening|greetings"
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
    # Version numbers — prevent "4.0" → "4. 0" which would trigger a false sentence split
    "1.0", "2.0", "3.0", "4.0", "5.0",
    "1.1", "2.1", "3.1", "4.1",
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
    streaming: bool = True,
) -> str:
    """Extract the first speakable sentence from a Markdown response for TTS.

    - Collects lines up to the first structural element (header, bullet, list)
    - If the whole response is structural, returns a static fallback phrase
    - Returns only the first complete sentence; a colon-ending sentence is
      converted to a period (list follow-ups are not spoken)
    - streaming=True (default): a period at the very end of the buffer is treated
      as potentially incomplete (e.g. "4." before "0" arrives) — wait for more text.
      streaming=False: called after the response is complete, accept period-ending sentences.
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

    # Strip inline markdown and bare URLs
    intro = _RE_MD_LINK.sub(r"\1", intro)
    intro = _RE_URL_PARENS.sub("", intro)
    intro = _RE_URL_BARE.sub("", intro)
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

    # Speak complete sentences. Rules:
    # - Sentence must end with proper punctuation (.!?) — incomplete fragments
    #   without punctuation are early-emission artifacts; return empty and let
    #   the caller retry once more text has streamed in.
    # - A sentence ending in ":" introduces a list: swap ":" for "." and stop.
    # - streaming=True: take only the first sentence (hold-back handles short
    #   openers by returning ""). streaming=False: keep concatenating until the
    #   min-length bar is cleared, so short acknowledgements like "Das klingt
    #   gut!" don't silence the whole response.
    sentences = re.split(r"(?<=[.!?])\s+", intro)
    collected: list[str] = []
    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue
        if s.endswith(":"):
            collected.append(s[:-1] + ".")
            break
        if not re.search(r"[.!?]$", s):
            break
        # During streaming the buffer may end mid-number: "4." could be "4.0" not yet
        # fully arrived. Only accept a period-ending sentence when confirmed by
        # following text (i.e. not the last segment in the split).
        # After streaming ends (streaming=False) this guard is skipped.
        if streaming and s is sentences[-1] and s.endswith("."):
            break
        collected.append(s)
        joined_so_far = _unmask_abbreviations(" ".join(collected))
        if streaming or len(joined_so_far) >= _SPEECH_MIN_RESULT_CHARS:
            break

    if not collected:
        return ""
    joined = _unmask_abbreviations(" ".join(collected))
    # Hold back speech if the collected text is too short — during streaming
    # this avoids a trivial opener while the informative follow-up is still
    # arriving; after streaming ends it means the whole response was trivial.
    if len(joined) < _SPEECH_MIN_RESULT_CHARS:
        return ""
    # Strip a trailing period — TTS produces a softer cadence without the hard
    # stop. "!" and "?" are kept because they carry intonation.
    if joined.endswith("."):
        joined = joined[:-1]
    return joined


# Boundary: sentence-ending punctuation followed by whitespace, OR any run of
# newlines. Used to locate the start of the trailing question across list items
# and paragraph breaks without collapsing them into one sentence first.
_RE_TRAILING_BOUNDARY = re.compile(r"[.!?]+\s+|\n+")


def generate_trailing_question_speech_text(text: str) -> str:
    """If the final sentence of ``text`` ends with '?', return a speakable copy.

    The whole response is examined (not just the intro) — this lets us pick up
    follow-up questions that come after structural markdown (lists, headers).
    """
    cleaned = _RE_MD_LINK.sub(r"\1", text)
    cleaned = _RE_URL_PARENS.sub("", cleaned)
    cleaned = _RE_URL_BARE.sub("", cleaned)
    cleaned = _RE_MD_FORMAT.sub("", cleaned).rstrip()
    if not cleaned.endswith("?"):
        return ""
    masked = _mask_abbreviations(cleaned)
    # Walk all boundaries before the final '?' — the last boundary marks the
    # start of the trailing question.
    boundary = 0
    for match in _RE_TRAILING_BOUNDARY.finditer(masked):
        if match.end() < len(masked):
            boundary = match.end()
    question = masked[boundary:]
    # Strip leading list markers (e.g. "- ", "* ", "1. ") so TTS doesn't read them
    question = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", question)
    question = _RE_WHITESPACE.sub(" ", question).strip()
    if not question.endswith("?"):
        return ""
    return _unmask_abbreviations(question)


def normalize_speech_for_dedup(text: str) -> str:
    """Normalize speech text for loose containment checks across clips."""
    return _RE_WHITESPACE.sub(" ", text.lower()).strip().rstrip("?.!,;:")


def generate_transition_speech_text(text: str) -> str:
    """Speakable version of a transition follow-up question.

    Unlike ``generate_speech_text`` this keeps the full text (no first-sentence
    split, no filler-opener stripping) — transitions are short and must be
    spoken completely.
    """
    cleaned = _RE_MD_LINK.sub(r"\1", text)
    cleaned = _RE_URL_PARENS.sub("", cleaned)
    cleaned = _RE_URL_BARE.sub("", cleaned)
    cleaned = _RE_MD_FORMAT.sub("", cleaned)
    cleaned = _RE_WHITESPACE.sub(" ", cleaned).strip()
    if not cleaned:
        return ""
    if cleaned.endswith("."):
        cleaned = cleaned[:-1]
    return cleaned
