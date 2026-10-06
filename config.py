"""Central configuration for ComicCraft.

All paths are absolute and derived from the project root, so the app works no
matter which directory uvicorn is started from. Secrets and tunables come from
environment variables (optionally loaded from a .env file in the project root).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# --- Folders -----------------------------------------------------------------
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
PANEL_FOLDER = STATIC_DIR / "panels"      # generated panel images
EXPORT_FOLDER = STATIC_DIR / "exports"    # exported comic PDFs
FONT_DIR = STATIC_DIR / "fonts"           # fonts for PDF generation
FONT_PATH = FONT_DIR / "DejaVuSans.ttf"
FONT_ITALIC_PATH = FONT_DIR / "DejaVuSans-Oblique.ttf"

for _folder in (PANEL_FOLDER, EXPORT_FOLDER, FONT_DIR):
    _folder.mkdir(parents=True, exist_ok=True)

# --- API keys ----------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
HF_API_KEY = os.getenv("HF_API_KEY", "").strip()  # optional: public SD models need no token

# --- Gemini models -----------------------------------------------------------
# The original docs used gemini-1.5-flash / gemini-1.5-pro. Those models have been
# shut down by Google (requests return 404), so the defaults below are current
# models. Override them in .env at any time.
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.5-flash-lite")  # fast outline
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-3.8-flash")           # richer story
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "120"))
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "3"))

# --- Image generation --------------------------------------------------------
# "diffusers"   -> real Stable Diffusion (needs torch + diffusers, ~4 GB download)
# "placeholder" -> fast fake images so you can test the whole app without a model
IMAGE_BACKEND = os.getenv("IMAGE_BACKEND", "diffusers").strip().lower()
# runwayml/stable-diffusion-v1-5 was removed from the Hub; this is the community mirror.
SD_MODEL_ID = os.getenv("SD_MODEL_ID", "stable-diffusion-v1-5/stable-diffusion-v1-5")
SD_STEPS = int(os.getenv("SD_STEPS", "0"))  # 0 = auto (30 on GPU, 20 on CPU)
SD_SIZE = int(os.getenv("SD_SIZE", "512"))  # width = height, multiple of 8

NUM_PANELS = 5


def to_web_path(path) -> str:
    """Convert an absolute file path inside the project to a web path like /static/x.png."""
    rel = Path(path).resolve().relative_to(BASE_DIR)
    return "/" + rel.as_posix()
