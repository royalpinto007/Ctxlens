"""Machine-readable JSON reporter."""

from __future__ import annotations

import json

from ctxlens.engine import Analysis


def to_dict(analysis: Analysis) -> dict:
    p = analysis.profile
    w = analysis.waste
    total = p.total_tokens
    return {
        "source": analysis.source,
        "format": analysis.session.source_format,
        "tokenizer": p.tokenizer_name,
        "total_tokens": total,
        "high_water_mark": p.high_water_mark,
        "turns": len(p.turn_stats),
        "segments": [
            {
                "segment": s.segment.value,
                "tokens": s.tokens,
                "count": s.count,
                "pct": round(s.pct_of(total), 2),
            }
            for s in p.segment_stats
        ],
        "growth": [
            {
                "turn": t.index,
                "tokens": t.tokens,
                "cumulative": t.cumulative,
                "by_segment": {seg.value: tok for seg, tok in t.by_segment.items()},
            }
            for t in p.turn_stats
        ],
        "top_consumers": [
            {
                "label": c.label,
                "segment": c.segment.value,
                "tokens": c.tokens,
                "turn": c.turn,
                "ref": c.ref,
            }
            for c in p.top_consumers
        ],
        "waste": {
            "total_waste": w.total_waste,
            "waste_ratio": round(w.waste_ratio, 4),
            "duplicate_tokens": w.duplicate_tokens,
            "tool_result_bloat_tokens": w.tool_result_bloat_tokens,
            "stale_tool_tokens": w.stale_tool_tokens,
            "tool_def_overage_tokens": w.tool_def_overage_tokens,
            "items": [
                {"kind": i.kind, "detail": i.detail, "tokens": i.tokens} for i in w.items
            ],
        },
        "recommendations": [
            {
                "severity": r.severity,
                "title": r.title,
                "detail": r.detail,
                "est_savings": r.est_savings,
            }
            for r in analysis.recommendations
        ],
    }


def to_json(analysis: Analysis, *, indent: int | None = 2) -> str:
    return json.dumps(to_dict(analysis), indent=indent, ensure_ascii=False)
