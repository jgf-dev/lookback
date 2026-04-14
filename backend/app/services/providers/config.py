"""Provider configuration: reads API keys from environment and exposes lazy client factories."""

import os


class ProviderUnavailableError(RuntimeError):
    """Raised when a provider SDK is missing or no API key is configured."""


def get_openai_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ProviderUnavailableError(
            "OPENAI_API_KEY is not set. "
            "Set it in your environment or .env file to enable OpenAI features."
        )
    return key


def get_gemini_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ProviderUnavailableError(
            "GEMINI_API_KEY is not set. "
            "Set it in your environment or .env file to enable Gemini features."
        )
    return key


def get_openai_client():
    """Return an authenticated ``openai.OpenAI`` client.

    Raises:
        ProviderUnavailableError: if the ``openai`` package is not installed or the key is absent.
    """
    try:
        import openai  # noqa: PLC0415
    except ImportError as exc:
        raise ProviderUnavailableError(
            "The 'openai' package is not installed. "
            "Install it with: pip install 'lookback-backend[ai]'"
        ) from exc

    api_key = get_openai_api_key()
    return openai.OpenAI(api_key=api_key)


def get_gemini_client():
    """Return a configured ``google.generativeai`` module (configured with the API key).

    Raises:
        ProviderUnavailableError: if ``google-generativeai`` is not installed or the key is absent.
    """
    try:
        import google.generativeai as genai  # noqa: PLC0415
    except ImportError as exc:
        raise ProviderUnavailableError(
            "The 'google-generativeai' package is not installed. "
            "Install it with: pip install 'lookback-backend[ai]'"
        ) from exc

    api_key = get_gemini_api_key()
    genai.configure(api_key=api_key)
    return genai
