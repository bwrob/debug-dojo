"""Module for installing and configuring various debugging tools and features.

This module provides functions to set up different debuggers (PDB, PuDB, IPDB,
Debugpy) and to install enhanced debugging features like Rich Traceback, Rich
Inspect, Rich Print, and a side-by-side object comparer based on `DojoSettings`.
"""

from __future__ import annotations

import builtins
import json
import os
import sys
from typing import Any, cast

from rich import print as rich_print

from debug_dojo._compare import inspect_objects_side_by_side
from debug_dojo._config_models import (
    DebuggerType,
    DojoSettings,
)

BREAKPOINT_ENV_VAR = "PYTHONBREAKPOINT"
IPDB_CONTEXT_SIZE = "IPDB_CONTEXT_SIZE"

_NOT_INSTALLED = (
    "[yellow]{name} is not installed. "
    "Please install it to use this debugger. "
    "Defaulting to standard debugger.[/yellow]"
)


def use_pdb(hook: str = "pdb.set_trace") -> None:
    """Set PDB as the default debugger.

    Configures `sys.breakpointhook` to use `pdb.set_trace` and sets the
    `PYTHONBREAKPOINT` environment variable.

    Args:
        hook (str): The hook string for `PYTHONBREAKPOINT`.

    """
    import pdb

    os.environ[BREAKPOINT_ENV_VAR] = hook
    sys.breakpointhook = cast("Any", pdb.set_trace)


def use_pudb(hook: str = "pudb.set_trace") -> None:
    """Set PuDB as the default debugger.

    Configures `sys.breakpointhook` to use `pudb.set_trace` and sets the
    `PYTHONBREAKPOINT` environment variable.

    Args:
        hook (str): The hook string for `PYTHONBREAKPOINT`.

    """
    try:
        import pudb
    except ImportError:
        rich_print(_NOT_INSTALLED.format(name="PuDB"))
        return

    os.environ[BREAKPOINT_ENV_VAR] = hook
    sys.breakpointhook = cast("Any", pudb.set_trace)


def use_ipdb(hook: str = "ipdb.set_trace", context_lines: int = 20) -> None:
    """Set IPDB as the default debugger.

    Configures `sys.breakpointhook` to use `ipdb.set_trace`, sets the
    `PYTHONBREAKPOINT` environment variable, and configures `IPDB_CONTEXT_SIZE`.

    Args:
        hook (str): The hook string for `PYTHONBREAKPOINT`.
        context_lines (int): Number of source code context lines to show.

    """
    try:
        import ipdb
    except ImportError:
        rich_print(_NOT_INSTALLED.format(name="IPDB"))
        return

    os.environ[BREAKPOINT_ENV_VAR] = hook
    os.environ[IPDB_CONTEXT_SIZE] = str(context_lines)
    sys.breakpointhook = cast("Any", ipdb.set_trace)


def use_debugpy(
    hook: str = "debugpy.breakpoint",
    host: str = "localhost",
    port: int = 1992,
    *,
    wait_for_client: bool = True,
) -> None:
    """Set Debugpy as the default debugger.

    Configures `sys.breakpointhook` to use `debugpy.breakpoint`, sets the
    `PYTHONBREAKPOINT` environment variable, and starts a debugpy server
    waiting for a client connection.

    Args:
        hook (str): The hook string for `PYTHONBREAKPOINT`.
        host (str): Host address to bind debugpy server.
        port (int): Port number to bind debugpy server.
        wait_for_client (bool): Whether to wait for client connection.

    """
    try:
        import debugpy
    except ImportError:
        rich_print(_NOT_INSTALLED.format(name="Debugpy"))
        return

    os.environ[BREAKPOINT_ENV_VAR] = hook
    sys.breakpointhook = debugpy.breakpoint

    launch_config = {
        "name": "debug-dojo",
        "type": "debugpy",
        "request": "attach",
        "connect": {
            "host": host,
            "port": port,
        },
    }
    rich_print(f"[blue]Connect your VSC debugger to port {port}.[/blue]")
    rich_print("[blue]Configuration:[/blue]")
    rich_print(json.dumps(launch_config, indent=4))

    _ = debugpy.listen((host, port))
    if wait_for_client:
        debugpy.wait_for_client()


