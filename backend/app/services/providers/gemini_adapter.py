"""Gemini provider adapter.

Provides:
- ``analyse_screenshot``: sends an image to Gemini vision and returns structured enrichment.

Raises ``ProviderUnavailableError`` when the SDK or API key is absent.
"""

import json

from app.services.providers.config import ProviderUnavailableError, get_gemini_client

_VISION_MODEL = "gemini-2.0-flash"

_DEFAULT_SYSTEM_PROMPT = (
    "You are a personal productivity assistant. "
    "Analyse this screenshot and extract: "
    "(1) a concise one-sentence description of what is shown, "
    "(2) up to five relevant tags as a JSON array, "
    "(3) any visible text (OCR) as a single string, "
    "(4) the most likely project/task name (or null). "
    "Respond ONLY with valid JSON matching: "
    '{"description": "...", "tags": [...], "ocr_text": "...", "project_task": "..." | null}'
)


def analyse_screenshot(
    image_bytes: bytes,
    mime_type: str = "image/png",
    prompt: str | None = None,
) -> dict:
    """Analyse *image_bytes* using Gemini vision.

    Args:
        image_bytes: Raw bytes of the screenshot.
        mime_type:   MIME type hint, e.g. ``"image/png"`` or ``"image/jpeg"``.
        prompt:      Optional instruction overriding the default analysis prompt.

    Returns:
        ``{"description": str, "tags": list[str], "ocr_text": str,
           "inferred_project_task": str | None,
           "provenance": {"provider": "gemini", "model": "gemini-2.0-flash"}}``

    Raises:
        ProviderUnavailableError: SDK missing or key absent.
    """
    genai = get_gemini_client()

    try:
        model = genai.GenerativeModel(_VISION_MODEL)
    except Exception as exc:  # noqa: BLE001
        raise ProviderUnavailableError(f"Failed to initialise Gemini model: {exc}") from exc

    image_part = {"mime_type": mime_type, "data": image_bytes}
    instruction = prompt or _DEFAULT_SYSTEM_PROMPT

    response = model.generate_content([instruction, image_part])

    raw = response.text or "{}"
    # Strip markdown code fences if the model wraps JSON in them
    stripped = raw.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        stripped = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = {"description": raw, "tags": [], "ocr_text": raw, "project_task": None}

    return {
        "description": parsed.get("description", ""),
        "tags": parsed.get("tags", []),
        "ocr_text": parsed.get("ocr_text", ""),
        "inferred_project_task": parsed.get("project_task"),
        "provenance": {"provider": "gemini", "model": _VISION_MODEL},
    }
