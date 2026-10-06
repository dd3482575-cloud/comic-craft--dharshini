import pytest
from PIL import Image

from app.image_generator import ImageGenerationError, generate_image, sanitize_filename


def test_sanitize_filename_is_safe_and_unique():
    a = sanitize_filename("A fox / in: <the> forest?!")
    b = sanitize_filename("A fox / in: <the> forest?!")
    assert a.endswith(".png") and a != b
    assert all(c.isalnum() or c in "_." for c in a)


def test_placeholder_backend_creates_png():
    path = generate_image("a brave fox", style="anime")
    with Image.open(path) as im:
        assert im.size[0] == im.size[1] > 0


def test_empty_prompt_rejected():
    with pytest.raises(ImageGenerationError):
        generate_image("   ")


def test_custom_filename_cannot_escape_folder():
    path = generate_image("fox", filename="../../evil")
    assert path.endswith("evil.png") and "static" in path
