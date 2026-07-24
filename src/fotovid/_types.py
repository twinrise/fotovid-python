from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WatermarkPosition = Literal[
    "top-left", "top-right", "bottom-left", "bottom-right", "center"
]
ImageFormat = Literal["webp", "jpeg", "jpg", "png"]
WatermarkType = Literal["text", "image", "combo"]
X264Preset = Literal[
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
    "placebo",
]


@dataclass
class MediaResult:
    """Result of a media-producing operation."""

    id: str
    type: str
    # Opaque, time-limited public URL on a custom domain
    # (e.g. https://tempfile.fotovid.co/...). Do not parse its query string;
    # it still expires (see expires_at) — keep your own copy.
    url: str
    expires_at: str
    duration: float | None = None


@dataclass
class ProbeResult:
    """Result of a probe — metadata only, no artifact."""

    id: str
    type: str
    width: int
    height: int
    duration_sec: float
    fps: str
    codec: str
    has_alpha: bool
