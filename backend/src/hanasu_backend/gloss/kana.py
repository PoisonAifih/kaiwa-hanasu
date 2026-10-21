import re

KATAKANA_START = ord("ァ")
KATAKANA_END = ord("ヶ")
KATAKANA_TO_HIRAGANA = 0x60
# Kanji (incl. 々 〆)
KANJI = re.compile(r"[㐀-䶿一-鿿豈-﫿々〆ヵヶ]")


def to_hiragana(text: str) -> str:
    return "".join(
        chr(ord(char) - KATAKANA_TO_HIRAGANA)
        if KATAKANA_START <= ord(char) <= KATAKANA_END
        else char
        for char in text
    )


def has_kanji(text: str) -> bool:
    return KANJI.search(text) is not None


def is_kanji(char: str) -> bool:
    return KANJI.fullmatch(char) is not None
