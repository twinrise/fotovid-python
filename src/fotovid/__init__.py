"""Typed Python client for the Fotovid media API."""

from ._client import Fotovid
from ._errors import FotovidError
from ._types import MediaResult, ProbeResult
from ._version import __version__

__all__ = ["Fotovid", "FotovidError", "MediaResult", "ProbeResult", "__version__"]
