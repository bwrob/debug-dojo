"""Tests for debug-dojo CLI functionalities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from debug_dojo._cli import cli


@patch("ipdb.set_trace")
def test_breakpoint_ipdb(
    mock_set_trace: MagicMock,
    runner: CliRunner,
    test_target_breakpoint: str,
) -> None:
    """Test breakpoint with ipdb from CLI."""
    args = ["run", "-d", "ipdb", test_target_breakpoint]
    result = runner.invoke(cli, args)

    assert result.exit_code == 0
    mock_set_trace.assert_called_once()


@patch("ipdb.post_mortem")
def test_post_mortem(
    mock_post_mortem: MagicMock,
    runner: CliRunner,
    test_target_exception: str,
) -> None:
    """Test post-mortem with ipdb from CLI."""
    args = ["run", "-d", "ipdb", test_target_exception]
    result = runner.invoke(cli, args)

    assert result.exit_code != 0
    mock_post_mortem.assert_called_once()


@patch("ipdb.post_mortem")
@patch("pdb.post_mortem")
def test_post_mortem_disabled(
    mock_pdb_pm: MagicMock,
    mock_ipdb_pm: MagicMock,
    runner: CliRunner,
    test_target_exception: str,
) -> None:
    """Test disabling post-mortem debugging via --no-post-mortem."""
    args = ["run", "--no-post-mortem", test_target_exception]
    result = runner.invoke(cli, args)

    assert result.exit_code != 0
    mock_ipdb_pm.assert_not_called()
    mock_pdb_pm.assert_not_called()
