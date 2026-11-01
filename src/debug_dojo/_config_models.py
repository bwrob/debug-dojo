"""Configuration models for Debug Dojo.

This module defines the runtime settings data structures for Debug Dojo,
including debugger backend options, exception behavior, and built-in mnemonics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DebuggerType(StrEnum):
    """Supported debugger backends."""

    DEBUGPY = "debugpy"
    IPDB = "ipdb"
    PDB = "pdb"
    PUDB = "pudb"

    @property
    def set_trace_hook(self) -> str:
        """Module-level hook string for PYTHONBREAKPOINT."""
        if self is DebuggerType.DEBUGPY:
            return "debugpy.breakpoint"
        return f"{self.value}.set_trace"


@dataclass(frozen=True, slots=True)
class DojoSettings:
    """Runtime configuration settings for Debug Dojo."""

    debugger: DebuggerType = DebuggerType.PDB
    """Default debugger to use for breakpoints."""
    post_mortem: bool = True
    """Whether to enter post-mortem debugging on unhandled exceptions."""
    rich_traceback: bool = True
    """Whether to install Rich traceback handler for enhanced error reporting."""
    show_locals: bool = False
    """Whether to display local variables in exception tracebacks."""
    debugpy_host: str = "localhost"
    """Host address for debugpy server."""
    debugpy_port: int = 1992
    """Port number for debugpy server."""
    debugpy_wait_for_client: bool = True
    """Whether debugpy should wait for an incoming client connection."""
    ipdb_context_lines: int = 20
    """Number of context lines to display in IPDB."""
    prompt_name: str = "debug-dojo> "
    """REPL prompt string."""
    inspect_mnemonic: str = "i"
    """Mnemonic to expose rich.inspect in builtins (empty to disable)."""
    print_mnemonic: str = "p"
    """Mnemonic to expose rich.print in builtins (empty to disable)."""
    compare_mnemonic: str = "c"
    """Mnemonic to expose object comparison in builtins (empty to disable)."""
    breakpoint_mnemonic: str = "b"
    """Mnemonic to expose breakpoint() in builtins (empty to disable)."""


DebugDojoConfig = DojoSettings
