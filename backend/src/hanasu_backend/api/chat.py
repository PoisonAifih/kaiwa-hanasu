import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from hanasu_backend.api.dependencies import (
    SettingsDep,
    get_corrector,
    get_glosser,
    get_partner,
)
from hanasu_backend.conversation.correction import Corrector
from hanasu_backend.conversation.models import (
    ChatRequest,
    Correction,
    CorrectionRequest,
    Message,
)
from hanasu_backend.conversation.partner import Partner
from hanasu_backend.errors import UpstreamError
from hanasu_backend.gloss.glosser import Glosser, Token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


class SegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text: str
    ruby: str | None


class TokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    surface: str
    start: int
    end: int
    reading: str
    lemma: str
    pos: str
    gloss: str | None
    entry_id: int | None
    furigana: list[SegmentOut]


class ChatResponse(BaseModel):
    reply: str
    # Optional translation
    translation: str | None
    # Null: no learner turn / check failed
    correction: Correction | None
    tokens: list[TokenOut]


@router.post("/chat")
async def chat(
    body: ChatRequest,
    settings: SettingsDep,
    partner: Annotated[Partner, Depends(get_partner)],
    corrector: Annotated[Corrector, Depends(get_corrector)],
    glosser: Annotated[Glosser, Depends(get_glosser)],
) -> ChatResponse:
    history = _trim_history(body.messages, settings.max_history_messages)
    # Reply + correction in parallel
    reply, correction = await asyncio.gather(
        partner.reply(history, body.level, body.scenario),
        _check_learner_turn(corrector, history, body.level),
    )
    return ChatResponse(
        reply=reply.text,
        translation=reply.translation,
        correction=correction,
        tokens=_gloss_reply(glosser, reply.text),
    )


@router.post("/correct")
async def correct(
    body: CorrectionRequest, corrector: Annotated[Corrector, Depends(get_corrector)]
) -> Correction:
    """Correction retry."""
    correction = await corrector.correct(body.text, body.partner_text, body.level)
    if correction is None:
        raise UpstreamError("The correction model failed")
    return correction


def _trim_history(messages: list[Message], limit: int) -> list[Message]:
    """History trim: starts at a learner turn."""
    if len(messages) <= limit:
        return messages
    trimmed = messages[-limit:]
    while trimmed and trimmed[0].role == "assistant":
        trimmed = trimmed[1:]
    return trimmed


async def _check_learner_turn(
    corrector: Corrector, history: list[Message], level: str
) -> Correction | None:
    if not history or history[-1].role != "user":
        return None
    partner_text = next((m.content for m in reversed(history[:-1]) if m.role == "assistant"), None)
    return await corrector.correct(history[-1].content, partner_text, level)


def _gloss_reply(glosser: Glosser, reply: str) -> list[Token]:
    # Gloss failure -> no tokens
    try:
        return glosser.gloss(reply)
    except Exception:
        logger.exception("Glossing failed for %r", reply)
        return []
