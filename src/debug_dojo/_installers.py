"""Module for installing opinionated debugging tools into Python's builtins."""

from __future__ import annotations

import builtins

from rich import inspect as rich_inspect, print as rich_print, traceback

from debug_dojo import _dpdb
from debug_dojo._compare import inspect_objects_side_by_side

__all__ = ["install_tools"]


def _inspect_with_defaults(obj: object, **kwargs: bool) -> None:
    """Inspect an object using Rich with methods and private attributes enabled."""
    if not kwargs:
        kwargs = {"methods": True, "private": True}
    rich_inspect(obj, console=None, title="", **kwargs)


def install_tools() -> None:
    """Configure `dpdb` and inject `b`, `p`, `i`, and `c` into `builtins`.

    >>> install_tools()
    >>> import builtins
    >>> all(callable(getattr(builtins, name)) for name in ("b", "p", "i", "c"))
    True

    """
    _dpdb.setup()
    _ = traceback.install(show_locals=False)
    builtins.__dict__["b"] = breakpoint
    builtins.__dict__["p"] = rich_print
    builtins.__dict__["i"] = _inspect_with_defaults
    builtins.__dict__["c"] = inspect_objects_side_by_side
