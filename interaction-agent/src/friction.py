"""Friction heuristics for Soofi session logging."""

import re

# Each entry: (compiled pattern, subtype).  All matches → confidence:low.
_FRICTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(nein[,!]?\s|nee[,!]?\s|falsch|nicht gemeint|ich meine|ich meinte|"
            r"gemeint war|das stimmt nicht|das stimmt nicht ganz|missverstanden|nicht richtig|"
            r"eigentlich wollte|eigentlich meinte)\b",
            re.I,
        ),
        "correction",
    ),
    (
        re.compile(
            r"\b(no[,!]?\s|wrong|i mean|i meant|that'?s not|not what i meant)\b",
            re.I,
        ),
        "correction",
    ),
    (
        re.compile(
            r"\b(können Sie das präzisier|was meinen Sie|ich verstehe nicht|"
            r"bitte erkläre|nicht klar|unklar)\b",
            re.I,
        ),
        "clarification_request",
    ),
    (
        re.compile(
            r"\b(und was ist mit|aber was|haben Sie vergessen|nicht erwähnt|fehlt noch|"
            r"da fehlt|fehlt da|fehlt noch|was ist mit|naja[,!]?\s|nur .{0,30}fehlt)\b",
            re.I,
        ),
        "incomplete_answer",
    ),
    (
        re.compile(
            r"\b(hätte erwartet|hätte ich erwartet|ich hätte .{0,20}erwartet|"
            r"warum hast du (das )?nicht|warum haben Sie (das )?nicht|"
            r"das hätte|solltest du|hättest du)\b",
            re.I,
        ),
        "unexpected_behavior",
    ),
]


def detect_friction(text: str) -> tuple[str, str] | None:
    """Return (subtype, confidence) if a friction pattern matches, else None."""
    for pattern, subtype in _FRICTION_PATTERNS:
        if pattern.search(text):
            return subtype, "low"
    return None
