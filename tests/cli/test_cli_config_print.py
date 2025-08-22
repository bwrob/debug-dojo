"""Tests for debug-dojo CLI config print command."""

from typer.testing import CliRunner

from debug_dojo._cli import cli
from debug_dojo._config_models import DebugDojoConfig

runner = CliRunner()


def test_config_print_default() -> None:
    """Test printing config from CLI."""
    args = ["--verbose"]
    result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0

    default_config = DebugDojoConfig()
    assert f"{type(default_config).__name__}" in result.output

    debuggers = default_config.debuggers
    assert f'"port": {debuggers.debugpy.port},' in result.output
    assert f'"context_lines": {debuggers.ipdb.context_lines}' in result.output

    features = default_config.features
    assert f'"{features.rich_inspect}"' in result.output
    assert f'"{features.rich_print}"' in result.output
    assert f'"{features.comparer}"' in result.output
    assert f'"{features.breakpoint}"' in result.output


def test_config_print_file() -> None:
    """Test printing config from CLI."""
    args = ["--config", "tests/assets/test_config.toml", "--verbose"]
    result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0

    assert "DebugDojoConfigV2" in result.output
    assert '"port": 1234,' in result.output
    assert '"context_lines": 1' in result.output
