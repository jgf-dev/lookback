"""API key authentication dependency.

When ``LOOKBACK_API_KEY`` is **not** set in the environment the application runs
in *dev mode*: every request is accepted and the actor is labelled ``"anonymous"``.

When ``LOOKBACK_API_KEY`` **is** set every request to a protected endpoint must
carry the header ``X-API-Key: <key>``.  A missing or wrong key returns HTTP 403.
"""

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

_ACTOR_ANONYMOUS = "anonymous"
_ACTOR_KEY_USER = "api_key_user"


def require_auth(api_key: str | None = Security(_HEADER)) -> str:
    """Validate the ``X-API-Key`` header and return the actor label.

    Returns:
        ``"anonymous"`` in dev mode (no key configured), ``"api_key_user"``
        when a valid key is supplied.

    Raises:
        HTTPException 403: when a key is configured but the header is missing
            or does not match.
    """
    expected = os.environ.get("LOOKBACK_API_KEY", "").strip()
    if not expected:
        return _ACTOR_ANONYMOUS  # dev mode — authentication disabled

    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Invalid or missing API key. "
                "Supply the correct value in the X-API-Key request header."
            ),
        )
    return _ACTOR_KEY_USER
