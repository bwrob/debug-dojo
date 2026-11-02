"""Tests for debugger backend adapters in `debug_dojo.adapters`."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from IPython.core.debugger import BdbQuit_excepthook, Pdb

from debug_dojo.adapters import (
    BREAKPOINT_ENV_VAR,
    DebuggerType,
    debugpy,
    dpdb,
    enter_post_mortem,
    get_adapter,
    ipdb,
    pdb,
    pudb,
    setup_debugger,
)
from debug_dojo.adapters.dpdb import (
    DEFAULT_CONTEXT_LINES,
    _get_debugger_cls,
    _init_pdb,
)

if TYPE_CHECKING:
    import pytest


def test_debugger_type_set_trace_hooks() -> None:
    """Test set_trace_hook property on DebuggerType."""
    assert DebuggerType.DPDB.set_trace_hook == "debug_dojo.adapters.dpdb.set_trace"
    assert DebuggerType.PDB.set_trace_hook == "pdb.set_trace"
    assert DebuggerType.IPDB.set_trace_hook == "ipdb.set_trace"
    assert DebuggerType.PUDB.set_trace_hook == "pudb.set_trace"
    assert DebuggerType.DEBUGPY.set_trace_hook == "debugpy.breakpoint"


def test_get_adapter_resolution() -> None:
    """Test get_adapter maps DebuggerType values and None to adapter modules."""
    assert get_adapter(None) is dpdb
    assert get_adapter(DebuggerType.DPDB) is dpdb
    assert get_adapter(DebuggerType.PDB) is pdb
    assert get_adapter(DebuggerType.IPDB) is ipdb
    assert get_adapter(DebuggerType.PUDB) is pudb
    assert get_adapter(DebuggerType.DEBUGPY) is debugpy


def test_get_debugger_cls_no_shell() -> None:
    """Test _get_debugger_cls initializes TerminalIPythonApp when no shell is active."""
    mock_app = MagicMock()
    mock_app.shell.debugger_cls = Pdb
    with (
        patch("debug_dojo.adapters.dpdb.get_ipython", return_value=None),
        patch("debug_dojo.adapters.dpdb.TerminalIPythonApp", return_value=mock_app),
    ):
        cls = _get_debugger_cls()
    assert cls is Pdb
    assert mock_app.interact is False
    mock_app.initialize.assert_called_once_with(["--no-term-title"])


def test_get_debugger_cls_no_shell_fallback() -> None:
    """Test _get_debugger_cls returns Pdb when app.shell remains None."""
    mock_app = MagicMock()
    mock_app.shell = None
    with (
        patch("debug_dojo.adapters.dpdb.get_ipython", return_value=None),
        patch("debug_dojo.adapters.dpdb.TerminalIPythonApp", return_value=mock_app),
    ):
        cls = _get_debugger_cls()
    assert cls is Pdb


def test_get_debugger_cls_existing_shell() -> None:
    """Test _get_debugger_cls reuses debugger_cls from an existing shell."""
    mock_shell = MagicMock()
    mock_shell.debugger_cls = Pdb
    with patch("debug_dojo.adapters.dpdb.get_ipython", return_value=mock_shell):
        cls = _get_debugger_cls()
    assert cls is Pdb


def test_init_pdb_uses_default_context() -> None:
    """Test _init_pdb passes DEFAULT_CONTEXT_LINES to debugger_cls."""
    mock_instance = MagicMock()
    mock_cls = MagicMock(return_value=mock_instance)
    with patch("debug_dojo.adapters.dpdb._get_debugger_cls", return_value=mock_cls):
        pdb_inst = _init_pdb()
    assert pdb_inst is mock_instance
    mock_cls.assert_called_once_with(context=DEFAULT_CONTEXT_LINES)


def test_wrap_sys_excepthook_idempotent() -> None:
    """Test wrap_sys_excepthook wraps sys.excepthook once and is idempotent."""
    orig_hook = sys.excepthook
    try:
        sentinel_hook = MagicMock()
        sys.excepthook = sentinel_hook
        dpdb.wrap_sys_excepthook()
        assert sys.excepthook is BdbQuit_excepthook
        assert getattr(BdbQuit_excepthook, "excepthook_ori", None) is sentinel_hook

        dpdb.wrap_sys_excepthook()
        assert getattr(BdbQuit_excepthook, "excepthook_ori", None) is sentinel_hook
    finally:
        sys.excepthook = orig_hook


def test_dpdb_set_trace_default_frame_and_shell_restore() -> None:
    """Test dpdb.set_trace resolves caller frame and restores shell state."""
    mock_pdb = MagicMock()
    mock_shell = MagicMock()
    mock_pdb.shell = mock_shell
    with patch("debug_dojo.adapters.dpdb._init_pdb", return_value=mock_pdb):
        dpdb.set_trace()
    mock_pdb.set_trace.assert_called_once()
    mock_shell.restore_sys_module_state.assert_called_once_with()


def test_dpdb_set_trace_explicit_frame_without_shell() -> None:
    """Test dpdb.set_trace with explicit frame when pdb has no shell attribute."""
    mock_pdb = MagicMock(spec=Pdb)
    explicit_frame = sys._getframe()  # ruff: ignore[private-member-access] -- obtain real frame for test assertion
    with patch("debug_dojo.adapters.dpdb._init_pdb", return_value=mock_pdb):
        dpdb.set_trace(frame=explicit_frame)
    mock_pdb.set_trace.assert_called_once_with(explicit_frame)


def test_dpdb_post_mortem_with_explicit_tb() -> None:
    """Test dpdb.post_mortem resets pdb and starts interaction with traceback."""
    mock_pdb = MagicMock()
    fake_tb = MagicMock()
    with patch("debug_dojo.adapters.dpdb._init_pdb", return_value=mock_pdb):
        dpdb.post_mortem(fake_tb)
    mock_pdb.reset.assert_called_once_with()
    mock_pdb.interaction.assert_called_once_with(None, fake_tb)


def test_dpdb_post_mortem_without_active_exception() -> None:
    """Test dpdb.post_mortem does not call interaction when no traceback exists."""
    mock_pdb = MagicMock()
    with patch("debug_dojo.adapters.dpdb._init_pdb", return_value=mock_pdb):
        dpdb.post_mortem(None)
    mock_pdb.reset.assert_called_once_with()
    mock_pdb.interaction.assert_not_called()


@patch("debug_dojo.adapters.dpdb.set_trace")
def test_dpdb_setup(mock_set_trace: MagicMock) -> None:
    """Test dpdb.setup configures PYTHONBREAKPOINT and sys.breakpointhook."""
    dpdb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debug_dojo.adapters.dpdb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("pdb.set_trace")
def test_pdb_setup(mock_set_trace: MagicMock) -> None:
    """Test pdb.setup configures PYTHONBREAKPOINT and sys.breakpointhook."""
    pdb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "pdb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("pdb.post_mortem")
def test_pdb_post_mortem(mock_pm: MagicMock) -> None:
    """Test pdb.post_mortem delegates to standard library pdb.post_mortem."""
    pdb.post_mortem(None)
    mock_pm.assert_called_once_with(None)


@patch("ipdb.set_trace")
def test_ipdb_setup(mock_set_trace: MagicMock) -> None:
    """Test ipdb.setup configures PYTHONBREAKPOINT, context size, and hook."""
    ipdb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "ipdb.set_trace"
    assert os.environ[ipdb.IPDB_CONTEXT_SIZE] == ipdb.DEFAULT_IPDB_CONTEXT_LINES
    assert sys.breakpointhook == mock_set_trace


def test_ipdb_setup_not_installed() -> None:
    """Test ipdb.setup falls back to dpdb when IPDB is not importable."""
    with patch.dict("sys.modules", {"ipdb": None}):
        ipdb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debug_dojo.adapters.dpdb.set_trace"


@patch("ipdb.post_mortem")
def test_ipdb_post_mortem(mock_pm: MagicMock) -> None:
    """Test ipdb.post_mortem delegates to ipdb.post_mortem."""
    ipdb.post_mortem(None)
    mock_pm.assert_called_once_with(None)


@patch("debug_dojo.adapters.dpdb.post_mortem")
def test_ipdb_post_mortem_fallback(mock_dpdb_pm: MagicMock) -> None:
    """Test ipdb.post_mortem falls back to dpdb.post_mortem when unimportable."""
    with patch.dict("sys.modules", {"ipdb": None}):
        ipdb.post_mortem(None)
    mock_dpdb_pm.assert_called_once_with(None)


@patch("pudb.set_trace")
def test_pudb_setup(mock_set_trace: MagicMock) -> None:
    """Test pudb.setup configures PYTHONBREAKPOINT and sys.breakpointhook."""
    pudb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "pudb.set_trace"
    assert sys.breakpointhook == mock_set_trace


def test_pudb_setup_not_installed() -> None:
    """Test pudb.setup falls back to dpdb when PuDB is not importable."""
    with patch.dict("sys.modules", {"pudb": None}):
        pudb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debug_dojo.adapters.dpdb.set_trace"


@patch("pudb.post_mortem")
def test_pudb_post_mortem(mock_pm: MagicMock) -> None:
    """Test pudb.post_mortem delegates to pudb.post_mortem."""
    pudb.post_mortem(None)
    mock_pm.assert_called_once_with(None)


@patch("debug_dojo.adapters.dpdb.post_mortem")
def test_pudb_post_mortem_fallback(mock_dpdb_pm: MagicMock) -> None:
    """Test pudb.post_mortem falls back to dpdb.post_mortem when unimportable."""
    with patch.dict("sys.modules", {"pudb": None}):
        pudb.post_mortem(None)
    mock_dpdb_pm.assert_called_once_with(None)


@patch("debugpy.listen")
@patch("debugpy.wait_for_client")
@patch("debugpy.breakpoint")
def test_debugpy_setup(
    mock_breakpoint: MagicMock,
    mock_wait_for_client: MagicMock,
    mock_listen: MagicMock,
) -> None:
    """Test debugpy.setup configures breakpoint hook and waits for client."""
    debugpy.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debugpy.breakpoint"
    assert sys.breakpointhook == mock_breakpoint
    mock_listen.assert_called_once_with(
        (debugpy.DEFAULT_DEBUGPY_HOST, debugpy.DEFAULT_DEBUGPY_PORT)
    )
    mock_wait_for_client.assert_called_once()


def test_debugpy_setup_not_installed() -> None:
    """Test debugpy.setup falls back to dpdb when Debugpy is not importable."""
    with patch.dict("sys.modules", {"debugpy": None}):
        debugpy.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debug_dojo.adapters.dpdb.set_trace"


@patch("debug_dojo.adapters.dpdb.post_mortem")
def test_debugpy_post_mortem(mock_dpdb_pm: MagicMock) -> None:
    """Test debugpy.post_mortem delegates to internal dpdb.post_mortem."""
    debugpy.post_mortem(None)
    mock_dpdb_pm.assert_called_once_with(None)


@patch("debug_dojo.adapters.dpdb.setup")
def test_setup_debugger_none_without_env(
    mock_dpdb_setup: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test setup_debugger(None) calls dpdb.setup when PYTHONBREAKPOINT is unset."""
    monkeypatch.delenv(BREAKPOINT_ENV_VAR, raising=False)
    setup_debugger(None)
    mock_dpdb_setup.assert_called_once_with()


@patch("debug_dojo.adapters.dpdb.setup")
def test_setup_debugger_none_respects_existing_env(
    mock_dpdb_setup: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test setup_debugger(None) preserves existing PYTHONBREAKPOINT when set."""
    monkeypatch.setenv(BREAKPOINT_ENV_VAR, "custom.debugger.set_trace")
    setup_debugger(None)
    mock_dpdb_setup.assert_not_called()
    assert os.environ[BREAKPOINT_ENV_VAR] == "custom.debugger.set_trace"


@patch("debug_dojo.adapters.pdb.setup")
def test_setup_debugger_explicit(mock_pdb_setup: MagicMock) -> None:
    """Test setup_debugger dispatches to explicit adapter setup."""
    setup_debugger(DebuggerType.PDB)
    mock_pdb_setup.assert_called_once_with()


@patch("debug_dojo.adapters.dpdb.post_mortem")
def test_enter_post_mortem_default(mock_dpdb_pm: MagicMock) -> None:
    """Test enter_post_mortem defaults to dpdb.post_mortem."""
    enter_post_mortem(None, None)
    mock_dpdb_pm.assert_called_once_with(None)
