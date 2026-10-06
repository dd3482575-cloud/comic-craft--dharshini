import json

import pytest

from app.gemini_client import GeminiError
from app.gemini_flash import parse_outline
from tests.conftest import FAKE_OUTLINE


def test_parse_plain_json():
    assert len(parse_outline(json.dumps(FAKE_OUTLINE))) == 5


def test_parse_markdown_fenced_json():
    raw = "```json\n" + json.dumps(FAKE_OUTLINE) + "\n```"
    assert parse_outline(raw)[0]["title"] == "Title 1"


def test_parse_json_with_chatter_around_it():
    raw = "Sure! Here you go:\n" + json.dumps(FAKE_OUTLINE) + "\nEnjoy!"
    assert len(parse_outline(raw)) == 5


def test_parse_wrapped_in_object():
    assert len(parse_outline(json.dumps({"panels": FAKE_OUTLINE}))) == 5


def test_extra_panels_are_trimmed_to_five():
    many = FAKE_OUTLINE + [dict(FAKE_OUTLINE[0], panel=6)]
    assert len(parse_outline(json.dumps(many))) == 5


def test_missing_key_raises():
    bad = [{"panel": 1, "title": "x"}]
    with pytest.raises(GeminiError):
        parse_outline(json.dumps(bad))


def test_garbage_raises():
    with pytest.raises(GeminiError):
        parse_outline("this is not json")
