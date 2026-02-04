"""Tests for the `_cli` module."""

from typer.testing import CliRunner

from debug_dojo._cli import cli


def test_run_debug_help(runner: CliRunner) -> None:
    """Test the help message for the run-debug command."""
    result = runner.invoke(cli, ["run-debug", "--help"])
    assert "Usage:" in result.output


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
    print(result.output)
    assert "Using debug-dojo configuration:" in result.output
