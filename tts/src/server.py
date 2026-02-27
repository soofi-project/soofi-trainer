import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

TTS_PROVIDER = os.getenv("TTS_PROVIDER", "openai")
TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")
TTS_SPEED = float(os.getenv("TTS_SPEED", "1.2"))

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

    assert _client is not None
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
