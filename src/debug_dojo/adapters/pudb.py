"""Third-party `pudb` debugger adapter."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any, cast

from rich import print as rich_print

from debug_dojo.adapters import dpdb
from debug_dojo.adapters._base import BREAKPOINT_ENV_VAR, DebuggerType

if TYPE_CHECKING:
    from types import TracebackType


def setup() -> None:
    """Set PuDB as the active debugger, falling back to DPDB if unavailable."""
    try:
        import pudb
    except ImportError:
        rich_print(
            "[yellow]PuDB is not installed. "
            "Please install it to use this debugger. "
            "Defaulting to internal dpdb debugger.[/yellow]"
        )
        dpdb.setup()
        return

    os.environ[BREAKPOINT_ENV_VAR] = DebuggerType.PUDB.set_trace_hook
    sys.breakpointhook = cast("Any", pudb.set_trace)


def post_mortem(tb: TracebackType | None = None) -> None:
    """Enter post-mortem debugging with PuDB, falling back to DPDB if unavailable.

    Args:
        tb (TracebackType | None): Traceback to inspect.

    """
    try:
        import pudb
    except ImportError:
        rich_print("[yellow]PuDB not available, falling back to DPDB.[/yellow]")
        dpdb.post_mortem(tb)
    else:
        pudb.post_mortem(tb)
