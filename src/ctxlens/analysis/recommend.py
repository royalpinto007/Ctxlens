"""Rule-based recommendations engine.

Turns a :class:`Profile` and :class:`WasteReport` into concrete, actionable
suggestions. Each rule is deliberately specific ("tool X's results account for
42% of tokens") so the output is directly usable, not generic advice.
"""

from __future__ import annotations

from dataclasses import dataclass

from ctxlens.analysis.profile import Profile
from ctxlens.analysis.waste import WasteReport
from ctxlens.models import Segment


@dataclass
class Recommendation:
    severity: str  # "high" | "medium" | "low"
    title: str
    detail: str
    est_savings: int = 0

    _ORDER = {"high": 0, "medium": 1, "low": 2}

    @property
    def sort_key(self) -> tuple[int, int]:
        return (self._ORDER.get(self.severity, 3), -self.est_savings)


def recommend(profile: Profile, waste: WasteReport) -> list[Recommendation]:
    recs: list[Recommendation] = []
    total = profile.total_tokens or 1
    seg = profile.segment_map()

    # 1. dominant tool results
    tr = seg.get(Segment.TOOL_RESULT)
    if tr and tr.pct_of(total) >= 30:
        recs.append(
            Recommendation(
                "high",
                "Tool results dominate the context",
                f"Tool results are {tr.tokens} tokens ({tr.pct_of(total):.0f}% of context). "
                "Truncate or summarize large tool outputs before they re-enter context.",
                est_savings=waste.tool_result_bloat_tokens,
            )
        )

    # 2. duplicated content / re-reads
    for g in waste.duplicate_groups[:3]:
        if g.wasted_tokens <= 0:
            continue
        what = f"'{g.key}'" if g.kind == "ref" else "identical content"
        recs.append(
            Recommendation(
                "high" if g.wasted_tokens > total * 0.1 else "medium",
                "Repeated content wastes tokens",
                f"{what} appears {g.occurrences} times (turns {g.turns}), "
                f"wasting ~{g.wasted_tokens} tokens. Cache it or reference the first copy.",
                est_savings=g.wasted_tokens,
            )
        )

    # 3. stale tool outputs
    if waste.stale_tool_tokens > 0:
        recs.append(
            Recommendation(
                "medium",
                "Stale tool outputs linger in context",
                f"~{waste.stale_tool_tokens} tokens of superseded tool output remain in context. "
                "Drop older results once a newer version for the same target arrives.",
                est_savings=waste.stale_tool_tokens,
            )
        )

    # 4. oversized tool definitions (paid every turn)
    td = seg.get(Segment.TOOL_DEFINITIONS)
    if td and waste.tool_def_overage_tokens > 0:
        recs.append(
            Recommendation(
                "medium",
                "Tool definitions are large",
                f"Tool schemas are {td.tokens} tokens and are re-sent every turn. "
                "Trim descriptions or expose fewer tools per turn.",
                est_savings=waste.tool_def_overage_tokens,
            )
        )

    # 5. system prompt weight
    sysseg = seg.get(Segment.SYSTEM)
    if sysseg and sysseg.pct_of(total) >= 25 and len(profile.turn_stats) > 1:
        recs.append(
            Recommendation(
                "low",
                "System prompt is a large fixed cost",
                f"The system prompt is {sysseg.tokens} tokens ({sysseg.pct_of(total):.0f}%). "
                "It is paid on every turn; tighten it if possible.",
            )
        )

    # 6. single biggest consumer callout
    if profile.top_consumers:
        top = profile.top_consumers[0]
        if top.tokens >= total * 0.2:
            recs.append(
                Recommendation(
                    "medium",
                    "One message is a large slice of context",
                    f"'{top.label}' (turn {top.turn}) alone is {top.tokens} tokens "
                    f"({top.tokens / total * 100:.0f}% of context).",
                )
            )

    # 7. healthy session
    if not recs:
        recs.append(
            Recommendation(
                "low",
                "No major context waste detected",
                f"Waste ratio is {waste.waste_ratio * 100:.1f}%. Context usage looks efficient.",
            )
        )

    recs.sort(key=lambda r: r.sort_key)
    return recs
