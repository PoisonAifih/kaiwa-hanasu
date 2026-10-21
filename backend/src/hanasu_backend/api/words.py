from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from hanasu_backend.api.dependencies import get_dictionary
from hanasu_backend.errors import WordNotFoundError
from hanasu_backend.gloss.dictionary import Dictionary

router = APIRouter(prefix="/api")


class SenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parts_of_speech: list[str]
    glosses: list[str]
    misc: list[str]
    info: list[str]


class WordOut(BaseModel):
    id: int
    kanji: list[str]
    readings: list[str]
    common: bool
    senses: list[SenseOut]


@router.get("/words/{entry_id}")
def get_word(entry_id: int, dictionary: Annotated[Dictionary, Depends(get_dictionary)]) -> WordOut:
    entry = dictionary.get_entry(entry_id)
    if entry is None:
        raise WordNotFoundError(f"No dictionary entry {entry_id}")
    return WordOut(
        id=entry.id,
        kanji=entry.kanji,
        readings=entry.readings,
        common=entry.common,
        senses=[SenseOut.model_validate(s) for s in dictionary.describe_senses(entry.raw_senses)],
    )
