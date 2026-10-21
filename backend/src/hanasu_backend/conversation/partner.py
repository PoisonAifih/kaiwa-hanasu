import re
from dataclasses import dataclass

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, ValidationError

from hanasu_backend.conversation.models import Message
from hanasu_backend.conversation.prompts import (
    OPENER_REQUEST,
    REPLY_SCHEMA,
    Level,
    Scenario,
    build_reply_system,
)
from hanasu_backend.errors import UpstreamError
from hanasu_backend.voice.speech_text import clean_speech_text

REPLY_TEMPERATURE = 0.8
KANA = re.compile(r"[぀-ヿ]")


class _DraftReply(BaseModel):
    reply: str
    translation: str


@dataclass(frozen=True, slots=True)
class PartnerReply:
    text: str
    # None = no usable translation
    translation: str | None


class Partner:
    """Conversation partner."""

    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def reply(
        self, history: list[Message], level: Level, scenario: Scenario
    ) -> PartnerReply:
        turns = [{"role": m.role, "content": m.content} for m in history]
        # Opener request
        if not turns or turns[0]["role"] == "assistant":
            turns.insert(0, {"role": "user", "content": OPENER_REQUEST})
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=REPLY_TEMPERATURE,
                messages=[
                    {"role": "system", "content": build_reply_system(level, scenario)},
                    *turns,
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "reply", "strict": True, "schema": REPLY_SCHEMA},
                },
            )
            content = response.choices[0].message.content or ""
        except (OpenAIError, IndexError) as error:
            raise UpstreamError(f"The conversation model failed: {error}") from error
        reply = parse_reply(content)
        if not reply.text:
            raise UpstreamError("The conversation model returned an empty reply")
        return reply


def parse_reply(content: str) -> PartnerReply:
    try:
        draft = _DraftReply.model_validate_json(content)
    except ValidationError:
        return PartnerReply(text=clean_speech_text(content), translation=None)
    translation = draft.translation.strip()
    # Drop Japanese copied into translation
    if not translation or KANA.search(translation):
        translation = None
    return PartnerReply(text=clean_speech_text(draft.reply), translation=translation)
