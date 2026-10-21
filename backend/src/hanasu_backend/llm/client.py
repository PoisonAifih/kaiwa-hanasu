from openai import AsyncOpenAI

from hanasu_backend.config import Settings
from hanasu_backend.errors import MissingApiKeyError

REQUEST_TIMEOUT_SECONDS = 30.0


def build_client(settings: Settings) -> AsyncOpenAI:
    if not settings.openrouter_api_key:
        raise MissingApiKeyError("OPENROUTER_API_KEY is not set in .env")
    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
