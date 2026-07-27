from __future__ import annotations

import json

from ctxlens.engine import analyze_file
from ctxlens.reporters import diff_to_dict, render_html, to_dict, to_json
from ctxlens.reporters.sparkline import hbar, sparkline


def test_sparkline_length_matches_input():
    assert len(sparkline([1, 2, 3, 4, 5])) == 5


def test_sparkline_empty():
    assert sparkline([]) == ""


def test_sparkline_flat():
    assert len(set(sparkline([3, 3, 3]))) == 1


def test_hbar_bounds():
    assert len(hbar(5, 10, width=20)) == 20
    assert hbar(0, 0, width=8) == "·" * 8


def test_json_report_roundtrips(claude_jsonl):
    a = analyze_file(claude_jsonl, tokenizer="heuristic")
    d = json.loads(to_json(a))
    assert d["total_tokens"] == a.total_tokens
    assert d["format"] == "claude-code-jsonl"
    assert d["segments"]
    assert "waste" in d and "recommendations" in d


def test_to_dict_segment_pct_sum(codex_session):
    a = analyze_file(codex_session, tokenizer="heuristic")
    d = to_dict(a)
    total_pct = sum(s["pct"] for s in d["segments"])
    assert 99.0 <= total_pct <= 101.0


def test_html_is_self_contained(claude_jsonl):
    a = analyze_file(claude_jsonl, tokenizer="heuristic")
    html = render_html(a)
    assert html.startswith("<!doctype html>")
    assert "<svg" in html
    # no external resources
    assert "http://" not in html and "https://" not in html
    assert "cdn" not in html.lower()


def test_html_escapes_content(openai_chat):
    a = analyze_file(openai_chat, tokenizer="heuristic")
    html = render_html(a)
    assert "<script>" not in html


def test_diff_dict_structure(openai_array, openai_chat):
    a = analyze_file(openai_array, tokenizer="heuristic")
    b = analyze_file(openai_chat, tokenizer="heuristic")
    d = diff_to_dict(a, b)
    assert d["delta_tokens"] == b.total_tokens - a.total_tokens
    assert d["segments"]
