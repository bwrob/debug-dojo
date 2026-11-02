"""Standard library `pdb` debugger adapter."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any, cast

from debug_dojo.adapters._base import BREAKPOINT_ENV_VAR, DebuggerType

if TYPE_CHECKING:
    from types import TracebackType


def setup() -> None:
    """Set standard library PDB as the active debugger."""
    import pdb

    os.environ[BREAKPOINT_ENV_VAR] = DebuggerType.PDB.set_trace_hook
    sys.breakpointhook = cast("Any", pdb.set_trace)


def post_mortem(tb: TracebackType | None = None) -> None:
    """Enter post-mortem debugging using standard library PDB.

    Args:
        tb (TracebackType | None): Traceback to inspect.

    """
    import pdb

    pdb.post_mortem(tb)
