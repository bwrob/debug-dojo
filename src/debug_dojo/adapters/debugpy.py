"""Third-party `debugpy` remote debugger adapter."""

from __future__ import annotations

import json
import os
import sys
from typing import TYPE_CHECKING

from rich import print as rich_print

from debug_dojo.adapters import dpdb
from debug_dojo.adapters._base import BREAKPOINT_ENV_VAR, DebuggerType

if TYPE_CHECKING:
    from types import TracebackType

DEFAULT_DEBUGPY_HOST = "localhost"
DEFAULT_DEBUGPY_PORT = 1992


def setup() -> None:
    """Set Debugpy as the active debugger and wait for client connection."""
    try:
        import debugpy
    except ImportError:
        rich_print(
            "[yellow]Debugpy is not installed. "
            "Please install it to use this debugger. "
            "Defaulting to internal dpdb debugger.[/yellow]"
        )
        dpdb.setup()
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


def post_mortem(tb: TracebackType | None = None) -> None:
    """Enter post-mortem debugging via internal DPDB fallback.

    Args:
        tb (TracebackType | None): Traceback to inspect.

    """
    dpdb.post_mortem(tb)
