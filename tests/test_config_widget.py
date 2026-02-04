"""Tests for the Config Widget."""

import pytest
from textual.app import App

from debug_dojo._tui import ConfigWidget


@pytest.mark.asyncio
async def test_config_display() -> None:
    """Test that config widget can display configuration."""
    widget = ConfigWidget()
    app = App[None]()

    async with app.run_test():
        await app.mount(widget)

        config = {"target": "foo.py", "backend": "debugpy"}

        widget.show_config(config)

        # Check that we can access the config later (state)
        # or just check that update works.
