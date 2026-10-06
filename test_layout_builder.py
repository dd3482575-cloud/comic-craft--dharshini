import pytest

from app import config
from app.layout_builder import build_comic_layout, split_story
from tests.conftest import FAKE_OUTLINE, FAKE_STORY


def test_split_story_finds_all_panels_and_strips_markdown():
    parts = split_story(FAKE_STORY)
    assert sorted(parts) == [1, 2, 3, 4, 5]
    assert "**" not in parts[1]
    assert parts[2].startswith("Caption: Caption 2")


def test_split_story_handles_alternate_header_styles():
    story = "## Panel 1 - Start\nHello\n\nPanel 2: Next\nWorld"
    parts = split_story(story)
    assert parts[1] == "Hello" and parts[2] == "World"


def test_build_layout_matches_images_and_text():
    images = [str(config.PANEL_FOLDER / f"p{i}.png") for i in range(1, 6)]
    layout = build_comic_layout(images, FAKE_STORY, FAKE_OUTLINE)
    assert [p["panel"] for p in layout] == [1, 2, 3, 4, 5]
    assert layout[0]["title"] == "Title 1"
    assert layout[0]["image_url"] == "/static/panels/p1.png"
    assert "Narration: Narration 1" in layout[0]["text"]


def test_build_layout_falls_back_to_scene_when_story_missing():
    images = [str(config.PANEL_FOLDER / "a.png")]
    layout = build_comic_layout(images, "no panels here", FAKE_OUTLINE[:1])
    assert layout[0]["text"] == "Scene 1."


def test_build_layout_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        build_comic_layout([], FAKE_STORY, FAKE_OUTLINE)
