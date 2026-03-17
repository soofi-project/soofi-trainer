import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

STT_PROVIDER = os.getenv("STT_PROVIDER")
if STT_PROVIDER != "openai":
    raise RuntimeError(f"STT_PROVIDER must be 'openai', got '{STT_PROVIDER}'")

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
            model="whisper-1",
            file=(filename, audio_bytes, file.content_type or "audio/webm"),
            language=lang,
            prompt=prompt,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    text = transcription.text.strip()
    if text.startswith(_PHANTOM_PREFIXES):
        text = ""
    return JSONResponse({"text": text})
