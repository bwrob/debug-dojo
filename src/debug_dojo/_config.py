"""Debug Dojo configuration module.

It includes configurations for different debuggers, exception handling, and features
that can be enabled or disabled.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeAlias, cast

from dacite import DaciteError, from_dict
from rich import print as rich_print
from tomlkit import parse
from tomlkit.exceptions import TOMLKitError
from typer import Exit

from debug_dojo._config_models import (
    DACITE_CONFIG,
    DebugDojoConfig,
    DebugDojoConfigV1,
    DebugDojoConfigV2,
    DebuggerType,
)

JSON: TypeAlias = (
    Mapping[str, "JSON"] | Sequence["JSON"] | str | int | float | bool | None
)


def _validate_model(
    model: type[DebugDojoConfigV1 | DebugDojoConfigV2],
    raw_config: JSON,
) -> DebugDojoConfigV1 | DebugDojoConfigV2:
    if not isinstance(raw_config, dict):
        msg = "Configuration must be a dictionary."
        raise DaciteError(msg)
    return from_dict(data_class=model, data=raw_config, config=DACITE_CONFIG)


def resolve_config_path(config_path: Path | None) -> Path | None:
    """Resolve the configuration path.

    Returning a default if none is provided.

    Args:
        config_path (Path | None): The explicit path to the configuration file, or None.

    Returns:
        Path | None: The resolved absolute path to the configuration file, or None if no
                     configuration file is found and no explicit path was given.

    Raises:
        FileNotFoundError: If an explicit `config_path` is provided but the file
                           does not exist.

    """
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


def load_raw_config(config_path: Path) -> JSON:
    """Load the Debug Dojo configuration from a file.

    Currently supports 'dojo.toml' or 'pyproject.toml'. If no path is provided, it
    checks the current directory for these files.

    Args:
        config_path (Path): The absolute path to the configuration file.

    Returns:
        JSON: The raw configuration data as a JSON-like dictionary.

    Raises:
        ValueError: If there is an error parsing the TOML file.

    """
    config_str = config_path.read_text(encoding="utf-8")

    try:
        config_data = parse(config_str).unwrap()
    except TOMLKitError as e:
        msg = f"Error parsing configuration file {config_path.resolve()}.."
        raise ValueError(msg) from e

    if config_path.name != "pyproject.toml":
        return config_data

    # If config is in [tool.debug_dojo] (pyproject.toml), extract it.
    try:
        dojo_config = cast("JSON", config_data["tool"]["debug_dojo"])
    except KeyError:
        return {}
    else:
        return dojo_config


def validated_and_updated_config(
    raw_config: JSON,
    *,
    verbose: bool,
) -> DebugDojoConfig:
    """Validate and update the raw configuration to the latest DebugDojoConfig version.

    Args:
        raw_config (JSON): The raw configuration data loaded from a file.
        verbose (bool): If True, print verbose messages during validation and update.

    Returns:
        DebugDojoConfig: A validated and updated DebugDojoConfig instance.

    Raises:
        typer.Exit: If the configuration cannot be validated against any known version.

    """
    config: DebugDojoConfigV1 | DebugDojoConfigV2 | None = None

    for model in (DebugDojoConfigV2, DebugDojoConfigV1):
        model_name = model.__name__
        try:
            config = _validate_model(model, raw_config)
        except (DaciteError, TypeError, ValueError) as e:
            if verbose:
                msg = (
                    f"[yellow]Configuration validation error for {model_name}:\n{e}\n\n"
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
    """Load the Debug Dojo configuration.

    Return a DebugDojoConfig instance with the loaded configuration.

    If no configuration file is found, it returns a default configuration. If a debugger
    is specified, it overrides the config.

    Args:
        config_path (Path | None): Optional path to a configuration file.
        verbose (bool): If True, print verbose messages during configuration loading.
        debugger (DebuggerType | None): Optional debugger type to override the default
                                        debugger specified in the configuration.

    Returns:
        DebugDojoConfig: The loaded and potentially overridden DebugDojoConfig instance.

    """
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
    config = validated_and_updated_config(raw_config, verbose=verbose)

    # If a debugger is specified, override the config.
    if debugger:
        config.debuggers.default = debugger

    return config
