"""Debug Dojo configuration module.

It includes configurations for different debuggers, exception handling,
and features that can be enabled or disabled.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TypeAlias, cast

from pydantic import ValidationError
from rich import print as rich_print
from tomlkit import parse
from tomlkit.exceptions import TOMLKitError
from typer import Exit

from ._config_models import (
    DebugDojoConfig,
    DebugDojoConfigV1,
    DebugDojoConfigV2,
    DebuggerType,
)

JSON_ro: TypeAlias = (
    Mapping[str, "JSON_ro"] | Sequence["JSON_ro"] | str | int | float | bool | None
)


def __filter_pydantic_error_msg(error: ValidationError) -> str:
    """Filter out specific lines from a Pydantic validation error."""
    return "\n".join(
        line
        for line in str(error).splitlines()
        if not line.startswith("For further information visit")
    )


def __resolve_config_path(config_path: Path | None) -> Path | None:
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

    # None means - use default config values
    return None


def __load_raw_config(config_path: Path) -> JSON_ro:
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
            dojo_config = cast(
                "dict[str, Any]",  # pyright: ignore[reportExplicitAny]
                config_data["tool"]["debug_dojo"],
            )
        except KeyError:
            return {}
        else:
            return dojo_config

    return config_data


def __validated_and_updated_config(
    raw_config: JSON_ro, *, verbose: bool
) -> DebugDojoConfig:
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
        msg = "[red]Unsupported configuration version or error.[/red]"
        rich_print(msg)
        raise Exit(code=1)

    while not isinstance(config, DebugDojoConfig):
        config = config.update()

    return config


def load_config(
    config_path: Path | None = None,
    *,
    verbose: bool = False,
    debugger: DebuggerType | None = None,
) -> DebugDojoConfig:
    """Load the Debug Dojo configuration and return a DebugDojoConfig instance."""
    resolved_path = __resolve_config_path(config_path)

    if verbose:
        if resolved_path:
            msg = f"Using configuration file: {resolved_path}."
        else:
            msg = "No configuration file found, using default settings."
        rich_print(f"[blue]{msg}[/blue]")

    if not resolved_path:
        return DebugDojoConfig()

    raw_config = __load_raw_config(resolved_path)
    config = __validated_and_updated_config(raw_config, verbose=verbose)

    # If a debugger is specified, override the config.
    if debugger:
        config.debuggers.default = debugger

    return config
