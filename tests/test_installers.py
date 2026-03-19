"""Test the `_installers` module."""

import builtins
import os
import sys
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from debug_dojo._config_models import (
    DebugDojoConfig,
    DebuggerType,
    DebugpyConfig,
    IpdbConfig,
    PdbConfig,
    PudbConfig,
)
from debug_dojo._installers import (
    BREAKPOINT_ENV_VAR,
    IPDB_CONTEXT_SIZE,
    install_breakpoint,
    install_by_config,
    install_compare,
    install_features,
    install_inspect,
    install_rich_print,
    set_debugger,
    use_debugpy,
    use_ipdb,
    use_pdb,
    use_pudb,
)


@pytest.fixture(autouse=True)
def cleanup_builtins() -> Iterator[None]:
    """Clean up builtins after each test."""
    yield
    builtins_to_cleanup: list[str] = ["i", "p", "c", "b"]
    for key in builtins_to_cleanup:
        if hasattr(builtins, key):
            delattr(builtins, key)


@patch("pdb.set_trace")
def test_use_pdb(mock_set_trace: MagicMock) -> None:
    """Test that PDB is set as the default debugger."""
    config = PdbConfig()
    use_pdb(config)
    assert os.environ[BREAKPOINT_ENV_VAR] == "pdb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("pudb.set_trace")
def test_use_pudb(mock_set_trace: MagicMock) -> None:
    """Test that PuDB is set as the default debugger."""
    config = PudbConfig()
    use_pudb(config)
    assert os.environ[BREAKPOINT_ENV_VAR] == "pudb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("ipdb.set_trace")
def test_use_ipdb(mock_set_trace: MagicMock) -> None:
    """Test that IPDB is set as the default debugger."""
    config = IpdbConfig(context_lines=10)
    use_ipdb(config)
    assert os.environ[BREAKPOINT_ENV_VAR] == "ipdb.set_trace"
    assert os.environ[IPDB_CONTEXT_SIZE] == "10"
    assert sys.breakpointhook == mock_set_trace


@patch("debugpy.listen")
@patch("debugpy.wait_for_client")
@patch("debugpy.breakpoint")
def test_use_debugpy(
    mock_breakpoint: MagicMock,
    mock_wait_for_client: MagicMock,
    mock_listen: MagicMock,
) -> None:
    """Test that Debugpy is set as the default debugger."""
    config = DebugpyConfig(host="localhost", port=5678)
    use_debugpy(config)
    assert os.environ[BREAKPOINT_ENV_VAR] == "debugpy.breakpoint"
    assert sys.breakpointhook == mock_breakpoint
    mock_listen.assert_called_once_with(("localhost", 5678))
    mock_wait_for_client.assert_called_once()


def test_inspect() -> None:
    """Test that the inspect function is installed in builtins."""
    install_inspect("i")
    assert hasattr(builtins, "i")


def test_compare() -> None:
    """Test that the compare function is installed in builtins."""
    install_compare("c")
    assert hasattr(builtins, "c")


def test_breakpoint() -> None:
    """Test that the breakpoint function is installed in builtins."""
    install_breakpoint("b")
    assert hasattr(builtins, "b")


def test_rich_print() -> None:
    """Test that the rich print function is installed in builtins."""
    install_rich_print("p")
    assert hasattr(builtins, "p")


@patch("debug_dojo._installers.install_inspect")
@patch("debug_dojo._installers.install_rich_print")
@patch("debug_dojo._installers.install_compare")
@patch("debug_dojo._installers.install_breakpoint")
def test_install_features(
    mock_breakpoint: MagicMock,
    mock_compare: MagicMock,
    mock_rich_print: MagicMock,
    mock_inspect: MagicMock,
    config: DebugDojoConfig,
) -> None:
    """Test that the specified debugging features are installed."""
    config.features.rich_inspect = "i"
    config.features.rich_print = "p"
    config.features.comparer = "c"
    config.features.breakpoint = "b"

    install_features(config.features)

    mock_inspect.assert_called_once_with("i")
    mock_rich_print.assert_called_once_with("p")
    mock_compare.assert_called_once_with("c")
    mock_breakpoint.assert_called_once_with("b")


@patch("debug_dojo._installers.use_pdb")
def test_set_debugger_pdb(mock_use_pdb: MagicMock, config: DebugDojoConfig) -> None:
    """Test that the PDB debugger is set correctly."""
    config.debuggers.default = DebuggerType.PDB
    set_debugger(config.debuggers)
    mock_use_pdb.assert_called_once_with(config.debuggers.pdb)


@patch("debug_dojo._installers.install_features")
@patch("debug_dojo._installers.set_exceptions")
@patch("debug_dojo._installers.set_debugger")
def test_install_by_config(
    mock_set_debugger: MagicMock,
    mock_set_exceptions: MagicMock,
    mock_install_features: MagicMock,
    config: DebugDojoConfig,
) -> None:
    """Test that the debugging tools are installed by config."""
    install_by_config(config)
    mock_set_debugger.assert_called_once_with(config.debuggers)
    mock_set_exceptions.assert_called_once_with(config.exceptions)
    mock_install_features.assert_called_once_with(config.features)
