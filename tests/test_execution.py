"""Tests for the `_execution` module."""

from __future__ import annotations

import os
import sys
from bdb import BdbQuit
from collections.abc import Callable
from pathlib import Path
from pdb import Restart
from unittest.mock import MagicMock, patch

import pytest

from debug_dojo._core.execution import (
    _activate_venv_paths,
    _configure_project_venv,
    _configure_sys_argv,
    _configure_sys_path,
    _find_venv_in_ancestors,
    _get_runner_and_target,
    _handle_exception,
    _is_importable_module,
    _is_runner_only_traceback,
    _resolve_project_venv,
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


def test_find_venv_in_ancestors(tmp_path: Path) -> None:
    """Test _find_venv_in_ancestors finds pyvenv.cfg in parent or returns None."""
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert _find_venv_in_ancestors(nested) is None

    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    assert _find_venv_in_ancestors(nested) == venv_dir.resolve()


def test_resolve_project_venv_uv_direct_and_relative(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _resolve_project_venv with direct and ancestor UV_PROJECT_ENVIRONMENT."""
    direct_venv = tmp_path / "custom_direct"
    direct_venv.mkdir()
    (direct_venv / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(direct_venv))
    assert _resolve_project_venv(tmp_path) == direct_venv.resolve()

    rel_venv = tmp_path / ".venv-custom"
    rel_venv.mkdir()
    (rel_venv / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", ".venv-custom")
    assert _resolve_project_venv(sub) == rel_venv.resolve()


def test_resolve_project_venv_fallbacks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _resolve_project_venv fallback order."""
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", "missing-venv")
    active_venv = tmp_path / "active_venv"
    active_venv.mkdir()
    (active_venv / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(active_venv))
    assert _resolve_project_venv(tmp_path) == active_venv.resolve()

    # Invalid VIRTUAL_ENV falls back to ancestor .venv search
    monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / "nonexistent"))
    assert _resolve_project_venv(tmp_path) is None


