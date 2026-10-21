import re
from dataclasses import dataclass
from itertools import groupby

from hanasu_backend.gloss.kana import has_kanji, is_kanji, to_hiragana


@dataclass(frozen=True, slots=True)
class Segment:
    text: str
    ruby: str | None


def align_furigana(surface: str, reading: str) -> list[Segment]:
    """読みます -> 読(よ) + みます"""
    if not has_kanji(surface):
        return [Segment(surface, None)]
    runs = ["".join(chars) for _, chars in groupby(surface, key=is_kanji)]
    # Kana literal, kanji wildcard
    pattern = "".join("(.+?)" if is_kanji(run[0]) else re.escape(to_hiragana(run)) for run in runs)
    match = re.fullmatch(pattern, to_hiragana(reading))
    if match is None:
        return [Segment(surface, reading)]
    readings = iter(match.groups())
    return [Segment(run, next(readings)) if is_kanji(run[0]) else Segment(run, None) for run in runs]
