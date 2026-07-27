"""Unicode sparkline / bar helpers for terminal charts (no dependencies)."""

from __future__ import annotations

_BLOCKS = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float]) -> str:
    """Render a compact single-line sparkline from a list of values."""
    if not values:
        return ""
    lo = min(values)
    hi = max(values)
    span = hi - lo
    if span == 0:
        return _BLOCKS[3] * len(values)
    out = []
    last = len(_BLOCKS) - 1
    for v in values:
        idx = int((v - lo) / span * last + 0.5)
        out.append(_BLOCKS[idx])
    return "".join(out)


def hbar(value: float, total: float, width: int = 24, fill: str = "█", empty: str = "·") -> str:
    """Horizontal proportional bar."""
    if total <= 0:
        return empty * width
    filled = int(round(value / total * width))
    filled = max(0, min(width, filled))
    return fill * filled + empty * (width - filled)