def test_activate_venv_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _activate_venv_paths registers site-packages and bin directories."""
    venv_dir = tmp_path / ".venv"
    posix_site = venv_dir / "lib" / "python3.12" / "site-packages"
    bin_dir = venv_dir / "bin"
    posix_site.mkdir(parents=True)
    bin_dir.mkdir(parents=True)

    monkeypatch.setenv("PATH", "")
    with patch("site.addsitedir") as mock_addsitedir:
        _activate_venv_paths(venv_dir)
        assert os.environ["PATH"] == str(bin_dir)
        mock_addsitedir.assert_called_once_with(str(posix_site))

        # Second call with existing PATH entry does not duplicate bin_dir
        monkeypatch.setenv("PATH", f"/usr/bin{os.pathsep}{bin_dir}")
        _activate_venv_paths(venv_dir)
        assert os.environ["PATH"] == f"/usr/bin{os.pathsep}{bin_dir}"

        # Call with non-empty PATH not containing bin_dir prepends bin_dir
        monkeypatch.setenv("PATH", "/usr/bin")
        _activate_venv_paths(venv_dir)
        assert os.environ["PATH"] == f"{bin_dir}{os.pathsep}/usr/bin"


def test_configure_project_venv_when_none_and_external(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _configure_project_venv skips active/missing venv and activates external."""
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    monkeypatch.chdir(tmp_path)
    with patch("debug_dojo._core.execution._activate_venv_paths") as mock_activate:
        _configure_project_venv("some.module")
        mock_activate.assert_not_called()

        ext_venv = tmp_path / ".venv"
        ext_venv.mkdir()
        (ext_venv / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
        script = tmp_path / "script.py"
        script.write_text("x = 1\n", encoding="utf-8")
        _configure_project_venv(str(script))
        mock_activate.assert_called_once_with(ext_venv.resolve())


def test_configure_sys_path(tmp_path: Path) -> None:
    """Test _configure_sys_path sets sys.path[0] for non-empty and empty sys.path."""
    orig_path = list(sys.path)
    try:
        _configure_sys_path(str(tmp_path))
        assert sys.path[0] == str(tmp_path)

        sys.path.clear()
        _configure_sys_path(str(tmp_path))
        assert sys.path == [str(tmp_path)]
    finally:
        sys.path = orig_path


def test_is_importable_module() -> None:
    """Test _is_importable_module handles paths, .py files, modules, and errors."""
    assert _is_importable_module("") is False
    assert _is_importable_module("dir/file") is False
    assert _is_importable_module("script.py") is False
    assert _is_importable_module("debug_dojo") is True
    with patch("importlib.util.find_spec", side_effect=ValueError("bad spec")):
        assert _is_importable_module("broken.spec") is False


def test_get_runner_and_target_nonexistent() -> None:
    """Test get_runner_and_target raises Exit(1) on unresolvable target."""
    with pytest.raises(SystemExit) as exc:
        _ = _get_runner_and_target("nonexistent_script_12345.py")
    assert exc.value.code == 1


@patch("debug_dojo._core.execution.post_mortem")
def test_handle_exception_with_post_mortem(mock_pm: MagicMock) -> None:
    """Test exception handler enters dpdb post-mortem."""
    exc = RuntimeError("Test error")
    with pytest.raises(SystemExit) as exit_exc:
        _handle_exception(exc)
    assert exit_exc.value.code == 1
    mock_pm.assert_called_once_with(exc.__traceback__)


def test_safe_execute_import_error() -> None:
    """Test safe_execute catches runner-only ImportError and raises Exit(1)."""
    runner = MagicMock(side_effect=ImportError("Cannot import target"))

    with pytest.raises(SystemExit) as exit_exc:
        _safe_execute(runner, "bad_mod")
    assert exit_exc.value.code == 1


@patch("debug_dojo._core.execution.post_mortem")
def test_safe_execute_user_import_error_enters_post_mortem(
    mock_pm: MagicMock,
) -> None:
    """Test safe_execute enters post-mortem on user-frame ImportError."""

    def user_runner(_target: str, **_kwargs: object) -> dict[str, object]:
        msg = "nested import failure"
        raise ImportError(msg)

    with (
        patch(
            "debug_dojo._core.execution._is_runner_only_traceback", return_value=False
        ),
        pytest.raises(SystemExit) as exit_exc,
    ):
        _safe_execute(user_runner, "script.py")
    assert exit_exc.value.code == 1
    mock_pm.assert_called_once()


def test_is_runner_only_traceback() -> None:
    """Test _is_runner_only_traceback distinguishes runner vs user frames."""
    assert _is_runner_only_traceback(None) is True

    fake_tb = MagicMock()
    fake_tb.tb_next = None
    with patch("debug_dojo._core.execution.is_runner_frame", return_value=False):
        assert _is_runner_only_traceback(fake_tb) is False


def test_safe_execute_restart_and_active_breakpoints() -> None:
    """Test _safe_execute loops on Restart and uses run_with_active_breakpoints."""
    calls: list[int] = []

    def restarting_runner(_target: str, **_kwargs: object) -> dict[str, object]:
        calls.append(1)
        if len(calls) == 1:
            raise Restart
        return {}

    def invoke_fn(fn: Callable[[], object]) -> object:
        return fn()

    with (
        patch(
            "debug_dojo._core.execution.has_active_breakpoints",
            side_effect=[False, True],
        ),
        patch(
            "debug_dojo._core.execution.run_with_active_breakpoints",
            side_effect=invoke_fn,
        ) as mock_run_bp,
    ):
        _safe_execute(restarting_runner, "target.py")

    assert len(calls) == 2  # ruff: ignore[magic-value-comparison] -- initial run + 1 restart
    mock_run_bp.assert_called_once()


def test_safe_execute_bdb_quit() -> None:
    """Test safe_execute catches BdbQuit and raises Exit(0)."""
    runner = MagicMock(side_effect=BdbQuit())

    with pytest.raises(SystemExit) as exit_exc:
        _safe_execute(runner, "target")
    assert exit_exc.value.code == 0


def test_safe_execute_keyboard_interrupt() -> None:
    """Test safe_execute catches KeyboardInterrupt and raises Exit(0)."""
    runner = MagicMock(side_effect=KeyboardInterrupt())

    with pytest.raises(SystemExit) as exit_exc:
        _safe_execute(runner, "target")
    assert exit_exc.value.code == 0


def test_safe_execute_system_exit_nonzero() -> None:
    """Test safe_execute catches SystemExit with non-zero exit code."""
    runner = MagicMock(side_effect=SystemExit(2))

    _safe_execute(runner, "target")


def test_safe_execute_system_exit_zero() -> None:
    """Test safe_execute catches SystemExit with code 0."""
    runner = MagicMock(side_effect=SystemExit(0))

    _safe_execute(runner, "target")


@patch("debug_dojo._core.execution.seed_cli_breakpoints")
@patch("runpy.run_path")
def test_execute_with_debug_default(
    mock_run_path: MagicMock,
    mock_seed_bps: MagicMock,
    tmp_path: Path,
) -> None:
    """Test execute_with_debug runs target and seeds optional CLI breakpoints."""
    dummy_file = tmp_path / "dummy.py"
    dummy_file.write_text("print('hello')", encoding="utf-8")
    execute_with_debug(
        target_name=str(dummy_file),
        target_args=[],
        breaks=["1"],
    )
    mock_seed_bps.assert_called_once_with(str(dummy_file), ["1"])
    mock_run_path.assert_called_once_with(str(dummy_file), run_name="__main__")
