from __future__ import annotations

import pytest

from ctxlens.tokenizers import (
    HeuristicTokenizer,
    available_tokenizers,
    get_tokenizer,
)


def test_heuristic_deterministic():
    tok = HeuristicTokenizer()
    text = "The quick brown fox jumps over the lazy dog."
    assert tok.count(text) == tok.count(text)


def test_heuristic_empty_is_zero():
    assert HeuristicTokenizer().count("") == 0


def test_heuristic_monotonic_with_length():
    tok = HeuristicTokenizer()
    short = tok.count("hello")
    long = tok.count("hello " * 50)
    assert long > short


def test_heuristic_long_words_cost_more_than_one():
    tok = HeuristicTokenizer()
    # a 20-char run should be several tokens, not one
    assert tok.count("supercalifragilistic") > 1


def test_count_all():
    tok = HeuristicTokenizer()
    assert tok.count_all(["a", "bb"]) == [tok.count("a"), tok.count("bb")]


def test_registry_auto_returns_something():
    tok = get_tokenizer("auto")
    assert tok.count("hello world") > 0
    assert tok.name  # has an identifier


def test_registry_heuristic_explicit():
    assert get_tokenizer("heuristic").name == "heuristic"


def test_registry_unknown_raises():
    with pytest.raises(ValueError):
        get_tokenizer("nope")


def test_available_tokenizers_includes_heuristic():
    assert "heuristic" in available_tokenizers()


def test_tiktoken_requested_but_missing_raises_or_works():
    # if tiktoken is not installed this raises ImportError; if it is, it works
    try:
        tok = get_tokenizer("tiktoken")
    except ImportError:
        return
    assert tok.count("hello") > 0


def test_count_accuracy_claude_tiktoken_is_approximate():
    from ctxlens.tokenizers import accuracy_note, count_accuracy

    try:
        tok = get_tokenizer("tiktoken")
    except ImportError:
        pytest.skip("tiktoken not installed")
    assert tok.name == "tiktoken:cl100k_base"
    assert count_accuracy(tok, "claude-code-jsonl") == "approximate"
    note = accuracy_note(tok, "claude-code-jsonl")
    assert note is not None
    assert "approximate" in note.lower()
    assert "OpenAI" in note or "cl100k" in note


def test_count_accuracy_openai_tiktoken_is_exact():
    from ctxlens.tokenizers import accuracy_note, count_accuracy

    try:
        tok = get_tokenizer("tiktoken")
    except ImportError:
        pytest.skip("tiktoken not installed")
    assert count_accuracy(tok, "openai-chat") == "exact"
    assert count_accuracy(tok, "codex-session") == "exact"
    assert accuracy_note(tok, "openai-chat") is None


def test_heuristic_always_approximate():
    from ctxlens.tokenizers import count_accuracy

    tok = get_tokenizer("heuristic")
    assert count_accuracy(tok, "openai-chat") == "approximate"
    assert count_accuracy(tok, "claude-code-jsonl") == "approximate"
