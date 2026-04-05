"""Session logging for the Soofi Interaction Agent.

Creates one Markdown file per session in session-logs/ immediately on first request.
Every event is flushed to disk continuously — no data loss on crash or browser close.
YAML frontmatter is prepended once on session close (rewrite) so counters are accurate.
"""

import asyncio
import collections
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SESSION_LOG_ENABLED: bool = os.getenv("SESSION_LOG_ENABLED", "true").lower() == "true"
SESSION_LOG_DIR: Path = Path(os.getenv("SESSION_LOG_DIR", "/app/session-logs"))
SESSION_LOG_TIMEOUT_S: int = int(os.getenv("SESSION_LOG_TIMEOUT_S", "300"))

# ---------------------------------------------------------------------------
# Friction heuristics
# ---------------------------------------------------------------------------

# Each entry: (compiled pattern, subtype).  All matches → confidence:low.
_FRICTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(nein[,!]?\s|falsch|nicht gemeint|ich meine|gemeint war|"
            r"das stimmt nicht|missverstanden|nicht richtig)\b",
            re.I,
        ),
        "correction",
    ),
    (
        re.compile(
            r"\b(no[,!]?\s|wrong|i mean|that'?s not|not what i meant)\b",
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
            r"was ist mit)\b",
            re.I,
        ),
        "incomplete_answer",
    ),
]


def _detect_friction(text: str) -> tuple[str, str] | None:
    """Return (subtype, confidence) if a friction pattern matches, else None."""
    for pattern, subtype in _FRICTION_PATTERNS:
        if pattern.search(text):
            return subtype, "low"
    return None


# ---------------------------------------------------------------------------
# SessionLogger
# ---------------------------------------------------------------------------


