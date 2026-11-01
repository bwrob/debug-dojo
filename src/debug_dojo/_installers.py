"""Module for installing opinionated debugging tools and features.

This module provides functions to set up debuggers (PDB, PuDB, IPDB, Debugpy)
and to install opinionated debugging features into Python's builtins: Rich
Traceback, Rich Inspect (`i`), Rich Print (`p`), side-by-side object comparer
(`c`), and breakpoint shortcut (`b`).
"""

from __future__ import annotations

import builtins
import json
import os
import sys
from enum import StrEnum
from typing import Any, cast

from rich import print as rich_print

from debug_dojo._compare import inspect_objects_side_by_side

BREAKPOINT_ENV_VAR = "PYTHONBREAKPOINT"
IPDB_CONTEXT_SIZE = "IPDB_CONTEXT_SIZE"
DEFAULT_IPDB_CONTEXT_LINES = "20"
DEFAULT_DEBUGPY_HOST = "localhost"
DEFAULT_DEBUGPY_PORT = 1992
DEFAULT_PROMPT = "debug-dojo> "

_NOT_INSTALLED = (
    "[yellow]{name} is not installed. "
    "Please install it to use this debugger. "
    "Defaulting to standard debugger.[/yellow]"
)


class DebuggerType(StrEnum):
    """Supported debugger backends."""

    DEBUGPY = "debugpy"
    IPDB = "ipdb"
    PDB = "pdb"
    PUDB = "pudb"

    @property
    def set_trace_hook(self) -> str:
        """Module-level hook string for PYTHONBREAKPOINT."""
        if self is DebuggerType.DEBUGPY:
            return "debugpy.breakpoint"
        return f"{self.value}.set_trace"


def use_pdb() -> None:
    """Set PDB as the active debugger.

    Configures `sys.breakpointhook` to use `pdb.set_trace` and sets the
    `PYTHONBREAKPOINT` environment variable.
    """
    import pdb

    os.environ[BREAKPOINT_ENV_VAR] = DebuggerType.PDB.set_trace_hook
    sys.breakpointhook = cast("Any", pdb.set_trace)


def use_pudb() -> None:
    """Set PuDB as the active debugger.

    Configures `sys.breakpointhook` to use `pudb.set_trace` and sets the
    `PYTHONBREAKPOINT` environment variable.
    """
    try:
        import pudb
    except ImportError:
        rich_print(_NOT_INSTALLED.format(name="PuDB"))
        return

    os.environ[BREAKPOINT_ENV_VAR] = DebuggerType.PUDB.set_trace_hook
    sys.breakpointhook = cast("Any", pudb.set_trace)


def use_ipdb() -> None:
    """Set IPDB as the active debugger.

    Configures `sys.breakpointhook` to use `ipdb.set_trace`, sets the
    `PYTHONBREAKPOINT` environment variable, and configures `IPDB_CONTEXT_SIZE`.
    """
    try:
        import ipdb
    except ImportError:
        rich_print(_NOT_INSTALLED.format(name="IPDB"))
        return

    os.environ[BREAKPOINT_ENV_VAR] = DebuggerType.IPDB.set_trace_hook
    os.environ[IPDB_CONTEXT_SIZE] = DEFAULT_IPDB_CONTEXT_LINES
    sys.breakpointhook = cast("Any", ipdb.set_trace)


def use_debugpy() -> None:
    """Set Debugpy as the active debugger.

    Configures `sys.breakpointhook` to use `debugpy.breakpoint`, sets the
    `PYTHONBREAKPOINT` environment variable, and starts a debugpy server
    waiting for a client connection on `localhost:1992`.
    """
    try:
        import debugpy
    except ImportError:
        rich_print(_NOT_INSTALLED.format(name="Debugpy"))
        return

    os.environ[BREAKPOINT_ENV_VAR] = DebuggerType.DEBUGPY.set_trace_hook
    sys.breakpointhook = debugpy.breakpoint

    launch_config = {
        "name": "debug-dojo",
        "type": "debugpy",
        "request": "attach",
        "connect": {
            "host": DEFAULT_DEBUGPY_HOST,
            "port": DEFAULT_DEBUGPY_PORT,
        },
    }
    rich_print(
        f"[blue]Connect your VSC debugger to port {DEFAULT_DEBUGPY_PORT}.[/blue]"
    )
    rich_print("[blue]Configuration:[/blue]")
    rich_print(json.dumps(launch_config, indent=4))

    _ = debugpy.listen((DEFAULT_DEBUGPY_HOST, DEFAULT_DEBUGPY_PORT))
    debugpy.wait_for_client()


def rich_traceback() -> None:
    """Install Rich Traceback for enhanced error reporting."""
    from rich import traceback

    _ = traceback.install(show_locals=False)


def install_inspect() -> None:
    """Inject `rich.inspect` into builtins under `i`."""
    from rich import inspect

    def inspect_with_defaults(obj: object, **kwargs: bool) -> None:
        """Inspect an object using Rich's inspect function."""
        if not kwargs:
            kwargs = {"methods": True, "private": True}
        return inspect(obj, console=None, title="", **kwargs)

    builtins.__dict__["i"] = inspect_with_defaults


def install_compare() -> None:
    """Inject the side-by-side object comparison function into builtins under `c`.

    >>> install_compare()
    >>> import builtins
    >>> callable(builtins.c)
    True

    """
    builtins.__dict__["c"] = inspect_objects_side_by_side


def install_breakpoint() -> None:
    """Inject the `breakpoint()` function into builtins under `b`.

    >>> install_breakpoint()
    >>> import builtins
    >>> callable(builtins.b)
    True

    """
    builtins.__dict__["b"] = breakpoint


def install_rich_print() -> None:
    """Inject `rich.print` into builtins under `p`.

    >>> install_rich_print()
    >>> import builtins
    >>> callable(builtins.p)
    True
    >>> p("test")
    test

    """
    from rich import print as rich_print

    builtins.__dict__["p"] = rich_print


def install_features() -> None:
    """Install opinionated debugging helpers (`i`, `p`, `c`, `b`) into builtins."""
    install_inspect()
    install_rich_print()
    install_compare()
    install_breakpoint()


def set_debugger(debugger: DebuggerType | None = None) -> None:
    """Configure the debugger backend if specified.

    Args:
        debugger (DebuggerType | None): Optional debugger backend override.

    """
    if debugger is DebuggerType.PDB:
        use_pdb()
    elif debugger is DebuggerType.PUDB:
        use_pudb()
    elif debugger is DebuggerType.IPDB:
        use_ipdb()
    elif debugger is DebuggerType.DEBUGPY:
        use_debugpy()

    sys.ps1 = DEFAULT_PROMPT


def install_tools(debugger: DebuggerType | None = None) -> None:
    """Install all opinionated debugging tools and features.

    Args:
        debugger (DebuggerType | None): Optional debugger backend override.

    """
    set_debugger(debugger)
    rich_traceback()
    install_features()
