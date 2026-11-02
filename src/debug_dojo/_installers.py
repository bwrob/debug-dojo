"""Module for installing opinionated debugging tools and features.

This module installs opinionated debugging features into Python's builtins:
Rich Traceback, Rich Inspect (`i`), Rich Print (`p`), side-by-side object
comparer (`c`), breakpoint shortcut (`b`), and configures the active debugger
adapter.
"""

from __future__ import annotations

import builtins
import sys

from debug_dojo._compare import inspect_objects_side_by_side
from debug_dojo.adapters import DebuggerType, setup_debugger

DEFAULT_PROMPT = "debug-dojo> "

__all__ = [
    "DEFAULT_PROMPT",
    "DebuggerType",
    "install_breakpoint",
    "install_compare",
    "install_features",
    "install_inspect",
    "install_rich_print",
    "install_tools",
    "rich_traceback",
    "set_debugger",
]


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
    """Configure the debugger backend and interactive prompt.

    Args:
        debugger (DebuggerType | None): Optional debugger backend override.

    """
    setup_debugger(debugger)
    sys.ps1 = DEFAULT_PROMPT


def install_tools(debugger: DebuggerType | None = None) -> None:
    """Install all opinionated debugging tools and features.

    Args:
        debugger (DebuggerType | None): Optional debugger backend override.

    """
    set_debugger(debugger)
    rich_traceback()
    install_features()
