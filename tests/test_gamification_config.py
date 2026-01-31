"""Tests for gamification configuration."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from debug_dojo._cli import cli
from debug_dojo._config_models import DebugDojoConfigV2

if TYPE_CHECKING:
    from click.testing import Result


def test_gamification_disabled_increment(runner: CliRunner) -> None:
    """Test that session is not incremented when gamification is disabled."""
    # Mock config to have gamification=False
    mock_config = DebugDojoConfigV2(gamification=False)

    with (
        patch("debug_dojo._cli.load_config", return_value=mock_config),
        patch("debug_dojo._cli.GamificationManager") as mock_manager_cls,
        patch("debug_dojo._cli.execute_with_debug"),
        patch("debug_dojo._cli.time.perf_counter", side_effect=[0.0, 1.0]),
    ):
        mock_instance = MagicMock()
        mock_manager_cls.return_value = mock_instance

        # Run command
        _ = runner.invoke(cli, ["run", "script.py"])

        # Verify increment_session was NOT called
        mock_instance.increment_session.assert_not_called()  # pyright: ignore[reportAny]


def test_gamification_enabled_increment(runner: CliRunner) -> None:
    """Test that session is incremented when gamification is enabled (default)."""
    # Mock config to have gamification=True
    mock_config = DebugDojoConfigV2(gamification=True)

    with (
        patch("debug_dojo._cli.load_config", return_value=mock_config),
        patch("debug_dojo._cli.GamificationManager") as mock_manager_cls,
        patch("debug_dojo._cli.execute_with_debug"),
        patch("debug_dojo._cli.time.perf_counter", side_effect=[0.0, 1.0]),
    ):
        mock_instance = MagicMock()
        mock_manager_cls.return_value = mock_instance

        # Run command
        _ = runner.invoke(cli, ["run", "script.py"])

        # Verify increment_session WAS called
        mock_instance.increment_session.assert_called_once()  # pyright: ignore[reportAny]


def test_belt_command_disabled(runner: CliRunner) -> None:
    """Test belt command output when disabled."""
    mock_config = DebugDojoConfigV2(gamification=False)

    with patch("debug_dojo._cli.load_config", return_value=mock_config):
        result: Result = runner.invoke(cli, ["belt"])

        assert "Gamification is disabled" in result.output
