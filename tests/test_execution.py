"""Tests for the `_execution` module."""

from __future__ import annotations

import sys
from bdb import BdbQuit
from unittest.mock import MagicMock

import pytest
import typer

from debug_dojo._config_models import DebugDojoConfig
from debug_dojo._execution import (
    ExecMode,
    _configure_sys_argv,
    _get_runner_and_target,
    _handle_exception,
    _install_debug_tools,
    _safe_execute,
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
    config = DebugDojoConfig()
    _install_debug_tools("myscript.py", ["--foo"], verbose=True, config=config)


def test_get_runner_and_target_nonexistent() -> None:
    """Test get_runner_and_target raises Exit(1) on nonexistent file."""
    with pytest.raises(typer.Exit) as exc:
        _ = _get_runner_and_target("nonexistent_script_12345.py", ExecMode.FILE)
    assert exc.value.exit_code == 1


def test_handle_exception_without_post_mortem() -> None:
    """Test exception handler when post-mortem is disabled."""
    config = DebugDojoConfig()
    config.exceptions.post_mortem = False

    exc = RuntimeError("Test error without post mortem")
    with pytest.raises(typer.Exit) as exit_exc:
        _handle_exception(exc, "test_target", config)
    assert exit_exc.value.exit_code == 1


def test_safe_execute_import_error() -> None:
    """Test safe_execute catches ImportError and raises Exit(1)."""
    runner = MagicMock(side_effect=ImportError("Cannot import target"))
    config = DebugDojoConfig()

    with pytest.raises(typer.Exit) as exit_exc:
        _safe_execute(runner, "bad_mod", config)
    assert exit_exc.value.exit_code == 1


def test_safe_execute_bdb_quit() -> None:
    """Test safe_execute catches BdbQuit and raises Exit(0)."""
    runner = MagicMock(side_effect=BdbQuit())
    config = DebugDojoConfig()

    with pytest.raises(typer.Exit) as exit_exc:
        _safe_execute(runner, "target", config)
    assert exit_exc.value.exit_code == 0


def test_safe_execute_keyboard_interrupt() -> None:
    """Test safe_execute catches KeyboardInterrupt and raises Exit(0)."""
    runner = MagicMock(side_effect=KeyboardInterrupt())
    config = DebugDojoConfig()

    with pytest.raises(typer.Exit) as exit_exc:
        _safe_execute(runner, "target", config)
    assert exit_exc.value.exit_code == 0


def test_safe_execute_system_exit_nonzero() -> None:
    """Test safe_execute catches SystemExit with non-zero exit code."""
    runner = MagicMock(side_effect=SystemExit(2))
    config = DebugDojoConfig()

    # SystemExit with code 2 should be caught and logged
    _safe_execute(runner, "target", config)


def test_safe_execute_system_exit_zero() -> None:
    """Test safe_execute catches SystemExit with code 0."""
    runner = MagicMock(side_effect=SystemExit(0))
    config = DebugDojoConfig()

    _safe_execute(runner, "target", config)
