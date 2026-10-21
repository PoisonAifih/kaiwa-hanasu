from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import StreamingResponse
from openai import OpenAIError
from pydantic import BaseModel, Field

from hanasu_backend.api.dependencies import SettingsDep, get_speaker, get_transcriber
from hanasu_backend.errors import (
    AudioTooLargeError,
    NoSpeakableTextError,
    NoSpeechError,
    UpstreamError,
)
from hanasu_backend.llm.speaker import OpenRouterSpeaker
from hanasu_backend.llm.transcriber import OpenRouterTranscriber
from hanasu_backend.voice.audio import detect_audio_format
from hanasu_backend.voice.speech_text import clean_speech_text

router = APIRouter(prefix="/api")

MAX_SPEECH_REQUEST_CHARS = 2000


class TranscriptOut(BaseModel):
    text: str


class SpeechIn(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_SPEECH_REQUEST_CHARS)


@router.post("/stt")
async def transcribe(
    audio: UploadFile,
    settings: SettingsDep,
    transcriber: Annotated[OpenRouterTranscriber, Depends(get_transcriber)],
) -> TranscriptOut:
    recording = await audio.read(settings.max_audio_bytes + 1)
    if len(recording) > settings.max_audio_bytes:
        raise AudioTooLargeError("The recording is too long")
    audio_format = detect_audio_format(recording)
    try:
        text = await transcriber.transcribe(
            recording, audio_format.filename, audio_format.content_type
        )
    except OpenAIError as error:
        raise UpstreamError(f"Transcription failed: {error}") from error
    if not text:
        raise NoSpeechError("No speech was detected")
    return TranscriptOut(text=text)


@router.post("/tts")
async def speak(
    body: SpeechIn,
    settings: SettingsDep,
    speaker: Annotated[OpenRouterSpeaker, Depends(get_speaker)],
) -> StreamingResponse:
    text = clean_speech_text(body.text)[: settings.max_speech_chars]
    if not text:
        raise NoSpeakableTextError("Nothing to read aloud")
    try:
        stream = await speaker.open_stream(text)
    except OpenAIError as error:
        raise UpstreamError(f"Speech failed: {error}") from error
    return StreamingResponse(
        stream.chunks,
        media_type=stream.pcm_format.content_type,
        # No proxy buffering
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-store"},
    )
