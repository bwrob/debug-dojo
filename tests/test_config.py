"""Test the `_config` module."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer import Exit

from debug_dojo._config import (
    load_config,
    load_raw_config,
    resolve_config_path,
    validated_and_updated_config,
)
from debug_dojo._config_models import DebugDojoConfig, DebuggerType


@pytest.fixture
def mock_config_file(tmp_path: Path) -> Path:
    """Create a mock config file."""
    config_content = """
[debuggers]
default = "pudb"
    """
    config_path = tmp_path / "dojo.toml"
    _ = config_path.write_text(config_content)
    return config_path


def test_resolve_config_path_exists(tmp_path: Path) -> None:
    """Test that the config path is resolved correctly when it exists."""
    config_path = tmp_path / "dojo.toml"
    _ = config_path.touch()
    resolved_path = resolve_config_path(config_path)
    assert resolved_path == config_path.resolve()


def test_resolve_config_path_not_exists() -> None:
    """Test that a FileNotFoundError is raised when the config path does not exist."""
    with pytest.raises(FileNotFoundError):
        _ = resolve_config_path(Path("non_existent_file.toml"))


def test_load_raw_config(mock_config_file: Path) -> None:
    """Test that the raw config is loaded correctly."""
    raw_config = load_raw_config(mock_config_file)
    assert raw_config == {"debuggers": {"default": "pudb"}}


def test_validated_and_updated_config() -> None:
    """Test that the config is validated and updated correctly."""
    raw_config = {"debuggers": {"default": "pudb"}}
    config = validated_and_updated_config(raw_config, verbose=False)
    assert isinstance(config, DebugDojoConfig)
    assert config.debuggers.default == DebuggerType.PUDB


def test_validated_and_updated_config_invalid() -> None:
    """Test that an Exit is raised when the config is invalid."""
    raw_config = {"debuggers": {"default": "invalid"}}
    with pytest.raises(Exit):
        _ = validated_and_updated_config(raw_config, verbose=False)


def test_load_config(mock_config_file: Path) -> None:
    """Test that the config is loaded correctly."""
    config = load_config(mock_config_file)
    assert config.debuggers.default == DebuggerType.PUDB


def test_load_config_no_file() -> None:
    """Test that the default config is loaded when no file is found."""
    with patch("pathlib.Path.exists", return_value=False):
        config = load_config()
        assert config == DebugDojoConfig()


def test_load_config_override_debugger() -> None:
    """Test that the debugger can be overridden."""
    config = load_config(debugger=DebuggerType.IPDB)
    assert config.debuggers.default == DebuggerType.IPDB
