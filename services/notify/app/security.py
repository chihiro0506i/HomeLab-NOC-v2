"""API‑token authentication helpers."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException, status


_NOTIFY_API_TOKEN: str = os.getenv("NOTIFY_API_TOKEN", "")


async def verify_token(
    x_notify_token: str = Header(..., alias="X-Notify-Token"),
) -> str:
    """FastAPI dependency that validates the ``X-Notify-Token`` header.

    Returns the token string on success so that downstream handlers can
    use it if needed.  Raises *401 Unauthorized* if the token is missing,
    empty, or does not match ``NOTIFY_API_TOKEN``.
    """
    if not _NOTIFY_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="NOTIFY_API_TOKEN is not configured on the server.",
        )
    if x_notify_token != _NOTIFY_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token.",
        )
    return x_notify_token