def rich_traceback(*, locals_in_traceback: bool) -> None:
    """Install Rich Traceback for enhanced error reporting.

    Args:
        locals_in_traceback (bool): Whether to include local variables in the traceback.

    """
    from rich import traceback

    _ = traceback.install(show_locals=locals_in_traceback)


def install_inspect(mnemonic: str = "i") -> None:
    """Inject `rich.inspect` into builtins under the given mnemonic.

    Args:
        mnemonic (str): The name to use for the inspect function in builtins.
            If an empty string, the feature is not installed.

    """
    if not mnemonic:
        return

    from rich import inspect

    def inspect_with_defaults(obj: object, **kwargs: bool) -> None:
        """Inspect an object using Rich's inspect function."""
        if not kwargs:
            kwargs = {"methods": True, "private": True}
        return inspect(obj, console=None, title="", **kwargs)

    builtins.__dict__[mnemonic] = inspect_with_defaults


def install_compare(mnemonic: str = "c") -> None:
    """Inject the side-by-side object comparison function into builtins.

    Args:
        mnemonic (str): The name to use for the compare function in builtins.
            If an empty string, the feature is not installed.

    >>> install_compare()
    >>> import builtins
    >>> callable(builtins.c)
    True

    """
    if not mnemonic:
        return

    builtins.__dict__[mnemonic] = inspect_objects_side_by_side


def install_breakpoint(mnemonic: str = "b") -> None:
    """Inject the `breakpoint()` function into builtins under the given mnemonic.

    Args:
        mnemonic (str): The name to use for the breakpoint function in builtins.
            If an empty string, the feature is not installed.

    >>> install_breakpoint()
    >>> import builtins
    >>> callable(builtins.b)
    True

    """
    if not mnemonic:
        return

    builtins.__dict__[mnemonic] = breakpoint


def install_rich_print(mnemonic: str = "p") -> None:
    """Inject `rich.print` into builtins under the given mnemonic.

    Args:
        mnemonic (str): The name to use for the print function in builtins.
            If an empty string, the feature is not installed.

    >>> install_rich_print()
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


def install_features(settings: DojoSettings) -> None:
    """Install debugging features based on the provided settings.

    Args:
        settings (DojoSettings): Settings specifying mnemonics for injected helpers.

    """
    install_inspect(settings.inspect_mnemonic)
    install_rich_print(settings.print_mnemonic)
    install_compare(settings.compare_mnemonic)
    install_breakpoint(settings.breakpoint_mnemonic)


def set_debugger(settings: DojoSettings) -> None:
    """Set the default debugger based on the provided settings.

    Args:
        settings (DojoSettings): Configuration settings for debuggers.

    """
    debugger = settings.debugger

    if debugger is DebuggerType.PDB:
        use_pdb(settings.debugger.set_trace_hook)
    elif debugger is DebuggerType.PUDB:
        use_pudb(settings.debugger.set_trace_hook)
    elif debugger is DebuggerType.IPDB:
        use_ipdb(settings.debugger.set_trace_hook, settings.ipdb_context_lines)
    else:
        use_debugpy(
            settings.debugger.set_trace_hook,
            settings.debugpy_host,
            settings.debugpy_port,
            wait_for_client=settings.debugpy_wait_for_client,
        )

    sys.ps1 = settings.prompt_name


def set_exceptions(settings: DojoSettings) -> None:
    """Configure exception handling based on the provided settings.

    Args:
        settings (DojoSettings): Configuration settings for exception handling.

    """
    if settings.rich_traceback:
        rich_traceback(locals_in_traceback=settings.show_locals)


def install_tools(settings: DojoSettings) -> None:
    """Install all debugging tools and features based on the given settings.

    Args:
        settings (DojoSettings): The runtime settings object.

    """
    set_debugger(settings)
    set_exceptions(settings)
    install_features(settings)


install_by_config = install_tools
