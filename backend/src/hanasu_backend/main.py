import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from hanasu_backend.api import chat, voice, words
from hanasu_backend.config import get_settings
from hanasu_backend.errors import (
    AudioTooLargeError,
    DictionaryMissingError,
    HanasuError,
    InvalidAudioError,
    MissingApiKeyError,
    NoSpeakableTextError,
    NoSpeechError,
    UpstreamError,
    WordNotFoundError,
)

ERROR_STATUS: dict[type[HanasuError], int] = {
    MissingApiKeyError: 503,
    DictionaryMissingError: 503,
    UpstreamError: 503,
    AudioTooLargeError: 413,
    InvalidAudioError: 415,
    NoSpeechError: 422,
    NoSpeakableTextError: 422,
    WordNotFoundError: 404,
}


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    app = FastAPI(title="Kaiwa-Hanasu")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(HanasuError, _render_error)
    app.include_router(chat.router)
    app.include_router(voice.router)
    app.include_router(words.router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


async def _render_error(_: Request, error: Exception) -> JSONResponse:
    status = ERROR_STATUS.get(type(error), 500)
    return JSONResponse(status_code=status, content={"detail": str(error)})


app = create_app()
