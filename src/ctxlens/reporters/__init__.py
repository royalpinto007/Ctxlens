"""Reporters: terminal, JSON, HTML, and diff."""

from ctxlens.reporters.diff import diff_to_dict, render_diff
from ctxlens.reporters.html import render_html
from ctxlens.reporters.json_report import to_dict, to_json
from ctxlens.reporters.terminal import render as render_terminal

__all__ = [
    "render_terminal",
    "to_dict",
    "to_json",
    "render_html",
    "render_diff",
    "diff_to_dict",
]
