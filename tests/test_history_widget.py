"""Tests for the History Widget."""

import pytest
from textual.app import App
from textual.widgets import OptionList

from debug_dojo._tui import HistoryWidget


@pytest.mark.asyncio
async def test_history_population() -> None:
    """Test that history widget can be populated."""
    widget = HistoryWidget()
    app = App[None]()

    async with app.run_test():
        await app.mount(widget)

        # Populate with dummy data
        items = ["Run 1", "Run 2", "Run 3"]
        expected_count = 3

        widget.update_history(items)

        option_list = widget.query_one(OptionList)
        assert option_list.option_count == expected_count

        # We assume input is chronologically ordered (oldest -> newest).
        # We want to select the NEWEST (last in list).
        last_index = expected_count - 1
        assert option_list.highlighted == last_index
