"""Session lifecycle, excepthook handling, and debugger entrypoint functions."""

from __future__ import annotations

import bdb
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from IPython.core.debugger import Pdb
from IPython.core.getipython import get_ipython
from IPython.terminal.ipapp import TerminalIPythonApp
from rich.console import Console

from debug_dojo._core.debugger.breakpoints import _apply_break_spec
from debug_dojo._core.debugger.debugger import DojoPdb
from debug_dojo._core.debugger.views import (
    DEFAULT_CONTEXT_LINES,
    _render_post_mortem_banner,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from types import FrameType, TracebackType

BREAKPOINT_ENV_VAR = "PYTHONBREAKPOINT"
DPDB_SET_TRACE_HOOK = "debug_dojo.set_trace"


def _get_debugger_cls() -> type[Pdb]:
    """Return the `DojoPdb` debugger class after ensuring an active IPython shell.

    Returns:
        type[Pdb]: The `DojoPdb` class (or fallback `Pdb` if shell creation fails).

    """
    shell = get_ipython()
    if shell is None:
        ipapp = TerminalIPythonApp()
        ipapp.interact = False
        ipapp.initialize(["--no-term-title", "--InteractiveShell.warn_venv=False"])
        shell = ipapp.shell

    if shell is None:
        return Pdb
    return DojoPdb


def _init_pdb() -> Pdb:
    """Initialize and return an IPython Pdb instance.

    Returns:
        Pdb: Configured IPython Pdb debugger instance.

    """
    debugger_cls = _get_debugger_cls()
    return debugger_cls(context=DEFAULT_CONTEXT_LINES)


def _bdb_quit_excepthook(
    exc_type: type[BaseException],
    exc_val: BaseException,
    exc_tb: TracebackType | None,
) -> None:
    """Suppress `bdb.BdbQuit` at top level and forward all other exceptions.

    Args:
        exc_type (type[BaseException]): Exception class.
        exc_val (BaseException): Exception instance.
        exc_tb (TracebackType | None): Exception traceback.

    """
    if issubclass(exc_type, bdb.BdbQuit):
        return
    orig = getattr(_bdb_quit_excepthook, "excepthook_ori", sys.__excepthook__)
    orig(exc_type, exc_val, exc_tb)


def wrap_sys_excepthook() -> None:
    """Wrap `sys.excepthook` with `_bdb_quit_excepthook` once."""
    if sys.excepthook is not _bdb_quit_excepthook:
        _bdb_quit_excepthook.excepthook_ori = sys.excepthook  # pyrefly: ignore[missing-attribute]
        sys.excepthook = _bdb_quit_excepthook


def set_trace(frame: FrameType | None = None) -> None:
    """Enter the internal DPDB debugger at the given or calling stack frame.

    Args:
        frame (FrameType | None): Target stack frame. Defaults to the caller's frame.

    """
    wrap_sys_excepthook()
    target_frame = (
        sys._getframe().f_back  # ruff: ignore[private-member-access] -- sys._getframe is required to resolve the caller stack frame
        if frame is None
        else frame
    )
    pdb_instance = _init_pdb()
    shell = getattr(pdb_instance, "shell", None)
    if shell is not None and hasattr(shell, "restore_sys_module_state"):
        shell.restore_sys_module_state()
    pdb_instance.set_trace(target_frame)


def setup() -> None:
    """Set internal DPDB as the active debugger."""
    wrap_sys_excepthook()
    os.environ[BREAKPOINT_ENV_VAR] = DPDB_SET_TRACE_HOOK
    sys.breakpointhook = cast("Any", set_trace)


def post_mortem(tb: TracebackType | None = None) -> None:
    """Enter post-mortem debugging on the given or active exception traceback.

    Args:
        tb (TracebackType | None): Traceback to inspect (defaults to active exc_info).

    """
    wrap_sys_excepthook()
    pdb_instance = _init_pdb()
    pdb_instance.reset()
    target_tb = sys.exc_info()[2] if tb is None else tb
    if target_tb is not None:
        console = (
            pdb_instance._console()  # ruff: ignore[private-member-access] -- _console is internal to DojoPdb in this package
            if isinstance(pdb_instance, DojoPdb)
            else Console(file=getattr(pdb_instance, "stdout", sys.stdout))
        )
        _render_post_mortem_banner(target_tb, console)
        pdb_instance.interaction(None, target_tb)


def pm() -> None:
    """Enter `dpdb` post-mortem debugging on the last unhandled exception."""
    last_exc = getattr(sys, "last_exc", None)
    tb = (
        last_exc.__traceback__
        if isinstance(last_exc, BaseException)
        else getattr(sys, "last_traceback", None)
    )
    post_mortem(tb)


def seed_cli_breakpoints(target_file: str, breaks: Sequence[str]) -> None:
    """Register CLI-supplied breakpoints before target execution.

    Args:
        target_file (str): Path to the resolved target script.
        breaks (Sequence[str]): Breakpoint specifications (`line`, `file:line`, `func`).

    """
    pdb_instance = _init_pdb()
    resolved_default = str(Path(target_file).resolve())
    for spec in breaks:
        _apply_break_spec(pdb_instance, resolved_default, spec)


def run_with_active_breakpoints(call: Callable[[], object]) -> None:
    """Execute `call` under `dpdb` trace dispatch so active breakpoints fire.

    Args:
        call (Callable[[], object]): Zero-argument callable executing the target.

    """
    wrap_sys_excepthook()
    pdb_instance = _init_pdb()
    shell = getattr(pdb_instance, "shell", None)
    if shell is not None and hasattr(shell, "restore_sys_module_state"):
        shell.restore_sys_module_state()
    pdb_instance.reset()
    caller_frame = sys._getframe()  # ruff: ignore[private-member-access] -- anchor botframe to runner frame
    pdb_instance.botframe = caller_frame
    pdb_instance.set_continue()
    prev_trace = sys.gettrace()
    sys.settrace(pdb_instance.trace_dispatch)
    try:
        _ = call()
    finally:
        pdb_instance.quitting = True
        sys.settrace(prev_trace)
