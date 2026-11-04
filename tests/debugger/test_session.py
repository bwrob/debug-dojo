"""Tests for debugger session lifecycle, excepthook, and top-level APIs."""

from __future__ import annotations

import bdb
import io
import os
import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from IPython.core.debugger import Pdb

import debug_dojo
from debug_dojo._core.debugger.debugger import DojoPdb
from debug_dojo._core.debugger.session import (
    BREAKPOINT_ENV_VAR,
    DEFAULT_CONTEXT_LINES,
    DPDB_SET_TRACE_HOOK,
    _bdb_quit_excepthook,
    _get_debugger_cls,
    _init_pdb,
    pm,
    post_mortem,
    set_trace,
    setup,
    wrap_sys_excepthook,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import FrameType


def _make_dojo_pdb(
    stdout: io.StringIO | None = None,
    *,
    pt_session_options: Mapping[str, object] | None = None,
) -> DojoPdb:
    stream = io.StringIO() if stdout is None else stdout
    with (
        patch.object(DojoPdb, "pt_init"),
        patch(
            "IPython.core.debugger.get_ipython",
            return_value=MagicMock(colors="neutral"),
        ),
    ):
        dbg = DojoPdb(
            stdout=stream,
            context=5,
            pt_session_options=pt_session_options,
        )
    dbg.reset()
    return dbg


def test_get_debugger_cls_no_shell() -> None:
    """Test _get_debugger_cls initializes TerminalIPythonApp when no shell is active."""
    mock_app = MagicMock()
    mock_app.shell.debugger_cls = Pdb
    with (
        patch("debug_dojo._core.debugger.session.get_ipython", return_value=None),
        patch(
            "debug_dojo._core.debugger.session.TerminalIPythonApp",
            return_value=mock_app,
        ),
    ):
        cls = _get_debugger_cls()
    assert cls is DojoPdb
    assert mock_app.interact is False
    mock_app.initialize.assert_called_once_with(
        ["--no-term-title", "--InteractiveShell.warn_venv=False"]
    )


def test_get_debugger_cls_no_shell_fallback() -> None:
    """Test _get_debugger_cls returns Pdb when app.shell remains None."""
    mock_app = MagicMock()
    mock_app.shell = None
    with (
        patch("debug_dojo._core.debugger.session.get_ipython", return_value=None),
        patch(
            "debug_dojo._core.debugger.session.TerminalIPythonApp",
            return_value=mock_app,
        ),
    ):
        cls = _get_debugger_cls()
    assert cls is Pdb


def test_get_debugger_cls_existing_shell() -> None:
    """Test _get_debugger_cls returns DojoPdb when an IPython shell is active."""
    mock_shell = MagicMock()
    with patch(
        "debug_dojo._core.debugger.session.get_ipython", return_value=mock_shell
    ):
        cls = _get_debugger_cls()
    assert cls is DojoPdb


def test_init_pdb_uses_default_context() -> None:
    """Test _init_pdb passes DEFAULT_CONTEXT_LINES to debugger_cls."""
    mock_instance = MagicMock()
    mock_cls = MagicMock(return_value=mock_instance)
    with patch(
        "debug_dojo._core.debugger.session._get_debugger_cls", return_value=mock_cls
    ):
        pdb_inst = _init_pdb()
    assert pdb_inst is mock_instance
    mock_cls.assert_called_once_with(context=DEFAULT_CONTEXT_LINES)


def test_wrap_sys_excepthook_idempotent() -> None:
    """Test wrap_sys_excepthook wraps sys.excepthook once and suppresses BdbQuit."""
    orig_hook = sys.excepthook
    try:
        sentinel_hook = MagicMock()
        sys.excepthook = sentinel_hook
        wrap_sys_excepthook()
        assert sys.excepthook is _bdb_quit_excepthook
        assert getattr(_bdb_quit_excepthook, "excepthook_ori", None) is sentinel_hook

        wrap_sys_excepthook()
        assert getattr(_bdb_quit_excepthook, "excepthook_ori", None) is sentinel_hook

        # BdbQuit is suppressed
        _bdb_quit_excepthook(bdb.BdbQuit, bdb.BdbQuit(), None)
        sentinel_hook.assert_not_called()

        # Other exceptions are forwarded
        err = RuntimeError("fail")
        _bdb_quit_excepthook(RuntimeError, err, None)
        sentinel_hook.assert_called_once_with(RuntimeError, err, None)
    finally:
        sys.excepthook = orig_hook


def test_dpdb_set_trace_default_frame_and_shell_restore() -> None:
    """Test set_trace restores shell state before arming bdb.set_trace."""
    call_order: list[str] = []

    def record_set_trace(_frame: FrameType | None) -> None:
        call_order.append("set_trace")

    mock_pdb = MagicMock()
    mock_shell = MagicMock()
    mock_shell.restore_sys_module_state.side_effect = lambda: call_order.append(
        "restore"
    )
    mock_pdb.set_trace.side_effect = record_set_trace
    mock_pdb.shell = mock_shell
    with patch("debug_dojo._core.debugger.session._init_pdb", return_value=mock_pdb):
        set_trace()
    assert call_order == ["restore", "set_trace"]


def test_dpdb_set_trace_explicit_frame_without_shell() -> None:
    """Test set_trace with explicit frame when pdb has no shell attribute."""
    mock_pdb = MagicMock(spec=Pdb)
    explicit_frame = sys._getframe()  # ruff: ignore[private-member-access] -- obtain real frame for test assertion
    with patch("debug_dojo._core.debugger.session._init_pdb", return_value=mock_pdb):
        set_trace(frame=explicit_frame)
    mock_pdb.set_trace.assert_called_once_with(explicit_frame)


def test_dpdb_post_mortem_with_explicit_tb() -> None:
    """Test post_mortem renders banner, resets pdb, and enters interaction."""
    buf = io.StringIO()
    dojo_pdb = _make_dojo_pdb(stdout=buf)
    fake_tb = MagicMock()
    fake_tb.tb_next = None
    fake_tb.tb_frame.f_code.co_filename = "script.py"
    fake_tb.tb_frame.f_code.co_name = "main"
    fake_tb.tb_lineno = 10
    with (
        patch("debug_dojo._core.debugger.session._init_pdb", return_value=dojo_pdb),
        patch.object(dojo_pdb, "reset") as mock_reset,
        patch.object(dojo_pdb, "interaction") as mock_interaction,
    ):
        post_mortem(fake_tb)
    mock_reset.assert_called_once_with()
    mock_interaction.assert_called_once_with(None, fake_tb)
    assert "Dojo Post-Mortem" in buf.getvalue()


def test_dpdb_post_mortem_without_active_exception() -> None:
    """Test post_mortem does not call interaction when no traceback exists."""
    mock_pdb = MagicMock()
    with patch("debug_dojo._core.debugger.session._init_pdb", return_value=mock_pdb):
        post_mortem(None)
    mock_pdb.reset.assert_called_once_with()
    mock_pdb.interaction.assert_not_called()


@patch("debug_dojo._core.debugger.session.set_trace")
def test_dpdb_setup(mock_set_trace: MagicMock) -> None:
    """Test setup configures PYTHONBREAKPOINT and sys.breakpointhook."""
    setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == DPDB_SET_TRACE_HOOK
    assert sys.breakpointhook == mock_set_trace


def test_top_level_debug_dojo_api() -> None:
    """Test debug_dojo.set_trace, post_mortem, and pm top-level exports."""
    assert debug_dojo.set_trace is set_trace
    assert debug_dojo.post_mortem is post_mortem
    assert debug_dojo.pm is pm

    fake_exc = RuntimeError("crash")
    with (
        patch.object(sys, "last_exc", fake_exc, create=True),
        patch("debug_dojo._core.debugger.session.post_mortem") as mock_pm_last,
    ):
        debug_dojo.pm()
        mock_pm_last.assert_called_once_with(fake_exc.__traceback__)

    with (
        patch.object(sys, "last_exc", None, create=True),
        patch.object(sys, "last_traceback", None, create=True),
        patch("debug_dojo._core.debugger.session.post_mortem") as mock_pm_fallback,
    ):
        debug_dojo.pm()
        mock_pm_fallback.assert_called_once_with(None)
