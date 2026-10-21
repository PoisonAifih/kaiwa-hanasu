import pytest

from hanasu_backend.errors import InvalidAudioError
from hanasu_backend.llm.speaker import read_pcm_format
from hanasu_backend.voice.audio import MP4, OGG, WAV, WEBM, detect_audio_format


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (b"\x1a\x45\xdf\xa3rest", WEBM),
        (b"OggSrest", OGG),
        (b"RIFF\x00\x00\x00\x00WAVEfmt ", WAV),
        (b"\x00\x00\x00\x20ftypM4A ", MP4),
    ],
)
def test_detects_browser_formats(header: bytes, expected) -> None:
    assert detect_audio_format(header) == expected


def test_rejects_empty_audio() -> None:
    with pytest.raises(InvalidAudioError):
        detect_audio_format(b"")


def test_reads_pcm_format_with_defaults() -> None:
    assert read_pcm_format("audio/pcm;rate=16000;channels=2").sample_rate == 16000
    assert read_pcm_format("audio/pcm").sample_rate == 24000
