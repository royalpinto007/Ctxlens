from __future__ import annotations

import json

from typer.testing import CliRunner

from ctxlens.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "ctxlens" in result.stdout


def test_formats_command():
    result = runner.invoke(app, ["formats"])
    assert result.exit_code == 0
    assert "claude-code-jsonl" in result.stdout


def test_analyze_terminal(claude_jsonl):
    result = runner.invoke(app, ["analyze", str(claude_jsonl)])
    assert result.exit_code == 0
    assert "ctxlens" in result.stdout


def test_analyze_json(claude_jsonl):
    result = runner.invoke(app, ["analyze", str(claude_jsonl), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["total_tokens"] > 0


def test_analyze_fail_over_threshold_exceeded(claude_jsonl):
    result = runner.invoke(
        app,
        ["analyze", str(claude_jsonl), "--tool-result-cap", "40", "--fail-over-ratio", "0.1"],
    )
    assert result.exit_code == 2


def test_analyze_fail_over_threshold_ok(claude_jsonl):
    result = runner.invoke(
        app, ["analyze", str(claude_jsonl), "--fail-over-ratio", "0.99"]
    )
    assert result.exit_code == 0


def test_report_html_to_file(tmp_path, codex_session):
    out = tmp_path / "r.html"
    result = runner.invoke(app, ["report", str(codex_session), "--html", "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert out.read_text().startswith("<!doctype html>")


def test_diff_json(openai_array, openai_chat):
    result = runner.invoke(
        app, ["diff", str(openai_array), str(openai_chat), "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "delta_tokens" in data


def test_analyze_missing_file():
    result = runner.invoke(app, ["analyze", "/no/such/file.jsonl"])
    assert result.exit_code == 1


def test_analyze_stdin(openai_array):
    raw = openai_array.read_text()
    result = runner.invoke(app, ["analyze", "-", "--json"], input=raw)
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["source"] == "<stdin>"
    assert data["total_tokens"] > 0
