"""Transcript parsers with format auto-detection."""

from __future__ import annotations

from pathlib import Path

from ctxlens.models import Session
from ctxlens.parsers.base import ParseError, Parser
from ctxlens.parsers.claude_code import ClaudeCodeParser
from ctxlens.parsers.codex import CodexParser
from ctxlens.parsers.openai_chat import OpenAIChatParser

#: registered parsers, most specific first
PARSERS: list[type[Parser]] = [ClaudeCodeParser, CodexParser, OpenAIChatParser]


def detect_parser(raw: str, path: Path | None = None) -> type[Parser]:
    """Return the parser class with the highest sniff confidence."""
    scored = [(p.sniff(raw, path), p) for p in PARSERS]
    scored.sort(key=lambda t: t[0], reverse=True)
    best_score, best = scored[0]
    if best_score <= 0.0:
        raise ParseError("could not detect transcript format")
    return best


def parse_text(raw: str, path: Path | None = None, fmt: str | None = None) -> Session:
    """Parse raw transcript text, auto-detecting the format unless ``fmt`` is
    given."""
    if fmt and fmt != "auto":
        parser_cls = _by_name(fmt)
    else:
        parser_cls = detect_parser(raw, path)
    return parser_cls().parse(raw, path)


def parse_file(path: str | Path, fmt: str | None = None) -> Session:
    """Parse a transcript file from disk."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    return parse_text(raw, p, fmt)


def _by_name(name: str) -> type[Parser]:
    for p in PARSERS:
        if p.format_name == name:
            return p
    raise ParseError(f"unknown format {name!r}; known: {[p.format_name for p in PARSERS]}")


def available_formats() -> list[str]:
    return [p.format_name for p in PARSERS]


__all__ = [
    "Parser",
    "ParseError",
    "ClaudeCodeParser",
    "CodexParser",
    "OpenAIChatParser",
    "PARSERS",
    "detect_parser",
    "parse_text",
    "parse_file",
    "available_formats",
]
