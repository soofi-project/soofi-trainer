import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

STT_PROVIDER = os.getenv("STT_PROVIDER")
if not STT_PROVIDER:
    raise RuntimeError("STT_PROVIDER is not set")

STT_LANGUAGE = os.getenv("STT_LANGUAGE")
if not STT_LANGUAGE:
    raise RuntimeError("STT_LANGUAGE is not set")
WHISPER_PROMPT = os.getenv("WHISPER_PROMPT")
if not WHISPER_PROMPT:
    raise RuntimeError("WHISPER_PROMPT is not set")

# Known Whisper hallucination phrases — returned on silence or noise.
# Whisper hallucinates these when it detects no clear speech signal.
# Filter by prefix/substring match to catch punctuation variants.
_PHANTOM_PREFIXES = (
    "Untertitel",
    "Vielen Dank fürs Zuschauen",
    "Vielen Dank für's Zuschauen",
    "Danke fürs Zuschauen",
    "Copyright WDR",
    "Untertitelung",
    "Bis zum nächsten Mal",
)

_client: AsyncOpenAI | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    _client = AsyncOpenAI(api_key=api_key)
    yield
    await _client.close()


app = FastAPI(title="Soofi STT", lifespan=lifespan)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> JSONResponse:
    if STT_PROVIDER != "openai":
        raise HTTPException(status_code=501, detail=f"STT provider '{STT_PROVIDER}' not supported")

    if _client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    audio_bytes = await file.read()
    filename = file.filename or "audio.webm"
    try:
        transcription = await _client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_bytes, file.content_type or "audio/webm"),
            language=STT_LANGUAGE,
            prompt=WHISPER_PROMPT,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    text = transcription.text.strip()
    if any(text.startswith(prefix) for prefix in _PHANTOM_PREFIXES):
        text = ""
    return JSONResponse({"text": text})
