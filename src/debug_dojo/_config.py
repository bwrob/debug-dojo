from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, cast

import tomlkit
from pydantic import BaseModel, ConfigDict
from rich import print as rich_print


class DebuggerType(Enum):
    """Enum for different types of debuggers."""

    PDB = "pdb"
    PUDB = "pudb"


class Features(BaseModel):
    """Configuration for installing debug features."""

    model_config = ConfigDict(extra="forbid")  # pyright: ignore[reportUnannotatedClassAttribute]

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


class DebugDojoConfig(BaseModel):
    """Configuration for Debug Dojo."""

    model_config = ConfigDict(extra="forbid")  # pyright: ignore[reportUnannotatedClassAttribute]

    debugger: DebuggerType = DebuggerType.PUDB
    """The type of debugger to use."""
    features: Features = Features()
    """Features to install for debugging."""


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
    return DebugDojoConfig.model_validate(raw_config)
