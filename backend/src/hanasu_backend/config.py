from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    # Repo .env, then backend/.env
    model_config = SettingsConfigDict(
        env_file=(REPO_DIR / ".env", BACKEND_DIR / ".env"), extra="ignore"
    )

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_chat_model: str = "google/gemini-2.5-flash"
    # Empty = chat model
    openrouter_correction_model: str = ""
    openrouter_tts_model: str = "google/gemini-3.8-flash-lite-tts"
    openrouter_tts_voice: str = "Kore"
    openrouter_stt_model: str = "openai/gpt-4o-mini-transcribe"
    # Empty = auto-detect
    openrouter_stt_language: str = "ja"

    max_audio_bytes: int = 10 * 1024 * 1024
    max_history_messages: int = 20
    max_speech_chars: int = 500
    dictionary_path: Path = BACKEND_DIR / "data" / "jmdict.sqlite"
    cors_origins: str = "http://localhost:5173"

    @property
    def correction_model(self) -> str:
        return self.openrouter_correction_model or self.openrouter_chat_model

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
