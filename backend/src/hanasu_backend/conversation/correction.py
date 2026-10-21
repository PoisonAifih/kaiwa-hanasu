import logging

from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from hanasu_backend.conversation.models import Correction, DraftCorrection, DraftIssue, Issue
from hanasu_backend.conversation.prompts import (
    CORRECTION_SCHEMA,
    Level,
    build_correction_input,
    build_correction_system,
)

logger = logging.getLogger(__name__)

CORRECTION_TEMPERATURE = 0.0


class Corrector:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def correct(
        self, learner_text: str, partner_text: str | None, level: Level
    ) -> Correction | None:
        """None = check failed."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=CORRECTION_TEMPERATURE,
                messages=[
                    {"role": "system", "content": build_correction_system(level)},
                    {"role": "user", "content": build_correction_input(learner_text, partner_text)},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "correction", "strict": True, "schema": CORRECTION_SCHEMA},
                },
            )
            draft = DraftCorrection.model_validate_json(response.choices[0].message.content or "")
        except (OpenAIError, ValidationError, IndexError) as error:
            logger.warning("Correction failed: %s", error)
            return None
        return finalize_correction(learner_text, draft)


def finalize_correction(original: str, draft: DraftCorrection) -> Correction:
    corrected = draft.corrected.strip() or original
    # Unchanged text counts as ok
    if draft.ok or (not draft.issues and corrected == original):
        return Correction(ok=True, original=original, corrected=original, issues=[])
    return Correction(
        ok=False,
        original=original,
        corrected=corrected,
        issues=[_locate_issue(original, issue) for issue in draft.issues],
    )


def _locate_issue(original: str, issue: DraftIssue) -> Issue:
    start = original.find(issue.original_span) if issue.original_span else -1
    if start < 0:
        return Issue(**issue.model_dump(), start=None, end=None)
    return Issue(**issue.model_dump(), start=start, end=start + len(issue.original_span))
