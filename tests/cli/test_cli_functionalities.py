"""Tests for debug-dojo CLI functionalities."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from debug_dojo.cli import cli

if TYPE_CHECKING:
    from debug_dojo.cli import CliRunner


@patch("debug_dojo._core.debugger.session.set_trace")
def test_breakpoint_dpdb(
    mock_set_trace: MagicMock,
    runner: CliRunner,
    test_target_breakpoint: str,
) -> None:
    """Test breakpoint with dpdb from CLI."""
    result = runner.invoke(cli, [test_target_breakpoint])

    assert result.exit_code == 0
    mock_set_trace.assert_called_once()


@patch("debug_dojo._core.execution.dpdb.post_mortem")
def test_post_mortem_dpdb(
    mock_dpdb_pm: MagicMock,
    runner: CliRunner,
    test_target_exception: str,
) -> None:
    """Test post-mortem enters dpdb when an unhandled exception occurs."""
    result = runner.invoke(cli, [test_target_exception])

    assert result.exit_code != 0
    mock_dpdb_pm.assert_called_once()
