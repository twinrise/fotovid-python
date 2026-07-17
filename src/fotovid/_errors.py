from __future__ import annotations

from typing import Any


class FotovidError(Exception):
    """Raised when the Fotovid API returns a non-2xx response."""

    def __init__(self, status: int, detail: Any = None) -> None:
        message: str | None = None
        if isinstance(detail, dict):
            candidate = detail.get("detail") or detail.get("message")
            if isinstance(candidate, str):
                message = candidate
        super().__init__(message or f"Fotovid API request failed with status {status}")
        self.status = status
        self.detail = detail
