"""Waste report: how many context tokens are avoidable.

Combines three sources of avoidable tokens:

* **duplicate tokens** - repeated refs / bodies (see :mod:`duplication`).
* **tool-result bloat** - tokens in oversized tool results above a per-result
  cap; long raw outputs that could be truncated or summarized.
* **stale tool outputs** - large tool results that sit in early turns and are
  later superseded by a *newer* result for the same ref, so the old copy is
  dead weight.
* **oversized tool definitions** - tool schema tokens beyond a reasonable
  budget, which are paid on every single turn.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ctxlens.models import Segment, Session
from ctxlens.analysis.duplication import DuplicateGroup, find_duplicates


@dataclass
class WasteItem:
    kind: str
    detail: str
    tokens: int


@dataclass
class WasteReport:
    total_tokens: int
    duplicate_tokens: int
    tool_result_bloat_tokens: int
    stale_tool_tokens: int
    tool_def_overage_tokens: int
    items: list[WasteItem] = field(default_factory=list)
    duplicate_groups: list[DuplicateGroup] = field(default_factory=list)

    @property
    def total_waste(self) -> int:
        return (
            self.duplicate_tokens
            + self.tool_result_bloat_tokens
            + self.stale_tool_tokens
            + self.tool_def_overage_tokens
        )

    @property
    def waste_ratio(self) -> float:
        return (self.total_waste / self.total_tokens) if self.total_tokens else 0.0


def build_waste_report(
    session: Session,
    *,
    tool_result_cap: int = 400,
    tool_def_budget: int = 800,
    dup_min_tokens: int = 20,
) -> WasteReport:
    total = session.total_tokens
    items: list[WasteItem] = []

    # 1. duplicates
    dup_groups = find_duplicates(session, min_tokens=dup_min_tokens)
    dup_tokens = sum(g.wasted_tokens for g in dup_groups)
    for g in dup_groups:
        kind = "duplicate file/tool" if g.kind == "ref" else "duplicate content"
        items.append(
            WasteItem(
                kind=kind,
                detail=f"{g.key} repeated {g.occurrences}x ({g.tokens_each} tok each)",
                tokens=g.wasted_tokens,
            )
        )

    # 2. tool-result bloat (tokens above the per-result cap)
    bloat = 0
    for m in session.messages:
        if m.segment == Segment.TOOL_RESULT and m.tokens > tool_result_cap:
            over = m.tokens - tool_result_cap
            bloat += over
            items.append(
                WasteItem(
                    kind="tool-result bloat",
                    detail=f"{m.ref or m.tool_name or 'tool result'} at turn {m.turn} "
                    f"is {m.tokens} tok (> {tool_result_cap} cap)",
                    tokens=over,
                )
            )

    # 3. stale tool outputs: an older result superseded by a newer one for the
    #    same ref still occupies context
    stale = _stale_tokens(session, items)

    # 4. oversized tool definitions (paid every turn)
    tool_def_overage = 0
    for m in session.messages:
        if m.segment == Segment.TOOL_DEFINITIONS and m.tokens > tool_def_budget:
            over = m.tokens - tool_def_budget
            tool_def_overage += over
            items.append(
                WasteItem(
                    kind="oversized tool definitions",
                    detail=f"tool schema is {m.tokens} tok (> {tool_def_budget} budget)",
                    tokens=over,
                )
            )

    items.sort(key=lambda i: i.tokens, reverse=True)
    return WasteReport(
        total_tokens=total,
        duplicate_tokens=dup_tokens,
        tool_result_bloat_tokens=bloat,
        stale_tool_tokens=stale,
        tool_def_overage_tokens=tool_def_overage,
        items=items,
        duplicate_groups=dup_groups,
    )


def _stale_tokens(session: Session, items: list[WasteItem]) -> int:
    """Tokens in tool results that were later replaced by a newer result for
    the same ref (only the older, superseded copies count)."""
    by_ref: dict[str, list] = {}
    for m in session.messages:
        if m.segment == Segment.TOOL_RESULT and m.ref:
            by_ref.setdefault(m.ref, []).append(m)
    stale = 0
    for ref, msgs in by_ref.items():
        if len(msgs) < 2:
            continue
        ordered = sorted(msgs, key=lambda m: m.turn)
        latest_body = ordered[-1].text.strip()
        # older occurrences that differ from the latest are genuinely stale;
        # byte-identical repeats are already counted as duplicates
        superseded = [m for m in ordered[:-1] if m.text.strip() != latest_body]
        for m in superseded:
            stale += m.tokens
            items.append(
                WasteItem(
                    kind="stale tool output",
                    detail=f"{ref} at turn {m.turn} superseded by a later result",
                    tokens=m.tokens,
                )
            )
    return stale
