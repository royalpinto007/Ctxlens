"""Self-contained HTML reporter.

Produces a single HTML string with an inline SVG growth chart and CSS. No
external CDN, fonts, or scripts are referenced, so the report opens offline and
is safe to attach to a CI artifact.
"""

from __future__ import annotations

import html

from ctxlens.engine import Analysis

_SEG_COLORS = {
    "system": "#8b5cf6",
    "tool_definitions": "#6366f1",
    "user": "#22c55e",
    "assistant": "#0ea5e9",
    "thinking": "#f59e0b",
    "tool_call": "#ec4899",
    "tool_result": "#ef4444",
}
_SEVERITY_COLOR = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}


def _esc(s: str) -> str:
    return html.escape(str(s))


def _growth_svg(analysis: Analysis, width: int = 720, height: int = 220) -> str:
    turns = analysis.profile.turn_stats
    if not turns:
        return "<p>No turns.</p>"
    pad = 36
    maxc = max(t.cumulative for t in turns) or 1
    n = len(turns)
    inner_w = width - 2 * pad
    inner_h = height - 2 * pad

    def x(i: int) -> float:
        return pad + (inner_w * i / (n - 1) if n > 1 else inner_w / 2)

    def y(v: float) -> float:
        return pad + inner_h - (v / maxc) * inner_h

    pts = [(x(i), y(t.cumulative)) for i, t in enumerate(turns)]
    line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    area = f"{pad},{pad + inner_h} " + line + f" {pad + inner_w},{pad + inner_h}"

    dots = "".join(
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="#0ea5e9">'
        f"<title>turn {turns[i].index}: {turns[i].cumulative:,} tok cumulative "
        f"(+{turns[i].tokens:,})</title></circle>"
        for i, (px, py) in enumerate(pts)
    )
    gridlines = ""
    for frac in (0.0, 0.5, 1.0):
        gy = pad + inner_h - frac * inner_h
        val = int(maxc * frac)
        gridlines += (
            f'<line x1="{pad}" y1="{gy:.1f}" x2="{pad + inner_w}" y2="{gy:.1f}" '
            f'stroke="#e5e7eb" stroke-dasharray="3 3"/>'
            f'<text x="{pad - 6}" y="{gy + 3:.1f}" text-anchor="end" '
            f'font-size="10" fill="#9ca3af">{val:,}</text>'
        )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Cumulative context growth">'
        f"{gridlines}"
        f'<polygon points="{area}" fill="#0ea5e9" fill-opacity="0.12"/>'
        f'<polyline points="{line}" fill="none" stroke="#0ea5e9" stroke-width="2"/>'
        f"{dots}</svg>"
    )


def _segment_bars(analysis: Analysis) -> str:
    p = analysis.profile
    total = p.total_tokens or 1
    rows = []
    for s in p.segment_stats:
        pct = s.pct_of(total)
        color = _SEG_COLORS.get(s.segment.value, "#64748b")
        rows.append(
            f'<div class="bar-row"><span class="bar-label">{_esc(s.segment.label)}</span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{pct:.1f}%;'
            f'background:{color}"></span></span>'
            f'<span class="bar-val">{s.tokens:,} ({pct:.1f}%)</span></div>'
        )
    return "".join(rows)


def _waste_rows(analysis: Analysis) -> str:
    w = analysis.waste
    rows = [
        ("Duplicate tokens", w.duplicate_tokens),
        ("Tool-result bloat", w.tool_result_bloat_tokens),
        ("Stale tool outputs", w.stale_tool_tokens),
        ("Oversized tool defs", w.tool_def_overage_tokens),
    ]
    body = "".join(f"<tr><td>{_esc(k)}</td><td>{v:,}</td></tr>" for k, v in rows)
    body += (
        f'<tr class="total"><td>Total waste</td>'
        f'<td>{w.total_waste:,} ({w.waste_ratio * 100:.1f}%)</td></tr>'
    )
    return body


def _consumer_rows(analysis: Analysis) -> str:
    return "".join(
        f"<tr><td>{c.turn}</td><td>{c.tokens:,}</td><td>{_esc(c.segment.label)}</td>"
        f"<td>{_esc(c.label)}</td></tr>"
        for c in analysis.profile.top_consumers[:10]
    )


