"""Tests for debug-dojo CLI config print command."""

import rich
from typer.testing import CliRunner

from debug_dojo._cli import cli
from debug_dojo._config_models import DebugDojoConfig


def test_config_print_default(runner: CliRunner) -> None:
    """Test printing config from CLI."""
    args = ["--verbose"]
    result = runner.invoke(cli, args)

    rich.print(result.output)

    assert result.exit_code == 0

    default_config = DebugDojoConfig()
    assert f"{type(default_config).__name__}" in result.output

    debuggers = default_config.debuggers
    assert f"port={debuggers.debugpy.port}" in result.output
    assert f"context_lines={debuggers.ipdb.context_lines}" in result.output

    features = default_config.features
    assert f"rich_inspect='{features.rich_inspect}'" in result.output
    assert f"rich_print='{features.rich_print}'" in result.output
    assert f"comparer='{features.comparer}'" in result.output
    assert f"breakpoint='{features.breakpoint}'" in result.output


def test_config_print_file(runner: CliRunner, test_config_path: str) -> None:
    """Test printing config from CLI."""
    args = ["--config", test_config_path, "--verbose"]
    result = runner.invoke(cli, args)

    rich.print(result.output)

    assert result.exit_code == 0

    assert "DebugDojoConfigV2" in result.output
    assert "port=1234" in result.output
    assert "context_lines=1" in result.output
