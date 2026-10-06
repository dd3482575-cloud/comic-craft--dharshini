"""Thin wrapper around the official `google-genai` SDK.

Shared by gemini_flash.py (outline) and gemini_pro.py (story). Provides lazy client
creation, retries with backoff for transient errors, and readable exceptions.
"""
import threading
import time

from app import config


class GeminiError(RuntimeError):
    """Raised when a Gemini call fails in a way the user should hear about."""


_client = None
_client_lock = threading.Lock()


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not config.GEMINI_API_KEY:
        raise GeminiError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key "
            "from https://aistudio.google.com/apikey"
        )
    with _client_lock:
        if _client is None:
            from google import genai
            from google.genai import types

            try:  # request timeout in milliseconds; skip if this SDK version lacks the option
                http_options = types.HttpOptions(timeout=config.GEMINI_TIMEOUT_SECONDS * 1000)
            except Exception:
                http_options = None
            _client = genai.Client(api_key=config.GEMINI_API_KEY, http_options=http_options)
    return _client


def generate_text(model: str, prompt: str, *, json_mode: bool = False, temperature: float = 0.9) -> str:
    """Send a prompt to a Gemini model and return the response text."""
    from google.genai import types

    client = _get_client()
    cfg = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json" if json_mode else "text/plain",
    )

    last_error = None
    for attempt in range(1, config.GEMINI_MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(model=model, contents=prompt, config=cfg)
            text = (response.text or "").strip()
            if not text:
                raise GeminiError(f"Model '{model}' returned an empty response (possibly blocked by safety filters).")
            return text
        except GeminiError:
            raise
        except Exception as exc:  # SDK raises google.genai.errors.APIError subclasses
            last_error = exc
            code = getattr(exc, "code", None)
            retryable = code in (429, 500, 502, 503, 504) or code is None
            if code == 404:
                raise GeminiError(
                    f"Model '{model}' was not found (404). Set GEMINI_FLASH_MODEL / GEMINI_PRO_MODEL "
                    "in .env to a model that is currently available to your API key."
                ) from exc
            if code in (400, 401, 403):
                raise GeminiError(f"Gemini rejected the request ({code}): {exc}") from exc
            if not retryable or attempt == config.GEMINI_MAX_RETRIES:
                break
            time.sleep(2 ** attempt)  # 2s, 4s, ...

    raise GeminiError(f"Gemini request failed after {config.GEMINI_MAX_RETRIES} attempts: {last_error}")
