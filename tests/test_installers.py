"""Test the `_installers` module."""

from __future__ import annotations

import builtins
import os
import sys
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from debug_dojo._config_models import (
    DebuggerType,
    DojoSettings,
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
    install_tools,
    set_debugger,
    set_exceptions,
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
    """Test that PDB is set as the default debugger."""
    use_pdb()
    assert os.environ[BREAKPOINT_ENV_VAR] == "pdb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("pudb.set_trace")
def test_use_pudb(mock_set_trace: MagicMock) -> None:
    """Test that PuDB is set as the default debugger."""
    use_pudb()
    assert os.environ[BREAKPOINT_ENV_VAR] == "pudb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("ipdb.set_trace")
def test_use_ipdb(mock_set_trace: MagicMock) -> None:
    """Test that IPDB is set as the default debugger."""
    use_ipdb(context_lines=10)
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
    use_debugpy(host="localhost", port=5678, wait_for_client=True)
    assert os.environ[BREAKPOINT_ENV_VAR] == "debugpy.breakpoint"
    assert sys.breakpointhook == mock_breakpoint
    mock_listen.assert_called_once_with(("localhost", 5678))
    mock_wait_for_client.assert_called_once()


@patch("debugpy.listen")
@patch("debugpy.wait_for_client")
@patch("debugpy.breakpoint")
def test_use_debugpy_no_wait(
    mock_breakpoint: MagicMock,
    mock_wait_for_client: MagicMock,
    mock_listen: MagicMock,
) -> None:
    """Test that Debugpy can be used without waiting for client."""
    use_debugpy(host="localhost", port=5678, wait_for_client=False)
    assert os.environ[BREAKPOINT_ENV_VAR] == "debugpy.breakpoint"
    assert sys.breakpointhook == mock_breakpoint
    mock_listen.assert_called_once_with(("localhost", 5678))
    mock_wait_for_client.assert_not_called()


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
    config: DojoSettings,
) -> None:
    """Test that the specified debugging features are installed."""
    install_features(config)

    mock_inspect.assert_called_once_with("i")
    mock_rich_print.assert_called_once_with("p")
    mock_compare.assert_called_once_with("c")
    mock_breakpoint.assert_called_once_with("b")


@patch("debug_dojo._installers.use_pdb")
def test_set_debugger_pdb(mock_use_pdb: MagicMock) -> None:
    """Test that the PDB debugger is set correctly."""
    settings = DojoSettings(debugger=DebuggerType.PDB)
    set_debugger(settings)
    mock_use_pdb.assert_called_once_with("pdb.set_trace")
    assert sys.ps1 == settings.prompt_name


@patch("debug_dojo._installers.use_ipdb")
def test_set_debugger_ipdb(mock_use_ipdb: MagicMock) -> None:
    """Test that the IPDB debugger is set correctly."""
    settings = DojoSettings(debugger=DebuggerType.IPDB, ipdb_context_lines=15)
    set_debugger(settings)
    mock_use_ipdb.assert_called_once_with("ipdb.set_trace", 15)


@patch("debug_dojo._installers.install_features")
@patch("debug_dojo._installers.set_exceptions")
@patch("debug_dojo._installers.set_debugger")
def test_install_tools(
    mock_set_debugger: MagicMock,
    mock_set_exceptions: MagicMock,
    mock_install_features: MagicMock,
    config: DojoSettings,
) -> None:
    """Test that the debugging tools are installed by settings."""
    install_tools(config)
    mock_set_debugger.assert_called_once_with(config)
    mock_set_exceptions.assert_called_once_with(config)
    mock_install_features.assert_called_once_with(config)


def test_install_by_config_alias(config: DojoSettings) -> None:
    """Test that install_by_config is an alias for install_tools."""
    assert install_by_config is install_tools


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


def test_install_features_empty_mnemonics() -> None:
    """Test install functions with empty mnemonics do nothing."""
    install_inspect("")
    install_compare("")
    install_breakpoint("")
    install_rich_print("")


def test_inspect_with_kwargs() -> None:
    """Test calling inspect with custom kwargs."""
    install_inspect("i")
    inspect_fn = getattr(builtins, "i")  # ruff: ignore[get-attr-with-constant] -- dynamically retrieve injected mnemonic from builtins module
    inspect_fn({"foo": "bar"}, methods=False)


@patch("debug_dojo._installers.use_pudb")
def test_set_debugger_pudb(mock_use_pudb: MagicMock) -> None:
    """Test set_debugger with PUDB."""
    settings = DojoSettings(debugger=DebuggerType.PUDB)
    set_debugger(settings)
    mock_use_pudb.assert_called_once_with("pudb.set_trace")


@patch("debug_dojo._installers.use_debugpy")
def test_set_debugger_debugpy(mock_use_debugpy: MagicMock) -> None:
    """Test set_debugger with DEBUGPY."""
    settings = DojoSettings(
        debugger=DebuggerType.DEBUGPY,
        debugpy_host="0.0.0.0",
        debugpy_port=5678,
        debugpy_wait_for_client=False,
    )
    set_debugger(settings)
    mock_use_debugpy.assert_called_once_with(
        "debugpy.breakpoint",
        "0.0.0.0",
        5678,
        wait_for_client=False,
    )


def test_set_exceptions_disabled() -> None:
    """Test set_exceptions when rich_traceback is disabled."""
    set_exceptions(DojoSettings(rich_traceback=False))


@patch("rich.traceback.install")
def test_set_exceptions_enabled(mock_install: MagicMock) -> None:
    """Test set_exceptions when rich_traceback is enabled with locals."""
    set_exceptions(DojoSettings(rich_traceback=True, show_locals=True))
    mock_install.assert_called_once_with(show_locals=True)
