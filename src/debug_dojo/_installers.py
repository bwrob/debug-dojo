"""Debugging tools for Python.

This module provides functions to set up debugging tools like PuDB and Rich Traceback.
It checks for the availability of these tools and configures them accordingly.
"""

from __future__ import annotations

import builtins
import os
import sys

from ._compareres import inspect_objects_side_by_side
from ._config import DebugDojoConfig, DebuggerType, Features

BREAKPOINT_ENV_VAR = "PYTHONBREAKPOINT"
PUDB_SET_TRACE = "pudb.set_trace"
PDB_SET_TRACE_ALT = "pdb.set_trace"


def _use_pdb() -> None:
    """Check if PuDB is available and set it as the default debugger."""
    import pdb

    # Set the environment variable. This will primarily affect child processes or later
    # Python startup if the script is re-run.
    os.environ[BREAKPOINT_ENV_VAR] = PDB_SET_TRACE_ALT

    # Crucially, to make `breakpoint()` work *immediately* in the current process,
    # we need to explicitly set `sys.breakpointhook`.
    sys.breakpointhook = pdb.set_trace


def _use_pudb() -> None:
    """Check if PuDB is available and set it as the default debugger."""
    import pudb  # pyright: ignore[reportMissingTypeStubs]

    # Set the environment variable. This will primarily affect child processes or later
    # Python startup if the script is re-run.
    os.environ[BREAKPOINT_ENV_VAR] = PUDB_SET_TRACE

    # Crucially, to make `breakpoint()` work *immediately* in the current process,
    # we need to explicitly set `sys.breakpointhook`.
    sys.breakpointhook = pudb.set_trace


def _rich_traceback() -> None:
    """Check if Rich Traceback is available and set it as the default."""
    from rich import traceback

    # Install rich traceback to enhance the debugging experience
    _ = traceback.install(show_locals=True)


def _inspect() -> None:
    """Print the object using a custom inspect function."""
    from rich import inspect

    def inspect_with_defaults(obj: object, **kwargs: object) -> None:
        """Inspect an object using Rich's inspect function."""
        if not kwargs:
            kwargs = {"methods": True, "private": True}
        return inspect(obj, **kwargs)  # pyright: ignore[reportArgumentType]

    # Inject the custom inspect function into builtins
    builtins.i = inspect_with_defaults  # pyright: ignore[reportAttributeAccessIssue]


def _compare() -> None:
    """Print the object using a custom inspect function."""
    # Inject the custom side-by-side comparison function into builtins
    builtins.c = inspect_objects_side_by_side  # pyright: ignore[reportAttributeAccessIssue]


def _breakpoint() -> None:
    """Install the breakpoint function."""
    # Set the breakpoint function to use PuDB's set_trace
    builtins.b = breakpoint  # pyright: ignore[reportAttributeAccessIssue]


def _rich_print() -> None:
    """Install the print from rich."""
    from rich import print as rich_print

    builtins.p = rich_print  # pyright: ignore[reportAttributeAccessIssue]


def _install_features(features: Features) -> None:
    """Install the specified debugging features."""
    if features.rich_inspect:
        _inspect()
    if features.rich_print:
        _rich_print()
    if features.rich_traceback:
        _rich_traceback()
    if features.comparer:
        _compare()
    if features.breakpoint:
        _breakpoint()


def _set_debugger(debugger: DebuggerType) -> None:
    """Set the debugger based on the configuration."""
    if debugger is DebuggerType.PDB:
        # PDB is the default, no special setup needed
        return _use_pdb()
    if debugger is DebuggerType.PUDB:
        return _use_pudb()
    return None


def install_by_config(config: DebugDojoConfig) -> None:
    """Install debugging tools."""
    _set_debugger(config.debugger)
    _install_features(config.features)
