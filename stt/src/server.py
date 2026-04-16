import logging
import os
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

log = logging.getLogger("soofi-stt")

STT_PROVIDER = os.getenv("STT_PROVIDER")
if STT_PROVIDER != "openai":
    raise RuntimeError(f"STT_PROVIDER must be 'openai', got '{STT_PROVIDER}'")

STT_MODEL = os.getenv("STT_MODEL")
if not STT_MODEL:
    raise RuntimeError("STT_MODEL is not set")

STT_LANGUAGE = os.getenv("STT_LANGUAGE")
if not STT_LANGUAGE:
    raise RuntimeError("STT_LANGUAGE is not set")

WHISPER_PROMPT_DE = os.getenv("WHISPER_PROMPT_DE", "")
WHISPER_PROMPT_EN = os.getenv("WHISPER_PROMPT_EN", "")
# Backwards compat: fall back to WHISPER_PROMPT if language-specific vars are unset
if not WHISPER_PROMPT_DE:
    WHISPER_PROMPT_DE = os.getenv("WHISPER_PROMPT", "")
if not WHISPER_PROMPT_EN:
    WHISPER_PROMPT_EN = os.getenv("WHISPER_PROMPT", "")

# Known Whisper hallucination phrases — returned on silence or noise.
# Whisper hallucinates these when it detects no clear speech signal.
# Filter by prefix match to catch punctuation variants.
_PHANTOM_PREFIXES = (
    # German
    "Untertitel",
    "Vielen Dank fürs Zuschauen",
    "Vielen Dank für's Zuschauen",
    "Danke fürs Zuschauen",
    "Copyright WDR",
    "Untertitelung",
    "Bis zum nächsten Mal",
    # English
    "Thank you for watching",
    "Thanks for watching",
    "Please subscribe",
    "Subscribe to",
    "Like and subscribe",
    "See you next time",
    "Thank you for listening",
)

STT_BASE_URL = os.getenv("STT_BASE_URL")  # None → api.openai.com, set → local endpoint


# Whole-word replacements applied to the transcript per language. Needed because
# Whisper occasionally normalizes proper nouns to more common spellings (e.g.
# "Soofi" → "Sofi") even when the WHISPER_PROMPT lists the intended spelling.
# Two env vars per language, pipe-separated, aligned 1:1:
#   STT_DE_REPLACEMENTS_KEYS=Sofi | Sofie
#   STT_DE_REPLACEMENTS_VALUES=Soofi | Soofi
# Matching is case-insensitive with word boundaries, so "Sofia" is not touched.
def _parse_replacements(lang: str) -> list[tuple[re.Pattern[str], str]]:
    keys_raw = os.getenv(f"STT_{lang.upper()}_REPLACEMENTS_KEYS", "")
    vals_raw = os.getenv(f"STT_{lang.upper()}_REPLACEMENTS_VALUES", "")
    if not keys_raw or not vals_raw:
        return []
    keys = [k.strip() for k in keys_raw.split("|")]
    vals = [v.strip() for v in vals_raw.split("|")]
    if len(keys) != len(vals):
        log.warning(
            "STT_%s_REPLACEMENTS_KEYS has %d entries but VALUES has %d — disabled",
            lang.upper(), len(keys), len(vals),
        )
        return []
    compiled: list[tuple[re.Pattern[str], str]] = []
    for k, v in zip(keys, vals):
        if not k or not v:
            continue
        compiled.append((re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE), v))
    return compiled


_STT_REPLACEMENTS: dict[str, list[tuple[re.Pattern[str], str]]] = {
    "de": _parse_replacements("de"),
    "en": _parse_replacements("en"),
}
for _lang, _rules in _STT_REPLACEMENTS.items():
    if _rules:
        log.info("Loaded %d STT transcript replacements for %s", len(_rules), _lang)


def _apply_replacements(text: str, language: str) -> str:
    for pattern, replacement in _STT_REPLACEMENTS.get(language, []):
        text = pattern.sub(replacement, text)
    return text

_client: AsyncOpenAI | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    _client = AsyncOpenAI(api_key=api_key, base_url=STT_BASE_URL)
    yield
    await _client.close()


app = FastAPI(title="Soofi STT", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


_MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB (Whisper limit)


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: Literal["de", "en", ""] = Form(default=""),
) -> JSONResponse:
    if _client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    lang = language or STT_LANGUAGE
    prompt = WHISPER_PROMPT_DE if lang == "de" else WHISPER_PROMPT_EN
    audio_bytes = await file.read(_MAX_AUDIO_BYTES + 1)
    if len(audio_bytes) > _MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail=f"Audio file exceeds {_MAX_AUDIO_BYTES // (1024*1024)} MB limit")
    filename = file.filename or "audio.webm"
    try:
        transcription = await _client.audio.transcriptions.create(
            model=STT_MODEL,
            file=(filename, audio_bytes, file.content_type or "audio/webm"),
            language=lang,
            prompt=prompt,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    text = transcription.text.strip()
    if text.startswith(_PHANTOM_PREFIXES):
        text = ""
    text = _apply_replacements(text, lang)
    return JSONResponse({"text": text})
