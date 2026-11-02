"""Dispatcher and protocol definitions for debugger adapters."""

from __future__ import annotations

import os
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from rich import print as rich_print

if TYPE_CHECKING:
    from types import TracebackType

BREAKPOINT_ENV_VAR = "PYTHONBREAKPOINT"


class DebuggerType(StrEnum):
    """Supported debugger backends."""

    DEBUGPY = "debugpy"
    DPDB = "dpdb"
    IPDB = "ipdb"
    PDB = "pdb"
    PUDB = "pudb"

    @property
    def set_trace_hook(self) -> str:
        """Module-level hook string for PYTHONBREAKPOINT."""
        if self is DebuggerType.DEBUGPY:
            return "debugpy.breakpoint"
        if self is DebuggerType.DPDB:
            return "debug_dojo.adapters.dpdb.set_trace"
        return f"{self.value}.set_trace"


class DebuggerAdapter(Protocol):
    """Protocol for debugger backend adapters."""

    def setup(self) -> None:
        """Configure the debugger backend and breakpoint hooks."""
        ...

    def post_mortem(self, tb: TracebackType | None = None) -> None:
        """Start a post-mortem debugging session for the given traceback."""
        ...


def get_adapter(debugger: DebuggerType | None = None) -> DebuggerAdapter:
    """Return the adapter corresponding to the given debugger type.

    Args:
        debugger (DebuggerType | None): Requested debugger backend. Defaults to DPDB.

    Returns:
        DebuggerAdapter: The resolved debugger adapter module.

    """
    from debug_dojo.adapters import debugpy, dpdb, ipdb, pdb, pudb

    if debugger is None:
        return dpdb
    adapters: dict[DebuggerType, DebuggerAdapter] = {
        DebuggerType.DEBUGPY: debugpy,
        DebuggerType.DPDB: dpdb,
        DebuggerType.IPDB: ipdb,
        DebuggerType.PDB: pdb,
        DebuggerType.PUDB: pudb,
    }
    return adapters[debugger]


def setup_debugger(debugger: DebuggerType | None = None) -> None:
    """Configure the requested debugger backend or default to internal DPDB.

    When `debugger` is `None` and `PYTHONBREAKPOINT` is not set in the
    environment, defaults to the internal `dpdb` adapter.

    Args:
        debugger (DebuggerType | None): Optional debugger backend override.

    """
    if debugger is not None:
        get_adapter(debugger).setup()
    elif not os.environ.get(BREAKPOINT_ENV_VAR):
        get_adapter(DebuggerType.DPDB).setup()


def enter_post_mortem(
    tb: TracebackType | None = None,
    debugger: DebuggerType | None = None,
) -> None:
    """Enter a post-mortem debugging session using the appropriate adapter.

    Args:
        tb (TracebackType | None): The traceback object from the unhandled exception.
        debugger (DebuggerType | None): The selected debugger type.

    """
    rich_print("[blue]Entering post-mortem debugging session...[/blue]")
    get_adapter(debugger).post_mortem(tb)
