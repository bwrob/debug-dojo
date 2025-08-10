"""Debugging tools for Python.

This module provides functions to set up debugging tools like PuDB and Rich Traceback.
It checks for the availability of these tools and configures them accordingly.
"""

from __future__ import annotations

import builtins
import json
import os
import sys

from rich import print as rich_print

from ._compareres import inspect_objects_side_by_side
from ._config_models import (
    DebugDojoConfig,
    DebuggersConfig,
    DebuggerType,
    ExceptionsConfig,
    FeaturesConfig,
)

BREAKPOINT_ENV_VAR = "PYTHONBREAKPOINT"


def _use_pdb() -> None:
    """Set PDB as the default debugger."""
    import pdb

    os.environ[BREAKPOINT_ENV_VAR] = "pdb.set_trace"
    sys.breakpointhook = pdb.set_trace


def _use_pudb() -> None:
    """Check if PuDB is available and set it as the default debugger."""
    import pudb  # pyright: ignore[reportMissingTypeStubs]

    os.environ[BREAKPOINT_ENV_VAR] = "pudb.set_trace"
    sys.breakpointhook = pudb.set_trace


def _use_ipdb() -> None:
    """Set IPDB as the default debugger."""
    import ipdb  # pyright: ignore[reportMissingTypeStubs]

    os.environ[BREAKPOINT_ENV_VAR] = "ipdb.set_trace"
    os.environ["IPDB_CONTEXT_SIZE"] = "20"
    sys.breakpointhook = ipdb.set_trace  # pyright: ignore[reportUnknownMemberType]


def _use_debugpy() -> None:
    """Check if IPDB is available and set it as the default debugger."""
    import debugpy  # pyright: ignore[reportMissingTypeStubs]

    os.environ[BREAKPOINT_ENV_VAR] = "debugpy.breakpoint"
    sys.breakpointhook = debugpy.breakpoint

    port = 6969
    _ = debugpy.listen(("localhost", port))

    config = {
        "name": "debug-dojo",
        "type": "debugpy",
        "request": "attach",
        "connect": {"port": port},
    }
    rich_print(
        f"[blue]Debugging via Debugpy. Connect your VSC debugger to port {port}.[/blue]"
    )
    rich_print("[blue]Configuration:[/blue]")
    rich_print(json.dumps(config, indent=4))

    debugpy.wait_for_client()


def _rich_traceback(*, locals_in_traceback: bool) -> None:
    """Check if Rich Traceback is available and set it as the default."""
    from rich import traceback

    _ = traceback.install(show_locals=locals_in_traceback)


def _inspect() -> None:
    """Print the object using a custom inspect function."""
    from rich import inspect

    def inspect_with_defaults(obj: object, **kwargs: object) -> None:
        """Inspect an object using Rich's inspect function."""
        if not kwargs:
            kwargs = {"methods": True, "private": True}
        return inspect(obj, **kwargs)  # pyright: ignore[reportArgumentType]

    builtins.i = inspect_with_defaults  # pyright: ignore[reportAttributeAccessIssue]


def _compare() -> None:
    """Print the object using a custom inspect function."""
    builtins.c = inspect_objects_side_by_side  # pyright: ignore[reportAttributeAccessIssue]


def _breakpoint() -> None:
    """Install the breakpoint function."""
    builtins.b = breakpoint  # pyright: ignore[reportAttributeAccessIssue]


def _rich_print() -> None:
    """Install the print from rich."""
    from rich import print as rich_print

    builtins.p = rich_print  # pyright: ignore[reportAttributeAccessIssue]


def _install_features(features: FeaturesConfig) -> None:
    """Install the specified debugging features."""
    if features.rich_inspect:
        _inspect()
    if features.rich_print:
        _rich_print()
    if features.comparer:
        _compare()
    if features.breakpoint:
        _breakpoint()


def _set_debugger(debugger_config: DebuggersConfig) -> None:
    """Set the debugger based on the configuration."""
    debugger = debugger_config.default

    if debugger == DebuggerType.PDB:
        _use_pdb()
    if debugger == DebuggerType.PUDB:
        _use_pudb()
    if debugger == DebuggerType.IPDB:
        _use_ipdb()
    if debugger == DebuggerType.DEBUGPY:
        _use_debugpy()

    sys.ps1 = debugger_config.prompt_name


def _set_exceptions(exceptions: ExceptionsConfig) -> None:
    """Set the exception handling based on the configuration."""
    if exceptions.rich_traceback:
        _rich_traceback(locals_in_traceback=exceptions.locals_in_traceback)


def install_by_config(config: DebugDojoConfig) -> None:
    """Install debugging tools."""
    _set_debugger(config.debuggers)
    _set_exceptions(config.exceptions)
    _install_features(config.features)
