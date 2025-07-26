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
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)
        return config_path

    # Default configuration path
    for path in (Path("dojo.toml"), Path("pyproject.toml")):
        if path.exists():
            return path
    return None


def load_config(config_path: Path | None = None) -> DebugDojoConfig:
    """Load the Debug Dojo configuration from a file."""
    resolved_path = resolve_config_path(config_path)
    if not resolved_path:
        return DebugDojoConfig()

    # Load the configuration from the file
    with resolved_path.open("rb") as f:
        config_data = tomlkit.load(f).unwrap()

    # Config is part of pyproject.toml, so we need to extract it
    if "tool" in config_data and "debug_dojo" in config_data["tool"]:
        config_data = cast(dict[str, Any], config_data["tool"]["debug_dojo"])
    else:
        msg = (
            f"Configuration for 'debug_dojo' not found in {resolved_path}. "
            "Ensure it is defined under [tool.debug_dojo] in the TOML file."
        )
        raise ValueError(msg)

    try:
        return DebugDojoConfig.model_validate(config_data)
    except Exception as e:
        msg = f"Error validating configuration: {e}"
        raise ValueError(msg) from e
