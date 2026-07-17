from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from typing import Any

from ._errors import FotovidError
from ._types import (
    ImageFormat,
    MediaResult,
    ProbeResult,
    WatermarkPosition,
    WatermarkType,
    X264Preset,
)

DEFAULT_BASE_URL = "https://api.fotovid.co"


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is None so we only send provided params."""
    return {key: value for key, value in params.items() if value is not None}


def _media(data: dict[str, Any]) -> MediaResult:
    return MediaResult(
        id=data["id"],
        type=data["type"],
        url=data["url"],
        expires_at=data["expires_at"],
        duration=data.get("duration"),
    )


def _probe(data: dict[str, Any]) -> ProbeResult:
    return ProbeResult(
        id=data["id"],
        type=data["type"],
        width=data["width"],
        height=data["height"],
        duration_sec=data["durationSec"],
        fps=data["fps"],
        codec=data["codec"],
        has_alpha=data["hasAlpha"],
    )


class Fotovid:
    """Typed client for the Fotovid media API.

    Methods mirror the REST resources (``client.video.*``, ``client.image.*``,
    ``client.audio.*``); parameter names match the API 1:1 (``source_url``,
    ``watermark_image_url``, ...).
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        key = api_key or os.environ.get("FOTOVID_API_KEY")
        if not key:
            raise ValueError(
                "Fotovid: missing API key. Pass api_key=... or set FOTOVID_API_KEY."
            )
        self._api_key = key
        self._base_url = (
            base_url or os.environ.get("FOTOVID_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self._timeout = timeout
        self.video = _Video(self)
        self.image = _Image(self)
        self.audio = _Audio(self)

    def _post(
        self,
        path: str,
        source_url: str,
        params: dict[str, Any],
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        body = json.dumps({"source_url": source_url, "params": params}).encode("utf-8")
        request = urllib.request.Request(
            self._base_url + path,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
                # Billed endpoints require an idempotency key; default to a fresh
                # UUID per call, overridable to make a retry replay (not re-charge).
                "Idempotency-Key": idempotency_key or str(uuid.uuid4()),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                data: dict[str, Any] = json.loads(response.read().decode("utf-8"))
                return data
        except urllib.error.HTTPError as error:
            detail: Any = None
            try:
                detail = json.loads(error.read().decode("utf-8"))
            except Exception:
                detail = None
            raise FotovidError(error.code, detail) from None


class _Video:
    def __init__(self, client: Fotovid) -> None:
        self._client = client

    def watermark(
        self,
        *,
        source_url: str,
        watermark_type: WatermarkType | None = None,
        text: str | None = None,
        font_size: int | None = None,
        font_color: str | None = None,
        watermark_image_url: str | None = None,
        scale: float | None = None,
        opacity: float | None = None,
        position: WatermarkPosition | None = None,
        padding: int | None = None,
        output_format: ImageFormat | None = None,
        quality: int | None = None,
        preset: X264Preset | None = None,
        idempotency_key: str | None = None,
    ) -> MediaResult:
        params = _clean(
            {
                "watermark_type": watermark_type,
                "text": text,
                "font_size": font_size,
                "font_color": font_color,
                "watermark_image_url": watermark_image_url,
                "scale": scale,
                "opacity": opacity,
                "position": position,
                "padding": padding,
                "output_format": output_format,
                "quality": quality,
                "preset": preset,
            }
        )
        return _media(
            self._client._post(
                "/v1/video/watermark", source_url, params, idempotency_key
            )
        )

    def trim(
        self,
        *,
        source_url: str,
        start: float | None = None,
        end: float | None = None,
        idempotency_key: str | None = None,
    ) -> MediaResult:
        params = _clean({"start": start, "end": end})
        return _media(
            self._client._post("/v1/video/trim", source_url, params, idempotency_key)
        )

    def extract_audio(
        self, *, source_url: str, idempotency_key: str | None = None
    ) -> MediaResult:
        return _media(
            self._client._post(
                "/v1/video/extract-audio", source_url, {}, idempotency_key
            )
        )

    def thumbnail(
        self,
        *,
        source_url: str,
        at: float | None = None,
        output_format: ImageFormat | None = None,
        quality: int | None = None,
        idempotency_key: str | None = None,
    ) -> MediaResult:
        params = _clean({"at": at, "output_format": output_format, "quality": quality})
        return _media(
            self._client._post(
                "/v1/video/extract-cover", source_url, params, idempotency_key
            )
        )

    def probe(
        self, *, source_url: str, idempotency_key: str | None = None
    ) -> ProbeResult:
        return _probe(
            self._client._post("/v1/video/probe", source_url, {}, idempotency_key)
        )


class _Image:
    def __init__(self, client: Fotovid) -> None:
        self._client = client

    def watermark(
        self,
        *,
        source_url: str,
        watermark_type: WatermarkType | None = None,
        text: str | None = None,
        font_size: int | None = None,
        font_color: str | None = None,
        watermark_image_url: str | None = None,
        scale: float | None = None,
        opacity: float | None = None,
        position: WatermarkPosition | None = None,
        padding: int | None = None,
        output_format: ImageFormat | None = None,
        quality: int | None = None,
        idempotency_key: str | None = None,
    ) -> MediaResult:
        params = _clean(
            {
                "watermark_type": watermark_type,
                "text": text,
                "font_size": font_size,
                "font_color": font_color,
                "watermark_image_url": watermark_image_url,
                "scale": scale,
                "opacity": opacity,
                "position": position,
                "padding": padding,
                "output_format": output_format,
                "quality": quality,
            }
        )
        return _media(
            self._client._post(
                "/v1/image/watermark", source_url, params, idempotency_key
            )
        )


class _Audio:
    def __init__(self, client: Fotovid) -> None:
        self._client = client

    def trim(
        self,
        *,
        source_url: str,
        start: float | None = None,
        end: float | None = None,
        idempotency_key: str | None = None,
    ) -> MediaResult:
        params = _clean({"start": start, "end": end})
        return _media(
            self._client._post("/v1/audio/trim", source_url, params, idempotency_key)
        )
