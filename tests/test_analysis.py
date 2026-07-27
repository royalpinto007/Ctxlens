from __future__ import annotations

from ctxlens.analysis import (
    build_profile,
    build_waste_report,
    find_duplicates,
    recommend,
)
from ctxlens.models import Message, Segment, Session
from ctxlens.parsers import parse_file
from ctxlens.tokenizers import HeuristicTokenizer


def _profile(path):
    return build_profile(parse_file(path), HeuristicTokenizer())


def test_profile_totals_match_segment_sum(claude_jsonl):
    p = _profile(claude_jsonl)
    assert p.total_tokens == sum(s.tokens for s in p.segment_stats)
    assert p.total_tokens > 0


def test_profile_cumulative_is_increasing(claude_jsonl):
    p = _profile(claude_jsonl)
    cums = [t.cumulative for t in p.turn_stats]
    assert cums == sorted(cums)
    assert p.high_water_mark == cums[-1]


def test_segment_stats_sorted_desc(codex_session):
    p = _profile(codex_session)
    toks = [s.tokens for s in p.segment_stats]
    assert toks == sorted(toks, reverse=True)


def test_top_consumers_sorted_desc(claude_jsonl):
    p = _profile(claude_jsonl)
    toks = [c.tokens for c in p.top_consumers]
    assert toks == sorted(toks, reverse=True)


def test_pct_of_bounds(claude_jsonl):
    p = _profile(claude_jsonl)
    for s in p.segment_stats:
        assert 0 <= s.pct_of(p.total_tokens) <= 100


def _dup_session():
    body = "the same large file content that gets read repeatedly " * 5
    msgs = [
        Message(Segment.TOOL_RESULT, body, turn=1, ref="A"),
        Message(Segment.TOOL_RESULT, body, turn=3, ref="B"),
        Message(Segment.ASSISTANT, "unique text here", turn=1),
    ]
    s = Session(source_format="test", messages=msgs)
    for m in s.messages:
        m.tokens = HeuristicTokenizer().count(m.text)
    return s


def test_find_duplicates_detects_identical_bodies():
    dups = find_duplicates(_dup_session())
    assert dups
    top = dups[0]
    assert top.occurrences == 2
    assert top.wasted_tokens == top.tokens_each  # one wasted copy


def test_find_duplicates_ignores_singletons():
    msgs = [Message(Segment.TOOL_RESULT, "abc " * 30, turn=1, ref="A")]
    s = Session("test", msgs)
    for m in s.messages:
        m.tokens = HeuristicTokenizer().count(m.text)
    assert find_duplicates(s) == []


def test_waste_report_ratio_and_totals():
    w = build_waste_report(_dup_session(), tool_result_cap=10)
    assert w.duplicate_tokens > 0
    assert w.total_waste >= w.duplicate_tokens
    assert 0 <= w.waste_ratio <= 1


def test_stale_not_double_counted_with_duplicate():
    # identical repeat should be a duplicate, contributing zero stale tokens
    w = build_waste_report(_dup_session(), tool_result_cap=100000)
    assert w.stale_tool_tokens == 0
    assert w.duplicate_tokens > 0


def test_stale_detected_when_content_changes():
    a = Message(Segment.TOOL_RESULT, "old content " * 20, turn=1, ref="R")
    b = Message(Segment.TOOL_RESULT, "new different content " * 20, turn=5, ref="R")
    s = Session("test", [a, b])
    for m in s.messages:
        m.tokens = HeuristicTokenizer().count(m.text)
    w = build_waste_report(s, tool_result_cap=100000)
    assert w.stale_tool_tokens > 0
    assert w.duplicate_tokens == 0


def test_tool_def_overage_flagged(openai_chat):
    s = parse_file(openai_chat)
    build_profile(s, HeuristicTokenizer())  # counts tokens onto messages
    w = build_waste_report(s, tool_def_budget=10)
    assert w.tool_def_overage_tokens > 0


def test_recommendations_nonempty_and_sorted(claude_jsonl):
    s = parse_file(claude_jsonl)
    p = build_profile(s, HeuristicTokenizer())
    w = build_waste_report(s, tool_result_cap=40)
    recs = recommend(p, w)
    assert recs
    order = {"high": 0, "medium": 1, "low": 2}
    keys = [order[r.severity] for r in recs]
    assert keys == sorted(keys)


def test_recommendations_healthy_session_has_low_note():
    msgs = [
        Message(Segment.USER, "hi there friend", turn=1),
        Message(Segment.ASSISTANT, "hello back to you", turn=1),
    ]
    s = Session("test", msgs)
    p = build_profile(s, HeuristicTokenizer())
    w = build_waste_report(s)
    recs = recommend(p, w)
    assert any(r.severity == "low" for r in recs)
