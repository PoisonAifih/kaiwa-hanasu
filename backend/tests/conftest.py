from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hanasu_backend.api import dependencies
from hanasu_backend.conversation.models import Correction, Message
from hanasu_backend.conversation.partner import PartnerReply
from hanasu_backend.gloss.dictionary import Dictionary
from hanasu_backend.gloss.dictionary_build import build_dictionary
from hanasu_backend.gloss.glosser import Glosser
from hanasu_backend.llm.speaker import PcmFormat, SpeechStream
from hanasu_backend.main import create_app


def _word(entry_id: int, kanji: list[str], kana: list[str], glosses: list[str], **extra) -> dict:
    return {
        "id": str(entry_id),
        "kanji": [{"common": True, "text": k, "tags": []} for k in kanji],
        "kana": [{"common": True, "text": k, "tags": [], "appliesToKanji": ["*"]} for k in kana],
        "sense": [
            {
                "partOfSpeech": extra.get("pos", ["n"]),
                "appliesToKanji": ["*"],
                "appliesToKana": ["*"],
                "misc": extra.get("misc", []),
                "info": [],
                "gloss": [{"lang": "eng", "text": g} for g in glosses],
            }
        ],
    }


SAMPLE_JMDICT = {
    "tags": {"n": "noun (common) (futsuumeishi)", "v1": "Ichidan verb", "uk": "usually kana"},
    "words": [
        _word(1, ["映画"], ["えいが"], ["movie", "film"]),
        _word(2, ["見る"], ["みる"], ["to see", "to look"], pos=["v1"]),
        _word(3, ["生"], ["なま"], ["raw"]),
        _word(4, ["生"], ["せい"], ["life"]),
        _word(5, ["有る"], ["ある"], ["to be"], misc=["uk"]),
        _word(6, ["或る"], ["ある"], ["a certain"], misc=["uk"]),
        _word(7, ["勉強"], ["べんきょう"], ["study"]),
        _word(8, ["東京"], ["とうきょう"], ["Tokyo"]),
        _word(9, ["駅"], ["えき"], ["station"]),
    ],
}


@pytest.fixture(scope="session")
def dictionary(tmp_path_factory: pytest.TempPathFactory) -> Dictionary:
    path: Path = tmp_path_factory.mktemp("dict") / "jmdict.sqlite"
    build_dictionary(SAMPLE_JMDICT, path)
    return Dictionary(path)


@pytest.fixture(scope="session")
def glosser(dictionary: Dictionary) -> Glosser:
    return Glosser(dictionary)


class FakePartner:
    def __init__(self) -> None:
        self.seen: list[Message] = []

    async def reply(self, history: list[Message], level: str, scenario: str) -> PartnerReply:
        self.seen = history
        return PartnerReply(text="映画を見ましたか？", translation="Did you watch a movie?")


class FakeCorrector:
    def __init__(self, result: Correction | None) -> None:
        self.result = result
        self.calls = 0

    async def correct(self, learner_text: str, partner_text: str | None, level: str):
        self.calls += 1
        return self.result


class FakeSpeaker:
    async def open_stream(self, text: str) -> SpeechStream:
        async def chunks() -> AsyncIterator[bytes]:
            yield b"\x00\x01"
            yield b"\x02\x03"

        return SpeechStream(PcmFormat(24000, 1), chunks())


class FakeTranscriber:
    def __init__(self, text: str) -> None:
        self.text = text

    async def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        return self.text


@pytest.fixture
def fakes(glosser: Glosser) -> dict:
    return {
        "partner": FakePartner(),
        "corrector": FakeCorrector(None),
        "transcriber": FakeTranscriber("映画を見ました"),
        "glosser": glosser,
    }


@pytest.fixture
def client(fakes: dict, dictionary: Dictionary) -> TestClient:
    app = create_app()
    overrides = app.dependency_overrides
    overrides[dependencies.get_partner] = lambda: fakes["partner"]
    overrides[dependencies.get_corrector] = lambda: fakes["corrector"]
    overrides[dependencies.get_glosser] = lambda: fakes["glosser"]
    overrides[dependencies.get_speaker] = FakeSpeaker
    overrides[dependencies.get_transcriber] = lambda: fakes["transcriber"]
    overrides[dependencies.get_dictionary] = lambda: dictionary
    return TestClient(app)
