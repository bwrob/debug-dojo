"""Debugger backend adapters and dispatch utilities."""

from __future__ import annotations

from debug_dojo.adapters import debugpy, dpdb, ipdb, pdb, pudb
from debug_dojo.adapters._base import (
    BREAKPOINT_ENV_VAR,
    DebuggerAdapter,
    DebuggerType,
    enter_post_mortem,
    get_adapter,
    setup_debugger,
)
from debug_dojo.adapters.dpdb import DojoPdb

__all__ = [
    "BREAKPOINT_ENV_VAR",
    "DebuggerAdapter",
    "DebuggerType",
    "DojoPdb",
    "debugpy",
    "dpdb",
    "enter_post_mortem",
    "get_adapter",
    "ipdb",
    "pdb",
    "pudb",
    "setup_debugger",
]
