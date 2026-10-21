class HanasuError(Exception):
    """Mapped to HTTP status."""


class MissingApiKeyError(HanasuError):
    pass


class UpstreamError(HanasuError):
    """OpenRouter failure."""


class InvalidAudioError(HanasuError):
    pass


class AudioTooLargeError(HanasuError):
    pass


class NoSpeechError(HanasuError):
    pass


class NoSpeakableTextError(HanasuError):
    pass


class DictionaryMissingError(HanasuError):
    pass


class WordNotFoundError(HanasuError):
    pass
