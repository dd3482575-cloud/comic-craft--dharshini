"""All HTTP routes for ComicCraft.

  GET  /                   homepage form
  POST /generate           form submit -> comic preview page
  POST /generate-comic/json  JSON API -> layout + PDF path
  GET  /export-success     download confirmation page
  GET  /test-image         developer utility: test image generation only
  GET  /health             quick configuration check
"""
import logging
import traceback

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import config
from app.exporters import save_pdf
from app.gemini_client import GeminiError
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import ImageGenerationError, generate_image
from app.layout_builder import build_comic_layout
from app.schemas import PromptRequest

logger = logging.getLogger("comiccraft")
router = APIRouter()
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

# Errors whose message is safe and useful to show to the user.
USER_ERRORS = (GeminiError, ImageGenerationError, ValueError)


def compose_prompt(prompt: str, character_name: str, setting: str, tone: str, style: str) -> str:
    """Combine the user's inputs into a single story prompt."""
    return (
        f"{prompt.strip()}\n"
        f"The main character is {character_name.strip()}. "
        f"The setting is: {setting.strip()}. "
        f"The tone is {tone.strip()}. The art style is {style.strip()}."
    )


def create_comic(prompt: str, character_name: str, setting: str, tone: str, style: str):
    """Run the full pipeline (blocking). Returns (layout, web_pdf_path)."""
    full_prompt = compose_prompt(prompt, character_name, setting, tone, style)

    outline = generate_outline(full_prompt)                                   # Step 1: Gemini Flash
    if not isinstance(outline, list) or not all("image_prompt" in p for p in outline):
        raise ValueError("Invalid outline structure from Gemini response.")

    full_story = generate_story(outline)                                      # Step 2: Gemini Pro
    images = [generate_image(p["image_prompt"], style=style) for p in outline]  # Step 3: Stable Diffusion
    layout = build_comic_layout(images, full_story, outline)                  # Step 4: layout
    pdf_path = save_pdf(layout)                                               # Step 5: PDF export
    return layout, config.to_web_path(pdf_path)


def _public_layout(layout: list) -> list:
    """Layout for API clients: hide server file-system paths."""
    return [{k: v for k, v in panel.items() if k != "image_path"} for panel in layout]


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"error": None, "form": {}})


@router.post("/generate", response_class=HTMLResponse)
async def generate_comic(
    request: Request,
    prompt: str = Form(..., min_length=3, max_length=1000),
    character_name: str = Form(..., min_length=1, max_length=60),
    setting: str = Form(..., min_length=1, max_length=80),
    tone: str = Form(..., min_length=1, max_length=40),
    style: str = Form(..., min_length=1, max_length=40),
):
    try:
        layout, web_pdf_path = await run_in_threadpool(
            create_comic, prompt, character_name, setting, tone, style
        )
        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={"layout": layout, "pdf_path": web_pdf_path},
        )
    except Exception as e:
        traceback.print_exc()
        message = str(e) if isinstance(e, USER_ERRORS) else f"Unexpected error: {e}"
        form = {"prompt": prompt, "character_name": character_name,
                "setting": setting, "tone": tone, "style": style}
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": message, "form": form},
            status_code=502 if isinstance(e, (GeminiError, ImageGenerationError)) else 500,
        )


@router.post("/generate-comic/json")
async def generate_comic_json(payload: PromptRequest):
    try:
        layout, web_pdf_path = await run_in_threadpool(
            create_comic, payload.prompt, payload.character_name, payload.setting, payload.tone, payload.style
        )
        return {"layout": _public_layout(layout), "pdf_path": web_pdf_path}
    except (GeminiError, ImageGenerationError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf_path: str = ""):
    # Only ever link to files inside /static/exports/ (prevents open-redirect style abuse).
    safe_path = pdf_path if pdf_path.startswith("/static/exports/") and ".." not in pdf_path else ""
    return templates.TemplateResponse(
        request=request, name="export_success.html", context={"pdf_path": safe_path}
    )


@router.get("/test-image")
async def test_image(prompt: str = "A futuristic city at sunset, sci-fi, cinematic, artstation", style: str = ""):
    try:
        image_path = await run_in_threadpool(generate_image, prompt, None, style or None)
        return {"message": "Image generated successfully", "path": config.to_web_path(image_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "gemini_key_set": bool(config.GEMINI_API_KEY),
        "image_backend": config.IMAGE_BACKEND,
        "flash_model": config.GEMINI_FLASH_MODEL,
        "pro_model": config.GEMINI_PRO_MODEL,
        "sd_model": config.SD_MODEL_ID,
    }
