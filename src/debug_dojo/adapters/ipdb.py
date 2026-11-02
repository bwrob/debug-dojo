"""Third-party `ipdb` debugger adapter."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any, cast

from rich import print as rich_print

from debug_dojo.adapters import dpdb
from debug_dojo.adapters._base import BREAKPOINT_ENV_VAR, DebuggerType

if TYPE_CHECKING:
    from types import TracebackType

IPDB_CONTEXT_SIZE = "IPDB_CONTEXT_SIZE"
DEFAULT_IPDB_CONTEXT_LINES = "20"


def setup() -> None:
    """Set IPDB as the active debugger, falling back to DPDB if unavailable."""
    try:
        import ipdb
    except ImportError:
        rich_print(
            "[yellow]IPDB is not installed. "
            "Please install it to use this debugger. "
            "Defaulting to internal dpdb debugger.[/yellow]"
        )
        dpdb.setup()
        return

    os.environ[BREAKPOINT_ENV_VAR] = DebuggerType.IPDB.set_trace_hook
    os.environ[IPDB_CONTEXT_SIZE] = DEFAULT_IPDB_CONTEXT_LINES
    sys.breakpointhook = cast("Any", ipdb.set_trace)


def post_mortem(tb: TracebackType | None = None) -> None:
    """Enter post-mortem debugging with IPDB, falling back to DPDB if unavailable.

    Args:
        tb (TracebackType | None): Traceback to inspect.

    """
    try:
        import ipdb
    except ImportError:
        rich_print("[yellow]IPDB not available, falling back to DPDB.[/yellow]")
        dpdb.post_mortem(tb)
    else:
        ipdb.post_mortem(tb)
