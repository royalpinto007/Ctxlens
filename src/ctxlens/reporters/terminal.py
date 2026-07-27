"""Rich terminal reporter."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ctxlens.engine import Analysis
from ctxlens.reporters.sparkline import hbar, sparkline

_SEVERITY_STYLE = {"high": "bold red", "medium": "yellow", "low": "green"}


def render(analysis: Analysis, console: Console | None = None) -> None:
    console = console or Console()
    p = analysis.profile
    w = analysis.waste

    console.print(_header(analysis))
    console.print(_segment_table(analysis))
    console.print(_growth_panel(analysis))
    if p.top_consumers:
        console.print(_consumers_table(analysis))
    console.print(_waste_panel(analysis))
    console.print(_recommendations(analysis))


def _header(a: Analysis) -> Panel:
    p = a.profile
    src = a.source or "<stdin>"
    ratio = a.waste_ratio * 100
    ratio_style = "red" if ratio >= 25 else "yellow" if ratio >= 10 else "green"
    body = Text.assemble(
        ("Source   ", "dim"), f"{src}\n",
        ("Format   ", "dim"), f"{a.session.source_format}   ",
        ("Tokenizer ", "dim"), f"{p.tokenizer_name}\n",
        ("Tokens   ", "dim"), f"{p.total_tokens:,}   ",
        ("Turns ", "dim"), f"{len(p.turn_stats)}   ",
        ("High-water ", "dim"), f"{p.high_water_mark:,}\n",
        ("Waste    ", "dim"),
        (f"{a.waste.total_waste:,} tokens ({ratio:.1f}%)", ratio_style),
    )
    return Panel(body, title="ctxlens", border_style="cyan", expand=False)


def _segment_table(a: Analysis) -> Table:
    p = a.profile
    total = p.total_tokens
    t = Table(title="Context composition by segment", title_justify="left", expand=False)
    t.add_column("Segment")
    t.add_column("Tokens", justify="right")
    t.add_column("%", justify="right")
    t.add_column("Msgs", justify="right")
    t.add_column("Share", justify="left")
    for s in p.segment_stats:
        pct = s.pct_of(total)
        t.add_row(
            s.segment.label,
            f"{s.tokens:,}",
            f"{pct:.1f}",
            str(s.count),
            Text(hbar(s.tokens, total), style="cyan"),
        )
    return t


def _growth_panel(a: Analysis) -> Panel:
    p = a.profile
    cumulative = [t.cumulative for t in p.turn_stats]
    per_turn = [t.tokens for t in p.turn_stats]
    lines = [
        Text.assemble(("cumulative  ", "dim"), (sparkline(cumulative), "green"),
                      (f"  peak {p.high_water_mark:,}", "dim")),
        Text.assemble(("per-turn    ", "dim"), (sparkline(per_turn), "magenta"),
                      (f"  max {max(per_turn) if per_turn else 0:,}", "dim")),
    ]
    return Panel(Group(*lines), title="Context growth", border_style="green",
                 title_align="left", expand=False)


def _consumers_table(a: Analysis) -> Table:
    t = Table(title="Biggest single consumers", title_justify="left", expand=False)
    t.add_column("Turn", justify="right")
    t.add_column("Tokens", justify="right")
    t.add_column("Segment")
    t.add_column("What")
    for c in a.profile.top_consumers[:8]:
        t.add_row(str(c.turn), f"{c.tokens:,}", c.segment.label, c.label)
    return t


def _waste_panel(a: Analysis) -> Panel:
    w = a.waste
    t = Table.grid(padding=(0, 2))
    t.add_column(justify="left")
    t.add_column(justify="right")
    t.add_row("Duplicate tokens", f"{w.duplicate_tokens:,}")
    t.add_row("Tool-result bloat", f"{w.tool_result_bloat_tokens:,}")
    t.add_row("Stale tool outputs", f"{w.stale_tool_tokens:,}")
    t.add_row("Oversized tool defs", f"{w.tool_def_overage_tokens:,}")
    t.add_row(Text("Total waste", style="bold"),
              Text(f"{w.total_waste:,} ({w.waste_ratio * 100:.1f}%)", style="bold red"))
    return Panel(t, title="Waste report", border_style="red", title_align="left", expand=False)


def _recommendations(a: Analysis) -> Panel:
    lines = []
    for r in a.recommendations:
        style = _SEVERITY_STYLE.get(r.severity, "white")
        head = Text.assemble((f"[{r.severity.upper()}] ", style), (r.title, "bold"))
        if r.est_savings:
            head.append(f"  (~{r.est_savings:,} tok)", style="dim")
        lines.append(head)
        lines.append(Text("    " + r.detail, style="dim"))
    return Panel(Group(*lines), title="Recommendations", border_style="yellow",
                 title_align="left", expand=False)
