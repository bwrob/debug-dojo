"""Tests for the Textual App foundation."""

from textual.app import App
from textual.screen import Screen

from debug_dojo._tui import DojoApp, MainScreen


def test_app_structure_exists() -> None:
    """Verify that the DojoApp and MainScreen classes exist."""
    assert issubclass(DojoApp, App), "DojoApp must inherit from Textual App"
    assert issubclass(MainScreen, Screen), "MainScreen must inherit from Textual Screen"


def test_app_instantiation() -> None:
    """Test that the app can be instantiated."""
    app = DojoApp()
    assert app is not None
