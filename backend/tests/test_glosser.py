from hanasu_backend.gloss.furigana import Segment, align_furigana
from hanasu_backend.gloss.glosser import Glosser
from hanasu_backend.gloss.kana import to_hiragana


def _by_surface(glosser: Glosser, text: str) -> dict:
    return {token.surface: token for token in glosser.gloss(text)}


def test_auxiliaries_join_the_verb_chip(glosser: Glosser) -> None:
    tokens = _by_surface(glosser, "映画を見ていました。")
    assert list(tokens) == ["映画", "を", "見ていました", "。"]
    assert tokens["見ていました"].gloss == "to see"
    assert tokens["見ていました"].lemma == "見る"


def test_particles_and_punctuation_have_no_gloss(glosser: Glosser) -> None:
    tokens = _by_surface(glosser, "映画を見ていました。")
    assert tokens["を"].gloss is None
    assert tokens["を"].entry_id is None
    assert tokens["。"].gloss is None


def test_desu_after_noun_stays_separate(glosser: Glosser) -> None:
    assert list(_by_surface(glosser, "映画です")) == ["映画", "です"]


def test_suru_joins_sahen_noun(glosser: Glosser) -> None:
    tokens = _by_surface(glosser, "勉強しました")
    assert tokens["勉強しました"].gloss == "study"


def test_reading_picks_the_right_homograph(glosser: Glosser) -> None:
    assert _by_surface(glosser, "生")["生"].gloss == "raw"


def test_normalized_form_disambiguates_kana_words(glosser: Glosser) -> None:
    assert _by_surface(glosser, "時間がある")["ある"].gloss == "to be"


def test_unknown_compound_falls_back_to_parts(glosser: Glosser) -> None:
    tokens = _by_surface(glosser, "東京駅")
    assert tokens["東京"].gloss == "Tokyo"
    assert tokens["駅"].gloss == "station"


def test_offsets_slice_the_original_text(glosser: Glosser) -> None:
    text = "東京駅で映画を見ました！"
    for token in glosser.gloss(text):
        assert text[token.start : token.end] == token.surface


def test_furigana_skips_okurigana() -> None:
    assert align_furigana("読みます", "よみます") == [Segment("読", "よ"), Segment("みます", None)]
    assert align_furigana("ひらがな", "ひらがな") == [Segment("ひらがな", None)]


def test_furigana_falls_back_to_whole_word_when_unalignable() -> None:
    assert align_furigana("今日", "きょう") == [Segment("今日", "きょう")]
    assert align_furigana("行く", "くる") == [Segment("行く", "くる")]


def test_katakana_converts_to_hiragana() -> None:
    assert to_hiragana("ビールー") == "びーるー"
