"""Tests for the `_cli` module."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from debug_dojo._cli import cli

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
BOX_TRANS = str.maketrans("┌┐└┘", "╭╮╰╯")


def normalize_cli_output(text: str) -> str:
    """Normalize ANSI escapes, box corners, and whitespace in CLI output.

    Args:
        text: Input string possibly containing ANSI escape sequences
            and platform differences.

    Returns:
        Clean normalized string with stripped ANSI, standard box corners,
        and collapsed consecutive blank lines.

    """
    clean_text = ANSI_ESCAPE.sub("", text).translate(BOX_TRANS)
    lines = [line.rstrip() for line in clean_text.splitlines()]
    normalized_lines: list[str] = []
    for line in lines:
        if not line and normalized_lines and not normalized_lines[-1]:
            continue
        normalized_lines.append(line)
    return "\n".join(normalized_lines).strip()


def test_no_args_prints_help(runner: CliRunner) -> None:
    """Test that running with no arguments prints help."""
    result = runner.invoke(cli, [])
    assert "Usage:" in result.output


def test_run_debug_help(runner: CliRunner) -> None:
    """Test the help message for the run command."""
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0
    assert "Usage: debug_dojo run" in result.output


def test_run_debug_non_existent_file(runner: CliRunner) -> None:
    """Test that running with a non-existent file exits with an error."""
    result = runner.invoke(cli, ["run", "non_existent_file.py"])
    assert result.exit_code == 1


def test_run_debug_invalid_module(runner: CliRunner) -> None:
    """Test that running with an invalid module exits with an error."""
    result = runner.invoke(cli, ["run", "-m", "non_existent_module"])
    assert result.exit_code == 1


def test_run_debug_module_and_exec_exclusive(runner: CliRunner) -> None:
    """Test that --module and --exec are mutually exclusive."""
    result = runner.invoke(cli, ["run", "-m", "-e", "target"])
    assert result.exit_code == 1


def test_run_debug_verbose(runner: CliRunner, test_target_inspect: str) -> None:
    """Test the --verbose flag."""
    result = runner.invoke(cli, ["run", "--verbose", test_target_inspect])
    assert result.exit_code == 0
    assert "Using debug-dojo configuration:" in result.output


def test_run_options_only_no_target(runner: CliRunner) -> None:
    """Test that running with options but no target does not execute."""
    result = runner.invoke(cli, ["run", "-v"])
    assert result.exit_code == 0
    assert "Using debug-dojo configuration:" in result.output


def test_normalize_cli_output_consecutive_blank_lines() -> None:
    """Test that normalize_cli_output collapses consecutive blank lines."""
    raw = "\x1b[32mhello\x1b[0m\n\n\nworld\n"
    assert normalize_cli_output(raw) == "hello\n\nworld"


def test_normalize_cli_output_box_corners() -> None:
    """Test that normalize_cli_output normalizes Windows box corners to rounded."""
    raw = "┌─ Options ─┐\n└───────────┘"
    assert normalize_cli_output(raw) == "╭─ Options ─╮\n╰───────────╯"


def test_cli_help_snapshot(runner: CliRunner, snapshot: SnapshotAssertion) -> None:
    """Test that CLI help output matches the syrupy snapshot."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert normalize_cli_output(result.output) == snapshot
