"""Deterministic, dependency-free heuristic tokenizer.

This does not reproduce any specific BPE vocabulary, but it approximates real
tokenizers well enough for *relative* profiling (which segment dominates, how
context grows, where the waste is). It is fully deterministic so tests and CI
need no network and no heavy dependencies.

The model: split text into word-ish, number, and symbol runs, then charge
longer runs more than one token (mirroring how BPE breaks long words into
several pieces). Whitespace is folded into adjacent tokens rather than counted
separately.
"""

from __future__ import annotations

import re

from ctxlens.tokenizers.base import Tokenizer

# words (incl. unicode letters), numbers, or any single non-space symbol
_TOKEN_RE = re.compile(r"[^\W\d_]+|\d+|[^\s\w]", re.UNICODE)

# average characters a real tokenizer packs into one token for long word runs
_CHARS_PER_PIECE = 4


class HeuristicTokenizer(Tokenizer):
    name = "heuristic"

    def count(self, text: str) -> int:
        if not text:
            return 0
        total = 0
        for match in _TOKEN_RE.finditer(text):
            piece = match.group(0)
            n = len(piece)
            if n <= _CHARS_PER_PIECE:
                total += 1
            else:
                # long runs get broken into multiple sub-tokens, rounding up
                total += (n + _CHARS_PER_PIECE - 1) // _CHARS_PER_PIECE
        return total
