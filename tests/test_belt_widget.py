"""Tests for the Belt Widget."""

import pytest
from textual.app import App
from textual.widgets import Static

from debug_dojo._tui import BeltWidget


@pytest.mark.asyncio
async def test_belt_stats_update() -> None:
    """Test that belt stats can be updated."""
    widget = BeltWidget()
    app = App[None]()

    async with app.run_test():
        await app.mount(widget)

        # Method doesn't exist yet
        widget.update_stats("Black", 42)

        stats_static = widget.query_one("#belt_stats", Static)
        # Verify content by checking render output (approximate)
        # render() returns the renderable.
        content = str(stats_static.render())
        assert "Black" in content
        assert "42" in content
