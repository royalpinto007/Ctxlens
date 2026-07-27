"""Shared helpers for turning provider content blocks into messages."""

from __future__ import annotations

import json
from typing import Any

from ctxlens.models import Message, Segment


def stringify(value: Any) -> str:
    """Coerce arbitrary JSON content into a stable text representation."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def tool_ref(tool_name: str | None, tool_input: Any) -> str | None:
    """Build a stable reference for a tool call so repeated identical calls
    (e.g. re-reading the same file) can be detected as duplication."""
    if not tool_name:
        return None
    key = _salient_input(tool_input)
    return f"{tool_name}:{key}" if key else tool_name


# input keys that identify *what* a tool acted on (used for duplicate detection)
_REF_KEYS = ("file_path", "path", "filename", "file", "url", "query", "command", "pattern")


def _salient_input(tool_input: Any) -> str:
    if isinstance(tool_input, dict):
        for k in _REF_KEYS:
            if k in tool_input and isinstance(tool_input[k], (str, int)):
                return f"{k}={tool_input[k]}"
    return ""


def block_to_message(block: dict, *, role: str, turn: int) -> Message | None:
    """Convert a single Anthropic-style content block into a Message."""
    btype = block.get("type")
    if btype == "text":
        seg = Segment.ASSISTANT if role == "assistant" else Segment.USER
        return Message(segment=seg, text=block.get("text", ""), turn=turn, role=role)
    if btype == "thinking":
        text = block.get("thinking") or block.get("text", "")
        return Message(segment=Segment.THINKING, text=text, turn=turn, role=role)
    if btype == "tool_use":
        name = block.get("name")
        payload = block.get("input", {})
        return Message(
            segment=Segment.TOOL_CALL,
            text=stringify(payload),
            turn=turn,
            role=role,
            tool_name=name,
            ref=tool_ref(name, payload),
            meta={"tool_use_id": block.get("id")},
        )
    if btype == "tool_result":
        content = block.get("content")
        return Message(
            segment=Segment.TOOL_RESULT,
            text=stringify(content),
            turn=turn,
            role=role,
            ref=block.get("tool_use_id"),
            meta={"tool_use_id": block.get("tool_use_id")},
        )
    return None
