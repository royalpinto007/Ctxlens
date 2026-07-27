"""Pluggable token counting.

The analysis layer never counts tokens directly; it goes through a
:class:`Tokenizer`. This keeps ctxlens usable with no heavy dependencies (the
:class:`HeuristicTokenizer` is deterministic and network-free) while still
allowing an exact count via tiktoken when it is installed.
"""

from ctxlens.tokenizers.base import Tokenizer
from ctxlens.tokenizers.heuristic import HeuristicTokenizer
from ctxlens.tokenizers.registry import available_tokenizers, get_tokenizer

__all__ = [
    "Tokenizer",
    "HeuristicTokenizer",
    "get_tokenizer",
    "available_tokenizers",
]
