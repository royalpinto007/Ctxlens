"""Compare two analyses (e.g. before/after a context optimization)."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from ctxlens.engine import Analysis
from ctxlens.models import Segment


@dataclass
class SegmentDelta:
    segment: Segment
    a_tokens: int
    b_tokens: int

    @property
    def delta(self) -> int:
        return self.b_tokens - self.a_tokens


def diff_segments(a: Analysis, b: Analysis) -> list[SegmentDelta]:
    amap = {s.segment: s.tokens for s in a.profile.segment_stats}
    bmap = {s.segment: s.tokens for s in b.profile.segment_stats}
    segments = sorted(set(amap) | set(bmap), key=lambda s: s.value)
    return [SegmentDelta(seg, amap.get(seg, 0), bmap.get(seg, 0)) for seg in segments]


def diff_to_dict(a: Analysis, b: Analysis) -> dict:
    return {
        "a": {"source": a.source, "total_tokens": a.total_tokens, "waste_ratio": round(a.waste_ratio, 4)},
        "b": {"source": b.source, "total_tokens": b.total_tokens, "waste_ratio": round(b.waste_ratio, 4)},
        "delta_tokens": b.total_tokens - a.total_tokens,
        "delta_waste_ratio": round(b.waste_ratio - a.waste_ratio, 4),
        "segments": [
            {"segment": d.segment.value, "a": d.a_tokens, "b": d.b_tokens, "delta": d.delta}
            for d in diff_segments(a, b)
        ],
    }


def _fmt_delta(n: int) -> str:
    return f"+{n:,}" if n > 0 else f"{n:,}"


def render_diff(a: Analysis, b: Analysis, console: Console | None = None) -> None:
    console = console or Console()
    t = Table(title="ctxlens diff", expand=False, title_justify="left")
    t.add_column("Metric")
    t.add_column(a.source or "A", justify="right")
    t.add_column(b.source or "B", justify="right")
    t.add_column("Delta", justify="right")

    dt = b.total_tokens - a.total_tokens
    t.add_row("Total tokens", f"{a.total_tokens:,}", f"{b.total_tokens:,}",
              _colored(_fmt_delta(dt), dt, lower_is_better=True))
    dw = b.waste_ratio - a.waste_ratio
    t.add_row("Waste ratio", f"{a.waste_ratio * 100:.1f}%", f"{b.waste_ratio * 100:.1f}%",
              _colored(f"{dw * 100:+.1f}%", dw, lower_is_better=True))
    t.add_row("Turns", str(len(a.profile.turn_stats)), str(len(b.profile.turn_stats)), "")

    for d in diff_segments(a, b):
        if d.a_tokens == 0 and d.b_tokens == 0:
            continue
        t.add_row(d.segment.label, f"{d.a_tokens:,}", f"{d.b_tokens:,}",
                  _colored(_fmt_delta(d.delta), d.delta, lower_is_better=True))
    console.print(t)


def _colored(text: str, value: float, *, lower_is_better: bool) -> str:
    if value == 0:
        return f"[dim]{text}[/dim]"
    good = value < 0 if lower_is_better else value > 0
    return f"[green]{text}[/green]" if good else f"[red]{text}[/red]"
