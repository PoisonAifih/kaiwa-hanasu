from typing import Literal

from pydantic import BaseModel, Field

from hanasu_backend.conversation.prompts import Level, Scenario

MAX_MESSAGE_CHARS = 1000
MAX_MESSAGES = 200

Category = Literal["grammar", "particle", "word_choice", "politeness", "naturalness"]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(default_factory=list, max_length=MAX_MESSAGES)
    level: Level = "beginner"
    scenario: Scenario = "free"


class CorrectionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    partner_text: str | None = Field(default=None, max_length=MAX_MESSAGE_CHARS)
    level: Level = "beginner"


class DraftIssue(BaseModel):
    """Model output."""

    category: Category
    original_span: str
    suggestion: str
    note: str


class DraftCorrection(BaseModel):
    ok: bool
    corrected: str
    issues: list[DraftIssue]


class Issue(DraftIssue):
    # Span offsets (None = not found)
    start: int | None
    end: int | None


class Correction(BaseModel):
    ok: bool
    original: str
    corrected: str
    issues: list[Issue]
