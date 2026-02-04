"""Tests for CLI TUI launch behavior."""

from unittest.mock import patch

from typer.testing import CliRunner

from debug_dojo._cli import cli

runner = CliRunner()


def test_cli_no_args_launches_tui() -> None:
    """Test that running cli with no args launches the TUI."""
    # We need to mock DojoApp class import.
    # Since it is imported inside the function (probably), or top level.
    # If top level, we patch 'debug_dojo._cli.DojoApp'.

    with patch("debug_dojo._cli.DojoApp") as mock_app_cls:
        mock_instance = mock_app_cls.return_value  # pyright: ignore[reportAny]
        mock_instance.run.return_value = None  # pyright: ignore[reportAny] # Exit without command

        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        mock_app_cls.assert_called_once()
        mock_instance.run.assert_called_once()  # pyright: ignore[reportAny]


def test_cli_tui_returns_command_executes_it() -> None:
    """Test that if TUI returns a command, it is executed."""
    with (
        patch("debug_dojo._cli.DojoApp") as mock_app_cls,
        patch("subprocess.run") as mock_run,
    ):
        mock_instance = mock_app_cls.return_value  # pyright: ignore[reportAny]
        mock_instance.run.return_value = "dojo run test.py"  # pyright: ignore[reportAny]

        result = runner.invoke(cli, [])

        assert result.exit_code == 0

        mock_run.assert_called_once()
        args, _ = mock_run.call_args  # pyright: ignore[reportAny]
        # Verify first argument is the command string
        assert args[0] == "dojo run test.py"
        # Verify shell=True is passed
        assert mock_run.call_args[1].get("shell") is True  # pyright: ignore[reportAny]
