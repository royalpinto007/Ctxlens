"""Tokenizer selection.

``get_tokenizer("auto")`` prefers tiktoken when available and silently falls
back to the heuristic tokenizer otherwise.

**Accuracy is format-dependent.** ``tiktoken`` defaults to OpenAI's
``cl100k_base`` encoding. That is exact for OpenAI/Codex chat transcripts and
only approximate for Claude Code sessions (Anthropic models do not use
``cl100k_base``). The heuristic is always an estimate. Callers must not treat
every tiktoken count as exact — use :func:`count_accuracy` / the analysis
``token_accuracy`` field.
"""

from __future__ import annotations

from typing import Literal

from ctxlens.tokenizers.base import Tokenizer
from ctxlens.tokenizers.heuristic import HeuristicTokenizer

# Source formats whose native tokenizers match OpenAI cl100k_base closely enough
# that a tiktoken:cl100k_base count is treated as exact.
_OPENAI_FORMATS = frozenset({"openai-chat", "codex-session"})

Accuracy = Literal["exact", "approximate"]


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
    ``tiktoken``  -> tiktoken (OpenAI cl100k_base), raising ImportError if unavailable

    The returned tokenizer's ``name`` identifies the encoding (e.g.
    ``tiktoken:cl100k_base``). Exactness for a given session still depends on
    ``source_format`` — see :func:`count_accuracy`.
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


def count_accuracy(tokenizer: Tokenizer, source_format: str) -> Accuracy:
    """Whether counts from ``tokenizer`` are exact for ``source_format``.

    * ``tiktoken:cl100k_base`` is exact for OpenAI chat and Codex sessions.
    * Claude Code and any other format are approximate under cl100k (wrong BPE).
    * The heuristic is always approximate.
    """
    name = getattr(tokenizer, "name", "") or ""
    if name.startswith("tiktoken:"):
        # Only claim exactness when the encoding matches the model family.
        # Default encoding is cl100k_base (OpenAI). No Anthropic encoding ships here.
        encoding = name.split(":", 1)[1]
        if encoding == "cl100k_base" and source_format in _OPENAI_FORMATS:
            return "exact"
        return "approximate"
    return "approximate"


def accuracy_note(tokenizer: Tokenizer, source_format: str) -> str | None:
    """Human-readable note when the count is approximate, else None."""
    if count_accuracy(tokenizer, source_format) == "exact":
        return None
    name = getattr(tokenizer, "name", "tokenizer")
    if name.startswith("tiktoken:") and source_format.startswith("claude"):
        return (
            f"{name} is OpenAI's cl100k_base encoding; counts for Claude Code "
            f"sessions ({source_format}) are approximate, not exact"
        )
    if name.startswith("tiktoken:"):
        return (
            f"{name} counts are approximate for source format {source_format!r} "
            "(no matching model encoding is available)"
        )
    return f"{name} is an estimate, not an exact model tokenizer count"
