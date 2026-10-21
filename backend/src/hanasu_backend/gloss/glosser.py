from dataclasses import dataclass, field
from os.path import commonprefix

from sudachipy import Dictionary as SudachiDictionary
from sudachipy import Morpheme, SplitMode

from hanasu_backend.gloss.dictionary import Dictionary, Entry, Form
from hanasu_backend.gloss.furigana import Segment, align_furigana
from hanasu_backend.gloss.kana import has_kanji, to_hiragana

# Glossed word classes
CONTENT_POS = {
    "名詞", "代名詞", "動詞", "形容詞", "形状詞", "副詞",
    "連体詞", "接続詞", "感動詞", "接頭辞", "接尾辞",
}
INFLECTING_POS = {"動詞", "形容詞"}
AUXILIARY = "助動詞"
CONJUNCTIVE_PARTICLE = "接続助詞"
TE_FORMS = {"て", "で"}
SUBSIDIARY = "非自立可能"
SAHEN_NOUN = "サ変可能"
SURU = "する"
NEGATIVE = "ない"
USUALLY_KANA = "uk"
NAME_LABELS = {"人名": "(name)", "地名": "(place)"}


@dataclass(frozen=True, slots=True)
class Token:
    surface: str
    start: int
    end: int
    reading: str
    lemma: str
    pos: str
    gloss: str | None
    entry_id: int | None
    furigana: list[Segment]


@dataclass(slots=True)
class _Chip:
    """食べ+まし+た -> 食べました"""

    morphemes: list[Morpheme] = field(default_factory=list)
    inflecting: bool = False

    @property
    def head(self) -> Morpheme:
        return self.morphemes[0]


class Glosser:
    def __init__(self, dictionary: Dictionary | None) -> None:
        self._dictionary = dictionary
        # Mode C, fallback to mode A
        self._tokenizer = SudachiDictionary(dict="core").tokenizer(SplitMode.C)

    def gloss(self, text: str) -> list[Token]:
        tokens: list[Token] = []
        for chip in _group_chips(self._tokenizer.tokenize(text)):
            tokens.extend(self._build_tokens(text, chip))
        return tokens

    def _build_tokens(self, text: str, chip: _Chip) -> list[Token]:
        head = chip.head
        if head.part_of_speech()[0] not in CONTENT_POS:
            return [_build_token(text, chip, None, None)]
        match = self._lookup(head)
        if match is None and len(chip.morphemes) == 1:
            parts = head.split(SplitMode.A)
            if len(parts) > 1:
                return [self._build_part(text, part) for part in parts]
        return [_build_token(text, chip, *(match or (None, None)))]

    def _build_part(self, text: str, morpheme: Morpheme) -> Token:
        chip = _Chip([morpheme])
        if morpheme.part_of_speech()[0] not in CONTENT_POS:
            return _build_token(text, chip, None, None)
        return _build_token(text, chip, *(self._lookup(morpheme) or (None, None)))

    def _lookup(self, morpheme: Morpheme) -> tuple[Entry, Form] | None:
        if self._dictionary is None:
            return None
        lemma, normalized = morpheme.dictionary_form(), morpheme.normalized_form()
        reading = to_hiragana(morpheme.reading_form())
        best: tuple[tuple, Entry, Form] | None = None
        for form in self._dictionary.list_forms([lemma, normalized]):
            entry = self._dictionary.get_entry(form.entry_id)
            if entry is None:
                continue
            score = _score(form, entry, lemma, normalized, reading)
            if best is None or score > best[0]:
                best = (score, entry, form)
        return None if best is None else (best[1], best[2])


def _score(form: Form, entry: Entry, lemma: str, normalized: str, reading: str) -> tuple:
    """Higher is better."""
    first_sense = entry.raw_senses[0] if entry.raw_senses else {}
    return (
        form.text == lemma,
        # Reading overlap (生: なま vs せい)
        len(commonprefix([to_hiragana(form.reading), reading])),
        # Normalized form (ある -> 有る)
        normalized in entry.kanji,
        form.common,
        not has_kanji(lemma) and USUALLY_KANA in first_sense.get("misc", []),
        -entry.id,
    )


def _group_chips(morphemes: list[Morpheme]) -> list[_Chip]:
    chips: list[_Chip] = []
    for morpheme in morphemes:
        if chips and _joins(chips[-1], morpheme):
            chips[-1].morphemes.append(morpheme)
            chips[-1].inflecting = True
            continue
        pos = morpheme.part_of_speech()[0]
        chips.append(_Chip([morpheme], inflecting=pos in INFLECTING_POS))
    return chips


def _joins(chip: _Chip, morpheme: Morpheme) -> bool:
    pos = morpheme.part_of_speech()
    if not chip.inflecting:
        return _is_suru_after_noun(chip, morpheme)
    if pos[0] == AUXILIARY:
        return True
    if pos[1] == CONJUNCTIVE_PARTICLE and morpheme.surface() in TE_FORMS:
        return True
    if pos[0] == "形容詞" and morpheme.dictionary_form() == NEGATIVE:
        return True
    last = chip.morphemes[-1]
    after_te = last.surface() in TE_FORMS and last.part_of_speech()[1] == CONJUNCTIVE_PARTICLE
    return after_te and pos[0] in INFLECTING_POS and pos[1] == SUBSIDIARY


def _is_suru_after_noun(chip: _Chip, morpheme: Morpheme) -> bool:
    """勉強 + する"""
    head_pos = chip.head.part_of_speech()
    return (
        len(chip.morphemes) == 1
        and head_pos[0] == "名詞"
        and head_pos[2] == SAHEN_NOUN
        and morpheme.part_of_speech()[0] == "動詞"
        and morpheme.dictionary_form() == SURU
    )


def _build_token(text: str, chip: _Chip, entry: Entry | None, form: Form | None) -> Token:
    head = chip.head
    start, end = head.begin(), chip.morphemes[-1].end()
    surface = text[start:end]
    reading = to_hiragana("".join(m.reading_form() for m in chip.morphemes))
    pos = head.part_of_speech()
    gloss = _short_gloss(entry, form) if entry else _label_name(pos)
    return Token(
        surface=surface,
        start=start,
        end=end,
        reading=reading,
        lemma=head.dictionary_form(),
        pos=pos[0],
        gloss=gloss,
        entry_id=entry.id if entry else None,
        furigana=align_furigana(surface, reading),
    )


def _short_gloss(entry: Entry, form: Form | None) -> str | None:
    for sense in entry.list_senses(form) or entry.raw_senses:
        if sense["gloss"]:
            return sense["gloss"][0]
    return None


def _label_name(pos: tuple[str, ...]) -> str | None:
    return next((NAME_LABELS[p] for p in pos if p in NAME_LABELS), None)
