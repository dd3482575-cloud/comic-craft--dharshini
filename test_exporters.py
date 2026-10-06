from app.exporters import save_pdf
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from tests.conftest import FAKE_OUTLINE, FAKE_STORY


def test_save_pdf_creates_valid_pdf_with_emoji_and_unicode():
    images = [generate_image(p["image_prompt"]) for p in FAKE_OUTLINE]
    story = FAKE_STORY.replace("Line 1!", "Héllo “quoted” 🦊 ñ")
    layout = build_comic_layout(images, story, FAKE_OUTLINE)
    path = save_pdf(layout)
    with open(path, "rb") as f:
        head = f.read(5)
    assert head == b"%PDF-" and path.endswith(".pdf")
