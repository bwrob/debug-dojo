"""Debug Dojo configuration module.

It includes configurations for different debuggers, exception handling,
and features that can be enabled or disabled.
"""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Any, cast

import tomlkit
from pydantic import BaseModel, ConfigDict, ValidationError
from rich import print as rich_print


class DebuggerType(Enum):
    """Enum for different types of debuggers."""

    PDB = "pdb"
    PUDB = "pudb"
    IPDB = "ipdb"
    DEBUGPY = "debugpy"


class BaseConfig(BaseModel):
    """Base configuration class with extra fields forbidden."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class DebugpyConfig(BaseConfig):
    """Configuration for debugpy debugger."""

    port: int = 1992
    """Port for debugpy debugger."""
    host: str = "localhost"
    """Host for debugpy debugger."""
    wait_for_client: bool = True
    """Whether to wait for the client to connect before starting debugging."""
    log_to_file: bool = False
    """Whether to log debugpy output to a file."""


class IpdbConfig(BaseConfig):
    """Configuration for ipdb debugger."""

    context_lines: int = 20
    """Number of context lines to show in ipdb."""


class DebuggersConfig(BaseConfig):
    """Configuration for debuggers."""

    default: DebuggerType = DebuggerType.IPDB
    """Default debugger to use."""
    debugpy: DebugpyConfig = DebugpyConfig()
    """Configuration for debugpy debugger."""
    ipdb: IpdbConfig = IpdbConfig()
    """Configuration for ipdb debugger."""


class ExceptionsConfig(BaseConfig):
    """Configuration for exceptions handling."""

    rich_traceback: bool = True
    """Enable rich traceback for better error reporting."""
    locals_in_traceback: bool = False
    """Include local variables in traceback."""
    post_mortem: bool = True
    """Enable post-mortem debugging after an exception."""


class FeaturesConfig(BaseConfig):
    """Configuration for installing debug features."""

    rich_inspect: str = "i"
    """Install rich inspect as 'i' for enhanced object inspection."""
    rich_print: str = "p"
    """Install rich print as 'p' for enhanced printing."""
    comparer: str = "c"
    """Install comparer as 'c' for side-by-side object comparison."""
    breakpoint: str = "b"
    """Install breakpoint as 'b' for setting breakpoints in code."""


class DebugDojoConfig(BaseModel):
    """Configuration for Debug Dojo."""

    model_config = ConfigDict(extra="forbid")  # pyright: ignore[reportUnannotatedClassAttribute]

    exceptions: ExceptionsConfig = ExceptionsConfig()
    debuggers: DebuggersConfig = DebuggersConfig()
    """Default debugger and configs."""
    features: FeaturesConfig = FeaturesConfig()
    """Features mnemonics ."""


def resolve_config_path(config_path: Path | None) -> Path | None:
    """Resolve the configuration path, returning a default if none is provided."""
    if config_path:
        if not config_path.exists():
            msg = f"Configuration file not found:\n{config_path.resolve()}"
            raise FileNotFoundError(msg)
        return config_path

    # Default configuration path
    for path in (Path("dojo.toml"), Path("pyproject.toml")):
        if path.exists():
            return path
    return None


def load_raw_config(
    config_path: Path,
) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
    """Load the Debug Dojo configuration from a file.

    Currently supports 'dojo.toml' or 'pyproject.toml'.
    If no path is provided, it checks the current directory for these files.
    """
    with config_path.open("rb") as f:
        config_data = tomlkit.load(f).unwrap()

    # If config is in [tool.debug_dojo] (pyproject.toml), extract it.
    if config_path.name == "dojo.toml":
        return config_data

    if config_path.name == "pyproject.toml":
        try:
            dojo_config = cast(
                "dict[str, Any]",  # pyright: ignore[reportExplicitAny]
                config_data["tool"]["debug_dojo"],
            )
        except KeyError:
            return {}
        else:
            return dojo_config

    # If the file is not recognized, raise an error.
    msg = (
        f"Unsupported configuration file: \n{config_path.resolve()}\n"
        "Expected 'dojo.toml' or 'pyproject.toml'."
    )
    raise ValueError(msg)


def load_config(
    config_path: Path | None = None,
    *,
    verbose: bool = False,
    debugger: DebuggerType | None = None,
) -> DebugDojoConfig:
    """Load the Debug Dojo configuration and return a DebugDojoConfig instance."""
    resolved_path = resolve_config_path(config_path)

    if verbose:
        if resolved_path:
            msg = f"Using configuration file: {resolved_path.resolve()}."
        else:
            msg = "No configuration file found, using default settings."
        rich_print(f"[blue]{msg}[/blue]")

    if not resolved_path:
        return DebugDojoConfig()

    raw_config = load_raw_config(resolved_path)

    try:
        config = DebugDojoConfig.model_validate(raw_config)
    except ValidationError as e:
        msg = (
            f"[red]Configuration validation error:\n{e}\n\n"
            f"Please check your configuration file {resolved_path.resolve()}.[/red]"
        )
        msg = "\n".join(
            [line for line in msg.splitlines() if "For further information" not in line]
        )
        rich_print(msg)
        sys.exit(1)

    if debugger:
        config.debuggers.default = debugger
    return config