def _rec_items(analysis: Analysis) -> str:
    out = []
    for r in analysis.recommendations:
        color = _SEVERITY_COLOR.get(r.severity, "#64748b")
        save = f' <span class="save">~{r.est_savings:,} tok</span>' if r.est_savings else ""
        out.append(
            f'<li><span class="sev" style="background:{color}">{_esc(r.severity)}</span>'
            f"<strong>{_esc(r.title)}</strong>{save}<br>"
            f'<span class="rec-detail">{_esc(r.detail)}</span></li>'
        )
    return "".join(out)


def render_html(analysis: Analysis) -> str:
    p = analysis.profile
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ctxlens report</title>
<style>
:root {{ color-scheme: light dark; }}
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  margin: 0; background: #f8fafc; color: #0f172a; }}
.wrap {{ max-width: 860px; margin: 0 auto; padding: 24px; }}
h1 {{ font-size: 22px; margin: 0 0 4px; }}
h2 {{ font-size: 15px; text-transform: uppercase; letter-spacing: .05em;
  color: #64748b; margin: 28px 0 10px; }}
.meta {{ color: #64748b; font-size: 13px; }}
.cards {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 14px; }}
.card {{ flex: 1 1 130px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 10px; padding: 12px 14px; }}
.card .n {{ font-size: 22px; font-weight: 700; }}
.card .k {{ font-size: 12px; color: #64748b; }}
.panel {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; }}
.bar-row {{ display: flex; align-items: center; gap: 10px; margin: 6px 0; font-size: 13px; }}
.bar-label {{ width: 130px; color: #475569; }}
.bar-track {{ flex: 1; background: #eef2f7; border-radius: 5px; height: 14px; overflow: hidden; }}
.bar-fill {{ display: block; height: 100%; }}
.bar-val {{ width: 150px; text-align: right; color: #334155; font-variant-numeric: tabular-nums; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid #eef2f7; }}
th {{ color: #64748b; font-weight: 600; }}
tr.total td {{ font-weight: 700; border-top: 2px solid #e2e8f0; }}
ul.recs {{ list-style: none; padding: 0; margin: 0; }}
ul.recs li {{ padding: 10px 0; border-bottom: 1px solid #eef2f7; font-size: 14px; }}
.sev {{ display: inline-block; color: #fff; font-size: 11px; text-transform: uppercase;
  padding: 1px 7px; border-radius: 999px; margin-right: 8px; }}
.rec-detail {{ color: #475569; font-size: 13px; }}
.save {{ color: #64748b; font-size: 12px; }}
@media (prefers-color-scheme: dark) {{
  body {{ background: #0b1120; color: #e2e8f0; }}
  .card, .panel {{ background: #111827; border-color: #1f2937; }}
  .bar-track {{ background: #1f2937; }}
  th, .meta, .bar-label, .rec-detail, .card .k, .save {{ color: #94a3b8; }}
  td {{ border-color: #1f2937; }}
}}
</style></head><body><div class="wrap">
<h1>ctxlens report</h1>
<div class="meta">{_esc(analysis.source or "&lt;stdin&gt;")} &middot;
  format {_esc(analysis.session.source_format)} &middot;
  tokenizer {_esc(p.tokenizer_name)}</div>
<div class="cards">
  <div class="card"><div class="n">{p.total_tokens:,}</div><div class="k">total tokens</div></div>
  <div class="card"><div class="n">{len(p.turn_stats)}</div><div class="k">turns</div></div>
  <div class="card"><div class="n">{p.high_water_mark:,}</div><div class="k">high-water mark</div></div>
  <div class="card"><div class="n">{analysis.waste.waste_ratio * 100:.1f}%</div><div class="k">waste ratio</div></div>
</div>
<h2>Context growth</h2>
<div class="panel">{_growth_svg(analysis)}</div>
<h2>Composition by segment</h2>
<div class="panel">{_segment_bars(analysis)}</div>
<h2>Biggest consumers</h2>
<div class="panel"><table><thead><tr><th>Turn</th><th>Tokens</th><th>Segment</th><th>What</th></tr></thead>
<tbody>{_consumer_rows(analysis)}</tbody></table></div>
<h2>Waste report</h2>
<div class="panel"><table><tbody>{_waste_rows(analysis)}</tbody></table></div>
<h2>Recommendations</h2>
<div class="panel"><ul class="recs">{_rec_items(analysis)}</ul></div>
</div></body></html>"""
