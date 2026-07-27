"""Exact token counting backed by tiktoken (optional dependency)."""

from __future__ import annotations

from ctxlens.tokenizers.base import Tokenizer


class TiktokenTokenizer(Tokenizer):
    """Wraps a tiktoken encoding.

    Constructing this raises :class:`ImportError` if tiktoken is not installed,
    so callers can fall back to the heuristic tokenizer gracefully.
    """

    def __init__(self, encoding: str = "cl100k_base") -> None:
        try:
            import tiktoken
        except ImportError as exc:  # pragma: no cover - exercised only w/o extra
            raise ImportError(
                "tiktoken is not installed; install with `pip install ctxlens[tiktoken]`"
            ) from exc
        self._enc = tiktoken.get_encoding(encoding)
        self.name = f"tiktoken:{encoding}"

    def count(self, text: str) -> int:
        if not text:
            return 0
        return len(self._enc.encode(text, disallowed_special=()))
