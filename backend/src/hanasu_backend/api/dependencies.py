import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from openai import AsyncOpenAI

from hanasu_backend.config import Settings, get_settings
from hanasu_backend.conversation.correction import Corrector
from hanasu_backend.conversation.partner import Partner
from hanasu_backend.errors import DictionaryMissingError
from hanasu_backend.gloss.dictionary import Dictionary
from hanasu_backend.gloss.glosser import Glosser
from hanasu_backend.llm.client import build_client
from hanasu_backend.llm.speaker import OpenRouterSpeaker
from hanasu_backend.llm.transcriber import OpenRouterTranscriber

logger = logging.getLogger(__name__)

SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_client() -> AsyncOpenAI:
    return build_client(get_settings())


@lru_cache
def get_dictionary() -> Dictionary:
    return Dictionary(get_settings().dictionary_path)


@lru_cache
def get_glosser() -> Glosser:
    try:
        dictionary = get_dictionary()
    except DictionaryMissingError as error:
        # No dictionary: furigana only
        logger.warning("%s", error)
        dictionary = None
    return Glosser(dictionary)


def get_partner(settings: SettingsDep) -> Partner:
    return Partner(get_client(), settings.openrouter_chat_model)


def get_corrector(settings: SettingsDep) -> Corrector:
    return Corrector(get_client(), settings.correction_model)


def get_speaker(settings: SettingsDep) -> OpenRouterSpeaker:
    return OpenRouterSpeaker(
        get_client(), settings.openrouter_tts_model, settings.openrouter_tts_voice
    )


def get_transcriber(settings: SettingsDep) -> OpenRouterTranscriber:
    return OpenRouterTranscriber(
        get_client(), settings.openrouter_stt_model, settings.openrouter_stt_language
    )
