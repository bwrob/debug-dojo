"""Debugging tools for Python.

This module provides functions to set up debugging tools like PuDB and Rich Traceback.
It checks for the availability of these tools and configures them accordingly.
"""

import builtins
import os
import sys

import pudb  # pyright: ignore[reportMissingTypeStubs]
from rich import (
    inspect,
    traceback,
)
from rich import (
    print as rich_print,
)

from .compareres import inspect_objects_side_by_side

BREAKPOINT_ENV_VAR = "PYTHONBREAKPOINT"
PUDB_SET_TRACE = "pudb.set_trace"


def use_pudb() -> None:
    """Check if PuDB is available and set it as the default debugger."""
    # Set the environment variable. This will primarily affect child processes or later
    # Python startup if the script is re-run.
    os.environ[BREAKPOINT_ENV_VAR] = PUDB_SET_TRACE

    # Crucially, to make `breakpoint()` work *immediately* in the current process,
    # we need to explicitly set `sys.breakpointhook`.
    sys.breakpointhook = pudb.set_trace


def use_rich_traceback() -> None:
    """Check if Rich Traceback is available and set it as the default."""
    # Install rich traceback to enhance the debugging experience
    _ = traceback.install(show_locals=True)


def install_inspect() -> None:
    """Print the object using a custom inspect function."""

    def inspect_with_defaults(obj: object, **kwargs: object) -> None:
        """Inspect an object using Rich's inspect function."""
        if not kwargs:
            kwargs = {"methods": True, "private": True}
        return inspect(obj, **kwargs)  # pyright: ignore[reportArgumentType]

    # Inject the custom inspect function into builtins
    builtins.i = inspect_with_defaults  # pyright: ignore[reportAttributeAccessIssue]


def install_compare() -> None:
    """Print the object using a custom inspect function."""
    # Inject the custom side-by-side comparison function into builtins
    builtins.c = inspect_objects_side_by_side  # pyright: ignore[reportAttributeAccessIssue]


def install_breakpoint() -> None:
    """Install the breakpoint function."""
    # Set the breakpoint function to use PuDB's set_trace
    builtins.b = pudb.set_trace  # pyright: ignore[reportAttributeAccessIssue]


def install_rich_print() -> None:
    """Install the print from rich."""
    builtins.p = rich_print  # pyright: ignore[reportAttributeAccessIssue]


def install_all() -> None:
    """Install debugging tools."""
    use_pudb()
    use_rich_traceback()

    install_inspect()
    install_compare()
    install_breakpoint()
    install_rich_print()
