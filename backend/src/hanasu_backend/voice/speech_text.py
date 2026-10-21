import re

# Markdown stripping
INLINE_MARKUP = re.compile(r"(\*\*|__|\*|`|~~)")
HEADING_MARKER = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+", re.MULTILINE)
LIST_MARKER = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+", re.MULTILINE)
EXTRA_SPACE = re.compile(r"[ \t]+")


def clean_speech_text(text: str) -> str:
    text = HEADING_MARKER.sub("", text)
    text = LIST_MARKER.sub("", text)
    text = INLINE_MARKUP.sub("", text)
    return EXTRA_SPACE.sub(" ", text).strip()
