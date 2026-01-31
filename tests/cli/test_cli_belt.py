"""Tests for debug-dojo CLI belt command."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from debug_dojo._cli import cli
from debug_dojo._gamification import GamificationManager

if TYPE_CHECKING:
    from click.testing import Result


def test_belt_command(runner: CliRunner) -> None:
    """Test the belt command output."""
    # Mock GamificationManager to return a specific state
    with patch("debug_dojo._cli.GamificationManager") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        # We don't mock display_status because we want to see if it runs
        # But display_status prints to console using Rich.
        # So we should probably verify that display_status was called.

        result: Result = runner.invoke(cli, ["belt"])

        assert result.exit_code == 0
        mock_instance.display_status.assert_called_once()


def test_belt_command_integration(runner: CliRunner, tmp_path: str) -> None:
    """Integration test for belt command."""
    # Use a real GamificationManager with a temp path

    with patch("debug_dojo._gamification.Path.home") as mock_home:
        mock_home.return_value = tmp_path

        # Initialize stats
        manager = GamificationManager()
        manager.increment_session()  # 1 session

        result: Result = runner.invoke(cli, ["belt"])

        assert result.exit_code == 0
        assert "White Belt" in result.output
        assert "Sessions: 1" in result.output
