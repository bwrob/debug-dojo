"""Dataclass models for Debug Dojo's configuration.

This module defines the data structures used to validate and manage the configuration of
debug-dojo, including settings for debuggers, exception handling, and features.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from dacite import Config


class DebuggerType(Enum):
    """Enum for different types of debuggers."""

    DEBUGPY = "debugpy"
    IPDB = "ipdb"
    PDB = "pdb"
    PUDB = "pudb"


@dataclass
class Features:
    """Legacy configuration for installing debug features (used in V1 config)."""

    rich_inspect: bool = True
    """Install rich inspect as 'i' for enhanced object inspection."""
    rich_print: bool = True
    """Install rich print as 'p' for enhanced printing."""
    rich_traceback: bool = True
    """Install rich traceback for better error reporting."""
    comparer: bool = True
    """Install comparer as 'c' for side-by-side object comparison."""
    breakpoint: bool = True
    """Install breakpoint as 'b' for setting breakpoints in code."""


@dataclass
class DebugpyConfig:
    """Configuration for debugpy debugger."""

    host: str = "localhost"
    """Host for debugpy debugger."""
    log_to_file: bool = False
    """Whether to log debugpy output to a file."""
    port: int = 1992
    """Port for debugpy debugger."""
    wait_for_client: bool = True
    """Whether to wait for the client to connect before starting debugging."""

    @property
    def set_trace_hook(self) -> str:
        return "debugpy.breakpoint"


@dataclass
class IpdbConfig:
    """Configuration for ipdb debugger."""

    context_lines: int = 20
    """Number of context lines to show in ipdb."""

    @property
    def set_trace_hook(self) -> str:
        return "ipdb.set_trace"


@dataclass
class PdbConfig:
    """Configuration for pdb debugger."""

    @property
    def set_trace_hook(self) -> str:
        return "pdb.set_trace"


@dataclass
class PudbConfig:
    """Configuration for pudb debugger."""

    @property
    def set_trace_hook(self) -> str:
        return "pudb.set_trace"


@dataclass
class DebuggersConfig:
    """Configuration for debuggers."""

    default: DebuggerType = DebuggerType.IPDB
    """Default debugger to use."""
    prompt_name: str = "debug-dojo> "
    """Prompt name for the debugger, used in the REPL."""

    debugpy: DebugpyConfig = field(default_factory=DebugpyConfig)
    """Configuration for debugpy debugger."""
    ipdb: IpdbConfig = field(default_factory=IpdbConfig)
    """Configuration for ipdb debugger."""
    pdb: PdbConfig = field(default_factory=PdbConfig)
    """Configuration for pdb debugger."""
    pudb: PudbConfig = field(default_factory=PudbConfig)
    """Configuration for pudb debugger."""


@dataclass
class ExceptionsConfig:
    """Configuration for exceptions handling."""

    locals_in_traceback: bool = False
    """Include local variables in traceback."""
    post_mortem: bool = True
    """Enable post-mortem debugging after an exception."""
    rich_traceback: bool = True
    """Enable rich traceback for better error reporting."""


@dataclass
class FeaturesConfig:
    """Configuration for installing debug features."""

    breakpoint: str = "b"
    """Install breakpoint as 'b' for setting breakpoints in code."""
    comparer: str = "c"
    """Install comparer as 'c' for side-by-side object comparison."""
    rich_inspect: str = "i"
    """Install rich inspect as 'i' for enhanced object inspection."""
    rich_print: str = "p"
    """Install rich print as 'p' for enhanced printing."""


@dataclass
class DebugDojoConfigV2:
    """Configuration for Debug Dojo."""

    exceptions: ExceptionsConfig = field(default_factory=ExceptionsConfig)
    """Better exception messages."""
    debuggers: DebuggersConfig = field(default_factory=DebuggersConfig)
    """Default debugger and configs."""
    features: FeaturesConfig = field(default_factory=FeaturesConfig)
    """Features mnemonics."""
    gamification: bool = True
    """Enable or disable gamification (Dojo Belts)."""


@dataclass
class DebugDojoConfigV1:
    """Legacy configuration for Debug Dojo (version 1)."""

    debugger: DebuggerType = DebuggerType.PUDB
    """The type of debugger to use."""
    features: Features = field(default_factory=Features)
    """Features to install for debugging."""

    def update(self) -> DebugDojoConfigV2:
        """Update the configuration to the latest version."""
        v2_exceptions = ExceptionsConfig(
            rich_traceback=self.features.rich_traceback,
        )
        v2_debuggers = DebuggersConfig(default=self.debugger)
        v2_features = FeaturesConfig(
            rich_inspect="i" if self.features.rich_inspect else "",
            rich_print="p" if self.features.rich_print else "",
            comparer="c" if self.features.comparer else "",
            breakpoint="b" if self.features.breakpoint else "",
        )
        return DebugDojoConfigV2(
            exceptions=v2_exceptions,
            debuggers=v2_debuggers,
            features=v2_features,
        )


DebugDojoConfig = DebugDojoConfigV2

DACITE_CONFIG = Config(cast=[Enum], strict=True)
