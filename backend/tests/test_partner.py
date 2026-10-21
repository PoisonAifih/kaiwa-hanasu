from hanasu_backend.conversation.partner import parse_reply


def test_parses_reply_and_translation() -> None:
    reply = parse_reply('{"reply": "**こんにちは**", "translation": " Hello "}')
    assert reply.text == "こんにちは"
    assert reply.translation == "Hello"


def test_plain_text_still_counts_as_reply() -> None:
    reply = parse_reply("こんにちは。元気ですか。")
    assert reply.text == "こんにちは。元気ですか。"
    assert reply.translation is None


def test_japanese_copied_into_translation_is_dropped() -> None:
    reply = parse_reply('{"reply": "何を買いましたか。", "translation": "何を買いましたか。"}')
    assert reply.translation is None


def test_empty_translation_becomes_none() -> None:
    assert parse_reply('{"reply": "はい", "translation": ""}').translation is None
