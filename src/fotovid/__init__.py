"""Typed Python client for the Fotovid media API."""

from ._client import Fotovid
from ._errors import FotovidError
from ._types import MediaResult, ProbeResult

__all__ = ["Fotovid", "FotovidError", "MediaResult", "ProbeResult"]
__version__ = "0.1.0"
