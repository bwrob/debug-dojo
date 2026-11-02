"""Test the `_installers` module."""

from __future__ import annotations

import builtins
import sys
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from debug_dojo._installers import (
    DEFAULT_PROMPT,
    DebuggerType,
    install_breakpoint,
    install_compare,
    install_features,
    install_inspect,
    install_rich_print,
    install_tools,
    rich_traceback,
    set_debugger,
)


@pytest.fixture(autouse=True)  # ruff: ignore[pytest-fixture-autouse] -- fixture must automatically reset Python builtins state after every installer test
def cleanup_builtins() -> Iterator[None]:
    """Clean up builtins after each test."""
    yield
    builtins_to_cleanup: list[str] = ["i", "p", "c", "b"]
    for key in builtins_to_cleanup:
        if hasattr(builtins, key):
            delattr(builtins, key)


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


@patch("debug_dojo._installers.setup_debugger")
def test_set_debugger(mock_setup_debugger: MagicMock) -> None:
    """Test set_debugger delegates to setup_debugger and sets sys.ps1."""
    set_debugger(DebuggerType.PDB)
    mock_setup_debugger.assert_called_once_with(DebuggerType.PDB)
    assert sys.ps1 == DEFAULT_PROMPT


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
