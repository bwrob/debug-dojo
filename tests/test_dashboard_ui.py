"""Tests for the Dashboard UI components."""

import pytest

from debug_dojo._tui import BeltWidget, ConfigWidget, DojoApp, HistoryWidget, MainScreen


def test_widgets_exist() -> None:
    """Verify that the widget classes exist."""
    assert HistoryWidget is not None
    assert ConfigWidget is not None
    assert BeltWidget is not None


@pytest.mark.asyncio
async def test_main_screen_structure() -> None:
    """Test that the MainScreen composes the expected widgets."""
    app = DojoApp()
    async with app.run_test() as pilot:
        # The app should push MainScreen on mount
        await pilot.pause()

        # Verify current screen is MainScreen
        assert isinstance(app.screen, MainScreen)
        assert app.screen.id == "main"

        # Verify widgets are present in the DOM
        # query_one raises if not found or multiple found
        assert app.screen.query_one(BeltWidget)
        assert app.screen.query_one(HistoryWidget)
        assert app.screen.query_one(ConfigWidget)

        # Verify IDs
        assert app.screen.query_one("#history_pane")
        assert app.screen.query_one("#config_pane")
