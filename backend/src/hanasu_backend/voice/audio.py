from dataclasses import dataclass

from hanasu_backend.errors import InvalidAudioError

# Magic bytes
WEBM_SIGNATURE = b"\x1a\x45\xdf\xa3"
OGG_SIGNATURE = b"OggS"
RIFF_SIGNATURE = b"RIFF"
WAVE_MARKER = b"WAVE"
MP4_MARKER = b"ftyp"
ID3_SIGNATURE = b"ID3"
MP3_FRAME_SYNC = 0xFF


@dataclass(frozen=True, slots=True)
class AudioFormat:
    filename: str
    content_type: str


WEBM = AudioFormat("speech.webm", "audio/webm")
OGG = AudioFormat("speech.ogg", "audio/ogg")
WAV = AudioFormat("speech.wav", "audio/wav")
MP4 = AudioFormat("speech.m4a", "audio/mp4")
MP3 = AudioFormat("speech.mp3", "audio/mpeg")


def detect_audio_format(audio: bytes) -> AudioFormat:
    if not audio:
        raise InvalidAudioError("The recording is empty")
    if audio.startswith(WEBM_SIGNATURE):
        return WEBM
    if audio.startswith(OGG_SIGNATURE):
        return OGG
    if audio.startswith(RIFF_SIGNATURE) and audio[8:12] == WAVE_MARKER:
        return WAV
    if audio[4:8] == MP4_MARKER:
        return MP4
    if _is_mp3(audio):
        return MP3
    raise InvalidAudioError("Unsupported audio format. Use webm, ogg, wav, m4a or mp3")


def _is_mp3(audio: bytes) -> bool:
    if audio.startswith(ID3_SIGNATURE):
        return True
    # Frame sync
    return len(audio) > 1 and audio[0] == MP3_FRAME_SYNC and audio[1] & 0xE0 == 0xE0
