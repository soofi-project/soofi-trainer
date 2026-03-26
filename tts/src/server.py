import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

log = logging.getLogger("soofi-tts")

TTS_PROVIDER = os.getenv("TTS_PROVIDER")
if TTS_PROVIDER != "openai":
    raise RuntimeError(f"TTS_PROVIDER must be 'openai', got '{TTS_PROVIDER}'")

TTS_MODEL = os.getenv("TTS_MODEL")
if not TTS_MODEL:
    raise RuntimeError("TTS_MODEL is not set")

_tts_speed_raw = os.getenv("TTS_SPEED")
if not _tts_speed_raw:
    raise RuntimeError("TTS_SPEED is not set")
try:
    TTS_SPEED = float(_tts_speed_raw)
except ValueError:
    raise RuntimeError(f"TTS_SPEED must be a number, got '{_tts_speed_raw}'")

TTS_BASE_URL = os.getenv("TTS_BASE_URL")  # None → api.openai.com, set → local endpoint

# Phonetic replacements for German Piper voices — english loanwords
# that Piper would mispronounce with German phoneme rules.
# Two env vars, pipe-separated, aligned 1:1:
#   TTS_DE_PHONETIC_KEYS=Fine-Tuning | Embedding
#   TTS_DE_PHONETIC_VALUES=Fein-Tjuning | Emmbädding
_DE_PHONETIC: dict[str, str] = {}
_phon_keys = os.getenv("TTS_DE_PHONETIC_KEYS", "")
_phon_vals = os.getenv("TTS_DE_PHONETIC_VALUES", "")
if _phon_keys and _phon_vals:
    _keys = [k.strip() for k in _phon_keys.split("|")]
    _vals = [v.strip() for v in _phon_vals.split("|")]
    if len(_keys) != len(_vals):
        log.warning(
            "TTS_DE_PHONETIC_KEYS has %d entries but VALUES has %d — phonetic replacement disabled",
            len(_keys), len(_vals),
        )
    else:
        _DE_PHONETIC = dict(zip(_keys, _vals))
        log.info("Loaded %d phonetic replacements", len(_DE_PHONETIC))

# Sort by key length descending so longer matches are replaced first,
# preventing partial matches from corrupting longer keys (e.g. "Fine" vs "Fine-Tuning").
_de_phonetic_sorted: list[tuple[str, str]] = sorted(
    _DE_PHONETIC.items(), key=lambda item: len(item[0]), reverse=True
)


def _apply_phonetic(text: str, language: str) -> str:
    """Replace english loanwords with phonetic German spelling for Piper voices."""
    if language != "de":
        return text
    for word, replacement in _de_phonetic_sorted:
        text = text.replace(word, replacement)
    return text


_client: AsyncOpenAI | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    _client = AsyncOpenAI(api_key=api_key, base_url=TTS_BASE_URL)
    yield
    await _client.close()


app = FastAPI(title="Soofi TTS", lifespan=lifespan)


class SynthesizeRequest(BaseModel):
    text: str
    voice: str
    language: Literal["de", "en"] = "de"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest) -> StreamingResponse:
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="text must not be empty")
    if _client is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    tts_input = _apply_phonetic(req.text, req.language)
    try:
        response = await _client.audio.speech.create(
            model=TTS_MODEL,
            voice=req.voice,  # type: ignore[arg-type]
            input=tts_input,
            speed=TTS_SPEED,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return StreamingResponse(response.iter_bytes(), media_type="audio/mpeg")
