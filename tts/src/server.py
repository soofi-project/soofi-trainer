import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

TTS_PROVIDER = os.getenv("TTS_PROVIDER")
if not TTS_PROVIDER:
    raise RuntimeError("TTS_PROVIDER is not set")

TTS_MODEL = os.getenv("TTS_MODEL")
if not TTS_MODEL:
    raise RuntimeError("TTS_MODEL is not set")

TTS_VOICE = os.getenv("TTS_VOICE")
if not TTS_VOICE:
    raise RuntimeError("TTS_VOICE is not set")

_tts_speed_raw = os.getenv("TTS_SPEED")
if not _tts_speed_raw:
    raise RuntimeError("TTS_SPEED is not set")
TTS_SPEED = float(_tts_speed_raw)

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


app = FastAPI(title="Soofi TTS", lifespan=lifespan)


class SynthesizeRequest(BaseModel):
    text: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest) -> StreamingResponse:
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="text must not be empty")
    if TTS_PROVIDER != "openai":
        raise HTTPException(status_code=501, detail=f"TTS provider '{TTS_PROVIDER}' not supported")

    if _client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        response = await _client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,  # type: ignore[arg-type]
            input=req.text,
            speed=TTS_SPEED,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return StreamingResponse(response.iter_bytes(), media_type="audio/mpeg")
