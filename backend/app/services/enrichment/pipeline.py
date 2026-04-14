from app.services.providers.config import ProviderUnavailableError


def enrich_with_context(raw_content: str) -> dict:
    """Enrich *raw_content* using GPT-4o reasoning when available.

    When the OpenAI provider is unavailable (SDK not installed or
    ``OPENAI_API_KEY`` not set) this falls back to the original local
    contextual-expansion stub so the pipeline continues to work.

    Args:
        raw_content: The raw text to enrich.

    Returns:
        Dict with ``enriched_content``, ``tags``, ``inferred_project_task``
        (may be *None*), and ``enriched_provenance``.
    """
    try:
        from app.services.providers.openai_adapter import reason_about_text  # noqa: PLC0415

        result = reason_about_text(raw_content)
        return {
            "enriched_content": result["enriched_content"],
            "tags": result["tags"],
            "inferred_project_task": result["inferred_project_task"],
            "enriched_provenance": result["provenance"],
        }
    except ProviderUnavailableError:
        return {
            "enriched_content": f"Contextual expansion: {raw_content}",
            "tags": [],
            "inferred_project_task": None,
            "enriched_provenance": {"provider": "internal", "method": "contextual_expansion"},
        }


def enrich_with_screenshot(image_bytes: bytes, mime_type: str = "image/png") -> dict:
    """Analyse a screenshot using Gemini vision.

    Falls back to a stub description when the Gemini provider is unavailable.

    Args:
        image_bytes: Raw bytes of the screenshot.
        mime_type:   MIME type hint (e.g. ``"image/png"`` or ``"image/jpeg"``).

    Returns:
        Dict with ``enriched_content`` (description), ``tags``, ``ocr_text``,
        ``inferred_project_task`` (may be *None*), and ``enriched_provenance``.
    """
    try:
        from app.services.providers.gemini_adapter import analyse_screenshot  # noqa: PLC0415

        result = analyse_screenshot(image_bytes, mime_type=mime_type)
        return {
            "enriched_content": result["description"],
            "tags": result["tags"],
            "ocr_text": result["ocr_text"],
            "inferred_project_task": result["inferred_project_task"],
            "enriched_provenance": result["provenance"],
        }
    except ProviderUnavailableError:
        return {
            "enriched_content": "[screenshot analysis unavailable — Gemini provider not configured]",
            "tags": [],
            "ocr_text": "",
            "inferred_project_task": None,
            "enriched_provenance": {"provider": "fallback", "method": "placeholder"},
        }
