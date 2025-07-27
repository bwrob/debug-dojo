from enum import Enum
from pathlib import Path
from typing import Any, cast

import tomlkit
from pydantic import BaseModel


class DebuggerType(Enum):
    """Enum for different types of debuggers."""

    IPDB = "ipdb"
    PDB = "pdb"
    PUDB = "pudb"


class InstallTools(BaseModel):
    """Configuration for installation tools."""

    install_rich_inspect: bool = True
    install_rich_print: bool = True
    install_compare: bool = True
    install_breakpoint: bool = True


class DebugDojoConfig(BaseModel):
    """Configuration for Debug Dojo."""

    # Example field, you can add more fields as needed
    debugger: DebuggerType = DebuggerType.IPDB
    install_tools: InstallTools = InstallTools()


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


def load_raw_config(config_path: Path) -> dict[str, Any]:
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
            dojo_config = cast(dict[str, Any], config_data["tool"]["debug_dojo"])
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


def load_config(config_path: Path | None = None) -> DebugDojoConfig:
    """Load the Debug Dojo configuration and return a DebugDojoConfig instance."""
    resolved_path = resolve_config_path(config_path)
    if not resolved_path:
        return DebugDojoConfig()

    raw_config = load_raw_config(resolved_path)
    return DebugDojoConfig.model_validate(raw_config)
