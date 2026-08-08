"""Pluggable token counting.

The analysis layer never counts tokens directly; it goes through a
:class:`Tokenizer`. This keeps ctxlens usable with no heavy dependencies (the
:class:`HeuristicTokenizer` is deterministic and network-free) while still
allowing OpenAI-exact counts via tiktoken when it is installed.

Tiktoken's default encoding is OpenAI ``cl100k_base``. It is **not** exact for
Claude Code sessions; see :func:`count_accuracy`.
"""

from ctxlens.tokenizers.base import Tokenizer
from ctxlens.tokenizers.heuristic import HeuristicTokenizer
from ctxlens.tokenizers.registry import (
    accuracy_note,
    available_tokenizers,
    count_accuracy,
    get_tokenizer,
)

__all__ = [
    "Tokenizer",
    "HeuristicTokenizer",
    "get_tokenizer",
    "available_tokenizers",
    "count_accuracy",
    "accuracy_note",
]
