"""Parser interface.

A parser turns a raw transcript (a file path or already-loaded object) into a
:class:`~ctxlens.models.Session`. Every concrete parser implements
:meth:`sniff` for auto-detection and :meth:`parse`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ctxlens.models import Session


class ParseError(ValueError):
    """Raised when a transcript cannot be parsed by any known parser."""


class Parser(ABC):
    #: stable identifier stored on Session.source_format
    format_name: str = "base"

    @classmethod
    @abstractmethod
    def sniff(cls, raw: str, path: Path | None = None) -> float:
        """Return a confidence score in [0, 1] that ``raw`` is this format."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw: str, path: Path | None = None) -> Session:
        """Parse ``raw`` text into a :class:`Session`."""
        raise NotImplementedError
