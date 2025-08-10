"""Debug Dojo configuration module.

It includes configurations for different debuggers, exception handling,
and features that can be enabled or disabled.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError
from rich import print as rich_print
from tomlkit import parse
from tomlkit.exceptions import TOMLKitError

from ._config_models import (
    DebugDojoConfig,
    DebugDojoConfigV1,
    DebugDojoConfigV2,
    DebuggerType,
)


def __filter_pydantic_error_msg(error: ValidationError) -> str:
    """Filter out specific lines from a Pydantic validation error."""
    return "\n".join(
        line
        for line in str(error).splitlines()
        if not line.startswith("For further information visit")
    )


def resolve_config_path(config_path: Path | None) -> Path | None:
    """Resolve the configuration path, returning a default if none is provided."""
    if config_path:
        if not config_path.exists():
            msg = f"Configuration file not found:\n{config_path.resolve()}"
            raise FileNotFoundError(msg)
        return config_path.resolve()

    # Default configuration path
    for path in (Path("dojo.toml"), Path("pyproject.toml")):
        if path.exists():
            return path.resolve()
    return None


def load_raw_config(
    config_path: Path,
) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
    """Load the Debug Dojo configuration from a file.

    Currently supports 'dojo.toml' or 'pyproject.toml'.
    If no path is provided, it checks the current directory for these files.
    """
    config_str = config_path.read_text(encoding="utf-8")

    try:
        config_data = parse(config_str).unwrap()
    except TOMLKitError as e:
        msg = f"Error parsing configuration file {config_path.resolve()}."
        raise ValueError(msg) from e

    # If config is in [tool.debug_dojo] (pyproject.toml), extract it.
    if config_path.name == "pyproject.toml":
        try:
            dojo_config = cast("dict[str, Any]", config_data["tool"]["debug_dojo"])
        except KeyError:
            return {}
        else:
            return dojo_config

    return config_data


def load_config(  # noqa: C901
    config_path: Path | None = None,
    *,
    verbose: bool = False,
    debugger: DebuggerType | None = None,
) -> DebugDojoConfig:
    """Load the Debug Dojo configuration and return a DebugDojoConfig instance."""
    resolved_path = resolve_config_path(config_path)

    if verbose:
        if resolved_path:
            msg = f"Using configuration file: {resolved_path}."
        else:
            msg = "No configuration file found, using default settings."
        rich_print(f"[blue]{msg}[/blue]")

    if not resolved_path:
        return DebugDojoConfig()

    raw_config = load_raw_config(resolved_path)

    config = None
    for model in (DebugDojoConfigV2, DebugDojoConfigV1):
        model_name = model.__name__
        try:
            config = model.model_validate(raw_config)
        except ValidationError as e:
            if verbose:
                msg = (
                    f"[yellow]Configuration validation error for {model_name}:\n"
                    f"{__filter_pydantic_error_msg(e)}\n\n"
                    f"Please check your configuration file {resolved_path}.[/yellow]"
                )
                rich_print(msg)
        else:
            if verbose or model_name != DebugDojoConfig.__name__:
                msg = (
                    f"[blue]Using configuration model: {model_name}.\n"
                    f"Current configuration model {DebugDojoConfig.__name__}. [/blue]"
                )
                rich_print(msg)
            break

    if not config:
        msg = (
            f"[red]Unsupported configuration version in {resolved_path.resolve()}.\n"
            "Please update your configuration file.[/red]"
        )
        rich_print(msg)
        sys.exit(1)

    while not isinstance(config, DebugDojoConfig):
        config = config.update()

    # If a debugger is specified, update the config.
    if debugger:
        config.debuggers.default = debugger

    return config
