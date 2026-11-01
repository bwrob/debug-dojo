"""Tests for the `_execution` module."""

from __future__ import annotations

import sys
from bdb import BdbQuit
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer

from debug_dojo._config_models import DebuggerType, DojoSettings
from debug_dojo._execution import (
    ExecMode,
    _configure_sys_argv,
    _enter_post_mortem,
    _get_runner_and_target,
    _handle_exception,
    _install_debug_tools,
    _safe_execute,
    execute_with_debug,
)


def test_configure_sys_argv() -> None:
    """Test configuring sys.argv for targets."""
    orig = sys.argv
    try:
        _configure_sys_argv("myscript.py", ["--arg1", "val1"])
        assert sys.argv == ["myscript.py", "--arg1", "val1"]
    finally:
        sys.argv = orig


def test_install_debug_tools_verbose() -> None:
    """Test installing debug tools with verbose=True."""
    settings = DojoSettings()
    _install_debug_tools("myscript.py", ["--foo"], verbose=True, settings=settings)


def test_get_runner_and_target_nonexistent() -> None:
    """Test get_runner_and_target raises Exit(1) on nonexistent file."""
    with pytest.raises(typer.Exit) as exc:
        _ = _get_runner_and_target("nonexistent_script_12345.py", ExecMode.FILE)
    assert exc.value.exit_code == 1


def test_handle_exception_without_post_mortem() -> None:
    """Test exception handler when post-mortem is disabled."""
    settings = DojoSettings(post_mortem=False)

    exc = RuntimeError("Test error without post mortem")
    with pytest.raises(typer.Exit) as exit_exc:
        _handle_exception(exc, "test_target", settings)
    assert exit_exc.value.exit_code == 1


@patch("pdb.post_mortem")
def test_handle_exception_with_post_mortem_pdb(mock_pm: MagicMock) -> None:
    """Test exception handler enters PDB post-mortem when debugger is PDB."""
    settings = DojoSettings(post_mortem=True, debugger=DebuggerType.PDB)

    exc = RuntimeError("Test error with pdb")
    with pytest.raises(typer.Exit) as exit_exc:
        _handle_exception(exc, "test_target", settings)
    assert exit_exc.value.exit_code == 1
    mock_pm.assert_called_once_with(exc.__traceback__)


@patch("ipdb.post_mortem")
def test_enter_post_mortem_ipdb(mock_pm: MagicMock) -> None:
    """Test post-mortem with IPDB."""
    _enter_post_mortem(None, DebuggerType.IPDB)
    mock_pm.assert_called_once_with(None)


@patch("pdb.post_mortem")
def test_enter_post_mortem_ipdb_fallback(mock_pdb_pm: MagicMock) -> None:
    """Test post-mortem fallback to PDB when IPDB is unimportable."""
    with patch.dict("sys.modules", {"ipdb": None}):
        _enter_post_mortem(None, DebuggerType.IPDB)
    mock_pdb_pm.assert_called_once_with(None)


@patch("pudb.post_mortem")
def test_enter_post_mortem_pudb(mock_pm: MagicMock) -> None:
    """Test post-mortem with PuDB."""
    _enter_post_mortem(None, DebuggerType.PUDB)
    mock_pm.assert_called_once_with(None)


@patch("pdb.post_mortem")
def test_enter_post_mortem_pudb_fallback(mock_pdb_pm: MagicMock) -> None:
    """Test post-mortem fallback to PDB when PuDB is unimportable."""
    with patch.dict("sys.modules", {"pudb": None}):
        _enter_post_mortem(None, DebuggerType.PUDB)
    mock_pdb_pm.assert_called_once_with(None)


def test_safe_execute_import_error() -> None:
    """Test safe_execute catches ImportError and raises Exit(1)."""
    runner = MagicMock(side_effect=ImportError("Cannot import target"))
    settings = DojoSettings()

    with pytest.raises(typer.Exit) as exit_exc:
        _safe_execute(runner, "bad_mod", settings)
    assert exit_exc.value.exit_code == 1


def test_safe_execute_bdb_quit() -> None:
    """Test safe_execute catches BdbQuit and raises Exit(0)."""
    runner = MagicMock(side_effect=BdbQuit())
    settings = DojoSettings()

    with pytest.raises(typer.Exit) as exit_exc:
        _safe_execute(runner, "target", settings)
    assert exit_exc.value.exit_code == 0


def test_safe_execute_keyboard_interrupt() -> None:
    """Test safe_execute catches KeyboardInterrupt and raises Exit(0)."""
    runner = MagicMock(side_effect=KeyboardInterrupt())
    settings = DojoSettings()

    with pytest.raises(typer.Exit) as exit_exc:
        _safe_execute(runner, "target", settings)
    assert exit_exc.value.exit_code == 0


def test_safe_execute_system_exit_nonzero() -> None:
    """Test safe_execute catches SystemExit with non-zero exit code."""
    runner = MagicMock(side_effect=SystemExit(2))
    settings = DojoSettings()

    _safe_execute(runner, "target", settings)


def test_safe_execute_system_exit_zero() -> None:
    """Test safe_execute catches SystemExit with code 0."""
    runner = MagicMock(side_effect=SystemExit(0))
    settings = DojoSettings()

    _safe_execute(runner, "target", settings)


@patch("runpy.run_path")
def test_execute_with_debug_default(mock_run_path: MagicMock, tmp_path: Path) -> None:
    """Test execute_with_debug runs target with default settings when config is None."""
    dummy_file = tmp_path / "dummy.py"
    dummy_file.write_text("print('hello')", encoding="utf-8")
    execute_with_debug(
        target_name=str(dummy_file),
        target_args=[],
        target_mode=ExecMode.FILE,
        verbose=False,
        config=None,
    )
    mock_run_path.assert_called_once_with(str(dummy_file), run_name="__main__")