class SessionLogger:
    """Logs one Soofi session to a Markdown file, written continuously."""

    def __init__(
        self, session_id: str, language: str = "de", log_dir: Path | None = None
    ) -> None:
        self.session_id = session_id
        self.language = language
        self.started_at = datetime.now()

        self._message_count = 0
        self._advisor_calls = 0
        self._training_calls = 0
        self._rag_sources_total = 0
        self._friction_events = 0
        self._recommendation = "none"
        self._training_started = False
        self._last_user_ts: datetime | None = None
        self._timeout_task: asyncio.Task[None] | None = None

        self._log_dir = log_dir or SESSION_LOG_DIR
        self._log_dir.mkdir(parents=True, exist_ok=True)
        ts = self.started_at.strftime("%Y-%m-%d_%H-%M-%S")
        short_id = session_id[:8] if session_id else uuid.uuid4().hex[:8]
        self._path = self._log_dir / f"{ts}_{short_id}.md"

        with open(self._path, "w", encoding="utf-8") as f:
            f.write(f"# Soofi Session — {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Verlauf\n\n")
            f.flush()

        logger.info("Session log created: %s", self._path.name)

    # -- internal helpers ----------------------------------------------------

    def _append(self, text: str) -> None:
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(text)
            f.flush()

    async def _run_timeout(self, timeout_s: int) -> None:
        try:
            await asyncio.sleep(timeout_s)
            _sessions.pop(self.session_id, None)
            self.finalize("timeout")
        except asyncio.CancelledError:
            pass

    # -- public API ----------------------------------------------------------

    async def reset_timeout(self) -> None:
        """Cancel any existing inactivity timeout and start a fresh one."""
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()
        self._timeout_task = asyncio.create_task(self._run_timeout(SESSION_LOG_TIMEOUT_S))

    def log_user_message(self, text: str) -> None:
        self._message_count += 1
        self._last_user_ts = datetime.now()
        ts = self._last_user_ts.strftime("%H:%M:%S")
        friction = _detect_friction(text)
        if friction:
            subtype, confidence = friction
            self._friction_events += 1
            self._append(
                f"<!-- type:friction subtype:{subtype} confidence:{confidence} ts:{ts} -->\n"
                f"<!-- friction: {text[:200].replace(chr(10), ' ')} -->\n"
                f"**[{ts}] Benutzer:**\n{text}\n\n"
            )
        else:
            self._append(
                f"<!-- type:user ts:{ts} -->\n"
                f"**[{ts}] Benutzer:**\n{text}\n\n"
            )

    def log_tool_call(self, tool_name: str, query: str = "") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        q = query[:120]
        if tool_name == "ask_advisor_tool":
            self._advisor_calls += 1
            self._append(
                f'<!-- type:tool_call tool:ask_advisor ts:{ts} query:"{q}" -->\n'
                f'**[{ts}] → Advisor** *(Suche: "{q}")*\n\n'
            )
        elif tool_name == "ask_training_agent_tool":
            self._training_calls += 1
            self._append(
                f'<!-- type:tool_call tool:ask_training_agent ts:{ts} query:"{q}" -->\n'
                f"**[{ts}] → Training Agent**\n\n"
            )
        elif tool_name == "ask_dataset_agent_tool":
            self._append(
                f'<!-- type:tool_call tool:ask_dataset_agent ts:{ts} query:"{q}" -->\n'
                f"**[{ts}] → Dataset Agent**\n\n"
            )

    def log_rag_sources(self, sources: list[dict[str, Any]]) -> None:
        if not sources:
            return
        self._rag_sources_total += len(sources)
        ts = datetime.now().strftime("%H:%M:%S")
        self._append(
            f"<!-- type:rag_sources ts:{ts} count:{len(sources)} -->\n"
            f"**[{ts}] RAG-Quellen:**\n"
        )
        for s in sources:
            file_name = s.get("file", s.get("source", s.get("title", "?")))
            section = s.get("section", "")
            score = s.get("score", None)
            line = f"- `{file_name}`"
            if section:
                line += f" § {section}"
            if score is not None:
                line += f" — Score: {score:.2f}" if isinstance(score, float) else f" — Score: {score}"
            self._append(line + "\n")
        self._append("\n")

    def log_agent_response(self, text: str) -> None:
        now = datetime.now()
        ts = now.strftime("%H:%M:%S")
        latency_ms: int | str = ""
        if self._last_user_ts:
            latency_ms = int((now - self._last_user_ts).total_seconds() * 1000)
        self._append(
            f"<!-- type:agent ts:{ts} latency_ms:{latency_ms} -->\n"
            f"**[{ts}] Soofi:**\n{text}\n\n"
        )
        # Heuristic recommendation detection
        text_lower = text.lower()
        if self._recommendation == "none":
            if "qlora" in text_lower:
                self._recommendation = "qlora"
            elif "lora" in text_lower:
                self._recommendation = "lora_finetuning"
            elif "rag" in text_lower or "retrieval" in text_lower:
                self._recommendation = "rag"

    def log_training_started(self, job_id: str) -> None:
        self._training_started = True
        ts = datetime.now().strftime("%H:%M:%S")
        self._append(
            f"<!-- type:training_started ts:{ts} job_id:{job_id} -->\n"
            f"**[{ts}] Training gestartet** (Job: `{job_id}`)\n\n"
        )

    def log_error(self, error: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._append(
            f"<!-- type:error ts:{ts} -->\n"
            f"**[{ts}] Fehler:** {error[:300]}\n\n"
        )

    def finalize(self, end_reason: str = "normal") -> None:
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()

        ended_at = datetime.now()
        duration_s = int((ended_at - self.started_at).total_seconds())
        ts = ended_at.strftime("%H:%M:%S")

        self._append(
            f"<!-- type:session_end ts:{ts} reason:{end_reason} -->\n\n"
            f"---\n\n"
            f"## Metadaten\n\n"
            f"| Schlüssel | Wert |\n"
            f"|-----------|------|\n"
            f"| Session-Ende | {end_reason} |\n"
            f"| Dauer | {duration_s // 60} min {duration_s % 60} s |\n"
            f"| Nachrichten | {self._message_count} |\n"
            f"| Advisor-Aufrufe | {self._advisor_calls} |\n"
            f"| Training-Aufrufe | {self._training_calls} |\n"
            f"| RAG-Quellen | {self._rag_sources_total} |\n"
            f"| Friction-Events | {self._friction_events} |\n"
            f"| Empfehlung | {self._recommendation} |\n"
            f"| Training gestartet | {'Ja' if self._training_started else 'Nein'} |\n"
        )

        # Prepend YAML frontmatter (one-time rewrite)
        frontmatter = (
            "---\n"
            f"session_id: {self.session_id}\n"
            f"started_at: {self.started_at.isoformat(timespec='seconds')}\n"
            f"ended_at: {ended_at.isoformat(timespec='seconds')}\n"
            f"duration_s: {duration_s}\n"
            f"language: {self.language}\n"
            f"end_reason: {end_reason}\n"
            f"message_count: {self._message_count}\n"
            f"advisor_calls: {self._advisor_calls}\n"
            f"training_calls: {self._training_calls}\n"
            f"rag_sources_total: {self._rag_sources_total}\n"
            f"recommendation: {self._recommendation}\n"
            f"training_started: {'true' if self._training_started else 'false'}\n"
            f"friction_events: {self._friction_events}\n"
            "---\n\n"
        )
        body = self._path.read_text(encoding="utf-8")
        self._path.write_text(frontmatter + body, encoding="utf-8")
        logger.info("Session log finalized: %s (reason=%s)", self._path.name, end_reason)


# ---------------------------------------------------------------------------
# Module-level sessions store (LRU-bounded)
# ---------------------------------------------------------------------------

_SESSIONS_MAX = 128
_sessions: collections.OrderedDict[str, SessionLogger] = collections.OrderedDict()


def get_or_create_logger(session_id: str, language: str = "de") -> SessionLogger | None:
    """Return the logger for session_id (creating it if new). None if logging is disabled."""
    if not SESSION_LOG_ENABLED:
        return None
    if not session_id:
        return None
    if session_id in _sessions:
        _sessions.move_to_end(session_id)
        return _sessions[session_id]
    sl = SessionLogger(session_id, language)
    _sessions[session_id] = sl
    # Evict oldest if over capacity
    while len(_sessions) > _SESSIONS_MAX:
        _, evicted = _sessions.popitem(last=False)
        evicted.finalize("evicted")
    return sl
