"""High-level orchestration used by the CLI and reporters.

`analyze_*` functions parse a transcript, build the profile, waste report, and
recommendations, and bundle them into a single :class:`Analysis` object.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ctxlens.analysis.profile import Profile, build_profile
from ctxlens.analysis.recommend import Recommendation, recommend
from ctxlens.analysis.waste import WasteReport, build_waste_report
from ctxlens.models import Session
from ctxlens.parsers import parse_file, parse_text
from ctxlens.tokenizers import accuracy_note, count_accuracy, get_tokenizer


@dataclass
class Analysis:
    session: Session
    profile: Profile
    waste: WasteReport
    recommendations: list[Recommendation]
    source: str | None = None
    #: "exact" only when the tokenizer encoding matches the session's model family
    token_accuracy: str = "approximate"
    #: human-readable caveat when counts are not exact; None when exact
    accuracy_note: str | None = None

    @property
    def total_tokens(self) -> int:
        return self.profile.total_tokens

    @property
    def waste_ratio(self) -> float:
        return self.waste.waste_ratio


def analyze_session(
    session: Session,
    *,
    tokenizer: str = "auto",
    top_n: int = 10,
    tool_result_cap: int = 400,
    tool_def_budget: int = 800,
    source: str | None = None,
) -> Analysis:
    tok = get_tokenizer(tokenizer)
    profile = build_profile(session, tok, top_n=top_n)
    waste = build_waste_report(
        session, tool_result_cap=tool_result_cap, tool_def_budget=tool_def_budget
    )
    recs = recommend(profile, waste)
    accuracy = count_accuracy(tok, session.source_format)
    note = accuracy_note(tok, session.source_format)
    return Analysis(
        session=session,
        profile=profile,
        waste=waste,
        recommendations=recs,
        source=source,
        token_accuracy=accuracy,
        accuracy_note=note,
    )


def analyze_file(path: str | Path, *, fmt: str | None = None, **kwargs) -> Analysis:
    session = parse_file(path, fmt)
    return analyze_session(session, source=str(path), **kwargs)


def analyze_text(raw: str, *, fmt: str | None = None, source: str | None = None, **kwargs) -> Analysis:
    session = parse_text(raw, None, fmt)
    return analyze_session(session, source=source, **kwargs)
