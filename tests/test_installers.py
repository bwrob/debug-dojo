"""Test the `_installers` module."""

from __future__ import annotations

import builtins
import os
import sys
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from debug_dojo._installers import (
    BREAKPOINT_ENV_VAR,
    DEFAULT_DEBUGPY_HOST,
    DEFAULT_DEBUGPY_PORT,
    DEFAULT_IPDB_CONTEXT_LINES,
    DEFAULT_PROMPT,
    IPDB_CONTEXT_SIZE,
    DebuggerType,
    install_breakpoint,
    install_compare,
    install_features,
    install_inspect,
    install_rich_print,
    install_tools,
    rich_traceback,
    set_debugger,
    use_debugpy,
    use_ipdb,
    use_pdb,
    use_pudb,
)


@pytest.fixture(autouse=True)  # ruff: ignore[pytest-fixture-autouse] -- fixture must automatically reset Python builtins state after every installer test
def cleanup_builtins() -> Iterator[None]:
    """Clean up builtins after each test."""
    yield
    builtins_to_cleanup: list[str] = ["i", "p", "c", "b"]
    for key in builtins_to_cleanup:
        if hasattr(builtins, key):
            delattr(builtins, key)


@patch("pdb.set_trace")
def test_use_pdb(mock_set_trace: MagicMock) -> None:
    """Test that PDB is set as the active debugger."""
    use_pdb()
    assert os.environ[BREAKPOINT_ENV_VAR] == "pdb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("pudb.set_trace")
def test_use_pudb(mock_set_trace: MagicMock) -> None:
    """Test that PuDB is set as the active debugger."""
    use_pudb()
    assert os.environ[BREAKPOINT_ENV_VAR] == "pudb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("ipdb.set_trace")
def test_use_ipdb(mock_set_trace: MagicMock) -> None:
    """Test that IPDB is set as the active debugger."""
    use_ipdb()
    assert os.environ[BREAKPOINT_ENV_VAR] == "ipdb.set_trace"
    assert os.environ[IPDB_CONTEXT_SIZE] == DEFAULT_IPDB_CONTEXT_LINES
    assert sys.breakpointhook == mock_set_trace


@patch("debugpy.listen")
@patch("debugpy.wait_for_client")
@patch("debugpy.breakpoint")
def test_use_debugpy(
    mock_breakpoint: MagicMock,
    mock_wait_for_client: MagicMock,
    mock_listen: MagicMock,
) -> None:
    """Test that Debugpy is set as the active debugger."""
    use_debugpy()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debugpy.breakpoint"
    assert sys.breakpointhook == mock_breakpoint
    mock_listen.assert_called_once_with((DEFAULT_DEBUGPY_HOST, DEFAULT_DEBUGPY_PORT))
    mock_wait_for_client.assert_called_once()


def test_inspect() -> None:
    """Test that the inspect function is installed in builtins."""
    install_inspect()
    assert hasattr(builtins, "i")


def test_compare() -> None:
    """Test that the compare function is installed in builtins."""
    install_compare()
    assert hasattr(builtins, "c")


def test_breakpoint() -> None:
    """Test that the breakpoint function is installed in builtins."""
    install_breakpoint()
    assert hasattr(builtins, "b")


def test_rich_print() -> None:
    """Test that the rich print function is installed in builtins."""
    install_rich_print()
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
) -> None:
    """Test that all opinionated debugging features are installed."""
    install_features()

    mock_inspect.assert_called_once_with()
    mock_rich_print.assert_called_once_with()
    mock_compare.assert_called_once_with()
    mock_breakpoint.assert_called_once_with()


def test_set_debugger_none() -> None:
    """Test that set_debugger with debugger=None does not enforce a debugger."""
    set_debugger(None)
    assert sys.ps1 == DEFAULT_PROMPT


@patch("debug_dojo._installers.use_pdb")
def test_set_debugger_pdb(mock_use_pdb: MagicMock) -> None:
    """Test that the PDB debugger is set correctly."""
    set_debugger(DebuggerType.PDB)
    mock_use_pdb.assert_called_once_with()
    assert sys.ps1 == DEFAULT_PROMPT


@patch("debug_dojo._installers.use_ipdb")
def test_set_debugger_ipdb(mock_use_ipdb: MagicMock) -> None:
    """Test that the IPDB debugger is set correctly."""
    set_debugger(DebuggerType.IPDB)
    mock_use_ipdb.assert_called_once_with()


@patch("debug_dojo._installers.use_pudb")
def test_set_debugger_pudb(mock_use_pudb: MagicMock) -> None:
    """Test set_debugger with PUDB."""
    set_debugger(DebuggerType.PUDB)
    mock_use_pudb.assert_called_once_with()


@patch("debug_dojo._installers.use_debugpy")
def test_set_debugger_debugpy(mock_use_debugpy: MagicMock) -> None:
    """Test set_debugger with DEBUGPY."""
    set_debugger(DebuggerType.DEBUGPY)
    mock_use_debugpy.assert_called_once_with()


@patch("debug_dojo._installers.install_features")
@patch("debug_dojo._installers.rich_traceback")
@patch("debug_dojo._installers.set_debugger")
def test_install_tools(
    mock_set_debugger: MagicMock,
    mock_rich_traceback: MagicMock,
    mock_install_features: MagicMock,
) -> None:
    """Test that the opinionated debugging tools are installed."""
    install_tools(DebuggerType.PDB)
    mock_set_debugger.assert_called_once_with(DebuggerType.PDB)
    mock_rich_traceback.assert_called_once_with()
    mock_install_features.assert_called_once_with()


def test_use_pudb_not_installed() -> None:
    """Test use_pudb when PuDB is not importable."""
    with patch.dict("sys.modules", {"pudb": None}):
        use_pudb()


def test_use_ipdb_not_installed() -> None:
    """Test use_ipdb when IPDB is not importable."""
    with patch.dict("sys.modules", {"ipdb": None}):
        use_ipdb()


def test_use_debugpy_not_installed() -> None:
    """Test use_debugpy when Debugpy is not importable."""
    with patch.dict("sys.modules", {"debugpy": None}):
        use_debugpy()


def test_inspect_with_kwargs() -> None:
    """Test calling inspect with custom kwargs."""
    install_inspect()
    inspect_fn = getattr(builtins, "i")  # ruff: ignore[get-attr-with-constant] -- dynamically retrieve injected mnemonic from builtins module
    inspect_fn({"foo": "bar"}, methods=False)


@patch("rich.traceback.install")
def test_rich_traceback(mock_install: MagicMock) -> None:
    """Test rich_traceback installs Rich traceback without locals."""
    rich_traceback()
    mock_install.assert_called_once_with(show_locals=False)
