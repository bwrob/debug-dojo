"""Tests for the `_cli` module."""

from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from debug_dojo._cli import cli, get_version, main

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from debug_dojo._cli import CliRunner

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
BOX_TRANS = str.maketrans("┌┐└┘", "╭╮╰╯")
SYNTAX_ERROR_EXIT_CODE = 2


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
    assert result.exit_code == 0


def test_help_flags(runner: CliRunner) -> None:
    """Test both -h and --help flags."""
    for flag in ("-h", "--help"):
        result = runner.invoke(cli, [flag])
        assert result.exit_code == 0
        assert "Usage:" in result.output


def test_version_flags(runner: CliRunner) -> None:
    """Test both -v and --version flags."""
    for flag in ("-v", "--version"):
        result = runner.invoke(cli, [flag])
        assert result.exit_code == 0
        assert "dojo " in result.output


def test_get_version_fallback() -> None:
    """Test get_version returns fallback on PackageNotFoundError."""
    with patch("debug_dojo._cli.version", side_effect=PackageNotFoundError):
        assert get_version() == "0.9.0"


def test_non_existent_file(runner: CliRunner) -> None:
    """Test that running with a non-existent file exits with an error."""
    result = runner.invoke(cli, ["non_existent_file.py"])
    assert result.exit_code == 1


def test_invalid_module(runner: CliRunner) -> None:
    """Test that running with an invalid module exits with an error."""
    result = runner.invoke(cli, ["non_existent_module_xyz"])
    assert result.exit_code == 1


def test_options_only_no_target(runner: CliRunner) -> None:
    """Test that running with options but no target does not execute."""
    result = runner.invoke(cli, ["-b", "1"])
    assert result.exit_code == 0


def test_break_with_equal_syntax(runner: CliRunner) -> None:
    """Test -b=loc and --break=loc syntax."""
    result = runner.invoke(cli, ["-b=10"])
    assert result.exit_code == 0
    result2 = runner.invoke(cli, ["--break=main"])
    assert result2.exit_code == 0


def test_break_missing_argument(runner: CliRunner) -> None:
    """Test that -b with missing argument outputs error and returns exit code 2."""
    result = runner.invoke(cli, ["-b"])
    assert result.exit_code == SYNTAX_ERROR_EXIT_CODE
    assert "requires an argument" in result.output

    result2 = runner.invoke(cli, ["-b="])
    assert result2.exit_code == SYNTAX_ERROR_EXIT_CODE
    assert "requires an argument" in result2.output


def test_unknown_option(runner: CliRunner) -> None:
    """Test that an unknown option returns exit code 2."""
    result = runner.invoke(cli, ["--unknown-flag"])
    assert result.exit_code == SYNTAX_ERROR_EXIT_CODE
    assert "Unknown option '--unknown-flag'" in result.output


def test_delimiter_double_dash(runner: CliRunner, test_target_inspect: str) -> None:
    """Test -- stops option parsing and forwards target and args."""
    result = runner.invoke(cli, ["--", test_target_inspect, "--custom-arg"])
    assert result.exit_code == 0

    # Test delimiter alone without target
    result_empty = runner.invoke(cli, ["--"])
    assert result_empty.exit_code == 0


def test_main_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() invokes cli() and calls sys.exit()."""
    monkeypatch.setattr("sys.argv", ["dojo", "--version"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


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
