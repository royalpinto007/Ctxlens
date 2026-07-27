"""Tokenizer selection.

``get_tokenizer("auto")`` prefers tiktoken when available and silently falls
back to the heuristic tokenizer otherwise, so the default experience is exact
where possible and always works offline.
"""

from __future__ import annotations

from ctxlens.tokenizers.base import Tokenizer
from ctxlens.tokenizers.heuristic import HeuristicTokenizer


def _try_tiktoken(encoding: str = "cl100k_base") -> Tokenizer | None:
    try:
        from ctxlens.tokenizers.tiktoken_tokenizer import TiktokenTokenizer

        return TiktokenTokenizer(encoding)
    except ImportError:
        return None


def available_tokenizers() -> list[str]:
    names = ["heuristic"]
    if _try_tiktoken() is not None:
        names.append("tiktoken")
    return names


def get_tokenizer(name: str = "auto") -> Tokenizer:
    """Return a tokenizer by name.

    ``auto``      -> tiktoken if installed, else heuristic
    ``heuristic`` -> always the dependency-free heuristic
    ``tiktoken``  -> tiktoken, raising ImportError if unavailable
    """
    name = (name or "auto").lower()
    if name == "heuristic":
        return HeuristicTokenizer()
    if name == "tiktoken":
        tok = _try_tiktoken()
        if tok is None:
            raise ImportError(
                "tiktoken requested but not installed; install with ctxlens[tiktoken]"
            )
        return tok
    if name == "auto":
        return _try_tiktoken() or HeuristicTokenizer()
    raise ValueError(f"unknown tokenizer: {name!r}")
