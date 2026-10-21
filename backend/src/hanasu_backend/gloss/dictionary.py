import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from hanasu_backend.errors import DictionaryMissingError

ANY_FORM = "*"
ENTRY_CACHE_SIZE = 4096


@dataclass(frozen=True, slots=True)
class Form:
    """Form + reading."""

    entry_id: int
    text: str
    reading: str
    is_kanji: bool
    common: bool


@dataclass(frozen=True, slots=True)
class Sense:
    parts_of_speech: list[str]
    glosses: list[str]
    misc: list[str]
    info: list[str]


@dataclass(frozen=True, slots=True)
class Entry:
    id: int
    kanji: list[str]
    readings: list[str]
    common: bool
    raw_senses: list[dict]

    def list_senses(self, form: Form | None = None) -> list[dict]:
        """Senses for this form."""
        if form is None:
            return self.raw_senses
        return [sense for sense in self.raw_senses if _applies_to(sense, form)]


def _applies_to(sense: dict, form: Form) -> bool:
    kana = sense["appliesToKana"]
    if ANY_FORM not in kana and form.reading not in kana:
        return False
    if not form.is_kanji:
        return True
    kanji = sense["appliesToKanji"]
    return ANY_FORM in kanji or form.text in kanji


class Dictionary:
    def __init__(self, path: Path) -> None:
        if not path.exists():
            raise DictionaryMissingError(
                f"{path} not found. Run: uv run python scripts/build_dictionary.py"
            )
        # Read-only, shared across threads
        self._db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
        self._tags = dict(self._db.execute("SELECT code, description FROM tags"))
        self.get_entry = lru_cache(maxsize=ENTRY_CACHE_SIZE)(self._read_entry)

    def list_forms(self, texts: Iterable[str]) -> list[Form]:
        unique = list(dict.fromkeys(t for t in texts if t))
        if not unique:
            return []
        placeholders = ",".join("?" * len(unique))
        rows = self._db.execute(
            "SELECT entry_id, text, reading, is_kanji, common FROM forms "
            f"WHERE text IN ({placeholders})",
            unique,
        )
        return [Form(row[0], row[1], row[2], bool(row[3]), bool(row[4])) for row in rows]

    def describe_tag(self, code: str) -> str:
        return self._tags.get(code, code)

    def describe_senses(self, raw_senses: list[dict]) -> list[Sense]:
        return [
            Sense(
                parts_of_speech=[self.describe_tag(p) for p in raw["partOfSpeech"]],
                glosses=raw["gloss"],
                misc=[self.describe_tag(m) for m in raw["misc"]],
                info=raw["info"],
            )
            for raw in raw_senses
        ]

    def _read_entry(self, entry_id: int) -> Entry | None:
        row = self._db.execute("SELECT body FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if row is None:
            return None
        body = json.loads(row[0])
        return Entry(
            id=entry_id,
            kanji=[k["text"] for k in body["kanji"]],
            readings=[k["text"] for k in body["kana"]],
            common=any(k["common"] for k in body["kanji"] + body["kana"]),
            raw_senses=body["sense"],
        )
