"""Test the `_config` module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from dacite import DaciteError
from typer import Exit

from debug_dojo._config import (
    _validate_model,
    load_config,
    load_raw_config,
    resolve_config_path,
    validated_and_updated_config,
)
from debug_dojo._config_models import (
    DebugDojoConfig,
    DebugDojoConfigV1,
    DebuggerType,
)


@pytest.fixture
def mock_config_file(tmp_path: Path) -> Path:
    """Create a mock config file.

    Returns:
        Path: The path to the created mock configuration file.

    """
    config_content = """
[debuggers]
default = "pudb"
    """
    config_path = tmp_path / "dojo.toml"
    _ = config_path.write_text(config_content, encoding="utf-8")
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


def test_validate_model_non_dict() -> None:
    """Test that _validate_model raises DaciteError when input is not a dict."""
    with pytest.raises(DaciteError, match="must be a dictionary"):
        _ = _validate_model(DebugDojoConfig, "not_a_dict")  # type: ignore[arg-type]


def test_read_config_file_invalid_toml(tmp_path: Path) -> None:
    """Test load_raw_config with invalid TOML."""
    bad_toml = tmp_path / "bad.toml"
    bad_toml.write_text("invalid = [toml", encoding="utf-8")
    with pytest.raises(ValueError, match="Error parsing configuration file"):
        _ = load_raw_config(bad_toml)


def test_read_config_file_pyproject_tool_section(tmp_path: Path) -> None:
    """Test load_raw_config extracts [tool.debug_dojo] from pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.debug_dojo.debuggers]\ndefault = "pdb"\n',
        encoding="utf-8",
    )
    data = load_raw_config(pyproject)
    assert data == {"debuggers": {"default": "pdb"}}


def test_validated_and_updated_config_v2_not_verbose() -> None:
    """Test updating V2 config when verbose is False."""
    raw_config = {"gamification": False}
    config = validated_and_updated_config(raw_config, verbose=False)
    assert isinstance(config, DebugDojoConfig)


def test_validated_and_updated_config_verbose_invalid() -> None:
    """Test validation with verbose=True triggers diagnostic printing."""
    raw_config = {"debuggers": {"default": "unknown_debugger"}}
    with pytest.raises(Exit):
        _ = validated_and_updated_config(raw_config, verbose=True)


def test_load_config_no_file_verbose() -> None:
    """Test load_config with verbose=True when no file exists."""
    with patch("debug_dojo._config.resolve_config_path", return_value=None):
        config = load_config(None, verbose=True)
        assert config == DebugDojoConfig()


def test_config_v1_update() -> None:
    """Test updating legacy V1 config to V2."""
    v1 = DebugDojoConfigV1()
    v2 = v1.update()
    assert v2.debuggers.default == v1.debugger
