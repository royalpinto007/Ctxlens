from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def claude_jsonl() -> Path:
    return FIXTURES / "claude_code_session.jsonl"


@pytest.fixture
def openai_chat() -> Path:
    return FIXTURES / "openai_chat.json"


@pytest.fixture
def openai_array() -> Path:
    return FIXTURES / "openai_chat_array.json"


@pytest.fixture
def codex_session() -> Path:
    return FIXTURES / "codex_session.json"
