"""Test setup: force offline-friendly settings BEFORE the app is imported."""
import os

os.environ["IMAGE_BACKEND"] = "placeholder"
os.environ["GEMINI_API_KEY"] = "test-key"

import pytest  # noqa: E402

from app import config  # noqa: E402

FAKE_OUTLINE = [
    {"panel": i, "title": f"Title {i}", "scene_description": f"Scene {i}.", "image_prompt": f"a fox in a forest, scene {i}"}
    for i in range(1, 6)
]
FAKE_STORY = "\n\n".join(
    f'**Panel {i}: Title {i}**\nCaption: Caption {i}\nNarration: Narration {i}\nDialogue:\nFinn: "Line {i}!"'
    for i in range(1, 6)
)


@pytest.fixture(autouse=True)
def cleanup_generated_files():
    """Delete any PNG/PDF files a test created in static/panels and static/exports."""
    before = {p for d in (config.PANEL_FOLDER, config.EXPORT_FOLDER) for p in d.iterdir()}
    yield
    for d in (config.PANEL_FOLDER, config.EXPORT_FOLDER):
        for p in d.iterdir():
            if p not in before and p.name != ".gitkeep":
                p.unlink()
