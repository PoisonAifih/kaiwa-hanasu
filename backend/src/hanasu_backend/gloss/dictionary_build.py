"""JMdict JSON -> SQLite."""

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

ANY_FORM = "*"

SCHEMA = """
CREATE TABLE entries (id INTEGER PRIMARY KEY, body TEXT NOT NULL);
CREATE TABLE forms (
    text TEXT NOT NULL,
    reading TEXT NOT NULL,
    entry_id INTEGER NOT NULL,
    is_kanji INTEGER NOT NULL,
    common INTEGER NOT NULL
);
CREATE TABLE tags (code TEXT PRIMARY KEY, description TEXT NOT NULL);
"""
FORMS_INDEX = "CREATE INDEX forms_text ON forms (text)"


def build_dictionary(source: dict, target: Path) -> int:
    """Returns the entry count."""
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".partial")
    partial.unlink(missing_ok=True)
    with sqlite3.connect(partial) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO tags VALUES (?, ?)", source.get("tags", {}).items())
        count = 0
        for word in source["words"]:
            entry_id = int(word["id"])
            db.execute("INSERT INTO entries VALUES (?, ?)", (entry_id, _encode_entry(word)))
            db.executemany("INSERT INTO forms VALUES (?, ?, ?, ?, ?)", _list_forms(word))
            count += 1
        db.execute(FORMS_INDEX)
    db.close()
    partial.replace(target)
    return count


def _encode_entry(word: dict) -> str:
    body = {
        "kanji": [{"text": k["text"], "common": k["common"]} for k in word["kanji"]],
        "kana": [
            {"text": k["text"], "common": k["common"], "appliesToKanji": k["appliesToKanji"]}
            for k in word["kana"]
        ],
        "sense": [
            {
                "partOfSpeech": s["partOfSpeech"],
                "appliesToKanji": s["appliesToKanji"],
                "appliesToKana": s["appliesToKana"],
                "misc": s["misc"],
                "info": s["info"],
                "gloss": [g["text"] for g in s["gloss"] if g.get("lang", "eng") == "eng"],
            }
            for s in word["sense"]
        ],
    }
    return json.dumps(body, ensure_ascii=False, separators=(",", ":"))


def _list_forms(word: dict) -> Iterator[tuple[str, str, int, int, int]]:
    entry_id = int(word["id"])
    for kana in word["kana"]:
        yield kana["text"], kana["text"], entry_id, 0, int(kana["common"])
        for kanji in word["kanji"]:
            if ANY_FORM in kana["appliesToKanji"] or kanji["text"] in kana["appliesToKanji"]:
                common = int(kanji["common"] and kana["common"])
                yield kanji["text"], kana["text"], entry_id, 1, common
