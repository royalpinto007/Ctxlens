"""Token counting backed by tiktoken (optional dependency).

The default encoding is OpenAI's ``cl100k_base``. That is **exact for OpenAI /
Codex transcripts** and only an approximation for Claude Code sessions —
Anthropic models do not use this encoding. Prefer the analysis
``token_accuracy`` field over assuming every tiktoken count is exact.
"""

from __future__ import annotations

from ctxlens.tokenizers.base import Tokenizer


class TiktokenTokenizer(Tokenizer):
    """Wraps a tiktoken encoding.

    Constructing this raises :class:`ImportError` if tiktoken is not installed,
    so callers can fall back to the heuristic tokenizer gracefully.

    ``name`` always includes the encoding id (e.g. ``tiktoken:cl100k_base``) so
    reported counts are traceable to a specific vocabulary.
    """

    def __init__(self, encoding: str = "cl100k_base") -> None:
        try:
            import tiktoken
        except ImportError as exc:  # pragma: no cover - exercised only w/o extra
            raise ImportError(
                "tiktoken is not installed; install with `pip install ctxlens[tiktoken]`"
            ) from exc
        self.encoding = encoding
        self._enc = tiktoken.get_encoding(encoding)
        self.name = f"tiktoken:{encoding}"

    def count(self, text: str) -> int:
        if not text:
            return 0
        return len(self._enc.encode(text, disallowed_special=()))
