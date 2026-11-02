"""Internal IPython-powered debugger adapter (`dpdb`)."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any, cast

from IPython.core.debugger import BdbQuit_excepthook, Pdb
from IPython.core.getipython import get_ipython
from IPython.terminal.ipapp import TerminalIPythonApp

from debug_dojo.adapters._base import BREAKPOINT_ENV_VAR, DebuggerType

if TYPE_CHECKING:
    from types import FrameType, TracebackType

DEFAULT_CONTEXT_LINES = 20


def _get_debugger_cls() -> type[Pdb]:
    """Return the IPython debugger class for the active or newly initialized shell.

    Returns:
        type[Pdb]: The debugger class provided by the active IPython shell.

    """
    shell = get_ipython()
    if shell is None:
        ipapp = TerminalIPythonApp()
        ipapp.interact = False
        ipapp.initialize(["--no-term-title"])
        shell = ipapp.shell

    if shell is None:
        return Pdb
    return cast("type[Pdb]", shell.debugger_cls)


def _init_pdb() -> Pdb:
    """Initialize and return an IPython Pdb instance.

    Returns:
        Pdb: Configured IPython Pdb debugger instance.

    """
    debugger_cls = _get_debugger_cls()
    return debugger_cls(context=DEFAULT_CONTEXT_LINES)


def wrap_sys_excepthook() -> None:
    """Wrap `sys.excepthook` with `BdbQuit_excepthook` once."""
    if sys.excepthook != BdbQuit_excepthook:
        BdbQuit_excepthook.excepthook_ori = sys.excepthook  # pyrefly: ignore[missing-attribute]
        sys.excepthook = BdbQuit_excepthook


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
    pdb_instance.set_trace(target_frame)
    shell = getattr(pdb_instance, "shell", None)
    if shell is not None and hasattr(shell, "restore_sys_module_state"):
        shell.restore_sys_module_state()


def setup() -> None:
    """Set internal DPDB as the active debugger."""
    wrap_sys_excepthook()
    os.environ[BREAKPOINT_ENV_VAR] = DebuggerType.DPDB.set_trace_hook
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
        pdb_instance.interaction(None, target_tb)
