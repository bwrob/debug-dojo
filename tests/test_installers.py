"""Test the `_installers` module."""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from debug_dojo._installers import install_tools


@pytest.fixture(autouse=True)  # ruff: ignore[pytest-fixture-autouse] -- fixture must automatically reset Python builtins state after every installer test
def cleanup_builtins() -> Iterator[None]:
    """Clean up builtins after each test."""
    yield
    for key in ("i", "p", "c", "b"):
        builtins.__dict__.pop(key, None)


@patch("rich.traceback.install")
@patch("debug_dojo._dpdb.setup")
def test_install_tools(
    mock_setup_dpdb: MagicMock,
    mock_traceback_install: MagicMock,
) -> None:
    """Test install_tools configures dpdb, traceback, and builtins."""
    install_tools()
    mock_setup_dpdb.assert_called_once_with()
    mock_traceback_install.assert_called_once_with(show_locals=False)
    for key in ("i", "p", "c", "b"):
        assert hasattr(builtins, key)

    inspect_fn = getattr(builtins, "i")  # ruff: ignore[get-attr-with-constant] -- dynamically retrieve injected mnemonic from builtins module
    inspect_fn({"foo": "bar"})
    inspect_fn({"foo": "bar"}, methods=False)
