import pytest
from fastapi.testclient import TestClient

from app import routes
from app.gemini_client import GeminiError
from app.main import app
from tests.conftest import FAKE_OUTLINE, FAKE_STORY

client = TestClient(app)
FORM = {"prompt": "A brave fox explores an enchanted forest.", "character_name": "Finn",
        "setting": "forest", "tone": "dramatic", "style": "comic book"}


@pytest.fixture
def fake_gemini(monkeypatch):
    monkeypatch.setattr(routes, "generate_outline", lambda prompt: [dict(p) for p in FAKE_OUTLINE])
    monkeypatch.setattr(routes, "generate_story", lambda outline: FAKE_STORY)


def test_home_page_renders_form():
    r = client.get("/")
    assert r.status_code == 200
    assert 'action="/generate"' in r.text and "Create Your Comic" in r.text


def test_health():
    data = client.get("/health").json()
    assert data["status"] == "ok" and data["image_backend"] == "placeholder"


def test_generate_form_shows_preview_with_five_panels(fake_gemini):
    r = client.post("/generate", data=FORM)
    assert r.status_code == 200
    assert r.text.count('class="panel"') == 5
    assert "Panel 3: Title 3" in r.text
    assert "Download Your Comic as PDF" in r.text
    assert "/static/exports/comic_" in r.text


def test_generated_pdf_and_images_are_served(fake_gemini):
    data = client.post("/generate-comic/json", json=FORM).json()
    pdf = client.get(data["pdf_path"])
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert client.get(data["layout"][0]["image_url"]).status_code == 200


def test_generate_json_hides_filesystem_paths(fake_gemini):
    data = client.post("/generate-comic/json", json=FORM).json()
    assert len(data["layout"]) == 5
    assert all("image_path" not in p for p in data["layout"])


def test_json_validation_error_for_short_prompt():
    assert client.post("/generate-comic/json", json={"prompt": "x"}).status_code == 422


def test_gemini_failure_is_shown_on_form_page(monkeypatch):
    def boom(prompt):
        raise GeminiError("quota exceeded")
    monkeypatch.setattr(routes, "generate_outline", boom)
    r = client.post("/generate", data=FORM)
    assert r.status_code == 502 and "quota exceeded" in r.text
    assert "A brave fox explores" in r.text  # form values preserved


def test_gemini_failure_json_returns_502(monkeypatch):
    def boom(prompt):
        raise GeminiError("no key")
    monkeypatch.setattr(routes, "generate_outline", boom)
    r = client.post("/generate-comic/json", json=FORM)
    assert r.status_code == 502 and r.json()["detail"] == "no key"


def test_export_success_page_and_link_safety():
    ok = client.get("/export-success", params={"pdf_path": "/static/exports/comic_1.pdf"})
    assert "Comic Exported Successfully" in ok.text and "/static/exports/comic_1.pdf" in ok.text
    evil = client.get("/export-success", params={"pdf_path": "https://evil.example/x.pdf"})
    assert "evil.example" not in evil.text


def test_test_image_route():
    data = client.get("/test-image", params={"prompt": "a robot", "style": "pixel art"}).json()
    assert data["message"] == "Image generated successfully"
    assert client.get(data["path"]).status_code == 200
