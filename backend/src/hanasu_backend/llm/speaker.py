from collections.abc import AsyncIterator
from contextlib import AsyncExitStack
from dataclasses import dataclass

from openai import AsyncOpenAI

# Raw PCM, streamed through
PCM_FORMAT = "pcm"
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_CHANNELS = 1


@dataclass(frozen=True, slots=True)
class PcmFormat:
    sample_rate: int
    channels: int

    @property
    def content_type(self) -> str:
        return f"audio/pcm;rate={self.sample_rate};channels={self.channels}"


@dataclass(frozen=True, slots=True)
class SpeechStream:
    """PCM stream."""

    pcm_format: PcmFormat
    chunks: AsyncIterator[bytes]


class OpenRouterSpeaker:
    def __init__(self, client: AsyncOpenAI, model: str, voice: str) -> None:
        self._client = client
        self._model = model
        self._voice = voice

    async def open_stream(self, text: str) -> SpeechStream:
        """Raises before any audio is sent."""
        connection = AsyncExitStack()
        response = await connection.enter_async_context(
            self._client.audio.speech.with_streaming_response.create(
                model=self._model, voice=self._voice, input=text, response_format=PCM_FORMAT
            )
        )
        pcm_format = read_pcm_format(response.headers.get("content-type", ""))
        return SpeechStream(pcm_format, _read_chunks(response.iter_bytes(), connection))


async def _read_chunks(
    chunks: AsyncIterator[bytes], connection: AsyncExitStack
) -> AsyncIterator[bytes]:
    async with connection:
        async for chunk in chunks:
            yield chunk


def read_pcm_format(content_type: str) -> PcmFormat:
    """audio/pcm;rate=24000;channels=1"""
    params = dict(
        part.strip().split("=", 1) for part in content_type.split(";")[1:] if "=" in part
    )
    rate, channels = params.get("rate", ""), params.get("channels", "")
    return PcmFormat(
        sample_rate=int(rate) if rate.isdigit() else DEFAULT_SAMPLE_RATE,
        channels=int(channels) if channels.isdigit() else DEFAULT_CHANNELS,
    )
