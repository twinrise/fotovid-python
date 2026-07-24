"""Shared low-level request helper used by both the sync (_client.py) and the
async (_tasks.py) surfaces — same auth, UA, and error handling either way.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ._errors import FotovidError
from ._version import __version__


def clean(params: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is None so we only send provided params."""
    return {key: value for key, value in params.items() if value is not None}


def request_json(
    *,
    base_url: str,
    api_key: str,
    timeout: float,
    path: str,
    method: str,
    body: dict[str, Any] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        # An explicit UA is required: the default urllib UA
        # ("Python-urllib/x.y") is blocked by the edge (Cloudflare) with a
        # 403 before the request ever reaches the API.
        "User-Agent": f"fotovid-python/{__version__}",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    if extra_headers:
        headers.update(extra_headers)
    request = urllib.request.Request(
        base_url + path, data=data, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result: dict[str, Any] = json.loads(response.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as error:
        detail: Any = None
        try:
            detail = json.loads(error.read().decode("utf-8"))
        except Exception:
            detail = None
        ra: int | None = None
        raw_retry_after = error.headers.get("Retry-After")
        if raw_retry_after is not None:
            try:
                ra = int(raw_retry_after)
            except ValueError:
                pass
        raise FotovidError(error.code, detail, retry_after=ra) from None
