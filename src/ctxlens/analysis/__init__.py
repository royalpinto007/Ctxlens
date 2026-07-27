"""Analysis layer: profiling, duplication, and waste detection."""

from ctxlens.analysis.duplication import DuplicateGroup, find_duplicates
from ctxlens.analysis.profile import (
    Consumer,
    Profile,
    SegmentStat,
    TurnStat,
    build_profile,
)
from ctxlens.analysis.waste import WasteItem, WasteReport, build_waste_report

__all__ = [
    "Profile",
    "SegmentStat",
    "TurnStat",
    "Consumer",
    "build_profile",
    "DuplicateGroup",
    "find_duplicates",
    "WasteReport",
    "WasteItem",
    "build_waste_report",
]
