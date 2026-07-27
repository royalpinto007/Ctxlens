"""Tokenizer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Tokenizer(ABC):
    """Abstract token counter.

    Implementations must be deterministic for a given input so analysis output
    is reproducible.
    """

    #: short stable identifier, e.g. "heuristic" or "tiktoken:cl100k_base"
    name: str = "base"

    @abstractmethod
    def count(self, text: str) -> int:
        """Return the number of tokens in ``text``."""
        raise NotImplementedError

    def count_all(self, texts: list[str]) -> list[int]:
        return [self.count(t) for t in texts]
