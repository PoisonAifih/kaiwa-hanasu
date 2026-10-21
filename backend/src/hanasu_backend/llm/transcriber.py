from openai import NOT_GIVEN, AsyncOpenAI


class OpenRouterTranscriber:
    def __init__(self, client: AsyncOpenAI, model: str, language: str) -> None:
        self._client = client
        self._model = model
        self._language = language

    async def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        # No prompt (echo risk)
        result = await self._client.audio.transcriptions.create(
            model=self._model,
            file=(filename, audio, content_type),
            language=self._language or NOT_GIVEN,
        )
        return result.text.strip()
