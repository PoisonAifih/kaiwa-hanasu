from fastapi.testclient import TestClient

from hanasu_backend.conversation.models import Correction

WEBM_HEADER = b"\x1a\x45\xdf\xa3" + b"\x00" * 16


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_opener_has_no_correction(client: TestClient, fakes: dict) -> None:
    response = client.post("/api/chat", json={"messages": []})
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "映画を見ましたか？"
    assert body["translation"] == "Did you watch a movie?"
    assert body["correction"] is None
    assert fakes["corrector"].calls == 0


def test_learner_turn_gets_correction_and_tokens(client: TestClient, fakes: dict) -> None:
    fakes["corrector"].result = Correction(ok=True, original="はい", corrected="はい", issues=[])
    response = client.post(
        "/api/chat",
        json={
            "messages": [
                {"role": "assistant", "content": "こんにちは"},
                {"role": "user", "content": "はい"},
            ],
            "level": "intermediate",
            "scenario": "cafe",
        },
    )
    body = response.json()
    assert body["correction"]["ok"] is True
    surfaces = [t["surface"] for t in body["tokens"]]
    assert "".join(surfaces) == body["reply"]
    movie = next(t for t in body["tokens"] if t["surface"] == "映画")
    assert movie["gloss"] == "movie"
    assert movie["furigana"] == [{"text": "映画", "ruby": "えいが"}]


def test_failed_correction_is_null_not_ok(client: TestClient, fakes: dict) -> None:
    fakes["corrector"].result = None
    response = client.post("/api/chat", json={"messages": [{"role": "user", "content": "はい"}]})
    assert response.status_code == 200
    assert response.json()["correction"] is None
    assert fakes["corrector"].calls == 1


def test_correct_retry_returns_correction(client: TestClient, fakes: dict) -> None:
    fakes["corrector"].result = Correction(ok=True, original="はい", corrected="はい", issues=[])
    assert client.post("/api/correct", json={"text": "はい"}).json()["ok"] is True


def test_correct_retry_failure_is_503(client: TestClient, fakes: dict) -> None:
    fakes["corrector"].result = None
    assert client.post("/api/correct", json={"text": "はい"}).status_code == 503


def test_history_is_trimmed(client: TestClient, fakes: dict) -> None:
    messages = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(41)
    ]
    client.post("/api/chat", json={"messages": messages})
    seen = fakes["partner"].seen
    assert len(seen) == 19
    assert seen[0].role == "user"
    assert seen[-1].content == "m40"


def test_unknown_level_is_rejected(client: TestClient) -> None:
    response = client.post("/api/chat", json={"messages": [], "level": "expert"})
    assert response.status_code == 422


def test_stt_returns_transcript(client: TestClient) -> None:
    response = client.post("/api/stt", files={"audio": ("a.webm", WEBM_HEADER, "audio/webm")})
    assert response.json() == {"text": "映画を見ました"}


def test_stt_with_no_speech_is_422(client: TestClient, fakes: dict) -> None:
    fakes["transcriber"].text = ""
    response = client.post("/api/stt", files={"audio": ("a.webm", WEBM_HEADER, "audio/webm")})
    assert response.status_code == 422


def test_stt_rejects_unknown_format(client: TestClient) -> None:
    response = client.post("/api/stt", files={"audio": ("a.txt", b"hello world!", "text/plain")})
    assert response.status_code == 415


def test_tts_streams_pcm(client: TestClient) -> None:
    response = client.post("/api/tts", json={"text": "**こんにちは**"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/pcm;rate=24000")
    assert response.content == b"\x00\x01\x02\x03"


def test_tts_with_only_markup_is_422(client: TestClient) -> None:
    assert client.post("/api/tts", json={"text": "**"}).status_code == 422


def test_word_detail(client: TestClient) -> None:
    body = client.get("/api/words/2").json()
    assert body["kanji"] == ["見る"]
    assert body["senses"][0]["glosses"] == ["to see", "to look"]
    assert body["senses"][0]["parts_of_speech"] == ["Ichidan verb"]


def test_unknown_word_is_404(client: TestClient) -> None:
    assert client.get("/api/words/999999").status_code == 404
