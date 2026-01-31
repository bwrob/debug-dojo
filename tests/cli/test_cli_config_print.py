"""Tests for debug-dojo CLI config print command."""

import rich
from typer.testing import CliRunner

from debug_dojo._cli import cli


def test_config_print_default(runner: CliRunner) -> None:
    """Test printing config from CLI."""
    args = ["run", "--verbose"]
    result = runner.invoke(cli, args)

    rich.print(result.output)

    assert result.exit_code == 0
    assert (
        "Using configuration file:" in result.output
        or "No configuration file found" in result.output
    )


def test_config_print_file(runner: CliRunner, test_config_path: str) -> None:
    """Test printing config from CLI."""
    args = ["run", "--config", test_config_path, "--verbose"]
    result = runner.invoke(cli, args)

    rich.print(result.output)

    assert result.exit_code == 0
