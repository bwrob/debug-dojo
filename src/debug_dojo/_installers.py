"""Module for installing and configuring various debugging tools and features.

This module provides functions to set up different debuggers (PDB, PuDB, IPDB,
Debugpy) and to install enhanced debugging features like Rich Traceback, Rich
Inspect, Rich Print, and a side-by-side object comparer. These installations
are typically driven by the `DebugDojoConfig`.
"""

from __future__ import annotations

import builtins
import json
import os
import sys

from rich import print as rich_print

from debug_dojo._compare import inspect_objects_side_by_side
from debug_dojo._config_models import (
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

_NOT_INSTALLED = (
    "[yellow]{name} is not installed."
    "Please install it to use this debugger."
    "Defaulting to standard debugger.[/yellow]"
)


def use_pdb(config: PdbConfig) -> None:
    """Set PDB as the default debugger.

    Configures `sys.breakpointhook` to use `pdb.set_trace` and sets the
    `PYTHONBREAKPOINT` environment variable.
    """
    import pdb

    os.environ[BREAKPOINT_ENV_VAR] = config.set_trace_hook
    sys.breakpointhook = pdb.set_trace


def use_pudb(config: PudbConfig) -> None:
    """Set PuDB as the default debugger.

    Configures `sys.breakpointhook` to use `pudb.set_trace` and sets the
    `PYTHONBREAKPOINT` environment variable.
    """
    try:
        import pudb  # pyright: ignore[reportMissingTypeStubs]
    except ImportError:
        rich_print(_NOT_INSTALLED.format(name="PuDB"))
        return

    os.environ[BREAKPOINT_ENV_VAR] = config.set_trace_hook
    sys.breakpointhook = pudb.set_trace


def use_ipdb(config: IpdbConfig) -> None:
    """Set IPDB as the default debugger.

    Configures `sys.breakpointhook` to use `ipdb.set_trace`, sets the
    `PYTHONBREAKPOINT` environment variable, and configures `IPDB_CONTEXT_SIZE`.
    """
    try:
        import ipdb  # pyright: ignore[reportMissingTypeStubs]
    except ImportError:
        rich_print(_NOT_INSTALLED.format(name="IPDB"))
        return

    os.environ[BREAKPOINT_ENV_VAR] = config.set_trace_hook
    os.environ[IPDB_CONTEXT_SIZE] = str(config.context_lines)
    sys.breakpointhook = ipdb.set_trace  # pyright: ignore[reportUnknownMemberType]


def use_debugpy(config: DebugpyConfig) -> None:
    """Set Debugpy as the default debugger.

    Configures `sys.breakpointhook` to use `debugpy.breakpoint`, sets the
    `PYTHONBREAKPOINT` environment variable, and starts a debugpy server
    waiting for a client connection.
    """
    try:
        import debugpy
    except ImportError:
        rich_print(_NOT_INSTALLED.format(name="Debugpy"))
        return

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


def rich_traceback(*, locals_in_traceback: bool) -> None:
    """Install Rich Traceback for enhanced error reporting.

    Args:
        locals_in_traceback (bool): Whether to include local variables in the traceback.

    """
    from rich import traceback

    _ = traceback.install(show_locals=locals_in_traceback)


def install_inspect(mnemonic: str = "i") -> None:
    """Injects `rich.inspect` into builtins under the given mnemonic.

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
    """Injects the side-by-side object comparison function into builtins.

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
    """Inject the`breakpoint()` function into builtins under the given mnemonic.

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
    """Injects `rich.print` into builtins under the given mnemonic.

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


def install_features(features: FeaturesConfig) -> None:
    """Installs debugging features based on the provided configuration.

    Args:
        features (FeaturesConfig): Configuration object specifying which features
                                   to install and their mnemonics.

    """
    install_inspect(features.rich_inspect)
    install_rich_print(features.rich_print)
    install_compare(features.comparer)
    install_breakpoint(features.breakpoint)


def set_debugger(config: DebuggersConfig) -> None:
    """Set the default debugger based on the provided configuration.

    Args:
        config (DebuggersConfig): Configuration object for debuggers.

    """
    debugger = config.default

    if debugger == DebuggerType.PDB:
        use_pdb(config.pdb)
    if debugger == DebuggerType.PUDB:
        use_pudb(config.pudb)
    if debugger == DebuggerType.IPDB:
        use_ipdb(config.ipdb)
    if debugger == DebuggerType.DEBUGPY:
        use_debugpy(config.debugpy)

    sys.ps1 = config.prompt_name


def set_exceptions(exceptions: ExceptionsConfig) -> None:
    """Configure exception handling based on the provided configuration.

    Args:
        exceptions (ExceptionsConfig): Configuration object for exception handling.

    """
    if exceptions.rich_traceback:
        rich_traceback(locals_in_traceback=exceptions.locals_in_traceback)


def install_by_config(config: DebugDojoConfig) -> None:
    """Installs all debugging tools and features based on the given configuration.

    This is the main entry point for applying `debug-dojo` settings.

    Args:
        config (DebugDojoConfig): The complete debug-dojo configuration object.

    """
    set_debugger(config.debuggers)
    set_exceptions(config.exceptions)
    install_features(config.features)
