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

from ._compare import inspect_objects_side_by_side
from ._config_models import (
    DebugDojoConfig,
    DebuggersConfig,
    DebuggerType,
    DebugpyConfig,
    ExceptionsConfig,
    FeaturesConfig,
    IpdbConfig,
    PdbConfig,
    PudbConfig,
)

BREAKPOINT_ENV_VAR = "PYTHONBREAKPOINT"
IPDB_CONTEXT_SIZE = "IPDB_CONTEXT_SIZE"


def _use_pdb(config: PdbConfig) -> None:
    """Set PDB as the default debugger."""
    import pdb

    os.environ[BREAKPOINT_ENV_VAR] = config.set_trace_hook
    sys.breakpointhook = pdb.set_trace


def _use_pudb(config: PudbConfig) -> None:
    """Check if PuDB is available and set it as the default debugger."""
    import pudb  # pyright: ignore[reportMissingTypeStubs]

    os.environ[BREAKPOINT_ENV_VAR] = config.set_trace_hook
    sys.breakpointhook = pudb.set_trace


def _use_ipdb(config: IpdbConfig) -> None:
    """Set IPDB as the default debugger."""
    import ipdb  # pyright: ignore[reportMissingTypeStubs]

    os.environ[BREAKPOINT_ENV_VAR] = config.set_trace_hook
    os.environ[IPDB_CONTEXT_SIZE] = str(config.context_lines)
    sys.breakpointhook = ipdb.set_trace  # pyright: ignore[reportUnknownMemberType]


def _use_debugpy(config: DebugpyConfig) -> None:
    """Check if IPDB is available and set it as the default debugger."""
    import debugpy  # pyright: ignore[reportMissingTypeStubs]

    os.environ[BREAKPOINT_ENV_VAR] = config.set_trace_hook
    sys.breakpointhook = debugpy.breakpoint

    launch_config = {
        "name": "debug-dojo",
        "type": "debugpy",
        "request": "attach",
        "connect": {
            "host": config.host,
            "port": config.port,
        },
    }
    rich_print(f"[blue]Connect your VSC debugger to port {config.port}.[/blue]")
    rich_print("[blue]Configuration:[/blue]")
    rich_print(json.dumps(launch_config, indent=4))

    _ = debugpy.listen((config.host, config.port))
    debugpy.wait_for_client()


def _rich_traceback(*, locals_in_traceback: bool) -> None:
    """Check if Rich Traceback is available and set it as the default."""
    from rich import traceback

    _ = traceback.install(show_locals=locals_in_traceback)


def _inspect(mnemonic: str = "i") -> None:
    """Print the object using a custom inspect function."""
    from rich import inspect

    def inspect_with_defaults(obj: object, **kwargs: bool) -> None:
        """Inspect an object using Rich's inspect function."""
        if not kwargs:
            kwargs = {"methods": True, "private": True}
        return inspect(obj, console=None, title="", **kwargs)

    builtins.__dict__[mnemonic] = inspect_with_defaults


def _compare(mnemonic: str = "c") -> None:
    """Print the object using a custom inspect function.

    >>> _compare()
    >>> import builtins
    >>> callable(builtins.c)
    True

    """
    if not mnemonic:
        return

    builtins.__dict__[mnemonic] = inspect_objects_side_by_side


def _breakpoint(mnemonic: str = "b") -> None:
    """Install the breakpoint function.

    >>> _breakpoint()
    >>> import builtins
    >>> callable(builtins.b)
    True

    """
    if not mnemonic:
        return

    builtins.__dict__[mnemonic] = breakpoint


def _rich_print(mnemonic: str = "p") -> None:
    """Install the print from rich.

    >>> _rich_print()
    >>> import builtins
    >>> callable(builtins.p)
    True
    >>> p("test")
    test

    """
    if not mnemonic:
        return

    from rich import print as rich_print

    builtins.__dict__[mnemonic] = rich_print


def _install_features(features: FeaturesConfig) -> None:
    """Install the specified debugging features."""
    _inspect(features.rich_inspect)
    _rich_print(features.rich_print)
    _compare(features.comparer)
    _breakpoint(features.breakpoint)


def _set_debugger(config: DebuggersConfig) -> None:
    """Set the debugger based on the configuration."""
    debugger = config.default

    if debugger == DebuggerType.PDB:
        _use_pdb(config.pdb)
    if debugger == DebuggerType.PUDB:
        _use_pudb(config.pudb)
    if debugger == DebuggerType.IPDB:
        _use_ipdb(config.ipdb)
    if debugger == DebuggerType.DEBUGPY:
        _use_debugpy(config.debugpy)

    sys.ps1 = config.prompt_name


def _set_exceptions(exceptions: ExceptionsConfig) -> None:
    """Set the exception handling based on the configuration."""
    if exceptions.rich_traceback:
        _rich_traceback(locals_in_traceback=exceptions.locals_in_traceback)


def install_by_config(config: DebugDojoConfig) -> None:
    """Install debugging tools."""
    _set_debugger(config.debuggers)
    _set_exceptions(config.exceptions)
    _install_features(config.features)
